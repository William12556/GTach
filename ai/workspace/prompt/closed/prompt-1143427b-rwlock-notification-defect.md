Created: 2026 July 30

# Prompt: Correct the RWLock Notification Defect

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-1143427b"
  task_type: "code_generation"
  source_ref: "change-1143427b"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-1143427b"
    change_iteration: 1

context:
  purpose: >
    Remove an unbounded wait from the application's configuration path. A
    writer that has entered the second stage of RWLock._acquire_write
    waits on _read_ready, but a departing reader signals only
    _write_ready, so with a single writer the wait never ends. The lock
    guards ConfigManager.load_config and save_config, which run on every
    application start.
  integration: >
    One method in src/gtach/utils/config.py: RWLock._release_read.
    Executor is Claude Code; AEL is not used. Ships in v0.3.0 per
    ai/task.md §8.3. Independent of the ConfigManager device-persistence
    retirement (task 7.4.1) — the retirement does not close this defect,
    for the reason recorded in ai/task.md §7.4.8.
  knowledge_references: []
  constraints:
    - "Modify only RWLock._release_read in src/gtach/utils/config.py. Change no other method and no other file."
    - "Do NOT redesign RWLock onto a single condition variable. That is the recorded primary alternative and is deliberately not taken here."
    - "Do NOT replace RWLock with threading.RLock. Recorded as an alternative; out of scope."
    - "Do NOT add a timeout to any wait. A timeout would convert a deadlock into a silent correctness violation."
    - "Do NOT remove or shortcut stage two of _acquire_write. It closes a genuine reader-entry window."
    - "Do not change ConfigManager.load_config or save_config, or any read_lock/write_lock call site."
    - "Do not touch the device-persistence methods at config.py:1400-1460. Those belong to task 7.4.1."
    - "Never hold two of the three locks (_readers_lock, _read_ready, _write_ready) simultaneously in the edited method."
    - "Google-style docstrings; PEP 8."

specification:
  description: >
    _release_read notifies _read_ready in addition to _write_ready when
    the reader count reaches zero, and releases _readers_lock before
    taking either condition.
  requirements:
    functional:
      - "When the last reader releases, both _write_ready and _read_ready are notified."
      - "When a reader releases and others remain, neither condition is notified — behaviour unchanged."
      - "_readers_lock is released before either condition variable is acquired."
      - "A writer waiting in stage two of _acquire_write is woken by the last reader's departure."
      - "Reader concurrency and writer exclusivity are unchanged."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Professional docstrings"
  performance:
    - target: "No additional lock acquisition on a non-final reader release"
      metric: "time"

design:
  architecture: >
    A departing reader can satisfy the predicate of either stage of
    _acquire_write, so it must signal both conditions. _release_write
    already does this; _release_read is brought into line with it.
  components:
    - name: "RWLock._release_read"
      type: "function"
      purpose: "Release read access and wake any writer whose predicate the release satisfies."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "No return value."
        raises:
          - "None."
      logic:
        - "Under _readers_lock: decrement self._readers and capture whether it reached zero into a local."
        - "Release _readers_lock before proceeding — do not nest the condition acquisitions inside it."
        - "If it reached zero: acquire _write_ready, notify_all, release; then acquire _read_ready, notify_all, release."
        - "Acquire the two conditions in sequence, never nested, so no thread holds both."
        - "If it did not reach zero, do nothing further."
  dependencies:
    internal:
      - "RWLock._acquire_write — waits on _write_ready in stage one and _read_ready in stage two; both are now signalled by a reader's departure."
      - "RWLock._acquire_read — also waits on _read_ready; its while-loop predicate absorbs the additional wakeup."
      - "ConfigManager.load_config (config.py:1175) and save_config (config.py:1320) — consumers; no call-site change."
    external: []

error_handling:
  strategy: >
    No new failure mode is introduced and no exception handling is added.
    The change removes a wait that nothing could end.
  exceptions:
    - exception: "None"
      condition: "The edited method performs counter arithmetic and condition notification only."
      handling: "No try/except is added. An exception here would indicate a corrupted lock, which must not be swallowed."
  logging:
    level: "None"
    format: "No logging is added. This method runs on every configuration read and must stay silent."

testing:
  unit_tests:
    - scenario: "Reader in; writer advances to stage two; second reader enters and leaves."
      expected: "The writer acquires within a bounded timeout. Hangs against the pre-change implementation."
    - scenario: "Writer acquires with no readers present."
      expected: "Acquires immediately."
    - scenario: "Two readers hold the lock concurrently."
      expected: "Both hold it at once; reader concurrency preserved."
    - scenario: "Reader attempts acquisition while a writer holds the lock."
      expected: "Blocks until the writer releases."
    - scenario: "Writer attempts acquisition while a reader holds the lock."
      expected: "Blocks until the reader releases, then acquires."
    - scenario: "Three readers release in sequence."
      expected: "Notification occurs only on the third release."
    - scenario: "Mixed reader and writer threads over repeated cycles."
      expected: "No thread blocks beyond its timeout; _readers and _writers both return to zero."
  edge_cases:
    - "Release when _readers is already zero — an unbalanced release. Behaviour is unchanged by this edit and is not defended against."
    - "Spurious wakeup of a reader waiting in _acquire_read: absorbed by its while-loop predicate."
    - "Two writers queued: the first to complete _release_write wakes the second, as before."
  validation:
    - "Every acquisition assertion in the generated tests carries a timeout, so a regression fails the suite rather than hanging it."
    - "get_stats returns zero active readers and writers after each test."

