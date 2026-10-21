"""Clean the Bokor worklist against the SAP equipment master.

For each sampled worklist row:
  1. Try a deterministic exact match: construct {SubLoc1-prefix}{clean(EquipmentNo)}
     and look for that normalized string in the master's TechnicalIdentNo.
  2. If that fails, filter the master to this row's SubLoc1 prefix and feed candidates
     to CleaningAgent in batches of BATCH_SIZE. Batches run in parallel (bounded by
     MAX_CONCURRENT_LLM to stay under the LLM rate limit).

Writes:
  Cleaned_Worklist_Bokor.xlsx  - per-field Suggested / Confidence / Evidence columns
  SubLoc1_Mismatches.xlsx      - punch-list where master disagreed with the worklist's SubLoc1
"""

import re
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

from agents import PREFIX_TO_SUBLOC1, cleaning_agent
from extraction import fetch_equipment_master, load_worklist_bokor

# ----- Edit these -----
SAMPLE_SIZE = None
REFRESH_KG = True       # True -> re-pull from Postgres; False -> use cached xlsx
SEED = 42
BATCH_SIZE = 100         # candidates per CleaningAgent call
MAX_CONCURRENT_LLM = 5   # parallel batch calls per row (safe for ~60 RPM rate limits)
# ----------------------

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[2]
PROCESSED_DIR = PROJECT_ROOT / "Code Folder" / "SD-TA Agent" / "Processed Data"

# OUTPUT_XLSX = PROCESSED_DIR / "Cleanly_Mapped_Worklist_Bokor_2024.xlsx"
# MISMATCH_XLSX = PROCESSED_DIR / "Final_SubLoc1_Mismatches_2024.xlsx"

OUTPUT_XLSX = PROCESSED_DIR / "Cleanly_Mapped_Worklist_Bokor_2026.xlsx"
MISMATCH_XLSX = PROCESSED_DIR / "Final_SubLoc1_Mismatches_2026.xlsx"



SUBLOC1_TO_PREFIX = {
    "BOCPP":  "BOCP",
    "BOK-":   "BOKA",
    "BOP-":   "BOPA",
    "BOV-":   "BOVA",
    "BODP-A": "BODA",
    "BODP-B": "BODB",
    "BODP-C": "BODC",
    "BODP-D": "BODD",
    "BODP-E": "BODE",
    "BODP-F": "BODF",
}


def normalize(s):
    return re.sub(r"[^A-Z0-9]", "", str(s or "").upper())


def tid_prefix_and_tail(tid):
    s = str(tid or "")
    if "-" not in s:
        return None, ""
    pfx, _, tail = s.partition("-")
    return pfx.upper(), normalize(tail)


def subloc1_implies_prefix(subloc1):
    s = str(subloc1 or "").strip().upper()
    for alias, pfx in SUBLOC1_TO_PREFIX.items():
        if s.startswith(alias.upper()):
            return pfx
    return None


def extract_tokens(equipmentno):
    """Pull candidate tag tokens for the deterministic step. Only splits on multi-tag
    separators (/ & ; ,) - anything messier is the LLM's job."""
    raw = re.sub(r"\([^)]*\)", " ", str(equipmentno or ""))
    sub_tags = re.split(r"[/&;,]", raw)
    tokens = [normalize(t) for t in sub_tags if t.strip()]
    return sorted({t for t in tokens if len(t) >= 3})


def resolve_deterministic(row, master):
    """Construct PREFIX+tag and look for that exact normalized TID. Returns None if ambiguous."""
    tokens = extract_tokens(row.get("EquipmentNo"))
    if not tokens:
        return None

    subloc_pfx = subloc1_implies_prefix(row.get("SubLoc1"))

    if subloc_pfx:
        targets = {subloc_pfx + t for t in tokens}
        hits = master[master["_TIDNorm"].isin(targets)]
        if len(hits) == 1:
            return build_deterministic_result(row, hits.iloc[0], "deterministic_prefix_match")
        if len(hits) > 1:
            return build_deterministic_result(row, hits.iloc[0], "deterministic_prefix_match_first")

    # Fallback: tail-only match (safety net for wrong SubLoc1).
    tail_hits = master[master["_TIDTail"].isin(tokens)]
    if len(tail_hits) == 1:
        return build_deterministic_result(row, tail_hits.iloc[0], "deterministic_tail_only")

    return None


