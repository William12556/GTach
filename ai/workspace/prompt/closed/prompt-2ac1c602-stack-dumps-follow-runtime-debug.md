Created: 2026 August 12

# Prompt: Arm Stack Dumps From the Runtime Debug Toggle

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-2ac1c602"
  task_type: "debug"
  source_ref: "change-2ac1c602"
  target_profile: "claude_code"
  date: "2026-08-12"
  iteration: 2
  coupled_docs:
    change_ref: "change-2ac1c602"
    change_iteration: 2

context:
  purpose: >
    Make /opt/gtach/stacks.log actually appear. Iteration 1 of this
    change arms faulthandler inside setup_logging, gated on that
    function's debug argument, which derives from the --debug
    command-line flag. bin/gtach.service's ExecStart is
    `/opt/gtach/venv/bin/gtach` with no such flag, so args.debug is
    False on every service-launched run and faulthandler is never
    armed. No stacks.log was created on the 2026-08-12 09:11
    verification run. Debug is enabled in the field at RUNTIME, via the
    OPTIONS screen toggle. The arming must follow that same signal.
  integration: >
    Two edits across two existing files: src/gtach/main.py and
    src/gtach/app.py. Everything else delivered under
    prompt-2ac1c602 iteration 1 is correct and must be left alone.
  knowledge_references:
    - "ai/workspace/issues/issue-2ac1c602-display-blank-no-connection.md"
    - "ai/workspace/change/change-2ac1c602-watchdog-terminates-process.md"
    - "ai/workspace/prompt/closed/prompt-2ac1c602-watchdog-terminates-process.md"
    - "ai/workspace/report/report-2ac1c602-watchdog-terminates-process.md"
  constraints:
    - "Do not modify bin/gtach.service. Adding --debug there is explicitly rejected: it would make debug logging permanent in production and write a full all-thread stack dump every 15 s for the life of every run."
    - "Do not alter GTachApplication._watchdog_shutdown, _force_exit, _EXIT_BACKSTOP_SEC, the WatchdogMonitor construction, the transport registration, or anything in src/gtach/core/watchdog.py or src/gtach/comm/transport.py. Iteration 1 delivered those correctly."
    - "Do not change the dump interval. It remains 15 s, repeating."
    - "Do not change _STACKS_LOG's path."
    - "Preserve the existing --debug startup path: passing --debug must still arm stack dumps at startup, exactly as now."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: >
    Extract the faulthandler arming into a pair of idempotent
    module-level helpers in main.py, then drive them from
    GTachApplication.toggle_debug_logging as well as from
    setup_logging.
  requirements:
    functional:
      - "Enabling debug through the OPTIONS toggle creates /opt/gtach/stacks.log and starts 15 s repeating all-thread dumps."
      - "Disabling debug through the OPTIONS toggle cancels the repeat timer and closes the file."
      - "Starting with --debug arms stack dumps at startup, as before."
      - "Arming twice does not open a second file handle or stack a second timer."
      - "Disarming when not armed is a no-op."
      - "A failure to arm or disarm must not prevent the debug log handler from being toggled."
    technical:
      language: "Python"
      version: "3.9+"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance: []