deliverable:
  format_requirements:
    - "Edit src/gtach/utils/config.py in place. Create no new file."
    - "Make the single edit below and change nothing else."
  files:
    - path: "src/gtach/utils/config.py"
      content: |
        EDIT — RWLock._release_read (currently config.py:180-186)

        Replace the whole method. Current text:

            def _release_read(self):
                """Release read access"""
                with self._readers_lock:
                    self._readers -= 1
                    if self._readers == 0:
                        with self._write_ready:
                            self._write_ready.notify_all()

        Replacement:

            def _release_read(self):
                """Release read access and wake any waiting writer.

                _acquire_write waits on _write_ready in its first stage and
                on _read_ready in its second. A departing reader can satisfy
                either predicate, so both conditions must be signalled.
                Notifying only _write_ready leaves a stage-two writer
                waiting on a condition that nothing signals, which is an
                unbounded wait on the live ConfigManager.load_config and
                save_config path (core review §3.1).

                _readers_lock is released before either condition is
                acquired, so no thread holds two of this lock's three
                primitives at once.
                """
                with self._readers_lock:
                    self._readers -= 1
                    last_reader = self._readers == 0

                if last_reader:
                    with self._write_ready:
                        self._write_ready.notify_all()
                    with self._read_ready:
                        self._read_ready.notify_all()

        Change nothing else in the file. In particular leave unchanged:
          - RWLock.__init__ and its three primitives
          - read_lock and write_lock, the two contextmanagers
          - _acquire_read
          - _acquire_write, including both of its stages
          - _release_write, which already notifies both conditions
          - get_stats
          - ConfigManager, its load_config and save_config, and every
            read_lock / write_lock call site
          - the device-persistence methods at config.py:1400-1460

        Note the two distinct corrections in this edit. The first is the
        added _read_ready notification, which is the defect fix. The
        second is separating the counter decrement from the notifications
        so _readers_lock is not held across a condition acquisition; that
        narrows the critical section and removes the only point where two
        of the three primitives were held together. Both are required —
        do not apply only the first.

success_criteria:
  - "python -m py_compile src/gtach/utils/config.py passes."
  - "pytest tests/ passes with no new failures."
  - "_release_read contains a notify_all on _write_ready and a notify_all on _read_ready."
  - "The two condition blocks in _release_read are sequential, not nested."
  - "_readers_lock is not held while either condition variable is acquired."
  - "_release_read reads self._readers exactly once, under _readers_lock, into a local."
  - "No other method of RWLock differs from its pre-change text."
  - "ConfigManager is unmodified."
  - "No file other than src/gtach/utils/config.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "config"
        path: "src/gtach/utils/config.py"
    classes:
      - name: "RWLock"
        module: "gtach.utils.config"
      - name: "ConfigManager"
        module: "gtach.utils.config"
    functions:
      - name: "_release_read"
        module: "gtach.utils.config"
        signature: "_release_read(self) -> None"
      - name: "_acquire_write"
        module: "gtach.utils.config"
        signature: "_acquire_write(self) -> None"
      - name: "_release_write"
        module: "gtach.utils.config"
        signature: "_release_write(self) -> None"
      - name: "_acquire_read"
        module: "gtach.utils.config"
        signature: "_acquire_read(self) -> None"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-1143427b-rwlock-notification-defect.md

  This is the smallest change that makes the lock correct. Two larger
  and arguably better options were considered and deliberately not taken
  — collapsing RWLock onto one condition variable, and replacing it with
  a plain threading.RLock. Both are recorded under
  alternatives_considered in change-1143427b. If the 7.4.1 retirement
  leaves RWLock with little remaining justification, the RLock option
  should be raised as its own cycle rather than folded into this one.

  There is no observable behaviour change in normal operation. The change
  removes a failure mode; it does not alter a function. Verification is
  therefore by the generated unit tests rather than by inspection of
  running behaviour.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-1143427b. |
| 1.1 | 2026-07-30 | Executed by Claude Code. The single edit applied; eight of the nine success criteria met, with the pytest criterion satisfied only vacuously — tests/ holds no test modules — and verification recorded against an ephemeral script under change-1143427b. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/. |

---

Copyright (c) 2026 William Watson. MIT License.
