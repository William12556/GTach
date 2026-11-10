# GTach Static Source Audit — src/gtach (audit-71ab3751)

Created: 2026 November 10

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 Scope and Method](#20-scope-and-method)
- [3.0 Findings](#30-findings)
- [4.0 Observations](#40-observations)
- [5.0 Scheduled Audit Dispositions](#50-scheduled-audit-dispositions)
- [6.0 Verification of Suspected Findings](#60-verification-of-suspected-findings)
- [7.0 Recommendations](#70-recommendations)
- [Version History](#version-history)

---

## 1.0 Summary

**Mode:** strategic (P02), static review only. No device, display, Bluetooth adapter or serial hardware was used.

**Audited commit:** `94ce959b953718a1899fc58b2e21df2ad1c866e9` (branch `main`). The working tree under `src/` was clean at the time of reading.

**Result:** 43 findings. No critical or high finding was identified. Version 1.1 integrates the valid findings of the four open scheduled daily audits ([5.0](#50-scheduled-audit-dispositions)); 13 findings were added (1 medium, 12 low), 3 existing findings were extended and one (B05) was withdrawn.

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 0 |
| Medium | 4 |
| Low | 39 |
| **Total** | **43** |

**Medium findings:**

1. **A01 — A connect that completes after `disconnect()` leaves an open RFCOMM link (consequence suspected).** `OBDTransport.connect` stores the handle without testing `_shutdown`. If the operator taps Setup on the DISCONNECTED screen while a connect is in flight and that connect then succeeds, the socket is never closed. Later connects to the same adapter from the setup probe or pairing are expected to fail with EBUSY until the process restarts.
2. **D01 — Discovery outcomes are not presented.** A scan that finds nothing sets a message that the DISCOVERY screen does not draw, and the setup loop starts the next scan at once. A failed scan leaves the spinner running with no message. The "No devices found" state of the DEVICE_LIST screen, which the designs specify, is not reachable.
3. **A02 — Serial transport does not recover from a removed device (suspected).** A raw `OSError` from `in_waiting` is outside `SerialTransport._IO_ERRORS`, so the link is never dropped and every poll logs a traceback.
4. **C08 — The stored-device probe acts after the operator has left the screen (from audit-005f1cf4 §4.0).** If New Setup is tapped while the probe runs and the probe then succeeds, setup completes although the stored device was deleted.

**Classification:** each finding is marked *confirmed* (follows from the source alone) or *suspected* (the consequence depends on runtime or library behaviour; see [6.0](#60-verification-of-suspected-findings)).

**Reviewed without finding:** `core/thread.py`, `core/watchdog.py`, `display/rendering/engine.py`, `comm/rfcomm.py`, `comm/tcp_transport.py`, `comm/models.py`, `comm/device_store.py` (locking), `utils/ack_state.py`, `utils/home.py`, `utils/waits.py`, `utils/updater.py`, `utils/stack_dump.py`, `utils/platform.py`, `display/models.py`, `display/typography.py`, `display/performance/monitor.py`, `display/setup_components/layout/circular_positioning.py`, `display/setup_components/rendering/device_surfaces.py`, `display/graphics/splash_graphics.py`.

**Not re-reported:** items already in `ai/task.md` (the six mypy candidate defects including `TouchAction.DRAG`, the Reset outcome log line, `--validate-config` logging side effects, fixed log paths, render caching `821919ce`).

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Scope and Method

### 2.1 Scope

- Every file under `src/gtach/`: 60 Python files (19,998 lines), `assets/engine_profiles.yaml` and `utils/default-config.txt`.
- Excluded: `tests/`, `bin/`, `ai/`, `docs/`, the font binary.
- Version 1.1 exception: the `bin/` and `tests/` locations cited by the open scheduled audits were read to validate those findings (`bin/gtach-preflight.sh`, `bin/gtach-verify-36b6ea95.sh`, `tests/test_lifecycle_sim.py`, `tests/test_callbacks_outside_locks.py`, `tests/test_sim_transport.py`). These files were not otherwise audited.

### 2.2 Method

- Each file was read in full. Cross-module paths were then traced: thread lifecycle, shutdown, setup entry and exit, reconnect, touch dispatch.
- Criteria: correctness, concurrency, error handling and recovery, resource management, dead code, configuration consistency. Efficiency observations are recorded separately in [4.0](#40-observations).
- Line numbers refer to the audited commit.

### 2.3 Tooling

| Tool | Result |
|---|---|
| `python -m compileall` (Python 3.13) | All 60 files compile. |
| `mypy 2.3.1 --ignore-missing-imports --check-untyped-defs` | No issues in 60 source files. Target version 3.9 cannot be selected in this mypy release. |
| AST check | No bare `except:` and no mutable default arguments. |
| flake8, bandit, pytest | Not run. The analysis environment had no package index access. |

### 2.4 Limitations

- pygame, pyserial, PyBluez and hyperpixel2r were not installed. Statements about their behaviour rest on their documentation and are marked as inference where a finding depends on them.
- The device runs Python 3.9; version-specific behaviour was not exercised.
- No finding was verified on the Pi. Per the project's verification principle, on-device measurement remains authoritative.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Findings

Finding IDs: A = comm, B = core and top level, C = display top level, D = display subfolders, E = utils, F = tests, G = bin, X = cross-cutting. Findings taken from a scheduled audit name their source.

```yaml
# T08 Audit Template v1.0 - YAML Format
audit_info:
  id: "audit-71ab3751"
  title: "GTach static source audit of src/gtach"
  date: "2026-11-10"
  mode: "strategic"
  status: "complete"
  auditor: "planner"

scope:
  target: "src/gtach/ @ 94ce959b953718a1899fc58b2e21df2ad1c866e9"
  criteria:
    - "correctness"
    - "concurrency"
    - "error_handling_and_recovery"
    - "resource_management"
    - "dead_code"
    - "configuration_consistency"
  exclusions:
    - "tests/ (except locations cited by the open scheduled audits)"
    - "bin/ (except locations cited by the open scheduled audits)"
    - "ai/"
    - "docs/"
    - "src/gtach/assets/fonts/"

findings:
  critical: []
  high: []
  medium:
    - location: "comm/transport.py:380-403, 461-468; app.py:466-486"
      description: >-
        [A01] (confirmed race; consequence suspected) connect() assigns
        self._handle and CONNECTED after _open() returns without testing
        _shutdown. _re_enter_setup stops the transport thread with a 2.0 s
        join, while an RFCOMM _open() can block for up to 10 s. If
        disconnect() runs during that _open() and the connect then succeeds,
        the handle is stored after disconnect() has run (disconnect() found
        no handle to close); reconnect_indefinitely then returns on _shutdown
        and nothing closes the socket. app._transport keeps the old transport referenced until
        _start_obd replaces it, which is after setup completes. Inference:
        an ELM327 accepts one RFCOMM connection, so the setup probe
        (start_device_probe) and pair_device then fail with EBUSY
        ('Device not available', 'Connection failed') until the process
        restarts or the operator uses Cancel on the WELCOME screen. The
        trigger is tapping Setup at the moment the adapter becomes
        reachable.
    - location: "display/setup_components/bluetooth/interface.py:322-357; display/setup.py:261-304, 469-515, 904-924"
      description: >-
        [D01] (confirmed) Discovery outcomes are not presented. (1) Zero
        devices: on_discovery_complete sets error_message 'No devices
        found...', status IDLE and an empty list. _render_discovery_screen
        does not draw error_message, and _setup_loop sees DISCOVERY + IDLE +
        no devices + no active operation and starts the next scan, so
        scanning repeats without end and without feedback.
        handle_touch_event clears error_message before it dispatches the
        Cancel tap. (2) Failure: status FAILED never satisfies the loop
        condition, so the spinner runs with no message and no retry. (3) The
        DEVICE_LIST 'No devices found' branch (setup.py:584-592) is entered
        only with a non-empty list, so it is unreachable. This deviates from
        design-a3b4c5d6 ('With zero devices, No devices found is shown') and
        design-2c6b8e4d ('Display No devices found message, offer retry').
        An adapter fault that makes hcitool return nothing (A07) looks the
        same as an empty scan. Related: ai/task.md discovery-fallback item.
    - location: "comm/serial_transport.py:27, 93-106; comm/transport.py:598-606"
      description: >-
        [A02] (suspected) SerialTransport._IO_ERRORS is
        (serial.SerialException,). _discard_input reads handle.in_waiting
        before every write and catches only TypeError, ValueError and
        AttributeError. Inference: pyserial's POSIX in_waiting is an
        unwrapped ioctl, which raises OSError (EIO) once the device is
        removed. That exception reaches send_command's generic handler,
        which returns None without changing state and without counting a
        timeout. The link is never dropped, no reconnect starts, and each
        poll (20 Hz) writes a traceback to error.log.
    - location: "display/setup.py:973-995, 997-1006; display/setup_components/state/coordinator.py complete_setup"
      description: >-
        [C08] (confirmed, timing-dependent; from audit-005f1cf4 section 4.0,
        still present) _on_probe_result does not check that the screen is
        still CURRENT_DEVICE. The probe can take up to 10 s, and 'new_setup'
        stays available meanwhile. If the operator taps New Setup and the
        probe then succeeds, complete_setup() sets COMPLETE although the
        stored device has been removed; _start_obd then raises 'No paired
        device found' and B03 applies. If the probe fails, the callback
        forces WELCOME with 'Device not available' whatever screen is shown.
  low:
    - location: "comm/transport.py:404-431"
      description: >-
        [A03] (confirmed; carried from audit-fccd5931 F1, still present)
        Refused connects increment _consecutive_connect_failures. After six
        refusals the first non-refused failure reports 'bluetooth wedged -
        reset required'.
    - location: "comm/transport.py:598-603"
      description: >-
        [A04] (confirmed) The I/O-error handler in send_command sets
        DISCONNECTED and discards the handle but records no
        _last_failure_cause. A mid-session ECONNRESET or ENOTCONN shows the
        DISCONNECTED screen without a cause line until the next connect
        fails.
    - location: "comm/obd.py:186-197"
      description: >-
        [A05] (confirmed) A missing vehicle reply to 0100 (ignition off with
        a powered OBD port: 'UNABLE TO CONNECT', 'NO DATA') is raised as an
        Exception and logged at ERROR with a traceback on every retry cycle
        (a few seconds each), for as long as the condition lasts. Each
        cycle also repeats ATZ. An expected operating state fills error.log.
    - location: "comm/pairing.py:156-185; comm/system_bluetooth.py:152-157"
      description: >-
        [A06] (mismatch confirmed, effect suspected; also audit-005f1cf4
        section 6.0, which adds that total discovery time is therefore not
        bounded by the requested timeout) Each discovery chunk waits 9 s (chunk_duration + 5)
        for 'hcitool scan --length 4'. Inference: the length unit is 1.28 s,
        so the inquiry takes about 5.1 s and remote-name resolution follows.
        When the wait expires the chunk's results are discarded although
        hcitool is still running (its own limit is 13 s), and the next
        chunk starts a second concurrent scan on the two-worker executor.
    - location: "comm/system_bluetooth.py:152-178, 251-255"
      description: >-
        [A07] (confirmed) discover_devices ignores hcitool's return code and
        stderr. A scan that fails (adapter down or busy) returns an empty
        list with no log record. A new SystemBluetoothManager is built per
        chunk, which runs 'bluetoothctl --version' each time and raises
        BluetoothError if bluetoothctl is absent even though hcitool is the
        tool used.
    - location: "comm/device_store.py:303-329; display/setup_components/bluetooth/interface.py:475; display/manager.py:2139-2155"
      description: >-
        [A09] (confirmed; includes audit-005f1cf4 section 9.0)
        _save_device_locked changes the in-memory store before saving, so
        after a failed write memory and disk differ until restart.
        Persistence results are not used.
        _remove_device_locked returns True without checking _save_config().
        on_pairing_complete ignores save_device()'s result, contrary to the
        note in _save_device_locked's docstring, so 'Setup Complete!' is
        shown when the device did not reach disk. _on_clear_settings ignores
        remove_device()'s result and removes only the primary device.
    - location: "comm/sim_bluetooth.py:214-224"
      description: >-
        [A10] (confirmed) Simulated pairing saves its fake device
        (AA:BB:CC:DD:EE:0x) as the primary device in the shared device
        store. Running 'gtach --transport simbt' on the Pi replaces the real
        paired adapter in devices.yaml; the next normal start retries the
        fake address until setup is repeated.
    - location: "comm/sim_transport.py:47, 142, 157"
      description: >-
        [A11] (confirmed) SimTransport.connect() clears _shutdown, so a
        disconnect() that lands between the supervising loop's test and
        connect() is undone and the loop does not exit. Two comments are
        stale ('~12s period'; 'begins near minimum'): the period is 60 s and
        the sweep starts at the midpoint (carried from audit-fccd5931).
    - location: "app.py:466-488"
      description: >-
        [B01] (confirmed) _re_enter_setup calls _start_setup_mode() without
        pairing_factory. In a simbt session, re-entering setup (Setup button
        or Clear settings) uses the real BluetoothPairing and a real RFCOMM
        verification against the fake address.
    - location: "app.py:490-501; display/setup_components/bluetooth/interface.py:557-573; display/setup.py:967-971"
      description: >-
        [B02] (confirmed) _start_obd always passes
        adapter_pre_initialised=True. The stored-device probe only connects
        and disconnects, and the Cancel path performs no probe, so ATZ is
        skipped in sessions where the adapter was never reset. The comment
        in obd.py:157 ('already reset by setup probe') does not hold for
        these two paths. An adapter left with headers on would yield no RPM.
    - location: "app.py:446-464"
      description: >-
        [B03] (confirmed) _obd_started is set before _start_obd runs. If
        _start_obd raises (TransportError, or RuntimeError from
        register_thread during shutdown), the flag stays set, the setup
        loop's retry is ignored as a duplicate, and no transport or OBD
        thread exists. Recovery requires the Setup button, which clears the
        flag.
    - location: "app.py:589-642; main.py:385-387"
      description: >-
        [B04] (confirmed) (1) main() returns 0 after a startup failure, a
        watchdog-requested exit or a runtime error, so systemd records
        'Succeeded'. (2) shutdown() runs all steps in one try block: an
        exception in an early step (for example stop_setup) skips
        display.stop, transport.disconnect, obd.stop and
        thread_manager.shutdown, leaving the 20 s backstop to end the
        process. (3) With a scan in progress the sequential join budgets
        (async workers 2 x 5 s, display 5 s, OBD 5 s, thread manager) can
        exceed the backstop.
    - location: "app.py:479-481; core/thread.py:188-207; comm/obd.py:89-96"
      description: >-
        [B06] (confirmed; from audit-005f1cf4 section 8.0 and audit-8264c76d
        observation) stop_thread calls stop_func before its own bounded
        join. For obd_protocol the stop function is OBDProtocol.stop, which
        joins for up to 5 s, so the 2.0 s passed by _re_enter_setup is not
        the bound: the callback can block for about 9 s (transport 2 s, OBD
        5 s + 2 s). The comment at app.py:477-478 does not hold. The total
        stays below the 15 s watchdog warning.
    - location: "core/watchdog.py:283-296"
      description: >-
        [B07] (confirmed; from audit-005f1cf4 observation)
        _handle_critical_timeout logs 'initiating emergency procedures' at
        ERROR on every 5 s check for a stalled non-critical thread, and
        takes no action for it.
    - location: "display/setup.py:794-807, 947-949; display/setup_components/state/coordinator.py:264-286"
      description: >-
        [C01] (confirmed) The PAIRING screen's Continue button maps to
        SetupAction.NEXT, and _handle_next_navigation has no PAIRING branch.
        The tap logs a warning and does nothing. The button is shown while
        OBD verification runs (which can take tens of seconds); completion
        is automatic.
    - location: "display/setup.py:482-491, 734-742"
      description: >-
        [C02] (confirmed) The discovery and pairing spinners pass an RGBA
        colour to pygame.draw.circle on a surface without per-pixel alpha.
        The alpha is ignored, so all eight dots have the same colour and the
        intended fade is absent.
    - location: "display/manager.py:285-299"
      description: >-
        [C03] (confirmed) _toggle_palette's docstring states that a failed
        save leaves the palette unchanged. The palette is switched first and
        never reverted; _save_config swallows the failure.
    - location: "display/manager.py:209-218, 473-511"
      description: >-
        [C04] (confirmed) _setup_manager, _in_setup_mode,
        _setup_entry_callback and _splash_screen are assigned after the
        touch initialisation inside one try block whose inner handler
        catches only ImportError. A RuntimeError from
        create_touch_interface() leaves them and touch_handler undefined;
        the display loop then raises AttributeError every frame.
        performance_monitor has the same pattern.
    - location: "display/manager.py:2625-2630, 814-822, 2636-2651"
      description: >-
        [C05] (confirmed) exit_setup_mode (setup thread) clears
        _setup_manager while the display thread and the touch thread read
        it twice without a local copy. A frame or touch in that window
        raises AttributeError, logs an error and draws the 'SETUP MODE'
        fallback for one frame.
    - location: "display/manager.py:1090-1105, 1297-1298; display/models.py RPMBands; assets/engine_profiles.yaml:18"
      description: >-
        [C09] (confirmed; from audit-005f1cf4 section 15.0) _gauge_max_rpm
        caps full scale at 9000 while its docstring states the configured
        redline is always on the dial, and RPMBands accepts a redline up to
        15000. A redline above 9000 is off the dial and its boundary mark is
        skipped. The packaged profiles (6500 to 7500) are unaffected.
    - location: "display/touch.py:160-167"
      description: >-
        [C06] (confirmed) A long press is decided by duration alone. A swipe
        that takes touch_long_press (1.0 s) or longer toggles the palette
        instead of navigating, and a hold on a button toggles the palette
        instead of pressing it.
    - location: "display/touch.py:140-147"
      description: >-
        [C07] (suspected) _touch_start is recorded only when it is None and
        has no expiry. If a touch-up event is lost, the next gesture is
        measured from the stale start time and position and is read as a
        long press or a swipe.
    - location: "display/async_operations.py:292-296; display/setup_components/bluetooth/interface.py:267, 393"
      description: >-
        [D02] (confirmed) Progress reporting is injected only when the task
        has a local named 'progress_callback'. discovery_task and
        pairing_task name the parameter 'progress_callback_inner'
        ('progress_callback' is a closure variable there), so their
        progress messages are never delivered and the DISCOVERY screen shows
        only the generic text.
    - location: "display/async_operations.py:224-250"
      description: >-
        [D03] (confirmed) cleanup_completed_operations has no caller.
        operations and progress_callbacks keep every operation, its result
        and its closures (including each SetupDisplayManager) for the life
        of the process.
    - location: "display/setup_components/state/coordinator.py:191-193, 227-229"
      description: >-
        [D04] (confirmed, rare) START_DISCOVERY and CANCEL transition first
        and reset the device list second; RETRY resets first. In the gap the
        setup loop can see DISCOVERY with stale devices and move to
        DEVICE_LIST, which the reset then empties.
    - location: "utils/config.py:207-219; display/models.py:208-209; utils/default-config.txt"
      description: >-
        [E01] (confirmed) rpm_warning and rpm_danger are validated, loaded
        and saved but read by no rendering or logic path. The eleven
        DisplayConfig.gesture_* fields have no reader, and the comment at
        comm/pairing.py:132-135 cites discover_all_devices, which
        BluetoothPairing does not define (both from audit-005f1cf4
        observations).
        utils/default-config.txt describes the retired nested schema
        (mode DIGITAL, fps_limit 60, bluetooth section) and is referenced
        by no source file.
    - location: "utils/config.py:373-386"
      description: >-
        [E05] (confirmed in isolation by audit-005f1cf4 section 10.0; impact
        suspected) ConfigStore.save holds the lock only while copying the
        unknown keys. Concurrent saves in one process share the temp path
        '.config.yaml.<pid>.tmp' and can fail with FileNotFoundError. The
        palette toggle is the only caller, so overlap is unlikely.
    - location: "utils/config.py:316-326"
      description: >-
        [E06] (confirmed; from audit-005f1cf4 section 11.0) load() coerces
        with kind(value), so it accepts values validate() rejects: a null
        palette becomes 'None', 'touch_long_press: true' becomes 1.0 and
        'fps_limit: 30.9' becomes 30, the last two without a warning. The
        display falls back for an unknown palette or mode, so the effect is
        a silent difference between --validate-config and runtime.
    - location: "utils/pi_reset.py:11-14"
      description: >-
        [E02] (confirmed) The module docstring states that subprocess is
        imported there and nowhere else, in particular nowhere under
        gtach.comm. comm/system_bluetooth.py:17 and utils/platform.py:19
        import and use it.
    - location: "utils/dependencies.py:330-338"
      description: >-
        [E03] (confirmed) In debug mode the ImportError handler calls
        importlib.util.find_spec(import_name). For 'RPi.GPIO' with the
        parent package absent this raises ModuleNotFoundError inside the
        handler, so 'gtach --validate-dependencies --debug' ends with a
        traceback on a Pi without RPi.GPIO.
    - location: "utils/terminal.py:30"
      description: >-
        [E04] (confirmed) TerminalRestorer calls sys.stdin.fileno() without
        a guard. A closed or absent stdin raises in the constructor and
        prevents application start.
    - location: "comm/transport.py:535, 566-580; comm/obd.py:231"
      description: >-
        [A12] (suspected; from audit-005f1cf4 section 12.0) _discard_input
        removes only bytes buffered before the write. A late reply that
        arrives after the discard is returned as the reply to the new
        command. The PID check rejects a late reply for another PID; a late
        010C reply is accepted once as a current RPM sample.
    - location: "tests/test_lifecycle_sim.py:257"
      description: >-
        [F01] (confirmed; residual of audit-005f1cf4 section 13.0)
        'assert proc.wait(timeout=10.0) is not None' is true for any exit
        status, so the SIGTERM test does not check how the process ended.
        The rest of section 13.0 is resolved: drop_link is now observed and
        the xfail markers are gone.
    - location: "tests/test_callbacks_outside_locks.py:223-240"
      description: >-
        [F02] (confirmed; from audit-8264c76d F2) The callback in
        test_callback_may_register_regions re-enters the coordinator on the
        dispatching thread. The coordinator lock is an RLock
        (touch_coordinator.py:36), so the test also passes if callbacks run
        under the lock. It gives no regression protection.
    - location: "tests/test_sim_transport.py:70-93"
      description: >-
        [F03] (confirmed; from audit-fccd5931 F2) 
        test_rpm_sweep_ignores_wall_clock_steps asserts '41 0C 39 08' at
        t = 30 s. The sweep gives 3650 RPM at both t = 0 and t = 30 s, so
        the assertion also passes if elapsed time is ignored.
    - location: "bin/gtach-verify-36b6ea95.sh:4, 199, 210, 273-277; main.py:357"
      description: >-
        [G01] (confirmed; from audit-005f1cf4 section 5.0, rated medium
        there) The script's header states it is read-only, but each
        'gtach --validate-config' it runs truncates /opt/gtach/start.log
        and can rotate debug.log, because main() sets up logging first.
        Check C7c then reads start.log, which holds only the validation
        run. Rated low here: the script verifies a closed audit, and the
        main.py cause is already in ai/task.md.
    - location: "bin/gtach-preflight.sh:21-31, 47-52, 66-74"
      description: >-
        [G02] (first case confirmed, second suspected; from audit-005f1cf4
        section 7.0 and audit-8264c76d F3) install_and_check installs before
        'pip check'. (1) If the check fails and no previous.whl exists, the
        rejected wheel stays installed and the probation marker is removed.
        (2) With an unrelated conflict already in the venv, a rollback
        installs the previous wheel but leaves installed.whl naming the
        rejected one, which the next update copies to previous.whl.
    - location: "bin/gtach-verify-36b6ea95.sh:41"
      description: >-
        [G03] (confirmed; from audit-005f1cf4 section 14.0 and
        audit-8264c76d F1) With '--since' as the last argument, 'shift 2'
        fails without shifting and the argument loop does not terminate.
    - location: "display/async_operations.py:192-207; display/setup.py:963-965; comm/pairing.py:360-437, 498-501"
      description: >-
        [X01] (confirmed) Cancellation has no effect on running work.
        cancel_operation cancels only PENDING operations; the Cancel button
        on the DISCOVERY screen calls neither cancel_operations nor
        cancel_discovery; pair_device never reads _cancel_pairing. An
        abandoned scan runs to completion and its callback still writes the
        device list and error message into the state, which is how the
        'No devices found' text can appear on the WELCOME screen up to
        about 30 s after Cancel.

metrics:
  items_audited: 67
  findings_total: 43
  findings_by_severity:
    critical: 0
    high: 0
    medium: 4
    low: 39

recommendations:
  - "See section 7.0."

traceability:
  design_refs:
    - "design-a3b4c5d6-component_display_setup_manager"
    - "design-2c6b8e4d-domain_display"
  issue_refs: []
  related_audits:
    - audit_ref: "audit-36b6ea95"
      relationship: "follow_up"
    - audit_ref: "audit-fccd5931"
      relationship: "supersedes"
    - audit_ref: "audit-005f1cf4"
      relationship: "supersedes"
    - audit_ref: "audit-8264c76d"
      relationship: "supersedes"
    - audit_ref: "audit-008e2929"
      relationship: "supersedes"

notes: "Static review only. Suspected findings require on-device verification (section 6.0)."

version_history:
  - version: "1.0"
    date: "2026-11-10"
    changes:
      - "Initial audit"
  - version: "1.1"
    date: "2026-11-10"
    changes:
      - "Integrated valid findings of the four open scheduled daily audits (13 added, 3 extended)"
      - "Withdrew B05"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t08_audit"
```

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Observations

These are efficiency opportunities and notes. They are not counted as findings.

### 4.1 Efficiency

| ID | Location | Observation | Trade-off |
|---|---|---|---|
| O1 | `main.py:81`; `display/manager.py:1389, 2310, 2434`; `comm/transport.py` TX/RX debug | The root logger is fixed at DEBUG and suppression is done at the handlers. Every `logger.debug` call therefore creates a `LogRecord` (and, for f-strings, the message) with debug off: per frame on the display thread and per command at 20 to 50 Hz on the OBD thread. The `isEnabledFor(DEBUG)` guards are always true. Setting the root level to WARNING after startup, and switching it in `toggle_debug_logging`, removes that work. | `start.log` needs DEBUG until startup completes; the toggle must restore the level. |
| O2 | `display/manager.py:977, 1438, 2557` | `_link_lost()` runs three times per frame, each taking the transport lock through the callback. One evaluation per frame is sufficient. | The method also updates the latch; a single call site keeps that behaviour. |
| O3 | `display/manager.py:1107-1393` | The radial face (track arcs, ticks, numerals, boundary marks, label) is recomputed and re-rendered every frame. | Already recorded as deferred item `821919ce`; no new action proposed. |
| O4 | `display/setup.py:337` | `render()` copies the 480x480 target, draws into the copy and blits it back on every frame of the uncached screens. Drawing to the target directly avoids one copy and one blit. | Cached screens still need their own surface. |
| O5 | `display/splash.py:477, 582` | The splash calls `validate_text_fits_circular_display` per frame. It renders the text again for a log-only check, and checks sizes 36 and 20 while the text is drawn at 72 and 40. | Splash lasts 4 s; the gain is small. |

### 4.2 Notes

- A device whose name matches no entry in `_classify_device` cannot be paired: the filter toggle (`toggle_device_filter`) and manual entry have no caller. This is the subject of the open discovery-fallback item in `ai/task.md`.
- `OBDResponse.timestamp` uses `time.time()` (`comm/obd.py:235`). No consumer reads it.

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Scheduled Audit Dispositions

Each finding and observation of the four open scheduled daily audits was re-checked against the audited commit.

### 5.1 audit-005f1cf4 (2026-10-08)

| Item | Disposition | ID here |
|---|---|---|
| §4.0 Continue probe acts after the user leaves the screen | Valid, still present | C08 (medium) |
| §5.0 Verification script overwrites service logs | Valid; rated low here | G01 |
| §6.0 Discovery chunk timeout | Valid; same as A06 | A06 (merged) |
| §7.0 Preflight restore path | Valid, script unchanged | G02 |
| §8.0 Stop timeout not honoured | Valid | B06 |
| §9.0 DeviceStore memory and disk diverge | Valid | A09 (merged) |
| §10.0 ConfigStore shared temp path | Valid; impact suspected | E05 |
| §11.0 ConfigStore load accepts values validate rejects | Valid | E06 |
| §12.0 Late OBD reply accepted once | Plausible; not verifiable statically | A12 (suspected) |
| §13.0 Link-loss tests | Resolved by change-50bf25ad, except the unchecked exit status | F01 |
| §14.0 Verification script loops on `--since` | Valid | G03 |
| §15.0 Gauge range cap | Valid | C09 |
| Observation: watchdog logs every cycle | Valid | B07 |
| Observation: `gesture_*` fields, `pairing.py` comment | Valid | E01 (merged) |
| Observation: unused coordinator paths call back under the lock | Valid but in dead code already tracked in `ai/task.md` | Not counted |
| Observation: `threading.enumerate()` in the SIGUSR1 handler | Not validated; depends on the interpreter version on the device | Not integrated |

### 5.2 audit-8264c76d (2026-10-08)

| Item | Disposition | ID here |
|---|---|---|
| F1 Verify script hangs on bare `--since` | Valid; duplicate of 005f1cf4 §14.0 | G03 |
| F2 Region-registration test cannot fail | Valid | F02 |
| F3 Preflight rollback state | Plausible; requires an inconsistent venv | G02 (merged) |
| Observation: `_probe_in_flight` | Agreed: not reachable, because the probe cannot be cancelled | Not counted |
| Observation: setup re-entry stop timeout | Valid | B06 |
| Observation: unreferenced `default-config.txt` | Valid | E01 |
| Observation: formatting commit also reworded docstrings | Historical; no code effect | Not integrated |

### 5.3 audit-008e2929 (2026-10-10)

| Item | Disposition | ID here |
|---|---|---|
| F1 Orphaned `_global_performance_manager` | Resolved (removed in `a039165`) | — |
| Observation: `type: ignore` candidate defects | Tracked in `ai/task.md` | Not counted |
| Observation: timed waits left by change-4f671d09 | Deliberate and documented; see B05 below | — |
| Observation: `wait_for_event` polls at 0.1 s | Cost not measurable statically | Not integrated |
| Observation: `verify_obd_connection` sleep ignores shutdown | Valid; at most 2 s (`interface.py:242`) | Not counted |

### 5.4 audit-fccd5931 (2026-10-15)

| Item | Disposition | ID here |
|---|---|---|
| F1 Refused connects count toward the wedge threshold | Valid, still present | A03 |
| F2 Wall-clock step test cannot detect a frozen sweep | Valid, test unchanged | F03 |
| Observation: stale `sim_transport.py` comments | Valid | A11 |

### 5.5 Withdrawn Finding

- **B05 (timed waits on the wall clock) is withdrawn.** Version 1.0 reported `app.py:594` and several joins as defects. change-4f671d09 excluded these sites deliberately, and its reasoning for `app.py:594` is correct: `Event.set()` wakes the waiter at once whatever the clock does, so a backward step only delays a re-check that has nothing to observe. The remaining sites affect only timeout expiry during shutdown, which the exit backstop bounds.

### 5.6 Result

- All valid content of the four scheduled audits is now carried in this report. They can be closed as superseded; closure is an owner decision and no file was moved.

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Verification of Suspected Findings

| ID | Verification | Expected if the finding holds |
|---|---|---|
| A01 | With the emulator stopped, wait for the DISCONNECTED screen. Start `elm327-emulator.service` and tap Setup while a connect attempt is in flight. Then list the process's sockets (`ls -l /proc/$(pidof -s python3)/fd`) and tap Continue on the Current Device screen. | An RFCOMM socket remains open after "Disconnected from RFCOMM device" is logged; the probe reports "Device not available" with EBUSY in `error.log`. |
| A02 | Run `gtach --transport serial` against a USB ELM327 and unplug it. | `error.log` repeats "Unexpected error during command send" at the poll rate; no "Link ... dropped" record; no reconnect after re-plugging. |
| A06 | Run discovery with debug on where several Bluetooth devices are in range. | `debug.log` shows "Bluetooth discovery chunk N timed out" and chunks that return no devices. |
| A12 | Not practical to provoke on demand. Review `debug.log` for a "Discarded N stale bytes" record shortly after a command timeout, and for an RPM sample that repeats the previous value. | A reply logged for one command that matches the preceding 010C exchange. |
| C07 | Not practical to provoke on demand. Review `debug.log` for a "Touch end" record whose duration spans two physical touches. | A duration far longer than the physical touch. |

Confidence: A01 race high, consequence medium; A02 medium; A06 medium; A12 low; C07 low.

[Return to Table of Contents](#table-of-contents)

---

## 7.0 Recommendations

Each `src/` change requires an issue, change and prompt set, unless it qualifies for the trivial exemption (P04.12).

1. **A01:** In `OBDTransport.connect`, after `_open()` returns, test `_shutdown` under `_lock`; if set, close the handle, leave the state DISCONNECTED and return False. Add a regression test in which `disconnect()` runs during a blocking `_open()`.
2. **D01:** On a completed scan with no devices, and on a failed scan, transition to DEVICE_LIST, which already draws "No devices found", the error line and Back/Retry. Decide this together with the open discovery-fallback item, because both change what follows an empty filtered scan.
3. **C08:** In `_on_probe_result`, act only while the screen is still CURRENT_DEVICE, and disable New Setup while a probe is in flight.
4. **A02:** Add `OSError` to `SerialTransport._IO_ERRORS`, or catch it in `_discard_input`.
5. **X01, A06, A07:** Make cancellation effective (call `cancel_operations` from the Cancel action; ignore completions of operations no longer registered), log hcitool's return code, and size the chunk wait to hcitool's own limit.
6. **A05:** Log the missing 0100 reply at WARNING without a traceback, and rate-limit it.
7. **B01, B02, B03:** Keep the pairing factory for setup re-entry; pass `adapter_pre_initialised` only when the session sent ATZ; set `_obd_started` after `_start_obd` succeeds or clear it on failure.
8. **A09, E05, E06:** Apply DeviceStore changes in memory only after a successful save and return the result; hold the ConfigStore lock for the whole save or use a unique temp name; reject non-matching types in `load()`.
9. **G02, G03, F01, F02, F03:** `bin/` and `tests/` corrections as given in the source audits. `bin/` changes are exempt from the issue/change/prompt workflow.
10. **Trivial-exemption candidates:** A04, A11 (comments), B06 (comment, or pass the caller's timeout to `OBDProtocol.stop`), B07, C03, C09 (docstring), E02, E03, E04.
11. **Efficiency:** O1 and O2 are small, contained changes; O1 has the larger effect.
12. The remaining low findings can be grouped by file when those files are next changed.
13. Close the four scheduled audits as superseded by this report (owner decision).

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-10 | Initial audit |
| 1.1 | 2026-11-10 | §5.0 added: dispositions for the four open scheduled daily audits; findings C08 (medium), A12, B06, B07, C09, E05, E06, F01, F02, F03, G01, G02, G03 added; A06, A09, E01 extended; B05 withdrawn; totals and section numbers updated |

---

Copyright (c) 2026 William Watson. MIT License.
