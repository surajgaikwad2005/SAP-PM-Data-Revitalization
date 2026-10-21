"""
Floating materials - Objective 2, "link materials never tagged to equipment".

A "floating" material was bought and charged to a maintenance job but sits on no
equipment BOM.  Filtered to Bokor that is ~1,300 rows / ~836 distinct materials.

Rather than one lookup, the agent walks four sources of evidence in order of how
trustworthy each one is and stops at the first that answers.  Every material
comes out with a confidence label, so PCSB can see what to trust and what to check.

  A  ALREADY ON A BOM   the material number is already on some equipment's BOM.
                        The strongest evidence there is - and it means the source
                        list is stale for these, which is worth telling PCSB.
  B  WORK ORDER         10 years of work-order history name the equipment the job
                        was raised against - a real "this part went to this
                        asset" event.
  C  ONE EQUIPMENT      the job's functional location holds exactly one piece of
                        equipment, so there is nothing to choose between.
  D  AI PICK            the location holds 2-10 candidates.  Claude Sonnet reads
                        the part, the candidate equipment and their manufacturers
                        and picks the best fit with a reason.  The manufacturer
                        named in the part description acts as the tie-breaker.
  E  REVIEW             location too broad or missing - a triage row, as before.

Nothing is written to SAP.  A, B and C are proposals a reviewer can accept
quickly; D needs a proper look; E needs an engineer.

Output columns: material, description, suggested_equipment, equipment_description,
how_we_know, evidence, confidence, trail, needs_pcsb_confirmation.  "how_we_know" is
written as plain English for the reader; the A-E route above is carried
separately in the internal "_route" column, which the counts key off and which
is dropped before the table is returned.
"""
from __future__ import annotations
import json

import pandas as pd

import config as C
import data
import llm

AGENT = "FLOATING_MATERIAL_LINK"
_CACHE = C.CACHE / "floating_ai_picks.json"
PROMPT_VERSION = "v1"
MAX_CANDIDATES_FOR_AI = 10          # above this the location is too broad to judge
BATCH = 8                           # materials per AI call

_SYSTEM = """You link a spare part to the equipment it belongs to, on an offshore
oil and gas platform.

You are given one spare part (its SAP description) and a short list of candidate
equipment that sit in the location where the part was used. Pick the ONE
candidate the part most likely belongs to, or say none.

Judge on:
  - what the part IS against what the equipment IS (a mechanical seal belongs to
    a pump, a fuse to a switchboard, a burner tip to a heater)
  - the manufacturer named in the part description against the equipment's
    manufacturer - a match is strong evidence
  - any model or tag code shared between the part description and the equipment

Answer with an empty equipment when nothing fits clearly. A wrong link is worse
than no link, so do not guess in order to fill the field.

Return ONLY JSON, one entry per item number given:
{"1": {"equipment": "<equipment number or empty>", "reason": "<= 12 words"}, ...}"""


# ---------------------------------------------------------------- helpers
def _short(m) -> str:
    return str(m).lstrip("0") or str(m)


def _fl_lookup(eq: pd.DataFrame):
    """Return a function: functional location -> equipment at or under it."""
    fl = eq["functional_location"].fillna("").astype(str).str.upper()

    def under(floc: str) -> list[str]:
        if not floc or floc == "NAN":
            return []
        floc = floc.upper()
        mask = (fl == floc) | fl.str.startswith(floc + "-") | fl.str.startswith(floc + ".")
        return eq.loc[mask, "equipment"].tolist()

    return under


def _field(eq_by_number, e, col) -> str:
    """Look the equipment up by its raw number, then by the zero-stripped one."""
    raw, short = eq_by_number
    for frame, keyval in ((raw, e), (short, _short(e))):
        try:
            v = frame.at[keyval, col]
            return "" if pd.isna(v) else str(v)
        except Exception:
            continue
    return ""


def _describe(eq_by_number, e) -> str:
    return _field(eq_by_number, e, "description")


def _manuf(eq_by_number, e) -> str:
    return _field(eq_by_number, e, "manufacturer")


def _ai_key(material, candidates) -> str:
    return f"{PROMPT_VERSION}|{material}|" + ",".join(sorted(c[0] for c in candidates))


