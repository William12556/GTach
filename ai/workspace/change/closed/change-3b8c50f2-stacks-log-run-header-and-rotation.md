Created: 2026 August 12

# Change: Give stacks.log a Run Header and Rotate It Once Per Process

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-3b8c50f2"
  title: "Write an identifying run header on every arming of stack dumps, and rotate stacks.log once per process lifetime with three backups"
  date: "2026-08-12"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-3b8c50f2"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-3b8c50f2"
  description: >
    Resolves issue-3b8c50f2. stacks.log is opened in append mode and
    faulthandler's dumps carry no timestamp, PID or run identifier, so
    successive process lifetimes concatenate indistinguishably. The
    file also has no rotation or size cap, unlike debug.log.

scope:
  summary: >
    Two additions inside enable_stack_dumps in src/gtach/main.py, plus
    two module-level constants and one module-level flag. Write a
    header line identifying the process before arming, on every arm.
    Rotate an existing non-empty stacks.log on the first arm of a
    process lifetime only, keeping three backups.
  affected_components:
    - name: "enable_stack_dumps"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "_STACKS_BACKUPS, _stacks_rotated (new module-level names)"
      file_path: "src/gtach/main.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "Per-dump timestamps. Deliberately rejected; see rational.alternatives_considered. Any Python-side timestamp source would stall in precisely the window the file exists to capture."
    - "disable_stack_dumps. Its teardown order is load-bearing and correct. It writes no footer: a footer would be absent whenever a run ends by crash or force-exit, which are the interesting cases, so its presence would be misleading."
    - "The 15 s dump interval and _STACKS_LOG's path. Both unchanged."
    - "Any runtime size check. It would require a Python thread, which stalls. Growth is bounded per run by rotation at the next arm, and measured at ~145 KB per hour armed."
    - "debug.log and start.log handling in setup_logging. Unchanged."
    - "GTachApplication.toggle_debug_logging. Unchanged; it already calls enable_stack_dumps, which is where both additions land."

