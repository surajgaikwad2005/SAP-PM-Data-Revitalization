"""
Pain Point #7 (Group C) - RBI Inspection Interval vs. SCE Maintenance Plan Interval
------------------------------------------------------------------------------
Scope: flag interval differences between RBI assessments and SCE
maintenance plan schedules, per equipment. Nothing else (no P&ID/
circuitization/corrosion-group analysis, no SAP writeback).

IMPORTANT - what this actually compares, and why:
  Before building, both candidate "interval" fields were inspected for
  real stored values:
    - RBI (RiskSummaryReport, Equipment Future Risk, 86 columns checked):
      there is NO stored "recommended inspection interval" field. RBI
      output here is a remaining-life ESTIMATE (`INT EST REM LIFE
      (years)` / `EXT EST REM LIFE (years)`, both fully populated) and a
      risk-matrix rank (`INSPECTION PRIORITY`, 1-25, not a duration).
      The Current-vs-Future-Risk sheet date gap is a fixed ~5-year RBI
      software modelling horizon on 1,683/1,685 rows, not an
      equipment-specific recommendation.
    - SAP's own Maintenance Plan export (Mplan_M014, Bokor-filtered,
      5,900 rows, all columns checked): carries `Maintenance strategy`
      (a code, e.g. PCSB25) and `Group Counter` (a package sequence
      number) but NOT a decoded numeric cycle - the interval for a
      strategy code lives in a separate SAP config table not present in
      any export available to this project.
  Neither literal field exists, so this check compares the two
  GROUNDED numbers that are actually available and meaningfully stand
  in for "when does this equipment next need attention":
    - RBI side  -> governing remaining life (the shorter of internal/
      external estimated remaining life - the standard RBI convention,
      since either degradation mode could govern failure first).
    - SCE side  -> the SCE Group's own required assurance-task interval
      from SSPS/GOPS4.0 (already extracted for Check 3) - the approved
      document SAP's maintenance plan is supposed to follow, since SAP's
      actual decoded schedule isn't available in any export we have.
  Status semantics are adapted accordingly (documented per status
  below) - MATCH/INTERVAL_DIFFERENCE compare "is the required interval
  covered by the remaining life", not literal numeric equality (which
  would be meaningless between a recurrence interval and a remaining-
  life estimate - they are different units of information).

Asset matching: RBI's `EQUIPMENT` tag -> SAP's `Technical IdentNo.`
(normalised substring match, Bokor only) -> Functional Location. Only
UNAMBIGUOUS matches (exactly one candidate FL) are used; everything else
is reported as ASSET_NOT_MATCHED rather than guessed. Piping is out of
scope (SAP does not carry piping circuits as Equipment objects with a
Technical IdentNo., so there is no reliable join for them).

Latest/relevant RBI assessment: where an equipment tag has multiple RBI
component rows (13 of 161 non-piping tags - different physical parts of
the same equipment, not dated re-assessments), the GOVERNING row (the
one with the shortest remaining life) is used, consistent with RBI
convention that the worst-case component drives the equipment's risk.

Statuses:
  MATCH                 - SCE's required interval is covered by (<=) the
                           RBI remaining life - no schedule/end-of-life
                           gap.
  INTERVAL_DIFFERENCE    - SCE's required interval EXCEEDS the RBI
                           remaining life - the next required task may
                           not occur before end-of-life. Flagged for
                           review, not assumed wrong.
  MISSING_RBI_INTERVAL   - asset matched, but RBI has no remaining-life
                           value to compare (neither INT nor EXT
                           populated).
  MISSING_SCE_PLAN       - asset matched and has RBI data, but is not a
                           registered SCE Functional Location, or its
                           SCE Group has no clearly-parseable SSPS/
                           GOPS4.0 interval to compare against.
  ASSET_NOT_MATCHED      - RBI and SAP records could not be confidently
                           associated (ambiguous tag match, or no match
                           at all).

Output: Data exploration/output/D4_RBI_vs_Maintenance_Interval.xlsx
  - Summary
  - RBI_vs_SCE_Interval_Comparison   (one row per non-piping RBI
                                       equipment record, every status
                                       represented, nothing dropped)

Run:
    python "code/agent/check4_rbi_vs_maintenance_interval.py"
"""

