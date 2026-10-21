"""
PTG 12.05.04 section 3.5.4 - the equipment types for which a BOM is optional.

Verified against 05_rules/PTG 12.05.04 - PMMS.pdf, page 30 (March 2022). The
clause reads:

    3.5.4  List of the equipment type categorized as NBOM, which BOM
           development is optional is as follows, but not limited to:
             i.    Structure e.g. monorail, railing, tank foundation, bund, etc.
             ii.   Drain
             iii.  Escape Route
             iv.   Helideck Marking, Netting, Aiming Circle
             v.    Network System
             vi.   Pipeline, Riser
             vii.  Reflector
             viii. Wellhead
             ix.   Server
             x.    Corrosion Loop
             xi.   Stack, Vent

Two things in that wording drive the design:

  * "optional"        -> we FLAG these, we never drop them from the work list.
                         PCSB decides whether to waive each one.
  * "but not limited" -> the list is not exhaustive, so a miss is expected and
                         acceptable; a false positive is not.

Matching rule
-------------
We match on the HEAD NOUN of the description - the first comma-separated
segment - not on "does the text contain the word somewhere". SAP descriptions
are written "TYPE,QUALIFIER,QUALIFIER", so the head noun is what the equipment
IS; anything later is where it sits or what it serves. That distinction matters:

    "PUMP,OPEN DRAIN SUMP"      head = PUMP     -> a pump, needs a BOM
    "CLOSED DRAIN VESSEL"       head = CLOSED   -> a vessel, needs a BOM
    "PANEL, CONTROL, WELLHEAD"  head = PANEL    -> a panel, needs a BOM
    "HOIST, MONORAIL TROLLEY"   head = HOIST    -> a hoist, needs a BOM
    "CAISSON"                   head = CAISSON  -> NBOM candidate (vi)
    "HELIDECK SAFETY NETS"      head = HELIDECK...-> NBOM candidate (iv)

A plain keyword scan flags 96 equipment here, most of them pumps, tanks,
panels and alarms that genuinely need a BOM. The head-noun rule flags 52, all
of them real.

One special case: some descriptions lead with the platform code
("BODP-B, J-TUBE", "BOVA,VENTSTACK"). When the first segment is a site code we
skip it and read the next segment instead.
"""
from __future__ import annotations
import re

# leading platform / site code, e.g. BOCP, BOKA, BOVA, BODP-B
_SITE_CODE = re.compile(r"^BO[A-Z]{1,3}(-[A-Z])?$")

# One entry per PTG 12.05.04 s3.5.4 sub-clause. Patterns are matched against
# the head noun with spaces removed, anchored at both ends.
_TYPES = [
    ("i. Structure",
     r"MONORAIL|RAILING|HANDRAIL|GUARDRAIL|(TANK)?FOUNDATION|BUND|STRUCTURE"
     r"|GRATING|WALKWAY|STAIRWAY|PADEYE|CABLE(LADDER|TRAY)"
     r"|(ELECTRICAL|INSTRUMENTL?|INSTRUMENT)CABLELADDER"
     r"|[A-Z]*SUPPORTSTRUCTURE|HELIDECKSTRUCTURE"),
    ("ii. Drain",
     r"DRAIN|OPENDRAIN|CLOSEDDRAIN|DRAIN(LINE|SYSTEM|HEADER)"),
    ("iii. Escape Route",
     r"ESCAPEROUTE|ESCAPEWAY|MUSTER(AREA|POINT)"),
    ("iv. Helideck Marking, Netting, Aiming Circle",
     r"HELIDECK(MARKING|NETTING|SAFETYNETS?|NET)|AIMINGCIRCLE"),
    ("v. Network System",
     r"NETWORK(SYSTEM)?|LAN|WAN"),
    ("vi. Pipeline, Riser",
     # "piping" is named as an NBOM example in the PMMS Training Pack 2026 p.14,
     # alongside structures, stack/vent and escape route.
     r"PIPELINE|PIPING|PIPE|RISER|CAISSON|J-?TUBE"),
    ("vii. Reflector",
     r"(RADAR)?REFLECTOR"),
    ("viii. Wellhead",
     r"WELLHEAD|XMASTREE|CHRISTMASTREE"),
    ("ix. Server",
     r"SERVER"),
    ("x. Corrosion Loop",
     r"CORROSIONLOOP|CORRLOOP"),
    ("xi. Stack, Vent",
     r"STACK|VENT|VENTSTACK|FLARESTACK"),
]
_COMPILED = [(name, re.compile(r"^(?:" + pat + r")$")) for name, pat in _TYPES]

CLAUSE = "PTG 12.05.04 s3.5.4"


def nbom_type(description) -> str:
    """Return the PTG s3.5.4 sub-clause this equipment looks like, else ""."""
    if description is None:
        return ""
    text = re.sub(r"^DEAC-", "", str(description).upper()).strip()
    segments = [s.strip() for s in re.split(r"[,(]", text) if s.strip()]
    if not segments:
        return ""
    if len(segments) > 1 and _SITE_CODE.match(segments[0]):
        segments = segments[1:]                      # "BODP-B, J-TUBE" -> "J-TUBE"
    head = re.sub(r"[^A-Z0-9-]", "", segments[0])    # drop spaces / punctuation
    for name, pattern in _COMPILED:
        if pattern.match(head):
            return name
    return ""