rational:
  problem_statement: >
    enable_stack_dumps (main.py:103-147) opens _STACKS_LOG with
    mode='a' and proceeds directly to faulthandler.enable and
    faulthandler.dump_traceback_later, writing nothing first.
    faulthandler introduces every dump with the identical literal
    "Timeout (0:00:15)!" and emits no timestamp, PID or run
    identifier.

    Dumps from successive process lifetimes therefore concatenate with
    nothing separating them. This bites hardest in the scenario the
    capability exists for: a watchdog-triggered restart, where the
    operator must distinguish the dumps that preceded termination from
    those that followed relaunch. change-2ac1c602 was written
    specifically to make that restart happen.

    Separately there is no rotation and no cap, where debug.log has
    both (_DEBUG_MAX_BYTES, _DEBUG_BACKUPS, issue-6a3b7c52). Measured
    growth from the 2026-08-12 file is 604 bytes per dump, four dumps
    per minute, ~145 KB per hour armed.
  proposed_solution: >
    1. RUN HEADER, on every arm. Immediately after opening the file and
    before faulthandler is armed, write one line:

      === gtach <version> pid <pid> armed <ISO-8601 local time> ===

    Every contiguous block of dumps is then attributable to a process
    and a wall-clock moment. This executes while the process is running
    normally — the operator has just enabled the toggle — so it cannot
    be lost to a stall, which is the property a per-dump timestamp
    would lack.

    The PID is deliberate and independently useful: a changed PID in a
    later header IS the systemd restart that issue-2ac1c602's
    verification step 3 requires evidence of.

    2. ROTATE ONCE PER PROCESS. On the first arm of a process
    lifetime, and only the first, rotate an existing non-empty
    stacks.log: shift stacks.log.2 to stacks.log.3, stacks.log.1 to
    stacks.log.2, stacks.log to stacks.log.1, discarding what was
    stacks.log.3. Guarded by a module-level _stacks_rotated flag.

    Rotation must be once per process, not once per arm. Arming happens
    on every OPTIONS toggle-on; rotating each time would let a few
    toggle cycles push the evidence just captured off the end of the
    backup chain. Within one run, re-arming appends after a fresh
    header, which the header alone makes legible.

    Append mode is retained. mode='w' is rejected: it would discard the
    previous run's dumps at relaunch, which is the opposite of the
    intent.
  alternatives_considered:
    - option: "Write a timestamp line before each dump, from a Python-side timer."
      reason_rejected: >
        The timer would be a Python thread, subject to the very stall
        the file exists to capture, so its markers would be missing
        from exactly the window that needs them. The entire value of
        faulthandler here is that its timer runs in C and is immune to
        that stall; a Python companion forfeits that property. A
        per-dump timestamp is also unnecessary: dump content is
        time-independent, and the fixed 15 s cadence combined with
        debug.log's bracketing entries places any dump to within ±15 s.
    - option: "Open stacks.log with mode='w' so each run starts clean."
      reason_rejected: >
        Discards the previous run's dumps at the moment of relaunch.
        After a watchdog-triggered restart the pre-termination dumps
        are the evidence being sought, and this would delete them.
    - option: "Rotate on every arm rather than once per process."
      reason_rejected: >
        Arming occurs on every OPTIONS toggle-on. Three toggle cycles
        would push a just-captured reproduction off the end of a
        three-deep backup chain.
    - option: "Use a RotatingFileHandler for stacks.log, as debug.log does."
      reason_rejected: >
        faulthandler writes to a file descriptor, not through the
        logging module. A logging handler cannot be given to
        faulthandler.dump_traceback_later, and interposing one would
        reintroduce the Python-side path that stalls.
    - option: "Check file size periodically and re-open when it exceeds a cap."
      reason_rejected: >
        Requires a Python thread, which stalls. Growth is modest and
        already bounded across runs by rotation at the next arm.
    - option: "Write a matching footer in disable_stack_dumps."
      reason_rejected: >
        A footer would be absent whenever a run ends by crash, watchdog
        force-exit or power loss — the interesting cases. Its presence
        would then imply an orderly end that did not occur, and its
        absence would be uninformative. The next header is the reliable
        boundary.
  benefits:
    - "Every contiguous block of dumps is attributable to a process and a wall-clock moment."
    - "A changed PID across two headers is direct evidence of a systemd restart, which issue-2ac1c602 verification step 3 needs."
    - "Cross-run accumulation is bounded at four files."
    - "The anchor is written at a moment when no stall can be in progress, so it cannot be lost to the condition being diagnosed."
    - "Brings stacks.log into line with the rotate-at-start treatment debug.log already receives."
  risks:
    - risk: >
        Rotation at arm time renames a file that a previous process may
        still hold open, if two GTach processes overlap.
      mitigation: >
        bin/gtach.service is Type=simple with a single ExecStart;
        systemd does not run two instances concurrently. On POSIX a
        rename does not disturb an open descriptor in any case: the
        older process would continue writing to the renamed inode,
        which remains readable as stacks.log.1. No data is lost.
    - risk: >
        importlib.metadata.version raises or is slow at arm time,
        delaying or preventing arming.
      mitigation: >
        Guard it exactly as parse_arguments already does
        (main.py:126-131), falling back to a literal when it fails.
        The whole header write is additionally wrapped so that a
        failure to write it never prevents arming — the dumps matter
        more than their label.
    - risk: >
        Rotation raises OSError on a full or read-only filesystem.
      mitigation: >
        Wrap rotation in its own try/except, print the existing style
        of warning to sys.stderr, and proceed to open and arm anyway.
        Failing to rotate must not cost the operator their dumps.
    - risk: >
        _stacks_rotated is read and written from more than one thread —
        setup_logging on the main thread at startup, the display thread
        via toggle_debug_logging thereafter.
      mitigation: >
        Single assignment from False to True, never back. A benign race
        could at worst rotate twice on two near-simultaneous first
        arms, which is harmless. No lock is warranted; adding one would
        introduce a Python-level lock into the arming path.

