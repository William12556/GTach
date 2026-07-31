Created: 2026 July 30

# Change: Correct the Path Markers, Narrow the Queue Handlers, Warn on a Discarded Singleton Path

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-d32ccc49"
  title: "Replace the three src/obdii markers in utils/home.py with src/gtach; import queue in comm/obd.py and catch queue.Full and queue.Empty specifically; log a WARNING in ConfigManager.__init__ when a later construction supplies a different config_path"
  date: "2026-07-30"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-d32ccc49"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-d32ccc49"
  description: >
    Resolves issue-d32ccc49. Sourced from
    ai/workspace/report/core-comm-utils-code-review.md v1.0 findings
    §5.4, §4.2 and §5.2, and §7.0 recommendation #8. Task list reference
    ai/task.md §7.4.7.

scope:
  summary: >
    Three independent housekeeping corrections in three files. Point the
    project-root and development-environment markers at the current
    package name. Catch the two queue exceptions the OBD sample path
    actually expects instead of everything. Say when a config_path
    handed to a second ConfigManager construction has been discarded.
    Nothing here is coupled to anything else here; they are grouped
    because each is a few lines and each is a report item in the same
    review.
  affected_components:
    - name: "OBDIIHome._find_project_root"
      file_path: "src/gtach/utils/home.py"
      change_type: "modify"
    - name: "OBDIIHome._detect_development_environment"
      file_path: "src/gtach/utils/home.py"
      change_type: "modify"
    - name: "OBDProtocol._protocol_loop"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "ConfigManager.__init__"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-f8a9b0c1-component_utils_home"
      sections:
        - "Development environment detection"
    - design_ref: "design-b4c5d6e7-component_utils_config_manager"
      sections:
        - "Singleton construction"
  out_of_scope:
    - "THE 7.4.1 CONFINEMENT. The §5.2 warning is sited in ConfigManager.__init__ and touches no device-persistence code. utils/config.py:1417-1478 — get_device_by_address, add_or_update_device, remove_device — together with BluetoothConfig.saved_devices at utils/config.py:435 and its serialisation at 462 and 486-492 are the region task 7.4.1 deletes in v0.4.0 under the §7.5.4 retire decision (ai/task.md §7.4.8). None of it is modified. This satisfies discharge step 6 of ai/workspace/report/task-list-cross-check-discrepancies.md §6.4."
    - "The RWLock at utils/config.py:140-230. Corrected by change-1143427b, which is implemented and closed. This change is written against the corrected file and does not revisit it."
    - "The deliberate legacy obdii names. utils/home.py:74-75, 90, 96-98 (the ~/.local/share/obdii and /opt/obdii data paths), the OBDIIHome class name, the _obdii_home singleton at home.py:210 and the OBDII_HOME environment variable at home.py:204; utils/config.py:1133 and 1268 (the ~/.obdii legacy migration path) and 720, 752 and 1583 (the obdii_debug_ log filename pattern). These are the installed data-location contract and the legacy-migration names. Renaming them would relocate an existing installation's configuration and logs and break the migration that reads them. §5.4 does not ask for it."
    - "OBDProtocol's discard-oldest policy itself (comm/obd.py:86-94). Whether a full queue should drop the oldest sample is a design question; this change narrows the handlers around that policy and leaves the policy alone."
    - "The other except Exception handlers in comm/obd.py — obd.py:101, 136 and 150. Each guards a broad region rather than a single queue call and none is named by §4.2."
    - "Making ConfigManager honour a second config_path, by re-initialising or by raising. §5.2 asks for a warning. Changing the singleton's semantics is a behavioural change deserving its own cycle, and it would collide with 7.4.1's work in the same class."
    - "ConfigManager.get_instance (utils/config.py:1554-1563) and reset_singleton (utils/config.py:1566-1569). get_instance delegates to cls(config_path) and therefore inherits the warning for free."

