"""
Check 2 (Group A) - Asset register structure vs TIPS3
------------------------------------------------------------------
TIPS3's hierarchy/registration rules are narrative, not a structured
rulebook - there is no table saying "SCE group X must be registered at
FL depth N". The one genuinely checkable rule that TIPS3 Appendix D does
give, per SCE Group, is its intended registration granularity ("At item
level, i.e. per crane" vs "At system level" vs "At area level" etc,
already extracted into `system_level_boundaries`). Two checks built on
that, both honestly framed as review signals (SME judgement needed, not
asserted defects, since neither has independent asset-count ground
truth):

  1. Registration granularity cross-check: classify each SCE Group's
     TIPS3 boundary text as "item" (many expected registrations, one per
     physical item) or "coarser" (system/sub-system/area/module/category
     level - few expected). Compare against how many distinct FLs are
     actually registered under that group in the approved register
     (Group G1). An "item"-level group with only 1 FL registered is a
     candidate under-registration - flagged for review, not asserted.

  2. Hierarchy-depth consistency: for each SCE Group, compute the FL-tree
     depth (steps from a platform root via Superior FunctLoc.) of every
     FL registered under it. Unlike (1), this needs no external ground
     truth - if a group's registrations span a wide depth range, some of
     them are very likely registered at the wrong level relative to the
     others, which is a structural finding regardless of what the
     "correct" absolute depth is.
  2b. Outlier re-attachment suggestion: pinpoints WHICH specific FL(s)
     are driving a flagged group's wide range (>=2 levels from the
     group's own modal/most-common depth - a 1-level difference is a
     legitimate secondary cluster, not an outlier), and where each one
     should likely attach. For an outlier registered TOO DEEP, its own
     ancestor chain is walked to find the ancestor already sitting at
     the group's modal depth - a concrete, grounded suggestion (not
     invented - it's already part of that FL's own lineage). For an
     outlier registered TOO SHALLOW, there is no such candidate to walk
     to (going deeper would mean pointing at a more specific node that
     doesn't exist in this FL's chain) - reported honestly as needing
     SME/engineering input rather than guessed.

Output: Data exploration/output/D2_Structure_TIPS3_Registration_Level.xlsx
  - Summary
  - Granularity_Review       (one row per SCE Group)
  - Depth_Inconsistency      (SCE Groups whose registrations span an
                              unusually wide hierarchy-depth range)
  - Outlier_FL_Reattachment  (the specific outlier FLs within those
                              groups, with a concrete re-attachment
                              suggestion where one can be grounded)

Run:
    python "code/agent/check2_structure_tips3.py"
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
TIPS3_FILE = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "tips3_extraction.xlsx"
OUT_XLSX = Path(__file__).resolve().parents[2] / "Data exploration" / "output" / "D2_Structure_TIPS3_Registration_Level.xlsx"

SCE_CODE_RE = re.compile(r"([A-Z]{2,3}\d{3})\s*$")
ITEM_LEVEL_RE = re.compile(r"item level|per\s+\w+|category of equipment", re.I)


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


def classify_granularity(boundary_text):
    if not isinstance(boundary_text, str) or not boundary_text.strip():
        return "unknown"
    return "item" if ITEM_LEVEL_RE.search(boundary_text) else "coarser"


def compute_depths(fl_df):
    """Depth of every FL = number of Superior FunctLoc. hops to a root
    (a FL whose own superior isn't in the file, or a cycle guard trips)."""
    parent = dict(zip(fl_df["fl"], fl_df["sup"]))
    valid_fls = set(fl_df["fl"])
    depth_cache = {}

    def depth_of(fl, seen=None):
        if fl in depth_cache:
            return depth_cache[fl]
        seen = seen or set()
        if fl in seen or fl not in valid_fls:
            return 0
        p = parent.get(fl)
        if p is None or p not in valid_fls or p == fl:
            depth_cache[fl] = 0
            return 0
        d = 1 + depth_of(p, seen | {fl})
        depth_cache[fl] = d
        return d

    return {fl: depth_of(fl) for fl in valid_fls}


def suggest_reattachment(fl_code, mode_depth, parent_map, depth_by_fl, descrip_by_fl, max_hops=10):
    """For an outlier FL sitting DEEPER than its group's modal depth, walk
    its own ancestor chain (which it's already, legitimately, part of) to
    find the ancestor sitting exactly at the modal depth - a concrete,
    grounded re-attachment candidate, not an invented one. For an outlier
    sitting SHALLOWER than the mode, there is no such candidate: going
    deeper would mean pointing at a more specific node that doesn't exist
    in this FL's own chain, and inventing one isn't something we can do
    safely - that's flagged as needing SME/engineering input instead."""
    current_depth = depth_by_fl.get(fl_code)
    if current_depth is None or current_depth <= mode_depth:
        return None, None
    node = parent_map.get(fl_code)
    for _ in range(max_hops):
        if node is None or node not in depth_by_fl:
            return None, None
        if depth_by_fl[node] == mode_depth:
            return node, descrip_by_fl.get(node)
        node = parent_map.get(node)
    return None, None


def main():
    # ------------------------------------------------------------------
    # FL hierarchy + depth
    # ------------------------------------------------------------------
    fl = pd.read_excel(SAP_FL_FILE, sheet_name="Data", dtype=str)
    fl.columns = [c.strip() for c in fl.columns]
    fl["fl"] = fl["Functional Location"].map(norm_fl)
    fl["sup"] = fl["Superior FunctLoc."].map(norm_fl)
    fl = fl.drop_duplicates(subset="fl")
    print(f"SAP FLs: {len(fl):,}")

    print("Computing hierarchy depth (Superior FunctLoc. walk)...")
    depths = compute_depths(fl)
    fl["depth"] = fl["fl"].map(depths)
    print(f"Depth range: {fl['depth'].min()}-{fl['depth'].max()}, median {fl['depth'].median():.0f}")

    # ------------------------------------------------------------------
    # Ground-truth register -> which FLs are registered under which SCE Group
    # ------------------------------------------------------------------
    con = sqlite3.connect(REGISTER_DB)
    reg = pd.read_sql("select functional_location, action from sce_register", con)
    con.close()
    reg["fl"] = reg["functional_location"].map(norm_fl)
    reg[["gt_category", "gt_sce_group"]] = reg["action"].apply(lambda a: pd.Series(normalize_action(a)))
    reg_sce = reg[reg["gt_category"].isin(["maintain", "classify", "relocate", "sce_other"])].copy()
    reg_sce = reg_sce.dropna(subset=["gt_sce_group"]).drop_duplicates(subset=["fl", "gt_sce_group"])
    # SCE Groups of the latest GOPS4 (Mar 2026): a group not among them is no
    # longer classified as SCE (PCSB, 9 Oct 2026) - its FLs are not SCE
    # registrations, and it is not a TIPS3 granularity question either.
    current_gops4 = set(pd.read_excel(GOPS4_FILE)["sce_group"].dropna().str.strip().str.upper())
    reg_sce = reg_sce[reg_sce["gt_sce_group"].str.upper().isin(current_gops4)]
    reg_sce = reg_sce.merge(fl[["fl", "depth"]], on="fl", how="left")
    print(f"\nRegister rows recommending an SCE group: {len(reg_sce):,}")

    # ------------------------------------------------------------------
    # TIPS3 registration boundary per group
    # ------------------------------------------------------------------
    tips3 = pd.read_excel(TIPS3_FILE, sheet_name="SCE_Group_Definitions")
    tips3 = tips3.dropna(subset=["sce_group"])
    tips3["granularity"] = tips3["system_level_boundaries"].map(classify_granularity)

    # ------------------------------------------------------------------
    # Check 1: registration granularity cross-check
    # ------------------------------------------------------------------
    counts = reg_sce.groupby("gt_sce_group")["fl"].nunique().rename("distinct_fls_registered")
    granularity_df = tips3[["sce_group", "sce_group_title", "system_level_boundaries", "granularity"]].merge(
        counts, left_on="sce_group", right_index=True, how="left"
    )
    granularity_df["distinct_fls_registered"] = granularity_df["distinct_fls_registered"].fillna(0).astype(int)

    def review_note(row):
        # Only the "item-level but ~0 registrations" direction is kept -
        # a "coarser" (system/area) group having many registrations was
        # tried and dropped: without independent asset-count ground
        # truth, a platform-wide system with hundreds of tagged
        # locations (e.g. Piping Systems, ESD) is the *expected* shape,
        # not a defect, and flagging every populated coarse group on a
        # single count threshold produced only noise.
        if row["sce_group"] not in current_gops4:
            return ""  # no longer an SCE Group per GOPS4.0
        if row["granularity"] == "item" and row["distinct_fls_registered"] <= 1:
            return "review: item-level group but <=1 FL registered - possible under-registration"
        return ""

    granularity_df["review_flag"] = granularity_df.apply(review_note, axis=1)
    granularity_df["in_gops4"] = granularity_df["sce_group"].isin(current_gops4).map({True: "Yes", False: "No - no longer SCE"})
    granularity_review = granularity_df.sort_values(
        ["review_flag", "distinct_fls_registered"], ascending=[False, True]
    )
    n_review = (granularity_df["review_flag"] != "").sum()
    print(f"SCE Groups flagged for granularity review: {n_review} of {len(granularity_df)}")

    # ------------------------------------------------------------------
    # Check 2: hierarchy-depth consistency within each SCE Group
    # ------------------------------------------------------------------
    depth_stats = reg_sce.groupby("gt_sce_group")["depth"].agg(["count", "min", "max", "median", "std"]).reset_index()
    depth_stats["range"] = depth_stats["max"] - depth_stats["min"]
    depth_stats = depth_stats.merge(
        tips3[["sce_group", "sce_group_title", "granularity"]], left_on="gt_sce_group", right_on="sce_group", how="left"
    )
    # only meaningful with >=5 registrations; flag a wide depth range
    depth_inconsistency = depth_stats[(depth_stats["count"] >= 5) & (depth_stats["range"] >= 4)].copy()
    depth_inconsistency = depth_inconsistency.sort_values("range", ascending=False)
    print(f"SCE Groups with wide hierarchy-depth range (>=4, n>=5 registrations): {len(depth_inconsistency)}")

    # ------------------------------------------------------------------
    # Check 2b: which SPECIFIC FLs are the outliers driving each flagged
    # group's wide range, and where should each one likely be re-attached?
    # Only FLs deviating >=2 levels from the group's own MODE depth are
    # treated as outliers - a 1-level difference from the mode (e.g. a
    # legitimate secondary sub-branch depth) is not flagged, avoiding the
    # same over-flagging mistake corrected elsewhere in this check.
    # ------------------------------------------------------------------
    parent_map = dict(zip(fl["fl"], fl["sup"]))
    depth_by_fl = dict(zip(fl["fl"], fl["depth"]))
    descrip_by_fl = dict(zip(fl["fl"], fl["FunctLocDescrip."]))

    outlier_rows = []
    for grp in depth_inconsistency["gt_sce_group"]:
        grp_rows = reg_sce[reg_sce["gt_sce_group"] == grp].dropna(subset=["depth"])
        mode_depth = int(grp_rows["depth"].mode().iat[0])
        outliers = grp_rows[(grp_rows["depth"] - mode_depth).abs() >= 2]
        for _, r in outliers.iterrows():
            target_fl, target_descrip = suggest_reattachment(r["fl"], mode_depth, parent_map, depth_by_fl, descrip_by_fl)
            if target_fl:
                recommendation = (f"This FL sits at depth {int(r['depth'])}, deeper than the group's typical "
                                  f"depth {mode_depth}. Its own hierarchy already passes through {target_fl} "
                                  f"({target_descrip}) at depth {mode_depth} - consider registering the SCE "
                                  f"tag there instead, consistent with how peer {grp} FLs are registered.")
            elif r["depth"] > mode_depth:
                recommendation = (f"This FL sits at depth {int(r['depth'])}, deeper than the group's typical "
                                  f"depth {mode_depth}, but no ancestor at depth {mode_depth} was found within "
                                  f"{10} hops - needs manual review.")
            else:
                recommendation = (f"This FL sits at depth {int(r['depth'])}, SHALLOWER than the group's typical "
                                  f"depth {mode_depth}. No deeper node exists in this FL's own hierarchy to "
                                  f"suggest automatically - needs SME/engineering input to identify the correct, "
                                  f"more specific attachment point.")
            outlier_rows.append({
                "sce_group": grp, "functional_location": r["fl"],
                "functional_location_descrip": descrip_by_fl.get(r["fl"]),
                "current_depth": int(r["depth"]), "group_typical_depth": mode_depth,
                "suggested_reattachment_fl": target_fl, "suggested_reattachment_descrip": target_descrip,
                "recommendation": recommendation,
            })
    outlier_suggestions = pd.DataFrame(outlier_rows)
    print(f"Outlier FLs identified within flagged groups: {len(outlier_suggestions)}")
    if len(outlier_suggestions):
        print(f"  - with a concrete re-attachment suggestion: {outlier_suggestions['suggested_reattachment_fl'].notna().sum()}")

    # ------------------------------------------------------------------
    summary = pd.DataFrame({
        "Metric": [
            "SAP FLs", "FL hierarchy depth range",
            "SCE Groups with a TIPS3 registration-boundary spec",
            "  - classified 'item level' (many registrations expected)",
            "  - classified 'coarser' (system/area/module/category level)",
            "SCE Groups flagged for granularity review",
            "SCE Groups with wide hierarchy-depth range (possible mis-registration)",
            "  - specific outlier FLs identified within those groups",
            "    - with a concrete re-attachment suggestion",
            "    - too deep, no ancestor found within 10 hops (needs manual review)",
            "    - too shallow, needs SME/engineering input (no automatic suggestion possible)",
        ],
        "Value": [
            len(fl), f"{fl['depth'].min()}-{fl['depth'].max()}",
            len(tips3),
            (tips3.granularity == "item").sum(),
            (tips3.granularity == "coarser").sum(),
            n_review,
            len(depth_inconsistency),
            len(outlier_suggestions),
            outlier_suggestions["suggested_reattachment_fl"].notna().sum() if len(outlier_suggestions) else 0,
            ((outlier_suggestions["suggested_reattachment_fl"].isna()) & (outlier_suggestions["current_depth"] > outlier_suggestions["group_typical_depth"])).sum() if len(outlier_suggestions) else 0,
            (outlier_suggestions["current_depth"] < outlier_suggestions["group_typical_depth"]).sum() if len(outlier_suggestions) else 0,
        ],
    })

    with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as xl:
        summary.to_excel(xl, sheet_name="Summary", index=False)
        granularity_review.to_excel(xl, sheet_name="Granularity_Review", index=False)
        depth_inconsistency.to_excel(xl, sheet_name="Depth_Inconsistency", index=False)
        outlier_suggestions.to_excel(xl, sheet_name="Outlier_FL_Reattachment", index=False)

    print(f"\nWritten to {OUT_XLSX}")


if __name__ == "__main__":
    main()
