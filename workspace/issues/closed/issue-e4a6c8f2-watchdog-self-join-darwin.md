Created: 2026 May 06

# Issue: Watchdog stop() Self-Join RuntimeError on Darwin Shutdown

---

```yaml
issue_info:
  id: "issue-e4a6c8f2"
  title: "WatchdogMonitor.stop() raises RuntimeError: cannot join current thread on Darwin"
  date: "2026-05-06"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "user_report"
  test_ref: ""
  description: >
    macOS visual test log shows RuntimeError during shutdown. WatchdogMonitor fires
    its own graceful shutdown callback, which calls GTachApplication.shutdown(),
    which calls self._watchdog.stop(), which calls self._thread.join(). Since the
    watchdog is calling this from its own monitoring thread, threading.join() raises
    RuntimeError: cannot join current thread.

affected_scope:
  components:
    - name: "WatchdogMonitor.stop"
      file_path: "src/gtach/core/watchdog.py"
  designs: []
  version: "0.2.21"

reproduction:
  prerequisites: "macOS; GTach running with --macos --debug"
  steps:
    - "Run: python -m gtach --macos --debug"
    - "Wait ~42s without interaction (watchdog critical timeout)"
    - "Observe log for RuntimeError"
  frequency: "always on Darwin watchdog-triggered shutdown"
  reproducibility_conditions: "Watchdog fires its own shutdown callback on Darwin"
  preconditions: ""
  test_data: ""
  error_output: >
    2026-05-06 11:39:14,977 WatchdogMonitor CRITICAL Initiating graceful shutdown
    2026-05-06 11:39:14,977 WatchdogMonitor INFO Calling graceful shutdown callback
    2026-05-06 11:39:14,978 gtach.app ERROR Shutdown error: cannot join current thread
    RuntimeError: cannot join current thread
      File "src/gtach/app.py", line 168, in shutdown
        self._watchdog.stop()
      File "src/gtach/core/watchdog.py", line 116, in stop
        self._thread.join(timeout=5.0)

behavior:
  expected: "Shutdown completes cleanly without RuntimeError"
  actual: "RuntimeError logged; watchdog thread cannot join itself; shutdown continues but with error"
  impact: >
    Shutdown is unclean on Darwin. Error is logged but non-fatal in practice.
    However it masks legitimate shutdown errors and leaves threads in undefined state.
  workaround: "None — occurs on every watchdog-triggered shutdown on macOS"

environment:
  python_version: "3.11"
  os: "macOS (Apple Silicon)"
  dependencies: []
  domain: "core"

analysis:
  root_cause: >
    WatchdogMonitor._initiate_graceful_shutdown() calls self.shutdown_callback()
    from within the watchdog's own monitoring thread (_monitor_loop). That callback
    calls GTachApplication.shutdown() -> self._watchdog.stop() -> self._thread.join().
    threading.Thread.join() raises RuntimeError if the calling thread is the thread
    being joined. This is a standard Python threading constraint.
  technical_notes: >
    Fix: in WatchdogMonitor.stop(), guard the join call:
      if threading.current_thread() is not self._thread:
          self._thread.join(timeout=5.0)
          if self._thread.is_alive():
              self.logger.warning("Watchdog monitor thread did not stop cleanly")
    This is a §1.4.12 trivial change: single function, net delta ~3 lines,
    no interface change, unambiguous.
  related_issues:
    - issue_ref: "issue-c3e5a7b9"
      relationship: "related — both are Darwin shutdown path defects"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial issue — discovered from Mac visual test log |

---

Copyright (c) 2026 William Watson. MIT License.
