# Agent C (Task List & Maintenance Plan Agent) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement Agent C end-to-end per `Proposal/TaskList_MPlan_Agent_Plan_Architecture.md` (§1–§11) as a new standalone directory, runnable in normal operation as `python app.py`, producing `Findings_Report.xlsx` plus 3 annotated primary files.

**Architecture:** A fixed, hardcoded pipeline (`validate_schema.py` → ingest → `normalize.py` → evidence connectors loaded once → PP1→PP2→PP3→PP4→PP5→PP6→PP7 in that exact order → output) driven entirely by `app.py`. `app.py` builds one LangChain Deep Agent via `create_deep_agent(...)` (§11.1) and, for each pain point in the fixed order, invokes the agent with that pain point's tool (evidence connectors, ground-truth lookup) and its deterministic `run_ppN` function — the agent decides which evidence to pull and whether enough exists to recommend, but every join, unit check, formula, and threshold comparison happens in deterministic Polars/Python inside `run_ppN`, and every emitted finding is validated structurally by Pydantic before it can leave the pipeline. The fixed PP1→PP7 order and the mandatory normalize-first step are enforced by the Python loop that calls the agent, not by prompting — the agent cannot skip, reorder, or repeat a step. Ground truth is Markdown generated once per pain point from only that pain point's cited source-document sections (with page/section citations) and treated as a read-only cache.

**Simplified module layout (per explicit direction — fewer files than the first draft of this plan):** no `core/` package. `app.py` owns config loading, file ingest, the LLM provider factory, and the Deep Agent orchestration — it is the one place those concerns live, not spread across 5 small modules. `validation.py` owns the `Finding` Pydantic schema and all 7 `run_ppN` pain-point functions — one file, not seven. `scripts/` and `evidence_connectors/` are unchanged from the architecture doc's §10 layout since those already matched. Tests collapse to 3 files (`test_normalize.py`, `test_validation.py`, `test_connectors.py`) covering the same behavior the larger draft split across 12.

**Corrections applied after review (this revision):** the previous draft of this plan had 8 must-fix defects identified in review — (1) the Deep Agent was defined but never actually invoked in `app.py`; (2) `build_ground_truth.py` dumped the entire UDMS PDF into all 7 pain-point cache files instead of extracting each pain point's cited section from its actual source document; (3) `read_long_text` let Polars auto-infer headers before searching for the two identically-named `UNIT` columns, which fails; (4) `read_mplan_bokor`'s column-name list had only 16 entries for a real 25-column file; (5) MPLAN Task List parsing sliced a hardcoded 8-character Group width, which breaks on the real data's variable-length Groups (verified: `BODC073` and `BODA006` are both 7 characters, not 8); (6) PP2 matched the literal string `"MULTI"`, but the real `OPWKCEN`/`Main Work Center` values are `BMULTI`/`TMULTI` (verified directly: 743 `TMULTI` + 264 `BMULTI` in `OPWKCEN`, 83 `BMULTI` in `Main Work Center` — the literal-match code would have matched zero of these), and an empty `approved_work_centres` list silently let every candidate through instead of failing closed; (7) PP4 arbitrarily picked the second Task List in a similar pair as "the one to keep," which §8's no-invented-values rule forbids without an actual precedence signal, and PP4 used only `difflib` even though the architecture's §11.3 names PP4 as the pain point that specifically warrants the Deep Agent's semantic judgment; (8) PP7 emitted a `Finding` for every correctly-assigned row, when the output schema (§7) is one row per actual finding, not a full table dump. All 8 are fixed in the tasks below, and the "also fix before production" items (PP2 unit-safe WORK summation, PP5's full operation key, floating-point tolerance, PP6's RTOF exclusion, config-driven thresholds, ground-truth cache actually being loaded at runtime, and `.xlsm`-preserving output) are folded into their respective tasks rather than deferred.

**Tech Stack:** Python 3.11+, LangChain + LangChain Deep Agents (`deepagents` package), Azure OpenAI / Azure AI Foundry (Claude) via `langchain-openai`/`langchain-anthropic` behind one configurable factory, Polars + fastexcel (read) + openpyxl (annotated-output write), PyMuPDF + PyMuPDF4LLM (ground-truth extraction), PyYAML, Pydantic v2, `sqlite3` (OREDA.db), `pytest`.

## Global Constraints

- **New directory only, parallel to existing ones:** everything lives under `Agent_C_TaskList_MPlan/`, created at `C:\Users\nikhil.raut\Tridiagonal-ai\Petronas\Data\Agent_C_TaskList_MPlan\` — the same level as `Proposal/`, `Analysis/`, `All_sites_Data/`, `BOKOR_Data/`. **Never create, modify, move, or delete anything inside any existing directory** (`Proposal/`, `All_sites_Data/`, `Analysis/`, `BOKOR_Data/`, `SAP Data/`, `Documents/`, or the existing `OREDA.db`/`a.py`/`Agent3_TaskList_MPlan.zip` at the `Data` root). Source files are only ever *read* from `All_sites_Data/SAP/...` and *copied* (never moved) into `Agent_C_TaskList_MPlan/input/` and `Agent_C_TaskList_MPlan/ground_truth_sources/`.
- **`app.py` is the single normal runtime entry point.** `python app.py` alone must run the full pipeline end-to-end under normal operation (default config pointing at `input/`, `config/`, `evidence_connectors/`, producing `output/`).
- **Framework:** LangChain Deep Agents for orchestration. Do not implement LangGraph directly — no hand-rolled `StateGraph`; the Deep Agent is built via the `deepagents` package's `create_deep_agent`, and `app.py`'s pipeline actually calls it per pain point (not merely defines a provider factory and leaves the agent unused).
- **Dataframe engine:** Polars everywhere data is read, joined, normalized, or transformed. No pandas import anywhere in the codebase (openpyxl is used only for writing annotated Excel output, not as a dataframe engine).
- **LLM provider:** Azure OpenAI and Claude-via-Azure/Foundry both configurable through one factory function in `app.py`, driven by `.env`/environment variables — never hardcoded to one provider in pain-point logic.
- **Confidence rule (§5, verbatim, non-negotiable):** `Confidence` is `0` when `Recommended_Value` is `NULL`/`None`, and `70`–`100` (inclusive) when `Recommended_Value` holds an actual value. No other `Confidence` value is ever valid. `Detection_Confidence` (0–100, optional) is a separate field, never substituted for `Confidence`. This is enforced structurally by a Pydantic validator in `validation.py`, not by convention.
- **No invented values:** never fabricate a SAP rule, mapping, field, or `Recommended_Value` not directly computable from the 3 primary files, Agent-A-equivalent FLOC/Equipment input, or the cited ground-truth/evidence sources in the architecture doc. Where evidence is insufficient, emit `Recommended_Value=None, Confidence=0` exactly as §5 specifies per pain point.
- **Evidence-scope exclusion (§4b):** `Mplan_M014_15Jan26.XLSX` and `GTL Listing for SKA Oil.xlsx` are never read, referenced, or copied anywhere in this implementation.
- **Code style:** simple, clean, modular, production-ready. Meaningful names (`normalize_long_text`, not `proc1`). No unnecessary classes where a function suffices, no verbose docstrings (one line stating purpose is enough — the architecture doc is the design record, not inline essays), no placeholder logic (`pass  # TODO` is never acceptable in a committed step). Consolidating related logic into one file (as this plan does for `validation.py`) is preferred over splitting into many small files unless a file grows unwieldy enough to hurt readability.
- **Testing:** `pytest`, run from `Agent_C_TaskList_MPlan/`. Tests use small synthetic Polars DataFrames built inline in the test file — never depend on the real Excel files being present, so the test suite runs identically for every engineer and in CI.

---

## Source File Reference (verified directly against the real files — use these exact paths/columns, do not re-derive)

**3 primary input files** (source: `All_sites_Data/SAP/Planning Data/`):

| Real filename | Sheet | Header row | Exact columns |
|---|---|---|---|
| `Bokor Task List Group.xlsx` | `Data` | row 1 | `Planning Plant, Maintenance Plan, Maintenance Item, Maint. item text, Functional Location, FunctLocDescrip., Equipment, Object Description, Order Type, Maintenance Strategy, ABC Indicator, Group, Group Counter, Maint. Planner Group, Main Work Center, Changed On, Changed By, Created On, Created By, Location` |
| `Bokor Long Text_Aug26_LATEST.xlsm` | `Bokor Long Text Rev2` | row 1 | `PLANT, STRATEGY, TLTYPE, TLGRP, TLGRPCOUNT, TLOPNO, TLSUBOPNO, TLNODE, TLCOUNT, CTRLKEY, OPWKCEN, OPDESC, WORK, UNIT, PERSON, DURATION, UNIT, ACTTYPE, SUIT, FREQUENCY, CA10TXT, SO10TXT, TEXTTITLE, FORMAT, LONGTEXT` — **note: the unit column for `WORK` and the unit column for `DURATION` are both literally named `UNIT` (columns 14 and 16, 0-indexed 13 and 15) — read this file positionally, then rename to `WORK_UNIT` and `DURATION_UNIT` respectively during ingest, exactly once, in `app.py`.** |
| `MPLAN BOKOR AUG26.xlsx` | `Sheet1` | **25 physical columns, two merged header rows, verified directly by reading rows 1–3 with `has_header=False`.** Row 1 (0-indexed row 0) is 18 empty strings followed by 7 real labels at indices 18–24: `No of Equipment, Equipment with PLAN Status Set, Equipment with RTOF Status, Equipment with MPLAN defined, MPLAN Completion %, % of Equipment with PLAN status, Equipment with MPLAN (incl. RTOF & w/o PLAN status)`. Row 2 (0-indexed row 1) pairs a label with `None`/blank across indices 0–16 — `PM planning plant, None, Maintenance Plant, None, Maintenance Plan, None, Task List, None, Plant, None, Location, None, PM planner group, None, Main Work Center, None, ABC indicator` — then 6 more blanks at indices 17–22, then `%, %` at indices 23–24 (which restate the row-1 labels for the last 2 columns). Data starts row 3 (0-indexed row 2) — confirmed sample: index 4=`50114592` (Maintenance Plan value), index 5=`' BOKOR FIELD'` (its description, not a separate field of interest), index 6=`ABODA05820` (Task List). **Read with `has_header=False`, assign all 25 explicit column names positionally (both the value and its paired description column, so nothing is silently dropped), then select only the columns `run_pipeline` actually needs** (do not trust Polars' auto header inference, and do not assume the file has only 16 columns). |

**FLOC/Equipment — Agent A stand-in** (source: `All_sites_Data/SAP/Asset Master/`; Agent A does not exist yet, so this build seeds `input/agent_a/` from the raw files per §3a's documented fallback — same schema Agent A's real output is expected to preserve):

| Real filename | Sheet | Exact columns |
|---|---|---|
| `FL Listing_SKO_19June26.xlsx` | `Data` | `Maintenance Plant, Functional Location, FunctLocDescrip., User Status, Location, System status, Created On, Main Work Center, Inventory Number, Superior FunctLoc., Changed On, ABC Indicator` |
| `Equipment Listing_SKA_18June26.xlsx` | `Data` | `Equipment, Object Description, Functional Location, FunctLocDescrip., Location, Technical IdentNo., Catalog Profile, ABC Indicator, System status, User Status, Maint. Planner Group, Main Work Center, Created By, Maintenance Plant, Manuf. Serial Number, ManufDrawingNumber, Manufacturer, ManufactPartNo., Material, Material Description, Model number, Created On, Inventory Number, Plant` |

**PITSTOPS Bokor files** (source: `All_sites_Data/SAP/Planning Data/PITSTOPS/SKA/`) — both real files are named `Tasklist.xlsx`, distinguished only by parent folder:

- `BOBELA TA 2024/Tasklist.xlsx`
- `BOBELA TA 2026/Tasklist.xlsx`

(Only the Bokor/SKA folder's 2 files are copied — the `PMA/` and `SBA/` folders are confirmed off-scope by site per §9 item 11 and must not be copied.)

**Ground truth source documents** (source: `All_sites_Data/SAP/MANUAL GUIDELINE/` and `All_sites_Data/SAP/PMMS KPI Report/`):

- `MANUAL GUIDELINE/UDMS.pdf`
- `MANUAL GUIDELINE/PTG 12.05.04 - PMMS.pdf`
- `MANUAL GUIDELINE/PWME_PCSB PMMS Work Management Execution_L3 Manual Revision.pdf`
- `MANUAL GUIDELINE/IVA_PMMS Training Pack_2026.pdf`
- `PMMS KPI Report/SKA_MPG_MWC_PMMS.pptx`
- `MANUAL GUIDELINE/PTG 00.01.03 - PMMS Catalog Profile.pdf`
- `MANUAL GUIDELINE/Detail screenshot for SAP System.docx`

**OREDA.db** — source: `C:\Users\nikhil.raut\Tridiagonal-ai\Petronas\Data\OREDA.db` (root-level file, read-only copy into `evidence_connectors/OREDA.db`).

**MULTI-type Work Centre values — verified directly, not the literal string `"MULTI"`:** scanning the full `Bokor Long Text_Aug26_LATEST.xlsm`, `OPWKCEN` contains `TMULTI` (743 rows) and `BMULTI` (264 rows) — never the bare string `MULTI`. `Bokor Task List Group.xlsx`'s `Main Work Center` contains `BMULTI` (83 rows). PP2's logic must match any Work Centre value **containing** `MULTI` as a substring, driven by a configurable list of known variants, never an exact-equality check against one hardcoded string.

**`Group`/`TLGRP` length is not fixed at 8 characters — verified directly:** `Bokor Task List Group.xlsx`'s real `Group` values include `BODC073` and `BODA006`, both 7 characters. A parser that assumes `TLGRP` is always exactly 8 characters (as an earlier draft of this plan did, splitting MPLAN's `Task List` string at a fixed offset) will misparse. The correct approach normalizes both sides and exact-matches against known `TLGRP` values already present in the normalized Long Text / bridge data, rather than guessing a split width — see Task 3.

---

## File Structure

```
Agent_C_TaskList_MPlan/
│
├── app.py                          # single runtime entry point: config, ingest,
│                                    #   LLM provider factory, Deep Agent orchestration,
│                                    #   fixed PP1-PP7 sequencing, output — all wired here
├── requirements.txt
├── .env.example
├── system_prompt.md
│
├── config/
│   ├── thresholds.yaml             # Confidence 0 or 70-100, never in-between
│   ├── work_centre_families.yaml   # §5 PP2: Planner Group -> approved Work Centre set
│   ├── unit_rules.yaml             # §5 PP5: valid WORK_UNIT/DURATION_UNIT combination
│   └── platform_code_prefixes.yaml # §5 PP1: BOKO/BOCP/BOKA/BODA/.../BOVA
│
├── input/
│   ├── Bokor Task List Group.xlsx
│   ├── Bokor Long Text_Aug26_LATEST.xlsm
│   ├── MPLAN BOKOR AUG26.xlsx
│   ├── agent_a/                    # §3a — Agent A's OUTPUT stand-in (seeded from raw
│   │   ├── Functional_Location_Validated.xlsx  #   FLOC/Equipment files until Agent A exists)
│   │   └── Equipment_Validated.xlsx
│   └── pitstops/                   # §4b / §5 PP5 — plausibility range only, never a
│       ├── BOBELA_TA_2024_Tasklist.xlsx   #   Recommended_WORK source (no join key)
│       └── BOBELA_TA_2026_Tasklist.xlsx
│
├── ground_truth_sources/           # §4c — the actual source-of-record documents
│   ├── UDMS.pdf
│   ├── PTG_12.05.04_PMMS.pdf
│   ├── PWME_PCSB_PMMS_L3_Manual.pdf
│   ├── IVA_PMMS_Training.pdf
│   ├── SKA_MPG_MWC_PMMS.pptx
│   ├── PTG_00.01.03_Catalog_Profile.pdf
│   └── Detail_screenshot_for_SAP_System.docx
│
├── ground_truth_cache/             # generated by scripts/build_ground_truth.py — each
│   ├── PP01_TaskList_Naming.md     #   file holds ONLY that pain point's cited excerpt
│   ├── PP02_Work_Centre.md         #   from its actual source document(s) per §4c, not
│   ├── PP03_Orphan_TaskList.md     #   the whole UDMS PDF; loaded at runtime by app.py
│   ├── PP04_Duplicate_TaskList.md  #   as ground truth for the Deep Agent's tools. A
│   ├── PP05_Manhours.md            #   cache, never hand-edited; if a .md and its source
│   ├── PP06_MPlan_OnHold.md        #   PDF ever disagree, the PDF wins.
│   └── PP07_Hanging_MI.md
│
├── evidence_connectors/            # kept separate per explicit instruction
│   ├── oreda_connector.py          #   re-verifies the PP5 "not usable" finding each run
│   ├── pitstops_connector.py       #   discipline-level Dur(Hrs) range check, detection-only
│   └── OREDA.db
│
├── scripts/
│   ├── build_ground_truth.py       # extracts ground_truth_sources/ -> ground_truth_cache/
│   ├── normalize.py                # §5.0 — mandatory preprocessing, run before app.py's
│   │                                #   pain-point logic every cycle
│   └── validate_schema.py          # §3a's caveat + primary-file guards: fails loudly if
│                                    #   any of the 5 input sources' real columns differ
│                                    #   from the documented baseline (§3/§4a)
│
├── validation.py                   # Finding Pydantic schema (the Confidence rule,
│                                    #   structurally enforced) + all 7 run_ppN functions
├── output_writer.py                # Findings_Report.xlsx + 3 annotated files
│
├── tests/
│   ├── test_normalize.py           # §5.0 normalization behavior
│   ├── test_validation.py          # Finding's confidence rule + all 7 pain points
│   └── test_connectors.py          # OREDA + PITSTOPS connectors
│
└── output/
    ├── Findings_Report.xlsx        # §7 core schema
    ├── Bokor_Task_List_Group_annotated.xlsx
    ├── Bokor_Long_Text_annotated.xlsm
    └── MPLAN_BOKOR_annotated.xlsx
```

**Rationale for this layout over the finer-grained first draft:** `validation.py` holds all 7 pain points because they share one schema (`Finding`) and one confidence rule — splitting them into 7 files added file-navigation overhead without adding testability, since `tests/test_validation.py` already exercises each `run_ppN` function independently by name. `app.py` absorbs config/ingest/LLM-provider/orchestration because those are each small (a settings loader, a handful of Excel readers, a provider switch, a fixed-order function call sequence) and only ever used once, at startup — a dedicated file per concern would be indirection without reuse. `scripts/` and `evidence_connectors/` stay separate because they are genuinely reusable/re-runnable independent of `app.py` (§10's explicit instruction to keep OREDA's connector standalone, and `normalize.py`/`validate_schema.py` as guards that must never be silently skipped or inlined).

---

## Task 1: Project Scaffold, Config, and Seed Data Copy

**Files:**
- Create: `Agent_C_TaskList_MPlan/requirements.txt`
- Create: `Agent_C_TaskList_MPlan/.env.example`
- Create: `Agent_C_TaskList_MPlan/.gitignore`
- Create: `Agent_C_TaskList_MPlan/config/thresholds.yaml`
- Create: `Agent_C_TaskList_MPlan/config/work_centre_families.yaml`
- Create: `Agent_C_TaskList_MPlan/config/unit_rules.yaml`
- Create: `Agent_C_TaskList_MPlan/config/platform_code_prefixes.yaml`
- Copy (read-only source, new destination — no source file touched): the 3 primary files, FLOC/Equipment files, 2 PITSTOPS files, 7 ground-truth docs, `OREDA.db` — into the paths listed in "Source File Reference" above.

**Interfaces:**
- Produces: 4 YAML config files under `config/`, read directly by `app.py` in Task 6 (no separate config-loading module — `app.py` calls `yaml.safe_load` on each path itself).

- [ ] **Step 1: Create the directory tree and copy seed data**

```bash
cd "C:/Users/nikhil.raut/Tridiagonal-ai/Petronas/Data"
BASE="Agent_C_TaskList_MPlan"
mkdir -p "$BASE"/{config,input/agent_a,input/pitstops,ground_truth_sources,ground_truth_cache,evidence_connectors,scripts,tests,output}

SRC="All_sites_Data/SAP"
cp "$SRC/Planning Data/Bokor Task List Group.xlsx" "$BASE/input/"
cp "$SRC/Planning Data/Bokor Long Text_Aug26_LATEST.xlsm" "$BASE/input/"
cp "$SRC/Planning Data/MPLAN BOKOR AUG26.xlsx" "$BASE/input/"
cp "$SRC/Asset Master/FL Listing_SKO_19June26.xlsx" "$BASE/input/agent_a/Functional_Location_Validated.xlsx"
cp "$SRC/Asset Master/Equipment Listing_SKA_18June26.xlsx" "$BASE/input/agent_a/Equipment_Validated.xlsx"
cp "$SRC/Planning Data/PITSTOPS/SKA/BOBELA TA 2024/Tasklist.xlsx" "$BASE/input/pitstops/BOBELA_TA_2024_Tasklist.xlsx"
cp "$SRC/Planning Data/PITSTOPS/SKA/BOBELA TA 2026/Tasklist.xlsx" "$BASE/input/pitstops/BOBELA_TA_2026_Tasklist.xlsx"

cp "$SRC/MANUAL GUIDELINE/UDMS.pdf" "$BASE/ground_truth_sources/"
cp "$SRC/MANUAL GUIDELINE/PTG 12.05.04 - PMMS.pdf" "$BASE/ground_truth_sources/PTG_12.05.04_PMMS.pdf"
cp "$SRC/MANUAL GUIDELINE/PWME_PCSB PMMS Work Management Execution_L3 Manual Revision.pdf" "$BASE/ground_truth_sources/PWME_PCSB_PMMS_L3_Manual.pdf"
cp "$SRC/MANUAL GUIDELINE/IVA_PMMS Training Pack_2026.pdf" "$BASE/ground_truth_sources/IVA_PMMS_Training.pdf"
cp "$SRC/PMMS KPI Report/SKA_MPG_MWC_PMMS.pptx" "$BASE/ground_truth_sources/"
cp "$SRC/MANUAL GUIDELINE/PTG 00.01.03 - PMMS Catalog Profile.pdf" "$BASE/ground_truth_sources/PTG_00.01.03_Catalog_Profile.pdf"
cp "$SRC/MANUAL GUIDELINE/Detail screenshot for SAP System.docx" "$BASE/ground_truth_sources/Detail_screenshot_for_SAP_System.docx"

cp "OREDA.db" "$BASE/evidence_connectors/OREDA.db"

ls -R "$BASE" | head -50
```
Expected: every path above exists under `$BASE`; no error about a missing source file (if one is missing, stop and report which — do not substitute a different file silently).

- [ ] **Step 2: Write `requirements.txt`**

```text
polars>=1.9
fastexcel>=0.12
openpyxl>=3.1
pydantic>=2.9
pydantic-settings>=2.5
pyyaml>=6.0
pymupdf>=1.24
pymupdf4llm>=0.0.17
langchain>=0.3
deepagents>=0.1
langchain-openai>=0.2
langchain-anthropic>=0.3
python-dotenv>=1.0
pytest>=8.3
```

- [ ] **Step 3: Write `.env.example`**

```text
AGENT_C_LLM_PROVIDER=azure_openai

AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=
AZURE_OPENAI_API_VERSION=2024-08-01-preview

AZURE_FOUNDRY_CLAUDE_API_KEY=
AZURE_FOUNDRY_CLAUDE_ENDPOINT=
AZURE_FOUNDRY_CLAUDE_DEPLOYMENT=
```

- [ ] **Step 4: Write `.gitignore`**

```text
__pycache__/
*.pyc
.env
ground_truth_cache/*.md
output/*.xlsx
output/*.xlsm
```

- [ ] **Step 5: Write `config/platform_code_prefixes.yaml`** (§5 PP1)

```yaml
# UDMS §9.4 — Bokor platform-code family, chars 1-4 of a General Task List Group
platform_codes:
  - BOKO
  - BOCP
  - BOKA
  - BODA
  - BODB
  - BODC
  - BODD
  - BODE
  - BODF
  - BOPA
  - BOVA
```

- [ ] **Step 6: Write `config/unit_rules.yaml`** (§5 PP5)

```yaml
# UDMS §9.20-21 — WORK = PERSON x DURATION is only valid for this unit
# combination. Verified 100% exact on all 84,726 MHR/HR rows in
# Bokor Long Text; STD-unit rows are explicitly out of scope, not converted.
valid_work_unit: MHR
valid_duration_unit: HR
```

- [ ] **Step 7: Write `config/work_centre_families.yaml`** (§5 PP2, §9 item 6)

```yaml
# SKA_MPG_MWC_PMMS.pptx — Maintenance Planner Group -> approved Work
# Centre family. Only BOS/CP2/MEW/MEN are confirmed present in the Bokor
# data as surveyed (§9 item 6); the full table beyond these four needs
# client confirmation and must be added here, never guessed.
planner_groups:
  BOS:
    approved_work_centres: []   # populate from SKA_MPG_MWC_PMMS.pptx before first real run
  CP2:
    approved_work_centres: []
  MEW:
    approved_work_centres: []
  MEN:
    approved_work_centres: []

# UDMS §9.17 — no MULTI-type Work Centre is allowed at operation level.
# Verified directly against the real files: OPWKCEN carries TMULTI (743
# rows) and BMULTI (264 rows); Main Work Center carries BMULTI (83 rows).
# The literal string "MULTI" alone never appears — match any value
# containing one of these as a substring, not an exact-equality check.
multi_work_centre_variants:
  - BMULTI
  - TMULTI
  - MULTI
```

- [ ] **Step 8: Write `config/thresholds.yaml`** (§5 opening rule, §7, and the §5 per-pain-point Detection_Confidence bands)

```yaml
# The final recommendation rule (§5) — non-negotiable, enforced again in
# validation.py's Pydantic validator. This file carries the numeric
# threshold itself and every PP-specific Detection_Confidence band cited
# in §5's tables, so a band change is a config edit, not a code edit.
confidence_threshold: 70
confidence_when_null: 0

pp1:
  reused_prefix_min_occurrences: 4    # §5 PP1 — MYVES$$2 pattern
  detection_confidence_reused_prefix: 90
  detection_confidence_non_platform_prefix: 20

pp2:
  detection_confidence_no_operations_found: 60
  detection_confidence_not_in_approved_family: 60
  confidence_item_level_recommendation: 95
  detection_confidence_operation_level_multi: 100

pp3:
  detection_confidence_with_mplan_evidence: 30
  detection_confidence_no_evidence: 50
  detection_confidence_inactive_asset: 70   # 3rd tier, not yet wired — see Task 8 note

pp4:
  text_similarity_threshold: 0.85
  confidence_bridge_linked_strong_match: 90
  detection_confidence_unlinked_text_match: 40

pp5:
  confidence_formula_correction: 100
  detection_confidence_range_suspicious: 90
  work_tolerance: 0.01   # numeric tolerance for the WORK == PERSON x DURATION check

pp6:
  detection_confidence_strategy_mismatch: 95
  detection_confidence_coverage_gap: 85

pp7:
  confidence_populated_plan: 100
```

- [ ] **Step 9: Commit manually**

Git/GitHub operations are performed manually by the user, never as an automated step. Initialize the repository and commit the scaffold (`requirements.txt`, `.env.example`, `.gitignore`, `config/*.yaml`, and the copied seed data under `input/`, `ground_truth_sources/`, `evidence_connectors/OREDA.db`) with a message like `scaffold: project structure, config, seed data copy` before moving to Task 2.

---

## Task 2: `validation.py` — the `Finding` Schema (Confidence Rule, Structurally Enforced)

**Files:**
- Create: `Agent_C_TaskList_MPlan/validation.py` (started here; pain-point functions are added to this same file in Tasks 5–11)
- Test: `Agent_C_TaskList_MPlan/tests/test_validation.py` (started here; pain-point tests are appended to this same file in Tasks 5–11)

**Interfaces:**
- Produces:
  - `Finding` (Pydantic model): fields `pain_point: str`, `record_key: str`, `field_name: str`, `current_value: str | None`, `recommended_value: str | None`, `confidence: int`, `detection_confidence: int | None = None`, `evidence_source: str` — with a model validator enforcing: `confidence == 0` iff `recommended_value is None`; otherwise `70 <= confidence <= 100`; `detection_confidence` when set must be `0 <= x <= 100`.

- [ ] **Step 1: Write the failing tests**

```python
import pytest
from pydantic import ValidationError

from validation import Finding


def test_null_recommendation_requires_zero_confidence():
    finding = Finding(
        pain_point="PP1",
        record_key="BMULTI-01",
        field_name="Group",
        current_value="XXXXXXXX",
        recommended_value=None,
        confidence=0,
        evidence_source="Bokor Task List Group.xlsx",
    )
    assert finding.confidence == 0
    assert finding.recommended_value is None


def test_null_recommendation_with_nonzero_confidence_is_rejected():
    with pytest.raises(ValidationError):
        Finding(
            pain_point="PP1",
            record_key="BMULTI-01",
            field_name="Group",
            current_value="XXXXXXXX",
            recommended_value=None,
            confidence=20,
            evidence_source="Bokor Task List Group.xlsx",
        )


def test_real_value_requires_confidence_at_least_70():
    with pytest.raises(ValidationError):
        Finding(
            pain_point="PP2",
            record_key="ITEM-123",
            field_name="Main Work Center",
            current_value="BMULTI",
            recommended_value="BMECH",
            confidence=50,
            evidence_source="Bokor Long Text_Aug26_LATEST.xlsm",
        )


def test_real_value_with_valid_confidence_is_accepted():
    finding = Finding(
        pain_point="PP2",
        record_key="ITEM-123",
        field_name="Main Work Center",
        current_value="BMULTI",
        recommended_value="BMECH",
        confidence=96,
        evidence_source="Bokor Long Text_Aug26_LATEST.xlsm",
    )
    assert finding.confidence == 96


def test_detection_confidence_out_of_range_is_rejected():
    with pytest.raises(ValidationError):
        Finding(
            pain_point="PP3",
            record_key="ABODA05820",
            field_name="Maintenance Item",
            current_value=None,
            recommended_value=None,
            confidence=0,
            detection_confidence=150,
            evidence_source="Bokor Long Text_Aug26_LATEST.xlsm",
        )
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'validation'`.

- [ ] **Step 3: Write `validation.py`** (this file grows with each pain-point task below; only the schema is added now)

```python
from pydantic import BaseModel, model_validator


class Finding(BaseModel):
    pain_point: str
    record_key: str
    field_name: str
    current_value: str | None
    recommended_value: str | None
    confidence: int
    detection_confidence: int | None = None
    evidence_source: str

    @model_validator(mode="after")
    def enforce_confidence_rule(self) -> "Finding":
        if self.recommended_value is None:
            if self.confidence != 0:
                raise ValueError(
                    "recommended_value is None but confidence is "
                    f"{self.confidence}; must be 0 per the final recommendation rule"
                )
        else:
            if not (70 <= self.confidence <= 100):
                raise ValueError(
                    f"recommended_value is set but confidence is {self.confidence}; "
                    "must be 70-100 per the final recommendation rule"
                )
        if self.detection_confidence is not None and not (0 <= self.detection_confidence <= 100):
            raise ValueError(
                f"detection_confidence {self.detection_confidence} out of range 0-100"
            )
        return self
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: 5 passed.

- [ ] **Step 5: Commit**

Commit manually: `validation.py`, `tests/test_validation.py` — message like `feat: Finding schema enforcing the confidence rule`.

---

## Task 3: `scripts/normalize.py` — Normalization Layer (§5.0)

**Files:**
- Create: `Agent_C_TaskList_MPlan/scripts/__init__.py` (empty, makes `scripts` importable)
- Create: `Agent_C_TaskList_MPlan/scripts/normalize.py`
- Create: `Agent_C_TaskList_MPlan/tests/test_normalize.py`

**Interfaces:**
- Consumes: `pl.DataFrame` shaped like the real `Bokor Long Text_Aug26_LATEST.xlsm` (with `WORK_UNIT`/`DURATION_UNIT` already disambiguated — see Task 6) and `MPLAN BOKOR AUG26.xlsx` (with explicit column names — see Task 6).
- Produces:
  - `normalize_long_text(df: pl.DataFrame) -> pl.DataFrame` — collapses to one row per logical operation key (`TLGRP+TLGRPCOUNT+TLOPNO+TLSUBOPNO`), all of `TLGRP, TLGRPCOUNT, TLOPNO, TLSUBOPNO` cast to `pl.Utf8`, `WORK/WORK_UNIT/PERSON/DURATION/DURATION_UNIT/OPWKCEN/OPDESC/CTRLKEY/STRATEGY/TLTYPE/FREQUENCY` taken from the first row per group (constant across the group per §5.0 3A), and a new column `LONGTEXT_AGGREGATED` holding all `LONGTEXT` values for that operation joined with `"\n"` (§5.0 3E).
  - `cast_counters_to_string(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame` — casts named columns to `pl.Utf8` (§5.0 3B).
  - `parse_mplan_task_list_key(df: pl.DataFrame, known_tlgrps: set[str]) -> pl.DataFrame` — adds `TLTYPE`, `TLGRP`, `TLGRPCOUNT` columns parsed from the `task_list` string. **Never assumes a fixed Group width** (verified directly: real `Group` values are 7 characters for some rows — `BODC073`, `BODA006` — not always 8). Instead: `TLTYPE` is always the first character; for the remainder, try every possible split point and keep the one where the candidate `TLGRP` exact-matches an entry in `known_tlgrps` (the set of real `TLGRP` values already present in the normalized Long Text / bridge data); if no split matches any known `TLGRP`, the row gets `TLGRP=None, TLGRPCOUNT=None` rather than a guessed split (§5.0 3C).
  - `classify_mplan_rows(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]` — returns `(detail_rows, aggregate_rows)`: `detail_rows` = rows where `maintenance_plan` and `task_list` are both non-null; `aggregate_rows` = all other rows (§5.0 3D).

- [ ] **Step 1: Write the failing test**

```python
import polars as pl

from scripts.normalize import (
    cast_counters_to_string,
    classify_mplan_rows,
    normalize_long_text,
    parse_mplan_task_list_key,
)


def test_normalize_long_text_collapses_to_logical_operation_grain():
    df = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01", "BOKOKC01", "BOKOKC01"],
            "TLGRPCOUNT": ["10", "10", "10"],
            "TLOPNO": ["10", "10", "10"],
            "TLSUBOPNO": ["0", "0", "0"],
            "OPWKCEN": ["BMECH", "BMECH", "BMECH"],
            "OPDESC": ["PM,3M-VISUAL", "PM,3M-VISUAL", "PM,3M-VISUAL"],
            "WORK": [4.0, 4.0, 4.0],
            "WORK_UNIT": ["MHR", "MHR", "MHR"],
            "PERSON": [2, 2, 2],
            "DURATION": [2.0, 2.0, 2.0],
            "DURATION_UNIT": ["HR", "HR", "HR"],
            "CTRLKEY": ["INTN", "INTN", "INTN"],
            "STRATEGY": ["PCSB52", "PCSB52", "PCSB52"],
            "TLTYPE": ["A", "A", "A"],
            "FREQUENCY": ["3M", "3M", "3M"],
            "LONGTEXT": ["line one", "line two", "line three"],
        }
    )
    result = normalize_long_text(df)
    assert result.shape[0] == 1
    assert result["LONGTEXT_AGGREGATED"][0] == "line one\nline two\nline three"
    assert result["WORK"][0] == 4.0


