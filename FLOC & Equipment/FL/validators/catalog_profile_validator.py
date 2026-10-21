"""Catalog Profile validation against the catalog standards workbook and public.catalog_profile."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ..config import settings
from ..core.common import (
    EvidenceRecord,
    ValidationResult,
    find_column,
    insert_after,
    load_cached_records,
    normalize_text,
    save_cached_records,
)
from ..data.database_evidence import load_asset_master_cache, load_reference_table


CATALOG_ALIASES = ["Catalog Profile", "CatalogProfile", "Catalogue Profile", "Catelog Profile"]
DESCRIPTION_ALIASES = ["Object Description", "Equipment Description", "FunctLocDescrip.", "Description", "Material Description"]
EQUIPMENT_ALIASES = ["Equipment", "Equipment Number"]


class CatalogProfileValidator:
    """
    Validates Catalog Profile from extracted standards Excel.

    Required minimum:
    - Catalog Profile

    Stronger validation when available:
    - Description/Object Description
    """

    def __init__(
        self,
        df: pd.DataFrame,
        standards_dir: str = settings.STANDARDS_DIR,
        cache_dir: str = settings.CACHE_DIR,
        rebuild_cache: bool = False,
        min_suggest_confidence: float = 0.85,
        min_review_confidence: float = 0.65,
        asset_cache_file: str = settings.ASSET_CACHE_FILE,
        force_asset_refresh: bool = False,
        use_database: bool = True,
    ):
        self.df = df
        self.catalog_col = find_column(df, CATALOG_ALIASES)
        self.description_col = find_column(df, DESCRIPTION_ALIASES)
        self.equipment_col = find_column(df, EQUIPMENT_ALIASES)
        self.min_suggest_confidence = min_suggest_confidence
        self.min_review_confidence = min_review_confidence
        self.asset_cache = load_asset_master_cache(asset_cache_file, force_asset_refresh) if self.catalog_col else {}
        self.equipment_lookup = self.asset_cache.get("equipment_lookup", {}) if isinstance(self.asset_cache, dict) else {}
        self.catalog_records = self._load_catalog_records(standards_dir, cache_dir, rebuild_cache, use_database) if self.catalog_col else []
        self.catalog_index = self._catalog_index(self.catalog_records)

    def validate_catalog_profile(self, row: pd.Series) -> ValidationResult:
        if not self.catalog_col:
            return ValidationResult("", "Skipped", "", "Catalog Profile column not found")

        current = normalize_text(row.get(self.catalog_col, ""))
        description = normalize_text(row.get(self.description_col, "")) if self.description_col else ""

        if current:
            matched_record = self._match_catalog_class(current)
            if matched_record:
                if description:
                    desc_tokens = {token for token in description.split() if len(token) >= 4}
                    class_tokens = {token for token in normalize_text(matched_record.value).split() if len(token) >= 4}
                    if desc_tokens and class_tokens and not desc_tokens.intersection(class_tokens):
                        return ValidationResult(
                            "",
                            "Manual Review",
                            "",
                            f"Catalog Profile {current} matches class '{matched_record.value}' but description does not confirm: {description}",
                        )
                return ValidationResult("", "OK", "", "")

            suggested, confidence, evidence = self._suggest_from_description(description)
            if suggested and confidence >= self.min_suggest_confidence:
                if suggested != current:
                    return ValidationResult(suggested, "Suggest Change", f"{confidence:.3f}", evidence)
                return ValidationResult("", "OK", "", "")

            if suggested and confidence >= self.min_review_confidence:
                return ValidationResult("", "Manual Review", "", evidence)
            return ValidationResult("", "Missing Evidence", "", f"Catalog Profile not found in public.catalog_profile: {current}")

        equipment_suggestion = self._suggest_from_equipment(row)
        if equipment_suggestion:
            suggested, confidence, evidence = equipment_suggestion
            if suggested in self.catalog_index:
                return ValidationResult(suggested, "Suggest Change", f"{confidence:.3f}", evidence)

        suggested, confidence, evidence = self._suggest_from_description(description)
        if suggested and confidence >= self.min_suggest_confidence:
            return ValidationResult(suggested, "Suggest Change", f"{confidence:.3f}", evidence)
        return ValidationResult("", "Manual Review", "", "Catalog Profile is blank")

    def _suggest_from_equipment(self, row: pd.Series) -> tuple[str, float, str] | None:
        equipment = normalize_text(row.get(self.equipment_col, "")) if self.equipment_col else ""
        if not equipment:
            return None
        master = self.equipment_lookup.get(equipment)
        if not master:
            return None
        profile = normalize_text(master.get("Catalog Profile", ""))
        if not profile:
            return None
        return profile, 0.98, f"Exact equipment match in asset master cache: Equipment={equipment}"

    def add_validation_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        output = df.copy()
        results = [self.validate_catalog_profile(row) for _, row in df.iterrows()]
        new_cols = pd.DataFrame(
            {
                "suggest_catalog_profile": [r.suggested_value for r in results],
                "catalog_profile_confidence_score": [r.confidence for r in results],
                "catalog_profile_evidence": [r.evidence if r.suggested_value else "" for r in results],
                "__catalog_profile_status": [r.status for r in results],
            }
        )
        return self._insert_after(output, self.catalog_col, new_cols)

    def _suggest_from_description(self, description: str) -> tuple[str, float, str]:
        if not description:
            return "", 0.0, ""
        desc_tokens = {token for token in description.split() if len(token) >= 4}
        if not desc_tokens:
            return "", 0.0, ""

        candidates = []
        for record in self.catalog_records:
            profile = record.key
            text = normalize_text(f"{record.value} {record.evidence_text}")
            hits = desc_tokens.intersection({token for token in text.split() if len(token) >= 4})
            if hits:
                class_hits = desc_tokens.intersection({token for token in normalize_text(record.value).split() if len(token) >= 4})
                score = min(0.92, 0.55 + 0.08 * len(hits) + 0.08 * len(class_hits))
                candidates.append((score, profile, record, hits))
        if not candidates:
            return "", 0.0, ""

        score, profile, record, hits = sorted(candidates, key=lambda item: item[0], reverse=True)[0]
        evidence = f"description token match {sorted(hits)[:6]}; {record.source_name} {record.source_ref}: {record.evidence_text}"
        return profile, score, evidence

    def _match_catalog_class(self, current: str) -> EvidenceRecord | None:
        """Look up the reference class for `current` without ever stripping
        a leading numeric prefix (e.g. "1MSV" stays "1MSV"); the digit-less
        suffix ("MSV") is only used to find the matching class for validation."""
        if current in self.catalog_index:
            return self.catalog_index[current]
        compact = "".join(char for char in current if char.isalnum())
        if compact in self.catalog_index:
            return self.catalog_index[compact]
        class_part = compact.lstrip("0123456789")
        if class_part and class_part in self.catalog_index:
            return self.catalog_index[class_part]
        return None

    @staticmethod
    def _insert_after(df: pd.DataFrame, source_col: str | None, new_cols: pd.DataFrame) -> pd.DataFrame:
        return insert_after(df, source_col, new_cols)

    @staticmethod
    def _load_catalog_records(standards_dir: str, cache_dir: str, rebuild_cache: bool, use_database: bool) -> list[EvidenceRecord]:
        folder = Path(standards_dir)
        files = sorted(path for path in folder.rglob("*.xlsx") if "catalog" in path.name.lower() or "catelog" in path.name.lower()) if folder.exists() else []
        cache_path = Path(cache_dir) / "catalog_profile_standards.json"
        cached = load_cached_records(cache_path, files, rebuild_cache)
        if cached is None:
            records = CatalogProfileValidator._extract_catalog_records(files)
            save_cached_records(cache_path, files, records)
            logging.info("Built %s Catalog Profile standard records", len(records))
        else:
            records = cached
            logging.info("Loaded %s Catalog Profile standard records from cache", len(records))

        records = CatalogProfileValidator._extract_database_catalog_records(cache_dir, rebuild_cache, use_database) + records
        return records

    @staticmethod
    def _catalog_index(records: list[EvidenceRecord]) -> dict[str, EvidenceRecord]:
        index: dict[str, EvidenceRecord] = {}
        for record in records:
            if record.key and record.key not in index:
                index[record.key] = record
        return index

    @staticmethod
    def _extract_catalog_records(files: list[Path]) -> list[EvidenceRecord]:
        records: list[EvidenceRecord] = []
        for path in files:
            workbook = pd.ExcelFile(path)
            for sheet_name in workbook.sheet_names:
                sheet = pd.read_excel(path, sheet_name=sheet_name, dtype=str).fillna("")
                class_col = find_column(sheet, ["Class", "Catalog Profile", "CatalogProfile"])
                desc_col = find_column(sheet, ["Class_Description", "Class Description", "Description"])
                symptom_col = find_column(sheet, ["Symptom_Code", "Symptom Code"])
                page_col = find_column(sheet, ["Source_Page", "Source Page", "Page"])
                if not class_col:
                    continue
                for _, row in sheet.iterrows():
                    profile = normalize_text(row.get(class_col, ""))
                    if not profile:
                        continue
                    desc = normalize_text(row.get(desc_col, "")) if desc_col else ""
                    symptom = normalize_text(row.get(symptom_col, "")) if symptom_col else ""
                    page = normalize_text(row.get(page_col, "")) if page_col else ""
                    records.append(
                        EvidenceRecord(
                            "catalog_profile",
                            profile,
                            desc,
                            path.name,
                            f"sheet {sheet_name} page {page}".strip(),
                            f"Class={profile}; Description={desc}; Symptom={symptom}",
                            0.92,
                        )
                    )
        dedup = {}
        for record in records:
            dedup[(record.evidence_type, record.key, record.source_name, record.source_ref)] = record
        return list(dedup.values())

    @staticmethod
    def _extract_database_catalog_records(cache_dir: str, rebuild_cache: bool, use_database: bool) -> list[EvidenceRecord]:
        table = load_reference_table("catalog_profile", cache_dir, use_database, rebuild_cache)
        records: list[EvidenceRecord] = []
        for _, row in table.iterrows():
            profile = normalize_text(row.get("class", ""))
            if not profile:
                continue
            class_description = normalize_text(row.get("class_description", ""))
            symptom_description = normalize_text(row.get("symptom_description", ""))
            symptom_code = normalize_text(row.get("symptom_code", ""))
            source_page = normalize_text(row.get("source_page", ""))
            records.append(
                EvidenceRecord(
                    "catalog_profile",
                    profile,
                    class_description,
                    "public.catalog_profile",
                    f"page {source_page}".strip(),
                    (
                        f"Class={profile}; Class Description={class_description}; "
                        f"Symptom={symptom_code} {symptom_description}"
                    ),
                    0.96,
                )
            )
        dedup = {}
        for record in records:
            dedup[(record.evidence_type, record.key, record.source_name, record.source_ref, record.evidence_text)] = record
        return list(dedup.values())
