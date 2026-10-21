import pandas as pd

RECONCILE_TOLERANCE_FRACTION = 0.05  # crew_size x hours_per_task vs. stated total_manhours
QUANTITY_CAVEAT_KEYWORDS = ("day-window", "elapsed", "not granular", "calendar")


def _normalize(text: str) -> str:
    return "".join(ch for ch in str(text).upper() if ch.isalnum())


def _parse_positive_number(value) -> float | None:
    try:
        parsed = float(str(value).strip())
    except (ValueError, TypeError):
        return None
    return parsed if parsed > 0 else None


def _find_candidate_operations(equipment_tag: str, normalized_operations: pd.DataFrame) -> list[dict]:
    if not equipment_tag:
        return []
    tag_normalized = _normalize(equipment_tag)
    if not tag_normalized:
        return []
    candidates = []
    for op in normalized_operations.to_dict("records"):
        combined_text = _normalize(f"{op.get('OPDESC', '')} {op.get('LONGTEXT_AGGREGATED', '')}")
        if tag_normalized in combined_text:
            candidates.append(op)
    return candidates


def _description_corroborates(job_description: str, op: dict) -> bool:
    if not job_description:
        return False
    desc_normalized = _normalize(job_description)
    combined_text = _normalize(f"{op.get('OPDESC', '')} {op.get('LONGTEXT_AGGREGATED', '')}")
    return desc_normalized in combined_text or combined_text in desc_normalized


def _validate_quantities(row: dict) -> tuple[bool, str | None]:
    notes = str(row.get("notes", "") or "").lower()
    if any(keyword in notes for keyword in QUANTITY_CAVEAT_KEYWORDS):
        return False, "extraction notes flag this quantity as a day-window/elapsed figure, not validated labor hours"

    crew_size = _parse_positive_number(row.get("crew_size"))
    hours_per_task = _parse_positive_number(row.get("hours_per_task"))
    total_manhours = _parse_positive_number(row.get("total_manhours"))

    if crew_size is None:
        return False, "crew_size missing or not a positive number"
    if hours_per_task is None and total_manhours is None:
        return False, "neither hours_per_task nor total_manhours is a positive number"

    if crew_size is not None and hours_per_task is not None and total_manhours is not None:
        computed = crew_size * hours_per_task
        if abs(computed - total_manhours) > RECONCILE_TOLERANCE_FRACTION * max(computed, total_manhours):
            return False, (
                f"crew_size x hours_per_task ({computed}) does not reconcile with the document's "
                f"stated total_manhours ({total_manhours}) within {RECONCILE_TOLERANCE_FRACTION:.0%} tolerance"
            )
    return True, None


def match_jms_to_operations(extraction_df: pd.DataFrame, normalized_operations: pd.DataFrame) -> pd.DataFrame:
    results = []
    for row in extraction_df.to_dict("records"):
        row = dict(row)
        existing_notes = str(row.get("notes", "") or "")

        if str(row.get("platform_verified_bokor", "")).strip().upper() != "TRUE":
            results.append({**row, "sap_record_key": None, "evidence_status": "Excluded — Platform"})
            continue

        candidates = _find_candidate_operations(row.get("equipment_tag", ""), normalized_operations)
        distinct_keys = {(c["TLGRP"], c["TLGRPCOUNT"], c["TLOPNO"]) for c in candidates}
        if len(distinct_keys) > 1:
            note = f"rejected as ambiguous — tag matched {len(distinct_keys)} distinct operations: {sorted(distinct_keys)}"
            results.append({**row, "notes": f"{existing_notes}; {note}".strip("; "), "sap_record_key": None, "evidence_status": "No Match"})
            continue
        if not candidates:
            results.append({**row, "sap_record_key": None, "evidence_status": "No Match"})
            continue

        matched_op = candidates[0]
        if not _description_corroborates(row.get("job_description", ""), matched_op):
            results.append({**row, "sap_record_key": None, "evidence_status": "No Match"})
            continue

        record_key = f"{matched_op['TLGRP']}-{matched_op['TLGRPCOUNT']}-{matched_op['TLOPNO']}"
        is_valid, invalid_reason = _validate_quantities(row)
        if not is_valid:
            note = f"Incomplete: {invalid_reason}"
            results.append({**row, "notes": f"{existing_notes}; {note}".strip("; "), "sap_record_key": record_key, "evidence_status": "Incomplete"})
            continue

        results.append({**row, "sap_record_key": record_key, "evidence_status": "Complete"})

    return pd.DataFrame(results)
