Created: 2026 July 30

# Change: Present by Page Flip, Falling Back to a Vertical-Blank Wait

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-49b21ace"
  title: "Establish a second framebuffer half and present with FBIOPAN_DISPLAY; fall back to FBIO_WAITFORVSYNC before a single-buffer write, then to the current unsynchronised write"
  date: "2026-07-30"
  author: "William Watson"
  status: "implemented"
  priority: "high"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-49b21ace"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-49b21ace"
  description: >
    Resolves issue-49b21ace. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0
    recommendations 3 and 4. Task list reference ai/task.md §7.3.4.

scope:
  summary: >
    Give the frame a presentation step. At initialisation, attempt to
    double yres_virtual and map two frame-sized halves; if that succeeds,
    compose into the half the controller is not scanning and present by
    panning. If it fails, wait for vertical blank before the existing
    single-buffer write. If that also fails, write as now. The selected
    mode is decided once at initialisation and logged.
  affected_components:
    - name: "DisplayRenderingEngine.__init__"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine._initialize_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine._setup_page_flip"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "add"
    - name: "DisplayRenderingEngine._wait_for_vsync"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "add"
    - name: "DisplayRenderingEngine._pan_display"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "add"
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine.cleanup"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Querying geometry via FBIOGET_FSCREENINFO and raising the mismatch log level — recommendation 21, task 7.3.3. This change reads FBIOGET_VSCREENINFO only, and only to modify and write it back."
    - "The buffer-view write path established by change-66ef59a0. The payload acquisition, size check and truncate/pad behaviour are unchanged; only the destination offset and what follows the write differ."
    - "Caching the static layer, reducing fps_limit or skipping frames — tasks 7.3.5 and 7.3.6."
    - "Boot configuration on the target. If the driver will not enlarge the virtual resolution, a config.txt change may be required; that is an operator action and is not performed by this change."
    - "Migrating to KMS. docs/pi-setup.md records the legacy fbdev path as an explicit choice."
    - "swap_buffers. It remains the documented no-op established by change-66ef59a0."

