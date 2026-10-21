"""
Draft BOM - turn extracted SPIR spare-parts data into proposed BOM lines.

This is the step that closes the loop: P4 says WHICH equipment need a BOM,
and this says WHAT GOES ON IT for the equipment we hold a SPIR sheet for.

Three things happen here, all deterministic - no model is called.

1. LINK the vendor's tag to a SAP equipment number.
   A dossier calls a machine "E-2430 A/B"; SAP calls it 11061994.  The bridge is
   the functional location, whose last segment IS the project tag:
       BOCP.GCO.BC1.E2430A-E2430A   ->  tag E2430A
   An "A/B" suffix means two units, so it expands to E2430A and E2430B.
   Matching is on the LAST segment only.  Matching anywhere in the string is
   wrong: "E2430A" also appears in BOCP.GCO.BC1.E2430A-243PG118, which is a
   pressure gauge mounted ON the cooler, not the cooler.

2. BUILD a proposed line per spare part - description, quantity, UOM.

3. FLAG what a human still has to settle.  Nothing here is loadable into SAP
   as-is, and the sheet says so on every row: see "material_action" below.

Why no line has a material number
---------------------------------
A BOM line of category L or N must point at a material master record.  The MESC
number column is blank on every SPIR sheet we hold - not an extraction failure,
the column is empty on the source, because MESC codes are assigned by PETRONAS
and the vendor filling in the form does not have them.  So each part must first
be created in the material master (MDG), and until then the only category that
will load is T (text item).  Each row therefore carries:
    proposed_item_category = T        - what can be loaded today
    material_action                   - what has to happen for it to become L/N
"""
from __future__ import annotations
import re

import pandas as pd

import config as C
import data
import spir_store


def _norm(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(text).upper())


def _is_placeholder(value: str) -> bool:
    """'-', 'N/A', 'N.A.', 'NIL' ... - the vendor's way of leaving a cell empty."""
    return re.sub(r"[^A-Z0-9]", "", str(value).upper()) in ("", "NA", "NIL")


def _part_number(row: dict) -> str:
    """The best part number on a row.

    The manufacturer and supplier part-number columns sit next to a brand-name
    column on the form, and on some sheets the brand lands in one of them.  A
    real part number carries a digit, so prefer a value that has one.
    """
    candidates = [str(row.get("manufacturer_part_no") or "").strip(),
                  str(row.get("supplier_part_no") or "").strip()]
    candidates = [c for c in candidates if not _is_placeholder(c)]
    for c in candidates:
        if any(ch.isdigit() for ch in c):
            return c
    return candidates[0] if candidates else ""


def expand_tag(tag: str) -> list[str]:
    """'E-2430 A/B' -> ['E2430A', 'E2430B'];  '402 XV-180' -> ['402XV180'].

    A trailing 'A/B' on a vendor tag means the document covers two identical
    units, each of which is its own equipment record in SAP.
    """
    t = str(tag or "").upper().strip()
    if not t:
        return []
    m = re.search(r"\s*([A-Z])\s*/\s*([A-Z])\s*$", t)
    if m:
        stem = _norm(t[:m.start()])
        return [stem + m.group(1), stem + m.group(2)]
    return [_norm(t)]


# One header can name several machines: "P-4027 A/B, P-4029 A/B & 403QA-101".
_TAG_SPLIT = re.compile(r"\s*(?:[,;]|&| and )\s*", re.I)

# What a tag looks like: one to four letters, an optional dash or space, three to
# five digits, and an optional unit letter - V-2430A, 403QA-101, K 6850, P5310A.
# A trailing "/B" is kept ("A-5230A/B"), because expand_tag turns that into both
# units; dropping it would link the A machine and quietly lose the B one.
_TAG_IN_TEXT = re.compile(r"\b([A-Z]{1,4}\s*-?\s*\d{3,5}\s*[A-Z]{0,2}(?:\s*/\s*[A-Z])?)\b")