rational:
  problem_statement: >
    utils/home.py tests for a marker path 'src/obdii' at three sites —
    home.py:114, 127 and 134 — left from before the rename to gtach. The
    layout is src/gtach, so none can match; the surrounding logic works
    through its other markers and the three tests are dead.

    comm/obd.py:83-94 wraps message_queue.put_nowait and get_nowait in
    'except Exception' at obd.py:85, 89 and 93. The comment at obd.py:86
    names queue fullness precisely; the handlers catch every exception,
    so a genuine programming error on the OBD sample path is discarded as
    ordinary queue pressure.

    ConfigManager.__new__ returns the existing instance without
    consulting config_path (utils/config.py:1094-1106) and __init__
    returns early at utils/config.py:1117-1118, so a second construction
    with a different path silently receives the original configuration.
  proposed_solution: >
    Replace the three markers with 'src/gtach'. Add 'import queue' to
    comm/obd.py and narrow each of the three handlers to the exception
    its call site can raise — queue.Full for the two puts, queue.Empty
    for the get. Add a guarded WARNING at the head of
    ConfigManager.__init__, before the double-initialisation return, when
    a config_path is supplied that differs from the one held.
  alternatives_considered:
    - option: "Delete the three src/obdii markers rather than correcting them."
      reason_rejected: >
        §7.0 recommendation #8 says update, not remove, and the corrected
        markers are useful: home.py:127's substring test is the cheapest
        development-environment signal available and works without
        touching the filesystem. Deleting them would leave detection
        resting entirely on .git and pyproject.toml.
    - option: "Derive the marker from __package__ rather than hard-coding 'gtach'."
      reason_rejected: >
        It would survive the next rename, but it introduces indirection
        into three one-line tests to guard against an event that has
        happened once in the project's life. §5.4 asks for a literal.
    - option: "Catch queue.Full only, and leave the get_nowait handler broad."
      reason_rejected: >
        get_nowait on an empty queue raises queue.Empty and nothing else
        of interest. Leaving one of the three broad would preserve
        exactly the ambiguity the finding objects to.
    - option: "Import Full and Empty by name rather than the queue module."
      reason_rejected: >
        'import queue' matches core/thread.py:19, which constructs the
        queue being used here, so the two files name the same module the
        same way.
    - option: "Raise from ConfigManager.__init__ when the path differs."
      reason_rejected: >
        It would turn a latent fault into a hard failure on a path the
        application exercises at app.py:32 and comm/pairing.py:42. §5.2
        asks for a warning, and a warning is what a caller that did not
        mean it needs.
    - option: "Have the second construction re-initialise against the new path."
      reason_rejected: >
        That is a behavioural change to a process-wide singleton, and it
        would defeat the double-initialisation guard at
        utils/config.py:1117 that exists to stop exactly that. It also
        overlaps the region task 7.4.1 is about to rework.
    - option: "Compare the paths as given, without normalisation."
      reason_rejected: >
        A caller passing a relative path that resolves to the same file
        would be warned for nothing, and the warning would then be
        ignored. os.path.abspath on both sides makes the comparison mean
        what it says.
  benefits:
    - "Three tests that could never match now can, and the answer they produce is unchanged, so a reader is no longer left to work out which of the layout and the test is wrong."
    - "A genuine programming error on the OBD sample path now propagates to the loop's own handler and is logged with a traceback, instead of being counted as queue pressure three times per sample."
    - "A caller whose config_path was thrown away is told, in the process where it happened."
    - "None of the three changes the application's behaviour in normal operation, which is what makes them safe to ship together in v0.3.0."
  risks:
    - risk: >
        Correcting home.py:127 and 134 makes two previously dead branches
        live and changes what _detect_development_environment returns.
      mitigation: >
        Checked in both environments rather than assumed. In a source
        checkout the method already returned True through the .git and
        pyproject.toml indicators at home.py:135-136, so only the branch
        changes. In an installed wheel neither the old marker nor the new
        one appears in the path and _find_project_root meets neither
        .git nor pyproject.toml, so the result is False either way. Unit
        tests assert both.
    - risk: >
        Narrowing the queue handlers lets an exception escape that
        previously did not, stopping the polling loop.
      mitigation: >
        It does not escape the thread. The enclosing try at obd.py:69
        catches Exception at obd.py:101, logs with exc_info, updates the
        heartbeat and sleeps 1.0 s, so an unexpected exception now
        appears in the log and the loop continues. That is the intended
        outcome of the finding.
    - risk: >
        The ConfigManager warning fires spuriously for equivalent paths.
      mitigation: >
        Compared with os.path.abspath on both sides, and only when a
        config_path was actually supplied — a construction with no
        argument requests nothing and is not warned about. Tests cover
        the same path, a different path, no path, and a relative path
        that resolves to the same file.
    - risk: >
        self.logger does not exist on the early-return path.
      mitigation: >
        It is assigned at utils/config.py:1167, after _initialized is set
        at 1164, so a first __init__ that failed between those two lines
        would leave the attribute absent. The warning therefore uses a
        module-level logging.getLogger call rather than self.logger, so
        it cannot itself raise AttributeError.
    - risk: >
        This change collides with task 7.4.1's deletion in utils/config.py.
      mitigation: >
        The edit is a single block inside __init__, above
        utils/config.py:1118. 7.4.1's region is utils/config.py:1417-1478
        plus the saved_devices field and its serialisation. Disjoint, and
        a validation criterion asserts that region is byte-identical.

