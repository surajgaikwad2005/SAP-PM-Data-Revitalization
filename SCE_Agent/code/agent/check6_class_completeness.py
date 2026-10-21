"""
Check 6 (Group A) - SCE Class / Catalog Profile / Barrier Group completeness
------------------------------------------------------------------------------
Ground truth: PTG 12.05.04 Appendix 7 (294 valid Catalog Profile codes,
already extracted) + the approved SCE register (Group G1) for which FLs
are genuinely SCE. SAP side: Equipment Listing's own `Catalog Profile`
field, ZCDIE03A's per-equipment classification characteristics, and the
FL-level `SCE GROUP BARRIER` field.

"SCE equipment" is defined the same way as Check 5: equipment sitting
under a Functional Location whose *effective* SCE status (register-
corrected, falling back to raw SAP) is SCE.

Four completeness dimensions checked, only for SCE equipment - two of
which are RESOLVED with a concrete suggested value, not just flagged as
missing, using a deterministic lookup (not a statistical/peer-majority
inference) in both cases:
  1. Catalog Profile validity - is the code populated and a real PTG code?
  2. Classification record existence - does the equipment have ANY row in
     ZCDIE03A at all (16,909 / 115,983 equipment do - checked here for
     the SCE subset specifically)? Where missing, a suggested class IS
     provided: ZCDIE03A's own CLASS field is the same code family as
     Equipment Listing's Catalog Profile, just without the leading "1"
     (verified: 99.98% exact match, 4,613/4,614, on equipment that carry
     both fields) - since Catalog Profile is independently ~100%
     populated and valid, the correct class is already sitting on that
     equipment's own record, just not yet copied into ZCDIE03A.
  3. Characteristic completeness - of the characteristics recorded for an
     equipment that DOES have a ZCDIE03A entry, how many actually have a
     value versus the literal placeholder "?" (98.8% of all 376,991
     characteristic rows in the file are "?", not a real value)? No
     suggested value here - the correct reading (e.g. a design pressure)
     requires actual site/engineering data no source in scope has.
  4. SCE Group Barrier completeness on the FL itself (BOKOR_FL's own
     `SCE GROUP BARRIER` field), restricted to FLs with effective SCE
     status. Where missing, a suggested value IS provided: SCE GROUP
     BARRIER is a deterministic 1:1 attribute of the SCE Group code, not
     something that varies per FL - verified directly, every one of the
     30 SCE Group codes with this field populated anywhere in the full
     33,159-FL dataset uses exactly ONE distinct value - so any other FL
     of the same SCE Group that already has it populated gives the exact
     answer, not a majority-vote guess.

Output: Data exploration/output/D5_SCE_Class_Barrier_Completeness.xlsx
  - Summary
  - Equipment_Findings     (one row per SCE equipment with a gap)
  - FL_Barrier_Findings    (one row per SCE FL missing its Barrier Group)

Run:
    python "code/agent/check6_class_completeness.py"
"""

import re
import sqlite3
import warnings
from pathlib import Path

import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
ASSET_MASTER = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Asset Master"
SAP_FL_FILE = ASSET_MASTER / "BOKOR_FL LIsting_SCE Group_Aug26.xlsx"
SAP_EQUIP_FILE = ASSET_MASTER / "Equipment Listing_SKA_18June26.xlsx"
ZCDIE03A_FILE = ASSET_MASTER / "ZCDIE03A_bokor.xlsx"
REGISTER_DB = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "sce_register.db"
PTG_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "ptg_12_05_04_extraction.xlsx"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "D5_SCE_Class_Barrier_Completeness.xlsx"

SCE_CODE_RE = re.compile(r"([A-Z]{2,3}\d{3})\s*$")


def norm_fl(s):
    if pd.isna(s):
        return None
    return re.sub(r"\s+", "", str(s)).upper().strip()


def normalize_action(action):
    a = str(action).strip()
    al = a.lower()
    if "non-sce" in al or "non sce" in al:
        return "non_sce", None
    if "inactive" in al:
        return "inactive", None
    if "delete" in al or "deleted" in al:
        return "delete", None
    m = SCE_CODE_RE.search(a)
    if m:
        code = m.group(1)
        if "classify" in al:
            return "classify", code
        if "relocate" in al:
            return "relocate", code
        if "maintain" in al:
            return "maintain", code
        return "sce_other", code
    return "unclassified", None


