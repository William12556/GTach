Created: 2026 July 30

# Test: RWLock Notification Defect

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-1143427b"
  title: "Unit tests for RWLock notification symmetry, reader concurrency and writer exclusivity"
  date: "2026-07-30"
  author: "William Watson"
  status: "planned"
  type: "unit"
  priority: "critical"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-1143427b"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "RWLock — _release_read, _acquire_write, _acquire_read, _release_write"
  design_refs: []
  change_refs:
    - "change-1143427b"
  requirement_refs:
    - "core-comm-utils-code-review.md §3.1"
    - "core-comm-utils-code-review.md §7.0 recommendation #1, correction branch"

scope:
  description: >
    Verifies that a departing reader wakes a writer blocked in either
    stage of _acquire_write, and that the correction preserves the lock's
    two defining properties: readers may proceed concurrently, and a
    writer excludes everyone. The defect is a lost wakeup, so the tests
    drive the interleaving explicitly rather than relying on chance.
  test_objectives:
    - "Reproduce the reported interleaving and confirm the writer completes."
    - "Confirm the reproduction fails against the pre-change implementation, so the test discriminates."
    - "Confirm both conditions are notified only when the last reader departs."
    - "Confirm reader concurrency is not lost to the fix."
    - "Confirm writer exclusivity is preserved."
    - "Confirm no thread holds two of the lock's three primitives simultaneously."
  in_scope:
    - "src/gtach/utils/config.py — the RWLock class"
  out_scope:
    - "ConfigManager.load_config and save_config beyond a single-threaded smoke check. Their locking calls are unchanged"
    - "get_stats' momentarily stale writer count — a monitoring accessor with no callers in src/gtach"
    - "The single-condition redesign and the threading.RLock replacement — recorded alternatives, not taken"
    - "The ConfigManager device-persistence retirement — task 7.4.1"
    - "Fairness or starvation properties. The lock's docstring claims reader-starvation prevention; that claim is untested and unchanged by this correction"
  dependencies:
    - "threading and threading.Barrier / Event for deterministic interleaving"
    - "No pygame, no psutil, no filesystem, no hardware"

test_environment:
  python_version: "3.9+ (development platform); 3.11 on target"
  os: "macOS Apple Silicon (development); Debian Linux Raspberry Pi OS (target)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
    - name: "threading"
      version: "stdlib"
    - name: "unittest.mock"
      version: "stdlib"
  test_framework: "pytest"
  test_data_location: >
    Inline. Every acquisition assertion uses a bounded wait — Event.wait
    or Thread.join with a timeout, never an unbounded acquire — so a
    regression fails the suite rather than hanging it. Suggested bound:
    2.0 s, three orders of magnitude above the expected acquisition time.

