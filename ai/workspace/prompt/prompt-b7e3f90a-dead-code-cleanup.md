prompt_info:
  id: "prompt-b7e3f90a"
  task_type: "refactor"
  source_ref: "change-b7e3f90a"
  date: "2026-06-18"
  iteration: 1
  coupled_docs:
    change_ref: "change-b7e3f90a"
    change_iteration: 1

context:
  purpose: >
    Remove approximately 5300 lines of confirmed dead code from src/gtach.
    Dead code was identified by static analysis documented in
    ai/workspace/report/dead-code-report.md.
  integration: >
    Pure removal — no new code, no interface changes. Active modules must
    continue to import and function identically after removal.
  constraints:
    - "Do not touch display/manager_backup.py or display/setup_original_backup.py"
    - "Do not modify any active module's public interface"
    - "Do not remove anything you cannot independently confirm is dead"
    - "The dead code report is a starting point — treat it as a hypothesis"

specification:
  description: >
    Verify and remove dead code items listed in the dead code report.
    Verification must precede every deletion. If verification is inconclusive,
    skip that item and note it.
  requirements:
    functional:
      - "Each item verified dead before removal"
      - "Active modules unchanged in behaviour"
      - "Import smoke test passes after all removals"
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "Use git rm for file deletions"
        - "No functional changes to retained code beyond removing dead constructs"

design:
  architecture: "Sequential verify-then-remove phases"
  components:
    - name: "Phase 1 — Dead files and packages"
      type: "deletion"
      purpose: "Remove seven dead files and two dead packages after independent verification"
      logic:
        - "For each candidate file/package: grep src/gtach recursively for the module name, class names, and any import of the file path"
        - "Confirm zero hits in active modules (exclude manager_backup.py and setup_original_backup.py from hit counts)"
        - "If confirmed dead: git rm the file or directory"
        - "Candidates: core/watchdog_enhanced.py, display/hardware_interface.py, display/ui_testing_framework.py, display/enhanced_touch_factory.py, display/performance.py, display/components/, utils/services/"
    - name: "Phase 2 — AsyncSyncBridge in core/thread.py"
      type: "modification"
      purpose: "Remove AsyncSyncBridge class and its references from ThreadManager"
      logic:
        - "Search for any call to async_bridge methods (set_event_loop, submit_async_task, send_message) outside of thread.py itself"
        - "Search for AsyncSyncBridge as a string literal (dynamic dispatch check)"
        - "If confirmed unused: remove the AsyncSyncBridge class definition entirely"
        - "Remove self.async_bridge = AsyncSyncBridge(...) from ThreadManager.__init__"
        - "Remove self.async_bridge.shutdown() from ThreadManager.shutdown"
    - name: "Phase 3 — Dead ThreadManager public API in core/thread.py"
      type: "modification"
      purpose: "Remove get_statistics, list_threads, get_thread_info, is_healthy methods"
      logic:
        - "For each method: grep src/gtach recursively for the method name as a call site"
        - "Also search as a string literal to catch getattr/dynamic dispatch"
        - "If confirmed no external callers: remove the method"
        - "_sync_timing context manager and _operation_count/_sync_overhead_start: remove after confirming all usages are only within the methods being removed in this phase"
    - name: "Phase 4 — Dead setup_logging group in utils/config.py"
      type: "modification"
      purpose: "Remove ConfigManager.setup_logging, _setup_production_logging, _setup_debug_logging, _log_pi_hardware_status"
      logic:
        - "Grep src/gtach for each method name as a call site"
        - "Also search as a string literal"
        - "Confirm logging is handled solely by main.py standalone setup_logging()"
        - "If confirmed dead: remove the four methods"
    - name: "Phase 5 — Unused font asset"
      type: "deletion"
      purpose: "Remove BebasNeue-Regular.ttf"
      logic:
        - "Grep src/gtach for 'BebasNeue' (case-insensitive)"
        - "If zero hits: git rm src/gtach/assets/fonts/BebasNeue-Regular.ttf"
    - name: "Phase 6 — Smoke test"
      type: "validation"
      purpose: "Confirm active modules import cleanly"
      logic:
        - "python -c 'import gtach' — must succeed without error"
        - "If any ImportError or NameError: identify the cause, restore the deleted item if necessary, and report"

