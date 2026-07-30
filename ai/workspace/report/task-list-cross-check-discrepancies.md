Created: 2026 July 30

# Task List Cross-Check — Discrepancies and Resolution Procedure

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Method](<#2.0 method>)
[3.0 Coverage Result](<#3.0 coverage result>)
[4.0 Discrepancy Summary](<#4.0 discrepancy summary>)
[5.0 D1 — Type Rule Did Not Cover Core §5.x](<#5.0 d1 — type rule did not cover core §5.x>)
[6.0 D2 — Missing Dependency 7.4.7 → 7.4.1](<#6.0 d2 — missing dependency 7.4.7 → 7.4.1>)
[7.0 D3 — Missing Dependency 7.3.5 → 7.3.11, 7.3.12](<#7.0 d3 — missing dependency 7.3.5 → 7.3.11, 7.3.12>)
[8.0 D4 — Missing Dependency 7.3.9 → 7.3.8](<#8.0 d4 — missing dependency 7.3.9 → 7.3.8>)
[9.0 D5 — Display §7.7 Sources No Triple](<#9.0 d5 — display §7.7 sources no triple>)
[10.0 Residual Observations](<#10.0 residual observations>)
[11.0 Discharge Checklist](<#11.0 discharge checklist>)
[Glossary](<#glossary>)
[Source Documents](<#source documents>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document records the discrepancies found when `ai/task.md` §7.3 and
§7.4 were cross-checked against the two source code reviews on 30 July
2026, and states the procedure for resolving each.

Five discrepancies were found. None invalidates the plan. All five have
been *recorded* in `ai/task.md` v6.0; three of the five are not yet
*discharged*, because discharge depends on work that has not been
authored. Section 4.0 distinguishes the two states, and §11.0 is the
checklist that closes them.

No source code is changed by anything in this document.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Method

Each numbered recommendation and each numbered finding in both source
reports was traced forward to the triple that claims it in `ai/task.md`
§7.3 and §7.4, and each triple's declared file set was traced back to the
file and line the report actually cites. Report line references were
checked against `src/gtach` at version 0.2.64 rather than taken on trust.

Two classes of defect were sought:

- **Coverage defects** — a recommendation claimed by no triple, or by
  more than one.
- **Consistency defects** — a triple whose declared scope, type
  classification, file set or ordering contradicts the report it derives
  from, or contradicts another triple.

No coverage defects were found. All five discrepancies are consistency
defects.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Coverage Result

| Source | Items | Claimed exactly once | Unclaimed | Double-claimed |
|---|---|---|---|---|
| `display-ui-graphics-review.md` §9.0 recommendations 1–29 | 29 | 29 | 0 | 0 |
| `core-comm-utils-code-review.md` §3.1–§3.6, §4.1–§4.4, §5.1–§5.9 | 19 | 19 | 0 | 0 |
| `core-comm-utils-code-review.md` §7.0 items #1–#8 | 8 | 8 | 0 | 0 |

Every file attribution in the §7.3 and §7.4 tables corresponds to a
location the source report actually cites. The coverage-check statements
in §7.3 and §7.4 of `ai/task.md` are correct as written.

Note that the display report's coverage is measured against its *numbered
recommendations*, which is the bound §7.1 sets. That bound is itself the
subject of D5.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Discrepancy Summary

| ID | Discrepancy | Class | Recorded | Discharged |
|---|---|---|---|---|
| D1 | §7.2 `issue_info.type` rule had no mapping for core §5.x | Classification | ✅ `task.md` v6.0 §7.2 | ☐ Applies when 7.4.4, 7.4.6, 7.4.7 are authored |
| D2 | 7.4.7 and 7.4.1 both edit `utils/config.py`; no dependency recorded | Sequencing | ✅ `task.md` v6.0 §7.6.1 | ☐ Blocked on the §7.5.4 decision |
| D3 | 7.3.5's static-layer cache is invalidated by 7.3.11 and 7.3.12 | Sequencing | ✅ `task.md` v6.0 §7.6.1 | ☐ Applies when 7.3.5 is authored |
| D4 | 7.3.9 registers touch regions that 7.3.8 relocates | Sequencing | ✅ `task.md` v6.0 §7.6.1 | ✅ Satisfied by the §7.6.2 order |
| D5 | Display §7.7 has no numbered recommendation and sources no triple | Coverage bound | ✅ `task.md` v6.0 §7.3.15 | ☐ Decision deferred to a P10 cycle |

"Recorded" means the plan now states the constraint. "Discharged" means
the constraint can no longer be violated by future work. D4 is the only
one where recording was sufficient, because the recommended authoring
order already satisfies it.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 D1 — Type Rule Did Not Cover Core §5.x

### 5.1 Observation

`ai/task.md` §7.2 specified `issue_info.type` as:

> `defect` for §3.x/§8.x items; `performance` for efficiency items;
> `enhancement` for UI proposals

The core report's §5.0 is titled *Logic and Design Findings*. It is
neither a §3.x coding error, nor an efficiency finding, nor a user
interface proposal, so the rule returned no value for it.

### 5.2 Extent

§5.x is not a marginal case. It governs one triple in full and parts of
two others:

| Triple | §5.x items it carries | Previously classifiable |
|---|---|---|
| 7.4.6 `2d545bf5` | §5.5, §5.9 — the whole triple | No |
| 7.4.4 `52414414` | §5.6, §5.7 | Partly, via §3.4 and §3.5 |
| 7.4.7 `d32ccc49` | §5.2, §5.4 | Partly, via §4.2 |
| 7.4.1 `394c3bbb` | §5.1 | Partly, via §3.1 and §3.6 |
| 7.4.5 `6481f8ce` | §5.3, §5.8 | Partly, via §4.3 |

Without a rule, 7.4.6 would have been typed by whoever authored it, and
the remaining four would have been typed by their non-§5.x component —
which is arbitrary where the §5.x item is the larger part of the work.

### 5.3 Resolution — Recorded

`ai/task.md` §7.2 now classifies §5.x by dominant effect:

- `defect` — the finding is an incorrect or unreachable behaviour:
  §5.3, §5.6, §5.7
- `performance` — the finding is a resource or latency concern:
  §5.5, §5.9
- `enhancement` — the finding is a maintainability or diagnostic
  improvement: §5.1, §5.2, §5.4

Where a triple mixes types, the issue takes the highest-severity
contributing type.

### 5.4 Resolution — Steps to Discharge

1. When authoring **7.4.6** (`2d545bf5`, §5.5 and §5.9), set
   `issue_info.type: performance`. Both items are latency concerns: a
   shutdown budget that silently exceeds the caller's request, and a
   UI-driven call that can block for several seconds.
2. When authoring **7.4.4** (`52414414`), set `issue_info.type: defect`.
   §3.4 (`KeyError` on malformed config) and §3.5 (`range(float)`
   `TypeError`) are the highest-severity contributors and both are
   defects.
3. When authoring **7.4.7** (`d32ccc49`), set `issue_info.type: defect`.
   §5.4 — the stale `src/obdii` marker — is unreachable code; that
   outranks §4.2 (`performance`) and §5.2 (`enhancement`) under the
   highest-severity rule.
4. When authoring **7.4.5** (`6481f8ce`), set `issue_info.type: defect`.
   §5.3 is a check-then-act race producing an unhandled `AttributeError`.
5. When authoring **7.4.1** (`394c3bbb`), set `issue_info.type: defect`
   under either §5.1 disposition. §3.1 (`RWLock` notification bug) and
   §3.6 (`device.address`) are recorded as defects regardless of whether
   they are fixed or removed. See §6.0.
6. After the last of these is authored, confirm no §5.x item was typed
   against the rule, and mark D1 discharged in this document's §11.0.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 D2 — Missing Dependency 7.4.7 → 7.4.1

### 6.1 Observation

Both triples modify `src/gtach/utils/config.py`:

- **7.4.1** `394c3bbb` carries core §3.1, §3.6 and §5.1. Under the
  *retire* disposition it deletes approximately 1,600 lines of
  `ConfigManager` device-persistence machinery.
- **7.4.7** `d32ccc49` carries core §5.2, which adds a warning when a
  later `ConfigManager(path)` call supplies a different `config_path`
  than the existing singleton holds.

`ai/task.md` §7.6.1 recorded no relationship between them. The §7.6.2
authoring order places 7.4.7 at step 5 and 7.4.1 at step 8, so the
default sequence writes the §5.2 warning into a file that 7.4.1 may then
substantially delete.

### 6.2 Why It Matters

The collision is survivable but wasteful in the *retire* case and
genuinely ambiguous in the *adopt* case:

- **Retire** — the §5.2 warning belongs on `ConfigManager.__new__` /
  `__init__`, which survive the deletion. If 7.4.7 sites the warning
  anywhere in the device-persistence block, the edit is lost.
- **Adopt** — `ConfigManager` gains the live pairing flow, so the
  singleton's `config_path` handling becomes materially more important
  than it is today, and §5.2 may warrant a stronger remedy than a
  warning.

Either way, the §5.1 disposition determines whether 7.4.7's edit is
correct.

### 6.3 Resolution — Recorded

`ai/task.md` §7.6.1 now carries:

> | 7.4.7 | 7.4.1 | Both modify `utils/config.py`. Under the *retire*
> disposition 7.4.1 deletes the device-persistence machinery; the §5.2
> singleton warning added by 7.4.7 must be sited in surviving code.
> 7.4.7 is authored after the §7.5.4 decision is recorded, or its change
> document must confine the edit to `ConfigManager.__new__`/`__init__` |

### 6.4 Resolution — Steps to Discharge

1. Carry out **§7.5.4**: decide whether the `ConfigManager`
   device-persistence path is intended for future use. This is a human
   decision, not an observation; no measurement resolves it.
2. Record the decision in `ai/task.md` §7.4.8, replacing the two
   conditional outcomes with the one taken.
3. Author the **7.4.1 issue document** — it is valid under either
   outcome, per §7.4.8, and may be authored before step 1 if convenient.
4. Author the **7.4.1 change document** to the decided scope.
5. Author **7.4.7** only after step 4, and site the §5.2 warning in
   `ConfigManager.__new__` or `__init__`.
6. If steps 1 to 4 are deferred and 7.4.7 must proceed first, state in
   the 7.4.7 change document's `out_of_scope` that the edit is confined
   to `ConfigManager.__new__`/`__init__` and touches no
   device-persistence code. That satisfies the constraint without the
   decision.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 D3 — Missing Dependency 7.3.5 → 7.3.11, 7.3.12

### 7.1 Observation

**7.3.5** `821919ce` carries display recommendation 9: pre-render the
RADIAL static layer once into a cached surface, blit it per frame, and
draw only the fill arc, indicator and centre on top. The display report
§5.3 enumerates what it considers invariant between frames: the black
corners, border ring, r=232 background, headroom arc, inert bottom arc,
zone boundary lines, inner edge ring, seven tick marks, seven numerals,
six band boundary marks and the `RPM × 1000` label.

Two later triples change that set:

- **7.3.11** `5014040c` (recommendation 26) replaces the full-field band
  colour with an annular band indicator on a fixed dark ground. The
  indicator's colour varies with the RPM band, so a ring that
  recommendation 9 treats as static becomes dynamic.
- **7.3.12** `5012004e` (recommendation 29) adds a dimmed night palette
  with a manual toggle. Every colour in the cached layer has a night
  variant, so the whole cache is invalid on toggle.

Recommendation 9 specifies no invalidation mechanism, because at the time
it was written the static set genuinely was static.

### 7.2 Why the Recommended Order Does Not Resolve It

This is the point that distinguishes D3 from D4. `ai/task.md` §7.6.2
places **7.3.5 at step 6** and **7.3.11 and 7.3.12 at step 9**. The
recommended order therefore implements the cache *before* the two changes
that invalidate it. Sequencing alone does not resolve D3; the "either
7.3.5 lands last" branch of the recorded row is not the branch the
current order takes.

The operative requirement is consequently the second branch: the 7.3.5
change document must specify an invalidation key.

### 7.3 Resolution — Recorded

`ai/task.md` §7.6.1 now carries:

> | 7.3.5 | 7.3.11, 7.3.12 | Recommendation 9 caches the RADIAL static
> layer. The annular band indicator (7.3.11) and the night palette
> (7.3.12) both alter static-layer content, so each requires a
> cache-invalidation path that recommendation 9 does not specify. Either
> 7.3.5 lands last, or its change document must specify an invalidation
> key covering band and palette state |

### 7.4 Resolution — Steps to Discharge

1. When authoring **7.3.5**, specify the cached surface as keyed rather
   than singular. The minimum key is a tuple of the state the layer
   depends on. At the time 7.3.5 is authored that is the viewport
   geometry and the `RPMBands` thresholds; after 7.3.11 it also includes
   the active band index, and after 7.3.12 the palette variant.
2. State in the 7.3.5 change document that the key is expected to gain
   members, and name 7.3.11 and 7.3.12 as the changes that will add them.
   Record them under `dependencies.required_changes` with relationship
   `blocks`.
3. Implement the cache as invalidate-on-key-change, not
   invalidate-on-demand. A caller that must remember to invalidate is a
   defect waiting to be filed; a key comparison cannot be forgotten.
4. When authoring **7.3.11**, add the active band index to the key and
   state in its change document that it does so.
5. When authoring **7.3.12**, add the palette variant to the key and
   state the same.
6. Verify at 7.3.12's implementation that toggling the night palette
   produces a full redraw of the cached layer on the next frame, not a
   stale blit. Mark D3 discharged in §11.0.

### 7.5 Alternative

If the invalidation key is judged to add more complexity than the cache
saves, the alternative is to move 7.3.5 after 7.3.12 in §7.6.2 — that is,
to take the first branch of the recorded row. This is a legitimate
resolution and is simpler, at the cost of deferring the report's largest
single render saving behind three user interface changes. The decision
belongs with whoever authors 7.3.5 and should be recorded in its change
document under `alternatives_considered`.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 D4 — Missing Dependency 7.3.9 → 7.3.8

### 8.1 Observation

**7.3.8** `44bca479` carries display recommendation 20, which relocates
touch-region registration out of the render path and into a mode-entry
hook. The display report §8.2 records that `_draw_options_menu`,
`_draw_update_view`, `_render_disconnected` and
`_draw_acknowledgement_mode` each call `clear_regions()` and re-register
on every frame, opening a 60 Hz window in which a touch is discarded.

**7.3.9** `b02ed4ea` carries recommendations 24 and 27, which change
button geometry and route all button drawing through a single helper that
applies the declared `TypographyConstants` values — including touch
expansion, which is registered with the touch coordinator.

If 7.3.9 lands first, it writes registration code inside the render path
that 7.3.8 then has to move.

### 8.2 Resolution — Recorded and Discharged

`ai/task.md` §7.6.1 now carries:

> | 7.3.9 | 7.3.8 | Recommendation 20 (7.3.8) relocates touch
> registration from the render path to a mode-entry hook.
> Recommendations 24 and 27 (7.3.9) re-register button regions. Authoring
> 7.3.9 first produces registration code that 7.3.8 then has to relocate |

Unlike D3, the existing §7.6.2 order already satisfies this: **7.3.8 is
at step 6** and **7.3.9 at step 9**. The row is therefore a guard against
reordering rather than a correction, and D4 is discharged by recording
alone.

### 8.3 Resolution — Steps to Preserve

1. Do not move 7.3.9 earlier than 7.3.8 in §7.6.2 without also revisiting
   this row.
2. When authoring **7.3.9**, have the single button helper register
   through the mode-entry hook that 7.3.8 introduces, not through a
   per-frame call. State this explicitly in the 7.3.9 change document, so
   the dependency is visible to the implementer without reference to
   `task.md`.
3. Record 7.3.8 under 7.3.9's `dependencies.required_changes` with
   relationship `blocked_by`.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 D5 — Display §7.7 Sources No Triple

### 9.1 Observation

Display report §7.7, *Options Screen Uses a Rectangular Layout*, observes
that four 300 px full-width bars stacked vertically on a circular panel
leave the four corner regions unusable and read as a cropped rectangular
dialogue. It is a substantive finding with a stated rationale.

It has **no numbered recommendation** in the report's §9.0. Every other
§7.x finding does: §7.1 → 23, §7.2 → 26, §7.3 → 24, §7.4 → 27, §7.5 →
25, §7.6 → 25, §7.8 → 28, §7.9 → 29. §7.7 alone terminates in the
findings section.

`ai/task.md` §7.1 bounds the display source to "§9.1 to §9.5,
recommendations 1 to 29", so §7.7 is outside scope by declaration rather
than by oversight. The coverage claim in §7.3 remains true.

### 9.2 Why It Matters

`ai/task.md` §7.6.4 states:

> Neither report is closed until all triples it sources are closed; both
> remain in `ai/workspace/report/`.

§7.7 sources no triple. Under a literal reading it can never be closed
and never blocks closure, which means it would simply disappear when the
report is archived — an open finding with no owner and no closure path.
Left implicit, this is the kind of gap that resurfaces two years later as
"why was this never addressed".

### 9.3 Resolution — Recorded

`ai/task.md` gains §7.3.15, which records the exclusion, its rationale,
and the disposition: §7.7 proposes a user interface redesign rather than
a code-review remediation, and it overlaps the button geometry work
already scoped in 7.3.9 (recommendation 24 reduces the options screen to
three items). It is deferred to a future requirements cycle (P10) rather
than converted to a twenty-first triple, and is to be revisited after
7.3.9 is implemented and the three-item layout can be observed on the
panel.

### 9.4 Resolution — Steps to Discharge

1. Implement **7.3.9** (`b02ed4ea`), which reduces the options screen to
   three targets of height ≥ 72 px with separation ≥ 16 px.
2. Observe the resulting layout on `gtach.local`. The three-item layout
   occupies materially less vertical extent than the current four-item
   layout, so the corner-region argument in §7.7 may be weakened or
   removed by 7.3.9 alone.
3. Decide one of:
   - **Closed by 7.3.9** — record in §7.3.15 that the finding is
     satisfied, and close it with the display report.
   - **Raise to P10** — open a T07 requirements item for a circular
     options layout, and record its reference in §7.3.15. The display
     report may then close, because §7.7 has an owner.
   - **Accept permanently** — record the rectangular layout as an
     accepted design position with a stated reason, and close.
4. Whichever is chosen, update §7.3.15 with the outcome before the
   display report is moved to `ai/workspace/report/closed/`.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Residual Observations

These were noted during the cross-check but are not discrepancies between
`ai/task.md` and the source reports. They are recorded so they are not
rediscovered.

### 10.1 Report Line References Drift

Three line references in the source reports are one to three lines off
against `src/gtach` at 0.2.64 — for example the display report's
`monitor.py:139` for the `uuid.uuid4()` call, which is at line 143.
Immaterial to the findings, and corrected in the triples authored so far
rather than in the reports, which are closed to amendment as historical
records. Authors of the remaining triples should verify line numbers
against source rather than copying them from the report.

### 10.2 `ai/task.md` §7.3 and §7.4 Tables Carry No Status Column

The tables list twenty triples with no indication of which have been
authored, implemented or closed. That information currently exists only
in git history and in the `closed/` subfolders. As the count of completed
triples rises this becomes the primary way the plan is misread. Adding a
status column is a documentation change requiring no governance cycle
(P03 §1.4.11).

### 10.3 `ai/workspace/report/README.md` Is Stale

It states that the folder is "excluded from git". `.gitignore` no longer
contains the `ai/workspace/report/` entry, and both source reviews are
tracked. One-line correction; no cycle required.

[Return to Table of Contents](<#table of contents>)

---

## 11.0 Discharge Checklist

Mark each item when the condition holds. D4 is complete.

| ID | Condition for discharge | Depends on | Status |
|---|---|---|---|
| D1 | 7.4.1, 7.4.4, 7.4.5, 7.4.6 and 7.4.7 authored with `issue_info.type` per §5.4 above | Authoring of five core triples | ☐ |
| D2 | §7.5.4 decided and recorded in §7.4.8; 7.4.1 change document authored; 7.4.7 authored after it, or confined to `__new__`/`__init__` | Human decision | ☐ |
| D3 | 7.3.5 change document specifies a keyed cache; 7.3.11 and 7.3.12 each extend the key; night-toggle redraw verified on target | Authoring of 7.3.5, 7.3.11, 7.3.12 | ☐ |
| D4 | §7.6.2 keeps 7.3.8 before 7.3.9; 7.3.9 registers through the mode-entry hook | — | ✅ Recorded and satisfied |
| D5 | 7.3.9 implemented and observed; §7.3.15 updated with one of the three outcomes | 7.3.9 implementation | ☐ |

[Return to Table of Contents](<#table of contents>)

---

## Glossary

**Discharged** — a constraint that can no longer be violated by future
work, because the work it constrains has been completed or the plan makes
violation impossible.

**Recorded** — a constraint that is stated in the plan but whose
observance still depends on the author of a future document.

**Invalidation key** — a tuple of the state a cached artefact depends on.
Comparing the key on each use makes a stale cache impossible, in contrast
to explicit invalidation, which depends on every mutating caller
remembering to call it.

**Triple** — the coupled T03 issue, T02 change and T04 prompt documents
sharing one UUID, per governance P00 §1.1.10 and P03 §1.4.2.

[Return to Table of Contents](<#table of contents>)

---

## Source Documents

- `ai/task.md` v6.0 — §7.0 Code Review Remediation, §7.2, §7.3, §7.4,
  §7.5, §7.6
- `ai/workspace/report/core-comm-utils-code-review.md` v1.0
- `ai/workspace/report/display-ui-graphics-review.md` v1.0
- `ai/governance.md` — P00 §1.1.10, P03 §1.4.2, §1.4.11, P04 §1.5.7,
  P09 §1.10.2, P10
- `src/gtach` at version 0.2.64

No external sources were used.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026 July 30 | Initial report: five discrepancies from the `ai/task.md` §7.3/§7.4 cross-check, with recorded state, discharge procedure and checklist. |

[Return to Table of Contents](<#table of contents>)

---

Copyright (c) 2026 William Watson. MIT License.
