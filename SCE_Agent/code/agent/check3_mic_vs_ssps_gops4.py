"""
Check 3 (Group B) - MIC vs SSPS & GOPS4.0
------------------------------------------------------------------------
Ground truth: SSPS Functionality_Tasks (391 assurance tasks, 52 SCE
groups) + GOPS4 Functionality_Tasks (107 tasks, 45 groups) - already
extracted. SAP side: MIC Report 2024_2025.xlsx (22,761 transactional
inspection records, Bokor M014) + QS28_M014.xlsx (5,464-row MIC master,
used only to confirm every MIC code used is a real, defined MIC).

Two dimensions kept - both checked against an actual approved document,
not an inferred/statistical pattern:
  1. sce_grp_mic_fl_mismatch - the MIC record's own SCE Grp - MIC code
     disagrees with its FL's SCE Grp - FL code (compared by leading
     CODE only, same lesson as Check 1 - the two fields hold slightly
     different description text for the same code in most rows, which
     is not a defect). Resolved using the approved discipline sign-off
     register (the same ground truth Check 1 uses, the actual external
     standard) - for every one of the 13 resolvable mismatch pairs, the
     register confirms the FL's OWN SCE Group tag, never the MIC's - the
     FL is registered correctly, and the MIC assigned to it is the side
     that's wrong.
  2. sce_group_missing_mic_coverage - an SCE Group with an SSPS/GOPS4
     assurance task requiring a clearly-parseable interval of <=24
     months has ZERO MIC records anywhere in the 2-year report window.
     Deliberately NOT flagging every group with zero MIC coverage - the
     `frequency` field is messy free text (RBI-based, condition-based,
     multi-year for structural/civil tasks); only groups with an
     unambiguous short interval are flagged, and groups already known
     to be legacy/retired per the latest GOPS4 (see
     check_gops4_currency.py) are excluded, since SAP doesn't track
     MICs against a code it no longer recognises.

Two dimensions were built, then deliberately REMOVED after review:
  - FL-level "missing core MIC" (peer-coverage based): inferred "this FL
    should have the same MICs as >=75% of its peers in the same SCE
    Group" from the DATA's own statistical pattern, not from anything
    actually written in SSPS/GOPS4/TIPS3. There is no documented rule
    that every FL in a group must carry an identical MIC set - different
    FLs can have genuinely different applicable tasks depending on their
    physical configuration. A statistical assumption is not a substitute
    for a standards-based check, so this was removed rather than kept as
    an unreliable proxy.
  - Performance-criteria compliance (MIC Report `Result` vs QS28
    Lower/Upper SpecLimit): circular, not independent - QS28 is the same
    system of record the MIC Report's own inspection-lot results are
    captured against, so "0 violations" doesn't demonstrate compliance,
    it just confirms SAP is internally self-consistent with itself.
    Removed as not a meaningful check.
  - (A third dimension, a rejected-inspection flag off UD/UDVal, was
    ruled out earlier and never built - every one of the 22,761 rows has
    UD="A1"/UDVal="A", so this extract cannot surface rejections at all;
    see Check 8 discussion, open question for the client.)

Output: Data exploration/output/D3_MIC_vs_SSPS_GOPS4.xlsx
  - Summary
  - SCE_Group_MIC_Mismatch     (36 rows, FL vs MIC code disagreement,
                                 resolved against the approved register)
  - Missing_MIC_Coverage       (SCE Groups, with the supporting <=24M
                                 task text that justifies the flag)

Run:
    python "code/agent/check3_mic_vs_ssps_gops4.py"
"""

import re
import sqlite3
import warnings
from pathlib import Path

import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
TRANS = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Transactional Data"
MIC_REPORT_FILE = TRANS / "MIC" / "MIC Report 2024_2025.xlsx"
QS28_FILE = TRANS / "MIC" / "QS28_M014.xlsx"
SAP_FL_FILE = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Asset Master" / "BOKOR_FL LIsting_SCE Group_Aug26.xlsx"
MPLAN_FILE = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Planning Data" / "Mplan_M014_15Jan26.XLSX"
SSPS_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "ssps_requirements.xlsx"
GOPS4_TASKS_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_functionality_tasks.xlsx"
GOPS4_GROUPS_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_sce_groups.xlsx"
REGISTER_DB = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "sce_register.db"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "D3_MIC_vs_SSPS_GOPS4.xlsx"

