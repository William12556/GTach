Created: 2026 October 07

# GTach Full-Codebase Static Audit (audit-36b6ea95)

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Tooling Results](<#2. tooling results>)
3. [Findings](<#3. findings>)
4. [Coverage Record](<#4. coverage record>)
5. [Limitations](<#5. limitations>)
6. [Version History](<#version history>)

---

## 1. Summary

**Mode:** strategic (P02.4.1). Static review only; no hardware, display, serial device, Bluetooth adapter or LAN host was available.

**Audited commit:** `2d6bb0cea13ed9d715ff1130555d328255be1aee` (branch `main`).

**Scope:** every file under `src/gtach/` (61 files, including `assets/engine_profiles.yaml`), `tests/` (13 files), `bin/*.sh`, `bin/*.py`, `bin/*.service` (13 files), `config/*.yaml` (2 files) and `pyproject.toml` — 90 files in total. Excluded: `src/gtach/display/manager_backup.py`, `src/gtach/display/setup_original_backup.py`, `ai/`, `ai-local/`, `releases/`, `3d-case/`, `docs/`, `bin/vendor/`.

**Method:** seven fixed batches (comm/; core and top-level modules; display top level; display subfolders; utils/; tests/; bin, config and pyproject), each file read in full against the ten criteria of the task brief, followed by a cross-cutting pass (lock ordering, shutdown, reconnect, configuration keys).

**Finding counts by severity:**

| Severity | Count |
|---|---|
| Critical | 1 |
| High | 5 |
| Medium | 29 |
| Low | 48 |
| **Total** | **83** |

**Top 5 risks:**

1. **Setup-mode deadlock (critical, D01).** Three locks in `SetupDisplayManager` and `SetupStateCoordinator` are taken in opposite orders by the display thread and the touch thread. A tap on a cached setup screen can deadlock both threads. The display then stops, and after 45 s the watchdog terminates the process.
2. **Touch input may be absent on a fresh install (high, suspected, G01).** The `hyperpixel2r` touch library is declared nowhere and neither installer installs it. `install.sh` also omits the `[pi]` extra. The touch layer then falls back silently to a mock, so no touch input reaches the application.
3. **Watchdog hard recovery cannot recover (high, B01).** The restart path calls `OBDProtocol.stop()` while holding the ThreadManager lock. `stop()` sets a shutdown flag that is never cleared, so the restarted OBD thread exits immediately. For the display thread, a second render loop is started while the stalled first one may still be alive.
4. **The panel can freeze while the application reports healthy (high, suspected, D02).** One failed page-flip pan disables page flipping without moving scan-out back. Every later frame is then written to the half of the framebuffer that is not displayed.
5. **Bluetooth verification runs under the async manager lock (high, D03).** On pairing success, a callback runs an RFCOMM connect and ATZ (up to about 15 s) while holding the async-operation lock. During that time the setup thread, and the display thread on the discovery screen, block.

These are compounded by B04: in production, every log record after startup at ERROR or CRITICAL level is discarded unless debug is switched on. Most of the failures above would therefore leave no trace in the field.

**Positive findings:** transport capture-then-use discipline (`transport.py:454-460`); the RFCOMM socket is closed on connect failure (`rfcomm.py:57-67`); `drop_link` and `disconnect` are kept separate, with tests; watchdog phase-1/phase-2 lock release (`watchdog.py:147-208`); a single sanctioned host action with a fixed path, no shell and 100% test coverage (`utils/pi_reset.py`); atomic, fsync'd writes in `ack_state.py` and `ConfigManager._atomic_save_config`; append-only, backed-up, verified boot-file edits in the installers; the update probation and rollback supervisor (`gtach-preflight.sh`).

**Related audits:**

- `audit-b4e8c012` (comm/ tactical): the `comm/bluetooth.py` empty stub is still present (A15). That report's other observations were descriptive and are superseded by this audit.
- `audit-2f612d17` (comm/ audit prompt): superseded in scope by this audit.
- `audit-splash-hang-debug-session-state-report`: Defects 1–3 are resolved (`DisplayMode.ACKNOWLEDGEMENT`, `_ack_state_manager` and `DisplayConfig.rpm_bands`/`engine_profile` exist). Defect 4 ("Heartbeat for unknown thread: setup") is resolved by `setup.py:148`, but registration has introduced the new defect C01.
- `audit-ui-navigation-logic-report`: Finding A (stale OPTIONS mode on setup re-entry) and Finding B (static simulation button) are resolved (`manager.py:612-617`, `manager.py:1810`). They are not re-reported.

[Return to Table of Contents](<#table of contents>)

---

## 2. Tooling Results

Environment: Linux x86_64 container, Python 3.13.16. The target is Python 3.9 on a Pi Zero 2W, so version-specific behaviour was not exercised. All tool output was written to a scratch directory; no repository file was modified by tooling. Tool by-products were removed after the run: `src/gtach.egg-info/`, `__pycache__/`, and the empty `cache/`, `data/` and `logs/` directories that the test run created (see F05).

| Tool | Result |
|---|---|
| `pip install -e .[dev]` | Succeeded. |
| `pytest --cov` | 287 passed, 1 warning, 8.0 s. The first attempt with `-p no:cacheprovider` failed because `addopts` contains `--strict-config` and `cache_dir` is then an unknown option; the run was repeated with `-o cache_dir=<scratch>`. The warning is a `PytestUnraisableExceptionWarning` from `test_stack_dump_toggle.py::test_close_failure_still_clears_state`, which leaves a file handle whose patched `close()` raises at garbage collection. Line coverage is 21% including the two backup files; excluding them, 27.4% (10,426 statements, 7,565 missed). Per-module figures are in F01 and Section 4. |
| `mypy src/` | 787 errors in 42 files, 465 excluding the backup files. Most frequent codes in scope: no-untyped-def 166, assignment 78, unreachable 50, index 34, var-annotated 31, attr-defined 19, union-attr 17, no-any-return 16, arg-type 13. Worst files in scope: `manager.py` 55, `config.py` 53, `circular_positioning.py` 32, `platform.py` 31, `touch_coordinator.py` 28. CLAUDE.md §4 rule 2 ("mypy clean") is not met. Reported once here and in the type-safety notes of individual findings. |
| `flake8 src/ tests/` | 5,640 issues, 3,838 excluding the backup files. Formatting noise dominates: W293 2,088, E501 1,261, E128 130, W291 114, E302 75, W292 43, E261 10 and others. Defect-relevant codes: F401 unused import 77, F841 unused variable 6, F541 6, F811 redefinition 4, F821 undefined name 3 (`ack_state.py`), F402 1, E722 bare except 1 (`watchdog.py:386`). |
| `black --check src tests` | 74 files would be reformatted (72 in scope); 1 unchanged. |
| `isort --check-only src tests` | 53 files incorrectly sorted (51 in scope). |
| `bandit -r src/` (backups excluded) | 41 issues, all low severity, high confidence: B110 try/except/pass 16, B603 subprocess without shell 7, B607 partial executable path 6, B112 try/except/continue 6, B404 subprocess import 4, B605 shell start 1 (`terminal.py:84`), B311 `random` 1 (`sim_bluetooth.py:196`, simulation only). No medium or high issues. |
| `pip-audit` | No known vulnerabilities in the resolved environment. `gtach` itself was skipped (not on PyPI). This audits the dev-host resolution of unpinned dependencies, not the Pi's venv. |
| `shellcheck bin/*.sh` (v0.11.0, installed via `shellcheck-py`) | 7 notes, no warnings or errors: SC2029 ×3 and SC2012 ×1 (`deploy.sh`), SC2235 and SC2035 (`build.sh`), SC2012 (`quiet-boot.sh`). |

Formatting-tool noise (W2xx, E1xx/E2xx/E3xx, E501, black and isort deltas) is recorded as one low finding (G05) rather than per file, as the brief requires.

[Return to Table of Contents](<#table of contents>)

---

## 3. Findings

Each description gives a bracketed finding ID (A = comm, B = core/top level, C = display top level, D = display subfolders, E = utils, F = tests, G = bin/config/pyproject, X = cross-cutting). "(suspected)" marks findings whose consequence depends on runtime behaviour that cannot be confirmed statically; Section 5 says how to verify them.

```yaml
# T08 Audit Template v1.0 - YAML Format
audit_info:
  id: "audit-36b6ea95"
  title: "GTach full-codebase static audit"
  date: "2026-10-07"
  mode: "strategic"
  status: "complete"
  auditor: "planner (Claude Code)"

scope:
  target: "src/gtach/, tests/, bin/*.sh, bin/*.py, bin/*.service, config/*.yaml, pyproject.toml @ 2d6bb0cea13ed9d715ff1130555d328255be1aee"
  criteria:
    - "correctness"
    - "concurrency"
    - "error_handling_and_recovery"
    - "resource_management"
    - "security"
    - "hardware_abstraction"
    - "type_safety_and_interfaces"
    - "dead_code_and_duplication"
    - "test_coverage"
    - "configuration_consistency"
  exclusions:
    - "src/gtach/display/manager_backup.py"
    - "src/gtach/display/setup_original_backup.py"
    - "ai/"
    - "ai-local/"
    - "releases/"
    - "3d-case/"
    - "docs/"
    - "bin/vendor/"

findings:
  critical:
    - location: "src/gtach/display/setup.py:203-211; src/gtach/display/setup.py:716-728; src/gtach/display/setup_components/state/coordinator.py:91-114"
      description: >-
        [D01] Lock-order inversion between SetupDisplayManager._render_cache_lock,
        _touch_regions_lock and SetupStateCoordinator._state_lock. On every frame
        where a cached screen (WELCOME, CURRENT_DEVICE, COMPLETE) is shown, the
        display thread holds _render_cache_lock and inside it calls
        _update_cached_screen_touch_regions. That call takes the coordinator's
        _state_lock via get_state() and then _touch_regions_lock via
        _update_touch_regions_safe, and it also reads devices.yaml inside the
        window (C06). The touch thread, on any setup tap, holds
        _touch_regions_lock (setup.py:723), then _state_lock (transition_to_screen,
        coordinator.py:93), and from within it calls back into
        setup._on_screen_transition → _invalidate_render_cache, which needs
        _render_cache_lock. A tap on Start Setup, Cancel or New Setup that lands
        inside the display thread's window deadlocks both threads. The display
        freezes, its heartbeat stops, and after 45 s the watchdog terminates the
        process. Why it matters: a hang during normal operation on the screen
        every new user sees first. Remediation: never call out while holding a
        lock — snapshot state under the lock and call callbacks and foreign
        locks after release; do not hold _render_cache_lock across get_state()
        or _update_touch_regions_safe(); document a single lock order
        (suspected: the interleaving frequency must be confirmed on hardware).
      issue_ref: ""
  high:
    - location: "src/gtach/comm/obd.py:80-103; src/gtach/comm/sim_transport.py:62-68; src/gtach/app.py:432-453,572-584"
      description: >-
        [A01/B02] OBDProtocol's inner poll loop tests only
        transport.is_connected() and never shutdown_event. SimTransport's
        is_connected() returns True unconditionally, even after disconnect().
        With simtcp or simbt, the non-daemon OBD thread (obd.py:48-51) therefore
        never exits. stop() returns after a 5 s join and logs "stopped" while
        the thread is still alive. ThreadManager.shutdown joins it again and
        gives up. main() then returns normally, and the interpreter blocks at
        exit joining the thread until systemd's SIGKILL. The same stall runs on
        the UI callback during _re_enter_setup, after which the old OBD thread
        keeps feeding message_queue next to the new one. For real transports,
        exit depends on the disconnect-then-stop ordering in app.py:579-582, so
        any future reordering reintroduces the hang. Remediation: test
        shutdown_event in the inner loop, make SimTransport honour disconnect(),
        and add a regression test (F02).
      issue_ref: ""
    - location: "src/gtach/core/thread.py:209-273; src/gtach/core/watchdog.py:313-334; src/gtach/comm/obd.py:59-65"
      description: >-
        [B01] The watchdog's hard recovery cannot recover a stalled thread.
        (a) _restart_thread calls the registered stop_func while holding
        _state_lock (thread.py:229-235). OBDProtocol.stop then joins for 5 s on
        a thread that is itself blocked in update_heartbeat waiting for that
        lock — the defect stop_thread already fixed (thread.py:310-315).
        (b) OBDProtocol.stop sets shutdown_event, which nothing clears, so the
        restarted thread running _protocol_loop exits on its first test. RPM
        acquisition is lost for the life of the process while the watchdog
        repeats restarts every 30-45 s.
        (c) 'display' is registered without a stop_func (manager.py:202), so a
        second display loop is started while the stalled original may still be
        running, giving two threads driving pygame and the framebuffer.
        Remediation: call stop_func outside the lock; start a replacement only
        after the old thread is confirmed dead; make OBDProtocol restartable
        (clear the event on start), or exclude it from restart and escalate
        instead.
      issue_ref: ""
    - location: "src/gtach/display/rendering/engine.py:798-818"
      description: >-
        [D02] Page-flip failure path. After at least one successful flip
        (buffer_index 1, scan-out on the second half), a failed
        _pan_display(target) sets page_flip False but leaves buffer_index and
        the hardware y-offset on half 1. Every later frame takes the
        single-buffer branch and is written at offset 0, which is not
        displayed. The panel freezes on the last good frame while the display
        thread, its heartbeat and the watchdog all report healthy, and the only
        trace is a single INFO line. Why it matters: a stale RPM indication
        with no fault visible to the driver. Remediation: on pan failure, pan
        back to 0 (or keep writing into the displayed half) before disabling
        page flipping, and add a test (suspected: requires a transient
        FBIOPAN_DISPLAY error).
      issue_ref: ""
    - location: "src/gtach/display/setup_components/bluetooth/interface.py:313-361; src/gtach/display/async_operations.py:298-306,330-338"
      description: >-
        [D03] AsyncOperationManager invokes progress and completion callbacks
        while holding its non-reentrant _operations_lock. On pairing success,
        on_pairing_complete runs verify_obd_connection inside that callback: an
        RFCOMM connect (10 s timeout) plus ATZ (5 s) (interface.py:135-172).
        For up to about 15 s every other user of the manager blocks. The setup
        thread blocks in start_discovery → cancel_operation/submit_operation
        (setup.py:180-185) and stops heartbeating. The display thread blocks if
        it renders the DISCOVERY screen (get_active_operation_progress →
        get_operation_status). A callback that queries the manager would
        self-deadlock. The callback also introduces the lock order
        operations → coordinator state → render cache (interface.py:335,342),
        and the operations dict is never pruned (cleanup_completed_operations
        has no caller). Remediation: copy the operation under the lock and
        invoke callbacks after release; run verification as its own operation.
      issue_ref: ""
    - location: "pyproject.toml:33-53; bin/install.sh:248; bin/pi-install.sh:241-243; src/gtach/display/touch_interface.py:64-69,291-305"
      description: >-
        [G01] Real touch input needs both RPi.GPIO and the hyperpixel2r Python
        package. hyperpixel2r is declared in neither dependencies nor the pi
        extra, and neither installer installs it. install.sh (the deploy.sh
        path) installs the wheel without [pi], so RPi.GPIO is missing too.
        HyperPixelTouchInterface.start then falls back silently to
        MockHyperPixelTouch, which never emits events. On a freshly provisioned
        Pi, setup, OPTIONS and the DISCONNECTED controls are unreachable.
        docs/pi-setup.md says "GTach does not use touch input", which
        contradicts the code. Remediation: declare hyperpixel2r in the pi
        extra, install with [pi] in both installers, and log the mock fallback
        at ERROR on a Raspberry Pi (suspected: the current device may carry a
        hand-installed package in its long-lived venv).
      issue_ref: ""
  medium:
    - location: "src/gtach/comm/obd.py:136-138"
      description: >-
        [A02] _initialize_protocol treats any non-empty 0100 response not
        starting with '7F' as "vehicle connected". It therefore accepts
        'NO DATA', 'UNABLE TO CONNECT', 'SEARCHING...' and '?'. The application
        reports an initialised link while the ECU is not answering, and the
        failure appears only as missing RPM samples. Remediation: require a
        '41 00'/'4100' response and treat the ELM error strings as failures.
      issue_ref: ""
    - location: "src/gtach/comm/obd.py:77-78"
      description: >-
        [A03] When initialisation fails, the outer loop continues immediately
        with no back-off: it repeats ATZ/ATE0/ATL0/ATS0/ATSP0/0100 and logs an
        error every iteration while the adapter answers but the vehicle does
        not. This busy-loops the adapter, floods logs and wastes CPU on the
        Pi Zero. Remediation: wait (on shutdown_event) before retrying.
      issue_ref: ""
    - location: "src/gtach/comm/transport.py:474-480,341-345"
      description: >-
        [A04] On an empty read (peer closed), send_command sets DISCONNECTED
        but neither discards the handle nor records last_failure_cause. The
        next connect() overwrites self._handle (transport.py:342) without
        closing the old one, so one socket is leaked per peer-initiated close,
        and the DISCONNECTED screen shows no cause in this case. Remediation:
        call _discard_handle() and set a cause in that branch.
      issue_ref: ""
    - location: "src/gtach/comm/transport.py:289-322,364-367"
      description: >-
        [A05] The connect-error classification is Bluetooth-specific but runs
        for every transport. An empty /sys/class/bluetooth reports 'no
        bluetooth controller' for TCP and serial failures. After six failed
        connects to a TCP emulator the cause becomes 'bluetooth wedged - reset
        required', which sends the operator to the wrong remedy. Remediation:
        let subclasses opt in to the adapter checks (RFCOMM only).
      issue_ref: ""
    - location: "src/gtach/comm/serial_transport.py:27-32; src/gtach/comm/transport.py:481-498"
      description: >-
        [A06] pyserial returns b'' on timeout, which the base class treats as a
        normal (empty) response and which resets _consecutive_timeouts to 0.
        The serial transport's dead-peer detection (issue-9c2f41d8) can
        therefore never trip. An adapter that powers off behind a still-open
        UART is polled forever with no drop_link and no reconnect.
        Remediation: count an empty serial response as a timeout.
      issue_ref: ""
    - location: "src/gtach/comm/system_bluetooth.py:51-58,76-79; src/gtach/comm/pairing.py:329-334,447-451"
      description: >-
        [A07] BluetoothSocket.settimeout() before connect() only stores the
        value; connect() creates the socket and never applies it. The
        configured pairing connection_timeout and the 10 s test timeout are
        ignored on the 'system' backend, and connect blocks for the kernel
        page timeout. Remediation: apply self.timeout when creating the socket.
      issue_ref: ""
    - location: "src/gtach/comm/pairing.py:75,163-173,579-596"
      description: >-
        [A08] Discovery futures that time out keep running in a two-worker
        pool. Two hung hcitool/bluetoothctl calls saturate it, and later
        chunks then queue behind them and time out in turn. shutdown() waits
        for the hung workers (wait=True) and __del__ calls it, so garbage
        collection or exit can block (suspected). Remediation: kill the child
        process on timeout and shut down with cancel_futures.
      issue_ref: ""
    - location: "src/gtach/comm/device_store.py:32"
      description: >-
        [A09] DeviceStore defaults to the CWD-relative path
        'config/devices.yaml' and has no lock. Twelve call sites construct
        independent instances, each with its own in-memory copy (app.py:64,
        setup.py:140,301,679,779,796,798,825, manager.py:2052, interface.py:29,
        transport.py:677, sim_bluetooth.py:211). A long-lived instance can save
        stale data over another instance's write. Remediation: one shared,
        lock-guarded instance with an absolute path from configuration.
      issue_ref: ""
    - location: "src/gtach/comm/transport.py:386,527; src/gtach/comm/obd.py:144,158,184; src/gtach/comm/pairing.py:216,222,241,372,426,507,549; src/gtach/comm/device_store.py:71,138,185,205,232,257; src/gtach/comm/system_bluetooth.py:154,194,208"
      description: >-
        [A11] Unexpected exceptions are logged without exc_info=True, breaking
        CLAUDE.md §4 rule 6. Tracebacks are lost on the transport, protocol,
        pairing and persistence paths, which are the ones field faults go
        through. The same pattern recurs in display/ (for example
        manager.py:259,310,353,388,454,509,644,843,1013,2161) and utils/.
        Remediation: add exc_info=True to every handler that catches
        Exception.
      issue_ref: ""
    - location: "src/gtach/app.py:472-478; src/gtach/core/thread.py:120-125"
      description: >-
        [B03] On setup re-entry the 'transport' entry is never stopped
        (_re_enter_setup stops only obd_protocol). register_thread('transport',
        new_thread) therefore finds the old entry RUNNING and returns silently.
        ThreadManager keeps the dead Thread object, shutdown joins the wrong
        thread, and the watchdog follows the new thread only because the
        heartbeat key happens to match. Remediation: stop_thread('transport')
        on re-entry, or let register_thread replace dead threads.
      issue_ref: ""
    - location: "src/gtach/main.py:61-114; src/gtach/app.py:187-211"
      description: >-
        [B04] After startup, start.log's handler is raised to CRITICAL+1 and
        debug.log stays at CRITICAL+1 unless debug is toggled on. No other
        handler exists, so every runtime ERROR and CRITICAL record — watchdog
        escalation, link loss, render faults — is discarded in production.
        Field faults cannot be diagnosed after the fact. Remediation: keep an
        always-on WARNING-level rotating handler, or let debug.log carry
        WARNING and above by default.
      issue_ref: ""
    - location: "src/gtach/core/thread.py:291-331,382-390"
      description: >-
        [B05] stop_thread and shutdown never call the registered stop_func.
        ThreadManager.shutdown, and the watchdog's fallback path
        (watchdog.py:373-374), can only join, so they rely on every thread
        having been signalled beforehand. Threads that no app code signals
        are joined to timeout. Remediation: call stop_func (outside the lock)
        before joining.
      issue_ref: ""
    - location: "src/gtach/display/setup.py:159-174,769-773; src/gtach/app.py:411-459"
      description: >-
        [C01] On SetupScreen.COMPLETE the setup loop calls on_complete and
        breaks. Its 'setup' entry stays RUNNING with a frozen heartbeat, so the
        watchdog warns at 15 s and soft then hard recovers at 30-40 s. The
        restarted _setup_loop immediately calls on_complete again (rejected by
        app.py:403-405) and exits. This restart and error cycle repeats for the
        life of the process after every completed setup. The cancel_setup path
        completes without stopping the setup thread, and _re_enter_setup
        replaces _setup_manager without calling stop_setup(), which leaves the
        old setup thread running. Remediation: mark the thread STOPPED on
        completion and stop the previous SetupDisplayManager on re-entry.
      issue_ref: ""
    - location: "src/gtach/display/setup.py:775-791"
      description: >-
        [C02] 'current_continue' runs a synchronous RFCOMMTransport.connect()
        (10 s socket timeout) on the touch-callback thread while
        _emit_touch_event holds the touch-interface lock (C04). Touch input is
        frozen for the duration, and nothing on screen changes because
        CURRENT_DEVICE is a cached screen. Under simbt the stored fake MAC can
        never connect, so Continue always fails on the development host.
        Remediation: run the probe as an async operation with a progress
        state.
      issue_ref: ""
    - location: "src/gtach/display/touch.py:83-150; src/gtach/display/manager.py:313-455,2064-2135,2606-2617"
      description: >-
        [C03] Touch callbacks (hyperpixel2r/mock thread) and the update worker
        (manager.py:2101-2113) write DisplayManager state — config.mode,
        _options_view, _options_page, _sim_mode, _in_setup_mode, _setup_manager,
        _update_status — while the display thread reads it every frame.
        DisplayManager has no lock, which breaks CLAUDE.md §4 rule 4.
        Single-attribute writes are atomic under the GIL, so the effect is torn
        multi-field transitions rather than crashes (suspected). Remediation:
        guard view state with one lock, or queue UI actions to the display
        thread.
      issue_ref: ""
    - location: "src/gtach/display/touch_interface.py:166-178"
      description: >-
        [C04] The registered callback is invoked while the non-reentrant
        interface lock is held, so the whole UI action chain runs under it.
        That chain includes app._re_enter_setup's transport disconnect and
        2-7 s of joins, and the RFCOMM probe (C02). Any path that registers or
        unregisters a callback from inside a callback would self-deadlock.
        Remediation: copy the callback under the lock and invoke it outside.
      issue_ref: ""
    - location: "src/gtach/display/manager.py:1131,1164"
      description: >-
        [C05] RPM is clamped to a hard-coded 7000 and the arc is scaled to
        max_rpm 7000 regardless of engine profile. generic_na_4cyl (redline
        7500) and any profile above 7000 (allowed up to 15000 by
        models.py:56-61) cannot show its redline mark or any RPM beyond 7000,
        so the gauge saturates below redline. Remediation: derive max_rpm and
        tick range from rpm_bands.redline_rpm.
      issue_ref: ""
    - location: "src/gtach/display/setup.py:300-301,679,820-832"
      description: >-
        [C06] DeviceStore() — a YAML file read and parse — is constructed
        inside render paths. While WELCOME is cached,
        _update_cached_screen_touch_regions runs on every frame, so
        devices.yaml is read and parsed 30-60 times per second on the
        Pi Zero 2W. That read also happens inside _render_cache_lock and
        widens D01's window. Remediation: cache has_device and refresh it on
        state change.
      issue_ref: ""
    - location: "src/gtach/display/setup.py:332-337,461-468"
      description: >-
        [C08] On the uncached DEVICE_LIST screen, error_message is cleared
        immediately after it is drawn, so errors such as 'OBD check failed'
        are visible for one frame (about 17 ms). WELCOME prints the fixed text
        'No devices found' for any error message, including 'Device not
        available'. Pairing and verification failures are therefore
        effectively invisible to the operator. Remediation: clear errors on
        the next user action or after a timeout, and render the actual
        message.
      issue_ref: ""
    - location: "src/gtach/display/setup_components/state/coordinator.py:67-70"
      description: >-
        [D04] get_state() returns the live SetupState under the lock, so the
        lock protects nothing. interface.py:182-241,284-361 and setup.py:468
        mutate pairing_status, discovered_devices, error_message and
        discovery_progress from async worker threads while the display thread
        iterates discovered_devices (setup.py:404-447). This breaks CLAUDE.md
        §4 rule 4. Remediation: route every mutation through update_state()
        and return copies.
      issue_ref: ""
    - location: "src/gtach/display/setup_components/bluetooth/interface.py:36,88-89,243-244,356-357"
      description: >-
        [D05] _active_operations is mutated from worker callbacks, the setup
        thread (setup.py:180) and the touch thread (setup.py:746,762) without a
        lock. A check-then-start race can launch duplicate discoveries.
        Remediation: guard it with a lock.
      issue_ref: ""
    - location: "src/gtach/display/input/touch_coordinator.py:211-250,468-484"
      description: >-
        [D06] Button callbacks run while the coordinator RLock is held.
        app._re_enter_setup (via disconnected_setup or confirm_clear_yes)
        therefore runs under it for 2-7 s, during which the display thread
        blocks in clear_regions/register_button_region (manager.py:1442,1567).
        The UI freezes immediately after the operator taps Setup.
        Remediation: resolve the hit under the lock and invoke the callback
        after release.
      issue_ref: ""
    - location: "src/gtach/utils/config.py:1100-1145; src/gtach/utils/home.py:67-107; src/gtach/app.py:134; src/gtach/display/manager.py:80,511-644; src/gtach/comm/device_store.py:32"
      description: >-
        [E01] Configuration is split across unrelated files, and the main one
        has no effect. ConfigManager's OBDConfig is loaded and discarded
        (app.py:134). pairing.py re-parses the same file for a
        bluetooth.pairing section that OBDConfig neither defines nor writes.
        DisplayManager keeps its own CWD-relative config.yaml with a flat
        schema and rewrites the whole file non-atomically with only its seven
        keys. DeviceStore uses CWD-relative config/devices.yaml. Under systemd
        (User=root, WorkingDirectory=/opt/gtach, installed package) these
        resolve to three locations:
        /root/.local/share/obdii/config/config.yaml (ConfigManager),
        /opt/gtach/config.yaml (DisplayManager) and
        /opt/gtach/config/devices.yaml (DeviceStore). In development,
        ConfigManager and DeviceStore write into the tracked repository
        config/. As a result, config/config.yaml values (display.fps_limit 30,
        engine_profile, rpm_bands, splash.*, every bluetooth.* and OBD key)
        have no effect, and the Pi runs at DisplayManager's default 60 fps,
        which ConfigValidator itself flags as too high for a Pi
        (config.py:398-399). Remediation: one file, one schema, one owner;
        inject the loaded config into DisplayManager, the transports and
        pairing.
      issue_ref: ""
    - location: "src/gtach/main.py:328-335; src/gtach/utils/config.py:1228-1247"
      description: >-
        [E02] `--validate-config` exits 0 for any file. load_config logs
        validation errors as warnings and returns the parsed config, and on
        any exception returns defaults instead of raising, so the CLI check
        can never fail. Remediation: add a strict validation path that
        returns errors to the CLI.
      issue_ref: ""
    - location: "tests/"
      description: >-
        [F01] Critical paths are thinly covered: comm/obd.py 20% (protocol
        loop, init and RPM parsing untested), comm/sim_transport.py 0%,
        comm/pairing.py 10%, comm/device_store.py 34%, core/thread.py 50%
        (_restart_thread untested), core/watchdog.py 49% (recovery untested),
        app.py 43% (_start_obd, _re_enter_setup, _on_setup_complete and
        shutdown ordering untested), display/manager.py 15%, setup.py 22%,
        bluetooth/interface.py 6%, touch_coordinator.py 11%,
        rendering/engine.py 28% (page flip untested). No test drives a thread
        lifecycle end to end — start, link loss, reconnect, shutdown — with
        SimTransport, which CLAUDE.md §6 names as the realistic-input harness.
        Remediation: add lifecycle integration tests on SimTransport.
      issue_ref: ""
    - location: "tests/"
      description: >-
        [F02] There are no regression tests for the defects in this audit: OBD
        thread exit with SimTransport (A01), handle discard on EOF (A04),
        serial dead-peer detection (A06), TCP/serial cause classification
        (A05), setup-mode lock ordering (D01), page-flip pan failure (D02),
        setup completion versus the watchdog (C01), and hard-recovery restart
        of obd_protocol (B01). CLAUDE.md §4 rule 3 requires a regression test
        with each fix.
      issue_ref: ""
    - location: "bin/gtach.service:9-15"
      description: >-
        [G02] The whole application runs as root with no sandboxing: no
        NoNewPrivileges, ProtectSystem, ProtectHome, PrivateTmp or
        CapabilityBoundingSet. As root it parses adapter responses, YAML
        files and staged wheels, and it runs a shell at exit (E03), so a
        defect in any of these has full system impact. Remediation: run as a
        dedicated user in the video/bluetooth/i2c groups with a narrowly
        scoped polkit or sudoers rule for /sbin/reboot, or at minimum add
        systemd hardening directives.
      issue_ref: ""
    - location: "src/gtach/display/setup.py:204-211,723-728; src/gtach/display/setup_components/state/coordinator.py:89,114; src/gtach/display/async_operations.py:301-304,333-336; src/gtach/display/touch_interface.py:173-178; src/gtach/display/input/touch_coordinator.py:211-240; src/gtach/core/thread.py:229-235"
      description: >-
        [X01] There is no documented lock hierarchy, and seven sites enter
        callbacks or foreign locks while holding a lock. D01 is the realised
        deadlock; D03, D06, B01 and C04 are the realised stalls. Remediation:
        adopt a project rule against calling out under a lock and document
        the remaining permitted orders in CLAUDE.md §4.
      issue_ref: ""
    - location: "src/gtach/app.py:558-588; src/gtach/core/thread.py:333-404"
      description: >-
        [X02] The shutdown sequence has no overall deadline. It runs
        sequential joins — 5 s watchdog, 5 s setup manager (latest only), 5 s
        display, 5 s OBD — and then ThreadManager.shutdown, which waits on
        worker_pool.shutdown(wait=True) and joins each thread with a 1 s
        floor. The 20 s backstop is armed only on the watchdog path. Never
        stopped: the touch interface (C14), the async workers,
        BluetoothPairing's executor (its non-daemon workers are joined at
        interpreter exit, so a running hcitool or bluetoothctl call delays
        exit), and earlier SetupDisplayManagers (C01). systemd's 90 s
        TimeoutStopSec is the effective bound, and with SimTransport it is
        always reached (A01). Remediation: one shutdown deadline, stop every
        component that owns a thread, and arm the backstop on every exit path.
      issue_ref: ""
  low:
    - location: "src/gtach/comm/device_store.py:131-135"
      description: >-
        [A10] devices.yaml is written to a temporary file without flush or
        fsync before os.replace. A power cut at ignition-off can leave an
        empty or truncated file on some filesystems, losing the pairing
        (suspected). Remediation: flush and fsync before the replace, as
        ConfigManager already does.
    - location: "src/gtach/comm/tcp_transport.py:43-47"
      description: >-
        [A12] The TCP socket is not closed when connect raises. RFCOMM fixed
        the same defect (rfcomm.py:57-67); TCP relies on CPython reference
        counting. Remediation: mirror the RFCOMM try/close.
    - location: "src/gtach/comm/sim_bluetooth.py:71-72,103-118,180-193"
      description: >-
        [A13] The simulated cancel events are never cleared. After one cancel,
        every later simulated discovery and pairing short-circuits (pairing
        always returns False), so simbt testing breaks after the first Cancel.
        Remediation: clear the events at the start of each operation, as
        BluetoothPairing does.
    - location: "src/gtach/comm/models.py:20; src/gtach/display/setup_models.py:45; src/gtach/comm/pairing.py:46-70,307-508"
      description: >-
        [A14] Duplication: there are two BluetoothDevice classes, converted
        by hand in interface.py:325 and sim_bluetooth.py:206. pairing.py reads
        YAML directly instead of using ConfigManager. pair_device and
        test_obd_connection duplicate the connect-and-test logic.
    - location: "src/gtach/comm/bluetooth.py; src/gtach/comm/pairing.py::BluetoothPairing._is_elm327_device; src/gtach/comm/pairing.py::BluetoothPairing.get_device_info; src/gtach/comm/pairing.py::BluetoothPairing.test_obd_connection; src/gtach/comm/system_bluetooth.py::SystemBluetoothManager.pair_device"
      description: >-
        [A15] Dead code. comm/bluetooth.py is an empty file (already flagged
        by audit-b4e8c012 and still present). pairing.py has the unused
        import `signal` and methods with no caller in src/
        (_is_elm327_device, get_device_info, test_obd_connection,
        discover_all_devices). SystemBluetoothManager.pair_device,
        connect_device, disconnect_device and is_device_connected have no
        callers. Unused imports remain in models.py, rfcomm.py,
        serial_transport.py and tcp_transport.py (flake8 F401).
    - location: "src/gtach/comm/transport.py:123-130"
      description: >-
        [A16] ConnectionError and TimeoutError shadow the builtins of the same
        names in any module that imports them. Remediation: rename them
        (TransportConnectionError and so on).
    - location: "src/gtach/comm/pairing.py:165"
      description: >-
        [A17] The chunk duration is computed from self.discovery_timeout
        rather than the effective `timeout`. When discovery_timeout is smaller
        than the chunk count, this yields 0 s scan chunks.
    - location: "src/gtach/comm/system_bluetooth.py:115-117,160-195"
      description: >-
        [A18] bluetoothctl processes are killed or terminated without wait()
        (zombies). The reader thread mutates the `devices` dict, unguarded,
        while the caller returns it.
    - location: "src/gtach/comm/obd.py:168-178"
      description: >-
        [A19] The PID byte (data[1]) is never checked against 0x0C, so a
        stray '41 xx' response from another PID would be decoded as RPM.
    - location: "src/gtach/core/thread.py:204-207,343"
      description: >-
        [B06] _active_futures is mutated from done-callbacks on worker threads
        without a lock while shutdown iterates it. This can raise
        "Set changed size during iteration".
    - location: "src/gtach/core/thread.py:191-195; src/gtach/core/watchdog.py:258-311,386"
      description: >-
        [B07] handle_thread_failure passes exc_info=True outside an except
        block, which logs "NoneType: None". Soft recovery performs no action:
        it only sleeps and re-reads the heartbeat. watchdog.py:386 has a bare
        except (E722). There are unused imports (signal in watchdog.py and
        app.py).
    - location: "src/gtach/core/thread.py:67-72"
      description: >-
        [B08] ThreadInfo reads the private Thread._target, _args and _kwargs,
        which CPython does not guarantee. Remediation: store the target
        explicitly at registration.
    - location: "src/gtach/app.py:378-382,512-516; src/gtach/comm/rfcomm.py:33; src/gtach/comm/tcp_transport.py:35; src/gtach/comm/serial_transport.py:38"
      description: >-
        [B09] _retry_interval_callback reads `retry_delay`, but the transports
        define `_retry_delay`, which nothing reads. The callback always yields
        None, and the per-transport retry_delay attributes are dead.
    - location: "src/gtach/app.py:38,134,545; src/gtach/main.py:21-22"
      description: >-
        [B10] Type and interface defects: the result of load_config() is
        unused (F841); `config_path: str = None` and
        `_start_handler: logging.Handler = None` are implicit Optionals
        (mypy no_implicit_optional); run() is annotated NoReturn but returns.
    - location: "src/gtach/__init__.py:10-13"
      description: >-
        [B11] Importing the package eagerly imports app (pygame and the
        transport stack), which defeats the deferred import in
        main.py:290-293. __version__ is hard-coded (see G06).
    - location: "src/gtach/app.py:401-409,455"
      description: >-
        [B12] The _obd_started flag is read and written without a lock from
        the setup-completion callback (setup thread or touch thread) and the
        UI re-entry callback.
    - location: "src/gtach/display/manager.py:750"
      description: >-
        [C10] `1.0 / self.config.fps_limit` raises ZeroDivisionError on every
        frame if fps_limit is 0 in config. It is caught, and the loop
        degrades to 10 Hz with an error per frame. PerformanceMonitor guards
        the same value (manager.py:182-184), but the loop does not.
    - location: "src/gtach/display/navigation_gestures.py:323-331"
      description: >-
        [C11] end_gesture_tracking holds the non-reentrant _gesture_lock and
        calls detect_gesture, which acquires it again (:149) — a certain
        self-deadlock if ever called. Only cancel_gesture is reachable
        (touch.py:137); the rest of the module is dead (0% coverage).
        Remediation: delete the module or the dead methods.
    - location: "src/gtach/display/manager.py:2137-2217,2601-2604,652-654,1050-1055; src/gtach/display/touch.py:257-316,413-479; src/gtach/display/touch_interface.py:468-795,899-971; src/gtach/display/typography.py:423-690,790-944"
      description: >-
        [C12] Dead code in display/: the RPM sliders and save button, change_mode
        (called only from dead code), run_main_thread_loop,
        _process_settings_touch, _provide_touch_feedback, the touch
        simulation helpers, MockTouchInterface's simulation API,
        get_available_interfaces, create_specific_interface, the MockGPIO
        object, ButtonRenderer/render_standard_button and the validate_*
        helpers. rpm_warning and rpm_danger are persisted but never drawn.
        The comment at manager.py:1050-1055 says _get_band_colour has no
        caller, but it is called at :1148.
    - location: "src/gtach/display/splash.py:301-305,499,551,561,585"
      description: >-
        [C13] _font_render_times grows by one entry per subtitle draw in the
        'minimal' and 'text_only' graphics modes (60 Hz) and is trimmed only in
        get_performance_report, which nothing calls (unbounded growth).
        `% 1 == 0` is always true, giving an INFO log per frame without
        pygame. Progress divides by duration, which is 0.0 when the splash is
        disabled.
    - location: "src/gtach/display/touch.py:381-390; src/gtach/display/manager.py:670-683; src/gtach/display/touch_interface.py:393-406"
      description: >-
        [C14] TouchHandler.stop() is never called, DisplayManager.stop() does
        not stop the touch interface, and the interface's stop() does not stop
        the real hyperpixel2r device.
    - location: "src/gtach/display/typography.py:747-752; src/gtach/display/manager.py:2626"
      description: >-
        [C15] get_rpm_large_font calls set_bold(True) on the shared cached
        180 px font, mutating it for every user. handle_touch_event logs every
        touch at INFO.
    - location: "src/gtach/display/touch_interface.py:97-98; src/gtach/display/touch.py:114; src/gtach/display/splash.py:173,212"
      description: >-
        [C16] Wall-clock time.time() is used for touch durations and splash
        timing. A clock step (NTP sync on a Pi with no RTC) can misclassify a
        press or end or extend the splash. Remediation: use time.monotonic().
    - location: "src/gtach/display/models.py:205-219; src/gtach/display/manager.py:489-499"
      description: >-
        [C17] There are two sets of gesture defaults (80/200/40/1.0/5.0 and
        50/100/30/2.0/3.0). The getattr defaults are dead because
        DisplayConfig always defines the fields.
    - location: "src/gtach/display/setup_components/state/coordinator.py:360-381,501"
      description: >-
        [D07] create_manual_device passes rssi= and omits signal_strength and
        last_seen, so it raises TypeError. get_setup_progress references the
        nonexistent PairingStatus.PAIRING. Both are dead (no callers).
    - location: "src/gtach/display/setup_components/rendering/device_surfaces.py:136-239,196,351,503-557; src/gtach/display/setup_components/layout/circular_positioning.py:56-181,319-573; src/gtach/display/graphics/splash_graphics.py:226-585"
      description: >-
        [D08] device_surfaces reads device.rssi, which the setup
        BluetoothDevice does not have (its field is signal_strength), so
        signal bars never render. The following have no callers:
        render_compact_device_item, get_cache_stats, optimize_cache, most of
        CircularPositioningEngine (position_in_circle, validate_*, the curved
        list and performance statistics), and splash_graphics'
        draw_obdii_connector, draw_progress_bar, draw_animated_dots and
        create_gradient_surface.
    - location: "src/gtach/display/performance/__init__.py:28-50; src/gtach/display/setup.py:32"
      description: >-
        [D09] get_performance_manager is imported but never called; the
        second PerformanceMonitor singleton API is dead.
    - location: "src/gtach/display/input/interfaces.py:17; src/gtach/display/input/touch_coordinator.py:20; src/gtach/display/rendering/interfaces.py:17; src/gtach/display/rendering/engine.py:25; src/gtach/display/performance/monitor.py:20,23; src/gtach/display/graphics/splash_graphics.py:346,535; src/gtach/display/typography.py:190,262"
      description: >-
        [D10] Hardware-abstraction inconsistency. These modules import pygame
        and psutil unconditionally while sibling modules wrap pygame in
        try/except, and signature annotations naming pygame.Rect or
        pygame.font.Font raise AttributeError at import when the conditional
        import yields None. The fallbacks are therefore unreachable. pygame
        and psutil are declared dependencies, so impact is nil; the
        conditional-import code is dead. RPi.GPIO is imported conditionally
        (touch_interface.py:27-61), which complies with CLAUDE.md §4 rule 5.
    - location: "src/gtach/display/rendering/engine.py:917-954"
      description: >-
        [D11] cleanup() closes fb and fb_dev but does not reset them to None.
        If the display thread outlived its 5 s join (manager.py:673), each
        later frame raises on the closed mmap and logs an error.
    - location: "src/gtach/utils/terminal.py:43-53,84"
      description: >-
        [E03] `os.system('stty sane')` runs through /bin/sh with a PATH lookup
        at every process exit — as root under systemd, where there is no TTY
        (bandit B605). This contradicts pi_reset.py:11-15's rule that only
        pi_reset invokes external commands. backup_framebuffer_settings (no
        callers) passes a 64-byte buffer for the 160-byte fb_var_screeninfo
        and would write a truncated struct back if used. Remediation: use
        termios restoration only; delete the framebuffer helpers.
    - location: "src/gtach/utils/config.py:229-274,343,552,682-1072,1313,1540"
      description: >-
        [E04] Dead code and stale schema in config.py: SessionManager (never
        instantiated), ConfigTransaction, legacy ~/.obdii migration, "Bleak"
        BluetoothConfig fields (the project uses RFCOMM), a validator that
        accepts the retired 'DIGITAL' mode, a DisplayConfig mode default of
        "DIGITAL", print() in place of logging, a re-imported datetime (F811)
        and a shadowed `field` (F402). RWLock is live and tested.
    - location: "src/gtach/utils/dependencies.py:139-245,584-627"
      description: >-
        [E05] The dependency validator checks pybluez and requests, which are
        not declared in pyproject, but not psutil (imported unconditionally by
        performance/monitor.py:20), gpiozero (declared, imported nowhere) or
        hyperpixel2r (G01). Its last-resort version check shells out to
        `pip show`.
    - location: "src/gtach/utils/updater.py:54-62,96-106; bin/gtach-preflight.sh:220-231"
      description: >-
        [E06] A staged wheel is accepted on zip integrity alone, with no hash
        or signature, and is installed as root at boot. This is acceptable
        only while /opt/gtach/updates is root-owned 0755 (install.sh:214,
        pi-install.sh:218). Record the trust assumption.
    - location: "src/gtach/utils/platform.py:77-111,820-947,1102; src/gtach/utils/ack_state.py:61,90,141"
      description: >-
        [E07] MockRegistry, the GPIO/hyperpixel/pygame mocks and
        import_module_with_mock have no callers. platform.py re-imports sys
        (F811). ack_state.py forward-references RPMBands without a
        TYPE_CHECKING import (F821, mypy name-defined).
    - location: "src/gtach/utils/home.py:126-161"
      description: >-
        [E08] _can_create_directory creates the parent directory as a side
        effect of a capability probe. Any path containing 'src/gtach' counts
        as development, which redirects ConfigManager to the repository
        root.
    - location: "tests/test_link_loss_recovery.py:185-191,315-343; tests/test_connect_error_classification.py:432-441,513-520,573-578; tests/test_disconnected_screen.py:175-181,314-336,517-524; tests/test_touch_dispatch.py:136-151,244-270; tests/test_stack_dump_toggle.py:244-250; tests/test_stacks_log_rotation.py:293-302,321-326; tests/utils/test_rwlock.py:368-488"
      description: >-
        [F03] Many tests assert on source text rather than behaviour, so they
        pin the implementation and fail on harmless refactors.
        test_touch_dispatch.py:260-270 requires `DisplayMode.RADIAL` to stay
        in touch.py, where only dead code references it, so it blocks
        dead-code removal (C12).
    - location: "tests/test_device_list_focus.py:211-233"
      description: >-
        [F04] TestSlotContents._slots re-implements slot selection inside the
        test, and four tests assert against that helper. The production rule
        (setup.py:413-418) is not exercised by them.
    - location: "tests/conftest.py; tests/test_watchdog_process_termination.py:32-55; tests/test_stack_dump_toggle.py:169-180"
      description: >-
        [F05] Test isolation. A real GTachApplication is constructed, whose
        ConfigManager singleton runs ensure_directories() against OBDII_HOME
        — the repository root in development. The test run created cache/,
        data/ and logs/ in the working tree, and the singleton persists
        across tests. test_close_failure_still_clears_state leaks a file
        handle (PytestUnraisableExceptionWarning). Remediation: set OBDII_HOME
        to tmp_path in conftest, reset the singleton, and restore close().
    - location: "tests/test_pi_reset.py:191-231"
      description: >-
        [F06] The "subprocess only in pi_reset" and "no shell=True" scans miss
        os.system (terminal.py:84, E03). The allow-list includes
        manager_backup.py, an excluded backup that is still packaged (G06).
    - location: "bin/gtach.service:4-16"
      description: >-
        [G03] StartLimitBurst=3 within 60 s leaves the unit failed until
        reboot after three quick start failures; the update rollback in
        gtach-preflight.sh:233-249 consumes exactly three starts. There is no
        TimeoutStopSec, so a hung stop (A01) delays shutdown by the 90 s
        default. After= without Wants=/Requires= orders bluetooth.service and
        hyperpixel2r-init.service but does not pull them in.
    - location: "pyproject.toml:11-61,135-144"
      description: >-
        [G04] `click>=8.0` is declared and never imported. Metadata is stale:
        the description ("GPIO-based Tachometer Application"), gpio keywords,
        placeholder URLs (https://github.com/user/GTach) and authors.
        Classifiers stop at Python 3.11. The mypy override lists unused
        gpiozero.* and obd.* (mypy reports an unused section) and has no entry
        for the untyped hyperpixel2r and bluetooth imports.
    - location: "pyproject.toml:104-131"
      description: >-
        [G05] Formatting-tool noise, summarised as one item. black and isort
        are pinned to 88 columns, while CLAUDE.md §7 requires PEP 8's 79 and
        flake8 (with no [tool.flake8] section) defaults to 79, producing 1,261
        in-scope E501. Neither formatter has been applied: black would
        reformat 72 in-scope files and isort 51, and there are 2,088 W293 and
        other whitespace codes. Remediation: choose one limit, configure all
        three tools to it, and run them once in a dedicated change.
    - location: "pyproject.toml:63-64; src/gtach/__init__.py:13; bin/build.sh:58-93"
      description: >-
        [G06] packages.find ships manager_backup.py and
        setup_original_backup.py (about 5,700 lines, 0% coverage) in the wheel
        installed on the Pi. The version string is duplicated in two files and
        kept in step only because build.sh rewrites __init__.py wholesale;
        pi-install.sh installs from the git tag without running build.sh.
        Both are currently 0.4.3.
    - location: "config/devices.yaml:2-5; config/config.yaml:7,36-43"
      description: >-
        [G07] devices.yaml's setup.completed, discovery_timeout and first_run
        keys are read by no code. config.yaml carries the retired
        bluetooth.saved_devices and display.rpm_bands/engine_profile, which no
        reader consumes (E01). Both tracked files are rewritten at runtime in
        development.
    - location: "bin/deploy.sh:172-201; bin/pull_logs.sh:101-104; bin/gen_splash.py:208-211; bin/release.sh:302; bin/gtach-preflight.sh:222"
      description: >-
        [G08] Script defects. deploy.sh stops the service, then transfers
        files under set -e, so a failed scp leaves the Pi with no running
        service; it starts the service and then reboots immediately; its
        remote commands interpolate client-side variables unquoted (SC2029).
        pull_logs.sh deletes local logs before an scp whose `*.log.*` glob
        fails when no rotated log exists. gen_splash.py hard-codes a macOS
        FreeCAD font path. release.sh lets gh create the tag on the remote
        default branch, which need not match the locally built wheel.
        preflight installs with --no-deps, so an update that adds a
        dependency fails at import and is rolled back.
    - location: "bin/pi-install.sh:47-48,199-204,260-266"
      description: >-
        [G09] The `curl | sudo bash` provisioning downloads the boot overlay,
        binaries and units by tag with no checksum; trust rests on GitHub TLS
        alone. Record the assumption, or publish checksums with releases.
    - location: "src/gtach/comm/transport.py:474-480"
      description: >-
        [X03] Reconnect path traced end to end. The sequence works: 5 × 1 s
        timeouts trigger drop_link; the supervisor polls at 1 s, waits 5 s
        and reconnects (RFCOMM socket closed on failure); the OBD thread runs
        a full re-init; the display recovers after two samples. Residual gaps:
        the peer-close branch records no cause and leaks the handle (A04);
        serial never drops (A06); TCP and serial causes are mislabelled (A05);
        init accepts 'NO DATA' (A02).
    - location: "src/gtach/assets/engine_profiles.yaml:21; src/gtach/display/manager.py:558,581; src/gtach/comm/pairing.py:51-62"
      description: >-
        [X04] Configuration keys versus usage. `default_profile` is read by no
        code: the 'abarth_595_turismo' default is hard-coded three times.
        DisplayManager reads engine_profile as a top-level key of its own
        file, whereas config/config.yaml nests it under display:.
        --obd-host, --obd-port and --serial-port exist only as CLI flags.
        bluetooth.pairing.* is read but never defined or written. See E01.

metrics:
  items_audited: 90
  findings_total: 83
  findings_by_severity:
    critical: 1
    high: 5
    medium: 29
    low: 48

recommendations:
  - "Promote D01, A01/B02, B01, D02, D03 and G01 to issue T-Docs via P03 (P02.6); D01 first."
  - "Adopt a no-callback-under-lock rule and document the lock order (X01); fix D01, D03, D06, C04 and B01 under it."
  - "Restore field diagnosability before further hardware debugging: keep WARNING-and-above logging always on (B04) and add exc_info=True to every broad handler (A11)."
  - "Unify configuration into one file, schema and owner, injected into DisplayManager, the transports and pairing (E01, G07, X04)."
  - "Declare and install the touch stack (hyperpixel2r, RPi.GPIO via [pi]) and log the mock fallback at ERROR on a Pi (G01)."
  - "Add SimTransport-based lifecycle and regression tests (F01, F02) before or together with the fixes above."
  - "Make OBDProtocol shutdown- and restart-safe and fix SimTransport.is_connected (A01/B02, B01)."
  - "Decide the line-length limit and apply black, isort and flake8 once in a dedicated change (G05), then address mypy in scope (465 errors)."
  - "Remove dead code (A15, C11, C12, D07, D08, D09, E04, E07) and stop packaging the backup files (G06)."
  - "Harden gtach.service: non-root user or sandbox directives, and TimeoutStopSec (G02, G03)."

traceability:
  design_refs:
    - ""
  issue_refs:
    - ""
  related_audits:
    - audit_ref: "audit-b4e8c012"
      relationship: "follow_up"
    - audit_ref: "audit-2f612d17"
      relationship: "supersedes"
    - audit_ref: "audit-splash-hang-debug-session-state-report"
      relationship: "follow_up"
    - audit_ref: "audit-ui-navigation-logic-report"
      relationship: "follow_up"

notes: >-
  Static, strategic audit of commit 2d6bb0cea13ed9d715ff1130555d328255be1aee.
  Every in-scope file was read in full. Tooling ran on Python 3.13 in a Linux
  container. Findings marked (suspected) need hardware or emulator
  confirmation; see Section 5.

version_history:
  - version: "1.0"
    date: "2026-10-07"
    changes:
      - "Initial audit"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t08_audit"
```

[Return to Table of Contents](<#table of contents>)

---

## 4. Coverage Record

One entry per in-scope file. "N/A" lists the criteria judged not applicable (1 correctness, 2 concurrency, 3 error handling, 4 resources, 5 security, 6 hardware abstraction, 7 type safety, 8 dead code, 9 test coverage, 10 configuration). "Cov" is pytest line coverage. Every file listed was reviewed in full, including those with zero findings.

### 4.1 src/gtach/ — top level and assets

| File | Lines | Cov | Purpose | Main symbols | N/A | Findings |
|---|---|---|---|---|---|---|
| `__init__.py` | 20 | 100% | Package exports, version | `__version__`, re-exports | 2,3,4,5,6 | 1 (B11) |
| `__main__.py` | 14 | 0% | `python -m gtach` entry | `main` | 1-6,10 | 0 |
| `app.py` | 592 | 43% | Application controller and lifecycle | `GTachApplication.start/_start_normal_mode/_start_setup_mode/_start_obd/_re_enter_setup/shutdown/_watchdog_shutdown/_on_reset_pi` | 6 | 6 (A01, B03, B04, B09, B10, B12) |
| `main.py` | 344 | 63% | CLI, logging, stack dumps | `setup_logging`, `enable_stack_dumps`, `disable_stack_dumps`, `parse_arguments`, `main` | 2,6 | 3 (B04, B10, E02) |
| `assets/engine_profiles.yaml` | 49 | n/a | RPM band profiles | `profiles`, `default_profile` | 2-9 | 1 (X04) |

### 4.2 src/gtach/comm/

| File | Lines | Cov | Purpose | Main symbols | N/A | Findings |
|---|---|---|---|---|---|---|
| `comm/__init__.py` | 28 | 100% | Exports | — | 1-6,10 | 0 |
| `comm/bluetooth.py` | 0 | n/a | Empty stub | — | all except 8 | 1 (A15) |
| `comm/device_store.py` | 264 | 34% | Paired-device persistence | `DeviceStore` | 6 | 3 (A09, A10, A11) |
| `comm/models.py` | 82 | 33% | Comm-layer device model | `BluetoothDevice` | 2-6 | 2 (A14, A15) |
| `comm/obd.py` | 184 | 20% | ELM327 protocol thread | `OBDProtocol._protocol_loop/_initialize_protocol/_request_rpm`, `OBDResponse` | 5,6 | 5 (A01, A02, A03, A11, A19) |
| `comm/pairing.py` | 603 | 10% | Bluetooth discovery and pairing | `BluetoothPairing` | 6 | 6 (A07, A08, A11, A14, A15, A17) |
| `comm/rfcomm.py` | 80 | 74% | RFCOMM transport | `RFCOMMTransport` | 2,5,6 | 1 (A15) |
| `comm/serial_transport.py` | 182 | 21% | Serial transport and port probe | `SerialTransport._discover_port/_probe_port` | 2,5,6 | 2 (A05, A06) |
| `comm/sim_bluetooth.py` | 255 | 0% | Simulated pairing | `SimBluetoothPairing` | 5,6 | 2 (A09, A13) |
| `comm/sim_transport.py` | 146 | 0% | Simulated transport | `SimTransport` | 5,6 | 1 (A01) |
| `comm/system_bluetooth.py` | 273 | 21% | bluetoothctl/hcitool backend | `SystemBluetoothManager`, `BluetoothSocket`, `discover_devices` | 6 | 4 (A07, A11, A15, A18) |
| `comm/tcp_transport.py` | 59 | 50% | TCP transport | `TCPTransport` | 2,6 | 3 (A05, A12, A15) |
| `comm/transport.py` | 681 | 78% | Transport base, reconnect supervisor, factory | `OBDTransport.connect/send_command/drop_link/reconnect_indefinitely`, `select_transport` | 6 | 5 (A04, A05, A11, A16, X03) |

### 4.3 src/gtach/core/

| File | Lines | Cov | Purpose | Main symbols | N/A | Findings |
|---|---|---|---|---|---|---|
| `core/__init__.py` | 17 | 100% | Exports | — | 1-6,10 | 0 |
| `core/thread.py` | 419 | 50% | Thread registry, restart, shutdown | `ThreadManager`, `ThreadInfo`, `ThreadStatus` | 5,6,10 | 6 (B01, B03, B05, B06, B07, B08) |
| `core/watchdog.py` | 431 | 49% | Heartbeat watchdog and escalation | `WatchdogMonitor` | 5,6,10 | 2 (B01, B07) |

### 4.4 src/gtach/display/ — top level

| File | Lines | Cov | Purpose | Main symbols | N/A | Findings |
|---|---|---|---|---|---|---|
| `display/__init__.py` | 39 | 65% | Exports, guarded TouchHandler import | — | 1-5,10 | 0 |
| `display/async_operations.py` | 356 | 24% | Worker pool for setup operations | `AsyncOperationManager`, `get_async_manager` | 5,6,10 | 1 (D03) |
| `display/manager.py` | 2688 | 15% | Display loop, modes, gauge, OPTIONS, DISCONNECTED | `DisplayManager` | 5,6 | 8 (A11, C03, C05, C10, C12, C14, C15, E01) |
| `display/models.py` | 227 | 86% | Display models and palettes | `RPMBands`, `DisplayMode`, `DisplayConfig`, `Palette` | 2-6 | 1 (C17) |
| `display/navigation_gestures.py` | 524 | 0% | Gesture handler (mostly dead) | `NavigationGestureHandler` | 5,6,10 | 1 (C11) |
| `display/setup.py` | 848 | 22% | Setup-mode UI | `SetupDisplayManager` | 5,6 | 5 (C01, C02, C06, C08, D01) |
| `display/setup_models.py` | 102 | 91% | Setup data models | `SetupState`, `BluetoothDevice`, `SetupScreen`, `SetupAction` | 2-6,10 | 1 (A14) |
| `display/splash.py` | 715 | 11% | Splash screen | `SplashScreen` | 5,6 | 2 (C13, C16) |
| `display/touch.py` | 478 | 28% | Touch-event processing and dispatch | `TouchHandler` | 5,10 | 4 (C03, C12, C14, C16) |
| `display/touch_interface.py` | 1007 | 22% | Touch hardware abstraction | `HyperPixelTouchInterface`, `MockTouchInterface`, `create_touch_interface` | 10 | 5 (C04, C12, C14, C16, G01) |
| `display/typography.py` | 943 | 42% | Fonts and button rendering | `FontManager`, `ButtonRenderer`, `TypographyConstants` | 2,5,6,10 | 3 (C12, C15, D10) |

### 4.5 src/gtach/display/ — subfolders

| File | Lines | Cov | Purpose | Main symbols | N/A | Findings |
|---|---|---|---|---|---|---|
| `graphics/__init__.py` | 29 | 0% | Exports | — | 1-7,9,10 | 0 |
| `graphics/splash_graphics.py` | 584 | 0% | Splash drawing primitives | `draw_automotive_gauge` | 2,3,5,10 | 2 (D08, D10) |
| `input/__init__.py` | 23 | 100% | Exports | — | 1-7,9,10 | 0 |
| `input/interfaces.py` | 94 | 84% | Touch interfaces and enums | `TouchRegion`, `TouchAction`, `GestureType` | 1-5,10 | 1 (D10) |
| `input/touch_coordinator.py` | 598 | 11% | Touch regions and hit-testing | `TouchEventCoordinator` | 5,10 | 2 (D06, D10) |
| `performance/__init__.py` | 50 | 41% | Exports, legacy singleton | `get_performance_manager` | 1-6,10 | 1 (D09) |
| `performance/interfaces.py` | 138 | 79% | Metrics types | `PerformanceMetrics`, `PerformanceMonitorInterface` | 1-6,10 | 0 |
| `performance/monitor.py` | 563 | 12% | FPS and memory metrics | `PerformanceMonitor` | 5,6,10 | 1 (D10) |
| `rendering/__init__.py` | 22 | 100% | Exports | — | 1-7,9,10 | 0 |
| `rendering/engine.py` | 962 | 28% | Surfaces, framebuffer mmap, page flip | `DisplayRenderingEngine.write_to_framebuffer/_setup_page_flip/_pan_display/cleanup` | 10 | 3 (D02, D10, D11) |
| `rendering/interfaces.py` | 118 | 77% | Rendering interface | `RenderingEngineInterface`, `RenderTarget` | 1-6,10 | 1 (D10) |
| `setup_components/__init__.py` | 7 | 100% | Package docstring | — | all | 0 |
| `setup_components/bluetooth/__init__.py` | 7 | 100% | Package docstring | — | all | 0 |
| `setup_components/bluetooth/interface.py` | 436 | 6% | Setup Bluetooth operations | `BluetoothSetupInterface` | 10 | 2 (D03, D05) |
| `setup_components/layout/__init__.py` | 7 | 100% | Package docstring | — | all | 0 |
| `setup_components/layout/circular_positioning.py` | 572 | 38% | Slot geometry | `CircularPositioningEngine` | 2,3,5,6,10 | 1 (D08) |
| `setup_components/rendering/__init__.py` | 7 | 100% | Package docstring | — | all | 0 |
| `setup_components/rendering/device_surfaces.py` | 556 | 41% | Device slot surfaces | `DeviceSurfaceRenderer` | 5,6,10 | 1 (D08) |
| `setup_components/state/__init__.py` | 7 | 100% | Package docstring | — | all | 0 |
| `setup_components/state/coordinator.py` | 512 | 32% | Setup state machine | `SetupStateCoordinator` | 5,6,10 | 3 (D01, D04, D07) |

### 4.6 src/gtach/utils/

| File | Lines | Cov | Purpose | Main symbols | N/A | Findings |
|---|---|---|---|---|---|---|
| `utils/__init__.py` | 22 | 100% | Exports | — | 1-7,9,10 | 0 |
| `utils/ack_state.py` | 239 | 17% | Acknowledgement persistence | `AcknowledgementStateManager` | 2,5,6 | 1 (E07) |
| `utils/config.py` | 1605 | 32% | ConfigManager, schema, RWLock, engine profiles | `ConfigManager`, `OBDConfig`, `RWLock`, `load_engine_profile` | 6 | 3 (E01, E02, E04) |
| `utils/dependencies.py` | 680 | 17% | Dependency validator | `DependencyValidator`, `validate_dependencies` | 2,4 | 1 (E05) |
| `utils/home.py` | 276 | 58% | Home and path resolution | `OBDIIHome`, `get_config_file` | 2,4,5,6 | 2 (E01, E08) |
| `utils/pi_reset.py` | 116 | 100% | Operator-initiated reboot | `reboot_device` | 2,4,6,8,10 | 0 |
| `utils/platform.py` | 1112 | 17% | Platform detection | `PlatformDetector`, `get_platform_type`, `is_raspberry_pi` | 4,10 | 1 (E07) |
| `utils/terminal.py` | 86 | 21% | Terminal restoration | `TerminalRestorer` | 2,9,10 | 1 (E03) |
| `utils/updater.py` | 106 | 0% | Update discovery and staging | `find_available_update`, `stage_pending` | 2,6 | 1 (E06) |

### 4.7 tests/

| File | Lines | Purpose | Tests | N/A | Findings |
|---|---|---|---|---|---|
| `tests/conftest.py` | 27 | SDL dummy driver, shared timeout | 0 | 1-8,10 | 1 (F05) |
| `tests/display/rendering/test_engine.py` | 191 | Framebuffer vertical offset | 8 | 2,5,6,10 | 1 (F02) |
| `tests/test_connect_error_classification.py` | 778 | Connect-error causes, socket close | 50 | 6,10 | 2 (F02, F03) |
| `tests/test_device_list_focus.py` | 601 | DEVICE_LIST slots and focus | 51 | 5,6,10 | 1 (F04) |
| `tests/test_disconnected_screen.py` | 524 | DISCONNECTED screen | 36 | 5,6,10 | 1 (F03) |
| `tests/test_link_loss_recovery.py` | 451 | Dead-link detection, reconnect loop | 23 | 5,6,10 | 2 (F02, F03) |
| `tests/test_pi_reset.py` | 427 | Reboot path containment | 24 | 6,10 | 1 (F06) |
| `tests/test_stack_dump_toggle.py` | 369 | Stack-dump arming | 22 | 5,6,10 | 2 (F03, F05) |
| `tests/test_stacks_log_rotation.py` | 326 | stacks.log headers and rotation | 19 | 5,6,10 | 1 (F03) |
| `tests/test_touch_dispatch.py` | 270 | Short-press dispatch | 15 | 5,6,10 | 1 (F03) |
| `tests/test_transport_heartbeat.py` | 103 | Reconnect heartbeat hook | 5 | 4,5,6,10 | 0 |
| `tests/test_watchdog_process_termination.py` | 222 | Watchdog exit path, advisory tier | 10 | 5,6 | 1 (F05) |
| `tests/utils/test_rwlock.py` | 488 | RWLock notification and exclusivity | 11 | 5,6,10 | 1 (F03) |

### 4.8 bin/, config/, pyproject.toml

| File | Lines | Purpose | N/A | Findings |
|---|---|---|---|---|
| `bin/build.sh` | 114 | Version bump and wheel build | 2,6,9 | 1 (G06) |
| `bin/collect-pi-config.sh` | 79 | Read-only Pi diagnostic | 2,4,6,9 | 0 |
| `bin/deploy.sh` | 90 | Build, transfer, install, reboot | 2,6,9 | 1 (G08) |
| `bin/gen_splash.py` | 77 | Boot splash generator | 2,5,6,9 | 1 (G08) |
| `bin/gtach-boot-splash.service` | 44 | One-shot framebuffer splash | 2,9 | 0 |
| `bin/gtach-preflight.sh` | 73 | Rollback and pending-wheel install | 2,6,9 | 3 (E06, G03, G08) |
| `bin/gtach.service` | 17 | Main systemd unit | 2,9 | 2 (G02, G03) |
| `bin/install.sh` | 292 | Developer install on Pi | 2,9 | 1 (G01) |
| `bin/pi-install.sh` | 298 | Release install from GitHub | 2,9 | 2 (G01, G09) |
| `bin/pull_logs.sh` | 27 | Fetch logs from Pi | 2,6,9 | 1 (G08) |
| `bin/quiet-boot.sh` | 228 | Boot-output suppression | 2,6,9 | 0 |
| `bin/release.sh` | 82 | GitHub release | 2,6,9 | 1 (G08) |
| `bin/vendor-hyperpixel2r.sh` | 32 | One-time driver extraction | 2,6,9 | 0 |
| `config/config.yaml` | 51 | ConfigManager schema instance | 1-9 | 2 (E01, G07) |
| `config/devices.yaml` | 5 | Device store seed | 1-9 | 1 (G07) |
| `pyproject.toml` | 144 | Packaging, tool configuration | 1-4,9 | 4 (G01, G04, G05, G06) |

**Final check:** 90 of 90 checklist files have an entry above (61 under `src/gtach/`, 13 under `tests/`, 13 under `bin/`, 2 under `config/`, plus `pyproject.toml`). No file was sampled or skipped.

[Return to Table of Contents](<#table of contents>)

---

## 5. Limitations

This audit is static. None of the following could be exercised: the Pi Zero 2W, the HyperPixel 2.1 Round panel and its touch controller, `/dev/fb0`, an ELM327 adapter (Bluetooth or serial), `gtach.local` or `ELM327-Emulator.local`, systemd, or Python 3.9. Items that need runtime verification:

| Finding | What to verify | How |
|---|---|---|
| D01 | Frequency of the setup-mode deadlock | On the Pi, arm stack dumps (OPTIONS → Debug: On) and tap Start Setup and Cancel on WELCOME repeatedly. A hang shows the display and touch threads blocked in `setup.py` lock acquisitions in `stacks.log`. Alternatively, script `MockTouchInterface.simulate_tap` against a headless DisplayManager in a loop. |
| G01 | Touch library on a fresh install | Provision a fresh SD card with `pi-install.sh` and with `deploy.sh`, then grep `/opt/gtach/start.log` for "Using mock HyperPixel implementation" and run `/opt/gtach/venv/bin/pip show hyperpixel2r RPi.GPIO`. |
| D02 | Panel freeze after a pan failure | Inject a failing `_pan_display` (monkeypatch to return False after N frames) on the Pi and observe the panel. Confirm whether the driver ever returns errors from `FBIOPAN_DISPLAY`. |
| A01/B02 | Exit hang with sim transports | Run `gtach --transport simtcp` and send SIGTERM. Measure the time to exit; expect it to hang until killed. |
| B01 | Hard-recovery behaviour | Stall the OBD thread (for example, block `send_command` in a test double) for more than 30 s and observe the restart log and RPM recovery. |
| D03, D06, C02, C04 | UI stalls | Time the display-thread heartbeat gap during pairing verification and DISCONNECTED → Setup, using the emulator. |
| A02 | 'NO DATA' accepted as success | Use the ELM327 emulator with the vehicle "off" (0100 → NO DATA) and check whether init reports success. |
| A06 | Serial dead peer | Use a USB-serial ELM327 and power the adapter off without unplugging the cable. |
| A07, A08, A17 | Pairing timeouts on the system backend | Pair against an absent MAC on the Pi and time `connect()`. Hang `hcitool` (for example, `rfkill block`) during discovery and watch the executor. |
| A10 | devices.yaml durability | Cut power during a pairing save, repeated on the target filesystem. |
| B04 | Lost runtime errors | Force an error after startup (unplug the adapter) with debug off and confirm nothing reaches any log file. |
| C05 | Gauge saturation | Select `generic_na_4cyl` and drive the simulator above 7000 RPM. |
| E01 | Effective configuration on the Pi | On the device, inspect `/root/.local/share/obdii/config/config.yaml`, `/opt/gtach/config.yaml` and `/opt/gtach/config/devices.yaml`; confirm which one each component reads and that `fps_limit: 30` has no effect. |
| G02, G03 | Service behaviour | `systemd-analyze security gtach`; force three start failures within 60 s and check `systemctl status`. |
| X02 | Shutdown duration | `time systemctl stop gtach` during an active discovery and while connected. |

Other limitations:

- Performance on the Pi Zero 2W (60 fps rendering, per-frame YAML reads in C06, 921,600-byte framebuffer writes per frame) was assessed by reasoning only.
- pip-audit covered the dev-host resolution of unpinned dependencies, not the versions installed in the Pi's venv.
- mypy, flake8 and coverage figures were produced on Python 3.13. Python 3.9-specific typing behaviour may differ.
- `bin/vendor/` and `docs/` were excluded. They were consulted only to confirm G01's provenance claims, not reviewed.
- The auditor field records the strategic-mode role ("planner") and the tool rather than a model identifier.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial audit |

---

Copyright (c) 2026 William Watson. MIT License.
