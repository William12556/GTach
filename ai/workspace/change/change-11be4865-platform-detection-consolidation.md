Created: 2026 July 30

# Change: Correct Hardware Revision Parsing and Consolidate Raspberry Pi Detection

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-11be4865"
  title: "Replace lstrip with an integer mask in hardware revision parsing; route DependencyValidator's Pi detection through PlatformDetector"
  date: "2026-07-30"
  author: "William Watson"
  status: "proposed"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-11be4865"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-11be4865"
  description: >
    Resolves issue-11be4865. Sourced from
    ai/workspace/report/core-comm-utils-code-review.md v1.0 findings §3.2
    and §4.4 and recommendation #3. Task list reference ai/task.md §7.4.3.

scope:
  summary: >
    Two independent corrections in the platform-detection path. In
    src/gtach/utils/platform.py, clear the revision word's flag bits
    numerically instead of with str.lstrip. In
    src/gtach/utils/dependencies.py, obtain the is_raspberry_pi conclusion
    from PlatformDetector instead of re-deriving it from a substring test,
    retaining the existing inline logic as an ImportError fallback.
  affected_components:
    - name: "PlatformDetector._detect_via_hardware_revision"
      file_path: "src/gtach/utils/platform.py"
      change_type: "modify"
    - name: "DependencyValidator._detect_platform"
      file_path: "src/gtach/utils/dependencies.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "The other five detection methods in PlatformDetector: _detect_via_device_tree, _detect_via_cpuinfo, _detect_via_bcm_gpio, _detect_via_system_platform and _resolve_conflicts. Unchanged."
    - "The revision_map contents. No key is added, removed or altered."
    - "The confidence values 0.95 and 0.7. Unchanged."
    - "The shape or keys of DependencyValidator.platform_info. Only the source of one value changes."
    - "The dependency table, validation logic or report formatting in dependencies.py."
    - "Adding Pi variant granularity to platform_info. DependencyValidator needs only the boolean."
    - "utils/home.py stale path markers — core report §5.4, task 7.4.7."

rational:
  problem_statement: >
    revision.lstrip('1000') at platform.py:347 removes every leading '0' or
    '1' character rather than a literal prefix, so a revision code whose
    leading digits are 0 or 1 is over-stripped. The result either misses
    revision_map or fails the six-character fallback test, discarding the
    highest-confidence detection method available. Separately,
    DependencyValidator._detect_platform re-implements Raspberry Pi
    detection as a substring test at dependencies.py:107-114, independently
    of the weighted multi-method PlatformDetector, so the two can disagree
    and --validate-dependencies can validate the wrong dependency set.
  proposed_solution: >
    Parse the revision as a hexadecimal integer, mask to the low 24 bits
    that carry the base code, and format back to six lowercase hex digits —
    exactly the key form already used in revision_map. Have
    DependencyValidator call the module-level is_raspberry_pi() accessor
    from utils.platform, falling back to the current inline detection only
    if that import fails.
  alternatives_considered:
    - option: "Use revision.removeprefix('1') instead of lstrip."
      reason_rejected: >
        Still a string operation standing in for a bit operation. It
        happens to be correct for the single-flag case and wrong for any
        other flag combination, which is the same class of fault at a
        smaller scale. It also requires Python 3.9 or later, which the
        project targets, but buys nothing over the mask.
    - option: "Slice a fixed-width six-character suffix: revision[-6:]."
      reason_rejected: >
        Offered by the report as an alternative and defensible, but it
        silently mishandles old-style four-digit codes by returning a
        four-character string that fails the fallback test. The mask
        handles both encodings and states the intent — clearing flag bits —
        directly.
    - option: "Have DependencyValidator construct its own PlatformDetector instance."
      reason_rejected: >
        get_detector() (platform.py:947) already provides a lazily
        constructed, lock-guarded singleton. A second instance would repeat
        the detection work, including subprocess and filesystem probes, for
        no benefit.
    - option: "Import get_platform_info() and use the whole dict."
      reason_rejected: >
        get_platform_info() calls check_gpio_availability(), which performs
        GPIO probing. DependencyValidator needs one boolean; triggering GPIO
        probes as a side effect of constructing a dependency report is
        disproportionate and could fail on a non-Pi host.
    - option: "Delete DependencyValidator._detect_platform's inline detection entirely, with no fallback."
      reason_rejected: >
        utils/__init__.py:12 imports DependencyValidator at package import
        time, so an import failure in platform.py would take the validator
        down with it. The validator's purpose is diagnosis; it should remain
        the most robust component, not the most fragile. The fallback costs
        a dozen retained lines.
  benefits:
    - "Hardware-revision detection, the highest-confidence method at 0.95, becomes correct for every revision encoding rather than for a subset."
    - "Old-style four-digit revision codes now resolve to RASPBERRY_PI_GENERIC instead of returning None."
    - "The application and --validate-dependencies can no longer reach contradictory conclusions about the host."
    - "Raspberry Pi detection has one authoritative implementation."
  risks:
    - risk: >
        A malformed Revision line that is not valid hexadecimal would raise
        ValueError where the string operation previously produced a
        harmless non-match.
      mitigation: >
        Catch ValueError explicitly around the int() conversion and return
        None, which is the existing behaviour for an unrecognised revision.
        The enclosing except Exception clause at platform.py:369 remains as
        a backstop.
    - risk: >
        Routing dependencies.py through platform.py introduces a package
        import that the original inline comment ('avoid import conflicts',
        dependencies.py:82) was written to prevent.
      mitigation: >
        utils/platform.py imports only the standard library, so no cycle
        exists. The import is nevertheless wrapped in try/except ImportError
        with the current inline detection retained as the fallback,
        consistent with the project's conditional-import standard. The stale
        comment is removed.
    - risk: >
        PlatformDetector's first call performs device-tree, cpuinfo, GPIO
        and subprocess probes, so DependencyValidator construction becomes
        more expensive than a single file read.
      mitigation: >
        get_detector() caches the singleton and PlatformDetector caches its
        detection result, so the cost is paid once per process and is
        already paid by the application itself. Use is_raspberry_pi(), not
        get_platform_info(), so GPIO capability probing is not triggered.
    - risk: >
        A behaviour change in --validate-dependencies output on hosts where
        the two detectors previously disagreed.
      mitigation: >
        That divergence is the defect. Note the changed conclusion in the
        T06 result if it is observed on any test host.

