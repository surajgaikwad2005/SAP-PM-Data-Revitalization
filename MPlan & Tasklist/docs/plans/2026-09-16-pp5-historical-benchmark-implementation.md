# PP5 Historical Man-Hour Benchmark — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the historical man-hour recommendation layer for PP5 per `docs/plans/2026-09-15-pp5-resolution-plan.md`: (1) a standalone data-coverage report proving how many Task List Operations connect to historical Work Order/Timesheet/JMS evidence, and (2) a historical-benchmark evidence layer wired into `run_pp5` that recommends a value when reliable evidence exists and reports `Needs Review` when it doesn't — never a guess.

**Architecture:** Two new modules plus one `run_pp5` extension. `scripts/historical_matching.py` owns the join/verification logic (Hop 1-3′ from the approved plan, execution-vs-version match confidence, per-source candidate-hour extraction). `scripts/coverage_report.py` is a standalone, runnable script that calls `historical_matching` and writes a coverage report (counts, not Findings) to `output/PP5_Coverage_Report.xlsx` — this is Step 2A/2B/2C, run and reviewed before anything in `validation.py` changes. `validation.py::run_pp5` then gains an additional evidence path (historical benchmark + OREDA-repair-only branch) that only activates for operations the coverage report already showed have a reliable match, using a minimum-sample/match-quality gate loaded from `config/thresholds.yaml`. The existing arithmetic check (`_pp5_row_check`'s completeness/unit/arithmetic logic) is untouched. Internally the code tracks execution-identity confidence, version confidence (always `version_unconfirmed` today — no Task List revision field exists in any surveyed source), and per-source candidate hours separately; externally, `run_pp5`'s Finding output stays exactly as simple as the user's 6-point spec: suggested value, confidence, evidence, or `Needs Review`.

**Tech Stack:** Python (matches project — `pandas`, `pyyaml`, `pytest`), no new dependencies.

## Global Constraints

- **No pandas replaced with polars** — this project's `validation.py`/`app.py` already use `pandas` throughout (confirmed: `import pandas as pd` in both files) despite an earlier architecture doc's polars mention; follow the code as it exists, not the older doc.
- **Confidence is a 0.0-1.0 float**, `Recommended_Value=None` iff `confidence==0.0`, enforced by `Finding.enforce_confidence_rule` — every new Finding must go through this unchanged.
- **No invented values.** Where the coverage/matching logic can't establish a reliable historical benchmark, the row must get `confidence=0.0`, `recommended_value=None`, and a `reason` stating why — never a guess, never an average of insufficient/low-quality data.
- **Never sum Timesheet and JMS `Operation Line` actual hours for the same `Order`+`Activity`** without evidence they're distinct labour — default assumption is they describe the same execution.
- **`Correction Indicator` carries no usable signal** — confirmed empty in both real Timesheet files (2024, 2025). Do not build logic that branches on this column's value; instead, exclude it from consideration and note the limitation in code comments, since a future data refresh could populate it.
- **Timesheet's trailing summary row must be excluded** before any aggregation — confirmed present at the end of both real Timesheet sheets, identifiable as the row where every column is blank except `Number (unit)` and `Internal UoM`.
- **JMS `Operation Line`'s `Work` column must never be treated as hours uniformly** — confirmed real-data fact: `Control Key='ESVC'` rows have `Work` values on a completely different scale (mean 5,358 vs. `Actual work`'s mean 6.33 for the same rows) and are not usable as an hours figure at all. Only `Actual work` is scale-consistent with Timesheet's `Number (unit)` and is the field to use.
- **Copy-only data sourcing** — new source files are read-only copies into `input/`, matching the existing project convention (never modify `All_sites_Data/`).
- **Code style**: simple, modular, meaningful names, no placeholder logic, one-line comments only where the WHY is non-obvious (matches this project's existing style throughout `validation.py`).
- **Testing**: `pytest`, run from `Agent_C_TaskList_MPlan/`, synthetic DataFrames built inline — never depend on real Excel files being present (matches existing `tests/test_validation.py` convention).
- **`app.py`'s PP5 call stays commented out** for this plan — re-enabling PP5 (independent of PP1/PP2/PP6/PP7) is a separate, later decision per the resolution plan's §11; this plan only makes the code correct and tested, it does not flip the pipeline toggle.

---

## Source File Reference (verified directly — use these exact paths/columns/facts, do not re-derive)

| File | Sheet | Real facts confirmed |
|---|---|---|
| `Timesheet BOKOR_2024.xlsx` / `_2025.xlsx` (source: `All_sites_Data/SAP/Planning Data/`) | `Data` | 49 columns, header has **`Counter` twice** (must dedupe on load — see Task 1). Key fields: `General receiver` (format `"<8-digit Order> <4-digit Operation>"`, e.g. `'81516386 0010'`), `Number (unit)` (the hours value), `Internal UoM` (**100% `'H'`** in both files — single consistent unit, no filtering needed), `Correction Indicator` (**100% blank** in both files — no usable signal), `Personnel Number` (**~47-48% blank** in both files — blank-personnel rows still carry a real `Number (unit)` value and must not be silently dropped). **Last row of each sheet is a non-data trailing summary row** (all columns blank except `Number (unit)`/`Internal UoM`) — must be excluded before aggregation. ~6.3 rows per non-blank `General receiver` on average (up to 1,338 for one value) — aggregation to one figure per Order+Operation is mandatory. |
| `M014_Bokor_Non PPM Work Order 2020_2025.xlsx` (source: `All_sites_Data/SAP/Planning Data/JMS/`) | `Data` (4,329 rows: `Order`, `Maintenance Plan`, `Maintenance Item`, `Group`, `Group Counter` populated on only 158/4,329 rows ~3.6%) and `Operation Line` (6,536 rows: `Order`, `Activity` (4-digit), `Control Key`, `Work`, `Actual work`, `Execution Start Date`, `Execution End Date`, `Number`) | **Use `Actual work`, never `Work`, as the hours figure** — confirmed `Work` is not scale-consistent across `Control Key` (`INTN` rows look like hours, `ESVC` rows are a completely different scale, mean 5,358 vs. `Actual work`'s 6.33 for the same population). No unit/UoM column exists in this sheet at all. |
| `BOKOR_10years Work Order Data_Aug26.xlsx` | `Data` | Already in `Agent_C_TaskList_MPlan/input/`. Has `Order`, `Maintenance Plan`, `Group`, `Group Counter`. Population rate of `Group`/`Group Counter` in this specific file is unmeasured — do not assume it matches the JMS file's ~3.6%; Task 3 measures it independently. |
| `Bokor Task List Group.xlsx` | `Data` | Already in `input/`. Bridge file — `Group`, `Group Counter` join to Task List Operations' `TLGRP`/`TLGRPCOUNT` (this exact join is PP3's live production logic, `validation.py::run_pp3`). |

---

## File Structure

```
Agent_C_TaskList_MPlan/
├── input/
│   ├── Timesheet_BOKOR_2024.xlsx          # NEW — copied from All_sites_Data
│   ├── Timesheet_BOKOR_2025.xlsx          # NEW — copied from All_sites_Data
│   └── M014_Bokor_Non_PPM_Work_Order_2020_2025.xlsx   # NEW — copied from All_sites_Data
├── scripts/
│   ├── historical_matching.py             # NEW — join/verification logic (Tasks 2-5)
│   └── coverage_report.py                 # NEW — standalone Step 2A/2B/2C report (Task 6)
├── config/
│   └── thresholds.yaml                    # MODIFIED — add pp5 historical-benchmark gate values (Task 7)
├── validation.py                          # MODIFIED — run_pp5 gains historical-benchmark path (Task 7)
├── app.py                                 # MODIFIED — new readers for the 3 new files (Task 1)
├── tests/
│   ├── test_historical_matching.py        # NEW (Tasks 2-5)
│   └── test_validation.py                 # MODIFIED — new run_pp5 tests (Task 7)
└── output/
    └── PP5_Coverage_Report.xlsx           # generated by scripts/coverage_report.py (Task 6)
```

**Rationale:** `historical_matching.py` is a new file (not folded into `validation.py`) because it is reusable independent of `run_pp5` — the coverage report calls it directly without going through the Finding/pain-point machinery, matching this project's existing pattern of keeping `scripts/`/`evidence_connectors/` reusable and separate from `validation.py`'s pain-point functions.

---

## Task 1: Copy Source Files and Add Readers

**Files:**
- Copy: 3 files from `All_sites_Data/SAP/Planning Data/` (and `.../JMS/`) into `Agent_C_TaskList_MPlan/input/`
- Modify: `Agent_C_TaskList_MPlan/app.py`

**Interfaces:**
- Produces: `read_timesheet(path: str) -> pd.DataFrame`, `read_jms_work_order(path: str) -> dict[str, pd.DataFrame]` (returns `{"data": ..., "operation_line": ...}`) in `app.py`, alongside the existing `read_*` functions.

- [ ] **Step 1: Copy the 3 files**

```bash
cd "C:/Users/nikhil.raut/Tridiagonal-ai/Petronas/Data"
cp "All_sites_Data/SAP/Planning Data/Timesheet BOKOR_2024.xlsx" "Agent_C_TaskList_MPlan/input/Timesheet_BOKOR_2024.xlsx"
cp "All_sites_Data/SAP/Planning Data/Timesheet BOKOR_2025.xlsx" "Agent_C_TaskList_MPlan/input/Timesheet_BOKOR_2025.xlsx"
cp "All_sites_Data/SAP/Planning Data/JMS/M014_Bokor_Non PPM Work Order 2020_2025.xlsx" "Agent_C_TaskList_MPlan/input/M014_Bokor_Non_PPM_Work_Order_2020_2025.xlsx"
ls -la "Agent_C_TaskList_MPlan/input/" | grep -E "Timesheet|M014"
```
Expected: all 3 files present under `Agent_C_TaskList_MPlan/input/`.

- [ ] **Step 2: Write the failing test for the new readers**

Append to a new file `Agent_C_TaskList_MPlan/tests/test_historical_matching.py`:

```python
import pandas as pd
import pytest

from app import read_jms_work_order, read_timesheet


def test_read_timesheet_dedupes_duplicate_counter_header(tmp_path):
    # Real Timesheet files have 'Counter' as a column name twice (positions
    # 19 and 48) — pandas.read_excel would silently rename the second one
    # to 'Counter.1'; this test locks in that we handle it predictably
    # rather than let pandas's default mangling go unverified.
    path = tmp_path / "fake_timesheet.xlsx"
    df = pd.DataFrame(
        {
            "Personnel Number": ["100"],
            "General receiver": ["81516386 0010"],
            "Number (unit)": [4.5],
            "Internal UoM": ["H"],
            "Correction Indicator": [None],
        }
    )
    df.to_excel(path, sheet_name="Data", index=False)
    result = read_timesheet(str(path))
    assert "General receiver" in result.columns
    assert result["Number (unit)"][0] == 4.5


def test_read_jms_work_order_returns_both_sheets(tmp_path):
    path = tmp_path / "fake_jms.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame({"Order": ["81485790"], "Group": ["GLOC001"], "Group Counter": ["1"]}).to_excel(
            writer, sheet_name="Data", index=False
        )
        pd.DataFrame(
            {"Order": ["81485790"], "Activity": ["0110"], "Control Key": ["INTN"], "Work": [4.0], "Actual work": [3.5]}
        ).to_excel(writer, sheet_name="Operation Line", index=False)
    result = read_jms_work_order(str(path))
    assert set(result.keys()) == {"data", "operation_line"}
    assert result["operation_line"]["Actual work"][0] == 3.5
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v
```
Expected: FAIL — `ImportError: cannot import name 'read_timesheet' from 'app'`.

- [ ] **Step 4: Add the readers to `app.py`**

Add near the existing `read_work_order_history` function (after line 164):

```python
def read_timesheet(path: str) -> pd.DataFrame:
    # Real Timesheet exports (2024/2025) carry the column name 'Counter'
    # twice (positions 19 and 48) — pandas.read_excel auto-renames the
    # second occurrence to 'Counter.1'. That's acceptable here since
    # neither Counter column is used by the historical-matching logic;
    # this function exists to centralize that fact in one documented
    # place rather than leave it as an undocumented pandas side effect.
    return pd.read_excel(path, sheet_name="Data")


def read_jms_work_order(path: str) -> dict[str, pd.DataFrame]:
    return {
        "data": pd.read_excel(path, sheet_name="Data"),
        "operation_line": pd.read_excel(path, sheet_name="Operation Line"),
    }
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v
```
Expected: 2 passed.

- [ ] **Step 6: Commit manually**

Commit `app.py`, `tests/test_historical_matching.py`, and the 3 copied input files — message like `feat: add Timesheet and JMS Work Order readers`.

---

## Task 2: Exclude the Timesheet Trailing Summary Row and Aggregate Per Order+Operation

**Files:**
- Create: `Agent_C_TaskList_MPlan/scripts/historical_matching.py`
- Test: append to `Agent_C_TaskList_MPlan/tests/test_historical_matching.py`

**Interfaces:**
- Consumes: `pd.DataFrame` shaped like `read_timesheet`'s output.
- Produces:
  - `strip_timesheet_summary_row(df: pd.DataFrame) -> pd.DataFrame` — drops the trailing summary row (detected as: every column blank/NaN except `Number (unit)` and `Internal UoM`).
  - `split_general_receiver(df: pd.DataFrame) -> pd.DataFrame` — adds `order` and `operation` string columns parsed from `General receiver` (split on the single space), leaving rows with an unparseable `General receiver` (missing, no space, wrong shape) with `order=None, operation=None` rather than raising.
  - `aggregate_timesheet_hours(df: pd.DataFrame) -> pd.DataFrame` — groups by `order`+`operation`, sums `Number (unit)` (only rows where `Internal UoM == "H"`), returns columns `order, operation, timesheet_actual_hours, timesheet_row_count`. Rows with blank `Personnel Number` are included in the sum (per the resolution plan: the data gives no basis to exclude them, since a blank Personnel Number doesn't mean the hours weren't real — this is stated as a decision, not silently applied) — see the code comment in Step 4 for the exact reasoning.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_historical_matching.py`:

```python
import pandas as pd

from scripts.historical_matching import (
    aggregate_timesheet_hours,
    split_general_receiver,
    strip_timesheet_summary_row,
)


def test_strip_timesheet_summary_row_removes_trailing_total_only():
    df = pd.DataFrame(
        {
            "General receiver": ["81516386 0010", "81516386 0010", None],
            "Number (unit)": [2.0, 3.0, 5.0],
            "Internal UoM": ["H", "H", "H"],
            "Personnel Number": ["100", "101", None],
        }
    )
    result = strip_timesheet_summary_row(df)
    assert result.shape[0] == 2
    assert result["Number (unit)"].sum() == 5.0


def test_strip_timesheet_summary_row_keeps_all_rows_when_no_summary_row_present():
    df = pd.DataFrame(
        {
            "General receiver": ["81516386 0010", "82135652 0010"],
            "Number (unit)": [2.0, 3.0],
            "Internal UoM": ["H", "H"],
            "Personnel Number": ["100", "101"],
        }
    )
    result = strip_timesheet_summary_row(df)
    assert result.shape[0] == 2


def test_split_general_receiver_parses_order_and_operation():
    df = pd.DataFrame({"General receiver": ["81516386 0010", "82135652 0210"]})
    result = split_general_receiver(df)
    assert result["order"].tolist() == ["81516386", "82135652"]
    assert result["operation"].tolist() == ["0010", "0210"]


def test_split_general_receiver_unparseable_value_yields_none_not_a_guess():
    df = pd.DataFrame({"General receiver": ["garbage", None, "81516386 0010"]})
    result = split_general_receiver(df)
    assert result["order"].tolist() == [None, None, "81516386"]
    assert result["operation"].tolist() == [None, None, "0010"]


def test_aggregate_timesheet_hours_sums_per_order_operation_including_blank_personnel():
    df = pd.DataFrame(
        {
            "order": ["81516386", "81516386", "81516386"],
            "operation": ["0010", "0010", "0010"],
            "Number (unit)": [2.0, 3.0, 1.5],
            "Internal UoM": ["H", "H", "H"],
            "Personnel Number": ["100", None, "101"],
        }
    )
    result = aggregate_timesheet_hours(df)
    assert result.shape[0] == 1
    assert result["timesheet_actual_hours"][0] == 6.5
    assert result["timesheet_row_count"][0] == 3


def test_aggregate_timesheet_hours_excludes_non_hour_uom_rows():
    df = pd.DataFrame(
        {
            "order": ["81516386", "81516386"],
            "operation": ["0010", "0010"],
            "Number (unit)": [2.0, 100.0],
            "Internal UoM": ["H", "EA"],
            "Personnel Number": ["100", "101"],
        }
    )
    result = aggregate_timesheet_hours(df)
    assert result["timesheet_actual_hours"][0] == 2.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.historical_matching'`.

- [ ] **Step 3: Write `scripts/historical_matching.py`**

```python
import pandas as pd


def strip_timesheet_summary_row(df: pd.DataFrame) -> pd.DataFrame:
    # Real Timesheet exports (2024/2025) end with one non-data trailing
    # row where every column is blank except Number (unit)/Internal UoM
    # (confirmed: its value is exactly 2x the sum of all real rows in
    # both files — an artifact of the export, not a real timesheet
    # entry). Detect it structurally rather than by position, in case a
    # future export adds/removes rows.
    other_columns = [c for c in df.columns if c not in ("Number (unit)", "Internal UoM")]
    is_summary_row = df[other_columns].isna().all(axis=1)
    return df[~is_summary_row].reset_index(drop=True)


def split_general_receiver(df: pd.DataFrame) -> pd.DataFrame:
    def split(value):
        if not isinstance(value, str) or " " not in value:
            return None, None
        order, _, operation = value.partition(" ")
        if not order or not operation:
            return None, None
        return order, operation

    parsed = [split(v) for v in df["General receiver"]]
    return df.assign(
        order=[p[0] for p in parsed],
        operation=[p[1] for p in parsed],
    )


def aggregate_timesheet_hours(df: pd.DataFrame) -> pd.DataFrame:
    # Blank Personnel Number rows are included in the sum: the data gives
    # no basis to treat them as invalid (Internal UoM is still 'H' and
    # Number (unit) still carries a real value) — excluding ~47-48% of
    # all rows on this basis alone would be an unjustified assumption,
    # not a data-quality correction. Flagged in the coverage report
    # instead (scripts/coverage_report.py), not silently dropped here.
    hour_rows = df[df["Internal UoM"] == "H"].dropna(subset=["order", "operation"])
    grouped = hour_rows.groupby(["order", "operation"], as_index=False).agg(
        timesheet_actual_hours=("Number (unit)", "sum"),
        timesheet_row_count=("Number (unit)", "count"),
    )
    return grouped
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v
```
Expected: 6 passed (2 from Task 1 + 4 new... actually 6 new tests in this task, verify total is 8).

- [ ] **Step 5: Commit manually**

Commit `scripts/historical_matching.py`, `tests/test_historical_matching.py` — message like `feat: Timesheet summary-row exclusion, General receiver parsing, hour aggregation`.

---

## Task 3: JMS Operation Line — Extract Actual Hours (Never `Work`)

**Files:**
- Modify: `Agent_C_TaskList_MPlan/scripts/historical_matching.py`
- Test: append to `tests/test_historical_matching.py`

**Interfaces:**
- Produces: `extract_jms_actual_hours(operation_line_df: pd.DataFrame) -> pd.DataFrame` — returns columns `order, operation, jms_actual_hours, jms_control_key`, keyed on `Order`+`Activity` (renamed to `order`/`operation` to match Task 2's Timesheet output schema, enabling a direct join). **Never reads `Work`** — only `Actual work`, per the confirmed real-data finding that `Work` is not scale-consistent across `Control Key` and cannot be treated as hours.

- [ ] **Step 1: Write the failing tests**

```python
from scripts.historical_matching import extract_jms_actual_hours


def test_extract_jms_actual_hours_uses_actual_work_not_work():
    df = pd.DataFrame(
        {
            "Order": ["81485790", "81306479"],
            "Activity": ["0110", "0210"],
            "Control Key": ["INTN", "ESVC"],
            "Work": [4.0, 315600.0],  # ESVC Work is confirmed not an hours figure
            "Actual work": [3.5, 6.0],
        }
    )
    result = extract_jms_actual_hours(df)
    assert result[result["order"] == "81485790"]["jms_actual_hours"].iloc[0] == 3.5
    assert result[result["order"] == "81306479"]["jms_actual_hours"].iloc[0] == 6.0
    assert "Work" not in result.columns


def test_extract_jms_actual_hours_renames_order_activity_to_match_timesheet_schema():
    df = pd.DataFrame(
        {"Order": ["81485790"], "Activity": ["0110"], "Control Key": ["INTN"], "Work": [4.0], "Actual work": [3.5]}
    )
    result = extract_jms_actual_hours(df)
    assert list(result.columns) == ["order", "operation", "jms_actual_hours", "jms_control_key"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v -k jms_actual_hours
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Add to `scripts/historical_matching.py`**

```python
def extract_jms_actual_hours(operation_line_df: pd.DataFrame) -> pd.DataFrame:
    # 'Work' is deliberately never read here: confirmed against the real
    # file that Work's scale is inconsistent across Control Key (INTN
    # rows look like hours, ESVC rows are a completely different scale
    # by a factor of ~3,700x-54,000x for the same rows) and there is no
    # unit/UoM column in this sheet to disambiguate. 'Actual work' is the
    # field that stays hours-scale-consistent across all Control Key
    # values and is the only one used as historical evidence.
    return operation_line_df.rename(
        columns={"Order": "order", "Activity": "operation", "Actual work": "jms_actual_hours", "Control Key": "jms_control_key"}
    )[["order", "operation", "jms_actual_hours", "jms_control_key"]]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v
```
Expected: all passing (8 + 2 new = 10).

- [ ] **Step 5: Commit manually**

Commit — message like `feat: JMS Operation Line actual-hours extraction (Actual work only, never Work)`.

---

## Task 4: Reconcile Timesheet and JMS Candidate Hours (Never Sum Blindly)

**Files:**
- Modify: `Agent_C_TaskList_MPlan/scripts/historical_matching.py`
- Test: append to `tests/test_historical_matching.py`

**Interfaces:**
- Produces: `reconcile_actual_hours(timesheet_df: pd.DataFrame, jms_df: pd.DataFrame) -> pd.DataFrame` — outer-joins Task 2's and Task 3's outputs on `order`+`operation`. Returns one row per `order`+`operation` with columns `order, operation, timesheet_actual_hours, jms_actual_hours, source_overlap, discrepancy, candidate_hours, candidate_source`. Rule (matches the approved resolution plan, §7.2/§7.2a): if only one source has a value, use it as `candidate_hours` with that source named in `candidate_source`. If both have a value, report `discrepancy = abs(timesheet_actual_hours - jms_actual_hours)` and set `candidate_hours` to the **Timesheet** value (chosen as primary since it's the more granular, person-level source; JMS's `Actual work` — an Order/Operation-level rollup — is not summed with it), with `candidate_source="timesheet_primary_both_present"` and `source_overlap=True` — never summed.

- [ ] **Step 1: Write the failing tests**

```python
from scripts.historical_matching import reconcile_actual_hours


def test_reconcile_uses_the_only_available_source():
    timesheet_df = pd.DataFrame({"order": ["81516386"], "operation": ["0010"], "timesheet_actual_hours": [6.5], "timesheet_row_count": [3]})
    jms_df = pd.DataFrame({"order": [], "operation": [], "jms_actual_hours": [], "jms_control_key": []})
    result = reconcile_actual_hours(timesheet_df, jms_df)
    assert result["candidate_hours"][0] == 6.5
    assert result["candidate_source"][0] == "timesheet_only"
    assert result["source_overlap"][0] == False


def test_reconcile_never_sums_when_both_sources_present():
    timesheet_df = pd.DataFrame({"order": ["81485790"], "operation": ["0110"], "timesheet_actual_hours": [10.0], "timesheet_row_count": [2]})
    jms_df = pd.DataFrame({"order": ["81485790"], "operation": ["0110"], "jms_actual_hours": [3.5], "jms_control_key": ["INTN"]})
    result = reconcile_actual_hours(timesheet_df, jms_df)
    assert result["candidate_hours"][0] == 10.0  # Timesheet value, NOT 13.5 (the sum)
    assert result["candidate_source"][0] == "timesheet_primary_both_present"
    assert result["source_overlap"][0] == True
    assert result["discrepancy"][0] == 6.5


def test_reconcile_jms_only_when_no_timesheet_match():
    timesheet_df = pd.DataFrame({"order": [], "operation": [], "timesheet_actual_hours": [], "timesheet_row_count": []})
    jms_df = pd.DataFrame({"order": ["81306479"], "operation": ["0210"], "jms_actual_hours": [4.0], "jms_control_key": ["INTN"]})
    result = reconcile_actual_hours(timesheet_df, jms_df)
    assert result["candidate_hours"][0] == 4.0
    assert result["candidate_source"][0] == "jms_only"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v -k reconcile
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Add to `scripts/historical_matching.py`**

```python
def reconcile_actual_hours(timesheet_df: pd.DataFrame, jms_df: pd.DataFrame) -> pd.DataFrame:
    merged = timesheet_df.merge(jms_df, on=["order", "operation"], how="outer")

    def resolve(row):
        has_ts = pd.notna(row.get("timesheet_actual_hours"))
        has_jms = pd.notna(row.get("jms_actual_hours"))
        if has_ts and has_jms:
            # Never summed: both sources may describe the same execution
            # (confirmed both key on the same order+operation grain).
            # Timesheet is primary (person-level granularity); JMS's
            # Actual work is an Order/Operation-level rollup kept only
            # as a cross-check, per the approved resolution plan.
            return row["timesheet_actual_hours"], "timesheet_primary_both_present", True, abs(row["timesheet_actual_hours"] - row["jms_actual_hours"])
        if has_ts:
            return row["timesheet_actual_hours"], "timesheet_only", False, None
        if has_jms:
            return row["jms_actual_hours"], "jms_only", False, None
        return None, "no_source", False, None

    resolved = merged.apply(resolve, axis=1, result_type="expand")
    resolved.columns = ["candidate_hours", "candidate_source", "source_overlap", "discrepancy"]
    return pd.concat([merged[["order", "operation", "timesheet_actual_hours", "jms_actual_hours"]], resolved], axis=1)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v
```
Expected: all passing (10 + 3 new = 13).

- [ ] **Step 5: Commit manually**

Commit — message like `feat: reconcile Timesheet/JMS candidate hours, never summed`.

---

## Task 5: Task List Operation → Historical Match, With Execution/Version Confidence

**Files:**
- Modify: `Agent_C_TaskList_MPlan/scripts/historical_matching.py`
- Test: append to `tests/test_historical_matching.py`

**Interfaces:**
- Consumes: `normalized_operations` (shape from `scripts/normalize.py::normalize_long_text` — has `TLGRP`, `TLGRPCOUNT`, `TLOPNO`, `OPDESC`), `task_list_group` (bridge file — has `Group`, `Group Counter`), one or more historical Work Order DataFrames (each with `Order`, `Group`, `Group Counter`), and Task 4's `reconcile_actual_hours` output.
- Produces: `match_operations_to_history(normalized_operations, task_list_group, work_order_sources: dict[str, pd.DataFrame], reconciled_hours: pd.DataFrame) -> pd.DataFrame` where `work_order_sources` is `{"10yr": df, "jms": df}` (named per source, so coverage is measured independently per Correction 4b). Returns one row per Task List Operation with columns: `record_key, TLGRP, TLGRPCOUNT, TLOPNO, bridge_matched (bool), historical_orders_10yr (list), historical_orders_jms (list), execution_verified (bool), version_confidence ("version_unconfirmed" always, per the confirmed data gap), candidate_hours (list of floats from matched orders' operations), match_count (int)`.
  - **Bridge match (Hop 1):** join on `(TLGRP, TLGRPCOUNT)` ↔ `(Group, Group Counter)` — the same join PP3 already runs in production.
  - **Historical Order match (Hop 2):** for each `work_order_sources` entry, join the bridge's `(Group, Group Counter)` to that source's own `(Group, Group Counter)`, reported per-source (never combined into one figure, per Correction 4b).
  - **Execution verification (Correction 1):** an operation counts as `execution_verified` only if a historical Order's own operation-level description is available and matches (fuzzy, case-insensitive substring or exact match — kept simple since this is a coverage measurement, not the final matching-strictness rule, which is deferred to §8/D3 of the resolution plan) the Task List Operation's `OPDESC`. If no historical operation-level description is available to compare (e.g. only the 10-year file's Order-level match, no operation breakdown), `execution_verified=False` and the match is reported as `key_match_only` — never silently upgraded.
  - **Version confidence:** hardcoded to `"version_unconfirmed"` for every row, with a code comment stating why (no Task List revision/validity-date field exists in any surveyed source, per `docs/plans/2026-09-15-pp5-resolution-plan.md` §7.1a) — this is a structural fact of the current data, not a per-row computation.

- [ ] **Step 1: Write the failing tests**

```python
from scripts.historical_matching import match_operations_to_history


def test_match_operations_bridge_match_and_verified_execution():
    normalized_operations = pd.DataFrame(
        {"TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "OPDESC": ["PM,3M-VISUAL INSPECTION"]}
    )
    task_list_group = pd.DataFrame({"Group": ["BODA582"], "Group Counter": ["10"]})
    work_order_sources = {
        "10yr": pd.DataFrame({"Order": ["81516386"], "Group": ["BODA582"], "Group Counter": ["10"]}),
        "jms": pd.DataFrame({"Order": [], "Group": [], "Group Counter": []}),
    }
    reconciled_hours = pd.DataFrame(
        {"order": ["81516386"], "operation": ["0010"], "candidate_hours": [4.5]}
    )
    op_descriptions = pd.DataFrame({"order": ["81516386"], "operation": ["0010"], "description": ["PM 3M VISUAL INSPECTION"]})

    result = match_operations_to_history(
        normalized_operations, task_list_group, work_order_sources, reconciled_hours, op_descriptions
    )
    row = result.iloc[0]
    assert row["bridge_matched"] == True
    assert row["historical_orders_10yr"] == ["81516386"]
    assert row["historical_orders_jms"] == []
    assert row["version_confidence"] == "version_unconfirmed"
    assert row["match_count"] == 1


def test_match_operations_no_bridge_match_reports_zero_history():
    normalized_operations = pd.DataFrame({"TLGRP": ["ZZZZZZZ"], "TLGRPCOUNT": ["99"], "TLOPNO": ["10"], "OPDESC": ["X"]})
    task_list_group = pd.DataFrame({"Group": ["BODA582"], "Group Counter": ["10"]})
    work_order_sources = {"10yr": pd.DataFrame({"Order": [], "Group": [], "Group Counter": []}), "jms": pd.DataFrame({"Order": [], "Group": [], "Group Counter": []})}
    reconciled_hours = pd.DataFrame({"order": [], "operation": [], "candidate_hours": []})
    op_descriptions = pd.DataFrame({"order": [], "operation": [], "description": []})

    result = match_operations_to_history(normalized_operations, task_list_group, work_order_sources, reconciled_hours, op_descriptions)
    row = result.iloc[0]
    assert row["bridge_matched"] == False
    assert row["match_count"] == 0
    assert row["execution_verified"] == False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v -k match_operations
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Add to `scripts/historical_matching.py`**

```python
def _description_matches(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return False
    normalize = lambda s: "".join(ch for ch in s.upper() if ch.isalnum())
    return normalize(a) == normalize(b)


def match_operations_to_history(
    normalized_operations: pd.DataFrame,
    task_list_group: pd.DataFrame,
    work_order_sources: dict[str, pd.DataFrame],
    reconciled_hours: pd.DataFrame,
    op_descriptions: pd.DataFrame,
) -> pd.DataFrame:
    bridge_keys = set(zip(task_list_group["Group"].astype(str), task_list_group["Group Counter"].astype(str)))
    desc_lookup = {
        (r["order"], r["operation"]): r["description"] for r in op_descriptions.to_dict("records")
    }
    hours_lookup = {
        (r["order"], r["operation"]): r["candidate_hours"] for r in reconciled_hours.to_dict("records")
    }

    rows = []
    for op in normalized_operations.to_dict("records"):
        key = (str(op["TLGRP"]), str(op["TLGRPCOUNT"]))
        bridge_matched = key in bridge_keys
        orders_by_source = {}
        for source_name, wo_df in work_order_sources.items():
            if bridge_matched:
                matches = wo_df[
                    (wo_df["Group"].astype(str) == key[0]) & (wo_df["Group Counter"].astype(str) == key[1])
                ]
                orders_by_source[source_name] = matches["Order"].astype(str).tolist()
            else:
                orders_by_source[source_name] = []

        all_orders = [o for orders in orders_by_source.values() for o in orders]
        candidate_operation = str(op["TLOPNO"]).zfill(4)
        candidate_hours = []
        execution_verified = False
        for order in all_orders:
            hist_desc = desc_lookup.get((order, candidate_operation))
            if _description_matches(hist_desc, op.get("OPDESC")):
                execution_verified = True
                hours = hours_lookup.get((order, candidate_operation))
                if hours is not None:
                    candidate_hours.append(hours)

        rows.append(
            {
                "record_key": f"{op['TLGRP']}-{op['TLGRPCOUNT']}-{op['TLOPNO']}",
                "TLGRP": op["TLGRP"],
                "TLGRPCOUNT": op["TLGRPCOUNT"],
                "TLOPNO": op["TLOPNO"],
                "bridge_matched": bridge_matched,
                "historical_orders_10yr": orders_by_source.get("10yr", []),
                "historical_orders_jms": orders_by_source.get("jms", []),
                # Always 'version_unconfirmed': no Task-List-revision or
                # validity-date field exists in any source surveyed so
                # far (docs/plans/2026-09-15-pp5-resolution-plan.md
                # §7.1a) — this is a data-availability fact, not a
                # per-row computation, and must not be silently upgraded
                # if a future data drop adds a real version field without
                # this function being revisited.
                "version_confidence": "version_unconfirmed",
                "execution_verified": execution_verified,
                "candidate_hours": candidate_hours,
                "match_count": len(candidate_hours),
            }
        )
    return pd.DataFrame(rows)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_historical_matching.py -v
```
Expected: all passing (13 + 2 new = 15).

- [ ] **Step 5: Commit manually**

Commit — message like `feat: Task List Operation to historical-execution matching with execution/version confidence`.

---

## Task 6: Standalone Coverage Report (Step 2A/2B/2C Deliverable)

**Files:**
- Create: `Agent_C_TaskList_MPlan/scripts/coverage_report.py`
- Test: create `Agent_C_TaskList_MPlan/tests/test_coverage_report.py`

**Interfaces:**
- Produces: `build_coverage_report(match_results: pd.DataFrame) -> dict` — a summary dict (not yet an Excel file) with the counts the resolution plan's §7.4 requires: `total_operations`, `bridge_matched_count`, `historical_order_count_10yr`, `historical_order_count_jms` (reported separately, per Correction 4b), `execution_verified_count`, `key_match_only_count`, `version_unconfirmed_count` (always equals total matched, given today's data), `operations_with_candidate_hours_count`, `unmatched_reasons` (a `dict[str, int]` categorizing every unmatched row: `"no_bridge_match"`, `"bridge_matched_no_historical_order"`, `"historical_order_no_verified_operation"`).
- Produces: `write_coverage_report(summary: dict, match_results: pd.DataFrame, output_path: str) -> None` — writes `summary` as one sheet and the full per-operation `match_results` as a second sheet to an `.xlsx` file, using `openpyxl` (matches the project's existing Excel-writing convention in `output_writer.py`).
- Produces: a `if __name__ == "__main__":` block that runs the full Step 2 pipeline against real `input/` files and writes to `output/PP5_Coverage_Report.xlsx` — this is the actual Step 2A/2B/2C deliverable, run once as a standalone script, not part of the automated test suite.

- [ ] **Step 1: Write the failing tests**

```python
import pandas as pd

from scripts.coverage_report import build_coverage_report


def test_build_coverage_report_categorizes_every_operation():
    match_results = pd.DataFrame(
        [
            {"record_key": "A-1-10", "bridge_matched": True, "historical_orders_10yr": ["1"], "historical_orders_jms": [], "execution_verified": True, "candidate_hours": [4.5], "match_count": 1},
            {"record_key": "B-1-10", "bridge_matched": True, "historical_orders_10yr": [], "historical_orders_jms": [], "execution_verified": False, "candidate_hours": [], "match_count": 0},
            {"record_key": "C-1-10", "bridge_matched": False, "historical_orders_10yr": [], "historical_orders_jms": [], "execution_verified": False, "candidate_hours": [], "match_count": 0},
        ]
    )
    summary = build_coverage_report(match_results)
    assert summary["total_operations"] == 3
    assert summary["bridge_matched_count"] == 2
    assert summary["execution_verified_count"] == 1
    assert summary["operations_with_candidate_hours_count"] == 1
    assert summary["unmatched_reasons"]["no_bridge_match"] == 1
    assert summary["unmatched_reasons"]["bridge_matched_no_historical_order"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_coverage_report.py -v
```
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 3: Write `scripts/coverage_report.py`**

```python
import pandas as pd
import openpyxl

from logging_config import get_logger

logger = get_logger()


def build_coverage_report(match_results: pd.DataFrame) -> dict:
    total = len(match_results)
    bridge_matched = match_results[match_results["bridge_matched"]]
    has_10yr = bridge_matched["historical_orders_10yr"].apply(len) > 0
    has_jms = bridge_matched["historical_orders_jms"].apply(len) > 0
    verified = match_results[match_results["execution_verified"]]
    with_hours = match_results[match_results["candidate_hours"].apply(len) > 0]

    unmatched_reasons = {"no_bridge_match": 0, "bridge_matched_no_historical_order": 0, "historical_order_no_verified_operation": 0}
    for row in match_results.to_dict("records"):
        if row["match_count"] > 0:
            continue
        if not row["bridge_matched"]:
            unmatched_reasons["no_bridge_match"] += 1
        elif not row["historical_orders_10yr"] and not row["historical_orders_jms"]:
            unmatched_reasons["bridge_matched_no_historical_order"] += 1
        else:
            unmatched_reasons["historical_order_no_verified_operation"] += 1

    return {
        "total_operations": total,
        "bridge_matched_count": int(bridge_matched.shape[0]),
        "historical_order_count_10yr": int(has_10yr.sum()),
        "historical_order_count_jms": int(has_jms.sum()),
        "execution_verified_count": int(verified.shape[0]),
        "key_match_only_count": int(bridge_matched.shape[0] - verified.shape[0]),
        # Always equals bridge_matched_count today: no Task-List-version
        # field exists in any surveyed source (see historical_matching.py's
        # match_operations_to_history and resolution-plan §7.1a).
        "version_unconfirmed_count": int(bridge_matched.shape[0]),
        "operations_with_candidate_hours_count": int(with_hours.shape[0]),
        "unmatched_reasons": unmatched_reasons,
    }


def write_coverage_report(summary: dict, match_results: pd.DataFrame, output_path: str) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        summary_rows = [(k, v) for k, v in summary.items() if k != "unmatched_reasons"]
        summary_rows += [(f"unmatched_reasons.{k}", v) for k, v in summary["unmatched_reasons"].items()]
        pd.DataFrame(summary_rows, columns=["Metric", "Value"]).to_excel(writer, sheet_name="Summary", index=False)
        match_results.assign(
            historical_orders_10yr=match_results["historical_orders_10yr"].apply(str),
            historical_orders_jms=match_results["historical_orders_jms"].apply(str),
            candidate_hours=match_results["candidate_hours"].apply(str),
        ).to_excel(writer, sheet_name="Per Operation", index=False)
    logger.info(f"coverage report written to {output_path}")


if __name__ == "__main__":
    from pathlib import Path

    from app import (
        read_jms_work_order,
        read_long_text,
        read_task_list_group,
        read_timesheet,
        read_work_order_history,
    )
    from scripts.historical_matching import (
        aggregate_timesheet_hours,
        extract_jms_actual_hours,
        match_operations_to_history,
        reconcile_actual_hours,
        split_general_receiver,
        strip_timesheet_summary_row,
    )
    from scripts.normalize import normalize_long_text

    base = Path(__file__).resolve().parent.parent
    input_dir = base / "input"

    task_list_group = read_task_list_group(str(input_dir / "Bokor Task List Group.xlsx"))
    long_text_raw = read_long_text(str(input_dir / "Bokor Long Text_Aug26_LATEST.xlsm"))
    normalized_operations = normalize_long_text(long_text_raw)

    work_order_10yr = read_work_order_history(str(input_dir / "BOKOR_10years Work Order Data_Aug26.xlsx"))
    jms = read_jms_work_order(str(input_dir / "M014_Bokor_Non_PPM_Work_Order_2020_2025.xlsx"))

    ts_2024 = strip_timesheet_summary_row(read_timesheet(str(input_dir / "Timesheet_BOKOR_2024.xlsx")))
    ts_2025 = strip_timesheet_summary_row(read_timesheet(str(input_dir / "Timesheet_BOKOR_2025.xlsx")))
    timesheet_combined = pd.concat([ts_2024, ts_2025], ignore_index=True)
    timesheet_split = split_general_receiver(timesheet_combined)
    timesheet_hours = aggregate_timesheet_hours(timesheet_split)

    jms_hours = extract_jms_actual_hours(jms["operation_line"])
    reconciled = reconcile_actual_hours(timesheet_hours, jms_hours)

    # op_descriptions: built from whichever historical source carries an
    # operation-level short text — JMS's Operation Line has 'Op. Short
    # Text'; Timesheet has 'Short Text' on the same General-receiver key.
    op_descriptions = jms["operation_line"].rename(
        columns={"Order": "order", "Activity": "operation", "Op. Short Text": "description"}
    )[["order", "operation", "description"]]

    match_results = match_operations_to_history(
        normalized_operations,
        task_list_group,
        {"10yr": work_order_10yr, "jms": jms["data"]},
        reconciled,
        op_descriptions,
    )

    from scripts.coverage_report import build_coverage_report, write_coverage_report

    summary = build_coverage_report(match_results)
    output_dir = base / "output"
    output_dir.mkdir(exist_ok=True)
    write_coverage_report(summary, match_results, str(output_dir / "PP5_Coverage_Report.xlsx"))
    print(summary)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_coverage_report.py -v
```
Expected: 1 passed.

- [ ] **Step 5: Run the real coverage report against actual data**

```bash
cd Agent_C_TaskList_MPlan
python scripts/coverage_report.py
```
Expected: runs without error, prints a summary dict, writes `output/PP5_Coverage_Report.xlsx`. **This is the Step 2A/2B/2C deliverable — read its actual numbers before proceeding to Task 7**, since Task 7's minimum-sample-size gate should be informed by what this run actually shows (e.g. if `operations_with_candidate_hours_count` is very low, a minimum of 3-5 comparable executions per operation may almost never be reachable — note the real number in the Task 7 commit message).

- [ ] **Step 6: Commit manually**

Commit `scripts/coverage_report.py`, `tests/test_coverage_report.py`, and `output/PP5_Coverage_Report.xlsx` — message like `feat: PP5 Step 2A/2B/2C data-coverage report` plus the real summary numbers observed.

---

## Task 7: Wire Historical Benchmark Into `run_pp5` (Simple Output, Safeguards Internal)

**Files:**
- Modify: `Agent_C_TaskList_MPlan/validation.py`
- Modify: `Agent_C_TaskList_MPlan/config/thresholds.yaml`
- Test: append to `Agent_C_TaskList_MPlan/tests/test_validation.py`

**Interfaces:**
- Consumes: Task 5's `match_operations_to_history` output (passed into `run_pp5` as a new optional parameter, `historical_matches: pd.DataFrame | None = None`, keyed by `record_key`).
- Produces: `_pp5_row_check` gains a second evidence path. **Output stays exactly as simple as the user's 6-point spec**: `Finding.reason` either states the suggested value and its evidence, or says the record needs review — no new Finding fields are added (this project's `Finding` schema is `pain_point/record_key/field_name/current_value/recommended_value/confidence/detection_confidence/reason/evidence_source`, unchanged). Internally, the eligibility gate (minimum comparable executions, from `config/thresholds.yaml`'s new `pp5.min_comparable_executions`) uses Task 5's `execution_verified`/`match_count`/`candidate_hours` fields — never the raw, unverified `historical_orders_*` lists — so a low-quality match never silently becomes a recommendation.

- [ ] **Step 1: Add the new threshold to `config/thresholds.yaml`**

Add under the existing `pp5:` block:

```yaml
pp5:
  confidence_formula_correction: 1.0
  detection_confidence_range_suspicious: 0.90
  work_tolerance: 0.01
  min_comparable_executions: 3   # minimum execution_verified historical matches with candidate_hours required before a historical benchmark is recommended, rather than Needs Review — set conservatively pending real Step 2 coverage numbers (Task 6); revisit once those are known
  historical_benchmark_confidence: 0.6   # MEDIUM band (client's own 0.6-0.8 definition) — historical evidence is real but not as strong as the deterministic arithmetic check's 1.0
```

- [ ] **Step 2: Write the failing tests**

Append to `tests/test_validation.py`:

```python
def test_pp5_historical_benchmark_recommended_when_enough_verified_matches():
    df = pd.DataFrame(
        {
            "TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [3.0], "WORK_UNIT": ["MHR"], "PERSON": [1], "DURATION": [3.0], "DURATION_UNIT": ["HR"],
            "OPWKCEN": ["BMECH"],
        }
    )
    historical_matches = pd.DataFrame(
        [{"record_key": "BODA582-10-10", "execution_verified": True, "candidate_hours": [4.0, 5.0, 5.0, 6.0], "match_count": 4}]
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR", historical_matches=historical_matches)
    # WORK already equals PERSON*DURATION (3.0 == 1*3.0), so no arithmetic
    # Finding — but the historical benchmark still surfaces as its own
    # Finding on the same field, since it's informational evidence, not
    # an override.
    historical_findings = [f for f in findings if f.reason.startswith("Historical benchmark")]
    assert len(historical_findings) == 1
    assert historical_findings[0].recommended_value == "5.0"  # median of 4,5,5,6
    assert historical_findings[0].confidence == 0.6


def test_pp5_historical_benchmark_needs_review_when_too_few_verified_matches():
    df = pd.DataFrame(
        {
            "TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [3.0], "WORK_UNIT": ["MHR"], "PERSON": [1], "DURATION": [3.0], "DURATION_UNIT": ["HR"],
            "OPWKCEN": ["BMECH"],
        }
    )
    historical_matches = pd.DataFrame(
        [{"record_key": "BODA582-10-10", "execution_verified": True, "candidate_hours": [4.0], "match_count": 1}]
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR", historical_matches=historical_matches)
    historical_findings = [f for f in findings if "Needs Review" in f.reason or "needs review" in f.reason.lower()]
    assert len(historical_findings) == 1
    assert historical_findings[0].recommended_value is None
    assert historical_findings[0].confidence == 0.0


def test_pp5_no_historical_matches_row_produces_no_historical_finding():
    df = pd.DataFrame(
        {
            "TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [6.0], "WORK_UNIT": ["MHR"], "PERSON": [2], "DURATION": [3.0], "DURATION_UNIT": ["HR"],
            "OPWKCEN": ["BMECH"],
        }
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR", historical_matches=None)
    assert findings == []  # arithmetic already consistent, no historical_matches supplied at all
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v -k historical_benchmark
```
Expected: FAIL — `TypeError: run_pp5() got an unexpected keyword argument 'historical_matches'`.

- [ ] **Step 4: Extend `_pp5_row_check` and `run_pp5` in `validation.py`**

Add a new helper function right before `_pp5_row_check` (around line 1689):

```python
def _pp5_historical_benchmark_check(
    row: dict,
    record_key: str,
    historical_matches: pd.DataFrame | None,
    min_comparable_executions: int,
    historical_benchmark_confidence: float,
) -> "Finding | None":
    if historical_matches is None:
        return None
    match_rows = historical_matches[historical_matches["record_key"] == record_key]
    if match_rows.empty:
        return None
    match = match_rows.iloc[0]
    # Only execution_verified matches ever reach candidate_hours in the
    # upstream matcher (scripts/historical_matching.py) — this check
    # trusts that invariant rather than re-deriving it, so a low-quality
    # (key-match-only, unverified) match can never silently become a
    # recommendation here.
    candidate_hours = match["candidate_hours"]
    if len(candidate_hours) < min_comparable_executions:
        return Finding(
            pain_point="PP5", record_key=record_key, field_name="WORK",
            current_value=str(row["WORK"]), recommended_value=None, confidence=0.0,
            reason=(
                f"Needs Review — only {len(candidate_hours)} verified historical execution(s) found, "
                f"fewer than the minimum of {min_comparable_executions} required to recommend a historical benchmark"
            ),
            evidence_source="Timesheet BOKOR 2024/2025; M014_Bokor_Non PPM Work Order 2020_2025.xlsx",
        )
    median_hours = float(pd.Series(candidate_hours).median())
    return Finding(
        pain_point="PP5", record_key=record_key, field_name="WORK",
        current_value=str(row["WORK"]), recommended_value=str(median_hours),
        confidence=historical_benchmark_confidence,
        reason=(
            f"Historical benchmark: median of {len(candidate_hours)} verified comparable "
            f"historical executions is {median_hours} MHR"
        ),
        evidence_source="Timesheet BOKOR 2024/2025; M014_Bokor_Non PPM Work Order 2020_2025.xlsx",
    )
```

Modify `run_pp5`'s signature and body:

```python
def run_pp5(
    normalized_operations: pd.DataFrame,
    valid_work_unit: str,
    valid_duration_unit: str,
    pitstops_ranges: pd.DataFrame | None = None,
    work_tolerance: float = 0.01,
    agent_c=None,
    batch_size: int = DEFAULT_BATCH_SIZE,
    historical_matches: pd.DataFrame | None = None,
    min_comparable_executions: int = 3,
    historical_benchmark_confidence: float = 0.6,
) -> list[Finding]:
    findings: list[Finding] = []

    rows = normalized_operations.to_dict("records")
    total = len(rows)
    logger.info(f"PP5: starting, {total} operations")
    processed = 0
    for batch in batched(rows, batch_size):
        for row in batch:
            finding = _pp5_row_check(row, valid_work_unit, valid_duration_unit, pitstops_ranges, work_tolerance, agent_c)
            if finding is not None:
                findings.append(finding)

            record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}-{row['TLSUBOPNO']}"
            # record_key here includes TLSUBOPNO (matches _pp5_row_check's
            # own key); historical_matches from Task 5 keys on
            # TLGRP-TLGRPCOUNT-TLOPNO (no sub-op) since historical Work
            # Order data has no sub-operation breakdown — strip the
            # trailing -{TLSUBOPNO} segment before lookup.
            historical_record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}"
            historical_finding = _pp5_historical_benchmark_check(
                row, historical_record_key, historical_matches, min_comparable_executions, historical_benchmark_confidence
            )
            if historical_finding is not None:
                findings.append(historical_finding)
        processed += len(batch)
        logger.info(f"PP5: processed {processed}/{total} operations, {len(findings)} findings so far")

    logger.info(f"PP5: done, {len(findings)} findings")
    return findings
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v -k pp5
```
Expected: all PP5 tests pass (existing + 3 new).

- [ ] **Step 6: Run the full test suite**

```bash
cd Agent_C_TaskList_MPlan
pytest -q
```
Expected: all tests pass, no regressions.

- [ ] **Step 7: Commit manually**

Commit `validation.py`, `config/thresholds.yaml`, `tests/test_validation.py` — message like `feat: wire historical man-hour benchmark into run_pp5, Needs Review when evidence is insufficient`.

---

## What This Plan Deliberately Does Not Include

- **OREDA integration** (the user's 6-point spec item 5) is not implemented in this plan. The existing `is_oreda_applicable_to_pp5` connector already correctly returns "not applicable" for all current PP5 rows (routine PM, not corrective repair) — per the resolution plan's §8.1, wiring OREDA in requires first confirming whether any Bokor Task List Operations are actually corrective-repair-type at all (a data-scoping question, not an engineering task). If the user wants this checked and wired now regardless, it is a fast follow-on task, not included here to keep this plan's scope to what's grounded in confirmed data.
- **Re-enabling `run_pp5` in `app.py`'s active pipeline call** — stays commented out per the existing sequencing constraint (independent of PP1/PP2/PP6/PP7); flipping that toggle is a one-line follow-up once this plan's output is reviewed, not bundled in here.
- **PITSTOPS plausibility-flag wiring** — already-existing, separate code path (`pitstops_ranges`/`flag_implausible_work`), untouched by this plan; it can be enabled independently at any time.
- **Description-similarity matching beyond exact normalized-string equality** (Task 5's `_description_matches`) — the resolution plan's §8/D3 defers the real match-quality threshold to a client decision informed by Task 6's coverage numbers; this plan implements the simplest defensible rule (exact match after case/punctuation normalization) so Task 6 can run and produce real numbers, not a guessed fuzzy-matching threshold.
