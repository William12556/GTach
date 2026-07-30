Created: 2026 July 30

# Change: Notify `_read_ready` When the Reader Count Reaches Zero

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-1143427b"
  title: "RWLock._release_read notifies _read_ready as well as _write_ready, waking a writer blocked in the second stage of _acquire_write"
  date: "2026-07-30"
  author: "William Watson"
  status: "closed"
  priority: "critical"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-1143427b"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-1143427b"
  description: >
    Resolves issue-1143427b. Sourced from
    ai/workspace/report/core-comm-utils-code-review.md v1.0 finding §3.1
    and the correction branch of §7.0 recommendation #1. Task list
    reference ai/task.md §7.4.9.

scope:
  summary: >
    One method in src/gtach/utils/config.py. RWLock._release_read gains a
    notify_all on _read_ready alongside its existing notify_all on
    _write_ready, restoring the symmetry _release_write already has and
    removing the lost-wakeup condition that can block a writer
    indefinitely.
  affected_components:
    - name: "RWLock._release_read"
      file_path: "src/gtach/utils/config.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "RWLock._acquire_read, _acquire_write, _release_write, read_lock, write_lock and get_stats. Unmodified."
    - "Redesigning RWLock onto a single condition variable. Recorded as the primary alternative; not taken."
    - "Replacing RWLock with threading.RLock. Recorded as an alternative; exceeds recommendation #1."
    - "ConfigManager.load_config and save_config. Their locking calls are unchanged."
    - "The ConfigManager device-persistence retirement — §3.6 and §5.1, task 7.4.1. This change is independent of that disposition."
    - "The §5.2 singleton config_path warning — task 7.4.7."
    - "get_stats' momentarily stale writer count. A monitoring accessor with no callers in src/gtach."

rational:
  problem_statement: >
    _acquire_write waits on _write_ready in its first stage and on
    _read_ready in its second. _release_write notifies both condition
    variables; _release_read notifies only _write_ready. A writer that
    has passed stage one — and so already holds _writers at 1 — but finds
    _readers greater than zero in stage two waits on _read_ready, which
    the departing reader never signals. With no other writer to complete
    a full cycle, that writer waits forever. The lock guards
    ConfigManager.load_config and save_config, which are on the live
    startup path.
  proposed_solution: >
    Add a notify_all on _read_ready to the reader-count-reaches-zero
    branch of _release_read, so a departing reader signals both
    conditions that its departure can satisfy.
  alternatives_considered:
    - option: "Collapse RWLock onto a single threading.Condition guarding both counters."
      reason_rejected: >
        This is the textbook construction and would remove the
        lost-wakeup class entirely rather than patching one instance of
        it. It is the technically superior fix. It is not taken here
        because it rewrites a 75-line class on the live configuration
        path, in a release whose purpose is to be low risk and
        attributable, and because report recommendation #1 asks for the
        notification bug to be corrected. Recorded so the option is not
        lost; a follow-on cycle can take it if the class survives the
        7.4.1 retirement.
    - option: "Replace RWLock with a plain threading.RLock."
      reason_rejected: >
        Almost certainly the right long-term answer: the guarded
        operation is reading and writing a small YAML file a handful of
        times per process lifetime, so reader concurrency buys nothing,
        and an RLock cannot exhibit this class of defect at all. Rejected
        for this change because it removes a public class rather than
        correcting it, which exceeds the scope of recommendation #1 and
        would change ConfigManager's concurrency contract in the same
        release as the retirement work. Worth raising separately.
    - option: "Add a timeout to the stage-two wait so the writer eventually proceeds."
      reason_rejected: >
        Converts a deadlock into a silent correctness violation — the
        writer would proceed while readers are still active. Strictly
        worse than the defect.
    - option: "Have _acquire_write skip stage two, relying on stage one's readers check."
      reason_rejected: >
        Stage one releases _write_ready before stage two acquires
        _read_ready, and _acquire_read's check of _writers is not
        performed under the same lock that mutates it. A reader can
        therefore enter between the stages. Stage two exists to close
        that window and removing it reintroduces a genuine race.
  benefits:
    - "Removes an unbounded wait from the application's startup path."
    - "Restores the signalling symmetry between _release_read and _release_write, so the invariant is legible to a future reader."
    - "One added statement; the smallest change that makes the lock correct."
  risks:
    - risk: >
        A spurious wakeup of readers blocked in _acquire_read, which also
        waits on _read_ready.
      mitigation: >
        _acquire_read waits inside a while loop on its predicate, so a
        wakeup that does not satisfy the predicate returns to waiting.
        This is the standard condition-variable contract and is already
        relied upon by the existing _release_write notification.
    - risk: >
        Additional lock acquisition in the reader release path.
      mitigation: >
        The acquisition occurs only in the _readers == 0 branch, not on
        every release, and only when a reader is genuinely the last out.
        The guarded operation is small-file YAML I/O; the cost is not
        measurable against it.
    - risk: >
        The nested acquisition order _readers_lock then _read_ready is
        introduced where _acquire_read uses _read_ready then
        _readers_lock — an inversion.
      mitigation: >
        The same inversion already exists between _readers_lock and
        _write_ready in the current _release_read and has not deadlocked,
        because the inner acquisitions are non-blocking with respect to
        each other: neither _read_ready nor _write_ready is held while
        waiting for _readers_lock. The change document for any future
        redesign should nonetheless treat this as a reason to collapse to
        one condition variable.
    - risk: >
        The defect is rarely reachable, so a regression would be equally
        rarely observed.
      mitigation: >
        test-1143427b drives the interleaving explicitly rather than
        relying on chance, and asserts a bounded acquisition time so a
        regression fails the suite instead of hanging it.

