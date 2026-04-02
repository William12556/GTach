# GTach — Claude Code Context

## Project

Real-time automotive RPM tachometer. Python package (gtach), Raspberry Pi Zero 2W
production target, macOS Apple Silicon development platform.

- Source: `src/gtach/` — subpackages: `comm`, `core`, `display`, `utils`
- Tests: `tests/` (pytest)
- Entry point: `gtach` → `src/gtach/main.py`
- Python: 3.9+  |  venv: `venv/`  |  Install: `pip install -e .[dev]`

## Governance

**Prime directive**: Do not create, add, remove, or change source code or documents
unless explicitly requested by the T04 prompt task.

- Governance: `ai/governance.md`
- Design docs: `workspace/design/`
- Active changes: `workspace/change/`
- Active prompts: `workspace/prompt/`
- Task invocation: `implement workspace/prompt/prompt-<uuid>-<name>.md`

## Technology Stack

| Concern | Implementation |
|---|---|
| Display / events | pygame (SDL2) |
| Serial transport | pyserial |
| Configuration | PyYAML |
| Threading | stdlib `threading` — all shared state behind `threading.Lock` |
| Logging | `NullHandler` in production; `--debug` flag enables DEBUG level |

## Code Standards

- PEP 8; type hints on all public interfaces
- Google-style docstrings
- Conditional imports for hardware dependencies (`try/except ImportError`)
- Platform detection: `platform.system() == 'Darwin'` for macOS guards
- Error handling: `logger.error(msg, exc_info=True)` on unexpected exceptions

## Common Commands

```bash
# Activate venv
source venv/bin/activate

# Run tests
pytest tests/

# Syntax check a file
python -c "import ast; ast.parse(open('src/gtach/path/to/file.py').read())"

# Run on macOS (dev mode)
python -m gtach --macos --debug
```

## Key Paths

```
src/gtach/
  main.py           entry point, CLI args
  app.py            application controller
  comm/             transport (RFCOMMTransport, SerialTransport, TCPTransport), OBD, DeviceStore
  core/             ThreadManager, WatchdogMonitor
  display/          DisplayManager, rendering, touch, setup
  utils/            ConfigManager, PlatformDetector
workspace/
  design/           T1/T2/T3 design documents
  change/           active change documents
  prompt/           T04 task prompts
  issues/           issue documents
```
