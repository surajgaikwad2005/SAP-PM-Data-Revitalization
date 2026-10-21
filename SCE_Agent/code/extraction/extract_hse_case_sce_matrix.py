"""
HSE Case Part 3A - SCE x MAH-Bowtie x Platform applicability matrix
------------------------------------------------------------------
Per user direction: the earlier general-purpose HSE Case chunking pass
(extract_hse_case.py) was too broad - the actual ground-truth table the
SCE Agent needs is one specific 4-page matrix in Book 2:

  Section 3A.1 "Safety Critical Elements for Bokor, Betty, Laila and
  Bakau Fields" - physical pages 644-647 of Book 2 (confirmed by finding
  every page carrying the table's own "SCE-PS Present on" header; page
  648 starts "PART 3B - EMERGENCY RESPONSE PLAN", confirming the table
  ends there).

The table cross-references, for every individual SCE (SI001, IC004,
PS014, SD001, ...): which of the 7 MAH Bowties it's linked to, and on
which of the 18 platforms it is present / not applicable.

This is NOT extractable reliably from plain text - get_text() reads the
wide, mostly-blank matrix in a misleading order. `page.find_tables()`
returns it as one real 33-row x 85-column grid instead, with blank cells
preserved as None at the correct column position - that's what's used
here. Column meaning is determined programmatically from the header rows
(search for known anchor labels), not hand-counted, so this remains
correct even if find_tables() ever renumbers columns slightly.

Two further structural quirks handled:
  - A barrier-category summary row (e.g. "SI  Structural Integrity") has
    every applicability cell blank - it's a section label, not data; kept
    in a separate sheet rather than mixed into the SCE-level rows.
  - When an SCE's description text wraps, find_tables() puts the wrapped
    remainder into an otherwise-all-blank continuation row immediately
    below - merged back into the parent row.

Output: Data exploration/output/hse_case_sce_matrix.xlsx
  - SCE_Platform_Matrix   (SCE code, description, one column per platform)
  - SCE_MAH_Bowtie_Matrix (SCE code, description, one column per MAH bowtie)
  - Barrier_Categories    (the section-summary rows, for reference)

Run:
    python "code/extraction/extract_hse_case_sce_matrix.py"
"""

import re
import warnings
from pathlib import Path

import fitz
import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
BOOK2 = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "HSE Case 2020" / "Integrated Operations HSE Case for BOBELABK Fields Book 2.pdf"
OUT_DIR = Path(__file__).resolve().parents[2] / "Data exploration" / "output"
OUT_DIR.mkdir(exist_ok=True)
OUT_XLSX = OUT_DIR / "hse_case_sce_matrix.xlsx"

PAGE_START, PAGE_END = 644, 647  # 1-indexed, confirmed by "SCE-PS Present on" scan

PLATFORMS = ["BOCPP-A", "BOK-A", "BOP-A", "BODP-A", "BOV-A", "BODP-B", "BODP-C", "BODP-D",
             "BODP-E", "BODP-F", "BEP-A", "BEDP-A", "BEV-A", "LADR-A", "BKP-A", "BKJT-A",
             "BK-3", "BKV-A"]
MAH_LABELS = [
    "H.01.01 Loss of Containment Hydrocarbon Under Pressure (Topsides)",
    "H.01.01 Loss of Containment Hydrocarbon Under Pressure (Risers/Pipelines)",
    "H.01.02 Loss of Containment Hydrocarbon Under Pressure (Platform Wells)",
    "H.06.03 Structure Failure",
    "H.08.02 Helicopter Crash",
    "H.08.03 Boat Collision",
    "MAH06 Overhead Equipment/Objects Under Tension",
]

SCE_CODE_RE = re.compile(r"^[A-Z]{2,3}\d{3}$")
BARRIER_CODE_RE = re.compile(r"^[A-Z]{2}$")


def clean(v):
    if v is None:
        return None
    v = re.sub(r"\s+", " ", str(v)).strip()
    return v if v else None


def find_col(header_rows, needle, occurrence=0):
    """Column index whose text (ffilled across header rows) matches
    `needle`. `occurrence` picks the Nth match, left to right."""
    hits = []
    for c in range(len(header_rows[0])):
        for r in header_rows:
            val = clean(r[c])
            if val and needle.lower() in val.lower():
                hits.append(c)
                break
    return hits[occurrence] if len(hits) > occurrence else None


def get_matrix_table(page):
    tabs = page.find_tables()
    for t in tabs.tables:
        rows = t.extract()
        if len(rows) < 5:  # must have at least the 4 header rows + 1 data row
            continue
        joined = " ".join(clean(c) or "" for c in rows[0])
        if "SCE-PS Present on" in joined:
            return rows
    raise RuntimeError("matrix table not found on this page")


