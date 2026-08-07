Created: 2026 July 30

# Issue: Framebuffer Geometry Is Assumed Rather Than Queried, and a Mismatch Is Logged at DEBUG

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-cb28980f"
  title: "fb_size is computed as width x height x 4 with no reference to the device's reported depth or stride, and a resulting size mismatch is silently corrected and logged at DEBUG"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-cb28980f"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Recommendation 21 (§9.4) addressing finding §8.3.
    Task list reference: ai/task.md §7.3.3.

affected_scope:
  components:
    - name: "DisplayRenderingEngine._initialize_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
  designs: []
  version: "0.2.67"

reproduction:
  prerequisites: >
    Any framebuffer device whose depth or stride differs from the
    engine's assumption. The fault is latent on the current target.
  steps:
    - "Read _initialize_framebuffer and observe fb_size derived as surface_size[0] * surface_size[1] * 4."
    - "Observe that neither bits_per_pixel nor line_length is read from the device."
    - "Read write_to_framebuffer and observe that a size mismatch is truncated or zero-padded and logged at DEBUG."
    - "On a device with a padded stride, observe that the resulting image is skewed rather than failing."
  frequency: "always"
  reproducibility_conditions: >
    The assumption itself is unconditional. Its consequences appear only
    where the device does not match it. On the current target it does
    match, so the fault is latent rather than active.
  preconditions: >
    docs/Debian_boot.txt.md sets dpi_output_format 0x7f216, an 18-bit
    6:6:6 panel format, and does not set framebuffer_depth. The engine
    nonetheless assumes 32 bits per pixel.
  test_data: >
    Geometry read on target 2026-07-30 per ai/task.md §7.5.1:
    bits_per_pixel 32, stride 1920, geometry 480 480 480 480 32,
    Size 921600. The assumption holds exactly on this device:
    480 x 480 x 4 = 921,600 and 480 x 4 = 1920.
  test_data_note: ""
  error_output: >
    None on the current target. On a mismatched device the symptom is a
    skewed or partially blank image with a DEBUG line that is not emitted
    at the production log level.

