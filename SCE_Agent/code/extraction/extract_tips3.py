"""
TIPS3 (Safety Critical Elements Manual) extraction
------------------------------------------------------------------
TIPS3 is NOT one narrative blob - direct inspection found four distinct
parts, each needing its own technique:

  1. Numbered procedural sections (2-10)  -> regex chunking (Lane 2, for
     citation; this is genuine prose guidance on the MAH/SCE process,
     roles & responsibilities, barrier types)
  2. Appendix B - Glossary of Terms       -> deterministic (acronym /
     definition pairs are plain alternating lines, not a bordered table)
  3. Section 10 - SCE catalog list        -> deterministic (code + title
     pairs grouped by barrier type) - a cross-check against the
     BARRIER OWNER sheet already in the SAP-side Excel
  4. Appendix D - SCE Group Description / Goal / Typical Equipment /
     System Level & Boundaries per SCE group -> LLM-assisted, because
     (like GOPS4's FUNCTIONALITY table) find_tables() returns a messy,
     misaligned grid here, not a clean one - the raw text per SCE group
     is captured deterministically and only the row-splitting is done by
     the model, verbatim, temperature 0.

Appendix A (references, numbered list) and Appendix C (a bowtie diagram
image) are skipped - no extractable ground-truth content.

Output: Data exploration/output/tips3_extraction.xlsx
  - Sections            (chunk-level, for citation)
  - Glossary
  - SCE_Catalog
  - SCE_Group_Definitions (Appendix D, LLM-structured)

Run:
    python "code/extraction/extract_tips3.py"
"""

import json
import re
import sys
import warnings
from pathlib import Path

import fitz
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # code/
from common.llm import chat, llm_run  # noqa: E402 - Langfuse-traced LLM access

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
TIPS3 = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "MANUAL GUIDELINE" / "050514 TIPS 3 SCE Manual Rev.1 1.pdf"
OUT_DIR = Path(__file__).resolve().parents[2] / "Data exploration" / "output"
OUT_DIR.mkdir(exist_ok=True)
OUT_XLSX = OUT_DIR / "tips3_extraction.xlsx"


BOILERPLATE_RE = re.compile(
    r"Exploration and Production\s*TITLE\s*:\s*SAFETY CRITICAL ELEMENTS MANUAL.*?Page \d+ of \d+\s*",
    re.S,
)
PAGE_MARK = "\x00PAGE{}\x00"
PAGE_MARK_RE = re.compile(r"\x00PAGE(\d+)\x00")
TOP_HEADING_RE = re.compile(r"\n(\d{1,2})\.\s*\n")


def strip_boilerplate(text):
    return BOILERPLATE_RE.sub("\n", text)


def load_doc_text(doc):
    """Concatenate all pages with an embedded page marker so chunk
    boundaries can be mapped back to a page range afterward."""
    parts = []
    for i in range(doc.page_count):
        parts.append(PAGE_MARK.format(i))
        parts.append(strip_boilerplate(doc[i].get_text()))
    return "".join(parts)


def page_range_for_span(text, start, end):
    """first_page = the page the heading itself sits on (last marker
    before `start`); last_page = the page the chunk's content runs to
    (last marker before `end`, i.e. right up to the next heading)."""
    before_start = [int(m.group(1)) for m in PAGE_MARK_RE.finditer(text, 0, start)]
    before_end = [int(m.group(1)) for m in PAGE_MARK_RE.finditer(text, 0, end)]
    first_page = before_start[-1] if before_start else 0
    last_page = before_end[-1] if before_end else first_page
    return first_page + 1, last_page + 1  # 1-indexed


