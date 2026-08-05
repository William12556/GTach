Created: 2026 August 05

# Issue: A Package Attribute Shadows Its Own Module, an Asset Is Not Packaged, and a Screen Instructs a Gesture That No Longer Acts

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-c1d4b8e6"
  title: "gtach/__init__.py binds the name 'main' to the function, so app.py's 'from . import main as _main' retrieves the function and the debug and startup log handlers are unreachable; engine_profiles.yaml is absent from the wheel because package-data names only fonts; and _draw_update_view still instructs a long press that no longer returns"
  date: "2026-08-05"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-c1d4b8e6"
    change_iteration: 1

source:
  origin: "test_result"
  test_ref: "logs/start.log, on-target sessions 2026-08-05 06:37 and 07:59"
  description: >
    Faults (a) and (b) were found by reading the logs pulled from
    gtach.local after the 7f2a9c04 and 3e8b1d72 deployments. Fault (a)
    was first recorded as ai/task.md §9.9.2 on 2026-08-05 without a T03
    being raised; this document raises it. Fault (c) was recorded by the
    executor of prompt-3e8b1d72 at §6.2 of its implementation report and
    is carried here at the operator's request so it is not lost.

affected_scope:
  components:
    - name: "GTachApplication.toggle_debug_logging"
      file_path: "src/gtach/app.py"
    - name: "GTachApplication._finish_startup_logging"
      file_path: "src/gtach/app.py"
    - name: "tool.setuptools.package-data"
      file_path: "pyproject.toml"
    - name: "DisplayManager._draw_update_view"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.3.3"

reproduction:
  prerequisites: >
    (a) and (c) are observable in a source checkout. (b) requires a
    built wheel, or the deployed installation at /opt/gtach.
  steps:
    - "(a) — read src/gtach/__init__.py:11. 'from .main import main' binds the name main in the gtach package namespace to the function."
    - "(a) — read src/gtach/app.py:155. 'from . import main as _main' therefore retrieves that function, not the module."
    - "(a) — read src/gtach/main.py:18-19. _start_handler and _debug_handler are module-level globals, so they are attributes of the module and not of the function."
    - "(a) — press the Debug control on the options screen and read the log: 'Could not toggle debug logging: 'function' object has no attribute '_debug_handler''."
    - "(b) — read pyproject.toml:68-69. package-data names 'assets/fonts/*.ttf' and 'assets/fonts/*.otf' only."
    - "(b) — list the wheel's assets: python -c \"import zipfile;print([n for n in zipfile.ZipFile('dist/gtach-0.3.3-py3-none-any.whl').namelist() if 'assets' in n])\". Only Michroma-Regular.ttf is present."
    - "(b) — start the application and read the WARNING: 'Engine profiles file not found at .../gtach/assets/engine_profiles.yaml, using defaults'."
    - "(c) — read src/gtach/display/manager.py:1672. _draw_update_view renders 'Long press to return'."
    - "(c) — confirm change-3e8b1d72 removed the long-press mode change from both handler paths, so that instruction no longer does anything."
  frequency: "always"
  reproducibility_conditions: >
    All three are unconditional. (a) fires on every toggle press and on
    every startup-logging finish. (b) fires once per start. (c) is drawn
    whenever the update view is shown.
  test_data: >
    (a) ON-TARGET EVIDENCE, logs/start.log 2026-08-05 07:59, three
    presses, three identical failures:

      07:59:38,814  DisplayManager INFO  Debug logging toggle -> on
      07:59:38,815  gtach.app DEBUG      Could not toggle debug logging:
                                         'function' object has no attribute '_debug_handler'
      07:59:39,437  DisplayManager INFO  Debug logging toggle -> off
      07:59:39,437  gtach.app DEBUG      Could not toggle debug logging: ...
      07:59:41,873  DisplayManager INFO  Debug logging toggle -> on
      07:59:41,873  gtach.app DEBUG      Could not toggle debug logging: ...

    The same failure was present in the 06:37 session, so it is not a
    consequence of either fix deployed since.

    TWO CONSEQUENCES, BOTH VISIBLE IN THE FILES. debug.log is 0 bytes
    while start.log holds 5,407 DEBUG lines, so debug output goes to the
    wrong file — _start_handler is never demoted, because
    _finish_startup_logging fails the same way. And _debug_logging_on
    initialises False (manager.py:77) while the application is already
    emitting DEBUG, so the options label reads 'Debug: Off' when debug
    is in fact on. The toggle inverts a flag that never described
    reality, which is why the control appears to work.

    WHY THE OBVIOUS FIXES DO NOT WORK. 'import gtach.main' binds the
    package and then resolves gtach.main by attribute lookup, which
    __init__ has overwritten — so it retrieves the function too.
    'from .main import _debug_handler' binds the value at import time,
    which is None, and main.py rebinds the global later. The reliable
    forms retrieve the module object from sys.modules:
    importlib.import_module('gtach.main'), or sys.modules['gtach.main'].

    (b) CURRENT IMPACT IS ZERO, AND THAT IS WORTH STATING PLAINLY. The
    abarth_595_turismo profile's six thresholds — 999, 3000, 4500, 5500,
    5800, 6000 — are identical to the RPMBands dataclass defaults at
    models.py:29-34. The fallback therefore produces exactly the right
    numbers today and nothing is visibly wrong.

    What is actually broken is everything the file exists for. It
    defines three profiles — abarth_595_turismo, generic_turbo_4cyl and
    generic_na_4cyl — of which two are unreachable; the engine_profile
    configuration key is inert; and the first tuning of any threshold
    will not reach the target.

    PRECEDENT. issue-d7f2b4e6, closed, was the same class of defect: the
    Michroma font was missing from the wheel. Its fix added
    'assets/fonts/*.ttf' to package-data — the line that is still there
    — and the YAML beside it was not added.

    (c) The instruction is wrong rather than merely stale.
    change-3e8b1d72 removed the long-press mode change from
    DisplayManager and from TouchHandler, and updated
    _draw_options_menu's footer to 'Swipe up to return'.
    _draw_update_view was outside that prompt's stated scope and still
    tells the operator to do something that has no effect.
  error_output: >
    (a) gtach.app DEBUG Could not toggle debug logging: 'function'
    object has no attribute '_debug_handler'

    (b) gtach.utils.config.load_engine_profile WARNING Engine profiles
    file not found at /opt/gtach/venv/lib/python3.9/site-packages/gtach/
    assets/engine_profiles.yaml, using defaults

    Preceded by: load_engine_profile DEBUG importlib.resources failed:
    expected str, bytes or os.PathLike object, not NoneType

    (c) None. It is drawn text.

