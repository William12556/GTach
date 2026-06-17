Created: 2026 June 12

```yaml
change_info:
  id: "change-55c879fd"
  title: "Read installed version from package metadata for splash and --version"
  date: "2026-06-12"
  author: "William Watson"
  status: "approved"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-55c879fd"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-55c879fd"
  description: >
    Replace hardcoded version literals with importlib.metadata reads and display
    the installed version on the splash screen in automotive mode.

scope:
  summary: >
    Three surgical edits: (1) SplashScreen.__init__ reads the installed version
    from importlib.metadata; (2) _render_graphics automotive branch calls
    _draw_version_text below the progress gauge; (3) parse_arguments --version
    action reads the installed version from importlib.metadata.
  affected_components:
    - name: "SplashScreen"
      file_path: "src/gtach/display/splash.py"
      change_type: "modify"
    - name: "parse_arguments"
      file_path: "src/gtach/main.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-gtach-master"
      sections:
        - "Splash screen"
  out_of_scope:
    - "__init__.py.__version__ — populated at build time; left unchanged."
    - "app.py startup log version line — already reads __version__ correctly."
    - "Typography size or positioning changes beyond adding the version line."
    - "Any other splash graphics changes."

rational:
  problem_statement: >
    Hardcoded version literals diverge from the installed wheel, making version
    confirmation on the device unreliable.
  proposed_solution: >
    importlib.metadata.version('gtach') is called once at SplashScreen init and
    once in parse_arguments. Both are guarded with try/except; on failure a safe
    fallback is used. The result is always the version of the wheel that is
    actually running.
  alternatives_considered:
    - option: "Read from gtach.__version__."
      reason_rejected: >
        __version__ is populated at build time from pyproject.toml and reflects
        source intent. importlib.metadata reflects installed reality — the
        distinction matters when diagnosing stale-wheel deployments.
  benefits:
    - "Splash confirms the running version on every boot without SSH."
    - "--version is correct for all installed versions."
    - "No new dependencies; importlib.metadata is stdlib (Python 3.8+)."
  risks:
    - risk: "importlib.metadata.version raises PackageNotFoundError in dev environments."
      mitigation: "try/except with fallback to 'v?.?.?' on splash and 'GTach' on --version."

technical_details:
  current_behavior: >
    SplashScreen.__init__: self._version_text = "v1.0.0".
    _render_graphics automotive branch: does not call _draw_version_text.
    parse_arguments: parser.add_argument('--version', action='version', version='GTach 0.2.0').
  proposed_behavior: >
    SplashScreen.__init__: reads importlib.metadata.version('gtach'), formats as
    'v{version}', falls back to 'v?.?.?' on error. Assigns to self._version_text.
    _render_graphics automotive branch: calls _draw_version_text at center_y + 110,
    below the progress gauge (which is centred at center_y + 20, radius 60).
    parse_arguments: reads importlib.metadata.version('gtach'), formats as
    'GTach {version}', falls back to 'GTach' on error.
  implementation_approach: "Three isolated edits; no structural change."
  code_changes:
    - component: "SplashScreen"
      file: "src/gtach/display/splash.py"
      change_summary: >
        In __init__, replace self._version_text = "v1.0.0" with an
        importlib.metadata read. In _render_graphics automotive else-branch,
        add _draw_version_text call at center_y + 110.
      functions_affected:
        - "__init__"
        - "_render_graphics"
      classes_affected:
        - "SplashScreen"
    - component: "parse_arguments"
      file: "src/gtach/main.py"
      change_summary: >
        Replace the literal 'GTach 0.2.0' in the --version action with an
        importlib.metadata read at call time.
      functions_affected:
        - "parse_arguments"
      classes_affected: []
  data_changes: []
  interface_changes: []

dependencies:
  internal: []
  external: []
  required_changes: []

testing_requirements:
  test_approach: "Visual verification on Pi after wheel deployment."
  test_cases:
    - scenario: "Boot with installed wheel v0.2.61."
      expected_result: "Splash automotive mode shows 'v0.2.61' below the progress gauge."
    - scenario: "gtach --version on Pi."
      expected_result: "Outputs 'GTach 0.2.61' (or current installed version)."
    - scenario: "Dev environment where gtach is not installed."
      expected_result: "Splash shows 'v?.?.?'; --version outputs 'GTach'. No crash."
  regression_scope:
    - "text_only and minimal splash modes — _draw_version_text already called there; unchanged."
    - "Splash duration and animation — unaffected."
  validation_criteria:
    - "Version on splash matches output of: /opt/gtach/venv/bin/pip show gtach | grep Version"
    - "--version output matches installed version."
    - "No startup crash in dev environment (PackageNotFoundError guarded)."

implementation:
  implementation_steps:
    - step: "Edit SplashScreen.__init__ to read installed version."
      owner: "Claude Code"
    - step: "Add _draw_version_text call in automotive branch of _render_graphics."
      owner: "Claude Code"
    - step: "Edit parse_arguments --version to read installed version."
      owner: "Claude Code"
  rollback_procedure: "Revert splash.py and main.py via git."
  deployment_notes: "Build wheel and deploy to Pi per standard workflow."

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  related_changes: []
  related_issues:
    - issue_ref: "issue-55c879fd"
      relationship: "resolves"

notes: ""

version_history:
  - version: "1.0"
    date: "2026-06-12"
    author: "William Watson"
    changes:
      - "Initial change document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```
