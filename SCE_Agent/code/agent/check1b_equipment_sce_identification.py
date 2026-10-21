"""
Check 1b (Group A) - Equipment-level SCE assignment + Catalog Profile
------------------------------------------------------------------------
Equipment has no SCE field of its own - it inherits SCE status from its
Functional Location (see Check 5). Check 1 already resolves, per FL,
whether SAP's SCE assignment agrees with the approved register. This
script rolls that same resolution down to every piece of EQUIPMENT
(Equipment Listing_SKA), joined through its FL, so the output is
equipment-actionable rather than FL-actionable - and carries each
equipment's own `Catalog Profile` field along for reuse in Check 6
(class/barrier completeness), since that is where Catalog Profile lives
in SAP (not on the FL).

Join chain:
    Equipment Listing_SKA  --[Functional Location]-->  FL Listing_SKO
        (confirms the FL exists in the full FL master / hierarchy;
         88 equipment reference an FL missing from FL Listing_SKO -
         reported as a data-integrity finding, not silently dropped)
    --[Functional Location]--> BOKOR_FL SCE overlay (SAP's SCE APPLICABLE/GROUP)
    --[Functional Location]--> approved SCE register (ground truth, Group G1)

Per equipment:
  1. Same finding categories as Check 1 (missing/mismatched/unsupported
     SCE assignment, structural status), now attached to the equipment
     sitting on that FL rather than just the FL row.
  2. `catalog_profile_populated` / `catalog_profile_valid_per_ptg` -
     Equipment Listing's own Catalog Profile field, cross-checked
     against PTG 12.05.04's 294 valid catalog-profile codes. This is a
     cleaner, fully-populated signal than Check 6's ZCDIE03A-based
     completeness check (which only covers 11% of SCE equipment) -
     turns out Catalog Profile itself is 100% populated and 99.997%
     valid; the real class-data gap Check 6 found is in ZCDIE03A's
     characteristic *values*, not in this template assignment.
  3. `gt_sce_group_is_legacy_per_gops4` - cross-reference to Check A3
     (GOPS4 currency): the register's recommended SCE group is itself
     no longer in the current GOPS4 list, so the "expected" value this
     check would otherwise assert needs SME reconciliation first.

Output: Data exploration/output/D1b_Equipment_SCE_Identification.xlsx
  - Summary
  - Findings                 (one row per flagged equipment)
  - FL_Not_In_Master         (equipment whose FL isn't in FL Listing_SKO)

Run:
    python "code/agent/check1b_equipment_sce_identification.py"
"""

import re
import sqlite3
import warnings
from pathlib import Path

import pandas as pd

warnings.simplefilter("ignore")

ROOT = Path(__file__).resolve().parents[2]
ASSET_MASTER = ROOT / "SAP_Data_New" / "SAP PM Data Revitalization" / "Asset Master"
SAP_EQUIP_FILE = ASSET_MASTER / "Equipment Listing_SKA_18June26.xlsx"
SAP_FL_MASTER_FILE = ASSET_MASTER / "FL Listing_SKO_19June26.xlsx"
SAP_FL_SCE_FILE = ASSET_MASTER / "BOKOR_FL LIsting_SCE Group_Aug26.xlsx"
REGISTER_DB = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "sce_register.db"
GOPS4_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_sce_groups.xlsx"
PTG_CLASS_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "ptg_12_05_04_extraction.xlsx"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "D1b_Equipment_SCE_Identification.xlsx"

