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
- Deploy: `bin/deploy.sh` (or `bin/build.sh` → `scp` → `bin/install.sh`); systemd service at `root@gtach.local`

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Governance

**Prime directive**: Do not create, add, remove, or change source code or documents
unless explicitly requested by the T03 prompt task.

- Governance: `ai/governance/software-engineering/governance.md` (AI-G&O governance 11.0)
- Workflow (`src/` changes only): T06 issue → T07 change → T03 prompt, sharing one 8-hex UUID
- Trivial exemption (P04.12): single function, ≤20 line delta, no interface change,
  unambiguous, human-approved → git commit is the sole audit record
- Active docs: `ai/workspace/{issues,change,prompt}/`; completed move to `closed/` subdirs

Task invocation:

```text
Implement ai/workspace/prompt/prompt-<uuid>-<name>.md and close the prompt T-Doc when finished. Leave the issue and change T-Docs active pending test results. Then, once you are finished, write a report of what you have done in ai/workspace/report/report-<uuid>-<name>.md.
```

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Technology Stack

| Concern | Implementation |
|---|---|
| Display / events | pygame (SDL2); framebuffer renderer (`SDL_VIDEODRIVER=dummy`, `/dev/fb0` mmap) on Pi |
| Serial transport | pyserial |
| Configuration | PyYAML — single flat config.yaml under GTACH_HOME (default /opt/gtach) |
| CLI | argparse |
| Threading | stdlib `threading` — all shared state behind `threading.Lock` |
| Logging | `start.log` (truncated at boot, always written) + `debug.log` (`RotatingFileHandler`, suppressed unless `--debug`) + error.log (WARNING and above, always on, 1 MB × 5, size rotation only) |
| Hardware (Pi) | `RPi.GPIO`, `hyperpixel2r` (`.[pi]` extra; conditional import) |

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Core Development Rules

1. **Package management**: pip only. Editable install: `pip install -e .[dev]`. Do not introduce `uv` or `poetry`.
2. **Code quality**: type hints on all public interfaces; `mypy` clean (strict settings in `pyproject.toml`);
   Google-style docstrings on public APIs; small, focused functions; follow existing patterns.
3. **Testing**: `pytest` (`pytest-cov` configured). New features require tests; bug fixes require regression
   tests; cover edge cases and error paths.
4. **Concurrency**: stdlib `threading` only; guard all shared state with `threading.Lock`. No async framework.
5. **Hardware dependencies**: conditional import (`try/except ImportError`) for `RPi.GPIO` and `hyperpixel2r`.
6. **Error handling**: log unexpected exceptions with `logger.error(msg, exc_info=True)`.
7. **Naming / style**: PEP 8 — `snake_case` functions/variables, `PascalCase` classes,
   `UPPER_SNAKE_CASE` constants; f-strings for formatting.
8. **Locks**: never call out while holding a lock — no callbacks, no calls into another component that may take a lock, no blocking I/O. Snapshot under the lock, act after releasing it (issue-e9216e17). A lock that exists to serialise access to one file may be held across that file's read or write (DeviceStore, change-453f0a80); it must still never be held across a callback or a call into another component.

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

- Format: `black`, `isort` (profile `black`). Lint: `flake8`. Type: `mypy` (strict settings; see `pyproject.toml`).
- Line length: 88 for black, isort and flake8 (`.flake8`).
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

# Run with simulation transport (choices: tcp, serial, rfcomm, simtcp, simbt)
gtach --transport simbt --debug

# Deploy to the Pi (full) or stage the wheel only
./bin/deploy.sh
./bin/deploy.sh --stage
```

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Key Paths

```
src/gtach/
  main.py           entry point, argparse CLI
  app.py            application controller
  comm/             transports (tcp, serial, rfcomm, simtcp, simbt), OBD, DeviceStore
  core/             ThreadManager, WatchdogMonitor
  display/          DisplayManager, rendering, touch, setup
  utils/            ConfigStore, gtach_home, PlatformDetector
ai/workspace/
  design/           design documents
  change/           active change documents
  prompt/           T03 task prompts
  issues/           issue documents
  report/           implementation reports
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-24 | Initial draft. Adapted Core Development Rules, Development Philosophy, and Coding Best Practices from `ai/doc/python-CLAUDE.md`; aligned with GTach toolchain (pip, pytest, mypy, black/isort/flake8), governance, and Linux-only runtime target. |
| 1.0 | 2026-09-23 | Merged the root `CLAUDE.md` and `ai/doc/CLAUDE.md` into this file. Kept the full task-invocation text, the error-handling rule and the deploy commands from the root version. Governance numbering updated to 10.5 (T06 issue, T07 change, T03 prompt, P04.12). Removed the non-existent `--macos` flag and the `obd` conditional import. |
| 1.1 | 2026-09-29 | Governance path updated for the AI-G&O 11.0 layout (`ai/governance/software-engineering/governance.md`). |
| 1.2 | 2026-10-07 | Logging row: error.log (change-269871a0) |
| 1.3 | 2026-10-07 | Rule 8: no call-outs under a lock (change-e9216e17) |
| 1.4 | 2026-10-07 | Configuration: single ConfigStore under GTACH_HOME (change-5fbff586) |
| 1.5 | 2026-10-07 | Hardware row: RPi.GPIO and hyperpixel2r in the .[pi] extra (change-52653cd6) |
| 1.6 | 2026-10-07 | Rule 8: file-serialising lock may span that file's I/O (change-4005360c) |
| 1.7 | 2026-10-07 | §7 line length: 88 for black, isort and flake8 (change-e4ee50fd) |
| 1.8 | 2026-10-07 | Rule 5: hyperpixel2r replaces gpiozero (removed by change-52653cd6) |

---

Copyright (c) 2026 William Watson. MIT License.
