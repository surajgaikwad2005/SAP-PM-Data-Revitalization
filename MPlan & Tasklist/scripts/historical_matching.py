import pandas as pd


def strip_timesheet_summary_row(df: pd.DataFrame) -> pd.DataFrame:
    other_columns = [c for c in df.columns if c not in ("Number (unit)", "Internal UoM")]
    is_summary_row = df[other_columns].isna().all(axis=1)
    return df[~is_summary_row].reset_index(drop=True)


def split_general_receiver(df: pd.DataFrame) -> pd.DataFrame:
    def split(value):
        if not isinstance(value, str) or " " not in value:
            return None, None
        order, _, operation = value.partition(" ")
        if not order or not operation:
            return None, None
        return order, operation

    parsed = [split(v) for v in df["General receiver"]]
    return df.assign(
        order=[p[0] for p in parsed],
        operation=[p[1] for p in parsed],
    )


def aggregate_timesheet_hours(df: pd.DataFrame) -> pd.DataFrame:
    hour_rows = df[df["Internal UoM"] == "H"].dropna(subset=["order", "operation"])
    grouped = hour_rows.groupby(["order", "operation"], as_index=False).agg(
        timesheet_actual_hours=("Number (unit)", "sum"),
        timesheet_row_count=("Number (unit)", "count"),
    )
    return grouped


def extract_jms_actual_hours(operation_line_df: pd.DataFrame) -> pd.DataFrame:
    result = operation_line_df.rename(
        columns={
            "Order": "order",
            "Activity": "operation",
            "Actual work": "jms_actual_hours",
            "Control Key": "jms_control_key",
        }
    )[["order", "operation", "jms_actual_hours", "jms_control_key"]]
    result["order"] = result["order"].astype(str)
    result["operation"] = result["operation"].astype(str)
    return result


def reconcile_actual_hours(timesheet_df: pd.DataFrame, jms_df: pd.DataFrame) -> pd.DataFrame:
    merged = timesheet_df.merge(jms_df, on=["order", "operation"], how="outer")

    def resolve(row):
        has_ts = pd.notna(row.get("timesheet_actual_hours"))
        has_jms = pd.notna(row.get("jms_actual_hours"))
        if has_ts and has_jms:
            return (
                row["timesheet_actual_hours"],
                "timesheet_primary_both_present",
                True,
                abs(row["timesheet_actual_hours"] - row["jms_actual_hours"]),
            )
        if has_ts:
            return row["timesheet_actual_hours"], "timesheet_only", False, None
        if has_jms:
            return row["jms_actual_hours"], "jms_only", False, None
        return None, "no_source", False, None

    resolved = merged.apply(resolve, axis=1, result_type="expand")
    resolved.columns = ["candidate_hours", "candidate_source", "source_overlap", "discrepancy"]
    return pd.concat(
        [merged[["order", "operation", "timesheet_actual_hours", "jms_actual_hours"]], resolved], axis=1
    )


