change_info:
  id: "change-b7e3f90a"
  title: "Remove dead code from src/gtach"
  date: "2026-06-18"
  author: "William Watson"
  status: "approved"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b7e3f90a"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b7e3f90a"
  description: >
    Remove ~5300 lines of unreachable code identified by static analysis.
    See ai/workspace/report/dead-code-report.md for the full inventory.

scope:
  summary: >
    Delete seven dead files and two dead packages. Remove dead class AsyncSyncBridge
    and unused public methods from ThreadManager. Remove dead setup_logging group
    from ConfigManager. Remove unused BebasNeue font asset.
  affected_components:
    - name: "core/watchdog_enhanced.py"
      file_path: "src/gtach/core/watchdog_enhanced.py"
      change_type: "delete"
    - name: "display/hardware_interface.py"
      file_path: "src/gtach/display/hardware_interface.py"
      change_type: "delete"
    - name: "display/ui_testing_framework.py"
      file_path: "src/gtach/display/ui_testing_framework.py"
      change_type: "delete"
    - name: "display/enhanced_touch_factory.py"
      file_path: "src/gtach/display/enhanced_touch_factory.py"
      change_type: "delete"
    - name: "display/performance.py"
      file_path: "src/gtach/display/performance.py"
      change_type: "delete"
    - name: "display/components/"
      file_path: "src/gtach/display/components/"
      change_type: "delete"
    - name: "utils/services/"
      file_path: "src/gtach/utils/services/"
      change_type: "delete"
    - name: "core/thread.py"
      file_path: "src/gtach/core/thread.py"
      change_type: "modify"
    - name: "utils/config.py"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
    - name: "BebasNeue-Regular.ttf"
      file_path: "src/gtach/assets/fonts/BebasNeue-Regular.ttf"
      change_type: "delete"
  out_of_scope:
    - "display/manager_backup.py — excluded by convention"
    - "display/setup_original_backup.py — excluded by convention"
    - "Any functional changes to active code"
    - "Test coverage additions"

rational:
  problem_statement: >
    Dead code imposes maintenance burden and inflates the deployed wheel without
    providing any runtime value.
  proposed_solution: >
    Delete confirmed dead files and packages. Remove confirmed dead classes and
    methods from active files. Each item must be independently verified before
    removal.
  benefits:
    - "Reduced codebase size (~5300 lines removed)"
    - "Cleaner import graph"
    - "Smaller deployed wheel"
    - "Reduced maintenance surface"
  risks:
    - risk: "False-positive identification — removing code that is actually reachable via a path not found by grep"
      mitigation: >
        Claude Code must independently verify each item before removal using its
        own source inspection. The dead code report is a starting point, not
        ground truth. See prompt tactical_brief for verification protocol.
    - risk: "Removing a method from ThreadManager that is called via getattr or dynamic dispatch"
      mitigation: >
        Search for the method name as a string literal in addition to as a direct
        call. If any dynamic usage is found, do not remove.

technical_details:
  current_behavior: "Dead code exists and is imported (or shadowed) at module load time."
  proposed_behavior: "Dead code removed; active modules unchanged in behaviour."
  implementation_approach: >
    Phase 1 — verify then delete dead files and packages via git rm.
    Phase 2 — verify then remove dead class/methods from core/thread.py.
    Phase 3 — verify then remove dead setup_logging group from utils/config.py.
    Phase 4 — git rm unused font asset.
    Each phase: grep-verify first, then remove only confirmed-dead items.
  code_changes:
    - component: "core/thread.py"
      file: "src/gtach/core/thread.py"
      change_summary: >
        Remove AsyncSyncBridge class and its instantiation in ThreadManager.__init__
        and ThreadManager.shutdown. Remove ThreadManager methods: get_statistics,
        list_threads, get_thread_info, is_healthy. Remove _sync_timing context
        manager and all its call sites. Remove _operation_count and
        _sync_overhead_start attributes and all references.
      classes_affected:
        - "AsyncSyncBridge (delete entire class)"
        - "ThreadManager (remove dead methods and instrumentation)"
    - component: "utils/config.py"
      file: "src/gtach/utils/config.py"
      change_summary: >
        Remove ConfigManager.setup_logging, _setup_production_logging,
        _setup_debug_logging, and _log_pi_hardware_status methods.
      functions_affected:
        - "ConfigManager.setup_logging"
        - "ConfigManager._setup_production_logging"
        - "ConfigManager._setup_debug_logging"
        - "ConfigManager._log_pi_hardware_status"

testing_requirements:
  test_approach: "Import smoke test — confirm gtach imports without error after removal."
  validation_criteria:
    - "python -c 'import gtach' succeeds"
    - "No NameError or ImportError at startup"
    - "Active modules (manager.py, setup.py, app.py) import cleanly"

notes: >
  Claude Code must treat the dead code report as a hypothesis, not a guarantee.
  Independent verification is mandatory before any deletion.

version_history:
  - version: "1.0"
    date: "2026-06-18"
    author: "William Watson"
    changes:
      - "Initial change document"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
