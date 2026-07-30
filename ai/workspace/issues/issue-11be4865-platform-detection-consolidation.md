Created: 2026 July 30

# Issue: Hardware Revision Parsed with lstrip; Two Independent Raspberry Pi Detectors Can Disagree

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-11be4865"
  title: "str.lstrip('1000') misused as prefix removal in hardware revision parsing; DependencyValidator re-implements Pi detection independently of PlatformDetector"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "open"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-11be4865"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/core-comm-utils-code-review.md v1.0, 2026-07-30.
    Finding §3.2 (str.lstrip misused as prefix removal), finding §4.4
    (duplicated Raspberry Pi detection logic), and §7.0 recommendation #3.
    Task list reference: ai/task.md §7.4.3.

affected_scope:
  components:
    - name: "PlatformDetector._detect_via_hardware_revision"
      file_path: "src/gtach/utils/platform.py"
    - name: "DependencyValidator._detect_platform"
      file_path: "src/gtach/utils/dependencies.py"
  designs: []
  version: "0.2.64"

reproduction:
  prerequisites: >
    A Linux host exposing /proc/cpuinfo with a Revision line. The
    production target is a Raspberry Pi Zero 2W (gtach.local).
  steps:
    - "Read the Revision line from /proc/cpuinfo on the target."
    - "Evaluate revision.lstrip('1000') against that string."
    - "Compare the result with the intended value — the revision with the overvoltage bit removed."
    - "Separately: run the application and note the platform reported by PlatformDetector."
    - "Run gtach --validate-dependencies and note the platform reported by DependencyValidator."
    - "Compare the two conclusions."
  frequency: "always"
  reproducibility_conditions: >
    The lstrip fault manifests for any revision code whose leading
    characters are '0' or '1' beyond the single overvoltage bit the comment
    intends to remove. Whether the specific revision in field use is
    affected is recorded as an open observation in ai/task.md §7.5.6.
    The detector divergence is present unconditionally: the two code paths
    share no logic.
  preconditions: ""
  test_data: >
    Pi Zero 2W base revision code '902120', present as a revision_map key
    at platform.py:323.
  error_output: "None. No exception is raised; detection silently returns a wrong or generic result."

