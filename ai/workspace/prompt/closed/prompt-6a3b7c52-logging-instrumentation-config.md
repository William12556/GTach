Created: 2026 August 05

# Prompt: Roll the Log at Start, and Measure Against the Frame Rate in Use

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-6a3b7c52"
  task_type: "debug"
  source_ref: "change-6a3b7c52"
  target_profile: "claude_code"
  date: "2026-08-05"
  iteration: 1
  coupled_docs:
    change_ref: "change-6a3b7c52"
    change_iteration: 1

context:
  purpose: >
    Two small independent faults.

    (a) debug.log has never truncated or rotated. main.py passes
    mode='w' to RotatingFileHandler, which SILENTLY OVERRIDES IT TO 'a'
    whenever maxBytes > 0 — verified against CPython by reproduction,
    and deliberate on its part. With maxBytes at 100 MB the threshold
    has never been reached either, so the file grew to 43 MB spanning
    three sessions and every analysis of it began by segmenting on
    timestamps.

    (b) PerformanceMonitor is constructed with a literal target_fps=60.
    At the configured 30 Hz its frame target is 16.67 ms instead of
    33.3, its dropped-frame threshold 25 ms instead of 50, its min_fps
    alert 48 instead of 24, and its history window twice the intended
    duration. Every dropped-frame figure read at 30 Hz is wrong.
  integration: >
    Two files: src/gtach/main.py and src/gtach/display/manager.py.
    Executor is Claude Code; AEL is not used.

    THE OPERATOR'S SPECIFICATION for (a), 2026-08-05: cap at 10 MB,
    rotate at start, keep ten versions.

    WHY (b) IS HARDCODED, and why the fix is a move rather than an
    edit. manager.py:136 calls _initialize_components(), which
    constructs the monitor at :169. manager.py:139 then calls
    _load_config(), which is the first thing to set self.config. The
    literal was the only value available at that point. PerformanceMonitor
    offers no way to change target_fps afterwards — it is consumed
    during __init__ at monitor.py:42, :50 and :74-75 — so the
    construction must move to after the configuration is loaded.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/main.py and src/gtach/display/manager.py."
    - "Do NOT modify src/gtach/display/performance/monitor.py. It already accepts target_fps; the defect is the caller's argument."
    - "Do NOT add a set_target_fps method. target_fps is consumed three times during __init__; a setter would have to rebuild the history deque and recompute both alert thresholds."
    - "Do NOT reorder _load_config and _initialize_components generally. Move the monitor's two lines only."
    - "Do NOT change start.log's handler. Plain FileHandler honours mode='w' and its truncate-at-boot behaviour is correct."
    - "Do NOT truncate debug.log at start. Rotate it. GTach runs under systemd with Restart=always, and truncating would erase the evidence of the crash that caused the restart."
    - "Do NOT record this change as fixing the sluggishness in ai/task.md §9.12. It reduces SD write volume; it does not establish that log I/O was the cause."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Cap the debug log at 10 MB with ten backups, drop the dead mode
    argument, and roll over once at startup when the file has content.
    Construct PerformanceMonitor after _load_config with the configured
    frame rate.
  requirements:
    functional:
      - "_DEBUG_MAX_BYTES is 10 MB; backupCount is 10."
      - "No mode argument is passed to RotatingFileHandler."
      - "A non-empty debug.log is rotated to debug.log.1 at startup and debug.log begins empty."
      - "An absent or empty debug.log is not rotated and no slot is consumed."
      - "At most ten backups exist; no debug.log.11."
      - "start.log still truncates at boot and produces no backups."
      - "PerformanceMonitor is constructed after _load_config with config.fps_limit."
      - "A non-positive or absent fps_limit falls back to the DisplayConfig default without raising."
      - "The startup line reports the configured rate."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.9)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Startup gains one stat call and, when the file has content, one rename. Steady state unchanged"
      metric: "time"

