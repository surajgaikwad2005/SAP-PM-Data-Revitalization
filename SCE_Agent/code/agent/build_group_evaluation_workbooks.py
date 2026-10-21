"""
Builds the two workbooks shared with PCSB for evaluation, one per group of
pain points:

  Group A - Pain Points 1-4 (SCE assignment, structure vs TIPS3, parent FL
            status, SCE class fields)
  Group B - Pain Points 5-8 (MIC vs SSPS/GOPS4.0, PS flag on MICs, RBI
            interval, rejected inspection lots)

Only completed pain points get output sheets; pain points still in progress
are listed in the Summary with their status and no output. Each workbook has:
  Summary          - status per pain point, then the result counts
  Column_Glossary  - the columns whose meaning is not obvious from the name
  PP<n>_<name>     - the output of each completed pain point: one row per
                     record needing action, with the current value, the
                     recommended value, a status and the source. Records the
                     agent confirmed as needing no action, and the working
                     sheets behind each result, are not carried here.

Does not recompute anything - reads the agent's output files in
Data exploration/output/ and reshapes them for the client.

Output:
  Data exploration/output/Group_A_Output_for_Evaluation.xlsx
  Data exploration/output/Group_B_Output_for_Evaluation.xlsx

Run:
    python "code/agent/build_group_evaluation_workbooks.py"
"""

import sys
from pathlib import Path

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill

OUT_DIR = Path(__file__).resolve().parents[2] / "Data exploration" / "output"
SAP_FL_FILE = (Path(__file__).resolve().parents[2] / "SAP_Data_New" / "SAP PM Data Revitalization" / "Asset Master"
               / "BOKOR_FL LIsting_SCE Group_Aug26.xlsx")

NAVY_FILL = PatternFill(start_color="1F3864", end_color="1F3864", fill_type="solid")
GREY_FILL = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
YELLOW_FILL = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF")
WRAP = Alignment(wrap_text=True, vertical="top")

READY = "Ready to apply"
PCSB_REVIEW = "PCSB review"


def metric_value(summary_df, contains):
    """Pull a Value from an agent Summary sheet's Metric column by substring match."""
    row = summary_df[summary_df["Metric"].astype(str).str.contains(contains, case=False, regex=False)]
    if not len(row):
        raise KeyError(contains)
    v = row["Value"].iloc[0]
    return int(v) if isinstance(v, float) and v.is_integer() else v


def style_header(ws):
    for cell in ws[1]:
        cell.fill = NAVY_FILL
        cell.font = HEADER_FONT
        cell.alignment = WRAP
    ws.freeze_panes = "A2"


def write_output_sheet(xl, name, df, widths=None):
    """One output sheet: navy header, sensible widths, and a yellow 'Remarks' column for PCSB's decision."""
    df.to_excel(xl, sheet_name=name, index=False)
    ws = xl.sheets[name]
    style_header(ws)
    for i, col in enumerate(df.columns, start=1):
        letter = ws.cell(row=1, column=i).column_letter
        longest = df[col].astype(str).str.len().quantile(0.9) if len(df) else 10
        ws.column_dimensions[letter].width = (widths or {}).get(col, min(max(len(col), longest) + 2, 60))
    cell = ws.cell(row=1, column=ws.max_column + 1, value="Remarks")
    cell.fill = YELLOW_FILL
    cell.font = Font(bold=True)
    ws.column_dimensions[cell.column_letter].width = 40
    ws.auto_filter.ref = ws.dimensions


def write_summary(xl, status_rows, result_rows):
    """Summary sheet: status of each pain point, then the result counts behind each output sheet."""
    ws = xl.book.create_sheet("Summary", 0)
    ws.append(["Pain Point", "Status", "Output sheet(s) in this workbook"])
    style_header(ws)
    for r in status_rows:
        ws.append(list(r))
        if r[1].startswith("In progress"):
            for cell in ws[ws.max_row]:
                cell.fill = GREY_FILL
    ws.append([])
    ws.append(["Pain Point", "Result", "Count", "Output sheet"])
    for cell in ws[ws.max_row]:
        cell.fill = NAVY_FILL
        cell.font = HEADER_FONT
    for pp, text, n, sheet in result_rows:
        ws.append([pp, text, n, sheet])
        if not text.startswith("  "):
            for cell in ws[ws.max_row]:
                cell.font = Font(bold=True)
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = WRAP
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 70
    ws.column_dimensions["C"].width = 34
    ws.column_dimensions["D"].width = 30


def write_glossary(xl, rows):
    ws = xl.book.create_sheet("Column_Glossary", 1)
    ws.append(["Sheet", "Column", "What it means"])
    style_header(ws)
    for r in rows:
        ws.append(list(r))
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for cell in row:
            cell.alignment = WRAP
    ws.column_dimensions["A"].width = 30
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 100


REMARKS_GLOSSARY = ("All output sheets", "Remarks",
                    "Blank - for PCSB's subject-matter expert to record the review decision on each row (agree / "
                    "disagree, corrected value, follow-up). Highlighted yellow.")