behavior:
  expected: >
    The hardware revision is parsed by removing the defined flag bits from
    the revision word, yielding the base revision code that indexes
    revision_map. The application and its dependency validator reach the
    same conclusion about the platform they are running on.
  actual: >
    Two faults.

    (a) lstrip misused as prefix removal — utils/platform.py:347.

        clean_revision = revision.lstrip('1000')

    The comment above the line states this removes the overvoltage bit.
    str.lstrip removes every leading character that appears in the given
    set — here the set {'1', '0'} — not the literal string '1000'. For a
    revision code beginning with several '0' or '1' characters, meaningful
    hex digits are stripped along with the flag, producing an incorrect
    clean_revision and a wrong or absent revision_map lookup. The
    downstream fallback at platform.py:359 tests
    len(clean_revision) == 6, so an over-stripped value also fails that
    test and detection returns None, discarding the highest-confidence
    detection method (0.95) available.

    (b) Duplicated, divergent Pi detection — utils/dependencies.py:107-114.

        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                platform_info['is_raspberry_pi'] = True

    DependencyValidator._detect_platform re-implements Raspberry Pi
    detection as a substring test, independently of the weighted,
    multi-method PlatformDetector in utils/platform.py, which combines
    device-tree, hardware-revision, cpuinfo, BCM GPIO and system-platform
    evidence and resolves conflicts by confidence. The two can disagree, so
    --validate-dependencies can report a different platform conclusion than
    the application's own runtime detection. Because platform_info drives
    which dependencies are treated as required (dependencies.py:247, 259,
    361), a disagreement changes which dependencies are validated.
  impact: >
    The report classifies fault (a) as High severity, affecting hardware
    detection on the production target. PlatformDetector.get_platform_type
    feeds GPIO capability checks, display hardware checks and mock
    selection; a misidentified variant degrades or disables those paths.
    Fault (b) makes the dependency report unreliable as a diagnostic, which
    is the one job it has.
  workaround: >
    None. Both paths are automatic.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    Fault (a) is a misreading of the str.lstrip contract: it takes a set of
    characters, not a prefix. The intent — clearing a flag bit — is a
    numeric operation expressed as a string operation, so it cannot be
    correct in general even if it happens to be correct for the particular
    revision on the bench.

    Fault (b) is the result of implementing platform detection twice. The
    inline comment at dependencies.py:82, "Get platform info directly to
    avoid import conflicts", records the original reason: an import-cycle
    concern. utils/platform.py imports only the standard library, so no
    cycle exists today, and the duplication has no remaining
    justification.
  technical_notes: >
    The Raspberry Pi revision word is a bitfield. In the new-style encoding
    the base code occupies the low 24 bits; the warranty and overvoltage
    flags sit above them. Masking with 0xFFFFFF and formatting back to six
    lowercase hex digits yields exactly the key form already used in
    revision_map (for example '902120', 'a03111'), and is correct for
    every code rather than for a chosen subset.

    Old-style four-digit codes exist for early Pi models. After masking and
    zero-padding these become six characters, which satisfies the
    len(clean_revision) == 6 fallback test at platform.py:359 and yields
    RASPBERRY_PI_GENERIC at 0.7 confidence. That is a correct conclusion —
    the device is a Pi — and is an improvement on the current behaviour for
    those codes.

    For fault (b), utils/platform.py exposes module-level accessors
    is_raspberry_pi() (platform.py:960) and get_platform_info()
    (platform.py:990) over a lazily constructed singleton (get_detector,
    platform.py:947). DependencyValidator needs only the boolean.
    platform_info in dependencies.py is a plain dict consumed at
    dependencies.py:247, 259, 361, 394-397 and 439-442, so its keys must be
    preserved exactly; only the source of the is_raspberry_pi value
    changes.

    utils/__init__.py:12 imports DependencyValidator, so any new import in
    dependencies.py is exercised at package import time. A relative import
    of .platform is safe — platform.py has no intra-package imports — but
    should carry a try/except ImportError fallback to the current inline
    detection, consistent with the project's conditional-import standard.
  related_issues: []

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Replace the lstrip call with an integer mask and six-digit hex
    reformat. Have DependencyValidator obtain is_raspberry_pi from
    PlatformDetector rather than re-deriving it, retaining the existing
    inline logic only as an ImportError fallback. See change-11be4865.
  change_ref: "change-11be4865"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    Flag bits are cleared numerically, not by string manipulation. Where a
    string operation stands in for a bit operation, the comment describing
    the intent should be treated as a signal to check the contract of the
    method used.
  process_improvements: >
    A capability that already has an authoritative implementation should be
    called, not re-derived. Where an import concern motivates duplication,
    the concern should be recorded and re-tested rather than left as a
    standing comment.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/utils/platform.py passes."
    - "python -m py_compile src/gtach/utils/dependencies.py passes."
    - "Unit test: '902120' and '1902120' both resolve to RASPBERRY_PI_ZERO_2W."
    - "Unit test: a revision beginning with several 0 or 1 characters is no longer over-stripped."
    - "Unit test: 'a03111' resolves to RASPBERRY_PI_4 unchanged."
    - "Unit test: DependencyValidator.platform_info['is_raspberry_pi'] agrees with gtach.utils.platform.is_raspberry_pi()."
    - "Unit test: with the .platform import forced to fail, DependencyValidator still populates platform_info and reports a plausible result."
    - "Confirm every key of platform_info is still present: system, machine, python_version, is_raspberry_pi, is_linux, is_development."
    - "On gtach.local: record the actual Revision string per ai/task.md §7.5.6 and confirm the parsed clean_revision equals the intended base code."
    - "On gtach.local: run gtach --validate-dependencies and confirm its platform line matches the application's own detection."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-11be4865"
  test_refs: []

notes: >
  This is task 7.4.3 in ai/task.md §7.4 and part of step 3 in the
  recommended authoring order (§7.6.2), being one of the two High severity
  core findings active in the running application. The core report's §6.0
  priority table lists it as item 3.

  ai/task.md §7.5.6 records an outstanding observation: the actual hardware
  revision string on the Pi Zero 2W target. That observation sets the
  severity recorded here — it determines whether the lstrip defect corrupts
  detection for the revision in field use, or is latent. It does not gate
  this triple; the defect is real either way and the fix is correct
  regardless of the outcome.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial issue document from core-comm-utils-code-review.md §3.2, §4.4 and recommendation #3."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial issue document from core-comm-utils-code-review.md §3.2, §4.4 and recommendation #3. |

---

Copyright (c) 2026 William Watson. MIT License.
