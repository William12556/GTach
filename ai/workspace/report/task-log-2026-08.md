Created: 2026 August 07

# Task List — Narrative Archive, August 2026

---

## Table of Contents

[0.0 Purpose](<#0.0 purpose>)
[1.0 Completed-Item Verification Detail](<#1.0 completed-item verification detail>)
[2.0 §7.0 Authoring Detail](<#2.0 §7.0 authoring detail>)
[3.0 Cross-Check — 2026-08-04](<#3.0 cross-check — 2026-08-04>)
[4.0 Implementation — 2026-08-04](<#4.0 implementation — 2026-08-04>)
[5.0 On-Target Session — 2026-08-05](<#5.0 on-target session — 2026-08-05>)
[6.0 Second On-Target Session — 2026-08-05](<#6.0 second on-target session — 2026-08-05>)
[7.0 §8.4 Observation Session — Discharged From Logs](<#7.0 §8.4 observation session — discharged from logs>)
[8.0 Long Run — 52 Minutes, 2026-08-05](<#8.0 long run — 52 minutes, 2026-08-05>)
[9.0 Flicker Discharged and Efficiency Triples Deferred](<#9.0 flicker discharged and efficiency triples deferred>)
[Version History](<#version history>)

---

## 0.0 Purpose

This document is the narrative and investigative record that formerly
occupied §9.0–§9.13 of `ai/task.md`, plus the extended verification detail
that formerly sat under its §3.0 and §7.0. It was split out on
2026-08-07 because `task.md` had grown to 1,841 lines and the narrative
made up roughly half of it — valuable as an audit trail, but not needed
on every read of the current task state.

`task.md` now holds only current state: what is open, what is blocked,
what is deferred, and a one-line summary of what is closed, each with a
pointer here for the reasoning and evidence behind it. Nothing recorded
below has been altered from the source revision (9.0–17.0 as numbered in
`task.md`'s own version history) — this is a relocation, not a rewrite.

Cross-references to old `task.md` section numbers (for example
`change-c1d4b8e6`'s citation of "§9.10") now resolve to the equivalent
section in this document.

[Return to Table of Contents](<#table of contents>)

---

## 1.0 Completed-Item Verification Detail

### 1.1 `b7e3f90a` — Dead code cleanup

| Item | Verification |
|---|---|
| `core/watchdog_enhanced.py` | absent — deleted |
| `display/hardware_interface.py` | absent — deleted |
| `display/ui_testing_framework.py` | absent — deleted |
| `display/enhanced_touch_factory.py` | absent — deleted |
| `display/performance.py` (flat file) | absent; `performance/` package remains — deleted |
| `display/components/` | absent — deleted |
| `utils/services/` | absent — deleted |
| `assets/fonts/BebasNeue-Regular.ttf` | absent — deleted |
| `AsyncSyncBridge` + dead `ThreadManager` API in `core/thread.py` | zero hits — removed |
| `ConfigManager.setup_logging` group in `utils/config.py` | zero hits — removed |

Governance documents moved to `issues/closed/`, `change/closed/`,
`prompt/closed/`.

### 1.2 `f993f871` — OPTIONS update check/install

| Requirement | Verification |
|---|---|
| `src/gtach/utils/updater.py` | present, pure stdlib |
| `_restart_callback`, `_options_view`, `_draw_update_view`, `_on_check_updates` in `display/manager.py` | present, matches deliverable |
| `GTachApplication._request_restart()` + wiring in `app.py` | present at both call sites |
| `gtach.service` `Restart=always` | confirmed, `bin/gtach.service:13` |

Consistent with `README.md` §3.1/§4.2. Governance documents closed.

### 1.3 UI Navigation Logic audit — Findings A and B

- **Finding A** (stale `OPTIONS` mode after re-pair) → `issue-c84ffe6f` /
  `change-c84ffe6f` / `prompt-c84ffe6f`. Fix verified:
  `DisplayManager.exit_setup_mode()` (`manager.py:1494–1498`) sets
  `self.config.mode = self._post_splash_mode` on exit.
- **Finding B** (non-indicating simulation toggle) → `issue-85cc0241` /
  `change-85cc0241` / `prompt-85cc0241`. Fix verified: button label at
  `manager.py:932` is `"Simulation mode" if self._sim_mode else "Bluetooth"`.

Both cycles were closed before this review. The audit report itself was
moved to `audit/closed/`.

### 1.4 Splash Screen Debug Session audit — Defects 1–4

All four qualified for the Trivial Change Exemption (§P03 §1.4.12) —
git commit history is the audit record.

| Defect | Verification |
|---|---|
| 1 — `DisplayMode.ACKNOWLEDGEMENT` missing | present, `display/models.py:68` |
| 2 — `_ack_state_manager` never initialized | imported and instantiated, `display/manager.py:54,117` |
| 3 — `rpm_bands`/`engine_profile` missing from `DisplayConfig` | both present, `display/models.py:101,104` |
| 4 — heartbeat key mismatch for `setup` thread | `setup.py:135` registers `'setup'` before `update_heartbeat('setup')` |

### 1.5 `comm/` transport layer audit (`b4e8c012` / `2f612d17` / `a4c8e2f1`)

Resolved by inspecting `ai/state/ralph/ael_20260617-131721.LOG`. The
audit genuinely completed all 20 items; the copy that reached
`ai/workspace/audit/` as `audit-b4e8c012-report.md` held only the last 6
of 20 sections — a late-loop overwrite or truncated copy during the
`workspace/` → `ai/workspace/` migration, not a false completion mark.
Closed 2026-07-29 on the strength of index and log evidence. The full
20-item text remains recoverable from the log's tool-call payloads if
wanted later.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 §7.0 Authoring Detail

Twenty issue/change/prompt triples were authored against two code-review
reports (`core-comm-utils-code-review.md`, `display-ui-graphics-review.md`).
The following authoring-time detail is retained for audit purposes; the
current status of each triple is in `task.md` §6.0/§7.0.

### 2.1 Directed Scope Decisions (display recs 25, 26, 29)

- **Rec 25 (`378703da`)** — place the numeric RPM in the RADIAL centre
  disc and retire DIGITAL as a separate mode. Consequences specified:
  the horizontal-swipe mode change and the unused
  `_render_mode_selector()` become dead and are removed; `DisplayMode.DIGITAL`
  handling in `display/models.py` and any persisted `config.mode` value
  require a migration path.
- **Rec 26 (`5014040c`)** — replace the full-field band colour with an
  annular band indicator on a fixed dark ground. Removes the
  band-to-text-colour coupling from `4c038bed`/rec 23.
- **Rec 29 (`5012004e`)** — add a dimmed night palette with a manual
  toggle (no ambient light sensor on target hardware, so automatic
  switching is out of scope). Interacts with `b02ed4ea` (touch geometry)
  and `5014040c` (night variant of the annular indicator).

### 2.2 Recorded Exclusion — Display §7.7

Display report §7.7 (*Options Screen Uses a Rectangular Layout*) has no
corresponding numbered recommendation and is outside the twenty-triple
scope. Deferred to a future requirements cycle (P10). Revisit after
`b02ed4ea`'s three-item layout is observed on the panel — it is also the
source of the entry-point gap recorded against `b02ed4ea` in `task.md`.

### 2.3 Corrections Found While Authoring (§9.7.2 of the source revision)

1. `394c3bbb`'s file list originally named `comm/device_store.py` and
   `comm/models.py`; neither may be modified — the change is confined to
   `utils/config.py`.
2. `b02ed4ea`'s touch-target expansion is applied by the caller, not
   inside `register_button_region` (which is read-only and shared with
   the setup subsystem).
3. A fourth transport-name list exists at `app.py:267`
   (`_fast_transports`), beyond the three core report §5.8 names.
4. `_handle_long_press` (`manager.py:204`) also assigns `DisplayMode.DIGITAL`
   and had to survive `378703da` with that assignment changed to RADIAL —
   it is the only route to OPTIONS pre-`3e8b1d72`.
5. `_get_band_colour` must outlive its last caller under DIGITAL's
   retirement, to preserve the hysteresis `4c038bed` added, which
   `5014040c` requires.
6. Recommendation 26's subject (the full-field band fill) exists only in
   DIGITAL, which `378703da` retires — what remains for `5014040c` is
   RADIAL's light-grey ground and the tick/numeral colours.
7. The night toggle (`5012004e`) has nowhere to go: `b02ed4ea`'s
   three-control budget is full, having already removed *Clear settings*
   for want of a fourth slot.

### 2.4 Dependency and Sequencing Notes (§7.6 of the source revision)

Key dependencies: `7.3.4` on `7.5.1`/`7.3.3`; `7.3.6` on `7.3.1`/`7.3.5`;
`7.3.11` on `7.3.1`; `7.3.12` on `7.3.11`; `7.4.1` on `7.5.4` (cleared);
`7.4.7` on `7.4.9` and `7.4.1` (shared `utils/config.py`); `7.4.5` on
`7.5.5`; `7.3.5` on `7.3.11`/`7.3.12` (static-layer cache invalidation);
`7.3.9` on `7.3.8` (touch-registration relocation).

Recommended authoring/implementation order and the order actually used
on 2026-08-04 are recorded in the source revision's §7.6.2 and §8.5; the
binding constraint — `378703da` before `5014040c` before `5012004e` — was
preserved in practice.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Cross-Check — 2026-08-04

William reported that several report-recommendation changes had been
completed: prompts closed, with the coupled issues and changes left open
pending test results. This section verifies that report against
governance-document state, `src/gtach`, and the pushed git history.

### 3.1 Method

Three sources, cross-checked against each other: governance documents in
`ai/workspace/{issues,change,prompt,test}/` and their `closed/`
subfolders for all twenty triples; targeted `Grep` for the symbols each
report recommendation names, against `src/gtach` at `pyproject.toml`
version `0.3.2`; and `git log --since=2026-07-30`, cross-checked against
`William12556/GTach` on GitHub — local `HEAD` matched the remote's most
recent commit exactly.

### 3.2 Newly Implemented Triples

Eight triples not recorded as authored as of 2026-07-30 were found
implemented, prompt closed with issue/change left active: `66ef59a0`,
`cb28980f`, `49b21ace`, `44bca479`, `4c3c3e1f`, `52414414`, `2d545bf5`,
`d32ccc49`. Each corresponds to a distinct git commit naming the change
document it implements.

This left eight triples unauthored: `821919ce`, `9ed1c77e`, `b02ed4ea`,
`378703da`, `5014040c`, `5012004e` (display, all gated to v0.4.0 by
design), and `394c3bbb`, `6481f8ce` (core, gated pending §7.5.4/§7.5.5).

### 3.3 Reclassification — `49b21ace` Moved to v0.3.0

Assigned to v0.4.0 originally, gated on the §7.5.1 observation via
`7.3.3`. `7.3.3` shipping cleared the gate mechanically — the application
reports its own framebuffer geometry at ERROR severity once
`FBIOGET_VSCREENINFO`/`FBIOGET_FSCREENINFO` land (`engine.py:200`). Git
commit sequence confirms `cb28980f` immediately preceded `49b21ace`, with
an intervening commit recording the reclassification. The on-device
confirmation of depth 32 / stride 1920 was taken later, in §7.0 below —
as a confirmation rather than a blocking observation.

### 3.4 Standing Closure Rule Deviation — `1143427b`

§8.2.1's rule: close the prompt when code lands; keep issue and change
active until a passing T06 result document exists. Four documents were
exempted as closed before the rule was recorded: `4c038bed`, `5a9dc15e`,
`11be4865`, `0b00759c` (plus `c5dedd71`, derived from `0b00759c`).

`1143427b` (`7.4.9`, the `RWLock` notification defect) is not on that
list, yet its issue, change and prompt are all closed. Its own change
document (`change-1143427b`, v1.2) records the closure against an unmet
criterion: on-target verification "outstanding, ships with v0.3.0"; the
coupled T05 is `status: "planned"` with all nine test cases `not_run`;
`ai/workspace/test/result/` is empty; `pytest tests/ collected 0 items`
at closure time; implementation step 3 (generating
`tests/utils/test_rwlock.py`) was not done because the coupled prompt
permitted no file outside `utils/config.py`.

`tests/utils/test_rwlock.py` and `tests/conftest.py` now exist in the
working tree with `.pyc` cache entries indicating a local pytest run, but
no T06 records it and the T05's status field is unchanged. Not a
source-code defect — the fix is verified by AST comparison and a
25-assertion development-platform run. A governance-process deviation.
Recommended resolution (undecided): (a) generate the T06 result document
from the now-existing test run, or (b) add `1143427b` to §8.2.1's
grandfather list with a stated reason.

### 3.5 Confirmed Not Yet Implemented (as of 2026-08-04)

- `394c3bbb` — `utils/config.py` still defined `get_device_by_address`,
  `add_or_update_device`, `remove_device`; `BluetoothConfig` still
  carried `saved_devices`.
- All six v0.4.0 display triples and `6481f8ce` had no governance
  documents or matching commits — absence corroborated, not assumed.

### 3.6 Verification Evidence

| Claim | Evidence |
|---|---|
| Eight triples implemented since 2026-07-30 | `git log --oneline --since=2026-07-30` — 32 commits, each UUID named in a `fix`/`feat`/`perf` commit message |
| Local history matches GitHub | `mcp__github__list_commits` — remote SHA `cfcf1fa9…` equals local `HEAD` |
| `7.3.3` implemented | `engine.py:40,200,367,387` — `FBIOGET_VSCREENINFO` present |
| `7.3.4` implemented | `engine.py:84-89,321-329,426-466` — page-flip/vsync symbols present |
| `7.4.1` not implemented | `config.py:1440,1459,1482` — device methods and `saved_devices` remain |

### 3.7 Remaining Eight Triples Authored — 2026-08-04

All twenty triples now exist. Twenty-four documents, one triple each, all
iteration 1, `target_profile: claude_code`. None implemented at time of
authoring.

Three of the four triples §8.1 flagged as "cannot be authored correctly
yet" — `821919ce`, `9ed1c77e`, `6481f8ce` — were authored anyway on
instruction, each carrying an explicit assumptions block and a
stop-and-report first implementation step:

| Triple | Gate | Assumptions recorded |
|---|---|---|
| `821919ce` | §7.5.3 frame-time baseline | Render cost material; static layer dominates over write path; a third 921,600-byte surface is affordable |
| `9ed1c77e` | §7.5.3, and `7.3.5` landing first | Frame cost after `821919ce` still justifies conditional rendering; 30 Hz is visually acceptable |
| `6481f8ce` | §7.5.5 race reproduction | Failure mode is `AttributeError` |

`394c3bbb` was not gated — §7.5.4 was already decided.

One open decision (`b02ed4ea`): the options menu is left with no entry
point to *Clear settings* — the three-control budget has no fourth slot,
and display §7.7's re-layout (deferred to P10) is where the space would
come from. The prompt instructs the executor not to resolve it by adding
a fourth button.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Implementation — 2026-08-04

Six of the eight v0.4.0 triples were implemented in a single session.
Full detail in `ai/workspace/report/v0.4.0-triple-implementation-session.md`.

### 4.1 Outcome

| Triple | Outcome | Commit |
|---|---|---|
| `b02ed4ea` | Implemented, verified, prompt closed | `a34fd49` |
| `378703da` | Implemented, verified, prompt closed | `7035a93` |
| `5014040c` | Implemented, verified, prompt closed | `730ae56` |
| `5012004e` | Implemented, verified, prompt closed | `2242387` |
| `394c3bbb` | Implemented, verified, prompt closed | `251ea74` |
| `6481f8ce` | Implemented, verified, prompt closed | `3f5fc5e`, `fe879f9`, `51a930b` |
| `821919ce` | Gate failed — stopped and reported | — |
| `9ed1c77e` | Gate failed — stopped and reported | — |

Branch `v0.4.0-display-triples` from `32927fc`, eight commits, not
pushed at the time. `main` unchanged. All sixteen issue and change
T-Docs remained active per §8.2.1; no T06 result documents were produced.

### 4.2 The Two Gated Triples

`821919ce` and `9ed1c77e` were not implemented in this session: both
prompts made the §7.5.3 `frame_time_ms` baseline a gate and instructed
stop-and-report if absent. It was absent — `ai/workspace/test/result/`
was empty. No substitute measurement was taken (macOS Apple Silicon is
not a proxy for a Pi Zero 2W).

### 4.3 Verification Method

`pytest tests/` was not used — the suite collected zero items and pytest
was not importable in the working environment. Each triple was verified
by an ephemeral script asserting its own prompt's success criteria
against the real source. The harnesses were not retained as project
artefacts.

### 4.4 §7.5.5 Discharged

The transport-race reproduction was carried out under `6481f8ce`, first
against unchanged files and again after Stage 1, with explicit
synchronisation. Pre-change: `AttributeError` in all three transports.
Post-change: handled `OSError`/`SerialException`, transport marked
DISCONNECTED. Correction to the §5.3 framing: the `AttributeError` was
caught by `send_command`'s broad `except Exception` and returned `None`
exactly as a handled I/O error does — the defect was silent in
production, and the reproduction had to classify by logged message
rather than return value.

### 4.5 Findings Requiring Decision

Four defects outside an implementing executor's authority:

1. **Live `DisplayMode.DIGITAL` references survive `378703da`.**
   `display/touch.py` (8 sites) and `display/navigation_gestures.py`
   (2 sites) still referenced the removed enum member, both instantiated
   at runtime. `378703da`'s four-file constraint excluded both modules
   and its own success criterion (repo-wide grep clean) was
   unsatisfiable within that constraint. **The only finding that could
   fault the running application** — subsequently confirmed on-target
   (§5.1 below) and fixed as `7f2a9c04`.
2. **Night palette toggle cannot fire.** `5012004e` specifies a
   double-tap; no `DOUBLE_TAP` gesture exists. Delivered with the
   registration conditional on `getattr(GestureType, 'DOUBLE_TAP', None)`,
   so the feature activates automatically once the gesture subsystem
   provides it. Until then, complete and unreachable.
3. **Contrast requirement arithmetically unsatisfiable.** `5014040c` and
   `5012004e` each fix palette values and require every band colour to
   reach 3:1 contrast — both cannot hold simultaneously (pure blue's
   luminance is too low). Measured as delivered: day blue 2.21:1, night
   blue 1.55:1, `FACE_TRACK` 1.67:1, `FACE_EDGE` 2.02:1, `FACE_LINE`
   2.76:1; all other pairs pass. Implemented as written because both
   prompts forbid changing the colours.
4. **`b02ed4ea` leaves *Clear settings* with no entry point.** Recorded
   as an open decision before implementation (§3.7 above); now live in
   source. §7.7's re-layout is where the recovered space comes from.

### 4.6 Deviations from Prompt Specifications

1. `BAND_COLOURS[0]` — `5014040c` EDIT C specified `(0, 0, 0)`;
   delivered as `(0, 0, 255)`, because black was DIGITAL's idle
   background and adopting it would have erased the idle arc segment.
   The prompt's own "unchanged" constraint on that colour governed.
2. Transport primitives delivered as concrete methods raising
   `NotImplementedError` rather than `@abstractmethod`, because abstract
   declarations would make `SimTransport` uninstantiable (it overrides
   all five skeleton methods and supplies none of the four primitives,
   and the prompt forbids modifying it).
3. `saved_devices` — `394c3bbb` required the string to appear nowhere in
   `src/gtach`; delivered with the token absent from code and the two
   explanatory comments reworded.
4. Minor: `app.py:91` still tests `transport_arg == 'simbt'` as a fourth
   literal transport-name site, left because `6481f8ce` Stage 3 named
   three sites and said to change nothing else.

### 4.7 Governance Gaps Left Open

No T06 result documents for the six implemented triples; §8.2's minimal
pytest suite remains unwritten (`tests/` collects zero items); the branch
was unpushed and unmerged with two of eight triples unimplemented.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 On-Target Session — 2026-08-05

`v0.4.0-display-triples` was deployed to `gtach.local` and `logs/`
pulled back.

### 5.1 §4.5 Item 1 Confirmed — Operator Trapped on the Options Screen

`logs/start.log` carried five lines and no other errors in 3.5 MB, all
`TouchHandler ERROR ... handling error: DIGITAL`. `touch.py:171` names
`DisplayMode.DIGITAL`, removed by `change-378703da`; the access raises
`AttributeError('DIGITAL')`, caught and swallowed at `touch.py:174`, so
the gesture silently does nothing. Two facts the static review had not
established: `TouchHandler`'s handlers are the ones that fire (registered
on a **started** touch interface), and the fault is swallowed, which is
why five ERROR lines sat in the log without anything appearing wrong.

Raised as **`7f2a9c04`**, severity high, ungated. Implemented and
verified working in §6.0 below; governance documents closed.

### 5.2 New — Debug Toggle Fires but the Handler Fails

```
TouchEventCoordinator DEBUG Button debug_toggle pressed
DisplayManager INFO Debug logging toggle -> on
gtach.app DEBUG Could not toggle debug logging:
          'function' object has no attribute '_debug_handler'
```

`app.py:155` does `from . import main as _main`, but `_main` binds to
the function `main`, not the module. Caught at `app.py:166`, logged at
DEBUG, nothing surfaces to the operator. Consequence: `debug.log` stayed
at 0 bytes while `start.log` held 57,560 DEBUG lines, and the options
label read *Debug: Off* while debug was in fact on. Not raised as a T03
at this point — recorded so it would not be lost. Raised on 2026-08-05
as part of `c1d4b8e6` (§6.1 below); still open — see `task.md`.

### 5.3 Scope Extension Agreed — Swipe Navigation for OPTIONS

The operator proposed swipe-down to enter and swipe-up to leave OPTIONS,
reasoning that a toggle has no second route when one direction fails —
exactly what §5.1 produced. Agreed by consensus, authored as
**`3e8b1d72`**, kept separate from `7f2a9c04` so a subsequent navigation
problem would stay attributable. Scoping found the touch subsystem
already dispatches `SWIPE_UP`/`SWIPE_DOWN` (no work needed in
`display/input`), and that two live long-press handlers exist
(`manager.py`, `touch.py`) which both had to change together.
Implemented and verified in §6.0; governance documents closed.

### 5.4 Root Cause of §5.1 — A File-Scoped Constraint on a Package-Wide Change

`prompt-378703da` removed an enum member — a package-wide interface
change — under a four-file constraint that could not simultaneously
satisfy its own repo-wide-grep success criterion. The executor recorded
the conflict and did not exceed scope; the defect was in the prompt. The
lesson: a change that alters a package-wide interface cannot be scoped
by file list — the scope is every reference, found by grep, not assumed
from the files the author expected to be involved. `change-7f2a9c04`
accordingly made its success criterion a repository-wide grep.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Second On-Target Session — 2026-08-05

`7f2a9c04` and `3e8b1d72` were implemented and deployed. The session log
carried **one ERROR in 362 KB** and no `DIGITAL` line: both fixes work,
swipe navigation operates, and the operator confirmed entering and
leaving OPTIONS.

### 6.1 Debug Toggle Still Broken — Raised as `c1d4b8e6`

The operator reported it working; the log disagreed — three presses,
three identical failures. Root cause: `gtach/__init__.py:11` does
`from .main import main`, so the package attribute `main` **is** the
function; `app.py`'s `from . import main as _main` retrieves the
function, whose namespace holds no `_debug_handler`. The same pattern
breaks `_finish_startup_logging`, so `_start_handler` is never demoted —
why `start.log` reached 3.5 MB while `debug.log` stayed at 0 bytes. The
fault is self-concealing: both sites log at DEBUG, and one of them is the
control that turns DEBUG on.

### 6.2 `engine_profiles.yaml` Is Not in the Wheel

`pyproject.toml` declared package-data as `assets/fonts/*.ttf`/`*.otf`
only; confirmed against the built wheel, only `Michroma-Regular.ttf` is
present under `assets/`. Current impact is zero — the
`abarth_595_turismo` profile's thresholds coincide with the `RPMBands`
dataclass defaults by coincidence — but `generic_turbo_4cyl` and
`generic_na_4cyl` are unreachable and the `engine_profile` key is inert.
Second occurrence of this defect class; `issue-d7f2b4e6` (Michroma font)
was the first.

### 6.3 A Second Stale Footer

`_draw_update_view` (`manager.py:1672`) still rendered *"Long press to
return"* after `change-3e8b1d72` made long press inert. Outside that
prompt's stated scope; its executor reported it rather than exceeding
scope. Raised at the operator's request.

§6.1–§6.3 were grouped into one triple, **`c1d4b8e6`**, on the
`change-d32ccc49` pattern (three small independent faults in three
files). Authored 2026-08-05. **Status as of this writing: change
document status `proposed` — not implemented.** See `task.md` for
current status; do not treat this triple as closed on the strength of
its prompt document alone, which is filed in `prompt/closed/` per this
project's convention of moving a prompt once its cycle is exercised, not
only once code lands.

### 6.4 Open — OBD Response Stream Desynchronises After a Timeout

Not raised as a T03 at time of writing (still not raised — see
`task.md` §4.0). The ELM327 emulator paired and answered cleanly, then a
`0100` timeout (1.0 s, shorter than the ELM327's protocol search) left
an undrained late response in the buffer, offsetting every subsequent
read by one command. Same class as `issue-a3f1d8e2` (closed). Severity
assessment **superseded by §8.0 below** — the initial "does not recover"
finding was drawn from a 90-second session and was wrong.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 §8.4 Observation Session — Discharged From Logs

Five of the six planned §7.5 observation items were answerable from logs
already pulled, because the instrumentation each depended on had since
shipped. Evidence: `logs/start.log`/`debug.log`, session 2026-08-05
08:42:18–08:43:36, application version 0.3.3.

### 7.1 Results

| Item | Result |
|---|---|
| Framebuffer geometry | Discharged: 480×480, 32-bit, stride 1920 (sysfs) — exactly what `engine.py` assumed. Display report §8.3 is not an active fault; page flip confirmed operating |
| Flicker characterisation | Outstanding at this point — the only item needing the panel directly (discharged in §9.0 below) |
| Frame-time baseline | Discharged indicatively — see §7.2 |
| `ConfigManager` disposition | Decided 2026-07-30 (retire); implemented by `394c3bbb` |
| Transport race | Discharged by `6481f8ce`'s reproduction (§4.4) |
| Hardware revision | Substantively answered: `Selected platform: RASPBERRY_PI_ZERO_2W (score: 1.85)` — detection correct |

### 7.2 The Frame-Time Baseline (Indicative)

Four periodic samples: RADIAL cost 14.7–19.3 ms against a 16.67 ms
budget (88–116% of budget); the static OPTIONS screen cost 6.3 ms per
frame, sixty times a second, to draw an unchanging image. Caveat: three
RADIAL samples from one 90-second session — direction, not a rigorous
baseline (firmed up in §8.0).

### 7.3 Gate Evaluation

`821919ce` gate **clears** — render cost is at or over the whole 60 Hz
budget, more strongly than framed at authoring. `9ed1c77e`'s two
recommendations separate: recommendation 12 (`fps_limit` 30) is
supported independently of any assumption (53 FPS observed, well under
60); recommendation 13 (conditional render) still needs `821919ce`'s
effect measured first.

### 7.4 Residual On-Panel Work

Reduced to two items: the §7.5.2 flicker characterisation, and a firmer
frame-time baseline from a longer, untouched run.

### 7.5 Collateral — OBD Desynchronisation Reproduces

Reproduced again, more clearly: `0100` received `ATSP0`'s acknowledgement
and `010C` was polled three times unanswered before a stale `0100`
answer arrived. Whether this corrupts the displayed reading was not
established at the time — **tested in §8.0, which supersedes this
section's severity assessment.**

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Long Run — 52 Minutes, 2026-08-05

A 52-minute run (08:42:56–09:34:42), simulation mode for the bulk and
Bluetooth against the ELM327 emulator for the final 75 seconds. 15.9 MB
of debug log, two warnings (both in the first two seconds — initial
`010C` timeouts) and no errors.

### 8.1 Frame-Time Baseline, Firm

297 samples: min 6.3 ms, p25 14.3, median 14.7, mean 16.0, p90 19.7, max
21.2 ms. **32% of frames exceed the 16.67 ms budget at 60 Hz; 0% exceed
33.3 ms at 30 Hz** (not one of 297). Render cost equivalent in simulation
(median 14.7 ms, n=290) and Bluetooth (14.9 ms, n=7) modes.

**Consequence for `9ed1c77e` recommendation 12:** reducing `fps_limit`
to 30 would eliminate every observed overrun with a one-line
configuration change — stronger than the recommendation claimed for
itself, and it should ship before `821919ce`.

### 8.2 OBD Desynchronisation — Corrected

Two findings supersede §6.4 and §7.5:

1. **It recovers.** In steady state every `TX: 010C` is matched by
   `410C…`. The offset is confined to the initialisation handshake; the
   earlier "does not recover" claim was drawn from a 90-second session
   and was wrong.
2. **The displayed value is correct.** Over the Bluetooth window (874
   responses, 4,193 frames), the emulator sent 14 distinct values
   spanning 0–4,208 RPM and not one displayed value fell outside that
   range — `_condition_rpm`'s EMA interpolates between them as designed.

Severity dropped from "may corrupt the primary reading" to
"initialisation-phase robustness": two timeouts, one ERROR, a few
seconds of delay at startup. Still worth a triple (not yet raised — see
`task.md` §4.0) but not urgent.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Flicker Discharged and Efficiency Triples Deferred

### 9.1 §7.5.2 Discharged — The Flicker Is Gone

`fps_limit` set to 30 on target, restarted 10:17:18. Observed: no
tearing, no flashing, no band thrash, needle reads acceptably at 30 Hz.
Discharges the last §8.4 item; closes display report §4.0 in full.

30 Hz baseline, 32 samples: FPS exactly 30.0 in every sample (against six
distinct values at 60 Hz); median frame 15.3 ms; **zero overruns**; 46%
of budget used at median (down from 88%). Render cost unchanged — only
the deadline moved. The finding: frame pacing went from irregular to
exact, and all five display-report §4.x flicker mechanisms had been
addressed in sequence (unsynchronised writes → `66ef59a0`/`49b21ace`;
band-colour thrash → `4c038bed`; value churn → `4c038bed`'s EMA; flash
duty cycle → `4c038bed`'s frame-counter phase; frame-time jitter →
`9ed1c77e` Part 2). No single change is claimed as *the* fix.

### 9.2 Consequence — `821919ce` and `9ed1c77e` Part 3 Lose Their Justification

`change-821919ce`'s own withdrawal condition, written 2026-08-04 before
any baseline existed: *"If RADIAL frames already complete well inside
the budget, this change buys little and its medium risk is not
justified — withdraw or defer it rather than proceeding."* Met: 46% of
budget used, zero overruns, flicker resolved. `9ed1c77e` Part 3 falls
with it — its own change document named the fallback (take the
`fps_limit` reduction alone if the render-cost assumption fails; it
did). **Both deferred, not rejected** — complete and implementable if a
heavier render path, a slower target, or a measured GIL-contention
problem makes them relevant again.

A T02 schema gap this exposed: `change_info.status` had no `deferred`
value (T03 has carried one since v1.0). Added in T04… T02-change.md
v1.4, with precedent in v1.3's addition of `closed`.

### 9.3 Two Small Defects the `fps_limit` Change Exposed

1. `PerformanceMonitor` is constructed with a hardcoded
   `target_fps=60` (`manager.py:159`); at 30 Hz its dropped-frame
   threshold, `min_fps` alarm and history sizing are all wrong for the
   actual rate. The startup "target: 60 FPS" line is the visible
   symptom.
2. `debug.log` never truncates — `main.py:47` passes `mode='w'` to
   `RotatingFileHandler`, which silently overrides it to `'a'` whenever
   `maxBytes > 0` (verified against CPython source). `debug.log` reached
   31.6 MB across three sessions.

### 9.4 §8.1's Advice Vindicated Twice

Recorded at authoring time that `821919ce`/`9ed1c77e` "cannot be
authored correctly yet" pending observations, then authored anyway on
instruction with explicit assumptions recorded. Both halves proved
useful: the prompts halted at their gates rather than optimising a fault
-free renderer, and the enumerated assumptions turned the deferral into
checking one number (A1) rather than re-arguing the design.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-07 | Split from `ai/task.md` §9.0–§9.13 and the extended §3.0/§7.0 verification detail, as part of the task-list size reduction recorded in `task.md`'s own version history (v18.0). No content altered from the source revision, only relocated and given its own table of contents. |

---

Copyright (c) 2026 William Watson. MIT License.
