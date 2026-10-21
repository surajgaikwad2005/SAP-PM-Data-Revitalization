"""Agent reviewer: unclear rows are investigated by a Claude tool-use agent before a decision is submitted."""

from __future__ import annotations

import copy
import logging
from typing import Any

from ..core.hierarchy_rules import AssetHierarchyIndex
from .agent_tools import AgentToolbox
from .llm_model import ClaudeClient
from .llm_reviewer import LLMReviewer
from .prompts import build_agent_task


class AgentReviewer(LLMReviewer):
    """
    Agent review: same row selection and merge rules as the hybrid reviewer, but each batch is investigated
    by a Claude tool-use agent that queries the FL/Equipment master, ECA report, catalog profiles, process
    codes and standards KB before submitting a decision per row.
    """

    mode = "agent"

    def __init__(
        self,
        index: AssetHierarchyIndex,
        agent_batch_size: int = 5,
        max_agent_turns: int = 14,
        use_database: bool = True,
        **kwargs: Any,
    ):
        super().__init__(**kwargs)
        self.agent_batch_size = max(1, agent_batch_size)
        self.max_agent_turns = max_agent_turns
        self.toolbox = AgentToolbox(
            index,
            cache_dir=str(self.cache_dir),
            use_database=use_database,
            standards_kb_file=str(self.standards_kb_file),
        )
        # Load reference data once; each batch works on a shallow copy with its own decisions.
        self.toolbox._eca_index()
        self.toolbox._catalog_table()
        self.toolbox._process_table()
        self.toolbox._standards_records()

    def _batch_size(self) -> int:
        return self.agent_batch_size

    def _call_llm(self, llm: ClaudeClient, validator_name: str, field: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results, uncached_rows = self._split_cached(validator_name, rows)
        if not uncached_rows:
            return results

        toolbox = copy.copy(self.toolbox)
        toolbox.decisions = {}
        prefix = field["result_prefix"]
        tools = toolbox.definitions(prefix)
        expected_rows = {int(row["excel_row"]) for row in uncached_rows}
        system, user = build_agent_task(validator_name, field.get("target_column", ""), uncached_rows, self.min_confidence)

        response = llm.run_tool_loop(
            system,
            user,
            tools,
            toolbox.handlers(),
            run_name=f"{validator_name} agent",
            max_turns=self.max_agent_turns,
            is_done=lambda: expected_rows.issubset(toolbox.decisions),
            metadata={"target_column": validator_name, "rows_count": len(uncached_rows)},
        )
        self._capture_usage(response)
        missing = expected_rows - set(toolbox.decisions)
        if missing:
            logging.warning("Agent %s did not submit rows %s; deterministic result kept", validator_name, sorted(missing))
        results.extend(self._store_decisions(uncached_rows, list(toolbox.decisions.values())))
        return results
