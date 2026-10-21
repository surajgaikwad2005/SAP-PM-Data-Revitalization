from pathlib import Path

import pymupdf4llm


def extract_pdf_text(path: str) -> str:
    return pymupdf4llm.to_markdown(path)


def extract_pdf_page_range(path: str, start_page: int, end_page: int) -> str:
    page_indices = list(range(start_page - 1, end_page))
    return pymupdf4llm.to_markdown(path, pages=page_indices)


def extract_pdf_page_ranges(path: str, page_ranges: list[tuple[int, int]]) -> str:
    sections = [extract_pdf_page_range(path, start, end) for start, end in page_ranges]
    return "\n\n---\n\n".join(sections)


def write_ground_truth_cache(
    pain_point: str, content: str, source_document: str, section_reference: str, cache_dir: str
) -> str:
    out_path = Path(cache_dir) / f"{pain_point}.md"
    header = (
        f"<!-- GENERATED CACHE — do not hand-edit. If this disagrees with "
        f"{source_document}, the source document wins. -->\n\n"
        f"# {pain_point}\n\n"
        f"**Source:** {source_document}\n"
        f"**Section:** {section_reference}\n\n"
    )
    out_path.write_text(header + content, encoding="utf-8")
    return str(out_path)


if __name__ == "__main__":
    base = Path(__file__).resolve().parent.parent
    sources_dir = base / "ground_truth_sources"
    cache_dir = base / "ground_truth_cache"
    cache_dir.mkdir(exist_ok=True)

    entries = [
        ("PP01_TaskList_Naming", "UDMS.pdf", "§9.2, §9.4", [(58, 61)]),
        ("PP02_Work_Centre", "UDMS.pdf", "§9.8, §9.17, §10.4", [(63, 63), (67, 67), (76, 76)]),
        ("PP03_Orphan_TaskList", "UDMS.pdf", "§9.6", [(62, 62)]),
        ("PP04_Duplicate_TaskList", "UDMS.pdf", "§9.6", [(62, 62)]),
        ("PP05_Manhours", "UDMS.pdf", "§9.20-21", [(69, 69)]),
        ("PP06_MPlan_OnHold", "UDMS.pdf", "§9.12, §11.1-11.5", [(64, 64), (81, 83)]),
        ("PP07_Hanging_MI", "UDMS.pdf", "§10", [(75, 75)]),
    ]
    for pain_point, source_filename, section, page_ranges in entries:
        content = extract_pdf_page_ranges(str(sources_dir / source_filename), page_ranges)
        write_ground_truth_cache(pain_point, content, source_filename, section, str(cache_dir))
        ranges_str = ", ".join(f"{s}-{e}" for s, e in page_ranges)
        print(f"wrote {pain_point} from {source_filename} pages {ranges_str}")
