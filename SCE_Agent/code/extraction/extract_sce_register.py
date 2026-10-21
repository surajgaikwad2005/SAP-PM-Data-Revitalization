"""
Group A - SCE register extraction (Lane 1: tabular register documents)
------------------------------------------------------------------------
Extracts the per-Functional-Location SCE register out of:

  - BOKOR SCE ID REPORT_Rev01 (4) 2.pdf            (38 pages, summary report)
  - BOKOR SIGN OFF PAGE_SCE ID_<DISCIPLINE>.pdf     (11 files, ~3,585 pages
                                                      combined - the detailed
                                                      per-FL attachments)

Document structure (confirmed by inspection, see
code/extraction/SCE_Document_Extraction_Strategy.md):

  ATTACHMENT <n>
  <ATTACHMENT TITLE>                       e.g. "SCE FUNCTIONAL LOCATION FOR ER003"
                                                 "NON-SCE FUNCTIONAL LOCATION"
                                                 "TO INACTIVE FUNCTIONAL LOCATION"

      SUMMARY
        Table <n>-A Functional Location to <ACTION PHRASE>    <count>
        Table <n>-B Functional Location to <ACTION PHRASE>    <count>
        TOTAL SCE FL FOR <TITLE-DERIVED CODE>                 <count>

      Table <n>-A Functional Location to <ACTION PHRASE>
        NO | FUNCTIONAL LOCATION | DESCRIPTION FUNCTIONAL LOCATION | JUSTIFICATION [| REMARKS]
        ... (rows continue across pages, header repeats each page) ...

Important: attachments are NOT all "SCE FUNCTIONAL LOCATION FOR <CODE>". A
full scan of the ELECTRICAL file found 14 attachments: 12 per-SCE-group
registers, plus "NON-SCE FUNCTIONAL LOCATION" (declassify / maintain as
non-SCE) and "TO INACTIVE FUNCTIONAL LOCATION" - other disciplines may also
carry "TO RELOCATE SCE GROUP" / "TO DELETE FL" per the categories the main
SCE ID Report itself defines. So the extractor keeps the attachment title
and the table's action phrase as free text rather than forcing them into a
fixed maintain/classify enum - `sce_group` is only populated when the title
is genuinely "SCE FUNCTIONAL LOCATION FOR <CODE>".

Every page is a genuine PDF table with (invisible) column dividers, so
PyMuPDF's native `page.find_tables()` extracts every row cleanly - no OCR,
no LLM, pure deterministic parsing. ~70 ms/page -> the full ~3,600 pages
takes under 5 minutes.

Output:
  Data exploration/output/sce_register.db      (SQLite, table: sce_register)
  Data exploration/output/sce_register.xlsx    (register + validation sheets)

Run:
    python "code/extraction/extract_sce_register.py"
"""

import re
import sqlite3
import warnings
from pathlib import Path

import fitz  # PyMuPDF
import pandas as pd

warnings.simplefilter("ignore")

# ----------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]
SCE_DIR = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Asset Master" / "BOKOR SCE REPORT"

OUT_DIR = Path(__file__).resolve().parents[2] / "Data exploration" / "output"
OUT_DIR.mkdir(exist_ok=True)
OUT_DB = OUT_DIR / "sce_register.db"
OUT_XLSX = OUT_DIR / "sce_register.xlsx"

# (filename, discipline label) - the 11 discipline sign-off PDFs
DISCIPLINE_FILES = [
    ("BOKOR SIGN OFF PAGE_SCE ID_ELECTRICAL.pdf", "ELECTRICAL"),
    ("BOKOR SIGN OFF PAGE_SCE ID_INSTRUMENT (Signed) mfm 1.pdf", "INSTRUMENT"),
    ("BOKOR SIGN OFF PAGE_SCE ID_MECHANICAL ROTATING 1.pdf", "MECHANICAL ROTATING"),
    ("BOKOR SIGN OFF PAGE_SCE ID_MECHANICAL STATIC REV.1 - signed approved.pdf", "MECHANICAL STATIC"),
    ("BOKOR SIGN OFF PAGE_SCE ID_METERING.pdf", "METERING"),
    ("BOKOR SIGN OFF PAGE_SCE ID_OPERATION.pdf", "OPERATION"),
    ("BOKOR SIGN OFF PAGE_SCE ID_PIPELINE 1.pdf", "PIPELINE"),
    ("BOKOR SIGN OFF PAGE_SCE ID_PIPING_Rev01 1.pdf", "PIPING"),
    ("BOKOR SIGN OFF PAGE_SCE ID_SAFETY.pdf", "SAFETY"),
    ("BOKOR SIGN OFF PAGE_SCE ID_STRUCTURE.pdf", "STRUCTURE"),
    ("BOKOR SIGN OFF PAGE_SCE ID_WELL.pdf", "WELL"),
]

