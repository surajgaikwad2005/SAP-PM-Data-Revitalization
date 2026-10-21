# BOM Agent

Deterministic-first checks over the Bokor BOM data, with one small LLM step
(P2) for fuzzy judgement.  Everything writes to a single workbook:
`../outputs/BOM_Agent_Output.xlsx`.

## Run it

```
cd "BOM AGENT/code"
python run.py                 # all processes; P2 uses Claude Sonnet
python run.py --no-llm        # skip the P2 AI pass (exact-match duplicates only)
python run.py --no-langfuse   # AI pass without tracing (not recommended)
python run.py --workers 8     # threads for the P2 AI pass
```

First run reads the `.xlsb` (slow, ~1 min) and caches it under `../_cache/`.
The P2 AI verdicts are cached too, so re-runs finish in seconds.

## Files

| file | what it does |
|---|---|
| `config.py` | all file paths and constants |
| `data.py` | loads the 3 inputs and turns the flattened `.xlsb` into one tidy row per BOM component |
| `llm.py` | Claude Sonnet client + Langfuse tracing (project "SAP PM Data Revitalization") |
| `p4_priority.py` | **P4** - which equipment need a BOM built, ranked SCE -> C1 -> C2 -> C3 |
| `nbom_rules.py` | the eleven "BOM optional" equipment types of PTG 12.05.04 §3.5.4, and the head-noun matcher used to flag them |
| `p2_duplicates.py` | **P2** - material numbers in the material master (plant M014) that are the same physical part, graded by description + part number; `--no-p2-llm` counts the near-duplicate pairs without asking the AI |
| `p1_category.py` | **P1** - materials typed inconsistently across BOMs, with a recommended category |
| `p3_uom_qty.py` | **P3** - unit-of-measure and quantity check on existing BOM lines |
| `spir_store.py` | the **SPIR store** - spare-parts rows already extracted from the vendor dossier PDFs. Extraction is a separate offline job (`../spir_extract_2pass.py`); the agent only reads what it produced. Swap `_records()` for a SELECT when this becomes a database |
| `draft_bom.py` | **Draft BOMs** - links a dossier's project tag to a SAP equipment number via the functional location, and turns the SPIR parts into proposed BOM lines |
| `floating_materials.py` | Objective 2 - links materials used on work orders but not on any BOM, through four tiers of evidence (already on a BOM > work-order equipment > single equipment at the location > AI pick > review) |
| `report.py` | writes the output workbook |
| `run.py` | runs everything |

Each `pN_*.py` also exposes a `run()` you can call on its own.

## Output workbook

| sheet | contents |
|---|---|
| Overview | plain-English summary of every process |
| Draft BOMs | proposed BOM lines built from the SPIR store: equipment, item, component, quantity, UOM, part number, source document + page, and what still has to happen before the line can load |
| P4 - BOMs to build | ranked work list: rank, tier, equipment, description, functional location, criticality, SCE flag, inactive flag, PTG §3.5.4 "BOM optional" type, note |
| P2 - Duplicate materials | keep_material, keep_description, retire_materials, reason, confidence, needs_pcsb_confirmation |
| P1 - Category to fix | material, description, categories_seen, recommended, why, needs_pcsb_confirmation |
| P3 - UOM and Qty | finding, material, description, detail, needs_pcsb_confirmation |
| Floating materials | material, description, suggested_equipment, equipment_description, how_we_know, confidence, evidence, needs_pcsb_confirmation |

Rows that need PCSB confirmation are filled amber. Each sheet's top three rows
are: the title, the exact **input file name(s)** it used, and the **basis
(data fields + rules)** the process applies. Both are set in `config.py`
(`SOURCES` and `BASIS`).

## What this build does NOT do yet (blocked on PCSB data)

* Build BOM content at scale. `draft_bom.py` does it for the equipment we hold a
  SPIR sheet for, but that is a handful - the full per-equipment **SPIR** set is
  still outstanding from PCSB.
* Produce a *loadable* BOM line. Every SPIR sheet held has a blank MESC column
  (PETRONAS assigns those codes, not the vendor), so no component has a material
  number. Each part must be created in the material master first; until then the
  only category that loads is T (text item).
* Planner visibility of stock level / price - needs an **MRP extract**
  (SAP MARA / MARD / MARC).

## Inputs (already in `BOM AGENT/`)

* `01_existing_BOMs/Bokor Data_BOM Data.xlsb` - existing BOM structure
* `01_existing_BOMs/BOM Report_Bokor_13Aug26.xlsx` - PCSB's own coverage pivot
* `02_equipment_master/Equipment Listing_SKA_18June26.xlsx` - equipment master (User Status, ABC)
* `03_materials_to_link/List of 'Floating' Material M014.xlsx` - orphan materials
* `03_materials_to_link/BOKOR_10years Work Order Data_Aug26.xlsx` - work-order history (equipment behind each job)
* `05_rules/` - PTG 12.05.04, PTS 12.00.04, UDMS (reference)
* `Material Master/Stock Item_for JDA3.xlsx` - SAP material master; P3 uses its unit of measure
  (plant M014 only) to check the unit on each BOM line, and P2 runs its duplicate check on it.
