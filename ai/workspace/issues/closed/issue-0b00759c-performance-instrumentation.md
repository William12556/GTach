Created: 2026 July 30

# Issue: Performance Instrumentation Measures Padded Frame Time and Costs More Than It Reports

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-0b00759c"
  title: "record_frame_end is called after the pacing sleep, so frame_time_ms measures idle padding; per-frame UUID, expiry scan, metrics call and psutil read add avoidable cost"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-0b00759c"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Recommendation 15 (§9.3) addressing finding §6.2;
    recommendations 16, 17 and 18 (§9.3) addressing finding §6.1.
    Task list reference: ai/task.md §7.3.7.

affected_scope:
  components:
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
    - name: "PerformanceMonitor.record_frame_start"
      file_path: "src/gtach/display/performance/monitor.py"
    - name: "PerformanceMonitor.record_frame_end"
      file_path: "src/gtach/display/performance/monitor.py"
    - name: "PerformanceMonitor.get_current_metrics"
      file_path: "src/gtach/display/performance/monitor.py"
    - name: "PerformanceMonitor._get_current_memory_usage"
      file_path: "src/gtach/display/performance/monitor.py"
  designs: []
  version: "0.2.64"

reproduction:
  prerequisites: >
    GTach running on gtach.local with performance monitoring active. The
    periodic performance log line is emitted from manager.py:448-452 every
    600 frames.
  steps:
    - "Run the application and read the periodic 'Performance: N FPS, N.Nms frame, N.NMB mem' log line."
    - "Observe that frame_time_ms sits at or near 16.7 ms regardless of what the display is actually rendering."
    - "Switch between the near-static OPTIONS screen and RADIAL mode, which the report calculates at over 5x overdraw."
    - "Observe that the reported frame time does not materially differ between them."
  frequency: "always"
  reproducibility_conditions: >
    Present on every frame in every mode. The reported figure only departs
    from the target when a frame overruns the 16.67 ms budget, at which
    point the sleep is skipped.
  preconditions: "fps_limit = 60; performance monitoring enabled."
  test_data: ""
  error_output: "None. No exception is raised; the telemetry is silently wrong."

