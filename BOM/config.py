"""
Central settings for the BOM Agent.

Everything the scripts need to find a file or label a value lives here, so the
other modules stay free of magic strings.  Paths are relative to the parent
folder ("BOM AGENT/"), which holds the numbered input folders.
"""
from __future__ import annotations
from pathlib import Path

# ---------------------------------------------------------------- folders
BASE = Path(__file__).resolve().parent.parent          # ...\BOM AGENT
CACHE = BASE / "_cache"                                 # slow reads are cached here
OUT = BASE / "outputs"                                  # the workbook is written here
CACHE.mkdir(exist_ok=True)
OUT.mkdir(exist_ok=True)

OUTPUT_WORKBOOK = OUT / "BOM_Agent_Output.xlsx"

# ---------------------------------------------------------------- input files
EQUIPMENT_FILE = BASE / "02_equipment_master" / "Equipment Listing_SKA_18June26.xlsx"

# SAP classification: one row per equipment per characteristic (class, Type,
# Body material, Set point, ...).  ~377k rows, so it is cached after first read.
CLASSIFICATION_FILE = BASE / "02_equipment_master" / "ZCDIE03A_bokor.xlsx"
EQUIPMENT_SHEET = "Data"

BOM_FILE = BASE / "01_existing_BOMs" / "Bokor Data_BOM Data.xlsb"
BOM_SHEET = "BOM"

BOM_REPORT_FILE = BASE / "01_existing_BOMs" / "BOM Report_Bokor_13Aug26.xlsx"

FLOATING_FILE = BASE / "03_materials_to_link" / "List of 'Floating' Material M014.xlsx"
FLOATING_SHEET = "Export"

# 10 years of Bokor work orders - used to recover the equipment / functional
# location behind each floating material's work order.
WO_HISTORY_FILE = BASE / "03_materials_to_link" / "BOKOR_10years Work Order Data_Aug26.xlsx"
WO_HISTORY_SHEET = "Data"

# SAP material master (stock item export) - one row per material per plant, with
# the material's own unit of measure.  ~540k rows across four plants, so only
# the Bokor plant's rows are kept and the parse is cached after first read.
MATERIAL_MASTER_FILE = BASE / "Material Master" / "Stock Item_for JDA3.xlsx"
MATERIAL_MASTER_SHEET = "Sheet1"

# ---------------------------------------------------------------- constants
SITE = "BOKOR"
PLANT = "M014"                                  # the SAP plant Bokor's materials sit under
DEMO_MODE: bool = False
DEMO_SIZE: int = 50

# SAP BOM item categories we recognise
#   I = assembly node (IBAU)   L = stock item   N = non-stock item   T = free text
ITEM_CATEGORIES = {"I", "L", "N", "T"}
MATERIAL_CATEGORIES = {"I", "L", "N"}          # categories that carry a material number

# Priority tiers for "which equipment gets a BOM built first"
# (No DOSH tier - Bokor is an offshore installation, outside DOSH jurisdiction.)
TIER_SCE = 1
TIER_C1 = 2
TIER_C2 = 3
TIER_C3 = 4
TIER_NONE = 5
TIER_LABEL = {
    TIER_SCE: "1 - Safety Critical Element",
    TIER_C1: "2 - Criticality 1",
    TIER_C2: "3 - Criticality 2",
    TIER_C3: "4 - Criticality 3",
    TIER_NONE: "5 - No criticality set",
}

# Confidence given to a row where two copies of a vendor sheet disagree and the
# agent deliberately reports both values instead of picking one.  Numeric so the
# column stays sortable, and below CONF_MEDIUM_MIN so it reads as "Low" on the
# scale printed at the top of every sheet.
CONF_CONFLICT = 0.45

# Confidence is scored as a number inside the agent - it has to be, because rows
# are ranked by it and a fine-grained value is what separates "the material master
# settles this" from "most other BOMs agree".  A reader does not need that
# precision, and a number invites false comparison between 0.80 and 0.85.  So the
# workbook shows a band instead, and these are the cut points.
CONF_HIGH_MIN = 0.85       # evidence settles it, or an independent document agrees
CONF_MEDIUM_MIN = 0.70     # the agent's pick, worth a look before acting
CONF_LABELS = ("Low", "Medium", "High")


