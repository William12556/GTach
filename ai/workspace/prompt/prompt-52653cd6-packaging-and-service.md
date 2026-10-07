Created: 2026 October 07

# Prompt: Packaging, Service Hardening and Script Corrections

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-52653cd6"
  task_type: "debug"
  source_ref: "change-52653cd6"
  target_profile: "claude_code"
  date: "2026-10-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-52653cd6"
    change_iteration: 1

context:
  purpose: "Correct packaging, the service unit, deployment scripts and the audit check script."
  integration: "pyproject.toml; src/gtach/__init__.py, display/touch_interface.py, utils/dependencies.py; bin/; CLAUDE.md; one test module."
  knowledge_references:
    - "ai/workspace/issues/issue-52653cd6-packaging-and-service.md"
    - "ai/workspace/change/change-52653cd6-packaging-and-service.md"
  constraints:
    - "Apply EDITS A to M of change-52653cd6 exactly; do not add other service directives (no User=, no CapabilityBoundingSet)."
    - "Do not change bin/pi-install.sh or anything under bin/vendor/."
    - "Scripts remain bash and keep their existing interfaces and defaults; new options are additive."
    - "Do not touch the backup modules (deleted by a later task)."
    - "Every logger .error/.critical in a broad handler passes exc_info=True."
    - "Python 3.9+ compatible. PEP 8. Type hints on public interfaces. Google-style docstrings."

specification:
  description: "Apply EDITS A to M and add tests/test_packaging_and_scripts.py."
  requirements:
    functional:
      - "pyproject pi extra = RPi.GPIO, hyperpixel2r; no click; metadata current."
      - "Single version source in pyproject.toml."
      - "Mock touch fallback logs ERROR on a Raspberry Pi."
      - "Service unit carries the specified limits and four hardening directives."
      - "Deployment scripts behave as specified."
    technical:
      language: "Python, bash, systemd"
      version: "3.9+"
      standards:
        - "Professional docstrings"
  performance: []

design:
  architecture: "No structural change."
  components:
    - name: "EDITS A to M"
      type: "module"
      purpose: "As in change-52653cd6 proposed_solution."
      logic:
        - "EDIT B: `from importlib.metadata import version as _version, PackageNotFoundError`; `try: __version__ = _version('gtach') except PackageNotFoundError: __version__ = '0+unknown'`. In build.sh delete the block that writes src/gtach/__init__.py and its echo line."
        - "EDIT C: import is_raspberry_pi lazily inside the fallback path; `log = self.logger.error if is_raspberry_pi() else self.logger.info`; guard the call with try/except so detection failure falls back to INFO."
        - "EDIT G order: mkdir; all scp; `systemctl stop gtach || true`; install.sh; reboot."
        - "EDIT H: `tmp=$(mktemp -d)`; `scp \"$PI:$REMOTE_DIR/*.log*\" \"$tmp/\"`; on success `rm -f \"$LOG_DIR\"/*` and move files in; always remove $tmp (trap)."
        - "EDIT J: `git fetch -q origin`; `git branch -r --contains HEAD | grep -q 'origin/'` or exit 1 with a message."
        - "EDIT K: wrap as `install_and_check()` used for new and rollback installs; on pip check failure echo its output via log()."

data_schema:
  entities: []

error_handling:
  strategy: "Scripts fail loudly before changing the Pi where possible."
  exceptions: []
  logging:
    level: "ERROR for mock fallback on a Pi"
    format: "Unchanged"

testing:
  unit_tests:
    - scenario: "As listed in change-52653cd6 testing_requirements.test_cases."
      expected: "As listed there."
  edge_cases:
    - "pull_logs.sh when the Pi has no rotated logs: succeeds with the live logs."
  validation:
    - "bash -n bin/*.sh"
    - "pytest tests/ passes."

deliverable:
  format_requirements:
    - "Edit in place; add one test module."
  files:
    - path: "pyproject.toml"
      content: "EDIT A"
    - path: "src/gtach/__init__.py, bin/build.sh"
      content: "EDIT B"
    - path: "src/gtach/display/touch_interface.py"
      content: "EDIT C"
    - path: "src/gtach/utils/dependencies.py"
      content: "EDIT D"
    - path: "bin/gtach.service, bin/install.sh, bin/deploy.sh, bin/pull_logs.sh, bin/gen_splash.py, bin/release.sh, bin/gtach-preflight.sh, bin/gtach-audit-checks.sh"
      content: "EDITS E to L"
    - path: "CLAUDE.md"
      content: "EDIT M"
    - path: "tests/test_packaging_and_scripts.py"
      content: "Tests"

success_criteria:
  - "pyproject.toml: pi extra has hyperpixel2r, no gpiozero; no click; URLs point to William12556/GTach."
  - "src/gtach/__init__.py contains no literal version; bin/build.sh does not write it."
  - "bin/gtach.service contains TimeoutStopSec=30, StartLimitBurst=5, StartLimitIntervalSec=120, Wants=bluetooth.service and the four hardening directives."
  - "bin/install.sh installs with [pi]; bin/deploy.sh stops the service only after all copies."
  - "bin/gtach-preflight.sh runs pip check after installs."
  - "bash -n passes for every bin/*.sh."
  - "pytest tests/ passes."

element_registry:
  source: ""
  entries:
    modules:
      - name: "gtach"
        path: "src/gtach/__init__.py"
    classes: []
    functions: []
    constants: []

notes: >
  Human verification on the Pi after ./bin/deploy.sh: the service starts;
  touch works; `systemd-analyze security gtach` lists the new
  directives; `time systemctl stop gtach` is under 30 s; error.log has no
  mock-fallback ERROR.
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial prompt implementing change-52653cd6 iteration 1. Target profile claude_code. |

---

Copyright (c) 2026 William Watson. MIT License.
