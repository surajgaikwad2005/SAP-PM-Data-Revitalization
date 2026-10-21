"""
The SPIR store - the agent's source of extracted spare-parts data.

Extraction is a SEPARATE, OFFLINE job (../extract_new_spir.py).  It reads the
vendor dossier PDFs once and writes what it found to disk.  The agent never
calls a vision model and never opens a PDF; it just reads what the extraction
already produced and maps it onto SAP equipment.

Today the store is backed by the extraction's own workbook, spir_extraction.xlsx,
specifically its "Parts" sheet - one row per spare part, already flattened and
holding only the latest extraction of each page (a re-run of a page replaces
that page's rows, so this store has nothing to deduplicate).  When
PCSB hand over the full SPIR set it becomes a real database table, and only
`parts()` below has to change - everything downstream keeps working.
"""
from __future__ import annotations
import json

import pandas as pd

import config as C

SPIR_DIR = C.BASE / "07_SPIR"
EXTRACT_DIR = SPIR_DIR / "_extracted"
WORKBOOK = EXTRACT_DIR / "spir_extraction.xlsx"

# The columns a part row carries, in the order a reader wants them.
PART_COLUMNS = [
    "source_pdf", "source_page", "doc_type", "extraction",
    "equipment_tag", "equipment_description", "manufacturer", "spir_number",
    "item_no", "description", "material_spec", "drawing_no",
    "supplier_brand", "manufacturer_part_no", "supplier_part_no", "mesc_number",
    "unit", "no_of_parts_per_unit", "qty_per_unit", "total_qty_installed",
    "qty_commissioning", "qty_initial_1yr", "qty_2yr_operation",
    "unit_price", "currency", "delivery_weeks",
]


def parts() -> pd.DataFrame:
    """One tidy row per spare part, from the extraction workbook's Parts sheet."""
    if not WORKBOOK.exists():
        return pd.DataFrame(columns=PART_COLUMNS)
    # Every cell as text, a blank as "" - what the extraction wrote.  Left to
    # pandas a blank becomes NaN, which is truthy, so `str(x or "")` downstream
    # turns an empty quantity or MESC cell into the text "nan".
    df = pd.read_excel(WORKBOOK, sheet_name="Parts", dtype=str, keep_default_na=False)
    df["source_page"] = df["source_page"].astype(int)
    for col in PART_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[PART_COLUMNS] if len(df) else pd.DataFrame(columns=PART_COLUMNS)


def summary() -> dict:
    df = parts()
    if not len(df):
        return {"part_rows": 0, "pages": 0, "documents": 0, "equipment_tags": 0}
    return {
        "part_rows": len(df),
        "pages": int(df.groupby(["source_pdf", "source_page"]).ngroups),
        "documents": int(df["source_pdf"].nunique()),
        "equipment_tags": int(df["equipment_tag"].dropna().nunique()),
    }


if __name__ == "__main__":
    print(json.dumps(summary(), indent=2))
    print(parts().to_string())