import re
import sqlite3
import warnings
from pathlib import Path

import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
ASSET_MASTER = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Asset Master"
RBI_FILE = (ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "RBI Record"
            / "RiskSummaryReport_01-09-2026-112923.xlsx")
SAP_FL_FILE = ASSET_MASTER / "BOKOR_FL LIsting_SCE Group_Aug26.xlsx"
SAP_EQUIP_FILE = ASSET_MASTER / "Equipment Listing_SKA_18June26.xlsx"
SSPS_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "ssps_requirements.xlsx"
GOPS4_TASKS_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_functionality_tasks.xlsx"
REGISTER_DB = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "sce_register.db"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "D4_RBI_vs_Maintenance_Interval.xlsx"

SCE_CODE_RE = re.compile(r"^([A-Z]{2,3}\d{3})")

MATCH = "MATCH"
INTERVAL_DIFFERENCE = "INTERVAL_DIFFERENCE"
MISSING_RBI_INTERVAL = "MISSING_RBI_INTERVAL"
MISSING_SCE_PLAN = "MISSING_SCE_PLAN"
ASSET_NOT_MATCHED = "ASSET_NOT_MATCHED"


def norm_fl(s):
    if pd.isna(s):
        return None
    return re.sub(r"\s+", "", str(s)).upper().strip()


def norm_tag(s):
    if pd.isna(s):
        return None
    t = re.sub(r"[^A-Z0-9]", "", str(s).upper())
    return t or None


def normalize_action(action):
    """Same normalisation used throughout this project - a register row's
    free-text action -> (category, recommended_sce_group)."""
    a = str(action).strip()
    al = a.lower()
    if "non-sce" in al or "non sce" in al:
        return "non_sce", None
    if "inactive" in al:
        return "inactive", None
    if "delete" in al or "deleted" in al:
        return "delete", None
    m = re.search(r"([A-Z]{2,3}\d{3})\s*$", a)
    if m:
        return "sce", m.group(1)
    return "unclassified", None


def parse_months(freq):
    """Same conservative parser as Check 3 - only a clean leading number
    (or Weekly/Monthly/Daily) is parsed; anything condition-based, RBI-
    based, or multi-part is left unknown, not guessed."""
    if pd.isna(freq):
        return None
    s = str(freq).strip()
    m = re.match(r"^(\d+)\s*M?\b", s, re.I)
    if m:
        return int(m.group(1))
    if re.match(r"^(Weekly|Monthly|Daily)\b", s, re.I):
        return 1
    return None


