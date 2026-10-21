import csv
import hashlib
import re
from difflib import SequenceMatcher
from itertools import combinations
from pathlib import Path
from typing import Literal, NamedTuple

from pydantic import BaseModel, model_validator

from evidence_connectors.pitstops_connector import flag_implausible_work

ConfidenceLabel = Literal["High", "Medium", "Low"]


def _load_csv_cache(cache_path) -> dict[str, dict]:
    path = Path(cache_path)
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as f:
        return {row["cache_key"]: row for row in csv.DictReader(f)}


def _save_csv_cache(cache_path, cache: dict[str, dict], columns: list[str]) -> None:
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in cache.values():
            writer.writerow({k: row.get(k, "") for k in columns})


def confidence_label(score: float) -> ConfidenceLabel:
    if score >= 0.8:
        return "High"
    if score >= 0.5:
        return "Medium"
    return "Low"


# PP5_Status (client spec, 2026-10): VALID / REVIEW_REQUIRED / CONFLICT / CANNOT_VERIFY.
# The Finding.evidence_level field carries this value directly for PP5 (see Finding docstring
# comment below) — no other pain point uses this field.
EvidenceLevel = Literal["VALID", "REVIEW_REQUIRED", "CONFLICT", "CANNOT_VERIFY"]


class Finding(BaseModel):
    pain_point: str
    record_key: str
    field_name: str
    current_value: str | None
    recommended_value: str | None
    confidence: ConfidenceLabel | None
    detection_confidence: float | None = None
    reason: str
    evidence_source: str
    # PP5-only — see EvidenceLevel above. None for every other pain point.
    candidate_value: str | None = None
    evidence_level: EvidenceLevel | None = None
    pp1_flag: str | None = None
    # PP1-only — raw SAP system status of every Equipment/FLOC linked to this Task
    # List's Maintenance Items, comma-joined when more than one distinct value is
    # present (client spec, 2026-10: surface the real status rather than only the
    # agent's own active/inactive judgement, so PCSB can filter by it themselves).
    # None for every other pain point.
    pp1_equipment_status: str | None = None
    pp1_floc_status: str | None = None
    # PP6 Check B (Frequency) internal reason code — FREQUENCY_NOT_ASSIGNED /
    # STRATEGY_NOT_IN_REFERENCE / FREQUENCY_AMBIGUOUS_PACKAGE / CYCLE_TEXT_UNPARSEABLE /
    # NO_EXECUTION_HISTORY / FREQUENCY_DEVIATION_REVIEW / FREQUENCY_OVERDUE_HOLD_SUSPECTED. Never
    # shown to the client directly — collapsed into pp6_status (see PP6Status below) for the
    # client-facing PP6_Flag column. None for every other pain point, and None for PP6 Check A
    # (Strategy) findings too — Check A is unaffected by this field.
    pp6_flag: str | None = None
    # PP6 Check B client-facing status (client spec, 2026-10): VALID / ON_HOLD / REVIEW — see
    # PP6Status below. None for every other pain point and for PP6 Check A findings.
    pp6_status: str | None = None
    pp6_first_missed_cycle: str | None = None
    pp6_consecutive_missed_cycles: int | None = None
    # PP6 Check B structured evidence (client spec, 2026-10): the technical field-list — real
    # Frequency/interval, last completed cycle, missed-cycle labels, consecutive-miss count,
    # schedule-anchor caveat — kept separate from `reason`, which instead carries the plain-
    # language sentence a PETRONAS user reads directly. None for every other pain point and for
    # PP6 Check A findings.
    pp6_evidence_detail: str | None = None

    @model_validator(mode="after")
    def enforce_confidence_rule(self) -> "Finding":
        if self.recommended_value is None:
            if self.confidence is not None:
                raise ValueError(
                    "recommended_value is None but confidence is "
                    f"{self.confidence!r}; must be None — reserved for "
                    "no-evidence cases, never a masked low-confidence guess"
                )
        else:
            if self.confidence is None:
                raise ValueError("recommended_value is set but confidence is None — must be High/Medium/Low")
        if self.detection_confidence is not None and not (0.0 <= self.detection_confidence <= 1.0):
            raise ValueError(
                f"detection_confidence {self.detection_confidence} out of range 0.0-1.0"
            )
        if self.candidate_value is not None and self.recommended_value is not None:
            raise ValueError(
                "candidate_value and recommended_value are both set — a candidate is only "
                "meaningful when there is no verified recommended_value"
            )
        return self


import pandas as pd

from logging_config import batched, get_logger

logger = get_logger()

DEFAULT_REUSE_THRESHOLD = 4  # §5 PP1 — MYVES$$2 pattern: default if config isn't supplied
DEFAULT_BATCH_SIZE = 1000  # config/thresholds.yaml's batch_size — progress-visibility only,


