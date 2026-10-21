"""Functional Location validation: format cleanup, master lookup, Level 8 (Tag) mapping and tier checks."""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import settings
from ..core.common import (
    FLOC_RE,
    EvidenceRecord,
    FunctionalLocationHierarchy,
    ValidationResult,
    find_column,
    insert_after,
    inventory_level,
    is_final_tag_floc,
    load_cached_records,
    normalize_floc,
    normalize_text,
    parent_floc,
    save_cached_records,
    split_floc,
)
from ..core.hierarchy_rules import PACKAGE_LEVELS, TAG_LEVEL, AssetHierarchyIndex, normalize_inventory
from ..data.database_evidence import load_asset_master_cache, load_reference_table

# A Level 8 Tag sits under a sub-process, functional boundary or package.
LEVEL8_SUPERIOR_LEVELS = {"5B", "5C", "6", "7", "7A", "7B"}


FLOC_ALIASES = ["Functional Location", "FunctLoc", "FLOC"]
DESCRIPTION_ALIASES = ["FunctLocDescrip.", "Functional Location Description", "FLOC Description", "Description"]
INVENTORY_ALIASES = ["Inventory Number", "Inventory"]
SUPERIOR_ALIASES = ["Superior FunctLoc.", "Superior Functional Location", "Superior FLOC", "Parent Functional Location"]
EQUIPMENT_ALIASES = ["Equipment", "Equipment Number"]
OBJECT_DESCRIPTION_ALIASES = ["Object Description", "Equipment Description", "Material Description"]
TECHNICAL_ID_ALIASES = ["Technical IdentNo.", "Technical IdentNo", "Technical Identification"]