def build_deterministic_result(row, master_row, method):
    orig_subloc1 = str(row.get("SubLoc1") or "").strip()
    master_pfx = master_row["_TIDPrefix"]
    subloc_pfx = subloc1_implies_prefix(orig_subloc1)

    result = {
        "Suggested TechnicalId":   master_row["TechnicalIdentNo"],
        "Suggested EquipmentNo":   master_row["EquipmentNo"],
        "EquipmentNo Confidence":  "High",
        "EquipmentNo Evidence":    f"Tail '{master_row['_TIDTail']}' matched TID '{master_row['TechnicalIdentNo']}' ({method}).",
        "MatchMethod":             method,
        "NeedsReview":             False,
    }
    if subloc_pfx and master_pfx and master_pfx != subloc_pfx:
        suggested = PREFIX_TO_SUBLOC1.get(master_pfx, orig_subloc1)
        result["Suggested SubLoc1"] = suggested
        result["SubLoc1 Confidence"] = "Medium"
        result["SubLoc1 Evidence"] = (
            f"Original SubLoc1 '{orig_subloc1}' implies '{subloc_pfx}', but master has this tag under "
            f"'{master_pfx}' (FL: {master_row['FunctionalLocation']}). Recommend '{suggested}' - verify."
        )
        result["NeedsReview"] = True
        result["_Mismatch"] = "deterministic"
        result["_OrigSubLoc1"] = orig_subloc1
    else:
        result["Suggested SubLoc1"] = orig_subloc1
        result["SubLoc1 Confidence"] = "High"
        result["SubLoc1 Evidence"] = "Consistent with master prefix."
    return result


def run_llm_path(row, master):
    """SubLoc1 -> prefix filter -> parallel batched CleaningAgent calls."""
    subloc_pfx = subloc1_implies_prefix(row.get("SubLoc1"))
    if subloc_pfx:
        pool = master[master["_TIDPrefix"] == subloc_pfx]
        print(f"  Pool: {len(pool)} rows under prefix '{subloc_pfx}'")
    else:
        pool = master
        print(f"  SubLoc1 unmappable - using full master: {len(pool)} rows")

    if pool.empty:
        return build_no_match_result(row, f"No candidates under SubLoc1 prefix '{subloc_pfx}'.")

    # Single-batch case
    if len(pool) <= BATCH_SIZE:
        return finalize_llm_result(row, cleaning_agent(row, pool), pool, method="llm")

    # Multi-batch: run in parallel, collect picks, then rank by confidence
    batches = [pool.iloc[s:s + BATCH_SIZE] for s in range(0, len(pool), BATCH_SIZE)]
    print(f"  Running {len(batches)} CleaningAgent batches in parallel (max {MAX_CONCURRENT_LLM} at a time)")

    picks = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_LLM) as ex:
        future_to_idx = {ex.submit(cleaning_agent, row, b): i for i, b in enumerate(batches)}
        for fut in as_completed(future_to_idx):
            i = future_to_idx[fut]
            r = fut.result()
            picked = r.get("suggested_equipment_no")
            print(f"    batch {i + 1}/{len(batches)} done -> {picked or 'no pick'}")
            if picked:
                picks.append(r)

    if not picks:
        return build_no_match_result(row, f"None of the {len(batches)} batches returned a convincing pick.")

    rank = {"High": 3, "Medium": 2, "Low": 1}
    picks.sort(key=lambda x: rank.get(x.get("equipment_no_confidence"), 0), reverse=True)
    return finalize_llm_result(row, picks[0], pool, method="llm_batched")


def finalize_llm_result(row, r, pool, method):
    """Turn an LLM response dict into our standard result dict."""
    orig_subloc1 = str(row.get("SubLoc1") or "").strip()
    suggested_subloc1 = r.get("suggested_subloc1") or orig_subloc1

    subloc_conf = r.get("subloc1_confidence", "Low")
    if suggested_subloc1 != orig_subloc1 and subloc_conf == "High":
        subloc_conf = "Medium"  # cap when overriding a human-entered value

    eq_conf = r.get("equipment_no_confidence", "Low")
    picked_eqp = r.get("suggested_equipment_no")

    # Look up the picked candidate's TechnicalIdentNo
    suggested_tid = None
    if picked_eqp:
        cand = pool[pool["EquipmentNo"].astype(str) == str(picked_eqp)]
        if not cand.empty:
            suggested_tid = cand.iloc[0]["TechnicalIdentNo"]

    # NeedsReview: honour LLM's explicit flag; otherwise default to confidence-based
    llm_needs_review = r.get("needs_review")
    if llm_needs_review is None:
        llm_needs_review = (not picked_eqp) or eq_conf == "Low"

    result = {
        "Suggested TechnicalId":   suggested_tid,
        "Suggested EquipmentNo":   picked_eqp,
        "EquipmentNo Confidence":  eq_conf,
        "EquipmentNo Evidence":    r.get("equipment_no_evidence", ""),
        "Suggested SubLoc1":       suggested_subloc1,
        "SubLoc1 Confidence":      subloc_conf,
        "SubLoc1 Evidence":        r.get("subloc1_evidence", ""),
        "MatchMethod":             method,
        "NeedsReview":             bool(llm_needs_review),
    }
    if suggested_subloc1 != orig_subloc1 and picked_eqp:
        result["_Mismatch"] = "llm"
        result["_OrigSubLoc1"] = orig_subloc1
    return result