technical_details:
  current_behavior: >
    enable_stack_dumps opens stacks.log in append mode and arms
    faulthandler immediately. Nothing identifies the process, the time,
    or the boundary between runs. The file grows without bound and is
    never rotated.
  proposed_behavior: >
    On the first arm of a process, an existing non-empty stacks.log is
    rotated to stacks.log.1 with up to three backups retained. On every
    arm, a header line naming the gtach version, PID and ISO-8601 local
    time is written before faulthandler is armed. Dump production is
    otherwise unchanged.
  implementation_approach: >
    Additions confined to enable_stack_dumps and the module-level
    constant block in src/gtach/main.py. No new third-party
    dependencies; os and sys are already imported. datetime is added.
  code_changes:
    - component: "main module constants"
      file: "src/gtach/main.py"
      change_summary: >
        Add _STACKS_BACKUPS = 3 beside the existing _STACKS_LOG, with a
        comment recording the measured growth rate that justifies it.
        Add module-level _stacks_rotated = False beside _stacks_file.
      functions_affected: []
      classes_affected: []
    - component: "enable_stack_dumps"
      file: "src/gtach/main.py"
      change_summary: >
        Before opening the file, and only when _stacks_rotated is
        False, rotate an existing non-empty _STACKS_LOG through
        _STACKS_BACKUPS generations; set _stacks_rotated True
        regardless of outcome. After opening and before arming, write
        the run header. Both steps individually guarded so neither can
        prevent arming.
      functions_affected:
        - "enable_stack_dumps"
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "enable_stack_dumps"
      change_type: "contract"
      details: >
        Signature and return contract unchanged: () -> bool, True when
        armed on return including when already armed, False when the
        file could not be opened. Side effects extended with rotation
        and a header write, neither of which affects the return value.
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "GTachApplication.toggle_debug_logging"
      impact: >
        None. It already calls enable_stack_dumps and is not modified.
        Both additions land inside the callee.
    - component: "setup_logging"
      impact: >
        None beyond calling enable_stack_dumps as it already does under
        --debug. That call becomes the first arm of the process when it
        occurs, and so is the one that rotates.
  external:
    - library: "datetime (stdlib)"
      version_change: "none"
      impact: "New import in main.py for the header timestamp."
    - library: "importlib.metadata (stdlib)"
      version_change: "none"
      impact: "Used for the version string, guarded as in parse_arguments."
  required_changes:
    - change_ref: "change-2ac1c602"
      relationship: >
        blocked_by. This change modifies enable_stack_dumps, delivered
        by change-2ac1c602 iteration 2. That change is implemented; its
        parent issue remains active pending a stall reproduction.

testing_requirements:
  test_approach: >
    Unit tests against a monkeypatched _STACKS_LOG in tmp_path, plus
    on-target confirmation of the header and of the rotation boundary
    across a real restart.
  test_cases:
    - scenario: "enable_stack_dumps on a first arm with no pre-existing file."
      expected_result: "No rotation occurs; the file is created; its first line matches the header pattern and contains the current PID."
    - scenario: "enable_stack_dumps on a first arm with a pre-existing non-empty file."
      expected_result: "The old content is at stacks.log.1; the new file's first line is a header."
    - scenario: "enable_stack_dumps on a first arm with a pre-existing EMPTY file."
      expected_result: "No rotation; stacks.log.1 is not created."
    - scenario: "disable then enable within one process, after a first arm that rotated."
      expected_result: "No second rotation; stacks.log.1 is unchanged; a second header is appended to stacks.log."
    - scenario: "Four successive first-arms across four simulated process lifetimes."
      expected_result: "stacks.log.1 through stacks.log.3 exist; stacks.log.4 does not."
    - scenario: "enable_stack_dumps called twice with no intervening disable."
      expected_result: "Returns True both times; exactly one header is written; no second file handle is opened."
    - scenario: "Rotation raises OSError."
      expected_result: "A warning is printed to stderr; the file is still opened and armed; the function returns True."
    - scenario: "The header write raises."
      expected_result: "faulthandler is still armed; the function returns True."
    - scenario: "importlib.metadata.version raises."
      expected_result: "A header is still written, carrying the fallback version literal."
    - scenario: "On target: enable debug via OPTIONS after a service restart."
      expected_result: "A header appears carrying a PID matching `systemctl show gtach -p MainPID`, and the previous run's dumps are at stacks.log.1."
  regression_scope:
    - "Startup with --debug, which arms via setup_logging."
    - "The OPTIONS debug toggle, both directions, repeatedly within one run."
    - "disable_stack_dumps teardown ordering, which must remain cancel-then-disable-then-close."
    - "start.log and debug.log handling, which must be untouched."
    - "tests/test_stack_dump_toggle.py, which must continue to pass unmodified."
    - "tests/ suite in full."
  validation_criteria:
    - "No Python-side periodic timer is introduced anywhere."
    - "disable_stack_dumps is unchanged."
    - "_STACKS_LOG and the 15 s interval are unchanged."
    - "pytest tests/ passes."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Add _STACKS_BACKUPS and _stacks_rotated to the module-level block in main.py."
      owner: "tactical"
    - step: "Add the rotation block to enable_stack_dumps, guarded by _stacks_rotated and by its own try/except."
      owner: "tactical"
    - step: "Add the header write after the open and before faulthandler is armed, guarded by its own try/except."
      owner: "tactical"
    - step: "Add unit tests per testing_requirements.test_cases items 1-9."
      owner: "tactical"
    - step: "Deploy to gtach.local; confirm the header and the rotation boundary across a restart."
      owner: "human"
  rollback_procedure: >
    Revert the commit. One file is modified and the additions are
    self-contained. Existing stacks.log.N files are inert once the
    rotation code is gone and may be removed manually.
  deployment_notes: >
    /opt/gtach must be writable by the service user (root), which it
    already is for start.log, debug.log and stacks.log. No service,
    packaging or configuration change.