rational:
  problem_statement: >
    The frame is written into the single buffer the panel is actively
    scanning out, at a rate that beats against the 60 Hz refresh, so the
    controller can read a buffer that is part previous frame and part
    next. The driver provides both mechanisms needed to prevent this —
    FBIO_WAITFORVSYNC and FBIOPAN_DISPLAY — and neither is used. After
    change-4c038bed removed band thrash and change-66ef59a0 removed the
    per-frame synchronisation that widened the write window, this is the
    remaining structural explanation for the reported flicker.
  proposed_solution: >
    Prefer page flipping: double yres_virtual through
    FBIOPUT_VSCREENINFO, map both halves, compose into the off-screen
    half and present by setting yoffset through FBIOPAN_DISPLAY. Where
    that is unavailable, precede the single-buffer write with a
    FBIO_WAITFORVSYNC so the write begins in the blanking interval.
    Where that is also unavailable, behave exactly as today.
  alternatives_considered:
    - option: "Implement only recommendation 3, the vertical-blank wait."
      reason_rejected: >
        It narrows the tear window rather than closing it. A 921,600-byte
        Python-level write will not reliably complete within the blanking
        interval on a Cortex-A53, so a seam can still appear. It is the
        right fallback, not the right primary.
    - option: "Implement only recommendation 4, the page flip."
      reason_rejected: >
        Leaves no improvement at all on a device that will not enlarge its
        virtual resolution — which is a real possibility on this hardware,
        since the DPI framebuffer is allocated at boot from firmware
        configuration.
    - option: "Apply both unconditionally — wait for vertical blank and then pan."
      reason_rejected: >
        They address the same problem by different means. With page
        flipping the frame is composed in a half the controller is not
        reading, so a pre-write wait blocks the render thread for no
        benefit. Treating them as additive would cost a frame period per
        frame.
    - option: "Retry the page-flip setup periodically at runtime if it fails at initialisation."
      reason_rejected: >
        The virtual resolution does not change while the device is open.
        A per-frame or periodic retry would add an ioctl to the frame path
        to test a condition that cannot change. The decision is taken once.
    - option: "Use FB_ACTIVATE_VBL on the pan so the driver defers the flip to the next blanking interval."
      reason_rejected: >
        Not rejected outright — it is the preferred flag and the change
        specifies it — but it must not be relied upon exclusively, because
        some drivers ignore it. The implementation sets it and does not
        assume it was honoured.
  benefits:
    - "Removes the mechanism by which a partially updated buffer can reach the panel, rather than narrowing the window in which it can."
    - "Degrades in two stages, so no target is left worse off than today."
    - "The selected mode is logged once at startup, so which path a given device took is answerable from the log rather than by inference."
  risks:
    - risk: >
        FBIOPUT_VSCREENINFO fails because the driver cannot enlarge the
        allocation, so page flipping is unavailable on the actual target.
      mitigation: >
        Expected and handled: the fallback to a vertical-blank wait is
        the operative path in that case, and it is an improvement on the
        current behaviour. Log the failure at INFO with the driver's
        errno so the operator can judge whether a boot-configuration
        change is worth making. Do not treat it as an error.
    - risk: >
        The vertical-blank wait blocks the display thread for up to one
        frame period, reducing time available for rendering and holding
        the GIL against the OBD thread.
      mitigation: >
        The wait returns at the start of blanking, so the budget lost is
        the remainder of the current scan-out — time the loop would
        otherwise have spent in its own pacing sleep. Confirm on target
        that frame_time_ms has not risen materially; if it has, the wait
        is costing more than it saves and should be reconsidered against
        the §7.5.3 baseline.
    - risk: >
        Doubling yres_virtual leaves the panel in a modified state if the
        process exits without restoring it.
      mitigation: >
        Capture the original fb_var_screeninfo at initialisation and
        restore yres_virtual and yoffset in cleanup. Wrap the restore so a
        failure there cannot mask the shutdown path.
    - risk: >
        Writing to the off-screen half addresses the wrong offset and the
        panel shows the wrong half, or nothing.
      mitigation: >
        The offset is fb_size for the second half and zero for the first,
        with fb_size already verified against the device: 480 x 480 x 4 =
        921,600, matching the reported Size exactly (§7.5.1). A fault here
        is immediately visible on the panel.
    - risk: >
        A partially applied FBIOPUT_VSCREENINFO leaves yres_virtual
        doubled but the mmap sized for one frame, so writes to the second
        half fall outside the mapping.
      mitigation: >
        Re-read the variable screen info after the put and act on what the
        driver actually granted, not on what was requested. Only enable
        page flipping if the re-read confirms yres_virtual is at least
        twice yres. Size the mmap from the confirmed value.

