Created: 2026 July 30

# Prompt: Correct Frame-Time Measurement and Reduce Instrumentation Overhead

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-0b00759c"
  task_type: "code_generation"
  source_ref: "change-0b00759c"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-0b00759c"
    change_iteration: 1

context:
  purpose: >
    Make frame_time_ms measure the cost of rendering a frame rather than
    the period of the display loop, and remove four instrumentation costs
    from the per-frame path. Without this, no rendering-efficiency change
    can be judged, because the current figure converges on the frame target
    regardless of render load.
  integration: >
    Two files: src/gtach/display/performance/monitor.py and
    src/gtach/display/manager.py. Seven edits. Executor is Claude Code;
    AEL is not used. This is the second item in the recommended authoring
    order of ai/task.md §7.6.2 and the direct prerequisite for the baseline
    observation recorded as §7.5.3.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/performance/monitor.py and src/gtach/display/manager.py."
    - "Do not change what is rendered. This change alters measurement only."
    - "Do not change the periodic log message text or its three reported fields."
    - "Do not change fps_limit, add frame skipping, or cache any rendered surface. Those are separate changes."
    - "Do not remove psutil. Rate-limit its use."
    - "Leave the dirty-region API (add_dirty_region, get_dirty_regions, clear_dirty_regions) untouched."
    - "Leave _calculate_current_fps, _update_metrics_history and get_historical_metrics untouched."
    - "Frame ID 0 is the disabled-monitoring sentinel. The first valid ID is 1, so no valid ID is ever falsy."
    - "Update type annotations wherever the frame ID type changes: record_frame_start, record_frame_end, _active_frames."
    - "Type hints on all public interfaces; Google-style docstrings; PEP 8."

specification:
  description: >
    Move record_frame_end before the pacing sleep; add a periodic-logging
    accessor to the monitor and stop calling get_current_metrics per frame;
    replace the UUID frame ID with a monotonic integer; cache the psutil
    memory reading at 1 Hz.
  requirements:
    functional:
      - "record_frame_end is called immediately after write_to_framebuffer and before the pacing sleep."
      - "record_frame_start returns a monotonically increasing int starting at 1, or 0 when monitoring is disabled."
      - "The stale-frame expiry scan is skipped when at most one frame is active."
      - "PerformanceMonitor.should_log_periodic() returns True exactly once every 600 recorded frames."
      - "The display loop constructs a metrics object only when should_log_periodic() returns True."
      - "_get_current_memory_usage reads psutil at most once per second and returns a cached value otherwise."
      - "reset_metrics clears the frame ID counter and the memory cache."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Remove one psutil /proc read, one UUID allocation, one dict comprehension and one metrics construction per frame"
      metric: "time"