class FunctionalLocationValidator:
    """
    Validates Functional Location.

    Required minimum:
    - Functional Location

    Stronger validation when available:
    - FunctLocDescrip.
    - Superior FunctLoc.
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
        index: AssetHierarchyIndex | None = None,
    ):
        self.df = df
        self.floc_col = find_column(df, FLOC_ALIASES)
        self.description_col = find_column(df, DESCRIPTION_ALIASES)
        self.object_description_col = find_column(df, OBJECT_DESCRIPTION_ALIASES)
        self.inventory_col = find_column(df, INVENTORY_ALIASES)
        self.superior_col = find_column(df, SUPERIOR_ALIASES)
        self.equipment_col = find_column(df, EQUIPMENT_ALIASES)
        self.technical_id_col = find_column(df, TECHNICAL_ID_ALIASES)
        self.hierarchy = FunctionalLocationHierarchy(df, self.floc_col, self.superior_col)
        self.min_suggest_confidence = min_suggest_confidence
        self.min_review_confidence = min_review_confidence
        self.standard_records = []
        self.standard_examples = {}
        self.standard_rules = []
        self.asset_cache = load_asset_master_cache(asset_cache_file, force_asset_refresh) if self.floc_col else {}
        self.asset_fl_lookup = self.asset_cache.get("fl_lookup", {}) if isinstance(self.asset_cache, dict) else {}
        self.asset_equipment_lookup = self.asset_cache.get("equipment_lookup", {}) if isinstance(self.asset_cache, dict) else {}
        self.asset_hierarchy = self._asset_hierarchy(self.asset_cache)
        self.index = index or AssetHierarchyIndex(self.asset_cache)
        self.level8_results: dict[tuple[str, str], dict[str, Any] | None] = {}
        self.description_to_floc = self._build_description_to_floc(self.asset_cache)
        self.technical_id_to_floc = self._build_technical_id_to_floc(self.asset_cache)
        self.process_index = self._load_process_index(cache_dir, rebuild_cache, use_database) if self.floc_col else {}

    def validate_functional_location(self, row: pd.Series) -> ValidationResult:
        if not self.floc_col:
            return ValidationResult("", "Skipped", "", "Functional Location column not found")

        current = normalize_floc(row.get(self.floc_col, ""))
        if not current:
            return ValidationResult("", "Manual Review", "", "Functional Location is blank")

        validation_floc = current
        if current.endswith("(SB)"):
            suggested = current[:-4] + "SB"
            return ValidationResult(suggested, "Suggest Change", "0.950", "Removed parentheses from (SB) suffix while preserving SB")
        elif "(DGS)" in current:
            suggested = current.replace("(DGS)", "")
            return ValidationResult(suggested, "Suggest Change", "0.950", "Removed non-standard (DGS) suffix from Functional Location")
        elif "/" in current:
            suggested = current.replace("/", "")
            return ValidationResult(suggested, "Suggest Change", "0.950", "Removed slash from Functional Location while preserving tag text")

        if not re.fullmatch(r"[A-Z0-9.-]+", validation_floc):
            cleaned = re.sub(r"[^A-Z0-9.-]", "", validation_floc)
            return ValidationResult(cleaned, "Suggest Change", "0.950", "Removed invalid characters from Functional Location")
        if any(token in validation_floc for token in ("..", "--", ".-", "-.")):
            return ValidationResult("", "Invalid Format", "", "Functional Location has invalid adjacent delimiters")

        parent = parent_floc(validation_floc)
        score = 0.0
        evidence: list[str] = []

        if validation_floc in self.asset_fl_lookup:
            score += 0.35
            evidence.append("Functional Location exists in asset master cache")

        master_suggestion = self._suggest_floc_from_master(row, validation_floc)
        if master_suggestion:
            suggested, confidence, reason = master_suggestion
            if suggested != validation_floc:
                return ValidationResult(suggested, "Suggest Change", f"{confidence:.3f}", reason)
            score += 0.45
            evidence.append(reason)

        tag_level = self._suggest_tag_level_floc(row, validation_floc)
        if tag_level:
            return tag_level
        inventory_check = self._check_inventory_consistency(row, validation_floc)
        if inventory_check:
            return inventory_check

        process_evidence = self._process_evidence(validation_floc)
        if process_evidence:
            score += 0.18
            evidence.append(process_evidence)

        if parent and self._floc_exists(parent):
            score += 0.30
            evidence.append(f"inferred parent exists: {parent}")
        elif parent:
            evidence.append(f"inferred parent missing: {parent}")

        superior = normalize_floc(row.get(self.superior_col, "")) if self.superior_col else ""
        if superior and parent and superior == parent:
            score += 0.25
            evidence.append("Superior Functional Location matches inferred parent")
        elif superior and parent:
            evidence.append(f"Superior Functional Location differs from inferred parent: {superior} vs {parent}")

        if self._is_leaf(validation_floc):
            score += 0.10
            evidence.append("FLOC is leaf in available hierarchy")
        if is_final_tag_floc(validation_floc):
            score += 0.15
            evidence.append("FLOC has final tag suffix after '-'")

        if score >= self.min_review_confidence:
            return ValidationResult("", "OK", "", "")
        return ValidationResult("", "Missing Evidence", "", "; ".join(evidence))

    def validate_inventory_number(self, row: pd.Series) -> ValidationResult:
        if not self.floc_col or not self.inventory_col:
            return ValidationResult("", "Skipped", "", "Inventory validation needs Functional Location and Inventory Number")

        floc = normalize_floc(row.get(self.floc_col, ""))
        current = normalize_text(row.get(self.inventory_col, ""))
        current_level = inventory_level(current)
        depth = len(split_floc(floc))
        child_count = self._child_count(floc)
        evidence = [f"depth={depth}", f"child_count={child_count}", f"parent={parent_floc(floc)}"]

        if is_final_tag_floc(floc) and child_count == 0:
            evidence.append("final tag FLOC and leaf node")
            if current_level == 8:
                return ValidationResult("", "OK", "", "")
            return ValidationResult("", "Manual Review", "", "; ".join(evidence))
        elif is_final_tag_floc(floc):
            evidence.append("final tag FLOC")
            if current_level == 8:
                return ValidationResult("", "OK", "", "")
            return ValidationResult("", "Manual Review", "", "; ".join(evidence))
        elif child_count > 0 and current_level == 8:
            evidence.append("inventory 8 has children, so it is unlikely to be final equipment level")
            return ValidationResult("", "Manual Review", "", "; ".join(evidence))
        elif floc in self.asset_fl_lookup and normalize_text(self.asset_fl_lookup[floc].get("Inventory Number", "")):
            expected = normalize_text(self.asset_fl_lookup[floc].get("Inventory Number", ""))
            evidence.append("inventory matched exact Functional Location in asset master cache")
            if current == expected:
                return ValidationResult("", "OK", "", "")
            return ValidationResult("", "Manual Review", "", "; ".join(evidence))
        else:
            return ValidationResult("", "OK", "", "")

    def add_validation_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        output = df.copy()
        floc_results = [self.validate_functional_location(row) for _, row in df.iterrows()]
        columns = {
            "suggest_functional_location": [r.suggested_value for r in floc_results],
            "functional_location_confidence_score": [r.confidence for r in floc_results],
            # Manual Review keeps its reason so the evidence is visible in the output.
            "functional_location_evidence": [
                r.evidence if r.suggested_value or r.status == "Manual Review" else "" for r in floc_results
            ],
            "__functional_location_status": [r.status for r in floc_results],
        }
        if self.equipment_col:
            columns.update(self._level8_columns(df))
        return self._insert_after(output, self.floc_col, pd.DataFrame(columns, index=df.index))

    def _level8_columns(self, df: pd.DataFrame) -> dict[str, list[str]]:
        """Equipment sheet: Level 8 status and the Superior FunctLoc. of the suggested Level 8 FL."""
        status, superior, confidence, evidence = [], [], [], []
        technical_col = self.technical_id_col
        for _, row in df.iterrows():
            floc = normalize_floc(row.get(self.floc_col, ""))
            key = (floc, normalize_text(row.get(technical_col, "")) if technical_col else "")
            result = self.level8_results.get(key)
            if result is None and floc in self.index.fl_records and self.index.inventory.get(floc) == "8":
                status.append("EXISTS")
            elif result and result["status"] in {"EXISTS", "NEW"}:
                status.append("EXISTS" if result["status"] == "EXISTS" else "NEW - to be created")
            elif result:
                status.append(result["status"])
            else:
                status.append("")
            if result and result["superior"] and result["floc"]:
                superior.append(result["superior"])
                confidence.append(f"{result['confidence']:.3f}")
                evidence.append(f"Superior FunctLoc. of Level 8 FL {result['floc']} is the package {result['superior']}")
            else:
                superior.append("")
                confidence.append("")
                evidence.append("")
        return {
            "level8_fl_status": status,
            "suggest_level8_superior_floc": superior,
            "level8_superior_floc_confidence_score": confidence,
            "level8_superior_floc_evidence": evidence,
        }

    def _suggestion_only(self, current: str, suggested: str, confidence: float, evidence: str) -> ValidationResult:
        if suggested and suggested != current and confidence >= self.min_suggest_confidence:
            return ValidationResult(suggested, "Suggest Change", f"{confidence:.3f}", evidence)
        if suggested and suggested != current and confidence >= self.min_review_confidence:
            return ValidationResult("", "Manual Review", "", evidence)
        return ValidationResult("", "OK", "", "")

    @staticmethod
    def _insert_after(df: pd.DataFrame, source_col: str | None, new_cols: pd.DataFrame) -> pd.DataFrame:
        return insert_after(df, source_col, new_cols)

    @staticmethod
    def _load_standard_records(standards_dir: str, cache_dir: str, rebuild_cache: bool) -> list[EvidenceRecord]:
        folder = Path(standards_dir)
        files = sorted(folder.rglob("*.md")) if folder.exists() else []
        cache_path = Path(cache_dir) / "functional_location_standards.json"
        cached = load_cached_records(cache_path, files, rebuild_cache)
        if cached is None:
            records: list[EvidenceRecord] = []
            for path in files:
                for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
                    text = normalize_text(line)
                    for floc in set(FLOC_RE.findall(text)):
                        records.append(
                            EvidenceRecord(
                                "floc_example",
                                normalize_floc(floc),
                                normalize_floc(floc),
                                path.name,
                                f"line {line_no}",
                                line.strip()[:700],
                                0.84,
                            )
                        )
                    if any(word in text for word in ("FUNCTIONAL LOCATION", "FLOC", "INVENTORY", "LEVEL", "TIER", "HIERARCHY")):
                        records.append(
                            EvidenceRecord(
                                "standard_rule_text",
                                hashlib.sha1(f"{path.name}:{line_no}".encode()).hexdigest()[:16],
                                "",
                                path.name,
                                f"line {line_no}",
                                line.strip()[:700],
                                0.70,
                            )
                        )
            save_cached_records(cache_path, files, records)
            logging.info("Built %s Functional Location standard evidence records", len(records))
        else:
            records = cached
            logging.info("Loaded %s Functional Location standard evidence records from cache", len(records))
        return records

    @staticmethod
    def _standard_examples(records: list[EvidenceRecord]) -> dict[str, str]:
        examples: dict[str, str] = {}
        for record in records:
            if record.evidence_type == "floc_example" and record.key not in examples:
                examples[record.key] = f"{record.source_name} {record.source_ref}: {record.evidence_text}"
        return examples

    @staticmethod
    def _standard_rules(records: list[EvidenceRecord]) -> list[EvidenceRecord]:
        rules = [record for record in records if record.evidence_type == "standard_rule_text"]
        return rules[:3000]

    def _floc_exists(self, floc: str) -> bool:
        return self.hierarchy.exists(floc) or self.asset_hierarchy.exists(floc) or normalize_floc(floc) in self.asset_fl_lookup

    def _child_count(self, floc: str) -> int:
        children = set(self.hierarchy.children.get(normalize_floc(floc), []))
        children.update(self.asset_hierarchy.children.get(normalize_floc(floc), []))
        return len(children)

    def _is_leaf(self, floc: str) -> bool:
        return self._child_count(floc) == 0

    def _suggest_floc_from_master(self, row: pd.Series, current: str) -> tuple[str, float, str] | None:
        equipment = normalize_text(row.get(self.equipment_col, "")) if self.equipment_col else ""
        if equipment and equipment in self.asset_equipment_lookup:
            master = self.asset_equipment_lookup[equipment]
            floc = normalize_floc(master.get("Functional Location", ""))
            if floc:
                return floc, 0.99, f"Exact equipment match in asset master cache: Equipment={equipment}"

        technical_id = normalize_text(row.get(self.technical_id_col, "")) if self.technical_id_col else ""
        if technical_id and technical_id in self.technical_id_to_floc:
            return self.technical_id_to_floc[technical_id], 0.94, f"Technical IdentNo. matched asset master cache: {technical_id}"

        if current in self.asset_fl_lookup:
            return None

        descriptions = []
        for col in [self.object_description_col, self.description_col]:
            if col:
                text = normalize_text(row.get(col, ""))
                if text:
                    descriptions.append(text)
        for description in descriptions:
            if description in self.description_to_floc:
                return self.description_to_floc[description], 0.90, "Description matched asset master cache"
        return None

    def _suggest_tag_level_floc(self, row: pd.Series, floc: str) -> ValidationResult | None:
        """
        Equipment sheet: equipment must sit on a Level 8 (Inventory 8) FLOC (PTG 12.05.04 s3.2.7).
        Equipment on a package (Inventory 6 / 7) is moved to the existing Level 8 FL under it, or to the
        new Level 8 FL derived from the hierarchy and peer packages (see AssetHierarchyIndex.find_level8_floc).
        """
        if not self.equipment_col:
            return None
        technical_id = row.get(self.technical_id_col, "") if self.technical_id_col else ""
        description = row.get(self.object_description_col, "") if self.object_description_col else ""
        result = self.index.find_level8_floc(floc, technical_id, description)
        self.level8_results[(floc, normalize_text(technical_id))] = result
        if not result:
            return None
        suggested, confidence, evidence = result["floc"], result["confidence"], result["evidence"]
        if not suggested or suggested == floc:
            return ValidationResult("", "Manual Review", "", evidence)
        if confidence >= self.min_suggest_confidence:
            return ValidationResult(suggested, "Suggest Change", f"{confidence:.3f}", evidence)
        # Candidate kept so the hybrid reviewer / agent can confirm it against the standards.
        return ValidationResult(suggested, "Manual Review", f"{confidence:.3f}", f"REVIEW: {evidence}")

    def _check_inventory_consistency(self, row: pd.Series, floc: str) -> ValidationResult | None:
        """FL sheet: the FLOC must be consistent with its Inventory Number (tier) in the hierarchy."""
        if self.equipment_col or floc not in self.index.fl_records:
            return None
        level = normalize_inventory(row.get(self.inventory_col, "")) if self.inventory_col else ""
        level = level or self.index.inventory.get(floc, "")
        kids = self.index.children.get(floc, [])
        superior = self.index.parent.get(floc, "")
        superior_level = self.index.inventory.get(superior, "")
        if level == TAG_LEVEL:
            if kids:
                return ValidationResult(
                    "", "Manual Review", "",
                    f"Inventory 8 (Tag) but FLOC has {len(kids)} child FLOCs (e.g. {', '.join(kids[:3])}); "
                    f"a Level 8 Tag must be a leaf (PTG 12.05.04 s3.2.7); FLOC is a package/boundary, not a Tag",
                )
            if superior and superior_level and superior_level not in LEVEL8_SUPERIOR_LEVELS:
                return ValidationResult(
                    "", "Manual Review", "",
                    f"Inventory 8 (Tag) but Superior FunctLoc. {superior} is Inventory {superior_level}; "
                    f"a Tag sits under a sub-process / functional boundary / package (5B, 5C, 6, 7, 7A, 7B)",
                )
            siblings = [s for s in self.index.children.get(superior, []) if s != floc and self.index.inventory.get(s) == TAG_LEVEL]
            dashed = sum(1 for s in siblings if "-" in s)
            if "-" not in floc and siblings and dashed / len(siblings) >= 0.8:
                return ValidationResult(
                    "", "Manual Review", "",
                    f"Inventory 8 (Tag) but code has no '-<tag>' segment while {dashed}/{len(siblings)} sibling Tags under {superior} do "
                    f"(e.g. {next(s for s in siblings if '-' in s)}); UOE MX GU 001 s4",
                )
            return None
        if level in PACKAGE_LEVELS and not kids:
            installed = self.index.equipment_by_floc.get(floc, [])
            if installed:
                record = self.index.equipment_records.get(installed[0], {})
                result = self.index.find_level8_floc(floc, record.get("Technical IdentNo.", ""), record.get("Object Description", ""))
                detail = f" {result['evidence']}" if result else ""
                return ValidationResult(
                    "", "Manual Review", "",
                    f"Inventory {level} package with installed equipment {', '.join(installed[:3])} and no Level 8 child; "
                    f"equipment must move to a Level 8 FL (PTG 12.05.04 s3.2.7).{detail}",
                )
        return None

    def _process_evidence(self, floc: str) -> str:
        parts = split_floc(floc)
        if len(parts) < 3:
            return ""
        process_code = parts[1]
        sub_process_code = parts[2].split("-", 1)[0]
        exact = self.process_index.get((process_code, sub_process_code))
        if exact:
            return exact
        process_only = self.process_index.get((process_code, ""))
        return process_only or ""

    def _standard_structure_evidence(self, floc: str) -> str:
        parts = split_floc(floc)
        if len(parts) < 2:
            return ""
        matched: list[str] = []
        if "." in floc:
            rule = self._first_standard_rule(("FUNCTIONAL LOCATION", "HIERARCHY", "STRUCTURE", "LEVEL", "FLOC"), min_hits=2)
            if rule:
                matched.append(f"hierarchy/naming standard: {rule}")
        if len(parts) >= 3:
            rule = self._first_standard_rule(("PROCESS", "SUBPROCESS", "FUNCTIONAL LOCATION", "SYSTEM"), min_hits=2)
            if rule:
                matched.append(f"process/subprocess standard: {rule}")
        if is_final_tag_floc(floc):
            rule = self._first_standard_rule(("INVENTORY", "EQUIPMENT", "TAG", "FUNCTIONAL LOCATION", "LEVEL"), min_hits=2)
            if rule:
                matched.append(f"final tag/inventory standard: {rule}")
        return "; ".join(matched[:2])

    def _first_standard_rule(self, keywords: tuple[str, ...], min_hits: int = 2) -> str:
        for record in self.standard_rules:
            text = normalize_text(record.evidence_text)
            if sum(1 for keyword in keywords if keyword in text) >= min_hits:
                return f"{record.source_name} {record.source_ref}: {record.evidence_text[:220]}"
        return ""

    @staticmethod
    def _asset_hierarchy(cache: dict[str, Any]) -> FunctionalLocationHierarchy:
        fl_df = cache.get("fl_df") if isinstance(cache, dict) else None
        if isinstance(fl_df, pd.DataFrame) and "Functional Location" in fl_df.columns:
            return FunctionalLocationHierarchy(fl_df, "Functional Location", "Superior FunctLoc." if "Superior FunctLoc." in fl_df.columns else None)
        return FunctionalLocationHierarchy(pd.DataFrame(), None, None)

    @staticmethod
    def _build_description_to_floc(cache: dict[str, Any]) -> dict[str, str]:
        output: dict[str, str] = {}
        equipment_lookup = cache.get("equipment_lookup", {}) if isinstance(cache, dict) else {}
        for row in equipment_lookup.values():
            floc = normalize_floc(row.get("Functional Location", ""))
            if not floc:
                continue
            for key in ["Object Description", "FunctLocDescrip.", "Material Description"]:
                description = normalize_text(row.get(key, ""))
                if description and description not in output:
                    output[description] = floc
        return output

    @staticmethod
    def _build_technical_id_to_floc(cache: dict[str, Any]) -> dict[str, str]:
        output: dict[str, str] = {}
        equipment_lookup = cache.get("equipment_lookup", {}) if isinstance(cache, dict) else {}
        for row in equipment_lookup.values():
            technical_id = normalize_text(row.get("Technical IdentNo.", ""))
            floc = normalize_floc(row.get("Functional Location", ""))
            if technical_id and floc and technical_id not in output:
                output[technical_id] = floc
        return output

    @staticmethod
    def _load_process_index(cache_dir: str, rebuild_cache: bool, use_database: bool) -> dict[tuple[str, str], str]:
        table = load_reference_table("process_subprocess", cache_dir, use_database, rebuild_cache)
        index: dict[tuple[str, str], str] = {}
        for _, row in table.iterrows():
            process_code = normalize_text(row.get("process_code", ""))
            sub_process_code = normalize_text(row.get("sub_process_code", ""))
            process_name = normalize_text(row.get("process_name", ""))
            sub_process_name = normalize_text(row.get("sub_process_name", ""))
            source_page = normalize_text(row.get("source_page", ""))
            if process_code:
                index.setdefault((process_code, ""), f"process code {process_code}={process_name}; source page {source_page}")
            if process_code and sub_process_code:
                index[(process_code, sub_process_code)] = (
                    f"process/subprocess code {process_code}/{sub_process_code}="
                    f"{process_name}/{sub_process_name}; source page {source_page}"
                )
        return index