def confidence_band(value) -> str:
    """Numeric confidence -> 'High' / 'Medium' / 'Low'.  Blank stays blank.

    A blank must not fall through to 'Low': an unrated row (an assembly heading,
    a spacer) would then read as a judgement the agent never made.
    """
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "" if value in (None, "") else str(value)
    if v != v:                      # NaN - float() accepts it, so test explicitly
        return ""
    if v >= CONF_HIGH_MIN:
        return "High"
    if v >= CONF_MEDIUM_MIN:
        return "Medium"
    return "Low"

# ---------------------------------------------------------------- source files per process
# Printed on each output sheet so a reader can see exactly what fed it.
_EQUIP = "02_equipment_master/Equipment Listing_SKA_18June26.xlsx  (sheet 'Data')"
_BOM = "01_existing_BOMs/Bokor Data_BOM Data.xlsb  (sheet 'BOM')"
_FLOAT = "03_materials_to_link/List of 'Floating' Material M014.xlsx  (sheet 'Export')"
_WOHIST = "03_materials_to_link/BOKOR_10years Work Order Data_Aug26.xlsx  (sheet 'Data')"
_SPIR = ("07_SPIR/_extracted/spir_extraction.xlsx  - the SPIR store, written by the "
         "separate offline extraction job (../extract_new_spir.py). The agent does not "
         "read the PDFs.")

_MATMASTER = ("Material Master/Stock Item_for JDA3.xlsx  (sheet 'Sheet1', plant M014) - "
              "used for the unit of measure only")

SOURCES = {
    "p4": [_EQUIP, _BOM],
    "p2": ["Material Master/Stock Item_for JDA3.xlsx  (sheet 'Sheet1', plant M014)",
           _BOM + " - only to see which material numbers are in use on Bokor BOMs",
           "+ Claude Sonnet for the near-duplicate judgement, when that step is switched on "
           "(traced in Langfuse)"],
    "p1": [_BOM],
    "p3": [_BOM, _EQUIP, _MATMASTER],
    "structure": [_BOM, _EQUIP],
    "floating": [_FLOAT, _WOHIST, _BOM, _EQUIP,
                 "+ Claude Sonnet to choose between candidate equipment (traced in Langfuse)"],
    "draft_bom": [_SPIR, _EQUIP, _BOM],
    "overview": [_BOM, _EQUIP, _FLOAT],
}

