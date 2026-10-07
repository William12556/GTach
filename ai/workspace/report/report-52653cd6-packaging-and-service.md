Created: 2026 October 07

# Report: Packaging, Service Unit and Deployment Scripts

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Files Changed](<#2. files changed>)
3. [Tests Added and Result](<#3. tests added and result>)
4. [Success Criteria](<#4. success criteria>)
5. [Deviations](<#5. deviations>)
6. [On-Device Verification Outstanding](<#6. on-device verification outstanding>)
7. [Version History](<#version history>)

---

## 1. Summary

prompt-52653cd6 (change-52653cd6, issue-52653cd6; audit-36b6ea95 G01, G02, G03, G04, G06, G08, E05) was implemented in commit `f9273e05eca60a5def61c5ecae60c4b46ba1c035`.

- **EDIT A, pyproject.toml:**
  - the `pi` extra is RPi.GPIO and hyperpixel2r; gpiozero and click are removed;
  - the description, keywords, URLs (William12556/GTach) and Python 3.12/3.13 classifiers are current;
  - the mypy override modules are RPi, hyperpixel2r and bluetooth.
- **EDIT B, version source:** `__version__` comes from `importlib.metadata`, falling back to `0+unknown`. build.sh no longer rewrites `__init__.py`.
- **EDIT C, touch fallback:** the mock-touch fallback messages log at ERROR on a Raspberry Pi and at INFO elsewhere. INFO is also used if detection fails.
- **EDIT D, dependency checks:**
  - the pybluez and requests checks are removed;
  - psutil is added as a required dependency;
  - version lookup uses `importlib.metadata` only; the pkg_resources and `pip show` fallbacks are removed.
- **EDIT E, gtach.service:**
  - start limits 5 starts in 120 s;
  - `Wants=bluetooth.service`;
  - `TimeoutStopSec=30`;
  - NoNewPrivileges, PrivateTmp, ProtectHome and ProtectSystem=full, each with a comment.
- **EDITS F to L, scripts:**
  - install.sh installs `[pi]` with the piwheels index;
  - deploy.sh copies everything first, then stops the service, installs and reboots, with no start before the reboot;
  - pull_logs.sh pulls into a temporary directory with one `*.log*` glob and replaces `logs/` only on success;
  - gen_splash.py takes `--font` or `$GTACH_SPLASH_FONT`, with a clear error for a missing file;
  - release.sh refuses unless HEAD is on origin and passes `--target`;
  - gtach-preflight.sh runs `pip check` after every install through `install_and_check()`;
  - gtach-audit-checks.sh describes ConfigStore and DeviceStore under GTACH_HOME.
- **EDIT M, CLAUDE.md:** §3 Hardware row; Version History 1.5.

[Return to Table of Contents](<#table of contents>)

---

## 2. Files Changed

| File | Change |
|---|---|
| `pyproject.toml` | EDIT A. |
| `src/gtach/__init__.py`, `bin/build.sh` | EDIT B. |
| `src/gtach/display/touch_interface.py` | EDIT C: `_mock_fallback_log()`. |
| `src/gtach/utils/dependencies.py` | EDIT D. |
| `bin/gtach.service` | EDIT E. |
| `bin/install.sh`, `bin/deploy.sh`, `bin/pull_logs.sh`, `bin/gen_splash.py`, `bin/release.sh`, `bin/gtach-preflight.sh`, `bin/gtach-audit-checks.sh` | EDITS F to L. |
| `CLAUDE.md` | EDIT M. |
| `tests/test_packaging_and_scripts.py` | New: 27 tests. |

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests Added and Result

`tests/test_packaging_and_scripts.py` has 27 tests, covering every change test case and the edge case:

- **pyproject:** the pi extra and dependencies; the URLs.
- **Version source:**
  - `__init__.py` has no literal release number;
  - with metadata missing, `0+unknown` (module reloaded);
  - build.sh does not write `__init__.py`.
- **Mock fallback level:** ERROR on a Pi, INFO elsewhere, INFO when detection fails.
- **gtach.service:** eight directives present.
- **Scripts:**
  - `bash -n` on the seven edited scripts;
  - `gen_splash.py` compiles;
  - install.sh uses `[pi]`;
  - deploy.sh stops only after the last `scp` and has no `systemctl start`;
  - preflight runs `pip check`.

The pull_logs.sh edge case (no rotated logs) is covered by design: the single `*.log*` glob matches the live logs.

pytest after this commit: 426 passed (399 before the commit).

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | How checked | Result |
|---|---|---|
| pi extra has hyperpixel2r, no gpiozero; no click; URLs point to William12556/GTach | `TestPyproject` | Pass |
| `__init__.py` has no literal version; build.sh does not write it | `TestVersion` | Pass |
| gtach.service has TimeoutStopSec=30, StartLimitBurst=5, StartLimitIntervalSec=120, Wants=bluetooth.service and the four hardening directives | `TestServiceUnit` | Pass |
| install.sh installs with [pi]; deploy.sh stops the service only after all copies | `TestScripts` | Pass |
| gtach-preflight.sh runs pip check after installs | `test_preflight_runs_pip_check`; code review | Pass |
| `bash -n` passes for every bin/*.sh | Ran it for all of bin/*.sh | Pass |
| `pytest tests/` passes | Full run | 426 passed |

[Return to Table of Contents](<#table of contents>)

---

## 5. Deviations

- **hyperpixel2r check:** the dependency validator already had a hyperpixel2r check, Pi-specific, which reports ERROR when missing on a Pi. It was kept as it was, rather than downgraded to optional, because a missing touch library on a Pi is the failure EDIT C makes loud.
- **release.sh:** the check follows the prompt's logic, HEAD contained in any `origin/` branch, rather than the change's wording "origin's default branch".
- **gpiozero mention:** CLAUDE.md §4 rule 5 still names gpiozero. EDIT M covers only the §3 Hardware row.
- **Test regex:** the literal-version test matches a dotted release number, so the `0+unknown` fallback string is not mistaken for one.

[Return to Table of Contents](<#table of contents>)

---

## 6. On-Device Verification Outstanding

After `./bin/deploy.sh`:

1. The service starts.
2. Touch works.
3. `systemd-analyze security gtach` lists the new directives.
4. `time systemctl stop gtach` is under 30 s.
5. error.log has no mock-fallback ERROR.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial implementation report for prompt-52653cd6. |

---

Copyright (c) 2026 William Watson. MIT License.