behavior:
  expected: >
    The engine reads the device's authoritative geometry and sizes its
    buffer from it. A discrepancy between what the device reports and
    what the engine can produce is reported at a severity that reaches the
    operator.
  actual: >
    Two faults.

    (a) Geometry is assumed. _initialize_framebuffer computes
    fb_size = surface_size[0] * surface_size[1] * 4, taking both the
    32-bit depth and a stride equal to width x 4 on faith. The device
    exposes both authoritatively and neither is consulted.

    (b) A mismatch is corrected silently. write_to_framebuffer compares
    the payload size against fb_size and, on a difference, truncates or
    zero-pads and logs at DEBUG (engine.py:565-566). Production runs at
    INFO, so the line is never emitted. Truncation or a stride mismatch
    produces a skewed or partially blank image rather than a clean
    failure, and the one diagnostic that would explain it is invisible.

    A stride mismatch is the more damaging case and the padding does not
    address it at all: padding corrects the total byte count while
    leaving every row after the first offset by the difference, which
    renders as a diagonal shear.
  impact: >
    Latent on the current target, which matches the assumption exactly.
    The report notes that the presence of dedicated ENOSPC recovery logic
    suggests a size mismatch has been encountered on hardware at some
    point, so the condition is not hypothetical. The cost of the fault is
    paid entirely at diagnosis time: a skewed display with no log line
    explaining it.
  workaround: >
    Running with --debug surfaces the existing DEBUG line, but only if the
    operator already suspects the framebuffer.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) 6.1.21-v8+, Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    The engine was written against a known panel and encoded that panel's
    properties as constants. That is correct until the device disagrees,
    at which point there is no mechanism to notice. The DEBUG log level
    reflects the same assumption: a mismatch was treated as a curiosity
    rather than as a fault, because it was not expected to occur.
  technical_notes: >
    Scope has narrowed since this task was planned. change-49b21ace has
    since introduced fcntl, struct, the FB_VAR_STRUCT layout and a working
    FBIOGET_VSCREENINFO call, together with the _fb_dev_usable guard. The
    remaining work is to use that infrastructure to derive fb_size rather
    than assume it, to obtain the stride, and to raise the log level.

    Departure from the report's literal instruction. The report names
    FBIOGET_FSCREENINFO as the source for line_length. struct
    fb_fix_screeninfo contains two unsigned long fields whose size and
    alignment differ between 32-bit and 64-bit builds, so unpacking it
    correctly requires architecture-dependent offset arithmetic. The
    sysfs attribute /sys/class/graphics/fb0/stride exposes the same value
    as text and is stable across architectures. Reading sysfs first and
    falling back to a derivation from xres_virtual and bits_per_pixel is
    both simpler and less likely to be wrong, and it is the same source
    the §7.5.1 observation used.

    The ordering in _initialize_framebuffer must change. fb_size is
    currently computed before the mmap, and _setup_page_flip then remaps
    at twice that value. Deriving fb_size from the device therefore has to
    happen before the mmap, which means opening fb_dev first and querying
    through it.

    An observation for a future cycle, not taken here. fb_fix_screeninfo
    also reports smem_len, the total video memory. On the current target
    Size is 921,600 — exactly one frame — which means change-49b21ace's
    attempt to double yres_virtual cannot succeed for want of memory. If
    smem_len were queried, _setup_page_flip could report that
    definitively rather than discovering it from an ioctl failure. That
    would modify a closed triple's code and is recorded rather than done.
  related_issues:
    - issue_ref: "issue-66ef59a0"
      relationship: "related"
    - issue_ref: "issue-49b21ace"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Query the device's depth, resolution and stride at initialisation;
    derive fb_size from stride and height rather than from the surface
    dimensions; report a geometry disagreement at ERROR; raise the
    write-path mismatch log from DEBUG to ERROR. See change-cb28980f.
  change_ref: "change-cb28980f"
  resolved_date: "2026-07-30"
  resolved_by: "Claude Code, per prompt-cb28980f"
  fix_description: >
    Four edits to src/gtach/display/rendering/engine.py, as specified, plus
    one addition covered below.

    _query_framebuffer_geometry reads xres, yres, xres_virtual and
    bits_per_pixel from FBIOGET_VSCREENINFO and the stride from
    /sys/class/graphics/<node>/stride, where <node> is the basename of
    framebuffer_path, falling back to xres_virtual x bits_per_pixel // 8
    when sysfs cannot be read. It logs the geometry and the stride source at
    INFO and returns None on any failure, logging at WARNING.

    _initialize_framebuffer opens the device, queries before mapping — the
    ordering matters because _setup_page_flip remaps at twice fb_size — and
    sizes fb_size as line_length x yres. Three disagreements are reported at
    ERROR and none is fatal: a depth other than 32, a resolution differing
    from the composed surface, and a stride differing from
    xres x bits_per_pixel // 8. Where the query fails the previous
    width x height x 4 assumption stands and the fallback is logged at
    WARNING.

    The write-path size mismatch moves from DEBUG to ERROR, guarded by
    _size_mismatch_logged so it fires once rather than at the frame rate,
    and counted in _size_mismatch_count. The message carries the stride and
    depth so the line is self-contained. cleanup reports a non-zero total.
    The truncate and pad behaviour is untouched.

    Addition: an impossibly small stride is not trusted to size the buffer.
    The prompt's edge_cases require that a line_length below
    xres x bpp // 8 be logged at ERROR and the assumption used instead, but
    EDIT 3's code guards only against zero and would size the mapping from
    the impossible value. A device reporting stride 960 for 480 px at 32-bit
    would then get fb_size 460,800 — half the buffer — and every frame
    truncated to half the panel. The stated requirement is implemented: such
    a stride is reported at ERROR, recorded in fb_line_length for the
    diagnostic, and the composed-surface assumption is used for the mapping.
    A stride at or above the minimum is the device's own account of its
    layout and still governs, so the padded-row case is unaffected.

verification:
  verified_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Development platform only (macOS, Python 3.11.14, pygame 2.6.1). The
    ioctl and sysfs surfaces do not exist here, so both were faked and the
    real engine driven against them over a real mmap. Seventy assertions,
    all passing. See change-cb28980f verification.test_results for the full
    record.

    On the geometry this target actually reports — 480x480, 32-bit, stride
    1920 — the derived fb_size is 921,600, identical to the previous
    assumption, and no ERROR is emitted. That is the result the change
    predicts for the current device.

    pytest tests/ — 11 passed, unchanged by this work.

    This issue is left active pending on-target results per ai/task.md
    §8.2.1.
  closure_notes: ""

