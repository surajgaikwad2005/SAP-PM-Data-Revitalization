import re

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.utils.dataframe import dataframe_to_rows

from validation import Finding

HEADER_BOLD_FONT = Font(bold=True)
CHECK_COLUMN_FILL = PatternFill(start_color="FFF2AE", end_color="FFF2AE", fill_type="solid")  # soft yellow — "columns to check"
FINDING_HIGHLIGHT_FILL = PatternFill(start_color="C6E8C6", end_color="C6E8C6", fill_type="solid")  # faint green — suggested/recommended value
WRAP_ALIGNMENT = Alignment(wrap_text=True, vertical="top")
MAX_COLUMN_WIDTH = 45
REMARK_COLUMN = "Remark"

# PP6_Flag status colors (client spec, 2026-10): VALID is a positive/clean result (green);
# ON_HOLD is the one result that should immediately stand out as an issue (red); REVIEW is a
# "needs more information" result, distinct from both (amber/orange) — never green, since a
# REVIEW row is not a confirmed-good outcome.
_PP6_FLAG_FILL = {
    "VALID": PatternFill(start_color="C6E8C6", end_color="C6E8C6", fill_type="solid"),
    "ON_HOLD": PatternFill(start_color="F4C7C3", end_color="F4C7C3", fill_type="solid"),
    "REVIEW": PatternFill(start_color="FCE4A6", end_color="FCE4A6", fill_type="solid"),
}

PP_CHECK_COLUMNS = {
    "PP1": ["group", "group_counter"],
    "PP2": ["opdesc", "long_text_aggregated"],
    "PP3": ["group", "group_counter"],
    "PP4": ["opdesc", "long_text_aggregated", "strategy", "frequency"],
    "PP5": ["work", "person", "duration", "work_unit", "duration_unit"],
    "PP6": ["maintenance_strategy", "equipment"],
    # PP7: a Finding exists iff maintenance_plan resolves to None.
    "PP7": ["maintenance_plan"],
}

PAIN_POINT_NAMES = {
    "PP1": "Task List Naming",
    "PP2": "Work Centre",
    "PP3": "Orphan Task List",
    "PP4": "Duplicate Task List",
    "PP5": "Manhours",
    "PP6": "Strategy / Frequency",
    "PP7": "Hanging Maintenance Item",
}

SHEET_NAMES = {
    "PP1": "PP1_TaskList_Naming",
    "PP2": "PP2_Work_Centre",
    "PP3": "PP3_Orphan_TaskList",
    "PP4": "PP4_Duplicate_TaskList",
    "PP5": "PP5_Manhours",
    "PP6": "PP6_Strategy_Frequency",
    "PP7": "PP7_Hanging_MI",
}


