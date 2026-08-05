Created: 2026 August 05

# Prompt: Reach the Module, Ship the Asset, Correct the Instruction

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-c1d4b8e6"
  task_type: "debug"
  source_ref: "change-c1d4b8e6"
  target_profile: "claude_code"
  date: "2026-08-05"
  iteration: 1
  coupled_docs:
    change_ref: "change-c1d4b8e6"
    change_iteration: 1

context:
  purpose: >
    Three small independent faults, found by reading the logs pulled
    from gtach.local on 2026-08-05.

    (a) The Debug control on the options screen reports success and does
    nothing. gtach/__init__.py:11 binds the name 'main' to the
    function, so app.py's 'from . import main as _main' retrieves the
    function and _main._debug_handler raises AttributeError. The same
    pattern breaks _finish_startup_logging, so start.log is never closed
    and grew to 3.5 MB in one session while debug.log stayed at 0 bytes.

    (b) assets/engine_profiles.yaml is not in the wheel — package-data
    names fonts only — so the application warns at every start and falls
    back to built-in defaults.

    (c) _draw_update_view still renders 'Long press to return' after
    change-3e8b1d72 made long press inert.
  integration: >
    Three files: src/gtach/app.py, pyproject.toml and
    src/gtach/display/manager.py. Executor is Claude Code; AEL is not
    used.

    ON-TARGET EVIDENCE for (a), logs/start.log 2026-08-05 07:59, three
    presses and three identical failures:

      07:59:38,814  DisplayManager INFO  Debug logging toggle -> on
      07:59:38,815  gtach.app DEBUG      Could not toggle debug logging:
                                         'function' object has no attribute '_debug_handler'

    THE FAULT IS SELF-CONCEALING. Both app.py sites wrap the access in
    try/except and log at DEBUG — and one of them is the control that
    turns DEBUG on. That is why it went unnoticed and why the operator
    reported the toggle as working: the label flips because
    _debug_logging_on is inverted before the callback is invoked.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/app.py, pyproject.toml and src/gtach/display/manager.py."
    - "Do NOT modify src/gtach/__init__.py. Removing 'from .main import main' would fix the shadowing at source and is deliberately rejected: the name is the package's public surface and the console entry point uses it."
    - "Do NOT modify src/gtach/main.py. Its globals are correct."
    - "Do NOT narrow or remove the try/except wrappers at either app.py site. They conceal the failure, but narrowing them is a separate judgement; the fault they concealed is what this change removes."
    - "Do NOT change _debug_logging_on's initial value at manager.py:77. Out of scope — see change-c1d4b8e6 risks."
    - "Do NOT change any engine profile VALUE. Only the packaging changes."
    - "Do NOT attempt to fix the OBD response desynchronisation visible in the same log. Unrelated and more serious; it has its own cycle."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Retrieve gtach.main from sys.modules at both app.py sites; add
    assets/*.yaml to package-data; correct the update view's footer.
  requirements:
    functional:
      - "toggle_debug_logging reaches gtach.main._debug_handler and sets its level."
      - "_finish_startup_logging reaches gtach.main._start_handler and demotes it."
      - "Neither raises AttributeError."
      - "No 'from . import main' remains anywhere in the repository."
      - "A built wheel contains gtach/assets/engine_profiles.yaml."
      - "_draw_update_view renders 'Swipe up to return'."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.9 on the Pi)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Negligible. A dict lookup replaces a failing attribute access on paths that run at human rates or once per start"
      metric: "time"

design:
  architecture: >
    A package that re-exports a submodule's member under the
    submodule's own name shadows it, and no amount of attribute
    traversal will reach past that. The module object is retrievable
    from sys.modules, which the import system populates under the full
    dotted name regardless of what the package namespace was later
    rebound to.
  components:
    - name: "GTachApplication.toggle_debug_logging"
      type: "function"
      purpose: "Turn debug.log on and off at runtime."
      logic:
        - "Retrieve the module: _main = sys.modules.get('gtach.main')."
        - "Return if it is None, matching the existing guard style."
        - "Everything after — the None check on _debug_handler, the setLevel calls, the log lines — is unchanged."
    - name: "GTachApplication._finish_startup_logging"
      type: "function"
      purpose: "Demote start.log once startup completes."
      logic:
        - "Same retrieval. Same following logic."
    - name: "package-data"
      type: "configuration"
      purpose: "Ship the assets the application reads."
      logic:
        - "Add 'assets/*.yaml' beside the two font globs."
    - name: "DisplayManager._draw_update_view"
      type: "function"
      purpose: "Instruct the gesture that works."
      logic:
        - "'Long press to return' becomes 'Swipe up to return'."
  dependencies:
    internal:
      - "src/gtach/__init__.py:11 — the cause. Read-only."
      - "src/gtach/main.py:18-19 — defines both handlers. Read-only."
      - "change-3e8b1d72 — corrected _draw_options_menu's footer; EDIT C covers the one it missed."
    external:
      - "setuptools package-data — build time only."

error_handling:
  strategy: >
    Unchanged. The existing guards and try/except blocks stay exactly as
    they are; what changes is that the code inside them now reaches the
    object it was always reaching for.
  exceptions:
    - exception: "AttributeError"
      condition: "Should no longer be reachable from either site."
      handling: "The existing try/except remains as a net. If it fires again the fix is incomplete."
  logging:
    level: "Unchanged"
    format: "Existing"

testing:
  unit_tests:
    - scenario: "THE DISCRIMINATING TEST. toggle_debug_logging(True) with gtach.main._debug_handler set to a real logging.Handler."
      expected: "The handler's level becomes logging.DEBUG."
    - scenario: "The same test against the PRE-CHANGE file."
      expected: "The handler's level is UNCHANGED and an AttributeError is caught internally. Run both ways and record both — a test passing against both proves nothing."
    - scenario: "toggle_debug_logging(False)."
      expected: "The handler's level becomes logging.CRITICAL + 1."
    - scenario: "toggle_debug_logging with gtach.main._debug_handler set to None."
      expected: "Returns without raising; the existing guard."
    - scenario: "toggle_debug_logging on a non-Linux sys.platform."
      expected: "Returns early, unchanged from today."
    - scenario: "_finish_startup_logging with _start_handler set."
      expected: "Its level becomes CRITICAL + 1."
    - scenario: "grep -rn 'from . import main' across the repository."
      expected: "No occurrence. Grep the repository, not just app.py — a third site may exist."
    - scenario: "python -m build (or the project's build script), then list the wheel's assets."
      expected: "gtach/assets/engine_profiles.yaml present alongside gtach/assets/fonts/Michroma-Regular.ttf."
    - scenario: "load_engine_profile('abarth_595_turismo') against the packaged file, compared field by field with the RPMBands dataclass defaults."
      expected: "Identical — six thresholds 999, 3000, 4500, 5500, 5800, 6000. This asserts that packaging the file changes no displayed value."
    - scenario: "load_engine_profile('generic_na_4cyl')."
      expected: "Thresholds DIFFERENT from the defaults. This is the only assertion that proves the file is genuinely being read rather than the fallback still running."
    - scenario: "load_engine_profile with the file absent."
      expected: "WARNING and fallback, unchanged."
    - scenario: "_draw_update_view's footer string."
      expected: "'Swipe up to return'."
    - scenario: "grep 'Long press to return' across src/gtach."
      expected: "No occurrence outside manager_backup.py and setup_original_backup.py."
  edge_cases:
    - "sys.modules.get('gtach.main') returns None if gtach.main was never imported. It always has been by the time app.py runs — app.py is reached through it — but the guard is kept because a test importing app.py in isolation could hit it."
    - "importlib.import_module('gtach.main') is an equally correct retrieval and returns the sys.modules entry. Either is acceptable; state which was used."
    - "Do NOT write 'import gtach.main' followed by 'gtach.main._debug_handler'. That is an attribute lookup on the package and fails exactly as the current code does. This is the trap; it looks right."
    - "Do NOT write 'from .main import _debug_handler'. It binds None at import time and main.py rebinds the global later."
    - "The wheel test requires an actual build. Listing src/gtach/assets/ proves nothing about packaging."
    - "After this lands, start.log will be much smaller and debug.log will carry the DEBUG output. That is the fix working — see the deployment note."
  validation:
    - "grep confirms no 'from . import main' remains."
    - "git diff confirms src/gtach/__init__.py and src/gtach/main.py are untouched."
    - "The built wheel's namelist contains the YAML."

deliverable:
  format_requirements:
    - "Edit the three files in place. Create no new file."
    - "One commit."
  files:
    - path: "src/gtach/app.py"
      content: |
        EDIT A — both sites.

        Grep the repository for 'from . import main' first. Two sites
        are known, in toggle_debug_logging and in
        _finish_startup_logging. Correct every site found.

        At each, replace:

                from . import main as _main

        with:

                # gtach/__init__.py re-exports the main FUNCTION under
                # the name 'main', so the package attribute shadows the
                # module and 'from . import main' retrieves the
                # function — whose namespace has no _debug_handler or
                # _start_handler. The module object is retrievable from
                # sys.modules, which the import system keys by the full
                # dotted name (issue-c1d4b8e6).
                _main = sys.modules.get('gtach.main')
                if _main is None:
                    return

        'import sys' is already present in toggle_debug_logging; confirm
        it is available at the other site and add it if not, following
        the file's existing import placement.

        Change NOTHING else in either method. The platform guard, the
        None check on the handler, the setLevel calls, the log lines and
        the surrounding try/except all stay exactly as they are — the
        code inside them was always correct, it simply never reached the
        module.

        Note for the commit message: state whether sys.modules.get or
        importlib.import_module was used. Both are correct.
    - path: "pyproject.toml"
      content: |
        EDIT B. At pyproject.toml:68-69:

            [tool.setuptools.package-data]
            "gtach" = ["assets/fonts/*.ttf", "assets/fonts/*.otf"]

        becomes:

            [tool.setuptools.package-data]
            # assets/*.yaml carries engine_profiles.yaml, which
            # load_engine_profile reads at startup. Its absence made two
            # of three engine profiles unreachable and the
            # engine_profile setting inert, and produced a WARNING on
            # every start (issue-c1d4b8e6). The fonts glob dates from
            # issue-d7f2b4e6, the same class of defect.
            "gtach" = [
                "assets/fonts/*.ttf",
                "assets/fonts/*.otf",
                "assets/*.yaml",
            ]

        Change nothing else in the file. Then BUILD A WHEEL and list its
        contents — the declaration is not the test.
    - path: "src/gtach/display/manager.py"
      content: |
        EDIT C. At manager.py:1672, inside _draw_update_view:

            self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, "Long press to return", small_font, (150, 150, 150), (240, 410), center=True)

        The string "Long press to return" becomes "Swipe up to return".

        change-3e8b1d72 removed the long-press mode change from both
        handler paths and corrected the identical footer in
        _draw_options_menu; this one was outside that prompt's stated
        scope and its executor reported it at §6.2 of the
        implementation report rather than exceeding scope.

        Change nothing else — not the font, not the colour, not the
        position, not the surrounding guard.

success_criteria:
  - "python -m py_compile src/gtach/app.py src/gtach/display/manager.py passes."
  - "pyproject.toml parses as valid TOML."
  - "pytest tests/ passes with no new failures."
  - "grep -rn 'from . import main' across the repository returns no match."
  - "toggle_debug_logging(True) sets gtach.main._debug_handler's level to DEBUG; the same test against the pre-change file leaves it unchanged. Both results recorded."
  - "toggle_debug_logging(False) sets it to CRITICAL + 1."
  - "_finish_startup_logging demotes gtach.main._start_handler."
  - "Neither method raises AttributeError."
  - "A freshly built wheel contains gtach/assets/engine_profiles.yaml."
  - "load_engine_profile('abarth_595_turismo') returns thresholds identical to the RPMBands dataclass defaults."
  - "load_engine_profile('generic_na_4cyl') returns thresholds that differ from the defaults."
  - "_draw_update_view renders 'Swipe up to return'."
  - "'Long press to return' does not appear in src/gtach outside the two backup files."
  - "src/gtach/__init__.py and src/gtach/main.py are byte-identical to their current text."
  - "manager.py:77's _debug_logging_on initialisation is byte-identical."
  - "No file other than the three named above is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "app"
        path: "src/gtach/app.py"
      - name: "main"
        path: "src/gtach/main.py"
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "config"
        path: "src/gtach/utils/config.py"
    classes:
      - name: "GTachApplication"
        module: "gtach.app"
      - name: "DisplayManager"
        module: "gtach.display.manager"
    functions:
      - name: "toggle_debug_logging"
        module: "gtach.app"
        signature: "toggle_debug_logging(self, enable: bool) -> None"
      - name: "_finish_startup_logging"
        module: "gtach.app"
        signature: "_finish_startup_logging(self) -> None"
      - name: "_draw_update_view"
        module: "gtach.display.manager"
        signature: "_draw_update_view(self) -> None"
      - name: "load_engine_profile"
        module: "gtach.utils.config"
        signature: "load_engine_profile(profile_name: str)"
    constants:
      - name: "_debug_handler"
        module: "gtach.main"
      - name: "_start_handler"
        module: "gtach.main"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-c1d4b8e6-packaging-logging-housekeeping.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results. Then, once you are finished, write
  a report of what you have done in the ai/workspace/report folder.

  EDIT A has two attractive wrong answers, both of which compile and
  both of which fail exactly as the current code does. 'import
  gtach.main' then 'gtach.main._debug_handler' is an attribute lookup on
  the shadowing package. 'from .main import _debug_handler' binds None
  at import time. Only a sys.modules retrieval reaches the module.

  EDIT B's test is a built wheel. Listing the source tree proves
  nothing — the file has been in src/gtach/assets/ all along; what was
  missing was the instruction to ship it.

  Two things to expect on the target after this lands, neither a
  regression. start.log will be dramatically smaller, because
  _finish_startup_logging demotes it for the first time and steady-state
  DEBUG moves to debug.log where change-bd8f95b7 intended it. And no
  displayed value will change: the profile now read from the file
  carries the same six thresholds the built-in defaults did, which is
  why one of the success criteria asserts exactly that.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial prompt document coupled to change-c1d4b8e6. |

---

Copyright (c) 2026 William Watson. MIT License.
