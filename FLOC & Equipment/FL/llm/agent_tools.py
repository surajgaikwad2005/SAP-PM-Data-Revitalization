"""Local tools (JSON schemas + handlers) the Claude agent calls to investigate master data and standards."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from ..config import settings
from ..core.common import compact_key, normalize_abc, normalize_floc, normalize_text
from ..core.hierarchy_rules import AssetHierarchyIndex, clean_value
from ..data.database_evidence import load_reference_table


def _tool(name: str, description: str, properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "strict": True,
        "input_schema": {"type": "object", "properties": properties, "required": required, "additionalProperties": False},
    }


STRING = {"type": "string"}
LIMIT = {"type": "integer", "description": "Maximum number of results (1-50)"}


class AgentToolbox:
    """Local tools the Claude agent uses to investigate master data, ECA, catalog and standards evidence."""

    def __init__(
        self,
        index: AssetHierarchyIndex,
        cache_dir: str = settings.CACHE_DIR,
        use_database: bool = True,
        standards_kb_file: str = settings.STANDARDS_KB_FILE,
    ):
        self.index = index
        self.cache_dir = cache_dir
        self.use_database = use_database
        self.standards_kb_file = standards_kb_file
        self._eca: dict[str, list[dict[str, str]]] | None = None
        self._catalog: pd.DataFrame | None = None
        self._process: pd.DataFrame | None = None
        self._standards: list[dict[str, Any]] | None = None
        self.decisions: dict[int, dict[str, Any]] = {}
        self.prefix = ""

    # ------------------------------------------------------------------ definitions
    def definitions(self, prefix: str) -> list[dict[str, Any]]:
        self.prefix = prefix
        return [
            _tool(
                "get_functional_location",
                "Master record and hierarchy context of one Functional Location: description, inventory tier, expected tier "
                "with reason, superior FLOC and its tier, ancestors, children sample, sibling tiers and installed equipment.",
                {"floc": STRING},
                ["floc"],
            ),
            _tool(
                "list_children",
                "Child Functional Locations of a FLOC with their inventory tier and description.",
                {"floc": STRING, "limit": LIMIT},
                ["floc", "limit"],
            ),
            _tool(
                "search_functional_locations",
                "Find Functional Locations whose code contains the text (compact match, e.g. a tag like PSV6410) or whose "
                "description contains all the words.",
                {"text": STRING, "limit": LIMIT},
                ["text", "limit"],
            ),
            _tool(
                "get_equipment",
                "Equipment master record (FLOC, Technical IdentNo., descriptions, catalog profile, ABC, manufacturer data).",
                {"equipment": STRING},
                ["equipment"],
            ),
            _tool(
                "search_equipment",
                "Find peer equipment by a field value. field is one of: Technical IdentNo., Model number, ManufactPartNo., "
                "Manufacturer, Object Description. Returns manufacturer data so peers can be compared.",
                {"field": {"type": "string", "enum": ["Technical IdentNo.", "Model number", "ManufactPartNo.", "Manufacturer", "Object Description"]}, "value": STRING, "limit": LIMIT},
                ["field", "value", "limit"],
            ),
            _tool(
                "get_eca_criticality",
                f"ECA criticality records ({settings.ECA_TABLE_FQN}) for this EXACT Functional Location only - never its parent "
                "or functional boundary. C1->ABC 1, C2->ABC 2, C3->ABC 3.",
                {"floc": STRING},
                ["floc"],
            ),
            _tool(
                "find_level8_floc",
                "Level 8 (Tag) Functional Location for equipment installed on `floc`. Returns status EXISTS (real Level 8 FL "
                "found under the package via Superior FunctLoc. chain or ECA equipment link), NEW (Level 8 FL derived from the "
                "functional boundary + Technical IdentNo. tag, named like the peer packages; to be created), AMBIGUOUS, NONE or "
                "CHECK, with the FLOC, its superior, confidence and evidence.",
                {"floc": STRING, "technical_ident_no": STRING, "object_description": STRING},
                ["floc", "technical_ident_no", "object_description"],
            ),
            _tool(
                "search_catalog_profiles",
                "Search public.catalog_profile by class code or description words.",
                {"text": STRING, "limit": LIMIT},
                ["text", "limit"],
            ),
            _tool(
                "lookup_process_code",
                "Appendix 2 process / sub-process code meaning (FLOC level 1 and 2). sub_process_code may be empty.",
                {"process_code": STRING, "sub_process_code": STRING},
                ["process_code", "sub_process_code"],
            ),
            _tool(
                "search_standards",
                "Search the PMMS standards knowledge base (PTG 12.05.04, PMMS manuals, ISO 14224, UDMS) for rules.",
                {"query": STRING, "limit": LIMIT},
                ["query", "limit"],
            ),
            _tool(
                "submit_decision",
                "Record the final decision for one row. Call exactly once per excel_row.",
                {
                    "excel_row": {"type": "integer"},
                    "suggested": {"type": "string", "description": "Suggested value; empty unless status is Suggest Change"},
                    "status": {"type": "string", "enum": ["OK", "Suggest Change", "Manual Review", "Missing Evidence"]},
                    "confidence": {"type": "number", "description": "0-1 confidence in the decision"},
                    "evidence": {"type": "string", "description": "Short facts used for the decision"},
                    "source": {"type": "string", "description": "Records, tables and standards the decision rests on"},
                },
                ["excel_row", "suggested", "status", "confidence", "evidence", "source"],
            ),
        ]

    def handlers(self) -> dict[str, Callable[[dict[str, Any]], Any]]:
        return {
            "get_functional_location": lambda args: self.index.floc_context(args["floc"]),
            "list_children": self.list_children,
            "search_functional_locations": lambda args: self.index.search_flocs(args["text"], self._limit(args)),
            "get_equipment": self.get_equipment,
            "search_equipment": self.search_equipment,
            "get_eca_criticality": self.get_eca_criticality,
            "find_level8_floc": self.find_level8_floc,
            "search_catalog_profiles": self.search_catalog_profiles,
            "lookup_process_code": self.lookup_process_code,
            "search_standards": self.search_standards,
            "submit_decision": self.submit_decision,
        }

    # ------------------------------------------------------------------ handlers
    def submit_decision(self, args: dict[str, Any]) -> str:
        row = int(args["excel_row"])
        status = args["status"]
        confidence = float(args.get("confidence") or 0)
        self.decisions[row] = {
            "excel_row": row,
            f"{self.prefix}_suggested": args.get("suggested", "") if status == "Suggest Change" else "",
            f"{self.prefix}_status": status,
            f"{self.prefix}_confidence": f"{confidence:.3f}" if status == "Suggest Change" else "",
            f"{self.prefix}_evidence": args.get("evidence", ""),
            f"{self.prefix}_source": args.get("source", ""),
        }
        return f"Decision recorded for row {row}."

    def list_children(self, args: dict[str, Any]) -> list[dict[str, str]]:
        floc = normalize_floc(args["floc"])
        return [
            {"floc": child, "inventory": self.index.inventory.get(child, ""), "description": self.index.fl_records.get(child, {}).get("FunctLocDescrip.", "")}
            for child in self.index.children.get(floc, [])[: self._limit(args)]
        ]

    def get_equipment(self, args: dict[str, Any]) -> dict[str, Any]:
        record = self.index.equipment_records.get(clean_value(args["equipment"]).lstrip("0"), {})
        return {k: v for k, v in record.items() if v} or {"error": "equipment not found"}

    def search_equipment(self, args: dict[str, Any]) -> list[dict[str, str]]:
        field, value = args["field"], compact_key(args["value"])
        if not value:
            return []
        keep = ["Equipment", "Functional Location", "Technical IdentNo.", "Object Description", "Manufacturer", "Model number", "ManufactPartNo.", "Catalog Profile"]
        output = []
        for record in self.index.equipment_records.values():
            candidate = compact_key(record.get(field, ""))
            if candidate and (candidate == value or (field == "Object Description" and value in candidate)):
                output.append({k: record.get(k, "") for k in keep})
                if len(output) >= self._limit(args):
                    break
        return output

    def get_eca_criticality(self, args: dict[str, Any]) -> list[dict[str, str]]:
        floc = normalize_floc(args["floc"])
        records = [{"match": "exact", **record} for record in self._eca_index().get(floc, [])[:12]]
        return records or [{"info": f"no ECA record for exact FLOC {floc}; criticality is not inherited from parent FLOCs"}]

    def find_level8_floc(self, args: dict[str, Any]) -> dict[str, Any]:
        result = self.index.find_level8_floc(args["floc"], args.get("technical_ident_no", ""), args.get("object_description", ""))
        if result is None:
            floc = normalize_floc(args["floc"])
            if floc in self.index.fl_records:
                return {"status": "OK", "floc": floc, "info": f"{floc} is already a valid Level 8 (Inventory 8) leaf FLOC"}
            return {"status": "NONE", "info": f"{floc} not found in FL master"}
        return result

    def search_catalog_profiles(self, args: dict[str, Any]) -> list[dict[str, str]]:
        table = self._catalog_table()
        if table.empty:
            return []
        text = normalize_text(args["text"])
        words = [w for w in re.findall(r"[A-Z0-9]+", text) if len(w) >= 3]
        scored = []
        for record in table.to_dict("records"):
            code = normalize_text(record.get("class", ""))
            haystack = normalize_text(f"{code} {record.get('class_description', '')} {record.get('symptom_description', '')}")
            score = 5 if compact_key(text) == compact_key(code) else sum(1 for w in words if w in haystack)
            if score:
                scored.append((score, code, record))
        seen, output = set(), []
        for score, code, record in sorted(scored, key=lambda item: -item[0]):
            if code in seen:
                continue
            seen.add(code)
            output.append({"class": code, "class_description": record.get("class_description", ""), "level": record.get("level", ""), "source_page": record.get("source_page", "")})
            if len(output) >= self._limit(args):
                break
        return output

    def lookup_process_code(self, args: dict[str, Any]) -> list[dict[str, str]]:
        table = self._process_table()
        process, sub = normalize_text(args["process_code"]), normalize_text(args.get("sub_process_code", ""))
        if table.empty or not process:
            return []
        mask = table["process_code"].map(normalize_text) == process
        if sub:
            sub_mask = mask & (table["sub_process_code"].map(normalize_text) == sub)
            if sub_mask.any():
                mask = sub_mask
        return table[mask].head(10).to_dict("records")

    def search_standards(self, args: dict[str, Any]) -> list[dict[str, str]]:
        words = {w for w in re.findall(r"[A-Z0-9]+", normalize_text(args["query"])) if len(w) >= 3}
        scored = []
        for record in self._standards_records():
            text = normalize_text(" ".join(str(record.get(k, "")) for k in ("value", "evidence_text", "interpretation", "keywords")))
            score = len(words & set(re.findall(r"[A-Z0-9]+", text)))
            if score:
                scored.append((score, record))
        return [
            {
                "rule_type": str(record.get("value", "")),
                "source": f"{record.get('source_name', '')} {record.get('source_ref', '')}",
                "rule_text": str(record.get("evidence_text", ""))[:600],
                "interpretation": str(record.get("interpretation", ""))[:300],
            }
            for _, record in sorted(scored, key=lambda item: -item[0])[: self._limit(args)]
        ]

    # ------------------------------------------------------------------ lazy reference data
    def _eca_index(self) -> dict[str, list[dict[str, str]]]:
        if self._eca is None:
            self._eca = {}
            table = load_reference_table(settings.ECA_TABLE, self.cache_dir, self.use_database, allow_local_fallback=False)
            for record in table.to_dict("records"):
                floc = normalize_floc(record.get("functional_location", ""))
                if floc:
                    self._eca.setdefault(floc, []).append(
                        {
                            "floc": floc,
                            "description": str(record.get("functional_location_description", "")),
                            "criticality": str(record.get("criticality", "")),
                            "abc": normalize_abc(record.get("criticality_norm", "")) or normalize_abc(record.get("criticality", "")),
                            "source": f"{record.get('source_file', '')} page {record.get('page_no', '')}",
                        }
                    )
        return self._eca

    def _catalog_table(self) -> pd.DataFrame:
        if self._catalog is None:
            self._catalog = load_reference_table("catalog_profile", self.cache_dir, self.use_database)
        return self._catalog

    def _process_table(self) -> pd.DataFrame:
        if self._process is None:
            self._process = load_reference_table("process_subprocess", self.cache_dir, self.use_database)
        return self._process

    def _standards_records(self) -> list[dict[str, Any]]:
        if self._standards is None:
            path = Path(self.standards_kb_file)
            try:
                self._standards = json.loads(path.read_text(encoding="utf-8")).get("records", []) if path.exists() else []
            except json.JSONDecodeError:
                self._standards = []
        return self._standards

    @staticmethod
    def _limit(args: dict[str, Any]) -> int:
        try:
            return max(1, min(50, int(args.get("limit", 20))))
        except (TypeError, ValueError):
            return 20
