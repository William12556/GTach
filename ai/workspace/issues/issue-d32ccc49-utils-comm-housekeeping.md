Created: 2026 July 30

# Issue: Unreachable Pre-Rename Path Marker; Queue Handlers That Catch Everything; a Singleton That Discards the Path It Is Given

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-d32ccc49"
  title: "utils/home.py tests for a src/obdii marker that cannot match after the rename to gtach; comm/obd.py wraps queue operations in except Exception rather than queue.Full and queue.Empty; ConfigManager silently discards a config_path supplied to a second construction"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "resolved"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-d32ccc49"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/core-comm-utils-code-review.md v1.0, 2026-07-30.
    Finding §5.4 with §7.0 recommendation #8; finding §4.2 and finding
    §5.2, whose remedies are stated inside the findings because §7.0 is a
    selective list of eight items and omits them. The report's own
    numbering is preserved so coverage remains auditable after the report
    closes (ai/task.md §7.6.4). Task list reference ai/task.md §7.4.7.

affected_scope:
  components:
    - name: "OBDIIHome._find_project_root"
      file_path: "src/gtach/utils/home.py"
    - name: "OBDIIHome._detect_development_environment"
      file_path: "src/gtach/utils/home.py"
    - name: "OBDProtocol._protocol_loop"
      file_path: "src/gtach/comm/obd.py"
    - name: "ConfigManager.__init__"
      file_path: "src/gtach/utils/config.py"
  designs:
    - design_ref: "design-f8a9b0c1-component_utils_home"
    - design_ref: "design-e5f6a7b8-component_comm_obd_protocol"
    - design_ref: "design-b4c5d6e7-component_utils_config_manager"
  version: "0.2.67"

reproduction:
  prerequisites: >
    A GTach source checkout, and separately an installed wheel, so both
    environments can be observed.
  steps:
    - "#8 §5.4 — read utils/home.py:114. The marker list is ['pyproject.toml', 'setup.py', '.git', 'src/obdii']."
    - "#8 §5.4 — read utils/home.py:127. The test is \"if 'src/obdii' in str(current_file)\"."
    - "#8 §5.4 — read utils/home.py:134. The indicator is project_root / 'src' / 'obdii'."
    - "#8 §5.4 — list the repository's src directory and confirm it contains gtach and not obdii. No path under src/obdii exists, so none of the three can match."
    - "§4.2 — read comm/obd.py:83-94. Three handlers, at obd.py:85, 89 and 93, each 'except Exception'. The first and third guard put_nowait; the second guards get_nowait."
    - "§4.2 — read comm/obd.py:14-21 and confirm the queue module is not imported, so the specific exception types are not currently nameable in the file."
    - "§5.2 — read utils/config.py:1094-1106. __new__ returns cls._instance without consulting config_path."
    - "§5.2 — read utils/config.py:1117-1118. __init__ returns early when _initialized is set, so self.config_path is never revised."
    - "§5.2 — construct ConfigManager('/tmp/a.yaml'), then ConfigManager('/tmp/b.yaml'), and observe that the second returns the first instance with config_path still '/tmp/a.yaml' and nothing logged."
  frequency: "always"
  reproducibility_conditions: >
    §5.4 is unconditional and, being unreachable, has no observable
    runtime effect at all — which is what makes it dead code rather than
    a fault.

    §4.2 is unconditional in structure. It becomes consequential only
    when an exception other than queue.Full or queue.Empty is raised at
    those call sites, which is by definition a programming error and is
    exactly the case the current handlers hide.

    §5.2 requires two constructions with different paths in one process.
    The application constructs ConfigManager once, at app.py:32, and
    BluetoothPairing constructs a default one at comm/pairing.py:42, so
    the discard is currently silent because the second construction
    passes no path rather than because the paths agree.
  preconditions: >
    Raspberry Pi Zero 2W target for §4.2. §5.4 and §5.2 are observable on
    any platform.
  test_data: >
    §5.4 checked in both environments rather than asserted.

    In a source checkout __file__ resolves under
    <repo>/src/gtach/utils/home.py, so 'src/gtach' is a substring and
    'src/obdii' is not. _detect_development_environment nevertheless
    returns True today, through the .git and pyproject.toml fallbacks at
    utils/home.py:135-136. Correcting the marker therefore changes the
    branch that produces the answer, not the answer.

    In an installed wheel __file__ resolves under site-packages, where
    neither 'src/obdii' nor 'src/gtach' appears, and _find_project_root
    walks up without meeting .git or pyproject.toml. Neither the old
    marker nor the new one matches, so the correction is behaviour-
    preserving there as well.

    §4.2 message queue. core/thread.py:107 constructs it as
    queue.Queue(maxsize=5), so it is bounded and queue.Full is genuinely
    reachable at obd.py:84 and 92. The put/get/put sequence at
    obd.py:83-94 is a discard-oldest policy on a full queue.

    §5.2 line drift. The report cites "lines ~1077-1101". __new__ is at
    utils/config.py:1094-1106 and __init__ at 1108-1169 at 0.2.67, after
    change-1143427b altered RWLock earlier in the file. The discard
    itself is at utils/config.py:1117-1118.
  error_output: >
    None for any of the three. §5.4 produces no output because it never
    matches. §4.2 converts an output that should exist — an unexpected
    exception — into silence. §5.2 produces no output, which is the
    finding.

