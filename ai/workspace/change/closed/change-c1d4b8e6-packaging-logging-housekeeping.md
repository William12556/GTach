Created: 2026 August 05

# Change: Reach the Module, Ship the Asset, Correct the Instruction

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-c1d4b8e6"
  title: "app.py retrieves the gtach.main module from sys.modules instead of by attribute traversal of a package that shadows it; package-data gains assets/*.yaml; and _draw_update_view's footer is corrected to the gesture that works"
  date: "2026-08-05"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c1d4b8e6"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-c1d4b8e6"
  description: >
    Resolves issue-c1d4b8e6. Raised under P04 from the on-target logs of
    2026-08-05 and from §6.2 of the prompt-3e8b1d72 implementation
    report.

scope:
  summary: >
    Three small independent corrections: two lines in app.py, one in
    pyproject.toml, one string in manager.py.
  affected_components:
    - name: "GTachApplication.toggle_debug_logging"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "GTachApplication._finish_startup_logging"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "tool.setuptools.package-data"
      file_path: "pyproject.toml"
      change_type: "modify"
    - name: "DisplayManager._draw_update_view"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "src/gtach/__init__.py. Its re-export of main is the cause of the shadowing and is NOT removed — the console entry point and external callers depend on it, and altering a package's public surface to suit a private call site is disproportionate. The call sites are corrected instead."
    - "src/gtach/main.py. Its module globals are correct; only the way app.py reaches them is wrong."
    - "The try/except wrappers around both app.py sites. They conceal the failure and narrowing them is a separate judgement; the fault they concealed is removed instead."
    - "_debug_logging_on's initial value (manager.py:77). It reads False while the application may already be at DEBUG. Correcting it means asking main.py for the effective level, which is a second change to the same subsystem and is deferred — see risks."
    - "The OBD response desynchronisation found in the same log. Unrelated, more serious, recorded in ai/task.md §9.10 for its own cycle."
    - "The engine profile VALUES. Only the packaging changes; abarth_595_turismo's thresholds are not touched."
    - "The two backup files carrying 'Long press to return'. Neither is imported."

rational:
  problem_statement: >
    gtach/__init__.py binds 'main' to the function, so app.py's two
    'from . import main as _main' sites retrieve the function and every
    attribute access raises AttributeError — leaving debug logging
    unturnable from the panel and start.log never closed. Separately,
    engine_profiles.yaml is not in the wheel, and the update view still
    instructs a long press that change-3e8b1d72 made inert.
  proposed_solution: >
    Retrieve the module from sys.modules; package the assets directory's
    YAML as well as its fonts; correct the footer string.
  alternatives_considered:
    - option: "Remove 'from .main import main' from gtach/__init__.py."
      reason_rejected: >
        Removes the shadowing at source and is the tidiest reading of
        the fault. Rejected because the name is part of the package's
        public surface — the console entry point and any external caller
        use it — and changing that to accommodate two private call sites
        is disproportionate. Recorded because it is the right answer if
        the package's exports are ever revisited."
    - option: "import gtach.main, then gtach.main._debug_handler."
      reason_rejected: >
        Does not work. The import registers sys.modules['gtach.main']
        but binds only 'gtach' locally; the subsequent gtach.main is an
        attribute lookup on the package, which __init__ has overwritten
        with the function. It fails identically to the current code,
        which is exactly the trap worth recording."
    - option: "from .main import _debug_handler."
      reason_rejected: >
        Also does not work. It binds the value at import time — None —
        and main.py rebinds the global afterwards under a global
        statement. The imported name would never see the handler."
    - option: "Package the whole assets directory rather than globbing by extension."
      reason_rejected: >
        Broader and arguably more robust. Not taken because the fonts
        glob is already there and works; adding a yaml glob beside it is
        the minimal change and keeps the declaration explicit about what
        ships. The build-time check proposed in issue-c1d4b8e6
        prevention is the durable answer."
    - option: "Fix only the debug toggle and defer the other two."
      reason_rejected: >
        The three are independent and each is a few lines. Grouping
        follows the change-d32ccc49 precedent and spends one cycle
        rather than three."
  benefits:
    - "Debug logging becomes controllable from the panel — the only diagnostic route on a device with no keyboard."
    - "start.log stops growing after startup, which is what change-bd8f95b7 designed and has never done."
    - "The engine_profile setting starts working, and the two unreachable profiles become reachable."
    - "The update view stops instructing a gesture that does nothing."
  risks:
    - risk: >
        Correcting _finish_startup_logging demotes _start_handler for
        the first time, so start.log becomes far smaller and stops
        carrying steady-state DEBUG. Anyone reading the next pulled log
        may take that for a regression.
      mitigation: >
        It is the intended behaviour of change-bd8f95b7 working for the
        first time. Stated in the deployment notes and expected rather
        than diagnosed. Debug output moves to debug.log, where it
        belongs."
    - risk: >
        _debug_logging_on still initialises False while the application
        may already be at DEBUG, so the label can misreport.
      mitigation: >
        Left out of scope deliberately. Once _finish_startup_logging
        works, the steady state after startup is debug-off, so False
        becomes correct in the ordinary case — the label was wrong
        mainly because the handler was never demoted. If it still
        misreports after this lands, correct it then, against evidence
        rather than in anticipation."
    - risk: >
        A third 'from . import main' site exists somewhere unexamined.
      mitigation: >
        The success criterion is a repository-wide grep for the pattern
        rather than a list of the two known sites — the discipline
        adopted in change-7f2a9c04 after a file-scoped criterion proved
        unsatisfiable."
    - risk: >
        Adding the YAML to the wheel changes what the target reads at
        startup, from built-in defaults to the file.
      mitigation: >
        The values are identical — abarth_595_turismo's six thresholds
        equal the RPMBands defaults — so no displayed number changes.
        This is asserted rather than assumed, by comparing the parsed
        profile with the dataclass defaults in the tests."
  benefits_measurement: >
    Debug toggle success rate: 0 of 3 presses -> 3 of 3. Bytes written
    to debug.log when debug is on: 0 -> non-zero. Engine profiles
    reachable: 0 of 3 -> 3 of 3. Screens instructing a removed gesture:
    1 -> 0.

