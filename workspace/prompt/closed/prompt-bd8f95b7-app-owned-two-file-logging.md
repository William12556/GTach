Created: 2026 June 12

```yaml
prompt_info:
  id: "prompt-bd8f95b7"
  task_type: "code_generation"
  source_ref: "change-bd8f95b7"
  date: "2026-06-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-bd8f95b7"
    change_iteration: 1

context:
  purpose: >
    Replace tee-based logging with application-owned file handlers that survive
    systemd launch and provide a toggle mechanism for the future OPTIONS debug
    button.
  integration: >
    Two files modified: main.py (setup_logging) and app.py (GTachApplication).
    Executor: Claude Code (no AEL).
  constraints:
    - "Linux-only file handlers: guard every open with sys.platform.startswith('linux')."
    - "Non-Linux behaviour must be preserved exactly (basicConfig stderr or NullHandler)."
    - "Handler open failures must be caught and printed to stderr; never abort startup."
    - "Do not call ConfigManager.setup_logging() — it is unused infrastructure."
    - "Do not modify faulthandler setup — stderr is captured by journald under systemd."
    - "No changes outside main.py and app.py."

specification:
  description: >
    Two-file Linux logging model with startup isolation and runtime toggle.
  requirements:
    functional:
      - "start.log truncated at boot; receives all root logger records during startup; detached after startup."
      - "debug.log truncated at boot; suppressed by default; activated by toggle or --debug flag."
      - "toggle_debug_logging(enable) activates/suppresses debug.log at runtime."
      - "Non-Linux: no file handlers; existing behaviour preserved."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "Tolerant error handling on all file operations."
        - "No new dependencies."

design:
  architecture: >
    Module-level handler references in main.py. GTachApplication calls finish
    and toggle via imported references. No new classes.
  components:
    - name: "setup_logging"
      type: "function"
      purpose: "Configure root logger with two-file handlers on Linux."
      logic:
        - "Replace the existing two-branch function with the implementation in deliverable file 1."
        - "Module-level _start_handler and _debug_handler are defined at module scope (initially None)."

    - name: "GTachApplication._finish_startup_logging"
      type: "function"
      purpose: "Detach start.log after startup is complete."
      logic:
        - "Import _start_handler from .main."
        - "If _start_handler is not None: log INFO 'Startup complete — start.log closed'; set _start_handler.setLevel(logging.CRITICAL + 1)."
        - "Tolerant of all exceptions; log at debug level."

    - name: "GTachApplication.toggle_debug_logging"
      type: "function"
      purpose: "Activate or suppress debug.log at runtime."
      logic:
        - "Import _debug_handler from .main."
        - "If _debug_handler is None or not Linux: return."
        - "enable=True: _debug_handler.setLevel(logging.DEBUG); log INFO 'Debug logging enabled'."
        - "enable=False: _debug_handler.setLevel(logging.CRITICAL + 1); log INFO 'Debug logging disabled'."
        - "Tolerant of all exceptions."

    - name: "GTachApplication.start"
      type: "function"
      purpose: "Call _finish_startup_logging at end of startup."
      logic:
        - "At the end of the start() try block, after self._clear_update_probation(), add: self._finish_startup_logging()."

  dependencies:
    internal:
      - "src/gtach/main.py — _start_handler, _debug_handler module references"

deliverable:
  format_requirements:
    - "Edit both files in place."
  files:
    - path: "src/gtach/main.py"
      content: |
        Replace the existing setup_logging() function and add two module-level
        references. The complete replacement for that section is:

            import logging
            import sys
            from logging.handlers import RotatingFileHandler

            # Module-level handler references for runtime manipulation.
            _start_handler: logging.Handler = None
            _debug_handler: logging.Handler = None

            _LOG_FORMAT = '%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s'
            _LOG_DATE_FMT = '%Y-%m-%d %H:%M:%S'
            _START_LOG = '/opt/gtach/start.log'
            _DEBUG_LOG = '/opt/gtach/debug.log'
            _DEBUG_MAX_BYTES = 100 * 1024 * 1024  # 100 MB


            def setup_logging(debug: bool = False) -> None:
                global _start_handler, _debug_handler

                if not sys.platform.startswith('linux'):
                    # Non-Linux: preserve existing behaviour.
                    if debug:
                        logging.basicConfig(
                            level=logging.DEBUG,
                            format='%(asctime)s %(name)s %(levelname)s %(message)s'
                        )
                    else:
                        logging.getLogger().addHandler(logging.NullHandler())
                    return

                formatter = logging.Formatter(_LOG_FORMAT, datefmt=_LOG_DATE_FMT)
                root = logging.getLogger()
                root.setLevel(logging.DEBUG)

                # start.log — truncated at boot; startup records only.
                try:
                    _start_handler = logging.FileHandler(_START_LOG, mode='w', encoding='utf-8')
                    _start_handler.setLevel(logging.DEBUG)
                    _start_handler.setFormatter(formatter)
                    root.addHandler(_start_handler)
                except OSError as e:
                    print(f'[gtach] WARNING: could not open {_START_LOG}: {e}', file=sys.stderr)

                # debug.log — truncated at boot; suppressed unless toggled on.
                try:
                    _debug_handler = RotatingFileHandler(
                        _DEBUG_LOG, mode='w', maxBytes=_DEBUG_MAX_BYTES,
                        backupCount=0, encoding='utf-8'
                    )
                    _debug_handler.setLevel(logging.CRITICAL + 1)  # suppressed
                    _debug_handler.setFormatter(formatter)
                    root.addHandler(_debug_handler)
                except OSError as e:
                    print(f'[gtach] WARNING: could not open {_DEBUG_LOG}: {e}', file=sys.stderr)

                if debug and _debug_handler is not None:
                    _debug_handler.setLevel(logging.DEBUG)

        The two module-level references (_start_handler, _debug_handler) must be
        placed at module scope, before setup_logging(). The existing imports of
        logging and sys are already present; add only the RotatingFileHandler
        import. Do not alter any other function or import in main.py.

    - path: "src/gtach/app.py"
      content: |
        1. Add the following two methods to GTachApplication, immediately after
           _clear_update_probation():

            def _finish_startup_logging(self) -> None:
                """Detach start.log after startup is complete.

                Raises the start handler threshold to suppress further writes.
                Startup records are retained in the file.
                """
                try:
                    import logging
                    import sys
                    if sys.platform.startswith('linux'):
                        from . import main as _main
                        if _main._start_handler is not None:
                            self.logger.info("Startup complete — start.log closed")
                            _main._start_handler.setLevel(logging.CRITICAL + 1)
                except Exception as e:
                    self.logger.debug(f"Could not finish startup logging: {e}")

            def toggle_debug_logging(self, enable: bool) -> None:
                """Activate or suppress debug.log at runtime.

                Args:
                    enable: True to start writing to debug.log; False to suppress.
                """
                try:
                    import logging
                    import sys
                    if not sys.platform.startswith('linux'):
                        return
                    from . import main as _main
                    if _main._debug_handler is None:
                        return
                    if enable:
                        _main._debug_handler.setLevel(logging.DEBUG)
                        self.logger.info("Debug logging enabled")
                    else:
                        _main._debug_handler.setLevel(logging.CRITICAL + 1)
                        self.logger.info("Debug logging disabled")
                except Exception as e:
                    self.logger.debug(f"Could not toggle debug logging: {e}")

        2. In GTachApplication.start(), at the end of the try block, add this
           call immediately after self._clear_update_probation():

               self._finish_startup_logging()

success_criteria:
  - "python -m py_compile src/gtach/main.py passes."
  - "python -m py_compile src/gtach/app.py passes."
  - "_start_handler and _debug_handler exist at module scope in main.py."
  - "setup_logging() on Linux opens both files and sets initial levels."
  - "setup_logging() on non-Linux preserves existing basicConfig/NullHandler."
  - "GTachApplication defines _finish_startup_logging() and toggle_debug_logging()."
  - "start() calls _finish_startup_logging() after _clear_update_probation()."

notes: >
  Executor is Claude Code (no AEL). Invoke from the project root:
  implement workspace/prompt/prompt-bd8f95b7-app-owned-two-file-logging.md
```

