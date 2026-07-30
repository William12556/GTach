Created: 2026 July 30

# Test: Platform Detection Consolidation

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-11be4865"
  title: "Unit tests for masked hardware-revision parsing and consolidated Raspberry Pi detection"
  date: "2026-07-30"
  author: "William Watson"
  status: "planned"
  type: "unit"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-11be4865"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "PlatformDetector._detect_via_hardware_revision; DependencyValidator._detect_platform"
  design_refs: []
  change_refs:
    - "change-11be4865"
  requirement_refs:
    - "core-comm-utils-code-review.md §3.2"
    - "core-comm-utils-code-review.md §4.4"
    - "core-comm-utils-code-review.md §7.0 recommendation #3"

scope:
  description: >
    Verifies that the revision word's flag bits are cleared numerically
    rather than by str.lstrip, and that DependencyValidator obtains its
    is_raspberry_pi conclusion from PlatformDetector with a working
    fallback. Establishes the regression net for change-11be4865 ahead of
    the v0.3.0 release (ai/task.md §8.2).
  test_objectives:
    - "Confirm every revision encoding resolves to the same base code the revision_map keys use."
    - "Confirm a non-hexadecimal revision returns None instead of raising."
    - "Confirm the 0.95 and 0.7 confidence paths are both still reachable."
    - "Confirm DependencyValidator and PlatformDetector cannot disagree."
    - "Confirm the ImportError fallback keeps DependencyValidator usable when platform detection is not."
  in_scope:
    - "src/gtach/utils/platform.py — _detect_via_hardware_revision only"
    - "src/gtach/utils/dependencies.py — _detect_platform only"
  out_scope:
    - "The other five detection methods: _detect_via_device_tree, _detect_via_cpuinfo, _detect_via_bcm_gpio, _detect_via_system_platform, _resolve_conflicts"
    - "_resolve_conflicts confidence weighting"
    - "GPIO capability probing (check_gpio_availability) and the mock registry"
    - "The dependency table, validation logic and report formatting in dependencies.py"
    - "Integration behaviour on real Pi hardware — that is ai/task.md §7.5.6"
  dependencies:
    - "unittest.mock for patching builtins.open and Path.exists"
    - "No pygame, no psutil, no hardware"

test_environment:
  python_version: "3.9+ (development platform); 3.11 on target"
  os: "macOS Apple Silicon (development); Debian Linux Raspberry Pi OS (target)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
    - name: "unittest.mock"
      version: "stdlib"
  test_framework: "pytest"
  test_data_location: "Inline fixtures; synthetic /proc/cpuinfo content via mock"