# ---------------------------------------------------------------------------
# Group A - Pain Points 1-4
# ---------------------------------------------------------------------------
PP1_FINDING = {
    "missing_sce_assignment": "SCE in the approved register, not assigned as SCE in SAP",
    "unsupported_sce_assignment": "Marked SCE in SAP, Non-SCE in the approved register",
    "sce_group_mismatch": "SCE Group in SAP differs from the approved register",
    "unsupported_sce_assignment_no_register_entry": "Marked SCE in SAP, no entry in the approved register",
    "declassified_group_set_non_sce": "Register SCE Group not in GOPS4.0 (no longer SCE); SCE APPLICABLE blank in SAP",
    "declassified_group_sap_still_sce": "Register SCE Group not in GOPS4.0 (no longer SCE); SAP marks it SCE under "
                                        "another group",
}
PP1_REC_APPLICABLE = {"missing_sce_assignment": "YES", "sce_group_mismatch": "YES", "unsupported_sce_assignment": "NO",
                      "declassified_group_set_non_sce": "NO"}
# Register SCE entries under a group that GOPS4.0 no longer has: no longer SCE (PCSB, 9 Oct 2026)
DECLASSIFIED = ["declassified_group_no_change", "declassified_group_set_non_sce", "declassified_group_sap_still_sce"]
GOPS4_BASIS = "GOPS4.pdf (Revision 4, March 2026), page 10 (45 SCE Groups) and page 12, Figure 1-1"


def pp1_status(finding, gops4_valid):
    if finding == "unsupported_sce_assignment_no_register_entry":
        return PCSB_REVIEW + " - no register entry"
    if finding == "declassified_group_sap_still_sce":
        return PCSB_REVIEW + " - register group no longer SCE; SAP group not backed by the register"
    return READY


def pp1_frame(df, current_applicable, current_group, ident_cols):
    """PP1 findings in client form; the register's Inactive / Delete status notes (no SCE action) are left out."""
    df = df[df["finding"].isin(PP1_FINDING)].copy()
    out = df[ident_cols].copy()
    out["Finding"] = df["finding"].map(PP1_FINDING)
    out["Current SCE APPLICABLE (SAP)"] = df[current_applicable]
    out["Current SCE GROUP (SAP)"] = df[current_group]
    out["Recommended SCE APPLICABLE"] = df["finding"].map(PP1_REC_APPLICABLE)
    out["Recommended SCE GROUP"] = df["gt_sce_group"].where(~df["finding"].isin(DECLASSIFIED))
    out["Status"] = [pp1_status(f, v) for f, v in zip(df["finding"], df["gt_sce_group_valid_per_latest_gops4"])]
    out["Discipline (register)"] = df["discipline"]
    out["Source (approved register document, page)"] = df["rule_reference"].replace("(no register entry)", "")
    gone = df["finding"].isin(DECLASSIFIED)
    out.loc[gone, "Source (approved register document, page)"] = df.loc[gone, "rule_reference"] + "; " + GOPS4_BASIS
    return out


def declassified_frame(fl_findings, eq_findings):
    """FLs the register identified as SCE under a group GOPS4.0 no longer has - now Non-SCE. Also the hand-over
    list for a new criticality and maintenance plan of declassified equipment (JDA-3 action item 2, 1 Oct 2026)."""
    action = {"declassified_group_no_change": "None - SAP already Non-SCE",
              "declassified_group_set_non_sce": "Set SCE APPLICABLE = NO",
              "declassified_group_sap_still_sce": "PCSB review - SAP marks it SCE under another group"}
    f = fl_findings[fl_findings["finding"].isin(DECLASSIFIED)]
    e = eq_findings[eq_findings["finding"].isin(DECLASSIFIED)]
    eq_count = e.groupby("Functional Location").size()
    return pd.DataFrame({
        "Functional Location": f["Functional Location"],
        "FL Description": f["FunctLocDescrip."],
        "Register SCE Group (not in GOPS4.0)": f["gt_sce_group"],
        "Current SCE APPLICABLE (SAP)": f["current_sap_applicable"],
        "Current SCE GROUP (SAP)": f["current_sap_sce_group"],
        "SCE status per GOPS4.0": "Non-SCE (declassified)",
        "SAP action": f["finding"].map(action),
        "Equipment installed": f["Functional Location"].map(eq_count).fillna(0).astype(int),
        "Register source (document, page)": f["rule_reference"],
        "GOPS4.0 basis": GOPS4_BASIS,
    }).sort_values(["Register SCE Group (not in GOPS4.0)", "Functional Location"])


