Created: 2026 July 30

# Issue: RWLock Writer Can Wait Forever — `_release_read` Never Notifies `_read_ready`

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-1143427b"
  title: "RWLock._release_read notifies only _write_ready, so a writer waiting in the second stage of _acquire_write is never woken — deadlock on the live ConfigManager path"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "open"
  severity: "critical"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-1143427b"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/core-comm-utils-code-review.md v1.0, 2026-07-30.
    Finding §3.1 and the correction branch of §7.0 recommendation #1.
    Task list reference: ai/task.md §7.4.9. Separated from 7.4.1 by the
    §7.4.8 finding that retiring the device-persistence path does not
    close this defect.

affected_scope:
  components:
    - name: "RWLock._acquire_write"
      file_path: "src/gtach/utils/config.py"
    - name: "RWLock._release_read"
      file_path: "src/gtach/utils/config.py"
    - name: "ConfigManager.load_config"
      file_path: "src/gtach/utils/config.py"
    - name: "ConfigManager.save_config"
      file_path: "src/gtach/utils/config.py"
  designs: []
  version: "0.2.64"

reproduction:
  prerequisites: >
    Concurrent access to a single ConfigManager instance: one thread in
    load_config or save_config taking the write lock while another holds
    a read lock. ConfigManager is a process-wide singleton, and
    references are held by GTachApplication (app.py:32), OBDPairing
    (comm/pairing.py:42) and the setup subsystem (display/setup.py:33).
  steps:
    - "Construct a RWLock."
    - "Thread A: call _acquire_read so _readers becomes 1."
    - "Thread B: call _acquire_write. Stage one waits until _readers is 0, so B blocks on _write_ready."
    - "Thread A: call _release_read. _readers drops to 0 and _write_ready is notified, so B proceeds, sets _writers to 1, and enters stage two."
    - "Thread C: call _acquire_read. Its check of _writers > 0 is racy — if C passes the check before B increments _writers, C increments _readers under _readers_lock."
    - "Thread B: stage two now observes _readers > 0 and waits on _read_ready."
    - "Thread C: call _release_read. It notifies _write_ready only."
    - "Thread B remains blocked on _read_ready with no writer left to call _release_write."
  frequency: "intermittent"
  reproducibility_conditions: >
    Requires a reader to enter between the writer's two stages. In the
    running application, configuration I/O is effectively single-threaded
    at startup, so the window is rarely hit. The defect is latent, not
    absent — the code path is exercised on every start.
  preconditions: >
    ConfigManager.load_config is called from app.py:75 and main.py:107.
    save_config is reachable from the setup and options flows.
  test_data: ""
  error_output: >
    None. No exception is raised. The symptom is a thread that never
    returns from load_config or save_config.

