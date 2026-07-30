Created: 2026 July 30

# Change: Correct Frame-Time Measurement and Reduce Instrumentation Overhead

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-0b00759c"
  title: "Move record_frame_end before the pacing sleep; gate periodic logging inside the monitor; replace the UUID frame ID with a counter; sample psutil at 1 Hz"
  date: "2026-07-30"
  author: "William Watson"
  status: "closed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-0b00759c"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-0b00759c"
  description: >
    Resolves issue-0b00759c. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 recommendations
    15, 16, 17 and 18. Task list reference ai/task.md §7.3.7.

scope:
  summary: >
    Make frame_time_ms measure render cost rather than loop period, and
    remove four per-frame instrumentation costs. Two files:
    src/gtach/display/manager.py and
    src/gtach/display/performance/monitor.py.
  affected_components:
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "PerformanceMonitor.__init__"
      file_path: "src/gtach/display/performance/monitor.py"
      change_type: "modify"
    - name: "PerformanceMonitor.record_frame_start"
      file_path: "src/gtach/display/performance/monitor.py"
      change_type: "modify"
    - name: "PerformanceMonitor.record_frame_end"
      file_path: "src/gtach/display/performance/monitor.py"
      change_type: "modify"
    - name: "PerformanceMonitor.should_log_periodic"
      file_path: "src/gtach/display/performance/monitor.py"
      change_type: "add"
    - name: "PerformanceMonitor._get_current_memory_usage"
      file_path: "src/gtach/display/performance/monitor.py"
      change_type: "modify"
    - name: "PerformanceMonitor.reset_metrics"
      file_path: "src/gtach/display/performance/monitor.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Any change to what is rendered. This change alters measurement only."
    - "Reducing fps_limit or skipping unchanged frames — recommendations 12 and 13, task 7.3.6."
    - "Caching the RADIAL static layer or rendered text — recommendations 9 and 10, task 7.3.5."
    - "The dirty-region API (add_dirty_region, get_dirty_regions, clear_dirty_regions). Unused by the current render path and left untouched."
    - "Removing psutil as a dependency."

rational:
  problem_statement: >
    record_frame_end is called after the pacing sleep, so the recorded
    interval spans render plus idle padding and converges on the frame
    target regardless of render cost. The telemetry therefore cannot be
    used to judge any rendering-efficiency change, and the dropped-frame
    test is evaluated against the padded value. Separately, the display
    loop calls get_current_metrics on every frame purely to read a counter
    the monitor already holds, which drags a psutil /proc read into the
    per-frame path; and the frame identifier is a UUID string allocated
    per frame where a process-local integer suffices.
  proposed_solution: >
    Call record_frame_end at the end of the rendered work, before the
    pacing sleep. Add a should_log_periodic() accessor to the monitor that
    tests its own frame counter, and call that from the loop instead of
    constructing a full metrics object. Replace the UUID frame ID with a
    monotonically increasing integer. Cache the psutil memory reading and
    refresh it at most once per second.
  alternatives_considered:
    - option: "Record two intervals — render time and loop period — and report both."
      reason_rejected: >
        More state and more reporting surface for no additional decision
        value. The loop period is already known: it is 1/fps_limit unless
        a frame overruns, and an overrun is exactly what the dropped-frame
        counter records.
    - option: "Leave the UUID and accept the allocation."
      reason_rejected: >
        The identifier never leaves the monitor, so the uniqueness
        guarantee a UUID provides is unused. A counter is strictly cheaper
        and equally correct. The report raises it as recommendation 17.
    - option: "Remove psutil sampling entirely."
      reason_rejected: >
        Memory figures are useful on a 512 MB target and the reported
        value has diagnostic value across long runs. Rate-limiting the read
        preserves the signal at a fraction of the cost.
    - option: "Keep get_current_metrics in the loop but memoise it."
      reason_rejected: >
        Adds a caching layer to work around a call that should not be made.
        A direct counter accessor is simpler and is what recommendation 16
        specifies.
  benefits:
    - "frame_time_ms becomes a true measure of render cost, which is the prerequisite for judging tasks 7.3.5 and 7.3.6 and for the baseline recorded as ai/task.md §7.5.3."
    - "The dropped-frame test at monitor.py:188 becomes meaningful for the first time."
    - "Removes a psutil /proc read, a UUID allocation, a dictionary comprehension and a full metrics construction from every frame."
  risks:
    - risk: >
        The change alters the meaning of a recorded quantity. Historical
        frame_time figures in logs are not comparable with figures recorded
        after this change.
      mitigation: >
        State the discontinuity in the T06 result and record the new
        baseline explicitly per ai/task.md §7.5.3. Do not compare across
        the change.
    - risk: >
        The dropped-frame count will rise, because the test now sees real
        render times and can fire on genuine overruns.
      mitigation: >
        Expected outcome, not a regression. Record the pre- and post-change
        counts in the T06 result so the rise is documented as intended.
    - risk: >
        Changing the frame ID type from str to int breaks the truthiness
        guard in _display_loop, which currently tests
        "if frame_id and len(frame_id) > 0". Frame ID 0 would be falsy.
      mitigation: >
        The guard is removed in the same edit and replaced by the
        should_log_periodic() call. Start the counter at 1 so no valid ID
        is falsy, and use 0 as the disabled-monitoring sentinel in place of
        the current empty string. Update the type annotations on
        record_frame_start, record_frame_end and _active_frames together.
    - risk: >
        A cached memory figure could go stale if the refresh interval is
        never reached in a short run.
      mitigation: >
        Seed the cache on the first call rather than returning zero, so a
        figure is always available.

