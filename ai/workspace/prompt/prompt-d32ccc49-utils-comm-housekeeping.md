Created: 2026 July 30

# Prompt: Correct the Path Markers, Narrow the Queue Handlers, Warn on a Discarded Singleton Path

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-d32ccc49"
  task_type: "debug"
  source_ref: "change-d32ccc49"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-d32ccc49"
    change_iteration: 1

context:
  purpose: >
    Three independent housekeeping corrections. utils/home.py tests for a
    marker path src/obdii at three sites, left from before the rename to
    gtach, so none can ever match. comm/obd.py wraps the OBD sample
    handoff in except Exception rather than the queue exceptions its own
    comment names, so a genuine programming error is discarded as queue
    pressure. ConfigManager silently ignores a config_path supplied to a
    second construction.
  integration: >
    Three files: src/gtach/utils/home.py, src/gtach/comm/obd.py and
    src/gtach/utils/config.py. Four edits, none dependent on another.
    Executor is Claude Code; AEL is not used.

    CONFINEMENT — READ THIS FIRST. Task 7.4.1 deletes the ConfigManager
    device-persistence path in v0.4.0 under the decision recorded in
    ai/task.md §7.4.8. That region is utils/config.py:1417-1478 —
    get_device_by_address, add_or_update_device, remove_device — plus
    BluetoothConfig.saved_devices at utils/config.py:435 and its
    serialisation at 462 and 486-492. The §5.2 warning must be sited in
    ConfigManager.__init__ and must touch none of it, so the two changes
    do not collide (ai/task.md §7.6.1 and §8.3).

    utils/config.py has already been modified by change-1143427b, which
    corrected the RWLock notification path. Read the current text; the
    line numbers in this prompt are the corrected file's.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/utils/home.py, src/gtach/comm/obd.py and src/gtach/utils/config.py."
    - "Do NOT modify utils/config.py:1417-1478, or utils/config.py:435, 462 and 486-492. That is task 7.4.1's region."
    - "Do NOT modify the RWLock class in utils/config.py. It was corrected by change-1143427b."
    - "Do NOT modify ConfigManager.__new__. The warning goes in __init__, which can see both the supplied path and the held one."
    - "Do NOT change ConfigManager's singleton semantics. Warn; do not re-initialise, and do not raise."
    - "Do NOT rename the legacy obdii names: home.py:74-75, 90, 96-98, 204 and 210, and config.py:720, 752, 1133, 1268 and 1583. They are the installed data-location contract and the legacy-migration path. Renaming them would move an existing installation's configuration and logs."
    - "Do NOT change the discard-oldest policy at comm/obd.py:86-94. Narrow the handlers around it; leave the policy."
    - "Do NOT change the except Exception handlers at comm/obd.py:101, 136 and 150. §4.2 names only the queue block."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Point the three project-root and development-environment markers at
    src/gtach; import queue in comm/obd.py and catch queue.Full and
    queue.Empty at the three sample-handoff sites; warn from
    ConfigManager.__init__ when a supplied config_path has been
    discarded.
  requirements:
    functional:
      - "The string 'src/obdii' does not appear anywhere in src/gtach."
      - "_find_project_root treats 'src/gtach' as a project marker."
      - "_detect_development_environment tests for 'src/gtach' in the resolved __file__ and for project_root/src/gtach."
      - "_detect_development_environment returns True from a source checkout and False from an installed layout, unchanged from before."
      - "comm/obd.py imports the queue module."
      - "The two put_nowait handlers catch queue.Full; the get_nowait handler catches queue.Empty."
      - "An exception of any other type at those three sites propagates to the loop handler at obd.py:101."
      - "ConfigManager.__init__ logs one WARNING when config_path is supplied, force_new is false, the instance is already initialised, and the supplied path does not resolve to the held one."
      - "No WARNING when the paths resolve to the same file, when no path is supplied, when force_new is set, or on a first construction."
      - "The warning names both paths and the two ways to construct against a different file."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "No measurable change. The queue edit alters exception types, not the fast path"
      metric: "time"

