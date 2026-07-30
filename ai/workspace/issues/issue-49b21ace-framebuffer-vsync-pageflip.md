Created: 2026 July 30

# Issue: Framebuffer Writes Are Unsynchronised with Panel Scan-Out

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-49b21ace"
  title: "The frame is written into the buffer the panel is actively scanning out, with no vertical-blank synchronisation and no page flip, producing a migrating tear seam"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "resolved"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-49b21ace"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Recommendations 3 and 4 (§9.1), both addressing finding §4.1.
    Task list reference: ai/task.md §7.3.4.

affected_scope:
  components:
    - name: "DisplayRenderingEngine._initialize_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
    - name: "DisplayRenderingEngine.cleanup"
      file_path: "src/gtach/display/rendering/engine.py"
  designs: []
  version: "0.2.67"

reproduction:
  prerequisites: >
    GTach running on gtach.local with the HyperPixel 2.1 Round panel.
    Any mode; the write path is unconditional.
  steps:
    - "Observe the panel while the display is updating."
    - "Look for a horizontal band that migrates vertically rather than a static join."
    - "Enable simulation mode from OPTIONS. The synthetic RPM sweeps every band boundary once per 6.28 s."
    - "Distinguish per display review §10.3: continuous flicker indicates tearing; flicker in bursts synchronised with band crossings indicates band thrash, which change-4c038bed already addresses."
  frequency: "always"
  reproducibility_conditions: >
    Structural. The write is unsynchronised on every frame regardless of
    content. Whether the resulting seam is perceptible depends on the beat
    between the write rate and the 60 Hz panel refresh.
  preconditions: >
    Legacy DPI fbdev path, dtoverlay=hyperpixel2r, KMS explicitly not
    used. SDL_VIDEODRIVER=dummy with no set_mode, so SDL provides no
    presentation path.
  test_data: >
    Framebuffer geometry read on target 2026-07-30 per ai/task.md §7.5.1:

      bits_per_pixel  32
      stride          1920
      geometry        480 480 480 480 32
      Size            921600
      YPanStep        1

    xres_virtual and yres_virtual both equal 480, so the device currently
    holds exactly one frame and there is no off-screen half to flip to.
    YPanStep of 1 confirms the driver implements panning, so
    FBIOPAN_DISPLAY is available in principle.
  error_output: "None. No exception is raised; the fault is visual."

