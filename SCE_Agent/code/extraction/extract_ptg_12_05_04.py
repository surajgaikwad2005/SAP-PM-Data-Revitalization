"""
PTG 12.05.04 (PMMS) extraction
------------------------------------------------------------------
This document has 754 real PDF bookmarks down to clause level - the
highest-fidelity chunking case in scope. Two things beyond generic
chunking are worth extracting as clean tables:

  - a Term/Definition glossary (deterministic grid, `find_tables()`
    returns it cleanly)
  - Appendix 7 "List of CATALOG PROFILE" - a 2-column (code, description)
    table spanning multiple pages - directly feeds `ptg_class_spec` for
    Check 6 (SCE class/catalog-profile completeness)

Output: Data exploration/output/ptg_12_05_04_extraction.xlsx
  - Sections    (23 level-1 bookmark chunks, for citation)
  - Glossary
  - Catalog_Profiles

Run:
    python "code/extraction/extract_ptg_12_05_04.py"
"""

import re
import warnings
from pathlib import Path

import fitz
import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
PTG = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "MANUAL GUIDELINE" / "PTG 12.05.04 - PMMS.pdf"
OUT_DIR = Path(__file__).resolve().parents[2] / "Data exploration" / "output"
OUT_DIR.mkdir(exist_ok=True)
OUT_XLSX = OUT_DIR / "ptg_12_05_04_extraction.xlsx"

BOILERPLATE_RE = re.compile(
    r"PETRONAS MAINTENANCE MANAGEMENT SYSTEM \(PMMS\)\s*PTG 12\.05\.04\s*March 2022\s*Page \d+ of \d+\s*Internal\s*",
    re.S,
)


def strip_boilerplate(text):
    return BOILERPLATE_RE.sub("\n", text)


def clean_cell(c):
    return re.sub(r"\s+", " ", str(c)).strip() if c else ""


def extract_sections(doc):
    """Level-1 bookmarks as citation chunks; every finer bookmark under
    each is kept as a sub-heading list for navigation within the chunk."""
    toc = doc.get_toc()
    lvl1 = [(i, t) for i, t in enumerate(toc) if t[0] == 1]
    sections = []
    for idx, (i, (lvl, title, page)) in enumerate(lvl1):
        next_page = lvl1[idx + 1][1][2] if idx + 1 < len(lvl1) else doc.page_count + 1
        p_start, p_end = page, max(page, next_page - 1)
        text = "\n".join(strip_boilerplate(doc[p - 1].get_text()) for p in range(p_start, p_end + 1))
        # sub-headings belonging to this section = every finer bookmark
        # between this level-1 entry and the next one
        end_idx = lvl1[idx + 1][0] if idx + 1 < len(lvl1) else len(toc)
        sub_headings = [t[1] for t in toc[i + 1:end_idx]]
        sections.append({
            "section_no": title.split(" ", 1)[0].rstrip(":"),
            "heading": title,
            "page_start": p_start,
            "page_end": p_end,
            "sub_heading_count": len(sub_headings),
            "char_count": len(text),
            "text": text.strip(),
            "source": f"PTG 12.05.04 (pages {p_start}-{p_end})",
        })
    return sections


def extract_glossary(doc):
    entries = []
    for pidx in range(doc.page_count):
        page = doc[pidx]
        for tbl in page.find_tables().tables:
            rows = tbl.extract()
            header_idx = None
            for i, r in enumerate(rows):
                joined = " ".join(clean_cell(c) for c in r).lower()
                if "term" in joined and "definition" in joined:
                    header_idx = i
                    break
            if header_idx is None:
                continue
            for r in rows[header_idx + 1:]:
                vals = [clean_cell(c) for c in r if clean_cell(c)]
                if len(vals) < 2:
                    continue
                no, term, definition = (vals + [None] * 3)[:3] if len(vals) >= 3 else (None, vals[0], vals[1])
                if not term or not definition or term.lower() == "term":
                    continue  # a repeated header row, not real data
                entries.append({"no": no, "term": term, "definition": definition,
                                "source": f"PTG 12.05.04 (page {pidx + 1})"})
    return entries


def extract_catalog_profiles(doc):
    # Match the level-1 "APPENDIX 7 :" heading itself, not the earlier
    # body-text bookmark ("3.4.8 ... Refer to Appendix 7 for the list...")
    # that mentions it in passing - `startswith`, not `in`, at level 1.
    toc = doc.get_toc()
    start_page = next((p for lvl, t, p in toc if lvl == 1 and t.upper().lstrip().startswith("APPENDIX 7")), None)
    end_page = next((p for lvl, t, p in toc if lvl == 1 and t.upper().lstrip().startswith("APPENDIX 8")), doc.page_count)
    if start_page is None:
        print("  Appendix 7 not found")
        return []
    print(f"  Appendix 7 spans pages {start_page}-{end_page - 1}")

    entries = []
    for pidx in range(start_page - 1, end_page - 1):
        page = doc[pidx]
        for tbl in page.find_tables().tables:
            rows = tbl.extract()
            for r in rows:
                vals = [clean_cell(c) for c in r if clean_cell(c)]
                if len(vals) != 2:
                    continue
                code, desc = vals
                if code.lower() == "catalog profile" or not re.match(r"^[A-Z0-9]{3,8}$", code):
                    continue
                entries.append({"catalog_profile": code, "description": desc,
                                "source": f"PTG 12.05.04 (page {pidx + 1})"})
    return entries


def main():
    doc = fitz.open(str(PTG))
    print(f"PTG 12.05.04: {doc.page_count} pages, {len(doc.get_toc())} bookmarks")

    sections = extract_sections(doc)
    print(f"\nLevel-1 sections: {len(sections)}")
    for s in sections:
        print(f"  {s['heading']:<65} pages {s['page_start']}-{s['page_end']}  ({s['sub_heading_count']} sub-headings, {s['char_count']} chars)")

    glossary = extract_glossary(doc)
    print(f"\nGlossary entries: {len(glossary)}")

    print("\nExtracting Appendix 7 catalog profiles...")
    profiles = extract_catalog_profiles(doc)
    print(f"Catalog profile entries: {len(profiles)}")

    doc.close()

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        pd.DataFrame(sections).to_excel(xl, sheet_name="Sections", index=False)
        pd.DataFrame(glossary).to_excel(xl, sheet_name="Glossary", index=False)
        pd.DataFrame(profiles).to_excel(xl, sheet_name="Catalog_Profiles", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