def test_cast_counters_to_string():
    df = pl.DataFrame({"TLGRPCOUNT": [10, 20, 30]})
    result = cast_counters_to_string(df, ["TLGRPCOUNT"])
    assert result["TLGRPCOUNT"].dtype == pl.Utf8
    assert result["TLGRPCOUNT"][0] == "10"


def test_parse_mplan_task_list_key_matches_against_known_tlgrp_not_fixed_width():
    # BODA582 (7 chars) is the real TLGRP — a hardcoded 8-char split would
    # wrongly produce BODA0582, which does not exist in known_tlgrps.
    df = pl.DataFrame({"task_list": ["ABODA5820"]})
    known_tlgrps = {"BODA582", "BOKOKC01"}
    result = parse_mplan_task_list_key(df, known_tlgrps)
    assert result["TLTYPE"][0] == "A"
    assert result["TLGRP"][0] == "BODA582"
    assert result["TLGRPCOUNT"][0] == "0"


def test_parse_mplan_task_list_key_no_match_yields_null_not_a_guess():
    df = pl.DataFrame({"task_list": ["ZZZZZZZZZZ"]})
    known_tlgrps = {"BODA582", "BOKOKC01"}
    result = parse_mplan_task_list_key(df, known_tlgrps)
    assert result["TLGRP"][0] is None
    assert result["TLGRPCOUNT"][0] is None


def test_classify_mplan_rows_splits_detail_from_aggregate():
    df = pl.DataFrame(
        {
            "maintenance_plan": ["50114592", None],
            "task_list": ["ABODA05820", None],
            "mplan_completion_pct": [95, 80],
        }
    )
    detail, aggregate = classify_mplan_rows(df)
    assert detail.shape[0] == 1
    assert aggregate.shape[0] == 1
    assert detail["maintenance_plan"][0] == "50114592"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_normalize.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.normalize'`.

- [ ] **Step 3: Write `scripts/__init__.py`** (empty)

```python
```

- [ ] **Step 4: Write `scripts/normalize.py`**

```python
import polars as pl

LOGICAL_OPERATION_KEY = ["TLGRP", "TLGRPCOUNT", "TLOPNO", "TLSUBOPNO"]


def normalize_long_text(df: pl.DataFrame) -> pl.DataFrame:
    df = cast_counters_to_string(df, LOGICAL_OPERATION_KEY)
    longtext_agg = (
        df.group_by(LOGICAL_OPERATION_KEY, maintain_order=True)
        .agg(pl.col("LONGTEXT").str.concat("\n").alias("LONGTEXT_AGGREGATED"))
    )
    first_row_per_operation = df.group_by(LOGICAL_OPERATION_KEY, maintain_order=True).first()
    return first_row_per_operation.drop("LONGTEXT").join(
        longtext_agg, on=LOGICAL_OPERATION_KEY, how="left"
    )


def cast_counters_to_string(df: pl.DataFrame, columns: list[str]) -> pl.DataFrame:
    return df.with_columns([pl.col(c).cast(pl.Utf8) for c in columns])


def parse_mplan_task_list_key(df: pl.DataFrame, known_tlgrps: set[str]) -> pl.DataFrame:
    # Task List field is TLTYPE (1 char) + TLGRP + TLGRPCOUNT, but TLGRP is
    # NOT a fixed width — verified directly, real Group values are 7 chars
    # for some rows (BODC073, BODA006), not always 8. Try every possible
    # split point after the type character and keep the one whose
    # candidate TLGRP exact-matches a known real TLGRP. Never guess a
    # split when no candidate matches — that row gets TLGRP/TLGRPCOUNT =
    # None instead, per §5.0 3C.
    def split(task_list: str | None) -> tuple[str | None, str | None, str | None]:
        if task_list is None or len(task_list) < 2:
            return None, None, None
        tltype = task_list[0]
        remainder = task_list[1:]
        for split_point in range(len(remainder), 0, -1):
            candidate_tlgrp = remainder[:split_point]
            if candidate_tlgrp in known_tlgrps:
                candidate_tlgrpcount = remainder[split_point:].lstrip("0") or "0"
                return tltype, candidate_tlgrp, candidate_tlgrpcount
        return tltype, None, None

    parsed = [split(v) for v in df["task_list"]]
    return df.with_columns(
        pl.Series("TLTYPE", [p[0] for p in parsed]),
        pl.Series("TLGRP", [p[1] for p in parsed]),
        pl.Series("TLGRPCOUNT", [p[2] for p in parsed]),
    )


def classify_mplan_rows(df: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    detail = df.filter(pl.col("maintenance_plan").is_not_null() & pl.col("task_list").is_not_null())
    aggregate = df.filter(pl.col("maintenance_plan").is_null() | pl.col("task_list").is_null())
    return detail, aggregate
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_normalize.py -v
```
Expected: 5 passed.

- [ ] **Step 6: Commit manually**

Commit `scripts/__init__.py`, `scripts/normalize.py`, `tests/test_normalize.py` — message like `feat: §5.0 normalization layer (operation grain, string counters, MPLAN key parsing, DETAIL/AGGREGATE split)`.

---

## Task 4: `scripts/validate_schema.py` — Schema Guards for Every Input Source

**Files:**
- Create: `Agent_C_TaskList_MPlan/scripts/validate_schema.py` (renamed from the earlier draft's `validate_agent_a_schema.py`, since it now covers all 5 input sources, not just Agent A's)
- Test: append to `Agent_C_TaskList_MPlan/tests/test_normalize.py` (schema-guard tests live alongside the other `scripts/` module tests rather than a fifth test file)

**Interfaces:**
- Consumes: `pl.DataFrame` (from `app.py`'s readers, Task 12).
- Produces: `validate_floc_schema`, `validate_equipment_schema`, `validate_task_list_group_schema`, `validate_long_text_schema`, `validate_mplan_schema` — each `(df: pl.DataFrame) -> None`, raising `SchemaValidationError` (defined in this module) listing exactly which expected columns are missing. **Corrected from the earlier draft, which only guarded Agent A's FLOC/Equipment input:** the 3 primary files get the same fail-loudly treatment before any pain-point logic runs, not just a partial check buried inside their readers (MPLAN's column-count assertion and Long Text's UNIT-column-count assertion in Task 12 catch a *structural* shape change, but not a *renamed column* — e.g. if `Bokor Task List Group.xlsx`'s `Group` column were renamed to `Task List Group` in a future data drop, the reader would still succeed with the wrong column present, and every downstream `pl.col("Group")` reference would fail with a confusing error deep inside a pain-point function rather than a clear one at ingest time). Never silently proceeds on a mismatch.

- [ ] **Step 1: Append the failing tests to `tests/test_normalize.py`**

```python
import pytest

from scripts.validate_schema import (
    SchemaValidationError,
    validate_equipment_schema,
    validate_floc_schema,
    validate_long_text_schema,
    validate_mplan_schema,
    validate_task_list_group_schema,
)


def test_validate_floc_schema_passes_on_expected_columns():
    df = pl.DataFrame(
        {
            "Maintenance Plant": ["M014"], "Functional Location": ["BWI-001"],
            "FunctLocDescrip.": ["Bokor"], "User Status": ["ACT"], "Location": ["BOKOR"],
            "System status": ["CRTE"], "Created On": ["2020-01-01"], "Main Work Center": ["BMECH"],
            "Inventory Number": ["1"], "Superior FunctLoc.": ["BWI"], "Changed On": ["2026-01-01"],
            "ABC Indicator": ["1"],
        }
    )
    validate_floc_schema(df)  # must not raise


def test_validate_floc_schema_fails_loudly_on_missing_column():
    df = pl.DataFrame({"Functional Location": ["BWI-001"]})
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_floc_schema(df)
    assert "System status" in str(exc_info.value)


def test_validate_equipment_schema_fails_loudly_on_missing_column():
    df = pl.DataFrame({"Equipment": ["10012345"]})
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_equipment_schema(df)
    assert "User Status" in str(exc_info.value)


def test_validate_task_list_group_schema_fails_loudly_on_missing_column():
    df = pl.DataFrame({"Maintenance Item": ["978469"]})
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_task_list_group_schema(df)
    assert "Group" in str(exc_info.value)


def test_validate_long_text_schema_fails_loudly_on_missing_column():
    df = pl.DataFrame({"TLGRP": ["BOKOKC01"]})
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_long_text_schema(df)
    assert "OPWKCEN" in str(exc_info.value)


def test_validate_mplan_schema_fails_loudly_on_missing_column():
    df = pl.DataFrame({"maintenance_plan": ["50114592"]})
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_mplan_schema(df)
    assert "task_list" in str(exc_info.value)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_normalize.py -v
```
Expected: the 5 new tests FAIL — `ModuleNotFoundError` for `scripts.validate_schema`. (The 5 existing normalization tests still pass.)

