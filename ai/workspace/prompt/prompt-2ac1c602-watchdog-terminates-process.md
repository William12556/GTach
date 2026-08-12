Created: 2026 August 12

# Prompt: Watchdog Critical-Thread Recovery Must Terminate the Process

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-2ac1c602"
  task_type: "debug"
  source_ref: "change-2ac1c602"
  target_profile: "claude_code"
  date: "2026-08-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-2ac1c602"
    change_iteration: 1

context:
  purpose: >
    Make WatchdogMonitor's terminal recovery action actually end the
    process, so systemd's Restart=always relaunches GTach instead of
    leaving a torn-down but living process with a dead screen. Make the
    'transport' thread genuinely monitored rather than merely named.
    Direct faulthandler's periodic stack dumps to an app-owned log file
    so the cause of the underlying process-wide thread stall becomes
    recoverable on the next reproduction.
  integration: >
    Five localised edits across four existing files: src/gtach/app.py,
    src/gtach/core/watchdog.py, src/gtach/comm/transport.py and
    src/gtach/main.py. No new modules. No new third-party dependencies.
    bin/gtach.service is correct as configured and must NOT be changed.
  knowledge_references:
    - "ai/workspace/issues/issue-2ac1c602-display-blank-no-connection.md"
    - "ai/workspace/change/change-2ac1c602-watchdog-terminates-process.md"
  constraints:
    - "Do not modify bin/gtach.service."
    - "Do not modify src/gtach/comm/rfcomm.py. The blocking connect() is out of scope."
    - "Do not add an import of gtach.core (or any core module) into gtach.comm."
    - "Do not attempt to diagnose or fix the ~52 s process-wide thread stall. Edit E makes it observable; that is the whole of the scope."
    - "Do not register the main thread with ThreadManager."
    - "GTachApplication.shutdown() must continue to run at most once per process lifetime."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: >
    Apply edits A-E exactly as specified, then add the unit tests in the
    testing section. Each edit is described with the current code and
    the required result.
  requirements:
    functional:
      - "A WatchdogMonitor critical-thread timeout causes the interpreter to exit."
      - "Component teardown for that path runs once, from GTachApplication.run()'s finally block, on the main thread."
      - "If orderly exit has not completed 20.0 s after the timeout, the process force-exits."
      - "The 'transport' thread is registered with ThreadManager and emits heartbeats."
      - "A thread in WatchdogMonitor.advisory_threads can produce warnings but can never trigger recovery or shutdown."
      - "Under --debug, faulthandler writes stack dumps and fatal tracebacks to /opt/gtach/stacks.log."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Main loop exits within 1.0 s of the watchdog callback returning"
      metric: "time"
    - target: "Process exits within 20.0 s of the critical timeout, unconditionally"
      metric: "time"