technical_details:
  current_behavior: >
    _display_loop (manager.py:397-456) calls record_frame_start at
    manager.py:413, renders, swaps and writes the framebuffer, computes
    _sleep, calls time.sleep(_sleep) at manager.py:441, then calls
    record_frame_end(frame_id) at manager.py:442. It then guards on
    "if frame_id and len(frame_id) > 0" and calls
    get_current_metrics() at manager.py:446 to test
    metrics.total_frames % 600 == 0.

    record_frame_start (monitor.py:136) allocates str(uuid.uuid4())[:8] at
    monitor.py:143 and scans _active_frames for expiry at
    monitor.py:148-153. record_frame_end (monitor.py:162) tests
    frame_time > self.frame_time_target * 1.5 at monitor.py:188.
    get_current_metrics (monitor.py:248) reaches
    _get_current_memory_usage (monitor.py:407), which calls
    self._process.memory_info() at monitor.py:411.
  proposed_behavior: >
    record_frame_end is called immediately after
    rendering_engine.write_to_framebuffer() and before the pacing sleep, so
    the recorded interval covers rendered work only. The loop tests
    self.performance_monitor.should_log_periodic() and constructs metrics
    only when that returns True. Frame IDs are integers from a monotonic
    counter, with 0 reserved for the disabled case. The psutil reading is
    cached and refreshed at most once per second.
  implementation_approach: >
    Six edits across two files.

    monitor.py EDIT A — __init__. Add:
      self._frame_id_counter = 0
      self._memory_cache_mb = 0.0
      self._memory_cache_ts = 0.0
      self._memory_sample_interval = 1.0
      self._log_interval_frames = 600
    Change the annotation of self._active_frames from Dict[str, float] to
    Dict[int, float].

    monitor.py EDIT B — record_frame_start. Change the return annotation
    from str to int. Return 0 instead of "" when not monitoring. Replace
    the UUID line with an incrementing counter (pre-increment so the first
    valid ID is 1). Retain the expiry scan but bound its cost: skip it
    entirely when len(self._active_frames) <= 1, which is the normal case.
    Return 0 in the except clause.

    monitor.py EDIT C — record_frame_end. Change the frame_id annotation
    from str to int. Change the "not frame_id" guard so it rejects 0 and
    accepts any positive ID. Leave the frame_time computation, the
    _frame_history append, the _frame_count increment, the dropped-frame
    test and the periodic _update_metrics_history call as they are.

    monitor.py EDIT D — add should_log_periodic() -> bool immediately after
    record_frame_end. Under self._lock, return True when self._frame_count
    is non-zero and self._frame_count % self._log_interval_frames == 0.
    Return False when not monitoring. Wrap in try/except returning False.

    monitor.py EDIT E — _get_current_memory_usage. Rate-limit the psutil
    read: return the cached value when time.time() - self._memory_cache_ts
    is less than self._memory_sample_interval; otherwise read
    self._process.memory_info(), update the cache and its timestamp, and
    return the new value. Seed on first call so a figure is always
    available. Retain the existing _memory_samples fallback and the
    except clause returning 0.0.

    monitor.py EDIT F — reset_metrics. Reset _frame_id_counter,
    _memory_cache_mb and _memory_cache_ts alongside the existing state so
    a reset leaves no stale reading.

    manager.py EDIT G — _display_loop. Move
    self.performance_monitor.record_frame_end(frame_id) from its current
    position after time.sleep(_sleep) to immediately after
    self.rendering_engine.write_to_framebuffer(), before _frame_end is
    read. Replace the block

        if frame_id and len(frame_id) > 0:
            metrics = self.performance_monitor.get_current_metrics()
            if metrics.total_frames % 600 == 0:
                self.logger.info(...)

    with a single guard on
    self.performance_monitor.should_log_periodic(), constructing metrics
    inside that guard. Leave the log message text and its three fields
    unchanged.
  code_changes:
    - component: "PerformanceMonitor"
      file: "src/gtach/display/performance/monitor.py"
      change_summary: >
        Integer frame IDs from a counter; bounded expiry scan; new
        should_log_periodic accessor; rate-limited psutil sampling; reset
        of the new state in reset_metrics.
      functions_affected:
        - "__init__"
        - "record_frame_start"
        - "record_frame_end"
        - "should_log_periodic"
        - "_get_current_memory_usage"
        - "reset_metrics"
      classes_affected:
        - "PerformanceMonitor"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        record_frame_end moved before the pacing sleep; per-frame
        get_current_metrics call replaced by should_log_periodic.
      functions_affected:
        - "_display_loop"
      classes_affected:
        - "DisplayManager"
  data_changes:
    - entity: "PerformanceMonitor._active_frames"
      change_type: "schema"
      details: "Key type changes from str to int. In-memory only; nothing is persisted."
  interface_changes:
    - interface: "PerformanceMonitor.record_frame_start() -> str"
      change_type: "signature"
      details: "Return type becomes int. Disabled sentinel changes from '' to 0. The only caller is DisplayManager._display_loop, updated in the same change."
      backward_compatible: "no"
    - interface: "PerformanceMonitor.record_frame_end(frame_id: str) -> float"
      change_type: "signature"
      details: "Parameter type becomes int. The only caller is DisplayManager._display_loop, updated in the same change."
      backward_compatible: "no"
    - interface: "PerformanceMonitor.should_log_periodic() -> bool"
      change_type: "contract"
      details: "New accessor. Additive."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "DisplayManager._display_loop"
      impact: "Sole caller of the two changed signatures. Updated in the same change."
    - component: "DisplayManager.get_status (manager.py:1548)"
      impact: "Calls get_current_metrics().to_dict(). Unaffected — that call is on demand, not per frame."
  external:
    - library: "psutil"
      version_change: "none"
      impact: "Read frequency reduced from once per frame to once per second."
  required_changes:
    - change_ref: "change-821919ce"
      relationship: "blocks"
    - change_ref: "change-9ed1c77e"
      relationship: "blocks"

