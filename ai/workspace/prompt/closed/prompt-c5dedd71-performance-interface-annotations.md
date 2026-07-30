

Created: 2026 July 30

# Prompt: Realign PerformanceMonitorInterface Frame-ID Annotations

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-c5dedd71"
  task_type: "refactor"
  source_ref: "change-c5dedd71"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-c5dedd71"
    change_iteration: 1

context:
  purpose: >
    Restore agreement between PerformanceMonitorInterface and its sole
    implementation. change-0b00759c replaced the UUID-string frame
    identifier with a monotonic integer in PerformanceMonitor but left the
    abstract base class declaring str, so the ABC now states a contract the
    only implementation does not honour. A static type checker reads this
    as a Liskov violation on two methods; a reader of the interface is
    told the wrong type.
  integration: >
    One file: src/gtach/display/performance/interfaces.py. Two edits, both
    annotation and docstring only. Executor is Claude Code; AEL is not
    used. This is a follow-on to task 7.3.7 of ai/task.md (change-0b00759c)
    and blocks nothing; it may be taken at any point.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/performance/interfaces.py."
    - "Annotations and docstrings only. No executable statement changes."
    - "Do not add or remove abstract methods."
    - "Do not add should_log_periodic to the ABC — see design.architecture for the rationale."
    - "Do not alter PerformanceMetrics, its defaults, to_dict, or MetricType."
    - "Do not alter the remaining eleven abstract method signatures. The ABC declares thirteen in total."
    - "Abstract method bodies stay `pass`."
    - "Do not touch src/gtach/display/performance/monitor.py — it is already correct as of change-0b00759c."
    - "Type hints on all public interfaces; Google-style docstrings; PEP 8."

specification:
  description: >
    Retype record_frame_start to return int and record_frame_end to accept
    an int frame_id in PerformanceMonitorInterface, and document the 0
    sentinel on both.
  requirements:
    functional:
      - "PerformanceMonitorInterface.record_frame_start is annotated -> int."
      - "PerformanceMonitorInterface.record_frame_end is annotated frame_id: int."
      - "Both docstrings state that 0 is the disabled-monitoring sentinel and that valid IDs are positive."
      - "PerformanceMonitor remains a concrete, instantiable subclass — no abstract method is left unimplemented."
      - "No runtime behaviour changes. Annotations are not enforced at runtime and nothing reads __annotations__."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "None. This change has no runtime cost or benefit."
      metric: "time"

design:
  architecture: >
    The ABC is a declaration of the frame-bracketing contract, not a
    behavioural component, so the correction is confined to the two
    declarations that change-0b00759c invalidated.

    should_log_periodic is deliberately NOT added as an abstract method.
    The ABC already omits four public PerformanceMonitor methods that
    DisplayManager calls or that form part of the monitor's public surface
    — get_performance_summary, add_dirty_region, get_dirty_regions and
    clear_dirty_regions. Declaring one of the five and not the other four
    replaces the present inconsistency with a different one. Deciding
    which of the five belong in the contract is a design question for a
    separate change against design-c9d0e1f2 / design-b8c9d0e1, not a
    correction of drift introduced by change-0b00759c. DisplayManager
    binds self.performance_monitor to the concrete PerformanceMonitor
    (manager.py:113) with no interface annotation, so the
    should_log_periodic call at manager.py:451 resolves against the
    concrete class and is not affected by this omission.
  components:
    - name: "PerformanceMonitorInterface.record_frame_start"
      type: "function"
      purpose: "Declare the frame-open half of the bracketing contract."
      interface:
        inputs: []
        outputs:
          type: "int"
          description: "Positive frame ID, or 0 when monitoring is disabled."
        raises:
          - "None declared. Implementations absorb their own errors."
      logic:
        - "Change the return annotation from str to int."
        - "Expand the docstring to a Google-style Returns block naming the 0 sentinel."
        - "Body stays `pass`."
    - name: "PerformanceMonitorInterface.record_frame_end"
      type: "function"
      purpose: "Declare the frame-close half of the bracketing contract."
      interface:
        inputs:
          - name: "frame_id"
            type: "int"
            description: "Identifier returned by record_frame_start. 0 means monitoring was disabled and the call is a no-op."
        outputs:
          type: "float"
          description: "Frame duration in seconds, or 0.0."
        raises:
          - "None declared. Implementations absorb their own errors."
      logic:
        - "Change the frame_id parameter annotation from str to int."
        - "Expand the docstring to Google-style Args and Returns blocks."
        - "Body stays `pass`."
  dependencies:
    internal:
      - "PerformanceMonitor (monitor.py:27) — sole implementer; already int-typed by change-0b00759c. Unmodified here."
      - "DisplayManager._display_loop (manager.py:413, 435) — sole caller; already passes and receives ints. Unmodified here."
      - "gtach.display.performance.__init__ — re-exports PerformanceMonitorInterface; unaffected."
    external:
      - "None."

data_schema:
  entities:
    - name: "frame identifier"
      attributes:
        - name: "value"
          type: "int"
          constraints: "0 is the disabled-monitoring sentinel. Valid identifiers are >= 1 and strictly increasing within a monitoring session. Unbounded — Python ints do not wrap."
      validation:
        - "In-memory only. Nothing is persisted or transmitted, so no migration is required."

error_handling:
  strategy: >
    The ABC declares no exceptions and raises none; every abstract body is
    `pass`. Error handling belongs to the implementation and is unchanged.
  exceptions:
    - exception: "None"
      condition: "Not applicable. No executable code is added or altered."
      handling: "Not applicable."
  logging:
    level: "ERROR"
    format: "logger.error(f'...: {e}')"