technical_details:
  current_behavior: >
    utils/home.py:114 lists 'src/obdii' among the project-root markers;
    home.py:127 tests whether 'src/obdii' is a substring of the resolved
    __file__; home.py:134 tests whether project_root / 'src' / 'obdii'
    exists. The layout is src/gtach, so all three fail.

    comm/obd.py:83-94 wraps the put/get/put discard-oldest sequence in
    three 'except Exception' handlers. The module does not import queue
    (obd.py:14-21).

    ConfigManager.__new__ returns cls._instance (utils/config.py:1101-1106)
    without reading config_path. __init__ returns at
    utils/config.py:1117-1118 when _initialized is set, before the path
    assignment at utils/config.py:1124-1127.
  proposed_behavior: >
    The three markers name src/gtach. The three queue handlers catch
    queue.Full, queue.Empty and queue.Full respectively. A second
    ConfigManager construction supplying a different absolute path logs
    one WARNING naming both paths and then behaves exactly as it does
    today.
  implementation_approach: >
    Four edits across three files, none dependent on another.

    src/gtach/utils/home.py

    EDIT 1 — replace 'src/obdii' with 'src/gtach' at home.py:114 and 127,
    and 'obdii' with 'gtach' in the path join at home.py:134. Add a short
    comment at home.py:114 recording that these were pre-rename markers,
    so the next reader does not have to establish it again.

    src/gtach/comm/obd.py

    EDIT 2 — add 'import queue' to the import block at obd.py:14-17.

    EDIT 3 — narrow the three handlers. obd.py:85 and obd.py:93 guard
    put_nowait and become 'except queue.Full'. obd.py:89 guards
    get_nowait and becomes 'except queue.Empty'. The comment at obd.py:86
    stays; it is now accurate rather than aspirational.

    src/gtach/utils/config.py

    EDIT 4 — insert a guarded WARNING at the head of __init__, before the
    existing double-initialisation return at utils/config.py:1117-1118.
    It fires only when config_path is not None, force_new is false, the
    instance is already initialised, and os.path.abspath of the supplied
    path differs from os.path.abspath of the held one. It uses a
    module-level logger rather than self.logger.
  code_changes:
    - component: "OBDIIHome"
      file: "src/gtach/utils/home.py"
      change_summary: >
        Point the three project-root and development-environment markers
        at src/gtach, the current layout.
      functions_affected:
        - "_find_project_root"
        - "_detect_development_environment"
      classes_affected:
        - "OBDIIHome"
    - component: "OBDProtocol"
      file: "src/gtach/comm/obd.py"
      change_summary: >
        Import queue and catch queue.Full and queue.Empty at the three
        sample-handoff sites instead of Exception.
      functions_affected:
        - "_protocol_loop"
      classes_affected:
        - "OBDProtocol"
    - component: "ConfigManager"
      file: "src/gtach/utils/config.py"
      change_summary: >
        Warn when a second construction supplies a config_path that the
        singleton will discard.
      functions_affected:
        - "__init__"
      classes_affected:
        - "ConfigManager"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "task 7.4.9 (1143427b)"
      impact: "Shipped and closed. utils/config.py has already been modified by it; this change is written against the corrected RWLock and does not touch it. ai/task.md §7.6.1 records the dependency."
    - component: "task 7.4.1 (394c3bbb)"
      impact: "Ships in v0.4.0 and deletes utils/config.py:1417-1478 plus the saved_devices field and serialisation. This change is confined to ConfigManager.__init__ so the two do not collide. ai/task.md §7.6.1 and §8.3 record the constraint."
    - component: "ThreadManager.message_queue"
      impact: "Read only. core/thread.py:107 constructs it as queue.Queue(maxsize=5), which is what makes queue.Full reachable. core/thread.py is not modified."
    - component: "ConfigManager.get_instance"
      impact: "utils/config.py:1554-1563 delegates to cls(config_path) and therefore gains the warning without being modified."
  external: []
  required_changes:
    - change_ref: "change-1143427b"
      relationship: "blocked_by"
    - change_ref: "change-394c3bbb"
      relationship: "related"

