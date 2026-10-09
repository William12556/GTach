Created: 2026 October 09

# Prompt: Monotonic Clock for Remaining Durations

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-e215a184"
  task_type: "debug"
  source_ref: "change-e215a184"
  target_profile: "claude_code"
  date: "2026-10-09"
  iteration: 1
  coupled_docs:
    change_ref: "change-e215a184"
    change_iteration: 1

context:
  purpose: "Durations, rates and cache ages in five files use time.monotonic()."
  integration: "device_surfaces.py, circular_positioning.py, rendering/engine.py, performance/monitor.py, utils/platform.py; tests/test_monotonic_durations.py."
  knowledge_references:
    - "ai/workspace/issues/issue-e215a184-wall-clock-durations-remaining.md"
    - "ai/workspace/change/change-e215a184-wall-clock-durations-remaining.md"
  constraints:
    - "CRITICAL: classify per variable or record field, not per line. Switch a variable to time.monotonic() at every assignment only if every read of it is a difference or comparison with a value from the same clock. Never subtract values from different clocks."
    - "Keep time.time() where any reader interprets the value as a wall-clock time (formatted as a date, compared with time.time(), logged or persisted as a timestamp). monitor.py 'timestamp' at ~line 539 stays time.time()."
    - "PlatformDetector info dict 'last_detection_time' (~line 733): grep its consumers; switch only if none interprets it as an epoch time; report the outcome."
    - "Only the five files listed; sim_transport.py and manager.py are out of scope."
    - "Requires change-273ca048 already applied."
    - "Line numbers are from ba661d4; locate code by symbol."

specification:
  description: "Clock switch per change-e215a184, with a classification table in the report."
  requirements:
    functional:
      - "Wall-clock steps do not affect FPS, frame-time, uptime, memory-cache age or the platform-detection cache."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Comment at each switched variable's initialisation citing issue-e215a184"
  performance: []

design:
  architecture: "Per-variable clock classification."
  components:
    - name: "Classification"
      type: "module"
      purpose: "Before editing, list every time.time() site in the five files with its variable, all reads, and the decision (monotonic or wall-clock with reason). Put this table in the report."
      logic:
        - "monitor.py variables to classify include _start_time, _memory_cache_ts (and its comment), _last_metrics_update, _active_frames values, frame-history 'timestamp' entries (~215, read ~445, ~564), memory-history 'timestamp' (~309), metrics last_update_time (~346, read ~363)."
        - "platform.py: _last_detection_time (init ~101, set ~144, reset ~761, read ~130, ~506, ~735) and the current_time locals."
        - "device_surfaces.py, circular_positioning.py, engine.py: local start/end pairs."
    - name: "tests/test_monotonic_durations.py"
      type: "module"
      purpose: "Clock-step regression tests."

data_schema:
  entities: []

error_handling:
  strategy: "Unchanged."
  exceptions: []
  logging:
    level: "Unchanged"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "PlatformDetector: run detection; monkeypatch time.time to return real+3600; run detection again within the cache duration."
      expected: "Cached result; the detection routine is not re-run (spy)."
    - scenario: "PerformanceMonitor: start monitoring; monkeypatch time.time to return real-3600; read uptime from the stats it reports."
      expected: "Uptime ≥ 0 and < 5 s."
  edge_cases:
    - "A record field read both as an age and as a displayed timestamp: keep time.time(), report it."
  validation:
    - "grep -n 'time.time()' over the five files lists only sites classified wall-clock in the report."
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Save code directly to the listed paths."
    - "Run pytest tests/ on completion; report pass/fail counts."
  files:
    - path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      content: "Clock switch"
    - path: "src/gtach/display/setup_components/layout/circular_positioning.py"
      content: "Clock switch"
    - path: "src/gtach/display/rendering/engine.py"
      content: "Clock switch"
    - path: "src/gtach/display/performance/monitor.py"
      content: "Clock switch"
    - path: "src/gtach/utils/platform.py"
      content: "Clock switch"
    - path: "tests/test_monotonic_durations.py"
      content: "Regression tests"

success_criteria:
  - "Classification table present in the report; every remaining time.time() in the five files is justified there."
  - "The two regression tests pass."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules: []
    classes:
      - name: "PerformanceMonitor"
        module: "gtach.display.performance.monitor"
      - name: "PlatformDetector"
        module: "gtach.utils.platform"
    functions: []
    constants: []

notes: "Human verification on the Pi: FPS and render-time figures in debug.log are plausible after boot (NTP step)."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial prompt implementing change-e215a184 iteration 1. Target profile claude_code. |
| 1.1 | 2026-10-09 | Implemented; closed |

---

Copyright (c) 2026 William Watson. MIT License.