behavior:
  expected: >
    A completed frame is presented without the panel ever scanning out a
    buffer that is partly the previous frame and partly the next.
  actual: >
    write_to_framebuffer seeks to offset zero and writes 921,600 bytes
    into the single buffer the display controller is actively reading
    (engine.py:388-389). The write loop runs at an independent, jittering
    rate near 60 Hz while the panel refreshes at 60 Hz. The beat between
    the two produces a tear seam that migrates vertically across the
    display — which the report identifies as the characteristic appearance
    of the reported symptom, a horizontal band of flicker rather than a
    static join.

    Two mechanisms the legacy Pi fbdev driver provides are unused:

    (a) No vertical-blank wait. FBIO_WAITFORVSYNC would let the write
    begin immediately after scan-out completes, confining it to the
    blanking interval rather than starting at an arbitrary scan
    position.

    (b) No page flip. FBIOPAN_DISPLAY changes the address the controller
    scans from, presenting a completed frame atomically. The driver
    reports YPanStep 1, so it supports panning; but yres_virtual is 480,
    so no second buffer currently exists to pan to.

    Change-4c038bed has since removed band thrash and value churn as
    candidate causes, and change-66ef59a0 removed the per-frame
    flush/sync/fsync that lengthened the write window. If flicker
    persists after those, this finding is the remaining explanation.
  impact: >
    The display is the product. A migrating tear seam is the reported
    symptom that initiated the display review, and after 4c038bed and
    66ef59a0 this is the last untreated candidate for it. Severity is
    recorded as High on that basis rather than on the report's own risk
    rating, which measures implementation risk rather than user impact.
  workaround: >
    None within the application. Reducing the frame rate changes the beat
    frequency and therefore how the seam moves, but does not remove it.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) 6.1.21-v8+, Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    The engine treats /dev/fb0 as a byte sink rather than as a display
    device with a scan-out cycle. Because SDL is used only as a software
    rasteriser — dummy driver, set_mode never called — there is no
    presentation step to inherit synchronisation from, and none was built
    in its place. Writing directly into the scanned buffer is correct only
    if the write is either atomic with respect to scan-out or confined to
    the blanking interval, and it is neither.
  technical_notes: >
    The two recommendations are alternative mechanisms for the same
    problem, not additive improvements. If page flipping is available, the
    frame is composed in a half the controller is not reading, so no
    pre-write vertical-blank wait is needed; the pan itself is what must
    be synchronised. If page flipping is unavailable, the vertical-blank
    wait is the fallback that narrows the tear window in the
    single-buffer write. The change document treats them as a degradation
    chain on that basis.

    Constant correction. The report cites FBIO_WAITFORVSYNC as 0x4620.
    That is the type and number portion only. In linux/fb.h the constant
    is declared _IOW('F', 0x20, __u32), which encodes direction and
    argument size as well:

      (1 << 30) | (4 << 16) | (0x46 << 8) | 0x20  =  0x40044620

    The other framebuffer ioctls in the same header are plain values and
    need no encoding: FBIOGET_VSCREENINFO 0x4600, FBIOPUT_VSCREENINFO
    0x4601, FBIOPAN_DISPLAY 0x4606. Some drivers mask the encoding bits
    and accept the bare 0x4620; relying on that is not safe.

    Doubling yres_virtual may fail. The Pi's DPI framebuffer is allocated
    at boot from firmware configuration, and FBIOPUT_VSCREENINFO cannot
    always enlarge it afterwards. If it fails, enabling page flipping may
    require a boot configuration change on the target — which is an
    operator action outside the application's control, not something the
    change can perform. The degradation path therefore has to be real
    rather than notional.

    struct fb_var_screeninfo is 40 unsigned 32-bit fields, 160 bytes.
    yres_virtual is field index 3, yoffset index 5, activate index 21.

    utils/terminal.py demonstrates the project's existing ioctl call
    pattern and is the reference for house style.
  related_issues:
    - issue_ref: "issue-66ef59a0"
      relationship: "blocked_by"
    - issue_ref: "issue-cb28980f"
      relationship: "related"
    - issue_ref: "issue-4c038bed"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Attempt to establish a second buffer by doubling yres_virtual, and
    present by panning. Fall back to a vertical-blank wait before a
    single-buffer write, and then to the current unsynchronised write.
    Each fallback is taken once, at initialisation where possible, and
    logged. See change-49b21ace.
  change_ref: "change-49b21ace"
  resolved_date: "2026-07-30"
  resolved_by: "Claude Code, per prompt-49b21ace"
  fix_description: >
    Eight edits to src/gtach/display/rendering/engine.py, as specified, plus
    three departures from the prompt's literal text — two of them necessary,
    recorded below and in change-49b21ace verification.test_results.

    The engine now decides its presentation mode once, in
    _initialize_framebuffer, and logs it at INFO. _setup_page_flip reads
    fb_var_screeninfo, doubles yres_virtual, writes it back, re-reads to see
    what the driver actually granted, and remaps over both halves only if
    the grant is at least twice yres. _wait_for_vsync issues
    FBIO_WAITFORVSYNC and disables itself on failure. _pan_display presents
    a half by setting yoffset and issuing FBIOPAN_DISPLAY. write_to_framebuffer
    writes to the half the controller is not scanning and pans, or waits for
    blanking and writes at offset zero, or writes at offset zero with no
    ioctl at all. cleanup restores the captured original screen info inside
    a guard that cannot prevent the close.

    FBIO_WAITFORVSYNC is 0x40044620, as the prompt derives. The derivation
    was checked independently: _IOW('F', 0x20, __u32) is
    (1 << 30) | (4 << 16) | (0x46 << 8) | 0x20, which is 0x40044620. The
    report's 0x4620 is the type and number portion only. 0x4620 appears in
    the file solely inside the comment explaining why it is wrong.

    Departure 1, necessary. The prompt's _setup_page_flip closes the
    existing mapping and then remaps:

        self.fb.close()
        self.fb = mmap.mmap(self.fb_dev.fileno(), self.fb_size * 2)

    If the remap raises — which it does whenever the driver grants the
    resize but the mapping cannot actually be extended — self.fb is left
    closed. page_flip is then False, so every subsequent frame takes the
    single-buffer path and calls seek on a closed mmap, raising ValueError
    into the general handler: no frame is ever delivered again and the panel
    stays blank. This contradicts the prompt's own design note, which
    requires the existing mapping to be left intact on failure. The new
    mapping is therefore established first and the old one closed only
    after it succeeds.

    Departure 2, necessary. The prompt's _pan_display builds its ioctl
    argument from self._original_var, the struct captured before the resize,
    whose yres_virtual is one frame. Panning to the second half then sends a
    struct in which yoffset is 480 while yres_virtual is 480 — internally
    inconsistent. Mainline Linux fb_pan_display validates yoffset against
    info->var.yres_virtual, the driver's own state, so it would accept this;
    a driver that validates the struct it was handed rejects it, and the
    first pan then fails, disabling page flipping permanently. Since the
    whole point of the re-read is to act on what the driver granted, the
    confirmed post-resize struct is kept as the pan template and
    _original_var is reserved for cleanup, its documented purpose.

    Departure 3, defensive. The prompt guards each ioctl helper with
    `if not self.fb_dev`. On the direct-file fallback path
    _initialize_framebuffer closes fb_dev but leaves the attribute bound, so
    that guard passes and fileno() then raises ValueError on a closed file —
    caught and logged, but as a misleading "Vertical-blank wait
    unavailable: I/O operation on closed file". A _fb_dev_usable() helper
    tests for both. No test failure is attributable to this change; it is a
    log-quality improvement, not a correction.