design:
  architecture: >
    Separation of signalling from teardown. The watchdog thread signals;
    the main thread tears down; a daemon timer bounds the whole
    sequence. The watchdog gains a third monitoring tier — advisory —
    below critical, for threads whose long blocking calls are expected
    behaviour rather than faults.
  components:
    - name: "EDIT A — src/gtach/main.py: faulthandler to an app-owned log"
      type: "function"
      purpose: "Relocate faulthandler arming from app.py and target a file alongside start.log and debug.log."
      logic:
        - "Add `import faulthandler` to the module imports."
        - "After the existing `_DEBUG_LOG = '/opt/gtach/debug.log'` line, add:  _STACKS_LOG = '/opt/gtach/stacks.log'"
        - "Beside the existing `_start_handler` / `_debug_handler` module-level references, add:  _stacks_file = None   # kept referenced so faulthandler's fd stays open"
        - "Inside setup_logging(), add `global _stacks_file` to the existing `global _start_handler, _debug_handler` statement."
        - "At the END of setup_logging(), add a guarded block: if debug is truthy, open _STACKS_LOG in mode 'a', buffering=1, encoding='utf-8'; assign to _stacks_file; call faulthandler.enable(file=_stacks_file); call faulthandler.dump_traceback_later(15, repeat=True, file=_stacks_file)."
        - "Wrap that block in try/except OSError, printing a warning to sys.stderr in the same style as the existing _START_LOG handler, and leaving _stacks_file as None on failure."
        - "Add a comment recording WHY: faulthandler's timer runs in C and is unaffected by a Python-level thread stall, so its dumps land inside a freeze; previously they went to sys.stderr, which under systemd is the journal and not the app-owned log set."
    - name: "EDIT B — src/gtach/app.py: remove the relocated faulthandler block"
      type: "class"
      purpose: "Avoid arming faulthandler twice and remove a comment that is false under systemd."
      logic:
        - "In GTachApplication.__init__, DELETE the block currently at lines 38-45: the comment beginning '# Diagnostic: when debugging, dump all thread stacks to stderr every' through and including the `faulthandler.dump_traceback_later(...)` call and its local `import faulthandler` / `import sys` lines."
        - "self._debug = debug is retained; only the faulthandler block goes."
    - name: "EDIT C — src/gtach/app.py: terminating watchdog callback"
      type: "class"
      purpose: "Make the watchdog's terminal recovery action end the process."
      logic:
        - "Add `import os` to the module imports."
        - "Add a class-level constant on GTachApplication:  _EXIT_BACKSTOP_SEC: float = 20.0"
        - "In __init__, MOVE `self._stop_event = threading.Event()` (currently at line 66) so it is created BEFORE the `self._watchdog = WatchdogMonitor(...)` construction. The attribute must exist before the callback is bound."
        - "Change the WatchdogMonitor construction argument from `shutdown_callback=self.shutdown` to `shutdown_callback=self._watchdog_shutdown`. Leave check_interval, warning_timeout, recovery_timeout and critical_timeout unchanged."
        - "Add method `_watchdog_shutdown(self) -> None`. It logs at CRITICAL that the watchdog has requested process termination; sets self._stop_event; then constructs threading.Timer(self._EXIT_BACKSTOP_SEC, self._force_exit), sets timer.daemon = True, and starts it. It must NOT call self.shutdown()."
        - "Add method `_force_exit(self) -> None`. It logs at CRITICAL that orderly exit did not complete within _EXIT_BACKSTOP_SEC seconds, calls logging.shutdown() inside a bare try/except, then calls os._exit(1)."
        - "Docstring on _watchdog_shutdown must record the ordering decision: teardown is left to run()'s finally block, which is idempotent via _shutdown_called, so that shutdown() is never invoked from the watchdog thread and the recovery path does not depend on WatchdogMonitor.stop()'s self-join guard."
    - name: "EDIT D — src/gtach/app.py and src/gtach/comm/transport.py: register and heartbeat the transport thread"
      type: "function"
      purpose: "Make the 'transport' entry in the watchdog's thread set correspond to a thread it can actually see."
      logic:
        - "In src/gtach/comm/transport.py, add Callable to the existing `from typing import Optional` import."
        - "Change the signature of OBDTransport.reconnect_indefinitely to:  def reconnect_indefinitely(self, retry_delay: float = 5.0, heartbeat: Optional[Callable[[], None]] = None) -> None:"
        - "Document the new parameter in the existing Args docstring block."
        - "Inside the `while not self._shutdown.is_set():` loop, call heartbeat() if it is not None: once at the top of the loop body, and once immediately after the `if self.connect():` test resolves — on both the True branch (before `return`) and the False branch (before the warning log)."
        - "Guard each heartbeat call so a raising callback cannot break the reconnect loop: wrap in try/except Exception and log at DEBUG with exc_info=True."
        - "In src/gtach/app.py, there are TWO places that start this thread: _start_normal_mode (currently line 338) and _start_obd (currently lines 301-303). Edit BOTH identically."
        - "At each site, build the thread as: threading.Thread(target=self._transport.reconnect_indefinitely, kwargs={'heartbeat': lambda: self._thread_manager.update_heartbeat('transport')}, name='transport', daemon=True)"
        - "At each site, call self._thread_manager.register_thread('transport', transport_thread) BEFORE transport_thread.start(), matching the existing registration order used for the display thread."
        - "Add a comment at each site noting that registration is what makes the thread visible to WatchdogMonitor, which iterates thread_manager.threads only."
    - name: "EDIT E — src/gtach/core/watchdog.py: advisory monitoring tier"
      type: "class"
      purpose: "Observe the transport thread without allowing an expected long blocking connect() to restart the application."
      logic:
        - "Change `self.critical_threads = {'display', 'transport', 'main'}` to `self.critical_threads = {'display'}`."
        - "Immediately below it add:  self.advisory_threads = {'transport'}"
        - "Comment both: 'main' was never registered with ThreadManager and so was never monitored; 'transport' is now registered but is advisory because a blocking connect() lasting tens of seconds is expected transport behaviour, not a fault, and must not be able to trigger a restart."
        - "In _check_thread_health phase 1, after `level` is determined and BEFORE `pending.append(...)`, clamp it:  if name in self.advisory_threads and level in ('critical', 'recovery'): level = 'warning'"
        - "Do not alter the lock discipline established by change-5a9dc15e: the clamp goes inside the existing `with self.thread_manager._lock:` traversal, which performs no blocking call, and phase 2 dispatch is unchanged."