def _none_if_na(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


_OBJECT_TYPE_CODES_BY_DESCRIPTION_KEYWORD = {
    "CENTRIFUGAL": "PUCE",
    "DIAPHRAGM": "PUDI",
    "GEAR": "PUGR",
    "JET": "PUJE",
    "PROGRESS": "PUPC",
    "PROGRESSIVE": "PUPC",
    "PLUNGER": "PUPL",
    "RECIPROCATING": "PURE",
}


def _last_significant_word(description: str) -> str:
    cleaned = description.replace(",", " ")
    words = [w for w in cleaned.split(" ") if w]
    return words[-1] if words else ""


def _object_type_code_for_description(description: str) -> str | None:
    upper = description.upper()
    if "PUMP" not in upper:
        return None
    for keyword, code in _OBJECT_TYPE_CODES_BY_DESCRIPTION_KEYWORD.items():
        if keyword in upper:
            return code
    return None


def _family_code_for_descriptions(descriptions: set[str]) -> str | None:
    codes = {_object_type_code_for_description(d) for d in descriptions}
    if None in codes or len(codes) < 2:
        return None
    families = {c[:2] for c in codes}
    if len(families) != 1:
        return None
    (family,) = families
    return family + "XX"


def _pp1_resolve_asset_location(
    group: str, group_counter: str, task_list_group: pd.DataFrame, platform_codes: list[str]
) -> tuple[str, str | None, set[str]]:
    if "Functional Location" not in task_list_group.columns:
        return "NO_EVIDENCE", None, set()
    rows = task_list_group[
        (task_list_group["Group"].astype(str) == group)
        & (task_list_group["Group Counter"].astype(str) == group_counter)
    ]
    prefixes: set[str] = set()
    for floc in rows["Functional Location"].dropna():
        floc = str(floc)
        prefix = floc.split(".")[0][:4] if "." in floc else floc[:4]
        if prefix in platform_codes:
            prefixes.add(prefix)
    if not prefixes:
        return "NO_EVIDENCE", None, prefixes
    if len(prefixes) == 1:
        (candidate,) = prefixes
        return "VERIFIED", candidate, prefixes
    return "SHARED_REVIEW", None, prefixes


def _build_wo_equipment_and_description_lookups(
    work_order_history: pd.DataFrame | None, agent_a_equipment: pd.DataFrame | None
) -> tuple[dict[tuple[str, str], set[str]], dict[str, str]]:
    wo_equipment_by_key: dict[tuple[str, str], set[str]] = {}
    equipment_to_description: dict[str, str] = {}
    if work_order_history is None or agent_a_equipment is None:
        return wo_equipment_by_key, equipment_to_description
    for r in work_order_history.dropna(subset=["Group", "Group Counter", "Equipment"]).to_dict("records"):
        key = (str(r["Group"]), str(r["Group Counter"]))
        wo_equipment_by_key.setdefault(key, set()).add(str(r["Equipment"]))
    for r in agent_a_equipment.dropna(subset=["Equipment", "Object Description"]).to_dict("records"):
        equipment_to_description[str(r["Equipment"])] = r["Object Description"]
    return wo_equipment_by_key, equipment_to_description


_SUFFIX_LEN = 4  # e.g. "PUCE" in "BOCPPUCE" — the 4 chars after the platform prefix


def _pp1_suffix_correlation_object_type(
    group: str,
    suffix: str,
    wo_equipment_by_key: dict[tuple[str, str], set[str]],
    equipment_to_description: dict[str, str],
) -> tuple[str | None, str]:
    other_descriptions: set[str] = set()
    for (other_group, other_counter), equipment_set in wo_equipment_by_key.items():
        if other_group == group:
            continue
        if other_group[-_SUFFIX_LEN:] != suffix:
            continue
        for equipment in equipment_set:
            description = equipment_to_description.get(equipment)
            if description is not None:
                other_descriptions.add(description)

    if not other_descriptions:
        return None, (
            f"No other Task List Group sharing the suffix '{suffix}' has any historical Work "
            "Order equipment with a resolvable Object Description — no suffix-correlation "
            "evidence available"
        )

    anchors = {_last_significant_word(d) for d in other_descriptions}
    if len(anchors) != 1:
        return None, (
            f"Suffix '{suffix}' also appears on other Groups, but their historical equipment "
            f"descriptions do not converge on one Object Type ({', '.join(sorted(other_descriptions))}) "
            "— suffix is not a reliable Object Type signal for this Group"
        )

    (anchor,) = anchors
    return suffix, (
        f"Suffix '{suffix}' also appears on other Task List Group(s) whose historical equipment "
        f"is consistently described as ending in '{anchor}' ({', '.join(sorted(other_descriptions))}) "
        "— a provisional, never-verified correlation only (not a UDMS-cited code; tested against "
        "independently-supported records, not against this Group's own usage)"
    )


def _pp1_resolve_object_type(
    group: str, group_counter: str,
    wo_equipment_by_key: dict[tuple[str, str], set[str]],
    equipment_to_description: dict[str, str],
) -> tuple[str, str | None, str]:
    equipment_set = wo_equipment_by_key.get((group, group_counter))
    if not equipment_set:
        return "NO_EVIDENCE", None, "no historical Work Order equipment found for this Task List"
    descriptions = {equipment_to_description[e] for e in equipment_set if e in equipment_to_description}
    if not descriptions:
        return "NO_EVIDENCE", None, "historical equipment found, but no Object Description available for any of it"

    if len(descriptions) == 1:
        (description,) = descriptions
        code = _object_type_code_for_description(description)
        if code is not None:
            return "VERIFIED", code, (
                f"10-year Work Order history shows this Task List used exclusively on equipment "
                f"described as '{description}'; per UDMS §9.4/§4.12 Figure 5, cited Object Type code "
                f"is '{code}'"
            )
        suffix = group[-_SUFFIX_LEN:] if len(group) >= _SUFFIX_LEN else group
        suffix_code, suffix_note = _pp1_suffix_correlation_object_type(
            group, suffix, wo_equipment_by_key, equipment_to_description
        )
        base_note = (
            f"10-year Work Order history shows this Task List used exclusively on equipment "
            f"described as '{description}', but no cited UDMS §4.12 Technical Object Type code "
            "exists for this equipment type in any file available to this project (only 7/448 "
            "Figure 5 entries are legible — all Pump variants)"
        )
        if suffix_code is not None:
            return "PROVISIONAL_SUFFIX", suffix_code, f"{base_note}. {suffix_note}"
        return "UNCODED", None, base_note

    anchors = {_last_significant_word(d) for d in descriptions}
    if len(anchors) == 1:
        family_code = _family_code_for_descriptions(descriptions)
        if family_code is not None:
            return "FAMILY", family_code, (
                "10-year Work Order history shows this Task List used across multiple equipment "
                f"descriptions in the same Object Type family ({', '.join(sorted(descriptions))}); "
                f"per UDMS §9.4's family/XX naming convention (p.61), cited family code is '{family_code}'"
            )
        suffix = group[-_SUFFIX_LEN:] if len(group) >= _SUFFIX_LEN else group
        suffix_code, suffix_note = _pp1_suffix_correlation_object_type(
            group, suffix, wo_equipment_by_key, equipment_to_description
        )
        base_note = (
            "10-year Work Order history shows this Task List used across multiple equipment "
            f"descriptions that share the '{next(iter(anchors))}' family ({', '.join(sorted(descriptions))}); "
            "no cited UDMS §4.12 Object Type code covers every equipment type here, so a PUXX-style "
            "value cannot be constructed without guessing"
        )
        if suffix_code is not None:
            return "PROVISIONAL_SUFFIX", suffix_code, f"{base_note}. {suffix_note}"
        return "UNCODED", None, base_note

    return "INCONSISTENT", None, (
        "10-year Work Order history shows this Task List used across multiple equipment "
        f"descriptions with no shared Object Type family ({', '.join(sorted(descriptions))}); "
        "applicability is inconsistent — this Task List may be incorrectly scoped or its "
        "historical usage may include unrelated work"
    )


def _pp1_historical_usage_check(
    group: str, group_counter: str,
    wo_equipment_by_key: dict[tuple[str, str], set[str]],
    equipment_to_description: dict[str, str],
    high_confidence: float,
    inconsistent_applicability_confidence: float,
    task_list_group: pd.DataFrame | None = None,
    platform_codes: list[str] | None = None,
) -> Finding | None:
    location_status, location_candidate, location_prefixes = (
        _pp1_resolve_asset_location(group, group_counter, task_list_group, platform_codes)
        if task_list_group is not None and platform_codes is not None
        else ("NO_EVIDENCE", None, set())
    )
    object_status, object_code, object_evidence = _pp1_resolve_object_type(
        group, group_counter, wo_equipment_by_key, equipment_to_description
    )

    if location_status == "NO_EVIDENCE" and object_status == "NO_EVIDENCE":
        return None
    if location_status == "NO_EVIDENCE" and object_status == "INCONSISTENT":
        return Finding(
            pain_point="PP1",
            record_key=f"{group}-{group_counter}",
            field_name="Group",
            current_value=group,
            recommended_value=None,
            confidence=None,
            detection_confidence=inconsistent_applicability_confidence,
            reason=f"{object_evidence} — review required before any Group naming correction is attempted",
            evidence_source=(
                "Bokor Task List Group.xlsx (Functional Location); BOKOR_10years Work Order Data_Aug26.xlsx; "
                "Equipment Listing_SKA_18June26.xlsx (agent_a); UDMS.pdf §9.4 (applicability must be "
                "established before naming can be corrected)"
            ),
        )
    if location_status == "NO_EVIDENCE" and object_status == "UNCODED":
        return Finding(
            pain_point="PP1",
            record_key=f"{group}-{group_counter}",
            field_name="Group",
            current_value=group,
            recommended_value=None,
            confidence=None,
            detection_confidence=0.55,
            reason=object_evidence,
            evidence_source=(
                "BOKOR_10years Work Order Data_Aug26.xlsx; Equipment Listing_SKA_18June26.xlsx "
                "(agent_a); UDMS.pdf §9.4, §4.12 (Technical Object Type code for this equipment type not available)"
            ),
        )

    location_ok = location_status == "VERIFIED"
    object_ok = object_status in ("VERIFIED", "FAMILY")

    if location_ok and object_ok:
        expected_group = f"{location_candidate}{object_code}"
        if expected_group == group:
            return None  # already compliant — nothing to flag
        return Finding(
            pain_point="PP1",
            record_key=f"{group}-{group_counter}",
            field_name="Group",
            current_value=group,
            recommended_value=expected_group,
            confidence=confidence_label(high_confidence),
            reason=(
                f"Asset Location verified from linked Functional Location(s) as '{location_candidate}' "
                f"(single consistent platform prefix). {object_evidence}. Per UDMS §9.4 "
                f"(<Asset Location><Object Type>), the corrected Group should be '{expected_group}', "
                f"not '{group}'"
            ),
            evidence_source=(
                "Bokor Task List Group.xlsx (Functional Location); BOKOR_10years Work Order Data_Aug26.xlsx; "
                "Equipment Listing_SKA_18June26.xlsx (agent_a); UDMS.pdf §9.4; §4.12 Figure 5"
            ),
        )

    candidate_parts = []
    if location_candidate is not None:
        candidate_parts.append(location_candidate)
    elif location_status == "SHARED_REVIEW":
        candidate_parts.append("/".join(sorted(location_prefixes)))
    else:
        candidate_parts.append("?")
    candidate_parts.append(object_code if object_code is not None else "?")
    candidate_group = "".join(candidate_parts)

    location_note = {
        "VERIFIED": f"Asset Location verified as '{location_candidate}'",
        "SHARED_REVIEW": (
            f"Asset Location shows multiple linked platform prefixes ({', '.join(sorted(location_prefixes))}) "
            "— this Task List may be deliberately shared field-wide, but no data available to this "
            "project distinguishes that from any other cause; ownership cannot be verified"
        ),
        "NO_EVIDENCE": "no linked Functional Location evidence available to establish Asset Location",
    }[location_status]

    return Finding(
        pain_point="PP1",
        record_key=f"{group}-{group_counter}",
        field_name="Group",
        current_value=group,
        recommended_value=None,
        confidence=None,
        detection_confidence=0.55,
        reason=(
            f"{location_note}. {object_evidence}. Provisional candidate Group '{candidate_group}' — "
            "SME review required before any correction is proposed"
        ),
        evidence_source=(
            "PROVISIONAL_SME_REVIEW — Bokor Task List Group.xlsx (Functional Location); "
            "BOKOR_10years Work Order Data_Aug26.xlsx; Equipment Listing_SKA_18June26.xlsx (agent_a); "
            "UDMS.pdf §9.4"
        ),
        candidate_value=candidate_group,
    )


_TRAILING_DIGITS_RE = re.compile(r"^(.+?)(\d+)$")


def build_equipment_class_lookup(equipment_class_master: pd.DataFrame) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for r in equipment_class_master.to_dict("records"):
        status = _none_if_na(r.get("Status"))
        klass = _none_if_na(r.get("Class"))
        if klass is None or status is None:
            continue
        try:
            if int(status) != 1:
                continue
        except (TypeError, ValueError):
            continue
        code = str(klass).strip()
        if not code:
            continue
        lookup[code] = {
            "level": _none_if_na(r.get("Level")),
            "description": _none_if_na(r.get("Class Description")),
        }
    return lookup


_LEVEL_1_FAMILY_CODES = ("ZA", "C", "E", "I", "M", "S", "T")


def _top_level_family(class_code: str) -> str | None:
    for family in _LEVEL_1_FAMILY_CODES:
        if class_code.startswith(family):
            return family
    return None


def detect_group_naming_method(
    group: str, equipment_class_lookup: dict[str, dict]
) -> tuple[str, str | None]:
    if len(group) <= 4:
        return "METHOD_1", None
    remainder = group[4:]
    if remainder in equipment_class_lookup:
        return "METHOD_2", remainder
    m = _TRAILING_DIGITS_RE.match(remainder)
    if m:
        stripped = m.group(1)
        if stripped in equipment_class_lookup:
            return "METHOD_2", stripped
    return "METHOD_1", None


def resolve_equipment_class_from_catalog_profile(
    catalog_profile: str | None, equipment_class_lookup: dict[str, dict]
) -> tuple[str, str | None]:
    if catalog_profile is None:
        return "UNRESOLVED", None
    cp = str(catalog_profile).strip()
    if not cp:
        return "UNRESOLVED", None
    if re.match(r"^0[A-Za-z]-", cp):
        return "NON_STANDARD_SCHEME", None
    if cp[0].isdigit():
        stripped = cp[1:]
        if stripped in equipment_class_lookup:
            return "RESOLVED", stripped
    return "UNRESOLVED", None


_LEGACY_SEQUENCE_RE = re.compile(r"^[A-Z0-9]{4}[0-9]+$")  # e.g. "BODA003", "BOKA094" — plain platform+digits


def classify_group_naming_convention(
    group: str, equipment_class_lookup: dict[str, dict]
) -> tuple[str, str | None]:
    if _LEGACY_SEQUENCE_RE.match(group):
        return "METHOD_1_LEGACY", None
    method, code = detect_group_naming_method(group, equipment_class_lookup)
    if method == "METHOD_2":
        return "METHOD_2", code
    return "NAMING_CONVENTION_REVIEW", None


_INACTIVE_EQUIPMENT_STATUSES = {"INAC INST"}
_INACTIVE_FLOC_STATUSES = {"INAC"}


def _pp1_kg_resolve_equipment_and_platform(
    linked_records: list[dict],
    equipment_class_lookup: dict[str, dict],
    platform_codes: list[str],
) -> dict:
    active = [
        r for r in linked_records
        if r.get("equipment_system_status") not in _INACTIVE_EQUIPMENT_STATUSES
        and r.get("floc_system_status") not in _INACTIVE_FLOC_STATUSES
    ]
    excluded_count = len(linked_records) - len(active)

    # Raw status values are surfaced to the client as-is (PP1_Equipment_Status /
    # PP1_FLOC_Status columns) so PCSB can filter by whatever status combination
    # they want, rather than relying only on this function's active/inactive call.
    # _none_if_na is required here: a missing status arrives from pandas as a
    # float NaN, not None, which "is not None" would silently let through.
    equipment_statuses = sorted({
        s for r in linked_records
        if (s := _none_if_na(r.get("equipment_system_status"))) is not None
    })
    floc_statuses = sorted({
        s for r in linked_records
        if (s := _none_if_na(r.get("floc_system_status"))) is not None
    })

    resolved_classes: dict[str, str] = {}  # equipment_id -> resolved class code
    unresolved_equipment: list[str] = []
    non_standard_equipment: list[str] = []
    equipment_evidence: list[dict] = []  # real per-Equipment evidence for Reason/Evidence text
    platform_prefixes: set[str] = set()
    no_equipment_count = 0

    for r in active:
        equipment_id = _none_if_na(r.get("equipment_id"))
        catalog_profile = _none_if_na(r.get("catalog_profile"))
        floc_key = _none_if_na(r.get("floc_natural_key"))
        platform_prefix = _none_if_na(r.get("platform_prefix"))

        if equipment_id is None:
            no_equipment_count += 1
        else:
            status, class_code = resolve_equipment_class_from_catalog_profile(catalog_profile, equipment_class_lookup)
            if status == "RESOLVED":
                resolved_classes[equipment_id] = class_code
                equipment_evidence.append({
                    "equipment_id": equipment_id, "catalog_profile": catalog_profile,
                    "resolved_class": class_code,
                    "class_description": equipment_class_lookup.get(class_code, {}).get("description"),
                    "floc": floc_key,
                })
            elif status == "NON_STANDARD_SCHEME":
                non_standard_equipment.append(equipment_id)
                equipment_evidence.append({
                    "equipment_id": equipment_id, "catalog_profile": catalog_profile,
                    "resolved_class": None, "class_description": None, "floc": floc_key,
                })
            else:
                unresolved_equipment.append(equipment_id)
                equipment_evidence.append({
                    "equipment_id": equipment_id, "catalog_profile": catalog_profile,
                    "resolved_class": None, "class_description": None, "floc": floc_key,
                })

        if platform_prefix is not None and platform_prefix in platform_codes:
            platform_prefixes.add(platform_prefix)

    distinct_classes = set(resolved_classes.values())

    return {
        "total_linked": len(linked_records),
        "excluded_inactive_count": excluded_count,
        "active_count": len(active),
        "no_equipment_count": no_equipment_count,
        "resolved_classes_by_equipment": resolved_classes,
        "distinct_classes": distinct_classes,
        "unresolved_equipment": unresolved_equipment,
        "non_standard_equipment": non_standard_equipment,
        "equipment_evidence": equipment_evidence,
        "platform_prefixes": platform_prefixes,
        "equipment_statuses": equipment_statuses,
        "floc_statuses": floc_statuses,
    }


def _pp1_kg_naming_check(
    task_list_key: str,
    linked_records: list[dict],
    equipment_class_lookup: dict[str, dict],
    platform_codes: list[str],
    high_confidence: float,
    medium_confidence: float,
    review_confidence: float,
) -> Finding:
    group, _, group_counter = task_list_key.rpartition("-")
    record_key = task_list_key

    def _no_finding(equipment_status: str | None = None, floc_status: str | None = None) -> Finding:
        return Finding(
            pain_point="PP1", record_key=record_key, field_name="Group",
            current_value=group, recommended_value=None, confidence=None,
            detection_confidence=None, reason="Current Group name already matches its applicable naming convention — no finding.",
            evidence_source="Knowledge Graph (live): MaintenanceItem -> USES_TASK_LIST -> TaskList; FOR_EQUIPMENT/FOR_FUNCTIONAL_LOCATION; Equipment Class Master",
            pp1_flag=None,
            pp1_equipment_status=equipment_status,
            pp1_floc_status=floc_status,
        )

    def _review(
        flag: str, reason: str, evidence: str, detection_confidence: float = review_confidence,
        equipment_status: str | None = None, floc_status: str | None = None,
    ) -> Finding:
        return Finding(
            pain_point="PP1", record_key=record_key, field_name="Group",
            current_value=group, recommended_value=None, confidence=None,
            detection_confidence=detection_confidence, reason=reason, evidence_source=evidence,
            pp1_flag=flag,
            pp1_equipment_status=equipment_status,
            pp1_floc_status=floc_status,
        )

    # Step 2 — detect naming convention from NAME STRUCTURE alone.
    convention, remainder_code = classify_group_naming_convention(group, equipment_class_lookup)
    if convention == "METHOD_1_LEGACY":
        return _no_finding()
    if convention == "NAMING_CONVENTION_REVIEW":
        return _review(
            "NAMING_CONVENTION_REVIEW",
            (
                f"Group '{group}' does not resolve to either the TA Planning Norm/Job Library convention "
                "(remainder after the 4-char platform prefix is not a real, Status=1 Equipment Class code, "
                "even after stripping a trailing Counter-style digit suffix) or a plain legacy platform+digits "
                "sequence name — no real KG field distinguishes which PCSB naming convention applies here "
                "(TaskList.tltype/strategy confirmed populated on only 3/1 of 951 real TaskList nodes, not "
                "usable as a discriminator), so this Group's naming convention cannot be determined without "
                "guessing"
            ),
            "Knowledge Graph (live): TaskList.natural_key; Equipment Class Master (Status=1 codes)",
        )

    if not linked_records:
        return _review(
            "EQUIPMENT_CLASS_UNRESOLVED",
            (
                f"Group '{group}' follows the TA Planning Norm/Job Library convention (remainder "
                f"'{remainder_code}' is a real Equipment Class code, "
                f"'{equipment_class_lookup.get(remainder_code, {}).get('description')}'), but no "
                "MaintenanceItem currently uses this Task List (no USES_TASK_LIST edge found) — no linked "
                "Equipment to verify against"
            ),
            "Knowledge Graph (live): MaintenanceItem -> USES_TASK_LIST -> TaskList (no linked MaintenanceItem found)",
        )

    resolution = _pp1_kg_resolve_equipment_and_platform(linked_records, equipment_class_lookup, platform_codes)
    equipment_status_text = ", ".join(resolution["equipment_statuses"]) or None
    floc_status_text = ", ".join(resolution["floc_statuses"]) or None

    if resolution["active_count"] == 0:
        return _review(
            "EQUIPMENT_CLASS_UNRESOLVED",
            (
                f"Group '{group}' follows the TA Planning Norm/Job Library convention (remainder "
                f"'{remainder_code}' is a real Equipment Class code), but every one of its "
                f"{resolution['total_linked']} linked MaintenanceItem(s) points to Equipment/Functional "
                "Location(s) that are all inactive (real system_status 'INAC'/'INAC INST' — this KG's "
                "equivalent of a deleted technical object) — nothing current to verify against"
            ),
            "Knowledge Graph (live): Equipment.system_status / FunctionalLocation.system_status (all inactive)",
            equipment_status=equipment_status_text, floc_status=floc_status_text,
        )

    equipment_ids = [e["equipment_id"] for e in resolution["equipment_evidence"]]
    evidence_source = (
        "Knowledge Graph (live): MaintenanceItem -> FOR_EQUIPMENT/FOR_FUNCTIONAL_LOCATION -> "
        "Equipment/FunctionalLocation; Equipment.catalog_profile; Equipment_Class_Master.xlsx (Status=1)"
    )

    # Step 6/5 — class resolution must be unambiguous and Status=1-valid.
    distinct_classes = resolution["distinct_classes"]
    if not distinct_classes:
        non_standard = resolution["non_standard_equipment"]
        unresolved = resolution["unresolved_equipment"]
        detail_parts = []
        if non_standard:
            detail_parts.append(
                f"{len(non_standard)} equipment ({', '.join(non_standard)}) use the non-standard Catalog "
                "Profile scheme (leading '0' + hyphenated free text) that never maps to the Equipment Class master"
            )
        if unresolved:
            detail_parts.append(
                f"{len(unresolved)} equipment ({', '.join(unresolved)}) have a Catalog Profile that does not "
                "resolve to any real, Status=1 Equipment Class code"
            )
        if resolution["no_equipment_count"]:
            detail_parts.append(
                f"{resolution['no_equipment_count']} linked MaintenanceItem(s) have no Equipment at all "
                "(Functional-Location-only link)"
            )
        detail = "; ".join(detail_parts) if detail_parts else "no active linked Equipment carries a resolvable Catalog Profile"
        return _review(
            "EQUIPMENT_CLASS_UNRESOLVED",
            (
                f"Group '{group}' follows the TA Planning Norm/Job Library convention (remainder "
                f"'{remainder_code}' is a real Equipment Class code, "
                f"'{equipment_class_lookup.get(remainder_code, {}).get('description')}'), but its "
                f"{resolution['active_count']} currently-active linked Equipment cannot be resolved to any "
                f"real Equipment Class: {detail}"
            ),
            evidence_source,
            equipment_status=equipment_status_text, floc_status=floc_status_text,
        )

    if len(distinct_classes) > 1:
        # Step 7 — NEVER majority-vote, even if one class dominates.
        class_breakdown = ", ".join(
            f"{eq}={cls}" for eq, cls in sorted(resolution["resolved_classes_by_equipment"].items())
        )
        return _review(
            "MULTIPLE_EQUIPMENT_CLASSES_REVIEW",
            (
                f"Group '{group}' has {resolution['active_count']} currently-active linked Equipment that "
                f"resolve to {len(distinct_classes)} DIFFERENT real Equipment Classes ({', '.join(sorted(distinct_classes))}) "
                f"via Catalog Profile — per-Equipment resolution: {class_breakdown} — cannot determine a single "
                "Equipment Class this Group's name should reflect; never majority-voted"
            ),
            evidence_source,
            equipment_status=equipment_status_text, floc_status=floc_status_text,
        )

    (resolved_class,) = distinct_classes
    resolved_desc = equipment_class_lookup.get(resolved_class, {}).get("description", resolved_class)

    platform_prefixes = resolution["platform_prefixes"]
    equipment_list_text = ", ".join(
        f"{e['equipment_id']} (Catalog Profile '{e['catalog_profile']}' -> Class '{e['resolved_class']}', FLOC '{e['floc']}')"
        for e in resolution["equipment_evidence"] if e["resolved_class"] is not None
    )
    if len(platform_prefixes) == 0:
        return _review(
            "NAMING_CONVENTION_REVIEW",
            (
                f"Group '{group}' resolves to a single Equipment Class ('{resolved_class}', '{resolved_desc}') "
                f"from its linked Equipment ({equipment_list_text}), but none of its linked Functional "
                "Location(s) resolve to a recognised platform code in config/platform_code_prefixes.yaml — "
                "platform cannot be established, so a corrected Group cannot be constructed"
            ),
            evidence_source,
            equipment_status=equipment_status_text, floc_status=floc_status_text,
        )
    if len(platform_prefixes) > 1:
        return _review(
            "NAMING_CONVENTION_REVIEW",
            (
                f"Group '{group}' resolves to a single Equipment Class ('{resolved_class}', '{resolved_desc}') "
                f"from its linked Equipment ({equipment_list_text}), but its linked Functional Location(s) span "
                f"{len(platform_prefixes)} DIFFERENT approved platform codes ({', '.join(sorted(platform_prefixes))}) "
                "— platform ownership is genuinely ambiguous from current data; never arbitrarily chosen"
            ),
            evidence_source,
            equipment_status=equipment_status_text, floc_status=floc_status_text,
        )

    (resolved_platform,) = platform_prefixes
    current_prefix = group[:4]
    prefix_ok = current_prefix == resolved_platform
    class_ok = remainder_code == resolved_class

    if prefix_ok and class_ok:
        return _no_finding(equipment_status=equipment_status_text, floc_status=floc_status_text)

    expected_group = f"{resolved_platform}{resolved_class}"
    if prefix_ok and not class_ok:
        flag = "EQUIPMENT_CLASS_MISMATCH"
        headline = (
            f"Group '{group}' names itself after Equipment Class '{remainder_code}' "
            f"('{equipment_class_lookup.get(remainder_code, {}).get('description')}'), but its "
            f"{resolution['active_count']} currently-active linked Equipment ({equipment_list_text}) all "
            f"resolve via Catalog Profile to Equipment Class '{resolved_class}' ('{resolved_desc}') instead — "
            "platform prefix is correct, Equipment Class is wrong"
        )
    elif class_ok and not prefix_ok:
        flag = "PREFIX_MISMATCH"
        headline = (
            f"Group '{group}' correctly names Equipment Class '{resolved_class}' ('{resolved_desc}'), but its "
            f"{resolution['active_count']} currently-active linked Equipment ({equipment_list_text}) resolve, "
            f"via their Functional Location(s), to platform '{resolved_platform}' — not the Group's own prefix "
            f"'{current_prefix}' — Equipment Class is correct, platform prefix is wrong"
        )
    else:
        flag = "NAMING_MISMATCH"
        headline = (
            f"Group '{group}' (prefix '{current_prefix}', Equipment Class '{remainder_code}') matches neither "
            f"the resolved platform '{resolved_platform}' nor the resolved Equipment Class '{resolved_class}' "
            f"('{resolved_desc}') of its {resolution['active_count']} currently-active linked Equipment "
            f"({equipment_list_text}) — both prefix and Equipment Class are wrong"
        )

    return Finding(
        pain_point="PP1", record_key=record_key, field_name="Group",
        current_value=group, recommended_value=expected_group,
        confidence=confidence_label(high_confidence),
        detection_confidence=high_confidence,
        reason=f"{headline}. Per UDMS §9.4 (<Asset Location><Equipment Class>), the corrected Group should be '{expected_group}'.",
        evidence_source=evidence_source,
        pp1_flag=flag,
        pp1_equipment_status=equipment_status_text,
        pp1_floc_status=floc_status_text,
    )


def run_pp1_kg_naming_check(
    task_list_group: pd.DataFrame,
    pp1_task_list_equipment: dict[str, list[dict]],
    equipment_class_master: pd.DataFrame,
    platform_codes: list[str],
    batch_size: int = DEFAULT_BATCH_SIZE,
    high_confidence: float = 0.9,
    medium_confidence: float = 0.65,
    review_confidence: float = 0.55,
) -> dict[str, Finding]:
    equipment_class_lookup = build_equipment_class_lookup(equipment_class_master)

    bridge_keys = task_list_group[["Group", "Group Counter"]].dropna().astype(str).drop_duplicates()
    total_keys = len(bridge_keys)
    logger.info(f"PP1: KG-native naming/Equipment-Class check, {total_keys} distinct Task List Groups")

    findings_by_key: dict[str, Finding] = {}
    processed = 0
    for batch in batched(bridge_keys.to_dict("records"), batch_size):
        for row in batch:
            group, group_counter = row["Group"], row["Group Counter"]
            task_list_key = f"{group}-{group_counter}"
            linked_records = pp1_task_list_equipment.get(task_list_key, [])
            finding = _pp1_kg_naming_check(
                task_list_key, linked_records, equipment_class_lookup, platform_codes,
                high_confidence, medium_confidence, review_confidence,
            )
            findings_by_key[task_list_key] = finding
        processed += len(batch)
        logger.info(f"PP1: KG-native check, processed {processed}/{total_keys} Task List Groups")
    logger.info(f"PP1: KG-native check done, {len(findings_by_key)} Task Lists evaluated")
    return findings_by_key


def _pp1_equipment_class_check(
    group: str,
    group_counter: str,
    remainder_code: str,
    equipment_class_lookup: dict[str, dict],
    linked_equipment: list[str],
    equipment_catalog_profile: dict[str, str | None],
    high_confidence: float,
    family_match_confidence: float,
    non_standard_scheme_confidence: float,
) -> Finding | None:
    if not linked_equipment:
        return Finding(
            pain_point="PP1",
            record_key=f"{group}-{group_counter}",
            field_name="Group",
            current_value=group,
            recommended_value=None,
            confidence=None,
            detection_confidence=0.3,
            reason=(
                f"Group '{group}' follows the TA Planning Norm convention (remainder '{remainder_code}' "
                f"is a real Equipment Class code, '{equipment_class_lookup[remainder_code]['description']}'), "
                "but this row has no linked Equipment in Bokor Task List Group.xlsx — no linked "
                "Equipment to verify against"
            ),
            evidence_source="Bokor Task List Group.xlsx (Equipment blank); Equipment Class.xlsx",
        )

    resolved_classes: set[str] = set()
    non_standard_count = 0
    unresolved_count = 0
    for equipment in linked_equipment:
        catalog_profile = equipment_catalog_profile.get(equipment)
        status, class_code = resolve_equipment_class_from_catalog_profile(catalog_profile, equipment_class_lookup)
        if status == "RESOLVED":
            resolved_classes.add(class_code)
        elif status == "NON_STANDARD_SCHEME":
            non_standard_count += 1
        else:
            unresolved_count += 1

    if not resolved_classes:
        if non_standard_count > 0:
            return Finding(
                pain_point="PP1",
                record_key=f"{group}-{group_counter}",
                field_name="Group",
                current_value=group,
                recommended_value=None,
                confidence=None,
                detection_confidence=non_standard_scheme_confidence,
                reason=(
                    f"Group '{group}' follows the TA Planning Norm convention (remainder '{remainder_code}' "
                    f"is a real Equipment Class code, '{equipment_class_lookup[remainder_code]['description']}'), "
                    f"but its linked Equipment ({', '.join(linked_equipment)}) uses the non-standard "
                    "Catalog Profile scheme (leading '0' + hyphenated free text, e.g. '0I-INSTRL') that "
                    "does not map to the Equipment Class master at all — cannot resolve via Equipment "
                    "Class, not a mismatch"
                ),
                evidence_source=(
                    "Bokor Task List Group.xlsx (Equipment); "
                    "Bokor EQ list all - 28.09.2026.xlsx (Catalog Profile, non-standard scheme); "
                    "Equipment Class.xlsx"
                ),
            )
        return Finding(
            pain_point="PP1",
            record_key=f"{group}-{group_counter}",
            field_name="Group",
            current_value=group,
            recommended_value=None,
            confidence=None,
            detection_confidence=0.4,
            reason=(
                f"Group '{group}' follows the TA Planning Norm convention (remainder '{remainder_code}' "
                f"is a real Equipment Class code, '{equipment_class_lookup[remainder_code]['description']}'), "
                f"but its linked Equipment ({', '.join(linked_equipment)}) has no Catalog Profile that "
                "resolves to any real Equipment Class code — cannot resolve, never guessed"
            ),
            evidence_source=(
                "Bokor Task List Group.xlsx (Equipment); "
                "Bokor EQ list all - 28.09.2026.xlsx (Catalog Profile); Equipment Class.xlsx"
            ),
        )

    if len(resolved_classes) > 1:
        return Finding(
            pain_point="PP1",
            record_key=f"{group}-{group_counter}",
            field_name="Group",
            current_value=group,
            recommended_value=None,
            confidence=None,
            detection_confidence=0.4,
            reason=(
                f"Group '{group}' follows the TA Planning Norm convention (remainder '{remainder_code}' "
                f"is a real Equipment Class code, '{equipment_class_lookup[remainder_code]['description']}'), "
                f"but its linked Equipment resolve to multiple DIFFERENT Equipment Classes "
                f"({', '.join(sorted(resolved_classes))}) — cannot verify which one the Group name "
                "should reflect, never guessed"
            ),
            evidence_source=(
                "Bokor Task List Group.xlsx (Equipment); "
                "Bokor EQ list all - 28.09.2026.xlsx (Catalog Profile); Equipment Class.xlsx"
            ),
        )

    (resolved_class,) = resolved_classes
    if resolved_class == remainder_code:
        return None  # already compliant — the real Equipment Class agrees with the Group's naming

    resolved_family = _top_level_family(resolved_class)
    remainder_family = _top_level_family(remainder_code)
    same_family = (
        resolved_family is not None and remainder_family is not None and resolved_family == remainder_family
    )
    resolved_desc = equipment_class_lookup.get(resolved_class, {}).get("description", resolved_class)
    remainder_desc = equipment_class_lookup.get(remainder_code, {}).get("description", remainder_code)

    if same_family:
        return Finding(
            pain_point="PP1",
            record_key=f"{group}-{group_counter}",
            field_name="Group",
            current_value=group,
            recommended_value=f"{group[:4]}{resolved_class}",
            confidence=confidence_label(family_match_confidence),
            reason=(
                f"Group '{group}' names itself after Equipment Class '{remainder_code}' "
                f"('{remainder_desc}'), but its linked Equipment ({', '.join(linked_equipment)}) "
                f"resolves via Catalog Profile to Equipment Class '{resolved_class}' ('{resolved_desc}') "
                f"— same top-level family ('{resolved_family}') but a different leaf class; Group name "
                "may be using a related but imprecise class code"
            ),
            evidence_source=(
                "Bokor Task List Group.xlsx (Equipment); "
                "Bokor EQ list all - 28.09.2026.xlsx (Catalog Profile); Equipment Class.xlsx"
            ),
        )

    return Finding(
        pain_point="PP1",
        record_key=f"{group}-{group_counter}",
        field_name="Group",
        current_value=group,
        recommended_value=f"{group[:4]}{resolved_class}",
        confidence=confidence_label(high_confidence),
        reason=(
            f"Group '{group}' names itself after Equipment Class '{remainder_code}' ('{remainder_desc}'), "
            f"but its linked Equipment ({', '.join(linked_equipment)}) resolves via Catalog Profile to "
            f"Equipment Class '{resolved_class}' ('{resolved_desc}') — a DIFFERENT top-level family "
            f"('{remainder_family}' vs '{resolved_family}'), a high-confidence naming/Equipment mismatch"
        ),
        evidence_source=(
            "Bokor Task List Group.xlsx (Equipment); "
            "Bokor EQ list all - 28.09.2026.xlsx (Catalog Profile); Equipment Class.xlsx"
        ),
    )


def run_pp1_equipment_class_check(
    task_list_group: pd.DataFrame,
    equipment_class_master: pd.DataFrame,
    equipment_extract: pd.DataFrame,
    batch_size: int = DEFAULT_BATCH_SIZE,
    high_confidence: float = 0.9,
    family_match_confidence: float = 0.6,
    non_standard_scheme_confidence: float = 0.5,
) -> list[Finding]:
    equipment_class_lookup = build_equipment_class_lookup(equipment_class_master)

    equipment_catalog_profile: dict[str, str | None] = {}
    for r in equipment_extract.dropna(subset=["Equipment"]).to_dict("records"):
        equipment_catalog_profile[str(r["Equipment"])] = _none_if_na(r.get("Catalog Profile"))

    equipment_by_key: dict[tuple[str, str], list[str]] = {}
    for r in task_list_group.dropna(subset=["Group", "Group Counter"]).to_dict("records"):
        equipment = _none_if_na(r.get("Equipment"))
        key = (str(r["Group"]), str(r["Group Counter"]))
        equipment_by_key.setdefault(key, [])
        if equipment is not None:
            equipment_by_key[key].append(str(equipment))

    bridge_keys = task_list_group[["Group", "Group Counter"]].dropna().astype(str).drop_duplicates()
    total_keys = len(bridge_keys)
    logger.info(f"PP1: Check E (Equipment Class naming), {total_keys} distinct Task List Groups")

    findings: list[Finding] = []
    processed = 0
    for batch in batched(bridge_keys.to_dict("records"), batch_size):
        for row in batch:
            group, group_counter = row["Group"], row["Group Counter"]
            method, remainder_code = detect_group_naming_method(group, equipment_class_lookup)
            if method != "METHOD_2":
                continue
            key = (group, group_counter)
            linked_equipment = equipment_by_key.get(key, [])
            finding = _pp1_equipment_class_check(
                group, group_counter, remainder_code, equipment_class_lookup,
                linked_equipment, equipment_catalog_profile,
                high_confidence, family_match_confidence, non_standard_scheme_confidence,
            )
            if finding is not None:
                findings.append(finding)
        processed += len(batch)
        logger.info(f"PP1: Check E, processed {processed}/{total_keys} Task List Groups")
    logger.info(f"PP1: Check E done, {len(findings)} findings")
    return findings


def run_pp1(
    task_list_group: pd.DataFrame,
    platform_codes: list[str],
    reuse_threshold: int = DEFAULT_REUSE_THRESHOLD,
    batch_size: int = DEFAULT_BATCH_SIZE,
    work_order_history: pd.DataFrame | None = None,
    agent_a_equipment: pd.DataFrame | None = None,
    historical_usage_confidence: float = 0.85,
    sce_naming_confidence: float = 0.65,
    inconsistent_applicability_confidence: float = 0.60,
    equipment_class_master: pd.DataFrame | None = None,
    equipment_extract: pd.DataFrame | None = None,
    equipment_class_high_confidence: float = 0.9,
    equipment_class_family_match_confidence: float = 0.6,
    equipment_class_non_standard_scheme_confidence: float = 0.5,
    pp1_task_list_equipment: dict[str, list[dict]] | None = None,
    pp1_kg_medium_confidence: float = 0.65,
    pp1_kg_review_confidence: float = 0.55,
    pp1_historical_review_confidence: float = 0.35,
) -> list[Finding]:
    findings: list[Finding] = []

    check_c_by_key: dict[tuple[str, str] | None, Finding] = {}
    if work_order_history is not None and agent_a_equipment is not None:
        wo_equipment_by_key, equipment_to_description = _build_wo_equipment_and_description_lookups(
            work_order_history, agent_a_equipment
        )
        bridge_keys = task_list_group[["Group", "Group Counter"]].dropna().astype(str).drop_duplicates()
        total_keys = len(bridge_keys)
        logger.info(f"PP1: Check C (historical usage), {total_keys} distinct Task Lists")
        processed = 0
        for batch in batched(bridge_keys.to_dict("records"), batch_size):
            for row in batch:
                key = (row["Group"], row["Group Counter"])
                finding = _pp1_historical_usage_check(
                    key[0], key[1], wo_equipment_by_key, equipment_to_description,
                    historical_usage_confidence,
                    inconsistent_applicability_confidence=inconsistent_applicability_confidence,
                    task_list_group=task_list_group,
                    platform_codes=platform_codes,
                )
                if finding is not None:
                    check_c_by_key[key] = finding
            processed += len(batch)
            logger.info(f"PP1: Check C, processed {processed}/{total_keys} Task Lists")
        logger.info(f"PP1: Check C evidence ready, {len(check_c_by_key)} keys with Object Type evidence")

    rows = task_list_group.to_dict("records")
    total = len(rows)
    logger.info(f"PP1: starting, {total} rows in {(total + batch_size - 1) // batch_size} batches")
    processed = 0
    for batch in batched(rows, batch_size):
        for row in batch:
            group = _none_if_na(row["Group"])
            if group is None:
                findings.append(
                    Finding(
                        pain_point="PP1",
                        record_key=str(row["Maintenance Item"]),
                        field_name="Group",
                        current_value=None,
                        recommended_value=None,
                        confidence=None,
                        detection_confidence=0.5,
                        reason=(
                            f"Maintenance Item '{row['Maintenance Item']}' has no Group/Task List "
                            "reference at all — there is no Group naming convention to validate "
                            "until this Item is linked to a Task List"
                        ),
                        evidence_source="Knowledge Graph (live): MaintenanceItem has no USES_TASK_LIST edge",
                    )
                )
        processed += len(batch)
        logger.info(f"PP1: processed {processed}/{total} rows, {len(findings)} findings so far")

    kg_native_by_key: dict[str, Finding] = {}
    if equipment_class_master is not None and pp1_task_list_equipment is not None:
        kg_native_by_key = run_pp1_kg_naming_check(
            task_list_group, pp1_task_list_equipment, equipment_class_master, platform_codes,
            batch_size=batch_size,
            high_confidence=equipment_class_high_confidence,
            medium_confidence=pp1_kg_medium_confidence,
            review_confidence=pp1_kg_review_confidence,
        )
        logger.info(f"PP1: KG-native check contributed {len(kg_native_by_key)} findings")

    for key, evidence in check_c_by_key.items():
        joined_key = f"{key[0]}-{key[1]}"
        kg_finding = kg_native_by_key.get(joined_key)

        if kg_finding is not None and (kg_finding.pp1_flag is None or kg_finding.recommended_value is not None):
            continue

        if kg_finding is not None:
            kg_native_by_key[joined_key] = Finding(
                pain_point="PP1",
                record_key=kg_finding.record_key,
                field_name=kg_finding.field_name,
                current_value=kg_finding.current_value,
                recommended_value=None,
                confidence=None,
                detection_confidence=kg_finding.detection_confidence,
                reason=(
                    f"{kg_finding.reason} Supporting 10-year historical evidence (LOW confidence, "
                    f"never overriding this review flag): {evidence.reason}"
                ),
                evidence_source=f"{kg_finding.evidence_source}; {evidence.evidence_source}",
                pp1_flag=kg_finding.pp1_flag,
            )
            continue

        findings.append(
            Finding(
                pain_point="PP1",
                record_key=evidence.record_key,
                field_name=evidence.field_name,
                current_value=evidence.current_value,
                recommended_value=None,
                confidence=None,
                detection_confidence=min(
                    evidence.detection_confidence if evidence.detection_confidence is not None else pp1_historical_review_confidence,
                    pp1_historical_review_confidence,
                ),
                reason=(
                    f"{evidence.reason} (10-year Work Order history only — the KG-native current-data "
                    "check did not run for this Task List, so this is supporting evidence only, LOW "
                    "confidence, with no Group suggestion of its own)"
                ),
                evidence_source=evidence.evidence_source,
                pp1_flag=None,
            )
        )

    findings += list(kg_native_by_key.values())
    logger.info(f"PP1: done, {len(findings)} findings")

    if work_order_history is not None and "SCE FL" in work_order_history.columns:
        sce_rows = work_order_history.dropna(subset=["SCE FL", "Group", "Group Counter"])[
            ["Group", "Group Counter", "SCE FL"]
        ].drop_duplicates()
        logger.info(f"PP1: Check D (SCE naming), {sce_rows.shape[0]} rows")
        processed = 0
        for batch in batched(sce_rows.to_dict("records"), batch_size):
            for r in batch:
                group = str(r["Group"])
                group_counter = str(r["Group Counter"])
                floc = r["SCE FL"]
                findings.append(
                    Finding(
                        pain_point="PP1",
                        record_key=f"{group}-{group_counter}",
                        field_name="Group",
                        current_value=group,
                        recommended_value=None,
                        confidence=None,
                        detection_confidence=sce_naming_confidence,
                        reason=(
                            f"Task List '{group}' is linked to Functional Location '{floc}', "
                            "flagged SCE (Safety Critical Element) in BOKOR_10years Work Order Data; "
                            "per UDMS §9.4 ('For SCE, the following similar rule shall be applied'), "
                            "this Group should follow the SCE <Asset Location><SCE Group> naming "
                            "branch, not the general Object Type one — but no SCE Group master/lookup "
                            "table exists in any file available to this project, so the exact "
                            "corrected code cannot be constructed or verified"
                        ),
                        evidence_source="BOKOR_10years Work Order Data_Aug26.xlsx (SCE FL); UDMS.pdf §9.4 (SCE naming branch, page 61)",
                    )
                )
            processed += len(batch)
            logger.info(f"PP1: Check D, processed {processed}/{sce_rows.shape[0]} rows")
        logger.info(f"PP1: Check D done, {len(findings)} total findings so far")


    return findings


def pp2_operation_key_suffix(opdesc: str | None) -> str:
    import hashlib

    import pandas as pd

    if opdesc is None or (isinstance(opdesc, float) and pd.isna(opdesc)):
        return ""
    text = str(opdesc).strip()
    if not text:
        return ""
    return "-" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def _pp2_consolidate_operations(normalized_operations: pd.DataFrame) -> pd.DataFrame:
    df = normalized_operations.copy()
    df["TLSUBOPNO"] = df["TLSUBOPNO"].astype(str)
    df["_OPDESC_KEY"] = df["OPDESC"].fillna("")
    df = df.sort_values(["TLGRP", "TLGRPCOUNT", "TLOPNO", "TLSUBOPNO"], kind="stable")
    agg_spec = {
        "OPDESC": ("OPDESC", "first"),
        "LONGTEXT_CONSOLIDATED": ("LONGTEXT_AGGREGATED", lambda s: "\n".join(v for v in s if v)),
        "OPWKCEN": ("OPWKCEN", "first"),
        "STRATEGY": ("STRATEGY", "first"),
        "PLANT": ("PLANT", "first"),
        "SUB_OPERATION_COUNT": ("TLSUBOPNO", "size"),
    }
    if "FREQUENCY" in df.columns:
        agg_spec["FREQUENCY"] = ("FREQUENCY", "first")
    grouped = df.groupby(["TLGRP", "TLGRPCOUNT", "TLOPNO", "_OPDESC_KEY"], as_index=False, sort=False).agg(**agg_spec)
    grouped = grouped.drop(columns=["_OPDESC_KEY"])
    grouped["OPERATION_KEY_SUFFIX"] = grouped["OPDESC"].apply(pp2_operation_key_suffix)
    return grouped


def _pp2_bokor_work_centres(work_centre_families: dict) -> dict[str, str]:
    bos = work_centre_families.get("BOS", {})
    discipline_map = dict(bos.get("discipline_work_centres", {}))
    discipline_map.setdefault("MULTI", "BMULTI")
    return discipline_map


_PP2_DISCIPLINE_LABELS = {
    "MECH": "Mechanical", "ELEC": "Electrical", "INST": "Instrument",
    "PROD": "Operations/Production support", "MATCO": "Material coordination",
    "MULTI": "multi-skill — genuinely combines more than one discipline",
}


_PP2_PROMPT_VERSION = "v2-batch"


def _pp2_normalize_text(opdesc: str | None, longtext: str | None) -> str:
    combined = f"{opdesc or ''}\n{longtext or ''}"
    return " ".join(combined.split())


def _pp2_classification_schema_version(valid_disciplines: list[str]) -> str:
    return ",".join(sorted(valid_disciplines))


def _pp2_cache_key(normalized_text: str, classification_schema_version: str) -> str:
    digest_input = f"{_PP2_PROMPT_VERSION}\x00{classification_schema_version}\x00{normalized_text}"
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


_PP2_CACHE_COLUMNS = ["cache_key", "normalized_text", "discipline", "confidence", "basis"]


def _pp2_load_cache(cache_path) -> dict[str, dict]:
    return _load_csv_cache(cache_path)


def _pp2_save_cache(cache_path, cache: dict[str, dict]) -> None:
    _save_csv_cache(cache_path, cache, _PP2_CACHE_COLUMNS)


_PP2_BATCH_PROMPT_HEADER = """You are classifying a batch of {count} distinct SAP PM Task List operations. \
For EACH operation, determine which maintenance discipline(s) it requires, based ONLY on the actual work \
described in that operation's own text — never on the current Work Centre code, the Task List name, or how \
frequently a discipline was historically used. Each operation is completely independent — do not let one \
operation's classification influence another's.

The valid Bokor-region disciplines are: {discipline_menu}. If an operation genuinely combines independent \
work from more than one of these disciplines within the same operation (not just adjacent equipment), \
classify it as MULTI instead of picking one.

Do not classify based on equipment nouns alone (e.g. "pump" does not automatically mean MECH — a pump \
operation that is actually an electrical winding test is ELEC). Base each classification on the actual verbs \
and tasks described in that operation's own text.

Reply UNCLEAR for an operation only if its scope genuinely cannot be determined from the text at all (e.g. \
the text is blank or meaningless) — do not reply UNCLEAR merely because the text is short.

Reply with EXACTLY {count} blocks, one per operation below, in this exact format and nothing else — repeat \
the ID line verbatim so your reply can be matched back to the correct operation:

ID: <the exact ID shown for that operation>
DISCIPLINE: <{reply_options}>
CONFIDENCE: <HIGH|MEDIUM|LOW>
BASIS: <one short sentence citing the specific words/phrases in that operation's own text>

Operations to classify:
"""


def _pp2_batch_prompt(items: list[tuple[str, str]], valid_disciplines: list[str]) -> str:
    discipline_menu = ", ".join(
        f"{code} ({_PP2_DISCIPLINE_LABELS.get(code, code)})" for code in valid_disciplines
    )
    reply_options = "|".join(valid_disciplines + ["UNCLEAR"])
    header = _PP2_BATCH_PROMPT_HEADER.format(
        count=len(items), discipline_menu=discipline_menu, reply_options=reply_options
    )
    blocks = []
    for item_id, operation_text in items:
        blocks.append(f"--- Operation ID: {item_id} ---\n{operation_text or '(blank)'}")
    return header + "\n\n".join(blocks)


def _parse_pp2_batch_reply(reply: str, expected_ids: set[str], valid_disciplines: list[str]) -> dict[str, tuple[str, str, str]]:
    valid_replies = set(valid_disciplines) | {"UNCLEAR"}
    results: dict[str, tuple[str, str, str]] = {}
    current_id = None
    current_discipline = None
    current_confidence = None
    current_basis = None

    def _flush():
        if current_id is not None and current_discipline is not None and current_confidence is not None:
            results[current_id] = (current_discipline, current_confidence, current_basis or "")

    for line in reply.splitlines():
        line = line.strip()
        upper = line.upper()
        if upper.startswith("ID:"):
            _flush()
            current_id = line.split(":", 1)[1].strip()
            current_discipline = None
            current_confidence = None
            current_basis = None
        elif upper.startswith("DISCIPLINE:"):
            value = line.split(":", 1)[1].strip().upper()
            if value in valid_replies:
                current_discipline = value
        elif upper.startswith("CONFIDENCE:"):
            value = line.split(":", 1)[1].strip().upper()
            if value in ("HIGH", "MEDIUM", "LOW"):
                current_confidence = value
        elif upper.startswith("BASIS:"):
            current_basis = line.split(":", 1)[1].strip()
    _flush()
    return {item_id: value for item_id, value in results.items() if item_id in expected_ids}


def _ask_agent_pp2_classify_batch(
    agent_c, items: list[tuple[str, str]], valid_disciplines: list[str], max_retries: int = 2
) -> dict[str, tuple[str, str, str]]:
    remaining = {item_id: (item_id, text) for item_id, text in items}
    results: dict[str, tuple[str, str, str]] = {}

    for attempt in range(max_retries + 1):
        if not remaining:
            break
        batch = list(remaining.values())
        prompt = _pp2_batch_prompt(batch, valid_disciplines)
        try:
            response = agent_c.invoke({"messages": [{"role": "user", "content": prompt}]})
            reply = response["messages"][-1].content.strip()
        except Exception:
            reply = ""
        parsed = _parse_pp2_batch_reply(reply, set(remaining.keys()), valid_disciplines)
        results.update(parsed)
        for item_id in parsed:
            remaining.pop(item_id, None)
        if remaining and attempt < max_retries:
            logger.info(f"PP2: batch retry {attempt + 1}/{max_retries}, {len(remaining)} item(s) missing/malformed")

    for item_id in remaining:
        results[item_id] = ("UNCLEAR", "LOW", "Deep Agent did not return a well-formed classification for this operation after retries")
    return results


def _pp2_finding_for_operation(
    record_key: str, current_value: str | None, has_scope_text: bool,
    discipline: str, agent_confidence: str, basis: str,
    bokor_work_centres: dict[str, str], confidence_scores: dict[str, float],
) -> Finding:
    if not has_scope_text:
        return Finding(
            pain_point="PP2",
            record_key=record_key,
            field_name="OPWKCEN",
            current_value=current_value,
            recommended_value=current_value,
            confidence="Low",
            detection_confidence=0.3,
            reason=(
                "Both Operation Description and Long Text are blank for this operation — "
                "there is no described work scope to classify a discipline from; echoing "
                "back the current Work Centre with low confidence rather than fabricating "
                "a suggestion"
            ),
            evidence_source="Bokor Long Text_Aug26_LATEST.xlsm (OPDESC and LONGTEXT both blank)",
        )

    if discipline == "UNCLEAR":
        return Finding(
            pain_point="PP2",
            record_key=record_key,
            field_name="OPWKCEN",
            current_value=current_value,
            recommended_value=current_value,
            confidence="Low",
            detection_confidence=0.4,
            reason=(
                f"Operation scope could not be confidently classified into a discipline: {basis}. "
                "Echoing back the current Work Centre with low confidence rather than "
                "fabricating a suggestion"
            ),
            evidence_source="Bokor Long Text_Aug26_LATEST.xlsm; Deep Agent semantic classification (UNCLEAR)",
        )

    target_wc = bokor_work_centres.get(discipline)
    confidence_score = confidence_scores.get(agent_confidence, 0.4)

    if target_wc is None:
        return Finding(
            pain_point="PP2",
            record_key=record_key,
            field_name="OPWKCEN",
            current_value=current_value,
            recommended_value=discipline,
            confidence="Low",
            detection_confidence=0.5,
            reason=(
                f"Operation scope indicates '{discipline}' discipline ({basis}), but no "
                "approved Bokor-region Work Centre is confirmed for this discipline in "
                "SKA_MPG_MWC_PMMS.pptx — recommending the discipline only, not a "
                "fabricated Work Centre code"
            ),
            evidence_source="Bokor Long Text_Aug26_LATEST.xlsm; SKA_MPG_MWC_PMMS.pptx (no confirmed mapping for this discipline)",
        )

    multi_note = (
        " This operation genuinely combines independent work from more than one discipline, "
        "so BMULTI (multi-skill) is the correct classification, not an error."
        if discipline == "MULTI" else ""
    )
    return Finding(
        pain_point="PP2",
        record_key=record_key,
        field_name="OPWKCEN",
        current_value=current_value,
        recommended_value=target_wc,
        confidence=confidence_label(confidence_score),
        reason=(
            f"Suggested '{target_wc}' because the operation scope requires '{discipline}' "
            f"discipline: {basis}.{multi_note}"
        ),
        evidence_source="Bokor Long Text_Aug26_LATEST.xlsm; SKA_MPG_MWC_PMMS.pptx; Deep Agent semantic classification of OPDESC+LONGTEXT",
    )


def run_pp2(
    normalized_operations: pd.DataFrame,
    work_centre_families: dict,
    agent_c,
    batch_size: int = DEFAULT_BATCH_SIZE,
    computed_confidence: dict[str, float] | None = None,
    cache_path: str = "ground_truth_cache/PP02_discipline_cache.csv",
    llm_batch_size: int = 15,
) -> list[Finding]:
    confidence_scores = computed_confidence or {"HIGH": 0.9, "MEDIUM": 0.65, "LOW": 0.4}
    bokor_work_centres = _pp2_bokor_work_centres(work_centre_families)
    valid_disciplines = list(bokor_work_centres.keys())

    operations = _pp2_consolidate_operations(normalized_operations)
    total = operations.shape[0]
    logger.info(f"PP2: starting, {total} unique Task List operations")

    rows_by_text: dict[str, list[dict]] = {}
    blank_rows: list[dict] = []
    for row in operations.to_dict("records"):
        opdesc = _none_if_na(row.get("OPDESC")) or ""
        longtext = _none_if_na(row.get("LONGTEXT_CONSOLIDATED")) or ""
        if not opdesc and not longtext:
            blank_rows.append(row)
            continue
        normalized_text = _pp2_normalize_text(opdesc, longtext)
        rows_by_text.setdefault(normalized_text, []).append(row)
    logger.info(
        f"PP2: {len(blank_rows)} operations with no text (skipped — no scope to classify), "
        f"{len(rows_by_text)} distinct non-blank texts across {total - len(blank_rows)} operations"
    )

    schema_version = _pp2_classification_schema_version(valid_disciplines)
    cache = _pp2_load_cache(cache_path)
    classification_by_text: dict[str, tuple[str, str, str]] = {}
    texts_needing_llm: list[str] = []
    for normalized_text in rows_by_text:
        key = _pp2_cache_key(normalized_text, schema_version)
        cached = cache.get(key)
        if cached is not None:
            classification_by_text[normalized_text] = (cached["discipline"], cached["confidence"], cached["basis"])
        else:
            texts_needing_llm.append(normalized_text)
    logger.info(
        f"PP2: {len(rows_by_text) - len(texts_needing_llm)} distinct texts served from cache, "
        f"{len(texts_needing_llm)} need a fresh Deep Agent call"
    )

    processed_texts = 0
    for text_batch in batched(texts_needing_llm, llm_batch_size):
        items = [(f"T{i}", text) for i, text in enumerate(text_batch)]
        batch_results = _ask_agent_pp2_classify_batch(agent_c, items, valid_disciplines)
        for i, text in enumerate(text_batch):
            discipline, agent_confidence, basis = batch_results[f"T{i}"]
            classification_by_text[text] = (discipline, agent_confidence, basis)
            cache_key = _pp2_cache_key(text, schema_version)
            cache[cache_key] = {
                "cache_key": cache_key,
                "normalized_text": text,
                "discipline": discipline,
                "confidence": agent_confidence,
                "basis": basis,
            }
        processed_texts += len(text_batch)
        logger.info(f"PP2: classified {processed_texts}/{len(texts_needing_llm)} new distinct texts")

    _pp2_save_cache(cache_path, cache)

    findings: list[Finding] = []
    for row in blank_rows:
        record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}{row.get('OPERATION_KEY_SUFFIX', '')}"
        current_value = _none_if_na(row.get("OPWKCEN"))
        findings.append(
            _pp2_finding_for_operation(
                record_key, current_value, False, "UNCLEAR", "LOW", "",
                bokor_work_centres, confidence_scores,
            )
        )
    for normalized_text, rows in rows_by_text.items():
        discipline, agent_confidence, basis = classification_by_text[normalized_text]
        for row in rows:
            record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}{row.get('OPERATION_KEY_SUFFIX', '')}"
            current_value = _none_if_na(row.get("OPWKCEN"))
            findings.append(
                _pp2_finding_for_operation(
                    record_key, current_value, True, discipline, agent_confidence, basis,
                    bokor_work_centres, confidence_scores,
                )
            )

    logger.info(f"PP2: done, {len(findings)} findings")
    return findings


