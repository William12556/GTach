Created: 2026 August 12

# Prompt: Give stacks.log a Run Header and Rotate It Once Per Process

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-3b8c50f2"
  task_type: "refactor"
  source_ref: "change-3b8c50f2"
  target_profile: "claude_code"
  date: "2026-08-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-3b8c50f2"
    change_iteration: 1

context:
  purpose: >
    Make stacks.log attributable and bounded. It is opened in append
    mode and faulthandler's dumps carry no timestamp, PID or run
    identifier, so dumps from successive process lifetimes concatenate
    indistinguishably — worst in the very scenario the file exists for,
    a watchdog-triggered restart. It also has no rotation or size cap,
    unlike debug.log.
  integration: >
    All edits are inside src/gtach/main.py: two module-level names and
    two additions to enable_stack_dumps. No other file is modified.
  knowledge_references:
    - "ai/workspace/issues/issue-3b8c50f2-stacks-log-run-header-and-rotation.md"
    - "ai/workspace/change/change-3b8c50f2-stacks-log-run-header-and-rotation.md"
    - "ai/workspace/report/report-2ac1c602-stack-dumps-follow-runtime-debug.md"
  constraints:
    - "Do NOT introduce any Python-side periodic timer, thread, or timestamp-per-dump mechanism. Such a timer would stall in exactly the window this file exists to capture, forfeiting the property that makes faulthandler valuable here. This is the single most important constraint in this prompt."
    - "Do not modify disable_stack_dumps. Its cancel-then-disable-then-close ordering is load-bearing and correct."
    - "Do not write a footer on disarm. It would be absent whenever a run ends by crash or force-exit, which are the interesting cases."
    - "Do not change _STACKS_LOG's path or the 15 s dump interval."
    - "Retain mode='a'. mode='w' would discard the previous run's dumps at relaunch."
    - "Do not modify setup_logging's handling of start.log or debug.log."
    - "Do not modify src/gtach/app.py. toggle_debug_logging already calls enable_stack_dumps; both additions land inside the callee."
    - "tests/test_stack_dump_toggle.py must continue to pass unmodified."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: >
    Apply edits I, J and K to src/gtach/main.py, then add the unit
    tests in the testing section.
  requirements:
    functional:
      - "Every arming of stack dumps writes one identifying header line before faulthandler is armed."
      - "The header carries the gtach version, the process PID, and an ISO-8601 local timestamp."
      - "An existing non-empty stacks.log is rotated on the FIRST arm of a process lifetime only."
      - "Rotation keeps three backups; stacks.log.4 is never created."
      - "Re-arming within one process appends a fresh header and does not rotate again."
      - "A failure to rotate, or to write the header, never prevents faulthandler from being armed."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Rotation and header write add no measurable delay to arming; both are O(1) filesystem operations performed once per arm"
      metric: "time"