behavior:
  expected: >
    A control that reports success has acted. An asset the application
    reads at runtime is in the distribution that ships it. A screen does
    not instruct a gesture that was removed.
  actual: >
    Three small, unrelated faults, grouped because each is a few lines
    and none interacts with the others.

    (a) src/gtach/__init__.py:11 binds 'main' to the function, so
    app.py's two 'from . import main as _main' sites retrieve the
    function and every attribute access on it raises AttributeError.
    Both are wrapped in try/except that logs at DEBUG, so the failures
    are invisible unless debug logging is on — which is itself what one
    of them controls.

    (b) pyproject.toml:69 declares package-data for fonts only, so
    assets/engine_profiles.yaml is not in the wheel. The application
    warns and falls back to the built-in defaults.

    (c) manager.py:1672 renders 'Long press to return' on the update
    view, after change-3e8b1d72 made long press inert.
  impact: >
    (a) Debug logging cannot be turned on from the panel, which removes
    the diagnostic route on a device with no keyboard. debug.log is
    never written and start.log is never closed, so it grew to 3.5 MB in
    one session. The label misreports the state.

    (b) Latent. Two of three engine profiles are unreachable and the
    engine_profile setting does nothing. No wrong number is displayed
    today, by coincidence.

    (c) Cosmetic, and misleading at the moment the operator is most
    likely to be stuck — mid update check, on a screen whose exit is not
    otherwise signposted.
  workaround: >
    (a) Start with --debug, which configures DEBUG at startup and does
    not use the broken path.
    (b) None from the panel. Editing the installed config has no effect,
    the profile file being absent.
    (c) Swipe up, which works.

environment:
  python_version: "3.11 development; 3.9 on target (/opt/gtach/venv)"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W, gtach.local"
  dependencies:
    - library: "setuptools"
      version: "any"
    - library: "PyYAML"
      version: "any"
  domain: "domain_1"