def _description_matches(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    normalize = lambda s: "".join(ch for ch in s.upper() if ch.isalnum())
    return normalize(a) == normalize(b)


def _normalize_identifier(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    normalized = "".join(ch for ch in str(value).upper() if ch.isalnum())
    return normalized or None


def _equipment_or_floc_matches(
    historical_equipment: str | None, historical_floc: str | None,
    task_list_equipment_floc_pairs: set[tuple[str | None, str | None]],
) -> bool:
    hist_equipment_n = _normalize_identifier(historical_equipment)
    hist_floc_n = _normalize_identifier(historical_floc)
    for tl_equipment, tl_floc in task_list_equipment_floc_pairs:
        tl_equipment_n = _normalize_identifier(tl_equipment)
        tl_floc_n = _normalize_identifier(tl_floc)
        if hist_equipment_n is not None and hist_equipment_n == tl_equipment_n:
            return True
        if hist_floc_n is not None and hist_floc_n == tl_floc_n:
            return True
    return False


def _equipment_or_floc_conflicts(
    historical_equipment: str | None, historical_floc: str | None,
    task_list_equipment_floc_pairs: set[tuple[str | None, str | None]],
) -> bool:
    if not task_list_equipment_floc_pairs:
        return False  # nothing to conflict with — Task List has no known Equipment/FLOC at all
    hist_equipment_n = _normalize_identifier(historical_equipment)
    hist_floc_n = _normalize_identifier(historical_floc)
    if hist_equipment_n is None and hist_floc_n is None:
        return False  # historical side has nothing to check — absence is not a conflict
    return not _equipment_or_floc_matches(historical_equipment, historical_floc, task_list_equipment_floc_pairs)


def _normalize_words(text: str) -> set[str]:
    return {w for w in "".join(ch if ch.isalnum() else " " for ch in text.upper()).split() if len(w) > 2}


def order_level_description_match(order_description: str | None, opdesc: str | None, longtext: str | None) -> bool:
    if not order_description:
        return False
    order_words = _normalize_words(order_description)
    if not order_words:
        return False
    for candidate in (opdesc, longtext):
        if not candidate:
            continue
        candidate_words = _normalize_words(candidate)
        if len(order_words & candidate_words) >= 2:
            return True
    return False


def match_operations_to_history(
    normalized_operations: pd.DataFrame,
    task_list_group: pd.DataFrame,
    work_order_sources: dict[str, pd.DataFrame],
    reconciled_hours: pd.DataFrame,
    op_descriptions: pd.DataFrame,
) -> pd.DataFrame:
    bridge_keys = set(zip(task_list_group["Group"].astype(str), task_list_group["Group Counter"].astype(str)))
    desc_lookup = {(r["order"], r["operation"]): r["description"] for r in op_descriptions.to_dict("records")}
    hours_lookup = {(r["order"], r["operation"]): r["candidate_hours"] for r in reconciled_hours.to_dict("records")}

    task_list_equipment_floc_lookup: dict[tuple[str, str], set[tuple[str | None, str | None]]] = {}
    if "Group" in task_list_group.columns and "Group Counter" in task_list_group.columns:
        has_equipment = "Equipment" in task_list_group.columns
        has_floc = "Functional Location" in task_list_group.columns
        for r in task_list_group.to_dict("records"):
            key = (str(r["Group"]), str(r["Group Counter"]))
            equipment = r.get("Equipment") if has_equipment else None
            floc = r.get("Functional Location") if has_floc else None
            if equipment or floc:
                task_list_equipment_floc_lookup.setdefault(key, set()).add((equipment, floc))
    order_equipment_lookup: dict[str, str] = {}
    order_floc_lookup: dict[str, str] = {}
    for wo_df in work_order_sources.values():
        for r in wo_df.to_dict("records"):
            order = str(r.get("Order"))
            if not order:
                continue
            equipment = r.get("Equipment")
            if equipment:
                order_equipment_lookup[order] = equipment
            floc = r.get("Functional Location")
            if floc:
                order_floc_lookup[order] = floc

    order_desc_lookup: dict[str, str] = {}
    for wo_df in work_order_sources.values():
        if "Description" not in wo_df.columns:
            continue
        for r in wo_df.to_dict("records"):
            order = str(r.get("Order"))
            desc = r.get("Description")
            if order and desc:
                order_desc_lookup[order] = desc
    hours_by_order: dict[str, list[tuple[str, float]]] = {}
    for r in reconciled_hours.to_dict("records"):
        if r["candidate_hours"] is None:
            continue
        hours_by_order.setdefault(r["order"], []).append((r["operation"], r["candidate_hours"]))

    rows = []
    for op in normalized_operations.to_dict("records"):
        key = (str(op["TLGRP"]), str(op["TLGRPCOUNT"]))
        bridge_matched = key in bridge_keys
        orders_by_source = {}
        for source_name, wo_df in work_order_sources.items():
            if bridge_matched and wo_df.shape[0] > 0:
                matches = wo_df[
                    (wo_df["Group"].astype(str) == key[0]) & (wo_df["Group Counter"].astype(str) == key[1])
                ]
                orders_by_source[source_name] = matches["Order"].astype(str).tolist()
            else:
                orders_by_source[source_name] = []

        all_orders = [o for orders in orders_by_source.values() for o in orders]
        candidate_operation = str(op["TLOPNO"]).zfill(4)
        task_list_equipment_floc_pairs = task_list_equipment_floc_lookup.get(key, set())
        candidate_hours = []
        execution_verified = False
        equipment_floc_match_count = 0
        equipment_floc_matched_orders: list[str] = []
        for order in all_orders:
            hist_desc = desc_lookup.get((order, candidate_operation))
            hist_equipment = order_equipment_lookup.get(order)
            hist_floc = order_floc_lookup.get(order)
            description_matches = _description_matches(hist_desc, op.get("OPDESC"))
            equipment_or_floc_matches = _equipment_or_floc_matches(
                hist_equipment, hist_floc, task_list_equipment_floc_pairs
            )
            equipment_or_floc_conflicts = _equipment_or_floc_conflicts(
                hist_equipment, hist_floc, task_list_equipment_floc_pairs
            )
            if description_matches and not equipment_or_floc_conflicts:
                execution_verified = True
                hours = hours_lookup.get((order, candidate_operation))
                if hours is not None:
                    candidate_hours.append(hours)
            elif equipment_or_floc_matches:
                equipment_floc_match_count += 1
                equipment_floc_matched_orders.append(order)

        order_level_match_count = 0
        order_level_candidate_hours: list[float] = []
        order_level_orders: list[str] = []
        if not execution_verified:
            for order in all_orders:
                order_desc = order_desc_lookup.get(order)
                if order_level_description_match(order_desc, op.get("OPDESC"), op.get("LONGTEXT_AGGREGATED")):
                    order_level_match_count += 1
                    order_level_orders.append(order)
                    for _operation, hours in hours_by_order.get(order, []):
                        order_level_candidate_hours.append(hours)

        if execution_verified:
            blocking_reason = None
        elif not bridge_matched:
            blocking_reason = "No Task List Group+Counter match in Bokor Task List Group.xlsx"
        elif not all_orders:
            blocking_reason = "Task List bridge-matched, but no historical Order found for this Group+Counter"
        elif order_level_match_count or equipment_floc_match_count:
            blocking_reason = (
                "Historical Order(s) found and partially comparable (Description or Equipment/FLOC matched, "
                "not both) — Operation-level work scope not verified"
            )
        else:
            blocking_reason = (
                "Historical Order(s) found for this Task List, but none share a matching Description or "
                "Equipment/FLOC with this specific operation"
            )

        rows.append(
            {
                "record_key": f"{op['TLGRP']}-{op['TLGRPCOUNT']}-{op['TLOPNO']}",
                "TLGRP": op["TLGRP"],
                "TLGRPCOUNT": op["TLGRPCOUNT"],
                "TLOPNO": op["TLOPNO"],
                "bridge_matched": bridge_matched,
                "historical_orders_10yr": orders_by_source.get("10yr", []),
                "historical_orders_jms": orders_by_source.get("jms", []),
                "version_confidence": "version_unconfirmed",
                "execution_verified": execution_verified,
                "candidate_hours": candidate_hours,
                "order_level_match_count": order_level_match_count,
                "order_level_orders": order_level_orders,
                "order_level_candidate_hours": order_level_candidate_hours,
                "equipment_floc_match_count": equipment_floc_match_count,
                "equipment_floc_matched_orders": equipment_floc_matched_orders,
                "blocking_reason": blocking_reason,
                "match_count": len(candidate_hours),
            }
        )
    return pd.DataFrame(rows)