def build_group_a(out=None):
    out = out or OUT_DIR / "Group_A_Output_for_Evaluation.xlsx"

    d1 = {s: pd.read_excel(OUT_DIR / "D1_SCE_Identification_Corrected.xlsx", sheet_name=s) for s in ["Summary", "Findings"]}
    d1b = pd.read_excel(OUT_DIR / "D1b_Equipment_SCE_Identification.xlsx", sheet_name="Findings")
    obsolete = pd.read_excel(OUT_DIR / "D_GOPS4_SCE_Group_Currency.xlsx", sheet_name="Obsolete_Codes")
    d2 = {s: pd.read_excel(OUT_DIR / "D2_Structure_TIPS3_Registration_Level.xlsx", sheet_name=s)
          for s in ["Granularity_Review", "Outlier_FL_Reattachment"]}
    d5 = {s: pd.read_excel(OUT_DIR / "D2_D5_Structure_Relocation_Reassignment.xlsx", sheet_name=s)
          for s in ["Summary", "FL_Hierarchy_Findings", "Equipment_Rollup"]}

    # ---- PP1
    decl = declassified_frame(d1["Findings"], d1b)
    fl1 = pp1_frame(d1["Findings"], "current_sap_applicable", "current_sap_sce_group",
                    ["Functional Location", "FunctLocDescrip."]).rename(columns={"FunctLocDescrip.": "FL Description"})
    eq1 = pp1_frame(d1b, "sap_sce_applicable", "sap_sce_group",
                    ["Equipment", "Object Description", "Functional Location", "Catalog Profile"]
                    ).rename(columns={"Object Description": "Equipment Description"})
    # SAP's SECONDARY SCE GROUP field is not covered by the currency check (SCE GROUP only) - read it here
    sap_fl = pd.read_excel(SAP_FL_FILE, dtype=str, usecols=["Functional Location", "SECONDARY SCE GROUP"])
    sap_fl["code"] = sap_fl["SECONDARY SCE GROUP"].str.extract(r"^([A-Z]{2}\d{3})", expand=False)
    secondary = sap_fl.dropna(subset=["code"]).groupby("code")["Functional Location"].apply(list)
    codes = pd.DataFrame({
        "Register SCE Group code": obsolete["sce_group_code"],
        "Description (HSE Case 2020)": obsolete["description_from_hse_case"],
        "Register rows using the code": obsolete["register_rows_using_this_code"],
        "In HSE Case 2020 SCE matrix": obsolete["referenced_in_hse_case_matrix"].map({True: "Yes", False: "No"}),
        "Used in SAP SCE GROUP today": obsolete["currently_used_in_sap_sce_group_field"].map({True: "Yes", False: "No"}),
        "Used in SAP SECONDARY SCE GROUP today": obsolete["sce_group_code"].map(
            lambda c: f"Yes - {len(secondary[c])} FL(s): {', '.join(secondary[c])}" if c in secondary else "No"),
        "SCE status per GOPS4.0": "No longer SCE - not among the 45 SCE Groups of GOPS4.0",
        "Register FLs declassified (PP1_Declassified_GOPS4)": obsolete["sce_group_code"].map(
            decl.groupby("Register SCE Group (not in GOPS4.0)").size()).fillna(0).astype(int),
        "GOPS4.0 basis": GOPS4_BASIS,
    })

    # ---- PP2: FL re-attachments and SCE Groups to confirm, in one sheet
    gran = d2["Granularity_Review"]
    tips3_level = dict(zip(gran["sce_group"], gran["system_level_boundaries"]))
    rows = []
    for r in d2["Outlier_FL_Reattachment"].itertuples():
        has_target = isinstance(r.suggested_reattachment_fl, str)
        rows.append({
            "Record type": "Functional Location", "Record": r.functional_location,
            "Description": r.functional_location_descrip, "SCE Group": r.sce_group,
            "TIPS3 registration level": tips3_level.get(r.sce_group),
            "Finding": f"Registered at hierarchy depth {r.current_depth}; the SCE Group is typically registered at "
                       f"depth {r.group_typical_depth}",
            "Recommendation": (f"Re-attach the SCE registration to {r.suggested_reattachment_fl} "
                               f"({r.suggested_reattachment_descrip}), already in this FL's own parent chain at "
                               f"depth {r.group_typical_depth}") if has_target
            else "No node at the typical depth in this FL's own parent chain - SME to identify the attachment point",
            "Status": READY if has_target else "SME input needed",
            "Source": "TIPS3 SCE Manual Appendix D; SAP FL hierarchy",
        })
    for r in gran[gran["review_flag"].notna()].itertuples():
        rows.append({
            "Record type": "SCE Group", "Record": r.sce_group, "Description": r.sce_group_title, "SCE Group": r.sce_group,
            "TIPS3 registration level": r.system_level_boundaries,
            "Finding": f"Registered per item / equipment category, but {r.distinct_fls_registered} Functional "
                       "Locations are registered under it at Bokor",
            "Recommendation": "PCSB to confirm whether Bokor has equipment of this SCE Group",
            "Status": PCSB_REVIEW, "Source": "TIPS3 SCE Manual Appendix D; SAP SCE GROUP field and approved register",
        })
    pp2 = pd.DataFrame(rows)

    # ---- PP3: only the SCE FL / parent combinations that need action or review
    h = d5["FL_Hierarchy_Findings"]
    review_boundary = h["boundary_resolution"].eq("insufficient_peer_data")
    act = h[h["hier_finding"].isin(["parent_inactive_in_sap", "sce_fl_inactive_in_sap", "parent_unassessed"])
            | review_boundary].copy()
    eq_count = d5["Equipment_Rollup"].groupby("Functional Location").size()
    pp3_finding = {
        "parent_inactive_in_sap": ("Active SCE FL under a parent FL that is inactive (INAC) in SAP",
                                   "Relocate under the next active ancestor (or reactivate the parent if its "
                                   "deactivation was in error)", READY),
        "sce_fl_inactive_in_sap": ("SCE FL is itself inactive (INAC) in SAP",
                                   "Confirm: if decommissioned, withdraw the SCE registration; if in service, "
                                   "reactivate the FL", "PCSB to confirm"),
        "parent_unassessed": ("Parent FL has no SCE status in the register, SAP or the SCE master template",
                              "Send the parent FL for SCE assessment", PCSB_REVIEW),
        "boundary": ("SCE FL under a Non-SCE parent; fewer than 5 FLs in its SCE Group to compare its placement with",
                     "Confirm the placement against the TIPS3 registration level", "SME review"),
    }
    key = act["hier_finding"].where(~review_boundary.loc[act.index], "boundary")
    pp3 = pd.DataFrame({
        "Functional Location": act["Functional Location"],
        "FL Description": act["FunctLocDescrip."],
        "SCE Group": act["eff_group"],
        "Equipment installed": act["Functional Location"].map(eq_count).fillna(0).astype(int),
        "Parent FL": act["Superior FunctLoc."],
        "Parent SCE status": act["parent_eff_status"].replace({"NON_SCE": "Non-SCE", "UNASSESSED": "Not assessed"}),
        "Parent SAP system status": act["parent_sap_system_status"],
        "Finding": key.map(lambda k: pp3_finding[k][0]),
        "Recommendation": key.map(lambda k: pp3_finding[k][1]),
        "Recommended new parent FL": act["suggested_relocation_target_fl"],
        "Recommended parent description": act["suggested_relocation_target_descrip"],
        "TIPS3 registration level": act["tips3_registration_boundary"],
        "Status": key.map(lambda k: pp3_finding[k][2]),
    })
    order = {"parent_inactive_in_sap": 0, "boundary": 1, "parent_unassessed": 2, "sce_fl_inactive_in_sap": 3}
    pp3 = pp3.iloc[key.map(order).argsort(kind="stable")]

    # ---- Summary
    hf = h["hier_finding"].value_counts()
    status_rows = [
        ("1. SCE assignment of Equipment and Functional Locations", "Completed",
         "PP1_FL_SCE_Assignment, PP1_Equipment_SCE_Assignment, PP1_Declassified_GOPS4, PP1_Codes_Not_In_GOPS4"),
        ("2. Asset register structure against TIPS3", "Completed", "PP2_TIPS3_Structure"),
        ("3. Equipment and parent FL SCE status - relocation / re-assignment", "Completed", "PP3_Parent_FL_Status"),
        ("4. Completeness of SCE class fields", "In progress - populating the SCE class fields", "(none yet)"),
    ]
    pp3_rows = [
        ("", "  Relocation recommended: active SCE FL under an inactive parent", int(hf.get("parent_inactive_in_sap", 0)),
         "PP3_Parent_FL_Status"),
        ("", "  SCE FL itself inactive in SAP - PCSB to confirm", int(hf.get("sce_fl_inactive_in_sap", 0)),
         "PP3_Parent_FL_Status"),
        ("", "  For review: parent never assessed / too few peers to confirm placement",
         int(hf.get("parent_unassessed", 0) + review_boundary.sum()), "PP3_Parent_FL_Status"),
    ]
    assert len(pp3) == sum(r[2] for r in pp3_rows)
    is_fl = pp2["Record type"] == "Functional Location"
    result_rows = [
        ("1. SCE assignment", "Functional Locations checked against the approved register",
         metric_value(d1["Summary"], "SAP FLs"), ""),
        ("", "  FLs with a recommended SCE assignment correction (ready to apply)",
         int((fl1["Status"] == READY).sum()), "PP1_FL_SCE_Assignment"),
        ("", "    - SCE in the register, not assigned as SCE in SAP",
         int((d1["Findings"]["finding"] == "missing_sce_assignment").sum()), "PP1_FL_SCE_Assignment"),
        ("", "    - marked SCE in SAP, Non-SCE in the register",
         int((d1["Findings"]["finding"] == "unsupported_sce_assignment").sum()), "PP1_FL_SCE_Assignment"),
        ("", "    - register SCE Group not in GOPS4.0, SCE APPLICABLE blank: set to NO",
         int((d1["Findings"]["finding"] == "declassified_group_set_non_sce").sum()), "PP1_FL_SCE_Assignment"),
        ("", "  FLs for PCSB review", int(fl1["Status"].str.startswith(PCSB_REVIEW).sum()), "PP1_FL_SCE_Assignment"),
        ("", "    - marked SCE in SAP, no entry in the register",
         int((d1["Findings"]["finding"] == "unsupported_sce_assignment_no_register_entry").sum()),
         "PP1_FL_SCE_Assignment"),
        ("", "    - register SCE Group not in GOPS4.0, SAP marks it SCE under another group",
         int((d1["Findings"]["finding"] == "declassified_group_sap_still_sce").sum()), "PP1_FL_SCE_Assignment"),
        ("", "  FLs registered SCE under a group no longer in GOPS4.0: now Non-SCE", len(decl),
         "PP1_Declassified_GOPS4"),
        ("", "    - SAP already Non-SCE, no change", int(decl["SAP action"].str.startswith("None").sum()),
         "PP1_Declassified_GOPS4"),
        ("", "  Equipment installed on these FLs (same findings)", len(eq1), "PP1_Equipment_SCE_Assignment"),
        ("", "    - ready to apply", int((eq1["Status"] == READY).sum()), "PP1_Equipment_SCE_Assignment"),
        ("", "  SCE Group codes in the register or HSE Case 2020 not in GOPS4.0 (no longer SCE)", len(codes),
         "PP1_Codes_Not_In_GOPS4"),
        ("2. Structure against TIPS3", "SCE Groups with a TIPS3 registration level", len(gran), ""),
        ("", "  FLs registered away from their SCE Group's typical depth", int(is_fl.sum()), "PP2_TIPS3_Structure"),
        ("", "    - re-attachment recommended", int((is_fl & (pp2["Status"] == READY)).sum()), "PP2_TIPS3_Structure"),
        ("", "    - SME input needed", int((pp2["Status"] == "SME input needed").sum()), "PP2_TIPS3_Structure"),
        ("", "  Item-level SCE Groups with no FL registered - PCSB to confirm", int((~is_fl).sum()),
         "PP2_TIPS3_Structure"),
        ("3. Parent FL status", "SCE Functional Locations checked",
         metric_value(d5["Summary"], "FLs: effective status = SCE"), ""),
        ("", "  Confirmed, no action: active SCE FL under an active SCE parent",
         metric_value(d5["Summary"], "FLs: effective status = SCE") - len(h), "(not listed)"),
        ("", "  SCE FL / parent FL combinations checked (parent not SCE, or SCE FL inactive)", len(h), ""),
        ("", "  Confirmed, no action: parent is a grouping node", int(hf.get("parent_grouping_node", 0)), "(not listed)"),
        ("", "  Confirmed, no action: SCE FL under a Non-SCE parent, placement consistent with its SCE Group",
         int(h["boundary_resolution"].eq("likely_correct_bottom_up").sum()), "(not listed)"),
        *pp3_rows,
        ("4. SCE class fields", "In progress - no output in this workbook yet", "", ""),
    ]

    glossary = [
        ("PP1_FL_SCE_Assignment", "Finding",
         "How SAP's SCE assignment (SCE APPLICABLE / SCE GROUP) differs from the approved SCE identification register "
         "(the 11 discipline sign-off documents)."),
        ("PP1_FL_SCE_Assignment", "Recommended SCE APPLICABLE / SCE GROUP",
         "The value in the approved register. Blank where the FL has no register entry - no value is proposed."),
        ("PP1_FL_SCE_Assignment", "Status",
         "Ready to apply: the register gives the value (for a register SCE Group not in GOPS4.0, GOPS4.0 makes the FL "
         "Non-SCE). PCSB review: no register entry, or the register group is no longer SCE while SAP marks the FL SCE "
         "under another group."),
        ("PP1_Declassified_GOPS4", "(sheet)",
         "FLs the approved register identified as SCE under an SCE Group that is not among the 45 SCE Groups of "
         "GOPS4.0 (Revision 4, March 2026). GOPS4.0 is the latest standard, so these FLs are no longer SCE. SAP action "
         "says whether SAP needs changing. Also the hand-over list for a new criticality and maintenance plan for the "
         "declassified equipment."),
        ("PP1_FL_SCE_Assignment", "Source (approved register document, page)",
         "The sign-off document and PDF page holding the register entry - open it to verify the row."),
        ("PP1_Equipment_SCE_Assignment", "(all columns)",
         "The PP1_FL_SCE_Assignment findings carried to each piece of equipment installed on the Functional Location "
         "(equipment take their SCE status from their FL)."),
        ("PP1_Codes_Not_In_GOPS4", "(all columns)",
         "SCE Group codes used in the approved register or the HSE Case 2020 SCE matrix that are not among the 45 "
         "SCE Groups of GOPS4.0 (GOPS4.pdf page 12, Figure 1-1). They are no longer SCE."),
        ("PP2_TIPS3_Structure", "Record type",
         "Functional Location: an FL registered at a different hierarchy depth from the rest of its SCE Group. SCE "
         "Group: a group TIPS3 registers per item or equipment category that has no FL registered at Bokor."),
        ("PP2_TIPS3_Structure", "Recommendation",
         "A re-attachment point is recommended only when the FL's own parent chain already passes through a node at "
         "the depth its SCE Group is typically registered at; otherwise SME input is requested."),
        ("PP3_Parent_FL_Status", "(sheet)",
         "Only the SCE Functional Locations that need action or review. The combinations confirmed as needing no "
         "action are counted in the Summary and not listed."),
        ("PP3_Parent_FL_Status", "Parent SCE status",
         "From the approved register; else SAP SCE APPLICABLE; else the SCE identification master template "
         "(BOKOR_MASTER TEMPLATE - SCE LIST.xlsx). An SCE Group not in GOPS4.0 counts as Non-SCE."),
        ("PP3_Parent_FL_Status", "Recommended new parent FL",
         "For an active SCE FL under an inactive parent: the first ancestor above that parent that is active in SAP."),
        REMARKS_GLOSSARY,
    ]

    with pd.ExcelWriter(out, engine="openpyxl") as xl:
        write_output_sheet(xl, "PP1_FL_SCE_Assignment", fl1)
        write_output_sheet(xl, "PP1_Equipment_SCE_Assignment", eq1)
        write_output_sheet(xl, "PP1_Declassified_GOPS4", decl)
        write_output_sheet(xl, "PP1_Codes_Not_In_GOPS4", codes)
        write_output_sheet(xl, "PP2_TIPS3_Structure", pp2, {"Finding": 50, "Recommendation": 60})
        write_output_sheet(xl, "PP3_Parent_FL_Status", pp3, {"Finding": 50, "Recommendation": 55})
        write_summary(xl, status_rows, result_rows)
        write_glossary(xl, glossary)
    print(f"Written {out}")


