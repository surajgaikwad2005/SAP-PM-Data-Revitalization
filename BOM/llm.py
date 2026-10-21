"""
Shared Claude Sonnet client, with Langfuse tracing.

Only P2 (duplicate materials) uses this - it asks Sonnet to judge whether two
part descriptions are the same physical item.

Team rule: every LLM call (local or cloud) must pass through Langfuse with the
agent / task name attached.  So chat_json() wraps each call in a Langfuse
"generation" and the script stops if Langfuse is unreachable (unless you pass
--no-langfuse).  Project: "SAP PM Data Revitalization".

Auth: model / host / key are read from ../env (the claude block).
Working route: POST {host}/anthropic/v1/messages  with  Authorization: Bearer <key>.
"""
from __future__ import annotations
import json
import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

ENV_FILE = Path(__file__).resolve().parent.parent / "env"
ANTHROPIC_VERSION = "2023-06-01"

LANGFUSE_PUBLIC_KEY = os.environ.get("LANGFUSE_PUBLIC_KEY", "pk-lf-f5ef6442-962c-4dd3-abff-b1de0295113f")
LANGFUSE_SECRET_KEY = os.environ.get("LANGFUSE_SECRET_KEY", "sk-lf-a405d581-6b95-4b40-b0df-a3558703f287")
LANGFUSE_HOST = os.environ.get("LANGFUSE_HOST") or os.environ.get("LANGFUSE_BASE_URL", "http://65.1.79.48:3000")
LF_PROJECT = "SAP PM Data Revitalization"


def _read_env() -> dict:
    txt = ENV_FILE.read_text(encoding="utf-8", errors="ignore")
    block = next((b for b in re.split(r"-{20,}", txt) if "claude" in b.lower()), txt)
    model = re.search(r"Model Deployment:\s*(\S+)", block)
    endpoint = re.search(r"Project Endpoint:\s*(\S+)", block)
    key = re.search(r"API Key\s*:?\s*([A-Za-z0-9]+)", block)
    return {
        "model": model.group(1).strip() if model else "claude-sonnet-4-6",
        "host": endpoint.group(1).split("/api/")[0].rstrip("/") if endpoint else "",
        "key": key.group(1) if key else "",
    }


CLAUDE = _read_env()
_LF = None
_LF_LOCK = threading.Lock()


# ---------------------------------------------------------------- Langfuse
def get_langfuse(required: bool = True):
    global _LF
    if _LF is not None:
        return _LF or None
    with _LF_LOCK:
        if _LF is not None:
            return _LF or None
        try:
            from langfuse import Langfuse, get_client
            Langfuse(public_key=LANGFUSE_PUBLIC_KEY, secret_key=LANGFUSE_SECRET_KEY, host=LANGFUSE_HOST)
            lf = get_client()
            if not lf.auth_check():
                raise RuntimeError("auth_check() returned False")
            print(f"Langfuse OK -> {LANGFUSE_HOST}  (project: {LF_PROJECT})")
            _LF = lf
            return lf
        except Exception as e:
            if required:
                sys.exit(f"Langfuse unavailable: {e}\n"
                         f"Every LLM call must be traced. Fix Langfuse or run with --no-langfuse.")
            print(f"WARNING: Langfuse unavailable ({e}) - running WITHOUT tracing.")
            _LF = False
            return None


# ---------------------------------------------------------------- transport
def _sonnet(system: str, user: str, max_tokens: int, temperature: float) -> tuple[str, dict]:
    if not CLAUDE["key"] or not CLAUDE["host"]:
        raise RuntimeError("Claude host/key not found in ../env")
    body = {
        "model": CLAUDE["model"],
        "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        "messages": [{"role": "user", "content": user}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    headers = {
        "Authorization": f"Bearer {CLAUDE['key']}",
        "anthropic-version": ANTHROPIC_VERSION,
        "Content-Type": "application/json",
    }
    for attempt in range(6):
        try:
            r = httpx.post(f"{CLAUDE['host']}/anthropic/v1/messages", json=body, timeout=180, headers=headers)
        except (httpx.TimeoutException, httpx.TransportError):
            time.sleep(2 ** attempt + random.random())
            continue
        if r.status_code == 200:
            j = r.json()
            text = "".join(b.get("text", "") for b in j.get("content", []) if b.get("type") == "text")
            return text, j.get("usage", {})
        if r.status_code in (429, 500, 502, 503, 529):       # transient - back off and retry
            time.sleep(2 ** attempt + random.random())
            continue
        raise RuntimeError(f"sonnet {r.status_code}: {r.text[:300]}")
    raise RuntimeError("sonnet: retries exhausted")


def extract_json(raw: str) -> dict:
    """Pull the first complete JSON object out of the model's reply."""
    t = raw.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1]
        t = t[4:] if t[:4].lower() == "json" else t
        t = t.strip().strip("`").strip()
    i = t.find("{")
    if i < 0:
        raise ValueError("no JSON object in reply")
    depth = 0
    in_str = esc = False
    for j in range(i, len(t)):
        c = t[j]
        if in_str:
            esc = (c == "\\" and not esc)
            if c == '"' and not esc:
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return json.loads(t[i:j + 1])
    return json.loads(t[i:])


# ---------------------------------------------------------------- public
def chat_json(system: str, user: str, *, agent: str, task: str, metadata: dict | None = None,
              max_tokens: int = 2000, temperature: float = 0.0, langfuse_required: bool = True) -> dict:
    """One Sonnet call, traced as a Langfuse generation. Returns parsed JSON."""
    lf = get_langfuse(required=langfuse_required)
    meta = {"agent": agent, "task": task, "project": LF_PROJECT, **(metadata or {})}
    if lf is None:
        text, _ = _sonnet(system, user, max_tokens, temperature)
        return extract_json(text)
    with lf.start_as_current_observation(name=agent, as_type="generation", model=CLAUDE["model"],
                                         input={"task": task, "user": user[:2000]}, metadata=meta) as gen:
        try:
            gen.update(tags=[agent])
        except Exception:
            pass
        text, usage = _sonnet(system, user, max_tokens, temperature)
        obj = extract_json(text)
        gen.update(output=obj, usage_details={
            "input": usage.get("input_tokens", 0),
            "output": usage.get("output_tokens", 0),
            "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0),
        })
        return obj


def map_concurrent(fn, items, workers: int = 8):
    """Run fn over items in a thread pool, keeping input order. Errors -> {'_error': ...}."""
    out = [None] * len(items)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fn, it): k for k, it in enumerate(items)}
        for f in futs:
            k = futs[f]
            try:
                out[k] = f.result()
            except Exception as e:                            # noqa: BLE001
                out[k] = {"_error": str(e)}
    return out


def flush():
    lf = get_langfuse(required=False)
    if lf:
        lf.flush()
