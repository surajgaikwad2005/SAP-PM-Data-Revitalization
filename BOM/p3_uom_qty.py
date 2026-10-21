"""
P3 - BOM unit of measure (UOM) and quantity check.

Every BOM line needs a unit and a quantity greater than zero, and the same
material should carry the same unit everywhere it is used.

Those two basic checks come back clean on the Bokor extract, and they always
will: SAP refuses to save an L or N line without a unit and a quantity, so they
re-test what the system already enforces at data entry.  They are kept as a
regression check on a future extract, not as a source of findings.

The real question - are the recorded values CORRECT? - cannot be answered from
the BOM alone, because the BOM is the thing being audited.  Settling it needs an
independent record: the SPIR installed-part counts (PTS 12.00.04), still
outstanding, and on the sheets held so far the installed-quantity column is
blank on every row.

The UNIT, though, does have an independent record: SAP's material master holds
each material's own unit of measure.  Where the material master file has been
supplied (data.material_master()), every BOM line whose component is in it is
compared against that unit - check 4 below.  Assemblies and text items are not
in the material master, so assemblies keep the one-SET convention check.

So this script also runs these checks, none of which needs the SPIR:

  1. IDENTICAL EQUIPMENT DISAGREE.  Two equipment of the same manufacturer
     and model are the same item and must carry the same quantities.  Where they
     do not, one of them is wrong, and the value used on most of the units is
     the correction.  This is the same majority-vote logic P1 uses for item
     category, and it is the only check here that can decide right from wrong
     rather than merely raise a suspicion.
  2. QUANTITY OUTLIER.  A material whose quantity on one BOM is an order of
     magnitude above its own normal.  Evidence of a suspect line, not proof - a
     larger piece of equipment may genuinely take more.
  3. DUPLICATE UNIT CODES.  The catalogue uses two codes for one unit (PC and
     EA, SET and ST).  No single material is ever issued in two units, so the
     per-material check cannot see this, but it is a real standardisation gap.
  4. MATERIAL MASTER UNIT.  The unit on the BOM line against the unit the
     material master records for that material at the Bokor plant.  The master
     is the material's own record, so the BOM line is the one to correct.

Output columns: finding, material, description, detail, confidence,
needs_pcsb_confirmation.
"""
from __future__ import annotations
from collections import Counter

import pandas as pd

import data

# Unit codes that mean the same thing.  SAP allows both to exist, so a catalogue
# drifts into carrying two codes for one unit.
_UOM_SYNONYMS = [
    ("PC", "EA"),        # piece / each
    ("SET", "ST"),
    ("KIT", "KT"),
    ("BOT", "BTL"),      # bottle
    ("BOT", "BT"),
    ("BTL", "BT"),
    ("PAK", "PK"),
    ("PAK", "PAC"),      # pack
    ("CYL", "CY"),       # cylinder
]

# A material has to appear on at least this many lines before it has a
# meaningful "normal" quantity to be an outlier against.
_OUTLIER_MIN_LINES = 5
_OUTLIER_RATIO = 10

# A fleet can run to a hundred identical units, so cap how many are named in a
# cell - the point is which quantity is the odd one out, not the full roll call.
_MAX_EQUIPMENT_LISTED = 6


def _short(m) -> str:
    return str(m).lstrip("0") or str(m)


