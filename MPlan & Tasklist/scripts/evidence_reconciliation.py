from dataclasses import dataclass, field

import pandas as pd

# ---------------------------------------------------------------------------
# PP5 reconciliation model (client spec, 2026-10) — JMS + Historical
# convergence/conflict only. PITSTOPS is supporting-only (duration
# plausibility, Step 14). OREDA is last-resort-only (Step 15). Never a
# median: historical evidence is always an observed min-max RANGE: a
# specific Suggested_WORK figure is only ever populated from JMS (a direct,
# independent job-level total), never manufactured from a historical range
# alone.
# ---------------------------------------------------------------------------


def _fmt_hours(value: float) -> str:
    """Display-only rounding (6 dp) to avoid raw float noise (e.g. 7.6000000000000005) in
    reason/evidence text — the underlying stored value is never rounded, only its text rendering.
    """
    rounded = round(value, 6)
    return str(int(rounded)) if rounded == int(rounded) else str(rounded)


@dataclass
class HistoricalRangeResult:
    available: bool
    min_hours: float | None
    max_hours: float | None
    execution_count: int
    reason: str
    source: str
    below_threshold_candidate_hours: list[float] = field(default_factory=list)


HISTORICAL_SOURCE = "Timesheet BOKOR 2024/2025; M014_Bokor_Non PPM Work Order 2020_2025.xlsx; BOKOR_PPM_Listing_2016_2025.xlsx"


def historical_range_lane(
    record_key: str,
    historical_matches: pd.DataFrame | None,
    min_comparable_executions: int,
) -> HistoricalRangeResult:
    """Step 6-9: comparable historical executions -> an observed min-max RANGE (never a median)."""
    if historical_matches is None:
        return HistoricalRangeResult(False, None, None, 0, "No historical match data supplied", HISTORICAL_SOURCE)
    match_rows = historical_matches[historical_matches["record_key"] == record_key]
    if match_rows.empty:
        return HistoricalRangeResult(False, None, None, 0, "No historical match found for this operation", HISTORICAL_SOURCE)
    match = match_rows.iloc[0]
    candidate_hours = list(match["candidate_hours"])
    if len(candidate_hours) < min_comparable_executions:
        return HistoricalRangeResult(
            False, None, None, len(candidate_hours),
            f"Only {len(candidate_hours)} verified comparable historical execution(s) found, "
            f"fewer than the minimum of {min_comparable_executions} required for a defensible range",
            HISTORICAL_SOURCE,
            below_threshold_candidate_hours=candidate_hours,
        )
    min_hours = float(min(candidate_hours))
    max_hours = float(max(candidate_hours))
    return HistoricalRangeResult(
        True, min_hours, max_hours, len(candidate_hours),
        f"Observed range of {len(candidate_hours)} verified comparable historical executions is "
        f"{_fmt_hours(min_hours)}-{_fmt_hours(max_hours)} MHR (values: {candidate_hours})",
        HISTORICAL_SOURCE,
    )


def tasklist_worklist_lane(
    opwkcen: str | None, pitstops_ranges: pd.DataFrame | None, sap_duration_hours: float | None = None
) -> str | None:
    """Step 14: PITSTOPS duration plausibility ONLY — returns annotation text or None.

    Never a WORK source, never part of the VALID/REVIEW_REQUIRED/CONFLICT decision.
    """
    if pitstops_ranges is None or opwkcen is None or sap_duration_hours is None:
        return None

    from evidence_connectors.pitstops_connector import DISCIPLINE_TO_OPWKCEN

    discipline = DISCIPLINE_TO_OPWKCEN.get(opwkcen)
    if discipline is None:
        return None
    matching = pitstops_ranges[pitstops_ranges["Discipline"] == discipline]
    if matching.empty:
        return None
    row = matching.iloc[0]
    within_range = row["min_hrs"] <= sap_duration_hours <= row["max_hrs"]
    return (
        f"PITSTOPS (supporting only, not a WORK source): SAP DURATION ({sap_duration_hours} hrs) is "
        f"{'within' if within_range else 'OUTSIDE'} the PITSTOPS '{discipline}' Discipline-level "
        f"duration range {row['min_hrs']}-{row['max_hrs']} hrs (n={row['n']}) — Discipline-level "
        "comparison only, not this specific operation"
    )


OREDA_FAILURE_MODE_PRIORITY = ["Breakdown", "Critical", "Structural deficiency", "All modes"]


@dataclass
class OredaResult:
    available: bool
    value: float | None
    reason: str
    source: str = "Knowledge Graph (oreda_data table)"