design:
  architecture: >
    Each run writes its own log; the previous ten survive. A component
    that needs configuration is constructed after configuration is
    available, rather than given a literal because the value is not yet
    known.
  components:
    - name: "main.setup_logging"
      type: "function"
      purpose: "Give the debug log a rotation policy that works."
      logic:
        - "Record whether _DEBUG_LOG exists and is non-empty BEFORE constructing the handler — construction opens the file."
        - "Construct RotatingFileHandler with maxBytes and backupCount and NO mode argument."
        - "If there was content, call handler.doRollover() once."
        - "Wrap the rollover so a failure logs and leaves the handler usable rather than aborting startup."
    - name: "DisplayManager.__init__"
      type: "function"
      purpose: "Build the monitor once the frame rate is known."
      logic:
        - "After self._load_config(), read config.fps_limit with a guarded fallback and construct the monitor."
    - name: "DisplayManager._initialize_components"
      type: "function"
      purpose: "Lose the monitor construction."
      logic:
        - "Remove the two monitor lines. Everything else in the method is unchanged."
  dependencies:
    internal:
      - "PerformanceMonitor — monitor.py. Read-only; only the argument changes."
      - "bin/gtach.service — StartLimitBurst=3 bounds a restart loop to three rapid starts, so ten slots cannot be exhausted quickly. Read-only."
    external:
      - "logging.handlers.RotatingFileHandler — its mode override is the behaviour being worked around."

error_handling:
  strategy: >
    Neither correction may prevent the application starting. A rollover
    failure leaves the handler usable; a monitor failure is logged and
    the display continues, matching the surrounding style.
  exceptions:
    - exception: "OSError"
      condition: "The log directory is not writable."
      handling: "The existing handler prints a warning and continues. Unchanged."
    - exception: "Exception"
      condition: "doRollover fails — a permission problem on a backup, say."
      handling: "Print a warning to stderr in the same style as the existing OSError path and carry on with the handler as constructed. An unrotated log is better than no application."
    - exception: "Exception"
      condition: "PerformanceMonitor construction fails."
      handling: "Log at ERROR and leave self.performance_monitor unset only if the surrounding code tolerates it — check how _display_loop uses it and preserve current behaviour."
  logging:
    level: "Unchanged"
    format: "Existing"