def _fleet_rows(material_lines: pd.DataFrame) -> tuple[list, int, int]:
    """Identical equipment (same manufacturer + model) that disagree on quantity.

    Two equipment of the same make and model are the same item, so a component
    fitted to both must be fitted in the same number.  Where they disagree one
    of them is wrong; where most of them agree, that value is the correction and
    the odd one out is the line to fix.

    Equipment marked inactive in SAP (system status INAC, or a DEAC- prefix on
    the description) are KEPT in the comparison - a decommissioned unit's BOM is
    still evidence of what the item takes - but they are named as inactive in
    the reason, because correcting a line on a dead record is wasted work and a
    reader has to be able to see that before acting.
    """
    eq = data.equipment()
    with_bom = set(material_lines["key"])
    fleet = eq[eq["manufacturer"].notna() & eq["model"].notna() & eq["key"].isin(with_bom)]
    inactive = dict(zip(eq["key"], eq["is_inactive"]))

    # A second pass over SAP's classification was tried here, to reach the 741
    # equipment whose master record has no manufacturer or model.  It was
    # removed: the classification file is a shell.  Only 1.2% of its 376,991
    # values are real, the "Type" characteristic that would identify equipment
    # sameness reads "?" on 9,577 of its 9,625 rows, and grouping on that
    # placeholder produced 33 findings that compared unrelated equipment.
    # data.equipment_classification() is kept ready for the day PCSB populate
    # it; until then there is nothing in it to match on.

    # one quantity per (equipment, component) - a component appears once per BOM
    qty = material_lines.groupby(["key", "component"])["quantity"].max()
    on_bom = set(qty.index.get_level_values(0))
    desc = material_lines.dropna(subset=["description"]).groupby("component")["description"].first()
    number = material_lines.groupby("key")["equipment"].first()

    # Strongest evidence first, so a cohort identified by make and model is
    # never diluted by the weaker classification cohort.
    cohorts = [(f"the same make and model ({mfr} {model})", keys, "model")
               for (mfr, model), keys in
               fleet.groupby(["manufacturer", "model"])["key"].apply(list).items()]

    rows, n_majority, n_tied = [], 0, 0
    for cohort, keys, kind in cohorts:
        if len(keys) < 2:
            continue
        per_component: dict = {}
        for k in keys:
            if k not in on_bom:
                continue
            for component, q in qty.loc[k].items():
                per_component.setdefault(component, []).append((k, q))

        for component, seen in per_component.items():
            quantities = [q for _, q in seen]
            if len(set(quantities)) < 2:
                continue                                   # the units agree
            counts = Counter(quantities).most_common()
            decided = len(counts) > 1 and counts[0][1] > counts[1][1]
            if decided:
                n_majority += 1
            else:
                n_tied += 1

            def where(q) -> str:
                """The equipment carrying quantity q, capped so the cell stays readable.
                An inactive one is named as such - it still counts, but the
                reader needs to know before acting on it."""
                names = [_short(number.get(k, k)) + (" (inactive in SAP)" if inactive.get(k) else "")
                         for k, qq in seen if qq == q]
                head = ", ".join(names[:_MAX_EQUIPMENT_LISTED])
                extra = len(names) - _MAX_EQUIPMENT_LISTED
                return f"{head} and {extra} more" if extra > 0 else head

            # Count against the equipment that actually carry this part, not the
            # whole make/model group - otherwise the numbers in the sentence do
            # not add up when some units do not list the component at all.
            n_inactive = sum(1 for k, _ in seen if inactive.get(k))
            if n_inactive == len(seen):
                caution = (" Every one of these is marked inactive in SAP, so confirm any of them "
                           "is still in service before spending time on this.")
            elif n_inactive:
                caution = (f" {n_inactive} of them "
                           f"{'is' if n_inactive == 1 else 'are'} marked inactive in SAP, so check "
                           f"whether they are still in service before changing anything.")
            else:
                caution = ""

            opening = (f"There are {len(seen)} equipment of {cohort} carrying this part, so "
                       f"they should all take the same number of it")

            if decided:
                majority_q, majority_n = counts[0]
                odd = "; ".join(f"equipment {where(q)} uses {q:g}" for q, _ in counts[1:])
                detail = (f"{opening}. {majority_n} of them use {majority_q:g}, but {odd}. The "
                          f"number used on most of them ({majority_q:g}) is most likely the right "
                          f"one, so the odd ones out are the lines to correct.{caution}")
            else:
                spread = "; ".join(f"equipment {where(q)} uses {q:g}" for q, _ in counts)
                detail = (f"{opening} - but they do not agree: {spread}. No number is used more "
                          f"often than the others, so there is nothing to follow and an engineer "
                          f"has to decide which is right.{caution}")
            rows.append(["Identical equipment are recorded with different quantities of this part",
                         _short(component),
                         desc.get(component, ""), detail,
                         "Other Bokor equipment", 0.85 if decided else 0.50, "Yes"])
    return rows, n_majority, n_tied


def _outlier_rows(material_lines: pd.DataFrame, already_flagged: set) -> list:
    """A material used in a quantity far above its own normal.

    Evidence of a suspect line rather than proof of an error - a larger piece of
    equipment may genuinely take more - so these are raised for a look, never corrected.
    Components the fleet check has already settled are left out: that evidence
    is stronger, and saying it twice only clutters the sheet.
    """
    grouped = material_lines.groupby("component")["quantity"]
    stats = pd.DataFrame({"lines": grouped.size(), "median": grouped.median(), "max": grouped.max()})
    desc = material_lines.dropna(subset=["description"]).groupby("component")["description"].first()

    rows = []
    for component, r in stats.iterrows():
        if _short(component) in already_flagged:
            continue
        if r["lines"] < _OUTLIER_MIN_LINES or not r["median"] > 0:
            continue
        if r["max"] < r["median"] * _OUTLIER_RATIO:
            continue
        rows.append(["This quantity is much higher than the same part uses elsewhere",
                     _short(component), desc.get(component, ""),
                     f"This part appears on {int(r['lines'])} BOM lines. Almost everywhere it is "
                     f"used {r['median']:g} at a time, but on one BOM it is {r['max']:g}. That may "
                     f"be genuine on a larger piece of equipment, so it is worth a look rather "
                     f"than a change.",
                     "Other Bokor BOMs", 0.60, "Yes"])
    return rows