prevention:
  preventive_measures: >
    Where a device exposes its own configuration, read it rather than
    encode it. Where a condition is corrected silently because it was not
    expected, the correction should be logged at a level the production
    configuration actually emits.
  process_improvements: >
    A log level is part of a diagnostic's contract. A DEBUG line
    describing a condition that produces a visible fault is equivalent to
    no line at all.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."
    - "On gtach.local, confirm the startup log reports the queried geometry: bits_per_pixel 32, stride 1920, derived fb_size 921600."
    - "Confirm the derived fb_size equals the previously assumed value on this device, so no behaviour changes on the current target."
    - "Confirm the display renders correctly in every mode, unchanged from v0.2.67."
    - "Unit test: with a mocked device reporting 16 bits per pixel, confirm an ERROR is logged and fb_size reflects the reported stride."
    - "Unit test: with a mocked stride of 2048 against a width of 480, confirm the stride disagreement is logged at ERROR."
    - "Unit test: with the geometry query unavailable, confirm the engine falls back to the current assumption and logs the fallback."
    - "Confirm the write-path mismatch is logged at ERROR, not DEBUG."
  verification_results: >
    Five of the eight steps are complete; three require gtach.local.

    PASS — python -m py_compile src/gtach/display/rendering/engine.py.

    PASS — with a mocked device reporting 16 bits per pixel, one ERROR is
    logged naming the depth, fb_size follows the reported stride, and
    initialisation continues with a live mapping.

    PASS — with a mocked stride of 2048 against a width of 480 at 32-bit,
    the stride disagreement is logged at ERROR naming both figures, fb_size
    becomes 2048 x 480, and the message states that zero-padding corrects
    the byte count but not the row offset.

    PASS — with FBIOGET_VSCREENINFO raising, the query returns None, the
    engine retains the 921,600-byte assumption, and two WARNINGs are logged:
    the query failure and the assumption being used. No ERROR is emitted,
    because an unavailable query is not a disagreement.

    PASS — the write-path mismatch is logged at ERROR rather than DEBUG.
    Across three mismatched frames exactly one ERROR is emitted, the count
    reaches three, the message carries the stride and depth, and both the
    pad and truncate directions still behave as before. cleanup then reports
    the total once, and is silent when no mismatch occurred.

    OUTSTANDING — on gtach.local, confirm the startup log reports
    bits_per_pixel 32, stride 1920 and fb_size 921,600. This is the step
    that turns the §7.5.1 manual observation into something checked at every
    start.

    OUTSTANDING — confirm the derived fb_size equals the previously assumed
    value on this device, so nothing changes behaviourally on the current
    target. Off-target this holds for the reported geometry; only the device
    can confirm what it reports.

    OUTSTANDING — confirm the display renders correctly in every mode,
    unchanged from v0.2.67. If an ERROR appears in the startup log instead,
    the device disagrees with an assumption the engine has been making
    silently, and that is the finding rather than a regression.

traceability:
  design_refs: []
  change_refs:
    - "change-cb28980f"
  test_refs: []

notes: >
  This is task 7.3.3 in ai/task.md §7.3.

  Its role has changed since the plan was written. §7.6.1 recorded 7.3.4
  as depending on 7.3.3 for the geometry facts, and §8.3 of the task list
  noted that implementing 7.3.3 would make the application self-report
  those facts and so clear its own gate. The manual §7.5.1 observation on
  2026-07-30 supplied them first, and 7.3.4 has since been implemented.
  This task is therefore no longer a prerequisite for anything: it is
  defensive hardening plus a log-level correction.

  That is a reduction in urgency, not in value. The observation confirms
  the geometry of one device at one moment; the query confirms it at every
  start, on every device.

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
      - "Initial issue document from display-ui-graphics-review.md recommendation 21."
  - version: "1.1"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status open -> resolved. change-cb28980f implemented; resolution date, executor and fix description recorded."
      - "Recorded one addition beyond the prompt's EDIT 3: an impossibly small stride is reported at ERROR and not trusted to size the mapping, which the prompt's edge_cases require but its code block did not implement."
      - "Recorded five of eight verification steps as PASS and three as OUTSTANDING pending gtach.local."
      - "Recorded that on the geometry this target reports the derived fb_size is 921,600, identical to the previous assumption, so no behavioural change is expected here."
      - "Left active pending on-target test results per ai/task.md §8.2.1."
  - version: "1.2"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status resolved -> closed. Source re-check confirms the fix present and unchanged. Closed on William's confirmation that GTach functions correctly on gtach.local."

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
| 1.0 | 2026-07-30 | Initial issue document from display-ui-graphics-review.md recommendation 21. |
| 1.1 | 2026-07-30 | Status open → resolved; fix description and per-step verification recorded, including the impossible-stride addition. Left active pending on-target results. |
| 1.2 | 2026-08-07 | Status resolved → closed. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
