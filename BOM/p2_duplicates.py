"""
P2 - duplicate / near-duplicate materials, on the MATERIAL MASTER.

Question answered: "Which material numbers are really the same physical part?"

The pool is SAP's material master for the Bokor plant (data.material_master()),
not the materials that happen to sit on a BOM: a duplicate is a fault in the
catalogue, and most of the catalogue is not on any BOM.

What the material master gives us to identify a part is thin - a description
cut off at 40 characters and a manufacturer part number filled on about a
quarter of the rows - so every group is graded by how much of that evidence
agrees, and the grade is the confidence shown on the sheet:

  HIGH    same description AND same part number.  The only grade that goes
          into the merge map.
  MEDIUM  same description, part number on some of the materials only (none
          conflicting);  or same part number under descriptions that differ
          only in wording.
  LOW     same description and no part number at all to confirm it.

A part number shared by descriptions that differ in a size, rating or code
(safety boots in sizes 5, 7 and 8 under one model number) is a model number,
not a duplicate: the strict rule already calls those different parts, so they
are counted in the summary and kept off the sheet.

"Same description" means identical once the usual abbreviations are spelled
out, punctuation is dropped and word order is ignored - the same notation-only
standard the strict rule below uses.

Two things keep materials apart whatever the description says: a different
unit of measure, and different part numbers.

Tier 2 - LOOK-ALIKES.  Descriptions that are close but not identical.  The
strict rule decides almost all of them mechanically (see strict_prefilter); the
few it cannot are shown to Claude Sonnet under the same STRICT standard as
before, every call traced in Langfuse under agent name "P2_MATERIAL_DEDUP".
With use_llm=False the pairs are counted and reported but nobody is asked, so
the size of the job is known before anything is spent.

The cost of a wrong merge is a wrong spare fitted to running equipment; the
cost of a missed merge is a duplicate that survives.  We take the second.

Assemblies (SAP material type IBAU) are created per equipment by design and are
not in the stock item export at all, so they never reach this check.  Whether
the same assembly has been needlessly repeated is a BOM STRUCTURE question
(bom_structure.py), with a different remedy.

Verdicts are cached on disk (_cache/p2_llm_verdicts.json), keyed by the
description pair AND the prompt version, so tightening the rule invalidates the
old verdicts automatically.

Output columns: keep_material, keep_description, retire_materials, basis,
confidence, needs_pcsb_confirmation.  Also returns merge_map {retired -> keep}
for the HIGH groups only.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections import Counter, defaultdict

import pandas as pd
from rapidfuzz import fuzz

import config as C
import data
import llm

AGENT = "P2_MATERIAL_DEDUP"
FUZZY_MIN = 88
BATCH = 20
_CACHE = C.CACHE / "p2_llm_verdicts.json"
# Bump when the adjudication rule changes - it is part of the cache key, so old
# verdicts are ignored rather than silently reused under a new rule.
PROMPT_VERSION = "v2-strict"

CONF_HIGH, CONF_MEDIUM, CONF_LOW = 0.95, 0.70, 0.40

# The stock item export stops a description at this many characters, so a
# description of exactly this length may have lost the size or rating that
# would tell two materials apart.
DESCRIPTION_LIMIT = 40

# A part number shorter than this is a code fragment, not an identifier.
_PN_MIN_LEN = 4
# One part number sitting under this many different descriptions is a generic
# value ("VARIOUS", a vendor code), not evidence that the materials are one part.
_PN_MAX_DESCRIPTIONS = 6

# Materials already on their way out are not duplicates to raise again.
_RETIRED = re.compile(r"MARKED FOR DELETION|DO NOT USE|\bDELETE\b|\bOBSOLETE\b")

_ABBREV = {
    r"\bVLV\b": "VALVE", r"\bGKT\b": "GASKET", r"\bGSKT\b": "GASKET", r"\bBRG\b": "BEARING",
    r"\bASSY\b": "ASSEMBLY", r"\bSS\b": "STAINLESS STEEL", r"\bCS\b": "CARBON STEEL",
    r"\bSPW\b": "SPIRAL WOUND", r"\bCPLG\b": "COUPLING", r"\bSCR\b": "SCREW", r"\bWSHR\b": "WASHER",
    r"\bHEX\b": "HEXAGON", r"\bSKT\b": "SOCKET", r"\bELEM\b": "ELEMENT", r"\bELMNT\b": "ELEMENT",
    r'"': " INCH ", r"#": " CLASS ",
}
_ABB = [(re.compile(p), v) for p, v in _ABBREV.items()]

_SYSTEM = """You compare pairs of SAP spare-part descriptions (coded short text:
TYPE,SPEC,SPEC,SIZE,MATERIAL,...). Decide whether the two descriptions denote
the SAME physical part, so that one material master could safely replace both.