CODE_RE = re.compile(r"^([A-Z]{2,3}\d{3})")
ACTION_CODE_RE = re.compile(r"([A-Z]{2,3}\d{3})\s*$")


def norm_fl(s):
    if pd.isna(s):
        return None
    return re.sub(r"\s+", "", str(s)).upper().strip()


def normalize_action(action):
    """Same normalisation used by Check 1 and every other check - one
    register row's free-text action -> (category, recommended_sce_group)."""
    a = str(action).strip()
    al = a.lower()
    if "non-sce" in al or "non sce" in al:
        return "non_sce", None
    if "inactive" in al:
        return "inactive", None
    if "delete" in al or "deleted" in al:
        return "delete", None
    m = ACTION_CODE_RE.search(a)
    if m:
        return "sce", m.group(1)
    return "unclassified", None


def parse_months(freq):
    """Leading-number frequency text -> months, or None if unparseable/
    conditional (RBI-based, condition-based, manufacturer-dependent,
    multi-part). Deliberately conservative - only a clean leading
    number (SSPS, e.g. "12") or number+M (GOPS4, e.g. "12M") is parsed;
    everything else is treated as unknown, not defaulted to a value."""
    if pd.isna(freq):
        return None
    s = str(freq).strip()
    # Bokor is an offshore facility: where a standard gives separate onshore
    # and offshore intervals (e.g. "24M (Onshore) / 48M (Offshore)"), the
    # offshore one is the requirement that applies.
    offshore = re.search(r"(\d+)\s*M?\s*\(\s*Offshore\s*\)", s, re.I)
    if offshore:
        return int(offshore.group(1))
    m = re.match(r"^(\d+)\s*M?\b", s, re.I)
    if m:
        return int(m.group(1))
    if re.match(r"^(Weekly|Monthly|Daily)\b", s, re.I):
        return 1
    return None