def oreda_lane(
    row: dict, oreda_conn, item_hint: str | None = None, is_general_repair_comparable: bool = False
) -> OredaResult:
    """Step 15: OREDA — last-resort only. Caller must already have confirmed both Historical and
    JMS are unavailable before using this; whenever OREDA is used, the result is ALWAYS
    REVIEW_REQUIRED (provisional), NEVER VALID.
    """
    source = "Knowledge Graph (oreda_data table)"
    if oreda_conn is None:
        return OredaResult(False, None, "No Knowledge Graph connection supplied to query OREDA", source)
    if item_hint is None:
        return OredaResult(
            False, None,
            "OREDA_NOT_APPLICABLE: no equipment/technical-object-type mapping is available "
            "to look up an OREDA item for this operation",
            source,
        )
    if not is_general_repair_comparable:
        return OredaResult(
            False, None,
            f"OREDA_NOT_APPLICABLE: item_hint resolved to '{item_hint}', but this operation's "
            "OPDESC/LONGTEXT describes routine inspection/test/calibration/service work, not "
            "general-repair-comparable labour — manhour_repair_mean is a corrective "
            "repair-after-failure quantity, structurally different from routine PM duration, "
            "and is never applied to that scope of work",
            source,
        )
    from evidence_connectors.oreda_connector import query_oreda_category_benchmark

    benchmark, matched_failure_mode = query_oreda_category_benchmark(
        oreda_conn, item_hint=item_hint, failure_modes=OREDA_FAILURE_MODE_PRIORITY
    )
    if benchmark is None:
        return OredaResult(
            False, None,
            f"OREDA_NOT_APPLICABLE: no comparable OREDA repair-hours benchmark found for category "
            f"'{item_hint}' across any of {OREDA_FAILURE_MODE_PRIORITY}",
            source,
        )
    return OredaResult(
        True, benchmark["manhour_repair_mean"],
        f"PROVISIONAL (OREDA last-resort benchmark, not a confirmed Bokor planning value) — "
        f"repair benchmark for category '{item_hint}', failure_mode='{matched_failure_mode}': "
        f"{benchmark['manhour_repair_mean']} MHR across {benchmark['matched_row_count']} matched "
        f"OREDA row(s) (range {benchmark['manhour_repair_min']}-{benchmark['manhour_repair_max']}, "
        f"source p.{benchmark['source_page']}) — operation's OPDESC/LONGTEXT text classified as "
        "general-repair-comparable work (overhaul/replacement-type), not routine PM",
        source,
    )


AGREEMENT_TOLERANCE_FRACTION = 0.10  # of the largest agreeing value — reused from the prior lane-agreement tolerance


@dataclass
class JmsResult:
    available: bool
    value: float | None
    reason: str
    source: str = "ground_truth_cache/PP05_JMS_ManHours.csv"


JMS_MIN_COMPARABLE_ENTRIES = 1  # Step 10-11: a single genuinely-matched, Complete JMS job figure is a direct source


def jms_lane(record_key: str, matched_jms_rows: pd.DataFrame | None, min_comparable_entries: int = JMS_MIN_COMPARABLE_ENTRIES) -> JmsResult:
    """Step 10-11: JMS as a direct reference. UNLIKE historical, a genuinely applicable JMS
    job-level total man-hours figure becomes a real candidate Suggested_WORK value directly.
    """
    source = "ground_truth_cache/PP05_JMS_ManHours.csv"
    if matched_jms_rows is None or matched_jms_rows.empty:
        return JmsResult(False, None, "No JMS workpack evidence found for this operation", source)

    rows_for_operation = matched_jms_rows[matched_jms_rows["sap_record_key"] == record_key]
    if rows_for_operation.empty:
        return JmsResult(False, None, "No JMS workpack evidence found for this operation", source)

    complete_rows = rows_for_operation[rows_for_operation["evidence_status"] == "Complete"]
    if complete_rows.empty:
        status_counts = rows_for_operation["evidence_status"].value_counts().to_dict()
        breakdown = "; ".join(f"{count} {status}" for status, count in status_counts.items())
        return JmsResult(False, None, f"No Complete JMS workpack evidence ({breakdown}, 0 Complete)", source)

    if len(complete_rows) < min_comparable_entries:
        return JmsResult(
            False, None,
            f"Only {len(complete_rows)} Complete JMS workpack match(es) found, fewer than the "
            f"minimum of {min_comparable_entries} required",
            source,
        )

    mhr_values = complete_rows["total_manhours"].astype(float)
    records = complete_rows.to_dict("records")
    citations = "; ".join(f"{r['source_pdf']} p.{r['source_page_number']}" for r in records)
    job_names = "; ".join(sorted({str(r.get("job_description") or "").strip() for r in records if r.get("job_description")}))

    if len(complete_rows) == 1:
        r = records[0]
        crew = r.get("crew_size")
        hours_per_task = r.get("hours_per_task")
        value = float(mhr_values.iloc[0])
        crew_note = f", crew {crew} x {hours_per_task} hrs" if crew and hours_per_task else ""
        return JmsResult(
            True, value,
            f"JMS job '{job_names or r.get('job_description', '')}'{crew_note} gives {value} MHR "
            f"(source: {citations})",
            source,
        )

    if mhr_values.nunique() == 1:
        # Multiple Complete JMS matches for the same operation that all agree exactly — a single
        # real figure, not an average/median manufacture.
        value = float(mhr_values.iloc[0])
        return JmsResult(
            True, value,
            f"JMS job(s) '{job_names}' agree on {value} MHR across {len(complete_rows)} Complete "
            f"match(es) (source: {citations})",
            source,
        )

    # Multiple Complete JMS matches that genuinely disagree with each other: no single defensible
    # JMS figure exists — never pick one arbitrarily, never average/median. Surfaced as unavailable
    # so the caller falls through to CANNOT_VERIFY/Historical-only logic rather than silently
    # trusting one of several conflicting JMS records.
    return JmsResult(
        False, None,
        f"{len(complete_rows)} Complete JMS workpack matches found for this operation, but they "
        f"disagree with each other ({sorted(mhr_values.tolist())} MHR, sources: {citations}) — no "
        "single defensible JMS figure; not used as evidence",
        source,
    )