behavior:
  expected: >
    A marker test names a path that can exist. An exception handler
    catches the exceptions its comment describes and lets everything else
    through. A singleton that is handed an argument it will not honour
    says so.
  actual: >
    Three housekeeping defects across three files, grouped because each
    is small, each is confined to a few lines, and none interacts with
    the others.

    (a) #8, §5.4 — unreachable marker. utils/home.py:114, 127 and 134
    each test for a path containing 'obdii' under src, left from before
    the project was renamed from obdii to gtach. The current layout is
    src/gtach, so none of the three can ever match.
    _find_project_root still works through 'pyproject.toml', 'setup.py'
    and '.git' (utils/home.py:114), and _detect_development_environment
    still works through the .git and pyproject.toml indicators
    (utils/home.py:135-136), so nothing is broken — three tests are
    simply dead.

    (b) §4.2 — over-broad queue handlers. comm/obd.py:83-94 wraps
    message_queue.put_nowait and get_nowait in 'except Exception'. The
    comment at obd.py:86 reads "Queue full — discard oldest, insert
    newest", which names queue.Full precisely; the handler catches
    everything. An AttributeError, a TypeError or any other genuine
    programming error at those call sites is treated as ordinary queue
    pressure and discarded, in the one place in the application where
    OBD samples are handed to the display.

    (c) §5.2 — silently discarded config_path. ConfigManager is a
    process-wide singleton. __new__ (utils/config.py:1094-1106) returns
    the existing cls._instance without looking at config_path, and
    __init__ (utils/config.py:1108) returns at utils/config.py:1117-1118
    when _initialized is already set, before reaching the assignment at
    utils/config.py:1124-1127. A second construction with a different
    path therefore receives the original configuration with no warning
    and no error.
  impact: >
    (a) None at runtime. It is a maintenance hazard: a reader
    encountering three tests for a path that cannot exist has to
    establish for themselves whether the layout or the test is wrong.

    (b) Latent. It hides the class of fault that is hardest to find —
    an unexpected exception on a hot path, silently swallowed, three
    times per sample.

    (c) Latent, and most likely to be met under test or by a --config
    override issued after another component has already constructed a
    ConfigManager. The caller receives a configuration that is not the
    one it asked for and has no way to detect it.
  workaround: >
    (a) None needed. (b) None. (c) Call ConfigManager.reset_singleton()
    (utils/config.py:1566-1569) before constructing with a different
    path, or pass force_new=True (utils/config.py:1096-1099). Both exist
    and both are undiscoverable from the failure, which is the point.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) 6.1.21-v8+, Raspberry Pi Zero 2W"
  dependencies:
    - library: "CPython queue"
      version: "stdlib"
  domain: "domain_1"

