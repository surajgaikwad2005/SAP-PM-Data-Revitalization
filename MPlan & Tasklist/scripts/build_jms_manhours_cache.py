from pathlib import Path

import pandas as pd

SCHEMA_COLUMNS = [
    "source_pdf",
    "source_page_number",
    "source_section_label",
    "platform_stated",
    "platform_verified_bokor",
    "job_description",
    "equipment_tag",
    "work_order_or_po_number",
    "crew_size",
    "crew_trade_breakdown",
    "hours_per_task",
    "total_manhours",
    "notes",
]


def merge_extraction_csvs(extraction_dir: str) -> pd.DataFrame:
    csv_paths = sorted(Path(extraction_dir).glob("*.csv"))
    frames = []
    for path in csv_paths:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
        missing = set(SCHEMA_COLUMNS) - set(frame.columns)
        if missing:
            raise ValueError(f"{path.name} is missing required columns: {sorted(missing)}")
        frames.append(frame[SCHEMA_COLUMNS])
    if not frames:
        return pd.DataFrame(columns=SCHEMA_COLUMNS)
    return pd.concat(frames, ignore_index=True)


def write_jms_manhours_cache(merged: pd.DataFrame, cache_dir: str) -> str:
    out_path = Path(cache_dir) / "PP05_JMS_ManHours.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(out_path, index=False, encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    extraction_dir = base / "ground_truth_sources" / "jms_workpacks" / "_extraction_csvs"
    cache_dir = base / "ground_truth_cache"

    merged = merge_extraction_csvs(str(extraction_dir))
    out_path = write_jms_manhours_cache(merged, str(cache_dir))

    source_pdfs = merged["source_pdf"].nunique()
    status_counts = merged["platform_verified_bokor"].value_counts().to_dict()
    print(f"wrote {len(merged)} rows from {source_pdfs} source PDFs to {out_path}")
    print(f"platform_verified_bokor breakdown: {status_counts}")
