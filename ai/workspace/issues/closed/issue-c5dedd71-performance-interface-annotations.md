Created: 2026 July 30

# Issue: PerformanceMonitorInterface Declares a Frame-ID Type Its Only Implementation No Longer Uses

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-c5dedd71"
  title: "record_frame_start and record_frame_end are annotated str on PerformanceMonitorInterface but int on PerformanceMonitor, so the abstract base class states a contract the implementation contradicts"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "closed"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-c5dedd71"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Identified during execution of prompt-0b00759c on 2026-07-30, in the
    post-implementation review of that change. Not sourced from either
    code review report and has no recommendation number. The defect was
    introduced by change-0b00759c, whose prompt constrained the executor
    to src/gtach/display/performance/monitor.py and
    src/gtach/display/manager.py, so interfaces.py could not be corrected
    in the same pass.

affected_scope:
  components:
    - name: "PerformanceMonitorInterface.record_frame_start"
      file_path: "src/gtach/display/performance/interfaces.py"
    - name: "PerformanceMonitorInterface.record_frame_end"
      file_path: "src/gtach/display/performance/interfaces.py"
  designs: []
  version: "0.2.64"

reproduction:
  prerequisites: >
    Working tree at or after the implementation of change-0b00759c. No
    running application is required — the defect is static and visible by
    inspection.
  steps:
    - "Read src/gtach/display/performance/interfaces.py:73 — def record_frame_start(self) -> str."
    - "Read src/gtach/display/performance/interfaces.py:78 — def record_frame_end(self, frame_id: str) -> float."
    - "Read src/gtach/display/performance/monitor.py — the same two methods on PerformanceMonitor, the sole subclass, are annotated -> int and frame_id: int."
    - "Run a static type checker over src/gtach/display/performance/ (pyproject.toml configures mypy at python_version 3.9)."
  frequency: "always"
  reproducibility_conditions: >
    Static and unconditional. Present in every environment and on every
    execution path, including paths never taken at runtime.
  preconditions: "None."
  test_data: ""
  error_output: >
    No runtime error. A type checker reports a Liskov substitution
    violation on both overrides — return type "int" incompatible with
    supertype "str", and argument 1 incompatible with supertype's "str".

behavior:
  expected: >
    The abstract base class declares the frame identifier as the type its
    implementations actually use, so the declared contract, the
    implementation and any static analysis agree.
  actual: >
    change-0b00759c replaced the 8-character UUID-prefix frame identifier
    with a monotonic integer in PerformanceMonitor, retyping
    record_frame_start to -> int, record_frame_end to frame_id: int and
    _active_frames to Dict[int, float], and changing the
    disabled-monitoring sentinel from "" to 0. The corresponding
    declarations on PerformanceMonitorInterface were left at str. The ABC
    now documents a string identifier that no code produces or consumes.
  impact: >
    No functional impact. Python does not enforce annotations at runtime,
    nothing in the codebase reads __annotations__, and PerformanceMonitor
    remains instantiable because the method names and arities are
    unchanged. The cost is to correctness of documentation and to static
    analysis: the two overrides are reported as Liskov violations, and a
    future second implementer reading the interface would be told to
    return a string. Severity is low for this reason and for no other.
  workaround: >
    None required. The defect has no runtime expression. Readers of
    interfaces.py must consult monitor.py to learn the real type.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W; macOS Apple Silicon for development"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    prompt-0b00759c enumerated the type annotations requiring update —
    "record_frame_start, record_frame_end, _active_frames" — but located
    all three in monitor.py and constrained the executor to two files.
    The abstract declarations of the first two, which live in a third
    file, were not enumerated and were therefore out of the executor's
    permitted scope. The omission is in the prompt's scoping, not in its
    execution.
  technical_notes: >
    PerformanceMonitor is the sole implementer of
    PerformanceMonitorInterface across the repository, so the correction
    cannot break another subclass.

    DisplayManager binds self.performance_monitor to the concrete
    PerformanceMonitor at manager.py:113 with no interface annotation.
    Call sites therefore resolve against the concrete class, which is
    already correct; this is why the defect produces no error at
    manager.py:413 or manager.py:435.

    A related but distinct gap is recorded here and deliberately excluded
    from the resolution: the ABC declares thirteen abstract methods and
    omits four public PerformanceMonitor methods — get_performance_summary
    (called by DisplayManager.get_status at manager.py:1554),
    add_dirty_region, get_dirty_regions and clear_dirty_regions — as well
    as should_log_periodic, added by change-0b00759c. Whether these belong
    in the contract is a design question, not annotation drift.
  related_issues:
    - issue_ref: "issue-0b00759c"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Retype the two abstract declarations to int and expand both docstrings
    to Google style, documenting 0 as the disabled-monitoring sentinel.
    Annotations and docstrings only; no abstract method is added or
    removed. See change-c5dedd71.
  change_ref: "change-c5dedd71"
  resolved_date: "2026-07-30"
  resolved_by: "Claude Code, per prompt-c5dedd71"
  fix_description: >
    Both edits applied as specified, to
    src/gtach/display/performance/interfaces.py only.

    record_frame_start is now declared -> int and record_frame_end
    frame_id: int. The record_frame_end return annotation remains float.
    Both one-line docstrings were replaced with Google-style docstrings:
    record_frame_start documents a positive, monotonically increasing
    identifier with 0 returned when monitoring is disabled or an error
    occurs; record_frame_end documents frame_id, with 0 meaning monitoring
    was disabled and the call a no-op, and a return of the frame duration
    in seconds or 0.0.

    Abstract bodies remain `pass`. No import was added or removed. No
    abstract method was added or removed, and should_log_periodic was not
    introduced, per the constraint carried from change-c5dedd71.