verification:
  verified_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Development platform only (macOS, Python 3.11.14, pygame 2.6.1). The
    ioctls cannot be exercised natively, so they were driven against a fake
    driver emulating the kernel's semantics — FBIOGET/PUT_VSCREENINFO,
    FBIOPAN_DISPLAY and FBIO_WAITFORVSYNC — over a real mmap of a temporary
    file. Eighty-six assertions, all passing. See change-49b21ace
    verification.test_results for the full record.

    All three presentation modes were exercised end to end, including the
    alternation of halves, every documented fallback, and both cleanup
    paths. The two necessary departures above were confirmed load-bearing
    by reverting them and re-running: the suite then fails four assertions,
    and the remap-failure case leaves the engine with a closed mapping and
    no way to deliver a frame.

    pytest tests/ — 11 passed, unchanged by this work.

    This issue is left active pending on-target results per ai/task.md
    §8.2.1. Nothing here establishes that tearing is gone; only that the
    mechanism behaves correctly and degrades as designed.
  closure_notes: ""

prevention:
  preventive_measures: >
    A device write path should be built against the device's own
    contract. Where a kernel interface exposes synchronisation
    primitives, not using them is a decision that should be recorded
    rather than defaulted into.
  process_improvements: >
    Constants copied from a report should be checked against the kernel
    header that defines them. The FBIO_WAITFORVSYNC value in the source
    report is the unencoded form and would not have worked as written on
    a driver that validates the encoding.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."
    - "On gtach.local, read the log at startup and confirm which presentation mode was selected: page flip, vsync-synchronised write, or plain write."
    - "If page flip was selected: confirm fbset -i reports yres_virtual 960 while the application runs."
    - "Observe the panel in RADIAL and DIGITAL modes and confirm no migrating horizontal band."
    - "Enable simulation mode and observe through several full sweeps; confirm no tear seam appears at any RPM."
    - "Confirm frame_time_ms from the periodic log line has not risen materially — a vertical-blank wait blocks, so the render budget must still be met."
    - "Force each fallback in turn — by patching the ioctl to raise — and confirm the display still renders in every mode."
    - "Confirm cleanup restores yres_virtual and yoffset to their original values and that the panel is usable after the application exits."
  verification_results: >
    Two of the eight steps are complete off-target, one is complete against
    an emulated driver, and five require gtach.local. Every step that
    depends on observing the panel is outstanding: this change cannot be
    judged without it.

    PASS — python -m py_compile src/gtach/display/rendering/engine.py.

    PASS (emulated) — force each fallback in turn and confirm the display
    still renders. All four degradation paths were driven by making the fake
    driver refuse the relevant ioctl: FBIOPUT_VSCREENINFO raising EINVAL; a
    put that succeeds but grants only one frame; a granted resize whose
    remap then fails; and FBIOPAN_DISPLAY failing at runtime after page
    flipping was active. In every case the frame is still delivered, the
    engine falls back exactly one stage, and the reason is logged once at
    INFO. The direct-file fallback path attempts no resize at all.

    PASS (emulated) — cleanup restores yres_virtual and yoffset. The
    restore issues FBIOPUT_VSCREENINFO with the captured original struct,
    returning yres_virtual to 480 and yoffset to 0, and both the mapping and
    the device are closed afterwards. With the restore forced to raise, the
    warning is logged and both are still closed. Whether the console is
    usable after exit can only be seen on the device.

    OUTSTANDING — read the startup log on gtach.local and record which of
    the three modes was selected. Every other on-target observation is
    uninterpretable without it. The prompt expects page flip to be refused
    on this target, the Pi's DPI framebuffer being allocated at boot from
    firmware configuration; if so the vertical-blank wait is the operative
    path.

    OUTSTANDING — if page flip was selected, confirm fbset -i reports
    yres_virtual 960 while the application runs.

    OUTSTANDING — observe RADIAL and DIGITAL for a migrating horizontal
    band. This is the observation the issue exists to satisfy.

    OUTSTANDING — observe several full sweeps in simulation mode for a tear
    seam at any RPM.

    OUTSTANDING — confirm frame_time_ms has not risen materially. This
    matters most in the vsync-synchronised mode, where the wait blocks for
    up to one refresh interval inside the frame budget; it is the plausible
    regression this change could introduce. Note that the ai/task.md §7.5.3
    baseline has still not been recorded — it is the outstanding step of the
    closed triple 0b00759c — so "has not risen" has no reference figure yet.

