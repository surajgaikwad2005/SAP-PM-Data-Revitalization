"""
Check 1 (Group A) - SCE assignment: SAP vs the approved SCE register
------------------------------------------------------------------------
Compares SAP's own SCE overlay (BOKOR_FL LIsting_SCE Group_Aug26.xlsx -
SCE APPLICABLE / SCE GROUP) against the ground truth extracted from the
approved SCE Identification Report + 11 discipline sign-offs (Group G1,
sce_register.db - 26,581 FL-level rows, one recommended action each).

Logic:
  1. Normalise the register's 107 distinct free-text `action` values into
     a category (maintain / classify / relocate / non_sce / inactive /
     delete) + a recommended SCE group code, via one regex (trailing code)
     plus keyword checks - no LLM needed, this is a closed, enumerable set.
  2. Join to SAP's FL-level SCE overlay on Functional Location.
  3. Flag:
     - SAP FL applicable=YES but register says non-SCE / no register
       entry at all  -> "unsupported SCE assignment"
     - Register recommends an SCE group but SAP is not marked
       applicable, or is marked with a different group -> "missing or
       mismatched SCE assignment"
     - Register says inactive/delete -> "structural status" (informational,
       cross-checked against SAP's own System status)
     - Duplicate register entries for one FL (81 cases, contradicting
       discipline sign-offs) -> excluded from the main join, but resolved
       with an independent signal: each FL's own equipment Catalog
       Profile, cross-referenced against a Catalog Profile -> dominant
       discipline lookup built from the *non*-duplicate register rows.
       Reported with an `equipment_type_resolution` column so review can
       be filtered straight to the likely-wrong entries, not just told
       "these are duplicates".

Output: Data exploration/output/D1_SCE_Identification_Corrected.xlsx
  - Summary
  - Findings              (every flagged FL, with rule_reference + evidence)
  - Duplicate_Register_FLs
  - Matches_Sample        (a sample of FLs that already agree, for sanity)
  - FL_Not_In_Master      (equipment whose FL is missing from FL Listing_SKO -
                            the one genuinely new finding folded in from what
                            was a separate equipment-level file, D1b, since
                            everything else in D1b duplicated these FL-level
                            findings one-for-one per equipment)

Run:
    python "code/agent/check1_sce_identification.py"
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
SAP_FL_MASTER_FILE = ASSET_MASTER / "FL Listing_SKO_19June26.xlsx"
REGISTER_DB = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "sce_register.db"
GOPS4_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_sce_groups.xlsx"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "D1_SCE_Identification_Corrected.xlsx"

SCE_CODE_RE = re.compile(r"([A-Z]{2,3}\d{3})\s*$")
# SAP's own SCE GROUP field holds "<CODE> <full description>" (e.g.
# "PS015 COLLISION AVOIDANCE SYS"), not the bare code the register uses -
# extract just the leading code so the two are actually comparable.
SCE_CODE_LEADING_RE = r"^([A-Z]{2,3}\d{3})"


def norm_fl(s):
    if pd.isna(s):
        return None
    return re.sub(r"\s+", "", str(s)).upper().strip()


def normalize_action(action):
    """One row's free-text action -> (category, recommended_sce_group)."""
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
    # Load SAP side
    # ------------------------------------------------------------------
    sap = pd.read_excel(SAP_FL_FILE, sheet_name="Data", dtype=str)
    sap.columns = [c.strip() for c in sap.columns]
    sap["fl"] = sap["Functional Location"].map(norm_fl)
    sap["sap_sce_group_code"] = sap["SCE GROUP"].str.extract(SCE_CODE_LEADING_RE, expand=False)
    sap = sap.rename(columns={
        "SCE APPLICABLE": "sap_sce_applicable",
        "SCE GROUP": "sap_sce_group",
        "SECONDARY SCE GROUP": "sap_secondary_sce_group",
        "SCE GROUP BARRIER": "sap_sce_barrier",
        "System status": "sap_system_status",
    })
    sap_cols = ["fl", "Functional Location", "FunctLocDescrip.", "sap_sce_applicable",
                "sap_sce_group", "sap_sce_group_code", "sap_secondary_sce_group",
                "sap_sce_barrier", "sap_system_status"]
    sap = sap[sap_cols].drop_duplicates(subset="fl")
    print(f"SAP FL SCE overlay: {len(sap):,} distinct FLs")

    # ------------------------------------------------------------------
    # Load ground truth (Group G1 register) and normalise
    # ------------------------------------------------------------------
    con = sqlite3.connect(REGISTER_DB)
    reg = pd.read_sql("select * from sce_register", con)
    con.close()
    reg["fl"] = reg["functional_location"].map(norm_fl)
    reg[["gt_category", "gt_sce_group"]] = reg["action"].apply(
        lambda a: pd.Series(normalize_action(a))
    )
    reg["source"] = reg["source_file"].astype(str) + " (page " + reg["printed_page"].astype("Int64").astype(str) + ")"
    print(f"Ground truth register: {len(reg):,} rows, {reg['fl'].nunique():,} distinct FLs")
    unclassified = reg[reg["gt_category"] == "unclassified"]
    print(f"Unclassified actions (should be 0): {len(unclassified)}")

    # duplicates: FLs with more than one register row
    dup_fls = reg["fl"].value_counts()
    dup_fls = dup_fls[dup_fls > 1].index
    duplicates_df = reg[reg["fl"].isin(dup_fls)].sort_values("fl").copy()
    print(f"FLs with multiple register rows: {len(dup_fls)} (excluded from the main join, listed separately)")

    reg_unique = reg[~reg["fl"].isin(dup_fls)].copy()

    # ------------------------------------------------------------------
    # Resolve duplicate discipline sign-offs using equipment type.
    # Each FL's equipment has its own Catalog Profile (SAP's own class
    # template code, e.g. "1ICTR" = pressure/diff transmitter). Build a
    # Catalog Profile -> dominant discipline lookup from the *non*-
    # duplicate register rows (no contradiction there, so this is a
    # clean, data-driven signal of "what discipline does this equipment
    # type actually belong to"), then apply it to the duplicate FLs -
    # whichever duplicate row's discipline agrees with its equipment's
    # own catalog-profile-implied discipline is the likely-correct one.
    # ------------------------------------------------------------------
    equip = pd.read_excel(SAP_EQUIP_FILE, sheet_name="Data", dtype=str)
    equip.columns = [c.strip() for c in equip.columns]
    equip = equip[equip["Location"].str.strip().str.upper() == "BOKOR"].copy()
    equip["fl"] = equip["Functional Location"].map(norm_fl)
    cp_by_fl = equip.groupby("fl")["Catalog Profile"].agg(lambda s: s.mode().iat[0] if len(s.mode()) else None)
    desc_by_fl = equip.groupby("fl")["Object Description"].agg(lambda s: s.mode().iat[0] if len(s.mode()) else None)

    # ------------------------------------------------------------------
    # Data-integrity check: equipment whose own FL doesn't exist in the
    # FL master at all (FL Listing_SKO). Folded in here (rather than a
    # separate equipment-level file) since it's the one genuinely new
    # finding beyond what Check 1's FL-level findings already cover.
    # ------------------------------------------------------------------
    fl_master = pd.read_excel(SAP_FL_MASTER_FILE, sheet_name="Data", dtype=str)
    fl_master.columns = [c.strip() for c in fl_master.columns]
    fl_master = fl_master[fl_master["Location"].str.strip().str.upper() == "BOKOR"].copy()
    fl_master["fl"] = fl_master["Functional Location"].map(norm_fl)
    fl_master_fls = set(fl_master["fl"].dropna())
    fl_not_in_master = equip[~equip["fl"].isin(fl_master_fls) & equip["fl"].notna()][
        ["Equipment", "Object Description", "Functional Location", "FunctLocDescrip."]
    ].copy()
    print(f"Equipment whose FL is missing from FL Listing_SKO master (data integrity): {len(fl_not_in_master):,}")

    def cp_stats(s):
        vc = s.value_counts()
        return pd.Series({"dominant_discipline": vc.idxmax(), "sample_count": len(s), "purity": vc.iloc[0] / len(s)})

    lookup_src = reg_unique.copy()
    lookup_src["catalog_profile"] = lookup_src["fl"].map(cp_by_fl)
    lookup_src = lookup_src.dropna(subset=["catalog_profile"])
    cp_lookup = lookup_src.groupby("catalog_profile")["discipline"].apply(cp_stats).unstack()
    print(f"Catalog Profile -> discipline lookup built from {len(lookup_src):,} clean register rows "
          f"({len(cp_lookup):,} distinct catalog profiles)")

    duplicates_df["catalog_profile"] = duplicates_df["fl"].map(cp_by_fl)
    duplicates_df["equipment_description"] = duplicates_df["fl"].map(desc_by_fl)
    duplicates_df = duplicates_df.merge(cp_lookup, left_on="catalog_profile", right_index=True, how="left")
    duplicates_df = duplicates_df.rename(columns={"dominant_discipline": "expected_discipline_per_equipment_type"})

    def resolve_duplicate(row):
        if pd.isna(row.get("expected_discipline_per_equipment_type")):
            return "insufficient_evidence_no_catalog_profile_match"
        if row["sample_count"] < 5 or row["purity"] < 0.75:
            return "insufficient_evidence_low_confidence"
        if row["discipline"] == row["expected_discipline_per_equipment_type"]:
            return "likely_correct"
        return "likely_contradicting_review"

    duplicates_df["equipment_type_resolution"] = duplicates_df.apply(resolve_duplicate, axis=1)
    n_resolved = (duplicates_df["equipment_type_resolution"] == "likely_contradicting_review").sum()
    print(f"Duplicate register rows flagged as likely-contradicting (equipment type points elsewhere): {n_resolved:,}")

    def dup_confidence(row):
        if str(row["equipment_type_resolution"]).startswith("insufficient_evidence"):
            return "Low"
        if pd.notna(row["purity"]) and pd.notna(row["sample_count"]):
            if row["purity"] >= 0.9 and row["sample_count"] >= 20:
                return "High"
            return "Medium"
        return "Low"

    duplicates_df["confidence"] = duplicates_df.apply(dup_confidence, axis=1)

    # ------------------------------------------------------------------
    # Join
    # ------------------------------------------------------------------
    merged = sap.merge(
        reg_unique[["fl", "sce_group", "gt_category", "gt_sce_group", "action",
                   "discipline", "attachment_title", "source"]],
        on="fl", how="left",
    )

    # SCE Groups of the latest GOPS4 (Mar 2026). PCSB (9 Oct 2026): a group not
    # among them is no longer classified as SCE, so a register SCE entry under
    # such a group is treated as declassified (see gops4_rule.py).
    gops4 = pd.read_excel(GOPS4_FILE)
    current_gops4_codes = set(gops4["sce_group"].dropna().str.strip().str.upper())

    def evaluate(row):
        sap_applicable = str(row["sap_sce_applicable"]).strip().upper()
        # compare CODES only - SAP's own SCE GROUP field holds the full
        # description too, never equal to the register's bare code
        sap_group_code = row["sap_sce_group_code"] if pd.notna(row["sap_sce_group_code"]) else None
        cat = row["gt_category"]

        if pd.isna(cat):
            if sap_applicable == "YES":
                return "unsupported_sce_assignment_no_register_entry", "High"
            return "no_finding", None

        sce_cat = cat in ("maintain", "classify", "relocate", "sce_other")
        if sce_cat and str(row["gt_sce_group"]).strip().upper() not in current_gops4_codes:
            # register SCE group no longer in GOPS4.0 -> no longer SCE
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

    # ------------------------------------------------------------------
    # SCE Group currency vs the latest GOPS4 (Mar 2026) - lets a reviewer
    # filter straight to findings whose "expected" SCE group is itself no
    # longer in the current standard (see check_gops4_currency.py), so
    # those get reconciled before being actioned rather than being
    # treated as an ordinary missing/mismatch finding.
    # ------------------------------------------------------------------
    def gops4_validity(code):
        if pd.isna(code) or not str(code).strip():
            return "N/A"
        return "Yes" if str(code).strip().upper() in current_gops4_codes else "No"

    merged["gt_sce_group_valid_per_latest_gops4"] = merged["gt_sce_group"].map(gops4_validity)

    findings = merged[merged["finding"] != "no_finding"].copy()
    findings["rule_reference"] = findings["source"].fillna("(no register entry)")
    findings["expected"] = findings["gt_sce_group"].fillna(findings["gt_category"])
    findings["current_sap_applicable"] = findings["sap_sce_applicable"]
    findings["current_sap_sce_group"] = findings["sap_sce_group"]
    findings["current_sap_sce_group_code"] = findings["sap_sce_group_code"]

    # ------------------------------------------------------------------
    # Confidence: how much evidence backs THIS specific finding being a
    # genuine issue (not severity - severity is business impact if true).
    #   High   - an explicit, direct contradiction against a single clean
    #            register source (mismatch/missing/unsupported), or an
    #            explicit inactive/delete instruction from the sign-off.
    #   Medium - the finding rests on an ABSENCE of register evidence
    #            (no_register_entry) rather than an explicit contradiction
    #            - the FL may simply be outside the 11 discipline
    #            documents' coverage.
    #   A register SCE group not in the latest GOPS4 is no longer SCE
    #   (PCSB, 9 Oct 2026) - the declassified_group_* findings - High.
    #   (Low is reserved for the Duplicate_Register_FLs sheet, where a
    #    resolution could not be backed by enough evidence at all.)
    # ------------------------------------------------------------------
    def confidence_level(row):
        f = row["finding"]
        if f == "unsupported_sce_assignment_no_register_entry":
            return "Medium"
        if f in ("missing_sce_assignment", "sce_group_mismatch", "unsupported_sce_assignment"):
            return "High"
        if f.startswith("declassified_group"):
            return "High"  # GOPS4.0 (Mar 2026) lists the current SCE Groups explicitly
        if f in ("structural_status_inactive", "structural_status_delete"):
            return "High"
        return "Medium"

    findings["confidence"] = findings.apply(confidence_level, axis=1)

    out_cols = ["Functional Location", "FunctLocDescrip.", "finding", "severity", "confidence",
                "current_sap_applicable", "current_sap_sce_group_code", "current_sap_sce_group",
                "gt_category", "gt_sce_group", "gt_sce_group_valid_per_latest_gops4",
                "action", "discipline", "rule_reference"]
    findings_out = findings[out_cols].sort_values(["severity", "finding"], ascending=[True, True])

    n_invalid_gops4 = (findings_out["gt_sce_group_valid_per_latest_gops4"] == "No").sum()
    print(f"Findings whose register SCE group is NOT in the latest GOPS4 (no longer SCE): {n_invalid_gops4:,}")

    print(f"\nTotal findings: {len(findings_out):,}")
    print(findings_out["finding"].value_counts())

    matches_sample = merged[merged["finding"] == "no_finding"].sample(
        min(50, (merged["finding"] == "no_finding").sum()), random_state=1
    )[["Functional Location", "sap_sce_applicable", "sap_sce_group", "gt_category", "gt_sce_group", "action"]]

    summary = pd.DataFrame({
        "Metric": [
            "SAP FLs (BOKOR_FL SCE overlay)",
            "Ground-truth register FLs (Group G1, deduplicated)",
            "FLs with duplicate register entries (excluded, see Duplicate_Register_FLs)",
            "FLs matched between SAP and register",
            "Total findings",
            "  - missing_sce_assignment",
            "  - sce_group_mismatch",
            "  - unsupported_sce_assignment",
            "  - unsupported_sce_assignment_no_register_entry",
            "  - structural_status_inactive",
            "  - structural_status_delete",
            "  - declassified_group_no_change (register SCE group not in GOPS4.0; SAP already Non-SCE)",
            "  - declassified_group_set_non_sce (register SCE group not in GOPS4.0; SCE APPLICABLE blank)",
            "  - declassified_group_sap_still_sce (register SCE group not in GOPS4.0; SAP marks SCE)",
            "  - of which expected SCE group is NOT in latest GOPS4 (no longer SCE)",
            "Duplicate register FLs (contradicting discipline sign-offs, see Duplicate_Register_FLs)",
            "  - resolved likely_correct (discipline matches equipment's catalog profile)",
            "  - resolved likely_contradicting_review (discipline does NOT match equipment type)",
            "  - insufficient evidence to resolve",
            "Equipment whose FL is missing from FL Listing_SKO master (data integrity, see FL_Not_In_Master)",
        ],
        "Value": [
            len(sap),
            reg_unique["fl"].nunique(),
            len(dup_fls),
            merged["gt_category"].notna().sum(),
            len(findings_out),
            (findings_out["finding"] == "missing_sce_assignment").sum(),
            (findings_out["finding"] == "sce_group_mismatch").sum(),
            (findings_out["finding"] == "unsupported_sce_assignment").sum(),
            (findings_out["finding"] == "unsupported_sce_assignment_no_register_entry").sum(),
            (findings_out["finding"] == "structural_status_inactive").sum(),
            (findings_out["finding"] == "structural_status_delete").sum(),
            (findings_out["finding"] == "declassified_group_no_change").sum(),
            (findings_out["finding"] == "declassified_group_set_non_sce").sum(),
            (findings_out["finding"] == "declassified_group_sap_still_sce").sum(),
            n_invalid_gops4,
            len(duplicates_df),
            (duplicates_df["equipment_type_resolution"] == "likely_correct").sum(),
            n_resolved,
            duplicates_df["equipment_type_resolution"].isin(
                ["insufficient_evidence_no_catalog_profile_match", "insufficient_evidence_low_confidence"]
            ).sum(),
            len(fl_not_in_master),
        ],
    })

    # ------------------------------------------------------------------
    # Column glossary - one row per (sheet, column), so a domain expert
    # opening the workbook doesn't need this script to know what every
    # field means. Placed as the first tab.
    # ------------------------------------------------------------------
    glossary_rows = [
        ("Findings", "Functional Location", "The SAP Functional Location (FL) code being evaluated."),
        ("Findings", "FunctLocDescrip.", "SAP's own text description of that FL."),
        ("Findings", "finding", "The type of discrepancy detected between SAP and the approved register. One of: "
                                 "missing_sce_assignment, sce_group_mismatch, unsupported_sce_assignment, "
                                 "unsupported_sce_assignment_no_register_entry, structural_status_inactive, "
                                 "structural_status_delete, declassified_group_no_change / _set_non_sce / "
                                 "_sap_still_sce (register SCE group not in GOPS4.0, so no longer SCE)."),
        ("Findings", "severity", "High/Medium - business impact IF the finding is correct. High = the FL's SCE "
                                  "status itself is wrong in SAP. Medium = an informational structural-status flag "
                                  "(register says the FL should be inactive/deleted)."),
        ("Findings", "confidence", "High/Medium/Low - how much evidence backs THIS finding being genuine (not "
                                    "severity - this is about trust in the finding itself). High = explicit, direct "
                                    "contradiction against a clean single-source register entry. Medium = either the "
                                    "register's own recommended SCE group is not in the latest GOPS4 (needs SME "
                                    "reconciliation before the finding can be actioned as-is), or the finding rests "
                                    "on an ABSENCE of register coverage rather than an explicit contradiction."),
        ("Findings", "current_sap_applicable", "SAP's current value of the SCE APPLICABLE field for this FL "
                                                "(Yes / No / blank)."),
        ("Findings", "current_sap_sce_group_code", "The bare SCE group code (e.g. PS015) extracted from SAP's "
                                                     "SCE GROUP field, for direct comparison with the register."),
        ("Findings", "current_sap_sce_group", "SAP's SCE GROUP field exactly as stored (code + description)."),
        ("Findings", "gt_category", "The approved register's recommendation, normalised into one of: maintain, "
                                     "classify, relocate, sce_other (all = 'should be this SCE group'), non_sce, "
                                     "inactive, delete."),
        ("Findings", "gt_sce_group", "The SCE group code the approved register recommends for this FL. Blank when "
                                      "gt_category is non_sce / inactive / delete (no group applies)."),
        ("Findings", "gt_sce_group_valid_per_latest_gops4", "Yes / No / N-A - does gt_sce_group still exist in the "
                                                              "current GOPS4 (March 2026) standard's 45-group list? "
                                                              "'No' means the group is no longer SCE (PCSB, 9 Oct "
                                                              "2026), so the FL is treated as declassified."),
        ("Findings", "action", "The original free-text recommendation exactly as written in the source sign-off "
                                "document (e.g. 'Maintain as PS015')."),
        ("Findings", "discipline", "Which of the 11 discipline sign-off documents this recommendation came from "
                                    "(e.g. INSTRUMENT, ELECTRICAL, MECHANICAL STATIC)."),
        ("Findings", "rule_reference", "Traceability - the exact source document and page number this finding is "
                                        "based on. Open this page to verify the finding by hand."),
        ("Duplicate_Register_FLs", "functional_location", "An FL that has MORE THAN ONE register entry (i.e. two "
                                                            "different discipline documents both claim it) - "
                                                            "excluded from the main Findings sheet and resolved "
                                                            "here instead."),
        ("Duplicate_Register_FLs", "equipment_description", "SAP's Object Description for the equipment sitting on "
                                                              "this FL - read this to judge the equipment type by "
                                                              "eye, same as the automated resolution does."),
        ("Duplicate_Register_FLs", "catalog_profile", "That equipment's SAP Catalog Profile code, i.e. its "
                                                        "PETRONAS-standard Equipment Class (PTG 12.05.04 / "
                                                        "PTG 00.01.03)."),
        ("Duplicate_Register_FLs", "sce_group", "The SCE group code as printed in this specific register row."),
        ("Duplicate_Register_FLs", "action", "The free-text recommendation from this specific document/row."),
        ("Duplicate_Register_FLs", "discipline", "Which discipline document produced THIS row (one row per "
                                                   "document that claims the FL)."),
        ("Duplicate_Register_FLs", "expected_discipline_per_equipment_type", "The discipline this Catalog Profile "
                                                                              "is empirically associated with "
                                                                              "elsewhere in the register (built "
                                                                              "only from FLs that have no "
                                                                              "duplicate/contradiction)."),
        ("Duplicate_Register_FLs", "sample_count", "How many other (non-duplicate) register rows share this "
                                                     "equipment's Catalog Profile - the size of the evidence base "
                                                     "behind expected_discipline_per_equipment_type."),
        ("Duplicate_Register_FLs", "purity", "Of those sample_count rows, the fraction that agree on the same "
                                              "discipline (0-1). Closer to 1 = a very consistent equipment-type-to-"
                                              "discipline pattern elsewhere in the data."),
        ("Duplicate_Register_FLs", "equipment_type_resolution", "The verdict for this row: likely_correct (this "
                                                                  "row's discipline matches the equipment type), "
                                                                  "likely_contradicting_review (does NOT match - "
                                                                  "review this one first), or "
                                                                  "insufficient_evidence_* (not enough data to "
                                                                  "judge - falls back to manual review)."),
        ("Duplicate_Register_FLs", "confidence", "High/Medium/Low, derived from sample_count and purity above. "
                                                   "Low always means equipment_type_resolution was "
                                                   "insufficient_evidence."),
        ("Duplicate_Register_FLs", "source", "Source document and page for this specific row."),
        ("Matches_Sample", "(all columns)", "A random sample of 50 FLs where SAP and the register already AGREE "
                                             "(no finding) - included only as a sanity check on the logic itself, "
                                             "not something requiring action."),
        ("FL_Not_In_Master", "(all columns)", "Equipment whose own Functional Location does not exist at all in "
                                               "the FL master (FL Listing_SKO) - a data-integrity issue distinct "
                                               "from any SCE-specific finding above."),
        ("Summary", "Metric / Value", "Headline counts for the whole check - see the Findings/Duplicate sheets for "
                                       "the underlying rows."),
    ]
    glossary_df = pd.DataFrame(glossary_rows, columns=["Sheet", "Column", "Meaning"])

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        glossary_df.to_excel(xl, sheet_name="Column_Glossary", index=False)
        summary.to_excel(xl, sheet_name="Summary", index=False)
        findings_out.to_excel(xl, sheet_name="Findings", index=False)
        dup_out_cols = ["functional_location", "equipment_description", "catalog_profile", "sce_group",
                        "action", "discipline", "expected_discipline_per_equipment_type",
                        "sample_count", "purity", "equipment_type_resolution", "confidence", "source"]
        duplicates_df[dup_out_cols].sort_values(
            ["equipment_type_resolution", "functional_location"]
        ).to_excel(xl, sheet_name="Duplicate_Register_FLs", index=False)
        matches_sample.to_excel(xl, sheet_name="Matches_Sample", index=False)
        fl_not_in_master.to_excel(xl, sheet_name="FL_Not_In_Master", index=False)

        # Readable column widths + wrapped, top-aligned text on the glossary tab
        from openpyxl.styles import Alignment
        ws = xl.sheets["Column_Glossary"]
        ws.column_dimensions["A"].width = 22
        ws.column_dimensions["B"].width = 40
        ws.column_dimensions["C"].width = 110
        wrap = Alignment(wrap_text=True, vertical="top")
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=3):
            for cell in row:
                cell.alignment = wrap
        for col, width in [("A", 30), ("B", 40), ("C", 45), ("D", 10), ("E", 12)]:
            xl.sheets["Findings"].column_dimensions[col].width = width
        for col, width in [("A", 30), ("B", 38), ("C", 16)]:
            xl.sheets["Duplicate_Register_FLs"].column_dimensions[col].width = width

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