def values_converge(a: float, b: float, tolerance_fraction: float = AGREEMENT_TOLERANCE_FRACTION) -> bool:
    largest = max(abs(a), abs(b))
    if largest == 0:
        return a == b
    return abs(a - b) <= tolerance_fraction * largest


def jms_within_historical_range(
    jms_value: float, range_min: float, range_max: float, tolerance_fraction: float = AGREEMENT_TOLERANCE_FRACTION
) -> bool:
    """Step 12-13: JMS 'close'/consistent with the Historical range — within the range outright,
    or within AGREEMENT_TOLERANCE_FRACTION of either bound."""
    if range_min <= jms_value <= range_max:
        return True
    if jms_value < range_min:
        return values_converge(jms_value, range_min, tolerance_fraction)
    return values_converge(jms_value, range_max, tolerance_fraction)


@dataclass
class OrderLevelFallbackResult:
    available: bool
    order_level_match_count: int
    candidate_hours: list[float]
    matched_orders: list[str]
    reason: str
    source: str


def order_level_fallback_lane(record_key: str, historical_matches: pd.DataFrame | None) -> OrderLevelFallbackResult:
    """Order-level-only matches (Operation not individually verified). Kept for potential future
    diagnostic use; per the new spec (Steps 6-13) this is NOT a source of Suggested_WORK or of the
    VALID/REVIEW_REQUIRED/CONFLICT decision — only genuinely operation-verified Historical executions
    and JMS drive that decision. Not called by the new PP5 decision path in validation.py.
    """
    source = "BOKOR_10years Work Order Data_Aug26.xlsx (Order-level Description/Equipment/FLOC, not Operation-verified)"
    if historical_matches is None:
        return OrderLevelFallbackResult(False, 0, [], [], "No historical match data supplied", source)
    match_rows = historical_matches[historical_matches["record_key"] == record_key]
    if match_rows.empty:
        return OrderLevelFallbackResult(False, 0, [], [], "No historical match found for this operation", source)
    match = match_rows.iloc[0]
    desc_match_count = int(match.get("order_level_match_count", 0) or 0)
    equipment_floc_match_count = int(match.get("equipment_floc_match_count", 0) or 0)
    match_count = desc_match_count + equipment_floc_match_count
    if match_count == 0:
        blocking_reason = match.get("blocking_reason")
        reason = f"No Order-level Description or Equipment/FLOC match found: {blocking_reason}" if blocking_reason else "No Order-level Description or Equipment/FLOC match found"
        return OrderLevelFallbackResult(False, 0, [], [], reason, source)
    candidate_hours = list(match.get("order_level_candidate_hours") or [])
    matched_orders = list(dict.fromkeys(
        list(match.get("order_level_orders") or []) + list(match.get("equipment_floc_matched_orders") or [])
    ))
    signal_parts = []
    if desc_match_count:
        signal_parts.append(f"{desc_match_count} by Description word-overlap")
    if equipment_floc_match_count:
        signal_parts.append(f"{equipment_floc_match_count} by Equipment/FLOC (Description did not also match)")
    reason = (
        f"{match_count} historical Work Order(s) ({', '.join(matched_orders)}) are candidate matches "
        f"({'; '.join(signal_parts)}), but the specific Operation within each Order was never verified "
        f"(no PPM Operation Line source available) — candidate hours (unverified scope): {candidate_hours or 'none recorded'}"
    )
    return OrderLevelFallbackResult(True, match_count, candidate_hours, matched_orders, reason, source)


def sum_task_list_work(operation_rows: pd.DataFrame, findings: list) -> pd.DataFrame:
    recommended_by_key = {
        f.record_key: float(f.recommended_value)
        for f in findings
        if f.field_name == "WORK" and f.recommended_value is not None
    }

    def effective_work(row) -> float:
        record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}-{row['TLSUBOPNO']}"
        return recommended_by_key.get(record_key, row["WORK"])

    work_col = operation_rows.apply(effective_work, axis=1)
    grouped = operation_rows.assign(_effective_work=work_col).groupby(
        ["TLGRP", "TLGRPCOUNT"], as_index=False
    ).agg(task_list_total_work=("_effective_work", "sum"), operation_count=("_effective_work", "count"))
    return grouped