def main():
    # ------------------------------------------------------------------
    # RBI: non-piping equipment. Where an equipment tag has multiple
    # component rows, keep the GOVERNING one (shortest remaining life).
    # ------------------------------------------------------------------
    rbi = pd.read_excel(RBI_FILE, sheet_name="Equipment Future Risk")
    rbi = rbi[rbi["EQUIPMENT TYPE"] != "Piping"].copy()
    rbi["governing_rem_life_years"] = rbi[["INT EST REM LIFE (years)", "EXT EST REM LIFE (years)"]].min(axis=1)
    print(f"RBI Equipment Future Risk, non-piping: {len(rbi):,} rows, "
          f"{rbi['EQUIPMENT'].nunique()} distinct equipment tags")

    rbi = rbi.sort_values("governing_rem_life_years").drop_duplicates(subset="EQUIPMENT", keep="first")
    print(f"After keeping the governing (worst-case) component per equipment tag: {len(rbi):,} rows")

    rbi["eq_norm"] = rbi["EQUIPMENT"].map(norm_tag)

    # ------------------------------------------------------------------
    # Asset matching: RBI equipment tag -> SAP Technical IdentNo. (Bokor
    # only), normalised substring match. Only unambiguous (exactly 1
    # candidate FL) matches are used.
    # ------------------------------------------------------------------
    eq = pd.read_excel(SAP_EQUIP_FILE, sheet_name="Data", dtype=str)
    eq = eq[eq["Location"] == "BOKOR"].copy()
    eq["tid_norm"] = eq["Technical IdentNo."].map(norm_tag)
    tid_lookup = eq[["tid_norm", "Functional Location"]].dropna(subset=["tid_norm"])

    def find_fls(e):
        if not e:
            return []
        hits = tid_lookup[tid_lookup["tid_norm"].str.contains(re.escape(e), regex=True)]
        return sorted(hits["Functional Location"].unique().tolist())

    rbi["matched_fls"] = rbi["eq_norm"].map(find_fls)
    rbi["n_matches"] = rbi["matched_fls"].map(len)
    print(f"Asset matching: {(rbi['n_matches'] == 1).sum()} unambiguous, "
          f"{(rbi['n_matches'] > 1).sum()} ambiguous, {(rbi['n_matches'] == 0).sum()} unmatched")

    rbi["Functional Location"] = rbi["matched_fls"].map(lambda x: x[0] if len(x) == 1 else None)
    rbi["status"] = None
    rbi["status_detail"] = None
    rbi.loc[rbi["n_matches"] == 0, "status_detail"] = "No SAP Technical IdentNo. match found for this RBI equipment tag."
    rbi.loc[rbi["n_matches"] > 1, "status_detail"] = rbi.loc[rbi["n_matches"] > 1, "matched_fls"].map(
        lambda fls: f"Ambiguous tag - {len(fls)} candidate Functional Locations, not guessed: "
                    + "; ".join(fls[:5]) + (" ..." if len(fls) > 5 else "")
    )
    rbi.loc[rbi["n_matches"] != 1, "status"] = ASSET_NOT_MATCHED

    # ------------------------------------------------------------------
    # SCE Group resolution: approved register first (with its source
    # citation), SAP's own SCE GROUP field only as a fallback when the
    # FL has no register entry.
    # ------------------------------------------------------------------
    fl = pd.read_excel(SAP_FL_FILE, sheet_name="Data", dtype=str)
    fl.columns = [c.strip() for c in fl.columns]
    fl["fl"] = fl["Functional Location"].map(norm_fl)
    fl["sap_sce_group_code"] = fl["SCE GROUP"].str.extract(SCE_CODE_RE, expand=False)
    fl_lookup = fl.set_index("fl")[["SCE APPLICABLE", "sap_sce_group_code"]]
    fl_lookup = fl_lookup[~fl_lookup.index.duplicated(keep="first")]

    con = sqlite3.connect(REGISTER_DB)
    reg = pd.read_sql("select * from sce_register", con)
    con.close()
    reg["fl"] = reg["functional_location"].map(norm_fl)
    reg[["gt_category", "gt_sce_group"]] = reg["action"].apply(lambda a: pd.Series(normalize_action(a)))
    reg["cite"] = reg["source_file"].astype(str) + " (page " + reg["printed_page"].astype("Int64").astype(str) + ")"
    reg_dup_fls = reg["fl"].value_counts()
    reg_dup_fls = reg_dup_fls[reg_dup_fls > 1].index
    reg_unique = reg[~reg["fl"].isin(reg_dup_fls)].drop_duplicates("fl")
    gt_cat_by_fl = reg_unique.set_index("fl")["gt_category"]
    gt_group_by_fl = reg_unique.set_index("fl")["gt_sce_group"]
    gt_source_by_fl = reg_unique.set_index("fl")["cite"]

    def resolve_sce_group(fl_code):
        if fl_code is None:
            return None, None, None, None
        norm = norm_fl(fl_code)
        cat = gt_cat_by_fl.get(norm)
        if pd.notna(cat):
            if cat == "sce":
                return gt_group_by_fl.get(norm), gt_source_by_fl.get(norm), "Approved register", "High"
            return None, None, f"Approved register marks this FL as {cat} - not a registered SCE asset.", None
        if norm in fl_lookup.index:
            row = fl_lookup.loc[norm]
            if str(row["SCE APPLICABLE"]).strip().upper() == "YES" and pd.notna(row["sap_sce_group_code"]):
                return (row["sap_sce_group_code"], None,
                        "SAP SCE GROUP field (no register entry for this FL)", "Medium")
        return None, None, "Not a registered SCE asset (no register entry, SAP SCE APPLICABLE != YES).", None

    resolved = rbi["Functional Location"].map(resolve_sce_group)
    (rbi["SCE Group"], rbi["SCE Group Source"],
     rbi["sce_group_basis"], rbi["SCE Group Confidence"]) = zip(*resolved)

    no_group_mask = (rbi["status"].isna()) & (rbi["SCE Group"].isna())
    rbi.loc[no_group_mask, "status"] = MISSING_SCE_PLAN
    rbi.loc[no_group_mask, "status_detail"] = rbi.loc[no_group_mask, "sce_group_basis"]

    # ------------------------------------------------------------------
    # Required interval per SCE Group: shortest parseable SSPS/GOPS4.0
    # assurance-task frequency (the most frequent task is binding).
    # ------------------------------------------------------------------
    ssps = pd.read_excel(SSPS_FILE, sheet_name="Functionality_Tasks")
    gops4_tasks = pd.read_excel(GOPS4_TASKS_FILE)
    ssps["months"] = ssps["frequency"].map(parse_months)
    gops4_tasks["months"] = gops4_tasks["frequency"].map(parse_months)
    tasks = pd.concat([
        ssps[["sce_group", "assurance_task", "frequency", "months", "source"]].assign(standard="SSPS"),
        gops4_tasks[["sce_group", "assurance_task", "frequency", "months", "source"]].assign(standard="GOPS4"),
    ], ignore_index=True)
    parseable = tasks[tasks["months"].notna()]
    binding_idx = parseable.groupby("sce_group")["months"].idxmin()
    binding_task = parseable.loc[binding_idx].set_index("sce_group")

    def lookup_task(grp):
        if grp is None or grp not in binding_task.index:
            return None, None, None, None
        r = binding_task.loc[grp]
        return r["months"], r["standard"], r["source"], str(r["assurance_task"])[:160]

    res = rbi["SCE Group"].map(lookup_task)
    (rbi["SCE Required Interval (months)"], rbi["Required Interval Standard"],
     rbi["Interval Source"], rbi["Assurance Task (excerpt)"]) = zip(*res)

    no_freq_mask = (rbi["status"].isna()) & (rbi["SCE Required Interval (months)"].isna())
    rbi.loc[no_freq_mask, "status"] = MISSING_SCE_PLAN
    rbi.loc[no_freq_mask, "status_detail"] = (
        "SCE Group " + rbi.loc[no_freq_mask, "SCE Group"].astype(str)
        + " has no clearly-parseable required interval in SSPS/GOPS4.0 to compare against."
    )

    # ------------------------------------------------------------------
    # RBI remaining life missing (defensive - always populated for
    # non-piping equipment in this dataset, but checked, not assumed).
    # ------------------------------------------------------------------
    no_rbi_mask = (rbi["status"].isna()) & (rbi["governing_rem_life_years"].isna())
    rbi.loc[no_rbi_mask, "status"] = MISSING_RBI_INTERVAL
    rbi.loc[no_rbi_mask, "status_detail"] = "RBI record exists but neither internal nor external remaining-life estimate is populated."

    # ------------------------------------------------------------------
    # Comparison: SCE required interval vs RBI governing remaining life.
    # ------------------------------------------------------------------
    compare_mask = rbi["status"].isna()
    rbi.loc[compare_mask, "RBI Remaining Life (months)"] = rbi.loc[compare_mask, "governing_rem_life_years"] * 12
    rbi.loc[compare_mask, "Difference (months)"] = (
        rbi.loc[compare_mask, "SCE Required Interval (months)"] - rbi.loc[compare_mask, "RBI Remaining Life (months)"]
    )
    rbi.loc[compare_mask & (rbi["Difference (months)"] > 0), "status"] = INTERVAL_DIFFERENCE
    rbi.loc[compare_mask & (rbi["Difference (months)"] <= 0), "status"] = MATCH

    def finding_text(row):
        if row["status"] == MATCH:
            return (f"{row['Required Interval Standard']}'s required interval for {row['SCE Group']} "
                    f"({row['SCE Required Interval (months)']:.0f} months) is covered by this equipment's "
                    f"RBI-assessed remaining life ({row['RBI Remaining Life (months)']:.0f} months / "
                    f"{row['RBI Remaining Life (months)'] / 12:.1f} years) - no schedule gap identified.")
        if row["status"] == INTERVAL_DIFFERENCE:
            return (f"{row['Required Interval Standard']}'s required interval for {row['SCE Group']} is "
                    f"{row['SCE Required Interval (months)']:.0f} months, which is "
                    f"{row['Difference (months)']:.0f} months LONGER than this equipment's RBI-assessed "
                    f"remaining life of {row['RBI Remaining Life (months)']:.0f} months "
                    f"({row['RBI Remaining Life (months)'] / 12:.1f} years). The next required task may not "
                    f"occur before end-of-life. Review required - this does not automatically mean the SCE "
                    f"plan is wrong.")
        return row["status_detail"]

    rbi["Finding"] = rbi.apply(finding_text, axis=1)
    print("\nStatus distribution:")
    print(rbi["status"].value_counts())

    out_cols = {
        "EQUIPMENT": "RBI Equipment Tag", "EQUIPMENT DESC": "Equipment Description",
        "EQUIPMENT TYPE": "Equipment Type", "Functional Location": "Asset (Functional Location)",
        "SCE Group": "SCE Group", "SCE Group Confidence": "SCE Group Confidence",
        "SCE Group Source": "SCE Group Source",
        "RBI Remaining Life (months)": "RBI Remaining Life (months)",
        "SCE Required Interval (months)": "SCE Required Interval (months)",
        "Difference (months)": "Difference (months)",
        "Required Interval Standard": "Required Interval Standard",
        "Interval Source": "Interval Source", "Assurance Task (excerpt)": "Assurance Task (excerpt)",
        "status": "Status", "Finding": "Finding",
    }
    findings_out = rbi[list(out_cols)].rename(columns=out_cols)
    findings_out = findings_out.sort_values(
        by="Status", key=lambda s: s.map({INTERVAL_DIFFERENCE: 0, MATCH: 1, MISSING_SCE_PLAN: 2,
                                           MISSING_RBI_INTERVAL: 3, ASSET_NOT_MATCHED: 4})
    )

    summary = pd.DataFrame({
        "Metric": [
            "RBI Equipment Future Risk - non-piping equipment (governing component per tag)",
            f"  - {MATCH}",
            f"  - {INTERVAL_DIFFERENCE}",
            f"  - {MISSING_SCE_PLAN}",
            f"  - {MISSING_RBI_INTERVAL}",
            f"  - {ASSET_NOT_MATCHED}",
        ],
        "Value": [
            len(findings_out),
            (findings_out["Status"] == MATCH).sum(),
            (findings_out["Status"] == INTERVAL_DIFFERENCE).sum(),
            (findings_out["Status"] == MISSING_SCE_PLAN).sum(),
            (findings_out["Status"] == MISSING_RBI_INTERVAL).sum(),
            (findings_out["Status"] == ASSET_NOT_MATCHED).sum(),
        ],
    })

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        findings_out.to_excel(xl, sheet_name="RBI_vs_SCE_Interval_Comparison", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
