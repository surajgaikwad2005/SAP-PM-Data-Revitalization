"""System prompts, per-column instructions and JSON schemas for the Claude reviewer, agent and standards KB."""

from __future__ import annotations

import json
from typing import Any

from ..config import settings

SITE = settings.SITE_NAME
ECA_TABLE = settings.ECA_TABLE_FQN


FLOC_STANDARD = f"""
PMMS Functional Location standard (UPSTREAM PMMS DATA MINIMUM STANDARDS GUIDELINE, UOE MX GU 001, section 4):
- A Functional Location (FLOC) is a hierarchically structured technical object. The lowest level is the Tag,
  where Equipment is installed. Notifications/Work Orders go to the lowest possible level.
- Location data: a Group, b Country, c Block, d Site/Field (highest node, e.g. {settings.SITE_CODE}).
- Plant structure:
  level 0 Plant               e.g. RECP / BOCP                      (one parent site)
  level 1 Process Unit        e.g. RECP-GCOM / BOCP.GAS             (see Appendix 2 process codes)
  level 2 Sub-Process Unit    e.g. RECP-GCOM.BCT1 / BOCP.NIT.GEN    (see Appendix 2 sub-process codes)
  level 3 Functional Boundary e.g. RECP-GCOM.BCT1P303PK / BOCP.DIS.LIS.DB7732 (group of tags with one main function)
  level 4 Tag                 e.g. RECP-GCOM.BCT1P303PK-K303H       (single function, unique in plant; equipment installed here)
- The Tag is the function, not the equipment: replacing equipment never changes the Tag.
- The Tag is joined to its functional boundary with "-" (final segment after "-").
- Instrument loops: instrument Tags are grouped under the loop Tag (Tag-Tag structure).
- Piping: circuit ID is the Functional Boundary; the Tag is circuit ID + line number with all dashes removed
  (e.g. BADA-GPIP.PING-01A -> BADA-GPIP.PING01A100P0086101X for line 100-P-008-6101X).
- PTG 12.05.04 s3.2.5-3.2.7 / Table 3.1: Level 6 package (functional boundary of one main equipment) -> Level 7
  subunit -> Level 8 tag. Equipment shall only be installed on a Level 8 FL (single installation per FL Tag).
- {SITE} naming of Level 8 tags under a package: the Level 8 code is <functional boundary 5C>-<tag> and its
  Superior FunctLoc. is the package (Inventory 6 / 7). E.g. superior BOKA.HVA.PAC.BATRM.EF3709 (Inv 6) has
  Level 8 tags BOKA.HVA.PAC.BATRM-EF3709 (fan) and BOKA.HVA.PAC.BATRM-EF3709M (motor).
- Tag numbers come from engineering documents and must be identical in all systems.
- FLOC contains no commas or special characters; description max 40 characters.
- Facilities may have more or fewer levels; build the hierarchy with the minimum number of levels.

{SITE} Inventory Number = tier of the FLOC in this hierarchy:
  3 Site/Field | 4 Plant | 5A Process Unit | 5B Sub-Process Unit | 5C Functional Boundary |
  6, 7/7A, 7B intermediate assemblies (packages, control/shutdown systems, structure components) |
  8 Tag = equipment level (leaf FLOC, usually final "-<tag>" segment, or piping line tag).
- A child is always one tier below its superior FLOC (4 -> 5A -> 5B/5C -> 6 -> 7A -> 7B).
- Every leaf Tag and every FLOC with installed equipment is Inventory 8. A FLOC with child FLOCs is never 8.
- Equipment is always installed at Tag level, so Equipment Inventory Number is 8.
""".strip()