test_cases:
  - case_id: "TC-001"
    description: "The reported interleaving — a reader entering between the writer's two stages"
    category: "negative"
    preconditions:
      - "A fresh RWLock"
    test_steps:
      - step: "1"
        action: "Thread A acquires the read lock, so _readers is 1"
      - step: "2"
        action: "Thread B calls _acquire_write and blocks in stage one on _write_ready"
      - step: "3"
        action: "Inject thread C's read acquisition so it lands between B's stage one and stage two, by patching _acquire_write's inter-stage point or by driving the counters directly"
      - step: "4"
        action: "Thread A releases; B advances to stage two and observes _readers > 0 from C"
      - step: "5"
        action: "Thread C releases"
      - step: "6"
        action: "Join B with a 2.0 s timeout"
    inputs:
      - parameter: "interleaving"
        value: "A in, B stage one, C in, A out, B stage two, C out"
        type: "sequence"
    expected_outputs:
      - field: "B completes _acquire_write"
        expected_value: "Within the timeout"
        validation: "Thread.join(timeout=2.0) followed by assert not B.is_alive()"
      - field: "pre-change behaviour"
        expected_value: "B still blocked at timeout"
        validation: "Run once against the unpatched method to confirm the test discriminates; record the outcome in the T06 result"
    postconditions:
      - "_readers is 0 and _writers is 1 until B releases"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "B acquires within the timeout"
    defects: []

  - case_id: "TC-002"
    description: "The last reader notifies both conditions"
    category: "positive"
    preconditions:
      - "A fresh RWLock with both conditions instrumented to count notify_all calls"
    test_steps:
      - step: "1"
        action: "Acquire and release a single read lock"
      - step: "2"
        action: "Read the two notification counts"
    inputs:
      - parameter: "readers"
        value: "1"
        type: "int"
    expected_outputs:
      - field: "_write_ready.notify_all count"
        expected_value: "1"
        validation: "Existing behaviour retained"
      - field: "_read_ready.notify_all count"
        expected_value: "1"
        validation: "The added notification. This is the fix"
    postconditions:
      - "Symmetry with _release_write, which already notifies both"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Both counts are 1"
    defects: []

  - case_id: "TC-003"
    description: "A non-final reader release notifies nothing"
    category: "boundary"
    preconditions:
      - "Notification counters instrumented"
    test_steps:
      - step: "1"
        action: "Acquire three read locks"
      - step: "2"
        action: "Release the first two, checking the counters after each"
      - step: "3"
        action: "Release the third"
    inputs:
      - parameter: "readers"
        value: "3"
        type: "int"
    expected_outputs:
      - field: "counts after the first two releases"
        expected_value: "0 and 0"
        validation: "The notification is confined to the _readers == 0 branch"
      - field: "counts after the third release"
        expected_value: "1 and 1"
        validation: "Fires once, on the last reader out"
    postconditions:
      - "No per-release cost is added for non-final readers"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Notification occurs exactly once, on the final release"
    defects: []

  - case_id: "TC-004"
    description: "Readers proceed concurrently"
    category: "positive"
    preconditions:
      - "A fresh RWLock"
    test_steps:
      - step: "1"
        action: "Start two threads, each acquiring the read lock and signalling an Event before releasing"
      - step: "2"
        action: "Assert both Events are set before either thread releases, using a Barrier inside the read lock"
    inputs:
      - parameter: "concurrent readers"
        value: "2"
        type: "int"
    expected_outputs:
      - field: "both readers inside the lock simultaneously"
        expected_value: "True"
        validation: "A two-party Barrier inside the read lock completes within the timeout. It would deadlock if reads were serialised"
    postconditions:
      - "The fix does not turn the lock into a mutex"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Barrier completes within the timeout"
    defects: []

  - case_id: "TC-005"
    description: "A writer excludes readers"
    category: "positive"
    preconditions:
      - "A fresh RWLock"
    test_steps:
      - step: "1"
        action: "Thread A takes the write lock and holds it, signalling an Event"
      - step: "2"
        action: "Thread B attempts the read lock"
      - step: "3"
        action: "Assert B has not acquired after a short interval, then release A and join B"
    inputs:
      - parameter: "hold duration"
        value: "0.2"
        type: "float"
    expected_outputs:
      - field: "B acquired while A held the lock"
        expected_value: "False"
        validation: "B's acquisition Event is unset at the check"
      - field: "B acquired after A released"
        expected_value: "True within the timeout"
        validation: "join(timeout=2.0)"
    postconditions:
      - "Writer exclusivity preserved"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "B blocked during, acquires after"
    defects: []

  - case_id: "TC-006"
    description: "A reader excludes a writer until it releases"
    category: "positive"
    preconditions:
      - "A fresh RWLock"
    test_steps:
      - step: "1"
        action: "Thread A takes the read lock and holds it"
      - step: "2"
        action: "Thread B attempts the write lock"
      - step: "3"
        action: "Assert B has not acquired, then release A and join B"
    inputs:
      - parameter: "hold duration"
        value: "0.2"
        type: "float"
    expected_outputs:
      - field: "B acquired while A held the read lock"
        expected_value: "False"
        validation: "B's acquisition Event is unset at the check"
      - field: "B acquired after A released"
        expected_value: "True within the timeout"
        validation: "This is the simple case of the fix — one reader, one writer, no interleaving"
    postconditions:
      - "The common path is unaffected by the change"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "B blocked during, acquires after"
    defects: []

  - case_id: "TC-007"
    description: "Uncontended acquisition is immediate"
    category: "positive"
    preconditions:
      - "A fresh RWLock"
    test_steps:
      - step: "1"
        action: "Acquire and release the write lock with no readers present"
      - step: "2"
        action: "Acquire and release the read lock with no writers present"
    inputs: []
    expected_outputs:
      - field: "both acquisitions"
        expected_value: "Complete without blocking"
        validation: "Wall time well under the timeout"
      - field: "counters after"
        expected_value: "_readers 0, _writers 0"
        validation: "get_stats returns both zero"
    postconditions:
      - "No leak in the common uncontended path"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Both complete and counters return to zero"
    defects: []

  - case_id: "TC-008"
    description: "Mixed reader and writer load over repeated cycles"
    category: "regression"
    preconditions:
      - "A fresh RWLock"
    test_steps:
      - step: "1"
        action: "Start four reader threads and two writer threads, each performing 50 acquire/release cycles against a shared counter"
      - step: "2"
        action: "Join all with a 2.0 s timeout each"
      - step: "3"
        action: "Assert the shared counter equals the expected total and the lock counters are zero"
    inputs:
      - parameter: "threads"
        value: "4 readers, 2 writers"
        type: "int"
      - parameter: "cycles each"
        value: "50"
        type: "int"
    expected_outputs:
      - field: "all threads joined"
        expected_value: "True"
        validation: "No thread alive after join; a lost wakeup would leave one blocked"
      - field: "shared counter"
        expected_value: "The expected total, with no lost increments"
        validation: "Writers hold exclusive access, so increments cannot race"
      - field: "get_stats"
        expected_value: "active_readers 0, active_writers 0"
        validation: "Balanced acquire/release across the run"
    postconditions:
      - "Exercises the interleaving stochastically as well as deterministically"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "All threads complete; counter correct; lock drained"
    defects: []

  - case_id: "TC-009"
    description: "_readers_lock is not held while a condition is acquired"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Parse src/gtach/utils/config.py with the ast module"
      - step: "2"
        action: "Locate _release_read and walk its With nodes"
      - step: "3"
        action: "Assert no With node whose context is _read_ready or _write_ready is nested inside one whose context is _readers_lock"
    inputs:
      - parameter: "source file"
        value: "src/gtach/utils/config.py"
        type: "path"
    expected_outputs:
      - field: "nested condition acquisitions inside _readers_lock"
        expected_value: "0"
        validation: "Static assertion. The pre-change method nested _write_ready inside _readers_lock"
      - field: "sequential condition blocks"
        expected_value: "2, both at the same nesting depth"
        validation: "_write_ready then _read_ready, neither inside the other"
    postconditions:
      - "Guards the second correction in the change, not only the first"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "No nesting and two sibling condition blocks"
    defects: []

  - case_id: "TC-010"
    description: "No other RWLock method changed"
    category: "regression"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Assert RWLock still defines read_lock, write_lock, _acquire_read, _acquire_write, _release_read, _release_write and get_stats"
      - step: "2"
        action: "Assert _acquire_write still contains two sequential With blocks, on _write_ready then _read_ready"
    inputs: []
    expected_outputs:
      - field: "method set"
        expected_value: "Unchanged"
        validation: "dir() comparison against the expected names"
      - field: "_acquire_write structure"
        expected_value: "Two stages retained"
        validation: "Stage two closes a genuine reader-entry window and must not have been removed"
    postconditions:
      - "The change is confined to _release_read as specified"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Method set and _acquire_write structure intact"
    defects: []

  - case_id: "TC-011"
    description: "ConfigManager load and save are unaffected in the single-threaded case"
    category: "regression"
    preconditions:
      - "A temporary configuration file via tempfile"
    test_steps:
      - step: "1"
        action: "Construct a ConfigManager against the temporary path"
      - step: "2"
        action: "Call load_config, mutate a field, call save_config, then load_config again"
    inputs:
      - parameter: "config path"
        value: "tempfile-backed"
        type: "path"
    expected_outputs:
      - field: "round trip"
        expected_value: "The mutated field survives the save and reload"
        validation: "Equality on the mutated field"
      - field: "wall time"
        expected_value: "No blocking"
        validation: "Completes well within the timeout"
    postconditions:
      - "The consumer of the lock behaves as before"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Round trip succeeds without blocking"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "core review §3.1 — RWLock notification bug"
      test_cases:
        - "TC-001"
        - "TC-002"
        - "TC-003"
        - "TC-009"
    - requirement_ref: "Lock properties preserved by the correction"
      test_cases:
        - "TC-004"
        - "TC-005"
        - "TC-006"
        - "TC-007"
        - "TC-008"
        - "TC-010"
        - "TC-011"
  code_coverage:
    target: "100% of _release_read branches; both stages of _acquire_write exercised"
    achieved: ""
  untested_areas:
    - component: "Reader-starvation prevention"
      reason: "The class docstring claims it; the claim predates this change and is neither verified nor altered by it. Testing fairness requires a scheduling model beyond the scope of a defect correction"
    - component: "get_stats consistency"
      reason: "Reads _writers under _readers_lock rather than _write_ready, so the writer count can be momentarily stale. A monitoring accessor with no callers in src/gtach; recorded in issue-1143427b and left out of scope"
    - component: "Behaviour after the 7.4.1 retirement"
      reason: "If RWLock's remaining justification is reduced by the retirement, the threading.RLock replacement should be raised as its own cycle. Out of scope here"

