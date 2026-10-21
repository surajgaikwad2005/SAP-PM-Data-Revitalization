"""
Write the single output workbook: outputs/BOM_Agent_Output.xlsx

Sheets:
  Overview             plain-English executive summary & KPI dashboard
  Draft BOMs           proposed BOM lines built from vendor SPIR forms
  P4 - BOMs to build   ranked work list by asset criticality & risk
  P2 - Duplicate materials duplicate material pairs to merge & retire
  P1 - Category to fix inconsistent item categories to standardize
  P3 - UOM and Qty     unit-of-measure & quantity integrity audit
  Floating materials   orphan spare parts linked to parent equipment

Styling is deliberately light: a title row, a bold header, frozen panes,
sensible column widths, and a yellow fill on the rows that need client
validation - nothing else is coloured, so the highlight means one thing only
and the eye goes straight to the rows that need an answer.
"""
from __future__ import annotations
import pandas as pd
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import config as C

_TITLE = Font(bold=True, size=13, color="1F3B5C")
_SUBTITLE = Font(italic=True, size=9, color="5A5A5A")
_HEAD = Font(bold=True, color="FFFFFF", size=10)
_HEAD_FILL = PatternFill("solid", fgColor="1F3B5C")
# The row fill every sheet shares: the rows that need client validation.
_YELLOW = PatternFill("solid", fgColor="FFEB9C")
# Draft BOMs sheet only: every row of an equipment that has no BOM at all in the
# current BOM extract, so the drafts that fill a gap stand out from the drafts
# that sit beside an existing BOM.
_GREEN = PatternFill("solid", fgColor="C6EFCE")
DRAFT_READY_KEY = ("Rows highlighted in green are equipment for which a draft BOM can be built now "
                   "from the vendor SPIR held - see the Draft BOMs sheet.")
NO_BOM_KEY = ("Rows highlighted in green belong to equipment that has NO BOM in the current "
              "BOM extract - these drafts fill a gap.")
# Drawn above the first row of each new block, so one machine's parts are
# visibly separate from the next machine's.
_BLOCK_RULE = Border(top=Side(style="medium", color="1F3B5C"))

CONFIDENCE_KEY = (
    "Confidence:   HIGH = the evidence settles it - SAP's own records, or an independent "
    "document, say so   |   MEDIUM = the Agent's best read of the evidence, worth checking "
    "before acting   |   LOW = not enough evidence to decide; an engineer has to look.      "
    "Rows highlighted in yellow require client validation."
)

# Friendly Title Case Column Mapping for Client Presentation
_RENAME_MAP = {
    "rank": "Serial Number",
    "priority_tier": "Priority Level",
    "confidence": "Confidence Score",
    "equipment": "Equipment Tag / ID",
    "bom_level": "BOM Level",
    "sap_equipment": "SAP Equipment No.",
    "equipment_description": "Equipment Description",
    "description": "Description",
    "functional_location": "Functional Location",
    "criticality": "Criticality (ABC)",
    "safety_critical": "Safety Critical (SCE)?",
    "inactive": "Inactive in SAP?",
    "bom_optional_ptg_type": "PTG Waiver Type",
    "note": "Remark",
    "material": "Material No.",
    "keep_material": "Keep Material No.",
    "keep_description": "Master Description",
    "retire_materials": "Duplicate Material(s) to Retire",
    "count": "Duplicate Count",
    "basis": "Reason",
    "categories_seen": "Current SAP Categories",
    "recommended": "Recommended Category",
    "why": "Reason for Recommendation",
    "finding": "Remark",
    "detail": "Reason",
    "suggested_equipment": "Linked Parent Equipment",
    "how_we_know": "Reason",
    "evidence": "Checked Against",
    "trail": "Source Evidence Trail",
    "needs_pcsb_confirmation": "Requires Client Validation?",
    "vendor_tag": "Vendor Tag No.",
    "item": "Item No.",
    "component_description": "Component Spare Description",
    "quantity": "Quantity",
    "uom": "Unit of Measure (UOM)",
    "proposed_item_category": "Proposed Category",
    "material_number": "MESC / Material No.",
    "material_action": "Material Master Action",
    "manufacturer": "Manufacturer / Brand",
    "part_number": "Manufacturer Part No.",
    "material_spec": "Material Specification",
    "source_document": "Source PDF File",
    "source_page": "Source Page No.",
    "spir_sheet": "SPIR Sheet No.",
    "spir_type": "Document Type",
    "existing_bom": "Existing BOM Status",
    "seen_on_pages": "Also Seen on Page(s)",
}

# The Draft BOMs sheet lists every spare part of a machine under that machine.
# These columns describe the MACHINE, so they are written once per block rather
# than repeated against each of its parts.
_DRAFT_REPEAT_COLS = ("equipment_description", "functional_location",
                      "existing_bom", "vendor_tag")