def split_tags(header: str) -> list[str]:
    """Split a tag header into the individual tags it names.

    A sheet shared across a whole train writes them on one line.  Left whole the
    string normalises to one long token that can never match anything, so the
    sheet contributes nothing at all.
    """
    parts = [p.strip() for p in _TAG_SPLIT.split(str(header or ""))]
    return [p for p in parts if p]


def tags_in_description(desc: str) -> list[str]:
    """Tag-looking tokens sitting inside an equipment description.

    Many sheets leave the tag box empty and write the tag into the equipment
    name instead: "V-2430A 3rd Stage Gaslift Compressor Suction Scrubber".  Used
    only as a fallback, and only a candidate that resolves to real SAP equipment
    is ever accepted - a model number that happens to look like a tag matches
    nothing and is dropped.
    """
    return [m.group(1) for m in _TAG_IN_TEXT.finditer(str(desc or "").upper())]


# Character slips the vision model makes inside tags, each seen on real sheets:
#   a digit 1 read as the letter I  - "24ISDV-101" for 241SDV-101
#   a V read as Y before the dash   - "251BDY-105" for 251BDV-105
_MISREADS = ((re.compile(r"(?<=\d)I(?=[A-Z])"), "1"),
             (re.compile(r"(?<=[A-Z]{2})Y(?=\s*-)"), "V"))


def misread_fix(tag: str) -> str:
    """The tag with the known misreads undone.  Only ever used when the tag as
    read names nothing in SAP AND the corrected one names real equipment."""
    t = str(tag or "").upper()
    for pattern, repl in _MISREADS:
        t = pattern.sub(repl, t)
    return t


def _clean_tid(raw_tid: str) -> list[str]:
    """Clean a Technical IdentNo value to extract candidate tag keys.
    e.g. 'BOPA-V100A-V' -> ['V100A', 'BOPAV100AV']
         'BOCP-402XV180' -> ['402XV180', 'BOCP402XV180']
    """
    if not raw_tid or pd.isna(raw_tid):
        return []
    raw = str(raw_tid).strip().upper()
    keys = [_norm(raw)]
    s1 = re.sub(r"^BO[A-Z]{1,3}[_\-]", "", raw)
    if s1 != raw:
        s2 = re.sub(r"[_\-][A-Z]$", "", s1)
        k1, k2 = _norm(s1), _norm(s2)
        if k1:
            keys.append(k1)
        if k2:
            keys.append(k2)
    return list(dict.fromkeys(keys))


def _equipment_index(eq: pd.DataFrame) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    """Returns (floc_index, tid_index) - hybrid matching on FLOC last segment and Technical IdentNo."""
    floc_idx: dict[str, list[dict]] = {}
    tid_idx: dict[str, list[dict]] = {}
    for rec in eq.to_dict("records"):
        floc = str(rec.get("functional_location") or "")
        if floc:
            last = _norm(re.split(r"[.\-]", floc)[-1])
            if last:
                floc_idx.setdefault(last, []).append(rec)
        tid = str(rec.get("tech_ident_no") or "")
        if tid:
            for k in _clean_tid(tid):
                tid_idx.setdefault(k, []).append(rec)
    return floc_idx, tid_idx


def _quantity(row: dict, page_constant: bool) -> tuple[str, str, str]:
    """(quantity, confidence, note) for one part.

    The correct source is the form's "TOTAL NO. OF IDENTICAL PARTS INSTALLED".
    Where that is blank we fall back to "no. of parts per unit".

    One guard on that fallback.  On some scanned sheets the per-part column is
    empty and the header's "NO. OF UNITS" (how many machines the document
    covers) gets read into every row instead.  The tell is the same value
    repeated down the whole page - but only when that value is not 1, because a
    sheet where every part is fitted once is perfectly ordinary.  A repeated
    value of 2 or more is reported as not stated rather than invented.
    """
    installed = str(row.get("total_qty_installed") or "").strip()
    if installed:
        return installed, "high", ("Quantity taken from the 'total no. of identical parts "
                                   "installed' column of the vendor's SPIR sheet.")

    per_unit = str(row.get("no_of_parts_per_unit") or "").strip()
    if per_unit:
        if page_constant and per_unit not in ("1", "1.0"):
            return "", "review", (f"No quantity given. Every row on this page reads '{per_unit}', "
                                  f"which is almost certainly how many machines the document "
                                  f"covers rather than how many of this part are fitted, so no "
                                  f"quantity has been assumed.")
        return per_unit, "high", ("Quantity taken from the 'no. of parts per unit' column, because "
                                  "the total-installed column was blank.")
    return "", "review", "The vendor's SPIR sheet does not state a quantity for this part."