def run_pp3(
    task_list_operation_counts: dict[str, int],
    task_list_real_mi_counts: dict[str, int],
    historical_usage_task_lists: set[str] | None = None,
    batch_size: int = DEFAULT_BATCH_SIZE,
) -> list[Finding]:
    findings: list[Finding] = []
    all_task_lists = set(task_list_operation_counts.keys())
    total = len(all_task_lists)
    logger.info(f"PP3: starting, {total} Task Lists")
    processed = 0
    for batch in batched(sorted(all_task_lists), batch_size):
        for record_key in batch:
            operation_count = task_list_operation_counts.get(record_key, 0)
            if operation_count == 0:
                continue

            real_mi_count = task_list_real_mi_counts.get(record_key, 0)
            if record_key not in task_list_real_mi_counts:
                confidence = 0.50
            elif real_mi_count > 0:
                continue  # a real Maintenance Item currently uses this Task List — not orphaned
            else:
                confidence = 0.85  # operation_count > 0 AND real_mi_count resolved cleanly to 0 — the clean, fully-resolved case

            has_history = historical_usage_task_lists is not None and record_key in historical_usage_task_lists
            if has_history:
                reason = (
                    f"'{record_key}' is flagged because it has no current Maintenance Item "
                    "assignment. Historical usage was identified, which indicates prior use but "
                    "does not change the current unassigned condition"
                )
            else:
                reason = (
                    f"'{record_key}' is flagged because it contains {operation_count} maintenance "
                    "operation(s) but is not referenced by any current, real (non-stub) Maintenance "
                    "Item in the Knowledge Graph"
                )
            findings.append(
                Finding(
                    pain_point="PP3",
                    record_key=record_key,
                    field_name="Maintenance Item",
                    current_value=None,
                    recommended_value=None,
                    confidence=None,
                    detection_confidence=confidence,
                    reason=reason,
                    evidence_source=(
                        f"Task List '{record_key}' contains {operation_count} operation(s) "
                        "(Knowledge Graph HAS_OPERATION); current real (non-stub) Maintenance Item "
                        f"count = {real_mi_count} (Knowledge Graph USES_TASK_LIST); UDMS.pdf §9.6"
                    ),
                )
            )
        processed += len(batch)
        logger.info(f"PP3: processed {processed}/{total} Task Lists, {len(findings)} findings so far")
    logger.info(f"PP3: done, {len(findings)} findings")
    return findings