testing_requirements:
  test_approach: >
    Unit tests on the development platform. home.py is tested against
    temporary directory trees, since path detection is the subject.
    obd.py is tested with a real queue.Queue(maxsize=5), since the
    exception types are the subject and a mock would not raise them.
    config.py is tested by constructing and resetting the singleton
    around each case.
  test_cases:
    - scenario: "grep for 'src/obdii' across src/gtach."
      expected_result: "No match."
    - scenario: "grep for the data-path and legacy occurrences of 'obdii'."
      expected_result: "All survive: home.py:74-75, 90, 96-98, 204, 210 and config.py:720, 752, 1133, 1268, 1583."
    - scenario: "_find_project_root from the repository checkout."
      expected_result: "Returns the repository root, as before."
    - scenario: "_find_project_root against a temporary tree containing only src/gtach, with no .git and no pyproject.toml."
      expected_result: "Returns that root. The branch was dead before this change."
    - scenario: "_detect_development_environment from the repository checkout."
      expected_result: "True, as before — through the corrected substring test rather than through the .git indicator."
    - scenario: "_detect_development_environment with a path containing neither marker and no project root."
      expected_result: "False, as before."
    - scenario: "Fill a queue.Queue(maxsize=5) and run the sample-handoff sequence."
      expected_result: "The oldest sample is discarded and the newest is present, exactly as before."
    - scenario: "put_nowait patched to raise TypeError."
      expected_result: "Propagates out of the narrowed handler to the loop handler at obd.py:101, logged with a traceback. Before the change it was swallowed."
    - scenario: "get_nowait patched to raise TypeError during the discard."
      expected_result: "Same — propagates rather than being swallowed."
    - scenario: "ConfigManager('/tmp/a.yaml') then ConfigManager('/tmp/b.yaml')."
      expected_result: "One WARNING naming both paths; config_path remains '/tmp/a.yaml'; the same instance is returned."
    - scenario: "ConfigManager('/tmp/a.yaml') then ConfigManager('/tmp/a.yaml')."
      expected_result: "No WARNING."
    - scenario: "ConfigManager('/tmp/a.yaml') then ConfigManager()."
      expected_result: "No WARNING. No path was requested, so none was discarded."
    - scenario: "ConfigManager('/tmp/a.yaml') then ConfigManager('./a.yaml') from /tmp."
      expected_result: "No WARNING. The paths normalise to the same file."
    - scenario: "ConfigManager(path, force_new=True) after an existing instance."
      expected_result: "A distinct instance initialised against the supplied path; no WARNING."
    - scenario: "reset_singleton() then ConfigManager('/tmp/b.yaml')."
      expected_result: "A fresh instance against '/tmp/b.yaml'; no WARNING."
    - scenario: "First construction, no prior instance."
      expected_result: "No WARNING under any argument."
  regression_scope:
    - "pytest tests/ — no new failures."
    - "Manual: gtach --validate-dependencies still reports a platform."
    - "Manual on target: the application starts, writes its configuration to the same location as before, and the log directory is unchanged."
    - "Manual on target: RPM is displayed, confirming the sample-handoff path still works under load."
  validation_criteria:
    - "python -m py_compile src/gtach/utils/home.py src/gtach/comm/obd.py src/gtach/utils/config.py passes."
    - "'src/obdii' does not appear anywhere in src/gtach."
    - "comm/obd.py imports queue."
    - "No 'except Exception' remains inside the sample-handoff block at comm/obd.py:83-94."
    - "The except Exception handlers at obd.py:101, 136 and 150 are unchanged."
    - "utils/config.py:1417-1478 is byte-identical."
    - "utils/config.py:435, 462 and 486-492 are byte-identical."
    - "The RWLock class in utils/config.py is byte-identical."
    - "ConfigManager.__new__ is byte-identical; the warning is in __init__."
    - "The warning uses a module-level logger, not self.logger."
    - "No file other than src/gtach/utils/home.py, src/gtach/comm/obd.py and src/gtach/utils/config.py is modified."

