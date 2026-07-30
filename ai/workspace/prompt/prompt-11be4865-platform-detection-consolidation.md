Created: 2026 July 30

# Prompt: Correct Hardware Revision Parsing and Consolidate Raspberry Pi Detection

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-11be4865"
  task_type: "code_generation"
  source_ref: "change-11be4865"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-11be4865"
    change_iteration: 1

context:
  purpose: >
    Make hardware-revision detection correct for every revision encoding
    rather than for a subset, and give the application and its dependency
    validator a single authoritative answer to the question of whether they
    are running on a Raspberry Pi.
  integration: >
    Two files: src/gtach/utils/platform.py and
    src/gtach/utils/dependencies.py. One edit each. Executor is Claude
    Code; AEL is not used. This is one of the two High severity core
    findings active in the running application (core report §6.0 item 3)
    and is step 3 in the recommended authoring order of ai/task.md §7.6.2.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/utils/platform.py and src/gtach/utils/dependencies.py."
    - "Do not alter revision_map: add, remove or change no key or value."
    - "Do not alter the confidence values 0.95 or 0.7, or the DetectionResult construction."
    - "Do not touch the other five detection methods: _detect_via_device_tree, _detect_via_cpuinfo, _detect_via_bcm_gpio, _detect_via_system_platform, _resolve_conflicts."
    - "Do not change the keys, order or value types of DependencyValidator.platform_info. Only the derivation of is_raspberry_pi changes."
    - "Do not change the dependency table, validation logic or report formatting in dependencies.py."
    - "Use is_raspberry_pi(), NOT get_platform_info(). The latter calls check_gpio_availability() and would trigger GPIO probing as a side effect of building a dependency report."
    - "Do not construct a new PlatformDetector. Use the module-level accessor, which is backed by the lock-guarded singleton in get_detector()."
    - "Keep the inline /proc/cpuinfo substring test as an ImportError fallback. utils/__init__.py imports DependencyValidator at package import time, so the validator must not be able to fail on an import."
    - "Add no new third-party dependency."
    - "Type hints on all public interfaces; Google-style docstrings; PEP 8."

specification:
  description: >
    Clear the revision word's flag bits with an integer mask instead of
    str.lstrip, and source DependencyValidator's is_raspberry_pi value from
    PlatformDetector.
  requirements:
    functional:
      - "clean_revision is the low 24 bits of the revision word, formatted as six lowercase hex digits."
      - "A revision string that is not valid hexadecimal causes _detect_via_hardware_revision to return None, not to raise."
      - "'902120' and '1902120' both resolve to RASPBERRY_PI_ZERO_2W at 0.95 confidence."
      - "An old-style four-digit revision resolves to RASPBERRY_PI_GENERIC at 0.7 confidence via the existing six-character fallback."
      - "DependencyValidator.platform_info['is_raspberry_pi'] equals gtach.utils.platform.is_raspberry_pi()."
      - "If importing or calling that accessor fails, the inline /proc/cpuinfo substring test is used and the fallback is logged at DEBUG."
      - "Every existing key of platform_info remains present with its current type."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Conditional imports for hardware dependencies (try/except ImportError)"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "No repeated platform detection; the singleton detector caches its result"
      metric: "time"

