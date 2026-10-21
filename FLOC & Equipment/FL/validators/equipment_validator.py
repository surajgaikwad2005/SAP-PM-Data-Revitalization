"""Technical IdentNo. validation for the Equipment sheet."""

from __future__ import annotations

import pandas as pd

from ..config import settings
from ..core.common import ValidationResult, find_column, insert_after, normalize_floc, normalize_text, split_floc, tag_suffix
from ..data.database_evidence import load_asset_master_cache


EQUIPMENT_ALIASES = ["Equipment", "Equipment Number"]
TECHNICAL_ID_ALIASES = ["Technical IdentNo.", "Technical IdentNo", "Technical Identification"]
FLOC_ALIASES = ["Functional Location", "FunctLoc", "FLOC"]
DESCRIPTION_ALIASES = ["Object Description", "Equipment Description", "Description"]


class EquipmentFieldValidator:
    def __init__(
        self,
        df: pd.DataFrame,
        asset_cache_file: str = settings.ASSET_CACHE_FILE,
        force_asset_refresh: bool = False,
        min_suggest_confidence: float = 0.85,
        min_review_confidence: float = 0.65,
    ):
        self.df = df
        self.equipment_col = find_column(df, EQUIPMENT_ALIASES)
        self.technical_id_col = find_column(df, TECHNICAL_ID_ALIASES)
        self.floc_col = find_column(df, FLOC_ALIASES)
        self.description_col = find_column(df, DESCRIPTION_ALIASES)
        self.min_suggest_confidence = min_suggest_confidence
        self.min_review_confidence = min_review_confidence
        cache = load_asset_master_cache(asset_cache_file, force_asset_refresh) if self.equipment_col else {}
        self.equipment_lookup = cache.get("equipment_lookup", {}) if isinstance(cache, dict) else {}

    def add_validation_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        output = df.copy()
        if not self.equipment_col or not self.technical_id_col:
            return output
        results = [self.validate_technical_ident_no(row) for _, row in df.iterrows()]
        new_cols = pd.DataFrame(
            {
                "suggest_technical_ident_no": [r.suggested_value for r in results],
                "technical_ident_no_confidence_score": [r.confidence for r in results],
                "technical_ident_no_evidence": [r.evidence if r.status != "OK" else "" for r in results],
                "__technical_ident_no_status": [r.status for r in results],
            }
        )
        return self._insert_after(output, self.technical_id_col, new_cols)

    def validate_technical_ident_no(self, row: pd.Series) -> ValidationResult:
        equipment = normalize_text(row.get(self.equipment_col, ""))
        current = normalize_text(row.get(self.technical_id_col, ""))
        if not equipment:
            return ValidationResult("", "Skipped", "", "Equipment number is blank")

        if current:
            floc_suggestion = self._suggest_from_floc_tag(row, current)
            if floc_suggestion:
                suggested, evidence = floc_suggestion
                return ValidationResult(suggested, "Suggest Change", "0.930", evidence)
            return ValidationResult("", "OK", "", "")

        master = self.equipment_lookup.get(equipment)
        if master:
            suggested = normalize_text(master.get("Technical IdentNo.", ""))
            if suggested:
                return ValidationResult(
                    suggested,
                    "Suggest Change",
                    "0.980",
                    f"Exact equipment match in asset master: Equipment={equipment}",
                )
        return ValidationResult("", "Missing Evidence", "", "Technical IdentNo. is blank and no reliable evidence was found")

    def _suggest_from_floc_tag(self, row: pd.Series, current: str) -> tuple[str, str] | None:
        floc = normalize_floc(row.get(self.floc_col, "")) if self.floc_col else ""
        floc_parts = split_floc(floc)
        current_parts = [part for part in current.split("-") if part]
        if not floc_parts or len(current_parts) < 2:
            return None

        floc_prefix = floc_parts[0]
        floc_tag = self._compact_tag(tag_suffix(floc))
        current_prefix = current_parts[0]
        current_body = "-".join(current_parts[1:])
        current_body_compact = self._compact_tag(current_body)
        if not floc_prefix or not floc_tag or not current_body_compact:
            return None

        prefix_wrong = current_prefix != floc_prefix
        body_matches = current_body_compact == floc_tag
        body_truncated = (
            floc_tag.startswith(current_body_compact)
            and len(floc_tag) > len(current_body_compact)
            and len(current_body_compact) >= 4
            and len(floc_tag) - len(current_body_compact) <= 3
        )

        if not prefix_wrong and not body_truncated:
            return None

        if body_matches:
            suggested_body = current_body
            reason = "Technical IdentNo. body matches Functional Location final tag after compact comparison"
        elif body_truncated:
            suggested_body = self._expand_body_preserving_style(current_parts[1:], floc_tag)
            reason = "Technical IdentNo. body is a truncated prefix of Functional Location final tag"
        else:
            return None

        suggested = "-".join([floc_prefix, suggested_body])
        if suggested == current:
            return None
        evidence = (
            f"{reason}; Functional Location={floc}; FL prefix={floc_prefix}; "
            f"FL final tag={floc_tag}; current Technical IdentNo.={current}"
        )
        return suggested, evidence

    @staticmethod
    def _compact_tag(value: str) -> str:
        return "".join(char for char in normalize_text(value) if char.isalnum())

    @staticmethod
    def _expand_body_preserving_style(body_parts: list[str], floc_tag: str) -> str:
        if len(body_parts) <= 1:
            return floc_tag
        first = "".join(char for char in normalize_text(body_parts[0]) if char.isalnum())
        if first and floc_tag.startswith(first):
            suffix = floc_tag[len(first):]
            if suffix:
                return "-".join([body_parts[0], suffix])
        return floc_tag

    @staticmethod
    def _insert_after(df: pd.DataFrame, source_col: str | None, new_cols: pd.DataFrame) -> pd.DataFrame:
        return insert_after(df, source_col, new_cols)