# ---------------------------------------------------------------------------
# Group B - Pain Points 5-8
# ---------------------------------------------------------------------------
def build_group_b(out=None):
    out = out or OUT_DIR / "Group_B_Output_for_Evaluation.xlsx"

    d3 = {s: pd.read_excel(OUT_DIR / "D3_MIC_vs_SSPS_GOPS4.xlsx", sheet_name=s)
          for s in ["Summary", "SCE_Group_MIC_Mismatch", "Missing_MIC_Coverage", "MIC_Declassified_Group"]}
    d6 = pd.read_excel(OUT_DIR / "D6_MIC_TaskList_PS_Matching.xlsx", sheet_name="MIC_Task_Validation")
    d9 = {s: pd.read_excel(OUT_DIR / "D9_SSPS_vs_GOPS4.xlsx", sheet_name=s)
          for s in ["Summary", "SSPS_Group_Status", "Contradicting_SSPS_Tasks", "GOPS4_Groups_No_SSPS"]}
    d8b = {s: pd.read_excel(OUT_DIR / "D8b_MIC_Result_vs_Specification.xlsx", sheet_name=s)
           for s in ["Summary", "Out_Of_Spec_Accepted", "YesNo_Result_Not_Y"]}

    # ---- PP5
    m = d3["SCE_Group_MIC_Mismatch"]
    wrong = m["resolution"].eq("likely_mic_assignment_wrong")
    mism = pd.DataFrame({
        "Functional Location": m["Functional Location"],
        "Equipment": m["EQ at WO Hdr"],
        "Work Order": m["Order"],
        "Order created on": pd.to_datetime(m["Created on"], errors="coerce").dt.date,
        "MIC": m["MIC"],
        "MIC Name": m["MIC Name"],
        "SCE Group of the FL (SAP)": m["SCE Grp - FL"],
        "SCE Group of the MIC": m["SCE Grp - MIC"],
        "SCE Group in approved register": m["approved_register_sce_group"],
        "Finding": wrong.map({True: "MIC belongs to another SCE Group; the register confirms the FL's SCE Group",
                              False: "MIC and FL SCE Groups differ; the FL has no register entry"}),
        "Recommendation": m["recommendation"].str.strip(),
        "Status": wrong.map({True: "Correct the MIC / task list", False: PCSB_REVIEW}),
        "Source (approved register document, page)": m["source"],
    })
    cov = d3["Missing_MIC_Coverage"]
    coverage = pd.DataFrame({
        "SCE Group": cov["sce_group"],
        "Finding": "No MIC recorded against this SCE Group in the 2024-2025 MIC report, although SCE FLs of the "
                   "group exist at Bokor",
        "Standard": cov["standard"],
        "Assurance task (excerpt)": cov["assurance_task_excerpt"],
        "Required frequency (months)": cov["months"],
        "Source (document, page)": cov["source"],
    })

    md = d3["MIC_Declassified_Group"]
    mic_decl = pd.DataFrame({
        "Functional Location": md["Functional Location"],
        "Equipment": md["EQ at WO Hdr"],
        "Work Order": md["Order"],
        "Inspection Lot": md["Inspection Lot"],
        "Order created on": pd.to_datetime(md["Created on"], errors="coerce").dt.date,
        "MIC": md["MIC"],
        "MIC Name": md["MIC Name"],
        "PS Req": md["PS Req"],
        "SCE Group of the FL (SAP)": md["SCE Grp - FL"],
        "SCE Group of the MIC": md["SCE Grp - MIC"],
        "Finding": "MIC recorded for an SCE Group no longer in GOPS4.0 (no longer SCE)",
        "Recommendation": md["recommendation"],
        "Status": "Remove from the SCE assurance task list",
    })
    st = d9["SSPS_Group_Status"]
    contra = st[st["Status in GOPS4.0"] == "Not in GOPS4.0"]
    ssps_gops4 = pd.DataFrame({
        "SCE Group": contra["SCE Group"],
        "SSPS group name": contra["SSPS group name"],
        "Finding": "The Bokor SSPS (prepared under GOPS3) still sets assurance tasks for this group as an SCE; the "
                   "group is not among the 45 SCE Groups of the latest GOPS4.0, so it is no longer SCE",
        "SSPS document": contra["SSPS document"],
        "SSPS pages": contra["SSPS pages"],
        "Applicable SSPS assurance tasks": contra["  of which applicable at Bokor"],
        "Register SCE FLs (now Non-SCE)": contra["Register SCE FLs with this group"],
        "MIC records 2024-2025": contra["MIC records 2024-2025 of this group"],
        "GOPS4.0 basis": contra["GOPS4.0 reference"],
        "Status": "PCSB to withdraw or update the SSPS",
    })
    no_ssps = d9["GOPS4_Groups_No_SSPS"]
    missing_doc = no_ssps[no_ssps["Finding"].str.startswith("Bokor SSPS exists")]

    # ---- PP6
    rec_ps = {"Should Be Marked as Required": "Y", "Incorrectly Marked as Required": "N"}
    ps = pd.DataFrame({
        "SCE Group": d6["sce_group"],
        "MIC": d6["mic"],
        "MIC Name": d6["mic_name"],
        "Current PS Req": d6["ps_req"],
        "Finding": d6["finding"],
        "Recommended PS Req": [rec_ps.get(f, cur) for f, cur in zip(d6["finding"], d6["ps_req"])],
        "Matched assurance task": d6["matched_assurance_task"],
        "Standard": d6["matched_source"],
        "Source (document, page)": d6["matched_source_citation"],
        "Match confidence": d6["match_confidence"],
        "Same result in the 3 runs": d6["consistent_across_runs"],
        "GOPS4.0 rule": d6["gops4_rule"].fillna(""),
    })
    order = {"Should Be Marked as Required": 0, "Incorrectly Marked as Required": 1}
    ps = ps.iloc[ps["Finding"].map(order).fillna(2).argsort(kind="stable")]

    # ---- PP8 (in progress): accepted results outside their own specification (agreed with PCSB, 9 Oct 2026)
    rec_cols = {"Order": "Work Order", "Inspection Lot": "Inspection Lot", "Functional Location": "Functional Location",
                "SCE Grp - FL": "SCE Group of the FL", "EQ at WO Hdr": "Equipment", "MIC": "MIC",
                "MIC Name": "MIC Name", "Specification": "Specification (AB)", "Result": "Result (AC)",
                "ResVal": "ResVal (AD)", "UD": "Usage decision", "Created on": "Result date", "Finding": "Finding",
                "Notifications on the FL on/after the result date": "Notifications on the FL on/after the result date"}
    oos = pd.concat([d8b["Out_Of_Spec_Accepted"], d8b["YesNo_Result_Not_Y"]], ignore_index=True)
    lots = oos[list(rec_cols)].rename(columns=rec_cols)
    lots["Result date"] = pd.to_datetime(lots["Result date"], errors="coerce").dt.date
    lots["Status"] = lots["Finding"].map(lambda f: "PCSB to confirm what '0' means" if f.startswith("YES / NO")
                                         else "PCSB to confirm the follow-up")

    status_rows = [
        ("5. MIC against SSPS and GOPS4.0", "Completed",
         "PP5_MIC_SCE_Group_Mismatch, PP5_MIC_Declassified_Group, PP5_Missing_MIC_Coverage, PP5_SSPS_vs_GOPS4"),
        ("6. Performance standards in MIC / task lists", "Completed", "PP6_MIC_PS_Validation"),
        ("7. RBI interval against SCE maintenance plan schedule", "In progress", "(none yet)"),
        ("8. Rejected inspection lots against notification history", "In progress - interim output: accepted "
         "results outside their specification", "PP8_Result_Outside_Spec"),
    ]
    fc = ps["Finding"].value_counts()
    result_rows = [
        ("5. MIC against SSPS / GOPS4.0", "MIC records in the 2024-2025 MIC report",
         metric_value(d3["Summary"], "MIC Report rows"), ""),
        ("", "  MIC records with both an FL and a MIC SCE Group",
         metric_value(d3["Summary"], "Total MIC records comparable"), ""),
        ("", "    - MIC carries the FL's SCE Group", metric_value(d3["Summary"], "correctly assigned"), "(not listed)"),
        ("", "    - MIC of an SCE Group no longer in GOPS4.0 (no longer SCE)", len(mic_decl),
         "PP5_MIC_Declassified_Group"),
        ("", "    - MIC of another SCE Group", len(mism), "PP5_MIC_SCE_Group_Mismatch"),
        ("", "      register confirms the FL's group - correct the MIC", int(wrong.sum()), "PP5_MIC_SCE_Group_Mismatch"),
        ("", "      FL has no register entry - PCSB review", int((~wrong).sum()), "PP5_MIC_SCE_Group_Mismatch"),
        ("", "  SCE Groups requiring a task every 24 months or less with no MIC in 2024-2025",
         coverage["SCE Group"].nunique(), "PP5_Missing_MIC_Coverage"),
        ("", "    - assurance tasks behind them", len(coverage), "PP5_Missing_MIC_Coverage"),
        ("", "  Bokor SSPS documents", len(st), ""),
        ("", "    - in line with GOPS4.0 (group maintained as SCE)", len(st) - len(contra), "(not listed)"),
        ("", "    - contradicting GOPS4.0 (group no longer SCE)", len(ssps_gops4), "PP5_SSPS_vs_GOPS4"),
        ("", "      applicable assurance tasks in them", int(ssps_gops4["Applicable SSPS assurance tasks"].sum()),
         "PP5_SSPS_vs_GOPS4"),
        ("", "  GOPS4.0 SCE Groups with an SSPS listed but not supplied: " + ", ".join(missing_doc["SCE Group"]),
         len(missing_doc), ""),
        ("6. PS flag on MICs", "MICs checked against their SCE Group's assurance tasks", len(ps), "PP6_MIC_PS_Validation"),
        ("", "  PS Req flag correct", int(fc.get("Correctly Assigned", 0)), "PP6_MIC_PS_Validation"),
        ("", "  Should be marked as required (Y)", int(fc.get("Should Be Marked as Required", 0)), "PP6_MIC_PS_Validation"),
        ("", "  Incorrectly marked as required (should be N)", int(fc.get("Incorrectly Marked as Required", 0)),
         "PP6_MIC_PS_Validation"),
        ("", "  Same result in the 3 matching runs", int(ps["Same result in the 3 runs"].eq("Yes").sum()),
         "PP6_MIC_PS_Validation"),
        ("", "  MICs of SCE Groups no longer in GOPS4.0 (PS Req = N is correct)", int(ps["GOPS4.0 rule"].ne("").sum()),
         "PP6_MIC_PS_Validation"),
        ("7. RBI interval", "In progress - no output in this workbook yet", "", ""),
        ("8. Rejected inspection lots", "In progress - interim output", "", ""),
        ("", "  MIC records in the 2024-2025 MIC report", metric_value(d8b["Summary"], "MIC records in the MIC report"),
         ""),
        ("", "    - lots with a rejected usage decision", metric_value(d8b["Summary"], "Lots with a rejected usage"), ""),
        ("", "  Numeric result outside its specification, accepted", len(d8b["Out_Of_Spec_Accepted"]),
         "PP8_Result_Outside_Spec"),
        ("", "    - inspection lots", d8b["Out_Of_Spec_Accepted"]["Inspection Lot"].nunique(), "PP8_Result_Outside_Spec"),
        ("", "    - Functional Locations", d8b["Out_Of_Spec_Accepted"]["Functional Location"].nunique(),
         "PP8_Result_Outside_Spec"),
        ("", "  YES / NO check recorded as '0' (not Y), accepted", len(d8b["YesNo_Result_Not_Y"]),
         "PP8_Result_Outside_Spec"),
        ("", "    - inspection lots", d8b["YesNo_Result_Not_Y"]["Inspection Lot"].nunique(), "PP8_Result_Outside_Spec"),
        ("", "    - Functional Locations", d8b["YesNo_Result_Not_Y"]["Functional Location"].nunique(),
         "PP8_Result_Outside_Spec"),
        ("", "  Flagged records with a notification on the FL on/after the result date",
         int((lots["Notifications on the FL on/after the result date"] > 0).sum()), "PP8_Result_Outside_Spec"),
    ]

    glossary = [
        ("PP5_MIC_SCE_Group_Mismatch", "SCE Group in approved register",
         "The FL's SCE Group in the approved register. Where it matches the FL's own SAP SCE Group, the MIC is the "
         "record to correct."),
        ("PP5_MIC_SCE_Group_Mismatch", "Source (approved register document, page)",
         "The sign-off document and PDF page holding the FL's register entry. Blank where the FL has no entry."),
        ("PP5_Missing_MIC_Coverage", "(sheet)",
         "SCE Groups whose Bokor SSPS (or GOPS4.0) requires an assurance task at least every 24 months, with SCE FLs at "
         "Bokor, but no MIC anywhere in the 2024-2025 MIC report. Tasks the Bokor SSPS marks not applicable are not "
         "counted; where onshore and offshore intervals are given, the offshore interval is used."),
        ("PP6_MIC_PS_Validation", "Finding",
         "Should Be Marked as Required: PS Req = N, but the MIC implements an assurance task of its SCE Group (high "
         "confidence). Incorrectly Marked as Required: PS Req = Y, but no assurance task of its SCE Group matches. "
         "Correctly Assigned: the flag agrees with the standard."),
        ("PP6_MIC_PS_Validation", "Matched assurance task / Source",
         "The applicable Bokor SSPS or GOPS4.0 task the MIC implements, with its document and page."),
        ("PP6_MIC_PS_Validation", "Same result in the 3 runs",
         "The matching was run three times; a finding is reported only when all three runs agree."),
        ("PP6_MIC_PS_Validation", "GOPS4.0 rule",
         "Filled for MICs of an SCE Group not in GOPS4.0: the group is no longer SCE, so the MIC is not a "
         "performance-standard task and PS Req = N is correct, whatever the GOPS3-era SSPS says."),
        ("PP5_MIC_Declassified_Group", "(sheet)",
         "MIC records whose SCE Group is not among the 45 SCE Groups of GOPS4.0. The group is no longer SCE, so the MIC "
         "should come off the SCE assurance task list; non-SCE maintenance stays in normal PM (GOPS4.0 page 4)."),
        ("PP5_SSPS_vs_GOPS4", "(sheet)",
         "Bokor SSPS documents (2022, prepared under GOPS3) that still set assurance tasks for an SCE Group that GOPS4.0 "
         "(March 2026) no longer has. GOPS4.0 is the latest standard, so the SSPS contradicts it for that group. Task "
         "and frequency differences within groups GOPS4.0 keeps are not listed: GOPS4.0 section 1.4 (page 11) allows "
         "them with endorsement."),
        ("PP8_Result_Outside_Spec", "(sheet)",
         "MIC records (MIC Report 2024_2025.xlsx) accepted (ResVal = A) although the result does not meet the "
         "specification: a numeric result outside its limit, or a YES / NO check recorded as '0'. Notifications are "
         "counted on the same Functional Location from the result date (extract ends 30 Dec 2025)."),
        REMARKS_GLOSSARY,
    ]

    with pd.ExcelWriter(out, engine="openpyxl") as xl:
        write_output_sheet(xl, "PP5_MIC_SCE_Group_Mismatch", mism, {"Recommendation": 70})
        write_output_sheet(xl, "PP5_MIC_Declassified_Group", mic_decl, {"Recommendation": 70})
        write_output_sheet(xl, "PP5_Missing_MIC_Coverage", coverage, {"Finding": 50, "Assurance task (excerpt)": 70})
        write_output_sheet(xl, "PP5_SSPS_vs_GOPS4", ssps_gops4, {"Finding": 60})
        write_output_sheet(xl, "PP6_MIC_PS_Validation", ps, {"Matched assurance task": 70})
        write_output_sheet(xl, "PP8_Result_Outside_Spec", lots, {"Finding": 60})
        write_summary(xl, status_rows, result_rows)
        write_glossary(xl, glossary)
    print(f"Written {out}")


if __name__ == "__main__":
    # optional: an output folder, e.g. when the default files are open in Excel
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT_DIR
    build_group_a(folder / "Group_A_Output_for_Evaluation.xlsx")
    build_group_b(folder / "Group_B_Output_for_Evaluation.xlsx")