design:
  architecture: >
    One authoritative platform detector. PlatformDetector combines
    device-tree, hardware-revision, cpuinfo, BCM GPIO and system-platform
    evidence and resolves conflicts by confidence; every other component
    consumes its conclusion rather than deriving its own. The revision
    parser treats the revision word as the bitfield it is.
  components:
    - name: "PlatformDetector._detect_via_hardware_revision"
      type: "function"
      purpose: "Identify the Pi variant from the /proc/cpuinfo Revision line."
      interface:
        inputs: []
        outputs:
          type: "Optional[DetectionResult]"
          description: "DetectionResult at 0.95 for a mapped revision, 0.7 for an unmapped but Pi-shaped one, None otherwise."
        raises:
          - "None. ValueError from the hex parse is caught and returns None; the enclosing except Exception clause remains as a backstop."
      logic:
        - "Leave everything up to and including the 'evidence' dict and revision_map exactly as it is."
        - "Replace the comment and the line 'clean_revision = revision.lstrip(\"1000\")' with a masked hexadecimal parse."
        - "clean_revision = format(int(revision, 16) & 0xFFFFFF, '06x')"
        - "Catch ValueError around the conversion and return None — an unparseable revision is not a detection."
        - "Leave the revision_map lookup, the 0.95 DetectionResult, the len == 6 and isalnum fallback at 0.7, the trailing return None and the outer except clause unchanged."
    - name: "DependencyValidator._detect_platform"
      type: "function"
      purpose: "Build the platform_info dict that drives which dependencies are treated as required."
      interface:
        inputs: []
        outputs:
          type: "Dict[str, Any]"
          description: "Keys: system, machine, python_version, is_raspberry_pi, is_linux, is_development."
        raises:
          - "None."
      logic:
        - "Remove the stale comment 'Get platform info directly to avoid import conflicts' and the redundant local 'import os' / 'import sys' — both modules are already imported at module scope (dependencies.py:14-15)."
        - "Leave the os.uname() block, its AttributeError fallback, the python_version construction and the platform_info dict literal exactly as they are."
        - "Replace the /proc/cpuinfo substring block with a guarded call to the authoritative accessor."
        - "On any exception from that call, log at DEBUG and fall back to the original inline substring test verbatim."
        - "Leave the is_development derivation, the debug log and the return statement unchanged."
  dependencies:
    internal:
      - "gtach.utils.platform.is_raspberry_pi — new import target for dependencies.py. platform.py imports only the standard library, so no cycle is created."
      - "gtach.utils.__init__ line 12 imports DependencyValidator at package import time; the new import is exercised there and is guarded."
    external: []

data_schema:
  entities:
    - name: "platform_info"
      attributes:
        - name: "system"
          type: "str"
          constraints: "From os.uname().sysname, or os.name on Windows. Unchanged."
        - name: "machine"
          type: "str"
          constraints: "From os.uname().machine, or 'unknown'. Unchanged."
        - name: "python_version"
          type: "str"
          constraints: "major.minor.micro. Unchanged."
        - name: "is_raspberry_pi"
          type: "bool"
          constraints: "Now sourced from PlatformDetector. Same key, same type."
        - name: "is_linux"
          type: "bool"
          constraints: "system == 'Linux'. Unchanged."
        - name: "is_development"
          type: "bool"
          constraints: "is_linux and not is_raspberry_pi. Derivation unchanged; its input may now differ."
      validation:
        - "All six keys must be present after the change. Consumers at dependencies.py:247, 259, 361, 394-397 and 439-442 index them directly."

error_handling:
  strategy: >
    The revision parse converts a silent wrong answer into an explicit
    None. The dependency validator's new import is guarded so the validator
    remains the most robust component in the package, not the most fragile.
  exceptions:
    - exception: "ValueError"
      condition: "The Revision line is not valid hexadecimal."
      handling: "Caught around int(revision, 16); return None."
    - exception: "Exception"
      condition: "Any other failure in _detect_via_hardware_revision."
      handling: "Existing handler retained: returns a DetectionResult with PlatformType.UNKNOWN, 0.0 confidence and the error string."
    - exception: "Exception"
      condition: "Import of, or call to, gtach.utils.platform.is_raspberry_pi fails."
      handling: "logger.debug records the fallback; the inline /proc/cpuinfo substring test runs instead."
    - exception: "FileNotFoundError, PermissionError"
      condition: "/proc/cpuinfo unavailable in the fallback path."
      handling: "Existing handler retained: pass, leaving is_raspberry_pi False."
  logging:
    level: "DEBUG"
    format: "self.logger.debug(f'PlatformDetector unavailable, using inline detection: {e}')"