technical_details:
  current_behavior: >
    RWLock is defined at config.py:140. _release_read (config.py:180-186)
    reads:

        def _release_read(self):
            """Release read access"""
            with self._readers_lock:
                self._readers -= 1
                if self._readers == 0:
                    with self._write_ready:
                        self._write_ready.notify_all()

    _acquire_write (config.py:188-199) waits on _write_ready in stage one
    and on _read_ready in stage two. _read_ready is notified only from
    _release_write (config.py:199-205).
  proposed_behavior: >
    _release_read notifies both condition variables when it is the last
    reader out, so a writer waiting in either stage is woken by a
    reader's departure.
  implementation_approach: >
    One edit in src/gtach/utils/config.py.

    Replace the body of _release_read's _readers == 0 branch so that
    _read_ready is notified in addition to _write_ready. Acquire and
    release each condition separately rather than nesting them, so no
    thread ever holds both at once:

        def _release_read(self):
            """Release read access"""
            with self._readers_lock:
                self._readers -= 1
                last_reader = self._readers == 0

            if last_reader:
                # Stage one of _acquire_write waits on _write_ready;
                # stage two waits on _read_ready. A departing reader can
                # satisfy either predicate, so both must be signalled.
                # Notifying only _write_ready leaves a stage-two writer
                # waiting on a condition nothing signals (core review §3.1).
                with self._write_ready:
                    self._write_ready.notify_all()
                with self._read_ready:
                    self._read_ready.notify_all()

    Note the second structural change: the counter decrement and the
    notifications are separated, so _readers_lock is released before
    either condition is acquired. The current code holds _readers_lock
    across the _write_ready acquisition. Separating them narrows the
    critical section and removes the only place where two of the three
    locks are held simultaneously.
  code_changes:
    - component: "RWLock"
      file: "src/gtach/utils/config.py"
      change_summary: >
        _release_read notifies _read_ready in addition to _write_ready
        when the reader count reaches zero, and no longer holds
        _readers_lock while doing so.
      functions_affected:
        - "_release_read"
      classes_affected:
        - "RWLock"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "ConfigManager.load_config (config.py:1175) and save_config (config.py:1320)"
      impact: "Consumers of the lock. No call site changes; the fix is internal to RWLock."
    - component: "GTachApplication (app.py:32, 75), main.py:107, OBDPairing (comm/pairing.py:42), display/setup.py:33"
      impact: "Hold ConfigManager references. Behaviour unchanged in the single-threaded case."
  external: []
  required_changes:
    - change_ref: "change-d32ccc49"
      relationship: "blocks"
    - change_ref: "change-394c3bbb"
      relationship: "related"