def _uom_synonym_rows(material_lines: pd.DataFrame) -> list:
    """Two unit codes in use for one and the same unit.

    No single material is ever issued in two different units, so the
    per-material check cannot see this - but the catalogue as a whole carries
    both codes, which is a standardisation gap.
    """
    used = material_lines["uom"].value_counts()
    rows = []
    for a, b in _UOM_SYNONYMS:
        if a in used.index and b in used.index:
            keep, drop = (a, b) if used[a] >= used[b] else (b, a)
            rows.append(["The catalogue uses two different codes for the same unit", "", "",
                         f"'{a}' is used on {used[a]:,} BOM lines and '{b}' on {used[b]:,}, but both "
                         f"mean the same thing. Nothing is wrong on any single line, so the other "
                         f"checks cannot see it, but the catalogue should settle on one code - "
                         f"'{keep}' is the one already in wider use, which would retire '{drop}'.",
                         "Other Bokor BOMs", 0.90, "Yes"])
    return rows


def _same_unit(a: str, b: str) -> bool:
    return (a, b) in _UOM_SYNONYMS or (b, a) in _UOM_SYNONYMS


def _material_master_rows(material_lines: pd.DataFrame) -> tuple[list, dict]:
    """BOM lines whose unit differs from the material master's unit.

    The material master is SAP's own record of the material, held per plant, so
    it is an independent check on the unit typed onto a BOM line - the one part
    of "is this value correct?" that does not have to wait for the SPIR.  One
    row per material, because a material carries one unit on every BOM line it
    appears on.

    Returns the rows and the coverage counts.  With no material master file the
    check is skipped and the counts say so.
    """
    mm = data.material_master()
    if not len(mm):
        return [], {"material_master_available": False}

    master_uom = dict(zip(mm["material"], mm["uom"]))
    lines = material_lines.dropna(subset=["uom"]).copy()
    lines["material"] = data._norm_key(lines["component"])
    lines["bom_uom"] = lines["uom"].astype(str).str.upper().str.strip()
    lines["master_uom"] = lines["material"].map(master_uom)

    covered = lines[lines["master_uom"].notna()]
    missing = lines[lines["master_uom"].isna()]
    differ = covered[covered["bom_uom"] != covered["master_uom"]]
    desc = lines.dropna(subset=["description"]).groupby("material")["description"].first()

    rows = []
    for material, g in differ.groupby("material"):
        master = g["master_uom"].iat[0]
        used = sorted(set(g["bom_uom"]))
        if all(_same_unit(u, master) for u in used):
            why = (f"The two are the same unit written two ways, so nothing is miscounted - but the "
                   f"BOM should carry the material's own code, '{master}'.")
            conf = 0.90
        else:
            why = (f"These are different units, so the quantity on those lines may be counting "
                   f"something other than what the material is issued in. The material master is the "
                   f"material's own record, so '{master}' is the unit to use - check the quantity "
                   f"still makes sense once it is changed.")
            conf = 0.85
        entered = " and ".join(f"'{u}'" for u in used)
        rows.append(["The unit on the BOM differs from the unit in the material master",
                     material, desc.get(material, ""),
                     f"The material master records this part in '{master}' at plant {data.C.PLANT}. On "
                     f"{len(g)} BOM line(s) it is entered as {entered}. {why}",
                     "SAP material master", conf, "Yes"])

    is_assembly = missing["material_type"] == "IBAU"
    n_differ = int(differ["material"].nunique())
    counts = {
        "material_master_available": True,
        "lines_checked_against_material_master": int(len(covered)),
        "materials_checked_against_material_master": int(covered["material"].nunique()),
        "materials_unit_matches_material_master": int(covered["material"].nunique()) - n_differ,
        "materials_unit_differs_from_material_master": n_differ,
        "lines_unit_differs_from_material_master": int(len(differ)),
        "assemblies_not_in_material_master": int(missing.loc[is_assembly, "material"].nunique()),
        "other_materials_not_in_material_master": int(missing.loc[~is_assembly, "material"].nunique()),
    }
    return rows, counts


