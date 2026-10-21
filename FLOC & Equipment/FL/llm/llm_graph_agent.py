"""LangGraph pipelines: prompt -> single structured Claude call (hybrid review and standards KB)."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from .llm_model import ClaudeClient, LLMResponse


class ValidationGraphState(TypedDict):
    validator_name: str
    target_column: str
    prefix: str
    rows: list[dict[str, Any]]
    min_confidence: float
    system: str
    prompt: str
    response: Any


class StandardsGraphState(TypedDict):
    chunk: dict[str, Any]
    system: str
    prompt: str
    response: Any


def run_validation_graph(
    llm: ClaudeClient,
    validator_name: str,
    rows: list[dict[str, Any]],
    min_confidence: float,
    target_column: str = "",
    prefix: str = "",
) -> LLMResponse:
    """Hybrid mode: build column prompt -> one Claude call with a strict JSON schema."""
    from .prompts import build_prompt, decision_schema

    def build_prompt_node(state: ValidationGraphState) -> dict[str, Any]:
        system, prompt = build_prompt(
            state["validator_name"], state["rows"], state["min_confidence"], state["target_column"], state["prefix"]
        )
        return {"system": system, "prompt": prompt}

    def call_model_node(state: ValidationGraphState) -> dict[str, Any]:
        return {
            "response": llm.complete_json(
                state["system"],
                state["prompt"],
                decision_schema(state["prefix"]),
                run_name=f"{state['validator_name']} validation",
                metadata={"target_column": state["validator_name"], "rows_count": len(state["rows"])},
            )
        }

    graph = StateGraph(ValidationGraphState)
    graph.add_node("build_column_prompt", build_prompt_node)
    graph.add_node("call_llm", call_model_node)
    graph.add_edge(START, "build_column_prompt")
    graph.add_edge("build_column_prompt", "call_llm")
    graph.add_edge("call_llm", END)
    result = graph.compile().invoke(
        {
            "validator_name": validator_name,
            "target_column": target_column,
            "prefix": prefix or validator_name,
            "rows": rows,
            "min_confidence": min_confidence,
            "system": "",
            "prompt": "",
            "response": None,
        }
    )
    return result["response"]


def run_standards_kb_graph(llm: ClaudeClient, chunk: dict[str, Any]) -> LLMResponse:
    from .prompts import STANDARDS_KB_SCHEMA, build_standards_kb_prompt

    def build_prompt_node(state: StandardsGraphState) -> dict[str, Any]:
        system, prompt = build_standards_kb_prompt(state["chunk"])
        return {"system": system, "prompt": prompt}

    def call_model_node(state: StandardsGraphState) -> dict[str, Any]:
        return {
            "response": llm.complete_json(
                state["system"],
                state["prompt"],
                STANDARDS_KB_SCHEMA,
                run_name="standards KB",
                metadata={"document_name": state["chunk"].get("document_name", ""), "source_ref": state["chunk"].get("source_ref", "")},
            )
        }

    graph = StateGraph(StandardsGraphState)
    graph.add_node("build_standards_prompt", build_prompt_node)
    graph.add_node("call_llm", call_model_node)
    graph.add_edge(START, "build_standards_prompt")
    graph.add_edge("build_standards_prompt", "call_llm")
    graph.add_edge("call_llm", END)
    result = graph.compile().invoke({"chunk": chunk, "system": "", "prompt": "", "response": None})
    return result["response"]
