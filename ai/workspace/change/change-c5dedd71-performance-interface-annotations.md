Created: 2026 July 30

# Change: Realign PerformanceMonitorInterface Frame-ID Annotations

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-c5dedd71"
  title: "Retype record_frame_start to -> int and record_frame_end to frame_id: int on PerformanceMonitorInterface, and document the 0 sentinel"
  date: "2026-07-30"
  author: "William Watson"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-c5dedd71"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-c5dedd71"
  description: >
    Resolves issue-c5dedd71. Corrects annotation drift introduced by
    change-0b00759c, whose prompt confined the executor to monitor.py and
    manager.py. Not sourced from either code review report; no
    recommendation number applies.

scope:
  summary: >
    Bring the two abstract frame-bracketing declarations into agreement
    with their sole implementation. One file:
    src/gtach/display/performance/interfaces.py. Two edits, both
    annotation and docstring only.
  affected_components:
    - name: "PerformanceMonitorInterface.record_frame_start"
      file_path: "src/gtach/display/performance/interfaces.py"
      change_type: "modify"
    - name: "PerformanceMonitorInterface.record_frame_end"
      file_path: "src/gtach/display/performance/interfaces.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Adding should_log_periodic to the abstract base class. See rational.alternatives_considered."
    - "Adding get_performance_summary, add_dirty_region, get_dirty_regions or clear_dirty_regions to the abstract base class. Same rationale."
    - "Any change to PerformanceMonitor. monitor.py is already correct as of change-0b00759c."
    - "Any change to PerformanceMetrics, its field defaults, to_dict, or MetricType."
    - "The remaining eleven abstract method signatures."
    - "Introducing a Protocol, TypeAlias or NewType for the frame identifier."
    - "Adding mypy to CI or changing its configuration in pyproject.toml."

rational:
  problem_statement: >
    change-0b00759c replaced the UUID-string frame identifier with a
    monotonic integer in PerformanceMonitor but left
    PerformanceMonitorInterface declaring str on both bracketing methods.
    The abstract base class now states a contract its only implementation
    contradicts. A static type checker reads the two overrides as Liskov
    violations, and a reader of the interface is told the wrong type.
  proposed_solution: >
    Change the record_frame_start return annotation from str to int and
    the record_frame_end frame_id parameter annotation from str to int,
    and replace both one-line docstrings with Google-style docstrings
    naming 0 as the disabled-monitoring sentinel and stating that valid
    identifiers are positive.
  alternatives_considered:
    - option: >
        Also declare should_log_periodic as an abstract method, so the
        accessor DisplayManager calls at manager.py:451 appears in the
        contract.
      reason_rejected: >
        The ABC already omits four public PerformanceMonitor methods —
        get_performance_summary, add_dirty_region, get_dirty_regions and
        clear_dirty_regions — one of which DisplayManager also calls, at
        manager.py:1554. Declaring one of the five and not the other four
        replaces the present inconsistency with a different one. Which of
        the five belong in the contract is a design question for
        design-c9d0e1f2 and design-b8c9d0e1, not a correction of drift
        introduced by change-0b00759c. Nothing breaks meanwhile:
        DisplayManager binds the concrete class at manager.py:113 with no
        interface annotation, so the call resolves against
        PerformanceMonitor.
    - option: >
        Revert monitor.py to the string identifier so the existing
        interface declaration becomes correct again.
      reason_rejected: >
        Reverses a deliberate performance correction. Recommendation 18 of
        the display review removed the per-frame UUID allocation
        specifically to take it out of the frame path. The interface is
        the document that is wrong, not the implementation.
    - option: >
        Widen both declarations to Union[str, int] to accommodate any
        implementation.
      reason_rejected: >
        Documents an ambiguity that does not exist. There is one
        implementation and it returns int. A union would also propagate
        into every caller as an unnecessary narrowing obligation.
    - option: >
        Delete PerformanceMonitorInterface, since it has exactly one
        implementer and no dependency injection point uses it.
      reason_rejected: >
        Removes a published symbol — it is re-exported from
        gtach.display.performance.__init__ and named in __all__ — and is a
        structural decision far outside the scope of correcting two
        annotations. Recorded here as a legitimate future question.
    - option: >
        Claim the Trivial Change Exemption (P03 §1.4.12) and edit directly
        under human approval, with git history as the sole audit record.
      reason_rejected: >
        Criterion 3 fails: the edit changes declared signatures on a
        public abstract base class, which is an interface change by
        definition. Criteria 1, 2, 4 and 5 hold, but §1.4.12 requires all
        five simultaneously.
  benefits:
    - "The abstract contract, the implementation and static analysis agree."
    - "A future second implementer is told the correct type."
    - "The 0 sentinel is documented at the point where the contract is declared, not only in the implementation."
    - "Two Liskov violations are cleared from the mypy report for src/gtach/display/performance/."
  risks:
    - risk: "The edit is mistaken for a behavioural change and the interfaces.py docstrings drift from monitor.py's over time."
      mitigation: "The prompt specifies docstring text that matches the wording already landed in monitor.py by change-0b00759c."
    - risk: "The executor takes the opportunity to add should_log_periodic or the dirty-region methods to the ABC."
      mitigation: "prompt-c5dedd71 lists this as an explicit constraint and as a success criterion — should_log_periodic must not appear in interfaces.py — and pins the abstract method count at thirteen."
    - risk: "A stale .pyc masks the edit during verification."
      mitigation: "Verification asserts on __annotations__ read from a fresh interpreter, not on source text alone."