design:
  architecture: >
    Three unrelated corrections in three files, deliberately not
    generalised. A marker names the layout that exists. A handler names
    the exception it expects, so an unexpected one reaches a handler that
    logs it. A constructor that cannot honour an argument says which
    argument and what it did instead.
  components:
    - name: "OBDIIHome._find_project_root"
      type: "function"
      purpose: "Locate the project root by marker."
      logic:
        - "Replace 'src/obdii' with 'src/gtach' in the markers list."
    - name: "OBDIIHome._detect_development_environment"
      type: "function"
      purpose: "Decide whether the package is running from source."
      logic:
        - "Replace the 'src/obdii' substring test with 'src/gtach'."
        - "Replace project_root / 'src' / 'obdii' with project_root / 'src' / 'gtach'."
    - name: "OBDProtocol._protocol_loop"
      type: "function"
      purpose: "Hand samples to the display without hiding programming errors."
      interface:
        raises:
          - "queue.Full and queue.Empty are handled locally; anything else reaches the loop handler at obd.py:101."
      logic:
        - "except Exception -> except queue.Full at the two put_nowait sites."
        - "except Exception -> except queue.Empty at the get_nowait site."
    - name: "ConfigManager.__init__"
      type: "function"
      purpose: "Report a discarded config_path."
      interface:
        inputs:
          - name: "config_path"
            type: "Optional[str]"
            description: "Honoured on the first construction only."
          - name: "force_new"
            type: "bool"
            description: "Bypasses the singleton; unchanged."
        outputs:
          type: "None"
          description: "Unchanged."
        raises:
          - "None. The comparison is wrapped so it cannot itself fail the constructor."
      logic:
        - "Inside the existing double-initialisation guard, before its return."
        - "Warn only when config_path is not None and the instance already holds a config_path."
        - "Compare with os.path.abspath on both sides."
        - "Use a module-level logging.getLogger call, not self.logger, which may not yet exist on this path."
  dependencies:
    internal:
      - "ThreadManager.message_queue — core/thread.py:107, queue.Queue(maxsize=5). Read only; core/thread.py is not modified."
      - "ConfigManager.get_instance — utils/config.py:1554-1563 delegates to cls(config_path) and gains the warning without being modified."
    external:
      - "queue — stdlib; added to comm/obd.py's imports."

error_handling:
  strategy: >
    Narrow where the expected exception is known, so the unexpected one
    reaches a handler that logs it with a traceback. The new warning is
    itself wrapped, because a diagnostic must not be able to break the
    constructor it diagnoses.
  exceptions:
    - exception: "queue.Full"
      condition: "message_queue is at its maxsize of 5 when put_nowait is called."
      handling: "Discard the oldest and retry, exactly as now."
    - exception: "queue.Empty"
      condition: "message_queue is empty when the discard's get_nowait is called."
      handling: "Pass, exactly as now."
    - exception: "Exception"
      condition: "Anything raised while comparing the two config paths."
      handling: "Pass. The warning is a diagnostic and must not fail construction."
  logging:
    level: "WARNING"
    format: "logging.getLogger(f'{__name__}.ConfigManager').warning(...)"

testing:
  unit_tests:
    - scenario: "grep 'src/obdii' across src/gtach."
      expected: "No match."
    - scenario: "grep the legacy occurrences of 'obdii'."
      expected: "All present: home.py:74-75, 90, 96-98, 204, 210; config.py:720, 752, 1133, 1268, 1583."
    - scenario: "_find_project_root from the repository checkout."
      expected: "The repository root, as before."
    - scenario: "_find_project_root against a temporary tree containing only src/gtach."
      expected: "That root. The branch was dead before this change."
    - scenario: "_detect_development_environment from the repository checkout."
      expected: "True, as before."
    - scenario: "_detect_development_environment with no marker and no project root."
      expected: "False, as before."
    - scenario: "Fill a real queue.Queue(maxsize=5) and run the sample handoff."
      expected: "Oldest discarded, newest present — unchanged behaviour."
    - scenario: "put_nowait patched to raise TypeError."
      expected: "Propagates out of the narrowed handler to obd.py:101 and is logged with a traceback."
    - scenario: "get_nowait patched to raise TypeError during the discard."
      expected: "Propagates rather than being swallowed."
    - scenario: "ConfigManager('/tmp/a.yaml') then ConfigManager('/tmp/b.yaml')."
      expected: "One WARNING naming both; config_path stays '/tmp/a.yaml'; the same instance is returned."
    - scenario: "ConfigManager('/tmp/a.yaml') then ConfigManager('/tmp/a.yaml')."
      expected: "No WARNING."
    - scenario: "ConfigManager('/tmp/a.yaml') then ConfigManager()."
      expected: "No WARNING."
    - scenario: "ConfigManager('/tmp/a.yaml') then ConfigManager('./a.yaml') with cwd /tmp."
      expected: "No WARNING; the paths normalise to the same file."
    - scenario: "ConfigManager(path, force_new=True) after an existing instance."
      expected: "A distinct instance against the supplied path; no WARNING."
    - scenario: "reset_singleton() then ConfigManager('/tmp/b.yaml')."
      expected: "A fresh instance against '/tmp/b.yaml'; no WARNING."
  edge_cases:
    - "A first __init__ that failed between utils/config.py:1164 and 1167 leaves _initialized set and logger absent. The warning uses a module-level logger and reads config_path with getattr, so it cannot raise on that path."
    - "A relative config_path supplied from a different working directory than the first construction — abspath resolves both against the current directory, so a genuine difference is reported and an equivalence is not."
    - "os.path.abspath does not resolve symlinks. Two paths reaching the same file by different links warn. Accepted: a warning is advisory and a false positive here is cheap."
    - "In an installed wheel neither the old nor the new home.py marker matches, and _find_project_root meets neither .git nor pyproject.toml, so the correction changes nothing there."
    - "queue.Full and queue.Empty are both subclasses of Exception, so narrowing cannot widen what is caught."
  validation:
    - "grep confirms 'except Exception' does not appear between comm/obd.py:83 and 94."
    - "git diff confirms utils/config.py:1417-1478 and 435, 462, 486-492 are untouched."