COLUMN_RENAME_MAP = {
    "TLGRP": "group",
    "TLGRPCOUNT": "group_counter",
    "TLOPNO": "tlopno",
    "TLSUBOPNO": "tlsubopno",
    "PLANT": "plant",
    "STRATEGY": "strategy",
    "TLTYPE": "tltype",
    "TLNODE": "tlnode",
    "TLCOUNT": "tlcount",
    "CTRLKEY": "ctrlkey",
    "OPWKCEN": "opwkcen",
    "OPDESC": "opdesc",
    "WORK": "work",
    "WORK_UNIT": "work_unit",
    "PERSON": "person",
    "DURATION": "duration",
    "DURATION_UNIT": "duration_unit",
    "ACTTYPE": "acttype",
    "SUIT": "suit",
    "FREQUENCY": "frequency",
    "CA10TXT": "ca10txt",
    "SO10TXT": "so10txt",
    "TEXTTITLE": "texttitle",
    "FORMAT": "format",
    "LONGTEXT": "long_text",
    "LONGTEXT_AGGREGATED": "long_text_aggregated",
    "LONGTEXT_CONSOLIDATED": "long_text_consolidated",
    "SUB_OPERATION_COUNT": "sub_operation_count",
    "OPERATION_KEY_SUFFIX": "operation_key_suffix",
    "Group": "group",
    "Group Counter": "group_counter",
    "Planning_Plant": "planning_plant",
    "Strategy": "strategy",
    "TaskList_Type": "tltype",
    "Operation_Count": "operation_count",
    "Sample_OPDESC": "opdesc",
    "Sample_Work_Center": "opwkcen",
    "TLG_Planning_Plant": "tlg_planning_plant",
    "TLG_Maintenance_Plan": "maintenance_plan",
    "TLG_Maintenance_Item": "maintenance_item",
    "TLG_Maint_Item_Text": "maint_item_text",
    "TLG_Functional_Location": "functional_location",
    "TLG_FunctLocDescrip": "functlocdescrip",
    "TLG_Equipment": "equipment",
    "TLG_Object_Description": "object_description",
    "TLG_Order_Type": "order_type",
    "TLG_Maintenance_Strategy": "maintenance_strategy",
    "TLG_ABC_Indicator": "abc_indicator",
    "TLG_Maint_Planner_Group": "maint_planner_group",
    "TLG_Main_Work_Center": "tlg_main_work_center",
    "TLG_Location": "location",
    "TLG_Linked_MI_Count": "linked_mi_count",
    "TLG_Distinct_Equipment_Count": "distinct_equipment_count",
    # task_list_group (PP6/PP7 source): Title Case With Spaces -> KG-native lowercase.
    "Planning Plant": "planning_plant",
    "Maintenance Plan": "maintenance_plan",
    "Maintenance Item": "maintenance_item",
    "Maint. item text": "maint_item_text",
    "Functional Location": "functional_location",
    "FunctLocDescrip.": "functlocdescrip",
    "Equipment": "equipment",
    "Object Description": "object_description",
    "Order Type": "order_type",
    "Maintenance Strategy": "maintenance_strategy",
    "ABC Indicator": "abc_indicator",
    "Maint. Planner Group": "maint_planner_group",
    "Main Work Center": "main_work_center",
    "Changed On": "changed_on",
    "Changed By": "changed_by",
    "Created On": "created_on",
    "Created By": "created_by",
    "Location": "location",
}


def _canonicalize_source_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {c: COLUMN_RENAME_MAP[c] for c in df.columns if c in COLUMN_RENAME_MAP}
    return df.rename(columns=rename)


def _pp1_key(row: dict) -> str:
    return f"{row['group']}-{row['group_counter']}"


def _pp2_key(row: dict) -> str:
    from validation import pp2_operation_key_suffix

    return f"{row['group']}-{row['group_counter']}-{row['tlopno']}{pp2_operation_key_suffix(row.get('opdesc'))}"


def _pp3_key(row: dict) -> str:
    return f"{row['group']}-{row['group_counter']}"


def _pp4_key(row: dict) -> str:
    return f"{row['group']}-{row['group_counter']}"


def _pp5_key(row: dict) -> str:
    return f"{row['group']}-{row['group_counter']}-{row['tlopno']}"


def _pp6_key(row: dict) -> str:
    return str(row["maintenance_item"])


def _pp7_key(row: dict) -> str:
    return str(row["maintenance_item"])


PP_SOURCE = {
    "PP1": ("normalized_operations", _pp1_key),
    "PP2": ("normalized_operations", _pp2_key),
    "PP3": ("normalized_operations", _pp3_key),
    "PP4": ("normalized_operations", _pp4_key),
    "PP5": ("normalized_operations", _pp5_key),
    "PP6": ("task_list_group", _pp6_key),
    "PP7": ("task_list_group", _pp7_key),
}


def _record_keys_for_pain_point(pain_point: str, row: dict) -> list[str]:
    _, key_fn = PP_SOURCE[pain_point]
    return [key_fn(row)]


def _confidence_word(confidence) -> str | None:
    if confidence is None:
        return None
    return str(confidence).upper()


def _short_evidence(f: Finding) -> str:
    text = f.evidence_source or ""
    return text if len(text) <= 300 else text[:297] + "..."


_ID_LIST_PATTERN = re.compile(r"\((?:\d[\d,\s]{20,}\d)\)")  # parenthesised run of 20+ digits — raw historical Order-ID dump
_HOURS_LIST_PATTERN = re.compile(r"\[(?:[\d.,\s]{20,})\]")  # bracketed run of 20+ chars — raw candidate-hours array dump


def _short_reason(f: Finding) -> str:
    text = f.reason or ""
    text = _ID_LIST_PATTERN.sub("(IDs omitted — see Evidence/KG for full list)", text)
    text = _HOURS_LIST_PATTERN.sub("[values omitted — see Evidence/KG for full list]", text)
    return text if len(text) <= 700 else text[:697] + "..."