def _similarity(a: str | None, b: str | None) -> float:
    if a is None or b is None:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _pp4_build_task_list_context(
    task_list_group: pd.DataFrame,
) -> dict[str, dict]:
    context: dict[str, dict] = {}
    for r in task_list_group.to_dict("records"):
        group = _none_if_na(r.get("Group"))
        group_counter = _none_if_na(r.get("Group Counter"))
        if group is None or group_counter is None:
            continue
        key = f"{group}-{group_counter}"
        entry = context.setdefault(key, {"object_descriptions": set(), "equipment": set(), "flocs": set()})
        description = _none_if_na(r.get("Object Description"))
        if description is not None:
            entry["object_descriptions"].add(description)
        equipment = _none_if_na(r.get("Equipment"))
        if equipment is not None:
            entry["equipment"].add(str(equipment))
        floc = _none_if_na(r.get("Functional Location"))
        if floc is not None:
            entry["flocs"].add(str(floc))
    return context


def _pp4_object_type_family(object_descriptions: set[str]) -> str | None:
    if not object_descriptions:
        return None
    codes = {_object_type_code_for_description(d) for d in object_descriptions}
    if None in codes:
        return None
    families = {c[:2] for c in codes}
    if len(families) != 1:
        return None
    (family,) = families
    return family


def _pp4_candidate_pairs(
    task_list_keys: list[str], context: dict[str, dict],
) -> list[tuple[str, str]]:
    equipment_index: dict[str, set[str]] = {}
    floc_index: dict[str, set[str]] = {}
    family_index: dict[str, set[str]] = {}
    for key in task_list_keys:
        entry = context.get(key, {"object_descriptions": set(), "equipment": set(), "flocs": set()})
        for equipment in entry["equipment"]:
            equipment_index.setdefault(equipment, set()).add(key)
        for floc in entry["flocs"]:
            floc_index.setdefault(floc, set()).add(key)
        family = _pp4_object_type_family(entry["object_descriptions"])
        if family is not None:
            family_index.setdefault(family, set()).add(key)

    candidate_pairs: set[tuple[str, str]] = set()
    for index in (equipment_index, floc_index, family_index):
        for keys_sharing_signal in index.values():
            if len(keys_sharing_signal) < 2:
                continue
            for a, b in combinations(sorted(keys_sharing_signal), 2):
                candidate_pairs.add((a, b))
    return sorted(candidate_pairs)


def _pp4_strategy_frequency_compatible(
    a_ops: list[dict], b_ops: list[dict],
) -> tuple[bool, str]:
    strategies_a = {_none_if_na(op.get("STRATEGY")) for op in a_ops} - {None}
    strategies_b = {_none_if_na(op.get("STRATEGY")) for op in b_ops} - {None}
    frequencies_a = {_none_if_na(op.get("FREQUENCY")) for op in a_ops} - {None}
    frequencies_b = {_none_if_na(op.get("FREQUENCY")) for op in b_ops} - {None}

    if not strategies_a or not strategies_b or not frequencies_a or not frequencies_b:
        return True, "Strategy/Frequency not available for one or both Task Lists — comparison proceeds without this signal"
    if strategies_a & strategies_b or frequencies_a & frequencies_b:
        return True, f"Strategy/Frequency overlap found (Strategies: {sorted(strategies_a, key=str)} vs {sorted(strategies_b, key=str)}; Frequencies: {sorted(frequencies_a, key=str)} vs {sorted(frequencies_b, key=str)})"
    return False, f"No Strategy or Frequency overlap (Strategies: {sorted(strategies_a, key=str)} vs {sorted(strategies_b, key=str)}; Frequencies: {sorted(frequencies_a, key=str)} vs {sorted(frequencies_b, key=str)}) — different maintenance interval/intent"


_PP4_PROMPT_VERSION = "v1-batch"
_PP4_CACHE_COLUMNS = ["cache_key", "verdict", "basis"]


def _pp4_cache_key(text_a: str, text_b: str) -> str:
    digest_input = f"{_PP4_PROMPT_VERSION}\x00{text_a}\x00{text_b}"
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


def _pp4_load_cache(cache_path) -> dict[str, dict]:
    return _load_csv_cache(cache_path)


def _pp4_save_cache(cache_path, cache: dict[str, dict]) -> None:
    _save_csv_cache(cache_path, cache, _PP4_CACHE_COLUMNS)


_PP4_BATCH_PROMPT_HEADER = """You are comparing pairs of SAP PM Task List operations to determine whether each pair \
performs the SAME technical maintenance work, PARTIALLY overlapping work, or DIFFERENT work — based ONLY on the \
technical work scope described. Do not decide whether either operation or Task List should be kept, deleted, or \
merged — that is a human decision, not yours.

Reply with EXACTLY {count} blocks, one per pair below, in this exact format and nothing else — repeat the ID line \
verbatim:

ID: <the exact ID shown for that pair>
VERDICT: <EQUIVALENT|PARTIAL_OVERLAP|DIFFERENT|UNCLEAR>
BASIS: <one short sentence citing the specific words/phrases that justify this>

Reply UNCLEAR only if the operation text genuinely cannot be compared (e.g. both sides are blank).

Pairs to compare:
"""


def _pp4_batch_prompt(items: list[tuple[str, str, str]]) -> str:
    # items: list of (pair_id, operation_a_text, operation_b_text).
    header = _PP4_BATCH_PROMPT_HEADER.format(count=len(items))
    blocks = [
        f"--- Pair ID: {pair_id} ---\nOperation A: {a or '(blank)'}\nOperation B: {b or '(blank)'}"
        for pair_id, a, b in items
    ]
    return header + "\n\n".join(blocks)