deliverable:
  format_requirements:
    - "Edit the three files in place. Create no new file."
    - "Apply the four edits below. Change nothing else."
  files:
    - path: "src/gtach/utils/home.py"
      content: |
        EDIT 1 — correct the three pre-rename markers

        At home.py:113-114, replace:

                # Look for project markers
                markers = ['pyproject.toml', 'setup.py', '.git', 'src/obdii']

        with:

                # Look for project markers. 'src/gtach' replaced
                # 'src/obdii', which was left from before the package was
                # renamed and could never match the current layout
                # (core review §5.4, recommendation #8).
                markers = ['pyproject.toml', 'setup.py', '.git', 'src/gtach']

        At home.py:127, replace:

                if 'src/obdii' in str(current_file):

        with:

                if 'src/gtach' in str(current_file):

        At home.py:134, replace:

                        project_root / "src" / "obdii",

        with:

                        project_root / "src" / "gtach",

        Change nothing else in the file. In particular leave the
        ~/.local/share/obdii and /opt/obdii data paths at home.py:74-75,
        90 and 96-98, the OBDIIHome class name, the _obdii_home singleton
        at home.py:210 and the OBDII_HOME environment variable at
        home.py:204 exactly as they are. Those are the installed
        data-location contract; renaming them would move an existing
        installation's configuration and logs.
    - path: "src/gtach/comm/obd.py"
      content: |
        EDIT 2 — import queue

        The import block at obd.py:14-17 currently reads:

            import logging
            import re
            import threading
            import time

        Add the queue module:

            import logging
            import queue
            import re
            import threading
            import time

        EDIT 3 — narrow the three handlers

        The block at obd.py:83-94 currently reads:

                            try:
                                self.thread_manager.message_queue.put_nowait(rpm_data)
                            except Exception:
                                # Queue full — discard oldest, insert newest
                                try:
                                    self.thread_manager.message_queue.get_nowait()
                                except Exception:
                                    pass
                                try:
                                    self.thread_manager.message_queue.put_nowait(rpm_data)
                                except Exception:
                                    pass

        Replace it with:

                            try:
                                self.thread_manager.message_queue.put_nowait(rpm_data)
                            except queue.Full:
                                # Queue full — discard oldest, insert newest.
                                # Narrowed from except Exception: a genuine
                                # programming error here was being counted as
                                # queue pressure and discarded, three times per
                                # sample (core review §4.2). Anything other
                                # than Full or Empty now reaches the loop's own
                                # handler below and is logged with a traceback.
                                try:
                                    self.thread_manager.message_queue.get_nowait()
                                except queue.Empty:
                                    pass
                                try:
                                    self.thread_manager.message_queue.put_nowait(rpm_data)
                                except queue.Full:
                                    pass

        message_queue is constructed as queue.Queue(maxsize=5) at
        core/thread.py:107, so queue.Full is genuinely reachable and the
        discard-oldest policy is doing real work. Leave that policy
        unchanged, and leave the except Exception handlers at obd.py:101,
        136 and 150 unchanged — §4.2 names only this block.
    - path: "src/gtach/utils/config.py"
      content: |
        EDIT 4 — warn when a supplied config_path is discarded

        __init__ currently begins, at utils/config.py:1116-1118:

                # Prevent double initialization of singleton
                if hasattr(self, '_initialized') and not force_new:
                    return

        Replace those three lines with:

                # Prevent double initialization of singleton
                if hasattr(self, '_initialized') and not force_new:
                    # __new__ returned the existing instance without
                    # consulting config_path, and this return leaves
                    # self.config_path as it was — so a caller asking for a
                    # different file silently receives the original
                    # configuration (core review §5.2). Say which path was
                    # discarded.
                    held = getattr(self, 'config_path', None)
                    if config_path is not None and held is not None:
                        try:
                            asked_abs = os.path.abspath(config_path)
                            held_abs = os.path.abspath(held)
                            if asked_abs != held_abs:
                                logging.getLogger(f'{__name__}.ConfigManager').warning(
                                    f"ConfigManager is a process-wide singleton: "
                                    f"requested config_path {asked_abs} was discarded; "
                                    f"the existing instance holds {held_abs}. Use "
                                    f"ConfigManager.reset_singleton() or force_new=True "
                                    f"to construct against a different file."
                                )
                        except Exception:
                            # A diagnostic must not be able to fail the
                            # constructor it diagnoses.
                            pass
                    return

        os and logging are already imported at module level in this file
        — os is used at utils/config.py:1130 and logging at 1167.

        Use logging.getLogger rather than self.logger. self.logger is
        assigned at utils/config.py:1167, after _initialized is set at
        1164, so a first construction that failed between those two lines
        would reach this path with no logger attribute.

        Change nothing else in the file. In particular:
          - ConfigManager.__new__ (utils/config.py:1094-1106) stays as it is
          - the RWLock class stays as it is; it was corrected by change-1143427b
          - utils/config.py:1417-1478 stays as it is; it is task 7.4.1's region
          - utils/config.py:435, 462 and 486-492 stay as they are, for the same reason
          - the ~/.obdii legacy migration paths at utils/config.py:1133 and
            1268 and the obdii_debug_ log filename pattern at 720, 752 and
            1583 stay as they are