design:
  architecture: >
    The monitor owns the periodic-logging decision instead of exposing a
    counter through a full metrics object, and owns the rate limit on its
    own psutil sampling. The caller's only responsibility is to bracket the
    rendered work correctly.
  components:
    - name: "PerformanceMonitor.__init__"
      type: "function"
      purpose: "Hold the frame ID counter, the memory cache and the interval constants."
      logic:
        - "Add self._frame_id_counter = 0"
        - "Add self._memory_cache_mb = 0.0"
        - "Add self._memory_cache_ts = 0.0"
        - "Add self._memory_sample_interval = 1.0"
        - "Add self._log_interval_frames = 600"
        - "Retype self._active_frames from Dict[str, float] to Dict[int, float]."
    - name: "PerformanceMonitor.record_frame_start"
      type: "function"
      purpose: "Issue a cheap frame identifier and record its start time."
      interface:
        inputs: []
        outputs:
          type: "int"
          description: "Positive frame ID, or 0 when monitoring is disabled or an error occurs."
        raises:
          - "None. Returns 0 on error, logged at ERROR."
      logic:
        - "Return 0 instead of '' when not self._monitoring."
        - "self._frame_id_counter += 1; frame_id = self._frame_id_counter."
        - "Record self._active_frames[frame_id] = current_time."
        - "Skip the expiry scan entirely when len(self._active_frames) <= 1 — the normal steady state."
        - "Otherwise run the existing cutoff scan unchanged, incrementing _dropped_frames per expired entry."
        - "Return 0 in the except clause."
    - name: "PerformanceMonitor.record_frame_end"
      type: "function"
      purpose: "Close a frame and record its duration."
      interface:
        inputs:
          - name: "frame_id"
            type: "int"
            description: "Identifier returned by record_frame_start. 0 means monitoring was disabled."
        outputs:
          type: "float"
          description: "Frame duration in seconds, or 0.0."
        raises:
          - "None. Returns 0.0 on error, logged at ERROR."
      logic:
        - "Guard becomes: if not self._monitoring or not frame_id — 0 is falsy and no valid ID is 0."
        - "Leave the _active_frames pop, the frame_time computation, the _frame_history append, the _frame_count increment, the dropped-frame test and the periodic _update_metrics_history call exactly as they are."
    - name: "PerformanceMonitor.should_log_periodic"
      type: "function"
      purpose: "Decide whether the caller should emit the periodic performance line, without constructing a metrics object."
      interface:
        inputs: []
        outputs:
          type: "bool"
          description: "True on every self._log_interval_frames-th recorded frame."
        raises:
          - "None. Returns False on error."
      logic:
        - "Return False when not self._monitoring."
        - "Under self._lock: return self._frame_count > 0 and self._frame_count % self._log_interval_frames == 0."
        - "Wrap in try/except Exception returning False."
    - name: "PerformanceMonitor._get_current_memory_usage"
      type: "function"
      purpose: "Report process RSS in MB, sampled at most once per second."
      interface:
        inputs: []
        outputs:
          type: "float"
          description: "Resident set size in MB."
        raises:
          - "None. Returns 0.0 on error."
      logic:
        - "If self._process is set: read now = time.time(); if self._memory_cache_ts and now - self._memory_cache_ts < self._memory_sample_interval, return self._memory_cache_mb."
        - "Otherwise call self._process.memory_info(), compute rss / (1024 * 1024), store it and now in the cache, and return it."
        - "Retain the existing elif self._memory_samples fallback and the else returning 0.0."
        - "Retain the existing except clause returning 0.0."
    - name: "PerformanceMonitor.reset_metrics"
      type: "function"
      purpose: "Clear the new state alongside the existing state."
      logic:
        - "Reset self._frame_id_counter = 0, self._memory_cache_mb = 0.0, self._memory_cache_ts = 0.0."
    - name: "DisplayManager._display_loop"
      type: "function"
      purpose: "Bracket rendered work correctly and stop constructing metrics per frame."
      logic:
        - "Move the record_frame_end call from after time.sleep to immediately after rendering_engine.write_to_framebuffer()."
        - "Replace the frame_id truthiness guard and the get_current_metrics call with a single should_log_periodic() test."
  dependencies:
    internal:
      - "DisplayManager._display_loop — the sole caller of the two retyped signatures; updated in this change."
      - "DisplayManager.get_status (manager.py:1548) — calls get_current_metrics().to_dict() on demand; unaffected."
    external:
      - "psutil — read frequency reduced; no version change."

data_schema:
  entities:
    - name: "PerformanceMonitor._active_frames"
      attributes:
        - name: "key"
          type: "int"
          constraints: "Positive. Was str (8-hex UUID prefix)."
        - name: "value"
          type: "float"
          constraints: "time.time() at frame start."
      validation:
        - "In-memory only. Nothing is persisted, so no migration is required."

error_handling:
  strategy: >
    Every changed path retains its existing try/except and returns the same
    kind of neutral value on failure. The new accessor returns False on
    error so a monitoring fault suppresses logging rather than raising into
    the display loop.
  exceptions:
    - exception: "Exception"
      condition: "Failure in record_frame_start."
      handling: "logger.error; return 0 (was '')."
    - exception: "Exception"
      condition: "Failure in record_frame_end."
      handling: "Existing handler retained; return 0.0."
    - exception: "Exception"
      condition: "Failure in should_log_periodic."
      handling: "Return False. Do not raise."
    - exception: "Exception"
      condition: "psutil read failure in _get_current_memory_usage."
      handling: "Existing handler retained; return 0.0. Do not poison the cache with a failed read."
  logging:
    level: "ERROR"
    format: "logger.error(f'...: {e}')"