verification:
  verified_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    All seven test cases from change-c5dedd71 pass, and all nine success
    criteria from prompt-c5dedd71 are met.

    record_frame_start.__annotations__['return'] is int.
    record_frame_end.__annotations__['frame_id'] is int, and its 'return'
    is still float. PerformanceMonitor() instantiates with no TypeError.
    __abstractmethods__ still holds thirteen names. A start_monitoring /
    record_frame_start / record_frame_end round trip returned IDs 1 then 2
    with positive float durations, matching post-change-0b00759c
    behaviour exactly. 'frame_id: str' does not appear anywhere in src/.
    'should_log_periodic' does not appear in interfaces.py.
    python -m py_compile passes on the edited file.

    The diff adds and removes no executable statement: it comprises the
    two annotations, the two docstrings, and the normalisation of trailing
    whitespace on one blank line between the methods.

    interfaces.py is the only file changed under src/. pytest tests/
    collected 0 items, as it has since commit 57ebbe6; the direct
    assertions above stand in its place.
  closure_notes: >
    Closed 2026-07-30 on human instruction, per P00 §1.1.14.4.

    Closure criteria for an issue (§1.1.14.3) are met in full: resolved
    and verified, with change-c5dedd71 implemented and tested. Unlike
    issue-0b00759c, this issue carried no on-target dependency — the
    defect was static and every verification step is executable on the
    development platform, so nothing is deferred to gtach.local.

    Two questions were deliberately excluded from the resolution and
    survive closure, recorded in change-c5dedd71 for a future T02: whether
    should_log_periodic, get_performance_summary, add_dirty_region,
    get_dirty_regions and clear_dirty_regions belong in
    PerformanceMonitorInterface; and whether the interface is warranted at
    all, given one implementer and no injection point. Neither is a defect
    and neither blocks this closure.

prevention:
  preventive_measures: >
    When a T04 prompt retypes a method that overrides an abstract
    declaration, the file holding that declaration belongs in the prompt's
    permitted file set. Enumerating the annotations to update is not
    sufficient if the enumeration is scoped to one file and the type is
    declared in another.
  process_improvements: >
    Post-implementation review of a change that alters a signature should
    grep the repository for the changed symbol before the change is
    reported complete. That step found this defect and cost nothing.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/performance/interfaces.py passes."
    - "The string 'frame_id: str' does not appear anywhere in src/."
    - "PerformanceMonitorInterface.record_frame_start.__annotations__['return'] is int."
    - "PerformanceMonitorInterface.record_frame_end.__annotations__['frame_id'] is int."
    - "len(PerformanceMonitorInterface.__abstractmethods__) is still 13."
    - "from gtach.display.performance import PerformanceMonitor; PerformanceMonitor() instantiates without TypeError."
    - "A record_frame_start / record_frame_end round trip on PerformanceMonitor behaves exactly as it did before the change."
    - "git diff --name-only reports interfaces.py as the only changed file under src/."
  verification_results: >
    All eight steps PASS, executed 2026-07-30 on macOS with Python
    3.11.14.

    PASS — python -m py_compile on interfaces.py.
    PASS — 'frame_id: str' absent from src/ (recursive grep, no match).
    PASS — record_frame_start.__annotations__['return'] is int.
    PASS — record_frame_end.__annotations__['frame_id'] is int.
    PASS — len(__abstractmethods__) is 13, unchanged.
    PASS — PerformanceMonitor() instantiates with no TypeError.
    PASS — round trip returns IDs 1 then 2 with positive float durations,
    identical to the behaviour before this change.
    PASS — interfaces.py is the only file changed under src/.

traceability:
  design_refs: []
  change_refs:
    - "change-c5dedd71"
  test_refs: []

notes: >
  Not a code review triple. This issue has no entry in ai/task.md §7.3 or
  §7.4 and no recommendation number in either review report, because it
  arose from the implementation of task 7.3.7 rather than from the reviews
  themselves. If it is to be tracked in ai/task.md it belongs in §7.0 as a
  follow-on to 7.3.7.

  The Trivial Change Exemption (P03 §1.4.12) was considered and is not
  claimed. Criteria 1, 2, 4 and 5 hold — two adjacent declarations, a net
  delta well under twenty lines, no design decision, and human approval
  available. Criterion 3 fails on its face: the edit changes declared
  signatures on a public abstract base class. The exemption is unavailable
  however small the diff, so the full T03 / T02 / T04 triple applies.

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
      - "Initial issue document from post-implementation review of change-0b00759c."
  - version: "1.1"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Status open -> closed. change-c5dedd71 implemented and verified via prompt-c5dedd71."
      - "Recorded resolution, verification and all eight verification steps as PASS."
      - "Closed per P00 §1.1.14.4; document moved to ai/workspace/issues/closed/ at final iteration 1."

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
| 1.0 | 2026-07-30 | Initial issue document from post-implementation review of change-0b00759c. |
| 1.1 | 2026-07-30 | Status open → closed; resolution and verification recorded, all eight steps PASS; closed per P00 §1.1.14.4. |

---

Copyright (c) 2026 William Watson. MIT License.
