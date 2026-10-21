# PP5 Three-Lane Evidence Reconciliation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure PP5's man-hour recommendation logic so three independent evidence lanes — Historical (Work Order + Timesheet), Tasklist/Worklist (PITSTOPS), and OREDA — each produce their own candidate MHR + reliability judgment, which a reconciliation step combines into one final suggested value (never a naive average) or `Needs Review`. Also add Task-List-level WORK summation from its operations' recommended values. Per direction: recommendations happen at the Operation grain; Task List totals are a derived sum, never computed independently.

**Architecture:** A new module, `scripts/evidence_reconciliation.py`, holds three lane functions (`historical_lane`, `tasklist_worklist_lane`, `oreda_lane`) each returning a uniform `LaneResult` shape (`available: bool`, `suggested_mhr: float | None`, `confidence: float`, `reason: str`), plus `reconcile_lanes(lane_results) -> ReconciliationResult` that decides the final suggested value from whichever lanes are available and reliable, and `sum_task_list_work(operation_findings) -> pd.DataFrame` for the Task-List-level rollup. `validation.py`'s `_pp5_historical_benchmark_check` is replaced by a new `_pp5_evidence_reconciliation_check` that calls `reconcile_lanes` and emits exactly one Finding per operation (never one Finding per lane) — matching the existing Finding schema and the project's "one row per pain point per field" output convention. The existing arithmetic check (`_pp5_row_check`'s completeness/unit/`WORK=PERSON×DURATION` logic) is untouched.

**Tech Stack:** Python, `pandas` (matches the rest of `validation.py`/`app.py`), no new dependencies.

## Global Constraints

- **No averaging.** `reconcile_lanes` must never compute a mean/average across available lane values as its primary method — each lane's applicability/reliability is checked first (per its own gate), and only lanes that pass contribute to the final value. If multiple lanes pass and their values are close, the reconciliation may report a combined value (e.g. weighted by confidence, or the highest-confidence lane's value) — but the exact combination rule is a decision this plan documents explicitly per lane, not an unstated average.
- **Confidence is a 0.0-1.0 float**, `Recommended_Value=None` iff `confidence==0.0` — enforced by `Finding.enforce_confidence_rule`, unchanged.
- **No invented values.** Confirmed real-data facts, not to be silently worked around:
  - PITSTOPS `Tasklist.xlsx`/`Worklist.xlsx` have no crew-size/headcount field. `Dur (Hrs)` is elapsed clock duration (verified: matches `PlanStart`/`PlanFinish` gaps, e.g. 2.5 hrs for an 08:30–11:00 window), not total labour effort. **The Tasklist/Worklist lane must report `available=False` with an explicit reason — it must never multiply `Dur (Hrs)` by an assumed crew size to fabricate an MHR.**
  - No Bokor Task List Operation is tagged corrective/repair-type (verified: `CTRLKEY` is `INTN` for 2,868/2,870 operations, `TLTYPE` is uniformly `A`, `STRATEGY` codes are all routine-PM-shaped — no repair/breakdown marker exists anywhere in the surveyed Task List data). **The OREDA lane's Repair Activity Check must correctly return `available=False` for every current Bokor operation** — this is expected, correct behavior given the data, not a bug to route around.
  - Historical lane's `execution_verified` is currently 0 for all operations (per the coverage report — no historical source has an operation-level description comparable to Task List `OPDESC`) — the historical lane will currently also report `available=False` for most/all rows. This is unchanged from the existing behavior; this plan restructures *how* that unavailability is reported (as one lane among three, not the only story), not the underlying data gap.
- **One Finding per operation for PP5's evidence-reconciliation path**, not one per lane — per-lane detail goes in the `reason`/`evidence_source` text, matching the existing single-Finding-per-check convention used throughout `validation.py`.
- **Task List-level summation is additive, not a new source of truth**: it sums each operation's *already-decided* recommended (or current, if no recommendation) WORK value — it never re-derives or overrides an operation-level decision.
- **Code style**: simple, modular, meaningful names, no placeholder logic, one-line comments only where the WHY is non-obvious — matches the rest of this project.
- **Testing**: `pytest`, synthetic DataFrames built inline, no dependency on real Excel files being present for unit tests (matches existing convention). The real coverage-style verification (does this lane actually fire correctly against real Bokor data) happens as a manual `app.py`/coverage-script run reported back, not as an automated test — consistent with how `scripts/coverage_report.py` (Step 2A/2B/2C) was verified earlier.

---

## Source Facts Reference (verified directly — use these, do not re-derive)

