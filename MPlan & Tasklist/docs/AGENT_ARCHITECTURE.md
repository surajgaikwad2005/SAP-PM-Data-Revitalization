# Agent C — How It's Built

Internal technical reference for the Agent C (Planning Data / Task List & MPlan) pipeline.
Path: `Agent_C_TaskList_MPlan/`

---

## 1. Python Files (18 files, 7,332 lines)

### Root

| File | Lines | What it does |
|---|---|---|
| `app.py` | 859 | Entry point. Loads settings, builds the LLM chat model + Deep Agent, pulls all data from the Knowledge Graph, runs PP1–PP7 in sequence, writes output workbooks. |
| `validation.py` | 3,358 | The core logic file. Defines the `Finding` model and all 7 pain-point checks (`run_pp1` … `run_pp7`), including every LLM prompt-building, parsing and caching function. ~46% of all project code. |
| `output_writer.py` | 740 | Writes the two output Excel workbooks (Recommendations, Findings Summary) from the list of `Finding` objects. |
| `report_generator.py` | 725 | Standalone PDF report generator — reads the output workbooks and renders a client-facing PDF. |
| `logging_config.py` | 20 | Shared logger factory (`agent_c` logger) and a `batched()` helper used everywhere items are chunked for LLM batching. |

### `evidence_connectors/`

| File | Lines | What it does |
|---|---|---|
| `__init__.py` | 0 | Package marker. |
| `oreda_connector.py` | 92 | Queries OREDA reliability-benchmark tables in the KG and judges whether OREDA is applicable evidence for PP5. |
| `pitstops_connector.py` | 45 | Loads/normalizes PITSTOPS task-list Excel exports and computes per-discipline duration ranges (plausibility evidence only). |

### `scripts/`

| File | Lines | What it does |
|---|---|---|
| `__init__.py` | 0 | Package marker. |
| `kg_client.py` | 98 | Thin Postgres client for the Knowledge Graph (see §4). |
| `normalize.py` | 52 | Normalizes long-text/operation rows and classifies MPLAN rows (detail vs. aggregate). |
| `evidence_reconciliation.py` | 322 | PP5 Tier-2 evidence logic — historical-range, JMS, OREDA and PITSTOPS "lanes" plus convergence checks. Pure logic, no LLM calls. |
| `historical_matching.py` | 278 | Matches Task List operations against 10-year work-order/timesheet history to build PP5 historical benchmarks. |
| `jms_workpack_matching.py` | 99 | Matches JMS work-pack rows to normalized operations by equipment tag/text similarity. |
| `validate_schema.py` | 73 | Schema validators for the 5 KG input tables (equipment, FLOC, long text, MPLAN, task-list-group). |
| `view_kg_data.py` | 206 | Standalone CLI/debug script to dump KG tables to Excel for manual inspection. |
| `generate_pdf_report.py` | 257 | CLI wrapper script around `report_generator.py`. |
| `build_ground_truth.py` | 54 | One-off utility to extract PDF/page-range text into the `ground_truth_cache` markdown files. |
| `build_jms_manhours_cache.py` | 54 | Merges JMS man-hours extraction CSVs into the `PP05_JMS_ManHours.csv` cache. |

No `.py` files exist under `config/` (YAML only) or `docs/` (Markdown only). `venv/` holds third-party packages (LangChain, deepagents, Anthropic SDK) — excluded here as it isn't project code.

---

## 2. LLM / Tool-Call Usage

All LLM calls go through **one object, `agent_c`** — a LangChain `deepagents.create_deep_agent(...)` instance built once in `app.py::build_agent_c` (lines 78–101) and passed as a parameter into `validation.py`'s pipeline functions. The underlying model is chosen in `app.py::get_chat_model` (lines 55–75): Azure OpenAI (`AzureChatOpenAI`) or Azure-hosted Claude (`ChatAnthropic`), selected via the `AGENT_C_LLM_PROVIDER` env var.

There are **4 call sites**, all via `agent_c.invoke({"messages": [{"role": "user", "content": prompt}]})`:

