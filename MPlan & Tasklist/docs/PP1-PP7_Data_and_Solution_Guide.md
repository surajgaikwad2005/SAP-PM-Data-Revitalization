# PP1–PP7: What We Check and How We Solve It

This document explains, in plain language, what each pain point (PP1 to PP7) checks, what data it needs, and how the agent tries to fix or flag the problem. It is based directly on the real code in `validation.py`, not a plan or a proposal — this is what the system actually does today.

**Current status:** Right now, only **PP5** is switched on in `app.py`. PP1, PP2, PP3, PP4, PP6, and PP7 are all written and tested, but temporarily turned off so PP5's output can be reviewed on its own. Turning any of them back on is a one-line change (uncomment the block in `app.py`).

A few words used everywhere below:
- **Verified / Recommended value** — the agent is confident enough to suggest a specific correct value.
- **Candidate value** — the agent has a possible answer, but it is not fully proven. A person needs to review it before it's accepted.
- **Flag only** — the agent found a real problem but has no safe way to suggest a fix. It just reports the issue.
- The agent **never guesses**. If there isn't enough real evidence, it says so instead of inventing a number or a name.

---

## PP1 — Task List Group Naming

### What we need to validate
Every Task List has a short code called the **Group** (e.g. `BOKOPUCE`). The rule (from the client's UDMS manual, section 9.4) says this code should be built as:

```
<Asset Location (4 letters)><Object Type (4 letters)>
```

For example, `BOCP` (a platform) + `PUCE` (Centrifugal Pump) = `BOCPPUCE`.

We need to check:
1. Does the Group start with one of the approved platform codes (BOKO, BOCP, BOKA, BODA, BODB, BODC, BODD, BODE, BODF, BOPA, BOVA)?
2. Does the second half of the Group actually match the real equipment this Task List is used on?
3. Is there a separate naming rule for Safety Critical Element (SCE) Task Lists, and are those followed too?

### How we solve it
We run four checks:

**Check 1 — Does the prefix match an approved platform code?**
If the first 4 letters of the Group aren't one of the approved codes, we flag it. If the same bad code is reused across 4+ different Task Lists, we treat that as a stronger signal something is systematically wrong (higher confidence flag).

**Check 2 — Is the "Location" part actually correct?**
We look at the real equipment (Functional Locations) linked to that Task List. If all of them point to the same platform, we treat that platform as *verified*. But real data shows about 1 in 4 Task Lists are linked to *multiple* platforms at once — in that case, we cannot safely say which one owns it, so we mark it "needs review" instead of guessing.

**Check 3 — Is the "Object Type" part actually correct?**
We look at what kind of equipment this Task List has historically been used on (from 10 years of Work Order history). If that equipment consistently matches a known code (we currently only have confirmed codes for Pump types — Centrifugal, Diaphragm, Gear, Jet, Progressive, Plunger, Reciprocating — because that's all the source document has clearly printed), we treat that as verified.

If there's no official code, we also try a softer method: checking if other, unrelated Task Lists use the same 4-letter suffix and consistently point to the same kind of equipment. If they do, we treat it as a *hint*, never proof — this suffix pattern has been tested and found unreliable in places (the same suffix can mean completely different equipment on different platforms), so it can only ever produce a **candidate**, never a final answer.

**Check 4 — SCE naming**
Safety Critical Element Task Lists are supposed to follow their own version of the naming rule. We flag when a Task List is marked SCE, but we cannot yet check if the naming itself is correct — there's no official list of approved SCE codes anywhere in the data we have.

### What you get
- **Fully verified fix** — only when *both* the Location and the Object Type are proven correct from real data. Example: "Location verified as BOCP, equipment confirmed as Centrifugal Pump → Group should be BOCPPUCE, not BOKOMRPR."
- **Candidate (needs review)** — when only one side is proven, or the equipment is spread across multiple platforms.
- **Flag only** — when we can't determine anything useful (no equipment history at all).

### Known gaps
- We only have confirmed naming codes for 7 types of Pumps. Everything else (valves, motors, compressors, etc.) has no official code to check against.
- There's no file anywhere that says "this Task List is deliberately shared across multiple platforms on purpose" — so multi-platform cases always need a human to confirm.
- There's no official SCE naming code list.

---

## PP2 — Work Centre Assignment

### What we need to validate
Every Task List Item and every individual Operation has a **Work Centre** — basically, which team/discipline (mechanical, electrical, instrument, etc.) is responsible for doing the work. We need to check that:
1. The assigned Work Centre matches the type of work actually being done.
2. Nobody is using a "MULTI" placeholder value (like `XMULTI`) instead of a real, specific Work Centre — the client's rules say this is not allowed at the individual-operation level.

### How we solve it
We figure out the "dominant discipline" for a Task List or Operation by adding up the work-hours logged against each discipline and picking the one with the most hours.

**If the Work Centre is a MULTI placeholder:**
We calculate the dominant discipline from the real operations under it, then recommend the Work Centre that matches that discipline — using an approved lookup table built from the client's own planning documents. If we can't find an approved Work Centre for that discipline yet, we still tell you the discipline, just with lower confidence.

**If the Work Centre is already a specific value (not MULTI):**
We check if it agrees with the dominant discipline calculated from the operations. If they disagree, we recommend the correct discipline's Work Centre.

**Close calls:**
If the top discipline only barely beats the second one (within 15% of total hours), we either skip the check entirely or lower our confidence — because there's no official tie-breaking rule yet.

### What you get
Almost always a recommendation of some kind (a specific Work Centre code, or at least the correct discipline name), with the confidence level reflecting how sure we are.

### Known gaps
No official tie-breaking rule exists for close calls between two disciplines. Some disciplines don't yet have an approved Work Centre mapped to them.

---

## PP3 — Orphaned Task Lists

### What we need to validate
Every Task List that has real operations logged against it should also be properly linked to a **Maintenance Item** (the record that connects it to actual equipment). If a Task List has work defined but no Item pointing to it, it's "orphaned" — floating with no real owner.

### How we solve it
We go through every Task List that has real operations and check if it has a matching row in the master bridge file (Bokor Task List Group).

- **No matching row at all** → orphaned. Flagged, with slightly more confidence if we can find some supporting evidence elsewhere (e.g. in the Maintenance Plan file).
- **Row exists, but the equipment behind it is INACTIVE** → also flagged — the Task List technically has an owner, but that owner isn't a live asset anymore.
- **Row exists, but we can't tell the equipment's status** → flagged as "unknown," lower confidence.

### What you get
This is a **flag-only** check — we tell you a Task List is orphaned or points to inactive equipment, but we never suggest what Maintenance Item it should have. That decision needs a person.

### Known gaps
If the equipment status files aren't supplied, this check can't tell active from inactive equipment and will assume everything with a bridge row is fine.

---

## PP4 — Duplicate / Overlapping Task Lists

### What we need to validate
Are there two different Task Lists that actually describe the same work? If so, that's wasted effort and confusing for planners — we want to flag likely duplicates.

### How we solve it
We compare every pair of Task Lists by looking at their descriptions (Object Description, short text, and long text) and measuring how similar the wording is.

- If both Task Lists clearly cover *different* types of equipment (based on known naming codes), we skip the comparison — no point comparing a pump task to a valve task.
- If the text is a very strong match across all three fields, we flag it as a likely duplicate with high confidence.
- If the match is weaker or only partial, and we have an AI reviewer available, we ask it to read both descriptions and judge whether they really describe the same task. Its answer (yes / no / unsure) adjusts our confidence.

### What you get
This is a **flag-only** check. We tell you "these two Task Lists look like duplicates," but we never decide which one to keep — that's a judgment call for the planning team.

### Known gaps
The equipment-type filtering only works for the small set of Pump types we have official codes for. For everything else, we rely purely on text similarity.

---

## PP5 — Planned Man-Hours (currently the only active check)

### What we need to validate
Every Operation has a planned **WORK** value (total man-hours), which should equal **PERSON × DURATION**. Beyond that simple math check, we also want to know: is the WORK value itself realistic, based on real history or industry benchmarks?

### How we solve it
This check runs in two layers:

**Layer 1 — The math check**
Does WORK actually equal PERSON times DURATION? If the units used aren't the ones we trust (man-hours and hours), we don't check the math at all — we just say there isn't enough reliable information. If the numbers don't match, we can suggest what the "correct" arithmetic answer would be (PERSON × DURATION), but only as a **candidate** — because we don't independently know if PERSON and DURATION themselves are even correct.

**Layer 2 — Does the number make sense against real evidence?**
We try up to four different sources of evidence, in order of trust:
1. **Real history** — has this exact operation actually been executed before, with hours logged? If we find at least 3 solid matching historical executions, that's our strongest evidence.
2. **PITSTOPS ranges** — plausible hour ranges by discipline, from turnaround planning data.
3. **OREDA** — an industry-standard reliability database with typical repair times for common equipment types. We only use this for actual repair/overhaul-type work, never routine inspections, and it's always treated as a *rough benchmark*, never final proof.
4. **JMS workpack data** — actual man-hours logged in a separate work-tracking system.

If two or more of these sources genuinely agree, or if there's strong single-source evidence, we recommend a value. If the evidence is weaker (only 1-2 historical matches, or only OREDA, or only a rough Order-level match with no specific Operation match), we offer it as a **candidate** for review instead of a final answer.

If there's truly nothing — no math problem and no useful evidence anywhere — we don't flag the row at all. Flagging something with zero real evidence would just create noise.

### What you get
A wide range of outcomes depending on evidence strength: fully recommended values (when solid history exists), candidate values needing sign-off (when evidence is partial), or a note saying no usable evidence exists and the current value is being left alone.

### Known gaps
- Two of the reconciliation settings (how close is "close enough" between two sources, and which source wins if they disagree) haven't been formally approved by the client yet — so even when two sources agree, that agreement currently can only produce a candidate, not a final recommendation.
- OREDA is never treated as proof by itself, even if it's the only evidence available.
- Most of the real operations in the data are routine inspections, not repairs — so OREDA (which is repair-focused) applies to only a small slice of the work.
- We have no independent way to confirm PERSON and DURATION are correct in the first place.

---

## PP6 — Maintenance Plan / Strategy Issues

### What we need to validate
Two separate things:
1. Does a Maintenance Item's **Strategy** (e.g. how often it should be maintained) match the Strategy on its actual Task List?
2. Does every active piece of equipment have at least one Maintenance Plan covering it?

### How we solve it

**Check A — Strategy mismatch**
The Task List's Strategy is treated as the source of truth (per the client's own rules). If the Maintenance Item's Strategy doesn't match its Task List's Strategy, we recommend correcting the Item to match the Task List — with high confidence, since the rule is explicit and doesn't depend on ambiguous evidence.

**Check B — Missing coverage**
We check every piece of equipment marked active (installed, in-service, not "removed from operation") and see if it appears anywhere in the master bridge file. If active equipment has zero Maintenance Plan coverage, we flag it — this is a real gap that needs attention, but we don't invent a Plan to assign it to.

### What you get
Check A gives a verified recommendation (correct the Item's Strategy). Check B is flag-only (report the coverage gap, no suggested fix).

### Known gaps
There's a third question this pain point is meant to eventually answer — "is a Maintenance Plan sitting on hold longer than its own scheduling frequency allows?" — but we don't have the scheduling data needed to check that yet, so it isn't implemented.

---

## PP7 — Hanging Maintenance Items

### What we need to validate
Every Maintenance Item should be linked to a Maintenance Plan. If the Maintenance Plan field is blank, the Item is "hanging" — it exists but isn't properly scheduled under any Plan.

### How we solve it
This is the simplest check: we go through every row in the bridge file and look for a blank Maintenance Plan field. If it's blank, we flag it.

### What you get
Flag-only — we identify the gap, but we don't and can't invent a Maintenance Plan for it.

### Known gaps
This check only looks at Items that are already in the bridge file. If an Item is missing from the bridge file entirely, that's a different problem — PP3 (Orphaned Task Lists) catches that case, not PP7.

---

## Quick summary table

| PP | What it checks | Can it recommend a fix? |
|----|----|----|
| PP1 | Task List Group naming (Location + Object Type) | Sometimes — only when both parts are independently proven |
| PP2 | Work Centre matches the right discipline | Usually — with confidence based on how clear the evidence is |
| PP3 | Task Lists with no owning Maintenance Item, or inactive owners | No — flag only |
| PP4 | Duplicate/overlapping Task Lists | No — flag only, never says which to keep |
| PP5 | Planned man-hours are correct and realistic | Sometimes — depends heavily on how much real evidence exists |
| PP6 | Strategy mismatch (Check A) + missing Plan coverage (Check B) | Check A: yes. Check B: no |
| PP7 | Maintenance Items with no Maintenance Plan | No — flag only |

**The one rule that applies everywhere:** if there isn't enough real evidence to be confident, the agent will never invent an answer. It will either offer a candidate that clearly says "needs review," or just flag the problem with no suggested value at all.
