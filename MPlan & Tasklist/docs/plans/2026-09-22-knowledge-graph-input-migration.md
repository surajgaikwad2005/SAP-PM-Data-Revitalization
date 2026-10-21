# Switching from Excel Files to the Knowledge Graph — Simple Plan

**Status: Connected to the real database and checked everything directly. Ready to start building. Nothing has been changed in the main code yet.**

## What we're doing

Right now, our tool reads its input directly from Excel files (Task List Group, Long Text, Work Order history, etc.). We're switching it to read the same information from the Knowledge Graph (KG) instead — a database where these files have already been loaded.

**Good news: this is a low-risk change.** All the actual checking logic (PP1 through PP7) doesn't care where the data comes from — it only cares about getting a table with the right columns. So we only need to change the small part of the code that loads the data in, not the part that checks it.

## What I checked directly against the live database (not just the document)

Using the connection details provided, I connected to the real database and looked at everything myself.

| Question | What's actually true (checked live) |
|---|---|
| Does the KG have fewer Task List Operations than our files? | Yes, confirmed live: 1,813 in the database vs. 2,871 in our files. **Per your instruction, we are not chasing this — moving on with what the KG has.** |
| Is OREDA really in the KG? | **Yes, confirmed.** It's a plain table called `oreda_data`, 10,924 rows, with the exact same columns our current OREDA code already expects (`item`, `failure_mode`, `manhour_repair_mean`, etc.). This is an easy, low-risk swap — same shape of data, just read from the database instead of a local file. |
| Do KG field names match our current column names? | **Yes, confirmed** for the fields we checked — Task List Operation fields in the KG are `work`, `person`, `duration`, `work_unit`, `duration_unit`, `opdesc`, `ctrlkey`, `opwkcen` — all recognizable matches to what we already use, just lowercased. |
| Does the KG have hours broken down per individual job-step (not just per whole job)? | **No — checked directly, confirmed absent.** A real Work Order record in the database only has whole-job totals (`total_sum_actual`, `total_sum_plan`). There is no per-step hours field anywhere on it. **This means the KG does not solve PP5's main open problem — it's the same limitation as our current Excel file, just in a different place.** This was the one open question from before; it now has a definite answer. |

## Something new I found that wasn't in the original document

The live database has a few extra tables that the reference document never mentioned:
- **`bokor_eca_report`** (6,472 rows) — Functional Location and Equipment criticality information
- **`catalog_profile`** and **`process_subprocess`** (smaller reference tables — symptom codes and process codes)

These aren't needed for the current migration, but they may be useful ground truth for other pain points later. Flagging them now so nothing gets missed — happy to look into what's in them if useful.

## What matches correctly

- Task Lists: 951 in the KG, 951 in our file — matches.
- Maintenance Items: 8,025 in the KG (this is higher than our file's 5,823 — worth a quick sanity check later, not blocking).
- Equipment and Location data — present and matches in shape.
- OREDA — present, same structure as today.

## What stays as Excel/file for now (per your decision)

- **Timesheet files (2024/2025)** — stay as direct Excel reads. Will move to the KG later; when they do, we switch that piece over the same way.
- **PITSTOPS worklist files** and the **hand-extracted workpack man-hours file** — not in the KG yet either; same plan, stay as-is until they're added.

## How we'll do it

1. Build one small piece of new code whose only job is "ask the database for X" — nothing else touches this.
2. Replace our file-reading functions one at a time, in this order (simplest and safest first):
   - Equipment and Functional Location data
   - OREDA (straightforward — same table shape as today, just a different connection)
   - Task List Group data (Maintenance Items, Maintenance Plans, Task Lists)
   - Task List Operations
   - Work Order history (now confirmed: this will still only give whole-job totals, same as today — no loss, but no gain either)
3. For each one we switch, compare the old (Excel/file) result and the new (KG) result side by side to make sure they match before removing the old way.
4. Once everything is switched, re-run our full test suite and a full real data run, and compare the results to today's numbers to make sure nothing dropped or changed unexpectedly.
5. Only after that passes do we remove the old Excel-reading code — and even then, we can keep it available as a backup for a while if you'd prefer.
6. Timesheet, PITSTOPS, and the workpack file each get their own small follow-up switch later, once they're loaded into the database — same side-by-side check each time.

## What we will NOT do as part of this

- Not changing any of the actual pain-point checking logic (PP1–PP7).
- Not turning back on the pain points that are currently switched off.
- Not deleting any Excel files or old code until the new version is proven to match.
- Not chasing why the KG's operation count is lower than our files' — per your instruction, we work with what's there.
