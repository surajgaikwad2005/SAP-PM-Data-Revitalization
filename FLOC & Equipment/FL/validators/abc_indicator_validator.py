"""ABC Indicator validation against the site ECA table (settings.ECA_TABLE_FQN), exact Functional Location only."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from ..config import settings
from ..core.common import (
    EvidenceRecord,
    ValidationResult,
    find_column,
    insert_after,
    normalize_abc,
    normalize_floc,
    normalize_text,
)
from ..data.database_evidence import load_reference_table


FLOC_ALIASES = ["Functional Location", "FunctLoc", "FLOC"]
ABC_ALIASES = ["ABC Indicator", "ABC", "Criticality"]
EQUIPMENT_ALIASES = ["Equipment", "Equipment Number"]


class ABCIndicatorValidator:
    """
    Validates ABC Indicator using ECA report evidence.

    Required minimum:
    - Functional Location
    - ABC Indicator
    """

    def __init__(
        self,
        df: pd.DataFrame,
        eca_dir: str = settings.ECA_DIR,
        cache_dir: str = settings.CACHE_DIR,
        rebuild_cache: bool = False,
        max_pdf_pages: int = 0,
        min_suggest_confidence: float = 0.85,
        min_review_confidence: float = 0.65,
        evidence_db: str = "",
        use_database: bool = True,
        index: Any = None,
    ):
        self.df = df
        self.index = index
        self.floc_col = find_column(df, FLOC_ALIASES)
        self.abc_col = find_column(df, ABC_ALIASES)
        self.equipment_col = find_column(df, EQUIPMENT_ALIASES)
        self.is_equipment_sheet = self.equipment_col is not None
        self.min_suggest_confidence = min_suggest_confidence
        self.min_review_confidence = min_review_confidence
        self.evidence_index = (
            self._load_eca_index(cache_dir, rebuild_cache, use_database)
            if self.floc_col and self.abc_col
            else {}
        )

    def validate_abc_indicator(self, row: pd.Series) -> ValidationResult:
        if not self.floc_col or not self.abc_col:
            return ValidationResult("", "Skipped", "", "ABC validation needs Functional Location and ABC Indicator")

        current = normalize_abc(row.get(self.abc_col, ""))
        floc = normalize_floc(row.get(self.floc_col, ""))
        records = self.evidence_index.get(floc, [])
        values = sorted({record.value for record in records})
        if len(values) > 1:
            listed = " | ".join(self._record_text(record) for record in records)
            return ValidationResult("", "Manual Review", "", f"Conflicting ECA criticality for exact FLOC {floc}: {listed}")
        suggested, confidence, evidence = self._best_abc_match(floc)
        if not suggested:
            suggested, confidence, evidence = self._cross_sheet_abc(floc)
            if suggested and current and suggested != current:
                return ValidationResult("", "Manual Review", "", f"{evidence} is {suggested}, sheet has {current}")
        if not suggested:
            # Criticality is never inherited from a parent / boundary FLOC.
            return ValidationResult("", "Missing Evidence", "", f"No {settings.ECA_TABLE_FQN} record for exact FLOC {floc}")
        if suggested != current and confidence >= self.min_suggest_confidence:
            return ValidationResult(suggested, "Suggest Change", f"{confidence:.3f}", evidence)
        if suggested != current and confidence >= self.min_review_confidence:
            return ValidationResult("", "Manual Review", "", evidence)
        return ValidationResult("", "OK", "", "")

    def add_validation_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        output = df.copy()
        results = [self.validate_abc_indicator(row) for _, row in df.iterrows()]
        new_cols = pd.DataFrame(
            {
                "suggest_abc_indicator": [r.suggested_value for r in results],
                "abc_indicator_confidence_score": [r.confidence for r in results],
                "abc_indicator_evidence": [r.evidence if r.suggested_value or r.status == "Manual Review" else "" for r in results],
                "__abc_indicator_status": [r.status for r in results],
            }
        )
        return self._insert_after(output, self.abc_col, new_cols)

    def _best_abc_match(self, floc: str) -> tuple[str, float, str]:
        """Exact Functional Location match in the site ECA table only - no base / parent inheritance."""
        clean_floc = normalize_floc(floc)
        records = self.evidence_index.get(clean_floc, []) if clean_floc else []
        if not records:
            return "", 0.0, ""
        record = records[0]
        confidence = min(record.confidence_base, 0.98 if self.is_equipment_sheet else 0.95)
        return record.value, confidence, f"{settings.ECA_TABLE_FQN} exact FLOC match; {self._record_text(record)}"

    @staticmethod
    def _record_text(record: EvidenceRecord) -> str:
        return f"{record.source_name} {record.source_ref}: {record.evidence_text} => ABC {record.value}"

    def _cross_sheet_abc(self, floc: str) -> tuple[str, float, str]:
        """Fallback when ECA has no record: ABC of the linked FL (equipment rows) or installed equipment (FL rows)."""
        if self.index is None or not floc:
            return "", 0.0, ""
        if self.is_equipment_sheet:
            value = normalize_abc(self.index.fl_records.get(floc, {}).get("ABC Indicator", ""))
            if value:
                return value, 0.88, f"No ECA record; FL sheet ABC Indicator of Functional Location {floc}"
            return "", 0.0, ""
        installed = self.index.equipment_by_floc.get(floc, [])
        values = {normalize_abc(self.index.equipment_records[eq].get("ABC Indicator", "")) for eq in installed} - {""}
        if len(values) == 1:
            return values.pop(), 0.88, f"No ECA record; Equipment sheet ABC Indicator of installed equipment {', '.join(installed[:3])}"
        return "", 0.0, ""

    @staticmethod
    def _insert_after(df: pd.DataFrame, source_col: str | None, new_cols: pd.DataFrame) -> pd.DataFrame:
        return insert_after(df, source_col, new_cols)

    @staticmethod
    def _load_eca_index(
        cache_dir: str,
        rebuild_cache: bool,
        use_database: bool = True,
    ) -> dict[str, list[EvidenceRecord]]:
        records = ABCIndicatorValidator._load_postgres_eca_records(cache_dir, rebuild_cache, use_database)
        index: dict[str, list[EvidenceRecord]] = {}
        for record in records:
            index.setdefault(record.key, []).append(record)
        return index

    @staticmethod
    def _load_postgres_eca_records(cache_dir: str, rebuild_cache: bool, use_database: bool) -> list[EvidenceRecord]:
        if not use_database:
            logging.info("ABC validation skipped %s because database usage is disabled", settings.ECA_TABLE_FQN)
            return []
        table = load_reference_table(
            settings.ECA_TABLE,
            cache_dir,
            use_database,
            rebuild_cache,
            allow_local_fallback=False,
        )
        records: list[EvidenceRecord] = []
        for _, row in table.iterrows():
            floc = normalize_floc(row.get("functional_location", ""))
            abc_value = normalize_abc(row.get("criticality_norm", "")) or normalize_abc(row.get("criticality", ""))
            if not floc or not abc_value:
                continue
            source_name = normalize_text(row.get("source_file", "")) or settings.ECA_TABLE_FQN
            source_ref = f"page {normalize_text(row.get('page_no', ''))}".strip()
            desc = normalize_text(row.get("functional_location_description", ""))
            evidence_text = (
                f"FLOC={floc}; Criticality={normalize_text(row.get('criticality', ''))}; "
                f"Criticality Norm={normalize_text(row.get('criticality_norm', ''))}; Description={desc}"
            )
            records.append(
                EvidenceRecord(
                    settings.ECA_TABLE_FQN,
                    floc,
                    abc_value,
                    source_name,
                    source_ref,
                    evidence_text[:700],
                    0.98,
                )
            )
        logging.info("Loaded %s ABC records from %s", len(records), settings.ECA_TABLE_FQN)
        return ABCIndicatorValidator._deduplicate(records)

    @staticmethod
    def _deduplicate(records: list[EvidenceRecord]) -> list[EvidenceRecord]:
        dedup = {}
        for record in records:
            dedup[(record.evidence_type, record.key, record.value, record.source_name, record.source_ref)] = record
        return list(dedup.values())