testing_requirements:
  test_approach: >
    Unit tests against RWLock directly on the development platform,
    driving the interleaving with explicit synchronisation rather than
    sleeps. Every acquisition assertion carries a timeout so a regression
    fails rather than hangs. Specified in test-1143427b.
  test_cases:
    - scenario: "Reproduce the reported interleaving: reader in, writer to stage two, second reader in and out."
      expected_result: "The writer acquires within the timeout. This case hangs against the pre-change implementation."
    - scenario: "Single writer, no readers."
      expected_result: "Acquires and releases immediately."
    - scenario: "Two concurrent readers."
      expected_result: "Both hold the read lock simultaneously; reader concurrency is preserved."
    - scenario: "Writer held while a reader attempts acquisition."
      expected_result: "The reader blocks until the writer releases; exclusivity preserved."
    - scenario: "Reader held while a writer attempts acquisition."
      expected_result: "The writer blocks until the reader releases, then acquires."
    - scenario: "Several readers release in sequence, only the last reaching zero."
      expected_result: "Notification occurs once, on the last release."
    - scenario: "Repeated acquire/release cycles across mixed reader and writer threads."
      expected_result: "No thread blocks beyond the timeout; counters return to zero."
    - scenario: "ConfigManager.load_config and save_config in a single-threaded sequence."
      expected_result: "Behaviour identical to before the change."
  regression_scope:
    - "tests/utils/ — the full utils suite once tests/ is populated per ai/task.md §8.2."
    - "Application startup on gtach.local: configuration loads without delay."
    - "Settings save from the OPTIONS screen completes."
  validation_criteria:
    - "python -m py_compile src/gtach/utils/config.py passes."
    - "pytest tests/ passes with no new failures."
    - "_release_read contains notify_all calls on both _write_ready and _read_ready."
    - "No test exceeds its acquisition timeout."
    - "No other method of RWLock is modified."

implementation:
  implementation_steps:
    - step: "Edit RWLock._release_read: compute last_reader under _readers_lock, release it, then notify _write_ready and _read_ready in turn."
      owner: "Claude Code"
    - step: "Compile check and run the existing test suite."
      owner: "Claude Code"
    - step: "Generate tests/utils/test_rwlock.py from test-1143427b and confirm the reproduction case fails against the pre-change implementation."
      owner: "Claude Code"
    - step: "Verify application startup and a settings save on gtach.local as part of the v0.3.0 deployment."
      owner: "William Watson"
  rollback_procedure: >
    Single method, single commit. git revert restores the previous
    behaviour. No data, configuration or interface migration is involved.
  deployment_notes: >
    No configuration change and no observable behaviour change in normal
    operation. The change removes a failure mode rather than altering a
    function. Ships in v0.3.0 per ai/task.md §8.3.