verification:
  implemented_date: "2026-08-12"
  implemented_by: "prompt-3b8c50f2 iteration 1 (claude_code)"
  verification_date: "2026-08-12"
  verified_by: "William Watson"
  test_results: >
    Unit: 18 tests in tests/test_stacks_log_rotation.py; full suite 92
    passed, 0 failed; tests/test_stack_dump_toggle.py passes
    unmodified.

    Source conformance confirmed: descending generation shift with
    os.replace, mode='a' retained, _stacks_rotated set in a finally
    clause, disable_stack_dumps unchanged, no Python-side periodic
    timer introduced.

    On target: three headers in /opt/gtach/stacks.log at lines 1, 33
    and 65, timestamped 12:06:54, 12:10:55 and 12:11:31, all carrying
    pid 725; stacks.log.1 present at 37287 bytes with no header, being
    pre-change content; no stacks.log.2 created. Header on every arm
    and rotation on first arm only, both as designed.

    Not observed on target: the three-generation cap. Only one rotation
    occurred, so stacks.log.4's non-creation rests on unit test alone.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-2ac1c602"
      relationship: >
        blocked_by. Delivered enable_stack_dumps, which this change
        extends.
    - change_ref: "change-6a3b7c52"
      relationship: >
        related. Established the rotate-at-start pattern and size cap
        for debug.log that this change adapts for a file faulthandler
        writes directly.
  related_issues:
    - issue_ref: "issue-3b8c50f2"
      relationship: "resolves"
    - issue_ref: "issue-2ac1c602"
      relationship: >
        related. Still active pending a reproduction of the ~52 s
        process-wide stall. The PID in this change's header supplies
        evidence for that issue's verification step 3.

notes: >
  The rejection of per-dump timestamps is recorded in
  alternatives_considered rather than left implicit, because it is the
  obvious first suggestion and the reason against it is not obvious: a
  Python-side timestamp source stalls in exactly the window the file
  exists to capture.

  No footer is written on disarm, for the same class of reason. A
  footer would be absent whenever a run ends by crash or force-exit —
  the interesting cases — so its presence would imply an orderly end
  that did not occur.

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-3b8c50f2 iteration 1."
      - "Run header on every arm; rotation once per process lifetime with three backups."
      - "Records the rejection of per-dump timestamps, of mode='w', of rotate-per-arm, of a RotatingFileHandler, of a runtime size check, and of a disarm footer, each with its reason."
  - version: "1.1"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Status proposed -> closed. Implemented by prompt-3b8c50f2 iteration 1; verification block completed."
      - "On-target observation confirmed a header on every arm and rotation on the first arm only; the three-generation cap remains unit-tested but unobserved."

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
| 1.0 | 2026-08-12 | Initial change document. Run header written on every arming of stack dumps; stacks.log rotated once per process lifetime with three backups. |
| 1.1 | 2026-08-12 | Status proposed -> closed. Implemented by prompt-3b8c50f2 iteration 1; verified by 18 unit tests and on-target observation of three headers with rotation on first arm only. |

---

Copyright (c) 2026 William Watson. MIT License.