data_schema:
  entities: []

error_handling:
  strategy: >
    Diagnostic paths must never destabilise the runtime paths they
    observe. Every new call that crosses a component boundary — the
    heartbeat callback, the stacks.log open, logging.shutdown() in the
    force-exit path — is individually guarded so its failure degrades
    diagnostics rather than the application.
  exceptions:
    - exception: "OSError"
      condition: "Opening /opt/gtach/stacks.log fails (permissions, full filesystem)."
      handling: "Print a warning to sys.stderr in the style of the existing _START_LOG handler; leave _stacks_file as None; continue startup."
    - exception: "Exception"
      condition: "The heartbeat callable raises inside reconnect_indefinitely."
      handling: "Log at DEBUG with exc_info=True and continue the reconnect loop. A failed heartbeat must not stop reconnection."
    - exception: "Exception"
      condition: "logging.shutdown() raises during _force_exit."
      handling: "Swallow it. os._exit(1) must be reached unconditionally."
  logging:
    level: "CRITICAL"
    format: "Existing _LOG_FORMAT in main.py; no format change."

testing:
  unit_tests:
    - scenario: "Construct GTachApplication and call _watchdog_shutdown directly."
      expected: "_stop_event.is_set() is True on return, and shutdown() has NOT been called."
    - scenario: "Run GTachApplication.run() in a thread with start() stubbed out, then call _watchdog_shutdown from the test thread."
      expected: "run() returns within 1.0 s; shutdown() has been called exactly once."
    - scenario: "Call GTachApplication.shutdown() twice in succession."
      expected: "The second call returns immediately; teardown side effects occur exactly once."
    - scenario: "WatchdogMonitor with a registered 'transport' thread whose last_heartbeat is aged beyond critical_timeout; run one _check_thread_health cycle."
      expected: "A warning is logged for 'transport'; _initiate_graceful_shutdown is not called; recovery_stats.shutdown_triggers is 0 and hard_recovery_attempts is 0."
    - scenario: "WatchdogMonitor with a registered 'display' thread whose last_heartbeat is aged beyond critical_timeout; run one _check_thread_health cycle."
      expected: "_initiate_graceful_shutdown is called and the shutdown callback runs."
    - scenario: "reconnect_indefinitely called with a heartbeat callable against a transport whose connect() returns False once, then True."
      expected: "The callable is invoked on both iterations; the method returns after the successful connect."
    - scenario: "reconnect_indefinitely called with a heartbeat callable that raises on every invocation."
      expected: "The reconnect loop still completes; no exception propagates out of reconnect_indefinitely."
    - scenario: "reconnect_indefinitely called with no heartbeat argument."
      expected: "Behaviour is unchanged from before this prompt; no exception."
  edge_cases:
    - "_watchdog_shutdown invoked twice — WatchdogMonitor._shutdown_initiated already guards this, but the second call must remain harmless."
    - "_watchdog_shutdown invoked before run() has entered its loop — _stop_event is already constructed by EDIT C's reordering, so the loop must exit on its first test."
    - "register_thread('transport', ...) called when a stale 'transport' entry is still RUNNING — ThreadManager logs a warning and returns; the reconnect loop must still function."
    - "Backstop timer still pending when the process exits normally — it is a daemon thread, so it must not delay interpreter shutdown."
  validation:
    - "pytest tests/ passes."
    - "python -c \"import ast; ast.parse(open('src/gtach/app.py').read())\" for each edited file."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Edit the existing files in place. Do not create new modules."
  files:
    - path: "src/gtach/main.py"
      content: "EDIT A"
    - path: "src/gtach/app.py"
      content: "EDIT B, EDIT C, EDIT D (app.py half)"
    - path: "src/gtach/comm/transport.py"
      content: "EDIT D (transport.py half)"
    - path: "src/gtach/core/watchdog.py"
      content: "EDIT E"
    - path: "tests/test_watchdog_process_termination.py"
      content: "Unit tests for testing.unit_tests items 1-5"
    - path: "tests/test_transport_heartbeat.py"
      content: "Unit tests for testing.unit_tests items 6-8"

