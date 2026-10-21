"""
Shared LLM access for code/agent and code/extraction - every call is traced in Langfuse.

Every LLM call, local or cloud, goes through chat() and is recorded in
Langfuse (project "SAP PM Data Revitalization") as a generation with its
prompt, response, token usage, cost, latency and any error. Calls made
inside llm_run() are grouped under one trace per script run, named
"SCE agent | <task>" and tagged with the agent name, component
(agent / extraction) and task, so a run can be found by any of them.

Providers (credentials and endpoints come from the project-root .env):
  local         - vLLM-hosted Qwen (OpenAI-compatible). Self-hosted, so
                  cost is recorded as 0; tokens are still tracked.
  azure_gpt     - Azure AI Foundry GPT deployment (OpenAI v1 API).
  azure_claude  - Azure AI Foundry Claude deployment (Anthropic Messages API).
Cloud costs are priced by Langfuse from its model definitions
(gpt-5.6-sol and claude-sonnet-4-6 both have one on the server).

Usage:
    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # code/
    from common.llm import llm_run, chat

    with llm_run(task="check7_mic_ps_llm_matching", component="agent"):
        text = chat(messages, name="match_mics PS002", metadata={"sce_group": "PS002"},
                    temperature=0)
"""

import contextvars
import os
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from langfuse import Langfuse, propagate_attributes
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

AGENT_NAME = "SCE agent"
LANGFUSE_PROJECT = "SAP PM Data Revitalization"
ANTHROPIC_VERSION = "2023-06-01"

_run = contextvars.ContextVar("sce_llm_run", default={})
_langfuse = None
_openai_clients = {}


def langfuse():
    global _langfuse
    if _langfuse is None:
        _langfuse = Langfuse(
            public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
            secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
            base_url=os.getenv("LANGFUSE_BASE_URL"),
        )
    return _langfuse


def _short(value, limit=200):
    """Langfuse trace-level metadata/tags must be short strings."""
    return str(value)[:limit]


@contextmanager
def llm_run(task, component, metadata=None):
    """One Langfuse trace per script run. component: "agent" or "extraction"."""
    lf = langfuse()
    trace_name = f"{AGENT_NAME} | {task}"
    run_id = f"{task}-{datetime.now():%Y%m%d-%H%M%S}"
    run_meta = {"agent": AGENT_NAME, "component": component, "task": task,
                "project": LANGFUSE_PROJECT, "run_id": run_id}
    run_meta.update({k: _short(v) for k, v in (metadata or {}).items()})
    token = _run.set(run_meta)
    try:
        with lf.start_as_current_observation(
            name=trace_name,
            as_type="agent" if component == "agent" else "chain",
            metadata=run_meta,
        ) as root:
            with propagate_attributes(trace_name=trace_name, session_id=run_id,
                                      tags=[AGENT_NAME, component, task],
                                      metadata={k: _short(v) for k, v in run_meta.items()}):
                trace_url = lf.get_trace_url(trace_id=root.trace_id)
                try:
                    yield root
                except BaseException as e:
                    root.update(level="ERROR", status_message=_short(repr(e), 1000))
                    raise
        print(f"[langfuse] run traced: {trace_url or trace_name} (session {run_id})")
    finally:
        _run.reset(token)
        lf.flush()


def _openai_client(provider):
    if provider not in _openai_clients:
        if provider == "local":
            _openai_clients[provider] = OpenAI(base_url=os.getenv("LOCAL_LLM_BASE_URL"), api_key="not-needed")
        elif provider == "azure_gpt":
            _openai_clients[provider] = OpenAI(
                base_url=os.getenv("AZURE_GPT_ENDPOINT").rstrip("/") + "/openai/v1/",
                api_key=os.getenv("AZURE_GPT_API_KEY"),
            )
        else:
            raise ValueError(f"unknown provider: {provider}")
    return _openai_clients[provider]


def _default_model(provider):
    return {"local": os.getenv("LOCAL_LLM_MODEL"),
            "azure_gpt": os.getenv("AZURE_GPT_DEPLOYMENT"),
            "azure_claude": os.getenv("AZURE_CLAUDE_DEPLOYMENT")}[provider]


def _call_openai_compatible(provider, model, messages, timeout, params):
    resp = _openai_client(provider).chat.completions.create(
        model=model, messages=messages, timeout=timeout, **params)
    usage = resp.usage
    usage_details = ({"input": usage.prompt_tokens, "output": usage.completion_tokens}
                     if usage else None)
    return resp.choices[0].message.content, usage_details


def _call_claude(model, messages, timeout, params):
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    body = {"model": model,
            "max_tokens": params.pop("max_tokens", 4096),
            "messages": [m for m in messages if m["role"] != "system"]}
    if system:
        body["system"] = system
    body.update(params)
    r = requests.post(
        os.getenv("AZURE_CLAUDE_ENDPOINT").rstrip("/") + "/anthropic/v1/messages",
        headers={"x-api-key": os.getenv("AZURE_CLAUDE_API_KEY"),
                 "anthropic-version": ANTHROPIC_VERSION, "content-type": "application/json"},
        json=body, timeout=timeout or 300)
    r.raise_for_status()
    data = r.json()
    text = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
    u = data.get("usage") or {}
    usage_details = {"input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0)}
    for src, dst in (("cache_read_input_tokens", "input_cache_read"),
                     ("cache_creation_input_tokens", "input_cache_creation")):
        if u.get(src):
            usage_details[dst] = u[src]
    return text, usage_details


def chat(messages, *, name, provider="local", model=None, metadata=None, timeout=None, **params):
    """Send a chat request and return the response text. Traced as a Langfuse generation.

    messages: OpenAI-style [{"role": ..., "content": ...}] (system messages are
              moved to Claude's `system` field automatically).
    name:     what this call is for, e.g. "match_mics PS002" - shown in Langfuse.
    metadata: per-call context (e.g. {"sce_group": "PS002"}) added to the trace.
    params:   passed to the API (temperature, max_tokens, extra_body, ...).
    """
    model = model or _default_model(provider)
    run_meta = _run.get()
    gen_meta = {"agent": AGENT_NAME, "provider": provider,
                "component": run_meta.get("component"), "task": run_meta.get("task")}
    gen_meta.update(metadata or {})
    if "extra_body" in params:
        gen_meta["extra_body"] = params["extra_body"]
    model_parameters = {k: v for k, v in params.items()
                        if isinstance(v, (str, int, float, bool)) and k != "extra_body"}

    with langfuse().start_as_current_observation(
        name=name, as_type="generation", model=model, input=messages,
        model_parameters=model_parameters, metadata=gen_meta,
    ) as gen:
        t0 = time.time()
        try:
            if provider == "azure_claude":
                text, usage_details = _call_claude(model, messages, timeout, dict(params))
            else:
                text, usage_details = _call_openai_compatible(provider, model, messages, timeout, params)
        except Exception as e:
            gen.update(level="ERROR", status_message=_short(repr(e), 1000),
                       metadata={**gen_meta, "latency_s": round(time.time() - t0, 2)})
            raise
        update = {"output": text, "usage_details": usage_details}
        if provider == "local":
            # self-hosted vLLM - no per-token price; record an explicit 0 so cost reports are complete
            update["cost_details"] = {"input": 0.0, "output": 0.0}
        gen.update(**update)
        return text