def _suggest_and_status(f: Finding) -> tuple[str | None, str]:
    if f.recommended_value is not None:
        return f.recommended_value, "Recommended"
    if f.candidate_value is not None:
        return f.candidate_value, "Candidate - PCSB review required"
    return None, "Insufficient evidence"


def _pp1_columns(matches: list[Finding]) -> dict[str, object]:
    f = matches[0]
    suggest, status = _suggest_and_status(f)
    return {
        "PP1_Flag": f.pp1_flag,
        "PP1_Suggest_Group": suggest,
        "PP1_Confidence": _confidence_word(f.confidence) or ("REVIEW" if f.candidate_value else None),
        "PP1_Evidence": _short_evidence(f),
        "PP1_Reason": _short_reason(f),
        "PP1_Status": status,
        # Raw SAP system status of the linked Equipment/FLOC, surfaced as-is (not
        # collapsed to active/inactive) so PCSB can filter by whatever status
        # combination they want (client spec, 2026-10).
        "PP1_Equipment_Status": f.pp1_equipment_status,
        "PP1_FLOC_Status": f.pp1_floc_status,
    }


def _pp2_columns(matches: list[Finding]) -> dict[str, object]:
    f = matches[0]
    suggest, _status = _suggest_and_status(f)
    return {
        "PP2_Suggest_Work_Center": suggest,
        "PP2_Confidence": _confidence_word(f.confidence) or "REVIEW",
        "PP2_Evidence": _short_evidence(f),
        "PP2_Reason": _short_reason(f),
    }


def _pp3_columns(matches: list[Finding]) -> dict[str, object]:
    f = matches[0]
    if f.detection_confidence is not None and f.detection_confidence >= 0.8:
        confidence_word = "HIGH"
    elif f.detection_confidence is not None and f.detection_confidence >= 0.5:
        confidence_word = "MEDIUM"
    else:
        confidence_word = "LOW"
    return {
        "PP3_Flag": "ORPHAN_TASK_LIST",
        "PP3_Confidence": confidence_word,
        "PP3_Evidence": _short_evidence(f),
        "PP3_Reason": _short_reason(f),
    }


_PP4_FLAG_PATTERN = re.compile(r"\bas (EXACT_DUPLICATE|STRONG_OVERLAP|PARTIAL_OVERLAP|REVIEW_REQUIRED)\b")


def _pp4_columns(matches: list[Finding]) -> dict[str, object]:
    f = matches[0]
    flag_match = _PP4_FLAG_PATTERN.search(f.reason or "")
    flag = flag_match.group(1) if flag_match else "REVIEW_REQUIRED"
    if f.detection_confidence is not None and f.detection_confidence >= 0.8:
        confidence_word = "HIGH"
    elif f.detection_confidence is not None and f.detection_confidence >= 0.5:
        confidence_word = "MEDIUM"
    else:
        confidence_word = "LOW"
    return {
        "PP4_Matched_Task_List": None,  # overwritten in _build_pp_dataframe's PP4 branch
        "PP4_Flag": flag,
        "PP4_Confidence": confidence_word,
        "PP4_Evidence": _short_evidence(f),
        "PP4_Reason": _short_reason(f),
    }


_PP5_STATUS_PRIORITY = {"CONFLICT": 0, "REVIEW_REQUIRED": 1, "CANNOT_VERIFY": 2, "VALID": 3}


def _pp5_columns(matches: list[Finding]) -> dict[str, object]:
    # Client spec (2026-10): PP5_Status is carried directly on Finding.evidence_level
    # (VALID / REVIEW_REQUIRED / CONFLICT / CANNOT_VERIFY). An operation can have more than one
    # Finding (one per TLSUBOPNO for Case B arithmetic, plus/or one Tier-2 evidence Finding) — when
    # several exist, prefer the one with a real Suggested_WORK, then the most severe status.
    def sort_key(f: Finding) -> tuple[int, int]:
        has_suggestion = 0 if f.recommended_value is not None else 1
        severity = _PP5_STATUS_PRIORITY.get(f.evidence_level, 4)
        return (has_suggestion, severity)

    chosen = min(matches, key=sort_key)
    return {
        "PP5_Status": chosen.evidence_level or "CANNOT_VERIFY",
        "PP5_Suggested_WORK": chosen.recommended_value,
        "PP5_Evidence": _short_evidence(chosen),
        "PP5_Reason": _short_reason(chosen),
    }


