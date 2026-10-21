"""
Check 7 (Group B) - Performance standards in MIC vs SSPS/GOPS4.0 (LLM-matched)
--------------------------------------------------------------------------------
Deterministic clause-number matching (MIC Name's leading "4.1" vs SSPS/GOPS4
assurance_task's leading "4.1") was tried first and dropped - too noisy (see
conversation: of MICs flagged PS Req=Y, only 94/192 matched a same-numbered
ground-truth clause, and 11/41 PS Req=N MICs matched anyway - clause numbers
between SAP's MIC catalog and the SSPS/GOPS4 documents are not reliably
synchronised).

This script instead asks the local LLM to semantically match each MIC (by
its actual text, "MIC Name") against the SSPS/GOPS4 assurance-task text for
that SAME SCE Group only (one LLM call per group, 32 groups) - meaning
matching, not clause-number matching. Ground truth text is passed verbatim;
the model is only asked to pick the best-fitting task index or say "no
match", never to invent or summarise task content.

Findings, from the resulting MIC -> task crosswalk. `finding` uses plain,
client-readable labels (not the internal ps_req_unsupported/ps_req_missing
naming used during development) so no glossary lookup is needed to read
the sheet directly:
  - "Incorrectly Marked as Required": MIC flagged PS Req=Y but the LLM
    found no matching SSPS/GOPS4 assurance task for that SCE Group at all -
    the "performance standard required" flag has no apparent basis.
  - "Should Be Marked as Required": MIC flagged PS Req=N but the LLM found
    a HIGH-confidence matching task - this MIC looks like it corresponds to
    a real performance-standard requirement that isn't flagged as one.
  - "Correctly Assigned": everything else - the flag is consistent with
    the evidence.
Both flagged labels are review flags (LLM matching, not a certainty).

One sheet only, not separate Findings/Full_Crosswalk sheets - every one of
the 233 MICs carries the same columns (finding, severity, match_confidence,
matched_source_citation), so a reviewer filters the `finding` column in
Excel to get either view, rather than the data being split across sheets
that show the same thing at different filter levels.

Output: Data exploration/output/D6_MIC_TaskList_PS_Matching.xlsx
  - Summary
  - MIC_Task_Validation    (all 233 MICs; filter `finding` for
                            ps_req_unsupported / ps_req_missing / no_finding)
  - LLM_Failures           (groups the LLM call failed for, if any)

Run:
    python "code/agent/check7_mic_ps_llm_matching.py"
"""

import json
import re
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # code/
from common.llm import chat, llm_run  # noqa: E402 - Langfuse-traced LLM access

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
MIC_REPORT_FILE = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Transactional Data" / "MIC" / "MIC Report 2024_2025.xlsx"
SSPS_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "ssps_requirements.xlsx"
GOPS4_TASKS_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_functionality_tasks.xlsx"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "D6_MIC_TaskList_PS_Matching.xlsx"
OUT_RAW_JSON = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "check7_llm_raw.json"

CODE_RE = re.compile(r"^([A-Z]{2,3}\d{3})")
N_RUNS = 3  # independent matching runs; a finding is reported only if all runs agree

SYSTEM_PROMPT = """You match SAP Measurement/Inspection Criteria (MICs) to the performance-standard \
assurance tasks they most likely implement, for ONE SCE Group at a time.

You will get two lists for a single SCE Group:
  MICS: SAP's actual inspection criteria in use, each with a code and short name.
  TASKS: the approved SSPS/GOPS4.0 assurance tasks defined for this SCE Group, each numbered.

For EACH mic in MICS, decide which task (if any) it is clearly implementing - based on matching \
MEANING, not matching numbers (SAP's own numbering does not line up with the document's numbering). \
Only match when the mic's short name and a task's content clearly describe the same inspection/check. \
If nothing fits well, say no match - do not force a weak match.

Return ONLY a JSON array, no prose, no markdown fences. One element per mic in MICS, in the same order:
{"mic": "<code copied verbatim>", "matched_task_index": <integer from TASKS, or null>, \
"match_confidence": "high" | "medium" | "none"}

"none" confidence must have matched_task_index = null.
"""


def extract_json_array(raw_content):
    text = re.sub(r"<think>.*?</think>", "", raw_content, flags=re.S).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON array found in response: {raw_content[:200]!r}")
    return text[start:end + 1]