### PP2 — Work Centre discipline classification
- **Function:** `_ask_agent_pp2_classify_batch` (validation.py:1368–1393), called from `run_pp2` (line 1477)
- **Task:** classify each distinct Task List operation's scope text (OPDESC + LONGTEXT) into a maintenance discipline (Mechanical, Electrical, Instrument, MULTI, UNCLEAR) with a confidence label and basis text, to recommend a corrected Work Centre.
- **Cache:** `ground_truth_cache/PP02_discipline_cache.csv`, keyed by `_pp2_cache_key(normalized_text, schema_version)`. `schema_version` bumps (forcing re-classification) if the valid-discipline list changes. Only cache misses reach the LLM, in batches of 15, up to 2 retries per batch.
- **Real log line:** `"PP2: {cache hits} distinct texts served from cache, {misses} need a fresh Deep Agent call"`.

### PP4 — Duplicate/overlap semantic comparison
- **Function:** `_ask_agent_pp4_classify_batch` (validation.py:1803–1826), called from `run_pp4` (line 1902)
- **Task:** for ambiguous Task List operation pairs (similar but not identical text), verdict EQUIVALENT / PARTIAL_OVERLAP / DIFFERENT / UNCLEAR, feeding the duplicate-Task-List score.
- **Cache:** `ground_truth_cache/PP04_semantic_cache.csv`, keyed by `_pp4_cache_key(text_a, text_b)`. Only pairs that survive deterministic exact-match + similarity pre-filtering reach this stage.
- **Real log line:** `"PP4: {cache hits} operation pair(s) served from cache, {misses} need a fresh Deep Agent call"`.

### PP5 — OREDA applicability check
- **Function:** `_ask_agent_oreda_worth_checking` (validation.py:2033–2046), called from the PP5 row-check path (line 2555/2573)
- **Task:** when WORK/DURATION units fall outside standard MHR/HR scope, asks the agent to invoke its `check_oreda_applicability` tool and report whether OREDA has usable reliability-benchmark data.
- **Cache:** none — runs fresh every time this uncommon unit-mismatch condition is hit.

### PP5 — Scope summarization
- **Function:** `_ask_agent_pp5_scope_batch` (validation.py:2245–2268), called from `_pp5_build_scope_lookup` (line 2271–2329), itself called from `run_pp5`
- **Task:** for operations whose Tier-1 arithmetic (WORK = PERSON × DURATION) is valid, extract ACTIVITY / EQUIPMENT / SCOPE short fields from OPDESC + LONGTEXT, used later to match against historical/JMS records for man-hours benchmarking.
- **Cache:** `ground_truth_cache/PP05_scope_cache.csv`, keyed by sha256 of `{prompt_version}\x00{normalized_text}`. Batches of 15, up to 2 retries.
- **Real log line:** `"PP5 scope: classified {n}/{total} new operations"`.

**Invocation volume:** each of the 3 batched call sites issues **1 LLM call per batch of up to 15 cache misses** (plus up to 2 retries only on malformed replies). Since all three caches persist across runs, repeat runs typically produce far fewer fresh calls than the first run — confirmed directly in this project's own logs (e.g. a real run showed `"0 need a fresh Deep Agent call"` for PP2 and PP4 once their caches were warm).

---

## 3. Tool Definitions

**No LangChain `Tool(...)`, `@tool` decorator, or `BaseTool` subclass exists anywhere in project code** (confirmed by a repo-wide search; every match was inside `venv/` third-party packages, not project code).

Instead, `build_agent_c` (app.py:78–101) passes two plain Python functions directly to `create_deep_agent(tools=tools, ...)`, which wraps them as callable tools itself:

1. **`read_ground_truth(pain_point_file: str) -> str`** — reads a cited ground-truth excerpt markdown file (e.g. `PP04_Duplicate_TaskList.md`) from `ground_truth_cache/`, giving the agent access to the client's pain-point spec text.
2. **`check_oreda_applicability() -> str`** — checks (via `evidence_connectors.oreda_connector.is_oreda_applicable_to_pp5`) whether the KG's `oreda_data` table has usable reliability data for PP5's man-hours check.

---

## 4. Knowledge Graph Client (`scripts/kg_client.py`, 98 lines)