def _consolidate(df: pd.DataFrame) -> pd.DataFrame:
    """One BOM per equipment: merge repeated parts, renumber items.

    A dossier often carries the same spare-parts sheet more than once (a
    revision, or the same sheet filed under two sections).  Left alone that puts
    the same part on the BOM twice, with item numbers restarting at 0010 on
    every page.  So parts are keyed on description + part number and merged.

    Where two copies of a part disagree on quantity, the disagreement is
    REPORTED, not silently resolved - the row is flagged for review and both
    values are shown.  Picking one would be guessing at which sheet revision is
    current, and that is PCSB's call.
    """
    out = []
    for equip, block in df.groupby("sap_equipment", sort=False):
        if equip == "":                      # unmatched rows keep their own shape
            out.append(block)
            continue
        merged: dict[tuple, dict] = {}
        for rec in block.to_dict("records"):
            key = (_norm(rec["component_description"]), _norm(rec["part_number"]))
            first = merged.get(key)
            if first is None:
                rec["seen_on_pages"] = str(rec["source_page"])
                merged[key] = rec
                continue
            first["seen_on_pages"] += f", {rec['source_page']}"
            a, b = str(first["quantity"]).strip(), str(rec["quantity"]).strip()
            if a and b and a != b:
                first["quantity"] = f"{a} or {b}"
                # Numeric, like every other confidence on the sheet, so the column
                # stays sortable.  Below 0.70 is "engineer action needed" on the
                # scale printed at the top of the sheet; the Remark says why.
                first["confidence"] = C.CONF_CONFLICT
                first["note"] = (f"Two copies of this sheet disagree on the quantity: page "
                                 f"{first['source_page']} says {a} and page {rec['source_page']} "
                                 f"says {b}. Both are shown - PCSB to confirm which is current.")
            elif b and not a:
                first["quantity"] = b
                first["confidence"] = rec["confidence"]
                first["note"] = rec["note"]
        rows = list(merged.values())
        for n, rec in enumerate(rows, start=1):
            rec["item"] = f"{n * 10:04d}"
        out.append(pd.DataFrame(rows))
    res = pd.concat(out, ignore_index=True)
    if "seen_on_pages" not in res.columns:
        res["seen_on_pages"] = ""
    res["seen_on_pages"] = res["seen_on_pages"].fillna(res["source_page"].astype(str))
    return res