testing:
  unit_tests:
    - scenario: "Import gtach.display.performance and instantiate PerformanceMonitor()."
      expected: "Instantiation succeeds — no TypeError for unimplemented abstract methods."
    - scenario: "Inspect PerformanceMonitorInterface.record_frame_start.__annotations__['return']."
      expected: "int."
    - scenario: "Inspect PerformanceMonitorInterface.record_frame_end.__annotations__['frame_id']."
      expected: "int."
    - scenario: "start_monitoring, record_frame_start, record_frame_end round trip on PerformanceMonitor."
      expected: "Unchanged from the post-change-0b00759c behaviour: IDs 1, 2, ...; a positive float duration."
    - scenario: "Enumerate PerformanceMonitorInterface.__abstractmethods__ before and after the edit."
      expected: "The same thirteen names."
  edge_cases:
    - "A future second implementer returning str: now correctly flagged by a type checker rather than silently accepted."
    - "No test or runtime path reads these annotations, so a stale .pyc or a skipped rebuild cannot produce a behavioural difference."
  validation:
    - "The string 'frame_id: str' does not appear anywhere in src/."
    - "No file under src/ other than interfaces.py differs from HEAD after the edit."

deliverable:
  format_requirements:
    - "Edit the file in place. Create no new file."
    - "Make the two edits below and change nothing else."
  files:
    - path: "src/gtach/display/performance/interfaces.py"
      content: |
        EDIT A — record_frame_start (currently interfaces.py:72-75)

        Replace:
                @abstractmethod
                def record_frame_start(self) -> str:
                    """Record start of frame rendering and return frame ID"""
                    pass

        with:
                @abstractmethod
                def record_frame_start(self) -> int:
                    """Record start of frame rendering and return frame ID.

                    Returns:
                        Positive, monotonically increasing frame ID, or 0 when
                        monitoring is disabled or an error occurs.
                    """
                    pass

        EDIT B — record_frame_end (currently interfaces.py:77-80)

        Replace:
                @abstractmethod
                def record_frame_end(self, frame_id: str) -> float:
                    """Record end of frame rendering and return frame time"""
                    pass

        with:
                @abstractmethod
                def record_frame_end(self, frame_id: int) -> float:
                    """Record end of frame rendering and return frame time.

                    Args:
                        frame_id: Identifier returned by record_frame_start. 0
                            means monitoring was disabled, and the call is a
                            no-op.

                    Returns:
                        Frame duration in seconds, or 0.0.
                    """
                    pass

        Preserve the surrounding blank lines and the existing indentation
        style of the file. Leave every other abstract method, the
        PerformanceMetrics dataclass, MetricType and the imports untouched.

success_criteria:
  - "python -m py_compile src/gtach/display/performance/interfaces.py passes."
  - "PerformanceMonitorInterface.record_frame_start is annotated -> int."
  - "PerformanceMonitorInterface.record_frame_end is annotated frame_id: int."
  - "The string 'frame_id: str' no longer appears in src/gtach/display/performance/interfaces.py."
  - "len(PerformanceMonitorInterface.__abstractmethods__) is still 13."
  - "should_log_periodic does not appear in interfaces.py."
  - "from gtach.display.performance import PerformanceMonitor; PerformanceMonitor() instantiates without TypeError."
  - "pytest tests/ passes with no new failures."
  - "git diff --name-only reports src/gtach/display/performance/interfaces.py as the only changed file under src/."

element_registry:
  source: ""
  entries:
    modules:
      - name: "interfaces"
        path: "src/gtach/display/performance/interfaces.py"
      - name: "monitor"
        path: "src/gtach/display/performance/monitor.py"
    classes:
      - name: "PerformanceMonitorInterface"
        module: "gtach.display.performance.interfaces"
      - name: "PerformanceMetrics"
        module: "gtach.display.performance.interfaces"
      - name: "MetricType"
        module: "gtach.display.performance.interfaces"
      - name: "PerformanceMonitor"
        module: "gtach.display.performance.monitor"
    functions:
      - name: "record_frame_start"
        module: "gtach.display.performance.interfaces"
        signature: "record_frame_start(self) -> int"
      - name: "record_frame_end"
        module: "gtach.display.performance.interfaces"
        signature: "record_frame_end(self, frame_id: int) -> float"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-c5dedd71-performance-interface-annotations.md

  Origin: the drift was identified during execution of prompt-0b00759c on
  2026-07-30. That prompt constrained the executor to two files, so
  interfaces.py could not be corrected in the same pass.

  Coupling: issue-c5dedd71 (T03, `defect`, severity `low`) and
  change-c5dedd71 (T02, maintenance classification `corrective`, priority
  `low`) are authored and carry UUID c5dedd71 at iteration 1, satisfying
  P03 §1.4.1 and §1.4.2 and the coupling declared in
  prompt_info.coupled_docs. Both are at status `open` / `proposed`
  respectively and require human approval before this prompt is executed.

  The Trivial Change Exemption (P03 §1.4.12) was considered and is not
  claimed. Criteria 1, 2, 4 and 5 hold, but criterion 3 fails on its face:
  the edit changes declared signatures on a public abstract base class.
  The exemption is unavailable however small the diff.

  This task is not sourced from either code review report and has no entry
  in ai/task.md §7.3 or §7.4. If it is to be tracked there, it belongs in
  §7.0 as a follow-on to 7.3.7 rather than as a new review triple.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-c5dedd71. |
| 1.1 | 2026-07-30 | Executed by Claude Code. Both edits applied; all nine success criteria met. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