def call_llm(sce_group, mics_block, tasks_block, run_no=1, retries=2):
    last_err = None
    user_content = f"SCE Group: {sce_group}\n\nMICS:\n{mics_block}\n\nTASKS:\n{tasks_block}"
    for attempt in range(retries + 1):
        try:
            content = chat(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                name=f"match_mics_to_ps_tasks {sce_group} run {run_no}",
                metadata={"sce_group": sce_group, "run": run_no, "attempt": attempt + 1},
                temperature=0,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                timeout=120,
            )
            json_str = extract_json_array(content)
            return json.loads(json_str), content
        except Exception as e:
            last_err = e
            time.sleep(1.5)
    raise RuntimeError(f"{sce_group}: failed after {retries + 1} attempts: {last_err}")


GOPS4_GROUPS_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_sce_groups.xlsx"
GOPS4_NOTE = ("SCE Group not among the 45 SCE Groups of GOPS4.0 (GOPS4.pdf page 10; Figure 1-1, page 12) - no longer "
              "SCE, so the MIC is not a performance-standard task (PS Req = N)")


def apply_gops4_rule(crosswalk):
    """PCSB (9 Oct 2026): an SCE Group not in the latest GOPS4.0 is no longer SCE. Its MICs therefore carry no
    performance-standard requirement, whatever the GOPS3-era SSPS says: PS Req = N is correct, Y is not."""
    current = set(pd.read_excel(GOPS4_GROUPS_FILE)["sce_group"].dropna())
    out = crosswalk.copy()
    gone = ~out["sce_group"].isin(current)
    out["gops4_rule"] = ""
    out.loc[gone, "gops4_rule"] = GOPS4_NOTE
    out.loc[gone, "finding"] = out.loc[gone, "ps_req"].map(
        {"Y": "Incorrectly Marked as Required"}).fillna("Correctly Assigned")
    out.loc[gone, "severity"] = out.loc[gone, "finding"].map({"Incorrectly Marked as Required": "Medium"})
    return out


def summarise(crosswalk, n_failures):
    consistent = crosswalk["consistent_across_runs"].eq("Yes")
    gone = crosswalk.get("gops4_rule", pd.Series("", index=crosswalk.index)).astype(str).ne("")
    return pd.DataFrame({
        "Metric": [
            "Distinct MICs (2024-2025 MIC Report)", "SCE Groups covered",
            "Independent matching runs", "SCE Group calls that failed (all runs)",
            "MICs with the same finding in every run",
            "MICs whose finding differed between runs (routed to SME review)",
            "MICs of SCE Groups no longer in GOPS4.0 (finding set by the GOPS4.0 rule)",
            "Findings - Incorrectly Marked as Required (PS Req=Y, no matching task found in any run)",
            "Findings - Should Be Marked as Required (PS Req=N, high-confidence task match in every run)",
            "Correctly Assigned (consistent across runs)",
        ],
        "Value": [
            len(crosswalk), crosswalk["sce_group"].nunique(), N_RUNS, n_failures,
            int(consistent.sum()), int((~consistent).sum()), int(gone.sum()),
            int((crosswalk["finding"] == "Incorrectly Marked as Required").sum()),
            int((crosswalk["finding"] == "Should Be Marked as Required").sum()),
            int((crosswalk["finding"] == "Correctly Assigned").sum()),
        ],
    })


def reapply_gops4_rule_only():
    """Re-apply the GOPS4.0 rule to the existing matching output, without new LLM runs."""
    x = pd.read_excel(OUT_XLSX, sheet_name=None)
    crosswalk = apply_gops4_rule(x["MIC_Task_Validation"])
    failures = x.get("LLM_Failures")
    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summarise(crosswalk, 0 if failures is None else len(failures)).to_excel(xl, sheet_name="Summary", index=False)
        crosswalk.to_excel(xl, sheet_name="MIC_Task_Validation", index=False)
        if failures is not None:
            failures.to_excel(xl, sheet_name="LLM_Failures", index=False)
    print(crosswalk["finding"].value_counts())
    print(f"Written to {OUT_XLSX}")