def extract_sections(full_text):
    """Top-level numbered sections (1., 2., ... 12.) as citation chunks.

    The same "N.\\n<title>" pattern also matches two false positives that
    must be filtered out: the Table of Contents (title immediately
    followed by a dot-leader + page number, e.g. "INTRODUCTION ....... 4")
    and Appendix A's own numbered reference list (also numbered 1-12,
    starting after the "APPENDIX A" marker) - real section headings have
    neither trait.
    """
    # "APPENDIX A" is also named in the Table of Contents (page 2) - use
    # the LAST occurrence, which is the real appendix heading, not the ToC.
    appendix_a_pos = full_text.rfind("APPENDIX A")
    cutoff = appendix_a_pos if appendix_a_pos != -1 else len(full_text)

    matches = list(TOP_HEADING_RE.finditer(full_text))
    sections = []
    for i, m in enumerate(matches):
        num = int(m.group(1))
        if not (1 <= num <= 12) or m.start() >= cutoff:
            continue
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        end = min(end, cutoff)
        body = PAGE_MARK_RE.sub("", full_text[start:end]).strip()
        if len(body) < 30:
            continue
        heading_line = body.split("\n")[0].strip()
        if "...." in body[:300]:
            continue  # Table of Contents entry (dot-leader + page number,
            # possibly after a wrapped multi-line title)
        p_start, p_end = page_range_for_span(full_text, m.start(), end)
        sections.append({
            "section_no": num,
            "heading": heading_line,
            "page_start": p_start,
            "page_end": p_end,
            "char_count": len(body),
            "text": body,
            "source": f"TIPS3 (pages {p_start}-{p_end})",
        })
    return sections


def extract_glossary(doc):
    """Appendix B: alternating short acronym line / definition line(s).

    The Table of Contents also lists "APPENDIX B: GLOSSARY OF TERMS &
    ABBREVIATIONS" as an entry, so matching on that phrase alone grabs the
    ToC page instead of the real appendix. The intro sentence below only
    appears on the real page - use that as the trigger instead."""
    TRIGGER = "the following definitions, abbreviations and acronyms are used"
    for i in range(doc.page_count):
        text = strip_boilerplate(doc[i].get_text())
        if TRIGGER not in text:
            continue
        # Glossary may span more than one page - collect until next APPENDIX
        j = i
        collected = []
        while j < doc.page_count:
            t = strip_boilerplate(doc[j].get_text())
            if j > i and "APPENDIX" in t:
                break
            collected.append(t)
            j += 1
        block = "\n".join(collected)
        block = block.split("GLOSSARY OF TERMS & ABBREVIATIONS")[1]
        block = block.split("the following definitions, abbreviations and acronyms are used:")[-1]
        lines = [l.strip() for l in block.split("\n") if l.strip()]
        entries = []
        k = 0
        while k < len(lines):
            term = lines[k]
            if re.match(r"^[A-Z0-9/\-]{2,10}$", term):
                defn_lines = []
                k += 1
                while k < len(lines) and not re.match(r"^[A-Z0-9/\-]{2,10}$", lines[k]):
                    defn_lines.append(lines[k])
                    k += 1
                entries.append({"term": term, "definition": " ".join(defn_lines), "source": "TIPS3 Appendix B"})
            else:
                k += 1
        return entries
    return []


def extract_sce_catalog(doc):
    """Section 10: SCE code + title pairs, grouped by the '10.N <Barrier>
    SCEs' sub-heading they fall under."""
    entries = []
    current_barrier = None
    code_re = re.compile(r"^([A-Z]{2}\d{3})$")
    barrier_re = re.compile(r"^10\.\d+\s*$")
    in_section_10 = False
    for i in range(doc.page_count):
        text = strip_boilerplate(doc[i].get_text())
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        j = 0
        while j < len(lines):
            line = lines[j]
            if line == "10." and j + 1 < len(lines) and "SAFETY CRITICAL ELEMENTS" in lines[j + 1]:
                in_section_10 = True
            elif re.match(r"^(11|APPENDIX)", line):
                in_section_10 = False
            if in_section_10 and barrier_re.match(line) and j + 1 < len(lines):
                current_barrier = lines[j + 1]
            if in_section_10 and code_re.match(line) and j + 1 < len(lines):
                entries.append({
                    "sce_group": line,
                    "sce_group_title": lines[j + 1],
                    "barrier_category": current_barrier,
                    "source": f"TIPS3 (page {i + 1})",
                })
            j += 1
    return entries