test_cases:
  - case_id: "TC-001"
    description: "Pi Zero 2W base revision with no flag bits set"
    category: "positive"
    preconditions:
      - "/proc/cpuinfo exists and contains a Revision line"
    test_steps:
      - step: "1"
        action: "Patch the cpuinfo read to return 'Revision : 902120'"
      - step: "2"
        action: "Call PlatformDetector()._detect_via_hardware_revision()"
    inputs:
      - parameter: "revision"
        value: "902120"
        type: "str"
    expected_outputs:
      - field: "result.platform_type"
        expected_value: "PlatformType.RASPBERRY_PI_ZERO_2W"
        validation: "Identity comparison against the enum member"
      - field: "result.confidence"
        expected_value: "0.95"
        validation: "Exact float comparison"
    postconditions:
      - "No exception raised"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Both expected outputs match"
    defects: []

  - case_id: "TC-002"
    description: "Pi Zero 2W revision with the overvoltage flag bit set — the case the lstrip defect was written for"
    category: "positive"
    preconditions:
      - "/proc/cpuinfo exists and contains a Revision line"
    test_steps:
      - step: "1"
        action: "Patch the cpuinfo read to return 'Revision : 1902120'"
      - step: "2"
        action: "Call _detect_via_hardware_revision()"
    inputs:
      - parameter: "revision"
        value: "1902120"
        type: "str"
    expected_outputs:
      - field: "result.platform_type"
        expected_value: "PlatformType.RASPBERRY_PI_ZERO_2W"
        validation: "Masking 0x1902120 with 0xFFFFFF yields 0x902120"
      - field: "result.confidence"
        expected_value: "0.95"
        validation: "Exact float comparison"
    postconditions:
      - "Result identical to TC-001"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Same platform_type and confidence as TC-001"
    defects: []

  - case_id: "TC-003"
    description: "Revision whose base code begins with characters lstrip would have consumed — the regression case"
    category: "negative"
    preconditions:
      - "A revision_map key beginning with '0' or '1' is injected for the duration of the test, or a synthetic code is used and the 0.7 fallback asserted"
    test_steps:
      - step: "1"
        action: "Patch the cpuinfo read to return a revision whose masked base code begins with '0' or '1', for example '1000042'"
      - step: "2"
        action: "Call _detect_via_hardware_revision()"
      - step: "3"
        action: "Assert the parsed clean_revision retains its leading characters"
    inputs:
      - parameter: "revision"
        value: "1000042"
        type: "str"
    expected_outputs:
      - field: "clean_revision"
        expected_value: "000042"
        validation: "Six characters. The former lstrip('1000') would have yielded '42', which fails the len == 6 test and discards the detection"
      - field: "result"
        expected_value: "DetectionResult with RASPBERRY_PI_GENERIC at 0.7"
        validation: "Unmapped but Pi-shaped, so the fallback path is taken rather than None"
    postconditions:
      - "Detection is not discarded"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "clean_revision is six characters and detection is not None"
    defects: []

  - case_id: "TC-004"
    description: "Pi 4 and Pi 5 mapped revisions still resolve"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Parametrise over 'a03111', 'b03112', 'c03114', 'd03114', 'c04170', 'd04170'"
      - step: "2"
        action: "Call _detect_via_hardware_revision() for each"
    inputs:
      - parameter: "revision"
        value: "a03111, b03112, c03114, d03114, c04170, d04170"
        type: "str"
    expected_outputs:
      - field: "result.platform_type"
        expected_value: "RASPBERRY_PI_4 for the a/b/c/d03 codes; RASPBERRY_PI_5 for the 04170 codes"
        validation: "Matches revision_map"
    postconditions:
      - "No mapped key regressed"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "All six resolve to the mapped variant at 0.95"
    defects: []

  - case_id: "TC-005"
    description: "Old-style four-digit revision code"
    category: "boundary"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Patch the cpuinfo read to return 'Revision : 0002'"
      - step: "2"
        action: "Call _detect_via_hardware_revision()"
    inputs:
      - parameter: "revision"
        value: "0002"
        type: "str"
    expected_outputs:
      - field: "clean_revision"
        expected_value: "000002"
        validation: "Zero-padded to six by the '06x' format"
      - field: "result.platform_type"
        expected_value: "PlatformType.RASPBERRY_PI_GENERIC"
        validation: "Satisfies the len == 6 and isalnum fallback; the device is a Pi, so this is a correct conclusion"
      - field: "result.confidence"
        expected_value: "0.7"
        validation: "Exact float comparison"
    postconditions:
      - "Improvement on the previous behaviour, which returned None for this input"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "RASPBERRY_PI_GENERIC at 0.7"
    defects: []

  - case_id: "TC-006"
    description: "Non-hexadecimal revision string"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Patch the cpuinfo read to return 'Revision : not-hex'"
      - step: "2"
        action: "Call _detect_via_hardware_revision()"
    inputs:
      - parameter: "revision"
        value: "not-hex"
        type: "str"
    expected_outputs:
      - field: "return value"
        expected_value: "None"
        validation: "The explicit ValueError guard returns None"
      - field: "exception"
        expected_value: "None raised"
        validation: "pytest.raises must not be needed; ValueError must not escape"
    postconditions:
      - "The outer except Exception backstop is not reached"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Returns None without raising"
    defects: []

  - case_id: "TC-007"
    description: "Revision line absent, and /proc/cpuinfo absent"
    category: "edge"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Patch the cpuinfo read to return content with no Revision line; call the method"
      - step: "2"
        action: "Patch Path.exists to return False; call the method"
    inputs:
      - parameter: "cpuinfo content"
        value: "No Revision line / file absent"
        type: "str"
    expected_outputs:
      - field: "return value"
        expected_value: "None in both cases"
        validation: "Behaviour unchanged from before change-11be4865"
    postconditions:
      - "No exception raised in either case"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "None returned, no exception"
    defects: []

  - case_id: "TC-008"
    description: "Uppercase and 0x-prefixed revision strings normalise correctly"
    category: "edge"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Parametrise over 'A03111' and '0xa03111'"
      - step: "2"
        action: "Call _detect_via_hardware_revision() for each"
    inputs:
      - parameter: "revision"
        value: "A03111, 0xa03111"
        type: "str"
    expected_outputs:
      - field: "result.platform_type"
        expected_value: "PlatformType.RASPBERRY_PI_4"
        validation: "int(s, 16) accepts both; format '06x' emits lowercase, matching revision_map keys"
    postconditions:
      - "No key normalisation was required in revision_map"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Both resolve to RASPBERRY_PI_4"
    defects: []

  - case_id: "TC-009"
    description: "DependencyValidator agrees with PlatformDetector"
    category: "positive"
    preconditions:
      - "gtach.utils.platform.is_raspberry_pi is importable"
    test_steps:
      - step: "1"
        action: "Patch gtach.utils.platform.is_raspberry_pi to return True"
      - step: "2"
        action: "Construct DependencyValidator() and read platform_info"
    inputs:
      - parameter: "is_raspberry_pi()"
        value: "True"
        type: "bool"
    expected_outputs:
      - field: "platform_info['is_raspberry_pi']"
        expected_value: "True"
        validation: "Sourced from the patched accessor, not from a substring test"
      - field: "platform_info['is_development']"
        expected_value: "False when is_linux is True"
        validation: "Derivation is_linux and not is_raspberry_pi is unchanged"
    postconditions:
      - "No second /proc/cpuinfo read occurred"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "platform_info reflects the patched value"
    defects: []

  - case_id: "TC-010"
    description: "DependencyValidator falls back when platform detection is unavailable"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Patch the .platform import inside _detect_platform to raise ImportError"
      - step: "2"
        action: "Patch the cpuinfo read to return content containing 'BCM'"
      - step: "3"
        action: "Construct DependencyValidator() and read platform_info"
    inputs:
      - parameter: "import is_raspberry_pi"
        value: "raises ImportError"
        type: "exception"
    expected_outputs:
      - field: "platform_info['is_raspberry_pi']"
        expected_value: "True"
        validation: "Inline substring fallback succeeded"
      - field: "log record"
        expected_value: "One DEBUG line containing 'PlatformDetector unavailable'"
        validation: "caplog at DEBUG level"
    postconditions:
      - "DependencyValidator constructed successfully; no exception propagated"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Validator usable and fallback logged"
    defects: []

  - case_id: "TC-011"
    description: "platform_info retains all six keys with their original types"
    category: "positive"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Construct DependencyValidator()"
      - step: "2"
        action: "Assert the key set and each value's type"
    inputs: []
    expected_outputs:
      - field: "platform_info keys"
        expected_value: "system, machine, python_version, is_raspberry_pi, is_linux, is_development"
        validation: "Exact set equality — consumers at dependencies.py index these directly"
      - field: "value types"
        expected_value: "str, str, str, bool, bool, bool"
        validation: "isinstance check per key"
    postconditions:
      - "The change-11be4865 backward-compatibility claim holds"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Key set and types match exactly"
    defects: []

  - case_id: "TC-012"
    description: "Non-Linux host with no /proc/cpuinfo"
    category: "edge"
    preconditions: []
    test_steps:
      - step: "1"
        action: "Patch os.uname to raise AttributeError and the cpuinfo read to raise FileNotFoundError"
      - step: "2"
        action: "Construct DependencyValidator()"
    inputs:
      - parameter: "os.uname"
        value: "raises AttributeError"
        type: "exception"
    expected_outputs:
      - field: "platform_info['is_raspberry_pi']"
        expected_value: "False"
        validation: "Default retained"
      - field: "platform_info['is_development']"
        expected_value: "False"
        validation: "is_linux is False, so the conjunction is False"
    postconditions:
      - "No exception raised"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Validator constructs with sane defaults"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "core review §3.2 — lstrip misused as prefix removal"
      test_cases:
        - "TC-001"
        - "TC-002"
        - "TC-003"
        - "TC-004"
        - "TC-005"
        - "TC-006"
        - "TC-008"
    - requirement_ref: "core review §4.4 — duplicated Pi detection"
      test_cases:
        - "TC-009"
        - "TC-010"
        - "TC-011"
        - "TC-012"
  code_coverage:
    target: "100% of _detect_via_hardware_revision and _detect_platform branches"
    achieved: ""
  untested_areas:
    - component: "PlatformDetector._resolve_conflicts"
      reason: "Unchanged by change-11be4865; confidence weighting is out of scope per §7.4.3"
    - component: "check_gpio_availability and the mock registry"
      reason: "Requires hardware or extensive mocking; no change under test touches it"