behavior:
  expected: >
    frame_time_ms reports the cost of rendering a frame. Instrumentation
    overhead is small relative to the quantity being measured.
  actual: >
    Four distinct problems.

    (a) Measurement defect. _display_loop computes the pacing sleep and
    calls time.sleep(_sleep) at manager.py:441, then calls
    self.performance_monitor.record_frame_end(frame_id) at manager.py:442
    — after the sleep. The recorded interval therefore spans render plus
    idle padding and converges on the 16.67 ms target regardless of actual
    render cost. Two consequences: reported frame_time_ms and fps are
    meaningless as a measure of render load; and the dropped-frame test
    frame_time > self.frame_time_target * 1.5 at monitor.py:188 can only
    fire when a frame overruns by more than 50%, and tests the padded value
    when it does.

    (b) Unconditional metrics call. manager.py:445-452 calls
    self.performance_monitor.get_current_metrics() on every frame, guarded
    only by "if frame_id and len(frame_id) > 0", purely to test
    metrics.total_frames % 600 == 0 — a value the monitor already holds
    internally as self._frame_count.

    (c) psutil read per frame. get_current_metrics reaches
    _get_current_memory_usage (monitor.py:407), which calls
    self._process.memory_info() at monitor.py:411. Because (b) calls
    get_current_metrics every frame, /proc is read at the frame rate.

    (d) Per-frame UUID and expiry scan. record_frame_start allocates
    str(uuid.uuid4())[:8] at monitor.py:143 for the frame ID, then builds a
    full list comprehension over self._active_frames at monitor.py:149-151
    to expire stale entries. Both run on every frame; the dictionary holds
    one live entry in normal operation.
  impact: >
    Fault (a) is the blocking one. The report states that the existing
    telemetry cannot be used to confirm or exclude frame-time jitter
    (§4.5), and ai/task.md §7.5.3 records that the logged figure measures
    padded rather than render time until this is corrected. Every
    subsequent rendering-efficiency task — 7.3.5, 7.3.6 — is judged against
    a baseline that does not currently exist. Faults (b), (c) and (d) place
    measurement overhead inside the budget being measured, on a Cortex-A53
    executing Python.
  workaround: >
    None within the application. External timing would require
    instrumentation that does not exist.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "psutil"
      version: "as installed"
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    The frame-end call was placed at the end of the loop body rather than
    at the end of the rendered work, so it measures the loop period instead
    of the render duration. The periodic-logging gate was written in the
    caller rather than the monitor, which forces a full metrics
    construction — including the psutil read — to obtain a counter the
    monitor already owns. The frame identifier was implemented as a UUID
    where a process-local monotonic integer is sufficient, since the ID
    never leaves the monitor.
  technical_notes: >
    Moving record_frame_end before the sleep changes the meaning of every
    historical figure in _frame_history. The dropped-frame test at
    monitor.py:188 becomes meaningful for the first time and will begin
    firing on genuine overruns; a rise in the dropped-frame count after
    this change is the expected result, not a regression.

    _calculate_current_fps derives from _frame_history timestamps rather
    than from frame_time, so the reported FPS remains a true rate after the
    change; only frame_time_ms changes meaning.

    The frame ID is typed str throughout (record_frame_start -> str,
    record_frame_end(frame_id: str), _active_frames: Dict[str, float]) and
    manager.py tests "if frame_id and len(frame_id) > 0". Changing to an
    integer requires the type annotations and that truthiness test to be
    updated together, and the empty-string sentinel returned when
    monitoring is disabled needs an integer equivalent.
  related_issues:
    - issue_ref: "issue-9ed1c77e"
      relationship: "blocks"
    - issue_ref: "issue-821919ce"
      relationship: "blocks"
    - issue_ref: "issue-c5dedd71"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Move record_frame_end before the pacing sleep; move the periodic
    logging gate inside the monitor; replace the UUID frame ID with a
    monotonic integer; sample psutil memory at 1 Hz rather than per frame.
    See change-0b00759c.
  change_ref: "change-0b00759c"
  resolved_date: "2026-07-30"
  resolved_by: "Claude Code, per prompt-0b00759c"
  fix_description: >
    Seven edits across the two files named in change-0b00759c, all
    applied as specified.

    Fault (a), the measurement defect: record_frame_end now sits
    immediately after rendering_engine.write_to_framebuffer() at
    manager.py:435, above the pacing time.sleep at manager.py:446, so the
    recorded interval spans rendered work only. The dropped-frame test at
    monitor.py:188 now evaluates real render times and its count is
    expected to rise.

    Fault (b), the unconditional metrics call: PerformanceMonitor gained
    should_log_periodic(), which tests self._frame_count against
    self._log_interval_frames (600) under the lock. _display_loop calls it
    in place of the old "if frame_id and len(frame_id) > 0" guard and
    constructs a metrics object only when it returns True. The log message
    text and its three fields are unchanged.

    Fault (c), the per-frame psutil read: _get_current_memory_usage caches
    the RSS figure in _memory_cache_mb with timestamp _memory_cache_ts and
    re-reads at most once per _memory_sample_interval (1.0 s). The
    _memory_samples fallback and the except clause returning 0.0 are
    retained, so a failed read cannot poison the cache.

    Fault (d), the per-frame UUID and expiry scan: record_frame_start now
    returns an int from _frame_id_counter (first valid ID 1, 0 reserved
    for the disabled case) and the expiry scan is skipped when
    len(_active_frames) <= 1, the steady state. _active_frames is retyped
    Dict[int, float] and the now-unused "import uuid" was removed.
    reset_metrics clears the counter and both cache fields.

    Not fixed in this change: the two matching declarations on
    PerformanceMonitorInterface (interfaces.py:73, 78) still read str,
    because prompt-0b00759c confined the executor to monitor.py and
    manager.py. Raised as issue-c5dedd71. No runtime effect — annotations
    are not enforced and PerformanceMonitor remains instantiable.
    Subsequently corrected under change-c5dedd71: interfaces.py:73 and 83
    now read "-> int" and "frame_id: int", matching the implementation.
    That triple is closed, so this residual is discharged.