design:
  architecture: >
    main.py owns the application's log files — _START_LOG, _DEBUG_LOG
    and _STACKS_LOG — and their handles. app.py owns the runtime
    decision about when debug is on. Iteration 1 placed the arming
    decision in main.py, which was correct for file ownership but wrong
    for the trigger. Splitting arming into helpers keeps ownership in
    main.py while letting app.py drive the decision, mirroring exactly
    how _debug_handler is already managed across the two modules.
  components:
    - name: "EDIT G — src/gtach/main.py: idempotent arm/disarm helpers"
      type: "function"
      purpose: "Make faulthandler arming callable at any point in the process lifetime, not only from setup_logging."
      logic:
        - "Add a module-level function `def enable_stack_dumps() -> bool:` after setup_logging."
        - "enable_stack_dumps declares `global _stacks_file`. If _stacks_file is not None it returns True immediately — already armed, no second handle, no second timer."
        - "Otherwise it opens _STACKS_LOG with mode='a', buffering=1, encoding='utf-8'; assigns _stacks_file; calls faulthandler.enable(file=_stacks_file); calls faulthandler.dump_traceback_later(15, repeat=True, file=_stacks_file); returns True."
        - "On OSError it prints the existing style of warning to sys.stderr, leaves _stacks_file as None, and returns False."
        - "Add a module-level function `def disable_stack_dumps() -> None:`. It declares `global _stacks_file`. If _stacks_file is None it returns immediately. Otherwise it calls faulthandler.cancel_dump_traceback_later(), then faulthandler.disable(), then closes _stacks_file inside a try/except, then sets _stacks_file = None."
        - "Order matters and must be as stated: cancel the timer and disable faulthandler BEFORE closing the file, or a dump can fire against a closed descriptor."
        - "In setup_logging, REPLACE the existing `if debug:` faulthandler block with a call to enable_stack_dumps() guarded by the same `if debug:` test. Move the explanatory comment currently attached to that block onto enable_stack_dumps's docstring, and extend it to record why arming is no longer reached only from here: bin/gtach.service passes no --debug, so the startup path is not the path that matters in production (issue-2ac1c602 iteration 3)."
        - "Both helpers must be safe to call from a thread other than the one that ran setup_logging. faulthandler's own calls are safe; the guard on _stacks_file is the only shared state and its transitions are single-assignment."
    - name: "EDIT H — src/gtach/app.py: drive the helpers from the runtime toggle"
      type: "class"
      purpose: "Arm stack dumps on the signal that actually turns debug on in the field."
      logic:
        - "In GTachApplication.toggle_debug_logging (currently app.py:208-238), retain every existing line: the linux platform guard, the sys.modules.get('gtach.main') retrieval established by issue-c1d4b8e6, the None checks, the _debug_handler level changes and the two INFO log lines."
        - "In the `if enable:` branch, after `_main._debug_handler.setLevel(logging.DEBUG)` and its INFO log, call `_main.enable_stack_dumps()` inside its own try/except Exception, logging any failure at DEBUG with exc_info=True."
        - "In the `else:` branch, after `_main._debug_handler.setLevel(logging.CRITICAL + 1)` and its INFO log, call `_main.disable_stack_dumps()` inside its own try/except Exception, logging any failure at DEBUG with exc_info=True."
        - "The inner try/except blocks are required: a failure to arm stack dumps must never prevent the debug log handler from being toggled, which is the operator's primary diagnostic control."
        - "Use getattr(_main, 'enable_stack_dumps', None) style access, or a hasattr guard, so a partially loaded or older gtach.main cannot raise AttributeError out of this method."
        - "Update the method docstring: it currently says only 'Activate or suppress debug.log at runtime'. It now also arms and disarms all-thread stack dumps to stacks.log."

data_schema:
  entities: []

error_handling:
  strategy: >
    Diagnostics must degrade independently. A failure in the stack-dump
    path must not affect the debug log path, and neither must affect
    the running application.
  exceptions:
    - exception: "OSError"
      condition: "Opening /opt/gtach/stacks.log fails."
      handling: "enable_stack_dumps prints a warning to sys.stderr, leaves _stacks_file as None, and returns False. Startup and the debug toggle both continue."
    - exception: "Exception"
      condition: "enable_stack_dumps or disable_stack_dumps raises when called from toggle_debug_logging."
      handling: "Caught by the inner try/except in toggle_debug_logging; logged at DEBUG with exc_info=True; the debug handler level change is unaffected."
    - exception: "Exception"
      condition: "Closing _stacks_file raises in disable_stack_dumps."
      handling: "Swallowed. _stacks_file must still be set to None so a subsequent enable_stack_dumps can re-arm."
  logging:
    level: "DEBUG"
    format: "Existing _LOG_FORMAT in main.py; no format change."