analysis:
  root_cause: >
    (a) An incomplete rename. The package moved from obdii to gtach and
    three string literals did not, and because the tests fail closed
    rather than open, nothing surfaced.

    (b) A handler written to the shape of the code rather than to the
    exception it expects, at a site where the specific exception type was
    not importable without adding an import.

    (c) A singleton whose constructor accepts a parameter it can only
    honour on the first call. The double-initialisation guard at
    utils/config.py:1117 is correct and necessary; what is missing is
    the acknowledgement that an argument was thrown away.
  technical_notes: >
    CONFINEMENT, RECORDED BEFORE ANYTHING ELSE. ai/task.md §7.4.8 records
    the §7.5.4 decision taken on 2026-07-30: retire the ConfigManager
    device-persistence path. Task 7.4.1 performs that deletion in v0.4.0.
    §7.6.1 and ai/task.md §8.3 therefore require this triple's §5.2 edit
    to be sited in ConfigManager.__new__ or __init__ and to touch no
    device-persistence code, so the two do not collide. The same
    constraint is recorded as discharge step 6 in
    ai/workspace/report/task-list-cross-check-discrepancies.md §6.4.
    The edit specified here is a single guarded warning inside __init__,
    placed before the early return at utils/config.py:1117-1118. The
    device-persistence methods 7.4.1 will delete are
    get_device_by_address, add_or_update_device and remove_device at
    utils/config.py:1417-1478, together with BluetoothConfig.saved_devices
    at utils/config.py:435 and its serialisation at 462 and 486-492. Note
    that the report cites those methods as "lines 1414, 1430, 1458"; at
    0.2.67 the device.address references are at utils/config.py:1431,
    1447 and 1475. Nothing in this triple is within that region.

    utils/config.py has already been modified by change-1143427b, which
    corrected the RWLock notification path — _release_read now notifies
    both _write_ready and _read_ready. That change is implemented and
    closed. This issue is written against the corrected file, and the
    line numbers here are the corrected file's.

    THREE CORRECTIONS TO THE SOURCE REPORT.

    (1) §4.2 cannot be implemented as written without an import. The
    report's recommendation is "Catch queue.Full / queue.Empty
    specifically". comm/obd.py does not import queue — its imports are
    logging, re, threading and time, plus dataclass, Optional,
    OBDTransport and ThreadManager (obd.py:14-21). The names are not
    currently available in the module and 'import queue' must be added.
    The report cites the block as "lines ~84-94"; it is obd.py:83-94,
    and it contains three handlers rather than the two the recommendation
    implies: put_nowait at obd.py:84 and 92, get_nowait at obd.py:88.

    (2) §5.2's line reference has drifted. "Lines ~1077-1101" now covers
    the tail of the ConfigTransaction machinery. __new__ is at
    utils/config.py:1094-1106 and __init__ at 1108-1169.

    (3) §5.4's remedy is correct and its consequence is worth stating,
    because the report does not. Changing 'src/obdii' to 'src/gtach' does
    not merely remove dead code; it makes utils/home.py:127 and 134 live
    for the first time. Both were checked in a source checkout and
    against an installed layout, and the answer
    _detect_development_environment returns is unchanged in both — True
    in a checkout, via a different branch, and False when installed. The
    correction is behaviour-preserving, and that was established rather
    than assumed.

    ON THE OTHER OCCURRENCES OF 'obdii'. utils/home.py carries several
    more: the user data directory ~/.local/share/obdii (home.py:90), the
    system paths /opt/obdii, /usr/local/share/obdii and
    /usr/share/obdii (home.py:96-98), the docstring that describes them
    (home.py:74-75), the OBDIIHome class name, the module-level singleton
    _obdii_home (home.py:210) and the OBDII_HOME environment variable
    read at home.py:204. utils/config.py carries the legacy ~/.obdii
    migration path (config.py:1133, 1268) and the obdii_debug_ log
    filename pattern (config.py:720, 752, 1583). None of these is in
    §5.4's scope and none is corrected here: they are the installed
    data-location contract and the legacy-migration names, and renaming
    them would relocate an existing installation's configuration and logs
    and break the migration path that reads them. Recorded so the
    distinction is not lost.
  related_issues:
    - issue_ref: "issue-1143427b"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Replace the three src/obdii markers in utils/home.py with src/gtach.
    Import queue in comm/obd.py and narrow the three handlers to
    queue.Full and queue.Empty as each site requires. Add a guarded
    WARNING in ConfigManager.__init__, before the double-initialisation
    return, when a config_path is supplied that differs from the one the
    existing singleton holds. See change-d32ccc49.
  change_ref: "change-d32ccc49"
  resolved_date: "2026-07-31"
  resolved_by: "Claude Code, per prompt-d32ccc49"
  fix_description: >
    Four edits across the three files named in change-d32ccc49. One
    deviation from the prompt's literal comment text, described below.

    Fault 1, the stale markers. utils/home.py now names 'src/gtach' in the
    _find_project_root marker list, in the _detect_development_environment
    substring test, and in the directory probe under project_root. The
    legacy data-location and migration names are untouched: every
    obdii-bearing line other than those three markers is byte-identical,
    checked line for line against the previous file.

    Fault 2, the queue handlers. comm/obd.py imports queue and the three
    sample-handoff handlers catch queue.Full, queue.Empty and queue.Full
    respectively. The discard-oldest policy is unchanged, as are the four
    except Exception handlers elsewhere in the file.

    Fault 3, the discarded singleton path. ConfigManager.__init__ warns once
    when a config_path is supplied, force_new is false, the instance is
    already initialised, and the supplied path does not resolve to the held
    one. It uses a module-level logging.getLogger rather than self.logger,
    which does not exist on that path if a first construction failed between
    the _initialized assignment and the logger assignment, and the whole
    comparison is wrapped so the diagnostic cannot fail the constructor.

    DEVIATION. The prompt's EDIT 1 and EDIT 3 comment text contains the
    literal strings 'src/obdii' and 'except Exception', which two of its own
    success criteria forbid anywhere in src/gtach and anywhere in the edited
    obd.py block. The comments were reworded — "the stale pre-rename marker"
    and "a catch-all handler" — so both criteria hold literally and the
    explanation survives. Nothing but comment prose differs from the
    prescribed text.