def main():
    # ------------------------------------------------------------------
    # Effective SCE status per FL (same derivation as Check 5)
    # ------------------------------------------------------------------
    fl = pd.read_excel(SAP_FL_FILE, sheet_name="Data", dtype=str)
    fl.columns = [c.strip() for c in fl.columns]
    fl["fl"] = fl["Functional Location"].map(norm_fl)
    fl["sap_sce_group_code"] = fl["SCE GROUP"].str.extract(r"^([A-Z]{2,3}\d{3})", expand=False)
    fl = fl.drop_duplicates(subset="fl")

    con = sqlite3.connect(REGISTER_DB)
    reg = pd.read_sql("select functional_location, action from sce_register", con)
    con.close()
    reg["fl"] = reg["functional_location"].map(norm_fl)
    reg[["gt_category", "gt_sce_group"]] = reg["action"].apply(lambda a: pd.Series(normalize_action(a)))
    reg_sorted = reg.sort_values(by="gt_sce_group", key=lambda s: s.isna())
    reg_dedup = reg_sorted.drop_duplicates(subset="fl", keep="first")
    fl = fl.merge(reg_dedup[["fl", "gt_category", "gt_sce_group"]], on="fl", how="left")

    def effective(row):
        if pd.notna(row["gt_category"]):
            cat = row["gt_category"]
            if cat in ("maintain", "classify", "relocate", "sce_other"):
                return "SCE", row["gt_sce_group"]
            return "NOT_SCE", None
        sap_app = str(row["SCE APPLICABLE"]).strip().upper()
        if sap_app == "YES":
            return "SCE", row["sap_sce_group_code"]
        return "NOT_SCE", None

    fl[["eff_status", "eff_group"]] = fl.apply(lambda r: pd.Series(effective(r)), axis=1)
    sce_fls = fl[fl["eff_status"] == "SCE"].copy()
    print(f"SCE Functional Locations: {len(sce_fls):,} of {len(fl):,}")

    # ------------------------------------------------------------------
    # FL Barrier Group completeness (dimension 4) - resolved, not just
    # flagged: SCE GROUP BARRIER is a DETERMINISTIC 1:1 attribute of the
    # SCE Group code itself, not something that varies per FL. Verified
    # directly: of the 30 SCE Group codes with a Barrier value populated
    # anywhere in the full 33,159-FL Bokor dataset, every single one uses
    # exactly ONE distinct value (e.g. every SD006 FL that has this field
    # filled says "SHUTDOWN SYSTEMS", never anything else). So for any FL
    # missing it, we can look up the exact value from any OTHER FL of the
    # same SCE Group that already has it - not a peer-majority guess, a
    # 100%-consistent lookup of an already-known field.
    # ------------------------------------------------------------------
    fl["sce_code_any"] = fl["SCE GROUP"].str.extract(r"^([A-Z]{2,3}\d{3})", expand=False)
    barrier_populated_all = fl[fl["SCE GROUP BARRIER"].notna() & (fl["SCE GROUP BARRIER"].str.strip() != "")]
    barrier_by_code = barrier_populated_all.groupby("sce_code_any")["SCE GROUP BARRIER"].agg(
        lambda s: s.mode().iat[0]
    )
    n_inconsistent_codes = (
        barrier_populated_all.groupby("sce_code_any")["SCE GROUP BARRIER"].nunique() > 1
    ).sum()
    print(f"SCE Group codes with a Barrier value populated anywhere: {len(barrier_by_code)} "
          f"({n_inconsistent_codes} use more than one distinct value - mode used for those)")

    sce_fls["barrier_populated"] = sce_fls["SCE GROUP BARRIER"].notna() & (sce_fls["SCE GROUP BARRIER"].str.strip() != "")
    fl_barrier_findings = sce_fls[~sce_fls["barrier_populated"]][
        ["Functional Location", "FunctLocDescrip.", "eff_group", "DISCIPLINE"]
    ].copy()
    fl_barrier_findings["finding"] = "sce_group_barrier_missing"
    fl_barrier_findings["severity"] = "Medium"
    fl_barrier_findings["suggested_barrier_group"] = fl_barrier_findings["eff_group"].map(barrier_by_code)
    fl_barrier_findings["recommendation"] = fl_barrier_findings["suggested_barrier_group"].map(
        lambda v: (f"Every other FL of this SCE Group that has SCE GROUP BARRIER populated uses "
                   f"\"{v}\" - recommend setting this FL's Barrier Group to the same value."
                   if pd.notna(v) else
                   "No other FL of this SCE Group has SCE GROUP BARRIER populated anywhere in the dataset - "
                   "cannot suggest a value automatically, needs SME input.")
    )
    n_suggested = fl_barrier_findings["suggested_barrier_group"].notna().sum()
    print(f"SCE FLs missing SCE GROUP BARRIER: {len(fl_barrier_findings):,} of {len(sce_fls):,} "
          f"({len(fl_barrier_findings) / len(sce_fls) * 100:.1f}%) - {n_suggested:,} have a suggested value")

    # ------------------------------------------------------------------
    # Equipment -> SCE FL
    # Equipment Listing_SKA spans multiple fields - filter Location ==
    # BOKOR before joining/reporting, so both the SCE-equipment subset
    # and the "all-equipment context" stats below are Bokor-scoped.
    # ------------------------------------------------------------------
    equip_raw = pd.read_excel(SAP_EQUIP_FILE, sheet_name="Data", dtype=str)
    equip_raw.columns = [c.strip() for c in equip_raw.columns]
    equip = equip_raw[equip_raw["Location"].str.strip().str.upper() == "BOKOR"].copy()
    equip["fl"] = equip["Functional Location"].map(norm_fl)
    sce_equip = equip[equip["fl"].isin(sce_fls["fl"])].copy()
    print(f"\nEquipment records (all fields): {len(equip_raw):,}; Location==BOKOR: {len(equip):,}; "
          f"sitting under an SCE FL: {len(sce_equip):,}")

    # ------------------------------------------------------------------
    # Dimension 1: Catalog Profile validity
    # ------------------------------------------------------------------
    profiles = pd.read_excel(PTG_FILE, sheet_name="Catalog_Profiles")
    valid_profiles = set(profiles["catalog_profile"].dropna().str.strip())
    sce_equip["catalog_profile_populated"] = sce_equip["Catalog Profile"].notna() & (sce_equip["Catalog Profile"].str.strip() != "")
    sce_equip["catalog_profile_valid"] = sce_equip["Catalog Profile"].isin(valid_profiles)

    # ------------------------------------------------------------------
    # Dimensions 2 & 3: ZCDIE03A classification record + characteristic fill
    # ------------------------------------------------------------------
    zc = pd.read_excel(ZCDIE03A_FILE, sheet_name="ZCDIE03A_bokor", dtype=str)
    zc.columns = [c.strip() for c in zc.columns]
    zc["populated"] = zc["CHAR.VALUE"].notna() & (zc["CHAR.VALUE"].str.strip() != "") & (zc["CHAR.VALUE"].str.strip() != "?")
    zc_agg = zc.groupby("EQ.NUMBER").agg(
        num_characteristics=("CHAR", "count"),
        num_populated=("populated", "sum"),
        classes=("CLASS", lambda s: ",".join(sorted(set(s.dropna())))),
    ).reset_index()
    zc_agg["completeness_pct"] = (zc_agg["num_populated"] / zc_agg["num_characteristics"] * 100).round(1)
    bokor_equipment = set(equip["Equipment"].str.strip())
    zc_bokor = zc[zc["EQ.NUMBER"].str.strip().isin(bokor_equipment)]
    bokor_with_zc = zc_bokor["EQ.NUMBER"].nunique()

    sce_equip = sce_equip.merge(zc_agg, left_on="Equipment", right_on="EQ.NUMBER", how="left")
    sce_equip["has_classification_record"] = sce_equip["EQ.NUMBER"].notna()

    print(f"SCE equipment with a ZCDIE03A classification record: "
          f"{sce_equip['has_classification_record'].sum():,} / {len(sce_equip):,} "
          f"({sce_equip['has_classification_record'].mean() * 100:.1f}%)")
    has_record = sce_equip[sce_equip["has_classification_record"]]
    if len(has_record):
        print(f"Of those, average characteristic completeness: {has_record['completeness_pct'].mean():.1f}%")

    # ------------------------------------------------------------------
    # Build findings
    # ------------------------------------------------------------------
    findings = []

    bad_profile = sce_equip[~sce_equip["catalog_profile_populated"]]
    for _, r in bad_profile.iterrows():
        findings.append({"Equipment": r["Equipment"], "Object Description": r["Object Description"],
                         "Functional Location": r["Functional Location"], "finding": "catalog_profile_missing",
                         "severity": "High", "suggested_class": None, "detail": ""})

    invalid_profile = sce_equip[sce_equip["catalog_profile_populated"] & ~sce_equip["catalog_profile_valid"]]
    for _, r in invalid_profile.iterrows():
        findings.append({"Equipment": r["Equipment"], "Object Description": r["Object Description"],
                         "Functional Location": r["Functional Location"], "finding": "catalog_profile_not_in_ptg_list",
                         "severity": "Medium", "suggested_class": None, "detail": r["Catalog Profile"]})

    # Resolved, not just flagged: ZCDIE03A's own CLASS field is the same
    # code family as Equipment Listing's Catalog Profile, just without
    # the leading "1" - verified directly on the 4,614 equipment that
    # have BOTH fields populated: a 99.98% exact match (4,613/4,614; one
    # outlier). Since Catalog Profile is independently ~100% populated
    # and valid (Check 1b), any equipment missing a ZCDIE03A record
    # already has its own correct class sitting right there in its own
    # Equipment Listing row - not inferred from peers, just not yet
    # copied into ZCDIE03A.
    no_record = sce_equip[~sce_equip["has_classification_record"]]
    for _, r in no_record.iterrows():
        cp = r.get("Catalog Profile")
        cp = cp.strip() if pd.notna(cp) else None
        # strip only the single leading "1" (the digit prefix convention,
        # e.g. "1ICTR" -> "ICTR"), not every leading "1" character
        suggested_class = (cp[1:] if cp.startswith("1") else cp) if cp else None
        detail = (f"From this equipment's own Catalog Profile ({cp})"
                  if suggested_class else "No Catalog Profile on this equipment either - cannot suggest a class.")
        findings.append({"Equipment": r["Equipment"], "Object Description": r["Object Description"],
                         "Functional Location": r["Functional Location"], "finding": "no_classification_record",
                         "severity": "High", "suggested_class": suggested_class, "detail": detail})

    low_complete = sce_equip[sce_equip["has_classification_record"] & (sce_equip["completeness_pct"] < 50)]
    for _, r in low_complete.iterrows():
        findings.append({"Equipment": r["Equipment"], "Object Description": r["Object Description"],
                         "Functional Location": r["Functional Location"], "finding": "characteristics_mostly_unanswered",
                         "severity": "High", "suggested_class": None,
                         "detail": f"{r['num_populated']:.0f}/{r['num_characteristics']:.0f} populated ({r['completeness_pct']}%)"})

    findings_df = pd.DataFrame(findings).sort_values(["severity", "finding"])
    print(f"\nTotal equipment findings: {len(findings_df):,}")
    print(findings_df["finding"].value_counts())

    # ------------------------------------------------------------------
    # UDMS (UOE MX GU 001, May 2015) section 4.19, PDF pp.35-36: the FL
    # classification characteristics that are mandatory for every FL
    # identified as an SCE (classes F_FL_GENERAL and F_FL_SCE). Measured
    # only - completeness of each field on the SCE FLs; no values are
    # proposed here except where already resolved above (Barrier).
    # ------------------------------------------------------------------
    def is_blank(s):
        return s.isna() | (s.astype(str).str.strip() == "")

    udms_fields = [
        ("F_FL_GENERAL", "DISCIPLINE", "Responsible discipline"),
        ("F_FL_GENERAL", "SCE APPLICABLE", "Y if it is an SCE"),
        ("F_FL_SCE", "SCE GROUP", "Populated for all SCEs"),
        ("F_FL_SCE", "SCE GROUP BARRIER", "Populated for all SCEs"),
        ("F_FL_SCE", "REASON SCE AWARDED", "From the SCE Identification outcome"),
        ("F_FL_SCE", "DATE SCE CARRIED OUT", "Last review date from the SCE Identification outcome"),
        ("F_FL_SCE", "PS REQUIRED", "Populated for all SCEs"),
    ]
    udms_rows = []
    for cls, field, rule in udms_fields:
        blank = is_blank(sce_fls[field])
        row = {"UDMS class": cls, "Field": field, "UDMS rule": rule, "SCE FLs": len(sce_fls),
               "Populated": int((~blank).sum()), "Blank": int(blank.sum())}
        if field == "SCE APPLICABLE":
            not_yes = ~sce_fls[field].fillna("").str.strip().str.upper().eq("YES")
            row["Not 'YES' (blank or NO)"] = int(not_yes.sum())
        udms_rows.append(row)
    udms_df = pd.DataFrame(udms_rows)
    udms_df["Populated %"] = (udms_df["Populated"] / udms_df["SCE FLs"] * 100).round(1)
    udms_df["Source"] = "UDMS (UOE MX GU 001, May 2015) section 4.19, PDF pages 35-36"
    print("\nUDMS SCE class-field completeness on SCE FLs:")
    print(udms_df[["Field", "Populated", "Blank"]].to_string(index=False))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    summary = pd.DataFrame({
        "Metric": [
            "SCE Functional Locations", "SCE FLs missing SCE GROUP BARRIER",
            "  - of which have a suggested value (from another FL of the same SCE Group)",
            "Equipment under an SCE FL", "  - catalog profile missing",
            "  - catalog profile not in PTG's 294-code list", "  - no ZCDIE03A classification record at all",
            "    - of which have a suggested class (from their own Catalog Profile)",
            "  - has a record but <50% of characteristics answered",
            "All-equipment context: catalog profile validity rate",
            "All-equipment context: Bokor equipment with a ZCDIE03A record",
            "All-equipment context: characteristic values genuinely answered (not '?') on Bokor equipment",
            "All-equipment context: ZCDIE03A equipment numbers not in the Bokor equipment listing",
        ],
        "Value": [
            len(sce_fls), len(fl_barrier_findings), n_suggested,
            len(sce_equip),
            (findings_df.finding == "catalog_profile_missing").sum(),
            (findings_df.finding == "catalog_profile_not_in_ptg_list").sum(),
            (findings_df.finding == "no_classification_record").sum(),
            findings_df.loc[findings_df.finding == "no_classification_record", "suggested_class"].notna().sum(),
            (findings_df.finding == "characteristics_mostly_unanswered").sum(),
            f"{equip['Catalog Profile'].isin(valid_profiles).mean() * 100:.1f}% "
            f"({(~equip['Catalog Profile'].isin(valid_profiles)).sum()} of {len(equip)} not in list)",
            # coverage = Bokor equipment actually found in ZCDIE03A (overlap of the two
            # lists), not a ratio of the two files' sizes
            f"{bokor_with_zc / equip['Equipment'].nunique() * 100:.1f}% "
            f"({bokor_with_zc:,} of {equip['Equipment'].nunique():,} equipment)",
            f"{zc_bokor['populated'].mean() * 100:.1f}% "
            f"({zc_bokor['populated'].sum():,} of {len(zc_bokor):,} characteristic rows)",
            f"{zc['EQ.NUMBER'].nunique() - bokor_with_zc:,} of {zc['EQ.NUMBER'].nunique():,}",
        ],
    })
    summary = pd.concat([summary, pd.DataFrame({
        "Metric": [f"UDMS SCE class field blank on SCE FLs: {f}" for f in udms_df["Field"]]
                  + ["UDMS SCE class field: SCE APPLICABLE not 'YES' on SCE FLs"],
        "Value": list(udms_df["Blank"]) + [int(udms_df.loc[udms_df.Field == "SCE APPLICABLE",
                                                          "Not 'YES' (blank or NO)"].iloc[0])],
    })], ignore_index=True)

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        findings_df.to_excel(xl, sheet_name="Equipment_Findings", index=False)
        fl_barrier_findings[["Functional Location", "FunctLocDescrip.", "eff_group", "DISCIPLINE",
                             "finding", "severity", "suggested_barrier_group", "recommendation"]].to_excel(
            xl, sheet_name="FL_Barrier_Findings", index=False
        )
        udms_df.to_excel(xl, sheet_name="UDMS_SCE_Field_Completeness", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
