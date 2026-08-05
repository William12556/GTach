Created: 2026 August 05

# Change: Roll the Log at Start, and Measure Against the Frame Rate in Use

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-6a3b7c52"
  title: "The debug handler takes a 10 MB cap with ten backups and rolls over once at startup when the file has content; PerformanceMonitor is constructed after _load_config with config.fps_limit instead of a hardcoded 60"
  date: "2026-08-05"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-6a3b7c52"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-6a3b7c52"
  description: >
    Resolves issue-6a3b7c52. Raised under P04 from the operator's
    specification of 2026-08-05 — 10 MB cap, rotate at start, ten
    versions — and from the hardcoded monitor target recorded in
    ai/task.md §9.11.7.4.

scope:
  summary: >
    Two small independent corrections in two files. The debug log gains
    a working rotation policy; the performance monitor learns the frame
    rate the application actually runs at.
  affected_components:
    - name: "setup_logging"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "_DEBUG_MAX_BYTES"
      file_path: "src/gtach/main.py"
      change_type: "modify"
    - name: "DisplayManager._initialize_components"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "DisplayManager.__init__"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "src/gtach/display/performance/monitor.py. Not modified. It already takes target_fps as a constructor argument; the defect is that the caller passes a literal."
    - "start.log and _start_handler. Its truncate-at-boot behaviour is correct and uses plain FileHandler, where mode='w' is honoured."
    - "The debug toggle path in app.py. change-c1d4b8e6 corrected it and it works."
    - "The sluggishness of ai/task.md §9.12. This change reduces SD write volume but does not establish that log I/O was the cause; the two candidates remain undistinguished. It must not be recorded as a fix for it."
    - "_debug_logging_on's initial value. Still out of scope, as change-c1d4b8e6 left it."
    - "The order of _initialize_components and _load_config generally. Only the monitor's construction moves; the rest of the ordering is untouched."

rational:
  problem_statement: >
    RotatingFileHandler discards mode='w' when maxBytes is set, so
    debug.log appends across every restart, and its 100 MB threshold
    has never been reached — the file grew to 43 MB across three
    sessions. Separately, PerformanceMonitor is constructed with a
    literal target_fps=60 because _initialize_components runs before
    _load_config, so at 30 Hz its frame target, history window and both
    alert thresholds are wrong.
  proposed_solution: >
    A 10 MB cap with ten backups and an explicit rollover at startup,
    per the operator's specification. The monitor constructed after the
    configuration is loaded, with the configured frame rate.
  alternatives_considered:
    - option: "Truncate at start — plain FileHandler with mode='w' and no rotation."
      reason_rejected: >
        Simplest, gives a clean per-session file, and loses the evidence
        of a crash at the moment the application restarts because of
        one. GTach runs under systemd with Restart=always, so this is
        not hypothetical. Rejected in favour of rotation, which gives
        the clean file and keeps the previous run."
    - option: "Keep appending and rely on the size threshold alone, reduced to 10 MB."
      reason_rejected: >
        Bounds the file without separating sessions, so every analysis
        continues to begin by working out which session a line belongs
        to — the cost paid throughout ai/task.md §9.11."
    - option: "Add a set_target_fps() method to PerformanceMonitor and call it after _load_config."
      reason_rejected: >
        target_fps is consumed during __init__ for frame_time_target,
        the history deque's maxlen and both alert thresholds
        (monitor.py:42, 50, 74-75). A setter would have to rebuild the
        deque and recompute the thresholds — more surface than moving
        one construction, in a file this change otherwise need not
        touch."
    - option: "Move _load_config before _initialize_components."
      reason_rejected: >
        Fixes the ordering at its root and risks more than it gains:
        other components built in _initialize_components may depend on
        the current order, and nothing here requires establishing that
        they do not. Moving the two monitor lines is the smaller
        change with the same effect."
  benefits:
    - "Each session's debug log is its own file, so an analysis no longer starts by segmenting on timestamps."
    - "The previous run survives a restart as debug.log.1, including a restart caused by a crash."
    - "Storage bounded at 110 MB rather than unbounded in practice."
    - "Dropped-frame counts and FPS alerts become correct at any configured frame rate."
    - "The startup line reports the real target rather than a constant."
  risks:
    - risk: >
        A restart loop consumes all ten backup slots and discards the
        evidence of the original fault.
      mitigation: >
        Checked rather than assumed: bin/gtach.service sets
        StartLimitIntervalSec=60 and StartLimitBurst=3, so systemd stops
        after three rapid starts. Ten slots is comfortable. Rotation is
        also skipped when the existing file is empty, so a restart
        before any debug output consumes no slot at all."
    - risk: >
        Rotating at start on a fresh install, where no debug.log exists,
        raises or creates spurious files.
      mitigation: >
        The rollover is conditional on the file existing and being
        non-empty, tested before the handler is constructed."
    - risk: >
        Moving the monitor's construction changes behaviour if anything
        between the two calls uses it.
      mitigation: >
        Nothing runs between them — manager.py:136 and :139 are
        consecutive statements — and _load_config does not reference the
        monitor. Asserted by test rather than by reading."
    - risk: >
        config.fps_limit is absent or zero, giving a division by zero in
        the monitor's frame_time_target.
      mitigation: >
        DisplayConfig defaults fps_limit to 60 and _load_config sets
        self.config on every path including its fallbacks. The
        construction guards against a non-positive value and falls back
        to the DisplayConfig default rather than propagating it."
    - risk: >
        Someone later reads this change as having fixed the
        sluggishness of §9.12.
      mitigation: >
        Stated in scope.out_of_scope and in the issue. The change
        reduces SD write volume; it does not establish that log I/O was
        the cause."
  benefits_measurement: >
    debug.log size across sessions: unbounded in practice, observed
    43 MB -> 10 MB per session, 110 MB total. Sessions per file: 3 -> 1.
    Correct dropped-frame threshold at 30 Hz: 25 ms -> 50 ms.

