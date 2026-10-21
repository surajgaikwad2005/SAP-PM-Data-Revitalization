"""Cross-sheet completion between the Functional Location sheet and the Equipment sheet."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

from ..config import settings
from ..core.common import ValidationResult, find_column, insert_after, normalize_floc
from ..core.hierarchy_rules import (
    TAG_LEVEL,
    AssetHierarchyIndex,
    clean_value,
    level_rank,
    normalize_inventory,
)


FLOC_ALIASES = ["Functional Location", "FunctLoc", "FLOC"]
EQUIPMENT_ALIASES = ["Equipment", "Equipment Number"]
TECHNICAL_ID_ALIASES = ["Technical IdentNo.", "Technical IdentNo", "Technical Identification"]
OBJECT_DESCRIPTION_ALIASES = ["Object Description", "Equipment Description"]


@dataclass(frozen=True)
class CompletionField:
    key: str                 # output prefix, e.g. inventory_number
    aliases: tuple[str, ...]  # input column aliases
    master_field: str         # column name in the asset cache records
    datasets: tuple[str, ...]  # "fl", "equipment"


# Fields completed across the Functional Location and Equipment sheets.
COMPLETION_FIELDS = [
    CompletionField("inventory_number", ("Inventory Number", "Inventory"), "Inventory Number", ("fl", "equipment")),
    CompletionField("superior_functional_location", ("Superior FunctLoc.", "Superior Functional Location"), "Superior FunctLoc.", ("fl",)),
    CompletionField("functional_location_description", ("FunctLocDescrip.", "Functional Location Description"), "FunctLocDescrip.", ("fl", "equipment")),
    CompletionField("location", ("Location",), "Location", ("fl", "equipment")),
    CompletionField("maintenance_plant", ("Maintenance Plant", "Maint. Plant"), "Maintenance Plant", ("fl", "equipment")),
    CompletionField("main_work_center", ("Main Work Center", "Main WorkCtr"), "Main Work Center", ("fl", "equipment")),
    CompletionField("maint_planner_group", ("Maint. Planner Group", "Planner Group"), "Maint. Planner Group", ("fl", "equipment")),
    CompletionField("manufacturer", ("Manufacturer",), "Manufacturer", ("fl", "equipment")),
    CompletionField("model_number", ("Model number", "Model Number"), "Model number", ("fl", "equipment")),
    CompletionField("manufacturer_part_no", ("ManufactPartNo.", "Manufacturer Part Number"), "ManufactPartNo.", ("fl", "equipment")),
    CompletionField("manufacturer_serial_number", ("Manuf. Serial Number", "Serial Number"), "Manuf. Serial Number", ("fl", "equipment")),
]

# Columns that are already correct in each sheet: no suggest_/confidence/source columns are produced for them.
# They are still read as *sources* when completing the other sheet.
SKIP_COLUMNS = {
    "fl": {
        "FunctLocDescrip.", "User Status", "Location", "System status", "Created On",
        "Main Work Center", "Superior FunctLoc.", "Changed On",
    },
    "equipment": {
        "Equipment", "Object Description", "FunctLocDescrip.", "Location", "System status", "User Status",
        "Maint. Planner Group", "Main Work Center", "Created By", "Maintenance Plant", "Manuf. Serial Number",
        "ManufDrawingNumber", "ManufactPartNo.", "Material", "Material Description", "Model number",
        "Created On", "Plant",
    },
}

# Organisational fields are inherited from the superior Functional Location in SAP PM.
INHERITABLE_FIELDS = {"Location", "Maintenance Plant", "Main Work Center", "Maint. Planner Group"}
MANUFACTURER_FIELDS = {"Manufacturer", "Model number", "ManufactPartNo.", "Manuf. Serial Number"}


def completion_field_config() -> dict[str, dict[str, Any]]:
    """FIELD_CONFIG entries for the LLM reviewer / agent."""
    config = {}
    for field in COMPLETION_FIELDS:
        config[field.key] = {
            "source_cols": ["Functional Location", "Equipment", "Technical IdentNo.", "Object Description", "FunctLocDescrip.", *field.aliases],
            "suggested_col": f"suggest_{field.key}",
            "status_col": f"__{field.key}_status",
            "confidence_col": f"{field.key}_confidence_score",
            "evidence_col": f"{field.key}_evidence",
            "result_prefix": field.key,
            "target_column": field.aliases[0],
        }
    return config


class MasterDataCompletionValidator:
    """
    Maps and completes data between the Functional Location sheet and the Equipment sheet.

    - Inventory Number follows the FLOC tier (Tag = 8) and the superior FLOC tier.
    - Equipment rows take FL-owned fields from their Functional Location.
    - FL rows take equipment-owned fields from installed equipment, org fields from the parent FLOC.
    - Manufacturer / model / part number are completed from peer equipment sharing a part or model number.
    Original columns are never edited; each field gets suggest_/confidence/evidence columns.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        index: AssetHierarchyIndex,
        min_suggest_confidence: float = 0.85,
        min_review_confidence: float = 0.65,
    ):
        self.df = df
        self.index = index
        self.min_suggest_confidence = min_suggest_confidence
        self.min_review_confidence = min_review_confidence
        self.floc_col = find_column(df, FLOC_ALIASES)
        self.equipment_col = self._exact_column(df, EQUIPMENT_ALIASES)
        self.technical_id_col = find_column(df, TECHNICAL_ID_ALIASES)
        self.object_description_col = find_column(df, OBJECT_DESCRIPTION_ALIASES)
        self.dataset = "equipment" if self.equipment_col else "fl"
        self.peer_columns = {field: self._exact_column(df, [field]) for field in MANUFACTURER_FIELDS}
        skipped = {self._key(name) for name in SKIP_COLUMNS[self.dataset]}
        self.columns = {
            field.key: col
            for field in COMPLETION_FIELDS
            if self.dataset in field.datasets
            and (col := self._exact_column(df, list(field.aliases)))
            and self._key(col) not in skipped
        }
        logging.info("Completion (%s sheet) fields: %s", self.dataset, ", ".join(self.columns) or "none")

    # ------------------------------------------------------------------ public
    def add_validation_columns(self, df: pd.DataFrame, suggested_floc_col: str = "suggest_functional_location") -> pd.DataFrame:
        output = df.copy()
        if not self.floc_col:
            return output
        handlers: dict[str, Callable[[pd.Series, str, str], ValidationResult]] = {
            "inventory_number": self._inventory,
            "superior_functional_location": self._superior,
        }
        for field in COMPLETION_FIELDS:
            col = self.columns.get(field.key)
            if not col:
                continue
            handler = handlers.get(field.key, self._cross_fill_handler(field))
            results = []
            for _, row in output.iterrows():
                floc = normalize_floc(row.get(suggested_floc_col, "")) or normalize_floc(row.get(self.floc_col, ""))
                results.append(handler(row, col, floc))
            new_cols = pd.DataFrame(
                {
                    f"suggest_{field.key}": [r.suggested_value for r in results],
                    f"{field.key}_confidence_score": [r.confidence for r in results],
                    f"{field.key}_evidence": [r.evidence if r.suggested_value else "" for r in results],
                    f"__{field.key}_status": [r.status for r in results],
                },
                index=output.index,
            )
            output = self._insert_after(output, col, new_cols)
            changes = sum(1 for r in results if r.status == "Suggest Change")
            logging.info("Completion %s: %s suggestions, %s manual review", field.key, changes, sum(1 for r in results if r.status == "Manual Review"))
        return output

    # ------------------------------------------------------------------ inventory number
    def _inventory(self, row: pd.Series, col: str, floc: str) -> ValidationResult:
        current = normalize_inventory(row.get(col, ""))
        if not floc:
            return ValidationResult("", "Missing Evidence", "", "Functional Location is blank")

        if self.dataset == "equipment":
            return self._equipment_inventory(row, current, floc)

        expected = self.index.expected_inventory(floc)
        if not expected:
            if current:
                return ValidationResult("", "OK", "", "")
            return ValidationResult("", "Missing Evidence", "", "Inventory Number is blank and FLOC tier could not be derived")
        value, confidence, reason = expected
        parent, _ = self.index.resolve_parent(floc)
        parent_level = self.index.inventory.get(parent, "")
        evidence = f"{reason}; parent={parent or '-'} (Inventory {parent_level or '?'})"

        if not current:
            return self._decide(value, confidence, f"Inventory Number blank; {evidence}")
        if level_rank(current) is None:
            return self._decide(value, confidence, f"Inventory Number '{current}' is not a valid tier; {evidence}")
        if current == value:
            return ValidationResult("", "OK", "", "")
        if value == TAG_LEVEL and confidence >= 0.95:
            return self._decide(value, confidence, f"Tag-level FLOC must be Inventory 8, found {current}; {evidence}")
        if current == TAG_LEVEL and self.index.child_count(floc) > 0:
            return self._decide(value, confidence, f"Inventory 8 but FLOC has {self.index.child_count(floc)} child FLOCs; {evidence}")
        parent_rank = level_rank(parent_level)
        if parent_rank is not None and (level_rank(current) or 0) <= parent_rank:
            return self._decide(value, confidence, f"Inventory {current} is not below parent tier {parent_level}; {evidence}")
        # Current tier is consistent with the hierarchy rules (e.g. 5B vs 5C) - accept it.
        return ValidationResult("", "OK", "", "")

    def _equipment_inventory(self, row: pd.Series, current: str, floc: str) -> ValidationResult:
        master_level = self.index.inventory.get(floc, "")
        original_floc = normalize_floc(row.get(self.floc_col, ""))
        remapped = floc != original_floc
        if remapped and not self.index.exists(floc):
            # Derived NEW Level 8 FL (not yet in the FL master): Inventory 8 at the confidence of that derivation.
            try:
                floc_confidence = float(row.get("functional_location_confidence_score", "") or 0)
            except ValueError:
                floc_confidence = 0.0
            confidence = min(0.90, floc_confidence) if floc_confidence else 0.80
            reason = f"Equipment moves to NEW Level 8 FL {floc} (to be created); equipment is installed at Level 8 (PTG 12.05.04 s3.2.7)"
        elif master_level == TAG_LEVEL:
            confidence, reason = 0.97, f"Equipment is installed on Level 8 FLOC {floc} (FL sheet Inventory 8)"
        elif remapped:
            confidence = 0.80
            reason = f"Suggested FLOC {floc} is FL sheet Inventory {master_level or '?'}, not Level 8"
        else:
            confidence = 0.80
            reason = f"Equipment installed on FLOC {floc} with FL sheet Inventory {master_level or '?'}; standard installs equipment at Tag level (Inventory 8)"
        if current == TAG_LEVEL:
            return ValidationResult("", "OK", "", "")
        prefix = "Inventory Number blank" if not current else f"Inventory Number {current} differs"
        return self._decide(TAG_LEVEL, confidence, f"{prefix}; {reason}")

    # ------------------------------------------------------------------ superior FLOC
    def _superior(self, row: pd.Series, col: str, floc: str) -> ValidationResult:
        current = normalize_floc(clean_value(row.get(col, "")))
        original = normalize_floc(row.get(self.floc_col, ""))
        parent, source = self.index.resolve_parent(original if not current else floc)
        if current:
            if self.index.exists(current) or current == settings.SITE_CODE:
                return ValidationResult("", "OK", "", "")
            if parent and parent != current:
                return self._decide(parent, 0.88, f"Superior FunctLoc. {current} does not exist in FL master; nearest existing ancestor is {parent}")
            return ValidationResult("", "Manual Review", "", f"Superior FunctLoc. {current} does not exist in FL master")
        if not parent:
            return ValidationResult("", "Missing Evidence", "", "Superior FunctLoc. blank and no existing ancestor found")
        confidence = 0.95 if source == "master" else 0.90
        return self._decide(parent, confidence, f"Superior FunctLoc. blank; {'master relation' if source == 'master' else 'longest existing FLOC prefix'} gives {parent}")

    # ------------------------------------------------------------------ cross-sheet fill
    def _cross_fill_handler(self, field: CompletionField) -> Callable[[pd.Series, str, str], ValidationResult]:
        def handler(row: pd.Series, col: str, floc: str) -> ValidationResult:
            current = clean_value(row.get(col, ""))
            candidates = self._candidates(row, field, floc)
            if not candidates:
                if current:
                    return ValidationResult("", "OK", "", "")
                return ValidationResult("", "Missing Evidence", "", f"{field.master_field} blank and no source in FL/Equipment data")
            value, confidence, evidence = candidates[0]
            if not current:
                return self._decide(value, confidence, f"{field.master_field} blank; {evidence}")
            if self._same(current, value):
                return ValidationResult("", "OK", "", "")
            if field.master_field in MANUFACTURER_FIELDS:
                # Keep existing manufacturer data; flag only when peers agree unanimously.
                if confidence < 0.86:
                    return ValidationResult("", "OK", "", "")
                return ValidationResult(value, "Manual Review", f"{min(confidence, 0.75):.3f}", f"REVIEW: {field.master_field} '{current}' differs; {evidence}")
            return ValidationResult(value, "Manual Review", f"{min(confidence, 0.80):.3f}", f"REVIEW: {field.master_field} '{current}' differs; {evidence}")

        return handler

    def _candidates(self, row: pd.Series, field: CompletionField, floc: str) -> list[tuple[str, float, str]]:
        name = field.master_field
        candidates: list[tuple[str, float, str]] = []
        if self.dataset == "equipment":
            equipment = clean_value(row.get(self.equipment_col, ""))
            fl_record = self.index.fl_records.get(floc, {})
            if fl_record.get(name):
                candidates.append((fl_record[name], 0.96, f"FL sheet value for Functional Location {floc}"))
            if name in MANUFACTURER_FIELDS:
                candidates.extend(self._peer_candidates(row, name, equipment))
            elif not candidates and name in INHERITABLE_FIELDS:
                candidates.extend(self._ancestor_candidates(floc, name))
        else:
            installed = self.index.equipment_by_floc.get(floc, [])
            values = {self.index.equipment_records[eq].get(name, "") for eq in installed} - {""}
            if len(values) == 1:
                value = values.pop()
                confidence = 0.95 if name not in {"FunctLocDescrip."} else 0.92
                candidates.append((value, confidence, f"Equipment sheet value of installed equipment {', '.join(installed[:3])}"))
            if name == "FunctLocDescrip." and not candidates and len(installed) == 1:
                description = self.index.equipment_records[installed[0]].get("Object Description", "")
                if description:
                    candidates.append((description[:40], 0.80, f"Object Description of installed equipment {installed[0]} (40-char limit)"))
            if name in INHERITABLE_FIELDS:
                candidates.extend(self._ancestor_candidates(floc, name))
        candidates.sort(key=lambda item: item[1], reverse=True)
        return candidates

    def _ancestor_candidates(self, floc: str, name: str) -> list[tuple[str, float, str]]:
        for distance, ancestor in enumerate(self.index.ancestors(floc), start=1):
            value = self.index.fl_records.get(ancestor, {}).get(name, "")
            if value:
                return [(value, max(0.86, 0.93 - 0.02 * (distance - 1)), f"Inherited from superior FLOC {ancestor} (SAP PM inheritance)")]
        return []

    def _peer_candidates(self, row: pd.Series, name: str, equipment: str) -> list[tuple[str, float, str]]:
        def value(field: str) -> str:
            col = self.peer_columns.get(field)
            return clean_value(row.get(col, "")) if col else ""

        part, model, manufacturer = value("ManufactPartNo."), value("Model number"), value("Manufacturer")
        lookups: list[tuple[dict, tuple[str, ...], str]] = []
        if name == "Manufacturer":
            lookups = [(self.index.part_to_manufacturer, (part,), f"ManufactPartNo. {part}"), (self.index.model_to_manufacturer, (model,), f"Model number {model}")]
        elif name == "Model number":
            lookups = [(self.index.part_to_model, (part, manufacturer), f"ManufactPartNo. {part} + Manufacturer {manufacturer}")]
        # ManufactPartNo. is not inferred: one model can carry several part numbers, so peers are no ground truth.
        candidates = []
        for index, key, label in lookups:
            if not all(key):
                continue
            peer_value, support, conflicts = AssetHierarchyIndex.peer_value(index, key)
            if equipment and self.index.equipment_records.get(equipment, {}).get(name) == peer_value:
                support -= 1  # do not count the row itself as a peer
            if not peer_value or support <= 0:
                continue
            if conflicts:
                confidence = 0.70
            else:
                confidence = 0.92 if support >= 2 else 0.86
            if name == "ManufactPartNo.":
                # One model can carry several part numbers: never auto-fill a part number from the model.
                confidence = min(confidence, 0.75)
            candidates.append((peer_value, confidence, f"{support} peer equipment with same {label} use {name}={peer_value}" + (f"; {conflicts} conflicting" if conflicts else "")))
        return candidates

    # ------------------------------------------------------------------ helpers
    def _decide(self, suggested: str, confidence: float, evidence: str) -> ValidationResult:
        if confidence >= self.min_suggest_confidence:
            return ValidationResult(suggested, "Suggest Change", f"{confidence:.3f}", evidence)
        if confidence >= self.min_review_confidence:
            # Candidate is kept for the LLM reviewer / agent to confirm.
            return ValidationResult(suggested, "Manual Review", f"{confidence:.3f}", f"REVIEW: {evidence}")
        return ValidationResult("", "Missing Evidence", "", evidence)

    @staticmethod
    def _same(left: str, right: str) -> bool:
        return re.sub(r"[^A-Z0-9]", "", left.upper()) == re.sub(r"[^A-Z0-9]", "", right.upper())

    @staticmethod
    def _key(name: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", str(name).upper())

    @classmethod
    def _exact_column(cls, df: pd.DataFrame, aliases: list[str]) -> str | None:
        normalized = {cls._key(col): col for col in df.columns if not str(col).startswith(("suggest_", "__"))}
        for alias in aliases:
            found = normalized.get(cls._key(alias))
            if found:
                return found
        return None

    @staticmethod
    def _insert_after(df: pd.DataFrame, source_col: str | None, new_cols: pd.DataFrame) -> pd.DataFrame:
        return insert_after(df, source_col, new_cols)