technical_details:
  current_behavior: >
    _detect_via_hardware_revision (platform.py:301) reads the Revision line
    from /proc/cpuinfo, then at platform.py:346-347:

        # Clean revision (remove overvoltage bit)
        clean_revision = revision.lstrip('1000')

    and looks clean_revision up in revision_map (platform.py:349). On a
    miss it tests len(clean_revision) == 6 and clean_revision.isalnum()
    (platform.py:359) and returns RASPBERRY_PI_GENERIC at 0.7 confidence,
    otherwise None.

    DependencyValidator.__init__ (dependencies.py:71) sets
    self.platform_info = self._detect_platform(). _detect_platform
    (dependencies.py:80) builds a dict with keys system, machine,
    python_version, is_raspberry_pi, is_linux and is_development, deriving
    is_raspberry_pi from a substring test on /proc/cpuinfo at
    dependencies.py:107-114.
  proposed_behavior: >
    clean_revision is computed as format(int(revision, 16) & 0xFFFFFF,
    '06x'), which clears the warranty and overvoltage flags above bit 23
    and yields the six-lowercase-hex-digit form used by revision_map. A
    non-hexadecimal revision returns None.

    DependencyValidator._detect_platform obtains is_raspberry_pi from
    gtach.utils.platform.is_raspberry_pi(). If that import or call fails,
    it falls back to the existing /proc/cpuinfo substring test. Every key
    of platform_info is preserved, and is_development continues to be
    derived as is_linux and not is_raspberry_pi.
  implementation_approach: >
    Two edits, one per file.

    EDIT 1 — utils/platform.py, _detect_via_hardware_revision. Replace the
    comment and the lstrip line (platform.py:346-347) with a masked parse:

        # Clear the warranty and overvoltage flag bits. The base revision
        # code occupies the low 24 bits; str.lstrip cannot express this,
        # because it removes every leading character in the given set
        # rather than a literal prefix (core review §3.2).
        try:
            clean_revision = format(int(revision, 16) & 0xFFFFFF, '06x')
        except ValueError:
            return None

    Everything after that line — the revision_map lookup, the
    DetectionResult construction at 0.95, the six-character fallback at 0.7,
    the final return None and the enclosing except clause — is unchanged.
    revision_map keys are already six lowercase hex digits, so the format
    string matches them without further normalisation.

    EDIT 2 — utils/dependencies.py, _detect_platform. Replace the Raspberry
    Pi detection block (dependencies.py:107-114) with a call to the
    authoritative detector, guarded:

        # Detect Raspberry Pi via the authoritative multi-method detector
        # rather than a second substring test that can disagree with it
        # (core review §4.4).
        try:
            from .platform import is_raspberry_pi as _is_raspberry_pi
            platform_info['is_raspberry_pi'] = _is_raspberry_pi()
        except Exception as e:
            # Fallback: this validator must remain usable even if platform
            # detection is unavailable, since diagnosing that condition is
            # part of its purpose.
            self.logger.debug(f"PlatformDetector unavailable, using inline detection: {e}")
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpuinfo = f.read()
                    if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                        platform_info['is_raspberry_pi'] = True
            except (FileNotFoundError, PermissionError):
                pass

    Remove the now-stale comment at dependencies.py:82, 'Get platform info
    directly to avoid import conflicts', and the redundant local
    'import os' / 'import sys' beneath it only if both are already imported
    at module scope — they are, at dependencies.py:14-15. Leave the
    os.uname() block, the python_version construction, the platform_info
    dict literal, the is_development derivation and the debug log at the end
    of the method unchanged.
  code_changes:
    - component: "PlatformDetector"
      file: "src/gtach/utils/platform.py"
      change_summary: "Revision flag bits cleared by integer mask; non-hexadecimal revision returns None."
      functions_affected:
        - "_detect_via_hardware_revision"
      classes_affected:
        - "PlatformDetector"
    - component: "DependencyValidator"
      file: "src/gtach/utils/dependencies.py"
      change_summary: "is_raspberry_pi sourced from PlatformDetector with the inline substring test retained as fallback; stale import-conflict comment and redundant local imports removed."
      functions_affected:
        - "_detect_platform"
      classes_affected:
        - "DependencyValidator"
  data_changes: []
  interface_changes:
    - interface: "DependencyValidator.platform_info"
      change_type: "contract"
      details: >
        Keys and value types are unchanged: system, machine, python_version,
        is_raspberry_pi, is_linux, is_development. Only the derivation of
        is_raspberry_pi changes, and consequently is_development, which is
        computed from it. Consumers at dependencies.py:247, 259, 361,
        394-397 and 439-442 require no modification.
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "gtach.utils.platform"
      impact: "New import target for dependencies.py. platform.py imports only the standard library, so no cycle is created."
    - component: "gtach.utils.__init__ (line 12)"
      impact: "Imports DependencyValidator at package import time, so the new import is exercised then. Guarded by try/except."
    - component: "PlatformDetector.get_platform_type / check_gpio_availability / import_module_with_mock"
      impact: "Consume _detect_via_hardware_revision indirectly via _run_all_detections. Behaviour improves; no signature change."
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    Unit tests on the development platform with /proc/cpuinfo mocked, plus
    an on-target confirmation of the actual revision string per
    ai/task.md §7.5.6.
  test_cases:
    - scenario: "Revision '902120' (Pi Zero 2W, no flags)."
      expected_result: "clean_revision '902120'; RASPBERRY_PI_ZERO_2W at 0.95 confidence."
    - scenario: "Revision '1902120' (Pi Zero 2W with the overvoltage flag)."
      expected_result: "clean_revision '902120'; RASPBERRY_PI_ZERO_2W at 0.95 confidence."
    - scenario: "Revision 'a03111' (Pi 4)."
      expected_result: "clean_revision 'a03111'; RASPBERRY_PI_4 at 0.95 confidence."
    - scenario: "A revision whose base code begins with '0' or '1' and which the current lstrip over-strips."
      expected_result: "The base code survives intact and the map lookup succeeds."
    - scenario: "Old-style four-digit revision '0002'."
      expected_result: "clean_revision '000002'; six characters, alphanumeric; RASPBERRY_PI_GENERIC at 0.7 confidence."
    - scenario: "Revision 'not-hex'."
      expected_result: "Returns None. No ValueError escapes."
    - scenario: "No Revision line in /proc/cpuinfo."
      expected_result: "Returns None, as before."
    - scenario: "DependencyValidator on a host where PlatformDetector reports a Pi."
      expected_result: "platform_info['is_raspberry_pi'] is True and matches gtach.utils.platform.is_raspberry_pi()."
    - scenario: "DependencyValidator with the .platform import patched to raise ImportError."
      expected_result: "platform_info is fully populated via the inline fallback; a DEBUG line records the fallback."
    - scenario: "DependencyValidator on a non-Linux host with no /proc/cpuinfo."
      expected_result: "is_raspberry_pi False, is_development False, no exception."
  regression_scope:
    - "tests/utils/ — full existing utils suite."
    - "gtach --validate-dependencies runs and produces a complete report."
    - "Application start-up: platform detection, GPIO capability check and mock selection all behave as before on a non-Pi development host."
  validation_criteria:
    - "python -m py_compile src/gtach/utils/platform.py passes."
    - "python -m py_compile src/gtach/utils/dependencies.py passes."
    - "pytest tests/ passes with no new failures."
    - "The string \"lstrip('1000')\" does not appear anywhere in src/gtach."
    - "Every key of platform_info is present and unchanged in type."

implementation:
  implementation_steps:
    - step: "EDIT 1 — replace the lstrip call in _detect_via_hardware_revision with a masked hexadecimal parse."
      owner: "Claude Code"
    - step: "EDIT 2 — route DependencyValidator._detect_platform's Pi detection through utils.platform, with the inline test as fallback."
      owner: "Claude Code"
    - step: "Compile check and run the existing test suite."
      owner: "Claude Code"
    - step: "Record the actual Revision string on gtach.local per ai/task.md §7.5.6 and confirm the parsed value."
      owner: "William Watson"
    - step: "Run gtach --validate-dependencies on the target and confirm agreement with the application's detection."
      owner: "William Watson"
  rollback_procedure: >
    Two files, one commit. git revert restores the previous behaviour. No
    data, configuration or interface migration is involved.
  deployment_notes: >
    On a host where the two detectors previously disagreed, the
    --validate-dependencies platform line will change. That is the intended
    outcome; record it in the T06 result if observed.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-11be4865"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-11be4865."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial change document coupled to issue-11be4865. |

---

Copyright (c) 2026 William Watson. MIT License.