testing:
  unit_tests:
    - scenario: "THE DISCRIMINATING TEST. An existing debug.log containing a known line, then setup_logging with the paths redirected to a temporary directory."
      expected: "debug.log.1 contains the known line; debug.log is empty. Run against the pre-change code too: it appends and produces no .1."
    - scenario: "No debug.log present."
      expected: "No exception; debug.log created; no .1."
    - scenario: "Empty debug.log present."
      expected: "No rotation; no .1; no slot consumed."
    - scenario: "Eleven consecutive setup_logging calls, each writing a distinguishable line."
      expected: "debug.log plus .1 to .10; no .11; the eleventh-oldest line is gone."
    - scenario: "handler.mode after construction."
      expected: "'a'. Assert it as expected and comment why, so the next reader does not 'fix' it back."
    - scenario: "_DEBUG_MAX_BYTES and handler.backupCount."
      expected: "10485760 and 10."
    - scenario: "More than 10 MB written in one session."
      expected: "Rotation occurs within the session."
    - scenario: "start.log across two setup_logging calls."
      expected: "Truncated each time; no start.log.1. Its behaviour must not change."
    - scenario: "A read-only log directory."
      expected: "Warning printed; application continues; unchanged from today."
    - scenario: "doRollover forced to raise."
      expected: "Warning printed; the handler still works; startup continues."
    - scenario: "DisplayManager built headlessly with fps_limit 30."
      expected: "performance_monitor.target_fps == 30."
    - scenario: "The same with fps_limit 60."
      expected: "60."
    - scenario: "With fps_limit 0, and with the attribute absent."
      expected: "Falls back to the DisplayConfig default; no ZeroDivisionError from monitor.py:42."
    - scenario: "monitor.frame_time_target at fps_limit 30."
      expected: "1/30. The dropped-frame threshold at monitor.py:181 is therefore 50 ms."
    - scenario: "The startup line at fps_limit 30."
      expected: "'target: 30 FPS'."
    - scenario: "Construction order."
      expected: "The monitor is constructed after _load_config. Assert by instrumenting both and recording the order, not by reading."
    - scenario: "record_frame_start, record_frame_end and should_log_periodic."
      expected: "Unchanged behaviour."
  edge_cases:
    - "Check the file size BEFORE constructing the handler. RotatingFileHandler opens the file in append mode on construction, so a size check afterwards still reads the old content — but the ordering matters if delay semantics ever change, and reading first is unambiguous."
    - "doRollover() must be called on the constructed handler, not before it exists: it operates on the handler's own stream, closing it, shifting debug.log.N to N+1, renaming debug.log to .1 and reopening."
    - "The first restart after this lands rotates the existing 43 MB file into debug.log.1. Expected, not a fault."
    - "manager.py:136 and :139 are consecutive statements, so nothing runs between _initialize_components and _load_config. Confirm that self.performance_monitor is not referenced anywhere in _load_config before moving the construction."
    - "DisplayConfig.fps_limit defaults to 60 in the dataclass. Use that as the fallback rather than a fresh literal, so there is one default."
    - "_display_loop reads self.config.fps_limit for its own pacing independently of the monitor. That is correct and unchanged; the two now agree, which they did not before."
  validation:
    - "grep confirms no mode= argument on the RotatingFileHandler call."
    - "grep confirms no literal 60 passed as target_fps."
    - "git diff confirms monitor.py and the start.log handler are untouched."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "One commit."
  files:
    - path: "src/gtach/main.py"
      content: |
        TWO EDITS.

        EDIT A — constants. Replace main.py:25:

            _DEBUG_MAX_BYTES = 100 * 1024 * 1024  # 100 MB

        with:

            # 10 MB is about ninety minutes of debug output at 30 Hz.
            # Ten backups gives roughly sixteen hours of history for
            # 110 MB of card. bin/gtach.service caps a restart loop at
            # three rapid starts (StartLimitBurst), so rotate-at-start
            # cannot exhaust the backups (issue-6a3b7c52).
            _DEBUG_MAX_BYTES = 10 * 1024 * 1024
            _DEBUG_BACKUPS = 10

        EDIT B — setup_logging. Replace the debug handler block:

            # debug.log — truncated at boot; suppressed unless toggled on.
            try:
                _debug_handler = RotatingFileHandler(
                    _DEBUG_LOG, mode='w', maxBytes=_DEBUG_MAX_BYTES,
                    backupCount=0, encoding='utf-8'
                )

        with:

            # debug.log — rotated at boot, so each run has its own file
            # and the previous ten survive; suppressed unless toggled on.
            #
            # NOTE the absence of mode='w'. RotatingFileHandler discards
            # it whenever maxBytes > 0 and opens in append mode
            # regardless — deliberate CPython behaviour, so that
            # rotation is not defeated by truncation. The previous
            # mode='w' here was dead, and debug.log had never truncated
            # despite the comment saying it did (issue-6a3b7c52).
            # Rotation at start is done explicitly below instead, which
            # keeps the previous run rather than discarding it — the
            # distinction that matters under systemd Restart=always.
            _had_content = False
            try:
                _had_content = os.path.getsize(_DEBUG_LOG) > 0
            except OSError:
                _had_content = False

            try:
                _debug_handler = RotatingFileHandler(
                    _DEBUG_LOG, maxBytes=_DEBUG_MAX_BYTES,
                    backupCount=_DEBUG_BACKUPS, encoding='utf-8'
                )
                if _had_content:
                    try:
                        _debug_handler.doRollover()
                    except Exception as e:
                        print(
                            f'[gtach] WARNING: could not rotate '
                            f'{_DEBUG_LOG}: {e}', file=sys.stderr
                        )

        keeping the setLevel, setFormatter, addHandler and the existing
        OSError handler below exactly as they are.

        Confirm 'import os' is present at module scope in main.py; add
        it following the file's existing import placement if not.

        Change nothing about _start_handler. Plain FileHandler honours
        mode='w' and start.log's truncate-at-boot behaviour is correct.
    - path: "src/gtach/display/manager.py"
      content: |
        EDIT C — move the monitor construction.

        First confirm that self.performance_monitor is not referenced
        anywhere inside _load_config. It should not be; check rather
        than assume, because the move depends on it.

        In _initialize_components, REMOVE:

            # Initialize performance monitor
            self.performance_monitor = PerformanceMonitor(target_fps=60)
            self.performance_monitor.start_monitoring()

        Everything else in that method stays.

        In __init__, immediately AFTER:

            # Configuration
            self._load_config()

        add:

            # Performance monitor, built here rather than in
            # _initialize_components because it takes the frame rate in
            # its constructor and self.config does not exist until
            # _load_config has run. It was previously given a literal 60
            # for that reason, which made every dropped-frame figure
            # wrong at any other rate and reported a constant in the
            # startup line (issue-6a3b7c52).
            try:
                _fps = getattr(self.config, 'fps_limit', 0) or 0
                if _fps <= 0:
                    _fps = DisplayConfig.fps_limit
                self.performance_monitor = PerformanceMonitor(target_fps=_fps)
                self.performance_monitor.start_monitoring()
            except Exception as e:
                self.logger.error(
                    f'Performance monitor initialization failed: {e}',
                    exc_info=True
                )

        DisplayConfig.fps_limit is the dataclass default and is already
        imported in this file. Use it rather than writing 60 again, so
        there is one default.

        Check how _display_loop uses self.performance_monitor and
        preserve the current behaviour if construction fails — if the
        loop assumes the attribute exists, the except branch must leave
        something usable or the guard must be at the call sites. State
        in the commit message which was found and what was done.