verification:
  verified_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Development platform only; see change-0b00759c
    verification.test_results for the full record and closure_notes below
    for the closure re-verification.

    Re-verified at closure against the current working tree: twenty-three
    assertions over the ten change test cases and the four prompt edge
    cases, all passing, driving the real PerformanceMonitor with pygame
    and psutil stubbed. The on-target observations remain outstanding and
    are owned by William Watson; they are the purpose of this issue, not
    conditions of its closure.
  closure_notes: >
    All four faults reported in behavior.actual are corrected, and the
    correction to fault (a) — the one that blocked everything else — is
    observable off-target: a bracketed 5 ms sleep is recorded as ~6 ms
    where before the change it would have been padded to the 16.67 ms
    frame target. Faults (b), (c) and (d) were verified by counting calls
    rather than by timing: should_log_periodic returns True only on frames
    600 and 1200 of a 1200-frame run, so get_current_metrics is
    constructed twice rather than 1200 times; a mocked memory_info() is
    invoked once across 100 rapid calls; frame IDs are ints from a
    monotonic counter and the expiry scan is skipped while at most one
    frame is active.

    Two behaviours that the change deliberately did not alter were
    confirmed unchanged: the periodic log line's text and its three
    fields, and get_current_metrics().to_dict(), which
    DisplayManager.get_status consumes on demand and which still returns
    a populated dict.

    Four verification steps remain open by design and are not conditions
    of this closure, all owned by William Watson and all requiring
    gtach.local: reading the periodic log line and confirming
    frame_time_ms is materially below 16.7 ms and differs between the
    OPTIONS screen and RADIAL mode; confirming the reported fps remains a
    true rate; confirming the psutil memory figure still updates on
    target; and recording the observed frame_time_ms as the ai/task.md
    §7.5.3 baseline. That last step is the reason this work was
    prioritised, and tasks 7.3.5 and 7.3.6 stay without a baseline until
    it is taken — but it is an observation to be made on hardware, not an
    outstanding defect in the code, and ai/task.md carries it
    independently of this triple.

    The residual recorded in fix_description is discharged:
    issue-c5dedd71 corrected the two PerformanceMonitorInterface
    annotations and its triple is closed.

    The absence of any test module under tests/ is a standing
    project-wide gap and is not raised as a residual against this issue.

