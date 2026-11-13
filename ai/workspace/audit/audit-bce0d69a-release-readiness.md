# Release-Readiness Audit — GTach v1.0.0 Release Candidate (audit-bce0d69a)

Created: 2026 November 13

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 Scope and Method](#20-scope-and-method)
- [3.0 Findings](#30-findings)
- [4.0 Dispositions](#40-dispositions)
- [5.0 Reviewed Without Finding](#50-reviewed-without-finding)
- [6.0 Recommendations](#60-recommendations)
- [7.0 Closure](#70-closure)
- [Version History](#version-history)

---

## 1.0 Summary

- **Mode:** strategic (governance P02.9.1), static review and local execution. No device, display panel, Bluetooth adapter or vehicle was used.
- **Authority:** `proposal-f8d0064b` §4.7 (WP7). Severity rule D11 applies.
- **Audited commit:** `d232eb3` on branch `claude/gtach-v1-release-run-g0106d`.
- **Result:** 13 findings. One high finding; it concerns the release-candidate version chosen by decision D1.

| Severity | Count |
|---|---|
| Critical | 0 |
| High | 1 |
| Medium | 3 |
| Low | 9 |
| **Total** | **13** |

- **H01:** `utils/updater.py` parses only purely numeric versions. With the version `1.0.0rc1` installed, the update check finds nothing, so a staged `1.0.0` wheel cannot be installed from the OPTIONS screen; a staged `1.0.0rc1` wheel is never offered to a `0.5.0` installation either.
- **Classification:** each finding is marked *confirmed* (reproduced or evident from the files) or *inferred* (depends on behaviour not exercised here).

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Scope and Method

### 2.1 Scope

`src/gtach/`, `bin/`, `pyproject.toml`, `README.md`, `docs/`, `CLAUDE.md`, `ai/context.md`, and the repository root files that a release carries. Criteria: defects, release blockers, packaging faults, and documentation that contradicts the source. Style, refactoring and feature ideas are excluded.

### 2.2 Method

- **Source:** `src/gtach/` was audited file by file at commit `94ce959b` by `audit-71ab3751` (closed 2026-11-12, 43 findings remediated) and by the scheduled audit `audit-d54d91ad`. This audit therefore read in full the modules changed since then or central to the release path (`main.py`, `app.py`, `core/`, `comm/transport.py`, `comm/obd.py`, `comm/rfcomm.py`, `comm/tcp_transport.py`, `comm/serial_transport.py`, `comm/models.py`, `comm/device_store.py`, `utils/updater.py`, `utils/pi_reset.py`, `utils/terminal.py`, `utils/home.py`, `utils/config.py`, `display/touch.py`), read the frame loop, link-state and engine-off paths of `display/manager.py`, and read the remaining modules at interface level during the design refresh (WP4).
- **Scripts and documents:** `bin/build.sh`, `bin/deploy.sh`, `bin/install.sh`, `bin/pi-install.sh`, `bin/release.sh`, `bin/gtach-preflight.sh`, `bin/gtach.service`, `README.md`, `docs/GTach_cli_cmds.md`, `docs/pi-setup.md` (scanned), `CLAUDE.md`, `ai/context.md`, `config/config.example.yaml` were compared with the source.
- **Release-specific checks:** behaviour of every version consumer with the D1 version `1.0.0rc1` (update check, install scripts, release script, splash screen).

### 2.3 Tooling

| Tool | Result |
|---|---|
| `pytest tests/` (Python 3.13.18 and 3.9.25) | 780 passed on both |
| `python -m mypy src/` (mypy 1.20.2, target 3.9) | No issues in 60 source files |
| `flake8 src`, `black --check src`, `isort --check src` | No finding in `src/` |
| AST check | No bare `except`, no mutable default argument, no `error`/`critical` call without `exc_info` in a broad handler |
| Reproduction of H01 | `_parse_version_str("1.0.0rc1")` returns `None` |
| Text measurement | `v1.0.0rc1` at the splash version font is 251 px wide; the chord at its position is 387 px |

### 2.4 Limitations

- Nothing was verified on the Pi. The Python 3.9 interpreter used here has no `socket.AF_BLUETOOTH`, so the Bluetooth paths ran only through test doubles.
- `bin/` scripts were read, not executed (they act on the Pi or on GitHub).
- The modules not read in full rely on `audit-71ab3751` and its remediation.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Findings

```yaml
# T08 Audit Template v1.0 - YAML Format
audit_info:
  id: "audit-bce0d69a"
  title: "Release-readiness audit for the GTach v1.0.0 release candidate"
  date: "2026-11-13"
  mode: "strategic"
  status: "in_progress"
  auditor: "planner (Claude Code session, proposal-f8d0064b)"

scope:
  target: "src/gtach/, bin/, pyproject.toml, README.md, docs/, CLAUDE.md, ai/context.md @ d232eb3"
  criteria:
    - "defects"
    - "release_blockers"
    - "packaging_faults"
    - "documentation_contradicting_source"
  exclusions:
    - "style, refactoring, feature ideas"
    - "tests/ (existing lint debt is an ai/task.md row, D7)"
    - "ai/ framework files"
    - "display geometry and font sizing (device measurement)"

findings:
  critical: []
  high:
    - location: "src/gtach/utils/updater.py:27-31 (_parse_version_str), 34-41, 44-52, 66-97"
      description: >-
        [H01] (confirmed) _parse_version_str converts each dot-separated
        part with int(), so any version with a pre-release, post-release
        or development segment ('1.0.0rc1', '1.0.0.dev1') yields None.
        Consequences with the D1 version 1.0.0rc1: (a) installed
        1.0.0rc1 -> get_installed_version() is None ->
        find_available_update() returns None, so 'Check for updates'
        reports 'No update found' for a staged 1.0.0 wheel; the planned
        step from the release candidate to 1.0.0 cannot use
        deploy.sh --stage; (b) a staged gtach-1.0.0rc1 wheel is skipped
        on a 0.5.0 installation, with no log record. No error is shown
        in either case. Workaround: full deploy (./bin/deploy.sh).
      issue_ref: "issue-c41037ea"
  medium:
    - location: "repository root; DISCLAIMER.md:39; source file headers"
      description: >-
        [M01] (confirmed) No LICENSE file exists. pyproject.toml declares
        the MIT license, DISCLAIMER.md and the header of the source
        files refer to 'the LICENSE file in the project root', and the
        MIT terms require the license text to accompany copies. The
        wheel and sdist therefore carry no license text.
    - location: "bin/release.sh:84-91"
      description: >-
        [M02] (confirmed by reading) release.sh always passes --latest
        to 'gh release create' and never --prerelease. Run with a
        pre-release version in pyproject.toml, it would publish the
        release candidate as the latest release, which
        bin/pi-install.sh resolves through the GitHub 'releases/latest'
        endpoint and installs on new devices.
    - location: "ai/context.md:13, 36"
      description: >-
        [M03] (confirmed) The worker context file names 'click' as the
        CLI library and 'gpiozero' as a Pi extra and conditional
        import. The source uses argparse; the Pi extras are RPi.GPIO
        and hyperpixel2r (pyproject.toml); psutil is a dependency and
        is not listed. CLAUDE.md is correct on all three.
  low:
    - location: "src/gtach/comm/obd.py:343-366 (_request_rpm)"
      description: >-
        [L01] (confirmed) A reply that starts with '41' and leaves an
        odd number of hexadecimal characters after filtering (for
        example '410C0FA0' followed by 'CAN ERROR', whose letters C, A
        and E are hexadecimal) makes bytes.fromhex raise ValueError.
        The broad handler logs 'RPM request error' at ERROR with a
        traceback for every such poll (up to 50 per second). No wrong
        value is shown; the sample is dropped.
    - location: "README.md §4.2, §5.2, §6.1"
      description: >-
        [L02] (confirmed) --config default is given as 'Auto-detected';
        it is GTACH_HOME/config.yaml. §5.2 omits error.log and
        stacks.log. §4.2 says the full deploy restarts the service; it
        reboots the Pi.
    - location: "docs/GTach_cli_cmds.md:5-8, 25, 97-100"
      description: >-
        [L03] (confirmed) 'Transfer deploy files only' names
        'gtach.service' without the bin/ directory, so the command
        fails from the repository root. The full deploy is described as
        restarting; it reboots. The log paragraph omits error.log.
    - location: "src/devop.md"
      description: >-
        [L04] (confirmed) A notes file inside src/ refers to version
        0.2.2 and to log files that no longer exist. It is not packaged.
    - location: "pyproject.toml:6-8, 21-33"
      description: >-
        [L05] (confirmed) build-system.requires lists 'build', which is
        a build front end and is not needed by the setuptools back end;
        every isolated build downloads it. Separately, the classifier
        'Development Status :: 4 - Beta' will not match a 1.0.0 release
        (owner decision).
    - location: "src/gtach/display/manager.py:328, 2405, 2428, 2519"
      description: >-
        [L06] (confirmed) Three comments cite 'issue-<pending>', and
        the long-press handler logs 'Double tap handling error'. No
        functional effect.
    - location: "src/gtach/utils/updater.py:24-25; src/gtach/app.py (_clear_update_probation); src/gtach/utils/stack_dump.py"
      description: >-
        [L07] (confirmed) The updates directory, the probation marker
        and the stack-dump default path are fixed under /opt/gtach and
        do not follow GTACH_HOME. This matches bin/gtach-preflight.sh,
        which is also fixed; a development run with GTACH_HOME set
        still reads /opt/gtach/updates.
    - location: "tests/"
      description: >-
        [L08] (confirmed) No test module covers utils/ack_state.py, and
        the updater functions are covered only for the staging marker.
    - location: "bin/build.sh:44-56; README.md §3.1; DISCLAIMER.md"
      description: >-
        [L09] (confirmed) build.sh accepts only X.Y.Z at its version
        prompt, so a pre-release version must be set in pyproject.toml
        by hand and kept with Enter. README §3.1 'Updates' installs the
        head of main, not the latest release. DISCLAIMER.md uses
        angle-bracket anchors that do not resolve on GitHub.

metrics:
  items_audited: 86
  findings_total: 13
  findings_by_severity:
    critical: 0
    high: 1
    medium: 3
    low: 9

recommendations:
  - "H01: order versions by a PEP 440 aware key (triple c41037ea)."
  - "M01: add the MIT LICENSE file; owner confirms the copyright line."
  - "M02: publish a pre-release version with --prerelease and without --latest."
  - "M03, L02, L03: correct the documents."
  - "L01: reject an odd-length reply before decoding (P04.12)."
  - "Device session: verify the update path from 1.0.0rc1 to 1.0.0 with a staged wheel."

traceability:
  design_refs:
    - "design-9a1f3c7e-domain_utils (§4.3 Updater)"
    - "design-f5a6b7c8-component_comm_obd_protocol (§4.3)"
  issue_refs:
    - "issue-c41037ea"
  related_audits:
    - audit_ref: "audit-71ab3751"
      relationship: "related"
    - audit_ref: "audit-d54d91ad"
      relationship: "related"

notes: >
  items_audited counts 60 Python files, 12 scripts and service files in
  bin/, pyproject.toml, 7 documents and the repository root files.

version_history:
  - version: "1.0"
    date: "2026-11-13"
    changes:
      - "Initial audit report."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t08_audit"
```

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Dispositions

Severity rule D11: critical and high are fixed through a triple; medium and low are fixed when trivial (P04.12) or document-only, otherwise deferred to `ai/task.md`.

| Finding | Disposition | Record |
|---|---|---|
| H01 | Fixed | DISPOSITION-H01 |
| M01 | Fixed (document) | DISPOSITION-M01 |
| M02 | Fixed (`bin/`, exempt from the triple) | DISPOSITION-M02 |
| M03 | Fixed (document) | DISPOSITION-M03 |
| L01 | Fixed (P04.12 trivial exemption) | DISPOSITION-L01 |
| L02 | Fixed (document) | DISPOSITION-L02 |
| L03 | Fixed (document) | DISPOSITION-L03 |
| L04 | Deferred — after 1.0; owner decides whether to delete or move the file | `ai/task.md` |
| L05 | `build` removed from `build-system.requires` (fixed); classifier left for the owner at 1.0.0 | DISPOSITION-L05 |
| L06 | Deferred — after 1.0; cosmetic, in `src/` | `ai/task.md` |
| L07 | Deferred — after 1.0; needs a matching change of `gtach-preflight.sh` | `ai/task.md` |
| L08 | Deferred — after 1.0 (updater version ordering is covered by the H01 tests) | `ai/task.md` |
| L09 | `DISCLAIMER.md` anchors fixed; `build.sh` prompt and README §3.1 deferred — after 1.0 | DISPOSITION-L09, `ai/task.md` |

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Reviewed Without Finding

- Thread lifecycle, watchdog escalation and the exit backstop (`core/`, `app.py`).
- Transport skeleton, failure causes, wedge escalation and link supervision (`comm/transport.py`), including the changes of `76ef5387`.
- Vehicle silent state and the engine-off display condition (`comm/obd.py`, `display/manager.py`), from `b29cbd71`.
- Logging set-up and the validation commands (`main.py`).
- `bin/gtach-preflight.sh`: handles a wheel by file name and does not parse versions, so it is not affected by H01.
- `bin/install.sh`: the version check compares the wheel file name with `gtach.__version__`; both are `1.0.0rc1` for the release candidate.
- `bin/pi-install.sh`: resolves the latest non-pre-release GitHub release.
- Packaging: `engine_profiles.yaml` and the font are declared as package data; verified in the built wheel in WP8.
- pygame and `pkg_resources`: no dependency on `pkg_resources` at import (WP3).
- `CLAUDE.md` and `config/config.example.yaml` agree with the source.
- The splash version text `v1.0.0rc1` fits its position by calculation; confirmation on the panel is part of the owner's device session.

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Recommendations

1. Verify on the device, with the release candidate installed: stage a wheel of a higher version with `./bin/deploy.sh --stage`, run "Check for updates", install, and confirm the restart and the probation clearance.
2. Confirm the copyright line of `LICENSE`.
3. At 1.0.0, decide the `Development Status` classifier.
4. Review `requirements-gtach-master.md` (row in `ai/task.md`).

[Return to Table of Contents](#table-of-contents)

---

## 7.0 Closure

Pending remediation and the follow-up pass.

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | Initial audit report; 13 findings |

---

Copyright (c) 2026 William Watson. MIT License.