def build_no_match_result(row, reason):
    return {
        "Suggested TechnicalId":   None,
        "Suggested EquipmentNo":   None,
        "EquipmentNo Confidence":  "Low",
        "EquipmentNo Evidence":    reason,
        "Suggested SubLoc1":       str(row.get("SubLoc1") or "").strip(),
        "SubLoc1 Confidence":      "Low",
        "SubLoc1 Evidence":        "No mapping.",
        "MatchMethod":             "no_match",
        "NeedsReview":             True,
        "_Mismatch":               "unmapped",
    }


# ====================== MAIN ======================

master = fetch_equipment_master(refresh=REFRESH_KG)
parts = master["TechnicalIdentNo"].fillna("").astype(str).map(tid_prefix_and_tail)
master["_TIDPrefix"] = parts.map(lambda t: t[0])
master["_TIDTail"]   = parts.map(lambda t: t[1])
master["_TIDNorm"]   = master["TechnicalIdentNo"].fillna("").astype(str).map(normalize)
print(f"Master ready: {len(master)} rows.")

worklist = load_worklist_bokor(sample=SAMPLE_SIZE, seed=SEED)

results = []
t0 = time.time()
for idx, row in worklist.iterrows():
    print(f"\n[{idx + 1}/{len(worklist)}] WorklistID={row.get('WorklistID','')} | "
          f"EquipmentNo={row.get('EquipmentNo','')} | SubLoc1={row.get('SubLoc1','')}")

    pick = resolve_deterministic(row, master)
    if pick:
        print(f"  Deterministic winner: {pick['Suggested EquipmentNo']}  "
              f"(TID: {pick['Suggested TechnicalId']})")
    else:
        pick = run_llm_path(row, master)

    results.append({
        "ID":                       row.get("ID"),
        "WorklistID":               row.get("WorklistID"),
        "EquipmentNo":              row.get("EquipmentNo"),
        "Suggested TechnicalId":    pick.get("Suggested TechnicalId"),
        "Suggested EquipmentNo":    pick.get("Suggested EquipmentNo"),
        "EquipmentNo Confidence":   pick.get("EquipmentNo Confidence"),
        "EquipmentNo Evidence":     pick.get("EquipmentNo Evidence"),
        "Loc":                      row.get("Loc"),
        "SubLoc1":                  row.get("SubLoc1"),
        "Suggested SubLoc1":        pick.get("Suggested SubLoc1"),
        "SubLoc1 Confidence":       pick.get("SubLoc1 Confidence"),
        "SubLoc1 Evidence":         pick.get("SubLoc1 Evidence"),
        "EqptType":                 row.get("EqptType"),
        "Discipline":               row.get("Discipline"),
        "Job Description":          row.get("Job Description"),
        "MatchMethod":              pick.get("MatchMethod"),
        "NeedsReview":              pick.get("NeedsReview", False),
        "_Mismatch":                pick.get("_Mismatch"),
        "_OrigSubLoc1":             pick.get("_OrigSubLoc1"),
    })

out_df = pd.DataFrame(results)

# Systematic SubLoc1 mismatch detection
pair_counts = Counter()
for _, r in out_df[out_df["_Mismatch"].isin(["deterministic", "llm"])].iterrows():
    pair_counts[(r["_OrigSubLoc1"], r["Suggested SubLoc1"])] += 1
systematic = {p: c for p, c in pair_counts.items() if c >= 5}
for (orig, sug), c in systematic.items():
    print(f"\nWARNING: Systematic SubLoc1 issue -- {c} rows with SubLoc1='{orig}' resolved under '{sug}'.")

# Main output (drop internal cols)
main_df = out_df.drop(columns=["_Mismatch", "_OrigSubLoc1"])
main_df.to_excel(OUTPUT_XLSX, index=False)
print(f"\nWrote {OUTPUT_XLSX.name} ({len(main_df)} rows)")

# Mismatch report
det_df = out_df[out_df["_Mismatch"] == "deterministic"].copy()
llm_df = out_df[out_df["_Mismatch"] == "llm"].copy()
unm_df = out_df[out_df["_Mismatch"] == "unmapped"].copy()
if not (det_df.empty and llm_df.empty and unm_df.empty):
    with pd.ExcelWriter(MISMATCH_XLSX, engine="openpyxl") as w:
        if not det_df.empty: det_df.to_excel(w, sheet_name="deterministic_mismatches", index=False)
        if not llm_df.empty: llm_df.to_excel(w, sheet_name="llm_mismatches", index=False)
        if not unm_df.empty: unm_df.to_excel(w, sheet_name="unmapped", index=False)
    print(f"Wrote {MISMATCH_XLSX.name}")

print("\n=== End-of-run ===")
print(f"Total rows        : {len(out_df)}")
print(out_df["MatchMethod"].value_counts())
print(f"NeedsReview       : {int(out_df['NeedsReview'].sum())}")
print(f"SubLoc1 mismatches: {len(det_df) + len(llm_df)}")
print(f"Elapsed           : {time.time() - t0:.0f}s")