# PP6_Confidence per status (client spec, 2026-10): VALID/ON_HOLD are both derived from a
# fully-resolved cycle sequence (High confidence); REVIEW covers several distinct "can't
# determine" reasons, some of which are closer to certain (e.g. no Frequency assigned at all)
# than others (e.g. an ambiguous Package match that is likely resolvable with more reference
# data) — Low is the default, Medium for the two reason codes where the gap looks more
# provisional than conclusive.
_PP6_REVIEW_MEDIUM_FLAGS = {"FREQUENCY_AMBIGUOUS_PACKAGE", "CYCLE_TEXT_UNPARSEABLE"}


def _pp6_columns(matches: list[Finding]) -> dict[str, object]:
    # Check A (Strategy, field_name="Maintenance Strategy") and Check B (Frequency,
    # field_name="Frequency") are independent findings that may both exist for the same
    # Maintenance Item — each contributes its own Suggest_* column; Check A's logic/output is
    # untouched by the Check B wiring below.
    strategy = None
    pp6_status = None
    first_missed_cycle = None
    consecutive_missed_cycles = None
    confidence = None
    evidence_detail = None
    reason_parts = []
    for f in matches:
        suggest, _status = _suggest_and_status(f)
        if f.field_name == "Maintenance Strategy":
            strategy = suggest
            reason_parts.append(_short_reason(f))
        elif f.field_name == "Frequency":
            pp6_status = f.pp6_status
            first_missed_cycle = f.pp6_first_missed_cycle
            consecutive_missed_cycles = f.pp6_consecutive_missed_cycles
            evidence_detail = f.pp6_evidence_detail
            # PP6_Reason (client spec, 2026-10): the plain-language sentence a PETRONAS user
            # reads directly — never the raw technical reason string used by every other pain
            # point's _short_reason, which is reserved for PP6_Evidence's structured detail.
            reason_parts.append(f.reason)
            if f.pp6_status == "REVIEW":
                confidence = "Medium" if f.pp6_flag in _PP6_REVIEW_MEDIUM_FLAGS else "Low"
            else:
                confidence = "High"
    return {
        "PP6_Suggest_Strategy": strategy,
        "PP6_Flag": pp6_status,
        "PP6_First_Missed_Cycle": first_missed_cycle,
        "PP6_Consecutive_Missed_Cycles": consecutive_missed_cycles,
        "PP6_Confidence": confidence,
        "PP6_Evidence": evidence_detail,
        "PP6_Reason": "; ".join(reason_parts),
    }


def _pp7_columns(matches: list[Finding]) -> dict[str, object]:
    f = matches[0]
    if f.detection_confidence is not None and f.detection_confidence >= 0.8:
        confidence_word = "HIGH"
    elif f.detection_confidence is not None and f.detection_confidence >= 0.5:
        confidence_word = "MEDIUM"
    else:
        confidence_word = "LOW"
    return {
        "PP7_Status": "HANGING_MAINTENANCE_ITEM",
        "PP7_Suggest_Action": "Assign a Maintenance Plan — Item currently has none",
        "PP7_Suggest_Maintenance_Plan": None,
        "PP7_Confidence": confidence_word,
        "PP7_Evidence": _short_evidence(f),
        "PP7_Reason": _short_reason(f),
    }


PP_COLUMN_BUILDERS = {
    "PP1": _pp1_columns,
    "PP2": _pp2_columns,
    "PP3": _pp3_columns,
    "PP4": _pp4_columns,
    "PP5": _pp5_columns,
    "PP6": _pp6_columns,
    "PP7": _pp7_columns,
}

