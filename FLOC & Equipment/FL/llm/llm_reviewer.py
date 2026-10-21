"""Hybrid reviewer: sends only the ambiguous rule results to Claude, one column at a time, and merges decisions back."""

from __future__ import annotations

import contextvars
import hashlib
import html
import json
import logging
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from ..config import settings
from ..core.common import normalize_text
from ..validators.master_data_mapper import completion_field_config
from .llm_graph_agent import run_validation_graph
from .llm_model import ClaudeClient, LLMModel


PROMPT_VERSION = "claude-v4"

FIELD_CONFIG: dict[str, dict[str, Any]] = {
    "functional_location": {
        "source_cols": ["Functional Location", "FunctLocDescrip.", "Superior FunctLoc.", "Equipment", "Technical IdentNo.", "Object Description"],
        "suggested_col": "suggest_functional_location",
        "status_col": "__functional_location_status",
        "confidence_col": "functional_location_confidence_score",
        "evidence_col": "functional_location_evidence",
        "result_prefix": "functional_location",
        "target_column": "Functional Location",
    },
    "abc_indicator": {
        "source_cols": ["Functional Location", "FunctLocDescrip.", "ABC Indicator"],
        "suggested_col": "suggest_abc_indicator",
        "status_col": "__abc_indicator_status",
        "confidence_col": "abc_indicator_confidence_score",
        "evidence_col": "abc_indicator_evidence",
        "result_prefix": "abc_indicator",
        "target_column": "ABC Indicator",
    },
    "catalog_profile": {
        "source_cols": ["Catalog Profile", "Object Description", "FunctLocDescrip.", "Material Description"],
        "suggested_col": "suggest_catalog_profile",
        "status_col": "__catalog_profile_status",
        "confidence_col": "catalog_profile_confidence_score",
        "evidence_col": "catalog_profile_evidence",
        "result_prefix": "catalog_profile",
        "target_column": "Catalog Profile",
    },
    "technical_ident_no": {
        "source_cols": ["Equipment", "Functional Location", "Technical IdentNo.", "Object Description"],
        "suggested_col": "suggest_technical_ident_no",
        "status_col": "__technical_ident_no_status",
        "confidence_col": "technical_ident_no_confidence_score",
        "evidence_col": "technical_ident_no_evidence",
        "result_prefix": "technical_ident_no",
        "target_column": "Technical IdentNo.",
    },
    **completion_field_config(),
}

# How each column is settled when the Python rules are NOT certain (certain rule results never reach Claude):
#   "python" = database / rule mapping only, never sent to Claude (e.g. ABC straight from the site ECA table)
#   "llm"    = one Claude call per batch with hierarchy context + standards evidence
#   "agent"  = Claude agent that looks up FL / Equipment / ECA / catalog / standards itself before deciding
FIELD_ROUTE = {
    "functional_location": "agent",           # tag-level mapping needs hierarchy search + naming standard
    "superior_functional_location": "agent",  # nearest real ancestor needs hierarchy search
    "inventory_number": "llm",                # tier decision from parent / sibling context
    "catalog_profile": "llm",                 # description vs catalog class matching
    "manufacturer": "agent",                  # peer equipment comparison
    "model_number": "agent",
    "manufacturer_part_no": "agent",
    "abc_indicator": "python",
    "technical_ident_no": "python",
    "functional_location_description": "python",
    "location": "python",
    "maintenance_plant": "python",
    "main_work_center": "python",
    "maint_planner_group": "python",
    "manufacturer_serial_number": "python",
}


def fields_for_route(route: str, validator: str = "all") -> list[str]:
    """Columns handled by `route`, limited to the --validator selection."""
    if validator == "all":
        allowed = set(FIELD_CONFIG)
    elif validator == "functional_location":
        allowed = {"functional_location", "superior_functional_location"}
    elif validator == "completion":
        allowed = set(completion_field_config())
    else:
        allowed = {validator}
    return [name for name in REVIEW_ORDER if FIELD_ROUTE.get(name) == route and name in allowed]


