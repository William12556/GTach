issue_info:
  id: "issue-b7e3f90a"
  title: "Dead code accumulation in src/gtach"
  date: "2026-06-18"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-b7e3f90a"
    change_iteration: 1

source:
  origin: "code_review"
  description: >
    Static analysis of src/gtach identified approximately 5300 lines of unreachable
    code across seven dead files, two dead packages, and several dead classes and
    methods within active files. See ai/workspace/report/dead-code-report.md.

affected_scope:
  components:
    - name: "core/watchdog_enhanced"
      file_path: "src/gtach/core/watchdog_enhanced.py"
    - name: "display/hardware_interface"
      file_path: "src/gtach/display/hardware_interface.py"
    - name: "display/ui_testing_framework"
      file_path: "src/gtach/display/ui_testing_framework.py"
    - name: "display/enhanced_touch_factory"
      file_path: "src/gtach/display/enhanced_touch_factory.py"
    - name: "display/performance (flat file)"
      file_path: "src/gtach/display/performance.py"
    - name: "display/components (package)"
      file_path: "src/gtach/display/components/"
    - name: "utils/services (package)"
      file_path: "src/gtach/utils/services/"
    - name: "core/thread (AsyncSyncBridge, unused ThreadManager API)"
      file_path: "src/gtach/core/thread.py"
    - name: "utils/config (setup_logging group)"
      file_path: "src/gtach/utils/config.py"
    - name: "assets/fonts/BebasNeue-Regular.ttf"
      file_path: "src/gtach/assets/fonts/BebasNeue-Regular.ttf"
  version: "0.2.63"

behavior:
  expected: "All code in src/gtach is reachable and maintained."
  actual: >
    Approximately 5300 lines of Python and one font asset exist with no reachable
    import path. Dead code imposes maintenance burden, confuses navigation, and
    inflates the deployed wheel.
  impact: "Maintenance overhead. No functional impact."
  workaround: "None required."

analysis:
  root_cause: >
    Incremental development left behind superseded implementations (watchdog_enhanced,
    components/, services/), refactored-away flat files now shadowed by packages
    (performance.py), and exploratory code never wired up (AsyncSyncBridge,
    ui_testing_framework, enhanced_touch_factory). The BebasNeue font was included
    but never referenced.
  technical_notes: >
    Detailed per-item analysis in ai/workspace/report/dead-code-report.md.
    Python package shadowing rule: when both performance.py and performance/
    exist in the same directory, the package takes precedence and the module
    is unreachable.

resolution:
  assigned_to: "Claude Code"
  approach: "Delete dead files and packages; remove dead classes/methods from active files."
  change_ref: "change-b7e3f90a"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-06-18"
    author: "William Watson"
    changes:
      - "Initial issue"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
