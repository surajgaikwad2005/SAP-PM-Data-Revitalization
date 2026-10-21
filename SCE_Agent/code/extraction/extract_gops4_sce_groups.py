"""
GOPS4 SCE Group standards extraction (deterministic - no LLM needed)
----------------------------------------------------------------------
Discovery: GOPS4.pdf is NOT plain narrative. From page ~20 to ~110 it is
organised exactly like SSPS - one section per SCE Group, same template
throughout:

    <CODE> <Name>
    PETRONAS OPERATIONAL PERFORMANCE STANDARD AND ASSURANCE TASK

    SCE GROUP: <CODE> <Name>
    SCE GOAL: <goal statement(s)>
    BARRIER AUTHORITY DISCIPLINE: <discipline>
    FUNCTIONALITY
      Functional Criteria | Assurance Task | Responsible Party |
      Minimum Acceptable Criteria | Frequency | Measurable Unit
      (rows...)
    AVAILABILITY: <text, often "Not applicable.">
    RELIABILITY: <text>
    SURVIVABILITY: <text>
    INTERDEPENDENCIES: <bullet list of other SCE Groups>
    REFERENCES (For Assurance Task): <bullet list>
    <Technical Authority sign-off block>

This is the *generic* (company-wide) counterpart to the *site-specific*
SSPS documents (Group G4) - same shape, same extraction technique
(PyMuPDF text + find_tables), no LLM required.

Only pages ~20-110 (the per-SCE-Group standards) are extracted this way.
Pages 0-19 are front matter (revision history, document structure,
introduction) - genuine narrative, handled separately if needed.

Output:
  Data exploration/output/gops4_sce_groups.xlsx
    - SCE_Groups: one row per SCE Group (goal, discipline, availability,
      reliability, survivability, interdependencies, references, source)
    - Functionality_Tasks: one row per assurance task (long form)

Run:
    python "code/extraction/extract_gops4_sce_groups.py"
"""

import re
import warnings
from pathlib import Path

import fitz
import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
GOPS4 = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "MANUAL GUIDELINE" / "GOPS4.pdf"
OUT_DIR = Path(__file__).resolve().parents[2] / "Data exploration" / "output"
OUT_DIR.mkdir(exist_ok=True)
OUT_XLSX = OUT_DIR / "gops4_sce_groups.xlsx"

SCE_GROUP_RE = re.compile(r"^SCE GROUP:\s*$", re.M)
CODE_RE = re.compile(r"^([A-Z]{2}\d{3})\s+(.+)$")
SECTION_LABELS = ["SCE GOAL:", "BARRIER AUTHORITY DISCIPLINE:", "FUNCTIONALITY",
                  "AVAILABILITY", "RELIABILITY", "SURVIVABILITY", "INTERDEPENDENCIES",
                  "REFERENCES (For Assurance Task)", "PETRONAS Revision"]


def clean_row(row):
    return [str(c).strip() for c in row if c not in (None, "")]


BOILERPLATE_RE = re.compile(
    r"PCSB GENERIC OPERATION\s*PERFORMANCE STANDARD \(GOPS\).*?"
    r"permission of the copyright owner\.\s*",
    re.S,
)


def strip_boilerplate(text):
    """Every page repeats the same title bar + copyright disclaimer -
    strip it so a section that spans a page break doesn't get that text
    stitched into the middle of it."""
    return BOILERPLATE_RE.sub("\n", text)


def split_sections(text):
    """Split one page's text into (label, body) chunks using the fixed
    section labels GOPS4 always uses, in the order they appear."""
    positions = []
    for label in SECTION_LABELS:
        for m in re.finditer(re.escape(label), text):
            positions.append((m.start(), label))
    positions.sort()
    sections = {}
    for i, (pos, label) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(text)
        body = text[pos + len(label):end].strip(" :\n")
        sections.setdefault(label, []).append(body)
    return sections


def main():
    doc = fitz.open(str(GOPS4))
    group_rows = []
    task_rows = []

    current_code = None
    current_name = None
    current_start_page = None
    buffer_text = []
    buffer_pages = []

    def flush():
        if current_code is None or not buffer_text:
            return
        full_text = "\n".join(buffer_text)
        sections = split_sections(full_text)
        source = f"GOPS4.pdf (pages {buffer_pages[0] + 1}-{buffer_pages[-1] + 1})"

        group_rows.append({
            "sce_group": current_code,
            "sce_group_name": current_name,
            "sce_goal": " ".join(sections.get("SCE GOAL:", [""])).strip(),
            "barrier_authority_discipline": " ".join(sections.get("BARRIER AUTHORITY DISCIPLINE:", [""])).strip(),
            "functionality_raw": " ".join(sections.get("FUNCTIONALITY", [""])).strip(),
            "availability": " ".join(sections.get("AVAILABILITY", [""])).strip(),
            "reliability": " ".join(sections.get("RELIABILITY", [""])).strip(),
            "survivability": " ".join(sections.get("SURVIVABILITY", [""])).strip(),
            "interdependencies": " | ".join(sections.get("INTERDEPENDENCIES", [""])).strip(),
            "references": " | ".join(sections.get("REFERENCES (For Assurance Task)", [""])).strip(),
            "source": source,
        })

        # Functionality tables: pull directly from PyMuPDF tables on this
        # section's pages (more reliable than text splitting for the grid).
        for pidx in buffer_pages:
            page = doc[pidx]
            for tbl in page.find_tables().tables:
                rows = tbl.extract()
                if not rows:
                    continue
                header = clean_row(rows[0])
                header_u = " ".join(header).upper()
                if "FUNCTIONAL CRITERIA" not in header_u or "ASSURANCE TASK" not in header_u:
                    continue
                for r in rows[1:]:
                    vals = clean_row(r)
                    if len(vals) < 2:
                        continue
                    rec = {"sce_group": current_code, "sce_group_name": current_name,
                           "source": f"GOPS4.pdf (page {pidx + 1})"}
                    labels = ["functional_criteria", "assurance_task", "responsible_party",
                              "minimum_acceptable_criteria", "frequency", "measurable_unit"]
                    for k, v in zip(labels, vals):
                        rec[k] = v
                    task_rows.append(rec)

    for pidx in range(doc.page_count):
        page = doc[pidx]
        text = strip_boilerplate(page.get_text())

        # New SCE Group starts where "SCE GROUP:" is followed by a code+name line
        m = SCE_GROUP_RE.search(text)
        if m:
            after = text[m.end():].strip().split("\n")
            code_line = after[0].strip() if after else ""
            cm = CODE_RE.match(code_line)
            if cm:
                flush()
                current_code, current_name = cm.group(1), cm.group(2).strip()
                current_start_page = pidx
                buffer_text, buffer_pages = [], []

        if current_code is not None:
            buffer_text.append(text)
            buffer_pages.append(pidx)

        # A "4.0 Responsible Technical Authority Signature" block ends the
        # entry; don't flush here though - the NEXT "SCE GROUP:" trigger
        # (or end of doc) does it, so trailing REFERENCES on a following
        # page are still captured.

    flush()
    doc.close()

    groups_df = pd.DataFrame(group_rows)
    tasks_df = pd.DataFrame(task_rows)

    print(f"SCE Groups found: {len(groups_df)}")
    print(f"Functionality task rows: {len(tasks_df)}")
    print("\nSCE Group codes:", groups_df["sce_group"].tolist())

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        groups_df.to_excel(xl, sheet_name="SCE_Groups", index=False)
        tasks_df.to_excel(xl, sheet_name="Functionality_Tasks", index=False)
    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