def _ai_pick(items, workers, langfuse_required) -> dict:
    """items: [(material, part_description, [(equipment, description, manufacturer), ...])]"""
    if not items:
        return {}
    try:
        cache = json.loads(_CACHE.read_text(encoding="utf-8"))
    except Exception:
        cache = {}

    todo = [it for it in items if _ai_key(it[0], it[2]) not in cache]
    print(f"   {len(items) - len(todo)} cached, {len(todo)} to ask Sonnet "
          f"({-(-len(todo) // BATCH)} batches)")
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]

    def do(batch):
        lines = []
        for n, (_mat, desc, cands) in enumerate(batch, 1):
            lines.append(f'{n}. PART: "{desc}"')
            for e, ed, mf in cands:
                tail = f"  [manufacturer: {mf}]" if mf else ""
                lines.append(f'     candidate {e}: "{ed}"{tail}')
        try:
            reply = llm.chat_json(_SYSTEM, "\n".join(lines), agent=AGENT,
                                  task="link_floating_material",
                                  metadata={"n_items": len(batch)}, max_tokens=1500,
                                  langfuse_required=langfuse_required)
        except Exception:
            return {}
        out = {}
        for n, (mat, _desc, cands) in enumerate(batch, 1):
            v = reply.get(str(n)) or {}
            picked = str(v.get("equipment", "")).strip()
            valid = {c[0] for c in cands}
            out[_ai_key(mat, cands)] = {
                "equipment": picked if picked in valid else "",
                "reason": str(v.get("reason", "")).strip()[:80],
            }
        return out

    for part in llm.map_concurrent(do, batches, workers=workers):
        if isinstance(part, dict):
            cache.update(part)
    try:
        _CACHE.write_text(json.dumps(cache), encoding="utf-8")
    except Exception:
        pass
    return {it[0]: cache[_ai_key(it[0], it[2])] for it in items if _ai_key(it[0], it[2]) in cache}