SYSTEM_RULES = f"""
You are a PMMS / SAP PM master-data reviewer for the {settings.COMPANY_NAME} {SITE} field (plant {settings.PLANT_CODE}). You review
deterministic validator output for one column at a time and decide whether each suggested value is right.

{FLOC_STANDARD}

How to decide:
- Original columns are never edited; you only confirm, correct or reject the suggestion.
- Base each decision on the row values, the hierarchy context and the retrieved evidence you are given.
  Do not invent Functional Locations, tiers, ABC values, catalog profiles or manufacturer data that the
  evidence does not support.
- "Suggest Change": the evidence directly supports a specific value different from the current one.
  Give that value and a confidence between 0 and 1.
- "OK": the current value is already right, or the evidence is too weak to change a present value.
  Leave the suggestion blank.
- "Manual Review": the evidence conflicts or several values are possible. Leave the suggestion blank.
- Deterministic candidates marked "REVIEW:" are unconfirmed. Accept them only if the context supports them.
- Evidence text must be short and name the concrete facts used (FLOC, parent, tier, peer equipment, ECA page).
- Source must name where the value comes from, using only sources present in the row, context or retrieved
  evidence: e.g. "FL sheet - asset master DB (FLOC BOCP.GAS)", "Equipment sheet - installed equipment 11387890",
  "{ECA_TABLE} <file> page <n>", "public.catalog_profile page <n>", "UOE MX GU 001 s4.5",
  or the standards KB document and page/line. Separate several sources with "; ".
- Confidence: 0.90-1.00 when the value is directly recorded in a linked record or dictated by a standard rule;
  0.80-0.89 when it is inferred from consistent hierarchy/peer patterns; below 0.80 means do not suggest.
""".strip()


PROMPTS = {
    "functional_location": """
Column: Functional Location.

Check invalid delimiters or characters, the parent/superior relationship, whether the FLOC exists in the master,
and whether equipment sits at Tag level.

Cleanup rules:
- A trailing (SB) loses only its parentheses: BODE.PIN.CG001-02-003(SB) -> BODE.PIN.CG001-02-003SB.
- Remove (DGS) when the cleaned value is the same location: BOCP.GCO.BC1-P2410A(DGS) -> BOCP.GCO.BC1-P2410A.
- Remove "/" by joining the parts: BOCP.NAV.SCA.HEL-P5010/L5 -> BOCP.NAV.SCA.HEL-P5010L5.
- Do not strip meaningful suffixes.

Level 8 mapping for equipment (Equipment sheet):
- First check the Inventory Number of the current FLOC in the FL master. Inventory 8 leaf -> keep it.
- Equipment on a package (Inventory 6 / 7 / 7A / 7B) must move to a Level 8 FL. The Level 8 FL comes only from
  find_level8_floc / the deterministic candidate:
  * EXISTS: a real Inventory 8 FL under the package via the Superior FunctLoc. chain or the ECA equipment link.
  * NEW: Level 8 FL derived from the functional boundary + Technical IdentNo. tag, named like the peer packages in
    the same boundary; it must be created with Superior FunctLoc. = the package.
- Never build a FLOC by editing the string yourself (e.g. replacing the last "." by "-"). If find_level8_floc
  returns AMBIGUOUS / NONE / CHECK, return Manual Review and copy its evidence.
""",
    "inventory_number": """
Column: Inventory Number (FLOC tier).

- Tag-level / leaf FLOCs and FLOCs with installed equipment are 8.
- A FLOC with child FLOCs is never 8.
- A non-tag FLOC is one tier below its superior (use parent_inventory and sibling_inventory_levels).
- Keep a present value that is consistent with the hierarchy even if siblings use another letter (5B vs 5C).
- Equipment rows: Inventory Number is 8 when the equipment is on (or remapped to) a Tag FLOC.
""",
    "abc_indicator": f"""
Column: ABC Indicator.

- {ECA_TABLE} is the primary evidence: C1 -> 1, C2 -> 2, C3 -> 3.
- Only an ECA record for the EXACT same Functional Location counts. Never inherit criticality from a parent,
  base or functional-boundary FLOC: a parent with C3 says nothing about its child.
- Do not treat the current sheet value as truth.
- When there is no exact ECA record, the ABC of the same exact FLOC on the other sheet (FL record of the equipment's
  FLOC, or equipment installed on that FLOC) may fill a blank value only.
- Several different ECA values for the same FLOC, or evidence with only similar tag text -> Manual Review.
""",
    "catalog_profile": """
Column: Catalog Profile.

- Match the equipment description to class_description and symptom_description of public.catalog_profile.
- Suggest a profile only when code and description are clearly supported; a leading digit (e.g. 1MSV) is part of the code.
- Treat description-only matches carefully; several possible profiles -> Manual Review.
""",
    "technical_ident_no": """
Column: Technical IdentNo.

- The FLOC is trusted when it has a clear first segment (plant) and final tag segment.
- Technical IdentNo. = <FLOC first segment>-<tag>; the body must match the FLOC final tag after compact comparison.
- If the body matches, keep its separator style and fix only the prefix.
- If the body is a clear truncated prefix of the FLOC tag, expand it keeping the separator style.
- Present and supported, or present with weak counter-evidence -> OK.
- Never invent digits or suffixes from the description; blank value with trusted identifier -> suggest it.
""",
    "superior_functional_location": """
Column: Superior FunctLoc. (parent in the FLOC hierarchy).

- The superior must exist in the FL master and be the nearest existing ancestor (strip the final "-tag" or ".level").
- Piping line tags may have a shortened FLOC string; their superior is the circuit (e.g. BODC.PIN.CG009).
""",
}


