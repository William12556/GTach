Created: 2026 June 24

# GTach — Claude Code Context

---

## Table of Contents

[1.0 Project](<#1.0 project>)
[2.0 Governance](<#2.0 governance>)
[3.0 Technology Stack](<#3.0 technology stack>)
[4.0 Core Development Rules](<#4.0 core development rules>)
[5.0 Development Philosophy](<#5.0 development philosophy>)
[6.0 Coding Best Practices](<#6.0 coding best practices>)
[7.0 Formatting and Type Checking](<#7.0 formatting and type checking>)
[8.0 Common Commands](<#8.0 common commands>)
[9.0 Key Paths](<#9.0 key paths>)
[Version History](<#version history>)

---

## 1.0 Project

Real-time automotive RPM tachometer. Python package (`gtach`).

- Runtime target: Raspberry Pi Zero 2W, Linux only.
- Build / development host: Mac Mini (Apple Silicon) — builds and deploys; not a runtime target.
- Source: `src/gtach/` — subpackages: `comm`, `core`, `display`, `utils`
- Tests: `tests/` (pytest)
- Entry point: `gtach` → `src/gtach/main.py` (argparse CLI)
- Python: 3.9+  |  dev venv: `venv/`  |  Pi venv: `/opt/gtach/venv`
- Install: `pip install -e .[dev]`  (Pi adds `.[pi]`)
- Deploy: `bin/build.sh` → `scp` → `bin/install.sh`; systemd service at `root@gtach.local`

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Governance

**Prime directive**: Do not create, add, remove, or change source code or documents
unless explicitly requested by the T04 prompt task.

- Governance: `ai/governance.md`
- Workflow (`src/` changes only): T03 issue → T02 change → T04 prompt, sharing one 8-hex UUID
- Trivial exemption (P03 §1.4.12): single function, ≤20 line delta, no interface change,
  unambiguous, human-approved → git commit is the sole audit record
- Active docs: `ai/workspace/{issues,change,prompt}/`; completed move to `closed/` subdirs
- Task invocation: `implement ai/workspace/prompt/prompt-<uuid>-<name>.md`
- Backup files (`manager_backup.py`, `setup_original_backup.py`) are excluded from all changes and audits

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Technology Stack

| Concern | Implementation |
|---|---|
| Display / events | pygame (SDL2); framebuffer renderer (`SDL_VIDEODRIVER=dummy`, `/dev/fb0` mmap) on Pi |
| Serial transport | pyserial |
| Configuration | PyYAML |
| CLI | argparse |
| Threading | stdlib `threading` — all shared state behind `threading.Lock` |
| Logging | `start.log` (truncated at boot, always written) + `debug.log` (`RotatingFileHandler`, suppressed unless `--debug`) |
| Hardware (Pi) | `RPi.GPIO`, `gpiozero` (`.[pi]` extra; conditional import) |

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Core Development Rules

1. **Package management**: pip only. Editable install: `pip install -e .[dev]`. Do not introduce `uv` or `poetry`.
2. **Code quality**: type hints on all public interfaces; `mypy` clean (strict config in `pyproject.toml`);
   Google-style docstrings on public APIs; small, focused functions; follow existing patterns.
3. **Testing**: `pytest` (`pytest-cov` configured). New features require tests; bug fixes require regression
   tests; cover edge cases and error paths.
4. **Concurrency**: stdlib `threading` only; guard all shared state with `threading.Lock`. No async framework.
5. **Hardware dependencies**: conditional import (`try/except ImportError`) for `RPi.GPIO`, `gpiozero`, `obd`.
6. **Naming / style**: PEP 8 — `snake_case` functions/variables, `PascalCase` classes,
   `UPPER_SNAKE_CASE` constants; f-strings for formatting.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Development Philosophy

- **Simplicity**: Write simple, straightforward code.
- **Readability**: Make code easy to understand.
- **Performance**: Consider performance without sacrificing readability.
- **Maintainability**: Write code that is easy to update.
- **Testability**: Ensure code is testable.
- **Reusability**: Create reusable components, subordinate to minimal-change scope.
- **Less code = less debt**: Minimize code footprint.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Coding Best Practices

- **Early returns**: Avoid nested conditions.
- **Descriptive names**: Clear variable and function names.
- **Constants over magic values**: Name fixed values.
- **DRY**: Do not repeat yourself.
- **Minimal changes**: Modify only code related to the task at hand.
- **Function ordering**: Define composing functions before their components.
- **TODO comments**: Mark issues in existing code with a `TODO:` prefix.
- **Build iteratively**: Start minimal and verify before adding complexity.
- **Test with realistic inputs**: Use `SimTransport` and the ELM327 emulator.
- **Clean logic**: Keep core logic clean; push implementation details to the edges.
- **Caveat**: Prefer functional or immutable style only where it improves clarity. GTach managers are
  stateful and lock-guarded; correctness of shared-state access takes precedence over functional form.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Formatting and Type Checking

- Format: `black`, `isort` (profile `black`). Lint: `flake8`. Type: `mypy` (strict; see `pyproject.toml`).
- Line length: PEP 8 (79). Note: `pyproject.toml` pins `black`/`isort` to 88, which diverges from PEP 8;
  reconcile before relying on either limit.
- Fix order on failures: formatting → type errors → linting.
- Optional handling: explicit `None` checks; narrow types before use.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Common Commands

```bash
# Activate dev venv
source venv/bin/activate

# Install (Pi adds .[pi])
pip install -e .[dev]

# Run tests
pytest

# Format, lint, type-check
black . && isort .
flake8 .
mypy src/

# Syntax check a file
python -c "import ast; ast.parse(open('src/gtach/path/to/file.py').read())"

# Run with simulation transport
gtach --transport simbt --debug
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Key Paths

```
src/gtach/
  main.py           entry point, argparse CLI
  app.py            application controller
  comm/             transports (rfcomm, serial, tcp, sim variants), OBD, DeviceStore
  core/             ThreadManager, WatchdogMonitor
  display/          DisplayManager, rendering, touch, setup
  utils/            ConfigManager, PlatformDetector
ai/workspace/
  design/           design documents
  change/           active change documents
  prompt/           T04 task prompts
  issues/           issue documents
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-24 | Initial draft. Adapted Core Development Rules, Development Philosophy, and Coding Best Practices from `ai/doc/python-CLAUDE.md`; aligned with GTach toolchain (pip, pytest, mypy, black/isort/flake8), governance, and Linux-only runtime target. |

---

Copyright (c) 2026 William Watson. MIT License.