technical_details:
  current_behavior: >
    _initialize_framebuffer (engine.py:132-156) computes fb_size as
    width x height x 4 and maps exactly that many bytes, falling back to
    direct file writing if mmap fails. write_to_framebuffer
    (engine.py:317-411) acquires a buffer view of back_surface, checks
    its size, then seeks to zero and writes (engine.py:388-389). Nothing
    consults the panel's scan-out position.
  proposed_behavior: >
    _initialize_framebuffer additionally attempts page-flip setup. If it
    succeeds, the mapping covers two frames and a buffer index selects
    which half receives the frame; write_to_framebuffer seeks to
    index x fb_size, writes, pans to present that half, and toggles the
    index. If it fails, write_to_framebuffer waits for vertical blank and
    then writes at offset zero as before. If the vertical-blank ioctl also
    fails, it is disabled after the first failure and the write proceeds
    unsynchronised.
  implementation_approach: >
    Seven edits in src/gtach/display/rendering/engine.py.

    EDIT 1 — module imports and constants. Add `import fcntl` and
    `import struct`. Define the ioctl constants at module scope with the
    derivation of the encoded one recorded in a comment:

      FBIOGET_VSCREENINFO = 0x4600
      FBIOPUT_VSCREENINFO = 0x4601
      FBIOPAN_DISPLAY     = 0x4606
      FBIO_WAITFORVSYNC   = 0x40044620   # _IOW('F', 0x20, __u32)
      FB_ACTIVATE_NOW     = 0
      FB_ACTIVATE_VBL     = 16
      FB_VAR_STRUCT       = '40I'        # 40 x __u32, 160 bytes
      FB_VAR_YRES_VIRTUAL = 3
      FB_VAR_YOFFSET      = 5
      FB_VAR_ACTIVATE     = 21

    EDIT 2 — __init__. Add presentation state: self.page_flip = False,
    self.vsync_available = False, self.buffer_index = 0,
    self._original_var = None, self._vsync_failed_logged = False.

    EDIT 3 — _initialize_framebuffer. After the existing mmap succeeds and
    use_mmap is True, call self._setup_page_flip(). Page flipping requires
    the mmap path; if the direct-file fallback was taken, leave page_flip
    False. After that, probe the vertical-blank ioctl once and record
    vsync_available. Log the selected mode at INFO: page flip, vsync
    write, or plain write.

    EDIT 4 — add _setup_page_flip(). Read fb_var_screeninfo via
    FBIOGET_VSCREENINFO on self.fb_dev, retain a copy as
    self._original_var, set yres_virtual to twice yres and activate to
    FB_ACTIVATE_NOW, write it back with FBIOPUT_VSCREENINFO, then re-read
    and verify the driver granted at least twice yres. On success,
    remap self.fb over two frames and set page_flip True. On any failure,
    log at INFO with the errno, leave page_flip False and leave the
    existing single-frame mapping intact. Return bool.

    EDIT 5 — add _wait_for_vsync(). Issue FBIO_WAITFORVSYNC on
    self.fb_dev with a packed zero argument. On failure set
    vsync_available False, log once at INFO, and return False. Return
    True on success.

    EDIT 6 — add _pan_display(index). Set yoffset to index x yres and
    activate to FB_ACTIVATE_VBL, issue FBIOPAN_DISPLAY. Return bool; on
    failure log once and return False so the caller can fall back.

    EDIT 7 — write_to_framebuffer. Leave the payload acquisition, the
    .length size check and the truncate/pad path exactly as
    change-66ef59a0 left them. Replace the seek-and-write block with:

      - If page_flip: target = self.buffer_index xor 1; seek to
        target x fb_size; write; if _pan_display(target) succeeds, set
        buffer_index = target. If the pan fails, disable page_flip and
        continue at offset zero from the next frame.
      - Else: if vsync_available, call _wait_for_vsync() first; then
        seek to zero and write, as now.

    EDIT 8 — cleanup. Before closing the mapping, if _original_var is
    not None, restore yres_virtual and yoffset by writing the captured
    struct back with FBIOPUT_VSCREENINFO. Guard it so a failure here
    cannot prevent the rest of cleanup from running.
  code_changes:
    - component: "DisplayRenderingEngine"
      file: "src/gtach/display/rendering/engine.py"
      change_summary: >
        Page-flip setup and teardown, vertical-blank wait and pan
        helpers, presentation-mode selection at initialisation, and a
        write path that targets the off-screen half and presents by
        panning when available.
      functions_affected:
        - "__init__"
        - "_initialize_framebuffer"
        - "_setup_page_flip"
        - "_wait_for_vsync"
        - "_pan_display"
        - "write_to_framebuffer"
        - "cleanup"
      classes_affected:
        - "DisplayRenderingEngine"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "change-66ef59a0"
      impact: "Must land first. This change edits the single clean write that 66ef59a0 leaves behind; applying it to the previous four-traversal path would conflict."
    - component: "DisplayManager._display_loop"
      impact: "Calls write_to_framebuffer. No call-site change. Note the loop's own pacing sleep now overlaps a possible blocking vertical-blank wait."
  external:
    - library: "fcntl, struct"
      version_change: "none"
      impact: "Standard library; newly imported in engine.py."
  required_changes:
    - change_ref: "change-66ef59a0"
      relationship: "blocked_by"