success_criteria:
  - "In src/gtach/app.py, the WatchdogMonitor construction passes shutdown_callback=self._watchdog_shutdown; grep -n 'shutdown_callback=self.shutdown' src/gtach/app.py returns no match."
  - "In src/gtach/app.py, self._stop_event is assigned on a line preceding the line assigning self._watchdog."
  - "GTachApplication._watchdog_shutdown exists, sets self._stop_event, starts a daemon threading.Timer targeting self._force_exit, and contains no call to self.shutdown()."
  - "GTachApplication._force_exit exists and calls os._exit(1)."
  - "GTachApplication._EXIT_BACKSTOP_SEC == 20.0."
  - "No executable occurrence of 'faulthandler' remains in src/gtach/app.py (searching src/ only; occurrences in comments, T-Docs and ai/ are out of scope)."
  - "src/gtach/main.py defines _STACKS_LOG = '/opt/gtach/stacks.log' and arms faulthandler.dump_traceback_later against it only when setup_logging's debug argument is truthy."
  - "OBDTransport.reconnect_indefinitely accepts a keyword parameter named heartbeat defaulting to None, and calling it with no heartbeat argument behaves as before."
  - "Both threading.Thread(... name='transport' ...) construction sites in src/gtach/app.py are preceded by a register_thread('transport', ...) call and pass a heartbeat binding."
  - "In src/gtach/core/watchdog.py, critical_threads == {'display'} and advisory_threads == {'transport'}."
  - "A thread named in advisory_threads whose heartbeat exceeds critical_timeout produces a warning and does not reach _handle_critical_timeout or _attempt_hard_recovery."
  - "No import of any gtach.core module appears in src/gtach/comm/transport.py."
  - "bin/gtach.service and src/gtach/comm/rfcomm.py are byte-identical to their pre-change state."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "app"
        path: "src/gtach/app.py"
      - name: "main"
        path: "src/gtach/main.py"
      - name: "watchdog"
        path: "src/gtach/core/watchdog.py"
      - name: "transport"
        path: "src/gtach/comm/transport.py"
    classes:
      - name: "GTachApplication"
        module: "gtach.app"
      - name: "WatchdogMonitor"
        module: "gtach.core.watchdog"
      - name: "ThreadManager"
        module: "gtach.core.thread"
      - name: "OBDTransport"
        module: "gtach.comm.transport"
    functions:
      - name: "_watchdog_shutdown"
        module: "gtach.app"
        signature: "(self) -> None"
      - name: "_force_exit"
        module: "gtach.app"
        signature: "(self) -> None"
      - name: "reconnect_indefinitely"
        module: "gtach.comm.transport"
        signature: "(self, retry_delay: float = 5.0, heartbeat: Optional[Callable[[], None]] = None) -> None"
      - name: "setup_logging"
        module: "gtach.main"
        signature: "(debug: bool = False) -> None"
      - name: "register_thread"
        module: "gtach.core.thread"
        signature: "(self, name: str, thread: threading.Thread, stop_func=None) -> None"
      - name: "update_heartbeat"
        module: "gtach.core.thread"
        signature: "(self, name: str) -> None"
    constants:
      - name: "_EXIT_BACKSTOP_SEC"
        module: "gtach.app"
        type: "float"
      - name: "_STACKS_LOG"
        module: "gtach.main"
        type: "str"
      - name: "advisory_threads"
        module: "gtach.core.watchdog"
        type: "set"

notes: >
  On-target verification is a human step and is not part of this prompt.
  After deployment to gtach.local, the two scenarios that close
  issue-2ac1c602 are: (1) start with no reachable ELM327 emulator or
  Bluetooth adapter, wait through one failed connect cycle, and confirm
  `systemctl status gtach` reports a NEW main PID and that
  `systemctl show gtach -p NRestarts` has incremented; (2) repeat with
  --debug and confirm /opt/gtach/stacks.log contains dumps timestamped
  inside the stall window listing every thread's stack.

  The second of those is the evidence needed to identify the cause of
  the ~52 s process-wide stall, which this prompt deliberately does not
  attempt to fix.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial prompt implementing change-2ac1c602 iteration 1. Five edits across app.py, main.py, watchdog.py and transport.py, plus two unit test modules. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