design:
  architecture: >
    Both additions execute at arming time — a moment when the process
    is by definition running normally, because the operator has just
    enabled the toggle or the process has just started. Nothing added
    by this change runs during a stall, which is why the anchor it
    writes survives one.
  components:
    - name: "EDIT I — src/gtach/main.py: module-level names"
      type: "module"
      purpose: "Declare the backup count and the once-per-process rotation flag."
      logic:
        - "Add `import datetime` to the module imports, in alphabetical position among the existing stdlib imports."
        - "Beside the existing `_stacks_file = None` declaration, add:  _stacks_rotated = False"
        - "Comment it: rotation is once per PROCESS, not once per arm, because arming occurs on every OPTIONS toggle-on and rotating each time would push a just-captured reproduction off the end of the backup chain (issue-3b8c50f2)."
        - "After the existing `_STACKS_LOG = '/opt/gtach/stacks.log'` line, add:  _STACKS_BACKUPS = 3"
        - "Comment it with the measured basis: a dump of four threads is ~604 bytes and the interval is 15 s, so an armed run produces ~145 KB per hour. Three backups plus the live file bound cross-run accumulation at four files."
    - name: "EDIT J — src/gtach/main.py: rotate on first arm"
      type: "function"
      purpose: "Bound cross-run accumulation without discarding the previous run."
      logic:
        - "Add a module-level helper `def _rotate_stacks_log() -> None:` immediately before enable_stack_dumps."
        - "The helper returns immediately if _STACKS_LOG does not exist or os.path.getsize(_STACKS_LOG) == 0."
        - "Otherwise it shifts generations from the highest downwards: for i in range(_STACKS_BACKUPS - 1, 0, -1), rename f'{_STACKS_LOG}.{i}' to f'{_STACKS_LOG}.{i+1}' when the source exists. Then rename _STACKS_LOG to f'{_STACKS_LOG}.1'."
        - "Descending order is required. Ascending order would overwrite each generation with the one below it before it had been moved."
        - "os.replace, not os.rename, so an existing destination is overwritten rather than raising on some platforms. What was stacks.log.3 is discarded, which is intended."
        - "In enable_stack_dumps, declare `global _stacks_rotated` alongside the existing `global _stacks_file`."
        - "After the early return for the already-armed case, and BEFORE the file is opened, add: if not _stacks_rotated, call _rotate_stacks_log() inside a try/except OSError that prints the existing style of warning to sys.stderr, then set _stacks_rotated = True in a finally clause so a failed rotation is not retried on every subsequent arm."
        - "Rotation must not prevent arming. A failure here costs history, not evidence; the open and arm must proceed regardless."
    - name: "EDIT K — src/gtach/main.py: write the run header"
      type: "function"
      purpose: "Give every contiguous block of dumps a process and a wall-clock anchor."
      logic:
        - "Add a module-level helper `def _stacks_header() -> str:` returning the header line."
        - "It resolves the version via importlib.metadata.version('gtach') inside a try/except Exception falling back to the literal 'unknown', exactly mirroring the guarded pattern already used in parse_arguments."
        - "It returns: f'=== gtach {version} pid {os.getpid()} armed {timestamp} ===\\n' where timestamp is datetime.datetime.now().isoformat(timespec='seconds')."
        - "In enable_stack_dumps, after the successful open of _stacks_file and BEFORE faulthandler.enable and faulthandler.dump_traceback_later, write the header: _stacks_file.write(_stacks_header()) inside its own try/except Exception that prints a warning to sys.stderr and continues."
        - "Ordering is required: the header must precede arming, so that no dump can be written above the header identifying it."
        - "The header write must never prevent arming. The dumps matter more than their label."
        - "Extend enable_stack_dumps's docstring: it now rotates on the first arm of the process and writes an identifying header on every arm. Record that the PID in the header is direct evidence of a systemd restart when it changes between two headers, which issue-2ac1c602's verification requires."

data_schema:
  entities:
    - name: "stacks.log run header"
      attributes:
        - name: "version"
          type: "str"
          constraints: "gtach distribution version, or the literal 'unknown' when unresolvable"
        - name: "pid"
          type: "int"
          constraints: "os.getpid() at arming time"
        - name: "timestamp"
          type: "str"
          constraints: "ISO-8601 local time, seconds precision"
      validation:
        - "The line begins with '=== gtach ' and ends with ' ===' followed by a newline."
        - "Exactly one header is written per successful arming."

error_handling:
  strategy: >
    Neither addition may cost the operator their dumps. Rotation and
    the header write are separately guarded, and arming proceeds
    whichever of them fails.
  exceptions:
    - exception: "OSError"
      condition: "A rename during rotation fails, or the file cannot be stat'd."
      handling: "Print a warning to sys.stderr in the existing style; set _stacks_rotated True regardless so it is not retried on every arm; continue to open and arm."
    - exception: "Exception"
      condition: "importlib.metadata.version('gtach') raises or the distribution is absent."
      handling: "Fall back to the literal 'unknown'; still emit a header."
    - exception: "Exception"
      condition: "Writing the header to the open file fails."
      handling: "Print a warning to sys.stderr; proceed to arm faulthandler; return True."
    - exception: "OSError"
      condition: "Opening _STACKS_LOG fails."
      handling: "Existing behaviour is retained: warn to sys.stderr, leave _stacks_file as None, return False."
  logging:
    level: "n/a"
    format: "Direct sys.stderr prints, matching the existing convention in setup_logging. Do NOT use the logging module here: arming can occur before or independently of handler configuration."

