Created: 2026 August 12

# Report: One Setup Button and a Retry-Countdown Arc on the DISCONNECTED Screen

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Instruction and Outcome](<#2.0 instruction and outcome>)
- [3.0 Edits Applied](<#3.0 edits applied>)
- [4.0 Tests Added](<#4.0 tests added>)
- [5.0 Verification Method](<#5.0 verification method>)
- [6.0 Success Criteria](<#6.0 success criteria>)
- [7.0 Deviations from the Prompt Specification](<#7.0 deviations from the prompt specification>)
- [8.0 Findings Requiring Decision](<#8.0 findings requiring decision>)
- [9.0 Commit Record](<#9.0 commit record>)
- [10.0 Work Remaining](<#10.0 work remaining>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records the implementation of
`prompt-4f1e82b7-disconnected-screen-diagnostics.md` (iteration 1,
coupled to `change-4f1e82b7` and `issue-4f1e82b7`).

The DISCONNECTED screen carried a Simulate button duplicating OPTIONS
page 0's `simulation_mode` control, and was visually identical whether
GTach was retrying, blocked on a wedged Bluetooth controller, or a live
process with every worker torn down. This change removes the duplicate
control and adds a retry-countdown arc driven by the display frame
clock.

Scope is what was changed and how it was verified. On-target
verification is a human step and is outside this prompt.

---

## 2.0 Instruction and Outcome

The instruction was to implement the prompt, close the prompt T-Doc,
commit and push it, and leave the issue and change T-Docs active pending
test results.

| Item | Outcome |
|---|---|
| EDIT U — one button on the DISCONNECTED screen | ✅ Applied |
| EDIT V — the retry-countdown arc | ✅ Applied |
| EDIT V(b) — `_retry_interval_callback` wiring | ✅ Applied, and nothing else |
| `tests/test_disconnected_screen.py` | ✅ Created, 24 tests |
| `pytest tests/` | ✅ 168 passed, 0 failed |
| Prompt T-Doc closed, committed and pushed | ✅ |

**The critical constraint is satisfied and is enforced by test at two
levels.** The arc's phase is `(time.monotonic() % period) / period` and
reads no transport attribute or transport-derived state.
`test_source_reads_monotonic_and_no_transport_state` parses the method,
strips its docstring and comments, and asserts that `_transport`,
`is_connected`, `last_failure_cause`, `_link_connected_callback` and
`_link_cause_callback` appear nowhere in the executable body.
`test_arc_advances_with_the_clock_alone` proves the same behaviourally:
it renders twice with the monotonic clock advanced by half a period and
nothing else changed, and asserts the filled arc's angular extent
halves.

No control was added in the freed slot. `_button_column`,
`_on_simulation_mode`, OPTIONS page 0's `simulation_mode` registration
and `_enter_setup_from_disconnected` are all byte-identical — verified
by diff, not by inspection. `src/gtach/comm/` is untouched throughout.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Edits Applied

### 3.1 EDIT U — one button

`_register_disconnected_regions` (manager.py:1712) now passes a
one-element sequence to `_button_column`, containing only the
`disconnected_setup` spec. `width=240` and `top=240` are unchanged, and
`_button_column` stacks downward from an explicit top, so the Setup
button occupies exactly the rect it did as first of two —
`test_setup_rect_is_the_first_rect` asserts that positionally.

`self._disconnected_btn_sim` is gone as an attribute, not merely as an
assignment: its initialiser at manager.py:143 was removed along with the
tuple unpacking and the render-loop entry. `grep` over `manager.py` for
both `_disconnected_btn_sim` and `disconnected_simulate` returns
nothing, asserted by
`test_sim_attribute_and_region_are_gone_from_the_module`.

The docstring records that Simulate lives on OPTIONS page 0 and is one
downward swipe away, and that the freed slot is deliberately empty
pending the Bluetooth-reset issue.

In `_render_disconnected`, the two-entry draw loop became a single
guarded `_draw_button` call for Setup.

One further reference existed outside `manager.py`:
`tests/test_connect_error_classification.py` set
`host._disconnected_btn_sim = None` on its render host. That line is now
dead — the render no longer reads the attribute — so it was replaced
with the `_draw_retry_arc` stub the render now needs. Noted in §7.

### 3.2 EDIT V — the retry-countdown arc

`self._retry_interval_callback = None` added beside the existing
`_link_connected_callback` and `_link_cause_callback` initialisers
(manager.py:113), matching their pattern and commented to say it
supplies the arc's PERIOD only.

`_RETRY_ARC_DEFAULT_PERIOD = 5.0` added as a class constant, matching
`reconnect_indefinitely`'s `retry_delay` default.

`_draw_retry_arc(self) -> None` (manager.py:2362) resolves the period
from the callback inside its own `try/except Exception`, accepting it
only when it is a real positive number. `bool` is explicitly rejected —
`True` is an `int` in Python and would otherwise yield a 1.0 s period,
which `test_bool_is_not_accepted_as_a_period` guards.

The phase is `(time.monotonic() % period) / period`, and the arc is
drawn full at phase 0, emptying as the next attempt approaches. The
modulo keeps the phase valid for any clock value and for a period
shorter than one frame interval; both are covered by tests.

The arc is drawn with the same polygon approximation and the same
palette the RPM gauge's donut arcs use — a 120° sweep centred on 6
o'clock at radii 186–200, which lies below the button column's `top=240`
plus its ≥72 px height and inside the r=238 viewport. The track uses
`palette.track` and the fill `palette.label`, both from the active
palette.

The whole body is wrapped so a failure cannot prevent the rest of the
screen rendering; failures log at DEBUG with `exc_info=True`. This
proved itself during development — the first test run failed with the
arc silently absent and a DEBUG line naming the exact `AttributeError`,
which is precisely the designed behaviour.

`_draw_retry_arc` is called from `_render_disconnected` after the button
is drawn, asserted by `test_arc_is_drawn_after_the_button`.

The docstring states plainly that the phase comes from the display frame
clock and not from transport state, why that matters, and that the arc
indicates approximately when the next attempt falls rather than being a
synchronised countdown.

### 3.3 EDIT V(b) — the interval wiring

`self._display._retry_interval_callback` is assigned at both sites in
`app.py` that already assign `_link_connected_callback` and
`_link_cause_callback`, using the same nested-`getattr` guard so that no
transport yet present yields `None` rather than raising.

It reads a `retry_delay` attribute from the transport. No such attribute
exists today — `reconnect_indefinitely` is started without a
`retry_delay`, so its 5.0 s default applies — so the callback yields
`None` and the arc uses its own 5.0 s fallback, which is the same value.
Reading the attribute rather than hard-coding 5.0 means the arc follows
any future configured value without further wiring. The comment at both
sites records this. See §8 finding 1.

Two hunks in `app.py`, twelve lines each; nothing else changed.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Tests Added

`tests/test_disconnected_screen.py` — 24 tests covering all eleven
`testing.unit_tests` scenarios and all three edge cases.

| Test | Prompt item |
|---|---|
| `test_exactly_one_region_registered` | item 1 |
| `test_no_simulate_region` | item 1 |
| `test_geometry_unchanged` | item 2, criterion 3 |
| `test_setup_rect_is_the_first_rect` | item 2 |
| `test_sim_attribute_and_region_are_gone_from_the_module` | criteria 1, 2 |
| `test_no_control_added_in_the_freed_slot` | criterion 11 |
| `test_default_period_constant` | criterion 6 |
| `test_callback_unset_uses_default` | item 3 |
| `test_zero_period_falls_back` | item 5 |
| `test_negative_period_falls_back` | item 6 |
| `test_raising_callback_falls_back` | item 7 |
| `test_non_numeric_period_falls_back` | error_handling |
| `test_bool_is_not_accepted_as_a_period` | error_handling |
| `test_period_shorter_than_a_frame_stays_in_range` | edge case 1 |
| `test_very_large_clock_still_yields_a_valid_phase` | edge case 2 |
| `test_drawing_failure_does_not_propagate` | item 8 |
| `test_arc_advances_with_the_clock_alone` | items 4, 9 |
| `test_phase_is_periodic` | item 4 |
| `test_source_reads_monotonic_and_no_transport_state` | items 9, 11; criterion 5 |
| `test_phase_line_derives_only_from_clock_and_period` | item 11 |
| `test_only_setup_is_drawn` | item 1 |
| `test_cause_line_is_unchanged` | item 10, criterion 10 |
| `test_title_and_message_unchanged` | criterion 10 |
| `test_arc_is_drawn_after_the_button` | EDIT V ordering |

Three harness notes:

**`_register_disconnected_regions` is driven against a recording
`_button_column`.** That records the specs, width and top it was called
with and returns one rect per spec, so the tests assert on the *call*
rather than on pygame geometry. This is what makes
`test_setup_rect_is_the_first_rect` meaningful without instantiating a
display.

**The arc tests assert on real geometry, not on a call count.**
`_sweep_extent` patches `pygame.draw.polygon`, captures the two polygons
the method emits, and computes the filled arc's angular extent with
`atan2`. `test_arc_advances_with_the_clock_alone` then asserts that
extent *halves* when the clock advances by half a period — a claim about
the phase arithmetic, not merely that something was drawn.

**`test_cause_line_is_unchanged` pins position, font and colour.**
`change-5e7a03c4`'s line must survive this change untouched, so the test
asserts `(240, 210)`, `font-18` and `(200, 160, 100)` rather than just
its presence.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification Method

As in the six preceding prompts, no `venv/` exists in the working tree
and the interpreter has none of the project's dependencies. A throwaway
virtualenv was rebuilt in the session scratchpad with `pytest<9`,
`pytest-cov`, `pygame`, `pyserial`, `pyyaml`, `psutil` and
`pip install -e .`, then deleted. `pip install -e .` rewrote
`src/gtach.egg-info/SOURCES.txt`; that file was restored with
`git checkout`.

```
$ pytest tests/
168 passed, 1 warning in 5.32s
```

The 144 tests standing at the end of `prompt-5e7a03c4` pass alongside
the 24 new ones.

`ast.parse` succeeded on `src/gtach/display/manager.py`,
`src/gtach/app.py` and the new test file.

Byte-identity was checked by diff:

```
$ git diff src/gtach/display/manager.py | grep -cE "^[-+].*def _button_column"          → 0
$ git diff src/gtach/display/manager.py | grep -cE "^[-+].*def _on_simulation_mode"      → 0
$ git diff src/gtach/display/manager.py | grep -cE "^[-+].*_enter_setup_from_disconnected" → 0
$ git status --porcelain src/gtach/comm/                                                  → empty
$ git diff -U0 src/gtach/app.py | grep "^@@"    → two hunks, both the wiring
```

The two `simulation_mode` occurrences in the `manager.py` diff are the
removed DISCONNECTED spec and one word in the new docstring; OPTIONS page
0's registration at manager.py:1626 and `_on_simulation_mode` at
manager.py:2049 are untouched.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Success Criteria

All fourteen criteria verified.

| # | Criterion | Result |
|---|---|---|
| 1 | `grep -n 'disconnected_simulate' manager.py` returns no match | ✅ |
| 2 | `grep -n '_disconnected_btn_sim' manager.py` returns no match | ✅ |
| 3 | One-element sequence, `width=240`, `top=240` unchanged | ✅ manager.py:1735–1741 |
| 4 | `_draw_retry_arc` defined and called from `_render_disconnected` | ✅ manager.py:2362, 2350 |
| 5 | Phase references `time.monotonic()`, no transport attribute | ✅ two tests, one source-level |
| 6 | Period falls back to 5.0 when unset, raising or non-positive | ✅ six tests |
| 7 | `_button_column` byte-identical | ✅ absent from the diff |
| 8 | `_on_simulation_mode` and OPTIONS page 0 registration byte-identical | ✅ manager.py:1626, 2049 |
| 9 | `_enter_setup_from_disconnected` byte-identical | ✅ context line only |
| 10 | `change-5e7a03c4`'s cause line unchanged | ✅ position, font and colour asserted |
| 11 | No control added in the freed slot | ✅ asserted by test |
| 12 | The only `app.py` change is the `_retry_interval_callback` wiring | ✅ two hunks |
| 13 | `src/gtach/comm/` byte-identical throughout | ✅ absent from `git status` |
| 14 | `pytest tests/` passes | ✅ 168 passed |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Deviations from the Prompt Specification

Two, both minor and both consequences of the prompt's own instructions.

**1. The interval callback reads a `retry_delay` attribute that does not
exist.** EDIT V(b) says to wire a callback "returning the transport's
configured retry delay". There is no such attribute: the retry delay is
`reconnect_indefinitely`'s parameter default, and `app.py` starts the
thread without passing one. The prompt also forbids modifying
`src/gtach/comm/`, so adding the attribute was not available. The
callback therefore reads `retry_delay` via `getattr` and yields `None`
today, so the arc uses its own 5.0 s fallback — numerically identical to
the configured value. This satisfies the functional requirement
("falls back to a 5.0 s period when the interval is unavailable") and
means the arc will follow a configured value automatically if one is
ever introduced. Recorded because the wiring reads as though it does
something today and does not. See §8 finding 1.

**2. One line changed in `tests/test_connect_error_classification.py`.**
That file's render host set `_disconnected_btn_sim = None`, an attribute
this change removes, and needed a `_draw_retry_arc` stub for the render
it now performs. One line replaced the other. No assertion in that
module changed and all its tests pass unmodified otherwise. The prompt
did not name it, but EDIT U's instruction to "check for and remove any
other reference" to the attribute covers it.

Beyond those, EDITs U, V and V(b) were applied as specified, and all
eleven unit-test scenarios plus the three edge cases were implemented.
Thirteen tests were added beyond the eleven scenarios, each asserting a
success criterion or stated error-handling rule the prompt lists without
allocating to a scenario.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Findings Requiring Decision

Three, none blocking.

1. **The arc's period is effectively hard-coded at 5.0 until something
   sets `retry_delay` on the transport.** As §7 records, the wiring is
   in place but inert. Making it live needs one attribute on
   `OBDTransport` — assigned from `reconnect_indefinitely`'s parameter,
   or from config — which is a `src/gtach/comm/` change this prompt
   forbids. Worth a line in `change-4f1e82b7` so the inert wiring is not
   later mistaken for a defect.

2. **The arc is not synchronised with the transport's retry timer, and
   deliberately so.** Its docstring says as much, but the operational
   consequence is worth stating: the arc reaching empty does not mean an
   attempt is happening at that instant, and after a connect that blocks
   for tens of seconds the arc will have swept several times with no
   attempt made. It answers "is the application alive" reliably and
   "when is the next attempt" only approximately. If the second question
   ever needs a true answer, it requires the transport to publish its
   next-attempt deadline — which reintroduces exactly the coupling the
   critical constraint forbids, and would need the freeze behaviour
   solved another way.

3. **`_render_disconnected` now performs meaningfully more work per
   frame** — two 122-point polygons on every frame at 30 FPS, where
   before it drew two rounded rects and three text runs. The prompt's
   performance target is that the screen still reports 30.0 FPS, which
   cannot be checked off-target; the RPM gauge draws several such arcs
   per frame at the same rate, so there is good reason to expect it
   holds. It remains an on-target check rather than a verified fact.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Commit Record

Committed and pushed as a single commit containing
`src/gtach/display/manager.py`, `src/gtach/app.py`,
`tests/test_disconnected_screen.py`, the one-line
`tests/test_connect_error_classification.py` update, this report and the
prompt T-Doc closure move.

Not included, and left uncommitted in the working tree: `.gitignore`,
`CLAUDE.md`, the `change-2ac1c602` and `issue-2ac1c602` modifications,
and the untracked `change-7d4e91a3` and `issue-7d4e91a3` T-Docs. These
are authoring work belonging to the user, not this prompt's deliverable.
The `change-4f1e82b7` and `issue-4f1e82b7` T-Docs for this triple were
already committed and remain active and unmodified.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Work Remaining

On-target verification on `gtach.local`, per the prompt's notes, with no
OBD connection available:

1. Confirm one button only on the DISCONNECTED screen.
2. Confirm Simulate is still reachable on OPTIONS page 0 by the downward
   swipe.
3. Confirm the arc sweeps and empties roughly once per retry interval.
4. **The point of the change:** confirm the arc KEEPS animating while a
   connect attempt is blocked. `gtach.local`'s current EBUSY state makes
   this readily reproducible.
5. Confirm the performance line still reports 30.0 FPS on this screen
   (§8 finding 3).

The freed button slot is intentionally empty. A Bluetooth reset button is
wanted there and is blocked on establishing which recovery command works
on this hardware — `hciconfig hci0 down && up` was tried on target and
left the controller unable to come back.

`issue-4f1e82b7` and `change-4f1e82b7` remain active pending the five
steps above.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial report. Implements prompt-4f1e82b7 iteration 1: Simulate removed from the DISCONNECTED screen, _draw_retry_arc added driven by time.monotonic() alone, and _retry_interval_callback wired in app.py, plus 24 unit tests. All fourteen success criteria verified. Two minor deviations recorded: the interval callback reads a transport attribute that does not yet exist, and one line of tests/test_connect_error_classification.py referencing the removed attribute was updated. Prompt T-Doc closed, committed and pushed; issue and change T-Docs left active. |

---

Copyright (c) 2026 William Watson. MIT License.