behavior:
  expected: >
    A writer waiting for readers to drain is woken when the last reader
    releases. No thread waits on a condition variable that nothing
    signals.
  actual: >
    _acquire_write (config.py:188-199) has two stages:

        with self._write_ready:
            while self._writers > 0 or self._readers > 0:
                self._write_ready.wait()
            self._writers += 1

        with self._read_ready:
            while self._readers > 0:
                self._read_ready.wait()

    _release_read (config.py:180-186) signals only _write_ready:

        with self._readers_lock:
            self._readers -= 1
            if self._readers == 0:
                with self._write_ready:
                    self._write_ready.notify_all()

    _read_ready is notified only from _release_write (config.py:204-205).
    A writer blocked in stage two is therefore waiting on a condition
    that the departing reader never signals, and is woken only if some
    other writer completes a full acquire-release cycle. With a single
    writer, it waits forever.
  impact: >
    Critical. The affected lock is not confined to the device-persistence
    subsystem: _rw_lock guards ConfigManager.load_config (config.py:1175,
    read lock at 1182, write lock at 1190) and save_config
    (config.py:1320, write lock at 1330). Those are the application's
    main configuration read and write, exercised by app.py:75 and
    main.py:107 on every start. A hang here blocks application startup or
    a settings save with no error, no log line and no recovery path.

    This corrects a claim in the source report. Report §5.1 states that
    the §3.1 and §3.6 bugs "have not surfaced in practice — the affected
    code is not exercised by the running application". That is accurate
    for §3.6, whose three methods have no callers, but not for §3.1: the
    lock underlies the live configuration path regardless of the
    device-persistence disposition.
  workaround: >
    None. The condition is not detectable from outside the lock and there
    is no timeout on the wait.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    The lock uses two condition variables over three separate underlying
    locks — _read_ready, _write_ready and _readers_lock — but the release
    paths do not signal both condition variables symmetrically.
    _release_write correctly notifies both; _release_read notifies only
    one. Because _acquire_write waits on _read_ready in its second stage
    and on _write_ready in its first, a reader's departure must signal
    both to be correct.

    The deeper cause is that _readers is mutated under _readers_lock but
    waited on via _read_ready, whose own lock is a different object. The
    counter is therefore not protected by the condition variable that
    guards waiting on it, which is the standard precondition for a
    condition variable to be free of lost wakeups.
  technical_notes: >
    The minimal correction is to notify _read_ready as well as
    _write_ready when the reader count reaches zero in _release_read.
    This wakes the stage-two writer and matches the symmetry
    _release_write already has.

    A stronger correction is to collapse the lock onto a single
    threading.Condition guarding both counters, which is the textbook
    reader-writer construction and removes the lost-wakeup class
    entirely. That is a larger change to a class of approximately 75
    lines and is recorded as the primary alternative in the change
    document.

    A third option is to remove RWLock altogether and use a plain
    threading.RLock. Reader concurrency buys nothing here: the guarded
    operation is reading and writing a small YAML file a handful of times
    per process lifetime. This is the simplest correct outcome but
    exceeds the scope of report recommendation #1 and is recorded rather
    than taken.

    get_stats (config.py:207-213) reads both counters under
    _readers_lock, though _writers is mutated under _write_ready. The
    reported writer count can therefore be momentarily stale. It is a
    monitoring accessor with no callers in src/gtach and is out of scope.
  related_issues:
    - issue_ref: "issue-394c3bbb"
      relationship: "related"
    - issue_ref: "issue-d32ccc49"
      relationship: "blocks"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Notify _read_ready in addition to _write_ready when the reader count
    reaches zero in _release_read, restoring the symmetry that
    _release_write already has. See change-1143427b.
  change_ref: "change-1143427b"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    A condition variable must be signalled by every path that can make
    its predicate true. Where two condition variables guard two stages of
    the same acquisition, both release paths must signal both.
  process_improvements: >
    Hand-written synchronisation primitives warrant a unit test that
    drives the interleaving explicitly, rather than relying on the
    absence of observed failures. Rarity of the window is not evidence of
    correctness.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/utils/config.py passes."
    - "Unit test: reproduce the interleaving in the reproduction steps and confirm the writer completes rather than blocking. The test must fail against the pre-change implementation."
    - "Unit test: confirm the writer acquisition completes within a bounded timeout, so a regression manifests as a test failure rather than a hung suite."
    - "Unit test: confirm concurrent readers still proceed in parallel — the fix must not serialise reads."
    - "Unit test: confirm writer exclusivity is preserved — no reader holds the lock while a writer does."
    - "Confirm ConfigManager.load_config and save_config behave unchanged in the single-threaded case."
    - "Confirm application startup on gtach.local is unaffected."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-1143427b"
  test_refs: []

notes: >
  This is task 7.4.9 in ai/task.md §7.4. It was separated from 7.4.1
  after a call-graph check established that the §5.1 retirement decision
  does not close this defect: _rw_lock guards the live configuration
  path, not only the device-persistence subsystem being retired. The
  reasoning is recorded in ai/task.md §7.4.8.

  §7.0 recommendation #1 is a disjunction — correct the notification bug
  or retire the subsystem. Its correction branch is claimed here; its
  retirement branch is claimed by 7.4.1.

  Released in v0.3.0 (ai/task.md §8.3) rather than with the 7.4.1
  retirement in v0.4.0, because it is a small correction on a live path
  and the retirement is a large deletion.

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
      - "Initial issue document from core-comm-utils-code-review.md §3.1 and recommendation #1, separated from 7.4.1 per ai/task.md §7.4.8."

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
| 1.0 | 2026-07-30 | Initial issue document from core-comm-utils-code-review.md §3.1 and recommendation #1, separated from 7.4.1 per ai/task.md §7.4.8. |

---

Copyright (c) 2026 William Watson. MIT License.
