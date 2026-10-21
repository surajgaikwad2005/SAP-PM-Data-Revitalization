"""
Load and tidy the three input files.  No business decisions here - just turn the
raw SAP extracts into clean tables the P1-P4 scripts can use.

Public functions
----------------
equipment()          one row per Bokor equipment, with plain flags
                     (needs_bom, is_nbom, is_sce, is_inactive, criticality)
bom_lines()          one row per BOM component - the messy .xlsb flattened out
bom_by_equipment()   one row per equipment that already has a BOM
floating_materials() the Bokor rows of the "floating material" list
wo_history()         10 years of Bokor work orders (order -> equipment / location)

Why bom_lines() is not trivial
------------------------------
The .xlsb is a flattened tree, not a plain line list.  For a two-level BOM the
same equipment produces:
  * one "assembly node" row  - L1ITMCAT is filled (usually 'I'), L2 empty
  * one row per child part    - L1ITMCAT blank, L1COMP just repeats the parent
                                number, and the real part sits in the L2 block
                                and the consolidated "C" block (CMATNO...).
Reading the L-columns level by level therefore invents thousands of "half
empty" lines.  bom_lines() picks the right block for each row so every output
row is one real component.
"""
from __future__ import annotations
import pandas as pd
import config as C

_SENTINELS = {"", "nan", "none", "nat", "<na>", "null"}


# ---------------------------------------------------------------- small helpers
def _blank(df: pd.DataFrame) -> pd.DataFrame:
    """Replace SAP's placeholder strings ('nan', 'NULL', ...) with a real blank."""
    for col in df.columns:
        s = df[col].astype(str).str.strip()
        df[col] = s.mask(s.str.lower().isin(_SENTINELS), pd.NA)
    return df


def _norm_key(s: pd.Series) -> pd.Series:
    """Normalise an SAP number so the same equipment matches across files
    (drop a trailing '.0' float artefact and leading zeros)."""
    out = s.astype(str).str.strip()
    out = out.mask(out.str.lower().isin(_SENTINELS), pd.NA)
    out = out.str.replace(r"\.0$", "", regex=True).str.lstrip("0")
    return out.mask(out.eq(""), pd.NA)


def _num(s: pd.Series) -> pd.Series:
    """Best-effort number parse (handles '1,000' style thousands separators)."""
    return pd.to_numeric(s.astype(str).str.replace(",", "", regex=False), errors="coerce")