```yaml
tactical_brief: |
  Executor: Claude Code. Implement change-bd8f95b7: two-file app-owned logging.

  FILE 1: src/gtach/main.py

  Add two module-level references at module scope (before setup_logging):
      _start_handler: logging.Handler = None
      _debug_handler: logging.Handler = None

  Add import at top of file:
      from logging.handlers import RotatingFileHandler

  Replace the entire setup_logging() function body with:

      global _start_handler, _debug_handler

      if not sys.platform.startswith('linux'):
          if debug:
              logging.basicConfig(
                  level=logging.DEBUG,
                  format='%(asctime)s %(name)s %(levelname)s %(message)s'
              )
          else:
              logging.getLogger().addHandler(logging.NullHandler())
          return

      _LOG_FORMAT = '%(asctime)s,%(msecs)03d %(name)s %(levelname)s %(message)s'
      formatter = logging.Formatter(_LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
      root = logging.getLogger()
      root.setLevel(logging.DEBUG)

      try:
          _start_handler = logging.FileHandler('/opt/gtach/start.log', mode='w', encoding='utf-8')
          _start_handler.setLevel(logging.DEBUG)
          _start_handler.setFormatter(formatter)
          root.addHandler(_start_handler)
      except OSError as e:
          print(f'[gtach] WARNING: could not open start.log: {e}', file=sys.stderr)

      try:
          _debug_handler = RotatingFileHandler(
              '/opt/gtach/debug.log', mode='w',
              maxBytes=100 * 1024 * 1024, backupCount=0, encoding='utf-8'
          )
          _debug_handler.setLevel(logging.CRITICAL + 1)
          _debug_handler.setFormatter(formatter)
          root.addHandler(_debug_handler)
      except OSError as e:
          print(f'[gtach] WARNING: could not open debug.log: {e}', file=sys.stderr)

      if debug and _debug_handler is not None:
          _debug_handler.setLevel(logging.DEBUG)

  FILE 2: src/gtach/app.py

  Add two methods to GTachApplication immediately after _clear_update_probation():

      def _finish_startup_logging(self) -> None:
          """Detach start.log after startup is complete."""
          try:
              import logging, sys
              if sys.platform.startswith('linux'):
                  from . import main as _main
                  if _main._start_handler is not None:
                      self.logger.info("Startup complete — start.log closed")
                      _main._start_handler.setLevel(logging.CRITICAL + 1)
          except Exception as e:
              self.logger.debug(f"Could not finish startup logging: {e}")

      def toggle_debug_logging(self, enable: bool) -> None:
          """Activate or suppress debug.log at runtime."""
          try:
              import logging, sys
              if not sys.platform.startswith('linux'):
                  return
              from . import main as _main
              if _main._debug_handler is None:
                  return
              if enable:
                  _main._debug_handler.setLevel(logging.DEBUG)
                  self.logger.info("Debug logging enabled")
              else:
                  _main._debug_handler.setLevel(logging.CRITICAL + 1)
                  self.logger.info("Debug logging disabled")
          except Exception as e:
              self.logger.debug(f"Could not toggle debug logging: {e}")

  In start(), add after self._clear_update_probation():
      self._finish_startup_logging()

  Verify: python -m py_compile src/gtach/main.py && python -m py_compile src/gtach/app.py
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-12 | Initial prompt document. |

---

Copyright (c) 2026 William Watson. MIT License.