def _parse_pp4_batch_reply(reply: str, expected_ids: set[str]) -> dict[str, tuple[str, str]]:
    valid_verdicts = {"EQUIVALENT", "PARTIAL_OVERLAP", "DIFFERENT", "UNCLEAR"}
    results: dict[str, tuple[str, str]] = {}
    current_id, current_verdict, current_basis = None, None, None

    def _flush():
        if current_id is not None and current_verdict is not None:
            results[current_id] = (current_verdict, current_basis or "")

    for line in reply.splitlines():
        line = line.strip()
        upper = line.upper()
        if upper.startswith("ID:"):
            _flush()
            current_id, current_verdict, current_basis = line.split(":", 1)[1].strip(), None, None
        elif upper.startswith("VERDICT:"):
            value = line.split(":", 1)[1].strip().upper()
            if value in valid_verdicts:
                current_verdict = value
        elif upper.startswith("BASIS:"):
            current_basis = line.split(":", 1)[1].strip()
    _flush()
    return {pair_id: value for pair_id, value in results.items() if pair_id in expected_ids}


def _ask_agent_pp4_classify_batch(
    agent_c, items: list[tuple[str, str, str]], max_retries: int = 2,
) -> dict[str, tuple[str, str]]:
    remaining = {pair_id: (pair_id, a, b) for pair_id, a, b in items}
    results: dict[str, tuple[str, str]] = {}
    for attempt in range(max_retries + 1):
        if not remaining:
            break
        batch = list(remaining.values())
        prompt = _pp4_batch_prompt(batch)
        try:
            response = agent_c.invoke({"messages": [{"role": "user", "content": prompt}]})
            reply = response["messages"][-1].content.strip()
        except Exception:
            reply = ""
        parsed = _parse_pp4_batch_reply(reply, set(remaining.keys()))
        results.update(parsed)
        for pair_id in parsed:
            remaining.pop(pair_id, None)
        if remaining and attempt < max_retries:
            logger.info(f"PP4: batch retry {attempt + 1}/{max_retries}, {len(remaining)} pair(s) missing/malformed")
    for pair_id in remaining:
        results[pair_id] = ("UNCLEAR", "Deep Agent did not return a well-formed verdict for this pair after retries")
    return results


def _pp4_compare_operations(
    key_a: str, key_b: str,
    ops_a: list[dict], ops_b: list[dict],
    agent_c,
    pending_llm_pairs: list[tuple[str, str, str]],
    pair_lookup: dict[str, tuple[dict, dict]],
) -> dict:
    equivalent = 0
    partial = 0
    matched_b: set[int] = set()
    a_only: list[str] = []
    pending_this_pair: list[tuple[int, int]] = []

    for i, op_a in enumerate(ops_a):
        text_a = _pp2_normalize_text(op_a.get("OPDESC"), op_a.get("LONGTEXT_CONSOLIDATED"))
        best_exact_j = None
        for j, op_b in enumerate(ops_b):
            if j in matched_b:
                continue
            text_b = _pp2_normalize_text(op_b.get("OPDESC"), op_b.get("LONGTEXT_CONSOLIDATED"))
            if text_a and text_a == text_b and op_a.get("OPWKCEN") == op_b.get("OPWKCEN"):
                best_exact_j = j
                break
        if best_exact_j is not None:
            equivalent += 1
            matched_b.add(best_exact_j)
            continue
        best_j, best_score = None, -1.0
        for j, op_b in enumerate(ops_b):
            if j in matched_b:
                continue
            text_b = _pp2_normalize_text(op_b.get("OPDESC"), op_b.get("LONGTEXT_CONSOLIDATED"))
            score = _similarity(text_a, text_b)
            if score > best_score:
                best_score, best_j = score, j
        if best_j is not None:
            pair_id = f"{key_a}|{key_b}|{i}|{best_j}"
            pair_lookup[pair_id] = (op_a, ops_b[best_j])
            pending_llm_pairs.append((pair_id, text_a, _pp2_normalize_text(ops_b[best_j].get("OPDESC"), ops_b[best_j].get("LONGTEXT_CONSOLIDATED"))))
            pending_this_pair.append((i, best_j))
        else:
            a_only.append(op_a.get("OPDESC") or "(no description)")

    return {
        "equivalent": equivalent,
        "matched_b": matched_b,
        "pending_this_pair": pending_this_pair,
        "a_only_provisional": a_only,
        "total_a": len(ops_a),
        "total_b": len(ops_b),
    }


def _pp4_classify_pair(
    equivalent: int, partial: int, total_a: int, total_b: int,
    strategy_compatible: bool,
) -> tuple[str | None, str]:
    if not strategy_compatible:
        return None, "different maintenance interval/intent — not a duplicate candidate"
    max_total = max(total_a, total_b)
    if max_total == 0:
        return "REVIEW_REQUIRED", "neither Task List has comparable operations to evaluate"
    equivalent_ratio = equivalent / max_total
    unique_count = (total_a - equivalent) + (total_b - equivalent)
    if equivalent == total_a and equivalent == total_b and unique_count == 0:
        return "EXACT_DUPLICATE", f"all {equivalent} operations are equivalent, no unique scope on either side"
    if equivalent_ratio >= 0.75:
        return "STRONG_OVERLAP", f"{equivalent}/{max_total} operations equivalent, some unique scope remains on one or both sides"
    if equivalent_ratio >= 0.4 or partial > 0:
        return "PARTIAL_OVERLAP", f"{equivalent}/{max_total} operations equivalent (+{partial} partial), substantial unique scope remains"
    return None, f"only {equivalent}/{max_total} operations equivalent — not a duplicate candidate"


def run_pp4(
    normalized_operations: pd.DataFrame,
    task_list_group: pd.DataFrame,
    agent_c=None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    llm_batch_size: int = 15,
    cache_path: str = "ground_truth_cache/PP04_semantic_cache.csv",
) -> list[Finding]:
    findings: list[Finding] = []
    context = _pp4_build_task_list_context(task_list_group)

    consolidated = _pp2_consolidate_operations(normalized_operations)
    ops_by_task_list: dict[str, list[dict]] = {}
    for row in consolidated.to_dict("records"):
        key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}"
        ops_by_task_list.setdefault(key, []).append(row)

    task_list_keys = sorted(ops_by_task_list.keys())
    candidate_pairs = _pp4_candidate_pairs(task_list_keys, context)
    logger.info(f"PP4: starting, {len(task_list_keys)} Task Lists, {len(candidate_pairs)} candidate pairs (pre-filtered from {len(task_list_keys) * (len(task_list_keys) - 1) // 2} all-pairs)")

    pending_llm_pairs: list[tuple[str, str, str]] = []
    pair_lookup: dict[str, tuple[dict, dict]] = {}
    pair_results: dict[tuple[str, str], dict] = {}
    pair_strategy_notes: dict[tuple[str, str], tuple[bool, str]] = {}

    processed = 0
    for key_a, key_b in candidate_pairs:
        ops_a = ops_by_task_list.get(key_a, [])
        ops_b = ops_by_task_list.get(key_b, [])
        strategy_compatible, strategy_note = _pp4_strategy_frequency_compatible(ops_a, ops_b)
        pair_strategy_notes[(key_a, key_b)] = (strategy_compatible, strategy_note)
        if not strategy_compatible:
            continue  # Step 5: different interval/intent — never compare operation text at all
        pair_results[(key_a, key_b)] = _pp4_compare_operations(
            key_a, key_b, ops_a, ops_b, agent_c, pending_llm_pairs, pair_lookup
        )
        processed += 1
        if processed % 200 == 0:
            logger.info(f"PP4: deterministic comparison, {processed}/{len(candidate_pairs)} candidate pairs processed")

    logger.info(f"PP4: {len(pending_llm_pairs)} ambiguous operation pair(s) need semantic comparison")
    llm_results: dict[str, tuple[str, str]] = {}

    cache = _pp4_load_cache(cache_path)
    pairs_needing_llm: list[tuple[str, str, str]] = []
    for pair_id, text_a, text_b in pending_llm_pairs:
        cache_key = _pp4_cache_key(text_a, text_b)
        cached = cache.get(cache_key)
        if cached is not None:
            llm_results[pair_id] = (cached["verdict"], cached.get("basis", ""))
        else:
            pairs_needing_llm.append((pair_id, text_a, text_b))
    logger.info(f"PP4: {len(pending_llm_pairs) - len(pairs_needing_llm)} operation pair(s) served from cache, {len(pairs_needing_llm)} need a fresh Deep Agent call")

    if pairs_needing_llm and agent_c is not None:
        processed_llm = 0
        pair_text_by_id = {pair_id: (text_a, text_b) for pair_id, text_a, text_b in pairs_needing_llm}
        for llm_batch in batched(pairs_needing_llm, llm_batch_size):
            batch_results = _ask_agent_pp4_classify_batch(agent_c, llm_batch)
            llm_results.update(batch_results)
            for pair_id, (verdict, basis) in batch_results.items():
                text_a, text_b = pair_text_by_id[pair_id]
                cache_key = _pp4_cache_key(text_a, text_b)
                cache[cache_key] = {"cache_key": cache_key, "verdict": verdict, "basis": basis}
            _pp4_save_cache(cache_path, cache)
            processed_llm += len(llm_batch)
            logger.info(f"PP4: semantic comparison, {processed_llm}/{len(pairs_needing_llm)} new operation pairs classified")
    elif pairs_needing_llm:
        for pair_id, _a, _b in pairs_needing_llm:
            llm_results[pair_id] = ("UNCLEAR", "No Deep Agent supplied — semantic comparison not attempted")

    # Fold the LLM verdicts back into each pair's equivalent/partial tally.
    for (key_a, key_b), result in pair_results.items():
        for i, j in result["pending_this_pair"]:
            pair_id = f"{key_a}|{key_b}|{i}|{j}"
            verdict, _basis = llm_results.get(pair_id, ("UNCLEAR", ""))
            if verdict == "EQUIVALENT":
                result["equivalent"] += 1
                result["matched_b"].add(j)
            elif verdict == "PARTIAL_OVERLAP":
                result["partial"] = result.get("partial", 0) + 1
                result["matched_b"].add(j)
            # DIFFERENT/UNCLEAR: op_a stays counted as unique (a_only), no change needed

    for (key_a, key_b), result in pair_results.items():
        strategy_compatible, strategy_note = pair_strategy_notes[(key_a, key_b)]
        equivalent = result["equivalent"]
        partial = result.get("partial", 0)
        total_a = result["total_a"]
        total_b = result["total_b"]
        flag, classification_note = _pp4_classify_pair(equivalent, partial, total_a, total_b, strategy_compatible)
        if flag is None:
            continue  # NOT_DUPLICATE — never included in PP4 findings, per client instruction

        record_key = f"{key_a} / {key_b}"
        context_a = context.get(key_a, {"object_descriptions": set(), "equipment": set(), "flocs": set()})
        context_b = context.get(key_b, {"object_descriptions": set(), "equipment": set(), "flocs": set()})
        shared_equipment = context_a["equipment"] & context_b["equipment"]
        shared_flocs = context_a["flocs"] & context_b["flocs"]

        findings.append(
            Finding(
                pain_point="PP4",
                record_key=record_key,
                field_name="Group",
                current_value=key_a,
                recommended_value=None,
                confidence=None,
                detection_confidence=(
                    0.9 if flag == "EXACT_DUPLICATE" else 0.75 if flag == "STRONG_OVERLAP" else 0.5 if flag == "PARTIAL_OVERLAP" else 0.3
                ),
                reason=(
                    f"'{key_a}' is flagged against '{key_b}' as {flag} because {classification_note} "
                    f"({strategy_note})"
                ),
                evidence_source=(
                    f"'{key_a}' contains {total_a} operation(s), '{key_b}' contains {total_b}; "
                    f"equivalent operation count = {equivalent}/{max(total_a, total_b)}"
                    + (f", partial overlap = {partial}" if partial else "")
                    + (f"; shared Equipment: {sorted(shared_equipment)}" if shared_equipment else "")
                    + (f"; shared Functional Location: {sorted(shared_flocs)}" if shared_flocs else "")
                    + f"; {strategy_note}"
                ),
            )
        )

    logger.info(f"PP4: done, {len(findings)} findings")
    return findings


def _ask_agent_oreda_worth_checking(agent_c) -> str:
    if agent_c is None:
        return ""
    prompt = (
        "A Bokor Long Text operation's WORK/DURATION units fall outside the MHR/HR scope "
        "the standard formula applies to. Before this is reported as insufficient evidence, "
        "use the check_oreda_applicability tool to confirm whether OREDA offers any usable "
        "signal here."
    )
    try:
        result = agent_c.invoke({"messages": [{"role": "user", "content": prompt}]})
        return str(result)
    except Exception:
        return ""


_OREDA_ITEM_HINT_KEYWORDS: dict[str, str] = {
    # Machinery > Pumps
    "CENTRIFUGAL PUMP": "Machinery Pumps Centrifugal",
    "RECIPROCATING PUMP": "Machinery Pumps Reciprocating",
    "ROTARY PUMP": "Machinery Pumps Rotary",
    "PUMP": "Machinery Pumps",
    # Machinery > Compressors
    "CENTRIFUGAL COMPRESSOR": "Machinery Compressors Centrifugal",
    "RECIPROCATING COMPRESSOR": "Machinery Compressors Reciprocating",
    "SCREW COMPRESSOR": "Machinery Compressors Screw",
    "COMPRESSOR": "Machinery Compressors",
    # Machinery > Gas Turbines / Turboexpanders / Combustion Engines
    "GAS TURBINE": "Machinery Gas Turbines",
    "TURBOEXPANDER": "Machinery Turboexpanders",
    "TURBINE": "Machinery Gas Turbines",
    "DIESEL ENGINE": "Machinery Combustion Enigens Diesel engine",
    "GAS ENGINE": "Machinery Combustion Enigens Gas engine",
    # Electric Equipment
    "GENERATOR": "Electric Equipment Electric Generators",
    "MOTOR": "Electric Equipment Electric motors",
    # Mechanical Equipment > Heat Exchangers
    "HEAT EXCHANGER": "Mechanical Equipment Heat Exchangers",
    # Mechanical Equipment > Vessels
    "SEPARATOR": "Mechanical Equipment Vessels Separator",
    "SCRUBBER": "Mechanical Equipment Vessels Scrubber",
    "COALESCER": "Mechanical Equipment Vessels Coalescer",
    "FLASH DRUM": "Mechanical Equipment Vessels Flash drum",
    "CONTACTOR": "Mechanical Equipment Vessels Contactor",
    "STRIPPER": "Mechanical Equipment Vessels Stripper",
    "VESSEL": "Mechanical Equipment Vessels",
    # Mechanical Equipment > Heaters and boilers
    "BOILER": "Mechanical Equipment Heaters and boilers",
    "FIRED HEATER": "Mechanical Equipment Heaters and boilers Direct HC fired heater",
    # Control and Safety Equipment > Fire & Gas Detectors
    "FLAME DETECTOR": "Control and Safety Equipment Fire & Gas Detectors Flame",
    "SMOKE DETECTOR": "Control and Safety Equipment Fire & Gas Detectors Smoke/Combustion",
    "HEAT DETECTOR": "Control and Safety Equipment Fire & Gas Detectors Heat",
    "H2S DETECTOR": "Control and Safety Equipment Fire & Gas Detectors H2S gas",
    "H2S GAS": "Control and Safety Equipment Fire & Gas Detectors H2S gas",
    "GAS DETECTOR": "Control and Safety Equipment Fire & Gas Detectors Hydrocarbon gas",
    # Control and Safety Equipment > Process sensors
    "FLOW TRANSMITTER": "Control and Safety Equipment Process sensors Flow",
    "LEVEL TRANSMITTER": "Control and Safety Equipment Process sensors Level",
    "LEVEL GAUGE": "Control and Safety Equipment Process sensors Level",
    "PRESSURE TRANSMITTER": "Control and Safety Equipment Process sensors Pressure",
    "PRESS TRANSMITTER": "Control and Safety Equipment Process sensors Pressure",
    "PRESSURE SWITCH": "Control and Safety Equipment Process sensors Pressure",
    "PRESS SWITCH": "Control and Safety Equipment Process sensors Pressure",
    "TEMPERATURE TRANSMITTER": "Control and Safety Equipment Process sensors Temperature",
    "TEMP TRANSMITTER": "Control and Safety Equipment Process sensors Temperature",
    "SHUTDOWN VALVE": "Control and Safety Equipment Valves ESD",
    "EMERGENCY SHUTDOWN VALVE": "Control and Safety Equipment Valves ESD",
    "ESD VALVE": "Control and Safety Equipment Valves ESD",
    "RELIEF VALVE": "Control and Safety Equipment Valves Relief",
    "PRESSURE SAFETY VALVE": "Control and Safety Equipment Valves PSV - Conventional",
    "PSV": "Control and Safety Equipment Valves PSV - Conventional",
    "BLOWDOWN VALVE": "Control and Safety Equipment Valves Blowdown",
    "BALL VALVE": "Control and Safety Equipment Valves Ball",
    "BUTTERFLY VALVE": "Control and Safety Equipment Valves Butterfly",
    "GATE VALVE": "Control and Safety Equipment Valves Gate",
    "GLOBE VALVE": "Control and Safety Equipment Valves Globe",
    "CHECK VALVE": "Control and Safety Equipment Valves Check",
    "DIAPHRAGM VALVE": "Control and Safety Equipment Valves Diaphragm",
    "CONTROL VALVE": "Control and Safety Equipment Valves Process control",
    "VALVE": "Control and Safety Equipment Valves",
}


def _resolve_oreda_item_hint(equipment_description: str | None, opdesc: str | None, longtext: str | None) -> str | None:
    for text in (equipment_description, opdesc, longtext):
        if text is None:
            continue
        upper = str(text).upper()
        for keyword, oreda_item in _OREDA_ITEM_HINT_KEYWORDS.items():
            if keyword in upper:
                return oreda_item
    return None


_ROUTINE_PM_KEYWORDS = (
    "INSPECTION", "INSP", "FUNC TEST", "FUNCTIONAL TEST", "CALIB", "CAL/FUNC",
    "SERVICE", "SERV", "TESTING", "VISUAL", "CHECK", "MONITORING", "LUBRICAT",
)
_GENERAL_REPAIR_COMPARABLE_KEYWORDS = ("OVERHAUL", "REPLACEMENT", "REPLACE", "REPAIR", "REBUILD", "CORRECTIVE", "BREAKDOWN")