def _add_assembly_nodes(df: pd.DataFrame) -> pd.DataFrame:
    """Give each drafted BOM the shape SAP expects, instead of a flat list.

    PMMS Training Pack 2026 p.14: an equipment BOM carries the ASSEMBLY as its
    item (material type IBAU, category I, quantity 1, unit SET), and the parts
    hang beneath the assembly, not off the equipment.  Drafting the parts
    straight onto the equipment produces a shape the BOM-structure check would
    itself flag, so the assembly node is drafted too.

    The assembly does not exist in SAP either - it is created with MMP1, the
    same way the parts are created in the material master - so it is proposed
    here rather than assumed, and numbered on its own scope: the assembly is
    item 0010 of the equipment BOM, and the parts restart at 0010 beneath it.
    """
    out = []
    for equip, block in df.groupby("sap_equipment", sort=False):
        block = block.copy()
        if equip == "":                      # unmatched tags keep their own shape
            block["bom_level"] = "-"
            out.append(block)
            continue
        first = block.iloc[0]
        node = {c: "" for c in block.columns}
        node.update({
            "sap_equipment": equip,
            "equipment_description": first["equipment_description"],
            "functional_location": first["functional_location"],
            "existing_bom": first["existing_bom"],
            "vendor_tag": first["vendor_tag"],
            "bom_level": "1 - Assembly",
            "item": "0010",
            "component_description": f"ASSEMBLY, {first['equipment_description']}".strip().rstrip(","),
            "quantity": "1",
            "uom": "SET",
            "proposed_item_category": "I",
            "material_number": "",
            "material_action": ("Create as assembly (MMP1), attach to equipment (IB01), "
                                "then build the parts below it (CS01)"),
            "source_document": first["source_document"],
            "source_page": first["source_page"],
            "evidence": "Proposed by the agent",
            "confidence": 0.70,
            "note": (f"The parts found for this equipment are grouped under one assembly, which is "
                     f"the shape a parts list is meant to have - the equipment carries the "
                     f"assembly, and the assembly carries the parts. Proposed, not found: no "
                     f"assembly exists for this equipment today."),
            "needs_pcsb_confirmation": "yes",
        })
        block["bom_level"] = "2 - Part"
        out.append(pd.concat([pd.DataFrame([node]), block], ignore_index=True))
    return pd.concat(out, ignore_index=True)