# ---------------------------------------------------------------- equipment master
def equipment() -> pd.DataFrame:
    df = pd.read_excel(C.EQUIPMENT_FILE, sheet_name=C.EQUIPMENT_SHEET, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[df["Location"].astype(str).str.upper().str.strip() == C.SITE]

    rename = {
        "Equipment": "equipment",
        "Object Description": "description",
        "Functional Location": "functional_location",
        "Technical IdentNo.": "tech_ident_no",
        "ABC Indicator": "criticality",
        "User Status": "user_status",
        "System status": "system_status",
        "Manufacturer": "manufacturer",
        "Model number": "model",
    }
    df = _blank(df.rename(columns=rename)[list(rename.values())].copy())

    us = df["user_status"].fillna("").str.upper()
    sys_ = df["system_status"].fillna("").str.upper()

    df["key"] = _norm_key(df["equipment"])
    # criticality: keep only 1 / 2 / 3
    df["criticality"] = df["criticality"].where(df["criticality"].isin(["1", "2", "3"]))
    # SAP User Status flags (space-separated tokens like "ACT BOM PLAN SCE")
    df["needs_bom"] = us.str.contains(r"\bBOM\b") & ~us.str.contains("NBOM")
    df["is_nbom"] = us.str.contains("NBOM")           # BOM formally waived
    df["is_sce"] = us.str.contains("SCE")
    df["is_inactive"] = sys_.str.contains("INAC") | df["description"].fillna("").str.upper().str.startswith("DEAC")

    if C.DEMO_MODE:
        # Include key SPIR matched equipment so draft_bom.py works cleanly in demo mode
        spir_target_keys = {"11061994", "11061995", "11057589"}
        sample_parts = [df[df["key"].isin(spir_target_keys)]]
        n_per_tier = max(5, C.DEMO_SIZE // 5)
        for tier_mask in [df["is_sce"], df["criticality"] == "1", df["criticality"] == "2", df["criticality"] == "3", ~df["is_sce"] & df["criticality"].isna()]:
            sub = df[tier_mask]
            if len(sub):
                sample_parts.append(sub.head(n_per_tier))
        demo_df = pd.concat(sample_parts, ignore_index=True).drop_duplicates("key")
        if len(demo_df) < C.DEMO_SIZE and len(df) > len(demo_df):
            extra = df[~df["key"].isin(demo_df["key"])].head(C.DEMO_SIZE - len(demo_df))
            demo_df = pd.concat([demo_df, extra], ignore_index=True)
        df = demo_df

    return df.reset_index(drop=True)


# ---------------------------------------------------------------- classification
def equipment_classification() -> pd.DataFrame:
    """SAP classification - one row per equipment per characteristic.

    Carries the equipment CLASS (ICTR, ICSW, ...) and its technical
    characteristics (Type, Body material, Set point, ...).  Useful where the
    equipment master's manufacturer and model are blank: two equipment of the
    same class and the same "Type" are the same kind of thing, which is weaker
    evidence than a shared make and model but far better than nothing.

    ~377,000 rows, so the parse is cached like the BOM extract.
    """
    cache = C.CACHE / "equipment_class.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = pd.read_excel(C.CLASSIFICATION_FILE, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    out = pd.DataFrame({
        "key": _norm_key(df["EQ.NUMBER"]),
        "equipment_class": df["CLASS"].astype(str).str.strip(),
        "characteristic": df["CHAR.DESC"].astype(str).str.strip(),
        "value": df["CHAR.VALUE"].astype(str).str.strip(),
    })
    out = out[out["key"].notna() & out["equipment_class"].notna()].reset_index(drop=True)
    try:
        out.to_parquet(cache)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------- material master
