"""
P4 - BOM completion priority.

Question answered: "Which equipment need a BOM built, and in what order?"

An equipment is on the list when:
  * its SAP User Status says a BOM is required  (contains "BOM", not "NBOM"), and
  * it has no BOM lines in the existing BOM extract.

Order (per UDMS guidance, no DOSH tier - Bokor is offshore):
  Safety Critical Elements  ->  Criticality 1  ->  Criticality 2  ->  Criticality 3
  ->  no criticality set.   Active equipment before inactive within each tier.

On top of the SAP NBOM user status, we also re-derive the PTG 12.05.04 s3.5.4
"BOM optional" equipment types from the description (see nbom_rules.py). Those
are FLAGGED, not removed: the clause says BOM development for them is optional,
so it is PCSB's call.

Output columns are plain: rank, priority_tier, equipment, description,
functional_location, criticality, safety_critical, inactive,
bom_optional_ptg_type, note.
"""
from __future__ import annotations
import pandas as pd
import config as C
import data
import nbom_rules


def _tier(row) -> int:
    if row["is_sce"]:
        return C.TIER_SCE
    return {"1": C.TIER_C1, "2": C.TIER_C2, "3": C.TIER_C3}.get(row["criticality"], C.TIER_NONE)


def run() -> tuple[pd.DataFrame, dict]:
    eq = data.equipment()
    have_bom = set(data.bom_by_equipment()["key"])

    need = eq[eq["needs_bom"] & ~eq["key"].isin(have_bom)].copy()
    need["priority_tier_num"] = need.apply(_tier, axis=1)
    need["priority_tier"] = need["priority_tier_num"].map(C.TIER_LABEL)

    need = need.sort_values(
        ["priority_tier_num", "is_inactive", "functional_location", "equipment"],
        na_position="last",
    ).reset_index(drop=True)
    need["rank"] = range(1, len(need) + 1)

    # PTG 12.05.04 s3.5.4 - equipment types for which a BOM is optional.
    # Flagged, never dropped: the clause says "optional", so PCSB decides.
    need["ptg_nbom"] = need["description"].map(nbom_rules.nbom_type)
    is_optional = need["ptg_nbom"] != ""

    notes = []
    for inactive, optional_type in zip(need["is_inactive"], need["ptg_nbom"]):
        parts = []
        if inactive:
            parts.append("Equipment is INACTIVE in SAP - confirm it is still real before building its BOM")
        if optional_type:
            parts.append(f"Looks like a {nbom_rules.CLAUSE} '{optional_type}' type, where a BOM is "
                         f"optional - PCSB to confirm whether to waive it (set User Status NBOM)")
        notes.append("  |  ".join(parts))
    need["note"] = notes

    # No confidence column here, deliberately.  Every row on this list is on it
    # for a deterministic reason - SAP User Status says a BOM is required and
    # the BOM extract has no lines for the equipment - so there is no judgement
    # to be more or less sure about.  A score derived from the criticality tier
    # would only restate priority_tier and invite the reader to sort by it as
    # though it meant something.  The other sheets score real judgement calls.
    worklist = pd.DataFrame({
        "rank": need["rank"],
        "priority_tier": need["priority_tier"],
        "equipment": need["equipment"],
        "description": need["description"],
        "functional_location": need["functional_location"],
        "criticality": need["criticality"].fillna("(not set)"),
        "safety_critical": need["is_sce"].map({True: "Yes", False: "-"}),
        "inactive": need["is_inactive"].map({True: "Yes", False: "-"}),
        "bom_optional_ptg_type": need["ptg_nbom"].replace("", "-"),
        # The list itself is SAP's own declaration (User Status says a BOM is
        # required, and no BOM lines exist).  A waiver flag is additionally
        # matched against a written clause, so it earns the stronger label.
        "evidence": need["ptg_nbom"].map(
            lambda t: "SAP record + PTG 12.05.04 s3.5.4" if t else "SAP record"),
        "note": need["note"],
    })

    summary = {
        "equipment_needing_a_bom": int(len(worklist)),
        "by_tier": worklist["priority_tier"].value_counts().sort_index().to_dict(),
        "inactive_in_the_list": int(need["is_inactive"].sum()),
        "bom_optional_per_ptg_3_5_4": int(is_optional.sum()),
        "bom_optional_by_type": need.loc[is_optional, "ptg_nbom"].value_counts().to_dict(),
        "note": "C1 + C2 (+ SCE) are the deck's committed scope; C3 and 'no criticality' are the remainder. "
                "PTG-optional equipment stay in the list, flagged - the clause says optional, so PCSB decides.",
    }
    return worklist, summary