testing:
  unit_tests:
    - scenario: "record_frame_start called twice with monitoring enabled."
      expected: "Returns 1 then 2."
    - scenario: "record_frame_start with monitoring disabled."
      expected: "Returns 0."
    - scenario: "record_frame_end(0)."
      expected: "Returns 0.0 with no warning logged."
    - scenario: "record_frame_start, sleep 5 ms, record_frame_end."
      expected: "Returned duration is approximately 0.005 s, not 0.0167 s."
    - scenario: "600 recorded frames, calling should_log_periodic after each."
      expected: "True returned exactly once, on frame 600."
    - scenario: "should_log_periodic with monitoring disabled."
      expected: "False."
    - scenario: "_get_current_memory_usage called 100 times in rapid succession, psutil mocked."
      expected: "memory_info() invoked once."
    - scenario: "_get_current_memory_usage, clock advanced past 1 s, called again."
      expected: "memory_info() invoked a second time."
    - scenario: "reset_metrics then record_frame_start."
      expected: "Frame ID restarts at 1."
    - scenario: "A frame exceeding frame_time_target * 1.5."
      expected: "_dropped_frames increments."
  edge_cases:
    - "Monitoring disabled mid-run: record_frame_end receives a valid ID after _monitoring goes False — returns 0.0, no exception."
    - "Frame ID counter over a long run: Python ints are unbounded; no wraparound handling needed."
    - "psutil absent, so self._process is None: the _memory_samples fallback path is taken and the cache is not consulted."
    - "First call to _get_current_memory_usage with _memory_cache_ts at 0.0: reads psutil and seeds the cache rather than returning 0.0."
  validation:
    - "No existing test asserts a string frame ID; if one does, update it in this change."
    - "get_status() still returns a populated performance_metrics dict."