def _sheet(writer, name: str, title: str, df: pd.DataFrame, sources: list[str], basis: str,
           group_by: str | None = None, repeat_cols: tuple[str, ...] = (),
           highlight=None, highlight_note: str = "") -> None:
    """Write one sheet.

    group_by / repeat_cols make a long sheet readable.  Where many rows belong to
    one parent (every spare part of one machine), the parent's details are
    identical on every row and the reader cannot see where one block ends and the
    next begins.  So the columns named in repeat_cols are written only on the
    first row of each block, and a rule is drawn above each new block.  The
    grouping key itself is always written on every row, so sorting and filtering
    still work and no row loses its identity.

    highlight is an optional row test: rows it accepts are filled green, and
    highlight_note is added to the sheet note to say what the green means.
    """
    df = df.copy()
    # Decided before any column is dropped or blanked below.
    marked = [bool(highlight(r)) for r in df.to_dict("records")] if highlight else []

    # Confidence is scored numerically so rows can be ranked, but a number invites
    # false precision - nobody can act on the difference between 0.80 and 0.85.
    # The sheet shows the band instead.  Rows keep the order the numbers gave them,
    # because the modules sorted before handing the frame over.
    if "confidence" in df.columns:
        df["confidence"] = df["confidence"].map(C.confidence_band)

    # A column with the same value on every row tells the reader nothing row by
    # row - it is a fact about the whole sheet.  State it once in the note and
    # take the column back, rather than repeating it hundreds of times.
    # Confidence is exempt: it is a per-row rating a reader looks for, and a sheet
    # missing it reads as "unrated" rather than "all the same".
    constants: list[str] = []
    if len(df) > 1:
        for col in list(df.columns):
            if col in (group_by, "confidence"):
                continue
            vals = df[col].astype(str).unique()
            if len(vals) == 1 and vals[0].strip():
                constants.append(f"{_RENAME_MAP.get(col, col)}: {vals[0]}")
                df = df.drop(columns=col)

    display_df = df.rename(columns=_RENAME_MAP)
    display_df.to_excel(writer, sheet_name=name, index=False, startrow=3)
    ws = writer.sheets[name]

    if C.DEMO_MODE:
        title += f"   [DEMO MODE - Sample of {C.DEMO_SIZE} equipment]"

    ws["A1"] = title
    ws["A1"].font = _TITLE
    ws["A2"] = "Input File(s):   " + "     |     ".join(sources)
    ws["A2"].font = _SUBTITLE
    ws["A3"] = ("Basis & Rules:   " + basis
                + ("   |   Every row on this sheet:   " + "   |   ".join(constants) if constants else "")
                + ("   |   " + CONFIDENCE_KEY if "confidence" in df.columns else "")
                + ("   |   " + highlight_note if highlight_note and any(marked) else ""))
    ws["A3"].font = _SUBTITLE

    # Header styling & column widths
    for col_idx, col_name in enumerate(display_df.columns, start=1):
        cell = ws.cell(row=4, column=col_idx)
        cell.font = _HEAD
        cell.fill = _HEAD_FILL
        cell.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")

        # Calculate dynamic column width
        max_len = max(len(str(col_name)), int(display_df[col_name].astype(str).str.len().quantile(0.9)))
        width = max(14, min(65, max_len + 4))
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    # Row shading & text alignment.  Rows are NOT coloured by confidence: the
    # only highlight is yellow on a row the client still has to validate, so
    # the colour carries exactly one meaning.  If EVERY row needs validating,
    # the fact is in the note above and painting the whole sheet yellow would
    # only make it harder to read - so nothing is painted.
    has_pcsb = "needs_pcsb_confirmation" in df.columns
    group_vals = df[group_by].astype(str).tolist() if group_by in df.columns else []
    prev_group = None

    for row_idx, orig_row in enumerate(df.itertuples(index=False), start=5):
        fill = None
        if has_pcsb and str(getattr(orig_row, "needs_pcsb_confirmation", "")).lower().startswith("yes"):
            fill = _YELLOW
        if marked and marked[row_idx - 5]:
            fill = _GREEN

        # First row of a new block: draw a rule above it and let it carry the
        # repeated columns; later rows in the block leave those cells empty.
        new_block = False
        if group_vals:
            this_group = group_vals[row_idx - 5]
            new_block = this_group != prev_group
            prev_group = this_group

        for col_idx, val in enumerate(orig_row, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            col_key = df.columns[col_idx - 1]

            if group_vals and not new_block and col_key in repeat_cols:
                cell.value = None

            if fill:
                cell.fill = fill
            if new_block and row_idx > 5:
                cell.border = _BLOCK_RULE

            # Confidence is a band (High/Medium/Low), centred like the other
            # short, scannable columns.
            if col_key == "confidence":
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif col_key in ("rank", "count", "item", "priority_tier", "safety_critical", "inactive"):
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(vertical="center", wrap_text=True)

    ws.freeze_panes = "A5"
    if len(display_df.columns):
        ws.auto_filter.ref = (f"A4:{get_column_letter(len(display_df.columns))}"
                              f"{4 + len(display_df)}")


def _p2_overview(p2: dict) -> str:
    if not p2.get("material_master_available"):
        return "The material master was not available, so duplicate materials were not checked."
    ai = (f"{p2['groups_ai_judged']:,} further groups were confirmed by the Agent on wording."
          if p2["ai_step_run"] else
          f"{p2['look_alike_pairs_needing_ai']:,} near-duplicate pairs (close but not identical "
          f"descriptions) were found and are waiting for the Agent's judgement - that step was "
          f"switched off for this run.")
    return (f"Run on the material master for plant M014: {p2['materials_compared']:,} materials compared. "
            f"{p2['groups_confirmed_high']:,} groups are confirmed duplicates (same description and same "
            f"part number), with {p2['material_numbers_to_retire']:,} material numbers to retire. "
            f"{p2['groups_same_description_part_number_on_some'] + p2['groups_same_part_number_wording_differs']:,} "
            f"groups are probable (Medium) and {p2['groups_same_description_no_part_number']:,} share a "
            f"description with no part number to confirm it (Low). {ai}")


def _overview(results: dict) -> pd.DataFrame:
    rows = [
        ("P4  Equipment Prioritization",
         f"{results['p4']['equipment_needing_a_bom']:,} equipment missing BOMs (ranked SCE -> C1 -> C2 -> C3). "
         f"{results['p4']['inactive_in_the_list']:,} marked INACTIVE. "
         f"{results['p4']['bom_optional_per_ptg_3_5_4']:,} flagged for PTG 12.05.04 s3.5.4 optional waiver."),
        ("P2  Duplicate Material Cleanup",
         _p2_overview(results["p2"])),
        ("P1  Item Category Consistency",
         f"{results['p1']['wrong_kind_assembly_vs_part']:,} materials are typed as the wrong KIND - an assembly "
         f"treated as a part or the reverse - affecting {results['p1']['wrong_kind_bom_lines_affected']:,} BOM "
         f"lines; settled by the SAP material type, so a majority cannot overrule it. A further "
         f"{results['p1']['materials_with_conflicting_category']:,} are typed inconsistently across BOMs "
         f"({results['p1']['auto_resolved']:,} auto-resolved, {results['p1']['left_for_pcsb']:,} for PCSB sign-off)."),
        ("P3  UOM & Quantity Audit",
         f"{results['p3']['lines_without_unit']:,} lines missing UOM and "
         f"{results['p3']['lines_without_quantity']:,} with zero/missing qty (SAP enforces both at entry, so "
         f"these stay clean). The findings are elsewhere: "
         f"{results['p3']['identical_equipment_quantity_disagreements']:,} components where identical equipment "
         f"disagree on the quantity ({results['p3']['of_those_a_majority_decides']:,} decided by majority, "
         f"{results['p3']['of_those_tied_for_engineer']:,} tied), "
         f"{results['p3']['quantity_outliers_to_check']:,} quantity outliers to check, and "
         f"{results['p3']['duplicate_unit_codes']:,} pairs of duplicate unit codes."
         + (f" Units were also checked against the material master: "
            f"{results['p3']['materials_checked_against_material_master']:,} materials on "
            f"{results['p3']['lines_checked_against_material_master']:,} BOM lines, of which "
            f"{results['p3']['materials_unit_differs_from_material_master']:,} materials "
            f"({results['p3']['lines_unit_differs_from_material_master']:,} lines) carry a different unit. "
            f"Assemblies are not in the material master; "
            f"{results['p3']['assemblies_not_counted_in_set']:,} of them are not counted in SET."
            if results['p3'].get('material_master_available') else
            " The material master was not available, so units were not checked against it.")),
        ("Floating Materials Linker",
         f"{results['floating']['floating_materials_bokor']:,} orphan materials analyzed. "
         f"{results['floating']['A_already_on_a_bom']:,} already on BOM, "
         f"{results['floating']['B_C_high_confidence_link']:,} linked via 10-yr Work Order history, "
         f"{results['floating']['D_ai_picked_from_short_list']:,} Agent candidate picks; "
         f"{results['floating']['E_left_for_engineer_review']:,} for engineer review."),
        ("Draft BOM Auto-Generation",
         f"A worked example, not coverage: {results['draft_bom']['draft_bom_lines']:,} parts drafted "
         f"under {results['draft_bom']['draft_assembly_nodes']} proposed assemblies for "
         f"{results['draft_bom']['equipment_linked']} equipment, read off "
         f"{results['draft_bom']['spir_pages_held']} vendor SPIR pages. "
         f"{results['draft_bom']['equipment_linked_in_backlog']} of them are among the "
         f"{results['p4']['equipment_needing_a_bom']:,} equipment awaiting a BOM (highlighted green on the "
         f"Draft BOMs sheet); the other "
         f"{results['draft_bom']['equipment_linked'] - results['draft_bom']['equipment_linked_in_backlog']} "
         f"already have a BOM, so their drafts are a vendor reference to compare it against. The pipeline "
         f"works end to end, but the vendor documents for the rest are still outstanding."),
        ("BOM Structure",
         f"{results['structure']['repeated_assembly_groups']:,} cases where several equipment of the "
         f"same model each carry their own assembly for the same thing "
         f"({results['structure']['assembly_numbers_involved']:,} assembly numbers that could become "
         f"fewer). {results['structure']['equipment_with_no_assembly_node']:,} equipment hold their "
         f"parts directly with no assembly grouping - an open question for PCSB, not a fault."),
        ("Data Dependencies Outstanding",
         f"Per-equipment vendor SPIR documents and MRP inventory extracts are outstanding from PCSB. "
         f"Two sources we already hold cannot be used as they stand: the vendor SPIR sheets received "
         f"so far leave the installed-quantity column blank on every row, and the equipment "
         f"classification extract covers "
         f"{results['classification']['equipment_classified']:,} equipment but only "
         f"{results['classification']['percent_filled']}% of its "
         f"{results['classification']['characteristic_values_held']:,} characteristic values are "
         f"actually filled in - the rest read '?'. Both would add real checking power once populated."),
    ]
    return pd.DataFrame(rows, columns=["Process Area", "Executive Summary of Findings"])


def write(p4_df, p2_df, p1_df, p3_df, floating_df, results: dict, draft_df=None, struct_df=None):
    with pd.ExcelWriter(C.OUTPUT_WORKBOOK, engine="openpyxl") as writer:
        _sheet(writer, "Overview", "BOM Agent - Master Results Overview",
               _overview(results), C.SOURCES["overview"], C.BASIS["overview"])
        if draft_df is not None and len(draft_df):
            _sheet(writer, "Draft BOMs",
                   f"Draft BOMs - Worked Example from the Vendor Documents Held So Far "
                   f"({results['draft_bom']['equipment_linked']} equipment: "
                   f"{results['draft_bom']['equipment_linked_in_backlog']} with no BOM today, "
                   f"{results['draft_bom']['equipment_linked'] - results['draft_bom']['equipment_linked_in_backlog']}"
                   f" with an existing BOM to compare)",
                   draft_df, C.SOURCES["draft_bom"], C.BASIS["draft_bom"],
                   group_by="sap_equipment", repeat_cols=_DRAFT_REPEAT_COLS,
                   highlight=lambda r: str(r.get("existing_bom", "")).startswith("no BOM today"),
                   highlight_note=NO_BOM_KEY)
        # Equipment on the worklist that already have a draft on the Draft BOMs sheet.
        drafted = set()
        if draft_df is not None and len(draft_df):
            drafted = {str(e).strip() for e in draft_df["sap_equipment"] if str(e).strip()}
        _sheet(writer, "P4 - BOMs to build",
               "Equipment BOM Creation Priority Worklist",
               p4_df, C.SOURCES["p4"], C.BASIS["p4"],
               highlight=lambda r: str(r.get("equipment", "")).strip() in drafted,
               highlight_note=DRAFT_READY_KEY)
        _sheet(writer, "P2 - Duplicate materials",
               "Duplicate Material Masters to Consolidate & Retire - Material Master, Plant M014",
               p2_df, C.SOURCES["p2"], C.BASIS["p2"])
        _sheet(writer, "P1 - Category to fix",
               "Inconsistent SAP Item Categories to Standardize",
               p1_df, C.SOURCES["p1"], C.BASIS["p1"])
        if struct_df is not None and len(struct_df):
            _sheet(writer, "BOM structure",
                   "How the Parts Lists Are Built - Assembly Structure Review",
                   struct_df, C.SOURCES["structure"], C.BASIS["structure"])
        _sheet(writer, "P3 - UOM and Qty",
               "BOM Material Quantity & Unit of Measure Audit",
               p3_df, C.SOURCES["p3"], C.BASIS["p3"])
        _sheet(writer, "Floating materials",
               "Orphan Floating Materials Linked to Equipment",
               floating_df, C.SOURCES["floating"], C.BASIS["floating"])
    return C.OUTPUT_WORKBOOK