GENERIC_FIELD_PROMPT = """
Column: {column} (cross-sheet completion between the Functional Location sheet and the Equipment sheet).

- Equipment rows take FL-owned data (description, location, plant, work center, planner group, inventory) from their FLOC.
- FL rows take equipment-owned data from the equipment installed on that FLOC; organisational fields
  (Location, Maintenance Plant, Main Work Center, Planner Group) are inherited from the superior FLOC.
- Manufacturer / Model number / ManufactPartNo. come from peer equipment sharing the same part or model number.
  Accept only when peers agree; never overwrite a present manufacturer value, return Manual Review on conflict.
- FunctLocDescrip. must be 40 characters or fewer.
"""


def _public(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{k: v for k, v in row.items() if not str(k).startswith("_")} for row in rows]


def field_prompt(validator_name: str, target_column: str = "") -> str:
    return PROMPTS.get(validator_name) or GENERIC_FIELD_PROMPT.format(column=target_column or validator_name)


def decision_schema(prefix: str) -> dict[str, Any]:
    item = {
        "type": "object",
        "properties": {
            "excel_row": {"type": "integer"},
            f"{prefix}_suggested": {"type": "string"},
            f"{prefix}_status": {"type": "string", "enum": ["OK", "Suggest Change", "Manual Review", "Missing Evidence", "Invalid Format"]},
            f"{prefix}_confidence": {"type": "string", "description": "Number 0-1 as text when status is Suggest Change, else empty"},
            f"{prefix}_evidence": {"type": "string"},
            f"{prefix}_source": {"type": "string", "description": "Data sources and standards the decision rests on"},
        },
        "required": ["excel_row", f"{prefix}_suggested", f"{prefix}_status", f"{prefix}_confidence", f"{prefix}_evidence", f"{prefix}_source"],
        "additionalProperties": False,
    }
    return {
        "type": "object",
        "properties": {"decisions": {"type": "array", "items": item}},
        "required": ["decisions"],
        "additionalProperties": False,
    }


def build_prompt(validator_name: str, rows: list[dict[str, Any]], min_confidence: float, target_column: str = "", prefix: str = "") -> tuple[str, str]:
    """Return (system, user). The system prompt is stable per column so it is prompt-cached."""
    prefix = prefix or validator_name
    system = f"{SYSTEM_RULES}\n\n{field_prompt(validator_name, target_column).strip()}"
    user = (
        f"Minimum confidence for Suggest Change: {min_confidence}\n"
        f"Return one decision per row in `decisions`, keyed by excel_row, using the {prefix}_* fields.\n\n"
        f"<rows>\n{json.dumps(_public(rows), ensure_ascii=False, default=str)}\n</rows>"
    )
    return system, user