testing:
  unit_tests:
    - scenario: "enable_stack_dumps called once with _STACKS_LOG monkeypatched to a tmp_path file."
      expected: "Returns True; the file exists; the module's _stacks_file is not None."
    - scenario: "enable_stack_dumps called twice in succession."
      expected: "Returns True both times; only one file object is opened; the second call does not re-arm the timer."
    - scenario: "disable_stack_dumps called after enable_stack_dumps."
      expected: "_stacks_file is None; the file object is closed."
    - scenario: "disable_stack_dumps called when nothing is armed."
      expected: "Returns without raising; _stacks_file remains None."
    - scenario: "enable_stack_dumps, disable_stack_dumps, enable_stack_dumps."
      expected: "Re-arms successfully; _stacks_file is not None after the third call."
    - scenario: "enable_stack_dumps with _STACKS_LOG pointing into a non-existent directory."
      expected: "Returns False; _stacks_file is None; no exception propagates."
    - scenario: "setup_logging(debug=False)."
      expected: "enable_stack_dumps is not called; _stacks_file remains None."
    - scenario: "setup_logging(debug=True)."
      expected: "enable_stack_dumps is called exactly once."
    - scenario: "toggle_debug_logging(True) with a stubbed gtach.main module exposing enable_stack_dumps."
      expected: "_debug_handler.setLevel(logging.DEBUG) is called AND enable_stack_dumps is called."
    - scenario: "toggle_debug_logging(False) with a stubbed gtach.main module."
      expected: "_debug_handler level is raised to CRITICAL+1 AND disable_stack_dumps is called."
    - scenario: "toggle_debug_logging(True) where enable_stack_dumps raises."
      expected: "_debug_handler.setLevel(logging.DEBUG) still occurs; no exception propagates out of toggle_debug_logging."
    - scenario: "toggle_debug_logging(True) where the stubbed gtach.main has no enable_stack_dumps attribute."
      expected: "No AttributeError; the debug handler is still toggled."
  edge_cases:
    - "Started with --debug AND then toggled on again through OPTIONS — the second arming must be a no-op, not a second timer."
    - "Toggled off, then on, then off — each transition must leave a consistent _stacks_file state."
    - "toggle_debug_logging called on a non-linux platform — the existing early return must still fire before any stack-dump call."
  validation:
    - "pytest tests/ passes."
    - "python -c \"import ast; ast.parse(open('src/gtach/main.py').read())\" and the same for src/gtach/app.py."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Edit the existing files in place. Do not create new modules."
  files:
    - path: "src/gtach/main.py"
      content: "EDIT G"
    - path: "src/gtach/app.py"
      content: "EDIT H"
    - path: "tests/test_stack_dump_toggle.py"
      content: "Unit tests for testing.unit_tests items 1-12"

success_criteria:
  - "src/gtach/main.py defines module-level functions named enable_stack_dumps and disable_stack_dumps."
  - "setup_logging contains no direct call to faulthandler.dump_traceback_later; that call appears only inside enable_stack_dumps."
  - "setup_logging calls enable_stack_dumps() when and only when its debug argument is truthy."
  - "GTachApplication.toggle_debug_logging calls enable_stack_dumps on the enable branch and disable_stack_dumps on the disable branch, each inside its own exception guard."
  - "Calling enable_stack_dumps twice does not open a second file object — assertable by identity of the module's _stacks_file across the two calls."
  - "disable_stack_dumps calls faulthandler.cancel_dump_traceback_later before closing _stacks_file."
  - "_STACKS_LOG still equals '/opt/gtach/stacks.log' and the dump interval is still 15 with repeat=True."
  - "bin/gtach.service is byte-identical to its pre-change state; grep -n 'debug' bin/gtach.service returns no match."
  - "src/gtach/core/watchdog.py and src/gtach/comm/transport.py are byte-identical to their post-iteration-1 state."
  - "GTachApplication._watchdog_shutdown, GTachApplication._force_exit and _EXIT_BACKSTOP_SEC are unchanged."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "main"
        path: "src/gtach/main.py"
      - name: "app"
        path: "src/gtach/app.py"
    classes:
      - name: "GTachApplication"
        module: "gtach.app"
    functions:
      - name: "setup_logging"
        module: "gtach.main"
        signature: "(debug: bool = False) -> None"
      - name: "enable_stack_dumps"
        module: "gtach.main"
        signature: "() -> bool"
      - name: "disable_stack_dumps"
        module: "gtach.main"
        signature: "() -> None"
      - name: "toggle_debug_logging"
        module: "gtach.app"
        signature: "(self, enable: bool) -> None"
    constants:
      - name: "_STACKS_LOG"
        module: "gtach.main"
        type: "str"
      - name: "_stacks_file"
        module: "gtach.main"
        type: "Optional[IO]"

notes: >
  On-target verification is a human step. After deployment to
  gtach.local with no reachable OBD transport: confirm
  /opt/gtach/stacks.log does NOT exist at startup; enable debug through
  the OPTIONS toggle; confirm the file appears and gains an all-thread
  dump roughly every 15 s; disable debug and confirm dumps stop;
  re-enable and confirm they resume.

  The purpose of this edit is to make the ~52 s process-wide stall
  observable. That stall did not recur on the 2026-08-12 09:11 run, so
  both it and the process-termination path delivered by iteration 1
  remain unverified on target. Neither the issue nor the change should
  be closed on this prompt alone.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Prompt iteration 2 for change-2ac1c602 iteration 2. Extracts faulthandler arming into enable_stack_dumps/disable_stack_dumps in main.py and drives them from GTachApplication.toggle_debug_logging, because iteration 1 gated arming on the startup --debug flag that bin/gtach.service never passes. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