# Column order per pain point, exactly as specified by the client.
PP_COLUMN_ORDER = {
    "PP1": [
        "PP1_Flag", "PP1_Suggest_Group", "PP1_Confidence", "PP1_Evidence", "PP1_Reason", "PP1_Status",
        "PP1_Equipment_Status", "PP1_FLOC_Status",
    ],
    "PP2": ["PP2_Suggest_Work_Center", "PP2_Confidence", "PP2_Evidence", "PP2_Reason"],
    "PP3": ["PP3_Flag", "PP3_Confidence", "PP3_Evidence", "PP3_Reason"],
    "PP4": ["PP4_Matched_Task_List", "PP4_Flag", "PP4_Confidence", "PP4_Evidence", "PP4_Reason"],
    # Client spec (2026-10): exactly these 4 columns — PP5_Status uses VALID/REVIEW_REQUIRED/
    # CONFLICT/CANNOT_VERIFY (replacing the old HIGH/MEDIUM/LOW confidence scheme), and
    # PP5_Suggested_WORK is blank unless a specific defensible value is supported (JMS-corroborated
    # or deterministic PERSON x DURATION — never a bare historical range/median).
    "PP5": ["PP5_Status", "PP5_Suggested_WORK", "PP5_Evidence", "PP5_Reason"],
    # PP6_Flag (client spec, 2026-10, final naming): VALID/ON_HOLD/REVIEW is the single
    # client-facing business outcome for Check B (Frequency) — replaces PP6_Suggest_Frequency,
    # which was the wrong output column (a resolved interval is not useful without the status).
    "PP6": [
        "PP6_Suggest_Strategy", "PP6_Flag", "PP6_First_Missed_Cycle",
        "PP6_Consecutive_Missed_Cycles", "PP6_Confidence", "PP6_Evidence", "PP6_Reason",
    ],
    "PP7": ["PP7_Status", "PP7_Suggest_Action", "PP7_Suggest_Maintenance_Plan", "PP7_Confidence", "PP7_Evidence", "PP7_Reason"],
}


def _pp5_business_key(record_key: str) -> str:
    parts = record_key.split("-")
    return "-".join(parts[:3]) if len(parts) >= 3 else record_key


def _findings_by_business_key(pain_point: str, findings: list[Finding]) -> dict[str, list[Finding]]:
    by_key: dict[str, list[Finding]] = {}
    for f in findings:
        if f.pain_point != pain_point:
            continue
        if pain_point == "PP4":
            left, _, right = f.record_key.partition(" / ")
            by_key.setdefault(left, []).append(f)
            by_key.setdefault(right, []).append(f)
        elif pain_point == "PP5":
            by_key.setdefault(_pp5_business_key(f.record_key), []).append(f)
        else:
            by_key.setdefault(f.record_key, []).append(f)
    return by_key


def _build_pp_dataframe(pain_point: str, source_df: pd.DataFrame, findings: list[Finding]) -> pd.DataFrame:
    source_df = _canonicalize_source_columns(source_df)
    by_key = _findings_by_business_key(pain_point, findings)

    out_rows = []
    for row in source_df.to_dict("records"):
        try:
            row_keys = _record_keys_for_pain_point(pain_point, row)
        except KeyError:
            row_keys = []
        matches: list[Finding] = []
        matched_key = None
        for k in row_keys:
            if k in by_key:
                matches = by_key[k]
                matched_key = k
                break
        out_row = dict(row)
        if matches:
            columns = PP_COLUMN_BUILDERS[pain_point](matches)
            if pain_point == "PP4":
                others = []
                for f in matches:
                    left, _, right = f.record_key.partition(" / ")
                    other = right if left == matched_key else left
                    others.append(other)
                columns["PP4_Matched_Task_List"] = "; ".join(sorted(set(others)))
            out_row.update(columns)
        else:
            for col in PP_COLUMN_ORDER[pain_point]:
                out_row.setdefault(col, None)
        out_rows.append(out_row)

    result = pd.DataFrame(out_rows)
    ordered_columns = [c for c in source_df.columns] + PP_COLUMN_ORDER[pain_point]
    for col in ordered_columns:
        if col not in result.columns:
            result[col] = None
    return result[ordered_columns]