implementation:
  implementation_steps:
    - step: "EDIT 1 — correct the three markers in utils/home.py."
      owner: "Claude Code"
    - step: "EDIT 2 — import queue in comm/obd.py."
      owner: "Claude Code"
    - step: "EDIT 3 — narrow the three queue handlers."
      owner: "Claude Code"
    - step: "EDIT 4 — add the discarded-path warning to ConfigManager.__init__."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Unit tests against temporary trees, a real bounded queue and the singleton."
      owner: "Claude Code"
    - step: "Confirm the 7.4.1 confinement by diffing utils/config.py and checking the device-persistence region is untouched."
      owner: "Claude Code"
    - step: "Deploy to gtach.local; confirm startup, configuration location and RPM display."
      owner: "William Watson"
  rollback_procedure: >
    Three files, one commit. git revert restores the previous behaviour.
    No data, configuration or interface migration is involved — in
    particular no configuration or log file moves, because the data-path
    names are deliberately not touched.
  deployment_notes: >
    None of the three is visible on the panel. The on-target step is a
    confirmation that nothing broke, not an observation of a new effect.
    Check that the configuration and log files are still where they were
    before the upgrade, which is the one way this change could go wrong
    on a real installation.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-1143427b"
      relationship: "blocked_by"
    - change_ref: "change-394c3bbb"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-d32ccc49"
      relationship: "resolves"

notes: >
  Task 7.4.7 in ai/task.md §7.4, released in v0.3.0 (§8.3). Per §8.2.1
  this change is left active when the code lands, pending a passing T06
  result; only prompt-d32ccc49 closes on implementation.

  ai/task.md §8.3 states that this triple "sites the §5.2 singleton
  warning in ConfigManager.__new__ or __init__ and touches no
  device-persistence code, so it does not collide with the 7.4.1
  retirement in v0.4.0". __init__ is chosen over __new__ because the
  discard is observable there — __init__ can see both the supplied path
  and the held one, whereas __new__ has no instance state to compare
  against before it returns.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-d32ccc49."
      - "Records the 7.4.1 confinement as the first out_of_scope entry, with the exact region 7.4.1 will delete."
      - "Records the deliberate legacy obdii data-path and migration names as out of scope, with the reason renaming them would be harmful."
      - "Records why __init__ rather than __new__ is the site for the §5.2 warning."

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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-d32ccc49. Records the 7.4.1 confinement and its exact region, the boundary against the deliberate legacy `obdii` names, and why `__init__` is the site for the §5.2 warning. |

---

Copyright (c) 2026 William Watson. MIT License.
