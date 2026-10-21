"""
Group G4 - SSPS (Site Specific Performance Standard) extraction
------------------------------------------------------------------
Site-specific counterpart to GOPS4's generic per-SCE-Group standards.
Unlike GOPS4, SSPS tables ARE clean column-major grids (PyMuPDF
`find_tables()` returns real per-column values) - fully deterministic,
no LLM needed.

Structure confirmed by inspection (SKA_BOKOR_PS_PC005.pdf and others):

    PETRONAS OPERATIONAL PERFORMANCE STANDARD AND ASSURANCE TASK
    SCE GROUP: <CODE> <Name>          SCE GOAL: <goal text>
    RESPONSIBLE TECHNICAL AUTHORITY: <name>
    FUNCTIONALITY
      Functional Criteria | Assurance Task | Responsible Party |
      Min Acceptable Criteria | Frequency (Mthly) | Measurable Unit |
      Verification task | Supporting Document for Verification |
      No. of manpower | Duration (HR) | Applicable or not |
      Existing PS Responsible Party | [Responsible Party] | [Frequency] |
      Justification/Remarks
      (rows continue across pages; header + SCE GROUP/GOAL banner repeat
      on every page)

The `sce_group` code is read from each document's own "SCE GROUP:" text,
not guessed from the filename - several files under SSPS INSTRUMENT/
SSPS TELECOM have lost their real long filenames (Windows 8.3 short
names only, e.g. "SK601E~1.PDF"), so filename can't be relied on anyway.

Output:
  Data exploration/output/ssps_requirements.xlsx
    - SSPS_Groups: one row per document (sce_group, goal, discipline, source)
    - Functionality_Tasks: one row per assurance task, all 15 columns kept,
      named from the document's own header text (deduplicated), each with
      a `source` = filename + page.

Run:
    python "code/extraction/extract_ssps_requirements.py"
"""

import re
import warnings
from pathlib import Path

import fitz
import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
SSPS_DIR = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Asset Master" / "BOKOR SCE REPORT" / "SSPS"
OUT_DIR = Path(__file__).resolve().parents[2] / "Data exploration" / "output"
OUT_DIR.mkdir(exist_ok=True)
OUT_XLSX = OUT_DIR / "ssps_requirements.xlsx"

SCE_GROUP_RE = re.compile(r"SCE GROUP:\s*\n?\s*([A-Z]{2}\d{3})\s+(.+)", re.M)
SCE_GOAL_RE = re.compile(r"SCE GOAL:\s*\n?(.+?)(?=RESPONSIBLE TECHNICAL AUTHORITY|BARRIER AUTHORITY|FUNCTIONALITY)", re.S)
AUTHORITY_RE = re.compile(r"RESPONSIBLE TECHNICAL AUTHORITY:\s*\n?(.+)")

HEADER_KEYWORDS = [
    ("functional criteria", "functional_criteria"),
    ("assurance task", "assurance_task"),
    ("responsible", "responsible_party"),
    ("min acceptable criteria", "min_acceptable_criteria"),
    ("minimum acceptable criteria", "min_acceptable_criteria"),
    ("frequency", "frequency"),
    ("measurable unit", "measurable_unit"),
    ("verification task", "verification_task"),
    ("supporting document", "supporting_document"),
    ("no. of manpower", "no_of_manpower"),
    ("duration", "duration_hr"),
    ("applicable or not", "applicable_or_not"),
    ("existing ps", "existing_ps_responsible_party"),
    ("justification", "justification_remarks"),
]


def clean_cell(c):
    return re.sub(r"\s+", " ", str(c)).strip() if c else ""


def map_headers(header_row):
    """Map each header cell to a canonical name via keyword match,
    de-duplicating repeats (e.g. 'Responsible Party' appears twice)."""
    names, seen = [], {}
    for cell in header_row:
        text = clean_cell(cell).lower()
        canon = None
        for kw, name in HEADER_KEYWORDS:
            if kw in text:
                canon = name
                break
        canon = canon or f"col_{len(names)}"
        n = seen.get(canon, 0)
        seen[canon] = n + 1
        names.append(canon if n == 0 else f"{canon}_{n + 1}")
    return names


def find_files():
    files = []
    for pdf in SSPS_DIR.rglob("*.[Pp][Dd][Ff]"):
        name_lower = pdf.name.lower()
        if "sign off" in name_lower or "signof" in name_lower:
            continue
        files.append(pdf)
    return sorted(files)


SHORT_NAME_RE = re.compile(r"~\d")


