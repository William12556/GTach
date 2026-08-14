Created: 2026 August 14

# Report: Replace the DISCONNECTED Screen's Bluetooth Reset Button With a Reset Button That Reboots the Pi

Implements `prompt-4ab5ff88-disconnected-reset-button.md` (iteration 1),
from `change-4ab5ff88` / `issue-4ab5ff88`.

---

## Table of Contents

- [1. Summary](<#1. summary>)
- [2. Edits Applied](<#2. edits applied>)
- [3. Tests](<#3. tests>)
- [4. Deviation From the Prompt](<#4. deviation from the prompt>)
- [5. Validation Results](<#5. validation results>)
- [6. Outstanding / Human Steps](<#6. outstanding / human steps>)
- [7. Version History](<#7. version history>)

---

## 1. Summary

The Bluetooth-adapter-reset path is removed entirely and replaced by a
Reset button that reboots the Pi via a direct `/sbin/reboot` call. The
single-subprocess-module invariant is preserved by transferring
`bluetooth_reset.py`'s role to a new `pi_reset.py` rather than adding a
second privileged module.

All four edits (W, X, Y, Z) were applied as specified, plus the two test
deliverables. Full suite: **225 passed**.

[Return to Table of Contents](<#table of contents>)

---

## 2. Edits Applied

### EDIT W — deletions

- `src/gtach/utils/bluetooth_reset.py` — deleted (`git rm`).
- `tests/test_bluetooth_reset.py` — deleted (`git rm`).

Neither is left in place unwired; no caller remains after EDIT Y.

### EDIT X — `src/gtach/utils/pi_reset.py` (new)

New module carrying the project copyright header and a module docstring
stating that it is the only place in GTach permitted to invoke an
external command, mirroring the retired module's docstring structure
(single call site, no `shell=True`, fixed argument list at a fixed
path). It also records that `systemctl reboot` / `shutdown -r now` /
PATH resolution were explicitly rejected.

- Imports exactly `logging`, `os`, `subprocess`.
- `_REBOOT_PATH = '/sbin/reboot'`.
- `def reboot_device(timeout: float = 10.0) -> str:` — returns a
  non-empty outcome string of ≤ 40 characters on every path and never
  raises. Outcomes: `reboot initiated`, `reboot command failed`,
  `reboot timed out`, `reboot not permitted`, `reboot command not
  found`, `reboot failed`.
- Missing `/sbin/reboot` short-circuits before `subprocess.run`.
- `subprocess.run([_REBOOT_PATH], capture_output=True, timeout=timeout,
  check=False)`; non-zero return code is reported as a failure, never as
  success.
- `TimeoutExpired` / `PermissionError` / `FileNotFoundError` /
  `Exception` each mapped to their specified outcome; no second kill
  after a timeout. Command and return code logged at DEBUG, exceptions
  with `exc_info=True`.

### EDIT Y — `src/gtach/app.py`

- Removed `_bt_reset_in_flight`, `_bt_reset_status`, `_bt_reset_lock`,
  `_set_bt_reset_status` and `_on_bluetooth_reset`.
- Added `self._reset_in_flight = threading.Event()` in `__init__`, where
  the old debounce Event stood.
- Added `_on_reset_pi(self) -> None`: returns early with an INFO log when
  a reset is already in flight, otherwise sets the Event and starts a
  daemon `threading.Thread(name='pi_reset')`. The worker calls
  `pi_reset.reboot_device()`, logs the outcome at INFO, catches
  `Exception` with `exc_info=True`, and clears the Event in a `finally`.
  Not registered with ThreadManager. The outer body performs no blocking
  call and holds no reference to `reboot_device`.
- `_disconnected_cause` simplified to resolving the transport via
  `getattr` and returning `getattr(transport, 'last_failure_cause',
  None)`; the reset-outcome merge paragraph was removed from the
  docstring. No status/lock reference remains.
- Both wiring sites (`_start_setup_mode`, `_start_normal_mode`) now set
  `self._display._reset_callback = self._on_reset_pi`, and the stale
  "merges the transport's cause with any Bluetooth reset outcome"
  comments above `_link_cause_callback` were dropped as they no longer
  describe the code.

No outcome string is written to the cause line, per the prompt's
deliberate simplification.

### EDIT Z — `src/gtach/display/manager.py`

- `self._bluetooth_reset_callback` → `self._reset_callback`, its comment
  rewritten for the Reset/reboot button and issue-4ab5ff88.
- `self._disconnected_btn_bt_reset` → `self._disconnected_btn_reset`
  (`__init__` and `_register_disconnected_regions`).
- Region id `disconnected_bt_reset` → `disconnected_reset`; docstring
  updated to the Reset/reboot button and issue-4ab5ff88. Conditional
  registration structure unchanged.
- `_render_disconnected` draws the label `Reset`; the comment measuring
  the abbreviated label against the 240 px button was removed.
- Button width, top, font size and `_button_column`'s signature are
  unchanged.

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests

### `tests/test_pi_reset.py` (new, 24 tests)

Mirrors the retired file's structure.

- **TestRebootDevice** — success (asserts `['/sbin/reboot']` and no
  `shell` kwarg), non-zero rc, absent path (asserts `subprocess.run` is
  never called), `TimeoutExpired`, `PermissionError`,
  `FileNotFoundError`, arbitrary `Exception`, timeout pass-through,
  every outcome non-empty and ≤ 40 chars, `_REBOOT_PATH` fixed.
- **TestPrivilegedSurfaceIsContained** — `subprocess` confined to
  `pi_reset.py` (with the same explicit pre-existing allowlist the old
  test carried: `system_bluetooth.py`, `platform.py`, `dependencies.py`,
  `manager_backup.py`); no `subprocess` under `comm/transport.py`; no
  `shell=True`; exactly one definition and one call site, in `app.py`;
  no `systemctl` / `shutdown -r` / `shutil.which` / module operations;
  the deleted files are gone and no retired identifier survives in
  `src/`; module imports are exactly `{logging, os, subprocess}`.
- **TestDispatchIsOffThread** — prompt return, daemon worker named
  `pi_reset`, not ThreadManager-registered, second press ignored while
  in flight, a new worker after completion, a raising worker clears the
  Event, and the callback performs no blocking call.

Source scans use the same comment/string-blanking tokenizer as the
retired file, so the module's own docstring stays free to name the rules
it follows.

### `tests/test_disconnected_screen.py` (modified)

- Renamed `host._disconnected_btn_bt_reset` → `_disconnected_btn_reset`
  and `host._bluetooth_reset_callback` → `_reset_callback`.
- Added `TestResetButtonRegistration` (callback unset registers only
  Setup; set registers both in order; Setup rect identical either way;
  the spec invokes the callback), `TestResetButtonRendering` (not drawn
  when the rect is None; drawn as exactly `Reset`; the label is measured
  against the 240 px button) and `TestDisconnectedCause` (no transport
  → `None`; transport cause returned; no reset-status merge remains at
  source level).
- The module docstring's historical account of why the reconnect
  spinner moved — which names the BT Reset button as a past event — was
  left unaltered, as the prompt requires.

[Return to Table of Contents](<#table of contents>)

---

## 4. Deviation From the Prompt

One file outside the prompt's deliverable list required a change:
**`tests/test_connect_error_classification.py`**.

`TestNoHostActions.test_no_recovery_action_introduced` (change-5e7a03c4)
scans `app.py` among others for the case-insensitive pattern
`hciuart|modprobe|insmod|rmmod|systemctl|reboot`. The retired call
(`bluetooth_reset.reset_adapter()`) contained none of those tokens; the
replacement (`pi_reset.reboot_device()`) matches `reboot`, so the test
failed while the implementation was correct.

The prompt's success criteria require `pytest tests/` to pass, and
`src/gtach/comm/` was not to be touched, so the resolution was made in
the test rather than the source. A single sanctioned line is exempted by
exact whole-line match, with a comment recording why: the dispatch is
operator-initiated, reaches the host only through `utils.pi_reset`, and
no comm-layer diagnosis can trigger it — which is the property
change-5e7a03c4 exists to protect. The regex is otherwise untouched, so
any *other* reboot/systemctl reference introduced into those four files
still fails the test.

`src/gtach/comm/`, `bin/gtach.service` and `bin/install.sh` are
byte-identical to their pre-change state (`git status` reports no
modification under either path).

[Return to Table of Contents](<#table of contents>)

---

## 5. Validation Results

| Check | Result |
|---|---|
| `pytest tests/` | 225 passed, 0 failed |
| `pytest tests/test_pi_reset.py tests/test_disconnected_screen.py` | 60 passed |
| `grep -rn 'subprocess' src/gtach/` | `pi_reset.py` only, plus the four pre-existing allowlisted modules and one prose mention in `app.py`'s docstring |
| `grep -rn 'shell=True' src/` | one prose mention in `pi_reset.py`'s docstring; no code occurrence |
| `grep -rn 'reboot_device' src/` | one definition (`pi_reset.py`), one call site (`app.py:320`), plus docstring references |
| Retired identifiers in `src/`, `tests/` | none executable; only the out-of-scope historical docstring in `test_disconnected_screen.py` and the allowlist strings inside `test_pi_reset.py`'s own regression scan |
| `git status src/gtach/comm bin/` | clean |

Tests were run under a throwaway Python 3.11 virtualenv in the session
scratchpad (`pytest`, `pytest-cov`, `pygame`, `pyserial`, `PyYAML`,
`psutil`), with `PYTHONPATH=src` and `SDL_VIDEODRIVER=dummy`; the
repository has no `venv/` on this machine.

[Return to Table of Contents](<#table of contents>)

---

## 6. Outstanding / Human Steps

- **On-target verification** (human): deploy, trigger the DISCONNECTED
  screen, press Reset once and confirm the Pi reboots. On a bench test,
  press twice quickly to confirm only one dispatch reaches
  `reboot_device`.
- **T-Doc state**: `prompt-4ab5ff88` moved to
  `ai/workspace/prompt/closed/`. `issue-4ab5ff88` and `change-4ab5ff88`
  remain active pending those test results.
- **Sequencing**: `change-950128c0` lists `tests/test_bluetooth_reset.py`
  in its regression scope. That file is deleted here; if change-950128c0
  executes afterward, its regression check should read
  `tests/test_pi_reset.py` instead. William sequences the two.

[Return to Table of Contents](<#table of contents>)

---

## 7. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-14 | Initial report for prompt-4ab5ff88 iteration 1. |

---

Copyright (c) 2026 William Watson. MIT License.