def run() -> tuple[pd.DataFrame, dict]:
    parts = spir_store.parts()
    eq = data.equipment()
    floc_idx, tid_idx = _equipment_index(eq)

    # How many BOM lines each equipment already has, so a draft is never
    # presented as filling a gap that is in fact already filled.
    existing = data.bom_by_equipment().set_index("key")["bom_lines"].to_dict()

    # A quantity column is trustworthy when it varies down the page.
    page_constant: dict[tuple, bool] = {}
    if len(parts):
        for key, block in parts.groupby(["source_pdf", "source_page"]):
            vals = {str(v).strip() for v in block["no_of_parts_per_unit"] if str(v).strip()}
            page_constant[key] = len(vals) == 1 and len(block) > 1

    rows: list[dict] = []
    linked_equipment: set[str] = set()
    unlinked_tags: set[str] = set()
    multi_equipment_sheets: list[str] = []

    def _resolve(tag_strings: list[str]) -> tuple[list[dict], bool]:
        """Every SAP equipment named by these tags, and whether a TID match was used.

        Deduplicated on the equipment number: one header can name the same machine
        twice, and a sheet must not be drafted onto it twice.
        """
        found: list[dict] = []
        via_tid = False
        seen: set[str] = set()
        for one in tag_strings:
            for key in expand_tag(one):
                hits = floc_idx.get(key, [])
                if not hits:
                    hits = tid_idx.get(key, [])
                    if hits:
                        via_tid = True
                for rec in hits:
                    ident = str(rec.get("equipment"))
                    if ident not in seen:
                        seen.add(ident)
                        found.append(rec)
        return found, via_tid

    for (pdf, page), block in parts.groupby(["source_pdf", "source_page"], sort=True):
        tag = str(block["equipment_tag"].iloc[0] or "").strip()
        header_desc = str(block["equipment_description"].iloc[0] or "").strip()
        sheet_ref = f"{pdf.split(chr(92))[-1]} p{page}"

        tag_list = split_tags(tag)
        # A tag naming nothing in SAP may be a misread of one that does.  Each tag
        # is corrected on its own, and only when the corrected form resolves.
        fixes = {}
        for t in tag_list:
            fix = misread_fix(t)
            if fix != t.upper() and not _resolve([t])[0] and _resolve([fix])[0]:
                fixes[t] = fix
        tag_list = [fixes.get(t, t) for t in tag_list]
        matches, matched_via_tid = _resolve(tag_list)
        matched_via_fix = bool(fixes)
        matched_via_desc = False

        # Fallback: the tag box is blank, or names nothing SAP recognises, but the
        # equipment NAME carries the tag - "V-2430A 3rd Stage ... Suction Scrubber".
        # Only a candidate that resolves to real equipment is ever accepted.
        if not matches:
            desc_tags = tags_in_description(header_desc)
            if desc_tags:
                found, via_tid = _resolve(desc_tags)
                if found:
                    matches, matched_via_tid = found, via_tid
                    matched_via_desc = True
                    tag_list = desc_tags

        # A sheet naming several DIFFERENT kinds of machine cannot be apportioned:
        # nothing on the page says which part belongs to which machine.  Copying
        # every part onto all of them would invent BOMs, so the sheet is reported
        # for a planner to split rather than drafted.
        several_kinds = (len(tag_list) > 1
                         and len({_norm(m.get("description")) for m in matches}) > 1)
        if several_kinds:
            multi_equipment_sheets.append(
                f"{sheet_ref}: covers {len(matches)} different equipment")
            matches = []

        if not matches and not several_kinds:
            unlinked_tags.add(tag or f"(no tag on {sheet_ref})")

        if several_kinds:
            unmatched_note = (
                "This one sheet covers several different machines, and nothing on the "
                "page says which part belongs to which. The parts are listed here so "
                "they are not lost, but the agent will not guess - a planner has to "
                "split this sheet between the machines it names.")
        else:
            unmatched_note = ("The vendor's tag on this sheet could not be matched to any "
                              "equipment in SAP, so there is nothing to attach this part to yet.")

        # One proposed BOM per matched equipment; an A/B sheet fills both.
        targets = matches or [None]
        for target in targets:
            if target is not None:
                linked_equipment.add(str(target["equipment"]))
            for n, (_, part) in enumerate(block.iterrows(), start=1):
                p = part.to_dict()
                qty, qconf, qnote = _quantity(p, page_constant.get((pdf, page), False))
                if target is not None:
                    if matched_via_desc:
                        link_note = ("The tag box on this sheet was blank, so the equipment was "
                                     "matched on the tag written inside the equipment name. "
                                     "Worth a second look before this BOM is built.")
                    elif matched_via_fix:
                        link_note = (f"The vendor's tag was read as {', '.join(fixes)}, which is "
                                     f"not in SAP; read as {', '.join(fixes.values())} it is - a "
                                     f"1 misread as I, or a V as Y. Worth a quick check against "
                                     f"the sheet.")
                    elif matched_via_tid:
                        link_note = ("The equipment was matched on its Technical IdentNo rather "
                                     "than its functional location.")
                    else:
                        link_note = ""
                    if link_note:
                        qnote = f"{qnote} {link_note}" if qnote else link_note
                # A dash or "N/A" in the MESC column means the vendor left it
                # blank, not that the part carries that number - same placeholders
                # _part_number guards against.
                mesc = str(p.get("mesc_number") or "").strip()
                if _is_placeholder(mesc):
                    mesc = ""
                had = existing.get(target["key"], 0) if target is not None else 0
                if target is None:
                    conf_val = 0.40
                elif matched_via_desc:
                    conf_val = 0.75
                elif matched_via_fix:
                    conf_val = 0.80
                elif matched_via_tid:
                    conf_val = 0.85
                else:
                    conf_val = 0.90 if qconf == "high" else 0.50
                rows.append({
                    "sap_equipment": target["equipment"] if target is not None else "",
                    "equipment_description": target["description"] if target is not None else "",
                    "functional_location": target["functional_location"] if target is not None else "",
                    "existing_bom": ("no BOM today - this fills a gap" if target is not None and not had
                                     else f"ALREADY HAS {had} BOM lines - compare, do not just add"
                                     if target is not None else ""),
                    "vendor_tag": tag,
                    "item": f"{n * 10:04d}",
                    "component_description": p.get("description") or "",
                    "quantity": qty,
                    "uom": p.get("unit") or "",
                    "proposed_item_category": "T",
                    "material_number": mesc,
                    # Kept short on purpose: the same sentence repeats on almost
                    # every row, so the full explanation lives once in the Basis
                    # note at the top of the sheet instead of 200 times down it.
                    "material_action": ("Has a MESC number - confirm it exists in SAP"
                                        if mesc else
                                        "Create in material master (MDG) first"),
                    "manufacturer": p.get("supplier_brand") or p.get("manufacturer") or "",
                    "part_number": _part_number(p),
                    "material_spec": p.get("material_spec") or "",
                    "source_document": str(pdf).split("\\")[-1],
                    "source_page": page,
                    "spir_sheet": p.get("spir_number") or "",
                    "spir_type": p.get("doc_type") or "",
                    "evidence": ("Vendor document (SPIR)" if target is not None
                                 else "Nothing found yet"),
                    "confidence": conf_val,
                    "note": unmatched_note if target is None else qnote,
                    "needs_pcsb_confirmation": "yes",
                })

    df = pd.DataFrame(rows)
    if len(df):
        df = df.sort_values(["sap_equipment", "source_page", "item"], kind="stable").reset_index(drop=True)
        df = _consolidate(df)
        # The linked equipment are the result; the tags we could not place go
        # last, so a reader sees the BOMs before the loose ends.
        df["_unlinked"] = (df["sap_equipment"] == "").astype(int)
        df = (df.sort_values(["_unlinked", "sap_equipment", "source_page", "item"], kind="stable")
                .drop(columns="_unlinked").reset_index(drop=True))
        df = _add_assembly_nodes(df)
        cols = ["bom_level"] + [c for c in df.columns if c != "bom_level"]
        df = df[cols]

    backlog = data_backlog(eq)
    # Count the parts and the assemblies separately: an assembly node is drafted
    # by us to give the list its shape, not read off a vendor sheet, so folding
    # it into "parts drafted" would overstate what the documents actually gave.
    linked = (df["sap_equipment"] != "") if len(df) else pd.Series(dtype=bool)
    is_part = linked & (df["bom_level"] == "2 - Part") if len(df) else linked
    is_node = linked & (df["bom_level"] == "1 - Assembly") if len(df) else linked
    summary = {
        "spir_pages_held": int(parts.groupby(["source_pdf", "source_page"]).ngroups) if len(parts) else 0,
        "spare_parts_read": int(len(parts)),
        "equipment_linked": len(linked_equipment),
        "equipment_linked_in_backlog": len(linked_equipment & backlog),
        "draft_bom_lines": int(is_part.sum()) if len(df) else 0,
        "draft_assembly_nodes": int(is_node.sum()) if len(df) else 0,
        "lines_without_quantity": int((is_part & (df["quantity"] == "")).sum()) if len(df) else 0,
        "lines_needing_material_creation": int((is_part & (df["material_number"] == "")).sum()) if len(df) else 0,
        "sheets_covering_several_equipment": sorted(multi_equipment_sheets),
        "vendor_tags_not_matched": sorted(unlinked_tags),
    }
    return df, summary


def data_backlog(eq: pd.DataFrame) -> set[str]:
    """Equipment that need a BOM and have none - the P4 backlog.

    Join on 'key', not on 'equipment'.  The BOM extract writes some equipment
    numbers zero-padded ("000000000010991834") and others bare, so matching the
    raw column drops more than half the BOMs and inflates the backlog.  'key' is
    the normalised form, and every one of the 5,379 BOMs matches on it.
    """
    have = set(data.bom_by_equipment()["key"])
    sel = eq[eq["needs_bom"] & ~eq["key"].isin(have)]
    return set(sel["equipment"].astype(str))


if __name__ == "__main__":
    import json
    df, s = run()
    print(json.dumps(s, indent=2))
    print(df.to_string())
