Created: 2026 June 12

```yaml
issue_info:
  id: "issue-55c879fd"
  title: "Splash screen displays a hardcoded placeholder version; --version is stale"
  date: "2026-06-12"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-55c879fd"
    change_iteration: 1

source:
  origin: "requirement_change"
  test_ref: ""
  description: >
    SplashScreen._version_text is initialised to the literal "v1.0.0" regardless
    of the installed wheel version. _draw_version_text() is never called in
    automotive mode (the default graphics mode), so no version is shown at all.
    The --version argparse action returns the literal 'GTach 0.2.0' which is
    stale. Both must read from the installed package metadata.

affected_scope:
  components:
    - name: "SplashScreen"
      file_path: "src/gtach/display/splash.py"
    - name: "setup_logging / parse_arguments"
      file_path: "src/gtach/main.py"
  designs:
    - design_ref: "design-gtach-master"
  version: "0.2.61"

reproduction:
  prerequisites: "Wheel installed at any version."
  steps:
    - "Boot GTach. Observe splash screen — no version text is shown."
    - "Run: /opt/gtach/venv/bin/gtach --version"
    - "Observe: 'GTach 0.2.0' regardless of installed version."
  frequency: "always"
  reproducibility_conditions: "Any installed version."
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    Splash screen displays the installed wheel version (e.g. v0.2.61) in the
    automotive graphics mode below the progress gauge.
    gtach --version returns the correct installed version.
  actual: >
    No version shown on splash in automotive mode.
    gtach --version returns the hardcoded stale literal 'GTach 0.2.0'.
  impact: >
    Version confirmation on the device is impossible without SSH.
    --version is misleading for diagnosis of deployed-vs-source mismatches.
  workaround: "SSH and check /opt/gtach/venv/bin/pip show gtach."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi Zero 2W)"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    SplashScreen.__init__ assigns self._version_text = "v1.0.0" unconditionally.
    _render_graphics does not call _draw_version_text in the automotive branch.
    parse_arguments passes the literal string 'GTach 0.2.0' to argparse version action.
  technical_notes: >
    importlib.metadata.version('gtach') reads the installed wheel's METADATA file
    and is the authoritative source for the deployed version. It is unaffected by
    source-tree changes and correctly reports what is actually running.
    __init__.py.__version__ is populated at build time and is also reliable, but
    importlib.metadata is preferred as it directly reflects the installed state.
    The fix is three surgical edits with ImportError guards.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: "2026-06-12"
  approach: "See change-55c879fd"
  change_ref: "change-55c879fd"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: "Never hardcode version strings; always read from package metadata."
  process_improvements: ""

traceability:
  design_refs:
    - "design-gtach-master"
  change_refs:
    - "change-55c879fd"
  test_refs: []

notes: ""

version_history:
  - version: "1.0"
    date: "2026-06-12"
    author: "William Watson"
    changes:
      - "Initial issue document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```