def _is_general_repair_comparable_activity(opdesc: str | None, longtext: str | None) -> bool:
    combined = " ".join(str(t).upper() for t in (opdesc, longtext) if t is not None)
    if not combined:
        return False
    if any(keyword in combined for keyword in _ROUTINE_PM_KEYWORDS):
        return False
    return any(keyword in combined for keyword in _GENERAL_REPAIR_COMPARABLE_KEYWORDS)


_PP5_SCOPE_PROMPT_VERSION = "v1-batch"


def _pp5_scope_cache_key(normalized_text: str) -> str:
    digest_input = f"{_PP5_SCOPE_PROMPT_VERSION}\x00{normalized_text}"
    return hashlib.sha256(digest_input.encode("utf-8")).hexdigest()


_PP5_SCOPE_CACHE_COLUMNS = ["cache_key", "normalized_text", "activity_type", "equipment", "scope"]


def _pp5_scope_load_cache(cache_path) -> dict[str, dict]:
    return _load_csv_cache(cache_path)


def _pp5_scope_save_cache(cache_path, cache: dict[str, dict]) -> None:
    _save_csv_cache(cache_path, cache, _PP5_SCOPE_CACHE_COLUMNS)


_PP5_SCOPE_BATCH_PROMPT_HEADER = """You are reading a batch of {count} SAP PM Task List operations (Operation \
Description + full Long Text) for a planned-maintenance man-hours review. For EACH operation, extract — do NOT \
invent — three short fields describing its scope, based ONLY on the text given:

ACTIVITY: the maintenance activity type (e.g. "6M Periodic Inspection", "Overhaul", "Functional Test", \
"Calibration", "Corrective Repair")
EQUIPMENT: the equipment/activity object in plain terms (e.g. "Gantry crane", "Centrifugal pump")
SCOPE: a short comma-separated list of the concrete tasks described (e.g. "Inspection, lubrication, functional \
test, load test")

You are NOT deciding how many man-hours this should take — only summarizing what kind of job this is, so it can \
later be matched against comparable historical executions and JMS work-pack records. Each operation is \
independent.

Reply with EXACTLY {count} blocks, one per operation below, in this exact format and nothing else — repeat the \
ID line verbatim:

ID: <the exact ID shown for that operation>
ACTIVITY: <short activity type>
EQUIPMENT: <short equipment/activity object>
SCOPE: <short comma-separated task list>

Operations to summarize:
"""


def _pp5_scope_batch_prompt(items: list[tuple[str, str]]) -> str:
    header = _PP5_SCOPE_BATCH_PROMPT_HEADER.format(count=len(items))
    blocks = []
    for item_id, operation_text in items:
        blocks.append(f"--- Operation ID: {item_id} ---\n{operation_text or '(blank)'}")
    return header + "\n\n".join(blocks)


def _parse_pp5_scope_batch_reply(reply: str, expected_ids: set[str]) -> dict[str, tuple[str, str, str]]:
    results: dict[str, tuple[str, str, str]] = {}
    current_id = None
    current_activity = None
    current_equipment = None
    current_scope = None

    def _flush():
        if current_id is not None and (current_activity or current_equipment or current_scope):
            results[current_id] = (current_activity or "", current_equipment or "", current_scope or "")

    for line in reply.splitlines():
        line = line.strip()
        upper = line.upper()
        if upper.startswith("ID:"):
            _flush()
            current_id = line.split(":", 1)[1].strip()
            current_activity = None
            current_equipment = None
            current_scope = None
        elif upper.startswith("ACTIVITY:"):
            current_activity = line.split(":", 1)[1].strip()
        elif upper.startswith("EQUIPMENT:"):
            current_equipment = line.split(":", 1)[1].strip()
        elif upper.startswith("SCOPE:"):
            current_scope = line.split(":", 1)[1].strip()
    _flush()
    return {item_id: value for item_id, value in results.items() if item_id in expected_ids}


def _ask_agent_pp5_scope_batch(agent_c, items: list[tuple[str, str]], max_retries: int = 2) -> dict[str, tuple[str, str, str]]:
    remaining = {item_id: (item_id, text) for item_id, text in items}
    results: dict[str, tuple[str, str, str]] = {}

    for attempt in range(max_retries + 1):
        if not remaining:
            break
        batch = list(remaining.values())
        prompt = _pp5_scope_batch_prompt(batch)
        try:
            response = agent_c.invoke({"messages": [{"role": "user", "content": prompt}]})
            reply = response["messages"][-1].content.strip()
        except Exception:
            reply = ""
        parsed = _parse_pp5_scope_batch_reply(reply, set(remaining.keys()))
        results.update(parsed)
        for item_id in parsed:
            remaining.pop(item_id, None)
        if remaining and attempt < max_retries:
            logger.info(f"PP5 scope: batch retry {attempt + 1}/{max_retries}, {len(remaining)} item(s) missing/malformed")

    for item_id in remaining:
        results[item_id] = ("", "", "")
    return results


def _pp5_build_scope_lookup(
    normalized_operations: pd.DataFrame,
    record_keys_needing_scope: set[str],
    agent_c,
    llm_batch_size: int = 15,
    cache_path: str = "ground_truth_cache/PP05_scope_cache.csv",
) -> dict[str, tuple[str, str, str]]:
    """Step 3 — LLM scope understanding (Operation Description + complete Long Text), only for
    operations whose Tier 1 arithmetic is valid (callers filter record_keys_needing_scope to
    that set). Reuses the agent_c Deep Agent batching/caching pattern already used by PP2/PP4.
    """
    if agent_c is None or not record_keys_needing_scope:
        return {}

    text_by_key: dict[str, str] = {}
    for row in normalized_operations.to_dict("records"):
        key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}"
        if key not in record_keys_needing_scope or key in text_by_key:
            continue
        opdesc = _none_if_na(row.get("OPDESC")) or ""
        longtext = _none_if_na(row.get("LONGTEXT_AGGREGATED")) or ""
        text_by_key[key] = " ".join(f"{opdesc}\n{longtext}".split())

    cache = _pp5_scope_load_cache(cache_path)
    scope_by_key: dict[str, tuple[str, str, str]] = {}
    keys_needing_llm: list[str] = []
    for key, text in text_by_key.items():
        if not text:
            scope_by_key[key] = ("", "", "")
            continue
        cache_key = _pp5_scope_cache_key(text)
        cached = cache.get(cache_key)
        if cached is not None:
            scope_by_key[key] = (cached["activity_type"], cached["equipment"], cached["scope"])
        else:
            keys_needing_llm.append(key)

    processed = 0
    for key_batch in batched(keys_needing_llm, llm_batch_size):
        items = [(k, text_by_key[k]) for k in key_batch]
        batch_results = _ask_agent_pp5_scope_batch(agent_c, items)
        for key in key_batch:
            activity, equipment, scope = batch_results.get(key, ("", "", ""))
            scope_by_key[key] = (activity, equipment, scope)
            cache_key = _pp5_scope_cache_key(text_by_key[key])
            cache[cache_key] = {
                "cache_key": cache_key,
                "normalized_text": text_by_key[key],
                "activity_type": activity,
                "equipment": equipment,
                "scope": scope,
            }
        processed += len(key_batch)
        logger.info(f"PP5 scope: classified {processed}/{len(keys_needing_llm)} new operations")

    if keys_needing_llm:
        _pp5_scope_save_cache(cache_path, cache)

    return scope_by_key


def _pp5_evidence_reconciliation_check(
    row: dict,
    record_key: str,
    historical_matches: pd.DataFrame | None,
    pitstops_ranges: pd.DataFrame | None,
    oreda_conn,
    min_comparable_executions: int,
    matched_jms_rows: pd.DataFrame | None = None,
    object_description_lookup: dict[tuple[str, str], str] | None = None,
    scope_lookup: dict[str, tuple[str, str, str]] | None = None,
) -> Finding:
    """Tier 2 — Steps 3-17 of the client's PP5 spec: JMS + Historical convergence/conflict model.
    Only called for operations whose Tier 1 arithmetic is valid (run_pp5 skips Tier 2 entirely for
    Case B operations, which are terminal).

    PITSTOPS (Step 14) is supporting-only: duration plausibility text, never a WORK source, never
    part of the status decision. OREDA (Step 15) is last-resort-only, used only when BOTH
    Historical and JMS are unavailable, and whenever used the result is ALWAYS REVIEW_REQUIRED,
    never VALID. Case B (Tier 1 arithmetic mismatch) is handled entirely in _pp5_row_check — this
    function only runs the Step 3+ evidence logic for operations whose Tier 1 arithmetic is valid.
    """
    from scripts.evidence_reconciliation import (
        _fmt_hours,
        historical_range_lane,
        jms_lane,
        jms_within_historical_range,
        oreda_lane,
        tasklist_worklist_lane,
        values_converge,
    )

    work = float(row["WORK"])

    # Step 14 — PITSTOPS: duration plausibility only, annotation text, never a decision input.
    pitstops_note = tasklist_worklist_lane(
        row.get("OPWKCEN"), pitstops_ranges, sap_duration_hours=_none_if_na(row.get("DURATION"))
    )

    # Step 10-13 — JMS as a direct reference.
    jms_result = jms_lane(record_key, matched_jms_rows)

    # Step 6-9 — Historical observed range (never a median).
    historical_result = historical_range_lane(record_key, historical_matches, min_comparable_executions)

    scope_note = None
    if scope_lookup is not None:
        activity, equipment, scope = scope_lookup.get(record_key, ("", "", ""))
        if activity or equipment or scope:
            scope_note = (
                f"Scope understanding (Deep Agent): activity='{activity}', equipment='{equipment}', "
                f"scope='{scope}'"
            )

    evidence_prefix = f"{scope_note}; " if scope_note else ""
    pitstops_suffix = f" {pitstops_note}" if pitstops_note else ""

    # --- Case E (CONFLICT): JMS and Historical both available but disagree with each other. ---
    if jms_result.available and historical_result.available:
        if jms_within_historical_range(jms_result.value, historical_result.min_hours, historical_result.max_hours):
            # Step 12 — converge.
            consistent_with_current = (
                historical_result.min_hours <= work <= historical_result.max_hours
                and values_converge(work, jms_result.value)
            )
            if consistent_with_current:
                # Case A — current WORK itself already matches both arithmetic and evidence.
                return Finding(
                    pain_point="PP5", record_key=record_key, field_name="WORK",
                    current_value=str(row["WORK"]), recommended_value=None, confidence=None,
                    reason=(
                        f"{evidence_prefix}Current WORK ({work} MHR) is consistent with both JMS "
                        f"({jms_result.reason}) and the historical observed range "
                        f"({_fmt_hours(historical_result.min_hours)}-{_fmt_hours(historical_result.max_hours)} MHR, "
                        f"{historical_result.execution_count} verified executions) — no change needed."
                        f"{pitstops_suffix}"
                    ),
                    evidence_source=f"VALID — JMS + Historical converge with current WORK; {jms_result.source}; {historical_result.source}",
                    evidence_level="VALID",
                )
            # Case C — JMS + Historical converge on a different value than current WORK.
            return Finding(
                pain_point="PP5", record_key=record_key, field_name="WORK",
                current_value=str(row["WORK"]), recommended_value=str(jms_result.value),
                confidence="Medium",
                reason=(
                    f"{evidence_prefix}Current WORK ({work} MHR) differs from converging evidence: "
                    f"JMS gives {jms_result.value} MHR ({jms_result.reason}), consistent with the "
                    f"historical observed range {_fmt_hours(historical_result.min_hours)}-{_fmt_hours(historical_result.max_hours)} MHR "
                    f"({historical_result.execution_count} verified executions). JMS value offered as the "
                    f"specific, defensible suggested WORK.{pitstops_suffix}"
                ),
                evidence_source=f"REVIEW_REQUIRED — JMS + Historical converge; {jms_result.source}; {historical_result.source}",
                evidence_level="REVIEW_REQUIRED",
            )
        # Step 12 — conflict: JMS and Historical clearly disagree with each other.
        return Finding(
            pain_point="PP5", record_key=record_key, field_name="WORK",
            current_value=str(row["WORK"]), recommended_value=None, confidence=None,
            reason=(
                f"{evidence_prefix}JMS and Historical evidence conflict: JMS gives {jms_result.value} MHR "
                f"({jms_result.reason}), while the historical observed range is "
                f"{_fmt_hours(historical_result.min_hours)}-{_fmt_hours(historical_result.max_hours)} MHR "
                f"({historical_result.execution_count} verified executions) — these do not agree. "
                f"No automatic recommendation is made; current WORK is {work} MHR.{pitstops_suffix}"
            ),
            evidence_source=f"CONFLICT — JMS vs Historical; {jms_result.source}; {historical_result.source}",
            evidence_level="CONFLICT",
        )

    # --- Only JMS available (no comparable historical executions). ---
    if jms_result.available and not historical_result.available:
        if values_converge(work, jms_result.value):
            return Finding(
                pain_point="PP5", record_key=record_key, field_name="WORK",
                current_value=str(row["WORK"]), recommended_value=None, confidence=None,
                reason=(
                    f"{evidence_prefix}Current WORK ({work} MHR) is consistent with JMS "
                    f"({jms_result.reason}); no comparable historical executions available "
                    f"({historical_result.reason}). No change needed.{pitstops_suffix}"
                ),
                evidence_source=f"VALID — JMS matches current WORK (no historical range available); {jms_result.source}",
                evidence_level="VALID",
            )
        return Finding(
            pain_point="PP5", record_key=record_key, field_name="WORK",
            current_value=str(row["WORK"]), recommended_value=str(jms_result.value),
            confidence="Medium",
            reason=(
                f"{evidence_prefix}Current WORK ({work} MHR) differs from JMS's direct job-level figure "
                f"of {jms_result.value} MHR ({jms_result.reason}). No comparable historical executions "
                f"are available to independently corroborate ({historical_result.reason}), but JMS alone "
                f"is a genuinely applicable, specific source, so its value is offered as the suggested "
                f"WORK.{pitstops_suffix}"
            ),
            evidence_source=f"REVIEW_REQUIRED — JMS only (no historical match); {jms_result.source}",
            evidence_level="REVIEW_REQUIRED",
        )

    # --- Only Historical available (no JMS match): Step 8/9 range logic alone. ---
    if historical_result.available and not jms_result.available:
        if historical_result.min_hours <= work <= historical_result.max_hours:
            # Case A.
            return Finding(
                pain_point="PP5", record_key=record_key, field_name="WORK",
                current_value=str(row["WORK"]), recommended_value=None, confidence=None,
                reason=(
                    f"{evidence_prefix}Current WORK ({work} MHR) falls within the observed historical "
                    f"range of {_fmt_hours(historical_result.min_hours)}-{_fmt_hours(historical_result.max_hours)} MHR "
                    f"({historical_result.execution_count} verified comparable executions). No JMS match "
                    f"available ({jms_result.reason}). No change needed.{pitstops_suffix}"
                ),
                evidence_source=f"VALID — within historical observed range; {historical_result.source}",
                evidence_level="VALID",
            )
        # Case D.
        return Finding(
            pain_point="PP5", record_key=record_key, field_name="WORK",
            current_value=str(row["WORK"]), recommended_value=None, confidence=None,
            reason=(
                f"{evidence_prefix}Current WORK ({work} MHR) falls OUTSIDE the observed historical "
                f"range of {_fmt_hours(historical_result.min_hours)}-{_fmt_hours(historical_result.max_hours)} MHR "
                f"({historical_result.execution_count} verified comparable executions). No JMS match "
                f"available ({jms_result.reason}) to provide a single defensible replacement value — "
                f"historical evidence supports review but a single observed value from the range is "
                f"not a defensible specific recommendation on its own. PP5_Suggested_WORK left "
                f"blank.{pitstops_suffix}"
            ),
            evidence_source=f"REVIEW_REQUIRED — outside historical observed range, no JMS to corroborate; {historical_result.source}",
            evidence_level="REVIEW_REQUIRED",
        )

    # --- Neither Historical nor JMS available. Step 15 — OREDA last-resort only. ---
    equipment_description = None
    if object_description_lookup is not None:
        equipment_description = object_description_lookup.get((str(row.get("TLGRP")), str(row.get("TLGRPCOUNT"))))
    item_hint = _resolve_oreda_item_hint(equipment_description, row.get("OPDESC"), row.get("LONGTEXT_AGGREGATED"))
    is_general_repair_comparable = _is_general_repair_comparable_activity(row.get("OPDESC"), row.get("LONGTEXT_AGGREGATED"))
    oreda_result = oreda_lane(row, oreda_conn, item_hint=item_hint, is_general_repair_comparable=is_general_repair_comparable)

    below_threshold_note = (
        f" ({len(historical_result.below_threshold_candidate_hours)} historical execution(s) found but "
        f"below the minimum of {min_comparable_executions} required: {historical_result.below_threshold_candidate_hours})"
        if historical_result.below_threshold_candidate_hours else ""
    )

    if oreda_result.available:
        # OREDA used -> ALWAYS REVIEW_REQUIRED, never VALID, always clearly provisional.
        return Finding(
            pain_point="PP5", record_key=record_key, field_name="WORK",
            current_value=str(row["WORK"]), recommended_value=None, confidence=None,
            reason=(
                f"{evidence_prefix}No Historical evidence ({historical_result.reason}{below_threshold_note}) "
                f"and no JMS match ({jms_result.reason}) are available. Last-resort OREDA benchmark: "
                f"{oreda_result.reason} — PROVISIONAL only, not a confirmed Bokor planning value; current "
                f"WORK is {work} MHR. SME review required.{pitstops_suffix}"
            ),
            evidence_source=f"REVIEW_REQUIRED — OREDA last-resort, provisional; {oreda_result.source}",
            evidence_level="REVIEW_REQUIRED",
        )

    # Case F — CANNOT_VERIFY: arithmetic fine, but insufficient comparable evidence of any kind
    # (Tier 1 is always valid here — Tier 2 is only ever reached for non-Case-B operations).
    return Finding(
        pain_point="PP5", record_key=record_key, field_name="WORK",
        current_value=str(row["WORK"]), recommended_value=None, confidence=None,
        reason=(
            f"{evidence_prefix}Tier 1 arithmetic is fine (WORK = PERSON x DURATION), but "
            f"insufficient comparable evidence exists to judge appropriateness: no JMS match "
            f"({jms_result.reason}), fewer than {min_comparable_executions} comparable historical "
            f"executions ({historical_result.reason}{below_threshold_note}), and no applicable OREDA "
            f"benchmark ({oreda_result.reason}).{pitstops_suffix}"
        ),
        evidence_source=f"CANNOT_VERIFY — no usable evidence from any source; {historical_result.source}; {jms_result.source}; {oreda_result.source}",
        evidence_level="CANNOT_VERIFY",
    )