deliverable:
  format_requirements:
    - "All deletions via git rm"
    - "In-file removals must produce syntactically valid Python"
    - "Do not alter any retained method signatures or docstrings"
  files:
    - path: "src/gtach/core/watchdog_enhanced.py"
      content: "delete"
    - path: "src/gtach/display/hardware_interface.py"
      content: "delete"
    - path: "src/gtach/display/ui_testing_framework.py"
      content: "delete"
    - path: "src/gtach/display/enhanced_touch_factory.py"
      content: "delete"
    - path: "src/gtach/display/performance.py"
      content: "delete"
    - path: "src/gtach/display/components/"
      content: "delete"
    - path: "src/gtach/utils/services/"
      content: "delete"
    - path: "src/gtach/core/thread.py"
      content: "modify — remove AsyncSyncBridge, dead ThreadManager methods, _sync_timing instrumentation"
    - path: "src/gtach/utils/config.py"
      content: "modify — remove setup_logging group"
    - path: "src/gtach/assets/fonts/BebasNeue-Regular.ttf"
      content: "delete"

success_criteria:
  - "All items independently verified dead before removal"
  - "python -c 'import gtach' succeeds after all removals"
  - "No skipped items without explanation"
  - "Any item that could not be confirmed dead is explicitly left in place and noted"

notes: >
  The dead code report was produced by grep-based static analysis. It is accurate
  to the best of the Strategic Domain's analysis but has not been machine-verified.
  Claude Code must not treat report findings as authoritative — independent
  verification is the control gate for every removal.

---

```yaml
tactical_brief: |
  Task: Remove confirmed dead code from src/gtach per ai/workspace/report/dead-code-report.md.

  CRITICAL — BE SKEPTICAL. The dead code report is a hypothesis produced by static
  analysis. You must independently verify each item before removing it. If you
  cannot confirm something is dead, leave it in place and say so.

  Verification protocol for every item:
  1. Grep src/gtach recursively for import paths, class names, and method names.
  2. Exclude manager_backup.py and setup_original_backup.py from hit counts.
  3. Also search as string literals to catch getattr/dynamic dispatch.
  4. Only proceed with removal if zero active-code hits are found.

  Phase 1 — Delete dead files/packages (verify first):
    src/gtach/core/watchdog_enhanced.py
    src/gtach/display/hardware_interface.py
    src/gtach/display/ui_testing_framework.py
    src/gtach/display/enhanced_touch_factory.py
    src/gtach/display/performance.py  (shadowed by performance/ package)
    src/gtach/display/components/     (coordinator.py, factory.py — not imported anywhere)
    src/gtach/utils/services/         (registry.py, configuration.py, platform.py, dependency.py)
  Use git rm for all deletions.

  Phase 2 — Modify src/gtach/core/thread.py:
    Remove class AsyncSyncBridge entirely.
    Remove self.async_bridge = ... from ThreadManager.__init__.
    Remove self.async_bridge.shutdown() from ThreadManager.shutdown.
    Remove methods: get_statistics, list_threads, get_thread_info, is_healthy.
    Remove _sync_timing context manager and all its with self._sync_timing() call sites.
    Remove _operation_count and _sync_overhead_start attributes.
    Verify no external callers exist before removing each item.

  Phase 3 — Modify src/gtach/utils/config.py:
    Remove methods: setup_logging, _setup_production_logging,
    _setup_debug_logging, _log_pi_hardware_status from ConfigManager.
    Verify no callers exist outside config.py before removing.

  Phase 4 — Delete font:
    git rm src/gtach/assets/fonts/BebasNeue-Regular.ttf  (if zero grep hits for BebasNeue).

  Smoke test after all changes:
    python -c 'import gtach'
    Must succeed. If it fails, identify and restore the offending removal.

  Do not touch: manager_backup.py, setup_original_backup.py.
  Do not change any retained method signatures or docstrings.
  Report any item skipped and the reason.
```