technical_details:
  current_behavior: >
    main.py:25 sets _DEBUG_MAX_BYTES to 100 MB. main.py:46-49 constructs
    RotatingFileHandler(_DEBUG_LOG, mode='w', maxBytes=_DEBUG_MAX_BYTES,
    backupCount=0), where the mode is discarded because maxBytes > 0.
    The handler's comment says the file is truncated at boot; it is not.
    manager.py:169, inside _initialize_components, constructs
    PerformanceMonitor(target_fps=60); manager.py:136 calls that method
    and :139 calls _load_config, so self.config does not yet exist.
  proposed_behavior: >
    The debug handler caps at 10 MB with ten backups and rolls over once
    at startup if the file has content, so each run begins clean and the
    previous ten survive. The monitor is constructed after _load_config
    with the configured frame rate.
  implementation_approach: >
    THREE EDITS, TWO FILES.

    EDIT A — main.py constants:

      _DEBUG_MAX_BYTES = 10 * 1024 * 1024
      _DEBUG_BACKUPS = 10

    EDIT B — main.py setup_logging. Record whether the file has content
    BEFORE constructing the handler, since construction opens it. Drop
    the mode argument, which is dead, and replace the misleading comment
    with one recording the actual behaviour. After construction, roll
    over if there was content.

    The rollover must come after the handler exists, because
    doRollover() operates on the handler's own stream: it closes the
    current file, shifts debug.log.N to N+1, renames debug.log to
    debug.log.1 and opens a fresh debug.log.

    EDIT C — manager.py. Remove the two monitor lines from
    _initialize_components and place them in __init__ immediately after
    self._load_config(), passing the configured rate:

      fps = getattr(self.config, 'fps_limit', 0) or 0
      if fps <= 0:
          fps = DisplayConfig.fps_limit          # the dataclass default
      self.performance_monitor = PerformanceMonitor(target_fps=fps)
      self.performance_monitor.start_monitoring()

    wrapped so a monitor failure is logged and does not prevent the
    display starting, matching the surrounding style.
  code_changes:
    - component: "setup_logging"
      file: "src/gtach/main.py"
      change_summary: >
        Debug handler capped at 10 MB with ten backups; the dead mode
        argument removed; an explicit rollover at startup when the file
        has content; the comment corrected.
      functions_affected:
        - "setup_logging"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        PerformanceMonitor construction moved out of
        _initialize_components to after _load_config, taking
        config.fps_limit with a guarded fallback.
      functions_affected:
        - "__init__"
        - "_initialize_components"
      classes_affected:
        - "DisplayManager"
  data_changes:
    - "debug.log.1 through debug.log.10 appear on the target. No existing file is read by the application; these are diagnostic output only."
  interface_changes: []

dependencies:
  internal:
    - component: "change-bd8f95b7"
      impact: "Established the two-file logging design. This corrects the debug file's rotation policy; start.log's behaviour is unchanged."
    - component: "change-c1d4b8e6"
      impact: "Made the debug toggle work, which is what makes debug.log fill at all. Not modified."
    - component: "change-0b00759c"
      impact: "Owns PerformanceMonitor and its frame bracketing. monitor.py is not modified; only the caller's argument changes."
    - component: "bin/gtach.service"
      impact: "Its StartLimitBurst=3 bounds how many backup slots a restart loop can consume. Read-only."
  external:
    - "logging.handlers.RotatingFileHandler — stdlib. Its mode override is the fault being worked around."
  required_changes:
    - change_ref: "change-c1d4b8e6"
      relationship: "related"

