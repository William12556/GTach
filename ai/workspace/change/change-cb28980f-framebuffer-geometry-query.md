Created: 2026 July 30

# Change: Derive Framebuffer Size from the Device, and Report Disagreement at ERROR

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-cb28980f"
  title: "Query bits_per_pixel, resolution and stride at initialisation and derive fb_size from them; log a geometry disagreement and a write-path size mismatch at ERROR"
  date: "2026-07-30"
  author: "William Watson"
  status: "implemented"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-cb28980f"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-cb28980f"
  description: >
    Resolves issue-cb28980f. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0 recommendation
    21. Task list reference ai/task.md §7.3.3.

scope:
  summary: >
    Replace the assumed framebuffer size with one derived from the
    device's own reported geometry, and raise the two diagnostics that
    describe a disagreement from DEBUG to ERROR. One file:
    src/gtach/display/rendering/engine.py.
  affected_components:
    - name: "DisplayRenderingEngine.__init__"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine._query_framebuffer_geometry"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "add"
    - name: "DisplayRenderingEngine._initialize_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "_setup_page_flip, _wait_for_vsync and _pan_display. change-49b21ace owns them and they are closed."
    - "Using smem_len to pre-check whether page flipping can succeed. Recorded in issue-cb28980f as an observation for a future cycle; it would modify a closed triple's code."
    - "The payload acquisition and truncate/pad behaviour from change-66ef59a0. Only the log level of the mismatch changes, not the correction applied."
    - "Changing surface_size or the surfaces themselves. The engine continues to compose at 480 x 480."
    - "Migrating to KMS, or altering dpi_output_format in boot configuration."

rational:
  problem_statement: >
    fb_size is computed as surface_size[0] x surface_size[1] x 4, taking
    both the 32-bit depth and a stride equal to width x 4 on faith,
    although the device reports both. Where the device disagrees, the
    payload is truncated or zero-padded and the fact is logged at DEBUG,
    which production does not emit. The result is a skewed or partially
    blank panel with no diagnostic. Padding is in any case the wrong
    correction for a stride mismatch: it fixes the byte count while
    leaving every row after the first offset, which renders as a shear.
  proposed_solution: >
    Read bits_per_pixel, xres, yres and xres_virtual from
    FBIOGET_VSCREENINFO — the call change-49b21ace already established —
    and the stride from sysfs, falling back to a derivation. Derive
    fb_size as stride x yres. Log the queried geometry at INFO at every
    start, and log a disagreement between the device and the composed
    surface at ERROR. Raise the write-path mismatch log to ERROR.
  alternatives_considered:
    - option: "Read line_length from FBIOGET_FSCREENINFO, as the report specifies."
      reason_rejected: >
        struct fb_fix_screeninfo contains two unsigned long fields whose
        size and alignment differ between 32-bit and 64-bit builds, so
        unpacking it correctly requires architecture-dependent offset
        arithmetic that is easy to get wrong and hard to test on a
        development machine with no framebuffer. The sysfs attribute
        exposes the same value as text, is stable across architectures,
        and is the source the §7.5.1 observation used. The report's intent
        — obtain the authoritative stride rather than assume it — is met.
    - option: "Fail initialisation when the device disagrees with the assumption."
      reason_rejected: >
        A skewed display is more useful than none, and the engine cannot
        know that a disagreement is fatal. Report at ERROR and continue.
    - option: "Resize the composed surface to match a device whose resolution differs."
      reason_rejected: >
        The layout is designed for a 480 x 480 circular viewport with
        hard-coded geometry throughout manager.py. Rescaling would be a
        substantial change with no current beneficiary.
    - option: "Leave the write-path mismatch at DEBUG and add a separate ERROR at initialisation only."
      reason_rejected: >
        A mismatch that appears at runtime rather than at start — after a
        mode change or a driver reconfiguration — would still be invisible.
        Both sites are raised.
    - option: "Log the write-path mismatch at ERROR on every occurrence."
      reason_rejected: >
        It would fire at the frame rate. The condition is persistent, so
        it is logged once and then suppressed, with the count reported at
        cleanup.
  benefits:
    - "fb_size reflects the device rather than an assumption, so a mismatched stride is sized correctly instead of sheared."
    - "The geometry appears in the log at every start, so §7.5.1 need not be repeated by hand on a new device."
    - "A disagreement reaches the operator at the production log level."
  risks:
    - risk: >
        Deriving fb_size from the device changes the mmap length and could
        break page flipping, which remaps at twice fb_size.
      mitigation: >
        On the current target the derived value is identical to the
        assumed one — 1920 x 480 = 921,600 — so nothing changes. Order the
        query before the mmap so both the initial mapping and
        _setup_page_flip see the same value. Log the derived size so a
        divergence from 921,600 is visible immediately.
    - risk: >
        sysfs is unavailable or the attribute is absent on some driver.
      mitigation: >
        Fall back to xres_virtual x bits_per_pixel // 8, and then to the
        current width x 4 assumption. Log which source was used at INFO.
    - risk: >
        The framebuffer node is not fb0, so a hard-coded sysfs path reads
        the wrong device's stride.
      mitigation: >
        Derive the sysfs path from self.framebuffer_path by taking its
        basename, rather than hard-coding fb0.
    - risk: >
        Raising the write-path log to ERROR floods the log at the frame
        rate on a genuinely mismatched device.
      mitigation: >
        Log once, guarded by a flag, and count the occurrences. Report the
        total at cleanup so the persistence is recorded without the flood.
    - risk: >
        Opening fb_dev earlier to query through it changes the failure
        path when the device cannot be opened at all.
      mitigation: >
        Retain the existing try/except structure. If the open fails, the
        query is skipped, the assumption stands, and the existing
        direct-file fallback runs exactly as now.