deliverable:
  format_requirements:
    - "Edit both files in place. Create no new file."
    - "Make the seven edits below and change nothing else."
  files:
    - path: "src/gtach/display/performance/monitor.py"
      content: |
        EDIT A — PerformanceMonitor.__init__

        Retype the _active_frames declaration (currently monitor.py:50):
            self._active_frames: Dict[int, float] = {}  # frame_id -> start_time

        Add alongside it:
            # Instrumentation cost reduction (change-0b00759c)
            self._frame_id_counter = 0        # monotonic frame ID source
            self._memory_cache_mb = 0.0       # cached psutil RSS reading
            self._memory_cache_ts = 0.0       # time.time() of that reading
            self._memory_sample_interval = 1.0   # seconds between psutil reads
            self._log_interval_frames = 600      # periodic log cadence

        EDIT B — record_frame_start (currently monitor.py:136)

        Change the signature to:
            def record_frame_start(self) -> int:

        Change the disabled-monitoring return from `return ""` to `return 0`.

        Replace:
                    frame_id = str(uuid.uuid4())[:8]
        with:
                    self._frame_id_counter += 1
                    frame_id = self._frame_id_counter

        Wrap the existing expiry scan so it only runs when it can do
        anything. Replace:
                    # Clean up old frame IDs (safety measure)
                    cutoff_time = current_time - 1.0  # 1 second timeout
                    expired_frames = [fid for fid, start_time in self._active_frames.items()
                                    if start_time < cutoff_time]
                    for fid in expired_frames:
                        del self._active_frames[fid]
                        self._dropped_frames += 1
        with:
                    # Clean up old frame IDs (safety measure). In steady state
                    # exactly one frame is active, so the scan is skipped.
                    if len(self._active_frames) > 1:
                        cutoff_time = current_time - 1.0  # 1 second timeout
                        expired_frames = [fid for fid, start_time in self._active_frames.items()
                                        if start_time < cutoff_time]
                        for fid in expired_frames:
                            del self._active_frames[fid]
                            self._dropped_frames += 1

        Change the except clause return from `return ""` to `return 0`.

        If `import uuid` (monitor.py:19) becomes unused after this edit,
        remove it. Check for other uses first.

        EDIT C — record_frame_end (currently monitor.py:162)

        Change the signature to:
            def record_frame_end(self, frame_id: int) -> float:

        Update the docstring to note that 0 means monitoring was disabled.
        The existing guard `if not self._monitoring or not frame_id:` is
        already correct for an integer sentinel of 0 — leave it as it is.

        Change nothing else in this method.

        EDIT D — add should_log_periodic immediately AFTER record_frame_end

            def should_log_periodic(self) -> bool:
                """Whether the caller should emit the periodic performance line.

                Replaces a per-frame get_current_metrics() call made only to
                read a frame counter the monitor already holds. Constructing
                the metrics object also performs a psutil read, so testing
                the counter directly removes that cost from the frame path.

                Returns:
                    True on every self._log_interval_frames-th recorded frame.
                """
                if not self._monitoring:
                    return False

                try:
                    with self._lock:
                        return (
                            self._frame_count > 0
                            and self._frame_count % self._log_interval_frames == 0
                        )
                except Exception as e:
                    self.logger.error(f"Error testing periodic log interval: {e}")
                    return False

        EDIT E — _get_current_memory_usage (currently monitor.py:407)

        Replace the body of the try block. Currently:
                    if self._process:
                        memory_info = self._process.memory_info()
                        return memory_info.rss / (1024 * 1024)  # Convert to MB
                    elif self._memory_samples:
                        return self._memory_samples[-1]['usage_mb']
                    else:
                        return 0.0

        Replace with:
                    if self._process:
                        now = time.time()
                        if (self._memory_cache_ts
                                and now - self._memory_cache_ts < self._memory_sample_interval):
                            return self._memory_cache_mb

                        memory_info = self._process.memory_info()
                        self._memory_cache_mb = memory_info.rss / (1024 * 1024)
                        self._memory_cache_ts = now
                        return self._memory_cache_mb
                    elif self._memory_samples:
                        return self._memory_samples[-1]['usage_mb']
                    else:
                        return 0.0

        Leave the except clause returning 0.0 unchanged. A failed read must
        not update the cache.

        EDIT F — reset_metrics (currently monitor.py:303)

        Alongside the existing self._active_frames.clear() (monitor.py:313),
        add:
                    self._frame_id_counter = 0
                    self._memory_cache_mb = 0.0
                    self._memory_cache_ts = 0.0

    - path: "src/gtach/display/manager.py"
      content: |
        EDIT G — DisplayManager._display_loop (currently manager.py:397-456)

        The current tail of the loop body reads:

                        # Swap buffers and write to framebuffer
                        self.rendering_engine.swap_buffers()
                        self.rendering_engine.write_to_framebuffer()

                        # Tick clock and record frame end
                        # pygame.time.Clock.tick() uses SDL_Delay which can block
                        # indefinitely on macOS when the Cocoa run loop stalls.
                        # Use time.sleep() for reliable frame pacing on all platforms.
                        _frame_end = time.monotonic()
                        _frame_elapsed = _frame_end - _frame_start
                        _frame_target = 1.0 / self.config.fps_limit
                        _sleep = _frame_target - _frame_elapsed
                        if _sleep > 0:
                            time.sleep(_sleep)
                        self.performance_monitor.record_frame_end(frame_id)

                        # Periodic performance logging
                        if frame_id and len(frame_id) > 0:  # Every few frames
                            metrics = self.performance_monitor.get_current_metrics()
                            if metrics.total_frames % 600 == 0:  # Every 10 seconds at 60fps
                                self.logger.info(
                                    f"Performance: {metrics.fps:.1f} FPS, "
                                    f"{metrics.frame_time_ms:.1f}ms frame, "
                                    f"{metrics.memory_usage_mb:.1f}MB mem"
                                )

        Replace it with:

                        # Swap buffers and write to framebuffer
                        self.rendering_engine.swap_buffers()
                        self.rendering_engine.write_to_framebuffer()

                        # Close the frame BEFORE the pacing sleep so the recorded
                        # interval measures render cost, not the loop period
                        # (display review §6.2, recommendation 15).
                        self.performance_monitor.record_frame_end(frame_id)

                        # Frame pacing.
                        # pygame.time.Clock.tick() uses SDL_Delay which can block
                        # indefinitely on macOS when the Cocoa run loop stalls.
                        # Use time.sleep() for reliable frame pacing on all platforms.
                        _frame_end = time.monotonic()
                        _frame_elapsed = _frame_end - _frame_start
                        _frame_target = 1.0 / self.config.fps_limit
                        _sleep = _frame_target - _frame_elapsed
                        if _sleep > 0:
                            time.sleep(_sleep)

                        # Periodic performance logging. The monitor owns the
                        # cadence test, so no metrics object is constructed on
                        # ordinary frames (recommendation 16).
                        if self.performance_monitor.should_log_periodic():
                            metrics = self.performance_monitor.get_current_metrics()
                            self.logger.info(
                                f"Performance: {metrics.fps:.1f} FPS, "
                                f"{metrics.frame_time_ms:.1f}ms frame, "
                                f"{metrics.memory_usage_mb:.1f}MB mem"
                            )

        Change nothing else in the method. record_frame_start stays where it
        is (manager.py:413) and the frame_id variable keeps its name.