testing_requirements:
  test_approach: >
    Rotation is tested against real files in a temporary directory by
    calling setup_logging with the log paths redirected, since the
    behaviour is entirely filesystem-visible and a mock would test the
    mock. The monitor change is tested by constructing a DisplayManager
    headlessly and asserting the monitor's target.
  test_cases:
    - scenario: "Existing debug.log with content, then setup_logging."
      expected_result: "debug.log.1 holds the old content; debug.log is empty."
    - scenario: "No debug.log present."
      expected_result: "No exception; debug.log created; no .1 produced."
    - scenario: "Empty debug.log present."
      expected_result: "No rotation; no slot consumed."
    - scenario: "Eleven consecutive setup_logging calls, each writing a distinguishable line."
      expected_result: "debug.log plus .1 to .10; no .11; the oldest line is gone."
    - scenario: "Writing more than 10 MB within one session."
      expected_result: "In-session rotation occurs."
    - scenario: "handler.mode after construction."
      expected_result: "'a'. Asserted as expected behaviour, with the reason in a comment."
    - scenario: "_DEBUG_MAX_BYTES and the handler's backupCount."
      expected_result: "10 MB and 10."
    - scenario: "start.log across two setup_logging calls."
      expected_result: "Truncated each time; no start.log.1 produced. Its behaviour must not change."
    - scenario: "A read-only log directory."
      expected_result: "The existing OSError handler prints a warning and the application continues, unchanged."
    - scenario: "DisplayManager constructed with fps_limit 30 in configuration."
      expected_result: "performance_monitor.target_fps is 30."
    - scenario: "The same with fps_limit 60."
      expected_result: "60."
    - scenario: "With fps_limit 0 or absent."
      expected_result: "Falls back to the DisplayConfig default; no ZeroDivisionError."
    - scenario: "monitor.frame_time_target at fps_limit 30."
      expected_result: "1/30, so the dropped-frame threshold is 50 ms rather than 25."
    - scenario: "The startup log line at fps_limit 30."
      expected_result: "Reports 30, not 60."
    - scenario: "Nothing references self.performance_monitor between _initialize_components and _load_config."
      expected_result: "Asserted by constructing a DisplayManager with the monitor construction stubbed to record its call order."
    - scenario: "The display loop, record_frame_start/end and should_log_periodic."
      expected_result: "Unchanged behaviour."
  regression_scope:
    - "tests/ — the suite currently collects 11 tests; none should change."
    - "On the target: restart and confirm debug.log begins empty with the previous session in debug.log.1."
    - "On the target: confirm the startup line reports 30 FPS."
    - "On the target: confirm start.log still truncates and still closes after startup."
    - "On the target: confirm ten restarts leave ten backups and no more."
  validation_criteria:
    - "python -m py_compile on both files passes."
    - "pytest tests/ passes with no new failures."
    - "No mode argument is passed to RotatingFileHandler."
    - "PerformanceMonitor is not constructed inside _initialize_components."
    - "No literal 60 is passed as target_fps."
    - "src/gtach/display/performance/monitor.py is byte-identical."
    - "start.log's handler construction is byte-identical."

implementation:
  implementation_steps:
    - step: "Write the rotation test first — existing content, then setup_logging, expect .1 — and confirm it fails against the current code, which appends."
      owner: "Claude Code"
    - step: "EDIT A and EDIT B in main.py."
      owner: "Claude Code"
    - step: "EDIT C in manager.py, with a test asserting the monitor's target follows configuration."
      owner: "Claude Code"
    - step: "Compile checks and the full assertion set."
      owner: "Claude Code"
    - step: "Deploy; restart twice; confirm debug.log.1 holds the previous session and the startup line reports 30."
      owner: "William Watson"
  rollback_procedure: >
    Single commit across two files. git revert restores the appending
    log and the hardcoded target. Existing debug.log.N files on the
    target are inert diagnostic output and may be deleted at leisure.
  deployment_notes: >
    Backup files appear alongside debug.log on the target. The first
    restart after this lands rotates the existing 43 MB file into
    debug.log.1, which is worth knowing before wondering where it went;
    it can be deleted once pulled.

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
    - change_ref: "change-c1d4b8e6"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-6a3b7c52"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-6a3b7c52, implementing the operator's specification of 10 MB, rotate at start, ten versions."
      - "Recorded rotate-at-start as chosen over truncate-at-start because systemd's Restart=always means truncation would erase the evidence of the crash that caused the restart."
      - "Recorded the crash-loop bound from bin/gtach.service's StartLimitBurst=3, and that rotation is skipped on an empty file so a restart before any output consumes no slot."
      - "Recorded that a set_target_fps method was rejected because target_fps is consumed during __init__ for three separate purposes, making a setter larger than moving one construction."
      - "Recorded that moving _load_config before _initialize_components was rejected as changing more than needed, and that only the monitor's two lines move."
      - "Recorded explicitly that this change is not a fix for the §9.12 sluggishness, whose causes remain undistinguished."

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
| 1.0 | 2026-08-05 | Initial change document coupled to issue-6a3b7c52. Rotate-at-start with a 10 MB cap and ten backups, and the performance monitor constructed after configuration with the configured frame rate. |

---

Copyright (c) 2026 William Watson. MIT License.