def _pp5_row_check(
    row: dict,
    valid_work_unit: str,
    valid_duration_unit: str,
    pitstops_ranges: pd.DataFrame | None,
    work_tolerance: float,
    agent_c,
) -> Finding | None:
    record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}-{row['TLSUBOPNO']}"

    work = _none_if_na(row["WORK"])
    person = _none_if_na(row["PERSON"])
    duration = _none_if_na(row["DURATION"])

    # 1. COMPLETENESS
    if work is None or person is None or duration is None:
        return Finding(
            pain_point="PP5", record_key=record_key, field_name="WORK",
            current_value=str(work), recommended_value=None, confidence=None,
            reason="WORK, PERSON, or DURATION is blank for this operation — no value to validate or compute",
            evidence_source="Bokor Long Text_Aug26_LATEST.xlsm; UDMS.pdf §9.20-21",
        )

    if row["WORK_UNIT"] != valid_work_unit or row["DURATION_UNIT"] != valid_duration_unit:
        agent_note = _ask_agent_oreda_worth_checking(agent_c)
        evidence_source = "Bokor Long Text_Aug26_LATEST.xlsm; UDMS.pdf §9.20-21"
        if agent_note:
            evidence_source += " + Deep Agent OREDA-applicability check"
        return Finding(
            pain_point="PP5", record_key=record_key, field_name="WORK",
            current_value=str(work), recommended_value=None, confidence=None,
            reason=(
                f"WORK_UNIT/DURATION_UNIT is '{row['WORK_UNIT']}'/'{row['DURATION_UNIT']}', "
                f"not the '{valid_work_unit}'/'{valid_duration_unit}' scope the WORK=PERSON*DURATION formula applies to"
            ),
            evidence_source=evidence_source,
        )

    # Step 2 / Case B — Tier 1 arithmetic mismatch: deterministic, no LLM/evidence lookup needed.
    # PP5_Suggested_WORK = PERSON x DURATION, PP5_Status = REVIEW_REQUIRED.
    computed_work = person * duration
    if abs(work - computed_work) > work_tolerance:
        range_flag = None
        if pitstops_ranges is not None:
            range_flag = flag_implausible_work(computed_work, row["OPWKCEN"], pitstops_ranges)
        return Finding(
            pain_point="PP5", record_key=record_key, field_name="WORK",
            current_value=str(work), recommended_value=str(computed_work),
            confidence="High",
            detection_confidence=0.90 if range_flag == "SUSPICIOUS" else None,
            reason=(
                f"PERSON is {person} and DURATION is {duration} {valid_duration_unit}. Based on the "
                f"confirmed SAP planning values, the calculated WORK is {computed_work} {valid_work_unit}, "
                f"while the recorded WORK is {work} {valid_work_unit}."
                + (" The calculated value also falls far outside PITSTOPS' plausible duration range for this discipline." if range_flag == "SUSPICIOUS" else "")
            ),
            evidence_source="Bokor Long Text_Aug26_LATEST.xlsm (PERSON x DURATION); UDMS.pdf §9.20-21",
            evidence_level="REVIEW_REQUIRED",
        )
    return None


def run_pp5(
    normalized_operations: pd.DataFrame,
    valid_work_unit: str,
    valid_duration_unit: str,
    pitstops_ranges: pd.DataFrame | None = None,
    work_tolerance: float = 0.01,
    agent_c=None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    historical_matches: pd.DataFrame | None = None,
    min_comparable_executions: int = 3,
    historical_benchmark_confidence: float = 0.6,
    oreda_conn=None,
    matched_jms_rows: pd.DataFrame | None = None,
    task_list_group: pd.DataFrame | None = None,
) -> list[Finding]:
    """PP5 — man-hours validation (client spec, 2026-10).

    Step 2 (Tier 1, deterministic): WORK vs PERSON x DURATION. A mismatch is Case B — terminal,
    no Tier 2 evidence lookup for that operation (_pp5_row_check returns the Finding directly).

    Steps 3-17 (Tier 2): only run for operations where every sub-operation's Tier 1 arithmetic is
    valid — Step 3 LLM scope understanding, then Step 6-17 JMS+Historical convergence/conflict
    (_pp5_evidence_reconciliation_check implements Cases A/C/D/E/F; OREDA Step 15 last-resort only).

    `historical_benchmark_confidence` is accepted for call-site/config-schema compatibility but is
    no longer used — the new spec never computes a confidence-weighted historical suggestion (it is
    always an observed range, Step 8), so there is nothing left for it to scale.
    """
    findings: list[Finding] = []

    object_description_lookup: dict[tuple[str, str], str] = {}
    if task_list_group is not None:
        for r in task_list_group.dropna(subset=["Group", "Group Counter", "Object Description"]).to_dict("records"):
            object_description_lookup[(str(r["Group"]), str(r["Group Counter"]))] = r["Object Description"]

    rows = normalized_operations.to_dict("records")
    total = len(rows)
    logger.info(f"PP5: starting, {total} operations")
    processed = 0
    pending_reconciliation: dict[str, tuple[dict, bool]] = {}
    for batch in batched(rows, batch_size):
        for row in batch:
            arithmetic_finding = _pp5_row_check(row, valid_work_unit, valid_duration_unit, pitstops_ranges, work_tolerance, agent_c)
            if arithmetic_finding is not None:
                findings.append(arithmetic_finding)

            historical_record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}"
            _, prior_had_arithmetic_finding = pending_reconciliation.get(historical_record_key, (row, False))
            pending_reconciliation[historical_record_key] = (
                row,
                prior_had_arithmetic_finding or arithmetic_finding is not None,
            )
        processed += len(batch)
        logger.info(f"PP5: processed {processed}/{total} operations, {len(findings)} findings so far")

    # Step 3 — LLM scope understanding, only for operations whose Tier 1 arithmetic is valid
    # (Case B operations are terminal and skip Tier 2 entirely, per spec).
    tier2_keys = {key for key, (_, had_arithmetic_finding) in pending_reconciliation.items() if not had_arithmetic_finding}
    scope_lookup = _pp5_build_scope_lookup(normalized_operations, tier2_keys, agent_c)

    for historical_record_key, (row, any_arithmetic_finding) in pending_reconciliation.items():
        if any_arithmetic_finding:
            continue  # Case B already terminal for this operation — no Tier 2 evidence lookup.
        findings.append(
            _pp5_evidence_reconciliation_check(
                row, historical_record_key, historical_matches, pitstops_ranges, oreda_conn,
                min_comparable_executions,
                matched_jms_rows=matched_jms_rows,
                object_description_lookup=object_description_lookup,
                scope_lookup=scope_lookup,
            )
        )

    logger.info(f"PP5: done, {len(findings)} findings")
    return findings


# ---------------------------------------------------------------------------
# PP6 Check B — Frequency validation (client-approved spec, 2026-10).
#
# Independent of, and never touching, Check A (Strategy consistency) above.
# Resolves each Task List's (STRATEGY, FREQUENCY) against the real
# Maintenance Strategy Master, parses the resolved row's real Maintenance
# cycle text into a calendar interval, anchors to the earliest real Work
# Order execution for the Task List's Maintenance Item(s), and walks the
# expected-cycle sequence forward to today to classify Covered/Missed.
# ---------------------------------------------------------------------------

import datetime as _dt

from dateutil.relativedelta import relativedelta as _relativedelta


def build_maintenance_strategy_lookup(
    maintenance_strategy_master: pd.DataFrame,
) -> dict[tuple[str, str], list[dict]]:
    """Index the real Maintenance Strategy Master by (Maintenance strategy, Cycle short text).

    Multiple rows can share the same key (confirmed real — e.g. PCSB25+'12' resolves to both
    Package 5 and Package 22) — callers must never arbitrarily pick one; see
    `_pp6_resolve_strategy_frequency` below, which surfaces >1 match as FREQUENCY_AMBIGUOUS_PACKAGE.
    """
    lookup: dict[tuple[str, str], list[dict]] = {}
    for r in maintenance_strategy_master.to_dict("records"):
        strategy = _none_if_na(r.get("Maintenance strategy"))
        cycle_short_text = _none_if_na(r.get("Cycle short text"))
        if strategy is None or cycle_short_text is None:
            continue
        key = (str(strategy).strip(), str(cycle_short_text).strip())
        lookup.setdefault(key, []).append(r)
    return lookup


# Pattern A: "<number>[space/dash]<...MONTH or YEAR...>" — e.g. "12 MONTHLY PPM", "1.5 Yearly PM",
# "10-YEARLY PM". The unit word (MONTH/YEAR) need not immediately follow the number — real examples
# like "2-MONTHLY PM PIGGING" and "3-MONTHLY Operational Pigging" have trailing free text too.
_CYCLE_PATTERN_A_RE = re.compile(r"^(\d+(?:\.\d+)?)[\s-]+.*\b(MONTH|YEAR)", re.IGNORECASE)

# Pattern B: "<number>M-<anything>" — e.g. "12M-CMPE PM", "6M-CMPE PM" — trailing bare "M" means
# MONTHS here, distinct from Pattern A's spelled-out MONTH/YEAR. Checked BEFORE Pattern A since
# text like "36M-MONTHLY PPM" also contains the word MONTHLY later in the string.
_CYCLE_PATTERN_B_RE = re.compile(r"^(\d+(?:\.\d+)?)M-", re.IGNORECASE)

# Pattern C: bare unit word, no leading number — implicitly 1 of that unit.
_CYCLE_PATTERN_C_RE = re.compile(r"^(DAILY|WEEKLY|MONTHLY|YEARLY)\b", re.IGNORECASE)

# Pattern D: "BI-<unit>" — 2 of that unit.
_CYCLE_PATTERN_D_RE = re.compile(r"^BI-(DAILY|WEEKLY|MONTHLY|YEARLY)\b", re.IGNORECASE)

_CYCLE_UNIT_FROM_WORD = {
    "DAY": "days", "DAILY": "days",
    "WEEK": "weeks", "WEEKLY": "weeks",
    "MONTH": "months", "MONTHLY": "months",
    "YEAR": "years", "YEARLY": "years",
}


def parse_maintenance_cycle_text(cycle_text: str | None) -> tuple[float, str] | None:
    """Parse a real Maintenance cycle text into (quantity, unit) where unit in
    {"days", "weeks", "months", "years"}. Returns None when unparseable — e.g. confirmed real,
    non-Bokor-reachable examples "120-CMPE PM" (no unit suffix) and "PRBI/SSI CYCLE PM". Never
    guesses a unit; a global code->interval mapping is deliberately never used (see client's
    1X/PCSB25-vs-PCSB52 correction) — only this row's own real cycle text is ever parsed.
    """
    if cycle_text is None:
        return None
    text = str(cycle_text).strip()
    if not text:
        return None

    m = _CYCLE_PATTERN_D_RE.match(text)
    if m:
        unit_word = m.group(1).upper()
        return 2.0, _CYCLE_UNIT_FROM_WORD[unit_word]

    m = _CYCLE_PATTERN_B_RE.match(text)
    if m:
        return float(m.group(1)), "months"

    m = _CYCLE_PATTERN_A_RE.match(text)
    if m:
        quantity = float(m.group(1))
        unit_word = m.group(2).upper()
        return quantity, _CYCLE_UNIT_FROM_WORD[unit_word]

    m = _CYCLE_PATTERN_C_RE.match(text)
    if m:
        unit_word = m.group(1).upper()
        return 1.0, _CYCLE_UNIT_FROM_WORD[unit_word]

    return None


def _add_interval(anchor: _dt.date, step_number: int, quantity: float, unit: str) -> _dt.date:
    """Real-calendar stepping — `step_number` whole intervals of (quantity, unit) added to anchor.

    Uses dateutil.relativedelta for months/years so e.g. Jan 31 + 1 month lands on a valid Feb
    date (clamped, never crashes/wraps) rather than naive 30/365-day multiplication. Fractional
    quantities (e.g. 1.5 years) are converted to whole months before stepping, since relativedelta
    itself does not accept fractional months/years.
    """
    if unit == "days":
        return anchor + _dt.timedelta(days=quantity * step_number)
    if unit == "weeks":
        return anchor + _dt.timedelta(weeks=quantity * step_number)
    if unit == "months":
        total_months = quantity * step_number
        whole_months = round(total_months)
        return anchor + _relativedelta(months=whole_months)
    if unit == "years":
        total_months = quantity * 12 * step_number
        whole_months = round(total_months)
        return anchor + _relativedelta(months=whole_months)
    raise ValueError(f"unrecognized interval unit {unit!r}")


# Threshold for "isolated miss" vs "multiple consecutive misses" (spec step 8 — not pinned to an
# exact number, client-approved judgment call applied here): 1 isolated Missed cycle with a later
# Covered cycle is a one-off gap (FREQUENCY_DEVIATION_REVIEW, lower severity). 2 or more CONSECUTIVE
# Missed cycles that are not followed by any later Covered cycle (i.e. the miss run extends to the
# present) is treated as the stronger FREQUENCY_OVERDUE_HOLD_SUSPECTED finding — two consecutive
# misses already indicates a pattern (a single skipped cycle can be a scheduling slip; two in a row
# with no recovery since is a much stronger signal of a suspended/on-hold plan). A run of 2+
# consecutive misses that IS followed by a later Covered cycle is still only a (larger) one-off gap,
# not an ongoing hold, so it is also reported as FREQUENCY_DEVIATION_REVIEW — what matters for the
# stronger flag is that the miss run reaches all the way to the most recent expected cycle.
_CONSECUTIVE_MISS_THRESHOLD = 2

# PP6_Flag (client spec, 2026-10, final naming): the 7 internal pp6_flag reason codes above
# collapse to exactly 3 client-facing values. VALID = frequency is being followed, or a missed
# cycle was later recovered. ON_HOLD = 2+ consecutive cycles missed with no recovery since
# (FREQUENCY_OVERDUE_HOLD_SUSPECTED only). REVIEW = frequency/status cannot be reliably
# determined from available data — every "can't determine" reason code maps here; the specific
# reason always goes in PP6_Reason, never in this field.
PP6Status = Literal["VALID", "ON_HOLD", "REVIEW"]

_PP6_STATUS_BY_FLAG: dict[str, PP6Status] = {
    "FREQUENCY_NOT_ASSIGNED": "REVIEW",
    "STRATEGY_NOT_IN_REFERENCE": "REVIEW",
    "FREQUENCY_AMBIGUOUS_PACKAGE": "REVIEW",
    "CYCLE_TEXT_UNPARSEABLE": "REVIEW",
    "NO_EXECUTION_HISTORY": "REVIEW",
    "FREQUENCY_DEVIATION_REVIEW": "VALID",
    "FREQUENCY_OVERDUE_HOLD_SUSPECTED": "ON_HOLD",
}


def _pp6_resolve_strategy_frequency(
    strategy: str, frequency: str, strategy_lookup: dict[tuple[str, str], list[dict]]
) -> tuple[str | None, list[dict], str]:
    """Returns (flag_or_None, matching_rows, detail_text). flag is None iff exactly 1 match."""
    key = (str(strategy).strip(), str(frequency).strip())
    matches = strategy_lookup.get(key, [])
    if not matches:
        return (
            "STRATEGY_NOT_IN_REFERENCE",
            [],
            (
                f"(STRATEGY, FREQUENCY) = ('{strategy}', '{frequency}') has 0 matching rows in the "
                "Maintenance Strategy Master (ground_truth_cache/Maintenance_Strategy_Master.xlsx, "
                "13 sheets) — this Strategy/Frequency combination is not covered by any of the "
                "13 reference sheets available to this project"
            ),
        )
    if len(matches) > 1:
        candidates = "; ".join(
            f"Package {m.get('Package')} '{m.get('Strategy description')}' "
            f"(cycle text '{m.get('Maintenance cycle text')}')"
            for m in matches
        )
        return (
            "FREQUENCY_AMBIGUOUS_PACKAGE",
            matches,
            (
                f"(STRATEGY, FREQUENCY) = ('{strategy}', '{frequency}') resolves to "
                f"{len(matches)} DIFFERENT Package rows in the Maintenance Strategy Master — "
                f"candidates: {candidates} — never arbitrarily resolved to one"
            ),
        )
    return None, matches, ""


def _pp6_collect_finish_dates(
    group: str, group_counter: str, work_order_finish_dates_by_key: dict[tuple[str, str], list[_dt.date]]
) -> list[_dt.date]:
    return sorted(work_order_finish_dates_by_key.get((str(group), str(group_counter)), []))