SCE_CODE_LEADING_RE = r"^([A-Z]{2,3}\d{3})"


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
    m = re.search(r"([A-Z]{2,3}\d{3})\s*$", a)
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
    # Equipment (with Catalog Profile) + FL master + SAP SCE overlay
    # Both Equipment Listing_SKA and FL Listing_SKO span multiple fields
    # (Baronia, Baram, Temana, ...) - filter Location == BOKOR on both
    # sides before joining, so the mapping (and every downstream count)
    # is scoped to Bokor only, matching the BOKOR_FL SCE overlay file.
    # ------------------------------------------------------------------
    equip_raw = pd.read_excel(SAP_EQUIP_FILE, sheet_name="Data", dtype=str)
    equip_raw.columns = [c.strip() for c in equip_raw.columns]
    print(f"Equipment records (all fields): {len(equip_raw):,}")
    equip = equip_raw[equip_raw["Location"].str.strip().str.upper() == "BOKOR"].copy()
    equip["fl"] = equip["Functional Location"].map(norm_fl)
    print(f"Equipment records (Location == BOKOR): {len(equip):,}")

    fl_master_raw = pd.read_excel(SAP_FL_MASTER_FILE, sheet_name="Data", dtype=str)
    fl_master_raw.columns = [c.strip() for c in fl_master_raw.columns]
    print(f"FL Listing_SKO records (all fields): {len(fl_master_raw):,}")
    fl_master = fl_master_raw[fl_master_raw["Location"].str.strip().str.upper() == "BOKOR"].copy()
    fl_master["fl"] = fl_master["Functional Location"].map(norm_fl)
    fl_master = fl_master.drop_duplicates(subset="fl")
    fl_master_fls = set(fl_master["fl"].dropna())
    print(f"FL Listing_SKO records (Location == BOKOR): {len(fl_master):,}")

    fl_not_in_master = equip[~equip["fl"].isin(fl_master_fls) & equip["fl"].notna()].copy()
    print(f"Equipment whose FL is missing from FL Listing_SKO (data integrity): {len(fl_not_in_master):,}")

    sap_sce = pd.read_excel(SAP_FL_SCE_FILE, sheet_name="Data", dtype=str)
    sap_sce.columns = [c.strip() for c in sap_sce.columns]
    sap_sce["fl"] = sap_sce["Functional Location"].map(norm_fl)
    sap_sce["sap_sce_group_code"] = sap_sce["SCE GROUP"].str.extract(SCE_CODE_LEADING_RE, expand=False)
    sap_sce = sap_sce.rename(columns={"SCE APPLICABLE": "sap_sce_applicable", "SCE GROUP": "sap_sce_group"})
    sap_sce = sap_sce[["fl", "sap_sce_applicable", "sap_sce_group", "sap_sce_group_code"]].drop_duplicates(subset="fl")

    # ------------------------------------------------------------------
    # Ground-truth register
    # ------------------------------------------------------------------
    con = sqlite3.connect(REGISTER_DB)
    reg = pd.read_sql("select * from sce_register", con)
    con.close()
    reg["fl"] = reg["functional_location"].map(norm_fl)
    reg[["gt_category", "gt_sce_group"]] = reg["action"].apply(lambda a: pd.Series(normalize_action(a)))
    reg["source"] = reg["source_file"].astype(str) + " (page " + reg["printed_page"].astype("Int64").astype(str) + ")"
    dup_fls = reg["fl"].value_counts()
    dup_fls = dup_fls[dup_fls > 1].index
    reg_unique = reg[~reg["fl"].isin(dup_fls)].copy()

    gops4 = pd.read_excel(GOPS4_FILE)
    current_codes = set(gops4["sce_group"].dropna().str.strip().str.upper())

    ptg = pd.read_excel(PTG_CLASS_FILE, sheet_name="Catalog_Profiles")
    valid_catalog_profiles = set(ptg["catalog_profile"].dropna().astype(str).str.strip().str.upper())

    # ------------------------------------------------------------------
    # Join everything on FL, evaluate per equipment
    # ------------------------------------------------------------------
    merged = equip.merge(sap_sce, on="fl", how="left").merge(
        reg_unique[["fl", "gt_category", "gt_sce_group", "action", "discipline", "source"]],
        on="fl", how="left",
    )

    def evaluate(row):
        sap_applicable = str(row["sap_sce_applicable"]).strip().upper()
        sap_group_code = row["sap_sce_group_code"] if pd.notna(row["sap_sce_group_code"]) else None
        cat = row["gt_category"]

        if pd.isna(cat):
            if sap_applicable == "YES":
                return "unsupported_sce_assignment_no_register_entry", "High"
            return "no_finding", None
        sce_cat = cat in ("maintain", "classify", "relocate", "sce_other")
        if sce_cat and str(row["gt_sce_group"]).strip().upper() not in current_codes:
            # register SCE group no longer in GOPS4.0 -> no longer SCE (PCSB, 9 Oct 2026)
            if sap_applicable == "YES":
                return "declassified_group_sap_still_sce", "High"
            if sap_applicable == "NO":
                return "declassified_group_no_change", "Low"
            return "declassified_group_set_non_sce", "Medium"
        if sce_cat:
            if sap_applicable != "YES":
                return "missing_sce_assignment", "High"
            if sap_group_code != row["gt_sce_group"]:
                return "sce_group_mismatch", "High"
            return "no_finding", None
        if cat == "non_sce":
            if sap_applicable == "YES":
                return "unsupported_sce_assignment", "High"
            return "no_finding", None
        if cat in ("inactive", "delete"):
            return f"structural_status_{cat}", "Medium"
        return "no_finding", None

    merged[["finding", "severity"]] = merged.apply(lambda r: pd.Series(evaluate(r)), axis=1)
    merged["catalog_profile_populated"] = merged["Catalog Profile"].notna() & (merged["Catalog Profile"].str.strip() != "")
    merged["catalog_profile_valid_per_ptg"] = merged["Catalog Profile"].astype(str).str.strip().str.upper().isin(
        valid_catalog_profiles
    )
    def gops4_validity(code):
        if pd.isna(code) or not str(code).strip():
            return "N/A"
        return "Yes" if str(code).strip().upper() in current_codes else "No"

    merged["gt_sce_group_valid_per_latest_gops4"] = merged["gt_sce_group"].map(gops4_validity)

    findings = merged[merged["finding"] != "no_finding"].copy()
    findings["rule_reference"] = findings["source"].fillna("(no register entry)")

    out_cols = ["Equipment", "Object Description", "Functional Location", "FunctLocDescrip.",
                "Catalog Profile", "catalog_profile_populated", "catalog_profile_valid_per_ptg",
                "sap_sce_applicable", "sap_sce_group_code", "sap_sce_group",
                "gt_category", "gt_sce_group", "gt_sce_group_valid_per_latest_gops4",
                "finding", "severity", "discipline", "rule_reference"]
    findings_out = findings[out_cols].sort_values(["severity", "finding"])

    print(f"\nTotal equipment-level findings: {len(findings_out):,}")
    print(findings_out["finding"].value_counts())
    n_legacy = (findings_out["gt_sce_group_valid_per_latest_gops4"] == "No").sum()
    print(f"  ... of which the register SCE group is NOT in the latest GOPS4 (no longer SCE): {n_legacy:,}")
    n_blank_catalog = (~merged["catalog_profile_populated"]).sum()
    n_invalid_catalog = (~merged["catalog_profile_valid_per_ptg"]).sum()
    print(f"Equipment with blank Catalog Profile: {n_blank_catalog:,} / {len(merged):,}")
    print(f"Equipment with a Catalog Profile not in PTG's 294 valid codes: {n_invalid_catalog:,} / {len(merged):,}")
    invalid_catalog_df = merged[~merged["catalog_profile_valid_per_ptg"]][
        ["Equipment", "Object Description", "Functional Location", "Catalog Profile"]
    ]

    summary = pd.DataFrame({
        "Metric": [
            "Equipment records", "Equipment with FL missing from FL Listing_SKO master",
            "Equipment with blank Catalog Profile",
            "Equipment with a Catalog Profile not in PTG 12.05.04's 294 valid codes",
            "Total equipment-level SCE findings",
            "  - missing_sce_assignment", "  - sce_group_mismatch",
            "  - unsupported_sce_assignment", "  - unsupported_sce_assignment_no_register_entry",
            "  - structural_status_inactive", "  - structural_status_delete",
            "  - declassified_group_no_change", "  - declassified_group_set_non_sce",
            "  - declassified_group_sap_still_sce",
            "  - of which register SCE group is not in GOPS4.0 (no longer SCE)",
        ],
        "Value": [
            len(equip), len(fl_not_in_master), n_blank_catalog, n_invalid_catalog,
            len(findings_out),
            (findings_out.finding == "missing_sce_assignment").sum(),
            (findings_out.finding == "sce_group_mismatch").sum(),
            (findings_out.finding == "unsupported_sce_assignment").sum(),
            (findings_out.finding == "unsupported_sce_assignment_no_register_entry").sum(),
            (findings_out.finding == "structural_status_inactive").sum(),
            (findings_out.finding == "structural_status_delete").sum(),
            (findings_out.finding == "declassified_group_no_change").sum(),
            (findings_out.finding == "declassified_group_set_non_sce").sum(),
            (findings_out.finding == "declassified_group_sap_still_sce").sum(),
            n_legacy,
        ],
    })

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        findings_out.to_excel(xl, sheet_name="Findings", index=False)
        fl_not_in_master[["Equipment", "Object Description", "Functional Location", "FunctLocDescrip."]].to_excel(
            xl, sheet_name="FL_Not_In_Master", index=False
        )
        invalid_catalog_df.to_excel(xl, sheet_name="Invalid_Catalog_Profile", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