technical_details:
  current_behavior: >
    app.py:155 and the equivalent line in _finish_startup_logging both
    do 'from . import main as _main'. gtach/__init__.py:11 has bound
    'main' to the function, so _main is the function and
    _main._debug_handler raises AttributeError. Both sites catch and log
    at DEBUG. pyproject.toml:69 lists only the two font globs.
    manager.py:1672 renders 'Long press to return'.
  proposed_behavior: >
    Both sites obtain the module object and reach its globals.
    package-data includes assets/*.yaml. The update footer reads 'Swipe
    up to return'.
  implementation_approach: >
    THREE INDEPENDENT EDITS.

    EDIT A — app.py, both sites. Replace the package-attribute traversal
    with a sys.modules retrieval:

        import sys
        _main = sys.modules.get('gtach.main')
        if _main is None:
            return

    or equivalently importlib.import_module('gtach.main'), which returns
    the sys.modules entry. Either reaches the module; attribute
    traversal of the package cannot, because __init__ has shadowed the
    name.

    Grep for the pattern first — the two known sites are in app.py, but
    the criterion is repository-wide.

    EDIT B — pyproject.toml:69. Add the YAML glob beside the fonts:

        "gtach" = [
            "assets/fonts/*.ttf",
            "assets/fonts/*.otf",
            "assets/*.yaml",
        ]

    EDIT C — manager.py:1672. 'Long press to return' becomes 'Swipe up
    to return', matching _draw_options_menu as corrected by
    change-3e8b1d72.
  code_changes:
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Both module references retrieve gtach.main from sys.modules
        rather than by attribute traversal of the shadowing package.
      functions_affected:
        - "toggle_debug_logging"
        - "_finish_startup_logging"
      classes_affected:
        - "GTachApplication"
    - component: "package-data"
      file: "pyproject.toml"
      change_summary: "assets/*.yaml added."
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: "_draw_update_view's footer corrected."
      functions_affected:
        - "_draw_update_view"
  data_changes:
    - "The wheel gains gtach/assets/engine_profiles.yaml. Existing installations acquire it at the next deployment; until then they continue on the identical built-in defaults."
  interface_changes: []

dependencies:
  internal:
    - component: "gtach/__init__.py:11"
      impact: "The cause of the shadowing. Read-only — deliberately not changed."
    - component: "src/gtach/main.py:18-19"
      impact: "Defines _start_handler and _debug_handler. Read-only."
    - component: "change-bd8f95b7"
      impact: "Its two-file logging design begins working once EDIT A lands. Not modified."
    - component: "change-3e8b1d72"
      impact: "Corrected _draw_options_menu's footer; EDIT C corrects the one it did not cover."
    - component: "load_engine_profile — utils/config.py"
      impact: "Reads the packaged YAML. Not modified; it already handles both the found and not-found paths."
  external:
    - "setuptools package-data — build-time only."
  required_changes:
    - change_ref: "change-3e8b1d72"
      relationship: "related"

testing_requirements:
  test_approach: >
    EDIT A is tested by calling both methods against a real gtach.main
    with the handlers set, and asserting the handler levels change.
    EDIT B is tested by building a wheel and listing its contents — the
    only test that proves packaging. EDIT C is a string assertion.
  test_cases:
    - scenario: "toggle_debug_logging(True) with gtach.main._debug_handler set to a real handler."
      expected_result: "The handler's level becomes DEBUG. No exception."
    - scenario: "toggle_debug_logging(False)."
      expected_result: "The handler's level becomes CRITICAL+1."
    - scenario: "The same two calls against the pre-change code."
      expected_result: "The handler's level is unchanged and an AttributeError is caught. The test must discriminate."
    - scenario: "toggle_debug_logging with _debug_handler None."
      expected_result: "Returns without raising, as the existing guard intends."
    - scenario: "_finish_startup_logging with _start_handler set."
      expected_result: "The handler's level becomes CRITICAL+1."
    - scenario: "toggle_debug_logging on a non-Linux platform."
      expected_result: "Returns early, unchanged."
    - scenario: "grep for 'from . import main' across the repository."
      expected_result: "No occurrence."
    - scenario: "Build a wheel and list its assets."
      expected_result: "gtach/assets/engine_profiles.yaml present alongside the font."
    - scenario: "load_engine_profile('abarth_595_turismo') from the installed layout."
      expected_result: "Returns the profile from the file; no WARNING."
    - scenario: "The parsed abarth profile compared field by field with the RPMBands dataclass defaults."
      expected_result: "Identical — confirming no displayed number changes as a result of packaging the file."
    - scenario: "load_engine_profile('generic_na_4cyl')."
      expected_result: "Returns that profile's thresholds, which differ from the defaults. This is the assertion that proves the file is actually being read."
    - scenario: "load_engine_profile with the file absent."
      expected_result: "Falls back with a WARNING, unchanged."
    - scenario: "_draw_update_view's footer string."
      expected_result: "'Swipe up to return'."
    - scenario: "grep 'Long press to return' across src/gtach."
      expected_result: "No occurrence outside the two backup files."
  regression_scope:
    - "tests/utils/ and tests/display/ — once populated per ai/task.md §8.2."
    - "On gtach.local: press Debug and confirm no 'Could not toggle debug logging' line, and that debug.log becomes non-empty."
    - "On gtach.local: confirm start.log stops growing after startup."
    - "On gtach.local: confirm no 'Engine profiles file not found' WARNING."
    - "On gtach.local: confirm the gauge's band boundaries are unchanged from the previous build."
    - "On gtach.local: open the update view and confirm the footer reads 'Swipe up to return'."
  validation_criteria:
    - "python -m py_compile on both Python files passes."
    - "pyproject.toml parses."
    - "pytest tests/ passes with no new failures."
    - "No EXECUTABLE occurrence of 'from . import main' remains in src/. Amended 2026-08-05 from 'remains in the repository', which was unsatisfiable: the string necessarily appears in this cycle's own T-Docs, in ai/task.md, in the closed prompt-bd8f95b7 where the faulty sites were written, and in the explanatory comments prompt-c1d4b8e6's own EDIT A text mandates verbatim. Those are documentation of the fault and are correct. See the implementation report §5.2."
    - "A freshly built wheel contains gtach/assets/engine_profiles.yaml."
    - "src/gtach/__init__.py and src/gtach/main.py are byte-identical."

implementation:
  implementation_steps:
    - step: "Write the discriminating test for EDIT A first and confirm it fails against the current code — the handler level unchanged, AttributeError caught."
      owner: "Claude Code"
    - step: "EDIT A at both app.py sites, after a repository-wide grep for the pattern."
      owner: "Claude Code"
    - step: "EDIT B in pyproject.toml; build a wheel and list its contents."
      owner: "Claude Code"
    - step: "EDIT C in manager.py."
      owner: "Claude Code"
    - step: "Compile checks and the full assertion set."
      owner: "Claude Code"
    - step: "Deploy to gtach.local; toggle debug and confirm debug.log fills; confirm no profile WARNING; confirm band boundaries unchanged; confirm the update footer."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across three files. git revert restores all three
    faults. No data or configuration migration; the wheel simply stops
    carrying the YAML again and the fallback resumes.
  deployment_notes: >
    EXPECT start.log TO SHRINK. Once _finish_startup_logging works,
    _start_handler is demoted at the end of startup and steady-state
    DEBUG goes to debug.log instead. The 3.5 MB and 362 KB start.log
    files from the two 2026-08-05 sessions are the symptom of that
    demotion never happening. A much smaller start.log after this lands
    is the fix working, not a regression.

    No displayed value changes. The profile now read from the file
    carries the same six thresholds the built-in defaults did.

verification:
  implemented_date: "2026-08-05"
  implemented_by: "Claude Code"
  verification_date: "2026-08-07"
  verified_by: "William Watson (confirmed resolved); source re-inspection by Claude"
  test_results: >
    No T06 exists — §8.2's pytest suite is still unwritten. Verified
    instead by source re-inspection against this document's success
    criteria: app.py:146 and app.py:173 both retrieve
    sys.modules.get('gtach.main') rather than the shadowed package
    attribute (EDIT A present at both sites); pyproject.toml:78 lists
    "assets/*.yaml" beside the fonts glob (EDIT B present); manager.py
    no longer contains the string "Long press to return" (EDIT C
    present). William confirmed on-target behaviour directly: debug
    toggle reaches the handler, engine profiles load, and the update
    view's footer reads correctly.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-3e8b1d72"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-c1d4b8e6"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-c1d4b8e6, grouping three small independent corrections on the change-d32ccc49 pattern."
      - "Recorded that gtach/__init__.py is deliberately not changed: removing the re-export would fix the shadowing at source but alters the package's public surface to suit two private call sites."
      - "Recorded both obvious alternative fixes as non-working, with the reason for each, so neither is attempted."
      - "Recorded that start.log will shrink markedly once _finish_startup_logging works, and that this is change-bd8f95b7's design operating for the first time rather than a regression."
      - "Recorded that packaging the YAML changes no displayed value, the abarth profile's thresholds equalling the dataclass defaults, and made that an explicit assertion rather than an assumption."
      - "Added an assertion on a non-default profile as the only test that proves the file is genuinely being read."
      - "Left _debug_logging_on's initial value out of scope, to be judged against evidence after the handler demotion works."
  - version: "1.1"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Amended the fourth validation criterion to cover executable occurrences in src/ only. As written it was unsatisfiable: the string necessarily appears in this cycle's own T-Docs, in ai/task.md, in the closed prompt-bd8f95b7, and in the explanatory comments prompt-c1d4b8e6's own EDIT A text mandates verbatim. Reported at implementation report §5.2 and amended here rather than in prompt-c1d4b8e6, which is closed and immutable per P00 §1.1.14.2."
      - "Second occurrence of this criterion defect; prompt-378703da was the first, and the prevention note recorded in change-7f2a9c04 did not bind subsequent authoring. The durable correction is a template rule — see T04-prompt.md v1.4 — rather than a further note."
  - version: "1.2"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Closed on William Watson's direct confirmation that all three faults are resolved, cross-checked by source re-inspection: sys.modules retrieval present at both app.py sites, assets/*.yaml present in pyproject.toml package-data, and 'Long press to return' absent from manager.py. No T06 result document exists — §8.2's pytest suite remains unwritten — so this closes on human confirmation plus source verification rather than a passing regression suite, the same gap already recorded against change-1143427b (ai/task.md §11.2)."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial change document coupled to issue-c1d4b8e6. Corrects the module retrieval at both `app.py` sites, packages `assets/*.yaml`, and fixes the update view's footer. |
| 1.1 | 2026-08-05 | Amended the fourth validation criterion to executable occurrences in `src/` only; as written it was unsatisfiable. Second occurrence of the defect, so the durable correction is a T04 template rule rather than another prevention note. |
| 1.2 | 2026-08-07 | Closed on William Watson's confirmation, cross-checked by source re-inspection of all three edits. No T06 exists; closes on human confirmation plus source verification per the `1143427b` precedent. |

---

Copyright (c) 2026 William Watson. MIT License.