testing_requirements:
  test_approach: >
    Unit tests on the development platform with fcntl.ioctl mocked, since
    no framebuffer device exists there, plus on-target confirmation which
    is the only way to observe the actual effect on tearing.
  test_cases:
    - scenario: "_setup_page_flip where the driver grants twice yres."
      expected_result: "page_flip True; mmap length is twice fb_size; _original_var captured."
    - scenario: "_setup_page_flip where FBIOPUT_VSCREENINFO raises OSError."
      expected_result: "page_flip False; the original single-frame mapping is intact; one INFO logged with the errno; no exception propagates."
    - scenario: "_setup_page_flip where the put succeeds but the re-read reports yres_virtual unchanged."
      expected_result: "page_flip False. The driver's actual grant governs, not the request."
    - scenario: "Direct-file fallback taken because mmap failed."
      expected_result: "page_flip False; _setup_page_flip is not attempted."
    - scenario: "Write with page_flip True, starting at buffer_index 0."
      expected_result: "Seek to fb_size, one write, pan to index 1, buffer_index becomes 1. The next frame targets offset 0."
    - scenario: "Write with page_flip True where _pan_display fails."
      expected_result: "page_flip disabled; the frame is still written; subsequent frames use offset zero."
    - scenario: "Write with page_flip False and vsync_available True."
      expected_result: "_wait_for_vsync called once before the write; seek to zero."
    - scenario: "_wait_for_vsync where the ioctl raises EINVAL."
      expected_result: "Returns False; vsync_available set False; logged once, not per frame; the write still happens."
    - scenario: "Write with both unavailable."
      expected_result: "Identical behaviour to change-66ef59a0: seek to zero, one write, no ioctl."
    - scenario: "cleanup with _original_var captured."
      expected_result: "FBIOPUT_VSCREENINFO issued with the original struct; the mapping and device are closed regardless of whether it succeeded."
    - scenario: "cleanup where the restore raises."
      expected_result: "The exception is contained; the mapping and device are still closed."
  regression_scope:
    - "tests/display/ once populated."
    - "Manual on target: every mode renders — SPLASH, DIGITAL, RADIAL, OPTIONS, DISCONNECTED, ACKNOWLEDGEMENT."
    - "Manual on target: the application exits cleanly and the console remains usable, confirming the screen info was restored."
    - "frame_time_ms compared against the §7.5.3 baseline."
  validation_criteria:
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."
    - "FBIO_WAITFORVSYNC is defined as 0x40044620, not 0x4620."
    - "The startup log states which presentation mode was selected."
    - "No ioctl is issued from write_to_framebuffer when both page_flip and vsync_available are False."
    - "No file other than engine.py is modified."

implementation:
  implementation_steps:
    - step: "EDIT 1 — imports and ioctl constants."
      owner: "Claude Code"
    - step: "EDIT 2 — presentation state in __init__."
      owner: "Claude Code"
    - step: "EDIT 3 — mode selection in _initialize_framebuffer."
      owner: "Claude Code"
    - step: "EDIT 4 to 6 — _setup_page_flip, _wait_for_vsync, _pan_display."
      owner: "Claude Code"
    - step: "EDIT 7 — write path."
      owner: "Claude Code"
    - step: "EDIT 8 — restore in cleanup."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Deploy to gtach.local. Record the selected mode from the log, confirm every screen renders, observe for a migrating band in simulation mode, and compare frame_time_ms against the §7.5.3 baseline."
      owner: "William Watson"
  rollback_procedure: >
    Single file, single commit. git revert restores the previous
    behaviour. If the panel is left in a modified virtual resolution by an
    unclean exit, rebooting the target restores it from firmware
    configuration.
  deployment_notes: >
    This is the highest-risk change in the v0.4.0 set and the one whose
    failure mode is most visible. Deploy it alone rather than batched, so
    a rendering fault is attributable. Read the startup log first: which
    of the three presentation modes was selected determines what the
    subsequent observation means.