verification:
  verified_date: "2026-07-31"
  verified_by: "Claude Code"
  test_results: >
    Development platform only (macOS, Python 3.11.14). The real OBDIIHome
    marker logic against synthetic directory trees, the real handoff block
    against a real queue.Queue, and the real ConfigManager singleton.
    Fifty-three assertions, all passing. See change-d32ccc49
    verification.test_results for the full record.

    All three faults were demonstrated before and after:

      1. _find_project_root against a tree whose only marker is src/gtach
         returned None — the branch was genuinely dead — and now returns
         that root. A tree carrying only the old src/obdii marker is
         correctly not matched.
      2. A TypeError raised by put_nowait was swallowed and counted as
         queue pressure; it now propagates to the loop's own handler.
      3. A second construction with a different path was silent; it now
         emits exactly one WARNING naming both paths. The instance
         returned and the held config_path are the same before and after,
         so nothing but the diagnostic changed.

    pytest tests/ — 11 passed, unchanged by this work.

    This issue is left active pending on-target results per ai/task.md
    §8.2.1. None of the three corrections is visible on the panel; the
    on-target step is a confirmation that nothing broke, and the
    configuration-location check is the one that matters.
  closure_notes: ""

prevention:
  preventive_measures: >
    A rename is not complete until the string literals that name the old
    identity are found as well as the symbols. A test that can never
    match is indistinguishable from a test that always fails, and neither
    is visible without being looked for. An exception handler names the
    exception it expects; 'except Exception' on a hot path is a decision
    that should be argued for in a comment.
  process_improvements: >
    The distinction drawn above — between the three stale markers and the
    many deliberate legacy 'obdii' names — is the kind of judgement a
    grep cannot make. It is recorded in this issue and in
    change-d32ccc49 so that a future reader who greps for 'obdii' does
    not undo it.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/utils/home.py src/gtach/comm/obd.py src/gtach/utils/config.py passes."
    - "grep confirms 'src/obdii' does not appear anywhere in src/gtach."
    - "grep confirms the data-path and legacy-migration occurrences of 'obdii' survive at home.py:74-75, 90, 96-98, 204, 210 and config.py:720, 752, 1133, 1268, 1583."
    - "Unit test: from a source checkout, confirm _find_project_root returns the repository root and _detect_development_environment returns True."
    - "Unit test: with a temporary tree containing only src/gtach and no .git or pyproject.toml, confirm _find_project_root finds it — the branch that was dead before this change."
    - "Unit test: with a path containing neither marker, confirm _detect_development_environment returns False."
    - "Unit test: fill the message queue to its maxsize of 5 and confirm the discard-oldest path runs and the newest sample is present."
    - "Unit test: make put_nowait raise TypeError and confirm it propagates to the loop's own handler at obd.py:101 and is logged with a traceback, rather than being swallowed."
    - "Unit test: construct ConfigManager('/tmp/a.yaml') then ConfigManager('/tmp/b.yaml'); confirm a WARNING naming both paths is logged and that config_path is unchanged."
    - "Unit test: construct ConfigManager('/tmp/a.yaml') then ConfigManager('/tmp/a.yaml'); confirm no WARNING."
    - "Unit test: construct ConfigManager('/tmp/a.yaml') then ConfigManager(); confirm no WARNING, since no path was requested."
    - "Unit test: construct ConfigManager('./a.yaml') from a directory where that resolves to the existing absolute path; confirm no WARNING."
    - "Unit test: confirm force_new=True and reset_singleton() still behave as they do today."
    - "Confirm utils/config.py:1417-1478 and utils/config.py:435, 462 and 486-492 are byte-identical, per the 7.4.1 confinement."
  verification_results: >
    Twelve of the fourteen steps are complete, one is met in substance with
    its stated expectation corrected, and one could not be reproduced from a
    source checkout.

    PASS — py_compile on all three files.

    PASS — 'src/obdii' does not appear in any .py file under src/gtach. The
    only remaining occurrence anywhere in the tree is inside a stale
    __pycache__ .pyc, which is build output and not source.

    PASS — every obdii-bearing line other than the three markers is
    byte-identical in both home.py and config.py, compared line for line
    against the previous file rather than by line number, since the numbers
    have drifted.

    PASS — from the source checkout _find_project_root returns the
    repository root and _detect_development_environment returns True.

    PASS — a temporary tree containing only src/gtach is now found. Against
    the previous file the same tree returned None, so the branch was dead
    exactly as the finding states. A tree carrying only the old marker is
    not matched.

    NOT REPRODUCIBLE — "_detect_development_environment returns False with
    no marker and no project root". It cannot return False from a source
    checkout: with no marker and no project root it falls through to the
    editable-mode test, which finds gtach under src/ and returns True. What
    was verified instead is that the fallback chain is unchanged from before
    the edit and that only the two marker lines differ. The step would hold
    in an installed layout, which is not available here.

    PASS — a real queue.Queue at maxsize 5 discards the oldest and admits
    the newest, giving [1, 2, 3, 4, 99]. The policy is unchanged.

    PASS — a TypeError from put_nowait propagates rather than being
    discarded, and so does a TypeError from get_nowait during the discard.
    Against the previous file the same TypeError was swallowed.

    PASS — a second construction with a different absolute path logs exactly
    one WARNING on the ConfigManager logger, naming both absolute paths and
    both escape hatches, and leaves config_path and the returned instance
    unchanged.

    PASS — the same path, and no path at all, each warn nothing.

    QUALIFIED — "construct ConfigManager('./a.yaml') from a directory where
    that resolves to the existing absolute path; confirm no WARNING". It
    holds, but only where the directory is not reached through a symlink. On
    macOS tempfile.mkdtemp returns /var/... while getcwd() after chdir
    returns /private/var/..., so os.path.abspath yields two different
    strings for one file and the warning fires. That is the false positive
    the change records under edge_cases as accepted; both behaviours are now
    asserted rather than one of them being glossed over. On Linux, where
    /tmp is a real directory, the step holds as written.

    PASS — force_new=True yields a distinct instance honouring the supplied
    path and warns nothing; reset_singleton() then a new path yields a fresh
    instance honouring it and warns nothing. A failure forced inside the
    diagnostic itself does not fail the constructor.

    PASS — the 7.4.1 confinement holds. ConfigManager.__init__ is the only
    method of that class that differs, __new__ is byte-identical, the RWLock
    class is byte-identical, BluetoothConfig is byte-identical, and the
    saved_devices occurrence count is unchanged.

    OUTSTANDING — on gtach.local, confirm the application starts, RPM is
    displayed, and the configuration and log files are still where they were
    before the upgrade. The last of those is the only way this change could
    go wrong on a real installation.

