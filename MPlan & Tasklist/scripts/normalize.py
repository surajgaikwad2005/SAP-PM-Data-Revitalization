import pandas as pd

LOGICAL_OPERATION_KEY = ["TLGRP", "TLGRPCOUNT", "TLOPNO", "TLSUBOPNO"]


def normalize_long_text(df: pd.DataFrame) -> pd.DataFrame:
    df = cast_counters_to_string(df, LOGICAL_OPERATION_KEY)
    longtext_agg = (
        df.groupby(LOGICAL_OPERATION_KEY, sort=False, dropna=False)["LONGTEXT"]
        .apply(lambda s: "\n".join("" if pd.isna(v) else str(v) for v in s))
        .reset_index(name="LONGTEXT_AGGREGATED")
    )
    first_row_per_operation = df.groupby(LOGICAL_OPERATION_KEY, sort=False, dropna=False, as_index=False).first()
    return first_row_per_operation.drop(columns=["LONGTEXT"]).merge(
        longtext_agg, on=LOGICAL_OPERATION_KEY, how="left"
    )


def cast_counters_to_string(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()
    for c in columns:
        df[c] = df[c].astype(str)
    return df


def parse_mplan_task_list_key(df: pd.DataFrame, known_tlgrps: set[str]) -> pd.DataFrame:
    def split(task_list) -> tuple[str | None, str | None, str | None]:
        if task_list is None or (isinstance(task_list, float) and pd.isna(task_list)) or len(str(task_list)) < 2:
            return None, None, None
        task_list = str(task_list)
        tltype = task_list[0]
        remainder = task_list[1:]
        for split_point in range(len(remainder), 0, -1):
            candidate_tlgrp = remainder[:split_point]
            if candidate_tlgrp in known_tlgrps:
                candidate_tlgrpcount = remainder[split_point:].lstrip("0") or "0"
                return tltype, candidate_tlgrp, candidate_tlgrpcount
        return tltype, None, None

    parsed = [split(v) for v in df["task_list"]]
    df = df.copy()
    df["TLTYPE"] = [p[0] for p in parsed]
    df["TLGRP"] = [p[1] for p in parsed]
    df["TLGRPCOUNT"] = [p[2] for p in parsed]
    return df


def classify_mplan_rows(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    detail_mask = df["maintenance_plan"].notna() & df["task_list"].notna()
    detail = df[detail_mask]
    aggregate = df[~detail_mask]
    return detail, aggregate