verification:
  implemented_date: "2026-07-30"
  implemented_by: "Claude Code, per prompt-49b21ace"
  verification_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Development platform only: macOS, Python 3.11.14, pygame 2.6.1, SDL
    dummy driver. The framebuffer ioctls do not exist on this platform, so
    they were driven against a fake driver emulating the kernel's semantics
    for FBIOGET_VSCREENINFO, FBIOPUT_VSCREENINFO, FBIOPAN_DISPLAY and
    FBIO_WAITFORVSYNC, over a real mmap of a temporary file. fcntl.ioctl was
    replaced inside the engine module only. Eighty-six assertions, all
    passing. This change is left active pending on-target results per
    ai/task.md §8.2.1.

    THREE DEPARTURES FROM THE PROMPT'S LITERAL TEXT. Two are necessary and
    were confirmed load-bearing by reverting them and re-running the suite,
    which then fails four assertions. The third is defensive and no test
    failure is attributed to it.

    Departure 1 — _setup_page_flip must remap before closing. The prompt
    closes the existing mapping and then calls mmap.mmap over twice
    fb_size. When the driver grants the resize but the mapping cannot in
    fact be extended, that call raises and self.fb is left closed. page_flip
    is False by then, so every later frame takes the single-buffer branch
    and calls seek on a closed mmap; the ValueError is caught by the general
    handler, framebuffer_errors climbs, and no frame is ever delivered
    again. The prompt's own design section requires the existing mapping to
    be left intact on failure, so the literal text contradicts it. Verified:
    with the prompt's ordering, the remap-failure scenario leaves e.fb
    closed, "frame still delivered after a failed remap" fails, and reading
    the mapping raises "ValueError: mmap closed or invalid". With the
    corrected ordering the engine keeps a working single-frame mapping and
    delivers the frame at offset zero.

    Departure 2 — the pan template must be the confirmed struct. The prompt
    builds _pan_display's argument from self._original_var, captured before
    the resize, whose yres_virtual is one frame. Panning to the second half
    then hands the driver a struct in which yoffset is 480 and yres_virtual
    is 480. Mainline Linux fb_pan_display validates yoffset against
    info->var.yres_virtual — the driver's state, not the argument — so on
    mainline this would be accepted; the scope of the defect is a driver
    that validates the struct it is given, which rejects it and disables
    page flipping on the first frame. Verified against a strict-driver
    emulation: the prompt's version fails the pan and page_flip goes False
    immediately, the corrected version pans successfully. Given that the
    whole purpose of the re-read is to act on the grant rather than the
    request, using the stale struct is also wrong on its own terms.
    _original_var is now reserved for cleanup, which is its documented
    purpose.

    Departure 3 — the ioctl guards test for an open device. The prompt uses
    `if not self.fb_dev`. The direct-file fallback in _initialize_framebuffer
    closes fb_dev but leaves the attribute bound, so the guard passes and
    fileno() raises ValueError on a closed file. The behaviour is already
    safe — the exception is caught — but the INFO line then reads
    "Vertical-blank wait unavailable: I/O operation on closed file", which
    misdescribes the situation. A _fb_dev_usable() helper tests both
    conditions. This is a log-quality change only.

    Evidence by test case.

    Page flip granted: page_flip True, the mapping covers 1,843,200 bytes,
    and the ioctl order is GET, PUT, GET — the re-read the design requires.
    No vsync probe is issued when page flipping succeeds, so the two
    mechanisms are alternatives rather than additive, as specified.

    Page-flip writes: from buffer_index 0 the frame lands in the upper half
    and the lower half is untouched, the pan is issued to yoffset 480, and
    buffer_index becomes 1. The next frame lands in the lower half and pans
    to 0. Exactly one ioctl is issued per frame on this path, the pan.

    Resize refused with EINVAL: page_flip False, the single-frame mapping
    remains and is 921,600 bytes, exactly one INFO is logged and it carries
    errno 22, and the next frame is still delivered.

    Short grant: with the put accepted but yres_virtual left at 480,
    page_flip is False and the log names both figures — granted 480, needed
    960. The grant governs, not the request.

    Runtime pan failure: the frame is still written to the target half, the
    call returns True, page_flip goes False, one INFO is logged, the next
    frame writes at offset zero, and no further pan is attempted. The INFO
    is not repeated on later frames.

    Vsync path: with page flipping unavailable and the vblank ioctl working,
    the mode line names the vsync-synchronised write, exactly one
    FBIO_WAITFORVSYNC is issued per frame, and instrumenting both the ioctl
    and the write shows the order is wait then write, not the reverse.

    Vsync unsupported: vsync_available is False after the probe, repeated
    calls return False, and exactly one INFO is logged across three failed
    calls.

    Neither mechanism: no ioctl whatsoever is issued on the frame path — the
    call list is empty — and the frame is written at offset zero. This is
    the requirement that the unavailable path cost nothing.

    Direct-file fallback: use_mmap False, page_flip False, and no
    FBIOPUT_VSCREENINFO is attempted.

    cleanup: FBIOPUT_VSCREENINFO is issued with the captured original
    struct, restoring yres_virtual to 480 and yoffset to 0; the mapping and
    device are both closed; _original_var is cleared, so a second cleanup is
    a no-op. With the restore forced to raise, the warning is logged and
    both are still closed.

    Guards and malformed geometry: all three helpers return False when
    fb_dev is absent. A driver reporting yres 0 refuses page flip and
    attempts no put, so yres_virtual is never set to 0. A pan to the half
    already displayed still toggles buffer_index. In mock rendering mode no
    ioctl is issued and neither the write nor cleanup raises.

    change-66ef59a0 invariants: get_view('0') is still the payload
    acquisition, the .length size check and the truncate/pad path are
    unchanged, no flush, sync or fsync has been reintroduced, convert(32, 0)
    appears only on the view-failure fallback, and swap_buffers remains the
    documented no-op.

    Constants: FBIO_WAITFORVSYNC is 0x40044620, and the derivation was
    checked independently rather than taken on trust —
    (1 << 30) | (4 << 16) | (0x46 << 8) | 0x20 is 0x40044620. No bare
    0x4620 constant appears anywhere in the file; the value occurs only
    inside the comment explaining why the report's figure is wrong.

    pytest tests/ — 11 passed, unchanged by this work. No test in tests/
    exercises the rendering engine.

    What this does NOT establish. Nothing here shows that tearing is
    reduced, because nothing here observes a panel. The emulated driver
    confirms the mechanism and its degradation chain; only gtach.local can
    confirm the effect, and the prompt expects page flip to be refused
    there, which would make the vertical-blank wait the operative path.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-66ef59a0"
      relationship: "blocked_by"
    - change_ref: "change-cb28980f"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-49b21ace"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-49b21ace."
  - version: "1.1"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status proposed -> implemented. Recorded implementation date, executor, verification date and development-platform test results."
      - "Recorded two necessary departures from prompt-49b21ace, both confirmed load-bearing by reverting them: _setup_page_flip must establish the new mapping before closing the old one, and _pan_display must build its argument from the confirmed post-resize struct rather than _original_var."
      - "Recorded one defensive departure: the ioctl guards test whether fb_dev is open rather than merely bound, because the direct-file fallback leaves a closed file bound to the attribute."
      - "Recorded that the ioctls were exercised against an emulated driver over a real mmap, and that nothing off-target establishes any reduction in tearing."
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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-49b21ace. |
| 1.1 | 2026-07-30 | Status proposed → implemented; development-platform test results recorded against an emulated framebuffer driver, including two necessary departures from the prompt's literal text. Left active pending on-target results. |

---

Copyright (c) 2026 William Watson. MIT License.