# Order in which columns are reviewed and share the row budget.
REVIEW_ORDER = [
    "functional_location",
    "inventory_number",
    "superior_functional_location",
    "abc_indicator",
    "technical_ident_no",
    "catalog_profile",
    "functional_location_description",
    "manufacturer",
    "model_number",
    "manufacturer_part_no",
    "location",
    "maintenance_plant",
    "main_work_center",
    "maint_planner_group",
    "manufacturer_serial_number",
]


class LLMReviewer:
    """
    Hybrid review coordinator.

    Python validators run first. This reviewer then sends only the ambiguous rows to Claude, one
    column at a time, together with hierarchy context and retrieved standards evidence.
    """

    mode = "hybrid"

    def __init__(
        self,
        env_file: str = settings.ENV_FILE,
        model: str | None = None,
        cache_dir: str = settings.CACHE_DIR,
        max_rows: int = 300,
        batch_size: int = 20,
        min_confidence: float = 0.85,
        validators: str = "all",
        include_missing_evidence: bool = False,
        review_suggestions: bool = True,
        parallel_fields: int = 2,
        effort: str = "medium",
        skip_confidence: float = 0.95,
        context_builder: Callable[[dict[str, str]], dict[str, Any]] | None = None,
        suggestion_guard: Callable[[str, pd.Series, str], str] | None = None,
        standards_kb_file: str = settings.STANDARDS_KB_FILE,
    ):
        self.env_file = env_file
        self.standards_kb_file = Path(standards_kb_file)
        self.model = model
        self.effort = effort
        self.cache_dir = Path(cache_dir)
        self.max_rows = max_rows
        self.batch_size = batch_size
        self.min_confidence = min_confidence
        self.validators = validators
        self.include_missing_evidence = include_missing_evidence
        self.review_suggestions = review_suggestions
        self.parallel_fields = max(1, parallel_fields)
        self.skip_confidence = skip_confidence
        self.context_builder = context_builder
        self.suggestion_guard = suggestion_guard  # returns a rejection reason, or "" when the suggestion is allowed
        self.evidence_records = self._load_cached_evidence()
        self.decision_cache_path = self.cache_dir / "claude_decision_cache.json"
        self.decision_cache = self._load_decision_cache()
        self.usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        self._cache_lock = threading.Lock()
        self._usage_lock = threading.Lock()
        self.model_name = ""

    def review(self, df: pd.DataFrame) -> pd.DataFrame:
        output = df.copy()
        llm = LLMModel(env_file=self.env_file, model=self.model, effort=self.effort).create_client()
        self.model_name = llm.model
        work_items = self._allocate(output)

        if self.parallel_fields > 1 and len(work_items) > 1:
            with ThreadPoolExecutor(max_workers=min(self.parallel_fields, len(work_items))) as executor:
                # Each worker runs in a copy of the current context so its Langfuse spans nest under the run trace.
                futures = {
                    executor.submit(contextvars.copy_context().run, self._review_field, llm, output, name, field, rows): (name, field)
                    for name, field, rows in work_items
                }
                for future in as_completed(futures):
                    name, field = futures[future]
                    results, _ = future.result()
                    self._apply_results(output, name, field, results)
        else:
            for name, field, rows in work_items:
                results, _ = self._review_field(llm, output, name, field, rows)
                self._apply_results(output, name, field, results)

        output.attrs["llm_usage"] = self.usage.copy()
        return output

    # ------------------------------------------------------------------ row selection
    def _allocate(self, df: pd.DataFrame) -> list[tuple[str, dict[str, Any], list[int]]]:
        candidates = {name: self._select_rows_for_field(df, FIELD_CONFIG[name]) for name in self._selected_validators(df)}
        allocation: dict[str, list[int]] = {name: [] for name in candidates}
        total = sum(len(rows) for rows in candidates.values())
        # max_rows <= 0 means every ambiguous row is reviewed by Claude.
        remaining = total if self.max_rows <= 0 else self.max_rows
        logging.info("LLM review: %s ambiguous rows found, reviewing %s", total, min(total, remaining))
        # Round-robin so every column gets its share of the row budget.
        while remaining > 0 and any(candidates.values()):
            for name in list(candidates):
                if remaining <= 0:
                    break
                if candidates[name]:
                    allocation[name].append(candidates[name].pop(0))
                    remaining -= 1
        work_items = []
        for name, rows in allocation.items():
            if rows:
                logging.info("LLM %s review selected %s rows", name, len(rows))
                work_items.append((name, FIELD_CONFIG[name], sorted(rows)))
            else:
                logging.info("LLM %s review skipped: no ambiguous rows", name)
        return work_items

    def _selected_validators(self, df: pd.DataFrame) -> list[str]:
        if isinstance(self.validators, (list, tuple)):
            requested = list(self.validators)
        elif self.validators == "all":
            requested = REVIEW_ORDER
        elif self.validators == "functional_location":
            requested = ["functional_location", "superior_functional_location"]
        elif self.validators == "completion":
            requested = [name for name in REVIEW_ORDER if name in completion_field_config()]
        else:
            requested = [self.validators]
        return [name for name in requested if name in FIELD_CONFIG and FIELD_CONFIG[name]["status_col"] in df.columns]

    def _select_rows_for_field(self, df: pd.DataFrame, field: dict[str, Any]) -> list[int]:
        status_col = field["status_col"]
        if status_col not in df.columns:
            return []
        review, suggest, missing = [], [], []
        confidence_col = field["confidence_col"]
        for idx, row in df.iterrows():
            status = str(row.get(status_col, ""))
            has_candidate = bool(str(row.get(field["suggested_col"], "")).strip())
            has_evidence = bool(str(row.get(field["evidence_col"], "")).strip())
            confidence = self._to_float(row.get(confidence_col, ""))
            if status in {"Manual Review", "Invalid Format"} and (has_candidate or has_evidence):
                review.append((confidence, idx))
            elif self.review_suggestions and status == "Suggest Change" and has_candidate and confidence < self.skip_confidence:
                suggest.append((confidence, idx))
            elif self.include_missing_evidence and status == "Missing Evidence":
                missing.append((0.0, idx))
        # Manual review first, then the least certain suggestions.
        return [idx for _, idx in sorted(review, reverse=True)] + [idx for _, idx in sorted(suggest)] + [idx for _, idx in missing]

    # ------------------------------------------------------------------ batching
    def _review_field(
        self,
        llm: ClaudeClient,
        df: pd.DataFrame,
        validator_name: str,
        field: dict[str, Any],
        row_indexes: list[int],
    ) -> tuple[list[dict[str, Any]], int]:
        all_results: list[dict[str, Any]] = []
        reviewed = 0
        batch_size = self._batch_size()
        total_batches = (len(row_indexes) + batch_size - 1) // batch_size
        for batch_no, start in enumerate(range(0, len(row_indexes), batch_size), start=1):
            batch_indexes = row_indexes[start : start + batch_size]
            batch = [self._row_payload(df, idx, validator_name, field) for idx in batch_indexes]
            started = time.perf_counter()
            logging.info("LLM %s batch %s/%s started: count=%s", validator_name, batch_no, total_batches, len(batch))
            try:
                results = self._call_llm(llm, validator_name, field, batch)
            except Exception as exc:
                logging.error("LLM %s batch %s/%s failed, deterministic result kept: %s", validator_name, batch_no, total_batches, exc)
                results = []
            all_results.extend(results)
            reviewed += len(batch)
            logging.info(
                "LLM %s batch %s/%s finished in %.1fs: reviewed=%s/%s",
                validator_name, batch_no, total_batches, time.perf_counter() - started, reviewed, len(row_indexes),
            )
        return all_results, reviewed

    def _batch_size(self) -> int:
        return self.batch_size

    def _row_payload(self, df: pd.DataFrame, idx: int, validator_name: str, field: dict[str, Any]) -> dict[str, Any]:
        row = df.loc[idx]
        payload: dict[str, str] = {}
        for col in field["source_cols"] + [field["suggested_col"], field["status_col"], field["confidence_col"], field["evidence_col"]]:
            if col in df.columns:
                value = str(row.get(col, ""))
                if value and value.lower() not in {"nan", "none"}:
                    payload[col.lstrip("_")] = value
        item: dict[str, Any] = {"excel_row": int(idx) + 2, "validator": validator_name, "row": payload}
        if self.context_builder:
            try:
                item["hierarchy_context"] = self.context_builder(payload)
            except Exception as exc:
                logging.debug("Context builder failed for row %s: %s", idx, exc)
        item["retrieved_evidence"] = self._retrieve_evidence(payload, validator_name)
        return item

    def _retrieve_evidence(self, row: dict[str, str], validator_name: str = "", max_items: int = 6) -> list[dict[str, str]]:
        query_text = normalize_text(" ".join(row.values()) + " " + validator_name.replace("_", " "))
        tokens = {token for token in re.findall(r"[A-Z0-9]+", query_text) if len(token) >= 4}
        if not tokens:
            return []
        field_words = set(validator_name.upper().split("_"))
        scored = []
        for record in self.evidence_records:
            evidence_text = normalize_text(
                " ".join(str(record.get(key, "")) for key in ("key", "value", "source_name", "evidence_text", "interpretation"))
            )
            words = set(re.findall(r"[A-Z0-9]+", evidence_text))
            hits = tokens & words
            if hits:
                bonus = 2 if field_words & set(str(record.get("value", "")).upper().split("_")) else 0
                scored.append((len(hits) + bonus, record))
        selected = []
        for _, record in sorted(scored, key=lambda item: item[0], reverse=True)[:max_items]:
            selected.append(
                {
                    "type": str(record.get("value", "")),
                    "source": f"{record.get('source_name', '')} {record.get('source_ref', '')}",
                    "text": str(record.get("evidence_text", ""))[:500],
                    "interpretation": str(record.get("interpretation", ""))[:300],
                }
            )
        return selected

    # ------------------------------------------------------------------ Claude call
    def _call_llm(self, llm: ClaudeClient, validator_name: str, field: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results, uncached_rows = self._split_cached(validator_name, rows)
        if not uncached_rows:
            return results
        response = run_validation_graph(
            llm,
            validator_name,
            uncached_rows,
            self.min_confidence,
            target_column=field.get("target_column", ""),
            prefix=field["result_prefix"],
        )
        self._capture_usage(response)
        data = response.data.get("decisions", []) if isinstance(response.data, dict) else []
        results.extend(self._store_decisions(uncached_rows, data))
        return results

    def _split_cached(self, validator_name: str, rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        results, uncached = [], []
        for row in rows:
            cache_key = self._decision_cache_key(validator_name, row)
            with self._cache_lock:
                cached = self.decision_cache.get(cache_key)
            if cached:
                results.append(cached)
            else:
                row["_cache_key"] = cache_key
                uncached.append(row)
        return results, uncached

    def _store_decisions(self, rows: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_row = {int(row.get("excel_row", 0)): row for row in rows}
        stored = []
        for item in decisions:
            if not isinstance(item, dict):
                continue
            source_row = by_row.get(int(item.get("excel_row", 0) or 0))
            if not source_row:
                continue
            with self._cache_lock:
                self.decision_cache[source_row["_cache_key"]] = item
            stored.append(item)
        for row in rows:
            row.pop("_cache_key", None)
        self._save_decision_cache()
        return stored

    def _capture_usage(self, response: Any) -> None:
        for key, value in (getattr(response, "usage", None) or {}).items():
            if key in self.usage and isinstance(value, int):
                with self._usage_lock:
                    self.usage[key] += value

    # ------------------------------------------------------------------ merge back
    def _apply_results(self, df: pd.DataFrame, validator_name: str, field: dict[str, Any], results: list[dict[str, Any]]) -> None:
        excel_to_idx = {idx + 2: idx for idx in df.index}
        prefix = field["result_prefix"]
        label = "Agent" if self.mode == "agent" else "LLM"
        for result in results:
            idx = excel_to_idx.get(int(result.get("excel_row", 0) or 0))
            if idx is None:
                continue

            status = str(result.get(f"{prefix}_status", "") or "")
            suggested = str(result.get(f"{prefix}_suggested", "") or "").strip()
            evidence = html.unescape(str(result.get(f"{prefix}_evidence", "") or ""))
            source = html.unescape(str(result.get(f"{prefix}_source", "") or ""))
            confidence_value = self._to_float(result.get(f"{prefix}_confidence", ""))
            source_col = f"__{prefix}_llm_source"
            if source_col not in df.columns:
                df[source_col] = ""
            df.at[idx, source_col] = source

            if status == "Suggest Change" and (not suggested or confidence_value < self.min_confidence):
                status = "Manual Review"
                suggested = ""
            if status == "Suggest Change" and (not source.strip() or not evidence.strip()):
                # Every Claude suggestion must be grounded in a named record or standard and give its evidence.
                status = "Manual Review"
                suggested = ""
                evidence = f"{evidence} (no source/evidence given - not accepted)".strip()
            if status == "Suggest Change" and self.suggestion_guard:
                reason = self.suggestion_guard(validator_name, df.loc[idx], suggested)
                if reason:
                    status = "Manual Review"
                    suggested = ""
                    evidence = f"{evidence} (rejected: {reason})".strip()

            if status and field["status_col"] in df.columns:
                df.at[idx, field["status_col"]] = status
            if status == "OK":
                if self._should_keep_deterministic_technical_candidate(df, idx, validator_name, field):
                    df.at[idx, field["status_col"]] = "Suggest Change"
                    continue
                for col in (field["suggested_col"], field["confidence_col"], field["evidence_col"]):
                    if col in df.columns:
                        df.at[idx, col] = ""
                continue
            if status == "Manual Review" and not suggested:
                # Unconfirmed deterministic candidate is withdrawn; the reason stays in the evidence.
                for col in (field["suggested_col"], field["confidence_col"]):
                    if col in df.columns:
                        df.at[idx, col] = ""
            if suggested and field["suggested_col"] in df.columns:
                df.at[idx, field["suggested_col"]] = suggested
            if suggested and field["confidence_col"] in df.columns:
                df.at[idx, field["confidence_col"]] = f"{confidence_value:.3f}"
            if evidence and field["evidence_col"] in df.columns:
                old = str(df.at[idx, field["evidence_col"]] or "")
                df.at[idx, field["evidence_col"]] = f"{old}; {label} {validator_name} review ({self.model_name}): {evidence}".strip("; ")

    def _should_keep_deterministic_technical_candidate(self, df: pd.DataFrame, idx: int, validator_name: str, field: dict[str, Any]) -> bool:
        if validator_name != "technical_ident_no":
            return False
        if field["suggested_col"] not in df.columns or field["evidence_col"] not in df.columns:
            return False
        suggested = str(df.at[idx, field["suggested_col"]] or "").strip()
        evidence = str(df.at[idx, field["evidence_col"]] or "")
        confidence = self._to_float(df.at[idx, field["confidence_col"]]) if field["confidence_col"] in df.columns else 0.0
        return bool(suggested and confidence >= self.min_confidence and "Functional Location" in evidence and "FL final tag" in evidence)

    # ------------------------------------------------------------------ caches
    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _load_cached_evidence(self) -> list[dict[str, Any]]:
        path = self.standards_kb_file
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return [record for record in payload.get("records", []) if isinstance(record, dict)]

    def _load_decision_cache(self) -> dict[str, dict[str, Any]]:
        if not self.decision_cache_path.exists():
            return {}
        try:
            data = json.loads(self.decision_cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}

    def _save_decision_cache(self) -> None:
        self.decision_cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self._cache_lock:
            text = json.dumps(self.decision_cache, indent=2, ensure_ascii=False)
        self.decision_cache_path.write_text(text, encoding="utf-8")

    def _decision_cache_key(self, validator_name: str, row: dict[str, Any]) -> str:
        payload = json.dumps(
            {
                "version": PROMPT_VERSION,
                "mode": self.mode,
                "model": self.model_name,
                "validator_name": validator_name,
                "row": row.get("row", {}),
                "context": row.get("hierarchy_context", {}),
            },
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        )
        return hashlib.sha1(payload.encode()).hexdigest()