analysis:
  root_cause: >
    (a) A package that re-exports a function under its module's own
    name. 'from .main import main' is a normal convenience import and
    the shadowing it causes is invisible at the definition site; it only
    bites a second module that later tries to reach the module rather
    than the function. The try/except around both call sites then hid
    the consequence.

    (b) package-data was extended once, for the fault it was raised
    against (issue-d7f2b4e6, the missing font), and a glob was written
    narrow enough to cover only that case. The YAML in the same
    directory was not considered because nothing had failed on it yet.

    (c) A file-scoped prompt. change-3e8b1d72's scope named
    _draw_options_menu's footer; the identical string in
    _draw_update_view was not in the file set the author had in mind,
    though it is in the same file. Its executor found and reported it
    rather than exceeding scope.
  technical_notes: >
    THIS IS A GROUPED HOUSEKEEPING TRIPLE, on the pattern of
    change-d32ccc49: three small faults in three files, each confined to
    a few lines, none dependent on another. They are grouped so one
    cycle covers them rather than three.

    ON THE __init__ SHADOWING, AND WHAT IS NOT PROPOSED. The tempting
    fix is to stop exporting main from __init__.py. That is rejected in
    change-c1d4b8e6: the console entry point and any external caller
    rely on it, and changing a package's public surface to work around a
    private call site is disproportionate. The two call sites are
    corrected instead.

    A THIRD SITE MAY EXIST. Both known sites are in app.py. The change
    document requires a repository-wide grep for the pattern rather than
    correcting only the two named here — the same discipline
    change-7f2a9c04 adopted after prompt-378703da's file-scoped
    criterion proved unsatisfiable.

    ON THE ORDER OF FIXING (a). Correcting the module reference will
    make _finish_startup_logging work for the first time, which demotes
    _start_handler at the end of startup. start.log will therefore
    become much smaller and stop capturing steady-state DEBUG. That is
    the intended design (change-bd8f95b7) and is a visible change in the
    logs pulled after this lands — worth expecting rather than
    diagnosing.

    NOT IN SCOPE — THE OBD DESYNCHRONISATION. The same log carries a
    separate and more serious finding: 0100 times out at 1.0 s during
    the ELM327 protocol search, the late response is not drained, and
    every subsequent read is offset by one command. It is unrelated to
    these three faults, needs its own investigation, and is recorded in
    ai/task.md §9.10 rather than absorbed here.
  related_issues:
    - issue_ref: "issue-d7f2b4e6"
      relationship: "related"
    - issue_ref: "issue-bd8f95b7"
      relationship: "related"
    - issue_ref: "issue-3e8b1d72"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Retrieve the module from sys.modules at both app.py sites; widen
    package-data to include assets/*.yaml; correct the update view's
    footer. See change-c1d4b8e6.
  change_ref: "change-c1d4b8e6"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    A package that re-exports a submodule's member under the submodule's
    own name shadows it. Where a module's globals must be reached at
    runtime, retrieve the module from sys.modules rather than by
    attribute traversal of the package.

    A try/except that logs at DEBUG around a control's only effect makes
    the control's failure invisible — doubly so when the control is the
    one that enables DEBUG.

    package-data written as a narrow glob covers the fault it was raised
    against and nothing else. A directory the application reads at
    runtime should be packaged as a directory.
  process_improvements: >
    Fault (b) is the second packaging defect of exactly this shape;
    issue-d7f2b4e6 was the first. A build-time check that every file
    under src/gtach/assets/ appears in the wheel would have caught both,
    and is cheaper than finding the third by deploying it.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on every modified file passes."
    - "grep confirms no 'from . import main' remains in src/gtach."
    - "toggle_debug_logging reaches _debug_handler and does not raise."
    - "_finish_startup_logging reaches _start_handler and does not raise."
    - "On target: pressing Debug produces no 'Could not toggle debug logging' line."
    - "On target: debug.log is non-empty after the toggle is turned on."
    - "On target: start.log stops growing once startup completes."
    - "A built wheel contains gtach/assets/engine_profiles.yaml."
    - "On target: no 'Engine profiles file not found' WARNING at startup."
    - "On target: selecting a non-default engine profile changes the band thresholds."
    - "_draw_update_view renders 'Swipe up to return'."
    - "The string 'Long press to return' does not appear in src/gtach outside the backup files."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-c1d4b8e6"
  test_refs: []

notes: >
  Raised under P04 from two on-target log readings and one finding
  carried from the prompt-3e8b1d72 implementation report §6.2. Not a
  numbered item of either code review; no §7.0 task number.

  issue_info.type is defect, severity medium. Fault (a) removes the
  panel's only diagnostic control on a device with no keyboard, and its
  failure is self-concealing. Faults (b) and (c) are latent and cosmetic
  respectively.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial issue document grouping three small faults found in the 2026-08-05 on-target logs and the prompt-3e8b1d72 report."
      - "Recorded the __init__ shadowing precisely: gtach/__init__.py:11 binds 'main' to the function, so both 'from . import main as _main' sites in app.py retrieve the function and the module globals are unreachable; and recorded why the two obvious alternative fixes also fail."
      - "Recorded that fault (a) is self-concealing — both call sites log at DEBUG, and one of them is the control that enables DEBUG."
      - "Recorded that fault (b) has zero current impact because the abarth profile's thresholds coincide exactly with the RPMBands defaults, and that what is broken is the two unreachable profiles and the inert engine_profile setting."
      - "Recorded issue-d7f2b4e6 as the precedent: the same packaging defect, whose fix added the fonts glob that still stands beside the unpackaged YAML."
      - "Recorded that correcting (a) will visibly shrink start.log, that being change-bd8f95b7's intended design working for the first time."
      - "Recorded the OBD response desynchronisation found in the same log as explicitly out of scope."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial issue document grouping the `__init__` module shadowing that breaks debug logging, the unpackaged `engine_profiles.yaml`, and the stale update-view footer. |

---

Copyright (c) 2026 William Watson. MIT License.