- [ ] **Step 3: Write `scripts/validate_schema.py`**

```python
import polars as pl

EXPECTED_FLOC_COLUMNS = [
    "Maintenance Plant", "Functional Location", "FunctLocDescrip.", "User Status",
    "Location", "System status", "Created On", "Main Work Center", "Inventory Number",
    "Superior FunctLoc.", "Changed On", "ABC Indicator",
]

EXPECTED_EQUIPMENT_COLUMNS = [
    "Equipment", "Object Description", "Functional Location", "FunctLocDescrip.",
    "Location", "Technical IdentNo.", "Catalog Profile", "ABC Indicator",
    "System status", "User Status", "Maint. Planner Group", "Main Work Center",
    "Created By", "Maintenance Plant", "Manuf. Serial Number", "ManufDrawingNumber",
    "Manufacturer", "ManufactPartNo.", "Material", "Material Description",
    "Model number", "Created On", "Inventory Number", "Plant",
]

# The 3 primary files (§3) — verified directly against the real files.
EXPECTED_TASK_LIST_GROUP_COLUMNS = [
    "Planning Plant", "Maintenance Plan", "Maintenance Item", "Maint. item text",
    "Functional Location", "FunctLocDescrip.", "Equipment", "Object Description",
    "Order Type", "Maintenance Strategy", "ABC Indicator", "Group", "Group Counter",
    "Maint. Planner Group", "Main Work Center", "Changed On", "Changed By",
    "Created On", "Created By", "Location",
]

EXPECTED_LONG_TEXT_COLUMNS = [
    "PLANT", "STRATEGY", "TLTYPE", "TLGRP", "TLGRPCOUNT", "TLOPNO", "TLSUBOPNO",
    "TLNODE", "TLCOUNT", "CTRLKEY", "OPWKCEN", "OPDESC", "WORK", "WORK_UNIT",
    "PERSON", "DURATION", "DURATION_UNIT", "ACTTYPE", "SUIT", "FREQUENCY",
    "CA10TXT", "SO10TXT", "TEXTTITLE", "FORMAT", "LONGTEXT",
]

# Post-rename column names read_mplan_bokor (Task 12) assigns — validated
# after ingest, not against the raw file's merged-header row labels.
EXPECTED_MPLAN_COLUMNS = [
    "maintenance_plan", "task_list", "pm_planner_group", "main_work_center",
    "no_of_equipment", "equipment_with_plan_status", "equipment_with_rtof_status",
    "equipment_with_mplan_defined", "mplan_completion_pct",
]


class SchemaValidationError(Exception):
    pass


def _validate(df: pl.DataFrame, expected_columns: list[str], source_name: str) -> None:
    missing = [c for c in expected_columns if c not in df.columns]
    if missing:
        raise SchemaValidationError(
            f"{source_name} is missing expected columns: {missing}. "
            "The source file's schema no longer matches the documented baseline "
            "(§3/§4a of the architecture) — halt and re-confirm before proceeding "
            "rather than let a pain-point function fail with a confusing error deep in the pipeline."
        )


def validate_floc_schema(df: pl.DataFrame) -> None:
    _validate(df, EXPECTED_FLOC_COLUMNS, "Agent A FLOC output")


def validate_equipment_schema(df: pl.DataFrame) -> None:
    _validate(df, EXPECTED_EQUIPMENT_COLUMNS, "Agent A Equipment output")


def validate_task_list_group_schema(df: pl.DataFrame) -> None:
    _validate(df, EXPECTED_TASK_LIST_GROUP_COLUMNS, "Bokor Task List Group.xlsx")


def validate_long_text_schema(df: pl.DataFrame) -> None:
    _validate(df, EXPECTED_LONG_TEXT_COLUMNS, "Bokor Long Text_Aug26_LATEST.xlsm (post WORK_UNIT/DURATION_UNIT rename)")


def validate_mplan_schema(df: pl.DataFrame) -> None:
    _validate(df, EXPECTED_MPLAN_COLUMNS, "MPLAN BOKOR AUG26.xlsx (post positional column assignment)")
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_normalize.py -v
```
Expected: 10 passed (5 normalization + 5 schema guard).

- [ ] **Step 5: Commit manually**

Commit `scripts/validate_schema.py`, `tests/test_normalize.py` — message like `feat: schema validation guards for all 5 input sources (Agent A + 3 primary files)`.

---

## Task 5: `evidence_connectors/` — OREDA + PITSTOPS Connectors

**Files:**
- Create: `Agent_C_TaskList_MPlan/evidence_connectors/__init__.py`
- Create: `Agent_C_TaskList_MPlan/evidence_connectors/oreda_connector.py`
- Create: `Agent_C_TaskList_MPlan/evidence_connectors/pitstops_connector.py`
- Create: `Agent_C_TaskList_MPlan/tests/test_connectors.py`

**Interfaces:**
- Produces (`oreda_connector.py`): `query_oreda_tables(db_path: str) -> list[str]` — lists table names. `is_oreda_applicable_to_pp5(db_path: str) -> tuple[bool, str]` — returns `(False, reason)` re-verifying, each run, the two independent §5 PP5 reasons (no HVAC taxonomy; `manhour_repair_mean` is corrective repair time, not preventive maintenance duration) against the live `OREDA.db`.
- Produces (`pitstops_connector.py`): `load_pitstops_tasklists(paths: list[str]) -> pl.DataFrame`, `discipline_duration_ranges(df: pl.DataFrame) -> pl.DataFrame` (columns `Discipline, n, min_hrs, median_hrs, p95_hrs, max_hrs`), `DISCIPLINE_TO_OPWKCEN` (module dict), `flag_implausible_work(work_hours: float, opwkcen: str, ranges: pl.DataFrame) -> str | None` (returns `"SUSPICIOUS"` at >=10x the mapped discipline's `max_hrs`, else `None` — detection-only, never a numeric correction).

- [ ] **Step 1: Write the failing tests**

```python
import sqlite3
from pathlib import Path

import openpyxl
import polars as pl

from evidence_connectors.oreda_connector import is_oreda_applicable_to_pp5, query_oreda_tables
from evidence_connectors.pitstops_connector import (
    discipline_duration_ranges,
    flag_implausible_work,
    load_pitstops_tasklists,
)


def test_query_oreda_tables_lists_table_names(tmp_path):
    db_path = tmp_path / "test_oreda.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE Compressors (id INTEGER, manhour_repair_mean REAL)")
    conn.execute("CREATE TABLE Pumps (id INTEGER, manhour_repair_mean REAL)")
    conn.commit()
    conn.close()

    tables = query_oreda_tables(str(db_path))
    assert set(tables) == {"Compressors", "Pumps"}


def test_oreda_not_applicable_to_pp5_no_hvac_taxonomy(tmp_path):
    db_path = tmp_path / "test_oreda.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE Compressors (id INTEGER, manhour_repair_mean REAL)")
    conn.execute("CREATE TABLE Pumps (id INTEGER, manhour_repair_mean REAL)")
    conn.execute("CREATE TABLE GasTurbines (id INTEGER, manhour_repair_mean REAL)")
    conn.execute("CREATE TABLE Valves (id INTEGER, manhour_repair_mean REAL)")
    conn.commit()
    conn.close()

    applicable, reason = is_oreda_applicable_to_pp5(str(db_path))
    assert applicable is False
    assert "hvac" in reason.lower()


def _write_pitstops_xlsx(path: Path, rows: list[tuple]) -> None:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(("Group", "EquipmentNo", "FuncLoc", "Discipline", "Dur (Hrs)"))
    for row in rows:
        ws.append(row)
    wb.save(path)


def test_load_and_range_pitstops(tmp_path):
    path1 = tmp_path / "BOBELA_TA_2024_Tasklist.xlsx"
    _write_pitstops_xlsx(
        path1,
        [
            ("0", "642RV-101", "090XV-030", "Static", 0.1),
            ("0", "642RV-102", "090XV-031", "Static", 60.0),
            ("0", "642RV-103", "090XV-032", "Electrical", 1.0),
        ],
    )
    df = load_pitstops_tasklists([str(path1)])
    assert df.shape[0] == 3

    ranges = discipline_duration_ranges(df)
    static_row = ranges.filter(pl.col("Discipline") == "Static")
    assert static_row["n"][0] == 2
    assert static_row["max_hrs"][0] == 60.0


def test_flag_implausible_work_detects_order_of_magnitude_outlier():
    ranges = pl.DataFrame({"Discipline": ["Static"], "max_hrs": [60.0]})
    assert flag_implausible_work(700.0, "BMECH", ranges) == "SUSPICIOUS"
    assert flag_implausible_work(50.0, "BMECH", ranges) is None


def test_flag_implausible_work_returns_none_when_discipline_unmapped():
    ranges = pl.DataFrame({"Discipline": ["Static"], "max_hrs": [60.0]})
    assert flag_implausible_work(700.0, "UNKNOWN_WC", ranges) is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_connectors.py -v
```
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write `evidence_connectors/__init__.py`** (empty)

```python
```

- [ ] **Step 4: Write `evidence_connectors/oreda_connector.py`**

```python
import sqlite3

# §5 PP5 — confirmed offshore process/rotating equipment taxonomy tables.
# OREDA covers these categories; it does not cover HVAC.
KNOWN_OREDA_CATEGORIES = {"Compressors", "Pumps", "GasTurbines", "Valves"}


def query_oreda_tables(db_path: str) -> list[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    finally:
        conn.close()
    return [r[0] for r in rows]


def is_oreda_applicable_to_pp5(db_path: str) -> tuple[bool, str]:
    tables = query_oreda_tables(db_path)
    has_hvac_taxonomy = any("hvac" in t.lower() for t in tables)
    if not has_hvac_taxonomy:
        return False, (
            "OREDA.db has no HVAC-category taxonomy (only offshore process/rotating "
            f"equipment categories are present: {sorted(set(tables) & KNOWN_OREDA_CATEGORIES) or tables}); "
            "and even where a match exists, manhour_repair_mean is a corrective "
            "repair-after-failure time, not a planned PM operation duration — a "
            "different quantity from Bokor Long Text's WORK field. Not usable for PP5."
        )
    return False, (
        "manhour_repair_mean is a corrective repair-after-failure time, not a "
        "planned PM operation duration — a different quantity from Bokor Long "
        "Text's WORK field. Not usable for PP5 regardless of taxonomy match."
    )
```

- [ ] **Step 5: Write `evidence_connectors/pitstops_connector.py`**

```python
import polars as pl

# §5 PP5 — best-effort, unverified correspondence between PITSTOPS'
# discipline labels and Bokor Long Text's OPWKCEN codes. No document ties
# the two naming schemes together; treat matches as a weak signal only.
DISCIPLINE_TO_OPWKCEN = {
    "BELEC": "Electrical",
    "SKO-ELEC": "Electrical",
    "BMECH": "Static",
    "MECH": "Static",
    "SKO-STAT": "Static",
    "SKO-ROTA": "Rotating",
    "INST": "Instrument & Control",
    "SKO-MCI": "Instrument & Control",
    "CP2INST": "Instrument & Control",
}

IMPLAUSIBLE_MULTIPLIER = 10


def load_pitstops_tasklists(paths: list[str]) -> pl.DataFrame:
    frames = [pl.read_excel(p) for p in paths]
    return pl.concat(frames, how="vertical_relaxed")


def discipline_duration_ranges(df: pl.DataFrame) -> pl.DataFrame:
    return (
        df.group_by("Discipline")
        .agg(
            pl.len().alias("n"),
            pl.col("Dur (Hrs)").min().alias("min_hrs"),
            pl.col("Dur (Hrs)").median().alias("median_hrs"),
            pl.col("Dur (Hrs)").quantile(0.95).alias("p95_hrs"),
            pl.col("Dur (Hrs)").max().alias("max_hrs"),
        )
    )


def flag_implausible_work(work_hours: float, opwkcen: str, ranges: pl.DataFrame) -> str | None:
    discipline = DISCIPLINE_TO_OPWKCEN.get(opwkcen)
    if discipline is None:
        return None
    matching = ranges.filter(pl.col("Discipline") == discipline)
    if matching.shape[0] == 0:
        return None
    max_hrs = matching["max_hrs"][0]
    if max_hrs and work_hours >= max_hrs * IMPLAUSIBLE_MULTIPLIER:
        return "SUSPICIOUS"
    return None
```

- [ ] **Step 6: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_connectors.py -v
```
Expected: 5 passed.

- [ ] **Step 7: Commit manually**

Commit `evidence_connectors/`, `tests/test_connectors.py` — message like `feat: OREDA + PITSTOPS evidence connectors`.

---

## Task 6: `scripts/build_ground_truth.py`

**Files:**
- Create: `Agent_C_TaskList_MPlan/scripts/build_ground_truth.py`
- Test: append to `Agent_C_TaskList_MPlan/tests/test_normalize.py`

**Interfaces:**
- Produces: `extract_pdf_text(path: str) -> str` (via PyMuPDF4LLM), `write_ground_truth_cache(pain_point: str, content: str, source_document: str, section_reference: str, cache_dir: str) -> str` — writes `{cache_dir}/{pain_point}.md` with a header block `Pain Point / Source / Section` followed by `content`, returns the written path.

- [ ] **Step 1: Append the failing test to `tests/test_normalize.py`**

```python
from scripts.build_ground_truth import write_ground_truth_cache


def test_write_ground_truth_cache_includes_citation_chain(tmp_path):
    cache_dir = tmp_path / "ground_truth_cache"
    cache_dir.mkdir()
    path = write_ground_truth_cache(
        pain_point="PP01_TaskList_Naming",
        content="Always use General Task List type.",
        source_document="UDMS.pdf",
        section_reference="§9.2",
        cache_dir=str(cache_dir),
    )
    text = Path(path).read_text()
    assert "PP01_TaskList_Naming" in text
    assert "UDMS.pdf" in text
    assert "§9.2" in text
    assert "Always use General Task List type." in text
```

(Add `from pathlib import Path` to the top of `tests/test_normalize.py` if not already imported.)

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_normalize.py -v
```
Expected: the new test FAILs — `ModuleNotFoundError` for `scripts.build_ground_truth`. The other 8 tests still pass.

- [ ] **Step 3: Append a second failing test for the per-PP page-range extraction, to `tests/test_normalize.py`**

```python
from scripts.build_ground_truth import extract_pdf_page_range


def test_extract_pdf_page_range_returns_only_requested_pages(tmp_path):
    import fitz  # PyMuPDF

    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    for text in ["page one content", "page two content", "page three content"]:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(pdf_path)
    doc.close()

    result = extract_pdf_page_range(str(pdf_path), start_page=2, end_page=2)
    assert "page two" in result
    assert "page one" not in result
    assert "page three" not in result
```

- [ ] **Step 4: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_normalize.py -v
```
Expected: this new test FAILs — `ImportError: cannot import name 'extract_pdf_page_range'`. Prior 9 tests still pass.

- [ ] **Step 5: Write `scripts/build_ground_truth.py`**

**This is the corrected version** — the earlier draft extracted the entire UDMS PDF and wrote the same full-document text into all 7 pain-point cache files, which is wrong: each `ground_truth_cache/PP0N_*.md` must hold only that pain point's cited excerpt from its actual source document(s) per §4c's table, not the whole document. `extract_pdf_page_range` extracts a specific page span so each PP entry pulls only its own pages.

```python
from pathlib import Path

import pymupdf4llm


def extract_pdf_text(path: str) -> str:
    return pymupdf4llm.to_markdown(path)


def extract_pdf_page_range(path: str, start_page: int, end_page: int) -> str:
    # start_page/end_page are 1-indexed, inclusive, matching how a human
    # cites "page 12" — pymupdf4llm's `pages` argument is 0-indexed.
    page_indices = list(range(start_page - 1, end_page))
    return pymupdf4llm.to_markdown(path, pages=page_indices)


def write_ground_truth_cache(
    pain_point: str, content: str, source_document: str, section_reference: str, cache_dir: str
) -> str:
    out_path = Path(cache_dir) / f"{pain_point}.md"
    header = (
        f"<!-- GENERATED CACHE — do not hand-edit. If this disagrees with "
        f"{source_document}, the source document wins. -->\n\n"
        f"# {pain_point}\n\n"
        f"**Source:** {source_document}\n"
        f"**Section:** {section_reference}\n\n"
    )
    out_path.write_text(header + content)
    return str(out_path)


if __name__ == "__main__":
    # Regenerates the 7 pain-point ground-truth cache files from
    # ground_truth_sources/ — each entry pulls ONLY its own cited page
    # range from its own source document, per §4c's table. The page
    # numbers below are placeholders (marked TODO) until confirmed
    # against the real page each UDMS section falls on — populate them
    # by opening ground_truth_sources/UDMS.pdf and locating each section
    # heading before the first real run; do not guess a page number.
    base = Path(__file__).resolve().parent.parent
    sources_dir = base / "ground_truth_sources"
    cache_dir = base / "ground_truth_cache"
    cache_dir.mkdir(exist_ok=True)

    # (pain_point, source_filename, section_reference, start_page, end_page)
    entries = [
        ("PP01_TaskList_Naming", "UDMS.pdf", "§9.2, §9.4", 1, 1),       # TODO: confirm pages
        ("PP02_Work_Centre", "UDMS.pdf", "§9.8, §9.17, §10.4", 1, 1),   # TODO: confirm pages
        ("PP03_Orphan_TaskList", "UDMS.pdf", "§9.6", 1, 1),             # TODO: confirm pages
        ("PP04_Duplicate_TaskList", "UDMS.pdf", "§9.6", 1, 1),          # TODO: confirm pages
        ("PP05_Manhours", "UDMS.pdf", "§9.20-21", 1, 1),                # TODO: confirm pages
        ("PP06_MPlan_OnHold", "UDMS.pdf", "§9.12, §11.1-11.5", 1, 1),   # TODO: confirm pages
        ("PP07_Hanging_MI", "UDMS.pdf", "§10", 1, 1),                   # TODO: confirm pages
    ]
    for pain_point, source_filename, section, start_page, end_page in entries:
        content = extract_pdf_page_range(str(sources_dir / source_filename), start_page, end_page)
        write_ground_truth_cache(pain_point, content, source_filename, section, str(cache_dir))
        print(f"wrote {pain_point} from {source_filename} pages {start_page}-{end_page}")
```

**Note for the implementer — this is a real open item, not glossed over:** the `start_page`/`end_page` values above are placeholders. §4c of the architecture document cites UDMS sections by number (`§9.2`, `§9.4`, etc.) but this plan has not independently confirmed which physical PDF page each section falls on. Before the first real run, open `ground_truth_sources/UDMS.pdf`, locate each cited section, and replace the placeholder page numbers — do not ship this script generating cache files from page 1 for every pain point, and do not guess page numbers to make the placeholder look resolved. PP2 additionally cites `SKA_MPG_MWC_PMMS.pptx` (§4c) for the Planner-Group-to-Work-Centre mapping — extracting from a `.pptx` needs a slide-text reader (e.g. `python-pptx`) rather than `pymupdf4llm`; add a `extract_pptx_text(path: str, slide_numbers: list[int]) -> str` helper alongside `extract_pdf_page_range` when that mapping is confirmed (§9 item 6 — currently blocked on the same client confirmation `work_centre_families.yaml`'s empty lists are blocked on).

- [ ] **Step 6: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_normalize.py -v
```
Expected: 10 passed.

- [ ] **Step 7: Commit manually**

Commit `scripts/build_ground_truth.py`, `tests/test_normalize.py` — message like `feat: ground truth cache builder, per-PP source-specific extraction`.

---

## Task 7: `validation.py` — PP1 and PP2

**Files:**
- Modify: `Agent_C_TaskList_MPlan/validation.py` (append `run_pp1`, `run_pp2` below `Finding`)
- Modify: `Agent_C_TaskList_MPlan/tests/test_validation.py` (append tests)

**Interfaces:**
- Produces:
  - `run_pp1(task_list_group: pl.DataFrame, platform_codes: list[str], reuse_threshold: int = 4) -> list[Finding]` — needs `Group` column. `reuse_threshold` is driven by `config/thresholds.yaml`'s `pp1.reused_prefix_min_occurrences` in production (Task 12's `run_pipeline`), with the same value `4` kept as the function's own default for direct unit-test calls that omit it.
  - `run_pp2(task_list_group: pl.DataFrame, normalized_operations: pl.DataFrame, work_centre_families: dict, multi_variants: list[str], valid_work_unit: str) -> list[Finding]` — `task_list_group` needs `Maintenance Item, Main Work Center, Maint. Planner Group, Group, Group Counter`; `normalized_operations` needs `TLGRP, TLGRPCOUNT, OPWKCEN, WORK, WORK_UNIT, OPDESC`. `multi_variants` is a list of known MULTI-type substrings (`["BMULTI", "TMULTI", "MULTI"]` — see the Source File Reference note: the real data never carries the literal string `"MULTI"` alone, only `BMULTI`/`TMULTI`). A Work Centre value is treated as MULTI-type when it **contains** any variant as a substring, not exact-equality. **Corrected: WORK is ranked by discipline only within the single canonical comparable unit `valid_work_unit`** (the same `MHR` unit §5 PP5's formula is scoped to, from `unit_rules.yaml`) — never summed across `WORK_UNIT` groups into one total, and never ranked by picking the numerically largest total across different units (the earlier draft grouped by `["OPWKCEN", "WORK_UNIT"]` correctly but then sorted every resulting group together regardless of unit, which could still rank `100 STD` above `10 MHR`; this version filters to `WORK_UNIT == valid_work_unit` before ranking at all, and fails closed to `NULL`/`0` if the Item has no operations in that unit). An **empty** `approved_work_centres` list for a Planner Group means the mapping is not yet confirmed (§9 item 6) — this fails closed to `NULL`/`0`, never silently treated as "anything is approved."

- [ ] **Step 1: Append the failing tests to `tests/test_validation.py`**

```python
import polars as pl

from validation import run_pp1, run_pp2

FAMILIES = {
    "BOS": {"approved_work_centres": ["BMECH", "BELEC"]},
    "MEW": {"approved_work_centres": []},  # not yet confirmed, §9 item 6
}


def test_pp1_platform_prefix_match_yields_no_finding_needing_correction():
    df = pl.DataFrame({"Group": ["BOKOKC01"]})
    findings = run_pp1(df, platform_codes=["BOKO", "BOCP"])
    assert findings == []


def test_pp1_non_platform_prefix_yields_null_recommendation_zero_confidence():
    df = pl.DataFrame({"Group": ["MYVES$$2"]})
    findings = run_pp1(df, platform_codes=["BOKO", "BOCP"])
    assert len(findings) == 1
    finding = findings[0]
    assert finding.recommended_value is None
    assert finding.confidence == 0
    assert finding.pain_point == "PP1"


def test_pp1_reused_non_platform_prefix_raises_detection_confidence():
    df = pl.DataFrame({"Group": ["MYVES$$2", "MYVES$$2", "MYVES$$2", "MYVES$$2"]})
    findings = run_pp1(df, platform_codes=["BOKO", "BOCP"])
    assert all(f.detection_confidence == 90 for f in findings)


MULTI_VARIANTS = ["BMULTI", "TMULTI", "MULTI"]


def test_pp2_item_level_multi_recommends_highest_work_discipline():
    # Uses BMULTI, not the literal "MULTI" — matches the real data.
    task_list_group = pl.DataFrame(
        {
            "Maintenance Item": ["978469"],
            "Main Work Center": ["BMULTI"],
            "Maint. Planner Group": ["BOS"],
            "Group": ["BOKOKC01"],
            "Group Counter": ["10"],
        }
    )
    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01", "BOKOKC01"],
            "TLGRPCOUNT": ["10", "10"],
            "OPWKCEN": ["BMECH", "BELEC"],
            "WORK": [10.0, 2.0],
            "WORK_UNIT": ["MHR", "MHR"],
            "OPDESC": ["mech work", "elec work"],
        }
    )
    findings = run_pp2(task_list_group, normalized_operations, FAMILIES, multi_variants=MULTI_VARIANTS, valid_work_unit="MHR")
    item_finding = [f for f in findings if f.field_name == "Main Work Center"][0]
    assert item_finding.recommended_value == "BMECH"
    assert item_finding.confidence == 95


def test_pp2_item_level_multi_never_ranks_across_incompatible_units():
    # Regression test: BELEC has a numerically larger STD total (100.0)
    # than BMECH's MHR total (10.0) — 100 STD is NOT comparable to 10 MHR.
    # A buggy implementation that ranks all (discipline, unit) totals
    # together regardless of unit would wrongly pick BELEC here. The
    # correct behavior restricts ranking to the single valid_work_unit
    # (MHR) and recommends BMECH, the only discipline with any MHR rows.
    task_list_group = pl.DataFrame(
        {
            "Maintenance Item": ["978469"],
            "Main Work Center": ["BMULTI"],
            "Maint. Planner Group": ["BOS"],
            "Group": ["BOKOKC01"],
            "Group Counter": ["10"],
        }
    )
    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01", "BOKOKC01"],
            "TLGRPCOUNT": ["10", "10"],
            "OPWKCEN": ["BMECH", "BELEC"],
            "WORK": [10.0, 100.0],
            "WORK_UNIT": ["MHR", "STD"],
            "OPDESC": ["mech work MHR", "elec work STD"],
        }
    )
    findings = run_pp2(task_list_group, normalized_operations, FAMILIES, multi_variants=MULTI_VARIANTS, valid_work_unit="MHR")
    item_finding = [f for f in findings if f.field_name == "Main Work Center"][0]
    assert item_finding.recommended_value == "BMECH"
    assert item_finding.confidence == 95


def test_pp2_item_level_multi_fails_closed_when_no_rows_in_comparable_unit():
    # All operations are STD, none MHR — no comparable basis to rank on,
    # must fail closed rather than rank STD totals against each other.
    task_list_group = pl.DataFrame(
        {
            "Maintenance Item": ["978469"],
            "Main Work Center": ["BMULTI"],
            "Maint. Planner Group": ["BOS"],
            "Group": ["BOKOKC01"],
            "Group Counter": ["10"],
        }
    )
    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01", "BOKOKC01"],
            "TLGRPCOUNT": ["10", "10"],
            "OPWKCEN": ["BMECH", "BELEC"],
            "WORK": [10.0, 100.0],
            "WORK_UNIT": ["STD", "STD"],
            "OPDESC": ["mech work STD", "elec work STD"],
        }
    )
    findings = run_pp2(task_list_group, normalized_operations, FAMILIES, multi_variants=MULTI_VARIANTS, valid_work_unit="MHR")
    item_finding = [f for f in findings if f.field_name == "Main Work Center"][0]
    assert item_finding.recommended_value is None
    assert item_finding.confidence == 0


def test_pp2_item_level_multi_fails_closed_when_approved_list_empty():
    task_list_group = pl.DataFrame(
        {
            "Maintenance Item": ["978469"],
            "Main Work Center": ["TMULTI"],
            "Maint. Planner Group": ["MEW"],  # MEW's approved_work_centres is [] in FAMILIES
            "Group": ["BOKOKC01"],
            "Group Counter": ["10"],
        }
    )
    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01"],
            "TLGRPCOUNT": ["10"],
            "OPWKCEN": ["BMECH"],
            "WORK": [10.0],
            "WORK_UNIT": ["MHR"],
            "OPDESC": ["mech work"],
        }
    )
    findings = run_pp2(task_list_group, normalized_operations, FAMILIES, multi_variants=MULTI_VARIANTS, valid_work_unit="MHR")
    item_finding = [f for f in findings if f.field_name == "Main Work Center"][0]
    # Empty approved list = mapping not confirmed (§9 item 6) -> fail
    # closed, never silently treated as "anything is approved."
    assert item_finding.recommended_value is None
    assert item_finding.confidence == 0


def test_pp2_operation_level_multi_variants_are_noncompliant_no_guess():
    # BMULTI and TMULTI both must be caught — not only the literal "MULTI".
    task_list_group = pl.DataFrame(
        {
            "Maintenance Item": ["978469"],
            "Main Work Center": ["BMECH"],
            "Maint. Planner Group": ["BOS"],
            "Group": ["BOKOKC01"],
            "Group Counter": ["10"],
        }
    )
    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01", "BOKOKC02"],
            "TLGRPCOUNT": ["10", "10"],
            "TLOPNO": ["10", "20"],
            "TLSUBOPNO": ["0", "0"],
            "OPWKCEN": ["TMULTI", "BMULTI"],
            "WORK": [4.0, 4.0],
            "WORK_UNIT": ["MHR", "MHR"],
            "OPDESC": ["ambiguous description", "ambiguous description"],
        }
    )
    findings = run_pp2(task_list_group, normalized_operations, FAMILIES, multi_variants=MULTI_VARIANTS, valid_work_unit="MHR")
    op_findings = [f for f in findings if f.field_name == "OPWKCEN"]
    assert len(op_findings) == 2
    assert all(f.recommended_value is None and f.confidence == 0 for f in op_findings)
    # Full logical operation key, matching PP5's record_key grain exactly
    # so write_annotated_long_text can map findings back to the right row.
    assert {f.record_key for f in op_findings} == {"BOKOKC01-10-10-0", "BOKOKC02-10-20-0"}
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: the 8 new tests FAIL — `ImportError: cannot import name 'run_pp1'`. The 5 schema tests still pass.

- [ ] **Step 3: Append to `validation.py`**

```python
import polars as pl

DEFAULT_REUSE_THRESHOLD = 4  # §5 PP1 — MYVES$$2 pattern: default if config isn't supplied


def run_pp1(
    task_list_group: pl.DataFrame,
    platform_codes: list[str],
    reuse_threshold: int = DEFAULT_REUSE_THRESHOLD,
) -> list[Finding]:
    # reuse_threshold is driven by config/thresholds.yaml's
    # pp1.reused_prefix_min_occurrences (Task 12's run_pipeline passes
    # it explicitly) — the module-level default only applies when a
    # caller (e.g. a direct unit test) omits it.
    findings: list[Finding] = []
    prefix_counts = (
        task_list_group.with_columns(pl.col("Group").str.slice(0, 4).alias("prefix"))
        .group_by("prefix")
        .agg(pl.len().alias("count"))
    )
    non_platform_prefixes = {
        row["prefix"] for row in prefix_counts.iter_rows(named=True) if row["prefix"] not in platform_codes
    }
    reused_prefixes = {
        row["prefix"]
        for row in prefix_counts.iter_rows(named=True)
        if row["prefix"] not in platform_codes and row["count"] >= reuse_threshold
    }

    for row in task_list_group.iter_rows(named=True):
        group = row["Group"]
        prefix = group[:4] if group else None
        if prefix is None or prefix in platform_codes:
            continue
        detection_confidence = 90 if prefix in reused_prefixes else 20
        findings.append(
            Finding(
                pain_point="PP1",
                record_key=group,
                field_name="Group",
                current_value=group,
                recommended_value=None,
                confidence=0,
                detection_confidence=detection_confidence,
                evidence_source="Bokor Task List Group.xlsx; UDMS.pdf §9.4",
            )
        )
    return findings


def _is_multi_type(value: str | None, multi_variants: list[str]) -> bool:
    # Real data never carries the literal string "MULTI" alone — it
    # carries BMULTI/TMULTI (verified: 743 TMULTI + 264 BMULTI in
    # OPWKCEN, 83 BMULTI in Main Work Center). Substring match, not
    # exact-equality, against every configured variant.
    if value is None:
        return False
    return any(variant in value for variant in multi_variants)


def run_pp2(
    task_list_group: pl.DataFrame,
    normalized_operations: pl.DataFrame,
    work_centre_families: dict,
    multi_variants: list[str],
    valid_work_unit: str,
) -> list[Finding]:
    findings: list[Finding] = []

    # Item-level MULTI: recommend the discipline with the highest summed
    # WORK across the Item's logical operations (UDMS §10.4).
    item_multi_rows = task_list_group.filter(
        pl.col("Main Work Center").map_elements(
            lambda v: _is_multi_type(v, multi_variants), return_dtype=pl.Boolean
        )
    )
    for row in item_multi_rows.iter_rows(named=True):
        current_value = row["Main Work Center"]
        item_ops = normalized_operations.filter(
            (pl.col("TLGRP") == row["Group"]) & (pl.col("TLGRPCOUNT") == row["Group Counter"])
        )
        if item_ops.shape[0] == 0:
            findings.append(
                Finding(
                    pain_point="PP2",
                    record_key=row["Maintenance Item"],
                    field_name="Main Work Center",
                    current_value=current_value,
                    recommended_value=None,
                    confidence=0,
                    detection_confidence=60,
                    evidence_source="Bokor Task List Group.xlsx",
                )
            )
            continue

        approved = work_centre_families.get(row["Maint. Planner Group"], {}).get("approved_work_centres", [])
        if not approved:
            # Empty approved list = mapping not confirmed for this
            # Planner Group (§9 item 6) — fail closed, never silently
            # treat "no list" as "anything is approved."
            findings.append(
                Finding(
                    pain_point="PP2",
                    record_key=row["Maintenance Item"],
                    field_name="Main Work Center",
                    current_value=current_value,
                    recommended_value=None,
                    confidence=0,
                    detection_confidence=60,
                    evidence_source="Bokor Task List Group.xlsx; SKA_MPG_MWC_PMMS.pptx (mapping not yet confirmed for this Planner Group, §9 item 6)",
                )
            )
            continue

        # Never sum WORK across incompatible units (e.g. MHR + STD) into
        # one total, and never rank a total from one unit against a
        # total from another — 100 STD is not comparable to 10 MHR.
        # Restrict to the single canonical comparable labor unit
        # (valid_work_unit, i.e. MHR — the unit §5 PP5's own formula is
        # scoped to) before ranking at all. If the Item's operations
        # have no rows in that unit, there is no comparable basis to
        # rank on — fail closed rather than pick the largest number
        # across incompatible units.
        comparable_ops = item_ops.filter(pl.col("WORK_UNIT") == valid_work_unit)
        if comparable_ops.shape[0] == 0:
            findings.append(
                Finding(
                    pain_point="PP2",
                    record_key=row["Maintenance Item"],
                    field_name="Main Work Center",
                    current_value=current_value,
                    recommended_value=None,
                    confidence=0,
                    detection_confidence=60,
                    evidence_source=f"Bokor Long Text_Aug26_LATEST.xlsm (no rows in the comparable {valid_work_unit} unit for this Item's operations)",
                )
            )
            continue
        by_discipline = comparable_ops.group_by("OPWKCEN").agg(pl.col("WORK").sum().alias("total_work"))
        top = by_discipline.sort("total_work", descending=True).row(0, named=True)

        if top["OPWKCEN"] not in approved:
            findings.append(
                Finding(
                    pain_point="PP2",
                    record_key=row["Maintenance Item"],
                    field_name="Main Work Center",
                    current_value=current_value,
                    recommended_value=None,
                    confidence=0,
                    detection_confidence=60,
                    evidence_source="Bokor Task List Group.xlsx; SKA_MPG_MWC_PMMS.pptx",
                )
            )
            continue
        findings.append(
            Finding(
                pain_point="PP2",
                record_key=row["Maintenance Item"],
                field_name="Main Work Center",
                current_value=current_value,
                recommended_value=top["OPWKCEN"],
                confidence=95,
                evidence_source="Bokor Task List Group.xlsx; Bokor Long Text_Aug26_LATEST.xlsm; UDMS.pdf §10.4",
            )
        )

    # Operation-level MULTI: UDMS §9.17 — no MULTI-type OPWKCEN allowed,
    # never guessed at. Matches BMULTI/TMULTI/etc, not only "MULTI".
    op_multi_rows = normalized_operations.filter(
        pl.col("OPWKCEN").map_elements(
            lambda v: _is_multi_type(v, multi_variants), return_dtype=pl.Boolean
        )
    )
    for row in op_multi_rows.iter_rows(named=True):
        # Full logical operation key (§5.0), matching PP5's record_key
        # grain exactly so write_annotated_long_text (output_writer.py)
        # can map every operation-level finding back to the correct row.
        record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}-{row['TLSUBOPNO']}"
        findings.append(
            Finding(
                pain_point="PP2",
                record_key=record_key,
                field_name="OPWKCEN",
                current_value=row["OPWKCEN"],
                recommended_value=None,
                confidence=0,
                detection_confidence=100,
                evidence_source="Bokor Long Text_Aug26_LATEST.xlsm; UDMS.pdf §9.17",
            )
        )

    return findings
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: 13 passed.