# ----------------------------------------------------------------------
# Regex patterns (confirmed against the real document text)
# ----------------------------------------------------------------------
# Generic attachment header: "ATTACHMENT <n>" followed by a title, either
# on the same line ("ATTACHMENT 1 SCE FUNCTIONAL LOCATION FOR ER010" - used
# by some discipline files) or on the next line ("ATTACHMENT 1\nSCE
# FUNCTIONAL LOCATION FOR ER003" - used by others) - `\s+` covers both.
# The title is captured verbatim; SCE_GROUP_IN_TITLE_RE below pulls a code
# out of it only when the title actually is a per-SCE-group register.
ATTACHMENT_RE = re.compile(r"ATTACHMENT\s+(\d+)\s+([A-Z0-9 \-/]+?)\s*\n", re.M)
SCE_GROUP_IN_TITLE_RE = re.compile(r"^SCE FUNCTIONAL LOCATION FOR\s+([A-Z0-9]+)$")

# "Table <n>-<letter> [Functional Location to | FL to] <ACTION PHRASE>" -
# the "Functional Location to"/"FL to" lead-in varies by discipline file
# (and is sometimes absent, e.g. "Table 1-C Relocate SCE Group"), and the
# verb is inconsistently cased ("Maintain" vs "maintain"). The action
# phrase itself is kept as free text either way (e.g. "Maintain as ER003",
# "classify as PC006", "Relocate SCE Group", "Declassify to Non-SCE").
_LEADIN = r"(?:Functional Location to|FL to)?\s*"
# Table letters are inconsistently cased between disciplines too
# ("Table 1-A" vs "Table 1-a") - accept both.
TABLE_HEADING_RE = re.compile(r"Table\s+(\d+)-([A-Za-z])\s+" + _LEADIN + r"([A-Za-z0-9\- ]+?)\s*\n")

TOTAL_RE = re.compile(r"TOTAL SCE FL FOR\s+([A-Z0-9\- ]+?)\s*\n\s*(\d+)")
SUBTOTAL_RE = re.compile(r"Table\s+\d+-[A-Za-z]\s+" + _LEADIN + r"([A-Za-z0-9\- ]+?)\s*\n\s*(\d+)")
PAGE_RE = re.compile(r"Page\s+(\d+)\s+of\s+(\d+)")


def clean_row(row):
    """PyMuPDF splits merged cells into several empty ('' / None) columns.
    Collapse to just the non-empty values, in order."""
    return [str(c).strip() for c in row if c not in (None, "")]


def _real_heading_events(text):
    """Locate every GENUINE 'Table n-X ... <action>' section heading in the
    page text, as a (text_offset, action_phrase) event.

    Every attachment's first page also repeats this exact phrase once
    inside the small SUMMARY table (immediately followed by a row count,
    e.g. '...as ER003\\n918'). That occurrence must be excluded, or a
    transition page (Table-A's tail + Table-B's start) gets both its
    tables mistyped from the summary line alone. A real section heading
    is always followed by the data-table header ('NO / FUNCTIONAL
    LOCATION / ...'), never by a bare number - that's the discriminator.
    Working in text-offset space (not pixel coordinates) keeps this
    exactly in the same reading order as the tables themselves.
    """
    events = []
    for m in TABLE_HEADING_RE.finditer(text):
        tail = text[m.end() : m.end() + 20].strip()
        if tail[:1].isdigit():
            continue  # this is the SUMMARY table's row, not a section heading
        events.append((m.start(), m.group(3).strip()))
    return events