testing:
  unit_tests:
    - scenario: "Revision '902120'."
      expected: "clean_revision '902120'; RASPBERRY_PI_ZERO_2W at 0.95."
    - scenario: "Revision '1902120' (overvoltage flag set)."
      expected: "clean_revision '902120'; RASPBERRY_PI_ZERO_2W at 0.95."
    - scenario: "Revision 'a03111'."
      expected: "clean_revision 'a03111'; RASPBERRY_PI_4 at 0.95."
    - scenario: "Revision 'c04170'."
      expected: "clean_revision 'c04170'; RASPBERRY_PI_5 at 0.95."
    - scenario: "Old-style revision '0002'."
      expected: "clean_revision '000002'; RASPBERRY_PI_GENERIC at 0.7 via the len == 6 fallback."
    - scenario: "Revision 'zzzz'."
      expected: "Returns None. No ValueError escapes the method."
    - scenario: "No Revision line present in /proc/cpuinfo."
      expected: "Returns None, unchanged from current behaviour."
    - scenario: "/proc/cpuinfo does not exist."
      expected: "Returns None, unchanged."
    - scenario: "DependencyValidator on a host PlatformDetector identifies as a Pi."
      expected: "platform_info['is_raspberry_pi'] is True and matches is_raspberry_pi()."
    - scenario: "DependencyValidator with the .platform import patched to raise ImportError."
      expected: "platform_info fully populated by the fallback; one DEBUG line emitted."
    - scenario: "DependencyValidator on a non-Linux host with no /proc/cpuinfo."
      expected: "is_raspberry_pi False, is_development False, no exception."
  edge_cases:
    - "Revision string with surrounding whitespace — already stripped at platform.py:311 by .strip()."
    - "Revision with a leading '0x' — int(s, 16) accepts it; the mask and format still produce a six-digit code."
    - "Uppercase revision letters — format(..., '06x') normalises to lowercase, matching revision_map keys."
    - "Revision word larger than 24 bits with several flags set — all bits above 23 are cleared, not only the overvoltage bit."
    - "PlatformDetector's first call performs subprocess and filesystem probes; the singleton caches, so DependencyValidator pays it at most once per process."
  validation:
    - "No existing test asserts the lstrip behaviour; if one does, update it in this change."
    - "gtach --validate-dependencies still produces a complete report."

deliverable:
  format_requirements:
    - "Edit both files in place. Create no new file."
    - "Make the two edits below and change nothing else."
  files:
    - path: "src/gtach/utils/platform.py"
      content: |
        EDIT 1 — _detect_via_hardware_revision (method begins at platform.py:301)

        Replace these two lines (currently platform.py:346-347):

                    # Clean revision (remove overvoltage bit)
                    clean_revision = revision.lstrip('1000')

        with:

                    # Clear the warranty and overvoltage flag bits. The base
                    # revision code occupies the low 24 bits of the revision
                    # word. str.lstrip cannot express this: it removes every
                    # leading character present in the given set — here {'1',
                    # '0'} — rather than a literal prefix, so a base code
                    # beginning with 0 or 1 is over-stripped (core review §3.2).
                    try:
                        clean_revision = format(int(revision, 16) & 0xFFFFFF, '06x')
                    except ValueError:
                        return None

        Change nothing else in the method. In particular leave unchanged:
          - the cpuinfo_path existence test and the Revision line scan
          - the `evidence` dict
          - the whole revision_map literal
          - `platform_type = revision_map.get(clean_revision)` and the
            DetectionResult returned at 0.95 confidence
          - the `if len(clean_revision) == 6 and clean_revision.isalnum():`
            fallback and the DetectionResult returned at 0.7 confidence
          - the trailing `return None`
          - the enclosing `except Exception as e:` clause

        Note: revision_map keys are already six lowercase hex digits
        ('902120', 'a03111', 'c04170', ...), so format(..., '06x') matches
        them directly. Do not normalise the keys.

    - path: "src/gtach/utils/dependencies.py"
      content: |
        EDIT 2 — DependencyValidator._detect_platform (method begins at
        dependencies.py:80)

        Step 2a — remove the stale preamble. Delete these four lines
        (currently dependencies.py:82-84 plus the following blank line):

                # Get platform info directly to avoid import conflicts
                import os
                import sys

        Both modules are already imported at module scope
        (dependencies.py:14-15), and the import-conflict concern the comment
        records no longer applies: utils/platform.py imports only the
        standard library.

        Step 2b — replace the Raspberry Pi detection block. Currently
        (dependencies.py:107-114):

                # Detect Raspberry Pi
                try:
                    with open('/proc/cpuinfo', 'r') as f:
                        cpuinfo = f.read()
                        if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                            platform_info['is_raspberry_pi'] = True
                except (FileNotFoundError, PermissionError):
                    pass

        Replace with:

                # Detect Raspberry Pi through the authoritative multi-method
                # detector rather than a second substring test that can
                # disagree with it. PlatformDetector weighs device-tree,
                # hardware-revision, cpuinfo, BCM GPIO and system-platform
                # evidence and resolves conflicts by confidence
                # (core review §4.4).
                try:
                    from .platform import is_raspberry_pi as _is_raspberry_pi
                    platform_info['is_raspberry_pi'] = _is_raspberry_pi()
                except Exception as e:
                    # This validator must remain usable even when platform
                    # detection is not, since reporting that condition is part
                    # of its purpose. Fall back to the direct check.
                    self.logger.debug(
                        f"PlatformDetector unavailable, using inline detection: {e}"
                    )
                    try:
                        with open('/proc/cpuinfo', 'r') as f:
                            cpuinfo = f.read()
                            if 'BCM' in cpuinfo or 'Raspberry Pi' in cpuinfo:
                                platform_info['is_raspberry_pi'] = True
                    except (FileNotFoundError, PermissionError):
                        pass

        Change nothing else in the method. In particular leave unchanged:
          - the os.uname() block and its AttributeError fallback
          - the python_version construction
          - the platform_info dict literal, including all six keys and their
            initial values
          - the is_development derivation
            (is_linux and not is_raspberry_pi)
          - the `if self.debug:` log line
          - the `return platform_info`

        Use is_raspberry_pi(), not get_platform_info(). The latter calls
        check_gpio_availability(), which performs GPIO probing —
        disproportionate as a side effect of constructing a dependency
        report, and liable to fail on a non-Pi host.

