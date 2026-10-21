def query_oreda_categories(conn) -> list[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT DISTINCT item FROM oreda_data WHERE item IS NOT NULL")
        return [r[0] for r in cur.fetchall()]


def _to_float_or_none(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def query_oreda_repair_benchmark(conn, item: str, failure_mode: str) -> dict | None:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT source_page, manhour_repair_min, manhour_repair_mean, manhour_repair_max
            FROM oreda_data
            WHERE item = %s AND failure_mode = %s AND manhour_repair_mean IS NOT NULL
            LIMIT 1
            """,
            (item, failure_mode),
        )
        row = cur.fetchone()
    if row is None:
        return None
    source_page, min_val, mean_val, max_val = row
    mean = _to_float_or_none(mean_val)
    if mean is None:
        return None
    return {
        "source_page": source_page,
        "manhour_repair_min": _to_float_or_none(min_val),
        "manhour_repair_mean": mean,
        "manhour_repair_max": _to_float_or_none(max_val),
    }


def _normalize_item_text(item: str) -> str:
    return " ".join(item.replace("\n", " ").split()).lower()


def query_oreda_category_benchmark(
    conn, item_hint: str, failure_modes: list[str]
) -> tuple[dict | None, str | None]:
    normalized_hint = _normalize_item_text(item_hint)
    with conn.cursor() as cur:
        for failure_mode in failure_modes:
            cur.execute(
                """
                SELECT source_page, item, manhour_repair_min, manhour_repair_mean, manhour_repair_max
                FROM oreda_data
                WHERE failure_mode = %s AND manhour_repair_mean IS NOT NULL
                """,
                (failure_mode,),
            )
            rows = cur.fetchall()
            matched = [r for r in rows if _normalize_item_text(r[1]).startswith(normalized_hint)]
            if not matched:
                continue
            means = [m for m in (_to_float_or_none(r[3]) for r in matched) if m is not None]
            if not means:
                continue
            means.sort()
            median_mean = means[len(means) // 2] if len(means) % 2 == 1 else (means[len(means) // 2 - 1] + means[len(means) // 2]) / 2
            mins = [m for m in (_to_float_or_none(r[2]) for r in matched) if m is not None]
            maxs = [m for m in (_to_float_or_none(r[4]) for r in matched) if m is not None]
            return {
                "source_page": matched[0][0],
                "matched_row_count": len(matched),
                "manhour_repair_min": min(mins) if mins else None,
                "manhour_repair_mean": median_mean,
                "manhour_repair_max": max(maxs) if maxs else None,
            }, failure_mode
    return None, None


def is_oreda_applicable_to_pp5(conn) -> tuple[bool, str]:
    return True, (
        "OREDA.db holds real, populated manhour_repair_mean/min/max labour-hour "
        "data across a rich equipment taxonomy. It is usable as a PROVISIONAL "
        "(never verified) man-hour candidate per-operation, gated on: (1) a genuine "
        "equipment-category match from the operation's Object Description/OPDESC/"
        "LONGTEXT, and (2) the operation's own activity being comparable to "
        "general-repair-scale labour (overhaul/replacement-type work) rather than "
        "routine inspection/test/calibration/service — manhour_repair_mean remains "
        "a corrective repair-after-failure quantity, structurally different from a "
        "routine PM operation's duration, and is never applied to routine PM text."
    )