def main():
    # ------------------------------------------------------------------
    # SAP side: MIC Report + QS28 master (used only to sanity-check every
    # MIC code used is a real, defined MIC - not for performance-limit
    # comparison, which was tried and dropped as circular)
    # ------------------------------------------------------------------
    mic = pd.read_excel(MIC_REPORT_FILE, sheet_name="Data", dtype=str)
    mic.columns = [c.strip() for c in mic.columns]
    mic["fl_code"] = mic["SCE Grp - FL"].str.extract(CODE_RE, expand=False)
    mic["mic_code"] = mic["SCE Grp - MIC"].str.extract(CODE_RE, expand=False)
    mic["fl"] = mic["Functional Location"].map(norm_fl)
    print(f"MIC Report: {len(mic):,} rows, {mic['MIC'].nunique()} distinct MIC codes, "
          f"{mic['fl_code'].nunique()} distinct SCE groups in use")

    qs28 = pd.read_excel(QS28_FILE, sheet_name="Data", dtype=str)
    qs28.columns = [c.strip() for c in qs28.columns]
    unmatched = set(mic["MIC"].dropna()) - set(qs28["Master Insp. Charac."].dropna())
    print(f"MIC codes in report not found in QS28 master (should be 0): {len(unmatched)}")

    # ------------------------------------------------------------------
    # Dimension 1: SCE Grp - MIC vs SCE Grp - FL, code-level only,
    # resolved against the approved discipline sign-off register
    # ------------------------------------------------------------------
    con = sqlite3.connect(REGISTER_DB)
    reg = pd.read_sql("select * from sce_register", con)
    con.close()
    reg["fl"] = reg["functional_location"].map(norm_fl)
    reg[["gt_category", "gt_sce_group"]] = reg["action"].apply(lambda a: pd.Series(normalize_action(a)))
    reg["source"] = reg["source_file"].astype(str) + " (page " + reg["printed_page"].astype("Int64").astype(str) + ")"
    reg_dup_fls = reg["fl"].value_counts()
    reg_dup_fls = reg_dup_fls[reg_dup_fls > 1].index
    reg_unique = reg[~reg["fl"].isin(reg_dup_fls)].drop_duplicates("fl")
    gt_sce_group_by_fl = reg_unique.set_index("fl")["gt_sce_group"]
    gt_source_by_fl = reg_unique.set_index("fl")["source"]

    comparable = mic[(mic["fl_code"].notna()) & (mic["mic_code"].notna())].copy()
    comparable_dedup = comparable.drop_duplicates(
        subset=["Functional Location", "EQ at WO Hdr", "SCE Grp - FL", "SCE Grp - MIC", "MIC", "MIC Name",
                "Order", "Created on"]
    )
    n_comparable = len(comparable_dedup)
    # SCE Groups of the latest GOPS4 (Mar 2026): a group not among them is no
    # longer classified as SCE (PCSB, 9 Oct 2026). A MIC record whose FL or
    # MIC group is such a group is an SCE assurance record for something that
    # is no longer an SCE - reported separately, not counted as consistent.
    current_codes = set(pd.read_excel(GOPS4_GROUPS_FILE)["sce_group"].dropna())
    declassified = ~(comparable_dedup["fl_code"].isin(current_codes) & comparable_dedup["mic_code"].isin(current_codes))
    n_correct = ((comparable_dedup["fl_code"] == comparable_dedup["mic_code"]) & ~declassified).sum()
    decl = comparable_dedup[declassified].copy()
    decl["finding"] = "MIC recorded for an SCE Group no longer in GOPS4.0 - no longer SCE"
    decl["recommendation"] = ("The SCE Group is not among the 45 SCE Groups of GOPS4.0 (GOPS4.pdf page 10 and "
                              "Figure 1-1, page 12), so it is no longer SCE. Remove this MIC from the SCE assurance "
                              "task list; any non-SCE maintenance stays in normal PM (GOPS4.0 page 4, Revision 4.0).")
    decl_out = decl[["Functional Location", "EQ at WO Hdr", "SCE Grp - FL", "SCE Grp - MIC", "MIC", "MIC Name",
                     "PS Req", "Inspection Lot", "Order", "Created on", "finding", "recommendation"]]
    print(f"MIC records of SCE Groups no longer in GOPS4.0: {len(decl_out):,} "
          f"({decl_out['MIC'].nunique()} MICs, {decl_out['Functional Location'].nunique()} FLs)")
    print(f"\nSCE Grp (FL) vs SCE Grp (MIC) - correctly matching: {n_correct:,} / {n_comparable:,}")

    mism = comparable[(comparable["fl_code"] != comparable["mic_code"])
                      & comparable["fl_code"].isin(current_codes) & comparable["mic_code"].isin(current_codes)].copy()
    mism["approved_register_sce_group"] = mism["fl"].map(gt_sce_group_by_fl)
    mism["source"] = mism["fl"].map(gt_source_by_fl)

    def resolve_mismatch(row):
        gt_grp = row["approved_register_sce_group"]
        if pd.isna(gt_grp):
            return ("insufficient_evidence",
                    "This FL has no entry in the approved register (or has a duplicate/contradicting entry) - "
                    "cannot confirm either side.")
        if gt_grp == row["fl_code"] and gt_grp != row["mic_code"]:
            return ("likely_mic_assignment_wrong",
                    f"The approved register confirms this FL's SCE Group is {gt_grp}, matching its own tag - "
                    f"the MIC {row['MIC']} ({row['mic_code']}) does not belong on this FL. Recommend reviewing "
                    f"why this MIC/task list was assigned here and replacing it with the correct {gt_grp} MIC.")
        if gt_grp == row["mic_code"] and gt_grp != row["fl_code"]:
            return ("likely_fl_tag_wrong",
                    f"The approved register confirms SCE Group {gt_grp} for this FL, matching the MIC's tag, "
                    f"not the FL's own SAP tag ({row['fl_code']}). Recommend correcting this FL's SCE Group to "
                    f"{gt_grp}.")
        return "inconclusive", "The approved register does not clearly back either side - needs manual review."

    mism[["resolution", "recommendation"]] = mism.apply(lambda r: pd.Series(resolve_mismatch(r)), axis=1)

    mism_out = mism[["Functional Location", "EQ at WO Hdr", "SCE Grp - FL", "SCE Grp - MIC", "MIC", "MIC Name",
                     "approved_register_sce_group", "source", "resolution", "recommendation",
                     "Order", "Created on"]].drop_duplicates()
    print(f"\nDimension 1 - SCE Grp (FL) vs SCE Grp (MIC) code mismatch: {len(mism_out):,} rows")
    print(mism_out["resolution"].value_counts())

    # ------------------------------------------------------------------
    # Pinpoint the affected Maintenance Plan(s) at each mismatched FL, so
    # these can be investigated directly in SAP alongside the Work Order
    # (the "Order" column above). The MIC Report has no Maintenance Plan
    # field itself, so this is a separate join against the Bokor Mplan
    # export by Functional Location. Where a candidate plan's own code or
    # item description is literally coded with the CORRECT SCE Group
    # (per the approved register), it's called out as the likely-correct
    # plan - a deterministic text match, not inferred; every other plan
    # at that FL is still listed for context, nothing hidden.
    # ------------------------------------------------------------------
    mplan = pd.read_excel(MPLAN_FILE, sheet_name="MPlan", dtype=str)
    mplan = mplan[mplan["Location"] == "BOKOR"].copy()
    mplan["fl"] = mplan["Functional Location"].map(norm_fl)
    mplan_by_fl = mplan.groupby("fl")

    def maintenance_plan_lookup(row):
        fl = norm_fl(row["Functional Location"])
        if fl not in mplan_by_fl.groups:
            return "No maintenance plan found for this FL in the Bokor Mplan export.", None, None
        cand = mplan_by_fl.get_group(fl)
        grp = row["approved_register_sce_group"]
        all_plans = sorted(cand["Maintenance Plan"].dropna().unique())
        if pd.isna(grp):
            return None, None, "; ".join(all_plans) if all_plans else None
        hits = cand[cand["Maintenance item description"].str.contains(str(grp), na=False)
                     | cand["Maintenance Plan"].str.contains(str(grp), na=False)]
        likely = sorted(hits["Maintenance Plan"].dropna().unique())
        others = sorted(set(all_plans) - set(likely))
        if likely:
            return None, "; ".join(likely), "; ".join(others) if others else None
        return (f"{len(all_plans)} maintenance plan(s) exist at this FL, but none are coded to {grp} - "
                f"needs manual review.", None, "; ".join(all_plans) if all_plans else None)

    mp_res = mism_out.apply(maintenance_plan_lookup, axis=1)
    (mism_out["maintenance_plan_note"], mism_out["likely_correct_maintenance_plan"],
     mism_out["other_maintenance_plans_at_fl"]) = zip(*mp_res)
    n_pinpointed = mism_out["likely_correct_maintenance_plan"].notna().sum()
    print(f"Likely-correct Maintenance Plan pinpointed for {n_pinpointed} / {len(mism_out)} mismatch rows")

    # ------------------------------------------------------------------
    # Dimension 2: SCE Groups with a clean <=24-month SSPS/GOPS4
    # requirement but zero MIC coverage anywhere in the 2-year window
    # ------------------------------------------------------------------
    ssps = pd.read_excel(SSPS_FILE, sheet_name="Functionality_Tasks")
    # The Bokor SSPS documents carry an "Applicable or not" column per task -
    # tasks the site marked N / N/A are not requirements at Bokor and are
    # excluded. (GOPS4.0 is generic and has no such column.)
    applicability = ssps["applicable_or_not"].fillna("").astype(str).str.upper().str.replace(" ", "")
    n_before = len(ssps)
    ssps = ssps[~applicability.isin(["N", "N/A", "NA"])]
    print(f"SSPS tasks marked not applicable at Bokor (excluded): {n_before - len(ssps)} of {n_before}")
    gops4_tasks = pd.read_excel(GOPS4_TASKS_FILE)
    ssps["months"] = ssps["frequency"].map(parse_months)
    gops4_tasks["months"] = gops4_tasks["frequency"].map(parse_months)
    print(f"\nSSPS tasks with a clearly-parseable frequency: {ssps['months'].notna().sum():,} / {len(ssps):,}")
    print(f"GOPS4 tasks with a clearly-parseable frequency: {gops4_tasks['months'].notna().sum():,} / {len(gops4_tasks):,}")

    # keep the real per-row document+page citation ("source", e.g.
    # "SKA_BOKOR_SSPS_ER005.pdf (page 1)" / "GOPS4.pdf (pages 17-20)") -
    # `standard` is just the SSPS/GOPS4 label, not a substitute for it
    # (same bug fixed in Check 7's crosswalk earlier - a citation that
    # only says "SSPS" isn't actually a citation)
    short_ssps = ssps[ssps["months"] <= 24][["sce_group", "assurance_task", "frequency", "months", "source"]].assign(standard="SSPS")
    short_gops4 = gops4_tasks[gops4_tasks["months"] <= 24][["sce_group", "assurance_task", "frequency", "months", "source"]].assign(standard="GOPS4")
    short_tasks = pd.concat([short_ssps, short_gops4], ignore_index=True)
    short_groups = set(short_tasks["sce_group"].dropna())
    print(f"SCE Groups with a clearly-parseable <=24-month requirement: {len(short_groups)}")


    mic_codes_used = set(mic["fl_code"].dropna())
    no_coverage_groups = sorted((short_groups - mic_codes_used) & current_codes)

    # Only a gap if Bokor actually has SCE assets in that group: at least one
    # FL identified for it in the approved register, or tagged with it in SAP.
    # A group with no SCE FLs at Bokor (e.g. no subsea isolation valves)
    # legitimately has no MICs.
    fl_sap = pd.read_excel(SAP_FL_FILE, sheet_name="Data", dtype=str)
    fl_sap.columns = [c.strip() for c in fl_sap.columns]
    sap_groups = set(fl_sap["SCE GROUP"].str.extract(CODE_RE, expand=False).dropna())
    register_groups = set(reg.loc[reg["gt_category"] == "sce", "gt_sce_group"].dropna())
    bokor_groups = sap_groups | register_groups
    missing_groups = [g for g in no_coverage_groups if g in bokor_groups]
    no_assets_groups = [g for g in no_coverage_groups if g not in bokor_groups]
    print(f"  - with no SCE FL at Bokor in register or SAP (not flagged): {no_assets_groups}")
    print(f"\nDimension 2 - SCE Groups with <=24M requirement, currently valid, "
          f"but ZERO MIC coverage in 2024-2025: {len(missing_groups)}")
    print(missing_groups)

    missing_detail = short_tasks[short_tasks["sce_group"].isin(missing_groups)].sort_values(
        ["sce_group", "months"]
    )
    missing_detail["assurance_task_excerpt"] = missing_detail["assurance_task"].astype(str).str.slice(0, 140)
    missing_out = missing_detail[["sce_group", "standard", "source", "assurance_task_excerpt", "frequency", "months"]]

    # ------------------------------------------------------------------
    summary = pd.DataFrame({
        "Metric": [
            "MIC Report rows (2024-2025, Bokor M014)",
            "Distinct MIC codes used",
            "Distinct SCE groups with MIC activity",
            "MIC codes not found in QS28 master (should be 0)",
            "Total MIC records comparable (both SCE Grp - FL and SCE Grp - MIC present)",
            "  - correctly assigned (SCE Grp - FL matches SCE Grp - MIC)",
            "  - MIC records of SCE Groups no longer in GOPS4.0 (no longer SCE)",
            "SCE Grp (FL) vs SCE Grp (MIC) code mismatches",
            "  - resolved likely_mic_assignment_wrong (register confirms the FL's tag)",
            "  - insufficient evidence (no register entry for that FL)",
            "SCE Groups with a clean <=24-month requirement (SSPS/GOPS4)",
            "  - currently valid per GOPS4 with ZERO MIC coverage in 2024-2025",
            "    - not flagged: no SCE FL at Bokor for this group (register or SAP)",
            "    - flagged: SCE FLs exist at Bokor but ZERO MIC coverage",
            "  - total flagged requirement rows (across those groups)",
            "Dimensions explored but removed (see module docstring)",
            "  - FL-level 'missing core MIC' (peer-coverage statistical inference, not a documented rule)",
            "  - Performance-criteria vs QS28 spec limit (circular - QS28 is the same system of record)",
            "  - Rejected-inspection flag (UD/UDVal are uniformly 'Accept' in this extract)",
        ],
        "Value": [
            len(mic), mic["MIC"].nunique(), mic["fl_code"].nunique(), len(unmatched),
            n_comparable, n_correct, len(decl_out),
            len(mism_out),
            (mism_out["resolution"] == "likely_mic_assignment_wrong").sum(),
            (mism_out["resolution"] == "insufficient_evidence").sum(),
            len(short_groups), len(no_coverage_groups), len(no_assets_groups), len(missing_groups),
            len(missing_out),
            "", "", "", "",
        ],
    })

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        mism_out.to_excel(xl, sheet_name="SCE_Group_MIC_Mismatch", index=False)
        decl_out.to_excel(xl, sheet_name="MIC_Declassified_Group", index=False)
        missing_out.to_excel(xl, sheet_name="Missing_MIC_Coverage", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