| Fact | Verified against | Implication |
|---|---|---|
| `Tasklist.xlsx` real columns: `..., 'Dur (Hrs)', 'Weightage', ...` — no crew/headcount/person-count column anywhere | `input/pitstops/BOBELA_TA_2024_Tasklist.xlsx`, direct read | Tasklist/Worklist lane cannot compute MHR from duration alone |
| Sample row: `PlanStart=2024-08-31 08:30`, `PlanFinish=2024-08-31 11:00`, `Dur (Hrs)=2.5` | Same file | Confirms `Dur (Hrs)` is elapsed clock time, matching the plan-window gap exactly — not labour-hours |
| `Worklist.xlsx` real columns: `..., 'Total Contractor', 'Main Contractor', ..., 'WorkOrder', ...` — no crew-size/MHR field; `WorkOrder` 100% empty in both real TA-window extracts | `input/pitstops/BOBELA_TA_2024/2026` (via prior session's file inspection) | Confirms Worklist cannot supply an MHR value or a Work Order join |
| Bokor Long Text `CTRLKEY`: `INTN`=2,868 rows, `SBOP`=2 rows. `TLTYPE`: `A`=2,870 rows (all). `STRATEGY`: `PCSB51/52/25/24/21/53/31/27/23/22` — all routine-maintenance-shaped codes, no repair/breakdown code | `input/Bokor Long Text_Aug26_LATEST.xlsm`, via `read_long_text`+`normalize_long_text` | Confirms no Bokor Task List Operation is identifiable as corrective/repair-type — OREDA lane will report `available=False` for all rows today |
| `OREDA.db`: single table `oreda_data`, `query_oreda_categories`/`query_oreda_repair_benchmark` already built and tested (fixed 2026-09-16) | `evidence_connectors/oreda_connector.py` | OREDA lane can call these directly once given an `item`/`failure_mode` to look up — but has no signal to decide *which* `item` an Operation maps to, since no repair-type tagging exists (see above) |
| PP5 coverage report (`output/PP5_Coverage_Report.xlsx`, generated 2026-09-16): `execution_verified_count=0` of 2,871 operations; `known_limitation` states neither historical source has an operation-level description comparable to `OPDESC` | `scripts/coverage_report.py` real run | Historical lane's `available=False` outcome for most/all rows is a known, already-documented data gap, not new |

---

## File Structure

```
Agent_C_TaskList_MPlan/
├── scripts/
│   └── evidence_reconciliation.py     # NEW — 3 lane functions, reconcile_lanes, sum_task_list_work
├── validation.py                       # MODIFIED — _pp5_historical_benchmark_check replaced by
│                                        #   _pp5_evidence_reconciliation_check; run_pp5 signature updated
├── config/
│   └── thresholds.yaml                 # MODIFIED — add pp5 lane-reliability thresholds
└── tests/
    ├── test_evidence_reconciliation.py # NEW
    └── test_validation.py              # MODIFIED — replace historical-benchmark PP5 tests with
                                         #   evidence-reconciliation-check tests
```

**Rationale:** `evidence_reconciliation.py` is a new file, not folded into `historical_matching.py` or `validation.py`, because it has a distinct responsibility (combining evidence across *three* sources including two — PITSTOPS, OREDA — that `historical_matching.py` never touches) and is independently testable/reusable, matching this project's existing pattern of one file per distinct concern (`historical_matching.py` for the historical join/aggregation, `oreda_connector.py`/`pitstops_connector.py` for their respective raw-data access, `validation.py` for Finding-emission only).

---

## Task 1: Lane Result Shape and the Historical Lane

**Files:**
- Create: `Agent_C_TaskList_MPlan/scripts/evidence_reconciliation.py`
- Create: `Agent_C_TaskList_MPlan/tests/test_evidence_reconciliation.py`

**Interfaces:**
- Produces: `LaneResult` — a small `dataclass` (or plain dict, see Step 3) with fields `available: bool`, `suggested_mhr: float | None`, `confidence: float`, `reason: str`, `source: str`.
- Produces: `historical_lane(record_key: str, historical_matches: pd.DataFrame | None, min_comparable_executions: int, base_confidence: float) -> LaneResult` — wraps the exact logic already in `_pp5_historical_benchmark_check` (median of `candidate_hours` when `len(candidate_hours) >= min_comparable_executions`, else unavailable), re-expressed as a `LaneResult` instead of a `Finding`.

- [ ] **Step 1: Write the failing tests**

```python
import pandas as pd

from scripts.evidence_reconciliation import LaneResult, historical_lane


def test_historical_lane_available_with_enough_verified_matches():
    historical_matches = pd.DataFrame(
        [{"record_key": "BODA582-10-10", "execution_verified": True, "candidate_hours": [4.0, 5.0, 5.0, 6.0], "match_count": 4}]
    )
    result = historical_lane("BODA582-10-10", historical_matches, min_comparable_executions=3, base_confidence=0.6)
    assert result.available is True
    assert result.suggested_mhr == 5.0
    assert result.confidence == 0.6
    assert "4" in result.reason


def test_historical_lane_unavailable_with_too_few_matches():
    historical_matches = pd.DataFrame(
        [{"record_key": "BODA582-10-10", "execution_verified": True, "candidate_hours": [4.0], "match_count": 1}]
    )
    result = historical_lane("BODA582-10-10", historical_matches, min_comparable_executions=3, base_confidence=0.6)
    assert result.available is False
    assert result.suggested_mhr is None
    assert result.confidence == 0.0


def test_historical_lane_unavailable_when_no_match_data_supplied():
    result = historical_lane("BODA582-10-10", None, min_comparable_executions=3, base_confidence=0.6)
    assert result.available is False


def test_historical_lane_unavailable_when_record_key_not_present():
    historical_matches = pd.DataFrame(
        [{"record_key": "OTHER-1-1", "execution_verified": True, "candidate_hours": [4.0, 5.0, 6.0], "match_count": 3}]
    )
    result = historical_lane("BODA582-10-10", historical_matches, min_comparable_executions=3, base_confidence=0.6)
    assert result.available is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v
```
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts.evidence_reconciliation'`.

- [ ] **Step 3: Write `scripts/evidence_reconciliation.py`** (start of file — historical lane only; other lanes added in later tasks)

```python
from dataclasses import dataclass

import pandas as pd


@dataclass
class LaneResult:
    available: bool
    suggested_mhr: float | None
    confidence: float
    reason: str
    source: str


def historical_lane(
    record_key: str,
    historical_matches: pd.DataFrame | None,
    min_comparable_executions: int,
    base_confidence: float,
) -> LaneResult:
    source = "Timesheet BOKOR 2024/2025; M014_Bokor_Non PPM Work Order 2020_2025.xlsx"
    if historical_matches is None:
        return LaneResult(False, None, 0.0, "No historical match data supplied", source)
    match_rows = historical_matches[historical_matches["record_key"] == record_key]
    if match_rows.empty:
        return LaneResult(False, None, 0.0, "No historical match found for this operation", source)
    match = match_rows.iloc[0]
    # Only execution_verified matches ever reach candidate_hours in the
    # upstream matcher (scripts/historical_matching.py) — this lane
    # trusts that invariant rather than re-deriving it.
    candidate_hours = match["candidate_hours"]
    if len(candidate_hours) < min_comparable_executions:
        return LaneResult(
            False, None, 0.0,
            f"Only {len(candidate_hours)} verified historical execution(s) found, "
            f"fewer than the minimum of {min_comparable_executions}",
            source,
        )
    median_hours = float(pd.Series(candidate_hours).median())
    return LaneResult(
        True, median_hours, base_confidence,
        f"Median of {len(candidate_hours)} verified comparable historical executions is {median_hours} MHR",
        source,
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v
```
Expected: 4 passed.

- [ ] **Step 5: Commit manually**

Commit `scripts/evidence_reconciliation.py`, `tests/test_evidence_reconciliation.py` — message like `feat: LaneResult shape and historical evidence lane`.

---

## Task 2: Tasklist/Worklist Lane — Correctly Reports Unavailable

**Files:**
- Modify: `Agent_C_TaskList_MPlan/scripts/evidence_reconciliation.py`
- Test: append to `tests/test_evidence_reconciliation.py`

**Interfaces:**
- Produces: `tasklist_worklist_lane(opwkcen: str | None, pitstops_ranges: pd.DataFrame | None) -> LaneResult` — **always returns `available=False`** with an explicit reason naming the real data gap (no crew-size field to convert `Dur (Hrs)` to MHR), regardless of input, per the confirmed real-data finding in this plan's Global Constraints. This function exists (rather than being omitted) so the reconciliation step has a uniform 3-lane shape to iterate over, and so the *reason* for unavailability is visible in the eventual Finding's evidence text — not silently absent.

- [ ] **Step 1: Write the failing tests**

```python
from scripts.evidence_reconciliation import tasklist_worklist_lane


def test_tasklist_worklist_lane_always_unavailable_no_crew_size_data():
    # Real-data fact (see plan's Source Facts Reference): neither
    # Tasklist.xlsx nor Worklist.xlsx has a crew-size/headcount column;
    # Dur (Hrs) is elapsed clock duration, not labour-hours. This lane
    # must never guess a crew size to fabricate an MHR.
    result = tasklist_worklist_lane(opwkcen="BMECH", pitstops_ranges=None)
    assert result.available is False
    assert result.suggested_mhr is None
    assert "crew" in result.reason.lower() or "duration" in result.reason.lower()


def test_tasklist_worklist_lane_unavailable_even_with_ranges_supplied():
    import pandas as pd

    ranges = pd.DataFrame({"Discipline": ["Static"], "n": [10], "max_hrs": [60.0]})
    result = tasklist_worklist_lane(opwkcen="BMECH", pitstops_ranges=ranges)
    assert result.available is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v -k tasklist_worklist
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Add to `scripts/evidence_reconciliation.py`**

```python
def tasklist_worklist_lane(opwkcen: str | None, pitstops_ranges: pd.DataFrame | None) -> LaneResult:
    # Always unavailable today: verified directly against the real
    # PITSTOPS Tasklist.xlsx/Worklist.xlsx files — neither carries a
    # crew-size/headcount column, and Dur (Hrs) is elapsed clock
    # duration (confirmed: matches PlanStart/PlanFinish gaps exactly),
    # not total labour effort. Multiplying duration by an assumed crew
    # size would be an invented value, which this project's rules
    # prohibit. This function returns a structured, visible
    # "unavailable" result (rather than being omitted) so the
    # reconciliation step and the eventual Finding's evidence text both
    # show this lane was checked and why it didn't contribute — not
    # silently absent. Revisit only if a crew-size field is ever added
    # to a future PITSTOPS extract.
    return LaneResult(
        False, None, 0.0,
        "Tasklist/Worklist has no crew-size field to convert Dur (Hrs) elapsed duration into MHR",
        "PITSTOPS Tasklist.xlsx/Worklist.xlsx",
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v
```
Expected: 6 passed.

- [ ] **Step 5: Commit manually**

Commit — message like `feat: Tasklist/Worklist evidence lane (correctly always unavailable, no crew-size data)`.

---

## Task 3: OREDA Lane — Repair Activity Gate

**Files:**
- Modify: `Agent_C_TaskList_MPlan/scripts/evidence_reconciliation.py`
- Test: append to `tests/test_evidence_reconciliation.py`

**Interfaces:**
- Produces: `is_repair_type_operation(row: dict) -> bool` — the Repair Activity Check from the resolution plan's §8.1. Returns `True` only if the operation's `CTRLKEY`/`STRATEGY` indicate corrective/breakdown work, not routine PM. Per the confirmed real-data finding, this returns `False` for every current Bokor operation (`CTRLKEY` is always `INTN`, an internal-planned-maintenance key; none of the real `STRATEGY` codes are breakdown/corrective-shaped) — implemented as an actual rule (not a hardcoded `False`), so it activates correctly if a future data drop ever includes corrective work.
- Produces: `oreda_lane(row: dict, oreda_db_path: str, item_hint: str | None = None) -> LaneResult` — calls `is_repair_type_operation` first; if `False`, returns unavailable immediately (never queries the database). If `True` and `item_hint` is provided, calls `evidence_connectors.oreda_connector.query_oreda_repair_benchmark`. Since no current Bokor operation is repair-type, and no field maps an Operation to an OREDA `item` taxonomy category today, `item_hint` defaults to `None` and the lane reports unavailable with a reason distinguishing "not a repair activity" from "no equipment-taxonomy mapping available" — two different gaps, not conflated into one message.

- [ ] **Step 1: Write the failing tests**

```python
from scripts.evidence_reconciliation import is_repair_type_operation, oreda_lane


def test_is_repair_type_operation_false_for_routine_pm_ctrlkey():
    # Real Bokor data: CTRLKEY='INTN' for 2,868/2,870 operations — an
    # internal planned-maintenance control key, not corrective/breakdown.
    row = {"CTRLKEY": "INTN", "STRATEGY": "PCSB51"}
    assert is_repair_type_operation(row) is False


def test_is_repair_type_operation_true_for_breakdown_ctrlkey():
    row = {"CTRLKEY": "PM03", "STRATEGY": "BREAKDOWN"}
    assert is_repair_type_operation(row) is True


def test_oreda_lane_unavailable_for_routine_pm_operation(tmp_path):
    row = {"CTRLKEY": "INTN", "STRATEGY": "PCSB51"}
    result = oreda_lane(row, oreda_db_path=str(tmp_path / "unused.db"))
    assert result.available is False
    assert "not" in result.reason.lower()
    assert "repair" in result.reason.lower()


def test_oreda_lane_unavailable_for_repair_operation_with_no_taxonomy_mapping(tmp_path):
    row = {"CTRLKEY": "PM03", "STRATEGY": "BREAKDOWN"}
    result = oreda_lane(row, oreda_db_path=str(tmp_path / "unused.db"), item_hint=None)
    assert result.available is False
    assert "taxonomy" in result.reason.lower() or "mapping" in result.reason.lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v -k "repair_type or oreda_lane"
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Add to `scripts/evidence_reconciliation.py`**

```python
# Real Bokor Task List data (verified 2026-09-16): CTRLKEY is 'INTN'
# (internal/planned-maintenance) for 2,868/2,870 operations, 'SBOP' for
# the remaining 2 — neither is a corrective/breakdown control key.
# STRATEGY codes (PCSB21/22/23/24/25/27/31/51/52/53) are all
# routine-maintenance-shaped, not breakdown codes. This set names the
# actual corrective/breakdown indicators this check would recognize,
# so the rule is real and re-evaluable against future data, not a
# hardcoded False.
BREAKDOWN_CTRLKEYS = {"PM03", "PM04"}
BREAKDOWN_STRATEGY_KEYWORDS = ("BREAKDOWN", "CORRECTIVE", "REPAIR")


def is_repair_type_operation(row: dict) -> bool:
    ctrlkey = str(row.get("CTRLKEY") or "")
    strategy = str(row.get("STRATEGY") or "").upper()
    if ctrlkey in BREAKDOWN_CTRLKEYS:
        return True
    return any(keyword in strategy for keyword in BREAKDOWN_STRATEGY_KEYWORDS)


def oreda_lane(row: dict, oreda_db_path: str, item_hint: str | None = None) -> LaneResult:
    source = "OREDA.db"
    if not is_repair_type_operation(row):
        return LaneResult(
            False, None, 0.0,
            "Operation is not a corrective/repair activity (routine planned maintenance, "
            "CTRLKEY/STRATEGY do not indicate breakdown work) — OREDA repair benchmarks do not apply",
            source,
        )
    if item_hint is None:
        return LaneResult(
            False, None, 0.0,
            "Operation is repair-type but no OREDA equipment-taxonomy mapping is available for it",
            source,
        )
    from evidence_connectors.oreda_connector import query_oreda_repair_benchmark

    benchmark = query_oreda_repair_benchmark(oreda_db_path, item=item_hint, failure_mode="Breakdown")
    if benchmark is None:
        return LaneResult(
            False, None, 0.0,
            f"No OREDA repair benchmark found for item '{item_hint}'",
            source,
        )
    return LaneResult(
        True, benchmark["manhour_repair_mean"], 0.5,
        f"OREDA repair benchmark for '{item_hint}': mean {benchmark['manhour_repair_mean']} MHR "
        f"(range {benchmark['manhour_repair_min']}-{benchmark['manhour_repair_max']}, source p.{benchmark['source_page']})",
        source,
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v
```
Expected: 10 passed.

- [ ] **Step 5: Commit manually**

Commit — message like `feat: OREDA evidence lane with Repair Activity Check gate`.

---

## Task 4: Reconciliation — Combine Lanes Without Averaging

**Files:**
- Modify: `Agent_C_TaskList_MPlan/scripts/evidence_reconciliation.py`
- Test: append to `tests/test_evidence_reconciliation.py`

**Interfaces:**
- Produces: `ReconciliationResult` — `dataclass` with `suggested_mhr: float | None`, `confidence: float`, `status: str` (one of `"RECOMMENDED"`, `"NEEDS_REVIEW"`, `"CONFLICT"`), `evidence: str` (a combined, human-readable summary of every lane's outcome, always including unavailable lanes with their reason — never silently dropping a lane from the evidence text).
- Produces: `reconcile_lanes(lanes: dict[str, LaneResult]) -> ReconciliationResult`, where `lanes` keys are `"historical"`, `"tasklist_worklist"`, `"oreda"`.
  - **Rule (per direction, "not simply average"):** collect only `available=True` lanes. If zero are available → `NEEDS_REVIEW`, `suggested_mhr=None`, `confidence=0.0`. If exactly one is available → use its value and confidence directly (`RECOMMENDED`). If two or more are available: compare their values — if all agree within a tolerance (10% of the largest value, since the plan doesn't currently have a client-specified tolerance and this needs to be revisited once real multi-lane data exists — see Task 4 Decision Note below), use the **highest-confidence** available lane's value as the suggested MHR (never a mean/average across lanes) and status `RECOMMENDED`, with the evidence text showing all agreeing values. If they disagree beyond tolerance, status is `CONFLICT` (not `RECOMMENDED`, not silently picking one), `suggested_mhr=None`, `confidence=0.0`, and the evidence text names every lane's conflicting value so a reviewer sees the disagreement directly.

- [ ] **Step 1: Write the failing tests**

```python
from scripts.evidence_reconciliation import LaneResult, ReconciliationResult, reconcile_lanes


def test_reconcile_needs_review_when_no_lane_available():
    lanes = {
        "historical": LaneResult(False, None, 0.0, "no data", "src1"),
        "tasklist_worklist": LaneResult(False, None, 0.0, "no crew size", "src2"),
        "oreda": LaneResult(False, None, 0.0, "not repair type", "src3"),
    }
    result = reconcile_lanes(lanes)
    assert result.status == "NEEDS_REVIEW"
    assert result.suggested_mhr is None
    assert result.confidence == 0.0
    assert "no data" in result.evidence
    assert "no crew size" in result.evidence
    assert "not repair type" in result.evidence


def test_reconcile_uses_single_available_lane_directly():
    lanes = {
        "historical": LaneResult(True, 5.0, 0.6, "median of 4 executions", "src1"),
        "tasklist_worklist": LaneResult(False, None, 0.0, "no crew size", "src2"),
        "oreda": LaneResult(False, None, 0.0, "not repair type", "src3"),
    }
    result = reconcile_lanes(lanes)
    assert result.status == "RECOMMENDED"
    assert result.suggested_mhr == 5.0
    assert result.confidence == 0.6


def test_reconcile_agreeing_lanes_uses_highest_confidence_value_not_average():
    lanes = {
        "historical": LaneResult(True, 8.0, 0.6, "median of 4 executions", "src1"),
        "tasklist_worklist": LaneResult(True, 8.3, 0.4, "comparable duration", "src2"),
        "oreda": LaneResult(False, None, 0.0, "not repair type", "src3"),
    }
    result = reconcile_lanes(lanes)
    assert result.status == "RECOMMENDED"
    assert result.suggested_mhr == 8.0  # historical's value (higher confidence), NOT the average 8.15
    assert result.confidence == 0.6


def test_reconcile_disagreeing_lanes_yields_conflict_not_a_guess():
    lanes = {
        "historical": LaneResult(True, 8.0, 0.6, "median of 4 executions", "src1"),
        "tasklist_worklist": LaneResult(False, None, 0.0, "no crew size", "src2"),
        "oreda": LaneResult(True, 50.0, 0.5, "OREDA repair benchmark", "src3"),
    }
    result = reconcile_lanes(lanes)
    assert result.status == "CONFLICT"
    assert result.suggested_mhr is None
    assert result.confidence == 0.0
    assert "8.0" in result.evidence
    assert "50.0" in result.evidence
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v -k reconcile
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Add to `scripts/evidence_reconciliation.py`**

```python
AGREEMENT_TOLERANCE_FRACTION = 0.10  # of the largest agreeing value — see plan's Decision Note; revisit once real multi-lane data exists to inform this threshold, not a client-confirmed number yet


@dataclass
class ReconciliationResult:
    suggested_mhr: float | None
    confidence: float
    status: str
    evidence: str


def reconcile_lanes(lanes: dict[str, "LaneResult"]) -> ReconciliationResult:
    evidence_lines = [f"{name}: {lane.reason}" for name, lane in lanes.items()]
    evidence = "; ".join(evidence_lines)

    available = {name: lane for name, lane in lanes.items() if lane.available}
    if not available:
        return ReconciliationResult(None, 0.0, "NEEDS_REVIEW", evidence)

    if len(available) == 1:
        (only_lane,) = available.values()
        return ReconciliationResult(only_lane.suggested_mhr, only_lane.confidence, "RECOMMENDED", evidence)

    values = [lane.suggested_mhr for lane in available.values()]
    largest = max(values)
    agree = all(abs(v - largest) <= AGREEMENT_TOLERANCE_FRACTION * largest for v in values)
    if not agree:
        return ReconciliationResult(None, 0.0, "CONFLICT", evidence)

    # Agreeing lanes: use the highest-confidence lane's own value — never
    # an average across lanes, per direction ("It should not simply
    # average 8, 9 and 10").
    best_lane = max(available.values(), key=lambda lane: lane.confidence)
    return ReconciliationResult(best_lane.suggested_mhr, best_lane.confidence, "RECOMMENDED", evidence)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v
```
Expected: 14 passed.

- [ ] **Step 5: Commit manually**

Commit — message like `feat: reconcile_lanes — combine evidence without averaging, CONFLICT status for disagreement`.

**Decision Note (surface to the user, do not silently resolve differently later):** the 10%-agreement tolerance and "use highest-confidence lane's value when lanes agree" rule are both this plan's own reasonable defaults, not values the client has confirmed. Once real multi-lane data exists (i.e., once the historical/PITSTOPS/OREDA gaps close enough for more than one lane to be available on the same operation), these numbers should be revisited with the client rather than assumed permanent.

---

## Task 5: Wire Reconciliation Into `run_pp5`

**Files:**
- Modify: `Agent_C_TaskList_MPlan/validation.py`
- Modify: `Agent_C_TaskList_MPlan/config/thresholds.yaml`
- Test: modify `Agent_C_TaskList_MPlan/tests/test_validation.py` (replace the 3 existing `test_pp5_historical_benchmark_*`/`test_pp5_no_historical_matches_supplied_*` tests with equivalents against the new reconciliation path)

**Interfaces:**
- Removes: `_pp5_historical_benchmark_check` (superseded — its logic now lives in `scripts.evidence_reconciliation.historical_lane`, called from the new function below).
- Produces: `_pp5_evidence_reconciliation_check(row: dict, record_key: str, historical_matches, pitstops_ranges, oreda_db_path, min_comparable_executions, historical_benchmark_confidence) -> Finding | None` — calls all three lanes, then `reconcile_lanes`, and emits exactly one `Finding`:
  - `status == "RECOMMENDED"` → `recommended_value=str(suggested_mhr)`, `confidence=confidence`, `reason` starts with `"Evidence-reconciled recommendation: "` followed by the combined `evidence` text.
  - `status in ("NEEDS_REVIEW", "CONFLICT")` → `recommended_value=None`, `confidence=0.0`, `reason` starts with `"Needs Review"` (kept literal for compatibility with anything grepping this string) followed by `" — "` and the status-specific explanation plus the combined `evidence` text (so `CONFLICT` is distinguishable from `NEEDS_REVIEW` in the reason text even though both currently map to the same Finding shape).
- `run_pp5`'s signature gains `oreda_db_path: str | None = None` (in addition to the existing `historical_matches`, `min_comparable_executions`, `historical_benchmark_confidence`) — passed through to the new check. `pitstops_ranges` (already a parameter) is passed to the Tasklist/Worklist lane instead of only the arithmetic check's plausibility flag.

- [ ] **Step 1: Add the OREDA db path setting to `config/thresholds.yaml`** — actually this is a file path, not a threshold; instead pass it from `app.py` directly (see Task 6). No `thresholds.yaml` change needed for this specific value; the existing `pp5.min_comparable_executions`/`pp5.historical_benchmark_confidence` stay as-is.

- [ ] **Step 2: Replace the 3 historical-benchmark tests in `tests/test_validation.py`**

Find and replace these three existing tests:

```python
def test_pp5_historical_benchmark_recommended_when_enough_verified_matches():
    ...
def test_pp5_historical_benchmark_needs_review_when_too_few_verified_matches():
    ...
def test_pp5_no_historical_matches_supplied_produces_no_historical_finding():
    ...
```

with:

```python
def test_pp5_evidence_reconciliation_recommended_when_historical_lane_available():
    df = pd.DataFrame(
        {
            "TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [3.0], "WORK_UNIT": ["MHR"], "PERSON": [1], "DURATION": [3.0], "DURATION_UNIT": ["HR"],
            "OPWKCEN": ["BMECH"], "CTRLKEY": ["INTN"], "STRATEGY": ["PCSB51"],
        }
    )
    historical_matches = pd.DataFrame(
        [{"record_key": "BODA582-10-10", "execution_verified": True, "candidate_hours": [4.0, 5.0, 5.0, 6.0], "match_count": 4}]
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR", historical_matches=historical_matches)
    reconciled = [f for f in findings if f.reason.startswith("Evidence-reconciled")]
    assert len(reconciled) == 1
    assert reconciled[0].recommended_value == "5.0"
    assert reconciled[0].confidence == 0.6


def test_pp5_evidence_reconciliation_needs_review_when_no_lane_available():
    df = pd.DataFrame(
        {
            "TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [3.0], "WORK_UNIT": ["MHR"], "PERSON": [1], "DURATION": [3.0], "DURATION_UNIT": ["HR"],
            "OPWKCEN": ["BMECH"], "CTRLKEY": ["INTN"], "STRATEGY": ["PCSB51"],
        }
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR", historical_matches=None)
    reconciled = [f for f in findings if "Needs Review" in f.reason]
    assert len(reconciled) == 1
    assert reconciled[0].recommended_value is None
    assert reconciled[0].confidence == 0.0
    # All three lanes' unavailability reasons must be visible, not dropped.
    assert "crew" in reconciled[0].reason.lower() or "duration" in reconciled[0].reason.lower()
    assert "repair" in reconciled[0].reason.lower()
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v -k evidence_reconciliation
```
Expected: FAIL — `AttributeError`/no matching findings, since `run_pp5` still calls the old `_pp5_historical_benchmark_check`.

- [ ] **Step 4: Replace `_pp5_historical_benchmark_check` in `validation.py`** with:

```python
def _pp5_evidence_reconciliation_check(
    row: dict,
    record_key: str,
    historical_matches: pd.DataFrame | None,
    pitstops_ranges: pd.DataFrame | None,
    oreda_db_path: str | None,
    min_comparable_executions: int,
    historical_benchmark_confidence: float,
) -> Finding | None:
    from scripts.evidence_reconciliation import historical_lane, oreda_lane, reconcile_lanes, tasklist_worklist_lane

    lanes = {
        "historical": historical_lane(record_key, historical_matches, min_comparable_executions, historical_benchmark_confidence),
        "tasklist_worklist": tasklist_worklist_lane(row.get("OPWKCEN"), pitstops_ranges),
        "oreda": oreda_lane(row, oreda_db_path or ""),
    }
    result = reconcile_lanes(lanes)

    if result.status == "RECOMMENDED":
        return Finding(
            pain_point="PP5", record_key=record_key, field_name="WORK",
            current_value=str(row["WORK"]), recommended_value=str(result.suggested_mhr),
            confidence=result.confidence,
            reason=f"Evidence-reconciled recommendation: {result.evidence}",
            evidence_source="Timesheet BOKOR 2024/2025; M014_Bokor_Non PPM Work Order 2020_2025.xlsx; PITSTOPS Tasklist.xlsx/Worklist.xlsx; OREDA.db",
        )
    status_note = "insufficient or contradictory evidence across all sources" if result.status == "CONFLICT" else "insufficient evidence"
    return Finding(
        pain_point="PP5", record_key=record_key, field_name="WORK",
        current_value=str(row["WORK"]), recommended_value=None, confidence=0.0,
        reason=f"Needs Review — {status_note}: {result.evidence}",
        evidence_source="Timesheet BOKOR 2024/2025; M014_Bokor_Non PPM Work Order 2020_2025.xlsx; PITSTOPS Tasklist.xlsx/Worklist.xlsx; OREDA.db",
    )
```

Update `run_pp5`'s signature (add `oreda_db_path: str | None = None`) and its call site (replace the `_pp5_historical_benchmark_check(...)` call with `_pp5_evidence_reconciliation_check(row, historical_record_key, historical_matches, pitstops_ranges, oreda_db_path, min_comparable_executions, historical_benchmark_confidence)`).

- [ ] **Step 5: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v -k pp5
```
Expected: all PP5 tests pass, including the 2 new evidence-reconciliation tests.

- [ ] **Step 6: Run the full test suite**

```bash
cd Agent_C_TaskList_MPlan
pytest -q
```
Expected: all tests pass, no regressions.

- [ ] **Step 7: Commit manually**

Commit `validation.py`, `tests/test_validation.py` — message like `feat: wire 3-lane evidence reconciliation into run_pp5, replacing historical-only benchmark check`.

---

## Task 6: Task-List-Level WORK Summation

**Files:**
- Modify: `Agent_C_TaskList_MPlan/scripts/evidence_reconciliation.py`
- Test: append to `tests/test_evidence_reconciliation.py`

**Interfaces:**
- Produces: `sum_task_list_work(operation_rows: pd.DataFrame, findings: list) -> pd.DataFrame` — groups by `TLGRP`+`TLGRPCOUNT`, and for each Task List sums each operation's **effective** WORK value: the Finding's `recommended_value` when one exists for that operation's `record_key` (i.e. `status == "RECOMMENDED"` produced a Finding with a real value), else the operation's own current `WORK`. Returns `TLGRP, TLGRPCOUNT, task_list_total_work, operation_count`. Never re-derives a value independently — purely additive over each operation's already-decided value, per the plan's Global Constraints.

- [ ] **Step 1: Write the failing tests**

```python
import pandas as pd

from scripts.evidence_reconciliation import sum_task_list_work
from validation import Finding


def test_sum_task_list_work_uses_recommended_value_when_present():
    operation_rows = pd.DataFrame(
        {
            "TLGRP": ["BODA582", "BODA582"], "TLGRPCOUNT": ["10", "10"],
            "TLOPNO": ["10", "20"], "TLSUBOPNO": ["0", "0"], "WORK": [3.0, 6.0],
        }
    )
    findings = [
        Finding(
            pain_point="PP5", record_key="BODA582-10-10-0", field_name="WORK",
            current_value="3.0", recommended_value="5.0", confidence=0.6,
            reason="x", evidence_source="y",
        )
    ]
    result = sum_task_list_work(operation_rows, findings)
    row = result.iloc[0]
    assert row["TLGRP"] == "BODA582"
    assert row["task_list_total_work"] == 11.0  # 5.0 (recommended, op 10) + 6.0 (current, op 20)
    assert row["operation_count"] == 2


def test_sum_task_list_work_uses_current_value_when_no_recommendation():
    operation_rows = pd.DataFrame(
        {"TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"], "WORK": [3.0]}
    )
    result = sum_task_list_work(operation_rows, findings=[])
    assert result.iloc[0]["task_list_total_work"] == 3.0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v -k sum_task_list_work
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Add to `scripts/evidence_reconciliation.py`**

```python
def sum_task_list_work(operation_rows: pd.DataFrame, findings: list) -> pd.DataFrame:
    # Purely additive over each operation's already-decided value — never
    # re-derives or overrides an operation-level Finding.
    recommended_by_key = {
        f.record_key: float(f.recommended_value)
        for f in findings
        if f.field_name == "WORK" and f.recommended_value is not None
    }

    def effective_work(row) -> float:
        record_key = f"{row['TLGRP']}-{row['TLGRPCOUNT']}-{row['TLOPNO']}-{row['TLSUBOPNO']}"
        return recommended_by_key.get(record_key, row["WORK"])

    work_col = operation_rows.apply(effective_work, axis=1)
    grouped = operation_rows.assign(_effective_work=work_col).groupby(
        ["TLGRP", "TLGRPCOUNT"], as_index=False
    ).agg(task_list_total_work=("_effective_work", "sum"), operation_count=("_effective_work", "count"))
    return grouped
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v
```
Expected: 16 passed.

- [ ] **Step 5: Commit manually**

Commit — message like `feat: sum_task_list_work — Task List total as sum of operation-level effective WORK`.

---

## Task 7: Run the Real Coverage Verification and Report Back

**Files:** none modified — this is a verification task, matching how Step 2A/2B/2C's real numbers were obtained earlier.

- [ ] **Step 1: Run the full test suite**

```bash
cd Agent_C_TaskList_MPlan
pytest -q
```
Expected: all tests pass (existing + all new evidence-reconciliation tests).

- [ ] **Step 2: Manually verify the reconciliation logic against real data** (not an automated test — matches how the Step 2 coverage report was verified earlier in this project)

Using the existing `app.py`/`scripts/coverage_report.py` ingestion pattern, load real `normalized_operations`, `historical_matches` (from Task 1-5 of the prior plan), `pitstops_ranges`, and confirm via a short ad-hoc script that:
- Every operation's `tasklist_worklist_lane` result is `available=False` with the crew-size reason (expected, given the confirmed data gap).
- Every operation's `oreda_lane` result is `available=False` with the "not a repair activity" reason (expected, given `CTRLKEY`/`STRATEGY` are uniformly routine-PM-shaped).
- The historical lane's availability rate matches the existing coverage report's `execution_verified_count` (0 today).
- Report these real counts back rather than assuming the plan's expectations hold — if any of them differ from what's stated in this plan's Source Facts Reference, stop and report the discrepancy before considering this task done.

- [ ] **Step 3: Report back**

Summarize: total operations evaluated, how many got `RECOMMENDED` vs `NEEDS_REVIEW` vs `CONFLICT`, and for `NEEDS_REVIEW`/`CONFLICT` rows, confirm the evidence text visibly shows all three lanes' reasons (not just one). This is the same honesty standard applied to the original Step 2 coverage report — a mostly-`NEEDS_REVIEW` result is expected and correct, not a sign the task failed.

---

## What This Plan Deliberately Does Not Include

- **No wiring of a real OREDA `item_hint`** — since no Bokor operation is repair-type today, there is no data to derive an `item_hint` mapping from, so `oreda_lane` is only ever called with the default `item_hint=None`. Building an Operation→OREDA-taxonomy mapping is out of scope until repair-type operations actually exist in the data.
- **No crew-size data sourcing for the Tasklist/Worklist lane** — that would require a new data source the client would need to supply; this plan doesn't propose acquiring one.
- **No re-enabling of PP1/PP2/PP3/PP4/PP6/PP7** in `app.py` — unrelated to this plan, stays as currently set (PP5 only, per the user's last explicit instruction).
- **No change to the arithmetic check** (`_pp5_row_check`'s completeness/unit/`WORK=PERSON×DURATION` logic) — untouched throughout.
- **No output-writer/Excel-schema changes** — the reconciled Finding still fits the existing `Finding`/`output_writer.py` shape (one row per pain point per field); `sum_task_list_work`'s output is a new DataFrame this plan produces but does not yet wire into `output_writer.py`'s Excel output — that would be a follow-up once the client confirms they want a Task-List-level rollup sheet.
