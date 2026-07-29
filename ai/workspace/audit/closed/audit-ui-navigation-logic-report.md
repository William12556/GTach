Created: 2026 May 29

# GTach UI Navigation Logic — Remediation Report

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Reported Symptoms](<#2.0 reported symptoms>)
[3.0 Architecture Context](<#3.0 architecture context>)
[4.0 Findings](<#4.0 findings>)
[5.0 Log Evidence](<#5.0 log evidence>)
[6.0 Recommended Remediation](<#6.0 recommended remediation>)
[7.0 Remediation Priority](<#7.0 remediation priority>)
[8.0 Secondary Observations](<#8.0 secondary observations>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document records an audit of the GTach display navigation logic
prompted by three operator-reported user-interface defects. It identifies
the responsible code paths, states the mechanism of each defect, and
proposes minimal remediation. No source code was modified.

Scope: source code only (`src/gtach/`). Files examined: `app.py`,
`display/manager.py`, `display/setup.py`, `display/setup_models.py`.
Runtime evidence: `gtach-debug.log` (2026-05-29 session).

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Reported Symptoms

| # | Symptom |
|---|---|
| S1 | No toggle from simulation mode back to Bluetooth mode in the options screen. |
| S2 | Clear settings → re-pair → select device lands on the options screen, although a device is found. Expected: the radial/digital connected screen. |
| S3 | The simulation button is not a state-indicating toggle. Its label does not show which mode it will activate. |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Architecture Context

The display loop (`DisplayManager._display_loop`) dispatches on two
orthogonal pieces of state:

- `_in_setup_mode` (bool) — when true, setup screens render regardless of
  `config.mode`.
- `config.mode` (`DisplayMode`) — selects the normal-mode screen:
  `DIGITAL`, `RADIAL`, `OPTIONS`, `ACKNOWLEDGEMENT`.

`OPTIONS` is a transient mode reached only by long-press
(`_handle_long_press`). `_save_config` refuses to persist transient modes,
and `_load_config` maps any persisted transient mode to `RADIAL`.

Two unrelated notions of "simulation" coexist:

1. Launch-time `--transport simbt`/`simtcp` selects a simulated transport
   (`SimTransport`).
2. Runtime `_sim_mode` (DisplayManager) injects synthetic RPM at the
   display layer only and does not alter the transport.

The options-screen "Simulation mode" button controls notion (2) exclusively.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Findings

### 4.1 Finding A — Stale `OPTIONS` mode persists after setup re-entry (S2)

The "Clear settings" button resides on the options screen, so
`config.mode == DisplayMode.OPTIONS` when `_on_clear_settings()` executes.
That handler invokes `_setup_entry_callback`, bound to
`GTachApplication._re_enter_setup()`, which calls `_start_setup_mode()`.

On re-entry, `_start_setup_mode()` reuses the existing `DisplayManager`
(the `start()`/splash path is guarded out) and never resets `config.mode`.
Setup renders correctly because `_in_setup_mode` is true.

On completion, `_on_setup_complete()` calls `exit_setup_mode()`
(`_in_setup_mode = False`) and `_start_obd()`. Neither resets
`config.mode`. Control returns to `_render_normal_modes()`, which dispatches
on `config.mode` — still `OPTIONS` — and renders `_draw_options_mode()`.

Net effect: after re-pairing, the connected screen is the options screen.
A full process restart does not exhibit this, because the post-splash
target is derived from persisted config (transient modes excluded); the
defect is specific to the in-process re-entry path.

### 4.2 Finding B — Simulation button is a static, non-indicating control (S1, S3)

`_draw_options_mode()` always labels the lower button "Simulation mode";
`_render_disconnected()` labels its equivalent "Simulate". Both invoke
`_on_simulation_mode()`, which toggles `_sim_mode` and then sets
`config.mode` to `DIGITAL` (on) or `RADIAL` (off).

The label is fixed and reflects neither the current `_sim_mode` state nor
the destination. Because the handler changes `config.mode`, the press also
leaves the options screen, so the toggle state is never observable on the
control itself. From the operator's perspective there is no visible
Bluetooth↔simulation toggle, matching S1 and S3.

### 4.3 Finding C — Conflated "simulation" terminology (contributing to S3)

The runtime `_sim_mode` flag and the launch-time simulated transport are
distinct mechanisms sharing the word "simulation". The options button
affects only the display-layer flag. The terminology overlap is a probable
source of the S3 expectation regarding the "Bluetooth connection emulator".

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Log Evidence

From `gtach-debug.log`, a clear-settings re-entry cycle:

| Time | Event |
|---|---|
| 07:35:41,358 | `Clearing device settings` |
| 07:35:41,372 | `Device store cleared — invoking setup_entry_callback` |
| 07:35:41,372 | `Re-entering setup from DISCONNECTED screen` |
| 07:35:46,383 | `Reusing existing DisplayManager for setup re-entry` |
| 07:36:47,185 | `Setup complete — invoking on_complete callback` |
| 07:36:47,186 | `Exited setup mode` |

Between `Exited setup mode` (07:36:47) and the next operator action
(07:37:24), the log contains no per-frame render markers for `RADIAL`
(`Radial mode: RPM=`), `DIGITAL` (`band colour`), `DISCONNECTED`
(`DISCONNECTED screen rendered`), or acknowledgement screens. The options
screen is the only normal mode without per-frame logging. The first
`Radial mode` line (07:37:24,071) appears immediately after the operator
pressed the simulation button (`Simulation mode off`, 07:37:24,055), which
set `config.mode = RADIAL`.

This corroborates Finding A: the connected screen sat on `OPTIONS` after a
device was paired, and only a manual button press moved it off.

Note: `_re_enter_setup` logs "from DISCONNECTED screen" unconditionally,
even when entered via the options "Clear settings" path. The log label is
inaccurate but not itself a defect.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Recommended Remediation

### 6.1 Finding A

Reset the display mode to the normal target on setup completion. Single
location, minimal delta. In `GTachApplication._on_setup_complete()`, after
`exit_setup_mode()`:

```python
self._display.config.mode = self._display._post_splash_mode
```

Equivalent alternative: reset `config.mode` inside
`DisplayManager.exit_setup_mode()`. One site only, to avoid divergence.

### 6.2 Finding B

Make the simulation control state-indicating, and keep its state observable.

1. In `_draw_options_mode()`, derive the label from `_sim_mode`:
   - `_sim_mode` false → label indicates entering simulation.
   - `_sim_mode` true → label indicates returning to live OBD / Bluetooth.
2. Consider not changing `config.mode` from within the options screen, so
   the operator can read the toggled state before returning by long-press.
   If the immediate mode switch is retained, the label change alone still
   resolves S1/S3.
3. Apply the same label convention to the `_render_disconnected()` button
   for consistency.

### 6.3 Finding C

UI terminology only. Disambiguate the display-layer flag from the
simulated transport in operator-visible labels (for example, naming the
display-layer flag distinctly from transport simulation). This is a design
decision and is deferred to consensus rather than treated as a fix.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Remediation Priority

| Priority | Finding | Symptom | Nature |
|---|---|---|---|
| 1 | A | S2 | Functional defect — wrong screen after re-pair |
| 2 | B | S1, S3 | Affordance defect — non-indicating toggle |
| 3 | C | S3 | Terminology clarification — design decision |

Findings A and B affect `src/` and, on approval, warrant T03 issues under
the governance pipeline. Finding C is a design question prior to any code.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Secondary Observations

These are non-blocking observations identified during the audit. They are
outside the reported symptoms; remediation is optional and deferred.

- `_handle_swipe_left` and `_handle_swipe_right` are identical; left and
  right swipes both toggle `DIGITAL`↔`RADIAL` with no distinct behaviour.
- Swipe navigation is gated on the `obd_protocol` thread being `RUNNING`.
  In `_sim_mode` that thread is not running, so layout swipes are
  unavailable during simulation.
- `_on_simulation_mode()` couples the simulation flag to layout: enabling
  forces `DIGITAL`, disabling forces `RADIAL`, discarding the prior layout.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-29 | Initial audit of UI navigation logic; Findings A–C and secondary observations. |

---

Copyright (c) 2026 William Watson. MIT License.