prevention:
  preventive_measures: >
    Instrumentation that brackets a measured region must be placed at the
    boundaries of that region, not at the boundaries of the enclosing loop.
    Any accessor invoked from a per-frame path should be reviewed for
    incidental cost — get_current_metrics performs a psutil read that is
    not evident at its call site.
  process_improvements: >
    A measurement change that alters the meaning of a recorded quantity
    should be landed and its new baseline recorded before any change that
    will be judged against that baseline.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/performance/monitor.py passes."
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "Confirm by inspection that record_frame_end is called before time.sleep in _display_loop."
    - "Run on gtach.local and read the periodic log line. frame_time_ms must now be materially below 16.7 ms, and must differ between the OPTIONS screen and RADIAL mode."
    - "Confirm the reported fps remains a plausible rate and has not become 1000/render_time."
    - "Confirm the psutil memory figure still updates and is no longer read per frame."
    - "Confirm no UUID string appears in the frame identifier path."
    - "Record the observed frame_time_ms as the baseline required by ai/task.md §7.5.3."
  verification_results: >
    Four of the eight steps are complete; four require gtach.local and are
    outstanding.

    PASS — py_compile on src/gtach/display/performance/monitor.py.
    PASS — py_compile on src/gtach/display/manager.py.
    PASS — record_frame_end is called before time.sleep in _display_loop:
    manager.py:435 against manager.py:446 by source order.
    PASS — no UUID string appears in the frame identifier path:
    "uuid.uuid4()" is gone from monitor.py and the unused "import uuid"
    was removed. record_frame_start returns ints from _frame_id_counter,
    confirmed 1 then 2 on a live object.

    Additionally confirmed off-target, ahead of the on-target steps: a
    5 ms bracketed sleep measured 6.28 ms rather than 16.67 ms, which is
    the fault (a) correction observable without the device; and a mocked
    psutil memory_info() was invoked once across 100 rapid calls and again
    only after the cache timestamp passed 1 s, which is the fault (c)
    correction.

    OUTSTANDING — run on gtach.local and read the periodic log line;
    frame_time_ms must be materially below 16.7 ms and must differ between
    the OPTIONS screen and RADIAL mode.
    OUTSTANDING — confirm the reported fps remains a plausible rate and
    has not become 1000/render_time. _calculate_current_fps was left
    untouched and derives from _frame_history timestamps, so this is
    expected to hold, but it has not been observed.
    OUTSTANDING — confirm the psutil memory figure still updates on the
    device.
    OUTSTANDING — record the observed frame_time_ms as the ai/task.md
    §7.5.3 baseline.

    Closure re-verification, 2026-07-30, against the working tree at that
    date. The four PASS steps were re-run and hold. Line references have
    since moved: record_frame_end is now manager.py:445 and the pacing
    time.sleep manager.py:456, the shift coming from change-4c038bed in
    the same file; the source order the step asserts is unaffected.
    Twenty-three assertions were executed against the real
    PerformanceMonitor with pygame and psutil stubbed — the ten change
    test cases, the four prompt edge cases, and additional checks that a
    failed psutil read returns 0.0 without poisoning the cache, that the
    _memory_samples fallback is taken when _process is None, that a stale
    entry is expired once a second frame makes the scan reachable, that
    record_frame_end after stop_monitoring returns 0.0 without raising,
    that get_current_metrics().to_dict() is still populated, and that the
    three signatures carry the int and bool annotations the prompt
    specifies. All pass. The four OUTSTANDING steps above still require
    gtach.local and are unchanged by this closure.

traceability:
  design_refs: []
  change_refs:
    - "change-0b00759c"
  test_refs: []

notes: >
  This is task 7.3.7 in ai/task.md §7.3 and the second item in the
  recommended authoring order (§7.6.2), because it is the prerequisite for
  measuring anything. ai/task.md §7.5.3 depends on it directly: until it
  ships, the logged figure measures padded rather than render time and no
  baseline exists for judging tasks 7.3.5 and 7.3.6.

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
      - "Initial issue document from display-ui-graphics-review.md recommendations 15, 16, 17 and 18."
  - version: "1.1"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Status open -> resolved. change-0b00759c implemented; resolution date, executor and fix description recorded for all four faults."
      - "Recorded four of eight verification steps as PASS and four as OUTSTANDING pending gtach.local."
      - "Recorded issue-c5dedd71 as related: the matching PerformanceMonitorInterface declarations were out of the executor's permitted file scope and still read str."
      - "Status is resolved rather than verified because the ai/task.md §7.5.3 baseline reading has not been taken."
  - version: "1.2"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status resolved -> closed. Verification date and verifier recorded; closure_notes replaced with the closure record."
      - "Recorded the closure re-verification: twenty-three assertions over the ten change test cases and four prompt edge cases against the real PerformanceMonitor, all passing."
      - "Noted that the change-c5dedd71 residual is discharged — the two PerformanceMonitorInterface annotations now read int and that triple is closed."
      - "Noted that the four on-target steps, including the ai/task.md §7.5.3 baseline reading, remain open by design and are owned by William Watson rather than being conditions of closure."
      - "Moved to ai/workspace/issues/closed/ per P00 §1.1.14.4."

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
| 1.0 | 2026-07-30 | Initial issue document from display-ui-graphics-review.md recommendations 15, 16, 17 and 18. |
| 1.1 | 2026-07-30 | Status open → resolved; fix description and per-step verification status recorded; issue-c5dedd71 linked; on-target §7.5.3 baseline noted as outstanding. |
| 1.2 | 2026-07-30 | Status resolved → closed; closure re-verification recorded; issue-c5dedd71 residual discharged; four on-target steps left open by design. Moved to ai/workspace/issues/closed/ per P00 §1.1.14.4. |

---

Copyright (c) 2026 William Watson. MIT License.