technical_details:
  current_behavior: >
    _initialize_framebuffer computes
    self.fb_size = self.surface_size[0] * self.surface_size[1] * 4,
    opens the device, maps fb_size bytes, then selects a presentation
    mode. write_to_framebuffer compares the payload size against fb_size
    and, on a difference, logs at DEBUG (engine.py:565-566) and truncates
    or zero-pads.
  proposed_behavior: >
    _initialize_framebuffer opens the device, queries its geometry,
    derives fb_size from stride x yres, logs the result, and only then
    maps. A disagreement between the device's resolution or depth and the
    composed surface is logged at ERROR. write_to_framebuffer logs a size
    mismatch at ERROR, once, and counts subsequent occurrences.
  implementation_approach: >
    Four edits in src/gtach/display/rendering/engine.py.

    EDIT 1 — constants and state. Add the FB_VAR indices the query needs
    alongside those change-49b21ace already defined: FB_VAR_XRES 0,
    FB_VAR_XRES_VIRTUAL 2, FB_VAR_BITS_PER_PIXEL 6. Add to __init__:
    self.fb_line_length = 0, self.fb_bits_per_pixel = 0,
    self._size_mismatch_logged = False, self._size_mismatch_count = 0.

    EDIT 2 — add _query_framebuffer_geometry(). Requires an open fb_dev.
    Read FBIOGET_VSCREENINFO and unpack with the existing FB_VAR_STRUCT.
    Take xres, yres, xres_virtual and bits_per_pixel. Obtain the stride
    by reading /sys/class/graphics/<node>/stride, where <node> is the
    basename of self.framebuffer_path; on failure derive it as
    xres_virtual x bits_per_pixel // 8. Return a dict, or None if the
    query could not be made. Log the outcome at INFO including which
    stride source was used.

    EDIT 3 — _initialize_framebuffer. Restructure so the device is opened
    before fb_size is fixed. Open fb_dev, call
    _query_framebuffer_geometry(), and if it returned geometry set
    self.fb_size = stride x yres, self.fb_line_length and
    self.fb_bits_per_pixel. If it returned None, retain the existing
    assumption and log at WARNING that geometry could not be queried.
    Then compare against the composed surface and log at ERROR if
    bits_per_pixel is not 32, if xres or yres differ from surface_size, or
    if stride differs from xres x bits_per_pixel // 8 — the shear
    condition. Continue in every case. Then map, and select the
    presentation mode exactly as now.

    EDIT 4 — write_to_framebuffer. Change the mismatch log from
    self.logger.debug to self.logger.error, guarded by
    self._size_mismatch_logged so it is emitted once, and increment
    self._size_mismatch_count on every occurrence. Include the stride and
    depth in the message so the line is self-contained. Leave the
    truncate and pad behaviour unchanged. Report the accumulated count at
    cleanup if it is non-zero.
  code_changes:
    - component: "DisplayRenderingEngine"
      file: "src/gtach/display/rendering/engine.py"
      change_summary: >
        Geometry queried at initialisation and fb_size derived from it;
        disagreement with the composed surface reported at ERROR;
        write-path size mismatch raised from DEBUG to ERROR, logged once
        and counted.
      functions_affected:
        - "__init__"
        - "_query_framebuffer_geometry"
        - "_initialize_framebuffer"
        - "write_to_framebuffer"
        - "cleanup"
      classes_affected:
        - "DisplayRenderingEngine"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "change-49b21ace"
      impact: "Supplies fcntl, struct, FB_VAR_STRUCT, the working FBIOGET_VSCREENINFO call and the _fb_dev_usable guard. Already implemented; this change reuses them and modifies none of its methods."
    - component: "change-66ef59a0"
      impact: "Supplies the buffer-view write path containing the mismatch log whose level is raised."
    - component: "_setup_page_flip"
      impact: "Remaps at twice fb_size. Reads the derived value because the query precedes the mapping. Not otherwise modified."
  external: []
  required_changes:
    - change_ref: "change-49b21ace"
      relationship: "blocked_by"

