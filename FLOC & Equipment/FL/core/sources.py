"""Human-readable source labels and confidence labels for the exported result columns."""

from __future__ import annotations

import re
from typing import Any

from ..config import settings

ECA_PATTERN = re.escape(settings.ECA_TABLE_FQN)

FLOC_STANDARD = "UOE MX GU 001 (PMMS Data Minimum Standards) s4.5 FLOC hierarchy"
FLOC_NAMING = "UOE MX GU 001 (PMMS Data Minimum Standards) s4.7 FLOC naming"
PIPING_STANDARD = "UOE MX GU 001 s4.8 piping FLOC naming"

# (pattern in deterministic evidence, source label). First match wins.
SOURCE_RULES: list[tuple[str, str]] = [
    (r"^Removed|parentheses|slash|invalid characters", f"{FLOC_NAMING} (no special characters)"),
    (ECA_PATTERN, f"ECA report ({settings.ECA_TABLE_FQN})"),
    (r"No ECA record; FL sheet", "FL sheet - asset master DB (linked Functional Location)"),
    (r"No ECA record; Equipment sheet", "Equipment sheet - asset master DB (installed equipment)"),
    (r"public\.catalog_profile|Catalog", "Catalog profile standard (PTG 00.01.03 / public.catalog_profile)"),
    (r"Exact equipment match in asset master", "Equipment master - asset master DB (exact equipment number)"),
    (r"Technical IdentNo\. matched asset master", "Equipment master - asset master DB (Technical IdentNo.)"),
    (r"Description matched asset master", "Equipment master - asset master DB (description match)"),
    (r"installed on Tag-level FLOC ([A-Z0-9.\-()/]+)", f"FL sheet - asset master DB (Inventory of linked Tag FLOC {{0}}) + {FLOC_STANDARD}"),
    (r"remapped to Tag level ([A-Z0-9.\-()/]+)", f"Tag FLOC {{0}} + {FLOC_STANDARD} (equipment at Tag level)"),
    (r"FL final tag|Functional Location final tag", f"FLOC final tag ({FLOC_NAMING}: tag numbers identical in all systems)"),
    (r"Tag FLOC|Tag level|<functional boundary>-<tag>|written as a '\.' level", f"FL master hierarchy + {FLOC_STANDARD} (equipment at Tag level)"),
    (r"piping circuit|part of the code", f"FL master hierarchy + {PIPING_STANDARD} (circuit = functional boundary)"),
    (r"Inventory|tier", f"FL master hierarchy (superior / sibling tiers) + {FLOC_STANDARD}"),
    (r"Superior FunctLoc|existing ancestor|longest existing FLOC prefix|master relation", f"FL master hierarchy (asset master DB) + {FLOC_STANDARD}"),
    (r"Inherited from superior FLOC ([A-Z0-9.\-]+)", "Superior FLOC {0} - FL sheet (SAP PM inheritance)"),
    (r"FL sheet value for Functional Location ([A-Z0-9.\-]+)", "FL sheet - asset master DB (Functional Location {0})"),
    (r"Equipment sheet value of installed equipment ([A-Z0-9\-]+)", "Equipment sheet - asset master DB (installed equipment {0})"),
    (r"Object Description of installed equipment", "Equipment sheet - asset master DB (Object Description)"),
    (r"peer equipment", "Equipment master - peer equipment with same part/model number"),
]


def deterministic_source(evidence: str) -> str:
    text = str(evidence or "").removeprefix("REVIEW: ")
    text = text.split("; LLM ", 1)[0].split("; Agent ", 1)[0]
    for pattern, label in SOURCE_RULES:
        match = re.search(pattern, text)
        if match:
            detail = ""
            if pattern == ECA_PATTERN:
                page = re.search(ECA_PATTERN + r" \w+; (.+?): FLOC=", text)
                detail = f" - {page.group(1)}" if page else ""
            return label.format(*match.groups()) + detail if match.groups() else label + detail
    return "Rule-based validation" if text else ""


def confidence_label(value: Any) -> str:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return str(value or "")
    if score >= 0.90:
        return "High"
    if score >= 0.80:
        return "Medium"
    return "Low"