def extract_pdf(path: Path, discipline: str):
    """Yield register rows + total-check rows for one PDF."""
    doc = fitz.open(str(path))
    current_title = None
    current_group = None
    current_action = None
    rows_out = []
    totals_out = []

    for pidx in range(doc.page_count):
        page = doc[pidx]
        text = page.get_text()

        for m in ATTACHMENT_RE.finditer(text):
            title = m.group(2).strip()
            gm = SCE_GROUP_IN_TITLE_RE.match(title)
            current_title = title
            current_group = gm.group(1) if gm else None

        for m in TOTAL_RE.finditer(text):
            # Use the attachment title already tracked from the ATTACHMENT
            # header (not the bare code in "TOTAL SCE FL FOR <code>"), so
            # this joins cleanly against the register rows' own
            # attachment_title during validation.
            totals_out.append(
                {
                    "source_file": path.name,
                    "discipline": discipline,
                    "attachment_title": current_title,
                    "action": "grand_total",
                    "reported_total": int(m.group(2)),
                }
            )
        for m in SUBTOTAL_RE.finditer(text):
            action, n = m.groups()
            totals_out.append(
                {
                    "source_file": path.name,
                    "discipline": discipline,
                    "attachment_title": current_title,
                    "action": action.strip(),
                    "reported_total": int(n),
                }
            )

        pg_m = PAGE_RE.search(text)
        printed_page = int(pg_m.group(1)) if pg_m else None

        try:
            tabs = page.find_tables()
        except Exception:
            continue

        # Order tables top-to-bottom and locate each DATA table's own text
        # offset, so it can be compared against the heading events in the
        # same offset space and typed correctly even on a transition page
        # (one table's tail + the next table's start on one page).
        page_tables = sorted(tabs.tables, key=lambda t: t.bbox[1])
        heading_events = _real_heading_events(text)
        search_from = 0
        dated_tables = []
        for tbl in page_tables:
            raw_rows = tbl.extract()
            if not raw_rows:
                continue
            header = clean_row(raw_rows[0])
            header_u = " ".join(header).upper()
            if "FUNCTIONAL LOCATION" not in header_u or "JUSTIFICATION" not in header_u:
                continue  # not a register data table (skip boilerplate/summary tables)
            offset = text.find("DESCRIPTION FUNCTIONAL LOCATION", search_from)
            if offset == -1:
                offset = search_from
            search_from = offset + 1
            dated_tables.append((offset, raw_rows))

        event_idx = 0
        for offset, raw_rows in dated_tables:
            while event_idx < len(heading_events) and heading_events[event_idx][0] <= offset:
                current_action = heading_events[event_idx][1]
                event_idx += 1

            for r in raw_rows[1:]:
                vals = clean_row(r)
                if len(vals) >= 4:
                    no, fl, desc, just = vals[0], vals[1], vals[2], " ".join(vals[3:])
                elif len(vals) == 3:
                    no, fl, desc, just = None, vals[0], vals[1], vals[2]
                else:
                    continue
                rows_out.append(
                    {
                        "source_file": path.name,
                        "discipline": discipline,
                        "attachment_title": current_title,
                        "sce_group": current_group,
                        "action": current_action,
                        "no": no,
                        "functional_location": fl,
                        "description": desc,
                        "justification": just,
                        "pdf_page_index": pidx,
                        "printed_page": printed_page,
                    }
                )
    doc.close()
    return rows_out, totals_out


