Created: 2026 April 30

# GTach Splash Screen Debug Session — State Audit Report

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Session Fix Inventory](<#2.0 session fix inventory>)
[3.0 Missing and Incomplete Fixes](<#3.0 missing and incomplete fixes>)
[4.0 Pi Runtime State](<#4.0 pi runtime state>)
[5.0 Fix Priority and Remediation](<#5.0 fix priority and remediation>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document is an informal audit of the fixes developed during the
'Debugging gtach splash screen hang on Pi' chat session. It records which
fixes reached the local filesystem and GitHub, which are absent or
incomplete, and the current runtime state of GTach on the Pi as evidenced
by `gtach-debug_PI.log` (2026-04-30).

Scope: source code only. No formal governance documentation required.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Session Fix Inventory

Five distinct fixes were identified and committed across three commits.

### 2.1 Commits

| SHA (short) | Date | Description |
|---|---|---|
| `e6a86664` | 2026-04-24 | `system_bluetooth.py` — rewrite `discover_devices()` using `hcitool scan` |
| `93129555` | 2026-04-25 | Restore all session fixes lost in git stash conflict |
| `1ce11b41` | 2026-04-25 | Push missing session fixes: `manager.py` splash-branch logic; `touch.py` optional interface param |

### 2.2 Fix Status

| Fix | File | Status |
|---|---|---|
| `discover_devices()` rewritten to `hcitool scan` with `bluetoothctl` fallback | `comm/system_bluetooth.py` | ✅ Present |
| `BluetoothSetupInterface.__init__()` — Darwin skip of `BluetoothPairing`, immediate `_pairing_ready.set()` | `display/setup_components/bluetooth/interface.py` | ✅ Present |
| `_start_macos_serial_discovery()` — new method, `/dev/cu.*` enumeration via `serial.tools.list_ports` | `display/setup_components/bluetooth/interface.py` | ✅ Present |
| `TouchHandler.__init__()` — optional `touch_interface` param; skip self-init when supplied | `display/touch.py` | ✅ Present |
| `_process_touch()` — setup-mode bypass: route directly to `_handle_short_press()`, skip gesture handler | `display/touch.py` | ✅ Present |
| `create_touch_interface()` — singleton pattern added | `display/touch_interface.py` | ✅ Present |
| `_draw_splash_mode()` — three-branch logic: setup path / acknowledged path / ACKNOWLEDGEMENT fallback | `display/manager.py` | ⚠️ Partial — code present but dependencies missing (see §3.0) |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Missing and Incomplete Fixes

Three dependent changes required by the `_draw_splash_mode()` three-branch
logic were **not committed**. All three cause `AttributeError` at runtime.

### 3.1 Defect 1 — `DisplayMode.ACKNOWLEDGEMENT` missing from enum

**File:** `src/gtach/display/models.py`  
**Severity:** Critical  

`_draw_splash_mode()` line 437:
```python
self.config.mode = DisplayMode.ACKNOWLEDGEMENT
```

`DisplayMode` in `models.py` defines only `SPLASH`, `DIGITAL`, `GAUGE`,
`SETTINGS`. `ACKNOWLEDGEMENT` is absent. This raises
`AttributeError: ACKNOWLEDGEMENT is not a valid DisplayMode`.

### 3.2 Defect 2 — `_ack_state_manager` never initialized

**File:** `src/gtach/display/manager.py`  
**Severity:** Critical  

`_draw_splash_mode()` line 434:
```python
elif self._ack_state_manager.is_acknowledged(self.config.rpm_bands, self.config.engine_profile):
```

`self._ack_state_manager` is referenced but never assigned in `__init__()`,
`_initialize_components()`, or `_initialize_legacy_components()`. The class
`AcknowledgementStateManager` exists in `src/gtach/utils/ack_state.py` but
is never imported or instantiated in `manager.py`.

This raises `AttributeError: 'DisplayManager' object has no attribute '_ack_state_manager'`.

### 3.3 Defect 3 — `rpm_bands` and `engine_profile` missing from `DisplayConfig`

**File:** `src/gtach/display/models.py`  
**Severity:** Critical  

Same line as Defect 2 passes `self.config.rpm_bands` and
`self.config.engine_profile` to `is_acknowledged()`. Neither attribute is
defined in the `DisplayConfig` dataclass.

### 3.4 Combined runtime effect of Defects 1–3

On every frame where `self._splash_screen.is_complete()` returns `True`:

1. `self._in_setup_mode` branch taken if in setup mode → correct.
2. Otherwise `elif self._ack_state_manager.is_acknowledged(...)` raises
   `AttributeError` (Defect 2), caught by the outer `except Exception` block.
3. The exception handler sets `self.config.mode = self._post_splash_mode`.

Net observable effect: the app transitions past the splash screen via the
exception path. The `ACKNOWLEDGEMENT` screen is never shown. An error is
logged on every splash-complete frame. Because the exception sets mode to
`_post_splash_mode` (or setup mode), the app continues to run.

### 3.5 Defect 4 — ThreadManager heartbeat key mismatch

**File:** `src/gtach/display/setup.py` / `src/gtach/core/thread_manager.py`  
**Severity:** Low  

`SetupDisplayManager._setup_loop()` calls:
```python
self.thread_manager.update_heartbeat('setup')
```

The thread is started as `threading.Thread(..., name='SetupManager')` and
registered with ThreadManager under key `'setup'` (or not registered at
all). The Pi log confirms the warning fires at approximately 15 Hz:
```
ThreadManager WARNING  Heartbeat for unknown thread: setup
```

This is a non-fatal log spam issue. The watchdog does not trigger because
the key is unknown (not monitored), but it indicates the 'setup' thread is
not registered with ThreadManager at startup.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Pi Runtime State

Source: `gtach-debug_PI.log`, 2026-04-30 13:02:37–13:02:56 (local time).

### 4.1 Startup sequence — normal

```
13:02:37  ConfigManager initialized
13:02:37  ThreadManager initialized (3 workers)
13:02:37  app INFO  Starting GTach application
13:02:37  app INFO  Setup required - entering setup mode
13:02:37  DisplayRenderingEngine  Using memory-mapped framebuffer (/dev/fb0, 480×480)
13:02:37  HyperPixelTouchInterface  Real HyperPixel touch device initialized ✅
13:02:37  SplashScreen initialized (4.0s)
13:02:37  NavigationGestureHandler initialized
13:02:37  Display loop started
13:02:37  Bluetooth pairing init started (async op_0)
13:02:37  SetupDisplayManager initialized
```

HyperPixel real hardware initialised successfully. Splash activated.

### 4.2 Post-splash state — stuck on WELCOME screen

From approximately 13:02:41 onward (after 4s splash), the log floods with:
```
SetupDisplayManager DEBUG  Using cached render for WELCOME
ThreadManager WARNING      Heartbeat for unknown thread: setup
```

at approximately 60 Hz. The log does not contain any touch event records,
setup screen transitions, or Bluetooth discovery activity after startup.

**Interpretation:** GTach reached setup mode past splash (transition
occurred via exception path, §3.4). The WELCOME screen is rendered and
visible. No touch events are being processed to advance to DISCOVERY.

### 4.3 Possible cause of WELCOME screen hang

Two candidates:

1. **Touch events not reaching `SetupDisplayManager`**: The touch callback
   chain (`HyperPixelTouchInterface` → `TouchHandler._handle_touch_event()`
   → `_process_touch()` → `_handle_setup_touch()` → `DisplayManager.handle_touch_event()`
   → `SetupDisplayManager.handle_touch_event()`) must be intact. Any break
   in this chain would result in the WELCOME screen being unresponsive to
   taps, exactly as observed.

2. **`DisplayManager._in_setup_mode` flag not set at transition time**: In
   `app.py` `_start_setup_mode()`, `set_setup_mode()` is called before splash
   completes (correct). However, if the exception path in `_draw_splash_mode()`
   clears the mode to `_post_splash_mode` (DIGITAL) instead of entering setup,
   `_in_setup_mode` may be True while `config.mode` is inconsistent. This
   warrants inspection.

The log does not contain sufficient touch-event-level debug output to
confirm which of these is the active failure mode without live testing.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Fix Priority and Remediation

### 5.1 Priority order

| Priority | Defect | File | Required Change |
|---|---|---|---|
| 1 | §3.2 | `display/manager.py` | Import `AcknowledgementStateManager` from `utils.ack_state`; initialize `self._ack_state_manager` in `__init__()` |
| 1 | §3.1 | `display/models.py` | Add `ACKNOWLEDGEMENT = auto()` to `DisplayMode` enum |
| 1 | §3.3 | `display/models.py` | Add `rpm_bands` and `engine_profile` fields to `DisplayConfig` (or remove the arguments from the `is_acknowledged()` call if not required) |
| 2 | §3.5 | `display/setup.py` + `core` | Register 'setup' thread with ThreadManager, or align heartbeat key with registered name |
| 3 | §4.3 | Investigation | Confirm touch routing chain integrity for WELCOME screen tap; add touch debug logging if needed |

### 5.2 Scope note

Defects 1–3 are incomplete parts of the `_draw_splash_mode()` fix committed
in `1ce11b41`. They meet the Trivial Change Exemption criteria (§P03
§1.4.12): each is confined to a single location, net delta ≤ 5 lines, no
interface change, unambiguous, and human-approved. No T03/T02/T04 documents
are required. Git commit history is the audit record.

Defect 4 (heartbeat key) also qualifies under the exemption.

Defect §4.3 (WELCOME touch hang) requires investigation before a fix can
be scoped. It may resolve automatically once Defects 1–3 are corrected if
the exception path in `_draw_splash_mode()` was masking a mode inconsistency.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-04-30 | Initial audit — informal session review |

---

Copyright (c) 2026 William Watson. MIT License.