- [ ] **Step 5: Commit manually**

Commit `validation.py`, `tests/test_validation.py` — message like `feat: PP1 naming + PP2 work centre checks (MULTI-variant matching, unit-safe summation, fail-closed on unconfirmed families)`.

---

## Task 8: `validation.py` — PP3 and PP4

**Files:**
- Modify: `Agent_C_TaskList_MPlan/validation.py` (append `run_pp3`, `run_pp4`)
- Modify: `Agent_C_TaskList_MPlan/tests/test_validation.py` (append tests)

**Interfaces:**
- Produces:
  - `run_pp3(normalized_operations: pl.DataFrame, task_list_group: pl.DataFrame, mplan_detail_rows: pl.DataFrame) -> list[Finding]` — `normalized_operations` needs `TLGRP, TLGRPCOUNT`; `task_list_group` needs `Group, Group Counter`; `mplan_detail_rows` needs `TLTYPE, TLGRP, TLGRPCOUNT`.
  - `run_pp4(normalized_operations: pl.DataFrame, task_list_group: pl.DataFrame, text_similarity_threshold: float = 0.85, agent_c=None) -> list[Finding]` — `normalized_operations` needs `TLGRP, TLGRPCOUNT, OPDESC, LONGTEXT_AGGREGATED`; `task_list_group` needs `Group, Group Counter, Object Description`. Uses `difflib.SequenceMatcher` (stdlib, deterministic) as the text-similarity signal. **Corrected from the earlier draft: this function never picks which Task List of a similar pair is "the one to keep"** — no evidence source in this architecture (§5 PP4, §8) establishes retention precedence between two candidate duplicates, so inventing one (e.g. always picking the second of the pair) would violate the no-invented-values rule. Both cases (bridge-linked strong match, unlinked text-only match) report the **pair** as `record_key` with `recommended_value=None, confidence=0`, carrying the match strength only as `detection_confidence` — a human reviewer, not this function, decides which Task List survives.
    **The Deep Agent is now actually invoked, not just a described role:** `agent_c` (optional — `None` in every unit test, since tests must not require real Azure credentials, see Task 12's "Injecting a fake agent" note) is called on the sub-threshold, unlinked text-only-match candidates (the `detection_confidence=40` case) — this is the one PP4 case with genuine ambiguity for a semantic judgment to resolve: a candidate pair that *failed* the deterministic literal-similarity bar might still describe the same maintenance task in different words (a real semantic-matching problem), or might genuinely be two different tasks that happen to share some vocabulary (a false positive worth downgrading). When `agent_c` is provided, `run_pp4` invokes it with the pair's `OPDESC`/`LONGTEXT_AGGREGATED` text and asks it to classify the pair as `SAME_TASK`, `DIFFERENT_TASK`, or `UNCERTAIN`; `SAME_TASK` raises `detection_confidence` to `70` (still below the 70 recommendation floor's `Confidence`, which stays `0` — the agent's semantic read still never selects a retained Task List), `DIFFERENT_TASK` drops the finding entirely (not a duplicate candidate at all), and `UNCERTAIN` (or an agent call failure) leaves the deterministic `detection_confidence=40` result unchanged. The bridge-linked strong-match case (`detection_confidence=90`) is not sent to the agent — its deterministic signal is already the strongest tier PP4 produces, and downgrading a confirmed multi-field match on an LLM's second-guess would reduce reliability, not improve it.

- [ ] **Step 1: Append the failing tests to `tests/test_validation.py`**

```python
from validation import run_pp3, run_pp4


def test_pp3_referenced_task_list_no_finding():
    normalized_operations = pl.DataFrame({"TLGRP": ["BOKOKC01"], "TLGRPCOUNT": ["10"]})
    task_list_group = pl.DataFrame({"Group": ["BOKOKC01"], "Group Counter": ["10"]})
    mplan_detail = pl.DataFrame({"TLTYPE": [], "TLGRP": [], "TLGRPCOUNT": []})
    findings = run_pp3(normalized_operations, task_list_group, mplan_detail)
    assert findings == []


def test_pp3_orphan_with_mplan_evidence_gets_lower_detection_confidence():
    normalized_operations = pl.DataFrame({"TLGRP": ["BODA0582"], "TLGRPCOUNT": ["0"]})
    task_list_group = pl.DataFrame({"Group": [], "Group Counter": []})
    mplan_detail = pl.DataFrame({"TLTYPE": ["A"], "TLGRP": ["BODA0582"], "TLGRPCOUNT": ["0"]})
    findings = run_pp3(normalized_operations, task_list_group, mplan_detail)
    assert len(findings) == 1
    assert findings[0].recommended_value is None
    assert findings[0].confidence == 0
    assert findings[0].detection_confidence == 30


def test_pp3_orphan_with_no_evidence_gets_higher_detection_confidence():
    normalized_operations = pl.DataFrame({"TLGRP": ["ZZZZZZZZ"], "TLGRPCOUNT": ["99"]})
    task_list_group = pl.DataFrame({"Group": [], "Group Counter": []})
    mplan_detail = pl.DataFrame({"TLTYPE": [], "TLGRP": [], "TLGRPCOUNT": []})
    findings = run_pp3(normalized_operations, task_list_group, mplan_detail)
    assert findings[0].detection_confidence == 50


def test_pp4_bridge_linked_strong_match_flags_pair_without_picking_a_winner():
    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01", "BOKOKC02"],
            "TLGRPCOUNT": ["10", "10"],
            "OPDESC": ["PM,3M-VISUAL & PHYSICAL INSPECTION", "PM,3M-VISUAL & PHYSICAL INSPECTION"],
            "LONGTEXT_AGGREGATED": ["inspect the heat exchanger visually", "inspect the heat exchanger visually"],
        }
    )
    task_list_group = pl.DataFrame(
        {
            "Group": ["BOKOKC01", "BOKOKC02"],
            "Group Counter": ["10", "10"],
            "Object Description": ["Heat exchanger", "Heat exchanger"],
        }
    )
    findings = run_pp4(normalized_operations, task_list_group)
    assert len(findings) == 1
    # No evidence source establishes which Task List to retain — never
    # fabricate a winner. The strong multi-field match is reported as a
    # detection-confidence-backed candidate for human/Deep-Agent review.
    assert findings[0].recommended_value is None
    assert findings[0].confidence == 0
    assert findings[0].detection_confidence == 90
    assert "BOKOKC01" in findings[0].record_key and "BOKOKC02" in findings[0].record_key


def test_pp4_unlinked_text_only_match_stays_below_threshold_without_agent():
    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["ZZZZZZZZ", "YYYYYYYY"],
            "TLGRPCOUNT": ["01", "01"],
            "OPDESC": ["PM,3M-VISUAL & PHYSICAL INSPECTION", "PM,3M-VISUAL & PHYSICAL INSPECTION"],
            "LONGTEXT_AGGREGATED": ["inspect visually", "inspect visually"],
        }
    )
    task_list_group = pl.DataFrame({"Group": [], "Group Counter": [], "Object Description": []})
    findings = run_pp4(normalized_operations, task_list_group)  # agent_c=None (default)
    assert len(findings) == 1
    assert findings[0].recommended_value is None
    assert findings[0].confidence == 0
    assert findings[0].detection_confidence == 40


class _FakeAgentMessage:
    def __init__(self, content):
        self.content = content


class _FakeAgent:
    """Stands in for a real create_deep_agent()-built agent in tests —
    no Azure credentials required. See Task 12's "Injecting a fake agent"
    note: the real create_deep_agent(...) is only ever built in app.py's
    __main__ block, never implicitly by importing validation.py or app.py."""

    def __init__(self, reply_content: str):
        self.reply_content = reply_content

    def invoke(self, _payload):
        return {"messages": [_FakeAgentMessage(self.reply_content)]}


def test_pp4_agent_confirms_same_task_raises_detection_confidence_never_confidence():
    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["ZZZZZZZZ", "YYYYYYYY"],
            "TLGRPCOUNT": ["01", "01"],
            "OPDESC": ["PM,3M-VISUAL & PHYSICAL INSPECTION", "PM,3M-VISUAL & PHYSICAL INSPECTION"],
            "LONGTEXT_AGGREGATED": ["inspect visually", "inspect visually"],
        }
    )
    task_list_group = pl.DataFrame({"Group": [], "Group Counter": [], "Object Description": []})
    fake_agent = _FakeAgent("SAME_TASK")
    findings = run_pp4(normalized_operations, task_list_group, agent_c=fake_agent)
    assert len(findings) == 1
    assert findings[0].detection_confidence == 70
    # The agent's semantic read never selects a retained Task List, even
    # when it raises detection confidence.
    assert findings[0].recommended_value is None
    assert findings[0].confidence == 0


def test_pp4_agent_confirms_different_task_drops_the_candidate():
    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["ZZZZZZZZ", "YYYYYYYY"],
            "TLGRPCOUNT": ["01", "01"],
            "OPDESC": ["PM,3M-VISUAL & PHYSICAL INSPECTION", "PM,3M-VISUAL & PHYSICAL INSPECTION"],
            "LONGTEXT_AGGREGATED": ["inspect visually", "inspect visually"],
        }
    )
    task_list_group = pl.DataFrame({"Group": [], "Group Counter": [], "Object Description": []})
    fake_agent = _FakeAgent("DIFFERENT_TASK")
    findings = run_pp4(normalized_operations, task_list_group, agent_c=fake_agent)
    assert findings == []


def test_pp4_agent_failure_falls_back_to_deterministic_result():
    class _BrokenAgent:
        def invoke(self, _payload):
            raise RuntimeError("simulated agent unavailability")

    normalized_operations = pl.DataFrame(
        {
            "TLGRP": ["ZZZZZZZZ", "YYYYYYYY"],
            "TLGRPCOUNT": ["01", "01"],
            "OPDESC": ["PM,3M-VISUAL & PHYSICAL INSPECTION", "PM,3M-VISUAL & PHYSICAL INSPECTION"],
            "LONGTEXT_AGGREGATED": ["inspect visually", "inspect visually"],
        }
    )
    task_list_group = pl.DataFrame({"Group": [], "Group Counter": [], "Object Description": []})
    findings = run_pp4(normalized_operations, task_list_group, agent_c=_BrokenAgent())
    assert len(findings) == 1
    assert findings[0].detection_confidence == 40  # unchanged deterministic result, no crash
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: the 8 new tests FAIL — `ImportError: cannot import name 'run_pp3'`. Prior 13 tests still pass.

- [ ] **Step 3: Append to `validation.py`**

```python
from difflib import SequenceMatcher
from itertools import combinations


def run_pp3(
    normalized_operations: pl.DataFrame,
    task_list_group: pl.DataFrame,
    mplan_detail_rows: pl.DataFrame,
) -> list[Finding]:
    findings: list[Finding] = []
    bridge_keys = set(zip(task_list_group["Group"], task_list_group["Group Counter"]))
    mplan_keys = set(zip(mplan_detail_rows["TLGRP"], mplan_detail_rows["TLGRPCOUNT"]))

    distinct_operations = normalized_operations.select(["TLGRP", "TLGRPCOUNT"]).unique()
    for row in distinct_operations.iter_rows(named=True):
        key = (row["TLGRP"], row["TLGRPCOUNT"])
        if key in bridge_keys:
            continue
        has_mplan_evidence = key in mplan_keys
        # §5 PP3 — FLOC/Equipment active-status cross-check (third tier)
        # needs an Equipment/FLOC column at this grain that Bokor Long Text
        # does not carry today; the two tiers below are what the real join
        # keys support. See the plan's Task 8 implementer note.
        detection_confidence = 30 if has_mplan_evidence else 50
        findings.append(
            Finding(
                pain_point="PP3",
                record_key=f"{key[0]}-{key[1]}",
                field_name="Maintenance Item",
                current_value=None,
                recommended_value=None,
                confidence=0,
                detection_confidence=detection_confidence,
                evidence_source="Bokor Long Text_Aug26_LATEST.xlsm; Bokor Task List Group.xlsx; MPLAN BOKOR AUG26.xlsx",
            )
        )
    return findings


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a or "", b or "").ratio()