testing:
  unit_tests:
    - scenario: "First arm, no pre-existing _STACKS_LOG (monkeypatched into tmp_path)."
      expected: "No .1 file is created; stacks.log exists; its first line matches '=== gtach ... pid <os.getpid()> armed ... ===' and contains the current PID."
    - scenario: "First arm with a pre-existing non-empty stacks.log."
      expected: "The prior content is at stacks.log.1; the new stacks.log begins with a header."
    - scenario: "First arm with a pre-existing but EMPTY stacks.log."
      expected: "No rotation; stacks.log.1 does not exist."
    - scenario: "disable_stack_dumps then enable_stack_dumps within the same process, after a first arm that rotated."
      expected: "No second rotation; stacks.log.1 is byte-identical to before; stacks.log now contains two header lines."
    - scenario: "Four successive first-arms with _stacks_rotated reset between them, simulating four process lifetimes."
      expected: "stacks.log.1, .2 and .3 exist; stacks.log.4 does not; the oldest content has been discarded."
    - scenario: "enable_stack_dumps called twice with no intervening disable."
      expected: "Returns True both times; exactly one header line in the file; the module's _stacks_file is the same object across both calls."
    - scenario: "_rotate_stacks_log monkeypatched to raise OSError."
      expected: "A warning is printed to stderr; enable_stack_dumps returns True; the file is opened, the header written and faulthandler armed; _stacks_rotated is True."
    - scenario: "importlib.metadata.version monkeypatched to raise."
      expected: "A header is still written and contains the fallback version literal."
    - scenario: "The open file object's write monkeypatched to raise on the header."
      expected: "enable_stack_dumps returns True; faulthandler was still armed."
    - scenario: "Rotation ordering with stacks.log, .1 and .2 all present and distinguishable by content."
      expected: "Contents shift outward by exactly one generation; no generation is overwritten by its neighbour before being moved."
  edge_cases:
    - "Started with --debug, so setup_logging performs the first arm, then the OPTIONS toggle re-arms later in the same run — the toggle must not rotate."
    - "Rotation when stacks.log.3 already exists — it is discarded, and os.replace must not raise on the existing destination."
    - "Toggled off and on several times in one run — one rotation, several headers."
  validation:
    - "grep for any use of threading.Timer, threading.Thread or time.sleep introduced by this change returns nothing in src/gtach/main.py beyond what already exists."
    - "pytest tests/ passes, including tests/test_stack_dump_toggle.py unmodified."
    - "python -c \"import ast; ast.parse(open('src/gtach/main.py').read())\""

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Edit the existing file in place. Do not create new modules."
  files:
    - path: "src/gtach/main.py"
      content: "EDIT I, EDIT J and EDIT K"
    - path: "tests/test_stacks_log_rotation.py"
      content: "Unit tests for testing.unit_tests items 1-10"

success_criteria:
  - "src/gtach/main.py defines _STACKS_BACKUPS = 3 and a module-level _stacks_rotated initialised to False."
  - "src/gtach/main.py defines module-level helpers _rotate_stacks_log and _stacks_header."
  - "In enable_stack_dumps, the header is written after _stacks_file is opened and before faulthandler.dump_traceback_later is called."
  - "In enable_stack_dumps, _rotate_stacks_log is called only when _stacks_rotated is False, and _stacks_rotated is set True whether or not rotation succeeded."
  - "_rotate_stacks_log shifts generations in DESCENDING order and uses os.replace."
  - "The file is still opened with mode='a'; no occurrence of mode='w' against _STACKS_LOG exists."
  - "disable_stack_dumps is byte-identical to its pre-change state."
  - "_STACKS_LOG still equals '/opt/gtach/stacks.log'; the dump interval is still 15 with repeat=True."
  - "No threading.Timer, threading.Thread, or periodic Python-side timer is introduced by this change anywhere in src/gtach/main.py."
  - "src/gtach/app.py, src/gtach/core/watchdog.py, src/gtach/comm/transport.py and bin/gtach.service are byte-identical to their pre-change state."
  - "tests/test_stack_dump_toggle.py passes unmodified."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "main"
        path: "src/gtach/main.py"
    classes: []
    functions:
      - name: "enable_stack_dumps"
        module: "gtach.main"
        signature: "() -> bool"
      - name: "disable_stack_dumps"
        module: "gtach.main"
        signature: "() -> None"
      - name: "_rotate_stacks_log"
        module: "gtach.main"
        signature: "() -> None"
      - name: "_stacks_header"
        module: "gtach.main"
        signature: "() -> str"
      - name: "setup_logging"
        module: "gtach.main"
        signature: "(debug: bool = False) -> None"
    constants:
      - name: "_STACKS_LOG"
        module: "gtach.main"
        type: "str"
      - name: "_STACKS_BACKUPS"
        module: "gtach.main"
        type: "int"
      - name: "_stacks_rotated"
        module: "gtach.main"
        type: "bool"
      - name: "_stacks_file"
        module: "gtach.main"
        type: "Optional[IO]"

notes: >
  On-target verification is a human step. After deployment to
  gtach.local: restart the service, enable debug through the OPTIONS
  toggle, and confirm that stacks.log opens with a header whose pid
  matches `systemctl show gtach -p MainPID`, and that the previous
  run's dumps are now at stacks.log.1. Toggle debug off and on again
  and confirm a second header appears with no further rotation.

  The PID in the header is not incidental. issue-2ac1c602 remains
  active pending evidence that a watchdog critical timeout produces a
  systemd restart; two headers with different PIDs in one stacks.log
  is exactly that evidence, captured automatically rather than
  requiring an operator to be watching systemctl at the moment it
  happens.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial prompt implementing change-3b8c50f2 iteration 1. Three edits in src/gtach/main.py plus one unit test module. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