verification:
  implemented_date: "2026-07-30"
  implemented_by: "Claude Code, per prompt-1143427b"
  verification_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Development platform only (macOS, Python 3.11). On-target verification
    is outstanding and ships with v0.3.0.

    The single edit was applied as specified. All five validation_criteria
    that do not require gtach.local hold, with one qualification recorded
    below.

    python -m py_compile src/gtach/utils/config.py passes.

    _release_read contains notify_all calls on both _write_ready and
    _read_ready, confirmed by walking the method's AST rather than by
    string matching: the method takes exactly three context managers —
    _readers_lock, _write_ready, _read_ready, one each — the _readers_lock
    block encloses no condition acquisition, the two condition blocks are
    sequential siblings in the body of the `if last_reader:` branch, and
    self._readers is read exactly once, into the local.

    No other method of RWLock is modified. An AST comparison of the
    pre- and post-change file reports _release_read as the only differing
    method, with the method set unchanged; ConfigManager's thirty-two
    methods are identical. git diff --stat confirms one file, 22
    insertions and 5 deletions.

    Twenty-five assertions were executed against the real RWLock, loaded
    from the working tree with yaml, pyserial, pygame and psutil stubbed.
    All pass. They cover the eight test_cases above except the last, and
    add the lock-discipline checks the coupled T05 document asks for.

    The evidence that the suite discriminates: run unchanged against the
    pre-change file it fails seven and passes eighteen. The seven failures
    are the deadlock reproduction, the notification-symmetry assertion,
    and five structural assertions. The eighteen that pass — reader
    concurrency, writer exclusivity in both directions, blocking and
    release ordering, notification only on the final reader release, the
    mixed reader/writer cycles, the spurious-wakeup and queued-writer edge
    cases, and the counters returning to zero throughout — pass
    identically before and after, which is the evidence that the edit
    removed a failure mode without altering a function.

    The deadlock reproduction required care. A writer only waits on
    _read_ready if a reader enters through the window between the two
    stages of _acquire_write, and that window is too narrow to hit by
    sleeping. A first attempt blocked the writer in stage one instead,
    which the pre-change code wakes correctly — it passed against both
    files and proved nothing. The reader's entry was therefore forced to
    occur at the stage-one to stage-two boundary by hooking the exit of
    the _write_ready block. The entry is real, incrementing _readers under
    _readers_lock as _acquire_read does; only its timing is controlled.
    That test is retained alongside the stage-one case, which is kept as a
    check that the ordinary path was not disturbed.

    Qualification on test case eight, ConfigManager.load_config and
    save_config in a single-threaded sequence: neither method was
    executed. Both are unmodified by AST comparison, and the coupled T05
    document places ConfigManager beyond a smoke check out of scope.
    Executing them writes a YAML file to the developer's filesystem, which
    is disproportionate to what it would establish given the methods are
    provably unchanged.

    pytest tests/ collected 0 items — the tests/ tree has held only
    README.md since commit 57ebbe6. The "no new failures" criterion is
    therefore vacuous rather than met, and the regression_scope entry
    naming tests/utils/ could not be exercised. It already anticipates
    this, being conditioned on tests/ being populated per ai/task.md §8.2.

    Only src/gtach/utils/config.py was modified.

    Deviation from the implementation steps. Step 3 calls for
    tests/utils/test_rwlock.py to be generated from test-1143427b and for
    the reproduction case to be confirmed against the pre-change
    implementation. The second half was done; the first was not.
    prompt-1143427b constrains the executor to src/gtach/utils/config.py
    and states that no other file is to be modified, and the prime
    directive forbids creating a file the T04 task does not request. The
    verification above therefore used an ephemeral script, which satisfies
    the substance of the step but leaves no persisted test module.
    test-1143427b remains at status planned and needs its own T04 prompt
    to be generated into tests/. This is a scope conflict between the
    change document and its own prompt, not a defect in the fix.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-394c3bbb"
      relationship: "related"
    - change_ref: "change-d32ccc49"
      relationship: "blocks"
  related_issues:
    - issue_ref: "issue-1143427b"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-1143427b."
  - version: "1.1"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status proposed -> implemented. Recorded implementation date, executor, verification date and development-platform test results."
      - "Recorded that the suite discriminates: 25/25 after the change, 18/25 against the pre-change file, the deadlock reproduction among the failures."
      - "Recorded the qualification on test case eight — ConfigManager.load_config and save_config were not executed, both being unmodified by AST comparison."
      - "Recorded that pytest collected 0 items, so the regression_scope entry for tests/utils/ could not be exercised."
      - "Recorded a deviation: implementation step 3 was not executed, because prompt-1143427b permits no file other than src/gtach/utils/config.py to be modified."
  - version: "1.2"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status implemented -> closed."
      - "Implementation steps 1 and 2 complete; step 3 partially complete and reassigned to its own cycle; step 4 open by design and owned by William Watson for the v0.3.0 deployment."
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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-1143427b. |
| 1.1 | 2026-07-30 | Status proposed → implemented; development-platform test results recorded, including the pre-change discrimination run; deviation on implementation step 3 recorded. |
| 1.2 | 2026-07-30 | Status implemented → closed. Moved to ai/workspace/change/closed/ per P00 §1.1.14.4. |

---

Copyright (c) 2026 William Watson. MIT License.