def _assembly_uom_rows(lines: pd.DataFrame) -> list:
    """Assemblies that are not counted in SET.

    PMMS Training Pack 2026 p.14 shows every assembly on the BOM carrying unit
    SET, with the parts beneath it in PC.  That makes sense: an assembly is one
    grouping, not a quantity of something.  Where an assembly is counted in EA,
    AS or PC instead, the unit is telling the planner it is a purchasable item,
    which it is not.
    """
    asm = lines[(lines["material_type"] == "IBAU") & lines["uom"].notna()]
    if not len(asm):
        return []
    desc = asm.dropna(subset=["description"]).groupby("component")["description"].first()
    rows = []
    for component, g in asm.groupby("component"):
        units = sorted(set(g["uom"]))
        if units == ["SET"]:
            continue
        off = [u for u in units if u != "SET"]
        rows.append(["This assembly is not counted in SET", _short(component),
                     desc.get(component, ""),
                     f"It is an assembly - a grouping of parts, not something you buy one of - so "
                     f"it should be counted in SET like every other assembly. It is recorded as "
                     f"{' and '.join(off)} on {len(g)} BOM line(s).",
                     "PMMS Training Pack p.14", 0.80, "Yes"])
    return rows


def run() -> tuple[pd.DataFrame, dict]:
    lines = data.bom_lines()
    material_lines = lines[lines["item_category"].isin(["I", "L", "N"]) & lines["component"].notna()]

    rows = []

    # --- the one check that can decide right from wrong --------------------
    fleet, n_majority, n_tied = _fleet_rows(material_lines)
    rows += fleet
    flagged = {r[1] for r in fleet}

    # --- suspects raised for a look, not verdicts --------------------------
    outliers = _outlier_rows(material_lines, flagged)
    rows += outliers

    synonyms = _uom_synonym_rows(material_lines)
    rows += synonyms

    asm_uom = _assembly_uom_rows(material_lines)
    rows += asm_uom

    # --- the unit against SAP's own record of the material -----------------
    mm_rows, mm_counts = _material_master_rows(material_lines)
    rows += mm_rows

    # --- completeness: SAP enforces these at entry, kept as a regression ---
    no_uom = material_lines[material_lines["uom"].isna()]
    for _, r in no_uom.iterrows():
        rows.append(["This BOM line has no unit of measure",
                     _short(r["component"]), r["description"],
                     f"The line sits on equipment {r['equipment']}, and no unit has been entered "
                     f"against it, so there is no way to tell what a quantity on it counts.",
                     "SAP record", 0.90, "Yes"])

    bad_qty = material_lines[~(material_lines["quantity"] > 0)]
    for _, r in bad_qty.iterrows():
        rows.append(["This BOM line has no quantity, or a quantity of zero",
                     _short(r["component"]), r["description"],
                     f"The line sits on equipment {r['equipment']}. Every part on a BOM has to say "
                     f"how many are fitted, and this one does not.",
                     "SAP record", 0.80, "Yes"])

    uom_per_material = material_lines.dropna(subset=["uom"]).groupby("component")["uom"].agg(lambda s: sorted(set(s)))
    for material, units in uom_per_material.items():
        if len(units) > 1:
            desc = material_lines.loc[material_lines["component"] == material, "description"].dropna()
            rows.append(["This material is recorded with more than one unit of measure",
                         _short(material), desc.iat[0] if len(desc) else "",
                         f"It is issued as {' on some BOM lines and '.join(units)} on others. A "
                         f"part should be counted the same way everywhere it is used, so one of "
                         f"these is wrong.", "SAP record", 0.70, "Yes"])

    if not rows:
        rows.append(["No problems found", "", "",
                     "Every BOM line has a unit and a quantity, each material is always issued in "
                     "the same unit, and identical equipment agree on how many of each part "
                     "they take.", "SAP record", 1.00, "No"])

    df = pd.DataFrame(rows, columns=["finding", "material", "description", "detail", "evidence",
                                     "confidence", "needs_pcsb_confirmation"])

    summary = {
        "lines_checked": int(len(material_lines)),
        "lines_without_unit": int(len(no_uom)),
        "lines_without_quantity": int(len(bad_qty)),
        "materials_with_mixed_units": int(sum(len(u) > 1 for u in uom_per_material)),
        "identical_equipment_quantity_disagreements": len(fleet),
        "of_those_a_majority_decides": n_majority,
        "of_those_tied_for_engineer": n_tied,
        "quantity_outliers_to_check": len(outliers),
        "duplicate_unit_codes": len(synonyms),
        "assemblies_not_counted_in_set": len(asm_uom),
        **mm_counts,
        "note": "A unit and a quantity being present is enforced by SAP at entry, so those checks "
                "come back clean and are kept as a regression test. The UNIT is confirmed against "
                "the material master where the material is in it (assemblies and text items are "
                "not). Whether a QUANTITY is correct needs an independent record - the SPIR "
                "installed-part counts (PTS 12.00.04), still outstanding. Until that arrives the "
                "strongest evidence available is that identical equipment must carry identical "
                "quantities.",
    }
    return df, summary