def display_name(path: Path, doc, sce_group, folder) -> str:
    """A handful of files under SSPS INSTRUMENT/TELECOM are saved on disk
    with a Windows-truncated 8.3-style short name (e.g. "SKA_BO~2.PDF") -
    the real filename is lost at the filesystem level. Recovery, in
    order: (1) the PDF's own embedded metadata Title, set when the
    source .xlsx was printed to PDF - recovers it for 4 of 6 files; (2)
    for the remaining 2 (SSPS TELECOM, no metadata title either), fall
    back to an honest descriptive citation built from the SCE Group the
    document's own content resolves to (already parsed regardless of
    filename) plus its folder - not a fabricated filename, but enough
    for a reviewer to actually locate the document."""
    if not SHORT_NAME_RE.search(path.stem):
        return path.name
    title = (doc.metadata or {}).get("title", "").strip()
    if title:
        return title
    if sce_group:
        return f"SSPS {sce_group} document, {folder} folder (original filename lost to a Windows path-length truncation on disk)"
    return path.name


def extract_pdf(path: Path):
    doc = fitz.open(str(path))
    full_text = "\n".join(doc[p].get_text() for p in range(doc.page_count))

    gm = SCE_GROUP_RE.search(full_text)
    sce_group, sce_group_name = (gm.group(1), gm.group(2).strip().split("\n")[0]) if gm else (None, None)
    disp_name = display_name(path, doc, sce_group, path.parent.name)
    goal_m = SCE_GOAL_RE.search(full_text)
    sce_goal = re.sub(r"\s+", " ", goal_m.group(1)).strip() if goal_m else None
    auth_m = AUTHORITY_RE.search(full_text)
    authority = auth_m.group(1).strip().split("\n")[0] if auth_m else None

    task_rows = []
    header_names = None
    last_criteria = None  # persists across pages/tables - a functional
    # criteria's assurance tasks (1.1, 1.2, ...) can continue onto the
    # next page, which find_tables() reports as a brand new table object
    for pidx in range(doc.page_count):
        page = doc[pidx]
        for tbl in page.find_tables().tables:
            rows = tbl.extract()
            header_idx = None
            for i, r in enumerate(rows):
                joined = " ".join(clean_cell(c) for c in r).lower()
                if "functional" in joined and "assurance task" in joined:
                    header_idx = i
                    break
            if header_idx is None:
                continue
            if header_names is None:
                header_names = map_headers(rows[header_idx])
            for r in rows[header_idx + 1:]:
                vals = [clean_cell(c) for c in r]
                if not any(vals):
                    continue
                rec = dict(zip(header_names, vals))
                if rec.get("functional_criteria"):
                    last_criteria = rec["functional_criteria"]
                else:
                    rec["functional_criteria"] = last_criteria
                if not rec.get("assurance_task"):
                    continue  # blank continuation row with nothing new
                rec["sce_group"] = sce_group
                rec["source"] = f"{disp_name} (page {pidx + 1})"
                task_rows.append(rec)
    doc.close()
    return {
        "sce_group": sce_group,
        "sce_group_name": sce_group_name,
        "sce_goal": sce_goal,
        "responsible_technical_authority": authority,
        "source_file": disp_name,
        "folder": path.parent.name,
    }, task_rows


def main():
    files = find_files()
    print(f"SSPS files found: {len(files)}")

    group_rows, all_task_rows, failures = [], [], []
    for path in files:
        try:
            group_rec, tasks = extract_pdf(path)
            group_rows.append(group_rec)
            all_task_rows += tasks
            print(f"  {path.name:<55} -> sce_group={group_rec['sce_group']!s:<8} {len(tasks)} tasks")
        except Exception as e:
            failures.append({"file": str(path), "error": str(e)})
            print(f"  {path.name:<55} -> FAILED: {e}")

    groups_df = pd.DataFrame(group_rows)
    tasks_df = pd.DataFrame(all_task_rows)
    failures_df = pd.DataFrame(failures)

    print(f"\nDocuments processed: {len(groups_df)}")
    print(f"Documents with no SCE GROUP code found: {groups_df['sce_group'].isna().sum()}")
    print(f"Total assurance-task rows: {len(tasks_df)}")

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        groups_df.to_excel(xl, sheet_name="SSPS_Groups", index=False)
        tasks_df.to_excel(xl, sheet_name="Functionality_Tasks", index=False)
        if len(failures_df):
            failures_df.to_excel(xl, sheet_name="Failures", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