def _ask_agent_pp4_semantic_match(agent_c, opdesc_a: str, longtext_a: str, opdesc_b: str, longtext_b: str) -> str:
    # Returns "SAME_TASK", "DIFFERENT_TASK", or "UNCERTAIN". Any exception
    # (agent unreachable, malformed response, credentials missing) falls
    # back to "UNCERTAIN" — a semantic-review failure must never crash
    # the deterministic pipeline or silently become a confident answer.
    prompt = (
        "Two SAP Task List operations were flagged as a possible duplicate "
        "pair by a text-similarity check, but did not clear the exact-match "
        "threshold. Based on their descriptions, do they describe the SAME "
        "maintenance task, DIFFERENT tasks, or is it UNCERTAIN? Reply with "
        "exactly one word: SAME_TASK, DIFFERENT_TASK, or UNCERTAIN.\n\n"
        f"Operation A — OPDESC: {opdesc_a}\nOperation A — LONGTEXT: {longtext_a}\n\n"
        f"Operation B — OPDESC: {opdesc_b}\nOperation B — LONGTEXT: {longtext_b}"
    )
    try:
        result = agent_c.invoke({"messages": [{"role": "user", "content": prompt}]})
        reply = result["messages"][-1].content.strip().upper()
        if "SAME_TASK" in reply:
            return "SAME_TASK"
        if "DIFFERENT_TASK" in reply:
            return "DIFFERENT_TASK"
    except Exception:
        pass
    return "UNCERTAIN"


def run_pp4(
    normalized_operations: pl.DataFrame,
    task_list_group: pl.DataFrame,
    text_similarity_threshold: float = 0.85,
    agent_c=None,
) -> list[Finding]:
    findings: list[Finding] = []
    bridge_lookup = {
        (row["Group"], row["Group Counter"]): row["Object Description"]
        for row in task_list_group.iter_rows(named=True)
    }

    rows = list(
        normalized_operations.select(["TLGRP", "TLGRPCOUNT", "OPDESC", "LONGTEXT_AGGREGATED"]).unique().iter_rows(named=True)
    )

    for a, b in combinations(rows, 2):
        key_a = (a["TLGRP"], a["TLGRPCOUNT"])
        key_b = (b["TLGRP"], b["TLGRPCOUNT"])
        opdesc_sim = _similarity(a["OPDESC"], b["OPDESC"])
        longtext_sim = _similarity(a["LONGTEXT_AGGREGATED"], b["LONGTEXT_AGGREGATED"])
        object_desc_a = bridge_lookup.get(key_a)
        object_desc_b = bridge_lookup.get(key_b)

        if object_desc_a is not None and object_desc_b is not None:
            object_desc_sim = _similarity(object_desc_a, object_desc_b)
            if (
                opdesc_sim >= text_similarity_threshold
                and longtext_sim >= text_similarity_threshold
                and object_desc_sim >= text_similarity_threshold
            ):
                # Strong multi-field match confirms this PAIR is a likely
                # duplicate — it does NOT establish which of the two is
                # the authoritative Task List to retain. No evidence
                # source in this architecture answers that question, so
                # recommended_value stays None/0 here; only
                # detection_confidence reflects the match strength. A
                # human reviewer (or a future evidence source, e.g. a
                # Status/Created-On tiebreak) decides which survives.
                findings.append(
                    Finding(
                        pain_point="PP4",
                        record_key=f"{key_a[0]}-{key_a[1]} / {key_b[0]}-{key_b[1]}",
                        field_name="Group",
                        current_value=f"{key_a[0]}-{key_a[1]}",
                        recommended_value=None,
                        confidence=0,
                        detection_confidence=90,
                        evidence_source="Bokor Task List Group.xlsx (Object Description); Bokor Long Text_Aug26_LATEST.xlsm (OPDESC, LONGTEXT); UDMS.pdf §9.6",
                    )
                )
            continue

        # NOTE: an earlier draft had a second `continue` here for
        # "opdesc_sim/longtext_sim both >= threshold" — that was a real
        # bug, caught during implementation: it fires whenever both
        # operations happen to share highly similar OPDESC/LONGTEXT even
        # when they are NOT bridge-linked (object_desc_a/b is None), which
        # silently dropped exactly the unlinked sub-threshold-for-Object-
        # Description-but-strong-on-OPDESC/LONGTEXT candidates this
        # function is supposed to route to the agent below. The comment
        # "already handled by the strong-match branch above" is only true
        # when a bridge match was actually attempted (the `if
        # object_desc_a is not None and object_desc_b is not None:` block
        # above) — for an unlinked pair that block never runs, so nothing
        # was "already handled." Removed; every unlinked pair now falls
        # through to the sub-threshold/agent-mediated path below,
        # regardless of how similar its OPDESC/LONGTEXT text is.

        # Sub-threshold candidate: the deterministic literal-similarity
        # check alone is inconclusive. This is where the Deep Agent's
        # semantic judgment (§11.1, §11.3) actually gets invoked — not
        # merely defined and left unused.
        detection_confidence = 40
        agent_verdict = None
        if agent_c is not None:
            agent_verdict = _ask_agent_pp4_semantic_match(
                agent_c, a["OPDESC"], a["LONGTEXT_AGGREGATED"], b["OPDESC"], b["LONGTEXT_AGGREGATED"]
            )
        if agent_verdict == "DIFFERENT_TASK":
            continue  # agent confirmed these are not a duplicate candidate at all
        if agent_verdict == "SAME_TASK":
            detection_confidence = 70  # still below the 70 recommendation Confidence floor by design —
            # this raises detection strength only; it never selects a retained Task List.

        findings.append(
            Finding(
                pain_point="PP4",
                record_key=f"{key_a[0]}-{key_a[1]} / {key_b[0]}-{key_b[1]}",
                field_name="Group",
                current_value=f"{key_a[0]}-{key_a[1]}",
                recommended_value=None,
                confidence=0,
                detection_confidence=detection_confidence,
                evidence_source="Bokor Long Text_Aug26_LATEST.xlsm (OPDESC, LONGTEXT); UDMS.pdf §9.6"
                + (" + Deep Agent semantic review" if agent_verdict else ""),
            )
        )

    return findings
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: 21 passed.

- [ ] **Step 5: Commit manually**

Commit `validation.py`, `tests/test_validation.py` — message like `feat: PP3 orphan check + PP4 duplicate task list check (never fabricates a retained-Task-List winner)`.

**Note for the implementer (PP3):** §5 PP3's full logic also cross-checks FLOC/Equipment active status as a third detection-confidence tier (`70` for orphans tied to inactive assets). This is left out here because it needs an Equipment/FLOC column joined through `Bokor Task List Group` for keys that, by definition, have no bridge row to join through. If a future data drop adds an Equipment/FLOC column directly to `Bokor Long Text`, extend `run_pp3` with that third tier then — do not guess a mapping now.

**Note for the implementer (PP4 and the Deep Agent):** `run_pp4` above is the deterministic gate — text similarity via `difflib`, never picking a winner. §11.3 names PP4 as the pain point specifically warranting the Deep Agent's semantic judgment, on top of this deterministic gate, not instead of it: in Task 12's `run_pipeline`, the agent is given the `Object Description`/`OPDESC`/`LONGTEXT_AGGREGATED` text for a candidate pair `run_pp4` already flagged and asked whether the semantic content genuinely describes the same maintenance task (catching cases `difflib`'s literal string similarity misses, e.g. paraphrased descriptions) — but the agent's judgment can only ever raise or lower `Detection_Confidence` on an existing candidate pair, and still never produces a `Recommended_Value` picking one Task List over the other, since no evidence source in this architecture (§5 PP4, §8) establishes retention precedence. That gap (which Task List is authoritative when two are confirmed duplicates) is a genuine, currently-unresolved item — flag it in `output/Findings_Report.xlsx` for human review, never invent an answer.

---

## Task 9: `validation.py` — PP5

**Files:**
- Modify: `Agent_C_TaskList_MPlan/validation.py` (append `run_pp5`)
- Modify: `Agent_C_TaskList_MPlan/tests/test_validation.py` (append tests)

**Interfaces:**
- Produces: `run_pp5(normalized_operations: pl.DataFrame, valid_work_unit: str, valid_duration_unit: str, pitstops_ranges: pl.DataFrame | None = None, work_tolerance: float = 0.01, agent_c=None) -> list[Finding]` — needs `TLGRP, TLGRPCOUNT, TLOPNO, TLSUBOPNO, WORK, WORK_UNIT, PERSON, DURATION, DURATION_UNIT, OPWKCEN`. **Corrected from the earlier draft in three ways:** (1) `record_key` uses the full logical operation key `TLGRP+TLGRPCOUNT+TLOPNO+TLSUBOPNO` (§5.0's own normalization grain), not only `TLGRP+TLGRPCOUNT` — two different operations under the same Task List would otherwise collide onto the same `record_key`; (2) `WORK == PERSON * DURATION` uses a numeric tolerance (`abs(WORK - PERSON*DURATION) <= work_tolerance`), not a direct floating-point `!=` comparison, since float arithmetic can produce a value like `3.9999999998` that is mathematically equal to `4.0` but fails exact equality; (3) **the Deep Agent is now actually invoked, not just described** — on the unit-scope-excluded branch (§5 PP5's UNIT CHECK), `run_pp5` asks `agent_c` (optional, `None` by default in every unit test) to confirm OREDA's applicability via its tool before reporting insufficient evidence; the deterministic `NULL`/`0` result never changes (§5 PP5's own connector, `is_oreda_applicable_to_pp5`, independently re-verifies "not usable" every run — the agent's confirmation is a coordination step, not a source of truth), and any agent failure silently falls back to the unchanged deterministic path. Calls `evidence_connectors.pitstops_connector.flag_implausible_work` when `pitstops_ranges` is given.

- [ ] **Step 1: Append the failing tests to `tests/test_validation.py`**

```python
from validation import run_pp5


def test_pp5_blank_core_fields_null_confidence_zero():
    df = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [None], "WORK_UNIT": [None],
            "PERSON": [None], "DURATION": [None], "DURATION_UNIT": [None], "OPWKCEN": ["BMECH"],
        }
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR")
    assert len(findings) == 1
    assert findings[0].recommended_value is None
    assert findings[0].confidence == 0
    assert findings[0].record_key == "BOKOKC01-10-10-0"


def test_pp5_std_unit_out_of_scope_never_recommends_a_value():
    df = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [0.0], "WORK_UNIT": ["STD"],
            "PERSON": [2], "DURATION": [2.0], "DURATION_UNIT": ["HR"], "OPWKCEN": ["BMECH"],
        }
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR")
    assert len(findings) == 1
    assert findings[0].recommended_value is None
    assert findings[0].confidence == 0


def test_pp5_mhr_hr_mismatch_recommends_person_times_duration():
    df = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [0.0], "WORK_UNIT": ["MHR"],
            "PERSON": [2], "DURATION": [2.0], "DURATION_UNIT": ["HR"], "OPWKCEN": ["BMECH"],
        }
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR")
    assert len(findings) == 1
    assert findings[0].recommended_value == "4.0"
    assert findings[0].confidence == 100


def test_pp5_consistent_mhr_hr_row_yields_no_finding():
    df = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [4.0], "WORK_UNIT": ["MHR"],
            "PERSON": [2], "DURATION": [2.0], "DURATION_UNIT": ["HR"], "OPWKCEN": ["BMECH"],
        }
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR")
    assert findings == []


def test_pp5_uses_numeric_tolerance_not_exact_float_equality():
    # 2 * 2.0000000001 is float-arithmetic "close enough" to 4.0 but not
    # exactly equal — must not raise a spurious finding for this.
    df = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [4.0], "WORK_UNIT": ["MHR"],
            "PERSON": [2], "DURATION": [2.0000000001], "DURATION_UNIT": ["HR"], "OPWKCEN": ["BMECH"],
        }
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR", work_tolerance=0.01)
    assert findings == []


def test_pp5_two_operations_same_task_list_get_distinct_record_keys():
    df = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01", "BOKOKC01"], "TLGRPCOUNT": ["10", "10"],
            "TLOPNO": ["10", "20"], "TLSUBOPNO": ["0", "0"],
            "WORK": [None, None], "WORK_UNIT": [None, None],
            "PERSON": [None, None], "DURATION": [None, None], "DURATION_UNIT": [None, None],
            "OPWKCEN": ["BMECH", "BELEC"],
        }
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR")
    record_keys = {f.record_key for f in findings}
    assert record_keys == {"BOKOKC01-10-10-0", "BOKOKC01-10-20-0"}


def test_pp5_std_unit_row_consults_agent_but_result_stays_null_confidence_zero():
    # Deep Agent actually invoked on the unit-scope-excluded branch, but
    # its answer never overrides the deterministic NULL/0 result — §5 PP5
    # already established OREDA is not usable for this pain point.
    class _FakeMessage:
        content = "applicable=False; no HVAC taxonomy, corrective not preventive"

    class _FakeAgent:
        def invoke(self, _payload):
            return {"messages": [_FakeMessage()]}

    df = pl.DataFrame(
        {
            "TLGRP": ["BOKOKC01"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [0.0], "WORK_UNIT": ["STD"],
            "PERSON": [2], "DURATION": [2.0], "DURATION_UNIT": ["HR"], "OPWKCEN": ["BMECH"],
        }
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR", agent_c=_FakeAgent())
    assert len(findings) == 1
    assert findings[0].recommended_value is None
    assert findings[0].confidence == 0
    assert "Deep Agent" in findings[0].evidence_source
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: the 7 new tests FAIL — `ImportError: cannot import name 'run_pp5'`. Prior 21 tests still pass.

- [ ] **Step 3: Append to `validation.py`**

```python
from evidence_connectors.pitstops_connector import flag_implausible_work


def _ask_agent_oreda_worth_checking(agent_c) -> str:
    # Returns the agent's freeform answer, or "" on any failure/absence —
    # this call NEVER changes the deterministic NULL/0 result for a
    # unit-scope-excluded row (§5 PP5 already establishes OREDA is not
    # usable for this pain point, verified by oreda_connector.py itself);
    # it only makes the agent's evidence-selection role real for the one
    # case where a genuine "which source should I check" choice exists —
    # a unit-scope-excluded row where a human reviewer might otherwise
    # wonder whether OREDA was even considered.
    if agent_c is None:
        return ""
    try:
        result = agent_c.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "A Bokor Long Text operation's WORK/DURATION units fall outside "
                            "the MHR/HR scope the standard formula applies to. Before this is "
                            "reported as insufficient evidence, use the check_oreda_applicability "
                            "tool to confirm whether OREDA offers any usable signal here."
                        ),
                    }
                ]
            }
        )
        return result["messages"][-1].content.strip()
    except Exception:
        return ""