testing_requirements:
  test_approach: >
    Unit tests on the development platform with fcntl.ioctl and the sysfs
    read mocked, plus on-target confirmation that the derived geometry
    matches the values observed by hand under §7.5.1.
  test_cases:
    - scenario: "Device reports 480 x 480 at 32 bits with stride 1920."
      expected_result: "fb_size 921600 — identical to the previous assumption. No ERROR logged. Geometry logged at INFO."
    - scenario: "Device reports 16 bits per pixel."
      expected_result: "ERROR logged naming the depth; fb_size derived from the reported stride; initialisation continues."
    - scenario: "Device reports stride 2048 against xres 480 at 32 bits."
      expected_result: "ERROR logged identifying the stride disagreement; fb_size is 2048 x 480, not 480 x 4 x 480."
    - scenario: "Device reports a resolution differing from surface_size."
      expected_result: "ERROR logged naming both; initialisation continues."
    - scenario: "sysfs stride unreadable."
      expected_result: "Stride derived from xres_virtual x bits_per_pixel // 8; the fallback source is logged at INFO."
    - scenario: "FBIOGET_VSCREENINFO raises."
      expected_result: "_query_framebuffer_geometry returns None; the width x height x 4 assumption is retained; WARNING logged; initialisation continues."
    - scenario: "framebuffer_path is /dev/fb1."
      expected_result: "The sysfs path read is /sys/class/graphics/fb1/stride."
    - scenario: "Write a payload whose size differs from fb_size, three times."
      expected_result: "Exactly one ERROR logged; _size_mismatch_count reaches 3; truncate or pad applied each time as before."
    - scenario: "cleanup after a run with a non-zero mismatch count."
      expected_result: "The total is reported once."
  regression_scope:
    - "tests/display/ once populated."
    - "Manual on target: startup log reports 32 bits, stride 1920, fb_size 921600, and no ERROR."
    - "Manual on target: every display mode renders unchanged from v0.2.67."
    - "Page flipping or the vsync fallback selects the same mode as before this change."
  validation_criteria:
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."
    - "fb_size is assigned from queried geometry when the query succeeds."
    - "The geometry query occurs before mmap.mmap is called."
    - "The write-path mismatch is logged at ERROR, not DEBUG."
    - "_setup_page_flip, _wait_for_vsync and _pan_display are unmodified."
    - "No file other than engine.py is modified."

