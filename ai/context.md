Created: 2026 June 17

# Project Context

---

## 1.0 Project

**Name:** GTach
**Description:** Retro-styled real-time RPM tachometer reading an ELM327 OBD-II Bluetooth adapter.

**Technology stack:** Python 3.9+ | pygame (SDL2), pyserial, PyYAML, click; Pi extras: RPi.GPIO, gpiozero
**Target platform:** Raspberry Pi Zero 2W with Pimoroni HyperPixel Round 480×480 (production); macOS Apple Silicon (development)

---

## 2.0 Commands

| Action | Command |
|---|---|
| Install | `python3 -m venv venv && source venv/bin/activate && pip install -e .[dev]` |
| Test | `pytest tests/` |
| Lint | `flake8 src/`; format with `black src/ tests/` and `isort src/ tests/` |
| Run (dev) | `python -m gtach --macos --debug` |
| Build | `./bin/build.sh` |
| Deploy | `./bin/deploy.sh` (full) or `./bin/deploy.sh --stage` (wheel only); Pi at `root@gtach.local` |

---

## 3.0 Code Style

- PEP 8; black and isort (profile black), line length 88; type hints on all public interfaces
- Google-style docstrings
- Hardware dependencies imported conditionally (`try/except ImportError`); macOS guarded by `platform.system() == 'Darwin'`
- Shared state behind `threading.Lock`; unexpected exceptions logged with `logger.error(msg, exc_info=True)`

---

## 4.0 Repository Conventions

**Branches:** `main` only; no feature branches in use.
**Commits:** conventional commits (`feat:`, `fix:`, `docs:`, `chore:`); fixes cite the T-Doc UUID, e.g. `fix: … (6d30b912)`.

---

## 5.0 Governance

| Artifact | Location |
|---|---|
| Governance | `ai/governance.md` |
| Designs | `ai/workspace/design/` |
| Changes | `ai/workspace/change/` |
| Prompts | `ai/workspace/prompt/` |
| Issues | `ai/workspace/issues/` |
| Reports | `ai/workspace/report/` |

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-06-17 | Initial template |
| 1.0 | 2026-09-23 | Project context filled in (GTach) |

---

Copyright (c) 2026 William Watson. MIT License.