def _write_dataframe_sheet(
    wb, sheet_title: str, df: pd.DataFrame, highlight_columns: list[str], check_columns: list[str] | None = None,
    status_fill_columns: dict[str, dict[str, PatternFill]] | None = None,
) -> None:
    check_columns = check_columns or []
    status_fill_columns = status_fill_columns or {}
    ws = wb.create_sheet(sheet_title)

    df = df.copy()
    df[REMARK_COLUMN] = None

    highlight_idx = {df.columns.get_loc(c) + 1 for c in highlight_columns if c in df.columns}
    check_idx = {df.columns.get_loc(c) + 1 for c in check_columns if c in df.columns}
    status_fill_idx = {
        df.columns.get_loc(col) + 1: fills for col, fills in status_fill_columns.items() if col in df.columns
    }

    for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=True), start=1):
        ws.append(row)
    if ws.max_row >= 1 and ws.max_column >= 1:
        last_col_letter = get_column_letter(ws.max_column)
        ws.auto_filter.ref = f"A1:{last_col_letter}{ws.max_row}"
    ws.freeze_panes = "A2"

    for col_idx in range(1, ws.max_column + 1):
        ws.cell(row=1, column=col_idx).font = HEADER_BOLD_FONT

    for col_idx in check_idx:
        ws.cell(row=1, column=col_idx).fill = CHECK_COLUMN_FILL
        for row_idx in range(2, ws.max_row + 1):
            ws.cell(row=row_idx, column=col_idx).fill = CHECK_COLUMN_FILL

    for row_idx in range(2, ws.max_row + 1):
        for col_idx in highlight_idx:
            cell = ws.cell(row=row_idx, column=col_idx)
            value = cell.value
            is_blank = value is None or value == "" or (isinstance(value, float) and pd.isna(value))
            if not is_blank:
                cell.fill = FINDING_HIGHLIGHT_FILL

    for row_idx in range(2, ws.max_row + 1):
        for col_idx, fills in status_fill_idx.items():
            cell = ws.cell(row=row_idx, column=col_idx)
            fill = fills.get(cell.value)
            if fill is not None:
                cell.fill = fill

    for row_idx in range(1, ws.max_row + 1):
        for col_idx in range(1, ws.max_column + 1):
            ws.cell(row=row_idx, column=col_idx).alignment = WRAP_ALIGNMENT
    for col_idx in range(1, ws.max_column + 1):
        col_letter = get_column_letter(col_idx)
        header_len = len(str(df.columns[col_idx - 1]))
        ws.column_dimensions[col_letter].width = min(max(header_len + 2, 12), MAX_COLUMN_WIDTH)


def write_recommendations_workbook(
    sources: dict[str, pd.DataFrame], findings: list[Finding], output_path: str
) -> dict[str, int]:
    import openpyxl

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    row_counts: dict[str, int] = {}
    for pain_point in ["PP1", "PP2", "PP3", "PP4", "PP5", "PP6", "PP7"]:
        source_name, _ = PP_SOURCE[pain_point]
        source_df = sources[source_name]
        pp_df = _build_pp_dataframe(pain_point, source_df, findings)
        _write_dataframe_sheet(
            wb, SHEET_NAMES[pain_point], pp_df,
            highlight_columns=[c for c in PP_COLUMN_ORDER[pain_point] if "Suggest" in c],
            check_columns=PP_CHECK_COLUMNS[pain_point],
            status_fill_columns={"PP6_Flag": _PP6_FLAG_FILL} if pain_point == "PP6" else None,
        )
        row_counts[pain_point] = pp_df.shape[0]

    wb.save(output_path)
    return row_counts


def _has_finding_signal(pain_point: str, row: dict) -> bool:
    if pain_point == "PP5":
        # Every Tier-1-valid operation now gets an explicit PP5_Status (client spec, 2026-10),
        # including VALID — but the curated *_Findings sheet should still only surface operations
        # that actually need attention, same as every other pain point.
        return row.get("PP5_Status") in ("REVIEW_REQUIRED", "CONFLICT", "CANNOT_VERIFY")
    if pain_point == "PP6":
        # Check B (Frequency) now emits a Finding for every Task List, including VALID (client
        # spec, 2026-10) — PP6_Reason is therefore always non-blank and can't be used as the
        # finding-signal test. A row is a real finding either because Check A (Strategy) flagged
        # it (PP6_Flag is None for Check A rows, but PP6_Suggest_Strategy will be set) or because
        # Check B's flag is ON_HOLD/REVIEW (VALID is not a finding).
        if row.get("PP6_Suggest_Strategy") not in (None, ""):
            return True
        return row.get("PP6_Flag") in ("ON_HOLD", "REVIEW")
    reason_cols = [c for c in row if c.endswith("_Reason")]
    return any(row.get(c) not in (None, "") for c in reason_cols)