| Function | Purpose |
|---|---|
| `get_connection()` | Opens a psycopg connection to the Postgres-backed KG using Azure CLI AAD token auth. |
| `get_nodes_by_type(conn, node_type)` | Fetches `node_id`/`natural_key` for all nodes of a given type. |
| `get_properties_for_type(conn, node_type)` | Fetches and pivots all `node_properties` rows for a type into a wide per-node_id table. |
| `get_full_table_for_type(conn, node_type)` | Convenience join of the above two — one flat table per node type. |
| `get_children(conn, source_id, relationship)` | Returns target_ids for a given source node and relationship (graph traversal). |
| `get_edges_by_relationship(conn, relationship)` | Returns all source/target pairs for a relationship type across the whole graph. |
| `get_table(conn, table_name)` | Direct passthrough `SELECT *` for a small allowlisted set of flat tables (`oreda_data`, `bokor_eca_report`, `catalog_profile`, `hierarchy_index`, `process_subprocess`). |

---

## 5. Entry Point & Orchestration (`app.py`)

`if __name__ == "__main__"` (lines 850–858): loads settings → builds chat model → opens KG connection → builds `agent_c` → calls `run_pipeline(...)`.

`run_pipeline()` (lines 552–847), real execution order per its own log labels:

1. **STEP 1/2** (line 565) — fetch Task List Group, Long Text, MPLAN, agent_a (FLOC/Equipment), 10-year Work Order history from the KG; validate schemas; also load Equipment Class master, Maintenance Strategy master, PITSTOPS task lists, and historical timesheet/JMS/PPM Excel caches if present (each guarded by file-existence checks — missing ground-truth files degrade gracefully rather than crashing).
2. **STEP 3** (line 679) — normalize long text and MPLAN rows (`normalize_long_text`, `parse_mplan_task_list_key`, `classify_mplan_rows`); build the PP1 Task List summary and merge Task-List-Group-derived columns; build JMS workpack matches if that cache exists.
3. **Pain-point execution** (unlabeled "STEP 4/5") — runs **PP1 → PP2 (only if `agent_c` supplied) → PP3 → PP4 → PP5 → PP6 → PP7**, in that fixed order, each appending `Finding` objects to one running list. **Only PP2, PP4 and PP5 take `agent_c`** — PP1, PP3, PP6, PP7 are pure rule-based checks with no LLM involvement.
4. **STEP 6** (line 819) — writes `SAP_PM_Agent_Recommendations.xlsx` and `SAP_PM_Agent_Findings_Summary.xlsx` via `output_writer.py`, logging a per-pain-point summary (checked / findings / suggestions / confidence breakdown / review-required counts).

A separate script, `scripts/generate_pdf_report.py` (using `report_generator.py`), is a standalone post-process that reads those output workbooks to produce the client PDF — **it is not invoked from `app.py`'s `run_pipeline`**.

---

## 6. Most Central vs. Peripheral

**Most central — the pipeline cannot function without these:**

1. **`validation.py`** — all 7 pain-point implementations and every LLM prompt/cache/parse function. The single most load-bearing file by a wide margin.
2. **`app.py::run_pipeline`** — the orchestrator defining execution order, data fetching and output assembly.
3. **`scripts/kg_client.py`** — every data source except the `ground_truth_cache` Excel/CSV files is fetched through this one thin client.
4. **`output_writer.py`** — the only path by which `Finding` objects become the two deliverable Excel workbooks.
5. **`scripts/normalize.py` + `scripts/evidence_reconciliation.py`** — `normalize.py` feeds literally every downstream pain point; `evidence_reconciliation.py` is the deterministic (non-LLM) decision core of PP5, the most evidence-heavy check.

**More peripheral / support:**

- `logging_config.py` — small, generic logging/batching helper.
- `evidence_connectors/pitstops_connector.py`, `oreda_connector.py` — narrow, single-purpose evidence adapters feeding only PP5's supporting/last-resort evidence lanes.
- `scripts/view_kg_data.py`, `build_ground_truth.py`, `build_jms_manhours_cache.py` — standalone CLI/debug/one-off cache-building utilities, not imported by `run_pipeline`.
- `report_generator.py` + `scripts/generate_pdf_report.py` — downstream, optional client-report generation, separate from the validation pipeline itself.
- `config/*.yaml` (not Python, but worth noting) — externalizes thresholds/mappings so `validation.py` stays data-driven rather than hardcoded.