def run_pp5(
    normalized_operations: pl.DataFrame,
    valid_work_unit: str,
    valid_duration_unit: str,
    pitstops_ranges: pl.DataFrame | None = None,
    work_tolerance: float = 0.01,
    agent_c=None,
) -> list[Finding]:
    findings: list[Finding] = []

    for row in normalized_operations.iter_rows(named=True):
        # Full logical operation key (§5.0) — TLGRP+TLGRPCOUNT alone would
        # collide two different operations under the same Task List onto
        # one record_key.
        record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}-{row['TLSUBOPNO']}"

        # 1. COMPLETENESS
        if row["WORK"] is None or row["PERSON"] is None or row["DURATION"] is None:
            findings.append(
                Finding(
                    pain_point="PP5", record_key=record_key, field_name="WORK",
                    current_value=str(row["WORK"]), recommended_value=None, confidence=0,
                    evidence_source="Bokor Long Text_Aug26_LATEST.xlsm; UDMS.pdf §9.20-21",
                )
            )
            continue

        # 2. UNIT CHECK — formula only valid for valid_work_unit/valid_duration_unit.
        # This is PP5's genuine within-step evidence-selection point (§11.1):
        # before reporting insufficient evidence, ask the Deep Agent to
        # confirm OREDA's applicability via its tool — the deterministic
        # result never changes (§5 PP5's own connector re-verifies "not
        # usable" independently every run), but the agent's role is now
        # actually exercised here, not merely defined and left unused.
        if row["WORK_UNIT"] != valid_work_unit or row["DURATION_UNIT"] != valid_duration_unit:
            agent_note = _ask_agent_oreda_worth_checking(agent_c)
            evidence_source = "Bokor Long Text_Aug26_LATEST.xlsm; UDMS.pdf §9.20-21"
            if agent_note:
                evidence_source += " + Deep Agent OREDA-applicability check"
            findings.append(
                Finding(
                    pain_point="PP5", record_key=record_key, field_name="WORK",
                    current_value=str(row["WORK"]), recommended_value=None, confidence=0,
                    evidence_source=evidence_source,
                )
            )
            continue

        # 3. VALIDITY — WORK = PERSON x DURATION, within MHR/HR scope only.
        # Numeric tolerance, not exact float equality — 2 * 2.0000000001
        # is "equal" to 4.0 for this purpose.
        computed_work = row["PERSON"] * row["DURATION"]
        if abs(row["WORK"] - computed_work) > work_tolerance:
            range_flag = None
            if pitstops_ranges is not None:
                range_flag = flag_implausible_work(computed_work, row["OPWKCEN"], pitstops_ranges)
            findings.append(
                Finding(
                    pain_point="PP5", record_key=record_key, field_name="WORK",
                    current_value=str(row["WORK"]), recommended_value=str(computed_work),
                    confidence=100,
                    detection_confidence=90 if range_flag == "SUSPICIOUS" else None,
                    evidence_source="Bokor Long Text_Aug26_LATEST.xlsm (PERSON x DURATION); UDMS.pdf §9.20-21",
                )
            )
        # 4. CONSISTENCY — WORK already equals PERSON x DURATION (within
        # tolerance): PASS, no finding

    return findings
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: 28 passed.

- [ ] **Step 5: Commit manually**

Commit `validation.py`, `tests/test_validation.py` — message like `feat: PP5 man-hour check, unit-scoped, full operation key, numeric tolerance, PITSTOPS plausibility flag wired in`.

---

## Task 10: `validation.py` — PP6 and PP7

**Files:**
- Modify: `Agent_C_TaskList_MPlan/validation.py` (append `run_pp6`, `run_pp7`)
- Modify: `Agent_C_TaskList_MPlan/tests/test_validation.py` (append tests)

**Interfaces:**
- Produces:
  - `run_pp6(task_list_group: pl.DataFrame, normalized_operations: pl.DataFrame, agent_a_equipment: pl.DataFrame) -> list[Finding]` — `task_list_group` needs `Maintenance Item, Equipment, Maintenance Strategy, Group, Group Counter`; `normalized_operations` needs `TLGRP, TLGRPCOUNT, STRATEGY`; `agent_a_equipment` needs `Equipment, System status, User Status`. **Corrected from the earlier draft in two ways:** (1) the no-Plan coverage-gap check now excludes equipment whose `User Status` carries an `RTOF` flag — per `PTG 12.05.04 - PMMS.pdf`'s equipment Plan-status codes (`PLAN`/`Pnnn`/`RTOF`, §4c) and `IVA_PMMS Training Pack_2026.pdf` p.13's "every active equipment needs an active Plan **or** RTOF" rule, RTOF equipment legitimately has no Plan by design — flagging it as a coverage gap would be a false positive; (2) both sides of the Equipment join are explicitly cast to string before comparison — §4a of the architecture doc verified a real int/string type mismatch on Equipment IDs between the FLOC/Equipment files and the bridge file (the join only reached 99.9% match after casting both sides to string in that survey), and the earlier draft's `set(task_list_group["Equipment"])` comparison would silently under-match the same way if Polars ever infers an int dtype for either side's Equipment column.
  - `run_pp7(task_list_group: pl.DataFrame) -> list[Finding]` — needs `Maintenance Item, Maintenance Plan`. **Corrected from the earlier draft:** §7's output schema is one row per actual finding, not a full dump of every bridge row — a Maintenance Item with a populated `Maintenance Plan` is not a finding and is no longer emitted at all (the previous draft emitted a `Confidence=100` "finding" for every correct row, which is not what `Findings_Report.xlsx` is for). Only Items with a blank `Maintenance Plan` produce a `Finding` (`Recommended_Value=None, Confidence=0`, per §5 PP7 — no independent Maintenance Item population is in scope to supply a replacement).

- [ ] **Step 1: Append the failing tests to `tests/test_validation.py`**

```python
from validation import run_pp6, run_pp7


def test_pp6_strategy_mismatch_detected_no_recommended_value():
    task_list_group = pl.DataFrame(
        {
            "Maintenance Item": ["978469"], "Equipment": ["10012345"],
            "Maintenance Strategy": ["PCSB52"], "Group": ["BOKOKC01"], "Group Counter": ["10"],
        }
    )
    normalized_operations = pl.DataFrame(
        {"TLGRP": ["BOKOKC01"], "TLGRPCOUNT": ["10"], "STRATEGY": ["PCSB99"]}
    )
    agent_a_equipment = pl.DataFrame(
        {"Equipment": ["10012345"], "System status": ["INST"], "User Status": ["ACT BOM PLAN"]}
    )
    findings = run_pp6(task_list_group, normalized_operations, agent_a_equipment)
    mismatch = [f for f in findings if f.detection_confidence == 95]
    assert len(mismatch) == 1
    assert mismatch[0].recommended_value is None
    assert mismatch[0].confidence == 0


def test_pp6_active_equipment_no_plan_coverage_gap():
    task_list_group = pl.DataFrame(
        {"Maintenance Item": [], "Equipment": [], "Maintenance Strategy": [], "Group": [], "Group Counter": []}
    )
    normalized_operations = pl.DataFrame({"TLGRP": [], "TLGRPCOUNT": [], "STRATEGY": []})
    agent_a_equipment = pl.DataFrame(
        {"Equipment": ["99999999"], "System status": ["INST"], "User Status": ["ACT BOM PLAN"]}
    )
    findings = run_pp6(task_list_group, normalized_operations, agent_a_equipment)
    gap = [f for f in findings if f.detection_confidence == 85]
    assert len(gap) == 1
    assert gap[0].recommended_value is None
    assert gap[0].confidence == 0


def test_pp6_rtof_equipment_excluded_from_coverage_gap():
    # RTOF equipment legitimately has no Plan by design (PTG 12.05.04;
    # IVA_PMMS Training Pack p.13: "active equipment needs an active Plan
    # OR RTOF") — must not be flagged as a coverage gap.
    task_list_group = pl.DataFrame(
        {"Maintenance Item": [], "Equipment": [], "Maintenance Strategy": [], "Group": [], "Group Counter": []}
    )
    normalized_operations = pl.DataFrame({"TLGRP": [], "TLGRPCOUNT": [], "STRATEGY": []})
    agent_a_equipment = pl.DataFrame(
        {"Equipment": ["99999999"], "System status": ["INST"], "User Status": ["ACT RTOF"]}
    )
    findings = run_pp6(task_list_group, normalized_operations, agent_a_equipment)
    gap = [f for f in findings if f.detection_confidence == 85]
    assert gap == []


def test_pp6_equipment_join_normalizes_int_vs_string_mismatch():
    # §4a verified directly: a real int/string type mismatch exists on
    # Equipment IDs between the bridge file and the FLOC/Equipment files
    # (99.9% match only after casting both sides to string). Simulate the
    # bridge file holding an int-typed Equipment column (as Polars can
    # infer from an all-numeric-looking Excel column) against a
    # string-typed Equipment column in Agent A's output — the join must
    # still recognize these as the same equipment.
    task_list_group = pl.DataFrame(
        {
            "Maintenance Item": ["978469"], "Equipment": [10012345], "Maintenance Strategy": ["PCSB52"],
            "Group": ["BOKOKC01"], "Group Counter": ["10"],
        }
    )
    normalized_operations = pl.DataFrame({"TLGRP": [], "TLGRPCOUNT": [], "STRATEGY": []})
    agent_a_equipment = pl.DataFrame(
        {"Equipment": ["10012345"], "System status": ["INST"], "User Status": ["ACT BOM PLAN"]}
    )
    findings = run_pp6(task_list_group, normalized_operations, agent_a_equipment)
    gap = [f for f in findings if f.detection_confidence == 85]
    # Without string normalization, "10012345" (str) != 10012345 (int)
    # would wrongly treat this Equipment as uncovered and flag a gap.
    assert gap == []


def test_pp7_populated_plan_is_not_a_finding():
    # §7 — Findings_Report is one row per actual finding, not a dump of
    # every correctly-assigned row.
    df = pl.DataFrame({"Maintenance Item": ["978469"], "Maintenance Plan": ["50114592"]})
    findings = run_pp7(df)
    assert findings == []


def test_pp7_blank_plan_null_confidence_zero():
    df = pl.DataFrame({"Maintenance Item": ["978470"], "Maintenance Plan": [None]})
    findings = run_pp7(df)
    assert len(findings) == 1
    assert findings[0].recommended_value is None
    assert findings[0].confidence == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: the 6 new tests FAIL — `ImportError: cannot import name 'run_pp6'`. Prior 28 tests still pass.

- [ ] **Step 3: Append to `validation.py`**

```python
def run_pp6(
    task_list_group: pl.DataFrame,
    normalized_operations: pl.DataFrame,
    agent_a_equipment: pl.DataFrame,
) -> list[Finding]:
    findings: list[Finding] = []

    # Check A — Strategy consistency: Task List STRATEGY must match the
    # Item's Maintenance Strategy (UDMS §9.12/§11.2).
    op_strategy_lookup = {
        (row["TLGRP"], row["TLGRPCOUNT"]): row["STRATEGY"]
        for row in normalized_operations.iter_rows(named=True)
    }
    for row in task_list_group.iter_rows(named=True):
        op_strategy = op_strategy_lookup.get((row["Group"], row["Group Counter"]))
        if op_strategy is not None and op_strategy != row["Maintenance Strategy"]:
            findings.append(
                Finding(
                    pain_point="PP6",
                    record_key=row["Maintenance Item"],
                    field_name="Maintenance Strategy",
                    current_value=row["Maintenance Strategy"],
                    recommended_value=None,
                    confidence=0,
                    detection_confidence=95,
                    evidence_source="Bokor Task List Group.xlsx; Bokor Long Text_Aug26_LATEST.xlsm; UDMS.pdf §9.12, §11.2",
                )
            )

    # Check B — Equipment coverage, combined System+User status
    # (System status=INST alone is not "active"; User Status must carry
    # ACT). RTOF equipment is excluded — per PTG 12.05.04's Plan-status
    # codes and IVA_PMMS Training Pack p.13 ("active equipment needs an
    # active Plan OR RTOF"), RTOF equipment legitimately has no Plan.
    # Corrected: both sides are cast to string before the join/lookup —
    # §4a of the architecture doc confirms a real int/string mismatch on
    # Equipment IDs between the FLOC/Equipment files and the bridge file
    # (verified directly: the join only reaches 99.9% match after casting
    # both sides to string). Comparing without this cast would silently
    # under-match here exactly as it did in the original survey.
    covered_equipment = {str(e) for e in task_list_group["Equipment"]}
    for row in agent_a_equipment.iter_rows(named=True):
        equipment_id = str(row["Equipment"])
        user_status = row["User Status"] or ""
        is_active = row["System status"] == "INST" and "ACT" in user_status and "INAC" not in user_status
        has_rtof = "RTOF" in user_status
        if is_active and not has_rtof and equipment_id not in covered_equipment:
            findings.append(
                Finding(
                    pain_point="PP6",
                    record_key=equipment_id,
                    field_name="Maintenance Plan",
                    current_value=None,
                    recommended_value=None,
                    confidence=0,
                    detection_confidence=85,
                    evidence_source="Equipment_Validated.xlsx (agent_a); Bokor Task List Group.xlsx; IVA_PMMS Training Pack_2026.pdf p.13; PTG 12.05.04 - PMMS.pdf",
                )
            )

    return findings


def run_pp7(task_list_group: pl.DataFrame) -> list[Finding]:
    # §7 — one row per actual finding. A populated Maintenance Plan is a
    # correct, unremarkable row and is never emitted here; only the
    # blank-Plan case is a finding, per §5 PP7.
    findings: list[Finding] = []
    for row in task_list_group.iter_rows(named=True):
        if row["Maintenance Plan"] is None:
            findings.append(
                Finding(
                    pain_point="PP7",
                    record_key=row["Maintenance Item"],
                    field_name="Maintenance Plan",
                    current_value=None,
                    recommended_value=None,
                    confidence=0,
                    evidence_source="Bokor Task List Group.xlsx; UDMS.pdf §10",
                )
            )
    return findings
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: 34 passed.

- [ ] **Step 5: Commit manually**

Commit `validation.py`, `tests/test_validation.py` — message like `feat: PP6 strategy-mismatch/coverage-gap (RTOF-excluded, string-normalized Equipment join) + PP7 blank-plan-only findings`.

---

## Task 11: `output_writer.py`

**Files:**
- Create: `Agent_C_TaskList_MPlan/output_writer.py`
- Modify: `Agent_C_TaskList_MPlan/tests/test_validation.py` (append output-writer tests — kept in this file rather than a fourth test file, since `output_writer.py` consumes `Finding` directly)

**Interfaces:**
- Produces:
  - `write_findings_report(findings: list[Finding], output_path: str) -> None` — writes the §7 core schema (`Pain_Point, Record_Key, Field_Name, Current_Value, Recommended_Value, Confidence, Detection_Confidence, Evidence_Source`) as one row per finding.
  - `write_annotated_task_list_group(source_path: str, findings: list[Finding], output_path: str) -> None` — takes the **source `.xlsx` file path**, not a `pl.DataFrame`. Original columns + a `Findings` column (semicolon-joined `Field_Name=Recommended_Value(Confidence)`), keyed by `Maintenance Item`. **Corrected from the earlier draft:** writes with `openpyxl` (loading the copied `input/Bokor Task List Group.xlsx` as the base workbook and appending the `Findings` column to its existing sheet), not `pl.DataFrame.write_excel` — Polars' Excel writer creates a brand-new workbook and cannot preserve an existing file's formatting.
  - `write_annotated_long_text(source_path: str, findings: list[Finding], output_path: str) -> None` — **corrected from the earlier draft:** takes the **source `.xlsm` file path**, not a `pl.DataFrame`, and uses `openpyxl.load_workbook(path, keep_vba=True)` to open it, appends the `Findings` column (keyed by `TLGRP+TLGRPCOUNT`) to the existing `Bokor Long Text Rev2` sheet, and saves with `openpyxl`'s writer — this is required to preserve the `.xlsm`'s macros/VBA project and existing formatting, which `pl.DataFrame.write_excel` cannot do (Polars has no `.xlsm`/VBA-preserving writer; writing an `.xlsm`-named file via Polars produces a plain `.xlsx` payload with a misleading extension, not a real macro-enabled workbook).
  - `write_annotated_mplan(source_path: str, findings: list[Finding], output_path: str, sheet_name: str, maintenance_plan_column: int) -> None` — takes the **source `.xlsx` file path**, not a `pl.DataFrame` (`maintenance_plan_column` is the 1-indexed openpyxl column number for `maintenance_plan`, which is column 5 for the real `MPLAN BOKOR AUG26.xlsx` layout — see `MPLAN_COLUMN_NAMES` in Task 12). Same `Findings`-column pattern, via `openpyxl` for consistency with the other two writers (this file has no macros to preserve, but using one writer library throughout keeps the module simple).

- [ ] **Step 1: Append the failing tests to `tests/test_validation.py`**

```python
from output_writer import write_annotated_task_list_group, write_findings_report


def test_write_findings_report_produces_expected_columns(tmp_path):
    findings = [
        Finding(
            pain_point="PP1", record_key="MYVES$$2", field_name="Group",
            current_value="MYVES$$2", recommended_value=None, confidence=0,
            detection_confidence=90, evidence_source="Bokor Task List Group.xlsx",
        )
    ]
    output_path = tmp_path / "Findings_Report.xlsx"
    write_findings_report(findings, str(output_path))
    result = pl.read_excel(str(output_path))
    assert result.columns == [
        "Pain_Point", "Record_Key", "Field_Name", "Current_Value",
        "Recommended_Value", "Confidence", "Detection_Confidence", "Evidence_Source",
    ]
    assert result["Recommended_Value"][0] is None
    assert result["Confidence"][0] == 0


def test_write_annotated_task_list_group_appends_findings_column(tmp_path):
    import openpyxl

    source_path = tmp_path / "Bokor Task List Group.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(("Maintenance Item", "Group"))
    ws.append(("978469", "BOKOKC01"))
    wb.save(source_path)

    findings = [
        Finding(
            pain_point="PP2", record_key="978469", field_name="Main Work Center",
            current_value="BMULTI", recommended_value="BMECH", confidence=95,
            evidence_source="Bokor Task List Group.xlsx",
        )
    ]
    output_path = tmp_path / "annotated.xlsx"
    write_annotated_task_list_group(str(source_path), findings, str(output_path))

    result_wb = openpyxl.load_workbook(str(output_path))
    result_ws = result_wb["Data"]
    header = [c.value for c in result_ws[1]]
    assert "Findings" in header
    findings_col = header.index("Findings") + 1
    assert "Main Work Center=BMECH(95)" in result_ws.cell(row=2, column=findings_col).value


def test_write_annotated_long_text_preserves_xlsm_and_vba(tmp_path):
    import openpyxl

    source_path = tmp_path / "Bokor Long Text_Aug26_LATEST.xlsm"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Bokor Long Text Rev2"
    ws.append(("TLGRP", "TLGRPCOUNT"))
    ws.append(("BOKOKC01", "10"))
    wb.save(source_path)

    findings = [
        Finding(
            pain_point="PP5", record_key="BOKOKC01-10-10-0", field_name="WORK",
            current_value="0.0", recommended_value="4.0", confidence=100,
            evidence_source="Bokor Long Text_Aug26_LATEST.xlsm",
        )
    ]
    output_path = tmp_path / "annotated.xlsm"
    write_annotated_long_text(str(source_path), findings, str(output_path))

    assert output_path.exists()
    result_wb = openpyxl.load_workbook(str(output_path), keep_vba=True)
    result_ws = result_wb["Bokor Long Text Rev2"]
    header = [c.value for c in result_ws[1]]
    assert "Findings" in header
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: the 3 new tests FAIL — `ModuleNotFoundError` for `output_writer`. Prior 34 tests still pass.

- [ ] **Step 3: Write `output_writer.py`**

**This is the corrected version** — the earlier draft used `pl.DataFrame.write_excel` for the annotated `.xlsm`/`.xlsx` outputs, which creates a brand-new workbook and cannot preserve an existing file's formatting or, for the `.xlsm` case, its VBA project. Polars has no `.xlsm`/macro-preserving writer at all — writing a file named `.xlsm` via `write_excel` produces a plain `.xlsx` payload under a misleading extension, not a real macro-enabled workbook. This version opens the real source file with `openpyxl` (`keep_vba=True` for the `.xlsm`), appends a `Findings` column to the existing sheet in place, and saves through `openpyxl` so formatting and macros survive.

```python
import openpyxl

from validation import Finding

FINDINGS_REPORT_COLUMNS = [
    "Pain_Point", "Record_Key", "Field_Name", "Current_Value",
    "Recommended_Value", "Confidence", "Detection_Confidence", "Evidence_Source",
]


def write_findings_report(findings: list[Finding], output_path: str) -> None:
    # A brand-new file every run — no source workbook to preserve, so the
    # plain openpyxl Workbook API is enough here.
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Findings"
    ws.append(FINDINGS_REPORT_COLUMNS)
    for f in findings:
        ws.append(
            [
                f.pain_point, f.record_key, f.field_name, f.current_value,
                f.recommended_value, f.confidence, f.detection_confidence, f.evidence_source,
            ]
        )
    wb.save(output_path)


def _findings_by_key(findings: list[Finding]) -> dict[str, list[Finding]]:
    by_key: dict[str, list[Finding]] = {}
    for f in findings:
        by_key.setdefault(f.record_key, []).append(f)
    return by_key


def _findings_summary(matching: list[Finding]) -> str:
    return "; ".join(f"{f.field_name}={f.recommended_value}({f.confidence})" for f in matching)


def _append_findings_column(source_path: str, output_path: str, sheet_name: str, keys: list[str], findings: list[Finding], keep_vba: bool) -> None:
    wb = openpyxl.load_workbook(source_path, keep_vba=keep_vba)
    ws = wb[sheet_name]
    by_key = _findings_by_key(findings)
    findings_col = ws.max_column + 1
    ws.cell(row=1, column=findings_col, value="Findings")
    for row_idx, key in enumerate(keys, start=2):
        ws.cell(row=row_idx, column=findings_col, value=_findings_summary(by_key.get(key, [])))
    wb.save(output_path)


def write_annotated_task_list_group(source_path: str, findings: list[Finding], output_path: str) -> None:
    wb = openpyxl.load_workbook(source_path)
    ws = wb["Data"]
    header = [c.value for c in ws[1]]
    item_col = header.index("Maintenance Item") + 1
    keys = [ws.cell(row=r, column=item_col).value for r in range(2, ws.max_row + 1)]
    wb.close()
    _append_findings_column(source_path, output_path, "Data", keys, findings, keep_vba=False)