def main():
    # ------------------------------------------------------------------
    # SAP side: distinct MICs per SCE group, with PS Req
    # ------------------------------------------------------------------
    mic = pd.read_excel(MIC_REPORT_FILE, sheet_name="Data", dtype=str)
    mic.columns = [c.strip() for c in mic.columns]
    mic["fl_code"] = mic["SCE Grp - FL"].str.extract(CODE_RE, expand=False)
    mic_u = mic.drop_duplicates("MIC")[["fl_code", "MIC", "MIC Name", "PS Req"]].dropna(subset=["fl_code"])
    print(f"Distinct MICs to match: {len(mic_u)}, across {mic_u['fl_code'].nunique()} SCE Groups")

    # ------------------------------------------------------------------
    # Ground truth: SSPS + GOPS4 assurance tasks, per group
    # ------------------------------------------------------------------
    ssps = pd.read_excel(SSPS_FILE, sheet_name="Functionality_Tasks")
    # Tasks the Bokor SSPS marks N / N/A in its "Applicable or not" column are
    # not requirements at Bokor - they are not offered to the model, so a MIC
    # can't be flagged "should be required" on the strength of one.
    applicability = ssps["applicable_or_not"].fillna("").astype(str).str.upper().str.replace(" ", "")
    n_before = len(ssps)
    ssps = ssps[~applicability.isin(["N", "N/A", "NA"])]
    print(f"SSPS tasks marked not applicable at Bokor (excluded): {n_before - len(ssps)} of {n_before}")
    gops4 = pd.read_excel(GOPS4_TASKS_FILE)
    # keep the real per-row document+page citation ("source", e.g.
    # "SKA_BOKOR_SSPS_ER005.pdf (page 1)" / "GOPS4.pdf (pages 17-20)") -
    # `source_type` is the SSPS/GOPS4 label used for prompt display only
    ssps_t = ssps[["sce_group", "assurance_task", "min_acceptable_criteria", "source"]].rename(
        columns={"min_acceptable_criteria": "criteria", "source": "source_citation"}
    ).assign(source_type="SSPS")
    gops4_t = gops4[["sce_group", "assurance_task", "minimum_acceptable_criteria", "source"]].rename(
        columns={"minimum_acceptable_criteria": "criteria", "source": "source_citation"}
    ).assign(source_type="GOPS4")
    ground_truth = pd.concat([ssps_t, gops4_t], ignore_index=True)
    ground_truth = ground_truth.dropna(subset=["assurance_task"])
    ground_truth = ground_truth[ground_truth["assurance_task"].astype(str).str.strip() != ""]

    groups = sorted(mic_u["fl_code"].unique())

    def run_matching(run_no):
        all_matches = []
        raw_responses = {}
        failures = []
        for i, grp in enumerate(groups):
            grp_mics = mic_u[mic_u["fl_code"] == grp]
            grp_tasks = ground_truth[ground_truth["sce_group"] == grp].reset_index(drop=True)

            if len(grp_tasks) == 0:
                print(f"[run {run_no}] [{i+1}/{len(groups)}] {grp}: no SSPS/GOPS4 tasks defined - all {len(grp_mics)} MICs unmatched")
                for _, r in grp_mics.iterrows():
                    all_matches.append({"sce_group": grp, "mic": r["MIC"], "mic_name": r["MIC Name"],
                                        "ps_req": r["PS Req"], "matched_task_index": None,
                                        "match_confidence": "none", "matched_source": None,
                                        "matched_source_citation": None, "matched_assurance_task": None})
                continue

            mics_block = "\n".join(
                f'- code="{r["MIC"]}", name="{r["MIC Name"]}"' for _, r in grp_mics.iterrows()
            )
            tasks_block = "\n".join(
                f'[{idx}] ({t["source_type"]}) {str(t["assurance_task"])[:300]}'
                for idx, t in grp_tasks.iterrows()
            )

            print(f"[run {run_no}] [{i+1}/{len(groups)}] {grp}: {len(grp_mics)} MICs vs {len(grp_tasks)} tasks...", end=" ")
            try:
                matches, raw_content = call_llm(grp, mics_block, tasks_block, run_no=run_no)
                raw_responses[grp] = raw_content
                by_mic = {m.get("mic"): m for m in matches}
                for _, r in grp_mics.iterrows():
                    m = by_mic.get(r["MIC"], {})
                    idx = m.get("matched_task_index")
                    conf = m.get("match_confidence", "none")
                    task_row = grp_tasks.iloc[idx] if idx is not None and 0 <= idx < len(grp_tasks) else None
                    all_matches.append({
                        "sce_group": grp, "mic": r["MIC"], "mic_name": r["MIC Name"], "ps_req": r["PS Req"],
                        "matched_task_index": idx, "match_confidence": conf,
                        "matched_source": task_row["source_type"] if task_row is not None else None,
                        "matched_source_citation": task_row["source_citation"] if task_row is not None else None,
                        "matched_assurance_task": str(task_row["assurance_task"])[:200] if task_row is not None else None,
                    })
                print(f"-> {sum(1 for m in matches if m.get('matched_task_index') is not None)} matched")
            except Exception as e:
                print(f"FAILED: {e}")
                failures.append({"sce_group": grp, "error": str(e)})
                for _, r in grp_mics.iterrows():
                    all_matches.append({"sce_group": grp, "mic": r["MIC"], "mic_name": r["MIC Name"],
                                        "ps_req": r["PS Req"], "matched_task_index": None,
                                        "match_confidence": "call_failed", "matched_source": None,
                                        "matched_source_citation": None, "matched_assurance_task": None})
        return all_matches, raw_responses, failures

    # Plain, client-readable labels directly in the `finding` column -
    # "ps_req_unsupported"/"ps_req_missing"/"no_finding" needed a glossary
    # lookup to interpret; these don't.
    FINDING_CORRECT = "Correctly Assigned"
    FINDING_UNSUPPORTED = "Incorrectly Marked as Required"
    FINDING_MISSING = "Should Be Marked as Required"

    def classify(row):
        if row["ps_req"] == "Y" and row["match_confidence"] in ("none", "call_failed"):
            return FINDING_UNSUPPORTED
        if row["ps_req"] == "N" and row["match_confidence"] == "high":
            return FINDING_MISSING
        return FINDING_CORRECT

    # Single sheet, not separate Findings/Full_Crosswalk sheets - all 233
    # MICs carry the same columns (finding, severity, confidence, source),
    # so a reviewer filters `finding` in Excel rather than needing two
    # sheets that show the same data at different levels of filtering.
    # The model's answer for the same MIC can differ between runs even at
    # temperature 0. So the matching is run N_RUNS times and a finding is
    # only reported when every run gives the same finding for that MIC;
    # otherwise the MIC is routed to SME review rather than flagged.
    FINDING_UNSTABLE = "Inconsistent across runs - SME review"
    runs, raw_responses, failures = [], {}, []
    for run_no in range(1, N_RUNS + 1):
        matches, raw, fails = run_matching(run_no)
        run_df = pd.DataFrame(matches)
        run_df["finding"] = run_df.apply(classify, axis=1)
        runs.append(run_df)
        raw_responses[f"run_{run_no}"] = raw
        failures += [dict(f, run=run_no) for f in fails]

    crosswalk = runs[0].copy()
    for run_no, run_df in enumerate(runs, start=1):
        crosswalk[f"finding_run_{run_no}"] = run_df["finding"].values
        crosswalk[f"confidence_run_{run_no}"] = run_df["match_confidence"].values
    run_cols = [f"finding_run_{n}" for n in range(1, N_RUNS + 1)]
    consistent = crosswalk[run_cols].nunique(axis=1) == 1
    crosswalk["consistent_across_runs"] = consistent.map({True: "Yes", False: "No"})
    crosswalk["finding"] = crosswalk["finding_run_1"].where(consistent, FINDING_UNSTABLE)
    crosswalk["severity"] = crosswalk["finding"].map({FINDING_UNSUPPORTED: "Medium", FINDING_MISSING: "Medium",
                                                      FINDING_UNSTABLE: "Review"})
    crosswalk = apply_gops4_rule(crosswalk)

    print(f"\nMICs: {len(crosswalk)}; same finding in all {N_RUNS} runs: {consistent.sum()}; "
          f"differing between runs: {(~consistent).sum()}")
    print(crosswalk["finding"].value_counts())

    summary = summarise(crosswalk, len(failures))

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        crosswalk.to_excel(xl, sheet_name="MIC_Task_Validation", index=False)
        if failures:
            pd.DataFrame(failures).to_excel(xl, sheet_name="LLM_Failures", index=False)

    OUT_RAW_JSON.write_text(json.dumps(raw_responses, indent=2), encoding="utf-8")
    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    import sys
    if "--gops4-rule-only" in sys.argv:
        reapply_gops4_rule_only()
    else:
        with llm_run(task="check7_mic_ps_llm_matching", component="agent"):
            main()