success_criteria:
  - "python -m py_compile src/gtach/utils/platform.py passes."
  - "python -m py_compile src/gtach/utils/dependencies.py passes."
  - "pytest tests/ passes with no new failures."
  - "The string \"lstrip('1000')\" does not appear anywhere in src/gtach."
  - "_detect_via_hardware_revision computes clean_revision via format(int(revision, 16) & 0xFFFFFF, '06x')."
  - "A ValueError from that conversion returns None rather than propagating."
  - "revision_map is byte-identical to its previous contents."
  - "The confidence values 0.95 and 0.7 are unchanged."
  - "dependencies.py imports is_raspberry_pi from .platform inside a try/except."
  - "The inline /proc/cpuinfo substring test survives as the except-branch fallback."
  - "The comment 'Get platform info directly to avoid import conflicts' no longer appears."
  - "The redundant local 'import os' and 'import sys' inside _detect_platform are removed."
  - "platform_info still returns exactly the keys system, machine, python_version, is_raspberry_pi, is_linux and is_development."
  - "No file other than the two named is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "platform"
        path: "src/gtach/utils/platform.py"
      - name: "dependencies"
        path: "src/gtach/utils/dependencies.py"
    classes:
      - name: "PlatformDetector"
        module: "gtach.utils.platform"
      - name: "PlatformType"
        module: "gtach.utils.platform"
      - name: "DetectionResult"
        module: "gtach.utils.platform"
      - name: "DetectionMethod"
        module: "gtach.utils.platform"
      - name: "DependencyValidator"
        module: "gtach.utils.dependencies"
    functions:
      - name: "_detect_via_hardware_revision"
        module: "gtach.utils.platform"
        signature: "_detect_via_hardware_revision(self) -> Optional[DetectionResult]"
      - name: "is_raspberry_pi"
        module: "gtach.utils.platform"
        signature: "is_raspberry_pi() -> bool"
      - name: "get_detector"
        module: "gtach.utils.platform"
        signature: "get_detector() -> PlatformDetector"
      - name: "_detect_platform"
        module: "gtach.utils.dependencies"
        signature: "_detect_platform(self) -> Dict[str, Any]"
    constants:
      - name: "RASPBERRY_PI_ZERO_2W"
        module: "gtach.utils.platform"
        type: "PlatformType"
      - name: "RASPBERRY_PI_GENERIC"
        module: "gtach.utils.platform"
        type: "PlatformType"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-11be4865-platform-detection-consolidation.md

  On a host where the two detectors previously disagreed, the
  --validate-dependencies platform line will change. That divergence is the
  defect being corrected; record the changed conclusion in the T06 result
  if it is observed.

  ai/task.md §7.5.6 records an outstanding observation — the actual
  Revision string on the Pi Zero 2W target. It sets the severity recorded
  in the issue but does not gate this work: the defect is real for the
  general case and the fix is correct regardless of the outcome.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-11be4865. |

---

Copyright (c) 2026 William Watson. MIT License.