# On what data + rules each process is done (printed under the source line).
BASIS = {
    "p4": (
        "Data: equipment master User Status (BOM / NBOM / SCE flags), ABC Indicator (criticality 1/2/3), "
        "System status (INAC), Object Description (DEAC- prefix and equipment type); existing BOM extract for "
        "which equipment already have a BOM.  "
        "Rules: (1) listed when User Status has 'BOM' and not 'NBOM' - the SAP BOM-required vs BOM-waived "
        "mechanism of PTG 12.05.04 s3.5.2 - AND no BOM lines exist.  (2) Ranked SCE -> Criticality 1 -> 2 -> 3 "
        "-> none per UDMS priority guidance; no DOSH tier (Bokor is offshore, outside DOSH jurisdiction); "
        "active before inactive within a tier.  (3) The eleven 'BOM optional' equipment types of "
        "PTG 12.05.04 s3.5.4 (Structure, Drain, Escape Route, Helideck Marking/Netting/Aiming Circle, Network "
        "System, Pipeline/Riser, Reflector, Wellhead, Server, Corrosion Loop, Stack/Vent) are re-derived from "
        "the description head noun and FLAGGED in 'bom_optional_ptg_type' - not removed, because the clause "
        "says BOM development for them is optional and the list is 'not limited to'.  Head-noun matching is "
        "used so a 'PUMP,OPEN DRAIN SUMP' or a 'PANEL, CONTROL, WELLHEAD' is not mistaken for a drain or a wellhead."
    ),
    "p2": (
        "Data: SAP material master for plant M014 - material number, description, manufacturer part number "
        "('Part Number 1') and unit of measure. Materials whose description says they are marked for deletion "
        "are left out. Assemblies are not in the material master and are not part of this check.  "
        "Rules: two materials are the 'same description' when the descriptions are identical once abbreviations "
        "are spelled out, punctuation is dropped and word order is ignored. Materials counted in different units, "
        "or carrying different part numbers, are never grouped.  "
        "Confidence: HIGH - same description AND same part number; these are the confirmed duplicates.  "
        "MEDIUM - same description with a part number on some of the materials only (none conflicting), or same "
        "part number with descriptions that differ only in wording.  LOW - same description and no part number "
        "recorded on any of them.  The material master export stops a description at 40 characters and a part "
        "number is recorded on about a quarter of materials, so a LOW group may be different items whose size or "
        "rating was cut off - the Reason says where the description sits at that limit.  "
        "Number to keep: the one used on Bokor BOMs, else the one holding stock, else the lowest number.  "
        "Near-duplicates (descriptions close but not identical) are judged by Claude Sonnet under a STRICT "
        "standard - SAME only when the descriptions carry exactly the same information and differ purely in "
        "notation; any difference in size, rating, grade, brand, model or code keeps them separate. That step can "
        "be switched off, in which case the pairs are counted but not judged.  "
        "Rationale: a wrong merge puts the wrong spare on running equipment; a missed merge only leaves a "
        "duplicate in the catalogue.  Interchangeability concept per PTS 12.00.04."
    ),
    "p1": (
        "Data: item category (I/L/N/T) and SAP material type on every BOM component line, across all equipment.  "
        "Rules: SAP BOM item categories per PTG 12.05.04 - I = assembly node (IBAU), L = stock item, N = non-stock "
        "item, T = free text.  A material is flagged when it carries more than one category across BOMs.  "
        "Recommendation: material type IBAU -> I; otherwise the majority category across the lines; genuine L-vs-N "
        "ties (which need the MRP / valuation view) are left for PCSB."
    ),
    "p3": (
        "Data: unit of measure and quantity on every material BOM line (category I/L/N with a component number); "
        "manufacturer and model from the equipment master, to tell which equipment are the same item.  "
        "Rules: (1) COMPLETENESS - a line needs a unit and a quantity > 0, and a material should carry one unit "
        "everywhere it is used. These come back clean and always will: SAP refuses to save an L/N line without "
        "them, so the check is kept as a regression test on a future extract, not as a source of findings.  "
        "(2) IDENTICAL EQUIPMENT - two equipment of the same manufacturer and model are the same item, so a "
        "component fitted to both must be fitted in the same number. Where they disagree one of them is wrong, "
        "and the quantity used on most of them is the correction (the same majority rule P1 uses for item "
        "category). This is the only check here that decides right from wrong rather than raising a suspicion, "
        "and it needs no data PCSB have not already supplied. Equipment marked inactive in SAP stay in the "
        "comparison - a decommissioned unit's BOM is still evidence of what the item takes - but are named as "
        "inactive, because correcting a line on a dead record is wasted work.  (3) OUTLIER - a quantity an order of magnitude "
        "above that material's own normal across at least five BOM lines; raised for a look, never corrected, "
        "because a larger piece of equipment may genuinely take more.  (4) DUPLICATE UNIT CODES - the catalogue carries two "
        "codes for one unit (PC and EA, SET and ST); no single material is ever issued in two units, so rule (1) "
        "cannot see this, but it is a real standardisation gap.  "
        "(5) MATERIAL MASTER UNIT - the unit on each BOM line is compared with the unit SAP's material master "
        "records for that material at plant M014. The material master is the material's own record, so where "
        "the two differ the BOM line is the one to correct. Assemblies and text items are not in the material "
        "master; assemblies are checked against the one-SET convention instead.  "
        "Confirming a QUANTITY against an independent record still needs the SPIR installed-part counts "
        "(PTS 12.00.04) - outstanding, and blank on every sheet held so far."
    ),
    "floating": (
        "Data: the Bokor floating-material list (material, description, work order); 10 years of Bokor work-order "
        "history (order -> equipment / functional location); the existing BOM lines; and the equipment master "
        "(functional location, description, manufacturer).  "
        "Rules: four sources of evidence are tried in order of trustworthiness and the first that answers wins.  "
        "(A) the material number is already on some equipment's BOM -> link it, and note the source list is stale.  "
        "(B) the work-order history names the equipment the job was raised against -> link it.  "
        "(C) the job's functional location holds exactly one equipment -> link it.  "
        "(D) the location holds 2-10 equipment -> Claude Sonnet picks the best fit from the part description, the "
        "candidate equipment descriptions and their manufacturers, and must answer 'none' rather than guess.  "
        "(E) anything broader or with no usable location -> engineer review, as before.  "
        "Where a material was used at several locations the NARROWEST location decides, because pooling a precise "
        "location with a vague one only blurs it.  Every row carries a confidence label; nothing is written to SAP."
    ),
    "draft_bom": (
        "Data: the SPIR store - spare-parts rows already extracted from the vendor Equipment Dossier PDFs and "
        "held on disk (description, part number, brand, unit, installed quantity, source document and page); "
        "the equipment master (functional location, description); and the existing BOM extract, to confirm the "
        "equipment has no BOM today.  No model is called and no PDF is opened at run time.  "
        "Rules: (1) LINK - a dossier names a machine by its project tag ('E-2430 A/B'), SAP by an equipment "
        "number.  The bridge is the functional location, whose LAST segment is the project tag "
        "(BOCP.GCO.BC1.E2430A-E2430A).  A trailing 'A/B' means two units, so it expands to E2430A and E2430B.  "
        "Matching is on the last segment only - matching anywhere in the string would also return every "
        "instrument mounted on the machine.  (2) QUANTITY - taken from 'total no. of identical parts installed'; "
        "where that is blank, from 'no. of parts per unit', except when one value repeats down the whole page "
        "and is not 1, which is the signature of the header's 'no. of units' having been read into the rows - "
        "then it is reported as not stated rather than invented.  (3) CONSOLIDATE - a dossier often files the "
        "same sheet twice, so parts are merged on description + part number and items renumbered; where two "
        "copies disagree on quantity BOTH values are shown and the line is flagged, because choosing one would "
        "be guessing which revision is current.  (4) CATEGORY - the MESC number column is blank on every sheet "
        "held (it is assigned by PETRONAS, not the vendor), so no line can be L or N, both of which need a "
        "material master record.  Every line is proposed as T (text item), which is what will load today, with "
        "the material-creation step it needs recorded against it: 'Create in material master (MDG) first' means "
        "the part has no MESC number and so does not exist in SAP yet - once created, the line can change from a "
        "text item to a stock (L) or non-stock (N) item, whichever PCSB decide to hold.  NOTHING HERE IS READY "
        "TO LOAD AS A PARTS LIST: these are drafts for PCSB to confirm."
    ),
    "structure": (
        "Data: the assembly nodes on every existing BOM (SAP material type IBAU) and the equipment "
        "master's manufacturer and model.  "
        "Rules: the intended shape is equipment -> assembly (category I, unit SET) -> materials "
        "(category L/N, unit PC), per PMMS Training Pack 2026 p.14.  (1) REPEATED ASSEMBLIES - "
        "where several equipment of the same model each carry their own separately-numbered "
        "assembly describing the same thing, PTG 12.05.04 s3.5.12 allows one assembly to serve "
        "every machine of the same construction type, so they can be consolidated. Grouped on the "
        "assembly description plus the equipment model, both normalised, because the manufacturer "
        "field carries name variants that would otherwise split one finding into several. These "
        "numbers must NOT be retired as duplicate materials - each is in use on its own equipment's "
        "BOM, so the BOMs are pointed at a shared assembly first and only then do the spares fall "
        "away.  (2) NO ASSEMBLY AT ALL - equipment holding parts directly, reported once as an open "
        "question: SAP permits it, PTG s3.5.10 describes even a single-level list as grouping parts "
        "into an assembly, and which Bokor intends is PCSB's to confirm."
    ),
    "overview": "See each process sheet for the data and rules it uses.",
}
