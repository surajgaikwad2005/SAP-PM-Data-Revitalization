# PP5 — Planned Man-Hours Validation & Recommendation Architecture (Planning Only, No Implementation)

Status: planning only. Governing version of the PP5 plan, incorporating the corrected architecture (evidence reconciliation engine, recommendation eligibility gate, explicit OREDA branch), the first five review corrections, three further corrections (version/identity integrity of the match, actual-labour-vs-elapsed-duration meaning, and output-field clarity), and two final clarifications (execution-identity and Task-List-version are separate, independently-tracked attributes — not one collapsed tier; and Step 2B's own output is candidate/diagnostic data, never described as "usable" or "reconciled" ahead of an approved reconciliation rule). **Only the Step 2 data-coverage investigation — run as three sub-steps, 2A/2B/2C — is approved to start. Automatic recommendation generation is explicitly not approved yet.**

---

## 1. Objective

Validate existing SAP Task List man-hours and recommend realistic values using historical execution data and applicable reference evidence — without inventing a value where evidence is insufficient.

**Management framing:** the agent first checks whether SAP man-hours are mathematically correct, then compares the maintenance activity against relevant historical execution and reference data. It recommends evidence-supported man-hours or flags the record for client review when evidence is insufficient.

---

## 2. Corrected Architecture

```
SAP Task List Operation
  WORK + PERSON + DURATION + Activity
        |
        v
Arithmetic Validation (Layer 1)
  WORK = PERSON x DURATION
        |
        v
Independent Evidence
  +-- Historical: WO + Timesheets -> verified operation matching -> actual labour MHR -> historical median
  +-- OREDA: activity applicability -> equipment taxonomy -> repair benchmark (Min/Mean/Max MHR)
  +-- Tasklist + Worklist: equipment, activity, discipline and duration context
        |
        v
Evidence Reconciliation Engine
  matching quality + sample sufficiency + source consistency
        |
        v
Recommendation Eligibility Gate
  Is independent evidence sufficiently reliable?
     Eligible     -> Suggested MHR (confidence + evidence)
     Not eligible -> Review Flag (insufficient evidence)
        |
        v
Client Validation Output
  Actual + Suggested + Confidence + Evidence + Approval
```

This supersedes the architecture's previous shape (§2 of the prior revision) in three ways: it adds an explicit **Evidence Reconciliation Engine** between "gather evidence" and "decide," gives OREDA its own branch instead of folding it into Step 5 only, and makes the arithmetic-vs-historical disagreement an explicit reconciliation case rather than an implicit "never override" rule.

### 2.1 Data Input Layer (unchanged from prior revision)

| Source | Key fields | Role |
|---|---|---|
| SAP Task List | Group + Counter + Operation; `WORK`, `PERSON`, `DURATION`; Operation description | The record being validated |
| 10-Year Work Orders | Group + Counter; Work Order ID; planned/actual totals | Links a Task List to its historical execution instances |
| Timesheets (2024, 2025) | WO + Operation; actual labour hours | Ground-level actual-hours evidence |
| Reference Data | Tasklist + Worklist (PITSTOPS); OREDA repair benchmarks | Supporting comparability and repair-specific benchmarks |

### 2.2 What Is Already Available vs. What Must Be Developed

| Component | Status |
|---|---|
| Arithmetic validation | Implemented |
| PITSTOPS plausibility | Dormant; needs validation |
| Historical data files | Available (see §3 for exactly which, and in what real shape) |
| Historical operation matching | To validate — **and, per Correction 1 below, verified beyond the join key alone** |
| Evidence reconciliation (duplicate-source handling) | To develop — Correction 2 |
| Historical MHR recommendation | To develop |
| Recommendation eligibility gate | To define — Correction 4 |
| OREDA applicability | Scope decision needed — Correction 5 |
| Planning Norms | Unavailable (confirmed, §4) |

---

## 3. What Was Verified Against the Real Files

Six real files were opened and their actual columns inspected (read-only) — not assumed — because the whole point of the first execution step (§7) is to measure join feasibility, not presume it.

| File | Location | What it actually contains |
|---|---|---|
| `BOKOR_10years Work Order Data_Aug26.xlsx` | Already in `Agent_C_TaskList_MPlan/input/` | Sheet `Data`, ~73,662 rows. Has `Order`, `Maintenance Plan`, `Maintenance Item`, `Group`, `Group Counter`, `Total sum (actual)`, `Total sum (plan)`. **No Operation-level key** (no `TLOPNO`/`Activity` equivalent) — this file only proves which Task List/Plan an Order belongs to, at Order grain, not which Operation within it. **`Group`/`Group Counter` population rate in this specific file has not yet been measured** — see Correction 4b below; do not assume it matches the JMS file's rate. |
| `Timesheet BOKOR_2024.xlsx` / `_2025.xlsx` | `All_sites_Data/SAP/Planning Data/` — **not yet copied into Agent C's `input/`** | Sheet `Data`, ~124k and ~122k rows respectively. Real actual-hours evidence: `Number (unit)` (the logged hours/quantity), keyed by **`General receiver`** — a single string field formatted `"<8-digit Order> <4-digit Operation>"` (e.g. `'81516386 0010'`), confirmed present and well-formed in ~77% of sampled rows. Also carries a standalone `Activity` column (the same 4-digit operation number). No `Group`/`Group Counter`/`TLGRP` field of any kind. |
| `PITSTOPS/SKA/BOBELA TA 2024/Worklist.xlsx` / `TA 2026/Worklist.xlsx` | `All_sites_Data/SAP/Planning Data/PITSTOPS/SKA/...` — **not yet copied into Agent C's `input/`** | Sheet `Export`, 294 and 192 rows. Has a `WorkOrder` column intended for exactly this kind of join — but it is **100% empty in both extracts** (both TA windows are still in "Prelim" pre-approval status per the `Request` column, so no SAP Work Order has been created against them yet). `FuncLoc` is also fully empty in the 2026 file. **These two files cannot currently join to Work Order/Timesheet history at all** — they are only usable as Reference Data for equipment/discipline-type comparison, not for the Matching Engine's Work-Order join. |
| `M014_Bokor_Non PPM Work Order 2020_2025.xlsx` | `All_sites_Data/SAP/Planning Data/JMS/` — **not yet copied into Agent C's `input/`** | Two sheets. `Data` (4,329 rows) mirrors file 1's schema plus `Revision`/`Room`, with `Group`+`Group Counter` populated on only 158/4,329 rows (~3.6%). **This 3.6% figure applies only to this JMS extract — it must not be generalized to the separate 10-year Work Order file, whose own population rate is unmeasured (Correction 4b).** **`Operation Line` (6,536 rows)** is the strongest find: `Order` + `Activity` (4-digit) at operation grain, with real `Work` and `Actual work` columns — i.e. planned vs. actual hours already broken out per operation, exactly the "actual labour hours" the historical benchmark needs. |

**What this confirms about the Matching Engine:**
- The **Order + 4-digit Operation** shape (seen as `General receiver` in Timesheets, and as split `Order`/`Activity` columns in the JMS file's `Operation Line` sheet) is a candidate join key at operation grain — but per Correction 1 below, a shared `Order`+`Activity` value is necessary, not sufficient, for treating two records as the same real-world operation.
- Nothing inspected so far carries the literal `TLGRP`/`TLGRPCOUNT`/`TLOPNO`/`TLSUBOPNO` values outside Agent C's own three primary input files. The link from "today's Task List Operation" to "a historical Order+Operation that executed it" has to run through the **existing bridge file** (`Bokor Task List Group.xlsx`, which already carries `Maintenance Plan`/`Group`/`Group Counter`) and then from there to the Work Order files' own `Maintenance Plan`/`Group`/`Group Counter` fields — a two-hop join.
- **Correction to a prior claim in this plan:** an earlier revision stated the Task-List-Operation-to-bridge-file join (Hop 1, `TLGRP`+`TLGRPCOUNT` ↔ `Group`+`Group Counter`) was "already proven and used by PP6." That citation was wrong — `run_pp6` is not called anywhere in `app.py`'s active pipeline today (verified: PP1, PP2, PP5, PP6, PP7 are all commented out of the live run, with only PP3 and PP4 active), so PP6 demonstrates this join only inside unit tests with synthetic data, not in production. The correct citation is **PP3** (`validation.py::run_pp3`, currently active in `app.py`), which builds `bridge_keys = set(zip(task_list_group["Group"], task_list_group["Group Counter"]))` and joins it against `TLGRP`/`TLGRPCOUNT` from normalized Long Text operations as its live orphan-detection logic. Hop 1 is genuinely proven in production — just via a different pain point than originally cited.

---

## 4. Ground Truth Hierarchy

There is no single authoritative ground truth for PP5's suggested MHR. Planning Norms — the one source that would have qualified outright — are confirmed unavailable (tracker ID 54 in `All_sites_Data/SAP/Bokor_Data_Update_Review_2026-09-15.md`: entire SAP folder searched for "norm," zero hits, status remains "Requested (15%)"). This is a settled fact as of today, independently corroborated by the client's own data tracker, not an open question requiring further searching.

| Evidence source | What it proves | Can it establish the suggested MHR? |
|---|---|---|
| Approved Planning Norm | Official standard effort | Yes, if available and applicable — **not available** |
| Historical Timesheets | Actual labour consumed | Yes, as a statistical recommendation after reliable matching |
| Historical Work Orders | Task List linkage and planned/actual execution context | Supporting evidence; totals must be checked for labour-hour meaning |
| Tasklist + Worklist | Comparable tasks and reference durations | Supporting evidence; duration must be converted correctly to MHR |
| OREDA | Industry repair man-hour statistics | Supporting benchmark for applicable repair work only |
| Client maintenance SME | Whether the proposed effort is appropriate | Can approve the recommendation as the accepted value |

**For the current PP5 implementation: historical actual labour is the primary quantitative evidence, not an authoritative standard.**

### 4.1 Two Different Types of Ground Truth

**A. Arithmetic ground truth.** If `PERSON = 2`, `DURATION = 4 HR`, current `WORK = 6 MHR`, then `2 × 4 = 8 MHR` is the deterministic correction — assuming `PERSON` and `DURATION` are themselves correct. This does **not** prove the maintenance activity actually requires 8 MHR; it only proves internal consistency. This is Layer 1, already implemented, confidence 1.0, and stays exactly as-is.

**B. Maintenance-effort ground truth.** A historical benchmark (e.g. 5 MHR) can be proposed, but historical data alone does not prove 5 MHR is the approved standard — a maintenance SME must validate whether the historical jobs had comparable scope, conditions, and resource requirements. This is Layer 3, and its output is a **suggestion pending approval**, never a correction with the same epistemic weight as Layer 1's arithmetic.

**Practical consequence:** Layer 3's output must never be labeled or treated as equivalent to Layer 1's. Until client approval, output is labeled **Suggested MHR**, not **Ground Truth MHR**.

### 4.2 Correction 3 — Arithmetic and Historical Disagreement Is a Reconciliation Case, Not a Silent Override

Keeping Layer 3 from overriding Layer 1 is necessary but not sufficient — a disagreement between them must be surfaced explicitly, not dropped. Worked example:

| Field | Value |
|---|---|
| Current WORK | 6 MHR |
| PERSON × DURATION (arithmetic correction) | 8 MHR |
| Historical benchmark (Layer 3) | 5 MHR |

Neither number proves the correct maintenance effort by itself. The agent must report **both** findings — the arithmetic inconsistency (6 → 8, confidence 1.0, per Layer 1's existing rule) and the historical benchmark (8 vs. 5, informational, per Layer 3's rule) — attached to the same operation, with an explicit **conflict/review status** rather than silently picking one or merging them into a single number. This is a new, distinct output requirement (see §9's output schema) beyond "Layer 3 must not override Layer 1" — it says what to do *with* the disagreement, not just that Layer 1 wins.

---

## 5. What Stays Exactly As-Is (Layer 1)

`_pp5_row_check` / `run_pp5`'s completeness gate, unit-scope gate (`MHR`/`HR` per `config/unit_rules.yaml`), and `WORK = PERSON × DURATION` arithmetic check (confidence 1.0 on a mismatch, citing UDMS §9.20-21) — untouched by everything in this plan.

---

## 6. Implementation Roadmap

**Step 1 — Validate current man-hours (Layer 1).** Existing, unchanged. Already implemented, tested, correct.

**Step 2 — Connect historical data (Matching Engine).** Prove the join chain (Task List Operation → Work Order → Timesheet → Actual Labour Hours) actually resolves at usable coverage before any recommendation logic is written. **This is the only step approved to execute now** — see §7. Per Correction 1, "resolves" means more than a shared join key — see §7.1.

**Step 3 — Find comparable maintenance activities (Layer 2 input).** Once Step 2's coverage is known, use `Tasklist.xlsx`/`Worklist.xlsx` as supporting Reference Data to compare equipment type, maintenance activity, discipline, and operation description. Per §3: the two `Worklist.xlsx` files cannot supply a Work Order join (empty `WorkOrder` field) — they contribute discipline/equipment-type comparability context only. **Not approved to start yet.**

**Step 4 — Calculate historical benchmark (Layer 3).** For operations with sufficient comparable historical executions, calculate a representative value (e.g. median actual MHR). Gated on the Recommendation Eligibility Gate (§8) being defined first — Correction 4. **Not approved to start yet.**

**Step 5 — Check OREDA applicability.** Given its own explicit branch in §2's corrected architecture — Correction 5, detailed in §8.1. **Not approved to start yet.**

**Step 6 — Generate recommendation (Recommendation Decision Engine → Client Output).** Produce suggested man-hours, confidence, and supporting evidence; flag for review where evidence is insufficient; report arithmetic/historical conflicts explicitly per §4.2. **Not approved to start yet.**

---

## 7. Approved Task: Step 2 — Historical Data Relationship Validation

**Goal:** produce a data-coverage report, not a recommendation engine. Measure how many Task List Operations have a reliable historical match before writing any benchmark logic. **This is the only work approved at this stage, and it runs as three sub-steps in sequence:**

- **Step 2A — Validate data relationships.** Measure Task List → Work Order → Operation matching coverage (§7.3's join table, §7.1/§7.1a's key-vs-verified-match distinction and version-integrity check).
- **Step 2B — Validate actual labour evidence.** Check units and field meaning, timesheet aggregation, duplicate sources, and historical operation identity (§7.2, §7.2a).
- **Step 2C — Produce coverage report.** Report execution-verified matches (split by version confidence), candidate actual hours, and unmatched reasons (§7.4).

Steps 3-6 (the recommendation engine) wait for Step 2's results across all three sub-steps.

### 7.1 Correction 1 — Operation Match Requires More Than a Shared Key

A shared `Order`+`Activity` value (e.g. operation `0010`) is **necessary but not sufficient** to treat a historical execution as the same real-world operation as today's Task List Operation — operation `0010` in one historical Work Order is not automatically the same activity as operation `0010` in today's Task List, since operation numbers are reused across different job types.

**Added requirement:** before accepting an `Order+Activity` match as evidence, verify:
- **Operation description** similarity (historical `Op. Short Text`/Timesheet `Short Text` vs. today's Task List `OPDESC`/`LONGTEXT_AGGREGATED`).
- **Equipment** consistency (same Equipment ID or Functional Location across the historical Order and today's Task List, via the existing bridge-file/Agent-A-equipment linkage).
- **Activity scope** (e.g. `Activity Type`/`Control Key` consistency, not just the numeric operation code).
- **Available historical Task List references**, where the historical Work Order itself carries a `Maintenance Plan`/`Task List` reference back to a Group+Counter — cross-check that this, where present, points to the *same* Task List Group being validated, not merely a plausible one.

This is a verification step within Step 2's coverage measurement, not a separate step — the coverage report (§7.3) must report matches at two tiers: "key match" (shares `Order`+`Activity`) and "verified match" (key match plus the above), so the eventual benchmark logic in Step 4 only ever draws from verified matches.

### 7.1a Further Correction — Task List Version/Identity Integrity, and a Known Data Gap

Beyond Correction 1's description/equipment/activity-scope checks, the match must also account for **Task List version drift**: a historical Work Order may have executed against a different revision of the Task List than the one being validated today, or against a Task List whose operations were later modified (added, removed, renumbered). Matching purely on `Order`+`Activity`+description/equipment similarity can still silently pair today's Operation with a historical execution of a *since-changed* version of the same nominal Task List.

Where the data supports it, the verified-match tier should additionally check:
- **Task List revision or validity date** — was the Task List itself the same version at the time of the historical execution as it is today?
- **Historical operation description and equipment** — already covered by Correction 1, restated here as part of the same version-integrity concern.
- **Suboperation identity**, where applicable (`TLSUBOPNO`-equivalent) — not just the top-level operation number, in case a single Order+Activity number covers multiple suboperations that were split or merged differently over time.
- **Historical execution date** — needed both to sanity-check plausibility (a very old execution may reflect an outdated Task List) and to support later trend analysis.

**Known data gap, stated rather than papered over:** based on the files inspected so far (§3), **no field carrying a Task-List-level revision number or validity date has been found** — `Bokor Task List Group.xlsx` carries `Changed On`/`Created On` for the bridge-file record itself (i.e. when that row was last edited in SAP), not a Task List content-version indicator. The only "Revision" field found anywhere in this project's data is on the Work Order side (`M014_Bokor_Non PPM Work Order 2020_2025.xlsx`'s `Data` sheet `Revision` column, and the newer `M014_WO_NN Listing_Jan2026_BOKOR.xlsx` — both carry TA/SD-window revision tags like `QTWL0725`, per the 2026-09-15 data-inventory review), which identifies which turnaround/shutdown window a Work Order belongs to, not which version of a Task List template it executed against. The `Operation Line` sheet's `Execution Start Date`/`Execution End Date` columns do give a real historical execution date, which is available and should be used.

**Per the instruction that governs this case:** since Task-List-version/validity-date information is not currently available, this limitation must be **recorded explicitly in the coverage report and carried into the eventual output** (§9's evidence field) — a match must never be labeled "fully verified" on the strength of operation-number, description, and equipment agreement alone if version/validity information could not be checked.

**Clarification — these are two separate attributes, not one collapsed tier.** A historical Work Order operation can be **reliably identified as the same execution** (via Correction 1's operation-number/description/equipment/activity-scope agreement) independent of whether the **Task List version** it ran against can also be confirmed. Record both as distinct fields on every match, not as a single combined status:
- **Execution-identity confidence**: `verified` / `key-match-only` — whether Correction 1's checks passed.
- **Version confidence**: `version-checked` / `version-unconfirmed` — whether §7.1a's version/validity check could be performed at all (today, given the data gap, this is `version-unconfirmed` for every match, with no exceptions until a version source is found).

A match can therefore be `execution: verified` + `version: unconfirmed` — this is a legitimate, common, and expected combination given the current data, not a downgraded or defective match. **Whether execution-verified-but-version-unconfirmed matches qualify as evidence for a recommendation is an eligibility question, not a data-quality verdict** — it is explicitly deferred to §8's Recommendation Eligibility Gate, to be decided *after* the coverage report shows how many matches actually fall into each combination (if nearly all matches are version-unconfirmed, treating them as automatically unusable would eliminate the evidence base entirely; if only a few are, a stricter rule may cost little). Step 2's coverage report must report the four-way split (verified/version-checked, verified/version-unconfirmed, key-match-only/version-checked, key-match-only/version-unconfirmed) as a measurement, and take no position on which combinations are usable.

### 7.2 Correction 2 — Duplicate Actual-Hour Counting Must Be Prevented

Both the Timesheet files and the JMS `M014_Bokor_Non PPM Work Order 2020_2025.xlsx`'s `Operation Line` sheet contain actual-hour evidence, and they may describe the same real-world execution (both key on `Order`+`Activity`, just under different column names — Timesheet's `General receiver`/`Number (unit)` vs. `Operation Line`'s `Order`+`Activity`/`Actual work`).

**Added requirement:** reconcile actual hours using `Order`+`Activity` as the common key across both sources before any aggregation:
- For a given `Order`+`Activity`, if both sources report a value, compare them — do not sum them, since they may well be reporting the same underlying labour.
- Select one source as authoritative per record (or reconcile a genuine difference with a stated reason, e.g. one source is a Timesheet-logged partial entry and the other an Order-level total), and document which rule was applied.
- Never combine Timesheet and Operation-Line hours for the same `Order`+`Activity` without first proving they represent distinct labour (e.g. different personnel, different date ranges within the same operation) — the default assumption is that they describe the same execution until shown otherwise.

This reconciliation logic belongs conceptually to the new **Evidence Reconciliation Engine** in §2's corrected architecture, but for Step 2 specifically it only needs to be *measured* (how often do both sources have a value for the same key, and do the values agree or conflict?) — not yet implemented as production logic.

### 7.2a Further Correction — Actual Labour Hours vs. Elapsed Duration, and Data-Quality Noise

§8's eligibility gate already requires checking that Timesheet and `Operation Line` values are in a labour-hour unit compatible with Task List `WORK` (MHR) — but unit compatibility alone does not establish that a field *means* labour effort. Two numerically similar fields can measure different things (e.g. person-hours actually worked vs. wall-clock elapsed time for a job with a crew, which differ by a factor of crew size), and a benchmark built on the wrong meaning would be wrong regardless of correct units.

**Added requirement, to measure (not yet resolve) during Step 2B:**
- Confirm what Timesheet's `Number (unit)` actually represents — per the earlier file inspection, `Internal UoM` is a real column in both Timesheet files and has not yet been read; it must be checked directly rather than assumed to always mean "labour hours" for every row.
- Confirm `Operation Line`'s `Actual work` is genuinely actual labour effort (crew-hours) and not, for example, elapsed job duration or a planned-vs-actual variance figure under a similar name.
- **Reversed entries, cancellations, and corrections**: Timesheet's own `Correction Indicator` column (seen in the file inspection) suggests corrected/reversed rows exist in the data — these must be identified and excluded (or netted) before aggregation, not treated as additional independent labour entries. A cancelled or corrected Timesheet line counted at face value would inflate or distort the benchmark.
- **Multiple Timesheet rows per execution**: a single real-world operation execution can generate several Timesheet rows (e.g. per person, per day, per correction) — these must be aggregated to one figure per `Order`+`Activity` execution before being used as a single data point in the historical sample, not treated as separate comparable executions in Step 4's sample-size count.

**Principle:** the benchmark must eventually be built from validated actual labour effort, not simply every numeric value found in a column that happens to be named something like "actual hours" — but Step 2B itself does not perform that validation, only measures toward it. **Correction — do not claim "usable" or "reconciled" hours as a Step 2B output.** Reconciliation rules (which source is authoritative, how to treat a disagreement, what counts as a duplicate vs. distinct labour) are not yet approved (§10 D4), and unit/meaning confirmation (§7.2a's own open questions) is not yet complete — so no hour value can honestly be called "usable" this early. Step 2B's actual deliverable is a set of **candidate** figures and diagnostics only:
- **Valid-unit candidate hours** — a value that passed the `Internal UoM`/unit-plausibility check, without yet asserting it represents the correct real-world quantity or has been reconciled against the other source.
- **Source overlap** — how often Timesheet and `Operation Line` both report a candidate value for the same `Order`+`Activity`.
- **Discrepancies** — the size and direction of disagreement where both sources have a candidate value, without resolving which is right.
- **Correction-indicator counts** — how many rows carry a `Correction Indicator`/reversal marker, reported as a fact, without yet deciding the rule for excluding or netting them.

None of these get promoted to "usable," "validated," or "reconciled" until §10 D4 (the reconciliation rule) and §7.2a's unit/meaning questions are both explicitly resolved — that resolution happens after the coverage report, using the report's own findings, not during Step 2B itself.

### 7.3 Join Table (Corrected)

| Hop | From | To | Real join field(s) | Status |
|---|---|---|---|---|
| 1 | Current Task List Operation (`Bokor Long Text`, normalized) | Bridge file (`Bokor Task List Group.xlsx`) | `TLGRP+TLGRPCOUNT` ↔ `Group`+`Group Counter` | **Proven in production** — this exact join is PP3's live orphan-detection logic (`validation.py::run_pp3`), currently active in `app.py`. (Corrected: an earlier revision of this plan mis-cited this as "used by PP6," which is disabled in the live pipeline and only exercises this join in unit tests — see §3.) |
| 2 | Bridge file | Historical Work Order (`BOKOR_10years Work Order Data_Aug26.xlsx` **and, separately,** `M014_Bokor_Non PPM Work Order 2020_2025.xlsx`'s `Data` sheet) | `Maintenance Plan`/`Group`+`Group Counter` | Partially proven — PP1/PP4 already join the 10-year Work Order file to Task Lists this way in production. **Coverage must be measured independently for each of the two Work Order sources** (Correction 4b) — the ~3.6% figure found so far applies only to the JMS non-PPM extract; the separate 10-year Work Order file's own population rate for `Group`/`Group Counter` has not yet been checked and must not be assumed to match. |
| 3 | Historical Work Order (`Order`) | Timesheet (`Order`+`Operation`, via `General receiver` split on the space delimiter) | `Order` | Field confirmed present and well-formed (~77% of sampled Timesheet rows); coverage against the specific Orders reached via Hop 2 is unmeasured. Subject to Correction 1's verified-match requirement, not just key presence. |
| 3′ (alternative/parallel route) | Historical Work Order (`Order`) | JMS file's own `Operation Line` sheet (`Order`+`Activity`, with `Work`/`Actual work` present) | `Order`+`Activity` | May be a more direct path to actual per-operation hours than Timesheet. **Must be reconciled against Hop 3's Timesheet result per Correction 2, not simply added as a second source.** |

### 7.4 Deliverable — Data-Coverage Report

Showing, for the population of Task List Operations currently in scope for PP5 (i.e. those the arithmetic check already evaluates):
- **(Step 2A)** How many Task List Operations reach a bridge-file `Group`+`Group Counter` match (Hop 1).
- **(Step 2A)** Of those, how many resolve to at least one historical `Order` — **reported separately for the 10-year Work Order file and the JMS non-PPM Work Order file**, not combined into one figure (Correction 4b).
- **(Step 2A)** Of those Orders, how many have a **key match** (`Order`+`Activity`/`Operation`) in Timesheet and/or `Operation Line`, and of those, how many are **execution-verified** per Correction 1 (description/equipment/activity-scope agreement) — reported as the four-way split from §7.1a (execution-identity confidence × version confidence), since execution verification and version confirmation are separate attributes, not one combined tier. Eligibility for recommendations is not decided here — that's §8's job, after this report exists.
- **(Step 2B)** Confirmation of what `Number (unit)`/`Actual work` actually measure (per §7.2a), and how many raw Timesheet/`Operation Line` rows carry a `Correction Indicator`/reversal marker, reported as a count — not yet excluded, netted, or otherwise resolved.
- **(Step 2B)** Where both Timesheet and `Operation Line` have a candidate value for the same `Order`+`Activity`: the source-overlap rate, and the size/direction of any discrepancy where both exist — measured, not resolved (the reconciliation rule itself is §10 D4, decided after this report).
- **(Step 2B)** How many **valid-unit candidate** actual-hour figures result per Operation — explicitly not described as "usable," "reconciled," or "validated," since those labels require the unit/meaning confirmation and reconciliation rule that this step only measures toward, per §7.2a's correction.
- **(Step 2C)** Unmatched records at each hop, with a reason category, so a later reviewer can see *where* the chain breaks — this is the consolidated report itself, drawing on 2A's and 2B's measurements.

**Data this task needs copied into scope (not yet in `Agent_C_TaskList_MPlan/input/`):**
- `Timesheet BOKOR_2024.xlsx`, `Timesheet BOKOR_2025.xlsx`
- `M014_Bokor_Non PPM Work Order 2020_2025.xlsx` (both its `Data` and `Operation Line` sheets)
- `PITSTOPS/SKA/BOBELA TA 2024/Worklist.xlsx`, `TA 2026/Worklist.xlsx` (for Step 3 later, not Step 2)

This is a data-sourcing/scoping note only — no copying is proposed to happen as part of this planning document.

---

## 8. Recommendation Eligibility Gate (Correction 4)

Before Step 4 can generate any suggested value, the following must be explicitly defined — none of these are resolved by this plan, and Step 4 does not start until they are:

| Rule | Question it answers | Depends on |
|---|---|---|
| Minimum comparable executions | How many verified-match historical executions are required before a benchmark is trusted? | Step 2's coverage numbers (§7.4) — cannot be set meaningfully before real counts are known |
| Match-quality requirements | What counts as "comparable" — how strict must Correction 1's description/equipment/activity-scope agreement be? | Step 2/3 findings on how much data survives strict vs. loose matching |
| Valid labour-hour units | Are Timesheet `Number (unit)` and `Operation Line` `Actual work` in the same unit as Task List `WORK` (MHR), or do they need conversion? | Direct inspection of real unit values in both sources — not yet checked |
| Outlier rules | How are implausible historical values excluded from the benchmark (e.g. a mis-logged 400-hour entry)? | Real distribution of actual hours per discipline, once Step 2/3 data is available |
| Handling of incomplete historical records | What happens when an operation has some but not enough verified matches — review flag, or a lower-confidence benchmark? | The minimum-comparable-executions rule above |

Only once these are answered does the gate have a defined "Eligible"/"Not eligible" boundary; until then, **no suggested MHR should be produced**, per the Final Decision in §11.

### 8.1 Correction 5 — OREDA as an Explicit Evidence Branch

OREDA gets its own branch in the corrected architecture (§2), not just a mention in Step 5:

```
Operation -> Repair Activity Check -> OREDA Taxonomy Match -> Repair MHR Benchmark
```

- **Repair Activity Check:** is this Task List Operation itself a corrective-repair activity (as opposed to routine planned maintenance)? Identifiable candidates: `TLTYPE`, `CTRLKEY`, `STRATEGY` — needs checking against real data to see if any Bokor Task List Operations are corrective-type at all, since PP5's current scope is planned PM.
- **OREDA Taxonomy Match:** if the operation is repair-type, does OREDA have a matching equipment-category table (per the existing `is_oreda_applicable_to_pp5` connector logic)?
- **Repair MHR Benchmark:** if both checks pass, OREDA's Min/Mean/Max MHR for that category becomes supporting evidence — never a substitute for planned PM hours.
- **If no valid match exists at either check:** record `OREDA_NOT_APPLICABLE` with the specific reason (not repair-type / no taxonomy match / both), as a first-class, visible output rather than a silent skip. This is a change from the current `is_oreda_applicable_to_pp5`'s unconditional `(False, reason)` — the corrected architecture wants that reason surfaced per-operation in the evidence output, not just logged.
- **When a benchmark is produced, the evidence record must capture more than the number itself:** the matched OREDA equipment taxonomy category, the specific repair activity/failure context the benchmark came from, the benchmark's unit, and a source reference (which OREDA table/row). A bare taxonomy-category match should not by itself qualify a benchmark if the actual repair scope differs from what's being validated — recording these details is what lets a reviewer catch that mismatch later, rather than trusting a category label alone.
- OREDA remains supporting evidence throughout — it must never automatically replace or outrank a historical Timesheet/Work-Order-derived benchmark; where both exist for the same operation, both are recorded (per §9's output schema), not merged into one number.

---

## 9. Client Output Schema (Recommendation Decision Engine → Client Validation Output)

### 9.1 Correction 3 — Separate Current, Arithmetic, and Historical Values

The previous revision's schema used a single field labeled "Actual WORK," which is ambiguous: "actual" naturally reads as *executed labour* (the historical/Timesheet sense), whereas the current SAP Task List `WORK` field is *planned* effort, not something that was executed. Conflating the two in one field risks a reader mistaking a historical actual-hours figure for what SAP currently has on record, or vice versa. The schema is corrected to keep every value distinct and separately labeled:

| Output field | Example |
|---|---|
| Current Planned WORK | 6 MHR |
| Arithmetic Expected WORK | 8 MHR |
| Historical Benchmark | 5 MHR |
| Suggested Planned WORK | Pending review |
| Arithmetic Status | Mismatch |
| Evidence Status | Conflict |
| Recommendation basis | Historical Timesheets |
| Comparable executions | 12 (verified matches only, per §7.1/§7.1a — never raw key matches) |
| Confidence | Calculated from approved evidence rules (§8) |
| Evidence | Matching Work Order IDs and timesheet records (reconciled per §7.2, validated per §7.2a) |
| OREDA status | `OREDA_NOT_APPLICABLE (reason)`, or a repair benchmark with taxonomy category, activity/failure context, unit, and source reference (per §8.1) |
| Client validation | Pending |

`Arithmetic Status` and `Evidence Status` together implement §4.2's conflict/review requirement: `Arithmetic Status` reports Layer 1's own result (`Match`/`Mismatch`) independent of any historical evidence, while `Evidence Status` reports whether the arithmetic result and the historical benchmark agree (`Consistent`) or disagree (`Conflict`) — so a reader can see both without needing to infer a conflict by comparing two differently-labeled numbers themselves. `Suggested Planned WORK` is only ever populated once the Recommendation Eligibility Gate (§8) is satisfied and, per §4.1, is never presented as more than a suggestion pending client/SME approval — it stays `Pending review` (not a number) whenever eligibility isn't met or an unresolved conflict exists.

Historical records used to calculate each recommendation must be retained so the client can reproduce and challenge the result.

**Labeling rule (§4.1):** until client approval, output is labeled **Suggested Planned WORK** (never **Ground Truth WORK**, and never conflated with **Historical Benchmark**, which is evidence, not a recommendation in its own right). `Client validation` starts at `Pending` for every Layer-3-sourced recommendation.

---

## 10. Decisions Still Needed From the Client

| # | Decision | Why | Status |
|---|---|---|---|
| D1 | Confirm OREDA's narrow applicability scope (§8.1) once it's known whether any corrective-repair-type Operations exist in the Bokor Task List data | Avoids building unused logic for a case that may not exist in this dataset | Open |
| D2 | ~~Confirm whether Planning Norms/historical timesheet data exist~~ | **Resolved.** Planning Norms confirmed absent. Historical timesheet data confirmed present. | Closed |
| D3 | Minimum comparable executions, match-quality requirements, valid labour-hour units, outlier rules, and incomplete-record handling (the full Eligibility Gate, §8) | Cannot be set meaningfully before Step 2's coverage numbers are known | Open, deferred until after Step 2 |
| D4 | Reconciliation rule when Timesheet and `Operation Line` disagree on actual hours for the same `Order`+`Activity` (§7.2) | Determines whether one source is authoritative, or a documented tie-break rule is needed | Open, deferred until Step 2 measures how often this actually happens |
| D5 | Whether an arithmetic/historical conflict (§4.2) is surfaced as a distinct Finding requiring human review, or folded into the existing PP5 Finding with an added conflict field | Determines the output schema's exact shape, not just its content | Open |
| D6 | Whether the absence of any Task-List-version/validity-date field (§7.1a) is acceptable as a permanent limitation (every match stays `version-unconfirmed`, though independently still eligible for `execution: verified`), or whether the client can point to a version/revision source not yet surveyed; and, once the coverage report shows the real split, whether execution-verified/version-unconfirmed matches are treated as eligible evidence for a recommendation | Directly determines whether the `version-checked` state in §7.1a is ever reachable, and separately, whether the (likely dominant) execution-verified/version-unconfirmed population is usable evidence at all or requires its own confidence discount | Open, deferred until after the coverage report per Correction 1's clarification (§7.1a) |
| D7 | Confirm what Timesheet `Number (unit)`/`Internal UoM` and `Operation Line` `Actual work` actually measure (labour-hours vs. elapsed duration), and the rule for handling `Correction Indicator`-flagged reversed/corrected rows (§7.2a) | Required before any value from either source can be trusted as "actual labour effort" rather than just "a number in a column with a similar name" | Open, to be answered by direct data inspection during Step 2B, not assumption |

---

## 11. Final Decision

**Approved:** proceed with Step 2 — historical data relationship validation, run as three sub-steps:
- **2A** — validate data relationships (join coverage per §7.3, key-vs-verified match tiers per §7.1, version-integrity limitation recorded per §7.1a).
- **2B** — validate actual labour evidence (units, field meaning, reversal/correction handling, and aggregation per §7.2/§7.2a; duplicate-source reconciliation measurement per §7.2).
- **2C** — produce the coverage report (§7.4), consolidating 2A and 2B into execution-verified-match counts (split by version confidence), candidate actual-hour figures, and unmatched-reason categories.

**Not approved:** automatic recommendation generation (Steps 3-6). No suggested MHR, benchmark calculation, or eligibility-gate implementation happens until Step 2's three sub-steps are complete and reviewed.

Once the coverage report is available, the matching, sample-size, reconciliation, unit/meaning, and confidence rules (§8, §10) must be defined before any recommendation-engine implementation begins. No further architecture redesign is anticipated at this stage — the corrected architecture in §2, as amended by all eight corrections above, is the target shape.

---

## 12. What This Plan Deliberately Does Not Include

- No join code, no benchmark calculation, no config changes, no output-writer changes — planning only.
- No proposal to copy the newly identified files into `Agent_C_TaskList_MPlan/input/` yet.
- No assumption that Step 2's coverage will turn out to be high, or that the 10-year Work Order file's `Group`/`Group Counter` population rate matches the JMS file's ~3.6% — both are to be measured independently.
- No summing of Timesheet and `Operation Line` actual hours without first proving they represent distinct labour.
- No treatment of a shared `Order`+`Activity` key alone as sufficient evidence of a true operation match — nor treatment of a description/equipment/activity-scope-verified match as "version-checked" absent an actual Task-List-version signal (§7.1a).
- No assumption that Timesheet `Number (unit)` or `Operation Line` `Actual work` mean labour-hours without checking `Internal UoM` and the field's real content, and no inclusion of `Correction Indicator`-flagged reversed/corrected rows at face value in any aggregate (§7.2a).
- No re-enabling of PP1/PP2/PP6/PP7 alongside PP5 — each stays gated on its own remaining items (see prior revision's §11 for detail, unchanged here).
- No collapsing of arithmetic ground truth (Layer 1) and maintenance-effort ground truth (Layer 3) into one confidence scale, one output label, or one silently-resolved value where they disagree — nor collapsing "current planned," "arithmetic expected," and "historical benchmark" into a single ambiguous "Actual WORK" field (§9.1).
- No treatment of `execution-verified`/`version-unconfirmed` as an automatically-disqualified or lesser match tier — it is a legitimate, expected combination given the current data, and its eligibility for recommendations is a §8 decision made after the coverage report exists, not a data-quality verdict made during Step 2 itself (§7.1a).
- No use of "usable," "reconciled," or "validated" to describe Step 2B's own output — its deliverable is candidate/valid-unit figures, source-overlap rates, discrepancies, and correction-indicator counts, pending the unit/meaning confirmation and reconciliation rule that only get decided afterward (§7.2a).