# ---------------------------------------------------------------- main
def run(use_llm: bool = True, workers: int = 4, langfuse_required: bool = True):
    floating = data.floating_materials().copy()
    eq = data.equipment()
    history = data.wo_history().set_index("work_order")
    bom = data.bom_lines()

    # index on both the raw and the zero-stripped number: equipment arriving from
    # the BOM extract is zero-padded, from the equipment master it is not.
    eq_lookup = eq.drop_duplicates("equipment").set_index("equipment")
    eq_short = eq.assign(_s=eq["equipment"].map(_short)).drop_duplicates("_s").set_index("_s")
    eq_by_number = (eq_lookup, eq_short)
    under = _fl_lookup(eq)

    # method A source: every material already sitting on a BOM
    on_bom = bom.dropna(subset=["component"]).copy()
    on_bom["mat"] = on_bom["component"].map(_short)
    bom_equipment = on_bom.groupby("mat")["equipment"].agg(lambda s: sorted(set(s))[:6])

    # method B source: the work-order history, which is fuller than the
    # floating file's own location column
    floating["hist_equipment"] = floating["work_order"].map(history["wo_equipment"])
    floating["hist_floc"] = floating["work_order"].map(history["wo_functional_location"])
    floating["floc"] = floating["hist_floc"].fillna(floating["wo_functional_location"])

    rows, ai_queue = [], []
    for material, g in floating.groupby("material"):
        mat = _short(material)
        desc = g["description"].dropna().iat[0] if g["description"].notna().any() else ""
        orders = sorted(set(g["work_order"].dropna()))
        base = {"material": mat, "description": desc}

        # --- A: already on a BOM ------------------------------------------
        if mat in bom_equipment.index:
            eqs = list(bom_equipment.loc[mat])
            rows.append({**base,
                         "suggested_equipment": ", ".join(_short(e) for e in eqs),
                         "equipment_description": _describe(eq_by_number, eqs[0]),
                         "_route": "A", "evidence": "SAP record",
                         "how_we_know": "Already on this equipment's BOM in SAP",
                         "confidence": 1.00,
                         "trail": f"material number found on {len(eqs)} existing BOM(s)",
                         "needs_pcsb_confirmation": "No - already linked; the source list looks stale"})
            continue

        # --- B: the work order names the equipment ------------------------
        hist_eq = sorted({str(e) for e in g["hist_equipment"].dropna()})
        if len(hist_eq) == 1:
            e = hist_eq[0]
            rows.append({**base,
                         "suggested_equipment": _short(e),
                         "equipment_description": _describe(eq_by_number, e),
                         "_route": "B", "evidence": "SAP work-order history",
                         "how_we_know": "The work order this part was used on was raised "
                                        "against this equipment",
                         "confidence": 0.90,
                         "trail": "work order " + ", ".join(orders[:3]),
                         "needs_pcsb_confirmation": "Yes - confirm the part belongs on this BOM"})
            continue

        # Candidate equipment from the job's location.  A material used on several
        # jobs has several locations; the NARROWEST one is the most informative,
        # so we judge on that and report the rest as context.  Pooling them all
        # would only blur a precise location with a vague one.
        flocs = sorted({str(x).upper() for x in g["floc"].dropna()})
        per_loc = [(f, under(f)) for f in flocs]
        useful = [(f, lst) for f, lst in per_loc if lst]
        cands = sorted(min(useful, key=lambda t: len(t[1]))[1]) if useful else []
        where = "; ".join(f"{f} ({len(lst)} eq)" for f, lst in per_loc) \
            or "(no functional location on the work order)"

        # --- C: exactly one equipment at that location --------------------
        if len(cands) == 1:
            e = cands[0]
            rows.append({**base,
                         "suggested_equipment": _short(e),
                         "equipment_description": _describe(eq_by_number, e),
                         "_route": "C", "evidence": "SAP functional location",
                         "how_we_know": "This is the only equipment at the location where "
                                        "the work was done",
                         "confidence": 0.90,
                         "trail": where,
                         "needs_pcsb_confirmation": "Yes - confirm the part belongs on this BOM"})
            continue

        # --- D: short candidate list -> AI picks --------------------------
        if use_llm and 2 <= len(cands) <= MAX_CANDIDATES_FOR_AI:
            trio = [(e, _describe(eq_by_number, e), _manuf(eq_by_number, e)) for e in cands]
            ai_queue.append((mat, desc, trio))
            rows.append({**base, "suggested_equipment": "", "equipment_description": "",
                         "_route": "D", "how_we_know": "", "confidence": 0.75,
                         "evidence": "Other Bokor data (Agent judgement)",
                         "trail": where, "needs_pcsb_confirmation": "Yes"})
            continue

        # --- E: review ----------------------------------------------------
        rows.append({**base,
                     "suggested_equipment": ", ".join(_short(e) for e in cands[:6]) if cands else "",
                     "equipment_description": "",
                     "_route": "E", "evidence": "Nothing found yet",
                     "how_we_know": ("The work order's location covers too many equipment to tell "
                                     "which one - an engineer needs to identify it" if cands
                                     else "The work order has no usable location, so there is "
                                          "nothing to point to an equipment"),
                     "confidence": 0.40,
                     "trail": where,
                     "needs_pcsb_confirmation": "Yes - discipline engineer to identify the equipment"})

    df = pd.DataFrame(rows)

    # resolve the AI queue and fill those rows back in
    if ai_queue:
        print(f"Floating: {len(ai_queue)} materials with a short candidate list -> Agent pick")
        picks = _ai_pick(ai_queue, workers, langfuse_required)
        cand_by_mat = {m: c for m, _d, c in ai_queue}
        for i in df.index[(df["_route"] == "D") & (df["how_we_know"] == "")]:
            mat = df.at[i, "material"]
            v = picks.get(mat) or {}
            chosen = v.get("equipment", "")
            cands = [c[0] for c in cand_by_mat.get(mat, [])]
            if chosen:
                df.at[i, "suggested_equipment"] = _short(chosen)
                df.at[i, "equipment_description"] = _describe(eq_by_number, chosen)
                df.at[i, "how_we_know"] = ("Several equipment sit at that location - the Agent "
                                           "matched the part description to this one")
                df.at[i, "confidence"] = 0.75
                df.at[i, "trail"] = f"{df.at[i, 'trail']}  |  Agent: {v.get('reason', '')}"
                df.at[i, "needs_pcsb_confirmation"] = "Yes - the Agent chose between candidates; confirm"
            else:
                df.at[i, "suggested_equipment"] = ", ".join(_short(e) for e in cands[:6])
                df.at[i, "_route"] = "E"
                df.at[i, "evidence"] = "Nothing found yet"
                df.at[i, "how_we_know"] = ("Several equipment sit at that location and none clearly "
                                           "matched - an engineer needs to choose")
                df.at[i, "confidence"] = 0.40
                df.at[i, "needs_pcsb_confirmation"] = "Yes - discipline engineer to choose"

    df = df.sort_values(["confidence", "material"], ascending=[False, True])

    # Count on the internal route letter (A-E), not on the confidence score or
    # on the reader-facing wording: the letter IS the evidence path the row
    # took, so both the scores and the plain-English text stay free to change.
    route = df["_route"]
    review = int((route == "E").sum())
    n_a = int((route == "A").sum())
    n_bc = int(route.isin(["B", "C"]).sum())
    n_d = int((route == "D").sum())

    # "_route" is internal bookkeeping - it is not part of the output.
    df = df[["material", "description", "suggested_equipment", "equipment_description",
             "how_we_know", "evidence", "confidence", "trail",
             "needs_pcsb_confirmation"]].reset_index(drop=True)
    summary = {
        "floating_materials_bokor": int(df["material"].nunique()),
        "work_orders_involved": int(floating["work_order"].nunique()),
        "A_already_on_a_bom": n_a,
        "B_C_high_confidence_link": n_bc,
        "D_ai_picked_from_short_list": n_d,
        "E_left_for_engineer_review": review,
        "answered_or_proposed": int(len(df) - review),
        "note": "Evidence order: already on a BOM > work-order equipment > single equipment at the "
                "job's location > Agent pick from a short list > engineer review. Nothing is written to SAP.",
    }
    return df, summary