test_execution_summary:
  total_cases: 11
  passed: 0
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: ""
  execution_time: ""
  test_cycle: "Initial"

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues: []

verification:
  verified_date: ""
  verified_by: ""
  verification_notes: ""
  sign_off: ""

traceability:
  requirements:
    - requirement_ref: "core-comm-utils-code-review.md §7.0 #1, correction branch"
      test_cases:
        - "TC-001"
        - "TC-002"
  designs: []
  changes:
    - change_ref: "change-1143427b"
      test_cases:
        - "TC-001"
        - "TC-002"
        - "TC-003"
        - "TC-004"
        - "TC-005"
        - "TC-006"
        - "TC-007"
        - "TC-008"
        - "TC-009"
        - "TC-010"
        - "TC-011"

notes: >
  Generated pytest file: tests/utils/test_rwlock.py, per P06 §1.7.3.

  Every acquisition assertion must be bounded. A lost-wakeup defect
  manifests as a thread that never returns, so an unbounded acquire in a
  test converts a regression into a hung suite with no diagnostic. Use
  Thread.join(timeout=...) and Event.wait(timeout=...) throughout, and
  assert on is_set or is_alive rather than relying on the call returning.

  TC-001 is the discriminating case: it must fail against the pre-change
  implementation. Run it once against the unpatched method before
  applying the change and record the outcome in the T06 result. A
  reproduction that passes both before and after proves nothing about the
  fix.

  TC-001 step 3 is the difficult part. The window between stage one and
  stage two of _acquire_write is not directly addressable from outside
  the class. Two workable approaches: patch _acquire_write with a variant
  that signals an Event between the stages, or drive _readers and
  _writers directly through the private attributes to construct the state
  the interleaving produces. The first is closer to the real execution
  path; the second is deterministic. Prefer the first, and fall back to
  the second if the timing proves unreliable.

  TC-009 asserts the second of the change's two corrections — that
  _readers_lock is released before either condition is taken. It is a
  static assertion because the property is structural rather than
  observable at runtime.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial test document for change-1143427b, per ai/task.md §8.2."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t05_test"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial test document for change-1143427b, per ai/task.md §8.2. |

---

Copyright (c) 2026 William Watson. MIT License.