success_criteria:
  - "python -m py_compile src/gtach/display/performance/monitor.py passes."
  - "python -m py_compile src/gtach/display/manager.py passes."
  - "pytest tests/ passes with no new failures."
  - "In _display_loop, the record_frame_end call appears above the time.sleep call by source order."
  - "The expression 'len(frame_id)' no longer appears in manager.py."
  - "get_current_metrics() is called in _display_loop only inside the should_log_periodic() guard."
  - "record_frame_start is annotated -> int and returns 0 when monitoring is disabled."
  - "record_frame_end is annotated frame_id: int."
  - "_active_frames is annotated Dict[int, float]."
  - "The string 'uuid.uuid4()' no longer appears in monitor.py; the uuid import is removed if it has no other use."
  - "PerformanceMonitor defines should_log_periodic() -> bool."
  - "_get_current_memory_usage consults self._memory_cache_ts before calling memory_info()."
  - "reset_metrics clears _frame_id_counter, _memory_cache_mb and _memory_cache_ts."
  - "No file other than the two named is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "monitor"
        path: "src/gtach/display/performance/monitor.py"
      - name: "manager"
        path: "src/gtach/display/manager.py"
    classes:
      - name: "PerformanceMonitor"
        module: "gtach.display.performance.monitor"
      - name: "PerformanceMetrics"
        module: "gtach.display.performance.monitor"
      - name: "DisplayManager"
        module: "gtach.display.manager"
    functions:
      - name: "record_frame_start"
        module: "gtach.display.performance.monitor"
        signature: "record_frame_start(self) -> int"
      - name: "record_frame_end"
        module: "gtach.display.performance.monitor"
        signature: "record_frame_end(self, frame_id: int) -> float"
      - name: "should_log_periodic"
        module: "gtach.display.performance.monitor"
        signature: "should_log_periodic(self) -> bool"
      - name: "_get_current_memory_usage"
        module: "gtach.display.performance.monitor"
        signature: "_get_current_memory_usage(self) -> float"
      - name: "reset_metrics"
        module: "gtach.display.performance.monitor"
        signature: "reset_metrics(self) -> None"
    constants:
      - name: "_log_interval_frames"
        module: "gtach.display.performance.monitor"
        type: "int"
      - name: "_memory_sample_interval"
        module: "gtach.display.performance.monitor"
        type: "float"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-0b00759c-performance-instrumentation.md

  Frame-time figures recorded before and after this change are not
  comparable. The dropped-frame count is expected to rise, because the test
  at monitor.py:188 now sees real render times. After deployment, record
  the observed frame_time_ms as the baseline required by ai/task.md §7.5.3;
  tasks 7.3.5 and 7.3.6 are judged against it.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-0b00759c. |

---

Copyright (c) 2026 William Watson. MIT License.