testing_requirements:
  test_approach: >
    Unit tests against PerformanceMonitor on the development platform with
    psutil present, plus an on-target reading of the periodic log line to
    establish the baseline required by ai/task.md §7.5.3.
  test_cases:
    - scenario: "Call record_frame_start twice with monitoring enabled."
      expected_result: "Returns 1 then 2. Both are truthy integers."
    - scenario: "Call record_frame_start with monitoring disabled."
      expected_result: "Returns 0."
    - scenario: "Call record_frame_end with frame_id 0."
      expected_result: "Returns 0.0 without warning; treated as the disabled sentinel."
    - scenario: "Bracket a 5 ms sleep with record_frame_start and record_frame_end."
      expected_result: "Returned frame time is approximately 5 ms, not the 16.67 ms target."
    - scenario: "Record 600 frames and call should_log_periodic after each."
      expected_result: "Returns True exactly once, on frame 600."
    - scenario: "Call should_log_periodic with monitoring disabled."
      expected_result: "Returns False."
    - scenario: "Call _get_current_memory_usage 100 times in rapid succession with psutil mocked."
      expected_result: "memory_info() is invoked once; the cached value is returned thereafter."
    - scenario: "Call _get_current_memory_usage, advance the clock past 1 s, call again."
      expected_result: "memory_info() is invoked a second time."
    - scenario: "Call reset_metrics then record_frame_start."
      expected_result: "Frame IDs restart at 1; the memory cache timestamp is cleared."
    - scenario: "Record a frame whose duration exceeds frame_time_target * 1.5."
      expected_result: "_dropped_frames increments."
  regression_scope:
    - "tests/display/ — full existing display suite."
    - "Any test asserting a string frame ID must be updated in the same change."
    - "DisplayManager.get_status() continues to return a populated performance_metrics dict."
  validation_criteria:
    - "python -m py_compile src/gtach/display/performance/monitor.py passes."
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "pytest tests/ passes with no new failures."
    - "record_frame_end appears before time.sleep in _display_loop by source inspection."
    - "get_current_metrics is not called unconditionally in the display loop."
    - "On gtach.local, frame_time_ms is materially below 16.7 ms and differs between OPTIONS and RADIAL."

