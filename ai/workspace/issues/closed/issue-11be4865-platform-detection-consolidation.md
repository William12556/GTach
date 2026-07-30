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
  status: "closed"
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
  resolved_date: "2026-07-30"
  resolved_by: "Claude Code, per prompt-11be4865"
  fix_description: >
    Two edits, one per file, exactly as specified.

    EDIT 1 — src/gtach/utils/platform.py,
    _detect_via_hardware_revision. The comment and
    clean_revision = revision.lstrip('1000') were replaced by

        try:
            clean_revision = format(int(revision, 16) & 0xFFFFFF, '06x')
        except ValueError:
            return None

    The mask clears every bit above bit 23, so all flag bits are removed
    rather than only a leading '1', and the '06x' format yields the six
    lowercase hex digits that revision_map already uses as keys. A
    revision line that is not valid hexadecimal now returns None instead
    of producing a harmless non-match. Everything else in the method is
    untouched: the cpuinfo scan, the evidence dict, revision_map (verified
    byte-identical), the 0.95 DetectionResult, the len == 6 / isalnum
    fallback at 0.7, the trailing return None and the enclosing
    except Exception clause.

    EDIT 2 — src/gtach/utils/dependencies.py, DependencyValidator.
    _detect_platform. The stale comment 'Get platform info directly to
    avoid import conflicts' and the redundant local 'import os' and
    'import sys' were removed; both modules are imported at module scope
    (dependencies.py:14-15). The /proc/cpuinfo substring block was
    replaced by a guarded call to the authoritative accessor:

        try:
            from .platform import is_raspberry_pi as _is_raspberry_pi
            platform_info['is_raspberry_pi'] = _is_raspberry_pi()
        except Exception as e:
            self.logger.debug(
                f"PlatformDetector unavailable, using inline detection: {e}"
            )
            <original substring test, verbatim>

    is_raspberry_pi() was used rather than get_platform_info(), so no GPIO
    probing is triggered as a side effect of building a dependency report.
    No new PlatformDetector is constructed; the accessor is backed by the
    lock-guarded singleton in get_detector(). The os.uname() block, the
    python_version construction, the platform_info dict literal, the
    is_development derivation, the debug log and the return statement are
    unchanged.

