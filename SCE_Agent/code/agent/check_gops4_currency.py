"""
Check A3 (Group A) - SCE Group currency: legacy codes vs latest GOPS4
----------------------------------------------------------------------
GOPS4 (March 2026 revision, page 12, Figure 1-1 "PETRONAS SCE Hardware
Barriers") is PCSB's own authoritative, current list of which SCE Groups
exist today - 45 codes across 8 barrier categories (Structural Integrity,
Process Containment, Ignition Control, Detection, Protection, Shutdown,
Emergency, Lifesaving). This list was already extracted deterministically
into gops4_sce_groups.xlsx (from the body-text FUNCTIONALITY sections,
one section per current group - Figure 1-1 is just this same set drawn
as an infographic, confirmed by cross-reading the two).

The HSE Case (2020) and the approved discipline sign-off register both
predate this GOPS4 revision, and both still reference a number of SCE
Group codes (e.g. PC005 "Hydrocarbon piping", SI010 "Wells Structure",
LS001 "Personal Survival Equipment") that do NOT appear anywhere in the
current 45-group GOPS4 list. That does not necessarily mean the barrier
itself no longer matters - it may have been renamed, folded into another
group, or genuinely retired - but it does mean anyone using the register
or HSE Case as-is to assign an SCE Group in SAP could be assigning a code
the current generic standard no longer recognises. This is a data-
currency reconciliation flag, surfaced for SME review, not an assertion
that the barrier itself is invalid.

Output: Data exploration/output/D_GOPS4_SCE_Group_Currency.xlsx
  - Summary
  - Obsolete_Codes                 (one row per legacy code, source counts)
  - Register_Rows_With_Legacy_Code (every register row using one, actionable)
  - HSE_Case_Rows_With_Legacy_Code

Run:
    python "code/agent/check_gops4_currency.py"
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
REGISTER_DB = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "sce_register.db"
GOPS4_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_sce_groups.xlsx"
HSE_MATRIX_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "hse_case_sce_matrix.xlsx"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "D_GOPS4_SCE_Group_Currency.xlsx"

CODE_RE = re.compile(r"([A-Z]{2,3}\d{3})")


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
        return "sce", m.group(1)
    return "unclassified", None


def main():
    # ------------------------------------------------------------------
    # Current, authoritative SCE Group list per latest GOPS4 (Mar 2026)
    # ------------------------------------------------------------------
    gops4 = pd.read_excel(GOPS4_FILE)
    current_codes = set(gops4["sce_group"].dropna().str.strip().str.upper())
    print(f"Current SCE Groups per latest GOPS4 (Figure 1-1 / body text): {len(current_codes)}")

    # ------------------------------------------------------------------
    # Ground-truth register (discipline sign-offs, pre-dates this GOPS4 rev)
    # ------------------------------------------------------------------
    con = sqlite3.connect(REGISTER_DB)
    reg = pd.read_sql("select * from sce_register", con)
    con.close()
    reg["fl"] = reg["functional_location"].map(norm_fl)
    reg[["gt_category", "gt_code"]] = reg["action"].apply(lambda a: pd.Series(normalize_action(a)))
    reg["source"] = reg["source_file"].astype(str) + " (page " + reg["printed_page"].astype("Int64").astype(str) + ")"
    reg_sce = reg[reg["gt_category"] == "sce"].dropna(subset=["gt_code"]).copy()
    reg_legacy = reg_sce[~reg_sce["gt_code"].isin(current_codes)].copy()
    print(f"Register rows recommending an SCE code: {len(reg_sce):,}")
    print(f"  ... of which the code no longer appears in current GOPS4: {len(reg_legacy):,}")

    # ------------------------------------------------------------------
    # HSE Case SCE x Platform matrix (2020, pre-dates this GOPS4 rev)
    # ------------------------------------------------------------------
    hse = pd.read_excel(HSE_MATRIX_FILE, sheet_name="SCE_Platform_Matrix")
    hse["code_norm"] = hse["sce_code"].astype(str).str.strip().str.upper()
    hse_legacy = hse[~hse["code_norm"].isin(current_codes)].copy()
    print(f"HSE Case SCE codes: {len(hse)}, of which not in current GOPS4: {len(hse_legacy)}")

    # ------------------------------------------------------------------
    # SAP's own SCE GROUP field (sanity check - should already be clean)
    # ------------------------------------------------------------------
    sap = pd.read_excel(SAP_FL_FILE, sheet_name="Data", dtype=str)
    sap.columns = [c.strip() for c in sap.columns]
    sap["code"] = sap["SCE GROUP"].str.extract(r"^([A-Z]{2,3}\d{3})", expand=False)
    sap_codes_used = set(sap["code"].dropna().unique())
    sap_legacy_codes = sorted(sap_codes_used - current_codes)
    print(f"SAP FL overlay SCE Group codes in use: {len(sap_codes_used)}, of which legacy: {len(sap_legacy_codes)}")

    # ------------------------------------------------------------------
    # Consolidate: one row per legacy code with a source-count breakdown
    # ------------------------------------------------------------------
    all_legacy_codes = sorted(set(reg_legacy["gt_code"]) | set(hse_legacy["code_norm"]) | set(sap_legacy_codes))
    hse_desc = hse.drop_duplicates("code_norm").set_index("code_norm")["description"]

    rows = []
    for code in all_legacy_codes:
        rows.append({
            "sce_group_code": code,
            "description_from_hse_case": hse_desc.get(code, ""),
            "register_rows_using_this_code": (reg_legacy["gt_code"] == code).sum(),
            "distinct_fls_in_register": reg_legacy.loc[reg_legacy["gt_code"] == code, "fl"].nunique(),
            "referenced_in_hse_case_matrix": code in set(hse_legacy["code_norm"]),
            "currently_used_in_sap_sce_group_field": code in sap_codes_used,
            "review_note": (
                "SAP is actively using this code today, but it is not in the current GOPS4 list - "
                "urgent reconciliation needed"
                if code in sap_codes_used else
                "Not currently used in SAP - register/HSE Case reference only, but would be assigning "
                "an obsolete code if actioned as-is"
            ),
        })
    obsolete_df = pd.DataFrame(rows).sort_values(
        ["currently_used_in_sap_sce_group_field", "register_rows_using_this_code"], ascending=[False, False]
    )

    reg_legacy_out = reg_legacy[["fl", "functional_location", "sce_group", "gt_code", "action",
                                 "discipline", "attachment_title", "source"]].sort_values("gt_code")
    hse_legacy_out = hse_legacy.drop(columns=["code_norm"])

    summary = pd.DataFrame({
        "Metric": [
            "Current SCE Groups per latest GOPS4 (Mar 2026)",
            "Register rows recommending an SCE code",
            "  - of which code is legacy (not in current GOPS4)",
            "Distinct legacy codes referenced in the register",
            "HSE Case SCE codes (2020)",
            "  - of which code is legacy (not in current GOPS4)",
            "SAP SCE GROUP codes currently in use",
            "  - of which code is legacy (not in current GOPS4)",
            "Total distinct legacy codes found across all sources",
        ],
        "Value": [
            len(current_codes),
            len(reg_sce), len(reg_legacy), reg_legacy["gt_code"].nunique(),
            len(hse), len(hse_legacy),
            len(sap_codes_used), len(sap_legacy_codes),
            len(all_legacy_codes),
        ],
    })

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        obsolete_df.to_excel(xl, sheet_name="Obsolete_Codes", index=False)
        reg_legacy_out.to_excel(xl, sheet_name="Register_Rows_With_Legacy_Code", index=False)
        hse_legacy_out.to_excel(xl, sheet_name="HSE_Case_Rows_With_Legacy_Code", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