_CANNOT_VERIFY_PHRASES = (
    "no evidence",
    "cannot resolve",
    "cannot verify",
    "no historical",
    "no linked equipment",
    "no linked functional location",
    "no value to validate",
    "insufficient evidence",
    "not available",
    "no object description available",
)


def _is_cannot_verify(f: Finding) -> bool:
    if f.pain_point == "PP5":
        return f.evidence_level == "CANNOT_VERIFY"
    reason = (f.reason or "").lower()
    return any(phrase in reason for phrase in _CANNOT_VERIFY_PHRASES)


def write_findings_summary_workbook(
    sources: dict[str, pd.DataFrame], findings: list[Finding], output_path: str, records_checked: dict[str, int]
) -> dict[str, dict]:
    import openpyxl

    wb = openpyxl.Workbook()
    wb.remove(wb.active)

    PP_BREAKDOWN_COLUMN = {
        "PP1": "PP1_Flag",
        "PP2": "PP2_Suggest_Work_Center",
        "PP3": "PP3_Flag",
        "PP4": "PP4_Flag",
        "PP5": "PP5_Status",
        "PP6": "PP6_Flag",
        "PP7": "PP7_Status",
    }
    breakdown_rows = []

    summary_rows = []
    for pain_point in ["PP1", "PP2", "PP3", "PP4", "PP5", "PP6", "PP7"]:
        source_name, _ = PP_SOURCE[pain_point]
        source_df = sources[source_name]
        pp_df = _build_pp_dataframe(pain_point, source_df, findings)
        finding_mask = pp_df.to_dict("records")
        finding_rows = [row for row in finding_mask if _has_finding_signal(pain_point, row)]
        findings_df = pd.DataFrame(finding_rows) if finding_rows else pp_df.iloc[0:0]
        _write_dataframe_sheet(
            wb, f"{pain_point}_Findings", findings_df,
            highlight_columns=[c for c in PP_COLUMN_ORDER[pain_point] if "Suggest" in c],
            check_columns=PP_CHECK_COLUMNS[pain_point],
            status_fill_columns={"PP6_Flag": _PP6_FLAG_FILL} if pain_point == "PP6" else None,
        )

        pp_findings = [f for f in findings if f.pain_point == pain_point]
        confidence_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        review_required = 0
        valid_count = 0
        cannot_verify_count = 0
        conflict_count = 0
        suggestions_generated = 0
        seen_keys_with_suggestion = set()
        by_key = _findings_by_business_key(pain_point, pp_findings)
        breakdown_column = PP_BREAKDOWN_COLUMN[pain_point]
        breakdown_counts: dict[str, int] = {}
        for key, matches in by_key.items():
            builder = PP_COLUMN_BUILDERS[pain_point]
            cols = builder(matches)
            if pain_point == "PP5":
                # PP5_Status (VALID/REVIEW_REQUIRED/CONFLICT/CANNOT_VERIFY) replaces the generic
                # HIGH/MEDIUM/LOW/REVIEW confidence scheme for this pain point (client spec, 2026-10).
                status_val = cols.get("PP5_Status")
                if cols.get("PP5_Suggested_WORK") not in (None, ""):
                    suggestions_generated += 1
                if status_val == "VALID":
                    valid_count += 1
                elif status_val == "CONFLICT":
                    conflict_count += 1
                elif status_val == "CANNOT_VERIFY":
                    cannot_verify_count += 1
                else:
                    review_required += 1
                continue
            if pain_point == "PP6" and cols.get("PP6_Flag") is not None:
                # Check B (Frequency) now carries a direct client-facing PP6_Flag (client spec,
                # 2026-10, final naming: VALID/ON_HOLD/REVIEW, collapsing the 7 internal pp6_flag
                # reason codes — see _PP6_STATUS_BY_FLAG in validation.py). Check B findings never
                # carry a suggestion (no suggestion is ever produced for Frequency), so the generic
                # has_suggestion path below would silently miscount every Check B row — classify by
                # PP6_Flag instead. Check A findings (PP6_Flag is None) fall through unchanged to
                # the generic logic beneath, exactly as before this branch existed. ON_HOLD maps
                # onto the shared "Conflict" summary column (the only slot representing a stronger,
                # attention-worthy divergence besides Review_Required).
                pp6_flag_val = cols["PP6_Flag"]
                if pp6_flag_val == "ON_HOLD":
                    conflict_count += 1
                elif pp6_flag_val == "REVIEW":
                    review_required += 1
                else:
                    valid_count += 1
                continue
            suggest_cols = [v for k, v in cols.items() if "Suggest" in k]
            confidence_val = cols.get(f"{pain_point}_Confidence")
            has_suggestion = any(v not in (None, "") for v in suggest_cols)
            if has_suggestion and key not in seen_keys_with_suggestion:
                seen_keys_with_suggestion.add(key)
                suggestions_generated += 1
                if confidence_val in confidence_counts:
                    confidence_counts[confidence_val] += 1
                elif confidence_val == "REVIEW":
                    review_required += 1
            elif not has_suggestion:
                if any(_is_cannot_verify(f) for f in matches):
                    cannot_verify_count += 1
                else:
                    valid_count += 1

        if breakdown_column in pp_df.columns:
            value_counts = pp_df[breakdown_column].fillna("(no finding)").astype(str).value_counts()
            breakdown_counts = value_counts.to_dict()
        else:
            breakdown_counts = {}

        for value, count in sorted(breakdown_counts.items(), key=lambda kv: (-kv[1], kv[0])):
            breakdown_rows.append(
                {
                    "Pain_Point": pain_point,
                    "Column": breakdown_column,
                    "Value": value,
                    "Count": count,
                }
            )

        # PP1-only: also break down the raw Equipment/FLOC system status columns, so
        # PCSB can see at a glance how many Task Lists carry each real status
        # combination, independent of the agent's own active/inactive judgement
        # (client spec, 2026-10).
        if pain_point == "PP1":
            for status_column in ("PP1_Equipment_Status", "PP1_FLOC_Status"):
                if status_column not in pp_df.columns:
                    continue
                status_counts = pp_df[status_column].fillna("(none linked)").astype(str).value_counts()
                for value, count in sorted(status_counts.to_dict().items(), key=lambda kv: (-kv[1], kv[0])):
                    breakdown_rows.append(
                        {
                            "Pain_Point": pain_point,
                            "Column": status_column,
                            "Value": value,
                            "Count": count,
                        }
                    )

        summary_rows.append(
            {
                "Pain_Point": pain_point,
                "Pain_Point_Name": PAIN_POINT_NAMES[pain_point],
                "Records_Checked": records_checked.get(pain_point, 0),
                "Findings": len(by_key),
                "Suggestions_Generated": suggestions_generated,
                "High_Confidence": confidence_counts["HIGH"],
                "Medium_Confidence": confidence_counts["MEDIUM"],
                "Low_Confidence": confidence_counts["LOW"],
                "Valid": valid_count,
                "Cannot_Verify": cannot_verify_count,
                "Review_Required": review_required,
                "Conflict": conflict_count,
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    summary_ws = wb.create_sheet("Summary", 0)
    for row in dataframe_to_rows(summary_df, index=False, header=True):
        summary_ws.append(row)
    for column_cells in summary_ws.columns:
        summary_ws.column_dimensions[column_cells[0].column_letter].width = 22
    for col_idx in range(1, summary_ws.max_column + 1):
        summary_ws.cell(row=1, column=col_idx).font = HEADER_BOLD_FONT
        for row_idx in range(1, summary_ws.max_row + 1):
            summary_ws.cell(row=row_idx, column=col_idx).alignment = WRAP_ALIGNMENT
    summary_ws.freeze_panes = "A2"

    breakdown_df = pd.DataFrame(breakdown_rows)
    breakdown_ws = wb.create_sheet("Flag_Breakdown", 1)
    for row in dataframe_to_rows(breakdown_df, index=False, header=True):
        breakdown_ws.append(row)
    for column_cells in breakdown_ws.columns:
        breakdown_ws.column_dimensions[column_cells[0].column_letter].width = 22
    for col_idx in range(1, breakdown_ws.max_column + 1):
        breakdown_ws.cell(row=1, column=col_idx).font = HEADER_BOLD_FONT
        for row_idx in range(1, breakdown_ws.max_row + 1):
            breakdown_ws.cell(row=row_idx, column=col_idx).alignment = WRAP_ALIGNMENT
    breakdown_ws.freeze_panes = "A2"

    wb.save(output_path)
    return {row["Pain_Point"]: row for row in summary_rows}
