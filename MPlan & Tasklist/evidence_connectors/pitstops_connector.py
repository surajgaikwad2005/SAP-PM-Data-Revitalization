import pandas as pd

DISCIPLINE_TO_OPWKCEN = {
    "BELEC": "Electrical",
    "SKO-ELEC": "Electrical",
    "BMECH": "Static",
    "MECH": "Static",
    "SKO-STAT": "Static",
    "SKO-ROTA": "Rotating",
    "INST": "Instrument & Control",
    "SKO-MCI": "Instrument & Control",
    "CP2INST": "Instrument & Control",
}

IMPLAUSIBLE_MULTIPLIER = 10


def load_pitstops_tasklists(paths: list[str]) -> pd.DataFrame:
    frames = [pd.read_excel(p) for p in paths]
    return pd.concat(frames, ignore_index=True)


def discipline_duration_ranges(df: pd.DataFrame) -> pd.DataFrame:
    grouped = df.groupby("Discipline")["Dur (Hrs)"]
    result = grouped.agg(
        n="count",
        min_hrs="min",
        median_hrs="median",
        p95_hrs=lambda s: s.quantile(0.95),
        max_hrs="max",
    ).reset_index()
    return result


def flag_implausible_work(work_hours: float, opwkcen: str, ranges: pd.DataFrame) -> str | None:
    discipline = DISCIPLINE_TO_OPWKCEN.get(opwkcen)
    if discipline is None:
        return None
    matching = ranges[ranges["Discipline"] == discipline]
    if matching.shape[0] == 0:
        return None
    max_hrs = matching["max_hrs"].iloc[0]
    if max_hrs and work_hours >= max_hrs * IMPLAUSIBLE_MULTIPLIER:
        return "SUSPICIOUS"
    return None
