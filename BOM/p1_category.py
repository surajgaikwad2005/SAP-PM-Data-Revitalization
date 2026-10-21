"""
P1 - BOM item category check.

Every BOM line must be typed correctly:
  I = assembly node (IBAU)   L = stock item   N = non-stock item   T = free text

The category is filled on every existing Bokor BOM line, so nothing here is
about blanks.  Two different faults are reported.

1. WRONG KIND - the line types an assembly as a part, or a part as an assembly.
   PMMS Training Pack 2026 p.14 shows the two side by side: an assembly (SAP
   material type IBAU) sits on the BOM as category I, and the real parts sit
   beneath it as L or N.  The material master therefore settles the category
   outright, and a majority of other BOM lines cannot overrule it.  This is the
   fault check 2 is blind to: a material typed wrongly but CONSISTENTLY on every
   BOM looks perfectly tidy to a consistency check and slips straight through.

2. INCONSISTENT - the same material is typed one way on one equipment's BOM and
   another way on another's.  Resolved by majority where there is one:
     a. SAP material type IBAU -> I.
     b. Otherwise the majority category across the BOM lines.
     c. A genuine tie is left for PCSB.

We do NOT guess stock (L) vs non-stock (N) from the material type - that needs
the MRP / valuation view, which is not in the data - so those go to PCSB.

Output columns: material, description, categories_seen, recommended, why,
confidence, needs_pcsb_confirmation.
"""
from __future__ import annotations
import pandas as pd
import data


def _recommend(cats_seen: list[str], mat_types: set[str]) -> tuple[str, str]:
    if "IBAU" in mat_types:
        return "I", ("SAP records this material as an assembly (material type IBAU), so it "
                     "should be category I on every BOM.")

    counts = pd.Series(cats_seen).value_counts()
    if len(counts) == 1:
        return counts.index[0], ("Only one category is actually used on the BOM lines, so that "
                                 "is the right one.")
    if counts.iloc[0] > counts.iloc[1]:
        top = counts.index[0]
        return top, (f"It is used as category '{top}' on {counts.iloc[0]} of {counts.sum()} BOM "
                     f"lines, so '{top}' is most likely the correct one.")
    return "", ("It is used equally often as more than one category, so there is no majority to "
                "follow. Telling a stock item from a non-stock item needs the SAP stock and "
                "costing view, which is not in the data - PCSB to decide.")


def _wrong_kind_rows(lines: pd.DataFrame) -> tuple[list, int]:
    """Lines whose category contradicts what the material actually IS.

    PMMS Training Pack 2026 p.14 shows the two kinds side by side: an assembly
    (SAP material type IBAU) sits on a BOM as category I, and a real part sits
    beneath it as L or N.  So the material type settles the category outright -
    an IBAU must be I, and anything else must never be I.

    This finds what the consistency check above cannot.  That check only fires
    when a material is typed DIFFERENTLY on different BOMs; a material typed
    wrongly but CONSISTENTLY everywhere looks perfectly tidy to it and slips
    through.  Here the answer comes from the material master, not from a vote,
    so being outnumbered does not make a line right.
    """
    rows, n_lines = [], 0
    for material, g in lines.groupby("component"):
        is_ibau = (g["material_type"] == "IBAU").any()
        cats = list(g["item_category"])
        wrong = [c for c in cats if c != "I"] if is_ibau else [c for c in cats if c == "I"]
        if not wrong:
            continue
        n_lines += len(wrong)
        desc = g["description"].dropna().mode().iat[0] if g["description"].notna().any() else ""
        seen = " / ".join(f"{c} x{cats.count(c)}" for c in sorted(set(cats)))
        if is_ibau:
            rec, why, conf = "I", (
                "SAP records this as an assembly (material type IBAU), so on a BOM it has to be "
                f"category I. It is used as {' and '.join(sorted(set(wrong)))} on "
                f"{len(wrong)} line(s), which types an assembly as though it were a part."), 0.95
        else:
            rec, why, conf = "(PCSB to decide - L or N)", (
                "This is a real part, not an assembly - SAP does not type it IBAU - so it cannot be "
                f"category I, yet it is used as I on {len(wrong)} line(s). It should be L or N; "
                "telling stock from non-stock needs the SAP stock and costing view, which is not "
                "in the data."), 0.80
        rows.append({
            "material": str(material).lstrip("0") or str(material),
            "description": desc,
            "categories_seen": seen,
            "recommended": rec,
            "why": why,
            "evidence": "SAP material master",
            "confidence": conf,
            "needs_pcsb_confirmation": "Yes",
        })
    return rows, n_lines


def run() -> tuple[pd.DataFrame, dict]:
    lines = data.bom_lines()
    lines = lines[lines["component"].notna() & lines["item_category"].notna()]

    # An assembly typed as a part, or a part typed as an assembly.  Decided by
    # the material master, so it stands regardless of what other BOMs do.
    wrong_kind, wrong_kind_lines = _wrong_kind_rows(lines)
    flagged = {r["material"] for r in wrong_kind}

    rows = list(wrong_kind)
    for material, g in lines.groupby("component"):
        if (str(material).lstrip("0") or str(material)) in flagged:
            continue                                    # already reported, with a firmer answer
        cats = sorted(set(g["item_category"]))
        if len(cats) < 2:
            continue                                    # consistent - nothing to do
        cats_all = list(g["item_category"])
        mtypes = set(g["material_type"].dropna())
        recommended, why = _recommend(cats_all, mtypes)
        rows.append({
            "material": str(material).lstrip("0") or str(material),
            "description": g["description"].dropna().mode().iat[0] if g["description"].notna().any() else "",
            "categories_seen": " / ".join(f"{c} x{cats_all.count(c)}" for c in cats),
            "recommended": recommended or "(PCSB to decide)",
            "why": why,
            "evidence": "Other Bokor BOMs",
            "confidence": 1.00 if recommended else 0.50,
            "needs_pcsb_confirmation": "No" if recommended else "Yes",
        })

    df = pd.DataFrame(rows, columns=["material", "description", "categories_seen",
                                     "recommended", "why", "evidence", "confidence",
                                     "needs_pcsb_confirmation"])
    df = df.sort_values(["needs_pcsb_confirmation", "material"], ascending=[False, True]).reset_index(drop=True)

    summary = {
        "materials_flagged": int(len(df)),
        "wrong_kind_assembly_vs_part": len(wrong_kind),
        "wrong_kind_bom_lines_affected": wrong_kind_lines,
        "materials_with_conflicting_category": int(len(df)) - len(wrong_kind),
        "auto_resolved": int((df["needs_pcsb_confirmation"] == "No").sum()),
        "left_for_pcsb": int((df["needs_pcsb_confirmation"] == "Yes").sum()),
        "note": "Two different faults. (1) WRONG KIND - the line types an assembly as a part or a "
                "part as an assembly; settled by the SAP material type (IBAU or not) per PMMS "
                "Training Pack 2026 p.14, so a majority cannot overrule it. A material typed "
                "wrongly but consistently everywhere is invisible to check (2). (2) INCONSISTENT - "
                "the same material is typed differently on different BOMs; resolved by majority "
                "where there is one, else left for PCSB.",
    }
    return df, summary
