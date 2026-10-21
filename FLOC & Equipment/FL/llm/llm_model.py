"""Claude (Azure AI Foundry) client with structured-output calls, a tool-use loop and Langfuse tracing."""

from __future__ import annotations

import contextlib
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Callable, Iterator

import anthropic
from anthropic import AnthropicFoundry

from ..config import settings


class LLMResponse:
    """Normalized Claude response: parsed JSON (when requested), raw text and token usage."""

    def __init__(self, content: str, data: Any = None, usage: dict[str, int] | None = None, stop_reason: str = ""):
        self.content = content
        self.data = data
        self.usage = usage or {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        self.stop_reason = stop_reason


class ClaudeClient:
    """
    Claude (Azure AI Foundry) client used by the hybrid reviewer and the standards KB builder.

    Configuration comes only from the .env file / process environment:
    - FOUNDRY_ANTHROPIC_BASE_URL  e.g. https://<resource>.services.ai.azure.com/anthropic
    - FOUNDRY_API_KEY
    - FOUNDRY_MODEL_DEPLOYMENT    e.g. claude-sonnet-4-6
    """

    def __init__(self, model: str, base_url: str, api_key: str, effort: str = "medium", max_tokens: int = settings.LLM_MAX_TOKENS):
        self.model = model
        self.effort = effort
        self.max_tokens = max_tokens
        self.client = AnthropicFoundry(
            api_key=api_key,
            base_url=base_url,
            max_retries=settings.LLM_MAX_RETRIES,
            timeout=settings.LLM_TIMEOUT_SECONDS,
        )
        self.usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        self._usage_lock = threading.Lock()

    # ------------------------------------------------------------------ single call with JSON schema
    def complete_json(
        self,
        system: str,
        user: str,
        schema: dict[str, Any],
        run_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """One Claude call whose final text is guaranteed to match `schema` (structured outputs)."""
        with _trace(run_name, "chain", None, {"system": system[:2000], "user": user[:20000]}, metadata) as span:
            message = self._stream(
                system=system,
                messages=[{"role": "user", "content": user}],
                run_name=run_name,
                metadata=metadata,
                output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
            )
            text = "".join(block.text for block in message.content if block.type == "text").strip()
            usage = self._record_usage(message)
            data = None
            if message.stop_reason == "refusal":
                logging.warning("Claude refused %s: %s", run_name, getattr(message, "stop_details", None))
            elif message.stop_reason == "max_tokens":
                logging.warning("Claude hit max_tokens for %s; response ignored", run_name)
            else:
                data = json.loads(text) if text else None
            _update(span, output=data if data is not None else text[:4000], usage=usage)
            return LLMResponse(text, data, usage, message.stop_reason or "")

    # ------------------------------------------------------------------ agentic tool loop
    def run_tool_loop(
        self,
        system: str,
        user: str,
        tools: list[dict[str, Any]],
        handlers: dict[str, Callable[[dict[str, Any]], Any]],
        run_name: str,
        max_turns: int = 12,
        is_done: Callable[[], bool] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> LLMResponse:
        """
        Manual agent loop: Claude calls the local tools until it stops asking for them
        (or `is_done()` reports that every decision was submitted).
        """
        messages: list[dict[str, Any]] = [{"role": "user", "content": user}]
        total = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        last_text = ""
        stop_reason = ""
        with _trace(run_name, "agent", self.model, {"user": user[:20000]}, metadata) as span:
            for turn in range(max_turns):
                message = self._stream(
                    system=system,
                    messages=messages,
                    run_name=f"{run_name} turn {turn + 1}",
                    metadata=metadata,
                    tools=tools,
                    output_config={"effort": self.effort},
                )
                usage = self._record_usage(message)
                for key in total:
                    total[key] += usage[key]
                stop_reason = message.stop_reason or ""
                last_text = "".join(block.text for block in message.content if block.type == "text")
                # Keep the full content (thinking + tool_use blocks) so the next request is valid.
                messages.append({"role": "assistant", "content": message.content})

                if stop_reason in {"refusal", "max_tokens"}:
                    logging.warning("Agent %s stopped: %s", run_name, stop_reason)
                    break
                if stop_reason != "tool_use":
                    break

                results = []
                for block in message.content:
                    if block.type != "tool_use":
                        continue
                    results.append(self._execute_tool(block, handlers, run_name))
                # All tool results go back in a single user message.
                messages.append({"role": "user", "content": results})
                if is_done and is_done():
                    break
            else:
                logging.warning("Agent %s reached max_turns=%s", run_name, max_turns)
            _update(span, output=last_text[:4000], usage=total)
        return LLMResponse(last_text, None, total, stop_reason)

    @staticmethod
    def _execute_tool(block: Any, handlers: dict[str, Callable[[dict[str, Any]], Any]], run_name: str) -> dict[str, Any]:
        handler = handlers.get(block.name)
        logging.info("%s tool call: %s %s", run_name, block.name, json.dumps(block.input, ensure_ascii=False, default=str)[:200])
        with _trace(f"{run_name} - tool {block.name}", "tool", None, block.input, None) as span:
            if handler is None:
                result, is_error = f"Unknown tool {block.name}", True
            else:
                try:
                    result, is_error = handler(dict(block.input or {})), False
                except Exception as exc:  # tool errors are returned to Claude, not raised
                    result, is_error = f"{type(exc).__name__}: {exc}", True
            text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
            _update(span, output=text[:4000])
            if is_error:
                _update_error(span, RuntimeError(text[:500]))
        return {"type": "tool_result", "tool_use_id": block.id, "content": text[:30000], "is_error": is_error}

    # ------------------------------------------------------------------ internals
    def _stream(
        self,
        system: str,
        messages: list[dict[str, Any]],
        run_name: str = "claude call",
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        # Every API request is its own Langfuse generation (model, input, output, token usage).
        generation_input = {"system": system[:2000], "messages": _trim_messages(messages)}
        with _trace(f"{run_name} - LLM call", "generation", self.model, generation_input, metadata) as span:
            try:
                # Streaming avoids HTTP timeouts on long batches; the stable system prompt is cached.
                with self.client.messages.stream(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                    thinking={"type": "adaptive"},
                    messages=messages,
                    **kwargs,
                ) as stream:
                    message = stream.get_final_message()
            except Exception as exc:
                _update_error(span, exc)
                raise
            _update_generation(span, message)
            return message

    def _record_usage(self, message: Any) -> dict[str, int]:
        usage = getattr(message, "usage", None)
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        input_tokens += int(getattr(usage, "cache_read_input_tokens", 0) or 0)
        input_tokens += int(getattr(usage, "cache_creation_input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        result = {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": input_tokens + output_tokens}
        with self._usage_lock:
            for key, value in result.items():
                self.usage[key] += value
        return result


class LLMModel:
    """Creates the configured Claude client (Azure AI Foundry) for hybrid validation."""

    _langfuse_client: Any = None
    _init_lock = threading.Lock()

    def __init__(self, env_file: str = settings.ENV_FILE, model: str | None = None, effort: str = "medium"):
        self.env_file = env_file
        self.model = model
        self.effort = effort

    def create_client(self) -> ClaudeClient:
        model, base_url, api_key = self._load_model_config()
        self._init_langfuse()
        logging.info("Using Claude deployment %s via Azure AI Foundry", model)
        return ClaudeClient(model=model, base_url=base_url, api_key=api_key, effort=self.effort)

    def _load_model_config(self) -> tuple[str, str, str]:
        root = settings.PROJECT_ROOT
        for path in [Path(self.env_file), Path(".env"), root / ".env"]:
            self._load_dotenv_file(path)

        model = self.model or os.getenv("FOUNDRY_MODEL_DEPLOYMENT", "")
        base_url = os.getenv("FOUNDRY_ANTHROPIC_BASE_URL", "").strip().rstrip("/")
        api_key = os.getenv("FOUNDRY_API_KEY", "")
        if not (model and base_url and api_key):
            raise ValueError(
                "Missing Claude config. Set FOUNDRY_ANTHROPIC_BASE_URL, FOUNDRY_API_KEY and "
                "FOUNDRY_MODEL_DEPLOYMENT in the .env file."
            )
        return model, base_url, api_key

    @staticmethod
    def _init_langfuse() -> None:
        if LLMModel._langfuse_client is not None:
            return
        with LLMModel._init_lock:
            if LLMModel._langfuse_client is not None:
                return
            secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
            public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
            base_url = os.getenv("LANGFUSE_BASE_URL", "") or os.getenv("LANGFUSE_HOST", "")
            if not (secret_key and public_key and base_url):
                logging.warning("Langfuse tracing OFF: LANGFUSE_SECRET_KEY / LANGFUSE_PUBLIC_KEY / LANGFUSE_BASE_URL missing in .env")
                return
            try:
                from langfuse import Langfuse

                client = Langfuse(public_key=public_key, secret_key=secret_key, base_url=base_url)
                if not client.auth_check():
                    logging.warning("Langfuse tracing OFF: authentication failed for %s", base_url)
                    return
                LLMModel._langfuse_client = client
                logging.info("Langfuse tracing ON: %s", base_url)
            except Exception as exc:
                logging.warning("Langfuse tracing OFF: %s", exc)

    @staticmethod
    @contextlib.contextmanager
    def run_trace(name: str, session_id: str = "", metadata: dict[str, Any] | None = None, env_file: str = settings.ENV_FILE) -> Iterator[Any]:
        """One root Langfuse trace per pipeline run; every Claude call made inside nests under it."""
        root = settings.PROJECT_ROOT
        for path in [Path(env_file), Path(".env"), root / ".env"]:
            LLMModel._load_dotenv_file(path)
        LLMModel._init_langfuse()
        client = LLMModel._langfuse_client
        if client is None:
            yield None
            return
        try:
            from langfuse import propagate_attributes

            # Langfuse SDK v4: trace name / session / tags are propagated to every observation in this context
            # (span.update_trace no longer exists). The trace is named after the agent, e.g. "Agent A".
            attributes_cm = propagate_attributes(
                trace_name=settings.AGENT_NAME,
                session_id=session_id or None,
                tags=[settings.AGENT_NAME, settings.TRACE_TAG],
            )
            span_cm = client.start_as_current_observation(
                name=name, as_type="span", metadata={"agent_name": settings.AGENT_NAME, **(metadata or {})}
            )
        except Exception as exc:
            logging.warning("Langfuse run trace not started: %s", exc)
            yield None
            return
        with attributes_cm, span_cm as span:
            yield span

    @staticmethod
    def flush_langfuse() -> None:
        client = LLMModel._langfuse_client
        if client is None:
            return
        try:
            client.flush()
        except Exception:
            pass

    @staticmethod
    def _load_dotenv_file(path: Path) -> None:
        if not path.exists() or not path.is_file():
            return
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value


class _NullSpan:
    def __enter__(self) -> None:
        return None

    def __exit__(self, *exc: Any) -> bool:
        return False


def _trace(name: str, as_type: str, model: str | None, input_payload: Any, metadata: dict[str, Any] | None) -> Any:
    client = LLMModel._langfuse_client
    if client is None:
        return _NullSpan()
    try:
        return client.start_as_current_observation(
            name=f"{settings.AGENT_NAME} - {name}",
            as_type=as_type,
            model=model,
            input=input_payload,
            metadata={"agent_name": settings.AGENT_NAME, **(metadata or {})},
        )
    except Exception:
        return _NullSpan()


def _trim_messages(messages: list[dict[str, Any]], limit: int = 20000) -> list[dict[str, Any]]:
    """JSON-safe, size-limited copy of the conversation for the Langfuse generation input."""
    output = []
    for message in messages[-6:]:
        content = message.get("content")
        if isinstance(content, str):
            text = content
        else:
            parts = []
            for block in content or []:
                block_type = _field(block, "type")
                if block_type == "text":
                    parts.append(str(_field(block, "text") or ""))
                elif block_type == "tool_use":
                    args = json.dumps(_field(block, "input") or {}, ensure_ascii=False, default=str)
                    parts.append(f"[tool_use {_field(block, 'name')}] {args}")
                elif block_type == "tool_result":
                    parts.append(f"[tool_result] {str(_field(block, 'content') or '')[:2000]}")
            text = "\n".join(parts)
        output.append({"role": message.get("role", ""), "content": text[:limit]})
    return output


def _field(block: Any, key: str) -> Any:
    """Read a content-block field from either an SDK object or a plain dict."""
    if isinstance(block, dict):
        return block.get(key)
    return getattr(block, key, None)


def _update_generation(span: Any, message: Any) -> None:
    if span is None:
        return
    try:
        usage = getattr(message, "usage", None)
        usage_details = {
            "input": int(getattr(usage, "input_tokens", 0) or 0),
            "output": int(getattr(usage, "output_tokens", 0) or 0),
            "cache_read_input_tokens": int(getattr(usage, "cache_read_input_tokens", 0) or 0),
            "cache_creation_input_tokens": int(getattr(usage, "cache_creation_input_tokens", 0) or 0),
        }
        text = "".join(block.text for block in message.content if block.type == "text")
        tool_calls = [
            {"name": block.name, "input": block.input} for block in message.content if block.type == "tool_use"
        ]
        span.update(
            output={"text": text[:4000], "tool_calls": tool_calls} if tool_calls else text[:4000],
            usage_details=usage_details,
            metadata={"stop_reason": message.stop_reason or ""},
        )
    except Exception:
        pass


def _update_error(span: Any, exc: Exception) -> None:
    if span is None:
        return
    try:
        span.update(level="ERROR", status_message=f"{type(exc).__name__}: {exc}"[:1000])
    except Exception:
        pass


def _update(span: Any, output: Any = None, usage: dict[str, int] | None = None) -> None:
    if span is None:
        return
    try:
        if usage is not None:
            span.update(output=output, usage_details={"input": usage["input_tokens"], "output": usage["output_tokens"]})
            return
    except Exception:
        pass
    try:
        span.update(output=output)
    except Exception:
        pass


__all__ = ["ClaudeClient", "LLMModel", "LLMResponse", "anthropic"]