success_criteria:
  - "python -m py_compile src/gtach/main.py src/gtach/display/manager.py passes."
  - "pytest tests/ passes with no new failures."
  - "The rotation test fails against the pre-change code and passes after. Both results recorded."
  - "_DEBUG_MAX_BYTES is 10 * 1024 * 1024 and _DEBUG_BACKUPS is 10."
  - "No mode argument is passed to RotatingFileHandler."
  - "A non-empty debug.log rotates to debug.log.1 at startup; an empty or absent one does not."
  - "Eleven starts leave debug.log and .1 to .10, and no .11."
  - "start.log's handler construction is byte-identical and it still truncates."
  - "A forced doRollover failure prints a warning and does not prevent startup."
  - "PerformanceMonitor is not constructed inside _initialize_components."
  - "PerformanceMonitor is constructed after _load_config with config.fps_limit."
  - "fps_limit of 0 or absent falls back to DisplayConfig.fps_limit with no ZeroDivisionError."
  - "No literal 60 is passed as target_fps."
  - "src/gtach/display/performance/monitor.py is byte-identical."
  - "No file other than the two named above is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "main"
        path: "src/gtach/main.py"
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "monitor"
        path: "src/gtach/display/performance/monitor.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "PerformanceMonitor"
        module: "gtach.display.performance.monitor"
      - name: "DisplayConfig"
        module: "gtach.display.models"
      - name: "RotatingFileHandler"
        module: "logging.handlers"
    functions:
      - name: "setup_logging"
        module: "gtach.main"
        signature: "setup_logging(debug: bool = False) -> None"
      - name: "_initialize_components"
        module: "gtach.display.manager"
        signature: "_initialize_components(self) -> None"
    constants:
      - name: "_DEBUG_MAX_BYTES"
        module: "gtach.main"
      - name: "_DEBUG_BACKUPS"
        module: "gtach.main"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-6a3b7c52-logging-instrumentation-config.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results. Then, once you are finished, write
  a report of what you have done in the ai/workspace/report folder.

  Write the rotation test first and run it against the unchanged file.
  It appends, which is the whole finding; a test that cannot show that
  is not testing this defect.

  Do not be tempted to restore mode='w' when you see the handler
  opening in append mode. That is CPython overriding the argument on
  purpose, it is why the previous code did not work, and the comment in
  EDIT B exists to stop exactly that correction being made again.

  Two things to expect on the target after this lands, neither a fault.
  The first restart rotates the existing 43 MB debug.log into
  debug.log.1 — pull it before deleting if you want the history. And
  the startup line will report 30 FPS rather than 60, which is the
  monitor telling the truth for the first time.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-05 | Initial prompt document coupled to change-6a3b7c52. |

---

Copyright (c) 2026 William Watson. MIT License.