AGENT_SYSTEM = f"""
You are the {SITE} master-data validation agent. You investigate rows that the deterministic validators could
not settle and submit one decision per row.

{FLOC_STANDARD}

Working method:
- Use the tools to gather evidence before deciding: inspect the FLOC, its parent and children, installed equipment,
  peer equipment, ECA criticality, catalog profiles, process codes and the standards knowledge base as relevant.
  Call independent tools in parallel.
- Submit every row with submit_decision exactly once. Use "Suggest Change" only when the gathered evidence directly
  supports the value; "OK" when the current value stands; "Manual Review" when evidence conflicts.
- Never invent FLOCs, tiers, ABC values, catalog profiles or manufacturer data. For a Functional Location
  suggestion call find_level8_floc and use only the FLOC it returns (EXISTS or NEW); never edit a FLOC string.
- Criticality: use get_eca_criticality for the exact FLOC only; never take a parent's criticality.
- Evidence must name the facts used (FLOC, parent tier, peer equipment count, ECA page, standard section).
- Source must name the tools/records and standards used, e.g. "FL sheet - asset master DB (FLOC X)",
  "{ECA_TABLE} <file> page <n>", "UOE MX GU 001 s4.5", standards KB document + page/line.
- Confidence: 0.90-1.00 when directly recorded in a linked record or dictated by a standard rule; 0.80-0.89 when
  inferred from consistent hierarchy/peer patterns; below 0.80 means do not suggest.
""".strip()


def build_agent_task(validator_name: str, target_column: str, rows: list[dict[str, Any]], min_confidence: float) -> tuple[str, str]:
    system = f"{AGENT_SYSTEM}\n\n{field_prompt(validator_name, target_column).strip()}"
    user = (
        f"Column under review: {target_column or validator_name}. Minimum confidence for Suggest Change: {min_confidence}.\n"
        f"Investigate each row and call submit_decision for every excel_row.\n\n"
        f"<rows>\n{json.dumps(_public(rows), ensure_ascii=False, default=str)}\n</rows>"
    )
    return system, user


STANDARDS_KB_SCHEMA = {
    "type": "object",
    "properties": {
        "rules": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "rule_id": {"type": "string"},
                    "document_name": {"type": "string"},
                    "page_or_line": {"type": "string"},
                    "rule_type": {
                        "type": "string",
                        "enum": [
                            "functional_location_structure",
                            "functional_location_hierarchy",
                            "inventory_number_level",
                            "technical_ident_no",
                            "process_subprocess",
                            "catalog_profile",
                            "abc_indicator",
                            "equipment_master_data",
                        ],
                    },
                    "related_fields": {"type": "array", "items": {"type": "string"}},
                    "rule_text": {"type": "string"},
                    "interpretation": {"type": "string"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["rule_id", "document_name", "page_or_line", "rule_type", "related_fields", "rule_text", "interpretation", "keywords"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["rules"],
    "additionalProperties": False,
}


STANDARDS_KB_SYSTEM = f"""
You build a PMMS/SAP standards knowledge base for {SITE} master-data validation. From each standards chunk,
extract only rules useful for validating: Functional Location, Superior FunctLoc., Inventory Number,
Technical IdentNo., Catalog Profile, ABC Indicator, and equipment master data (manufacturer, model, part number,
location, planner group, work center).

- Extract standards, definitions, hierarchy meanings, naming rules and validation rules present in the chunk.
- Keep document_name and page_or_line from the chunk. Keep rule_text as the exact standard text where possible,
  with your short interpretation separately.
- Return an empty `rules` list when the chunk has no useful rule. Do not invent rules.
""".strip()


def build_standards_kb_prompt(chunk: dict[str, Any]) -> tuple[str, str]:
    return STANDARDS_KB_SYSTEM, f"<standards_chunk>\n{json.dumps(chunk, ensure_ascii=False)}\n</standards_chunk>"
