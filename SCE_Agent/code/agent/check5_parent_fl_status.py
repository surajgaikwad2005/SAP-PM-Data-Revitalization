"""
Check 5 (Group A) - Equipment vs parent FL SCE status: relocation / reassignment
------------------------------------------------------------------------------------
Equipment has no SCE field of its own in any SAP extract in scope - it
inherits its SCE status from its own Functional Location. So "equipment's
and parent FL SCE status" resolves to two linked checks:

  1. FL-level: does each FL's effective SCE status agree with its own
     parent (Superior FunctLoc.)'s effective SCE status? Flag only the
     cases that actually indicate a structural problem:
       - child FL is SCE, immediate parent is explicitly Non-SCE
       - child FL is SCE, immediate parent is being made Inactive/Deleted
       - child FL is SCE, immediate parent's status is still unassessed
       - child FL is SCE and active, immediate parent is INAC in SAP's
         own System status (orphaning risk the register alone misses)
       - child FL is SCE but is itself INAC in SAP (SCE registration on
         a deactivated FL - confirm decommissioned or reactivate)
     (Two SCE FLs simply having *different* SCE Group codes is NOT
     flagged - a child SCE system sitting under a different SCE parent
     system is normal, not a defect.)

     "Unassessed" parents are split using the SCE identification master
     template (BOKOR_MASTER TEMPLATE - SCE LIST.xlsx, sheet BOKOR ASSET
     HIERARCHY): its Q1-Q8 questionnaire is only applied to "FL WITH EQ"
     / "FL WITHOUT EQ" rows, so a parent typed "FL" (pure grouping node,
     e.g. ".SD" shutdown system, ".CS" control system) with no SCE answer
     is unassessed BY DESIGN of the bottom-up method, not a gap. Where
     the template does record SCE = No for an FL that neither the
     register nor SAP covers, that is used as its NON_SCE status. Only
     parents missing from the template entirely remain parent_unassessed.

  2. Equipment-level: every equipment record rolled up to its FL's
     finding (from this check and from Check 1's D1), so the output is
     directly actionable - "this equipment needs re-location/re-
     assignment because its FL is <reason>".

  3. Concrete relocation proposal: for the unambiguous cases (parent
     being made inactive/deleted), `suggest_relocation_target()` walks
     up the Superior FunctLoc. chain past the bad parent and proposes
     the first ancestor FL that is itself NOT inactive/deleted as the
     new parent - "recommends for re-location", not just flags that
     relocation is needed. Deliberately NOT extended to the "Non-SCE
     parent" review cases - those are usually already correct (bottom-
     up registration), so forcing a relocation suggestion there would
     be noise, not a proposal.

"Effective" SCE status per FL is the ground-truth-corrected view from
Check 1 (the approved register) where available, falling back to SAP's
own raw SCE APPLICABLE/SCE GROUP only where the register has no entry -
running this on raw SAP data alone would be checking against a field
that's 67% unassessed.

Output: Data exploration/output/D2_D5_Structure_Relocation_Reassignment.xlsx
  - Summary
  - FL_Hierarchy_Findings   (one row per FL with a structural problem)
  - Equipment_Rollup        (one row per affected equipment)

Run:
    python "code/agent/check5_parent_fl_status.py"
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
REGISTER_DB = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "sce_register.db"
TIPS3_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "tips3_extraction.xlsx"
GOPS4_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "gops4_sce_groups.xlsx"
SCE_TEMPLATE_FILE = ASSET_MASTER / "BOKOR SCE REPORT" / "BOKOR_MASTER TEMPLATE - SCE LIST.xlsx"
SCE_TEMPLATE_SHEET = "BOKOR ASSET HIERARCHY"
SCE_TEMPLATE_CITE = f"{SCE_TEMPLATE_FILE.name} (sheet '{SCE_TEMPLATE_SHEET}')"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "D2_D5_Structure_Relocation_Reassignment.xlsx"

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
    # SAP FL SCE overlay + hierarchy
    # ------------------------------------------------------------------
    fl = pd.read_excel(SAP_FL_FILE, sheet_name="Data", dtype=str)
    fl.columns = [c.strip() for c in fl.columns]
    fl["fl"] = fl["Functional Location"].map(norm_fl)
    fl["superior_fl"] = fl["Superior FunctLoc."].map(norm_fl)
    fl["sap_sce_group_code"] = fl["SCE GROUP"].str.extract(r"^([A-Z]{2,3}\d{3})", expand=False)
    fl = fl.drop_duplicates(subset="fl")
    print(f"SAP FL overlay: {len(fl):,} FLs")

    # ------------------------------------------------------------------
    # Hierarchy depth - needed to actually resolve, not just flag for
    # human confirmation, whether a "SCE under Non-SCE parent" FL really
    # sits at the level its SCE Group's peers typically register at.
    # ------------------------------------------------------------------
    def compute_depths(fl_df):
        parent = dict(zip(fl_df["fl"], fl_df["superior_fl"]))
        valid_fls = set(fl_df["fl"])
        depth_cache = {}

        def depth_of(f, seen=None):
            if f in depth_cache:
                return depth_cache[f]
            seen = seen or set()
            if f in seen or f not in valid_fls:
                return 0
            p = parent.get(f)
            if p is None or p not in valid_fls or p == f:
                depth_cache[f] = 0
                return 0
            d = 1 + depth_of(p, seen | {f})
            depth_cache[f] = d
            return d

        return {f: depth_of(f) for f in valid_fls}

    fl["depth"] = fl["fl"].map(compute_depths(fl))

    # ------------------------------------------------------------------
    # Ground truth register -> per-FL effective status
    # ------------------------------------------------------------------
    con = sqlite3.connect(REGISTER_DB)
    reg = pd.read_sql("select functional_location, action from sce_register", con)
    con.close()
    reg["fl"] = reg["functional_location"].map(norm_fl)
    reg[["gt_category", "gt_sce_group"]] = reg["action"].apply(lambda a: pd.Series(normalize_action(a)))
    # a handful of FLs have >1 register row (112, see Check 1) - keep the
    # first "has an SCE code" row if any, else the first row, so the
    # hierarchy check always has exactly one effective status per FL
    reg_sorted = reg.sort_values(by="gt_sce_group", key=lambda s: s.isna())  # non-null gt_sce_group first
    reg_dedup = reg_sorted.drop_duplicates(subset="fl", keep="first")

    fl = fl.merge(reg_dedup[["fl", "gt_category", "gt_sce_group"]], on="fl", how="left")

    # ------------------------------------------------------------------
    # SCE identification master template: node type (FL / FL WITH EQ /
    # FL WITHOUT EQ / EQ) and the SCE answer per FL. Used only where the
    # register and SAP are both silent.
    # ------------------------------------------------------------------
    tmpl = pd.read_excel(SCE_TEMPLATE_FILE, sheet_name=SCE_TEMPLATE_SHEET, header=1, dtype=str,
                         usecols=["FL/EQ NUMBER", "FL/EQ", "SCE"])
    tmpl["fl"] = tmpl["FL/EQ NUMBER"].map(norm_fl)
    tmpl = tmpl.dropna(subset=["fl"]).drop_duplicates(subset="fl")
    tmpl = tmpl.rename(columns={"FL/EQ": "tmpl_node_type", "SCE": "tmpl_sce"})
    tmpl["tmpl_node_type"] = tmpl["tmpl_node_type"].str.strip().str.upper()
    tmpl["tmpl_sce"] = tmpl["tmpl_sce"].str.strip().str.upper()
    fl = fl.merge(tmpl[["fl", "tmpl_node_type", "tmpl_sce"]], on="fl", how="left")
    fl["sap_inactive"] = fl["System status"].fillna("").str.upper().str.contains("INAC")
    print(f"FLs found in SCE master template: {fl['tmpl_node_type'].notna().sum():,}")

    # SCE Groups of the latest GOPS4 (Mar 2026): a group not among them is no
    # longer classified as SCE (PCSB, 9 Oct 2026), so an FL registered SCE
    # under such a group is treated as Non-SCE here.
    current_gops4 = set(pd.read_excel(GOPS4_FILE)["sce_group"].dropna().str.strip().str.upper())

    def effective(row):
        if pd.notna(row["gt_category"]):
            cat = row["gt_category"]
            if cat in ("maintain", "classify", "relocate", "sce_other"):
                if str(row["gt_sce_group"]).strip().upper() not in current_gops4:
                    return "NON_SCE", None
                return "SCE", row["gt_sce_group"]
            if cat == "non_sce":
                return "NON_SCE", None
            if cat in ("inactive", "delete"):
                return cat.upper(), None
        sap_app = str(row["SCE APPLICABLE"]).strip().upper()
        if sap_app == "YES":
            if str(row["sap_sce_group_code"]).strip().upper() not in current_gops4 and pd.notna(row["sap_sce_group_code"]):
                return "NON_SCE", None
            return "SCE", row["sap_sce_group_code"]
        if sap_app == "NO":
            return "NON_SCE", None
        if row["tmpl_sce"] == "NO":
            return "NON_SCE", None
        return "UNASSESSED", None

    fl[["eff_status", "eff_group"]] = fl.apply(lambda r: pd.Series(effective(r)), axis=1)
    fl["eff_source"] = "SCE master template"
    fl.loc[fl["SCE APPLICABLE"].fillna("").str.strip().str.upper().isin(["YES", "NO"]), "eff_source"] = "SAP SCE APPLICABLE"
    fl.loc[fl["gt_category"].notna() & (fl["gt_category"] != "unclassified"), "eff_source"] = "Approved register"
    fl.loc[fl["eff_status"] == "UNASSESSED", "eff_source"] = None
    print("Effective status distribution:")
    print(fl["eff_status"].value_counts())

    # ------------------------------------------------------------------
    # Hierarchy check: child SCE FL vs its immediate parent's effective status
    # ------------------------------------------------------------------
    status_by_fl = fl.set_index("fl")[["eff_status", "eff_group", "FunctLocDescrip.", "eff_source",
                                       "sap_inactive", "tmpl_node_type", "tmpl_sce"]]
    superior_by_fl = fl.set_index("fl")["superior_fl"]

    def suggest_relocation_target(start_fl, max_hops=6):
        """For a child FL whose immediate parent is inactive/deleted: walk
        up the Superior FunctLoc. chain (skipping the bad parent) and
        suggest the first ancestor that is itself NOT inactive/deleted -
        i.e. a stable FL to re-parent under. Any effective status other
        than INACTIVE/DELETE is an acceptable target (SCE, NON_SCE and
        UNASSESSED all still represent an FL that actually exists and
        isn't being removed - bottom-up registration means the target
        doesn't need to be SCE itself). An ancestor that is INAC in
        SAP's own System status is skipped too."""
        seen = set()
        current = superior_by_fl.get(start_fl)
        for _ in range(max_hops):
            if current is None or current in seen or current not in status_by_fl.index:
                return None
            seen.add(current)
            status = status_by_fl.loc[current, "eff_status"]
            if isinstance(status, pd.Series):
                status = status.iloc[0]
            if status not in ("INACTIVE", "DELETE") and not status_by_fl.loc[current, "sap_inactive"]:
                return current
            current = superior_by_fl.get(current)
        return None  # no stable ancestor found within max_hops - needs manual review

    def hierarchy_finding(row):
        if row["eff_status"] != "SCE":
            return None, None
        if row["sap_inactive"]:
            # The SCE FL itself is deactivated in SAP - relocation is moot
            # (usually the whole branch is INAC). Either the asset is
            # decommissioned and the SCE registration should be withdrawn,
            # or the FL should be reactivated.
            return "sce_fl_inactive_in_sap", "Medium"
        parent = row["superior_fl"]
        if parent not in status_by_fl.index:
            return "parent_fl_not_found", "Medium"
        parent_status = status_by_fl.loc[parent, "eff_status"]
        if isinstance(parent_status, pd.Series):  # duplicate index guard
            parent_status = parent_status.iloc[0]
        if status_by_fl.loc[parent, "sap_inactive"] and parent_status not in ("INACTIVE", "DELETE"):
            # Active SCE FL under a parent already INAC in SAP - orphaned
            # today, whatever the register says about the parent.
            return "parent_inactive_in_sap", "High"
        if parent_status == "NON_SCE":
            # NOT automatically a defect: the project's own objective is
            # to register SCE bottom-up ("map FL SCE Group registration
            # based on equipment's (bottom-up)"), and TIPS3's own SCE
            # Group definitions each specify their own registration
            # boundary (some "at system level", some "at item level" -
            # see Appendix D) - a child SCE FL under a non-SCE parent
            # area/system FL is frequently the *correct* structure, not
            # an error. Surfaced for SME review against the group's own
            # boundary spec, not asserted as wrong.
            return "parent_non_sce_review_boundary", "Low"
        if parent_status in ("INACTIVE", "DELETE"):
            # This one IS unambiguous regardless of registration level:
            # if the parent is removed/deactivated, the child SCE FL (and
            # its equipment) is orphaned - a real risk either way.
            return f"parent_{parent_status.lower()}", "High"
        if parent_status == "UNASSESSED":
            if status_by_fl.loc[parent, "tmpl_node_type"] == "FL":
                # Grouping node - the template's questionnaire is never
                # applied to these, by design of bottom-up registration.
                return "parent_grouping_node", "Informational"
            return "parent_unassessed", "Low"
        return None, None

    fl[["hier_finding", "hier_severity"]] = fl.apply(lambda r: pd.Series(hierarchy_finding(r)), axis=1)
    fl_findings = fl[fl["hier_finding"].notna()].copy()

    # ------------------------------------------------------------------
    # TIPS3 Appendix D's own registration-boundary text per SCE Group -
    # already extracted (same source Check 2 uses) - looked up directly
    # instead of telling the reviewer to go find it themselves.
    # ------------------------------------------------------------------
    tips3 = pd.read_excel(TIPS3_FILE, sheet_name="SCE_Group_Definitions")
    boundary_by_group = tips3.dropna(subset=["sce_group"]).drop_duplicates("sce_group").set_index("sce_group")[
        "system_level_boundaries"
    ]
    fl_findings["tips3_registration_boundary"] = fl_findings["eff_group"].map(boundary_by_group)

    # ------------------------------------------------------------------
    # Concrete relocation target for the unambiguous cases (parent being
    # made inactive/deleted) - the spec asks the agent to "recommend for
    # re-location", not just flag that relocation is needed.
    # ------------------------------------------------------------------
    needs_target = fl_findings["hier_finding"].isin(["parent_inactive", "parent_delete", "parent_inactive_in_sap"])
    fl_findings["suggested_relocation_target_fl"] = None
    fl_findings.loc[needs_target, "suggested_relocation_target_fl"] = fl_findings.loc[needs_target, "fl"].map(
        suggest_relocation_target
    )
    fl_findings["suggested_relocation_target_descrip"] = fl_findings["suggested_relocation_target_fl"].map(
        lambda t: status_by_fl.loc[t, "FunctLocDescrip."] if pd.notna(t) and t in status_by_fl.index else None
    )
    fl_findings["suggested_relocation_target_status"] = fl_findings["suggested_relocation_target_fl"].map(
        lambda t: status_by_fl.loc[t, "eff_status"] if pd.notna(t) and t in status_by_fl.index else None
    )

    # ------------------------------------------------------------------
    # Resolve "SCE under Non-SCE parent" directly, rather than asking a
    # human to go confirm the level - compare this FL's own hierarchy
    # depth against its SCE Group's typical (modal) depth among its
    # OTHER registered FLs (same peer-depth logic as Check 2's
    # Outlier_FL_Reattachment). >=2 levels off is treated as a CONFIRMED
    # placement issue, with a concrete relocation target suggested where
    # the FL's own ancestor chain already passes through the group's
    # typical depth. Within 1 level is resolved as genuinely-expected
    # bottom-up registration, not a defect - no SME review needed.
    # ------------------------------------------------------------------
    depth_by_fl = dict(zip(fl["fl"], fl["depth"]))
    parent_by_fl = dict(zip(fl["fl"], fl["superior_fl"]))
    descrip_by_fl = dict(zip(fl["fl"], fl["FunctLocDescrip."]))
    sce_fls_all = fl[fl["eff_status"] == "SCE"].dropna(subset=["eff_group"])
    peer_count_by_group = sce_fls_all.groupby("eff_group")["depth"].size()
    mode_depth_by_group = sce_fls_all.groupby("eff_group")["depth"].agg(lambda s: s.mode().iat[0])

    def suggest_target_by_depth(start_fl, mode_depth, max_hops=10):
        node = parent_by_fl.get(start_fl)
        for _ in range(max_hops):
            if node is None or node not in depth_by_fl:
                return None
            if depth_by_fl[node] == mode_depth:
                return node
            node = parent_by_fl.get(node)
        return None

    def resolve_boundary(row):
        grp = row["eff_group"]
        n_peers = peer_count_by_group.get(grp, 0)
        if pd.isna(grp) or n_peers < 5:
            return "insufficient_peer_data", None
        mode_depth = mode_depth_by_group[grp]
        if abs(row["depth"] - mode_depth) < 2:
            return "likely_correct_bottom_up", mode_depth
        return "confirmed_outlier", mode_depth

    boundary_rows = fl_findings["hier_finding"] == "parent_non_sce_review_boundary"
    resolved = fl_findings.loc[boundary_rows].apply(lambda r: pd.Series(resolve_boundary(r)), axis=1)
    fl_findings.loc[boundary_rows, "boundary_resolution"] = resolved[0].values
    fl_findings.loc[boundary_rows, "group_typical_depth"] = resolved[1].values
    fl_findings.loc[boundary_rows, "boundary_reattachment_target"] = fl_findings.loc[boundary_rows].apply(
        lambda r: suggest_target_by_depth(r["fl"], r["group_typical_depth"])
        if r["boundary_resolution"] == "confirmed_outlier" else None,
        axis=1,
    )
    fl_findings.loc[boundary_rows, "boundary_reattachment_target_descrip"] = fl_findings.loc[
        boundary_rows, "boundary_reattachment_target"
    ].map(lambda t: descrip_by_fl.get(t) if pd.notna(t) else None)

    if boundary_rows.any():
        print("\nBoundary-review resolution (parent_non_sce_review_boundary):")
        print(fl_findings.loc[boundary_rows, "boundary_resolution"].value_counts())
        n_confirmed = (fl_findings.loc[boundary_rows, "boundary_resolution"] == "confirmed_outlier").sum()
        n_target = fl_findings.loc[boundary_rows, "boundary_reattachment_target"].notna().sum()
        print(f"  - confirmed outliers with a concrete relocation target: {n_target} of {n_confirmed}")

    def recommend(row):
        if row["hier_finding"] == "parent_non_sce_review_boundary":
            resolution = row.get("boundary_resolution")
            if resolution == "likely_correct_bottom_up":
                return (f"FL is SCE ({row['eff_group']}) under a Non-SCE parent, at depth {int(row['depth'])} - "
                        f"consistent with how its {int(peer_count_by_group.get(row['eff_group'], 0))} peer FLs "
                        f"in this SCE Group typically register (depth {int(row['group_typical_depth'])}). "
                        f"Confirmed as expected bottom-up registration, not a defect - no action needed.")
            if resolution == "confirmed_outlier":
                target = row.get("boundary_reattachment_target")
                if pd.notna(target):
                    return (f"FL is SCE ({row['eff_group']}) at depth {int(row['depth'])}, inconsistent with "
                            f"peer {row['eff_group']} FLs' typical depth {int(row['group_typical_depth'])} - "
                            f"CONFIRMED placement issue, not just a boundary review. Its own hierarchy already "
                            f"passes through {target} ({row.get('boundary_reattachment_target_descrip')}) at "
                            f"the typical depth - recommend relocating the SCE registration there.")
                return (f"FL is SCE ({row['eff_group']}) at depth {int(row['depth'])}, inconsistent with peer "
                        f"{row['eff_group']} FLs' typical depth {int(row['group_typical_depth'])} - CONFIRMED "
                        f"placement issue, but no ancestor at the typical depth could be found automatically - "
                        f"needs SME/engineering input to identify the correct attachment point.")
            boundary = row["tips3_registration_boundary"]
            if pd.notna(boundary) and str(boundary).strip():
                return (f"FL is SCE ({row['eff_group']}) under a Non-SCE parent - fewer than 5 peer FLs "
                        f"registered under this SCE Group, not enough evidence to confirm the level "
                        f"automatically. TIPS3 Appendix D specifies this SCE Group's registration boundary as: "
                        f"\"{boundary}\" - needs manual SME review against that spec.")
            return (f"FL is SCE ({row['eff_group']}) under a Non-SCE parent - likely correct bottom-up "
                    f"registration, but TIPS3 Appendix D has no extracted registration-boundary text for this "
                    f"SCE Group - confirm manually against the source document.")
        if row["hier_finding"] in ("parent_inactive", "parent_delete"):
            action = row["hier_finding"].split("_")[1]
            target = row["suggested_relocation_target_fl"]
            if pd.notna(target):
                return (f"FL is SCE ({row['eff_group']}) but its parent FL is being made {action} - "
                        f"RECOMMENDATION: relocate this FL (and its equipment) to sit directly under "
                        f"{target} ({row['suggested_relocation_target_descrip']}), the next stable ancestor "
                        f"in the hierarchy above the {action} parent, before the parent is actioned.")
            return (f"FL is SCE ({row['eff_group']}) but its parent FL is being made {action} - relocate "
                    f"this FL (and its equipment) under an active parent FL before the parent is actioned. "
                    f"No stable ancestor could be found automatically within 6 hierarchy levels - needs "
                    f"manual review to pick a target.")
        if row["hier_finding"] == "parent_inactive_in_sap":
            target = row["suggested_relocation_target_fl"]
            if pd.notna(target):
                return (f"FL is SCE ({row['eff_group']}) and active, but its parent FL is INAC in SAP System "
                        f"status - the FL and its equipment are orphaned under a deactivated node. "
                        f"RECOMMENDATION: relocate it to sit directly under {target} "
                        f"({row['suggested_relocation_target_descrip']}), the next active ancestor, or "
                        f"reactivate the parent if its deactivation was in error.")
            return (f"FL is SCE ({row['eff_group']}) and active, but its parent FL is INAC in SAP System status. "
                    f"No active ancestor found within 6 hierarchy levels - needs manual review to pick a target.")
        if row["hier_finding"] == "sce_fl_inactive_in_sap":
            return (f"FL is registered SCE ({row['eff_group']}) but is itself INAC in SAP System status. "
                    f"Confirm whether the asset is decommissioned (withdraw the SCE registration) or still in "
                    f"service (reactivate the FL so its SCE maintenance can be planned).")
        if row["hier_finding"] == "parent_grouping_node":
            return (f"Parent FL is a grouping node (type 'FL') in {SCE_TEMPLATE_CITE}. The SCE identification "
                    f"questionnaire is only applied to FLs that carry equipment, so the parent is unassessed by "
                    f"design of bottom-up registration - no action needed.")
        if row["hier_finding"] == "parent_unassessed":
            return (f"Parent FL's SCE status has not been assessed, and it does not appear in "
                    f"{SCE_TEMPLATE_CITE} - send to SCE identification for assessment.")
        if row["hier_finding"] == "parent_fl_not_found":
            return "Parent FL referenced in Superior FunctLoc. does not exist in the FL master - data integrity issue."
        return ""

    fl_findings["recommended_action"] = fl_findings.apply(recommend, axis=1)
    fl_findings["parent_eff_status"] = fl_findings["superior_fl"].map(
        lambda p: status_by_fl.loc[p, "eff_status"] if p in status_by_fl.index else None
    )
    fl_findings["parent_status_source"] = fl_findings["superior_fl"].map(
        lambda p: status_by_fl.loc[p, "eff_source"] if p in status_by_fl.index else None
    )
    fl_findings["parent_sap_system_status"] = fl_findings["superior_fl"].map(
        lambda p: ("INAC" if status_by_fl.loc[p, "sap_inactive"] else "Active") if p in status_by_fl.index else None
    )

    # confirmed_outlier is a real, resolved placement issue - not the same
    # confidence level as an unresolved "please review" item, so it gets
    # promoted to Medium severity; likely_correct_bottom_up is resolved as
    # NOT an issue at all, so it's explicitly downgraded rather than left
    # at the blanket "Low" every parent_non_sce_review_boundary row got
    # before this was resolved per-FL.
    severity_override = {"confirmed_outlier": "Medium", "likely_correct_bottom_up": "Informational",
                         "insufficient_peer_data": "Low"}
    fl_findings.loc[boundary_rows, "hier_severity"] = fl_findings.loc[boundary_rows, "boundary_resolution"].map(
        severity_override
    )

    print(f"\nFL hierarchy findings: {len(fl_findings):,}")
    print(fl_findings["hier_finding"].value_counts())

    fl_out_cols = ["Functional Location", "FunctLocDescrip.", "eff_status", "eff_group", "depth",
                   "Superior FunctLoc.", "parent_eff_status", "parent_status_source", "parent_sap_system_status",
                   "hier_finding", "hier_severity",
                   "tips3_registration_boundary", "boundary_resolution", "group_typical_depth",
                   "boundary_reattachment_target", "boundary_reattachment_target_descrip",
                   "suggested_relocation_target_fl",
                   "suggested_relocation_target_descrip", "suggested_relocation_target_status",
                   "recommended_action"]
    fl_findings_out = fl_findings[fl_out_cols].sort_values(["hier_severity", "hier_finding"])

    # ------------------------------------------------------------------
    # Equipment rollup
    # ------------------------------------------------------------------
    equip_raw = pd.read_excel(SAP_EQUIP_FILE, sheet_name="Data", dtype=str)
    equip_raw.columns = [c.strip() for c in equip_raw.columns]
    equip = equip_raw[equip_raw["Location"].str.strip().str.upper() == "BOKOR"].copy()
    equip["fl"] = equip["Functional Location"].map(norm_fl)
    print(f"\nEquipment records (all fields): {len(equip_raw):,}; Location==BOKOR: {len(equip):,}")

    flagged_fls = fl_findings.set_index("fl")
    equip_flagged = equip[equip["fl"].isin(flagged_fls.index)].copy()
    equip_flagged = equip_flagged.merge(
        flagged_fls[["hier_finding", "hier_severity", "suggested_relocation_target_fl", "recommended_action", "eff_group"]],
        left_on="fl", right_index=True, how="left",
    )
    equip_out_cols = ["Equipment", "Object Description", "Functional Location", "FunctLocDescrip.",
                       "eff_group", "hier_finding", "hier_severity", "suggested_relocation_target_fl",
                       "recommended_action"]
    equip_out = equip_flagged[equip_out_cols].sort_values(["hier_severity", "hier_finding"])

    print(f"Equipment affected (sitting under a flagged FL): {len(equip_out):,}")

    summary = pd.DataFrame({
        "Metric": [
            "SAP FLs", "Equipment records",
            "FLs: effective status = SCE", "FLs: effective status = NON_SCE",
            "FLs: effective status = UNASSESSED", "FLs: effective status = INACTIVE/DELETE",
            "  - of which NON_SCE taken from the SCE master template (register and SAP silent)",
            "FL hierarchy findings",
            "  - parent_non_sce_review_boundary", "  - parent_inactive", "  - parent_delete",
            "  - parent_inactive_in_sap (active SCE FL under a parent INAC in SAP)",
            "      - of which have a concrete relocation target suggested",
            "  - sce_fl_inactive_in_sap (SCE FL itself INAC in SAP)",
            "  - parent_grouping_node (parent is a grouping node - unassessed by design)",
            "  - parent_unassessed (parent missing from the SCE master template)", "  - parent_fl_not_found",
            "    - resolved likely_correct_bottom_up (matches peer depth, no action needed)",
            "    - resolved confirmed_outlier (CONFIRMED placement issue, not just review)",
            "      - of which have a concrete relocation target suggested",
            "    - insufficient_peer_data (<5 peer FLs in that SCE Group - needs manual SME review)",
            "Equipment affected",
        ],
        "Value": [
            len(fl), len(equip),
            (fl.eff_status == "SCE").sum(), (fl.eff_status == "NON_SCE").sum(),
            (fl.eff_status == "UNASSESSED").sum(), fl.eff_status.isin(["INACTIVE", "DELETE"]).sum(),
            ((fl.eff_status == "NON_SCE") & (fl.eff_source == "SCE master template")).sum(),
            len(fl_findings_out),
            (fl_findings_out.hier_finding == "parent_non_sce_review_boundary").sum(),
            (fl_findings_out.hier_finding == "parent_inactive").sum(),
            (fl_findings_out.hier_finding == "parent_delete").sum(),
            (fl_findings_out.hier_finding == "parent_inactive_in_sap").sum(),
            fl_findings_out.loc[fl_findings_out.hier_finding == "parent_inactive_in_sap",
                                "suggested_relocation_target_fl"].notna().sum(),
            (fl_findings_out.hier_finding == "sce_fl_inactive_in_sap").sum(),
            (fl_findings_out.hier_finding == "parent_grouping_node").sum(),
            (fl_findings_out.hier_finding == "parent_unassessed").sum(),
            (fl_findings_out.hier_finding == "parent_fl_not_found").sum(),
            (fl_findings_out["boundary_resolution"] == "likely_correct_bottom_up").sum(),
            (fl_findings_out["boundary_resolution"] == "confirmed_outlier").sum(),
            fl_findings_out.loc[fl_findings_out["boundary_resolution"] == "confirmed_outlier",
                                "boundary_reattachment_target"].notna().sum(),
            (fl_findings_out["boundary_resolution"] == "insufficient_peer_data").sum(),
            len(equip_out),
        ],
    })

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        fl_findings_out.to_excel(xl, sheet_name="FL_Hierarchy_Findings", index=False)
        equip_out.to_excel(xl, sheet_name="Equipment_Rollup", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