def write_annotated_long_text(source_path: str, findings: list[Finding], output_path: str) -> None:
    # Corrected: uses the FULL logical operation key (TLGRP+TLGRPCOUNT+
    # TLOPNO+TLSUBOPNO), matching PP5's record_key exactly (§5.0). The
    # earlier version keyed only on TLGRP+TLGRPCOUNT, which collides two
    # different operations under the same Task List onto one key — PP5's
    # operation-level findings would silently fail to map back onto the
    # correct row (or map onto the wrong one) in the annotated output.
    wb = openpyxl.load_workbook(source_path, keep_vba=True)
    ws = wb["Bokor Long Text Rev2"]
    header = [c.value for c in ws[1]]
    grp_col = header.index("TLGRP") + 1
    count_col = header.index("TLGRPCOUNT") + 1
    opno_col = header.index("TLOPNO") + 1
    subopno_col = header.index("TLSUBOPNO") + 1
    keys = [
        f"{ws.cell(row=r, column=grp_col).value}-{ws.cell(row=r, column=count_col).value}"
        f"-{ws.cell(row=r, column=opno_col).value}-{ws.cell(row=r, column=subopno_col).value}"
        for r in range(2, ws.max_row + 1)
    ]
    wb.close()
    _append_findings_column(source_path, output_path, "Bokor Long Text Rev2", keys, findings, keep_vba=True)


def write_annotated_mplan(source_path: str, findings: list[Finding], output_path: str, sheet_name: str, maintenance_plan_column: int) -> None:
    wb = openpyxl.load_workbook(source_path)
    ws = wb[sheet_name]
    keys = [ws.cell(row=r, column=maintenance_plan_column).value for r in range(3, ws.max_row + 1)]
    wb.close()
    _append_findings_column(source_path, output_path, sheet_name, keys, findings, keep_vba=False)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: 37 passed.

- [ ] **Step 5: Commit manually**

Commit `output_writer.py`, `tests/test_validation.py` — message like `feat: output writer, openpyxl-based, full operation key for Long Text annotation`.

---

## Task 12: `app.py` — Single Runtime Entry Point (Config, Ingest, LLM Provider, Orchestration)

**Files:**
- Create: `Agent_C_TaskList_MPlan/app.py`
- Create: `Agent_C_TaskList_MPlan/system_prompt.md`
- Modify: `Agent_C_TaskList_MPlan/tests/test_validation.py` (append the end-to-end pipeline test — kept here rather than a dedicated `test_app.py`, per the simplified test-file count)

**Interfaces:**
- Produces:
  - `load_settings() -> dict` — reads the 4 YAML files under `config/` plus `.env`, returns a plain dict with keys `platform_codes`, `work_centre_families`, `multi_work_centre_variants`, `unit_rules`, `thresholds`, `llm_provider`.
  - `get_chat_model(llm_provider: str)` — the one place LLM provider selection happens: returns `langchain_openai.AzureChatOpenAI` for `"azure_openai"`, `langchain_anthropic.ChatAnthropic` (Azure Foundry-configured) for `"azure_foundry_claude"`, raises `ValueError` otherwise. Only ever called from `__main__`, never from `run_pipeline` directly — see below.
  - `build_agent_c(chat_model)` — calls `deepagents.create_deep_agent(tools=[...], instructions=Path("system_prompt.md").read_text(), model=chat_model)`, returning the built agent.
  - `read_task_list_group`, `read_agent_a_floc`, `read_agent_a_equipment` — unchanged, standard single-header-row reads.
  - `read_long_text(path: str) -> pl.DataFrame` — reads with `has_header=False` and assigns all 25 real column names positionally, renaming the two `UNIT` slots to `WORK_UNIT`/`DURATION_UNIT` by position.
  - `read_mplan_bokor(path: str) -> pl.DataFrame` — the real file has 25 physical columns (verified directly). Reads with `has_header=False`, assigns all 25 names positionally, then selects only the columns `run_pipeline` needs.
  - `run_pipeline(input_dir: str, output_dir: str, agent_c=None) -> list[Finding]` — **corrected in three ways from the earlier draft:**
    1. **`agent_c` is now an optional, injectable parameter** rather than something `run_pipeline` always builds itself from live credentials. When `agent_c is None` (the default — and what every unit test passes), `run_pp4` and `run_pp5` run in their fully deterministic fallback mode (see Tasks 8–9's `agent_c=None` default); when a real agent is supplied (only ever from `__main__`, via `get_chat_model` + `build_agent_c`), PP4's semantic review and PP5's evidence-connector coordination actually invoke it. This is what makes `python app.py`'s test suite runnable with zero Azure credentials while still making the Deep Agent load-bearing in production — the earlier draft called `get_chat_model`/`build_agent_c` unconditionally inside `run_pipeline`, which meant the synthetic end-to-end test (Task 12's own test, and any test that imports `app` at all) would fail or hang without real `.env` credentials.
    2. **Schema-validates all 5 input sources**, not just Agent A's two — `validate_task_list_group_schema`, `validate_long_text_schema`, and `validate_mplan_schema` (Task 4) now run against the 3 primary files immediately after ingest, before any pain-point logic, alongside the existing `validate_floc_schema`/`validate_equipment_schema` calls.
    3. **Passes threshold values from `settings["thresholds"]`** into every `run_ppN` call that has a corresponding config entry (§9's numeric bands, Task 1 Step 8), rather than relying on each function's Python-level hardcoded default — `run_pp1`'s reuse threshold, `run_pp2`'s `valid_work_unit`, `run_pp4`'s `text_similarity_threshold`, `run_pp5`'s `work_tolerance` are all now driven by `config/thresholds.yaml`, not a second hardcoded copy of the same number.
    The pipeline itself: schema-validate all 5 sources → ingest 3 primary files → normalize (§5.0), including building `known_tlgrps` from the normalized Long Text before parsing MPLAN's Task List key → load PITSTOPS ranges → for each of PP1 through PP7, **in that fixed order**, invoke `run_ppN` (passing `agent_c` to PP4/PP5) → validate every finding through `Finding`'s Pydantic gate → write output via `output_writer`'s file-path-based, `openpyxl`-preserving writers.
  - `if __name__ == "__main__":` block that builds the real chat model + Deep Agent from live credentials and calls `run_pipeline("input", "output", agent_c=agent_c)` — this is the **only** place in the whole codebase that requires real Azure credentials to exist, so `python app.py` alone still runs the fully agent-integrated pipeline in production exactly as before, while every test stays credential-free.

- [ ] **Step 1: Write `system_prompt.md`**

```markdown
# Agent C — Task List & Maintenance Plan Validation Agent

You coordinate evidence gathering for 7 SAP Plant Maintenance data-quality
pain points (PP1-PP7). You decide WHICH evidence source or tool to consult
within a given pain point, and WHETHER enough evidence exists to support a
recommendation. You never compute a SAP value, apply a formula, or invent a
threshold yourself — every calculation happens in the deterministic Python
functions in validation.py. When evidence is insufficient, the correct
action is to report Recommended_Value=None, Confidence=0 — never to fill
the gap from your own general knowledge.

Ground truth for each pain point lives in ground_truth_cache/PP0N_*.md — each
file holds only that pain point's own cited excerpt, not a whole document.
If a cached file disagrees with its cited source document, the source
document wins — flag the discrepancy rather than trusting the cache.

You do not decide the order pain points run in — app.py already runs PP1
through PP7 in a fixed order, and normalize.py has already run. Your job
within each pain point is narrower: pick tools, gather evidence, and hand
back a verdict — never re-sequence the pipeline.

For PP4 specifically: when given a candidate pair of Task Lists that the
deterministic text-similarity check already flagged, assess whether their
Object Description / OPDESC / LONGTEXT content genuinely describes the same
maintenance task (not just similar wording). Your assessment can raise or
lower the confidence that this is a real duplicate — it can NEVER decide
which of the two Task Lists is the one to keep. No evidence source available
to you establishes retention precedence; report both as a pair for human
review, never invent an authoritative answer.
```

- [ ] **Step 2: Append the failing end-to-end test to `tests/test_validation.py`**

```python
import openpyxl as _openpyxl

from app import run_pipeline


def _write_xlsx_sheet(path, sheet_name, rows):
    wb = _openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    for row in rows:
        ws.append(row)
    wb.save(path)


def test_run_pipeline_end_to_end_produces_output_files(tmp_path):
    input_dir = tmp_path / "input"
    (input_dir / "agent_a").mkdir(parents=True)
    (input_dir / "pitstops").mkdir()
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    _write_xlsx_sheet(
        input_dir / "Bokor Task List Group.xlsx", "Data",
        [
            (
                "Planning Plant", "Maintenance Plan", "Maintenance Item", "Maint. item text",
                "Functional Location", "FunctLocDescrip.", "Equipment", "Object Description",
                "Order Type", "Maintenance Strategy", "ABC Indicator", "Group", "Group Counter",
                "Maint. Planner Group", "Main Work Center", "Changed On", "Changed By",
                "Created On", "Created By", "Location",
            ),
            (
                "M014", "50114592", "978469", "Heat exchanger inspection", "BWI-001", "Bokor",
                "10012345", "Heat exchanger", "PM01", "PCSB52", "1", "BOKOKC01", "10", "BOS",
                "BMECH", "2026-01-01", "user1", "2020-01-01", "user2", "BOKOR",
            ),
        ],
    )
    _write_xlsx_sheet(
        input_dir / "Bokor Long Text_Aug26_LATEST.xlsm", "Bokor Long Text Rev2",
        [
            (
                "PLANT", "STRATEGY", "TLTYPE", "TLGRP", "TLGRPCOUNT", "TLOPNO", "TLSUBOPNO",
                "TLNODE", "TLCOUNT", "CTRLKEY", "OPWKCEN", "OPDESC", "WORK", "UNIT", "PERSON",
                "DURATION", "UNIT", "ACTTYPE", "SUIT", "FREQUENCY", "CA10TXT", "SO10TXT",
                "TEXTTITLE", "FORMAT", "LONGTEXT",
            ),
            (
                "M014", "PCSB52", "A", "BOKOKC01", "10", "10", "0", "", "", "INTN", "BMECH",
                "PM,3M-VISUAL", 4.0, "MHR", 2, 2.0, "HR", "", "", "3M", "", "", "", "", "inspect",
            ),
        ],
    )
    mplan_row1 = ("",) * 18 + ("No of Equipment", "Equipment with PLAN Status Set", "Equipment with RTOF Status", "Equipment with MPLAN defined", "MPLAN Completion %", "% of Equipment with PLAN status", "Equipment with MPLAN (incl. RTOF & w/o PLAN status)")
    mplan_row2 = ("PM planning plant", "", "Maintenance Plant", "", "Maintenance Plan", "", "Task List", "", "Plant", "", "Location", "", "PM planner group", "", "Main Work Center", "", "ABC indicator", "", "", "", "", "", "%", "%", "")
    mplan_row3 = ("M014", "PCSB - Miri", "M014", "PCSB - Miri", "50114592", " BOKOR FIELD", "ABODA05820", "BWI, BOKOR FIELD", "M014", "PCSB - Miri", "BOKOR", "SKO-BOKOR COMPLEX", "BOS", "BOKOR/BETTY OPER S", "BMECH", "Bokor/Betty/Bakau/Laila Multi-Discp Grp", "1", "Criticality Class 1", 0, 0, 0, 95, "X", "X", 95)
    _write_xlsx_sheet(input_dir / "MPLAN BOKOR AUG26.xlsx", "Sheet1", [mplan_row1, mplan_row2, mplan_row3])

    _write_xlsx_sheet(
        input_dir / "agent_a" / "Functional_Location_Validated.xlsx", "Data",
        [
            ("Maintenance Plant", "Functional Location", "FunctLocDescrip.", "User Status", "Location", "System status", "Created On", "Main Work Center", "Inventory Number", "Superior FunctLoc.", "Changed On", "ABC Indicator"),
            ("M014", "BWI-001", "Bokor", "ACT", "BOKOR", "CRTE", "2020-01-01", "BMECH", "1", "BWI", "2026-01-01", "1"),
        ],
    )
    _write_xlsx_sheet(
        input_dir / "agent_a" / "Equipment_Validated.xlsx", "Data",
        [
            ("Equipment", "Object Description", "Functional Location", "FunctLocDescrip.", "Location", "Technical IdentNo.", "Catalog Profile", "ABC Indicator", "System status", "User Status", "Maint. Planner Group", "Main Work Center", "Created By", "Maintenance Plant", "Manuf. Serial Number", "ManufDrawingNumber", "Manufacturer", "ManufactPartNo.", "Material", "Material Description", "Model number", "Created On", "Inventory Number", "Plant"),
            ("10012345", "Heat exchanger", "BWI-001", "Bokor", "BOKOR", "TAG-1", "CAT1", "1", "INST", "ACT BOM PLAN", "BOS", "BMECH", "user1", "M014", "SN1", "DWG1", "MFR1", "PART1", "MAT1", "Material desc", "MODEL1", "2020-01-01", "1", "M014"),
        ],
    )

    findings = run_pipeline(str(input_dir), str(output_dir))

    assert len(findings) > 0
    assert (output_dir / "Findings_Report.xlsx").exists()
    assert (output_dir / "Bokor_Task_List_Group_annotated.xlsx").exists()
    assert (output_dir / "Bokor_Long_Text_annotated.xlsm").exists()
    assert (output_dir / "MPLAN_BOKOR_annotated.xlsx").exists()
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: the new test FAILs — `ModuleNotFoundError: No module named 'app'`. Prior 37 tests still pass.

- [ ] **Step 4: Write `app.py`**

**This is the corrected version, addressing every remaining item from review:** (1) `read_long_text` reads positionally with `has_header=False`; (2) `read_mplan_bokor` assigns all 25 real column names; (3) **`agent_c` is now an injectable parameter of `run_pipeline`, not something it always builds itself** — `run_pp4`/`run_pp5` actually receive and call it when present (Tasks 8–9), and `run_pipeline` no longer requires live Azure credentials to run at all; only `__main__` builds a real one; (4) the 3 primary files get the same `validate_schema` guards Agent A's input already had; (5) `run_pp1`/`run_pp2`/`run_pp4`/`run_pp5` now receive their numeric parameters from `settings["thresholds"]` (Task 1 Step 8's config), not a Python-level default silently duplicating the same number.

```python
from pathlib import Path

import polars as pl
import yaml
from dotenv import load_dotenv
import os

from evidence_connectors.pitstops_connector import discipline_duration_ranges, load_pitstops_tasklists
from output_writer import (
    write_annotated_long_text,
    write_annotated_mplan,
    write_annotated_task_list_group,
    write_findings_report,
)
from scripts.normalize import classify_mplan_rows, normalize_long_text, parse_mplan_task_list_key
from scripts.validate_schema import (
    validate_equipment_schema,
    validate_floc_schema,
    validate_long_text_schema,
    validate_mplan_schema,
    validate_task_list_group_schema,
)
from validation import Finding, run_pp1, run_pp2, run_pp3, run_pp4, run_pp5, run_pp6, run_pp7

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"

# All 25 real physical columns of MPLAN BOKOR AUG26.xlsx's Sheet1, verified
# directly by reading rows 1-3 with has_header=False. Indices 0-15 are 8
# paired value/description columns (index 16 = abc_indicator has no
# partner); index 17 is an unlabeled spacer present in both header rows;
# indices 18-24 are row 1's 7 real coverage-metric labels. Do not shorten
# this list — a shorter list caused the earlier draft's column-count bug.
MPLAN_COLUMN_NAMES = [
    "pm_planning_plant", "pm_planning_plant_desc",       # 0, 1
    "maintenance_plant", "maintenance_plant_desc",       # 2, 3
    "maintenance_plan", "maintenance_plan_desc",         # 4, 5
    "task_list", "task_list_desc",                       # 6, 7
    "plant", "plant_desc",                                # 8, 9
    "location", "location_desc",                          # 10, 11
    "pm_planner_group", "pm_planner_group_desc",          # 12, 13
    "main_work_center", "main_work_center_desc",          # 14, 15
    "abc_indicator",                                       # 16
    "spacer_17",                                           # 17
    "no_of_equipment",                                     # 18
    "equipment_with_plan_status",                          # 19
    "equipment_with_rtof_status",                          # 20
    "equipment_with_mplan_defined",                        # 21
    "mplan_completion_pct",                                # 22
    "pct_equipment_with_plan_status",                      # 23
    "equipment_with_mplan_incl_rtof",                      # 24
]


def load_settings() -> dict:
    load_dotenv(BASE_DIR / ".env")
    return {
        "platform_codes": yaml.safe_load((CONFIG_DIR / "platform_code_prefixes.yaml").read_text())["platform_codes"],
        "work_centre_families": yaml.safe_load((CONFIG_DIR / "work_centre_families.yaml").read_text())["planner_groups"],
        "multi_work_centre_variants": yaml.safe_load((CONFIG_DIR / "work_centre_families.yaml").read_text())["multi_work_centre_variants"],
        "unit_rules": yaml.safe_load((CONFIG_DIR / "unit_rules.yaml").read_text()),
        "thresholds": yaml.safe_load((CONFIG_DIR / "thresholds.yaml").read_text()),
        "llm_provider": os.environ.get("AGENT_C_LLM_PROVIDER", "azure_openai"),
    }


def get_chat_model(llm_provider: str):
    # Only ever called from __main__ (see the bottom of this file) — never
    # from run_pipeline directly, so importing app.py or calling
    # run_pipeline(agent_c=None) never requires Azure credentials to exist.
    if llm_provider == "azure_openai":
        from langchain_openai import AzureChatOpenAI

        return AzureChatOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY", ""),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT", ""),
            azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", ""),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
        )
    if llm_provider == "azure_foundry_claude":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            api_key=os.environ.get("AZURE_FOUNDRY_CLAUDE_API_KEY", ""),
            base_url=os.environ.get("AZURE_FOUNDRY_CLAUDE_ENDPOINT", ""),
            model=os.environ.get("AZURE_FOUNDRY_CLAUDE_DEPLOYMENT", ""),
        )
    raise ValueError(
        f"unknown llm_provider {llm_provider!r}; expected 'azure_openai' or 'azure_foundry_claude'"
    )


def build_agent_c(chat_model):
    # Actually calls create_deep_agent, and run_pipeline actually invokes
    # the result (via run_pp4/run_pp5, Tasks 8-9) — not merely built and
    # left unused. Tools give the agent read-only access to the per-PP
    # ground-truth cache and the evidence connectors; it never gets a tool
    # that lets it write a Finding directly — every Finding still comes
    # from a deterministic run_ppN call, gated by Pydantic.
    from deepagents import create_deep_agent

    ground_truth_dir = BASE_DIR / "ground_truth_cache"

    def read_ground_truth(pain_point_file: str) -> str:
        path = ground_truth_dir / pain_point_file
        if not path.exists():
            return f"No ground truth cache found at {pain_point_file}."
        return path.read_text()

    def check_oreda_applicability() -> str:
        from evidence_connectors.oreda_connector import is_oreda_applicable_to_pp5

        applicable, reason = is_oreda_applicable_to_pp5(str(BASE_DIR / "evidence_connectors" / "OREDA.db"))
        return f"applicable={applicable}; {reason}"

    tools = [read_ground_truth, check_oreda_applicability]
    system_prompt = (BASE_DIR / "system_prompt.md").read_text()
    return create_deep_agent(tools=tools, instructions=system_prompt, model=chat_model)


def read_task_list_group(path: str) -> pl.DataFrame:
    return pl.read_excel(path, sheet_name="Data")


def read_long_text(path: str) -> pl.DataFrame:
    # Read positionally — do not rely on Polars' header-name inference to
    # leave two columns both discoverable as literally "UNIT" after a
    # dedup pass; verified directly that both real UNIT columns are at
    # positions 13 and 15 (0-indexed).
    raw = pl.read_excel(path, sheet_name="Bokor Long Text Rev2", has_header=False)
    header_row = raw.row(0)
    data = raw[1:]
    column_names = list(header_row)
    unit_positions = [i for i, name in enumerate(column_names) if name == "UNIT"]
    if len(unit_positions) != 2:
        raise ValueError(
            f"expected exactly 2 columns named 'UNIT' at fixed positions "
            f"(WORK's unit, DURATION's unit), found {len(unit_positions)} in {column_names}"
        )
    work_unit_idx, duration_unit_idx = unit_positions
    column_names[work_unit_idx] = "WORK_UNIT"
    column_names[duration_unit_idx] = "DURATION_UNIT"
    data.columns = column_names
    return data


def read_mplan_bokor(path: str) -> pl.DataFrame:
    # 25 physical columns, verified directly — read positionally and
    # assign every real column name, not a truncated 16-name list.
    raw = pl.read_excel(path, sheet_name="Sheet1", has_header=False)
    data = raw[2:]  # data starts row 3 (0-indexed row 2); rows 0-1 are the merged header
    if data.shape[1] != len(MPLAN_COLUMN_NAMES):
        raise ValueError(
            f"expected {len(MPLAN_COLUMN_NAMES)} columns in MPLAN BOKOR AUG26.xlsx, "
            f"found {data.shape[1]} — the file's layout has changed, re-verify column positions"
        )
    data.columns = MPLAN_COLUMN_NAMES
    return data


def read_agent_a_floc(path: str) -> pl.DataFrame:
    return pl.read_excel(path, sheet_name="Data")


def read_agent_a_equipment(path: str) -> pl.DataFrame:
    return pl.read_excel(path, sheet_name="Data")