technical_details:
  current_behavior: >
    interfaces.py:73 declares record_frame_start(self) -> str and
    interfaces.py:78 declares record_frame_end(self, frame_id: str) ->
    float, each with a single-line docstring. PerformanceMonitor
    implements them as -> int and frame_id: int. The mismatch has no
    runtime expression: annotations are not enforced, nothing reads
    __annotations__, and abstract-method satisfaction is by name and
    arity, so PerformanceMonitor instantiates normally.
  proposed_behavior: >
    The two declarations read -> int and frame_id: int, with Google-style
    docstrings stating that valid identifiers are positive and
    monotonically increasing and that 0 means monitoring was disabled.
    Runtime behaviour is identical in every respect.
  implementation_approach: >
    Two in-place edits to a single file, executed by Claude Code per
    prompt-c5dedd71. Abstract method bodies remain `pass`. No import is
    added or removed — int is a builtin. No other declaration in the file
    is touched.
  code_changes:
    - component: "PerformanceMonitorInterface"
      file: "src/gtach/display/performance/interfaces.py"
      change_summary: >
        record_frame_start return annotation str -> int; record_frame_end
        frame_id parameter annotation str -> int; both one-line docstrings
        replaced with Google-style docstrings documenting the 0 sentinel.
      functions_affected:
        - "record_frame_start"
        - "record_frame_end"
      classes_affected:
        - "PerformanceMonitorInterface"
  data_changes:
    - entity: "frame identifier"
      change_type: "schema"
      details: >
        Declaration only. The represented value became int at
        change-0b00759c; this change records that fact in the abstract
        contract. In-memory and process-local — never persisted or
        transmitted — so no migration exists to perform.
  interface_changes:
    - interface: "PerformanceMonitorInterface"
      change_type: "signature"
      details: >
        record_frame_start(self) -> str becomes record_frame_start(self)
        -> int. record_frame_end(self, frame_id: str) -> float becomes
        record_frame_end(self, frame_id: int) -> float.
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "PerformanceMonitor (src/gtach/display/performance/monitor.py)"
      impact: >
        None. Sole implementer, already int-typed by change-0b00759c. This
        change makes the existing implementation conformant rather than
        requiring anything of it.
    - component: "DisplayManager._display_loop (src/gtach/display/manager.py:413, 435)"
      impact: >
        None. Sole caller, already passing and receiving ints, and bound
        to the concrete class at manager.py:113 rather than to the
        interface.
    - component: "gtach.display.performance.__init__"
      impact: "None. Re-exports the symbol unchanged; __all__ is not modified."
  external:
    - library: "None"
      version_change: "n/a"
      impact: "No external dependency is added, removed or re-versioned."
  required_changes:
    - change_ref: "change-0b00759c"
      relationship: "blocked_by"