traceability:
  design_refs:
    - "design-f8a9b0c1-component_utils_home"
    - "design-e5f6a7b8-component_comm_obd_protocol"
    - "design-b4c5d6e7-component_utils_config_manager"
  change_refs:
    - "change-d32ccc49"
  test_refs: []

notes: >
  This is task 7.4.7 in ai/task.md §7.4 and part of step 5 in the
  recommended authoring order (§7.6.2). Released in v0.3.0 (§8.3).

  issue_info.type is defect per ai/task.md §7.2 as extended in v6.0, and
  per the discharge step recorded in
  ai/workspace/report/task-list-cross-check-discrepancies.md §5.4 item 3:
  §5.4 is unreachable code, which outranks §4.2 (performance) and §5.2
  (enhancement) under the highest-severity rule.

  §7.6.1 records two dependencies for this task, both on utils/config.py.
  7.4.9 (1143427b) has shipped and is closed, so this issue is written
  against the corrected RWLock. 7.4.1 (394c3bbb) ships in v0.4.0 and
  deletes the device-persistence path; the §5.2 warning is confined to
  ConfigManager.__init__ so the two do not collide.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial issue document from core-comm-utils-code-review.md findings §5.4, §4.2 and §5.2 with §7.0 recommendation #8."
      - "Recorded three corrections to the source report: §4.2's remedy requires an import queue that comm/obd.py does not have, and the block is obd.py:83-94 with three handlers; §5.2's line reference has drifted to utils/config.py:1094-1169; and §5.4's correction makes two dead tests live, which was checked in both a source checkout and an installed layout and is behaviour-preserving in each."
      - "Recorded the distinction between the three stale src/obdii markers and the deliberate legacy obdii data-path and migration names, which are not touched."
      - "Recorded the confinement of the §5.2 edit to ConfigManager.__init__ per ai/task.md §7.4.8 and §7.6.1."
  - version: "1.1"
    date: "2026-07-31"
    author: "Claude Code"
    changes:
      - "Status open -> resolved. change-d32ccc49 implemented; resolution date, executor and fix description recorded for all three faults."
      - "Recorded a before-and-after demonstration of each fault, including that _find_project_root returned None for a src/gtach-only tree and a TypeError at the queue handoff was swallowed."
      - "Recorded a deviation: the prompt's own comment text contains the two strings its success criteria forbid, so the comments were reworded."
      - "Recorded twelve of fourteen verification steps as PASS, one QUALIFIED for a symlink-dependent path comparison, and one NOT REPRODUCIBLE from a source checkout."
      - "Left active pending on-target test results per ai/task.md §8.2.1."

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
| 1.0 | 2026-07-30 | Initial issue document from core-comm-utils-code-review.md findings §5.4, §4.2 and §5.2 with §7.0 recommendation #8. Records three corrections to the source report, the boundary against the deliberate legacy `obdii` names, and the confinement of the §5.2 edit required by ai/task.md §7.4.8. |
| 1.1 | 2026-07-31 | Status open → resolved; fix description and per-step verification recorded, with each of the three faults demonstrated before and after. Left active pending on-target results. |

---

Copyright (c) 2026 William Watson. MIT License.