def _to_date(value) -> _dt.date | None:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    try:
        ts = pd.Timestamp(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(ts):
        return None
    return ts.date()


class _PP6Verdict(NamedTuple):
    pp6_flag: str | None
    suggested_interval: str | None
    reason: str  # plain-language sentence — PP6_Reason (client-facing, no technical jargon)
    evidence_detail: str  # structured field-list — PP6_Evidence (frequency/last completed/missed cycles/...)
    evidence_source: str
    pp6_status: "PP6Status"
    first_missed_cycle: str | None
    consecutive_missed_cycles: int


def _pp6_frequency_check_for_task_list(
    group: str,
    group_counter: str,
    strategy: str | None,
    frequency: str | None,
    strategy_lookup: dict[tuple[str, str], list[dict]],
    finish_dates: list[_dt.date],
    today: _dt.date,
) -> _PP6Verdict:
    """Always returns a verdict — every Task List gets a PP6_Status (VALID included), mirroring
    PP5's evidence_level convention, so PP6_First_Missed_Cycle/PP6_Consecutive_Missed_Cycles have
    a row to report against even when the plan is currently fine.
    """
    master_source = "ground_truth_cache/Maintenance_Strategy_Master.xlsx (13 real sheets, concatenated)"

    if frequency is None or str(frequency).strip() == "":
        return _PP6Verdict(
            "FREQUENCY_NOT_ASSIGNED",
            None,
            "Maintenance frequency could not be validated because no Frequency code is assigned "
            "to this Task List yet.",
            "No Frequency code assigned.",
            "Bokor Long Text_Aug26_LATEST.xlsm (FREQUENCY blank)",
            _PP6_STATUS_BY_FLAG["FREQUENCY_NOT_ASSIGNED"],
            None,
            0,
        )

    if strategy is None or str(strategy).strip() == "":
        return _PP6Verdict(
            "STRATEGY_NOT_IN_REFERENCE",
            None,
            f"Maintenance frequency could not be validated because this Task List has Frequency "
            f"'{frequency}' but no Maintenance Strategy assigned, so it cannot be matched against "
            "the Maintenance Strategy Master.",
            f"Frequency: {frequency}; Strategy: not assigned.",
            "Bokor Long Text_Aug26_LATEST.xlsm (STRATEGY blank); " + master_source,
            _PP6_STATUS_BY_FLAG["STRATEGY_NOT_IN_REFERENCE"],
            None,
            0,
        )

    flag, matches, detail = _pp6_resolve_strategy_frequency(strategy, frequency, strategy_lookup)
    if flag == "STRATEGY_NOT_IN_REFERENCE":
        return _PP6Verdict(
            flag,
            None,
            f"Maintenance frequency could not be validated because Strategy '{strategy}' with "
            f"Frequency '{frequency}' does not match any entry in the Maintenance Strategy Master.",
            f"Strategy: {strategy}; Frequency: {frequency}; {detail}",
            f"Bokor Long Text_Aug26_LATEST.xlsm; {master_source}",
            _PP6_STATUS_BY_FLAG[flag],
            None,
            0,
        )
    if flag == "FREQUENCY_AMBIGUOUS_PACKAGE":
        candidate_packages = ", ".join(
            f"Package {m.get('Package')} ('{m.get('Maintenance cycle text')}')" for m in matches
        )
        return _PP6Verdict(
            flag,
            None,
            f"Maintenance frequency could not be validated because Strategy '{strategy}' with "
            f"Frequency '{frequency}' matches multiple maintenance packages. The correct package "
            "cannot be determined without additional information.",
            f"Strategy: {strategy}; Frequency: {frequency}; Matching packages: {candidate_packages}.",
            f"Bokor Long Text_Aug26_LATEST.xlsm; {master_source}",
            _PP6_STATUS_BY_FLAG[flag],
            None,
            0,
        )

    (row,) = matches
    cycle_text = _none_if_na(row.get("Maintenance cycle text"))
    follow_up_float = _none_if_na(row.get("Follow-up float"))
    package = row.get("Package")

    parsed = parse_maintenance_cycle_text(cycle_text)
    if parsed is None:
        return _PP6Verdict(
            "CYCLE_TEXT_UNPARSEABLE",
            None,
            f"Maintenance frequency could not be validated because the maintenance cycle text "
            f"for Strategy '{strategy}' with Frequency '{frequency}' ('{cycle_text}') does not "
            "follow a recognised format, so the interval cannot be determined.",
            f"Strategy: {strategy}; Frequency: {frequency}; Package: {package}; "
            f"Maintenance cycle text: '{cycle_text}' (unparseable).",
            f"Bokor Long Text_Aug26_LATEST.xlsm; {master_source} (Package {package})",
            _PP6_STATUS_BY_FLAG["CYCLE_TEXT_UNPARSEABLE"],
            None,
            0,
        )
    quantity, unit = parsed
    interval_text = f"{quantity:g} {unit}"

    if follow_up_float is None:
        follow_up_days = 0.0
    else:
        try:
            follow_up_days = float(follow_up_float)
        except (TypeError, ValueError):
            follow_up_days = 0.0

    if not finish_dates:
        return _PP6Verdict(
            "NO_EXECUTION_HISTORY",
            interval_text,
            f"Maintenance frequency is {interval_text}, but no completed maintenance was found "
            "for this Task List, so the frequency cannot be validated against real execution "
            "history.",
            f"Frequency: {interval_text}; Package: {package} ('{cycle_text}'); "
            "Last completed: none found.",
            (
                "Knowledge Graph (live): WorkOrder -FOR_MAINTENANCE_ITEM-> MaintenanceItem "
                f"(0 Work Orders found); {master_source} (Package {package})"
            ),
            _PP6_STATUS_BY_FLAG["NO_EXECUTION_HISTORY"],
            None,
            0,
        )

    anchor = finish_dates[0]
    cycles: list[tuple[_dt.date, bool, _dt.date | None]] = []  # (expected_date, covered, matched_wo_date)
    step_number = 0
    while True:
        expected = _add_interval(anchor, step_number, quantity, unit)
        if expected > today:
            break
        window_end = expected + _dt.timedelta(days=follow_up_days)
        covered_date = next(
            (d for d in finish_dates if expected <= d <= window_end), None
        )
        cycles.append((expected, covered_date is not None, covered_date))
        step_number += 1
        if step_number > 2000:  # safety valve — never loop unbounded on a malformed interval
            break

    evidence_source = (
        "Knowledge Graph (live): WorkOrder -FOR_MAINTENANCE_ITEM-> MaintenanceItem "
        f"(basic_finish_date, {len(finish_dates)} real Work Orders); {master_source} (Package {package})"
    )
    anchor_caveat = "Schedule anchor is based on the earliest known execution date; original SAP schedule date was not available."

    def _cycle_label(expected: _dt.date) -> str:
        return expected.strftime("%B %Y")

    anchor_label = _cycle_label(anchor)

    if not cycles:
        # Anchor itself is in the future relative to "today" or no interval has elapsed yet.
        return _PP6Verdict(
            None,
            interval_text,
            f"Maintenance frequency is {interval_text}. The first expected cycle has not yet "
            "arrived since the earliest known execution, so there is nothing to validate yet.",
            f"Frequency: {interval_text}; Last completed: {anchor_label}; "
            f"Next expected cycle not yet due. {anchor_caveat}",
            evidence_source,
            "VALID",
            None,
            0,
        )

    missed = [c for c in cycles if not c[1]]
    covered = [c for c in cycles if c[1]]

    if not missed:
        last_covered = covered[-1]
        last_covered_label = _cycle_label(last_covered[0])
        return _PP6Verdict(
            None,
            interval_text,
            f"Maintenance frequency is {interval_text}. The last completed maintenance was in "
            f"{last_covered_label} and the next cycle is still within the allowed period. The "
            "Maintenance Plan is currently following its assigned frequency.",
            f"Frequency: {interval_text}; Last completed: {last_covered_label} "
            f"(execution found on {last_covered[2].isoformat()}); Missed cycles: none; "
            f"Consecutive missed cycles: 0. {anchor_caveat}",
            evidence_source,
            "VALID",
            None,
            0,
        )

    # Classify: find the longest trailing run of consecutive misses (a run ending at the last cycle).
    trailing_miss_run = 0
    for _expected, is_covered, _wo in reversed(cycles):
        if is_covered:
            break
        trailing_miss_run += 1

    missed_labels = ", ".join(_cycle_label(c[0]) for c in missed)
    last_covered_before_misses = covered[-1] if covered else None

    # PP6_First_Missed_Cycle (client spec, 2026-10): the earliest missed cycle in the whole
    # sequence, not just the trailing run — "when did this start" evidence for the reviewer.
    first_missed_label = _cycle_label(missed[0][0])

    if trailing_miss_run >= _CONSECUTIVE_MISS_THRESHOLD:
        trailing_missed_labels = ", ".join(_cycle_label(c[0]) for c in missed[-trailing_miss_run:])
        last_completed_label = (
            _cycle_label(last_covered_before_misses[0]) if last_covered_before_misses is not None else "never"
        )
        return _PP6Verdict(
            "FREQUENCY_OVERDUE_HOLD_SUSPECTED",
            interval_text,
            f"Maintenance frequency is {interval_text}. The last completed maintenance was in "
            f"{last_completed_label}. The {trailing_missed_labels} cycle(s) were not completed. "
            f"{trailing_miss_run} consecutive cycles have therefore been missed, so the "
            "Maintenance Plan is flagged as ON_HOLD for validation.",
            f"Frequency: {interval_text}; Last completed: {last_completed_label}; "
            f"Missed cycles: {trailing_missed_labels}; "
            f"Consecutive missed cycles: {trailing_miss_run}. {anchor_caveat} (Package {package}, "
            f"'{cycle_text}', Follow-up tolerance {follow_up_float} days.)",
            evidence_source,
            _PP6_STATUS_BY_FLAG["FREQUENCY_OVERDUE_HOLD_SUSPECTED"],
            first_missed_label,
            trailing_miss_run,
        )

    recovered_label = _cycle_label(covered[-1][0])
    return _PP6Verdict(
        "FREQUENCY_DEVIATION_REVIEW",
        interval_text,
        f"Maintenance frequency is {interval_text}. The {missed_labels} cycle(s) were missed, but "
        f"maintenance was completed in {recovered_label} and subsequent cycles were completed. "
        "The plan has recovered and is currently following its frequency.",
        f"Frequency: {interval_text}; Missed cycles: {missed_labels}; Recovered: {recovered_label}; "
        f"Consecutive missed cycles: {trailing_miss_run}. {anchor_caveat} (Package {package}, "
        f"'{cycle_text}', Follow-up tolerance {follow_up_float} days.)",
        evidence_source,
        _PP6_STATUS_BY_FLAG["FREQUENCY_DEVIATION_REVIEW"],
        first_missed_label,
        trailing_miss_run,
    )


def run_pp6_frequency_check(
    task_list_group: pd.DataFrame,
    normalized_operations: pd.DataFrame,
    maintenance_strategy_master: pd.DataFrame | None,
    work_order_history: pd.DataFrame | None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    today: _dt.date | None = None,
) -> list[Finding]:
    """PP6 Check B — Frequency validation (spec steps 1-10). Independent of Check A."""
    findings: list[Finding] = []
    if maintenance_strategy_master is None:
        logger.info("PP6: Check B (Frequency) skipped — no Maintenance Strategy Master available")
        return findings

    today = today or _dt.date.today()
    strategy_lookup = build_maintenance_strategy_lookup(maintenance_strategy_master)

    # STRATEGY resolution (fixed 2026-10-06, client-confirmed root cause):
    # TaskListOperation nodes never received a real `strategy` property
    # when the KG was built (confirmed directly — the property doesn't
    # exist on that node type at all, despite the raw Long Text Excel
    # source having STRATEGY populated on 99.99% of rows), and
    # TaskList.strategy is itself populated on only 3/951 real nodes —
    # both are effectively unusable. MaintenanceItem.maintenance_strategy
    # is a real, separately-loaded KG property, populated on 5,823/8,025
    # Maintenance Items (72.6%), and resolves to a real, non-null value
    # for all 951/951 real Task Lists when joined via USES_TASK_LIST
    # (verified: zero Task Lists have disagreeing Strategy values across
    # their own linked Maintenance Items — always exactly one real value
    # or all-null, never a genuine conflict). task_list_group already
    # carries this field as "Maintenance Strategy" (the same column
    # Check A already reads as its "current value") — use it here too,
    # instead of the near-empty per-operation reconstruction. FREQUENCY
    # has no such KG gap (it's a real TaskListOperation property) and is
    # still read from normalized_operations as before.
    frequency_lookup: dict[tuple[str, str], str | None] = {}
    for row in normalized_operations.to_dict("records"):
        key = (str(row["TLGRP"]), str(row["TLGRPCOUNT"]))
        if key not in frequency_lookup:
            frequency_lookup[key] = _none_if_na(row.get("FREQUENCY"))

    strategy_by_key: dict[tuple[str, str], str | None] = {}
    for row in task_list_group.dropna(subset=["Group", "Group Counter"]).to_dict("records"):
        key = (str(row["Group"]), str(row["Group Counter"]))
        if key not in strategy_by_key:
            strategy_by_key[key] = _none_if_na(row.get("Maintenance Strategy"))

    strategy_frequency_lookup: dict[tuple[str, str], tuple[str | None, str | None]] = {
        key: (strategy_by_key.get(key), frequency_lookup.get(key))
        for key in set(strategy_by_key) | set(frequency_lookup)
    }

    work_order_finish_dates_by_key: dict[tuple[str, str], list[_dt.date]] = {}
    if work_order_history is not None:
        for r in work_order_history.dropna(subset=["Group", "Group Counter"]).to_dict("records"):
            finish = _to_date(r.get("Basic finish date"))
            if finish is None:
                continue
            key = (str(r["Group"]), str(r["Group Counter"]))
            work_order_finish_dates_by_key.setdefault(key, []).append(finish)

    task_list_keys = task_list_group[["Group", "Group Counter"]].dropna().astype(str).drop_duplicates()
    verdict_by_key: dict[tuple[str, str], _PP6Verdict] = {}
    total_keys = len(task_list_keys)
    logger.info(f"PP6: Check B (Frequency), {total_keys} distinct Task List Groups")
    processed = 0
    for batch in batched(task_list_keys.to_dict("records"), batch_size):
        for row in batch:
            key = (row["Group"], row["Group Counter"])
            strategy, frequency = strategy_frequency_lookup.get(key, (None, None))
            finish_dates = _pp6_collect_finish_dates(key[0], key[1], work_order_finish_dates_by_key)
            verdict_by_key[key] = _pp6_frequency_check_for_task_list(
                key[0], key[1], strategy, frequency, strategy_lookup, finish_dates, today,
            )
        processed += len(batch)
        logger.info(f"PP6: Check B, processed {processed}/{total_keys} Task List Groups")

    bridge_rows = task_list_group.to_dict("records")
    for row in bridge_rows:
        key = (str(row["Group"]), str(row["Group Counter"]))
        verdict = verdict_by_key.get(key)
        if verdict is None:
            continue
        # Every Task List now gets a Finding — including VALID (all-covered / isolated-recovered-
        # miss / nothing-elapsed-yet) — so PP6_Status/PP6_First_Missed_Cycle/
        # PP6_Consecutive_Missed_Cycles always have a row to report against (client spec, 2026-10;
        # mirrors PP5's evidence_level convention). The curated *_Findings sheet still filters
        # VALID out via _has_finding_signal, same as every other pain point.
        findings.append(
            Finding(
                pain_point="PP6",
                record_key=str(row["Maintenance Item"]),
                field_name="Frequency",
                current_value=_none_if_na(row.get("Maintenance Strategy")),
                recommended_value=None,
                confidence=None,
                detection_confidence=None,
                reason=verdict.reason,
                evidence_source=verdict.evidence_source,
                pp6_flag=verdict.pp6_flag,
                candidate_value=verdict.suggested_interval,
                pp6_status=verdict.pp6_status,
                pp6_first_missed_cycle=verdict.first_missed_cycle,
                pp6_consecutive_missed_cycles=verdict.consecutive_missed_cycles,
                pp6_evidence_detail=verdict.evidence_detail,
            )
        )

    logger.info(f"PP6: Check B done, {len(findings)} findings")
    return findings


def run_pp6(
    task_list_group: pd.DataFrame,
    normalized_operations: pd.DataFrame,
    batch_size: int = DEFAULT_BATCH_SIZE,
    maintenance_strategy_master: pd.DataFrame | None = None,
    work_order_history: pd.DataFrame | None = None,
    today: _dt.date | None = None,
) -> list[Finding]:
    # Check B (Active Equipment without Maintenance Plan) was removed
    # (2026-10-05, client-confirmed): it duplicated PP7's Hanging
    # Maintenance Item check from the Equipment side rather than the
    # Maintenance Item side, and per the original process spec's own
    # step numbering, that kind of orphan/hanging detection belongs to
    # PP7, not PP6 (Strategy/Frequency). PP6 is Strategy-consistency-only
    # until Frequency validation (the spec's actual second PP6 check) is
    # built.
    findings: list[Finding] = []

    op_strategy_lookup = {
        (row["TLGRP"], row["TLGRPCOUNT"]): row["STRATEGY"]
        for row in normalized_operations.to_dict("records")
    }
    bridge_rows = task_list_group.to_dict("records")
    logger.info(f"PP6: Check A (Strategy consistency), {len(bridge_rows)} bridge rows")
    processed = 0
    for batch in batched(bridge_rows, batch_size):
        for row in batch:
            op_strategy = _none_if_na(op_strategy_lookup.get((row["Group"], row["Group Counter"])))
            maintenance_strategy = _none_if_na(row["Maintenance Strategy"])
            if op_strategy is not None and maintenance_strategy is not None and op_strategy != maintenance_strategy:
                findings.append(
                    Finding(
                        pain_point="PP6",
                        record_key=str(row["Maintenance Item"]),
                        field_name="Maintenance Strategy",
                        current_value=maintenance_strategy,
                        recommended_value=op_strategy,
                        confidence=confidence_label(0.95),
                        detection_confidence=0.95,
                        reason=(
                            f"Maintenance Item's Strategy '{maintenance_strategy}' does not match "
                            f"its Task List's Strategy '{op_strategy}'; per UDMS §9.12/§11.2 the "
                            f"Task List Strategy is authoritative, so the Item's Strategy should be "
                            f"corrected to '{op_strategy}'"
                        ),
                        evidence_source="Bokor Task List Group.xlsx; Bokor Long Text_Aug26_LATEST.xlsm; UDMS.pdf §9.12, §11.2",
                    )
                )
        processed += len(batch)
        logger.info(f"PP6: Check A, processed {processed}/{len(bridge_rows)} bridge rows")

    # Check B (Frequency) — independent, additive second check. Never touches Check A's findings
    # or logic above; only appends its own findings to the same list.
    frequency_findings = run_pp6_frequency_check(
        task_list_group, normalized_operations, maintenance_strategy_master, work_order_history,
        batch_size=batch_size, today=today,
    )
    findings += frequency_findings

    logger.info(f"PP6: done, {len(findings)} findings ({len(frequency_findings)} from Check B Frequency)")
    return findings


def run_pp7(task_list_group: pd.DataFrame, batch_size: int = DEFAULT_BATCH_SIZE) -> list[Finding]:
    findings: list[Finding] = []
    bridge_rows = task_list_group.to_dict("records")
    logger.info(f"PP7: starting, {len(bridge_rows)} Maintenance Items")
    processed = 0
    for batch in batched(bridge_rows, batch_size):
        for row in batch:
            maintenance_item = row["Maintenance Item"]
            maintenance_plan = _none_if_na(row.get("Maintenance Plan"))
            if maintenance_plan is not None:
                continue  # VALID — a real HAS_ITEM edge resolves to this Plan; not a finding
            findings.append(
                Finding(
                    pain_point="PP7",
                    record_key=str(maintenance_item),
                    field_name="Maintenance Plan",
                    current_value=None,
                    recommended_value=None,
                    confidence=None,
                    detection_confidence=0.95,
                    reason=(
                        f"Maintenance Item '{maintenance_item}' is flagged as a Hanging Maintenance "
                        "Item because no Maintenance Plan relationship (HAS_ITEM edge) exists for it "
                        "in the Knowledge Graph — per UDMS §10, every Maintenance Item should be "
                        "linked to a Maintenance Plan"
                    ),
                    evidence_source=(
                        f"Maintenance Item {maintenance_item}; Knowledge Graph HAS_ITEM "
                        "(MaintenancePlan -> MaintenanceItem) relationship count = 0; UDMS.pdf §10"
                    ),
                )
            )
        processed += len(batch)
        logger.info(f"PP7: processed {processed}/{len(bridge_rows)} Maintenance Items, {len(findings)} findings so far")
    logger.info(f"PP7: done, {len(findings)} findings")
    return findings
