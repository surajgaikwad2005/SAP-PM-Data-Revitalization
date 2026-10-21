# PP5 — JMS Workpack Evidence as a Fourth Lane

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the ~29 JMS/Job Planning workpack PDFs (already surveyed, being re-extracted page-by-page under `docs/plans/2026-09-16-pp5-evidence-reconciliation-implementation.md`'s ground-truth convention) as a fourth, independent evidence lane in PP5's recommendation logic — alongside the existing Historical, Tasklist/Worklist, and OREDA lanes — without changing how those three lanes or the reconciliation engine work.

**Architecture:** Three new pieces, following the existing lane pattern exactly, with a matching/validation gate significantly stricter than a first draft of this plan proposed (revised 2026-09-17 per direct correction — see below):
1. **Consolidated extraction table** (`ground_truth_cache/PP05_JMS_ManHours.csv`) — one row per PDF/page/task entry, built by merging the per-file CSVs already being produced in the scratchpad (see Task 1).
2. **SAP matching step** (`scripts/jms_workpack_matching.py::match_jms_to_operations`) — joins each extraction row to a Task List Operation only when **all four** signals agree: verified Bokor platform, equipment tag, activity/description, and unambiguous scope (the tag+description combination resolves to exactly one operation, never a best-guess pick among several). Produces `evidence_status` per row with **four** distinct values (not three): `Complete`, `Incomplete`, `Excluded — Platform`, `No Match` — see Task 2 for exact rules. A row is never `Complete` unless its manpower, duration, and unit data are individually validated AND its `crew_size × hours_per_task` reconciles with the document's own stated `total_manhours` within tolerance.
3. **Fourth lane** (`scripts/evidence_reconciliation.py::jms_workpack_lane`) — consumes the matched table, computes a candidate MHR only when **multiple independent `Complete` rows** exist for the same operation (mirroring `historical_lane`'s `min_comparable_executions` gate — a single-document match is evidence, never an automatic recommendation on its own), and reports `available=False` with a reason distinguishing every non-recommending case (`Incomplete` evidence vs. `Excluded — Platform` vs. `No Match` vs. "only one Complete match, below the minimum"). Confidence is capped below the historical lane's, since JMS sourcing is single-workpack evidence, not cross-validated the way multiple historical executions are.

**Correction applied 2026-09-17 (direct instruction, tightening this plan's original matching design):** SAP matching must require verified platform, equipment, activity, AND scope together — not equipment-tag-alone with description as a soft secondary signal. Ambiguous matches (tag/description that could resolve to more than one operation) must be rejected outright, never resolved by picking the "best" candidate. Manpower, duration, units, and documented totals must all be validated — not read at face value — before a row can count as `Complete`. Incomplete evidence and platform exclusions must be visibly distinct statuses/reasons, never conflated into one `Partial` bucket. No automatic recommendation may ever come from weak (single-source, unvalidated, or ambiguous) evidence. Source PDF/page citations must survive into every downstream Finding's evidence text, the same as the other three lanes already do.

**Tech Stack:** Python, `pandas` (matches the rest of the codebase), no new dependencies.

## Global Constraints

- **Do not assume every listed person works the full activity duration.** Where a PDF lists manpower (a roster/crew list) but no activity duration is stated anywhere in that document, `Evidence Status = Partial` and no MHR is calculated — manpower alone is never multiplied by an assumed or borrowed duration from a different document/section.
- **Confirmed real-data facts, not to be silently reinterpreted:**
  - Most JMS documents have only 1-3 joint Purchase Order/Work Order numbers covering an entire workpack (not one per equipment line) — so `work_order_or_po_number` alone is an unreliable join key on its own; matching must primarily use Equipment tag + activity description + maintenance scope, per the corrected design.
  - Several documents filed under the BOKOR folder are genuinely Betty/Laila/BEDP-A/LADR-A jobs (`platform_verified_bokor=FALSE`) — these must never match to a Bokor Task List Operation, regardless of how well their equipment tag or description otherwise lines up.
  - Some documents state platform codes (e.g. `LADR-A`) without ever using the word "Bokor" (`platform_verified_bokor=UNKNOWN`) — these are excluded from matching by default (§ Task 2) unless the client confirms the platform mapping.
  - Several extraction rows carry internal document inconsistencies already flagged in `notes` (e.g. task-level sums not reconciling with document-stated totals, duplicate equipment tags reused across different platforms, "TBA" placeholder tags). The matching step must surface these via `Evidence Status`/`notes`, never silently resolve them in the SAP-matching agent's favor.
- **No change to the Historical, Tasklist/Worklist, or OREDA lanes, or to `reconcile_lanes`'s combination logic.** The fourth lane plugs into the exact same `dict[str, LaneResult]` shape `reconcile_lanes` already accepts — confirmed by reading the current code, no signature change needed there.
- **Confidence is a 0.0-1.0 float**, `Recommended_Value=None` iff `confidence==0.0` — the `Finding` schema's rule, unchanged.
- **Code style**: simple, modular, meaningful names, no placeholder logic — matches the rest of this project.
- **Testing**: `pytest`, synthetic DataFrames built inline, no dependency on real Excel/PDF files for unit tests.

---

## Task 1: Finish and Consolidate the Per-PDF Extraction

**Status:** in progress as of this plan's writing — re-extraction of the ~29 useful PDFs is running one-file-at-a-time (per direction) under `docs/plans/2026-09-16-pp5-evidence-reconciliation-implementation.md`'s schema (`C:\Users\NIKHIL~1.RAU\...\scratchpad\jms_manhours_schema.md`), each PDF's rows written to its own scratchpad CSV (`jms_manhours_2023_03.csv`, `jms_manhours_2023_05A.csv`, etc.).

**Files:**
- Create: `Agent_C_TaskList_MPlan/scripts/build_jms_manhours_cache.py`
- Create: `Agent_C_TaskList_MPlan/ground_truth_cache/PP05_JMS_ManHours.csv` (generated output, not hand-edited — matches this project's `GENERATED CACHE` convention)

**Interfaces:**
- Produces: `merge_extraction_csvs(csv_paths: list[str]) -> pd.DataFrame` — concatenates every per-PDF scratchpad CSV into one DataFrame, validating that every row's `source_pdf` matches the expected file for that CSV (fails loudly on a mismatch, since a wrong `source_pdf` value would silently misattribute evidence).
- Produces: a `if __name__ == "__main__":` block that runs the merge against every completed per-PDF CSV and writes `ground_truth_cache/PP05_JMS_ManHours.csv`, with a `GENERATED CACHE` header comment matching `scripts/build_ground_truth.py`'s existing convention.

- [ ] **Step 1: Confirm every dispatched extraction has completed and produced its CSV**

Check the scratchpad for one CSV per PDF in the ~29-file list (2023: 03, 05A, 07, 08, 09, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 26, 29, 30, 31, 32; 2024: the 231pp TA workpack, the MCM CWR schedule, 3 Instrument workpacks, plus the V-1010 Lifting Plan as a manpower-only source). Any file whose extraction failed or is still running must be re-dispatched (one file per agent, per direction) before proceeding — do not merge a partial set and call it complete.

- [ ] **Step 2: Write the failing test**

```python
import pandas as pd

from scripts.build_jms_manhours_cache import merge_extraction_csvs


def test_merge_extraction_csvs_concatenates_and_validates_source_pdf(tmp_path):
    csv_a = tmp_path / "jms_manhours_2023_09.csv"
    pd.DataFrame(
        {
            "source_pdf": ["2023/09. Fuel Gas Superheater (1Yearly) PPM.pdf"] * 2,
            "source_page_number": ["13", "13"],
            "source_section_label": ["Manhour Summary List"] * 2,
            "platform_stated": ["BOCPP-A", "BEP-A"],
            "platform_verified_bokor": ["TRUE", "TRUE"],
            "job_description": ["E-5920A", "E-640"],
            "equipment_tag": ["E-5920A", "E-640"],
            "work_order_or_po_number": ["", ""],
            "crew_size": ["2", "2"],
            "crew_trade_breakdown": ["", ""],
            "hours_per_task": ["12", "12"],
            "total_manhours": ["24", "24"],
            "notes": ["", ""],
        }
    ).to_csv(csv_a, index=False)

    result = merge_extraction_csvs([str(csv_a)])
    assert result.shape[0] == 2
    assert set(result["source_pdf"]) == {"2023/09. Fuel Gas Superheater (1Yearly) PPM.pdf"}


def test_merge_extraction_csvs_rejects_mismatched_source_pdf(tmp_path):
    csv_a = tmp_path / "jms_manhours_2023_09.csv"
    pd.DataFrame(
        {
            "source_pdf": ["2023/10. UPS System Battery Discharge Test 2Y PPM.pdf"],  # wrong file for this CSV's name
            "source_page_number": ["13"], "source_section_label": ["x"], "platform_stated": ["BOKOR"],
            "platform_verified_bokor": ["TRUE"], "job_description": ["x"], "equipment_tag": ["x"],
            "work_order_or_po_number": [""], "crew_size": ["2"], "crew_trade_breakdown": [""],
            "hours_per_task": ["12"], "total_manhours": ["24"], "notes": [""],
        }
    ).to_csv(csv_a, index=False)

    import pytest
    with pytest.raises(ValueError, match="source_pdf"):
        merge_extraction_csvs([str(csv_a)], expected_source_pdfs={"jms_manhours_2023_09.csv": "2023/09. Fuel Gas Superheater (1Yearly) PPM.pdf"})
```

- [ ] **Step 3: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_jms_workpack_matching.py -v -k merge_extraction_csvs
```
Expected: FAIL — `ModuleNotFoundError`.

- [ ] **Step 4: Write `scripts/build_jms_manhours_cache.py`**

```python
from pathlib import Path

import pandas as pd


def merge_extraction_csvs(csv_paths: list[str], expected_source_pdfs: dict[str, str] | None = None) -> pd.DataFrame:
    frames = []
    for path in csv_paths:
        df = pd.read_csv(path, dtype=str)
        if expected_source_pdfs is not None:
            filename = Path(path).name
            expected = expected_source_pdfs.get(filename)
            if expected is not None:
                mismatched = df[df["source_pdf"] != expected]
                if not mismatched.empty:
                    raise ValueError(
                        f"{filename}: found source_pdf values other than the expected "
                        f"'{expected}' — {mismatched['source_pdf'].unique().tolist()}"
                    )
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


if __name__ == "__main__":
    import glob

    scratchpad_csvs = glob.glob(
        r"C:\Users\NIKHIL~1.RAU\AppData\Local\Temp\claude\c--Users-nikhil-raut-Tridiagonal-ai-Petronas-Data\*\scratchpad\jms_manhours_*.csv"
    )
    merged = merge_extraction_csvs(scratchpad_csvs)

    base = Path(__file__).resolve().parent.parent
    out_path = base / "ground_truth_cache" / "PP05_JMS_ManHours.csv"
    header = (
        "# GENERATED CACHE — do not hand-edit. Source: ground_truth_sources/jms_workpacks/BOKOR/*.pdf\n"
        "# Regenerate via scripts/build_jms_manhours_cache.py after any source PDF changes.\n"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(header)
        merged.to_csv(f, index=False)
    print(f"wrote {merged.shape[0]} rows to {out_path}")
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_jms_workpack_matching.py -v
```
Expected: 2 passed.

- [ ] **Step 6: Run the real merge and inspect the result**

```bash
cd Agent_C_TaskList_MPlan
python scripts/build_jms_manhours_cache.py
```
Expected: writes `ground_truth_cache/PP05_JMS_ManHours.csv`, prints a row count. Manually spot-check: every `source_pdf` value corresponds to a real file under `ground_truth_sources/jms_workpacks/BOKOR/`, and the count of distinct `source_pdf` values matches the number of PDFs actually extracted (report this number — if it's not the full ~29, list which are missing before proceeding to Task 2).

- [ ] **Step 7: Commit manually**

Commit `scripts/build_jms_manhours_cache.py`, `tests/test_jms_workpack_matching.py`, `ground_truth_cache/PP05_JMS_ManHours.csv` — message like `feat: consolidate per-PDF JMS workpack man-hour extractions into one ground-truth cache`.

---

## Task 2: SAP Operation Matching (Strict — Corrected 2026-09-17)

**Files:**
- Create: `Agent_C_TaskList_MPlan/scripts/jms_workpack_matching.py`
- Test: append to `Agent_C_TaskList_MPlan/tests/test_jms_workpack_matching.py`

**Interfaces:**
- Consumes: the merged extraction DataFrame (Task 1's output), `normalized_operations` (from `scripts/normalize.py::normalize_long_text`, same shape used by `historical_matching.py`).
- Produces: `match_jms_to_operations(extraction_df: pd.DataFrame, normalized_operations: pd.DataFrame) -> pd.DataFrame`.

**Matching rule — all four signals required, none optional:**
1. **Platform** — `platform_verified_bokor` must be exactly `"TRUE"`. `"FALSE"` or `"UNKNOWN"` are an immediate `Excluded — Platform` status, checked *before* any equipment/description matching is attempted (so a coincidentally-matching tag on a Betty/Laila row is never even considered).
2. **Equipment tag** — normalized-substring match against the operation's `OPDESC`/`LONGTEXT_AGGREGATED` text (as before).
3. **Activity/description** — `job_description` must also normalized-match somewhere in the same operation's `OPDESC`/`LONGTEXT_AGGREGATED` text. A tag match alone, with no corroborating description match, is not a match — both must agree on the *same* candidate operation.
4. **Scope/ambiguity check** — if the equipment tag (independent of description) matches more than one distinct `(TLGRP, TLGRPCOUNT, TLOPNO)` operation, the match is rejected outright as ambiguous — never resolved by picking the first, the best-scoring, or the most-recent candidate. An ambiguous row gets `sap_record_key=None`, `evidence_status="No Match"`, and a `notes` addition stating it was rejected as ambiguous (with the list of candidate keys), so this is visibly different from a row with no candidates at all.

**Four evidence_status values (not three) — visibly distinct, never conflated:**
- `"Excluded — Platform"` — platform is not verified Bokor. Checked first; nothing else about this row is evaluated once this applies.
- `"No Match"` — platform is Bokor, but no single unambiguous operation satisfies both the equipment-tag and description checks together (includes the ambiguous-match case above).
- `"Incomplete"` — a valid, unambiguous, Bokor-verified match was found, but the row's own manpower/duration/unit data fails validation (see below) — this is the correct bucket for the V-1010 Lifting Plan case (manpower present, no duration anywhere) AND for any row whose numbers exist but don't validate.
- `"Complete"` — matched, unambiguous, Bokor-verified, AND the row's manpower/duration/units/total all pass validation (below).

**Validation required before a row can be `"Complete"` (all of the following, not just presence-of-a-number):**
- `crew_size` parses as a positive number.
- `hours_per_task` parses as a positive number, OR `total_manhours` is present with no `hours_per_task` (some extraction rows only ever had a document-stated total, never a per-task hours figure — still validatable on its own).
- If a row's `notes` field (carried over from extraction) contains any of the known unit/meaning caveats already flagged during extraction (`"day-window"`, `"elapsed"`, `"not granular"`, `"calendar"`) — these rows are `Incomplete`, not `Complete`, regardless of whether crew_size/hours_per_task are individually present, since the extraction agents themselves already flagged the *quantity* as suspect, not just missing.
- If both `crew_size`×`hours_per_task` and a separately-stated `total_manhours` are present, they must reconcile within a tolerance (default 5%) — a mismatch makes the row `Incomplete` with the discrepancy stated in `notes`, never silently trusting one figure over the other.

**Source citation preserved:** every output row keeps `source_pdf` and `source_page_number` unchanged from the input — these must survive into the eventual Finding's evidence text exactly like the other three lanes already cite their sources.

- [ ] **Step 1: Write the failing tests**

```python
import pandas as pd

from scripts.jms_workpack_matching import match_jms_to_operations


def test_match_complete_when_platform_equipment_activity_and_validated_numbers_all_agree():
    extraction_df = pd.DataFrame(
        {
            "source_pdf": ["2023/09. Fuel Gas Superheater (1Yearly) PPM.pdf"], "source_page_number": ["13"],
            "equipment_tag": ["E-5920A"], "job_description": ["Preventive Maintenance IPS"],
            "platform_verified_bokor": ["TRUE"], "crew_size": ["2"], "hours_per_task": ["12"],
            "total_manhours": ["24"], "notes": [""],
        }
    )
    normalized_operations = pd.DataFrame(
        {
            "TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"],
            "OPDESC": ["E-5920A Preventive Maintenance IPS"], "LONGTEXT_AGGREGATED": ["E-5920A PM"],
        }
    )
    result = match_jms_to_operations(extraction_df, normalized_operations)
    assert result.iloc[0]["sap_record_key"] == "BODA582-10-10"
    assert result.iloc[0]["evidence_status"] == "Complete"


def test_match_no_match_when_tag_matches_but_description_does_not():
    # Tag alone is not enough — description must corroborate the SAME operation.
    extraction_df = pd.DataFrame(
        {
            "source_pdf": ["x.pdf"], "source_page_number": ["1"],
            "equipment_tag": ["E-5920A"], "job_description": ["Completely unrelated activity text"],
            "platform_verified_bokor": ["TRUE"], "crew_size": ["2"], "hours_per_task": ["12"],
            "total_manhours": ["24"], "notes": [""],
        }
    )
    normalized_operations = pd.DataFrame(
        {"TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "OPDESC": ["E-5920A PM"], "LONGTEXT_AGGREGATED": ["E-5920A"]}
    )
    result = match_jms_to_operations(extraction_df, normalized_operations)
    assert result.iloc[0]["evidence_status"] == "No Match"
    assert result.iloc[0]["sap_record_key"] is None


def test_match_no_match_when_tag_is_ambiguous_across_multiple_operations():
    extraction_df = pd.DataFrame(
        {
            "source_pdf": ["x.pdf"], "source_page_number": ["1"],
            "equipment_tag": ["V-1010"], "job_description": ["Cleaning"],
            "platform_verified_bokor": ["TRUE"], "crew_size": ["7"], "hours_per_task": ["12"],
            "total_manhours": ["252"], "notes": [""],
        }
    )
    normalized_operations = pd.DataFrame(
        {
            "TLGRP": ["BODA582", "BODB582"], "TLGRPCOUNT": ["10", "20"], "TLOPNO": ["10", "10"],
            "OPDESC": ["V-1010 Cleaning A", "V-1010 Cleaning B"],
            "LONGTEXT_AGGREGATED": ["V-1010", "V-1010"],
        }
    )
    result = match_jms_to_operations(extraction_df, normalized_operations)
    assert result.iloc[0]["evidence_status"] == "No Match"
    assert result.iloc[0]["sap_record_key"] is None
    assert "ambiguous" in result.iloc[0]["notes"].lower()


def test_match_excluded_platform_checked_before_any_equipment_matching():
    extraction_df = pd.DataFrame(
        {
            "source_pdf": ["2023/17. AB PLC (BE) Preventive Maintenance (Yearly).pdf"], "source_page_number": ["5"],
            "equipment_tag": ["LCP 801"], "job_description": ["AB PLC PM"],
            "platform_verified_bokor": ["FALSE"], "crew_size": ["1"], "hours_per_task": ["6"],
            "total_manhours": ["6"], "notes": [""],
        }
    )
    normalized_operations = pd.DataFrame(
        {"TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "OPDESC": ["LCP 801 PM"], "LONGTEXT_AGGREGATED": ["AB PLC PM"]}
    )
    result = match_jms_to_operations(extraction_df, normalized_operations)
    assert result.iloc[0]["evidence_status"] == "Excluded — Platform"
    assert result.iloc[0]["sap_record_key"] is None


def test_match_incomplete_when_manpower_present_but_no_duration_anywhere():
    # The V-1010 Lifting Plan case.
    extraction_df = pd.DataFrame(
        {
            "source_pdf": ["2023/05B. BOCPP-A V-1010 Lifting Plan Beyond 8T [Approved].pdf"], "source_page_number": ["6"],
            "equipment_tag": ["V-1010"], "job_description": ["Lifting Plan"],
            "platform_verified_bokor": ["TRUE"], "crew_size": ["7"], "hours_per_task": [""],
            "total_manhours": [""], "notes": [""],
        }
    )
    normalized_operations = pd.DataFrame(
        {"TLGRP": ["BOCPPA1"], "TLGRPCOUNT": ["1"], "TLOPNO": ["10"], "OPDESC": ["V-1010 Lifting Plan"], "LONGTEXT_AGGREGATED": ["Lifting Plan for V-1010"]}
    )
    result = match_jms_to_operations(extraction_df, normalized_operations)
    assert result.iloc[0]["evidence_status"] == "Incomplete"
    assert result.iloc[0]["sap_record_key"] == "BOCPPA1-1-10"


def test_match_incomplete_when_crew_times_hours_does_not_reconcile_with_stated_total():
    extraction_df = pd.DataFrame(
        {
            "source_pdf": ["x.pdf"], "source_page_number": ["1"],
            "equipment_tag": ["E-1234"], "job_description": ["Some PM job"],
            "platform_verified_bokor": ["TRUE"], "crew_size": ["2"], "hours_per_task": ["12"],
            "total_manhours": ["999"],  # 2*12=24, nowhere near 999
            "notes": [""],
        }
    )
    normalized_operations = pd.DataFrame(
        {"TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "OPDESC": ["E-1234 Some PM job"], "LONGTEXT_AGGREGATED": ["E-1234"]}
    )
    result = match_jms_to_operations(extraction_df, normalized_operations)
    assert result.iloc[0]["evidence_status"] == "Incomplete"
    assert "reconcile" in result.iloc[0]["notes"].lower() or "discrepan" in result.iloc[0]["notes"].lower()


def test_match_incomplete_when_extraction_notes_flag_day_window_or_elapsed_caveat():
    extraction_df = pd.DataFrame(
        {
            "source_pdf": ["2023/08. 6Y Switchgear PPM.pdf"], "source_page_number": ["12"],
            "equipment_tag": ["SR100E1"], "job_description": ["Perform 6Y Switchgear PPM"],
            "platform_verified_bokor": ["TRUE"], "crew_size": ["2"], "hours_per_task": ["24"],
            "total_manhours": ["48"],
            "notes": ["day-window figure, not granular labor hours"],
        }
    )
    normalized_operations = pd.DataFrame(
        {"TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "OPDESC": ["SR100E1 Perform 6Y Switchgear PPM"], "LONGTEXT_AGGREGATED": ["SR100E1"]}
    )
    result = match_jms_to_operations(extraction_df, normalized_operations)
    assert result.iloc[0]["evidence_status"] == "Incomplete"


def test_match_source_pdf_and_page_number_survive_unchanged():
    extraction_df = pd.DataFrame(
        {
            "source_pdf": ["2023/09. Fuel Gas Superheater (1Yearly) PPM.pdf"], "source_page_number": ["13"],
            "equipment_tag": ["E-5920A"], "job_description": ["Preventive Maintenance IPS"],
            "platform_verified_bokor": ["TRUE"], "crew_size": ["2"], "hours_per_task": ["12"],
            "total_manhours": ["24"], "notes": [""],
        }
    )
    normalized_operations = pd.DataFrame(
        {"TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "OPDESC": ["E-5920A Preventive Maintenance IPS"], "LONGTEXT_AGGREGATED": ["E-5920A"]}
    )
    result = match_jms_to_operations(extraction_df, normalized_operations)
    assert result.iloc[0]["source_pdf"] == "2023/09. Fuel Gas Superheater (1Yearly) PPM.pdf"
    assert result.iloc[0]["source_page_number"] == "13"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_jms_workpack_matching.py -v -k match_
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Write `scripts/jms_workpack_matching.py`**

```python
import pandas as pd

RECONCILE_TOLERANCE_FRACTION = 0.05  # crew_size x hours_per_task vs. stated total_manhours
QUANTITY_CAVEAT_KEYWORDS = ("day-window", "elapsed", "not granular", "calendar")


def _normalize(text: str) -> str:
    return "".join(ch for ch in str(text).upper() if ch.isalnum())


def _parse_positive_number(value) -> float | None:
    try:
        parsed = float(str(value).strip())
    except (ValueError, TypeError):
        return None
    return parsed if parsed > 0 else None


def _find_candidate_operations(equipment_tag: str, normalized_operations: pd.DataFrame) -> list[dict]:
    if not equipment_tag:
        return []
    tag_normalized = _normalize(equipment_tag)
    if not tag_normalized:
        return []
    candidates = []
    for op in normalized_operations.to_dict("records"):
        combined_text = _normalize(f"{op.get('OPDESC', '')} {op.get('LONGTEXT_AGGREGATED', '')}")
        if tag_normalized in combined_text:
            candidates.append(op)
    return candidates


def _description_corroborates(job_description: str, op: dict) -> bool:
    if not job_description:
        return False
    desc_normalized = _normalize(job_description)
    combined_text = _normalize(f"{op.get('OPDESC', '')} {op.get('LONGTEXT_AGGREGATED', '')}")
    # Simple containment check, deliberately not fuzzy-matched — the real
    # match-quality threshold is a client decision (resolution plan §8/D3),
    # not something to over-engineer here. Kept strict on purpose: a tag
    # match with no corroborating description text is rejected, not
    # accepted on the tag alone.
    return desc_normalized in combined_text or combined_text in desc_normalized


def _validate_quantities(row: dict) -> tuple[bool, str | None]:
    notes = str(row.get("notes", "") or "").lower()
    if any(keyword in notes for keyword in QUANTITY_CAVEAT_KEYWORDS):
        return False, "extraction notes flag this quantity as a day-window/elapsed figure, not validated labor hours"

    crew_size = _parse_positive_number(row.get("crew_size"))
    hours_per_task = _parse_positive_number(row.get("hours_per_task"))
    total_manhours = _parse_positive_number(row.get("total_manhours"))

    if crew_size is None:
        return False, "crew_size missing or not a positive number"
    if hours_per_task is None and total_manhours is None:
        return False, "neither hours_per_task nor total_manhours is a positive number"

    if crew_size is not None and hours_per_task is not None and total_manhours is not None:
        computed = crew_size * hours_per_task
        if abs(computed - total_manhours) > RECONCILE_TOLERANCE_FRACTION * max(computed, total_manhours):
            return False, (
                f"crew_size x hours_per_task ({computed}) does not reconcile with the document's "
                f"stated total_manhours ({total_manhours}) within {RECONCILE_TOLERANCE_FRACTION:.0%} tolerance"
            )
    return True, None


def match_jms_to_operations(extraction_df: pd.DataFrame, normalized_operations: pd.DataFrame) -> pd.DataFrame:
    results = []
    for row in extraction_df.to_dict("records"):
        row = dict(row)
        existing_notes = str(row.get("notes", "") or "")

        # 1. Platform gate — checked first, before any equipment/description
        # matching is even attempted.
        if str(row.get("platform_verified_bokor", "")).strip().upper() != "TRUE":
            results.append({**row, "sap_record_key": None, "evidence_status": "Excluded — Platform"})
            continue

        # 2 & 4. Equipment-tag candidates, then reject as ambiguous if more
        # than one distinct operation matches the tag alone.
        candidates = _find_candidate_operations(row.get("equipment_tag", ""), normalized_operations)
        distinct_keys = {(c["TLGRP"], c["TLGRPCOUNT"], c["TLOPNO"]) for c in candidates}
        if len(distinct_keys) > 1:
            note = f"rejected as ambiguous — tag matched {len(distinct_keys)} distinct operations: {sorted(distinct_keys)}"
            results.append({**row, "notes": f"{existing_notes}; {note}".strip("; "), "sap_record_key": None, "evidence_status": "No Match"})
            continue
        if not candidates:
            results.append({**row, "sap_record_key": None, "evidence_status": "No Match"})
            continue

        # 3. Description must also corroborate the SAME candidate — a tag
        # match alone is not sufficient.
        matched_op = candidates[0]
        if not _description_corroborates(row.get("job_description", ""), matched_op):
            results.append({**row, "sap_record_key": None, "evidence_status": "No Match"})
            continue

        record_key = f"{matched_op['TLGRP']}-{matched_op['TLGRPCOUNT']}-{matched_op['TLOPNO']}"
        is_valid, invalid_reason = _validate_quantities(row)
        if not is_valid:
            note = f"Incomplete: {invalid_reason}"
            results.append({**row, "notes": f"{existing_notes}; {note}".strip("; "), "sap_record_key": record_key, "evidence_status": "Incomplete"})
            continue

        results.append({**row, "sap_record_key": record_key, "evidence_status": "Complete"})

    return pd.DataFrame(results)
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_jms_workpack_matching.py -v
```
Expected: all passing.

- [ ] **Step 5: Commit manually**

Commit `scripts/jms_workpack_matching.py`, `tests/test_jms_workpack_matching.py` — message like `feat: strict SAP matching for JMS workpack evidence (platform+equipment+activity+scope required, ambiguous matches rejected, quantities validated)`.

---

## Task 3: Fourth Evidence Lane (Corrected — Requires Multiple Independent Complete Matches)

**Files:**
- Modify: `Agent_C_TaskList_MPlan/scripts/evidence_reconciliation.py`
- Test: append to `Agent_C_TaskList_MPlan/tests/test_evidence_reconciliation.py`

**Interfaces:**
- Produces: `jms_workpack_lane(record_key: str, matched_jms_rows: pd.DataFrame | None, min_comparable_entries: int = 2) -> LaneResult` — filters `matched_jms_rows` (Task 2's output) to `sap_record_key == record_key`.
  - **No rows for this key at all** → unavailable, reason states "no JMS workpack evidence for this operation."
  - **Rows exist, but zero are `Complete`** (all `Excluded — Platform`, `No Match`, or `Incomplete`) → unavailable, reason names the specific status breakdown (e.g. "1 Incomplete: manpower listed but no validated duration; 0 Complete") — never a generic "unavailable," and explicitly distinct from the platform-exclusion case per direction.
  - **Fewer than `min_comparable_entries` `Complete` rows** (default 2 — mirrors `historical_lane`'s `min_comparable_executions` gate; a single-document match is evidence, never grounds for an automatic recommendation on its own, per direction) → unavailable, reason states how many `Complete` rows were found vs. the minimum required.
  - **`min_comparable_entries` or more `Complete` rows** → available, `suggested_mhr` = median `total_manhours` across those rows, confidence capped at `JMS_WORKPACK_LANE_CONFIDENCE` (below `historical_lane`'s, since this is workpack-sourced rather than cross-validated historical execution data), and the reason/evidence text includes each contributing row's `source_pdf`+`source_page_number` (not just a count), so the citation trail is visible in the eventual Finding exactly like the other lanes.

- [ ] **Step 1: Write the failing tests**

```python
import pandas as pd

from scripts.evidence_reconciliation import jms_workpack_lane


def test_jms_workpack_lane_available_with_two_or_more_complete_rows():
    matched = pd.DataFrame(
        [
            {"sap_record_key": "BODA582-10-10", "evidence_status": "Complete", "total_manhours": "24",
             "source_pdf": "a.pdf", "source_page_number": "13"},
            {"sap_record_key": "BODA582-10-10", "evidence_status": "Complete", "total_manhours": "20",
             "source_pdf": "b.pdf", "source_page_number": "9"},
        ]
    )
    result = jms_workpack_lane("BODA582-10-10", matched, min_comparable_entries=2)
    assert result.available is True
    assert result.suggested_mhr == 22.0  # median of 24, 20
    assert "a.pdf" in result.reason and "b.pdf" in result.reason


def test_jms_workpack_lane_unavailable_with_only_one_complete_row_below_minimum():
    # Single-document Complete match is evidence, never grounds for an
    # automatic recommendation on its own — per direction.
    matched = pd.DataFrame(
        [{"sap_record_key": "BODA582-10-10", "evidence_status": "Complete", "total_manhours": "24",
          "source_pdf": "a.pdf", "source_page_number": "13"}]
    )
    result = jms_workpack_lane("BODA582-10-10", matched, min_comparable_entries=2)
    assert result.available is False
    assert "1" in result.reason and "2" in result.reason  # states found-vs-required counts


def test_jms_workpack_lane_unavailable_distinguishes_incomplete_from_platform_exclusion():
    matched = pd.DataFrame(
        [{"sap_record_key": "BODA582-10-10", "evidence_status": "Incomplete", "total_manhours": "",
          "source_pdf": "a.pdf", "source_page_number": "6"}]
    )
    result = jms_workpack_lane("BODA582-10-10", matched, min_comparable_entries=2)
    assert result.available is False
    assert "incomplete" in result.reason.lower()

    matched_excluded = pd.DataFrame(
        [{"sap_record_key": "BODA582-10-10", "evidence_status": "Excluded — Platform", "total_manhours": "",
          "source_pdf": "b.pdf", "source_page_number": "1"}]
    )
    result_excluded = jms_workpack_lane("BODA582-10-10", matched_excluded, min_comparable_entries=2)
    assert result_excluded.available is False
    assert "platform" in result_excluded.reason.lower()
    # The two reasons must be visibly different from each other, not both a generic "unavailable."
    assert result.reason != result_excluded.reason


def test_jms_workpack_lane_unavailable_when_no_jms_evidence_at_all():
    matched = pd.DataFrame(columns=["sap_record_key", "evidence_status", "total_manhours", "source_pdf", "source_page_number"])
    result = jms_workpack_lane("BODA582-10-10", matched)
    assert result.available is False
    assert "no jms" in result.reason.lower()


def test_jms_workpack_lane_unavailable_when_matched_rows_not_supplied():
    result = jms_workpack_lane("BODA582-10-10", None)
    assert result.available is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v -k jms_workpack_lane
```
Expected: FAIL — `ImportError`.

- [ ] **Step 3: Add to `scripts/evidence_reconciliation.py`**

```python
JMS_WORKPACK_LANE_CONFIDENCE = 0.4  # lower than historical_lane's — workpack-sourced, not cross-validated historical execution data


def jms_workpack_lane(record_key: str, matched_jms_rows: pd.DataFrame | None, min_comparable_entries: int = 2) -> LaneResult:
    source = "ground_truth_cache/PP05_JMS_ManHours.csv"
    if matched_jms_rows is None or matched_jms_rows.empty:
        return LaneResult(False, None, 0.0, "No JMS workpack evidence found for this operation", source)

    rows_for_operation = matched_jms_rows[matched_jms_rows["sap_record_key"] == record_key]
    if rows_for_operation.empty:
        return LaneResult(False, None, 0.0, "No JMS workpack evidence found for this operation", source)

    complete_rows = rows_for_operation[rows_for_operation["evidence_status"] == "Complete"]
    if complete_rows.empty:
        # Distinguish WHY there's no Complete evidence — never a generic
        # "unavailable" — since Incomplete (manpower/duration validation
        # failed) and Excluded — Platform (wrong site) are different
        # findings a reviewer needs to tell apart, per direction.
        status_counts = rows_for_operation["evidence_status"].value_counts().to_dict()
        breakdown = "; ".join(f"{count} {status}" for status, count in status_counts.items())
        return LaneResult(False, None, 0.0, f"No Complete JMS workpack evidence ({breakdown}, 0 Complete)", source)

    if len(complete_rows) < min_comparable_entries:
        return LaneResult(
            False, None, 0.0,
            f"Only {len(complete_rows)} Complete JMS workpack match(es) found, fewer than the "
            f"minimum of {min_comparable_entries} required — a single-document match is evidence, "
            "not grounds for an automatic recommendation",
            source,
        )

    mhr_values = complete_rows["total_manhours"].astype(float)
    median_mhr = float(mhr_values.median())
    citations = "; ".join(
        f"{r['source_pdf']} p.{r['source_page_number']}" for r in complete_rows.to_dict("records")
    )
    return LaneResult(
        True, median_mhr, JMS_WORKPACK_LANE_CONFIDENCE,
        f"Median of {len(complete_rows)} Complete JMS workpack matches is {median_mhr} MHR "
        f"(sources: {citations})",
        source,
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_evidence_reconciliation.py -v
```
Expected: all passing.

- [ ] **Step 5: Commit manually**

Commit — message like `feat: JMS workpack evidence lane, requiring 2+ independent Complete matches before recommending, distinguishing Incomplete from Excluded-Platform`.

---

## Task 4: Wire the Fourth Lane Into `run_pp5`

**Files:**
- Modify: `Agent_C_TaskList_MPlan/validation.py`
- Test: append to `Agent_C_TaskList_MPlan/tests/test_validation.py`

**Interfaces:**
- `_pp5_evidence_reconciliation_check` gains a `matched_jms_rows: pd.DataFrame | None` parameter, adds `"jms_workpack": jms_workpack_lane(record_key, matched_jms_rows)` to its `lanes` dict — no other change to that function's logic, since `reconcile_lanes` already handles an arbitrary number of lanes.
- `run_pp5` gains a `matched_jms_rows: pd.DataFrame | None = None` parameter, threaded through to the reconciliation check exactly like `historical_matches`/`oreda_db_path` already are.

- [ ] **Step 1: Write the failing tests**

```python
def test_pp5_jms_workpack_lane_recommends_only_with_two_or_more_complete_matches():
    df = pd.DataFrame(
        {
            "TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [3.0], "WORK_UNIT": ["MHR"], "PERSON": [1], "DURATION": [3.0], "DURATION_UNIT": ["HR"],
            "OPWKCEN": ["BMECH"], "CTRLKEY": ["INTN"], "STRATEGY": ["PCSB51"],
        }
    )
    matched_jms_rows = pd.DataFrame(
        [
            {"sap_record_key": "BODA582-10-10", "evidence_status": "Complete", "total_manhours": "24",
             "source_pdf": "a.pdf", "source_page_number": "13"},
            {"sap_record_key": "BODA582-10-10", "evidence_status": "Complete", "total_manhours": "26",
             "source_pdf": "b.pdf", "source_page_number": "9"},
        ]
    )
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR", matched_jms_rows=matched_jms_rows)
    reconciled = [f for f in findings if f.reason.startswith("Evidence-reconciled")]
    assert len(reconciled) == 1
    assert reconciled[0].recommended_value == "25.0"  # median of 24, 26


def test_pp5_jms_workpack_lane_does_not_recommend_from_a_single_complete_match():
    df = pd.DataFrame(
        {
            "TLGRP": ["BODA582"], "TLGRPCOUNT": ["10"], "TLOPNO": ["10"], "TLSUBOPNO": ["0"],
            "WORK": [6.0], "WORK_UNIT": ["MHR"], "PERSON": [1], "DURATION": [3.0], "DURATION_UNIT": ["HR"],
            "OPWKCEN": ["BMECH"], "CTRLKEY": ["INTN"], "STRATEGY": ["PCSB51"],
        }
    )
    matched_jms_rows = pd.DataFrame(
        [{"sap_record_key": "BODA582-10-10", "evidence_status": "Complete", "total_manhours": "24",
          "source_pdf": "a.pdf", "source_page_number": "13"}]
    )
    # WORK (6.0) != PERSON*DURATION (3.0) so the arithmetic check already
    # fires, and the reconciliation Finding is not suppressed — but it
    # must still say Needs Review, not silently promote the single JMS
    # match to a recommendation.
    findings = run_pp5(df, valid_work_unit="MHR", valid_duration_unit="HR", matched_jms_rows=matched_jms_rows)
    reconciled_recommendations = [f for f in findings if f.reason.startswith("Evidence-reconciled")]
    assert len(reconciled_recommendations) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v -k jms_workpack
```
Expected: FAIL — `TypeError: unexpected keyword argument 'matched_jms_rows'`.

- [ ] **Step 3: Update `validation.py`**

Add `matched_jms_rows: pd.DataFrame | None` to `_pp5_evidence_reconciliation_check`'s signature, add the `"jms_workpack": jms_workpack_lane(record_key, matched_jms_rows)` entry to its `lanes` dict (importing `jms_workpack_lane` alongside the other three lane imports), and add `matched_jms_rows: pd.DataFrame | None = None` to `run_pp5`'s signature, passed through at its call site.

- [ ] **Step 4: Run test to verify it passes, then the full suite**

```bash
cd Agent_C_TaskList_MPlan
pytest tests/test_validation.py -v -k pp5
pytest -q
```
Expected: all passing, no regressions.

- [ ] **Step 5: Commit manually**

Commit `validation.py`, `tests/test_validation.py` — message like `feat: wire JMS workpack evidence lane into run_pp5, requiring multiple independent matches before recommending`.

---

## Task 5: Wire Into `app.py` and Run Against Real Data

**Files:**
- Modify: `Agent_C_TaskList_MPlan/app.py`

**Interfaces:**
- `run_pipeline` reads `ground_truth_cache/PP05_JMS_ManHours.csv` (when present), runs `match_jms_to_operations` against `normalized_operations`, and passes the result to `run_pp5`'s new `matched_jms_rows` parameter — following the exact same "optional, only if the file exists" pattern already used for `historical_matches`/`oreda_db_path`.

- [ ] **Step 1: Add the ingestion block to `app.py`**, mirroring the existing historical-matching ingestion block (same location, same "only if the source files are present" guard).

- [ ] **Step 2: Run `python app.py` and report the real numbers** — how many of the 403 (or however many after Task 1-4's re-extraction) PP5 findings now have a JMS-workpack-sourced `available=True` lane, how many operations move from `NEEDS_REVIEW` to `RECOMMENDED` as a result, and how many JMS extraction rows landed in each `Evidence Status` bucket (Complete/Partial/No Match) — report these honestly, without assuming the join works well until the real numbers confirm it.

- [ ] **Step 3: Commit manually**

Commit `app.py` — message like `feat: wire JMS workpack evidence into the PP5 pipeline`.

---

## What This Plan Deliberately Does Not Include

- No changes to the Historical, Tasklist/Worklist, or OREDA lanes, or to `reconcile_lanes`'s no-averaging combination logic — confirmed these need no modification to accept a 4th lane.
- No re-enabling of PP1/PP2/PP3/PP4/PP6/PP7 in `app.py` — unrelated, stays as currently set.
- No assumption that the equipment-tag-based SAP matching in Task 2 will achieve high coverage — Task 5 measures and reports the real join rate rather than presupposing it, matching this project's established discipline (the same honesty standard applied to the original Step 2 historical-matching coverage report).
- No multiplying of manpower-only evidence (e.g. the V-1010 Lifting Plan) by an assumed or borrowed duration — `Evidence Status = Partial` rows never produce a candidate MHR, per direction.