success_criteria:
  - "python -m py_compile src/gtach/utils/home.py src/gtach/comm/obd.py src/gtach/utils/config.py passes."
  - "pytest tests/ passes with no new failures."
  - "'src/obdii' does not appear anywhere in src/gtach."
  - "The legacy obdii occurrences at home.py:74-75, 90, 96-98, 204 and 210 and at config.py:720, 752, 1133, 1268 and 1583 are unchanged."
  - "comm/obd.py imports queue."
  - "No 'except Exception' appears between comm/obd.py:83 and 94 after the edit."
  - "The except Exception handlers elsewhere in comm/obd.py are unchanged."
  - "ConfigManager.__init__ warns for a second construction with a different absolute path, and does not warn for the same path, no path, force_new, or a first construction."
  - "The warning uses logging.getLogger, not self.logger."
  - "ConfigManager.__new__ is byte-identical to its current text."
  - "The RWLock class in utils/config.py is byte-identical to its current text."
  - "utils/config.py:1417-1478 is byte-identical to its current text."
  - "utils/config.py:435, 462 and 486-492 are byte-identical to their current text."
  - "src/gtach/core/thread.py is unmodified."
  - "No file other than src/gtach/utils/home.py, src/gtach/comm/obd.py and src/gtach/utils/config.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "home"
        path: "src/gtach/utils/home.py"
      - name: "obd"
        path: "src/gtach/comm/obd.py"
      - name: "config"
        path: "src/gtach/utils/config.py"
      - name: "thread"
        path: "src/gtach/core/thread.py"
    classes:
      - name: "OBDIIHome"
        module: "gtach.utils.home"
      - name: "OBDProtocol"
        module: "gtach.comm.obd"
      - name: "ConfigManager"
        module: "gtach.utils.config"
      - name: "ThreadManager"
        module: "gtach.core.thread"
    functions:
      - name: "_find_project_root"
        module: "gtach.utils.home"
        signature: "_find_project_root(self) -> Optional[Path]"
      - name: "_detect_development_environment"
        module: "gtach.utils.home"
        signature: "_detect_development_environment(self) -> bool"
      - name: "_protocol_loop"
        module: "gtach.comm.obd"
        signature: "_protocol_loop(self) -> None"
      - name: "__init__"
        module: "gtach.utils.config"
        signature: "__init__(self, config_path: Optional[str] = None, force_new: bool = False)"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-d32ccc49-utils-comm-housekeeping.md
  and close the prompt when finished. Leave the issue and change active
  pending test results (ai/task.md §8.2.1).

  None of the three corrections is visible on the panel. The on-target
  step is a confirmation that nothing broke: the application starts, the
  configuration and log files are still where they were before the
  upgrade, and RPM is displayed. The configuration-location check is the
  one that matters, because it is the only way this change could go
  wrong on a real installation — and the reason the legacy obdii data
  paths are explicitly not touched.

  The confinement recorded at the head of this prompt is a governance
  requirement, not a preference. ai/task.md §8.3 states that this triple
  "sites the §5.2 singleton warning in ConfigManager.__new__ or
  __init__ and touches no device-persistence code, so it does not
  collide with the 7.4.1 retirement in v0.4.0". __init__ is chosen
  because it can see both the supplied path and the held one, which
  __new__ cannot before it returns.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-d32ccc49. |

---

Copyright (c) 2026 William Watson. MIT License.