APPENDIX_D_SYSTEM_PROMPT = """You restructure text from an SCE (Safety Critical Element) manual appendix
into JSON. The input covers one or more SCE Group entries, each with 4 fields whose column alignment was
lost during PDF text extraction: Description, SCE Goal, Typical Equipment Types, System Level / Boundaries.
Each entry also has "SCE Group : <CODE>" and "SCE Group Title : <Name>" markers.

Return ONLY a JSON array, no prose, no markdown fences. Each element:
{
  "sce_group": "...",
  "sce_group_title": "...",
  "description": "...",
  "sce_goal": "...",
  "typical_equipment_types": "...",
  "system_level_boundaries": "..."
}

Rules:
- Copy source text verbatim into the right field - do not invent, summarise, or drop content.
- If a field is genuinely not present for an entry, use an empty string.
- Only include entries that have both an SCE Group code and title.
"""


def extract_json_array(raw_content):
    text = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON array found: {raw_content[:200]!r}")
    return text[start:end + 1]


def extract_appendix_d(doc):
    """Appendix D: find its page range, then feed the raw (boilerplate-
    stripped) text to the LLM in page-sized batches to restructure into
    rows - same rationale as GOPS4's FUNCTIONALITY table."""
    start_page = None
    end_page = doc.page_count
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if "APPENDIX D" in t and "GUIDANCE ON SCE GOALS" in t:
            start_page = i
        elif start_page is not None and re.search(r"APPENDIX [E-Z]", t):
            end_page = i
            break

    if start_page is None:
        print("  Appendix D not found")
        return []

    print(f"  Appendix D spans pages {start_page + 1}-{end_page}")
    all_rows = []
    # batch ~4 pages per LLM call to keep prompts a manageable size
    batch_size = 4
    for b_start in range(start_page, end_page, batch_size):
        b_end = min(b_start + batch_size, end_page)
        raw = "\n".join(strip_boilerplate(doc[p].get_text()) for p in range(b_start, b_end))
        raw = re.sub(r"\n{2,}", "\n", raw).strip()
        if len(raw) < 50:
            continue
        content = chat(
            [
                {"role": "system", "content": APPENDIX_D_SYSTEM_PROMPT},
                {"role": "user", "content": raw},
            ],
            name=f"extract_tips3_appendix_d pages {b_start + 1}-{b_end}",
            metadata={"document": "TIPS3 SCE Manual", "section": "Appendix D", "pages": f"{b_start + 1}-{b_end}"},
            temperature=0,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        try:
            rows = json.loads(extract_json_array(content))
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  batch pages {b_start + 1}-{b_end}: PARSE FAILED: {e}")
            continue
        for r in rows:
            r["source"] = f"TIPS3 Appendix D (pages {b_start + 1}-{b_end})"
        all_rows += rows
        print(f"  batch pages {b_start + 1}-{b_end}: {len(rows)} SCE group entries")
    return all_rows


def main():
    doc = fitz.open(str(TIPS3))
    print(f"TIPS3: {doc.page_count} pages")

    full_text = load_doc_text(doc)
    sections = extract_sections(full_text)
    print(f"\nNumbered sections found: {len(sections)}")
    for s in sections:
        print(f"  {s['section_no']}. {s['heading'][:60]!r} (pages {s['page_start']}-{s['page_end']}, {s['char_count']} chars)")

    glossary = extract_glossary(doc)
    print(f"\nGlossary entries: {len(glossary)}")

    catalog = extract_sce_catalog(doc)
    print(f"SCE catalog entries (section 10): {len(catalog)}")

    print("\nExtracting Appendix D via LLM...")
    appendix_d = extract_appendix_d(doc)
    print(f"Appendix D entries: {len(appendix_d)}")

    doc.close()

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        pd.DataFrame(sections).to_excel(xl, sheet_name="Sections", index=False)
        pd.DataFrame(glossary).to_excel(xl, sheet_name="Glossary", index=False)
        pd.DataFrame(catalog).to_excel(xl, sheet_name="SCE_Catalog", index=False)
        pd.DataFrame(appendix_d).to_excel(xl, sheet_name="SCE_Group_Definitions", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    with llm_run(task="extract_tips3", component="extraction"):
        main()