def main():
    all_rows = []
    all_totals = []

    # Main summary report (small, 38 pages) - same structure, discipline="ALL"
    main_report = SCE_DIR / "BOKOR SCE ID REPORT_Rev01 (4) 2.pdf"
    if main_report.exists():
        print(f"Extracting: {main_report.name}")
        rows, totals = extract_pdf(main_report, "ALL")
        print(f"  -> {len(rows)} rows, {len(totals)} total-checks")
        all_rows += rows
        all_totals += totals

    for fname, discipline in DISCIPLINE_FILES:
        path = SCE_DIR / fname
        if not path.exists():
            print(f"  ! missing file, skipped: {fname}")
            continue
        print(f"Extracting: {fname}  ({discipline})")
        rows, totals = extract_pdf(path, discipline)
        print(f"  -> {len(rows)} rows, {len(totals)} total-checks")
        all_rows += rows
        all_totals += totals

    register_df = pd.DataFrame(all_rows)
    totals_df = pd.DataFrame(all_totals).drop_duplicates()

    print(f"\nTotal register rows extracted: {len(register_df):,}")

    # --------------------------------------------------------------
    # Validation: extracted row counts per (file, attachment, action)
    # vs the document's own printed "TOTAL SCE FL FOR ..." / per-table
    # subtotal figures.
    # --------------------------------------------------------------
    # Join case-insensitively: the SUMMARY row's own subtotal line and the
    # real section heading are sometimes cased differently by the same
    # document ("FL to maintain as PC003" vs "Functional Location to
    # Maintain as PC003") even though they describe the same table - that
    # is a cosmetic authoring inconsistency, not a data difference.
    def _key(df, col):
        return df[col].astype(str).str.strip().str.lower()

    extracted_counts = (
        register_df.groupby(["source_file", "discipline", "attachment_title", "action"])
        .size()
        .reset_index(name="extracted_count")
    )
    grand_totals = (
        register_df.groupby(["source_file", "discipline", "attachment_title"])
        .size()
        .reset_index(name="extracted_count")
    )
    grand_totals["action"] = "grand_total"
    extracted_counts = pd.concat([extracted_counts, grand_totals], ignore_index=True)
    extracted_counts["_title_key"] = _key(extracted_counts, "attachment_title")
    extracted_counts["_action_key"] = _key(extracted_counts, "action")

    totals_df["_title_key"] = _key(totals_df, "attachment_title")
    totals_df["_action_key"] = _key(totals_df, "action")

    validation_df = totals_df.merge(
        extracted_counts[["source_file", "discipline", "_title_key", "_action_key", "extracted_count"]],
        on=["source_file", "discipline", "_title_key", "_action_key"],
        how="left",
    ).drop(columns=["_title_key", "_action_key"])
    validation_df["extracted_count"] = validation_df["extracted_count"].fillna(0).astype(int)
    validation_df["match"] = validation_df["extracted_count"] == validation_df["reported_total"]
    print(
        f"Validation: {validation_df['match'].sum()}/{len(validation_df)} "
        f"attachment/table totals match the document's own printed total exactly"
    )

    # --------------------------------------------------------------
    # Write SQLite DB
    # --------------------------------------------------------------
    with sqlite3.connect(OUT_DB) as con:
        register_df.to_sql("sce_register", con, if_exists="replace", index=False)
        totals_df.to_sql("sce_register_reported_totals", con, if_exists="replace", index=False)
        validation_df.to_sql("sce_register_validation", con, if_exists="replace", index=False)
    print(f"SQLite DB written to: {OUT_DB}")

    # --------------------------------------------------------------
    # Write Excel workbook
    # --------------------------------------------------------------
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary = pd.DataFrame(
            {
                "Metric": [
                    "Files processed",
                    "Total register rows extracted",
                    "Distinct attachment titles found",
                    "Distinct SCE Group codes found",
                    "Distinct Functional Locations",
                    "Attachment/table totals matching document's own printed total",
                ],
                "Value": [
                    1 + len(DISCIPLINE_FILES),
                    len(register_df),
                    register_df["attachment_title"].nunique(),
                    register_df["sce_group"].nunique(),
                    register_df["functional_location"].nunique(),
                    f"{validation_df['match'].sum()}/{len(validation_df)}",
                ],
            }
        )
        summary.to_excel(xl, sheet_name="Summary", index=False)
        register_df.to_excel(xl, sheet_name="SCE_Register", index=False)
        validation_df.to_excel(xl, sheet_name="Validation_vs_Doc_Totals", index=False)

        by_group = (
            register_df.groupby(["discipline", "attachment_title", "action"])
            .size()
            .reset_index(name="count")
        )
        by_group.to_excel(xl, sheet_name="Counts_by_Attachment", index=False)

        mismatches = validation_df[~validation_df["match"]]
        mismatches.to_excel(xl, sheet_name="Mismatches_for_review", index=False)

    print(f"Excel workbook written to: {OUT_XLSX}")


if __name__ == "__main__":
    main()