traceability:
  design_refs: []
  change_refs:
    - "change-49b21ace"
  test_refs: []

notes: >
  This is task 7.3.4 in ai/task.md §7.3. Its §7.6.1 dependency on §7.5.1
  was cleared on 2026-07-30: the geometry read confirmed 32 bits per
  pixel and a 1920-byte stride, so display review §8.3 is not an active
  fault and the assumption the engine makes about the buffer is correct.

  The report ranks recommendation 4 as Medium risk and notes it depends
  on §8.3 being resolved first. It is, so the dependency is discharged.
  Recommendation 3 is ranked Low risk with the qualification "degrade
  gracefully if EINVAL", which the degradation chain implements.

  §7.5.2 — characterising the flicker — remains unobserved. It does not
  gate this work: the finding is structural and the correction is right
  regardless. What §7.5.2 determines is priority. If the flicker proves
  to have been band thrash, already corrected by 4c038bed, this becomes
  an efficiency and correctness improvement rather than the fix for the
  reported symptom.

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
      - "Initial issue document from display-ui-graphics-review.md recommendations 3 and 4."
  - version: "1.1"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status open -> resolved. change-49b21ace implemented; resolution date, executor and fix description recorded."
      - "Recorded two necessary departures from the prompt's literal text: the remap must precede the close of the old mapping, and the pan template must be the confirmed post-resize struct rather than _original_var."
      - "Recorded one defensive departure: the ioctl guards test whether fb_dev is open, not merely bound."
      - "Confirmed the FBIO_WAITFORVSYNC encoding independently as 0x40044620."
      - "Recorded three verification steps as complete and five as OUTSTANDING; every panel observation requires gtach.local."
      - "Noted that the frame_time_ms step has no reference figure until the ai/task.md §7.5.3 baseline is recorded."
      - "Left active pending on-target test results per ai/task.md §8.2.1."

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
| 1.0 | 2026-07-30 | Initial issue document from display-ui-graphics-review.md recommendations 3 and 4. |
| 1.1 | 2026-07-30 | Status open → resolved; fix description and per-step verification recorded, including two necessary departures from the prompt's literal text. Left active pending on-target results. |

---

Copyright (c) 2026 William Watson. MIT License.