test_execution_summary:
  total_cases: 12
  passed: 0
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: ""
  execution_time: ""
  test_cycle: "Initial"

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues: []

verification:
  verified_date: ""
  verified_by: ""
  verification_notes: ""
  sign_off: ""

traceability:
  requirements:
    - requirement_ref: "core-comm-utils-code-review.md §7.0 #3"
      test_cases:
        - "TC-001"
        - "TC-009"
  designs: []
  changes:
    - change_ref: "change-11be4865"
      test_cases:
        - "TC-001"
        - "TC-002"
        - "TC-003"
        - "TC-004"
        - "TC-005"
        - "TC-006"
        - "TC-007"
        - "TC-008"
        - "TC-009"
        - "TC-010"
        - "TC-011"
        - "TC-012"

notes: >
  Generated pytest file: tests/utils/test_platform_detection.py, per P06
  §1.7.3. TC-003 is the regression case that distinguishes the masked
  parse from the former lstrip: it is the only case where the two
  implementations disagree on a Pi-shaped input, so it must not be
  dropped if the case list is trimmed.

  ai/task.md §7.5.6 — recording the actual revision string on the Pi Zero
  2W — remains outstanding. It is an observation, not a unit test, and
  determines only whether the defect was live or latent in field use. It
  does not affect any case here.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial test document for change-11be4865, per ai/task.md §8.2."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t05_test"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial test document for change-11be4865, per ai/task.md §8.2. |

---

Copyright (c) 2026 William Watson. MIT License.