def material_master() -> pd.DataFrame:
    """SAP material master for the Bokor plant - one row per material.

    The stock item export carries every plant; a material's unit and status are
    set per plant, so only C.PLANT's rows are kept.  Returns an empty frame if
    the file has not been supplied, so a caller can skip its check rather than
    fail.

    ~540,000 rows in the workbook, so the parse is cached like the BOM extract.
    """
    cols = ["material", "description", "uom", "part_number", "material_status", "material_type",
            "stock_on_hand"]
    cache = C.CACHE / "material_master_v2.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    if not C.MATERIAL_MASTER_FILE.exists():
        return pd.DataFrame(columns=cols)
    df = pd.read_excel(C.MATERIAL_MASTER_FILE, sheet_name=C.MATERIAL_MASTER_SHEET, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[df["Plant"].astype(str).str.strip().str.startswith(C.PLANT)]
    df = _blank(df.copy())
    out = pd.DataFrame({
        "material": _norm_key(df["Material"]),
        "description": df["Description Line 1"],
        "uom": df["UOM"].astype("string").str.upper().str.strip(),
        "part_number": df["Part Number 1"],
        "material_status": df["Current Material Status"],
        "material_type": df["Material Type"],
        "stock_on_hand": _num(df["Stock on Hand"]).fillna(0),
    })
    out = out[out["material"].notna()].drop_duplicates("material").reset_index(drop=True)
    try:
        out.to_parquet(cache)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------- raw BOM (.xlsb)
def _bom_raw() -> pd.DataFrame:
    cache = C.CACHE / "bom_raw.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = pd.read_excel(C.BOM_FILE, sheet_name=C.BOM_SHEET, engine="pyxlsb", dtype=str)
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = _blank(df)
    df["key"] = _norm_key(df["EQNO"])
    try:
        df.to_parquet(cache)
    except Exception:
        pass
    return df


# ---------------------------------------------------------------- tidy BOM lines
def bom_lines() -> pd.DataFrame:
    """One row per real BOM component (see module docstring for the why)."""
    raw = _bom_raw()

    has_c = raw["CMATNO"].notna()             # the consolidated component block is filled
    has_l1 = raw["L1ITMCAT"].notna()          # this row describes an L1 item directly

    def pick(c_col, l1_col, l2_col):
        """Take the C block if present, else the L1 block, else the L2 block."""
        out = raw[c_col].where(has_c)
        out = out.fillna(raw[l1_col].where(has_l1))
        return out.fillna(raw[l2_col])

    lines = pd.DataFrame({
        "equipment": raw["EQNO"],
        "key": raw["key"],
        "item_category": pick("CITMCAT", "L1ITMCAT", "L2ITMCAT"),
        "component": pick("CMATNO", "L1COMP", "L2COMP"),
        "description": pick("CMATDESC", "L1COMPDESC", "L2COMPDESC"),
        "quantity": _num(pick("CQTY", "L1QTY", "L2QTY")),
        "uom": pick("CUOM", "L1UNIT", "L2UNIT"),
        "material_type": pick("CMMATTYPE", "L1MATTYPE", "L2MATTYPE"),
        "material_group": raw["CMATGRP"].where(has_c),
        # 90% populated and worth carrying: two materials built by unrelated
        # manufacturers are unlikely to be the same part (P2 uses it as a
        # caution, not a rule - see the alias problem noted there).
        "manufacturer": raw["MANUF"],
    })
    lines["item_category"] = lines["item_category"].astype("string").str.upper().str.strip()
    # an "assembly node" is an L1 row typed 'I' - it groups the child parts
    lines["is_assembly_node"] = has_l1.values & lines["item_category"].eq("I")
    # a line is "complete" when it can actually be uploaded to SAP
    is_text = lines["item_category"].eq("T")
    is_material = lines["item_category"].isin(C.MATERIAL_CATEGORIES)
    lines["is_complete"] = (
        (is_text & lines["description"].notna())
        | (is_material & lines["component"].notna() & lines["uom"].notna() & (lines["quantity"] > 0))
    )
    return lines[lines["key"].notna()].reset_index(drop=True)


def bom_by_equipment() -> pd.DataFrame:
    """One row per equipment that already has a BOM in the .xlsb."""
    lines = bom_lines()
    g = lines.groupby("key").agg(
        equipment=("equipment", "first"),
        bom_lines=("component", "size"),
        assembly_nodes=("is_assembly_node", "sum"),
        incomplete_lines=("is_complete", lambda s: int((~s).sum())),
    ).reset_index()
    g["has_bom"] = True
    return g


# ---------------------------------------------------------------- floating materials
def floating_materials() -> pd.DataFrame:
    df = pd.read_excel(C.FLOATING_FILE, sheet_name=C.FLOATING_SHEET, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    df = _blank(df)
    df = df[df["Location"].astype(str).str.upper().str.strip() == C.SITE]
    out = df.rename(columns={
        "Work Order": "work_order",
        "Historical - WO_Functional Loc.": "wo_functional_location",
        "Equipment": "wo_equipment",
        "Material": "material",
        "Material Description": "description",
    })[["work_order", "wo_functional_location", "wo_equipment", "material", "description"]]
    out["material"] = _norm_key(out["material"])
    out["work_order"] = _norm_key(out["work_order"])
    if C.DEMO_MODE:
        top_mats = out["material"].dropna().unique()[:30]
        out = out[out["material"].isin(top_mats)]
    return out.reset_index(drop=True)


# ---------------------------------------------------------------- work-order history
def wo_history() -> pd.DataFrame:
    """One row per work order: the equipment and functional location it was raised against.

    The floating-material list only carries a thin functional-location column.
    This 10-year extract covers 241 of the 263 floating work orders and, for
    80% of all orders, names the actual equipment - which is the strongest
    evidence available for where a floating part belongs.
    """
    cache = C.CACHE / "wo_history.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    df = pd.read_excel(C.WO_HISTORY_FILE, sheet_name=C.WO_HISTORY_SHEET, dtype=str)
    df.columns = [str(c).strip() for c in df.columns]
    df = _blank(df)
    out = pd.DataFrame({
        "work_order": _norm_key(df["Order"]),
        "wo_equipment": df["Equipment"],
        "wo_functional_location": df["Functional Location"],
        "wo_description": df.get("Description"),
    })
    out = out[out["work_order"].notna()].drop_duplicates("work_order").reset_index(drop=True)
    try:
        out.to_parquet(cache)
    except Exception:
        pass
    return out