testing_requirements:
  test_approach: >
    Static assertion on the declared annotations plus a behavioural
    no-change check. There is no new behaviour to exercise; the objective
    is to prove the contract now matches and that nothing else moved. The
    tests/ tree currently contains no test modules, so verification is by
    direct interpreter assertion.
  test_cases:
    - scenario: "Import PerformanceMonitorInterface and read record_frame_start.__annotations__['return']."
      expected_result: "int."
    - scenario: "Import PerformanceMonitorInterface and read record_frame_end.__annotations__['frame_id']."
      expected_result: "int."
    - scenario: "Instantiate PerformanceMonitor()."
      expected_result: "Succeeds. No TypeError for unimplemented abstract methods."
    - scenario: "Enumerate PerformanceMonitorInterface.__abstractmethods__."
      expected_result: "The same thirteen names as before the change."
    - scenario: "start_monitoring, then two record_frame_start / record_frame_end round trips."
      expected_result: "Frame IDs 1 then 2; positive float durations. Identical to post-change-0b00759c behaviour."
    - scenario: "Grep src/ for 'frame_id: str'."
      expected_result: "No match."
    - scenario: "Grep interfaces.py for 'should_log_periodic'."
      expected_result: "No match."
  regression_scope:
    - "Import of gtach.display.performance and its re-exported symbols."
    - "PerformanceMonitor instantiation, which is where an ABC error would surface."
    - "The DisplayManager display loop frame path, which must be unchanged."
  validation_criteria:
    - "python -m py_compile src/gtach/display/performance/interfaces.py passes."
    - "pytest tests/ passes with no new failures."
    - "git diff --name-only reports src/gtach/display/performance/interfaces.py as the only changed file under src/."
    - "The diff contains no added or removed executable statement — only annotations, docstrings and their surrounding whitespace."

implementation:
  effort_estimate: "Under one hour including verification."
  implementation_steps:
    - step: "Approve issue-c5dedd71 and change-c5dedd71."
      owner: "William Watson"
    - step: "Execute prompt-c5dedd71-performance-interface-annotations.md — edits A and B."
      owner: "Claude Code"
    - step: "Run the validation criteria and the seven test cases above."
      owner: "Claude Code"
    - step: "Commit; set change status to implemented and issue status to resolved."
      owner: "William Watson"
  rollback_procedure: >
    git revert of the single commit, or restore the two declarations to
    -> str and frame_id: str. Nothing depends on the change and no state
    is created, so rollback is unconditional and carries no data risk.
  deployment_notes: >
    No deployment consideration. The change cannot alter the behaviour of
    the running application on gtach.local and does not need to be
    observed on the device. It may be committed independently of any
    other work.

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
    - change_ref: "change-0b00759c"
      relationship: "blocked_by"
  related_issues:
    - issue_ref: "issue-c5dedd71"
      relationship: "resolves"
    - issue_ref: "issue-0b00759c"
      relationship: "related"

notes: >
  Impact analysis (P03 §1.4.5, §1.4.9): the change touches two
  declarations in one file. PerformanceMonitor is the sole implementer
  across the repository and DisplayManager the sole caller; both already
  use the integer identifier. No component requires modification as a
  consequence, no data structure changes, and there is no cascading
  effect. System integrity, performance and security are unaffected —
  Python discards annotations at runtime and the frame path executes
  identically.

  Maintenance classification (P03 §1.4.7): corrective.

  Design document updates (P03 §1.4.3, §1.4.4): none identified. No
  design document in ai/workspace/design/ specifies the frame identifier
  type. If design-c9d0e1f2 (rendering engine) or design-b8c9d0e1 (display
  manager) is later extended to describe the performance monitoring
  contract, it should reference change-0b00759c for the integer identifier
  and this change for the interface declaration.

  Deliberately excluded and recorded for a future decision: whether
  should_log_periodic, get_performance_summary, add_dirty_region,
  get_dirty_regions and clear_dirty_regions belong in
  PerformanceMonitorInterface, and whether the interface is warranted at
  all given it has one implementer and no injection point. Both are
  design questions requiring a T02 of their own.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-c5dedd71."

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
| 1.0 | 2026-07-30 | Initial change document resolving issue-c5dedd71. |

---

Copyright (c) 2026 William Watson. MIT License.