implementation:
  implementation_steps:
    - step: "EDIT 1 — FB_VAR indices and geometry state."
      owner: "Claude Code"
    - step: "EDIT 2 — add _query_framebuffer_geometry."
      owner: "Claude Code"
    - step: "EDIT 3 — restructure _initialize_framebuffer to query before mapping."
      owner: "Claude Code"
    - step: "EDIT 4 — raise the write-path log level, guard and count."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Deploy to gtach.local; confirm the logged geometry matches the §7.5.1 observation and that no ERROR appears."
      owner: "William Watson"
  rollback_procedure: >
    Single file, single commit. git revert restores the previous
    behaviour. No data, configuration or interface migration is involved.
  deployment_notes: >
    On the current target the derived fb_size is identical to the assumed
    one, so no behavioural change is expected. The startup log gaining
    the geometry line is the visible effect. If an ERROR appears, the
    device disagrees with an assumption the engine has been making
    silently, and that is the finding.

verification:
  implemented_date: "2026-07-30"
  implemented_by: "Claude Code, per prompt-cb28980f"
  verification_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Development platform only: macOS, Python 3.11.14, pygame 2.6.1. Neither
    the framebuffer ioctls nor /sys/class/graphics exists here, so both were
    faked — a driver returning a controllable fb_var_screeninfo, and a
    sysfs stub whose requested paths are recorded — and the real engine was
    driven against them over a real mmap of a temporary file. Seventy
    assertions, all passing. Left active pending on-target results per
    ai/task.md §8.2.1.

    All four edits applied and all thirteen success criteria met, with one
    qualification and one addition recorded below.

    QUALIFICATION on the criterion "FBIOGET_FSCREENINFO does not appear
    anywhere in the file". The string does appear, once, and necessarily:
    the prompt's own EDIT 2 docstring explains that the stride is read from
    sysfs "rather than FBIOGET_FSCREENINFO" because struct
    fb_fix_screeninfo carries unsigned long fields whose size and alignment
    differ between 32- and 64-bit builds. The criterion and the prescribed
    text cannot both be satisfied literally. The intent — that the ioctl is
    not used — holds: no such constant is defined and no call references
    one, confirmed by walking the AST for a Name node of that identifier.
    The prose that explains why it was avoided is the opposite of a
    violation.

    ADDITION beyond EDIT 3: an impossibly small stride is not trusted. The
    prompt's edge_cases require that a line_length below xres x bpp // 8 be
    logged at ERROR and the assumption used instead. EDIT 3's code guards
    only against zero and would size the mapping from the impossible value.
    Verified by running the suite against a build carrying the literal EDIT
    3: a device reporting stride 960 for 480 px at 32-bit yields fb_size
    460,800, half the buffer, and every frame is truncated to half the
    panel. The literal version does still log the stride disagreement, so it
    is not silent — this is a question of which value to trust, not of
    diagnostics. The stated requirement is implemented: the impossible
    stride is reported at ERROR in its own message, retained in
    fb_line_length for the write-path diagnostic, and the composed-surface
    assumption is used for the mapping. A stride at or above the minimum is
    the device's own account of its layout and still governs, so the
    ordinary padded-row case is untouched — a reported stride of 1984 still
    gives fb_size 952,320.

    Evidence by test case.

    Matching geometry, 480x480 at 32-bit with stride 1920: fb_size is
    921,600, identical to the previous assumption; no ERROR is emitted; the
    INFO line reads "Framebuffer geometry: 480x480, virtual 480, 32-bit,
    stride 1920 (sysfs)"; fb_line_length and fb_bits_per_pixel are recorded;
    the mapping is sized to the derived value. This is the outcome predicted
    for the current target.

    Depth 16: one ERROR names the depth and states that colour will be
    wrong, fb_size follows the reported stride, and initialisation
    continues with a live mapping.

    Stride 2048 against 480 px at 32-bit: one ERROR names both figures and
    states that zero-padding corrects the byte count but not the row offset;
    fb_size becomes 983,040.

    Resolution 320x240 against a 480x480 surface: one ERROR names both and
    initialisation continues.

    sysfs unreadable: the stride is derived as xres_virtual x bpp // 8, the
    INFO line reports "(derived)" rather than "(sysfs)", and no ERROR is
    emitted because the derived value agrees.

    FBIOGET_VSCREENINFO raising: the query returns None, the 921,600-byte
    assumption is retained, and two WARNINGs are logged — the query failure
    with exc_info and the assumption being used. No ERROR, since an
    unavailable query is not a disagreement.

    Node derivation: with framebuffer_path /dev/fb1 the path read is
    /sys/class/graphics/fb1/stride, captured from the sysfs stub rather than
    inferred. No "graphics/fb0" literal appears in the file.

    Write-path mismatch: across three mismatched frames exactly one ERROR is
    emitted, the count reaches three, and the message carries the stride and
    depth and says further occurrences are suppressed. Both directions still
    behave as before — the pad preserves the frame and zero-fills the tail,
    the truncate keeps the leading fb_size bytes. cleanup then reports
    "mismatched on 3 frames this session" once, and is silent when the count
    is zero.

    Edge cases: yres 0 never yields fb_size 0 — the assumption is retained
    and the resolution ERROR fires naming 480x0. The direct-file fallback
    performs no query at all, since _fb_dev_usable reports the closed
    device. In mock rendering mode no ioctl is issued and neither the write
    nor cleanup raises.

    Ordering: the query call precedes mmap.mmap in _initialize_framebuffer
    by source position, which the design requires because _setup_page_flip
    remaps at twice fb_size and both must see the same value.

    Untouched by this change, confirmed by comparing unparsed ASTs against
    the previous commit: _setup_page_flip, _wait_for_vsync, _pan_display,
    _fb_dev_usable and swap_buffers are all byte-identical. The only methods
    that differ are __init__, _initialize_framebuffer, write_to_framebuffer
    and cleanup, plus the new _query_framebuffer_geometry.

    pytest tests/ — 11 passed, unchanged by this work. No test in tests/
    exercises the rendering engine.

    What this does not establish: what this particular device reports. The
    whole value of the change is that the answer is now in the log at every
    start rather than assumed, and only gtach.local can supply it.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-49b21ace"
      relationship: "blocked_by"
    - change_ref: "change-66ef59a0"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-cb28980f"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-cb28980f."
  - version: "1.1"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status proposed -> implemented. Recorded implementation date, executor, verification date and development-platform test results."
      - "Recorded a qualification: the FBIOGET_FSCREENINFO criterion cannot be met literally, because the prompt's own EDIT 2 docstring names the ioctl in explaining why it is avoided. The ioctl is not used."
      - "Recorded an addition: an impossibly small stride is reported at ERROR and not trusted to size the mapping, as the prompt's edge_cases require and its EDIT 3 code did not implement; verified against a literal build, which sizes the buffer at half the panel."
      - "Recorded that _setup_page_flip, _wait_for_vsync and _pan_display are byte-identical to their previous text."
      - "Left active pending on-target test results per ai/task.md §8.2.1."

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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-cb28980f. |
| 1.1 | 2026-07-30 | Status proposed → implemented; development-platform test results recorded against a faked ioctl and sysfs surface, including one qualification and one addition. Left active pending on-target results. |

---

Copyright (c) 2026 William Watson. MIT License.