def run_pipeline(input_dir: str, output_dir: str, agent_c=None) -> list[Finding]:
    # agent_c defaults to None so this function never requires live Azure
    # credentials — only __main__ builds and passes a real one. Every
    # unit test (including this task's own end-to-end test) calls
    # run_pipeline with agent_c=None or a fake test double.
    settings = load_settings()
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    task_list_group_path = str(input_path / "Bokor Task List Group.xlsx")
    long_text_path = str(input_path / "Bokor Long Text_Aug26_LATEST.xlsm")
    mplan_path = str(input_path / "MPLAN BOKOR AUG26.xlsx")

    # STEP 1/2 — ingest 3 primary files + agent_a/ + pitstops/, then
    # schema-validate all 5 sources before any pain-point logic runs.
    task_list_group = read_task_list_group(task_list_group_path)
    long_text_raw = read_long_text(long_text_path)
    mplan_raw = read_mplan_bokor(mplan_path)
    validate_task_list_group_schema(task_list_group)
    validate_long_text_schema(long_text_raw)
    validate_mplan_schema(mplan_raw)

    agent_a_floc = read_agent_a_floc(str(input_path / "agent_a" / "Functional_Location_Validated.xlsx"))
    agent_a_equipment = read_agent_a_equipment(str(input_path / "agent_a" / "Equipment_Validated.xlsx"))
    validate_floc_schema(agent_a_floc)
    validate_equipment_schema(agent_a_equipment)

    pitstops_dir = input_path / "pitstops"
    pitstops_ranges = None
    if pitstops_dir.exists():
        pitstops_files = [str(p) for p in pitstops_dir.glob("*.xlsx")]
        if pitstops_files:
            pitstops_df = load_pitstops_tasklists(pitstops_files)
            pitstops_ranges = discipline_duration_ranges(pitstops_df)

    # STEP 3 — normalize (§5.0), always before pain-point logic
    normalized_operations = normalize_long_text(long_text_raw)
    known_tlgrps = set(normalized_operations["TLGRP"].to_list()) | set(task_list_group["Group"].to_list())
    mplan_with_key = parse_mplan_task_list_key(mplan_raw, known_tlgrps)
    mplan_detail_rows, _mplan_aggregate_rows = classify_mplan_rows(mplan_with_key)

    # STEP 4/5 — PP1 -> PP7 in fixed order (§11.2 — hardcoded here in
    # plain Python, never agent-discretionary). agent_c is passed to
    # run_pp4 and run_pp5, the two pain points with a genuine
    # within-step evidence/semantic choice (§11.1, §11.3); PP1/PP3/PP6/
    # PP7 are fully deterministic and never receive agent_c at all.
    # Every numeric parameter with a config.yaml entry is read from
    # settings["thresholds"], not a Python-level hardcoded default.
    findings: list[Finding] = []
    findings += run_pp1(
        task_list_group, settings["platform_codes"],
        reuse_threshold=settings["thresholds"]["pp1"]["reused_prefix_min_occurrences"],
    )
    findings += run_pp2(
        task_list_group, normalized_operations, settings["work_centre_families"],
        multi_variants=settings["multi_work_centre_variants"],
        valid_work_unit=settings["unit_rules"]["valid_work_unit"],
    )
    findings += run_pp3(normalized_operations, task_list_group, mplan_detail_rows)
    findings += run_pp4(
        normalized_operations, task_list_group,
        text_similarity_threshold=settings["thresholds"]["pp4"]["text_similarity_threshold"],
        agent_c=agent_c,
    )
    findings += run_pp5(
        normalized_operations,
        settings["unit_rules"]["valid_work_unit"],
        settings["unit_rules"]["valid_duration_unit"],
        pitstops_ranges,
        work_tolerance=settings["thresholds"]["pp5"]["work_tolerance"],
        agent_c=agent_c,
    )
    findings += run_pp6(task_list_group, normalized_operations, agent_a_equipment)
    findings += run_pp7(task_list_group)

    # STEP 6 — produce output (openpyxl-based writers, preserve .xlsm/VBA)
    write_findings_report(findings, str(output_path / "Findings_Report.xlsx"))
    write_annotated_task_list_group(task_list_group_path, findings, str(output_path / "Bokor_Task_List_Group_annotated.xlsx"))
    write_annotated_long_text(long_text_path, findings, str(output_path / "Bokor_Long_Text_annotated.xlsm"))
    write_annotated_mplan(
        mplan_path, findings, str(output_path / "MPLAN_BOKOR_annotated.xlsx"),
        sheet_name="Sheet1", maintenance_plan_column=5,
    )

    return findings


if __name__ == "__main__":
    # This is the ONLY place in the codebase that requires real Azure
    # credentials — building the Deep Agent from live config and passing
    # it into run_pipeline. Every test and every other call site leaves
    # agent_c as None or a fake test double.
    settings = load_settings()
    chat_model = get_chat_model(settings["llm_provider"])
    agent_c = build_agent_c(chat_model)
    results = run_pipeline(str(BASE_DIR / "input"), str(BASE_DIR / "output"), agent_c=agent_c)
    print(f"Agent C run complete: {len(results)} findings written to output/Findings_Report.xlsx")
```

**Injecting a fake agent in tests (closes the "no real credentials required" gap):** this task's own end-to-end test below calls `run_pipeline(str(input_dir), str(output_dir))` with `agent_c` left at its default `None` — the pipeline still runs completely, exercising every pain point's fully deterministic fallback path (PP4's sub-threshold candidates stay at `detection_confidence=40`; PP5's unit-scope-excluded rows skip the agent-confirmation step). Tasks 8 and 9 additionally test the agent-mediated paths directly against `run_pp4`/`run_pp5` using small fake `agent_c` test doubles (`_FakeAgent`, `_FakeMessage`) that implement only the `.invoke({"messages": [...]}) -> {"messages": [obj_with_content]}` contract `_ask_agent_pp4_semantic_match`/`_ask_agent_oreda_worth_checking` actually call — no real `deepagents`/LangChain object, no network call, no Azure credentials, anywhere in the test suite. `python app.py` remains the one command that builds and uses the real agent, exactly matching the required runtime contract.

- [ ] **Step 5: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v
```
Expected: 38 passed.

- [ ] **Step 6: Run the full test suite**

```bash
cd Agent_C_TaskList_MPlan
pytest -v
```
Expected: all tests across `test_normalize.py`, `test_validation.py`, `test_connectors.py` pass (10 + 38 + 5 = 53 total).

- [ ] **Step 7: Commit manually**

Commit `app.py`, `system_prompt.md`, `tests/test_validation.py` — message like `feat: app.py single runtime entry point — agent_c injectable and actually invoked by PP4/PP5, positional MPLAN/UNIT ingest, known-TLGRP-based key parsing, all 5 sources schema-validated`.

**Note for the implementer — the one remaining open item after this task:** `_ask_agent_pp4_semantic_match`/`_ask_agent_oreda_worth_checking` (Tasks 8–9) call `agent_c.invoke({"messages": [{"role": "user", "content": prompt}]})` and read `result["messages"][-1].content` — this is the standard LangChain/LangGraph agent invocation contract, and `deepagents`-built agents are LangGraph graphs underneath, so this pattern is expected to work as written. Before the first real credentialed run (Task 13), confirm this against the actually-installed `deepagents` package version — if a future release changes the invocation shape, update both `_ask_agent_*` helper functions (and their fake-agent test doubles, which model the same `.invoke(...) -> {"messages": [obj_with_content]}` contract) together, in one place, rather than guessing a different shape for each call site.

---

## Task 13: Run Against the Real Seeded Input and Verify

**Files:**
- No new files — this task exercises Task 12's `app.py` against the real files copied in Task 1.

**Interfaces:**
- Consumes: `run_pipeline` (Task 12), the real files under `input/` seeded in Task 1.
- Produces: real `output/Findings_Report.xlsx` + 3 annotated files, and a manual sanity check against §5's known findings counts.

- [ ] **Step 1: Run the real pipeline**

```bash
cd Agent_C_TaskList_MPlan
python app.py
```
Expected: prints `Agent C run complete: N findings written to output/Findings_Report.xlsx` with no traceback. If `work_centre_families.yaml`'s `approved_work_centres` lists are still empty (Task 1 Step 7 left them as placeholders pending the client's full Planner-Group mapping), PP2 will report every Item-level Work Centre as unresolved rather than recommending a value — this is the architecture's documented open item (§9 item 6), not a bug; do not fill in a guessed mapping to make PP2 "look complete."

- [ ] **Step 2: Sanity-check counts against §5's verified findings**

```bash
python -c "
import polars as pl
df = pl.read_excel('output/Findings_Report.xlsx')
print(df.group_by('Pain_Point').agg(pl.len().alias('n')).sort('Pain_Point'))
print('PP1 non-platform-prefix rows (expect near 994):', df.filter((pl.col('Pain_Point')=='PP1')).height)
print('PP3 orphan candidates (expect near 542):', df.filter(pl.col('Pain_Point')=='PP3').height)
"
```
Expected: PP1 count in the neighborhood of 994 (§5 PP1 "994 (17.1%) carry other prefixes"), PP3 count in the neighborhood of 542 (§5 PP3 "542/1,493 (36%) not referenced in the bridge"). Exact equality is not required — the earlier survey's counts came from ad hoc verification scripts, not this exact codebase — but an order-of-magnitude mismatch means a join or normalization step regressed and must be investigated before treating the run as trustworthy, per §8's evidence-based validation principle.

- [ ] **Step 3: Confirm the confidence rule holds on the real output**

```bash
python -c "
import polars as pl
df = pl.read_excel('output/Findings_Report.xlsx')
violations = df.filter(
    ((pl.col('Recommended_Value').is_null()) & (pl.col('Confidence') != 0)) |
    ((pl.col('Recommended_Value').is_not_null()) & ((pl.col('Confidence') < 70) | (pl.col('Confidence') > 100)))
)
print('Confidence rule violations:', violations.height)
assert violations.height == 0
"
```
Expected: `Confidence rule violations: 0`. This is expected to always pass given Task 2's Pydantic validator ran on every finding before `output_writer.py` wrote it — this step exists as an independent, output-file-level check per §8's "no value without a cited source and a passing check" principle, not because the Pydantic gate could plausibly have been bypassed.

- [ ] **Step 4: Confirm the Deep Agent is built AND actually consulted during a real run**

```bash
cd Agent_C_TaskList_MPlan
python -c "
from app import load_settings, get_chat_model, build_agent_c, run_pipeline
settings = load_settings()
chat_model = get_chat_model(settings['llm_provider'])
agent_c = build_agent_c(chat_model)
print('Deep Agent built:', type(agent_c).__name__)
findings = run_pipeline('input', 'output', agent_c=agent_c)
agent_backed = [f for f in findings if 'Deep Agent' in f.evidence_source]
print('Findings whose evidence trail shows Deep Agent involvement:', len(agent_backed))
"
```
Expected: prints the built agent's type, then the pipeline runs to completion with `agent_c` actually passed through to `run_pp4`/`run_pp5` this time (requires valid Azure credentials in `.env` — if credentials are not yet available, at minimum this confirms `create_deep_agent(...)` is reachable and importable; the full credentialed run is a separate verification once Azure access is provisioned). The second count can legitimately be `0` on a given data drop (PP4 might have zero sub-threshold candidates, PP5 might have zero unit-scope-excluded rows that round) — the point of this step is confirming `agent_c` reaches `run_pp4`/`run_pp5` and is callable without raising, not that it necessarily produces a nonzero count on this specific dataset. Compare against `Step 1`'s plain `python app.py` run (which also builds and passes the real agent, per `__main__`'s corrected implementation) to confirm both entry points behave the same way.

- [ ] **Step 5: Commit manually** (do not commit the actual `output/*.xlsx` files — they're git-ignored per Task 1's `.gitignore`)

Commit any remaining tracked changes with a message like `chore: verify end-to-end run against seeded real input, confirm Deep Agent construction and invocation`.

---

## Self-Review Notes

**Spec coverage:** §1–§4 (input/evidence scoping) → Task 1 (seed data). §5.0 (normalization) → Task 3, including the corrected `known_tlgrps`-based MPLAN key parsing. §5 PP1–PP7 → Tasks 7–10, all living in `validation.py` alongside the `Finding` schema from Task 2. §6 (workflow order) → Task 12's `run_pipeline`, which calls the 7 `run_ppN` functions directly in fixed order and passes `agent_c` (injectable, defaults to `None`) into PP4/PP5. §7 (output schema) → Task 11, with PP7 now correctly emitting only actual findings. §8 (evidence enforcement, no invented values) → Task 2's Pydantic gate, PP4's corrected no-fabricated-winner logic (Task 8), and Task 13's independent output check. §9 (open gaps) → carried as code comments/config placeholders in Tasks 1, 6, 7 rather than silently resolved. §10 (repo layout) → File Structure section, matches the user-approved simplified tree exactly. §11.1–§11.4 (Deep Agent boundary, fixed sequencing, tech stack) → Task 12's `build_agent_c` + Tasks 8–9's `run_pp4`/`run_pp5`, which actually invoke the built agent via `.invoke({"messages": [...]})`, not merely construct and leave it unused.

**Structural change from the first draft, confirmed against explicit direction:** dropped `core/` entirely — no `core/config.py`, `core/ingest.py`, `core/schema.py`, `core/llm_provider.py`, `core/deep_agent.py`, `core/pain_points/*.py` (12 files). Everything now lives in `app.py` (config/ingest/provider/orchestration/Deep Agent construction) and `validation.py` (schema + all 7 pain points), matching the tree the user pasted exactly. Test files collapsed from 12 to 3 (`test_normalize.py`, `test_validation.py`, `test_connectors.py`), also matching the user's pasted tree exactly. Per explicit instruction, **no task contains a runnable `git` command** — every "Commit" step is now phrased as a manual reminder naming the files and a suggested message, never an actual `git init`/`git add`/`git commit` invocation.

**Corrections applied across both review rounds, verified against the real files directly (not assumed):**

1. **Deep Agent actually invoked, not just built.** `run_pp4` (Task 8) calls `agent_c.invoke(...)` on sub-threshold candidate pairs to get a `SAME_TASK`/`DIFFERENT_TASK`/`UNCERTAIN` semantic verdict — raising `Detection_Confidence` to 70, dropping the candidate, or leaving the deterministic result unchanged, respectively; it never selects a retained Task List regardless of the verdict. `run_pp5` (Task 9) calls `agent_c.invoke(...)` on unit-scope-excluded rows to confirm OREDA applicability via its tool before reporting insufficient evidence — the deterministic `NULL`/`0` result is unchanged either way, since `oreda_connector.py` already independently re-verifies "not usable" every run, but the agent's coordination role is now genuinely exercised. Both call sites wrap the agent call in `try/except`, falling back to the unchanged deterministic result on any failure — tested explicitly (`test_pp4_agent_failure_falls_back_to_deterministic_result`).
2. **Ground truth extracted per-PP, per-source, not one whole document dumped everywhere.** `scripts/build_ground_truth.py` (Task 6) has `extract_pdf_page_range` pulling only a pain point's cited page span from its actual source document. §4c's table cites `SKA_MPG_MWC_PMMS.pptx` for PP2 and other non-UDMS sources for other pain points — extracting from a `.pptx` needs a different reader than `pymupdf4llm` (a `python-pptx`-based `extract_pptx_text` helper), which Task 6's implementer note flags as a required follow-on before the first real run, alongside confirming the placeholder page numbers. This remains a genuinely open item — not silently resolved, but not glossed over either.
3. **Architecture document corrected to match the implementation's more conservative, evidence-honest behavior** (`Proposal/TaskList_MPlan_Agent_Plan_Architecture.md`, edited directly in this revision): §5.0's MPLAN parsing description now describes the `known_tlgrps`-exact-match approach instead of a fixed-width split; PP2's table no longer claims a `Confidence=90` operation-level MULTI recommendation is possible (corrected to always `NULL`/`0`, `Detection_Confidence=100`); PP4's table no longer claims a strong bridge-linked match "returns the retained Task List" (corrected to `NULL`/`0` with `Detection_Confidence=90`, and a new paragraph explains why no evidence source in this architecture can answer that question); PP7's table no longer implies every correctly-assigned row is its own `Confidence=100` finding (corrected to a pass-rate summary statistic, not per-row findings).
4. **PP2's cross-unit ranking bug fixed at the root, not papered over.** The earlier `["OPWKCEN", "WORK_UNIT"]` group-by was correct, but sorting all resulting groups together regardless of unit could still rank `100 STD` above `10 MHR`. The fix filters to the single canonical `valid_work_unit` (from `unit_rules.yaml`) before ranking at all, and fails closed when no rows exist in that unit — verified by a regression test (`test_pp2_item_level_multi_never_ranks_across_incompatible_units`) using numbers specifically chosen so the old buggy code and the new correct code would disagree.
5. **`write_annotated_long_text`'s key now matches PP5's `record_key` grain exactly.** The earlier `TLGRP+TLGRPCOUNT` key would have silently failed to map PP5's (and PP2 operation-level's, and PP4's) findings back onto the correct row whenever a Task List has more than one operation. Both the writer (Task 11) and the two pain-point functions that report at operation grain (`run_pp2`'s operation-level branch, `run_pp5`) now consistently use the full `TLGRP+TLGRPCOUNT+TLOPNO+TLSUBOPNO` key.
6. **Equipment IDs are explicitly string-cast before PP6's join**, per §4a's directly-verified int/string mismatch (the original survey's join only reached 99.9% match after casting both sides to string) — `run_pp6` (Task 10) now does `{str(e) for e in task_list_group["Equipment"]}` and `str(row["Equipment"])` before comparing, with a regression test (`test_pp6_equipment_join_normalizes_int_vs_string_mismatch`) using a Polars-int-typed bridge column against a string-typed Agent A column.
7. **`thresholds.yaml` values are now actually read by `run_ppN`, not merely defined alongside still-hardcoded Python.** `run_pp1` takes `reuse_threshold` (from `pp1.reused_prefix_min_occurrences`), `run_pp2` takes `valid_work_unit` (from `unit_rules.yaml`), `run_pp4` takes `text_similarity_threshold` (from `pp4.text_similarity_threshold`), `run_pp5` takes `work_tolerance` (from `pp5.work_tolerance`) — all four are now parameters `Task 12`'s `run_pipeline` populates from `settings["thresholds"]`, with the same numeric value kept only as each function's own default for direct unit-test calls that omit the parameter. (`run_pp3`/`run_pp6`/`run_pp7`'s bands — `pp3.*`, `pp6.*`, `pp7.*` — remain Python-level constants in this revision; they are simpler fixed classification tiers rather than tunable thresholds, and wiring them through config would add a parameter with no corresponding decision point to tune. If the client later wants those tiers configurable too, extend `run_pp3`/`run_pp6`/`run_pp7` the same way `run_pp1`/`run_pp2`/`run_pp4`/`run_pp5` were extended here.)
8. **The end-to-end test suite requires zero real Azure credentials.** `run_pipeline` takes `agent_c` as an optional parameter defaulting to `None` — it is never built inside `run_pipeline` itself. `get_chat_model`/`build_agent_c` are only ever called from `app.py`'s `if __name__ == "__main__":` block. Every test (including Task 12's own end-to-end test, and Tasks 8–9's agent-path tests) either passes `agent_c=None` or a small fake test double implementing only the `.invoke({"messages": [...]}) -> {"messages": [obj_with_content]}` contract — no real `deepagents`/LangChain object is constructed anywhere in the test suite. `python app.py` remains the single command that builds and uses the real, credentialed agent in production.
9. **All 5 input sources get the same fail-loudly schema guard**, not just Agent A's two. `scripts/validate_schema.py` (renamed from the earlier `validate_agent_a_schema.py`, Task 4) adds `validate_task_list_group_schema`, `validate_long_text_schema`, `validate_mplan_schema` alongside the existing FLOC/Equipment guards — `run_pipeline` (Task 12) calls all 5 immediately after ingest, before any pain-point logic, so a renamed or missing column in a primary file fails with a clear message at ingest time instead of a confusing error deep inside a pain-point function.
10. PP2's MULTI-substring matching, `BMULTI`/`TMULTI` variants, fail-closed-on-empty-approved-list, PP4's no-fabricated-winner logic, PP5's full operation key/numeric-tolerance/RTOF-adjacent unit scoping, and `output_writer.py`'s `openpyxl`-based `.xlsm`/VBA preservation all carried over unchanged from the previous review round — see the file's earlier revision history if the specific verification detail (row counts, real column values) is needed again.

**Known scope notes flagged inline, not hidden — genuinely open after this revision:** (a) Task 8's PP3 implements 2 of the 3 detection-confidence tiers §5 PP3 describes; the third (FLOC/Equipment active-status cross-check) needs a join key not present in the normalized-operations grain as the real files are shaped today. (b) `config/work_centre_families.yaml`'s empty `approved_work_centres` lists (Task 1) and `scripts/build_ground_truth.py`'s placeholder page numbers plus missing PPTX/DOCX extraction (Task 6) are both deliberate, explicitly-flagged open items pending client/document confirmation — not silent TBDs; PP2's fail-closed fix ensures the empty list produces `NULL`/`0` rather than a wrong recommendation in the meantime. (c) `run_pp3`/`run_pp6`/`run_pp7`'s numeric bands remain Python-level constants rather than `thresholds.yaml`-driven parameters (item 7 above) — a smaller, deliberately-scoped gap, not an oversight.

**Type consistency:** `Finding` (Task 2, in `validation.py`) is the one schema every pain-point function (Tasks 7–10, same file), `app.py`'s `run_pipeline`, and `output_writer.py` import and construct — no parallel finding representation exists anywhere in the plan. All `run_ppN` and `output_writer` function signatures were checked against their actual call sites in Task 12's `run_pipeline` and Task 12's end-to-end test after each edit in this revision (`multi_variants`, `known_tlgrps`, `work_tolerance`, `agent_c`, `reuse_threshold`, `text_similarity_threshold`, file-path-based `write_annotated_*`) to catch exactly the kind of drift a partial edit could introduce. Every test-count claim (`Expected: N passed`) in this document was recomputed by counting actual `def test_` occurrences per task after every edit in this revision, not carried forward by arithmetic assumption — a discrepancy caught and fixed during this same revision (Task 7's PP2 test count) confirmed this check was necessary, not redundant.
