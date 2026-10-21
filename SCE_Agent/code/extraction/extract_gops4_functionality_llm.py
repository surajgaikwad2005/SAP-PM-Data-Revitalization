"""
GOPS4 FUNCTIONALITY table extraction via LLM - full run (all 45 SCE Groups)
------------------------------------------------------------------------------
Follows the pilot in test_llm_gops4_functionality.py, which validated this on
2 SCE Groups (PC003, SI002). Same method, all groups:

The FUNCTIONALITY block (raw text, produced by extract_gops4_sce_groups.py)
loses its table-column structure during plain-text PDF extraction - header
labels then repeating groups of values, with variable-length notes/bullets
embedded. The LLM's only job is to re-impose column structure on text that
is already 100% present (temperature 0, explicit verbatim-copy instruction)
- it never introduces facts from outside the block for that SCE Group.

Server note: this endpoint does not separate the model's reasoning trace
from its answer - a Qwen3-style <think>...</think> block lands directly in
`content`. Fixed by passing enable_thinking=False (chat_template_kwargs)
plus a defensive parser that strips any <think> block regardless.

Input:
  Data exploration/output/gops4_sce_groups.xlsx (SCE_Groups sheet,
  `functionality_raw` column) - produced by extract_gops4_sce_groups.py

Output:
  Data exploration/output/gops4_functionality_tasks.xlsx

Run:
    python "code/extraction/extract_gops4_functionality_llm.py"
"""

import json
import re
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # code/
from common.llm import chat, llm_run  # noqa: E402 - Langfuse-traced LLM access

IN_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_sce_groups.xlsx"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_functionality_tasks.xlsx"
OUT_RAW_JSON = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_functionality_llm_raw.json"

SYSTEM_PROMPT = """You restructure GOPS (Generic Operation Performance Standard) text into JSON.
The input is the FUNCTIONALITY section of one SCE Group's performance standard, extracted from a
PDF table whose column borders were lost during text extraction - the values are still all present,
just run together in reading order: a 6-column header (Functional Criteria, Assurance Task,
Responsible Party, Minimum Acceptable Criteria, Frequency, Measurable Unit), then repeating groups
of those same 6 values, one group per assurance task.

Return ONLY a JSON array, no prose, no markdown fences. Each element:
{
  "functional_criteria": "...",
  "assurance_task": "...",
  "responsible_party": "...",
  "minimum_acceptable_criteria": "...",
  "frequency": "...",
  "measurable_unit": "..."
}

Rules:
- Do not invent, summarise, or drop any words - copy the source text verbatim into the right field.
- Multiple assurance tasks can share one functional_criteria (e.g. "1.1", "1.2", "1.3" under "1.");
  repeat the functional_criteria text for each in that case.
- If a field is genuinely absent for a task, use an empty string, never invent a value.
- If the block is empty or has no real content, return [].
"""


def extract_json_array(raw_content):
    text = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON array found in response: {raw_content[:200]!r}")
    return text[start:end + 1]


def call_llm(sce_group, functionality_raw, retries=2):
    last_err = None
    for attempt in range(retries + 1):
        try:
            content = chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"SCE Group: {sce_group}\n\nFUNCTIONALITY block:\n{functionality_raw}"},
                ],
                name=f"extract_gops4_functionality {sce_group}",
                metadata={"sce_group": sce_group, "document": "GOPS4.pdf", "attempt": attempt + 1},
                temperature=0,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            json_str = extract_json_array(content)
            return json.loads(json_str), content
        except Exception as e:
            last_err = e
            time.sleep(1.5)
    raise RuntimeError(f"{sce_group}: failed after {retries + 1} attempts: {last_err}")


def main():
    df = pd.read_excel(IN_XLSX, sheet_name="SCE_Groups")
    print(f"SCE Groups to process: {len(df)}")

    all_rows = []
    raw_responses = {}
    failures = []

    for i, row in df.iterrows():
        grp, name, raw = row["sce_group"], row["sce_group_name"], row["functionality_raw"]
        if not isinstance(raw, str) or not raw.strip():
            print(f"[{i+1}/{len(df)}] {grp}: empty block, skipping")
            continue
        print(f"[{i+1}/{len(df)}] {grp} - {name} ({len(raw)} chars)...", end=" ")
        try:
            tasks, raw_content = call_llm(grp, raw)
            raw_responses[grp] = raw_content
            for t in tasks:
                t["sce_group"] = grp
                t["sce_group_name"] = name
                t["source"] = row["source"]
                all_rows.append(t)
            print(f"-> {len(tasks)} tasks")
        except Exception as e:
            print(f"FAILED: {e}")
            failures.append({"sce_group": grp, "error": str(e)})

    cols = ["sce_group", "sce_group_name", "functional_criteria", "assurance_task",
            "responsible_party", "minimum_acceptable_criteria", "frequency",
            "measurable_unit", "source"]
    tasks_df = pd.DataFrame(all_rows).reindex(columns=cols)
    failures_df = pd.DataFrame(failures)

    print(f"\nTotal task rows extracted: {len(tasks_df)}")
    print(f"Groups failed: {len(failures_df)}")
    if len(failures_df):
        print(failures_df.to_string(index=False))

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        tasks_df.to_excel(xl, sheet_name="Functionality_Tasks", index=False)
        if len(failures_df):
            failures_df.to_excel(xl, sheet_name="Failures", index=False)

    OUT_RAW_JSON.write_text(json.dumps(raw_responses, indent=2), encoding="utf-8")
    print(f"\nWritten to {OUT_XLSX}")
    print(f"Raw LLM responses saved to {OUT_RAW_JSON} (for audit)")


if __name__ == "__main__":
    with llm_run(task="extract_gops4_functionality_llm", component="extraction"):
        main()
