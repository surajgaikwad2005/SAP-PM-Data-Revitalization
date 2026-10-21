"""
BOM structure check - is the parts list BUILT correctly?

Every other process asks whether the CONTENT of a BOM is right.  This one asks
whether its SHAPE is right, which is the half of the requirement that reads
"...for the structure of assembly if any".

PMMS Training Pack 2026 p.14 shows the intended shape:

    Functional Location
      └─ Equipment                         (the lowest level of the hierarchy)
           └─ Assembly   category I, unit SET, material type IBAU
                └─ Materials   category L or N, unit PC

and states that a BOM "can be created as single or multilevel".

Two things are reported.

1. THE SAME ASSEMBLY BUILT MANY TIMES OVER.  An assembly node is created per
   equipment, which is normal - but where a dozen identical machines each get
   their own separately-numbered assembly with the same description, that is a
   dozen things to maintain instead of one.  PTG 12.05.04 s3.5.12 is explicit
   that a main assembly "can then be assigned to one or more equipment... that
   has the same construction type".

   The remedy matters here and is easy to get wrong.  These numbers must NOT be
   retired the way a duplicate material is retired: each one is load-bearing in
   its own equipment's BOM.  The work is to point those BOMs at a single shared
   assembly first, and only then retire what falls out.  That is a BOM
   restructuring job, not a material-master cleanup, and it belongs to whoever
   owns BOM structure.

2. EQUIPMENT WITH NO ASSEMBLY AT ALL.  Reported once, as an observation rather
   than as thousands of findings, because it is a question and not yet a fault:
   SAP permits components hung directly off an equipment BOM, while PTG s3.5.10
   describes even the single-level case as grouping components into an assembly.
   Which of those is Bokor's intended practice is PCSB's to say.

Output columns: finding, material, description, detail, confidence,
needs_pcsb_confirmation.
"""
from __future__ import annotations
import re
from collections import defaultdict

import pandas as pd

import data


def _norm(text) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())


def _short(m) -> str:
    return str(m).lstrip("0") or str(m)


def run() -> tuple[pd.DataFrame, dict]:
    eq = data.equipment()
    lines = data.bom_lines()
    lines = lines[lines["component"].notna()]
    assemblies = lines[lines["material_type"] == "IBAU"]

    info = eq.set_index("key")[["manufacturer", "model", "is_inactive"]]
    number = lines.groupby("key")["equipment"].first()

    # --- 1. the same assembly, built once per machine ----------------------
    # Keyed on what the assembly IS plus the model it sits on.  Model rather
    # than manufacturer, because the manufacturer field carries name variants
    # ("FISHER CTRLS." against "FISHER CONTROLS") that would split one finding
    # into several; the model is normalised too, so "164-A" and "164A" meet.
    buckets: dict = defaultdict(set)
    for component, g in assemblies.groupby("component"):
        described = g["description"].dropna()
        if not len(described):
            continue
        for key in set(g["key"]):
            if key not in info.index or pd.isna(info.loc[key, "model"]):
                continue
            buckets[(_norm(described.iat[0]), _norm(info.loc[key, "model"]))].add((component, key))

    rows, n_numbers = [], 0
    for pairs in buckets.values():
        components = sorted({c for c, _ in pairs})
        keys = sorted({k for _, k in pairs})
        # Needs to be several machines AND several assembly numbers: one machine
        # carrying two assemblies is a different fault, and several machines
        # sharing one assembly is exactly what we want to see.
        if len(components) < 2 or len(keys) < 2:
            continue
        n_numbers += len(components)
        inactive = sum(1 for k in keys if info.loc[k, "is_inactive"])
        makes = sorted({str(info.loc[k, "manufacturer"]) for k in keys
                        if pd.notna(info.loc[k, "manufacturer"])})
        model = next((info.loc[k, "model"] for k in keys if pd.notna(info.loc[k, "model"])), "")
        described = assemblies.loc[assemblies["component"] == components[0], "description"].dropna()
        note = ""
        if inactive:
            note = (f" {inactive} of the {len(keys)} are marked inactive in SAP, so confirm they "
                    f"are still in service before restructuring anything.")
        rows.append([
            "The same assembly has been created separately for each machine",
            _short(components[0]),
            described.iat[0] if len(described) else "",
            f"{len(keys)} equipment of the same model ({makes[0] if makes else '?'} {model}) each "
            f"carry their own assembly for this - {len(components)} separate assembly numbers "
            f"({', '.join(_short(c) for c in components[:4])}"
            f"{' and more' if len(components) > 4 else ''}) describing the same thing. The standard "
            f"allows one assembly to serve every machine of the same construction type, so these "
            f"could become one. Do NOT simply retire the spare numbers - each is in use on its own "
            f"machine's parts list; the BOMs have to be pointed at the shared assembly first, and "
            f"only then do the others fall away.{note}",
            "PTG 12.05.04 s3.5.12", 0.75, "Yes"])

    # --- 2. equipment whose BOM has no assembly at all ---------------------
    with_bom = set(lines["key"])
    with_assembly = set(assemblies["key"])
    flat = sorted(with_bom - with_assembly)
    if flat:
        sample = ", ".join(_short(number.get(k, k)) for k in flat[:4])
        rows.append([
            "Some equipment hold their parts directly, with no assembly grouping",
            "", "",
            f"{len(flat):,} of the {len(with_bom):,} equipment that have a parts list "
            f"({100 * len(flat) / len(with_bom):.0f}%) hang their parts straight off the equipment "
            f"with no assembly in between - for example {sample}. SAP allows this, but the standard "
            f"describes even a simple parts list as grouping its parts into one assembly. This is "
            f"raised as a question rather than a fault: PCSB to confirm which shape Bokor intends, "
            f"because it decides how the remaining {len(flat):,} should be built.",
            "Other Bokor BOMs", 0.50, "Yes"])

    df = pd.DataFrame(rows, columns=["finding", "material", "description", "detail",
                                     "evidence", "confidence", "needs_pcsb_confirmation"])

    summary = {
        "equipment_with_a_bom": len(with_bom),
        "repeated_assembly_groups": len(rows) - (1 if flat else 0),
        "assembly_numbers_involved": n_numbers,
        "equipment_with_no_assembly_node": len(flat),
        "note": "Structure, not content. Repeated assemblies are a restructuring opportunity per "
                "PTG 12.05.04 s3.5.12 - the numbers must NOT be retired as duplicate materials, "
                "because each one is in use on its own equipment's BOM. Equipment holding parts "
                "directly is reported as an open question for PCSB, not as a fault.",
    }
    return df, summary