verification:
  verified_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Verified 2026-07-30 on macOS 26.5.1 (Darwin 25.5.0, arm64),
    Python 3.11.14.

    tests/ contains no test modules — only README.md — so pytest collects
    zero items and the suite provides no regression signal. Verification
    was carried out with an ephemeral script exercising
    _detect_via_hardware_revision against a synthetic /proc/cpuinfo and
    constructing real DependencyValidator instances. Twenty-one
    assertions, covering all ten unit-test scenarios and all five edge
    cases in prompt-11be4865 and all ten test cases in change-11be4865.
    All twenty-one pass.

    The same script run unchanged against the pre-change files from HEAD
    fails six assertions and passes the other fifteen identically. The six
    failures are the defect:

      - '0002' (old-style four-digit) returned None; lstrip removed the
        leading zeros, leaving '2', which fails the len == 6 fallback.
        Now '000002' -> RASPBERRY_PI_GENERIC at 0.7.
      - '0x902120' returned None; lstrip removed the leading '0' and
        stopped at 'x', leaving a seven-character string. Now
        RASPBERRY_PI_ZERO_2W at 0.95.
      - 'A03111' (uppercase) returned RASPBERRY_PI_GENERIC at 0.7; the
        uppercase form missed the lowercase revision_map keys and fell
        through to the generic branch, downgrading a positively
        identifiable Pi 4. Now RASPBERRY_PI_4 at 0.95.
      - 'c0902120' (several flag bits set) returned None; lstrip strips
        nothing because the leading character is 'c', leaving eight
        characters. Now RASPBERRY_PI_ZERO_2W at 0.95.
      - With PlatformDetector reporting a Pi on a host with no
        /proc/cpuinfo, platform_info['is_raspberry_pi'] was False — the
        two detectors' conclusions differed. Now True.
      - No DEBUG line was emitted when platform detection was
        unavailable, there being no such path. Now exactly one.

    The fifteen behaviour-preservation assertions pass identically before
    and after: '902120', '1902120', 'a03111' and 'c04170' at 0.95; 'zzzz'
    returning None with no ValueError escaping; a missing Revision line
    and a missing /proc/cpuinfo both returning None; platform_info holding
    exactly the six keys with unchanged value types; is_raspberry_pi
    agreeing with the accessor on this host; is_development derived as
    is_linux and not is_raspberry_pi; the fallback path fully populating
    platform_info with a bool; and validate_all / get_summary /
    print_report / can_start_application completing without exception.

    Compile: python -m py_compile passes on both files. revision_map is
    byte-identical to its previous contents (sha1 of platform.py:321-344
    unchanged). The confidence values 0.95 and 0.7 are unchanged. The
    string "lstrip('1000')" does not appear anywhere in src/gtach. No file
    other than the two named is modified.
  closure_notes: >
    Both faults reported in behavior.actual are corrected. Fault (a) is
    removed by expressing the flag clear as the bit operation it is;
    fault (b) by giving the validator one authoritative source for the
    conclusion, with the previous inline test retained only as an
    ImportError fallback so the validator cannot be taken down by a
    failure in the component it exists to report on.

    One observation bears on the severity recorded here and on the open
    item at ai/task.md §7.5.6. Both '902120' and '1902120' — the Pi Zero
    2W base code with and without the overvoltage flag — parse correctly
    under the old lstrip as well as the new mask, because neither begins
    with '0' or '1' beyond the single flag digit. For the production
    target's revision specifically the defect is therefore latent, not
    active, and the High severity recorded above rests on the general case
    rather than on observed misdetection on gtach.local. This does not
    change the correctness of the fix. §7.5.6 remains open; recording the
    actual Revision string on target is still worth doing, but the
    argument for the fix no longer depends on it. ai/task.md was not
    modified — that is outside this triple.

    A second finding, not anticipated by the issue: the old lstrip path
    silently downgraded an uppercase revision string from a specific
    variant at 0.95 to RASPBERRY_PI_GENERIC at 0.7, because revision_map
    keys are lowercase and lstrip does no case normalisation. format(...,
    '06x') normalises as a side effect. This is a real improvement beyond
    the two faults as reported.

    The other five detection methods, the revision_map contents, the
    confidence values and the shape of platform_info were reviewed and
    left unchanged as the issue specifies.

    Two verification steps remain open by design and are not conditions of
    this closure, both owned by William Watson: recording the actual
    Revision string on gtach.local and confirming the parsed
    clean_revision, and running gtach --validate-dependencies on target to
    confirm its platform line matches the application's own detection.

    The absence of any test module under tests/ is a standing project-wide
    gap and is not raised as a residual against this issue.

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
  verification_results: >
    Steps 1-8 executed 2026-07-30 and all pass. Steps 9 and 10 are
    on-target and remain open; they are owned by William Watson and are
    not conditions of this closure.

    1. python -m py_compile src/gtach/utils/platform.py — passes.

    2. python -m py_compile src/gtach/utils/dependencies.py — passes.

    3. '902120' and '1902120' both resolve to RASPBERRY_PI_ZERO_2W at 0.95
    confidence, clean_revision '902120' in both cases. Note that both also
    resolved correctly before the change: the Zero 2W base code begins
    with '9', so lstrip removed only the flag digit. The Pi Zero 2W
    revision is not among the codes the defect corrupts — see
    closure_notes.

    4. A revision that the old lstrip over-strips no longer is. Four cases
    were exercised, each failing before the change and passing after:
    '0002' (leading zeros consumed, left as '2', detection lost — now
    '000002' -> RASPBERRY_PI_GENERIC at 0.7); '0x902120' (leading '0'
    consumed, 'x' retained, seven characters, detection lost — now
    RASPBERRY_PI_ZERO_2W at 0.95); 'c0902120' with several flag bits set
    (lstrip strips nothing, eight characters, detection lost — now
    RASPBERRY_PI_ZERO_2W at 0.95); and 'A03111' uppercase (missed the
    lowercase map keys, downgraded to RASPBERRY_PI_GENERIC at 0.7 — now
    RASPBERRY_PI_4 at 0.95).

    5. 'a03111' resolves to RASPBERRY_PI_4 at 0.95, unchanged before and
    after. 'c04170' -> RASPBERRY_PI_5 at 0.95 was checked alongside it and
    is likewise unchanged.

    6. DependencyValidator.platform_info['is_raspberry_pi'] equals
    gtach.utils.platform.is_raspberry_pi() on the verification host; both
    are False, this being macOS. Because agreement is trivial where both
    report False, divergence was forced as well: with the accessor patched
    to report a Pi on a host with no /proc/cpuinfo, the validator now
    reports True and is_development False. Before the change the validator
    reported False regardless of the detector's conclusion — the fault as
    reported.

    7. With the .platform import forced to raise ImportError, platform_info
    is fully populated by the inline fallback, is_raspberry_pi is a bool,
    and exactly one DEBUG line is emitted:
    "PlatformDetector unavailable, using inline detection: <error>".

    8. platform_info holds exactly system, machine, python_version,
    is_raspberry_pi, is_linux and is_development, with value types str,
    str, str, bool, bool, bool — identical before and after. validate_all,
    get_summary, print_report and can_start_application all complete
    without exception, so the dependency report still builds end to end.

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
  - version: "1.1"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Resolved and verified via change-11be4865 / prompt-11be4865. Resolution, verification and verification_enhanced blocks populated; status -> closed; moved to ai/workspace/issues/closed/ per P00 §1.1.14.4."

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
| 1.1 | 2026-07-30 | Resolved and verified. Status closed; moved to ai/workspace/issues/closed/ per P00 §1.1.14.4. |

---

Copyright (c) 2026 William Watson. MIT License.