implementation:
  implementation_steps:
    - step: "monitor.py EDIT A — add counter, memory cache and interval state to __init__; retype _active_frames."
      owner: "Claude Code"
    - step: "monitor.py EDIT B — integer frame IDs and bounded expiry scan in record_frame_start."
      owner: "Claude Code"
    - step: "monitor.py EDIT C — retype record_frame_end and correct its sentinel guard."
      owner: "Claude Code"
    - step: "monitor.py EDIT D — add should_log_periodic."
      owner: "Claude Code"
    - step: "monitor.py EDIT E — rate-limit _get_current_memory_usage."
      owner: "Claude Code"
    - step: "monitor.py EDIT F — reset the new state in reset_metrics."
      owner: "Claude Code"
    - step: "manager.py EDIT G — move record_frame_end before the sleep; replace the metrics call with should_log_periodic."
      owner: "Claude Code"
    - step: "Compile check and run the existing test suite."
      owner: "Claude Code"
    - step: "Deploy to gtach.local and record the baseline frame_time_ms per ai/task.md §7.5.3."
      owner: "William Watson"
  rollback_procedure: >
    Two files, one commit. git revert restores the previous behaviour. No
    persisted data or configuration is involved.
  deployment_notes: >
    Frame-time figures recorded before and after this change are not
    comparable. Note the changeover point in the operational log.