def contiguous_blocks(row):
    """Column ranges of consecutive non-None cells in a header row, in
    left-to-right order - one block per label, however many lines (cells)
    that label's own text wraps across."""
    blocks = []
    start = None
    for c, v in enumerate(list(row) + [None]):  # sentinel None to close the last block
        if clean(v) is not None:
            if start is None:
                start = c
        else:
            if start is not None:
                blocks.append(start)
                start = None
    return blocks


def build_column_map(header_rows):
    """Map each of the 18 platform names and 7 MAH labels to a column
    index. Both live one column to the LEFT of where their own label text
    starts (confirmed by inspection: the label sits in its own cell(s),
    the checkmark/value for that column is un-labelled and lands
    immediately before it) - true whether the label is a single cell
    (platform codes) or wraps across several (MAH bowtie names)."""
    code_row = header_rows[2]  # row with 'BOCPP-A', 'BOK-A', ...
    platform_cols = {}
    for c, v in enumerate(code_row):
        name = clean(v)
        if name in PLATFORMS and name not in platform_cols.values():
            platform_cols[max(c - 1, 0)] = name

    sce_code_col = find_col(header_rows, "SCE\nCode".split("\n")[0]) or find_col(header_rows, "SCE Code")
    desc_col = find_col(header_rows, "Safety Critical Elements")

    # MAH columns: the label row's first 7 contiguous text blocks are the
    # 7 MAH bowties, in order (further blocks are "Consequences", "SCE
    # Code", "Safety Critical Elements", then the platform-group labels).
    mah_cols = {}
    row0 = header_rows[1]
    block_starts = contiguous_blocks(row0)[:len(MAH_LABELS)]
    for i, c in enumerate(block_starts):
        mah_cols[max(c - 1, 0)] = MAH_LABELS[i]

    return sce_code_col, desc_col, platform_cols, mah_cols


def main():
    doc = fitz.open(str(BOOK2))
    print(f"HSE Case Book 2: extracting Part 3A.1 matrix, pages {PAGE_START}-{PAGE_END}")

    sce_rows, barrier_rows = [], []
    col_map = None
    pending_desc_continuation = None  # (row_dict) awaiting a wrapped description tail

    for pidx in range(PAGE_START - 1, PAGE_END):
        page = doc[pidx]
        rows = get_matrix_table(page)
        header_rows = rows[:4]
        if col_map is None:
            col_map = build_column_map(header_rows)
        sce_code_col, desc_col, platform_cols, mah_cols = col_map

        for r in rows[3:]:  # row 3 onward: first barrier-category row, then SCE rows
            code = clean(r[sce_code_col]) if sce_code_col is not None else None
            desc = clean(r[desc_col]) if desc_col is not None else None
            # description sometimes lands one column to the right when the
            # code cell itself is merged - fall back to scanning nearby cells
            if desc is None and sce_code_col is not None:
                for off in (1, 2):
                    v = clean(r[sce_code_col + off]) if sce_code_col + off < len(r) else None
                    if v:
                        desc = v
                        break

            if code is None and desc and pending_desc_continuation is not None:
                # wrapped continuation of the previous row's description
                pending_desc_continuation["description"] = (
                    (pending_desc_continuation["description"] or "") + " " + desc
                ).strip()
                continue

            if code is None:
                continue

            platform_vals = {name: clean(r[c]) for c, name in platform_cols.items()}
            mah_vals = {name: clean(r[c]) for c, name in mah_cols.items()}

            record = {
                "sce_code": code,
                "description": desc,
                **platform_vals,
                "_mah": mah_vals,
                "source": f"HSE Case Book 2, Part 3A.1 (page {pidx + 1})",
            }

            if BARRIER_CODE_RE.match(code) and not SCE_CODE_RE.match(code):
                barrier_rows.append({"barrier_code": code, "barrier_name": desc,
                                    "source": record["source"]})
                pending_desc_continuation = None
            elif SCE_CODE_RE.match(code):
                sce_rows.append(record)
                pending_desc_continuation = record
            else:
                pending_desc_continuation = None

    doc.close()

    platform_df = pd.DataFrame([
        {"sce_code": r["sce_code"], "description": r["description"],
         **{p: r.get(p) for p in PLATFORMS}, "source": r["source"]}
        for r in sce_rows
    ])
    mah_df = pd.DataFrame([
        {"sce_code": r["sce_code"], "description": r["description"],
         **r["_mah"], "source": r["source"]}
        for r in sce_rows
    ])
    barrier_df = pd.DataFrame(barrier_rows)

    print(f"\nSCE rows extracted: {len(platform_df)}")
    print(f"Barrier category rows: {len(barrier_df)}")
    print(f"Distinct SCE codes: {platform_df['sce_code'].nunique()}")
    print("\nSample:")
    print(platform_df.head(5).to_string())

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        platform_df.to_excel(xl, sheet_name="SCE_Platform_Matrix", index=False)
        mah_df.to_excel(xl, sheet_name="SCE_MAH_Bowtie_Matrix", index=False)
        barrier_df.to_excel(xl, sheet_name="Barrier_Categories", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