Apply a STRICT standard. A wrong merge means the wrong spare is fitted to
running offshore equipment. A missed merge only leaves a duplicate in the
catalogue. When those two risks compete, choose DIFFERENT.

Answer SAME only when the two descriptions carry exactly the same information
and differ ONLY in notation for the same terms:
  - an abbreviation against its full word  (VLV / VALVE, GKT / GASKET)
  - spacing, punctuation or separators     (SIDD. / SIDD,  2 IN / 2IN)
  - the order of the same terms

Answer DIFFERENT whenever anything else is not identical, including:
  - any difference in a number, size, length, bore, thread or rating
  - any difference in pressure class, voltage, current, temperature or material grade
  - any difference in a part number, model, drawing or code, even ONE character
  - any difference in manufacturer or brand
  - a term, qualifier, suffix or code present in one description and absent
    from the other - do NOT treat a shorter description as an abbreviated form
    of a longer one
  - anything you are unsure about

Do not infer that an omitted detail is implied. Do not treat a suspected typo
in a code as the same code. Missing information is a difference.

Return ONLY JSON with an entry for every pair number:
{"1": {"same": true|false, "reason": "<= 12 words"}, "2": {...}, ...}"""


def _normalise(text) -> str:
    if pd.isna(text):
        return ""
    t = str(text).upper()
    for rx, repl in _ABB:
        t = rx.sub(repl, t)
    t = re.sub(r"[^A-Z0-9 ]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _part_number(v) -> str:
    """A part number reduced to its letters and digits, or '' if it is not one."""
    if pd.isna(v):
        return ""
    t = re.sub(r"[^A-Z0-9]", "", str(v).upper())
    return t if len(t) >= _PN_MIN_LEN else ""


def _short(m) -> str:
    return str(m).lstrip("0") or str(m)


def _pool() -> tuple[pd.DataFrame, int]:
    """One row per material in the Bokor plant's material master.

    Returns (pool, n_already_marked_for_deletion).  Materials whose description
    says they are marked for deletion are left out: someone has already dealt
    with them, and listing them again as duplicates would only be noise.

    used_on_lines is how many Bokor BOM lines carry the material.  It is not a
    filter - it is how the number to KEEP is chosen, because retiring the one
    that is on the BOMs means editing every one of those BOMs.
    """
    mm = data.material_master()
    if not len(mm):
        return pd.DataFrame(), 0
    mm = mm[mm["description"].notna()].copy()
    retired = mm["description"].str.upper().str.contains(_RETIRED)
    pool = mm[~retired].copy()

    lines = data.bom_lines()
    lines = lines[lines["component"].notna()]
    used = data._norm_key(lines["component"]).value_counts()

    pool["norm"] = pool["description"].map(_normalise)
    pool = pool[pool["norm"] != ""]
    # word order is notation, not information - see the strict rule
    pool["desc_key"] = pool["norm"].map(lambda s: " ".join(sorted(s.split())))
    pool["pn"] = pool["part_number"].map(_part_number)
    pool["uom"] = pool["uom"].fillna("")
    pool["at_limit"] = pool["description"].str.len() >= DESCRIPTION_LIMIT
    pool["used_on_lines"] = pool["material"].map(used).fillna(0).astype(int)
    pool["stock_on_hand"] = pool["stock_on_hand"].fillna(0)
    return pool.reset_index(drop=True), int(retired.sum())


def _key(da, db) -> str:
    """Cache key for one pair. Includes PROMPT_VERSION so a change to the
    adjudication rule re-asks rather than reusing a verdict from the old rule."""
    payload = "\x00".join(sorted((str(da), str(db))) + [PROMPT_VERSION])
    return hashlib.sha1(payload.encode()).hexdigest()


def strict_prefilter(da, db) -> str:
    """Apply the strict rule mechanically. Returns 'same', 'different' or 'ask'.

    Under "any difference keeps them separate", most pairs need no judgement at
    all - the difference is right there in the tokens. Only one case genuinely
    needs the model: the two descriptions differ by the same number of purely
    alphabetic tokens, which might be two spellings of the same word
    (CMPR / CMP, SIG / SIGNL). Everything else is decided here.
    """
    ta, tb = _normalise(da).split(), _normalise(db).split()
    if sorted(ta) == sorted(tb):
        return "same"                       # notation or word order only

    ca, cb = Counter(ta), Counter(tb)
    only_a = sorted((ca - cb).elements())
    only_b = sorted((cb - ca).elements())

    # A term in one description and not the other is a difference, not an
    # abbreviation. A shorter description is never an abbreviated longer one.
    if len(only_a) != len(only_b):
        return "different"

    # Any differing token carrying a digit is a size, rating or code change.
    if any(ch.isdigit() for t in only_a + only_b for ch in t):
        return "different"

    return "ask"


def _look_alike_pairs(pool: pd.DataFrame, same_unit) -> list[tuple]:
    """Pairs the strict rule cannot decide on its own - the only ones worth a question.

    The material master has no material group to compare within, and 128,000
    materials cannot all be compared with each other.  The strict rule itself
    supplies the blocking: a pair can only survive it if both descriptions
    carry the SAME number of words and exactly the SAME digit-bearing tokens
    (any other pair is 'different' before anyone is asked).  So materials are
    bucketed on those two things plus the unit, and only materials in the same
    bucket are compared.  Nothing the old all-pairs search could have passed to
    the model is lost; what is skipped is only what the rule would have thrown
    out anyway.

    One representative per distinct description (the most-used material), and
    never a pair already sitting in the same group.
    """
    rep: dict = {}
    for m, key, used, uom in zip(pool["material"], pool["desc_key"], pool["used_on_lines"], pool["uom"]):
        k = (key, uom)
        if k not in rep or used > rep[k][1]:
            rep[k] = (m, used)

    buckets = defaultdict(list)
    for (key, uom), (m, _) in rep.items():
        tokens = key.split()
        digits = tuple(t for t in tokens if any(ch.isdigit() for ch in t))
        buckets[(uom, len(tokens), digits)].append((key, m))

    pairs = []
    for items in buckets.values():
        if len(items) < 2:
            continue
        for i in range(len(items)):
            ki, mi = items[i]
            for j in range(i + 1, len(items)):
                kj, mj = items[j]
                if fuzz.token_set_ratio(ki, kj) < FUZZY_MIN:
                    continue
                if same_unit(mi, mj):
                    continue
                pairs.append((mi, mj))
    return pairs


def _ask_sonnet(pool, pairs, workers, langfuse_required) -> dict:
    if not pairs:
        return {}
    desc = pool.set_index("material")["description"]
    try:
        cache = json.loads(_CACHE.read_text(encoding="utf-8"))
    except Exception:
        cache = {}

    todo = [(a, b) for a, b in pairs if _key(desc[a], desc[b]) not in cache]
    print(f"   {len(pairs) - len(todo)} cached, {len(todo)} to ask Sonnet "
          f"({-(-len(todo) // BATCH)} batches)")
    batches = [todo[i:i + BATCH] for i in range(0, len(todo), BATCH)]

    def do(batch):
        user = "Pairs:\n" + "\n".join(
            f'{k}. A: "{desc[a]}"  |  B: "{desc[b]}"' for k, (a, b) in enumerate(batch, 1))
        try:
            reply = llm.chat_json(_SYSTEM, user, agent=AGENT, task="adjudicate_material_pairs",
                                  metadata={"n_pairs": len(batch)}, max_tokens=1600,
                                  langfuse_required=langfuse_required)
        except Exception:
            return {}
        out = {}
        for k, (a, b) in enumerate(batch, 1):
            v = reply.get(str(k)) or {}
            out[_key(desc[a], desc[b])] = {"same": bool(v.get("same")),
                                           "reason": str(v.get("reason", "")).strip()[:80]}
        return out

    for part in llm.map_concurrent(do, batches, workers=workers):
        if isinstance(part, dict):
            cache.update(part)
    try:
        _CACHE.write_text(json.dumps(cache), encoding="utf-8")
    except Exception:
        pass
    return {(a, b): cache[_key(desc[a], desc[b])] for a, b in pairs if _key(desc[a], desc[b]) in cache}


_COLS = ["keep_material", "keep_description", "retire_materials", "basis",
         "confidence", "needs_pcsb_confirmation"]


def run(use_llm: bool = True, workers: int = 8, langfuse_required: bool = True):
    pool, n_marked = _pool()
    if not len(pool):
        df = pd.DataFrame([{
            "keep_material": "", "keep_description": "", "retire_materials": "",
            "basis": "The material master file has not been supplied, so duplicate materials "
                     "could not be checked.",
            "confidence": CONF_LOW, "needs_pcsb_confirmation": "Yes"}], columns=_COLS)
        return df, {}, {"material_master_available": False, "duplicate_groups": 0,
                        "material_numbers_to_retire": 0}

    info = pool.set_index("material")
    parent = {m: m for m in pool["material"]}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    # ------------------------------------------------------------------ HIGH
    # Same description, same unit, and a part number on every material that
    # agrees.  These unions are the confirmed duplicates; everything after
    # this works on the confirmed sets as single units.
    desc_groups = []               # (members, distinct part numbers, n with a part number)
    n_split_by_pn = n_split_by_unit = 0
    repeated = pool[pool.duplicated("desc_key", keep=False)]
    for key, by_desc in repeated.groupby("desc_key"):
        if by_desc["uom"].nunique() > 1:
            n_split_by_unit += 1
        for _, grp in by_desc.groupby("uom"):
            if len(grp) < 2:
                continue
            members = list(grp["material"])
            pns = [p for p in grp["pn"] if p]
            distinct = sorted(set(pns))
            # Materials sharing a part number are one part, whatever else is
            # in the group.
            by_pn = defaultdict(list)
            for m, p in zip(grp["material"], grp["pn"]):
                if p:
                    by_pn[p].append(m)
            for ms in by_pn.values():
                for m in ms[1:]:
                    union(ms[0], m)
            if len(distinct) > 1:
                # Different part numbers under one description: different parts.
                # The materials with no part number cannot be placed with either.
                n_split_by_pn += 1
                continue
            desc_groups.append((members, distinct, len(pns)))

    # Same part number, descriptions that differ only in notation the key did
    # not already absorb - nothing to add here: desc_key equality IS the
    # notation-only test, so those are already in the groups above.

    confirmed = defaultdict(list)
    for m in pool["material"]:
        confirmed[find(m)].append(m)

    def best(members):
        """The number to keep: the one the BOMs use, then the one holding stock,
        then the lowest number.  Returns (material, why)."""
        sub = info.loc[members].reset_index()
        sub["has_stock"] = sub["stock_on_hand"] > 0
        sub = sub.sort_values(["used_on_lines", "has_stock", "material"], ascending=[False, False, True])
        top = sub.iloc[0]
        if top["used_on_lines"] > 0:
            why = "it is the one used on Bokor BOMs"
        elif top["has_stock"]:
            why = "it is the one holding stock"
        else:
            why = "it is the lowest number"
        return top["material"], why

    def stock_note(retire) -> str:
        held = [m for m in retire if info.at[m, "stock_on_hand"] > 0]
        if not held:
            return ""
        return (f" Stock is held against {', '.join(_short(m) for m in held[:5])}"
                f"{' and others' if len(held) > 5 else ''}, so it has to be moved before "
                f"{'that number is' if len(held) == 1 else 'those numbers are'} retired.")

    rows, merge_map = [], {}
    unit_keep = {}                                  # confirmed set root -> its keep number
    for root, members in confirmed.items():
        if len(members) < 2:
            unit_keep[root] = members[0]
            continue
        keep, why = best(members)
        unit_keep[root] = keep
        retire = [m for m in members if m != keep]
        for m in retire:
            merge_map[_short(m)] = _short(keep)
        pn = info.at[keep, "part_number"]
        note = stock_note(retire)
        rows.append({
            "keep_material": _short(keep),
            "keep_description": info.at[keep, "description"],
            "retire_materials": ", ".join(_short(m) for m in retire),
            "basis": (f"Same description and same part number ({pn}), counted in the same unit "
                      f"({info.at[keep, 'uom']}), so these are the same part. {_short(keep)} is kept "
                      f"because {why}.{note}"),
            "confidence": CONF_HIGH,
            "needs_pcsb_confirmation": "Yes - stock to move first" if note else "No",
            "_grade": "high", "_n": len(retire),
        })

    def candidate_row(members, basis, conf, grade):
        """One row over the confirmed sets these materials belong to."""
        roots = sorted({find(m) for m in members})
        if len(roots) < 2:
            return
        keeps = [unit_keep[r] for r in roots]
        keep, why = best(keeps)
        retire = [m for m in keeps if m != keep]
        rows.append({
            "keep_material": _short(keep),
            "keep_description": info.at[keep, "description"],
            "retire_materials": ", ".join(_short(m) for m in retire),
            "basis": f"{basis} If they are confirmed as one part, {_short(keep)} would be kept "
                     f"because {why}.{stock_note(retire)}",
            "confidence": conf,
            "needs_pcsb_confirmation": "Yes - confirm these are the same physical part",
            "_grade": grade, "_n": len(retire),
        })

    # ---------------------------------------------------------- MEDIUM / LOW
    # Same description, but the part number cannot confirm it.
    n_at_limit = 0
    for members, distinct, n_with_pn in desc_groups:
        if distinct and n_with_pn == len(members):
            continue                                    # already confirmed above
        cut = bool(info.loc[members, "at_limit"].any())
        cut_note = (f" The description sits at the {DESCRIPTION_LIMIT}-character limit of the "
                    f"material master export, so a size or rating may have been cut off and these "
                    f"may be different items." if cut else "")
        if distinct:
            candidate_row(
                members,
                f"Same description and unit. A part number ({distinct[0]}) is recorded on "
                f"{n_with_pn} of the {len(members)} materials and none conflicts, but the others "
                f"have none to confirm it.{cut_note}",
                CONF_MEDIUM, "medium")
        else:
            n_at_limit += cut
            candidate_row(
                members,
                f"Same description and unit, but no part number is recorded on any of them, so "
                f"there is nothing to confirm they are the same part.{cut_note}",
                CONF_LOW, "low")

    # Same part number under different descriptions.
    n_pn_generic = n_pn_different = 0
    with_pn = pool[pool["pn"] != ""]
    with_pn = with_pn[with_pn.duplicated("pn", keep=False)]
    for pn, grp in with_pn.groupby("pn"):
        if grp["desc_key"].nunique() < 2:
            continue
        if grp["desc_key"].nunique() > _PN_MAX_DESCRIPTIONS:
            n_pn_generic += 1
            continue
        for _, same_unit_grp in grp.groupby("uom"):
            if same_unit_grp["desc_key"].nunique() < 2:
                continue
            members = list(same_unit_grp["material"])
            descs = list(dict.fromkeys(same_unit_grp["description"]))
            shown = "; ".join(f"'{d}'" for d in descs[:3]) + (" and others" if len(descs) > 3 else "")
            verdicts = {strict_prefilter(descs[0], d) for d in descs[1:]}
            raw_pn = same_unit_grp["part_number"].iat[0]
            if "different" in verdicts:
                n_pn_different += 1                     # a shared model number, not a duplicate
            else:
                candidate_row(
                    members,
                    f"Same part number ({raw_pn}) and unit, with descriptions that differ only in "
                    f"wording: {shown}.",
                    CONF_MEDIUM, "medium_pn")

    # ------------------------------------------------------------ look-alikes
    pairs = _look_alike_pairs(pool, lambda a, b: find(a) == find(b))
    desc = info["description"]
    ask = [(a, b) for a, b in pairs if strict_prefilter(desc[a], desc[b]) == "ask"]
    n_ai_same = 0
    print(f"P2: {len(pool):,} materials -> {len(pairs):,} look-alike pairs, "
          f"{len(ask):,} the strict rule cannot decide"
          f"{'' if use_llm else '  (AI step is OFF - counted, not asked)'}")
    if use_llm:
        for (a, b), verdict in _ask_sonnet(pool, ask, workers, langfuse_required).items():
            if not verdict.get("same"):
                continue
            n_ai_same += 1
            pn_a, pn_b = info.at[a, "pn"], info.at[b, "pn"]
            if pn_a and pn_b and pn_a != pn_b:
                continue                                # different part numbers settle it
            candidate_row(
                [a, b],
                f"The descriptions are worded differently but mean the same thing "
                f"('{desc[a]}' / '{desc[b]}'; {verdict.get('reason', '')}).",
                CONF_MEDIUM, "medium_ai")

    # ------------------------------------------------------------------ sheet
    order = {"high": 0, "medium": 1, "medium_pn": 2, "medium_ai": 3, "low": 4}
    if rows:
        df = pd.DataFrame(rows)
        df["_o"] = df["_grade"].map(order)
        df = df.sort_values(["_o", "_n", "keep_material"], ascending=[True, False, True]).reset_index(drop=True)
    else:
        df = pd.DataFrame(columns=_COLS + ["_grade", "_n"])
    grades = Counter(df["_grade"]) if len(df) else Counter()

    summary = {
        "material_master_available": True,
        "materials_in_material_master": int(len(pool) + n_marked),
        "already_marked_for_deletion": n_marked,
        "materials_compared": int(len(pool)),
        "materials_with_a_part_number": int((pool["pn"] != "").sum()),
        "duplicate_groups": int(len(df)),
        "groups_confirmed_high": int(grades["high"]),
        "material_numbers_to_retire": int(len(merge_map)),
        "groups_same_description_part_number_on_some": int(grades["medium"]),
        "groups_same_description_no_part_number": int(grades["low"]),
        "of_those_description_at_the_40_character_limit": int(n_at_limit),
        "groups_same_part_number_wording_differs": int(grades["medium_pn"]),
        "same_part_number_but_different_parts_not_listed": n_pn_different,
        "descriptions_split_by_different_part_numbers": n_split_by_pn,
        "descriptions_split_by_different_units": n_split_by_unit,
        "part_numbers_ignored_as_generic": n_pn_generic,
        "look_alike_pairs_found": len(pairs),
        "look_alike_pairs_needing_ai": len(ask),
        "ai_step_run": bool(use_llm),
        "ai_confirmed_same": n_ai_same,
        "groups_ai_judged": int(grades["medium_ai"]),
        "note": "Only HIGH groups (same description and same part number) are in the merge map. "
                "The material master description stops at 40 characters and a part number is "
                "recorded on about a quarter of materials, so most groups are candidates until "
                "PCSB supply the long description and manufacturer data.",
    }
    return df[_COLS], merge_map, summary