verification:
  implemented_date: "2026-07-30"
  implemented_by: "Claude Code, per prompt-0b00759c"
  verification_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Development platform only. On-target verification is outstanding — see
    the note below on the §7.5.3 baseline.

    All seven edits applied as specified. Compile checks pass on both
    files (python -m py_compile). Source-order checks: record_frame_end is
    at manager.py:435 and the pacing time.sleep at manager.py:446, so the
    frame closes before the sleep; "len(frame_id)" no longer appears in
    manager.py; get_current_metrics is called in _display_loop only inside
    the should_log_periodic guard; "uuid.uuid4()" no longer appears in
    monitor.py and the now-unused "import uuid" was removed.

    All ten test cases above were executed directly against
    PerformanceMonitor on macOS (Python 3.11.14, psutil and pygame
    present) and all pass: frame IDs 1 then 2; 0 when monitoring is
    disabled; record_frame_end(0) returns 0.0 with no warning; a 5 ms
    bracketed sleep measured 6.28 ms rather than the 16.67 ms target;
    should_log_periodic returned True only at frames 600 and 1200 over a
    1200-frame run, and False when monitoring is disabled; a mocked
    memory_info() was invoked once across 100 rapid calls and a second
    time after the cache timestamp was advanced past 1 s; frame IDs
    restart at 1 after reset_metrics; a 30 ms frame incremented
    _dropped_frames.

    pytest tests/ collected 0 items — the tests/ tree has contained only
    README.md since commit 57ebbe6 (project reset for governance). The
    "no new failures" criterion is therefore vacuous, and the
    regression_scope entry naming tests/display/ could not be exercised.
    The direct assertions above stand in its place. No existing test
    asserted a string frame ID, because no tests exist.

    Only the two named files were modified.

    Closure re-verification, 2026-07-30. The seven edits were re-checked
    against the working tree and all six validation_criteria that do not
    require gtach.local hold. Line references have moved since
    implementation — record_frame_end is now manager.py:445 and the pacing
    time.sleep manager.py:456, the shift introduced by change-4c038bed in
    the same file — but the source order the criterion asserts is intact,
    "len(frame_id)" is still absent from manager.py, get_current_metrics
    appears in _display_loop only at manager.py:462 inside the
    should_log_periodic guard (its other call site, manager.py:1627, is
    get_status, which is on-demand and was always out of scope), and
    "uuid" no longer appears anywhere in monitor.py.

    Twenty-three assertions were executed against the real
    PerformanceMonitor with pygame and psutil stubbed: the ten test_cases
    above, the four prompt edge cases, and six further checks — a failed
    psutil read returns 0.0 without writing the cache; the _memory_samples
    fallback is taken when _process is None; a stale entry is expired once
    a second active frame makes the scan reachable, incrementing
    _dropped_frames; record_frame_end after stop_monitoring returns 0.0
    without raising; get_current_metrics().to_dict() is still populated,
    which is the regression_scope entry for DisplayManager.get_status; and
    the three signatures carry the int, int and bool annotations. All
    pass.

    The regression_scope entry naming tests/display/ remains unexecutable
    — tests/ still holds only README.md — and the validation criterion
    "pytest tests/ passes with no new failures" remains vacuous rather
    than met. The direct assertions stand in its place. This is a standing
    project-wide gap, not a residual of this change.

    The remaining validation criterion — frame_time_ms materially below
    16.7 ms on gtach.local and differing between OPTIONS and RADIAL — and
    implementation step 9, recording the ai/task.md §7.5.3 baseline, are
    owned by William Watson and are the purpose of this change rather than
    conditions of its closure.
  issues_found:
    - issue_ref: "issue-c5dedd71"

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-821919ce"
      relationship: "blocks"
    - change_ref: "change-9ed1c77e"
      relationship: "blocks"
    - change_ref: "change-c5dedd71"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-0b00759c"
      relationship: "resolves"
    - issue_ref: "issue-c5dedd71"
      relationship: "introduced_by"

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-0b00759c."
  - version: "1.1"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Status proposed -> implemented. Recorded implementation date, executor and development-platform test results."
      - "Recorded issue-c5dedd71 in issues_found: the two abstract declarations on PerformanceMonitorInterface still read str, because this change's prompt confined the executor to monitor.py and manager.py."
      - "Noted that pytest collected 0 items and that on-target verification of the §7.5.3 baseline remains outstanding."
  - version: "1.2"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status implemented -> closed. Verification date and verifier recorded."
      - "Recorded the closure re-verification: all six off-target validation_criteria re-checked, twenty-three assertions against the real PerformanceMonitor, all passing."
      - "Recorded that the manager.py line references moved under change-4c038bed without affecting the source order asserted by the criteria."
      - "Recorded that the tests/display/ regression_scope entry remains unexecutable and the pytest criterion vacuous rather than met."
      - "Moved to ai/workspace/change/closed/ per P00 §1.1.14.4."

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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-0b00759c. |
| 1.1 | 2026-07-30 | Status proposed → implemented; implementation and development-platform test results recorded; issue-c5dedd71 recorded in issues_found; on-target §7.5.3 baseline noted as outstanding. |
| 1.2 | 2026-07-30 | Status implemented → closed; closure re-verification recorded. Moved to ai/workspace/change/closed/ per P00 §1.1.14.4. |

---

Copyright (c) 2026 William Watson. MIT License.
