Created: 2026 July 30

# Prompt: Present by Page Flip, Falling Back to a Vertical-Blank Wait

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-49b21ace"
  task_type: "code_generation"
  source_ref: "change-49b21ace"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-49b21ace"
    change_iteration: 1

context:
  purpose: >
    Give the frame a presentation step. The engine currently writes
    921,600 bytes into the single buffer the panel is actively scanning
    out, at a rate that beats against the 60 Hz refresh, so the controller
    can read a buffer that is part previous frame and part next. Prefer
    page flipping; fall back to a vertical-blank wait; fall back again to
    the present behaviour.
  integration: >
    One file: src/gtach/display/rendering/engine.py. Eight edits.
    Executor is Claude Code; AEL is not used. change-66ef59a0 must be
    implemented first — this edits the single clean write it leaves
    behind.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/rendering/engine.py."
    - "change-66ef59a0 must already be applied. Do not re-introduce main_surface, convert(32, 0), bytes materialisation, flush, sync or fsync."
    - "Leave the payload acquisition, the `.length` size check and the truncate/pad path exactly as they are. Only the destination offset and what follows the write change."
    - "Do NOT add FBIOGET_FSCREENINFO or change the size-mismatch log level. That is task 7.3.3."
    - "FBIO_WAITFORVSYNC is 0x40044620, NOT the 0x4620 the source report cites. See the derivation in EDIT 1; 0x4620 omits the direction and size encoding and will be rejected by a driver that validates it."
    - "Page flipping requires the mmap path. If _initialize_framebuffer fell back to direct file writing, do not attempt it."
    - "Never issue an ioctl from write_to_framebuffer when both page_flip and vsync_available are False. The unavailable path must cost nothing."
    - "Every ioctl failure is handled and logged once, never per frame. A device without these capabilities must behave exactly as it does today."
    - "Act on what the driver granted, not what was requested — always re-read after FBIOPUT_VSCREENINFO."
    - "Do not change swap_buffers. It remains the documented no-op from change-66ef59a0."
    - "Type hints on all new methods; Google-style docstrings; PEP 8."

specification:
  description: >
    Add page-flip setup and teardown, a vertical-blank wait and a pan
    helper; select the presentation mode once at initialisation and log
    it; write to the off-screen half and present by panning when
    available.
  requirements:
    functional:
      - "At initialisation the engine attempts to double yres_virtual and map two frame-sized halves."
      - "Page flipping is enabled only if a re-read confirms the driver granted at least twice yres."
      - "When page flipping is active, each frame is written to the half the controller is not scanning, then presented with FBIOPAN_DISPLAY."
      - "When page flipping is unavailable but the vertical-blank ioctl works, the write is preceded by FBIO_WAITFORVSYNC."
      - "When neither is available, behaviour is identical to change-66ef59a0."
      - "The selected mode is logged once at INFO during initialisation."
      - "cleanup restores the original yres_virtual and yoffset."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "No ioctl on the frame path when no synchronisation mechanism is available"
      metric: "time"

design:
  architecture: >
    A three-stage degradation chain decided once at initialisation. Page
    flipping and the vertical-blank wait are alternative mechanisms for
    the same problem, not additive: with page flipping the frame is
    composed in a half the controller is not reading, so a pre-write wait
    would block for no benefit.
  components:
    - name: "DisplayRenderingEngine._setup_page_flip"
      type: "function"
      purpose: "Attempt to establish a second framebuffer half."
      interface:
        inputs: []
        outputs:
          type: "bool"
          description: "True if page flipping is available."
        raises:
          - "None. All failures are caught, logged at INFO and reported as False."
      logic:
        - "Read fb_var_screeninfo from self.fb_dev with FBIOGET_VSCREENINFO into a 160-byte buffer."
        - "Retain an unmodified copy as self._original_var for cleanup."
        - "Unpack with FB_VAR_STRUCT; set index FB_VAR_YRES_VIRTUAL to twice the current yres (index 1) and index FB_VAR_ACTIVATE to FB_ACTIVATE_NOW."
        - "Write back with FBIOPUT_VSCREENINFO."
        - "Re-read with FBIOGET_VSCREENINFO and verify yres_virtual >= 2 x yres. If not, log at INFO and return False."
        - "Close the existing mmap and remap over 2 x self.fb_size."
        - "Return True."
        - "On any exception: log at INFO including e.errno where available, leave the existing mapping intact, return False. This is an expected outcome on a device whose framebuffer is fixed at boot, not an error."
    - name: "DisplayRenderingEngine._wait_for_vsync"
      type: "function"
      purpose: "Block until the start of the vertical blanking interval."
      interface:
        inputs: []
        outputs:
          type: "bool"
          description: "True if the wait succeeded."
        raises:
          - "None."
      logic:
        - "Issue FBIO_WAITFORVSYNC on self.fb_dev.fileno() with struct.pack('I', 0) as the argument."
        - "On success return True."
        - "On exception set self.vsync_available False, log once at INFO guarded by self._vsync_failed_logged, return False."
    - name: "DisplayRenderingEngine._pan_display"
      type: "function"
      purpose: "Present a half by changing the scan-out origin."
      interface:
        inputs:
          - name: "index"
            type: "int"
            description: "0 or 1 — which half to present."
        outputs:
          type: "bool"
          description: "True if the pan succeeded."
        raises:
          - "None."
      logic:
        - "Take the current variable screen info, set FB_VAR_YOFFSET to index x yres and FB_VAR_ACTIVATE to FB_ACTIVATE_VBL."
        - "Issue FBIOPAN_DISPLAY."
        - "On exception log once at INFO and return False, so the caller can disable page flipping and continue."
        - "FB_ACTIVATE_VBL asks the driver to latch the flip at the next blanking interval. Some drivers ignore it; do not assume it was honoured."
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      type: "function"
      purpose: "Deliver the composed frame, synchronised where possible."
      logic:
        - "Leave everything up to and including the truncate/pad block unchanged."
        - "If self.page_flip: target = self.buffer_index ^ 1; seek to target * self.fb_size; write; if _pan_display(target) then self.buffer_index = target, else set self.page_flip False."
        - "Else: if self.vsync_available, call self._wait_for_vsync(); then seek to 0 and write."
        - "Leave the statistics update and both exception handlers unchanged."
  dependencies:
    internal:
      - "change-66ef59a0 — establishes the single clean write this edits."
      - "DisplayManager._display_loop — no call-site change."
    external:
      - "fcntl, struct — standard library, newly imported."

data_schema:
  entities:
    - name: "fb_var_screeninfo"
      attributes:
        - name: "layout"
          type: "40 x __u32"
          constraints: "160 bytes. struct format '40I'."
        - name: "yres"
          type: "__u32"
          constraints: "Index 1."
        - name: "yres_virtual"
          type: "__u32"
          constraints: "Index 3. Doubled to create the second half."
        - name: "yoffset"
          type: "__u32"
          constraints: "Index 5. Set to index x yres to present a half."
        - name: "activate"
          type: "__u32"
          constraints: "Index 21. FB_ACTIVATE_NOW 0 for the resize, FB_ACTIVATE_VBL 16 for the pan."
      validation:
        - "The struct is read, modified and written back whole. Do not construct one from scratch — the remaining fields carry timing and format information that must be preserved."

error_handling:
  strategy: >
    Every capability is probed, never assumed. A failure at any stage
    degrades to the next mechanism and is logged once at INFO, because on
    hardware that does not support these operations it is an expected
    outcome rather than a fault.
  exceptions:
    - exception: "OSError"
      condition: "FBIOPUT_VSCREENINFO cannot enlarge the allocation."
      handling: "Log at INFO with errno; page_flip stays False; the existing single-frame mapping is untouched."
    - exception: "OSError"
      condition: "FBIO_WAITFORVSYNC unsupported — typically EINVAL or ENOTTY."
      handling: "Set vsync_available False so it is not retried; log once; the write proceeds."
    - exception: "OSError"
      condition: "FBIOPAN_DISPLAY fails at runtime."
      handling: "Disable page_flip; log once; subsequent frames write at offset zero."
    - exception: "Exception"
      condition: "Restoring the original screen info during cleanup fails."
      handling: "Contain it. The mapping and device must still close."
  logging:
    level: "INFO"
    format: "Capability probes log at INFO, not WARNING or ERROR — absence of a capability is not a fault. Unexpected failures inside the write path retain the existing ERROR handlers."

testing:
  unit_tests:
    - scenario: "_setup_page_flip where the driver grants twice yres."
      expected: "Returns True; page_flip True; mmap length is 2 x fb_size."
    - scenario: "_setup_page_flip where FBIOPUT_VSCREENINFO raises OSError(EINVAL)."
      expected: "Returns False; the original mapping is intact; one INFO logged."
    - scenario: "_setup_page_flip where the put succeeds but the re-read shows yres_virtual unchanged."
      expected: "Returns False. The grant governs, not the request."
    - scenario: "Direct-file fallback in force."
      expected: "_setup_page_flip is not called; page_flip False."
    - scenario: "Write with page_flip True from buffer_index 0."
      expected: "Seek to fb_size; one write; pan to 1; buffer_index becomes 1."
    - scenario: "Write with page_flip True where the pan fails."
      expected: "page_flip disabled; the frame is still written; the next frame uses offset 0."
    - scenario: "Write with vsync_available True."
      expected: "_wait_for_vsync called once before the write."
    - scenario: "_wait_for_vsync raising EINVAL twice."
      expected: "Returns False both times; exactly one INFO logged; vsync_available False after the first."
    - scenario: "Write with both mechanisms unavailable."
      expected: "No ioctl issued; seek to 0; one write. Identical to change-66ef59a0."
    - scenario: "cleanup with _original_var captured."
      expected: "FBIOPUT_VSCREENINFO issued with the original struct; mapping and device closed."
    - scenario: "cleanup where the restore raises."
      expected: "Exception contained; mapping and device still closed."
  edge_cases:
    - "self.fb_dev is None because the direct-file path was taken — every ioctl helper must guard on it."
    - "yres is 0 in a malformed struct — guard the doubling so yres_virtual is never set to 0."
    - "The pan is requested for the half already displayed — harmless, but buffer_index must still toggle correctly."
    - "cleanup called twice — the restore must be idempotent or guarded by clearing _original_var."
    - "Mock rendering mode with pygame unavailable — no framebuffer, no ioctl, no exception."
  validation:
    - "grep confirms 0x40044620 appears and 0x4620 does not appear as a standalone constant."
    - "The startup log line names the selected mode."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/rendering/engine.py in place. Create no new file."
    - "Apply the eight edits below. Change nothing else."
  files:
    - path: "src/gtach/display/rendering/engine.py"
      content: |
        EDIT 1 — imports and module-scope constants

        Add to the existing imports (mmap, os, time, threading, logging are
        already present):

            import fcntl
            import struct

        Add after the imports, before the first class:

            # Linux framebuffer ioctls (linux/fb.h).
            #
            # The first three are plain values in the header. FBIO_WAITFORVSYNC
            # is declared _IOW('F', 0x20, __u32), which encodes direction and
            # argument size as well as type and number:
            #
            #   (1 << 30) | (4 << 16) | (0x46 << 8) | 0x20 == 0x40044620
            #
            # The display review cites 0x4620, which is the type and number
            # portion only. Some drivers mask the encoding and accept it;
            # relying on that is not safe.
            FBIOGET_VSCREENINFO = 0x4600
            FBIOPUT_VSCREENINFO = 0x4601
            FBIOPAN_DISPLAY = 0x4606
            FBIO_WAITFORVSYNC = 0x40044620

            FB_ACTIVATE_NOW = 0
            FB_ACTIVATE_VBL = 16

            # struct fb_var_screeninfo is 40 x __u32 == 160 bytes.
            FB_VAR_STRUCT = '40I'
            FB_VAR_YRES = 1
            FB_VAR_YRES_VIRTUAL = 3
            FB_VAR_YOFFSET = 5
            FB_VAR_ACTIVATE = 21

        EDIT 2 — __init__

        Add alongside the existing framebuffer state (near the
        self._view_fallback_logged line):

                # Presentation mode, decided once in _initialize_framebuffer
                self.page_flip = False           # second half established
                self.vsync_available = False     # FBIO_WAITFORVSYNC works
                self.buffer_index = 0            # half currently displayed
                self._original_var = None        # for restoration in cleanup
                self._vsync_failed_logged = False
                self._pan_failed_logged = False

        EDIT 3 — _initialize_framebuffer

        After the mmap succeeds and self.use_mmap is set True, and before
        the method returns, add capability selection:

                    # Presentation mode. Page flipping needs the mmap path;
                    # if the direct-file fallback was taken there is no
                    # mapping to extend.
                    if self.use_mmap:
                        self.page_flip = self._setup_page_flip()

                    if not self.page_flip:
                        self.vsync_available = self._wait_for_vsync()

                    if self.page_flip:
                        mode = "page flip"
                    elif self.vsync_available:
                        mode = "vsync-synchronised write"
                    else:
                        mode = "unsynchronised write"
                    self.logger.info(f"Framebuffer presentation mode: {mode}")

        Place this so it runs on both the mmap and direct-file paths — the
        vsync probe is useful in either case, page-flip setup only in the
        first.

        EDIT 4 — add _setup_page_flip immediately after _initialize_framebuffer

            def _setup_page_flip(self) -> bool:
                """Attempt to establish a second framebuffer half.

                Doubles yres_virtual so the device holds two frames, then
                remaps over both. Failure is an expected outcome on hardware
                whose framebuffer is allocated at boot, so it is logged at
                INFO and reported as False rather than raised.

                Returns:
                    True if page flipping is available.
                """
                if not self.fb_dev:
                    return False

                try:
                    raw = fcntl.ioctl(
                        self.fb_dev.fileno(), FBIOGET_VSCREENINFO,
                        bytes(struct.calcsize(FB_VAR_STRUCT))
                    )
                    self._original_var = raw

                    var = list(struct.unpack(FB_VAR_STRUCT, raw))
                    yres = var[FB_VAR_YRES]
                    if yres <= 0:
                        self.logger.info("Page flip unavailable: driver reports yres 0")
                        return False

                    var[FB_VAR_YRES_VIRTUAL] = yres * 2
                    var[FB_VAR_ACTIVATE] = FB_ACTIVATE_NOW
                    fcntl.ioctl(
                        self.fb_dev.fileno(), FBIOPUT_VSCREENINFO,
                        struct.pack(FB_VAR_STRUCT, *var)
                    )

                    # Act on what the driver granted, not what was requested.
                    confirmed = struct.unpack(FB_VAR_STRUCT, fcntl.ioctl(
                        self.fb_dev.fileno(), FBIOGET_VSCREENINFO,
                        bytes(struct.calcsize(FB_VAR_STRUCT))
                    ))
                    if confirmed[FB_VAR_YRES_VIRTUAL] < yres * 2:
                        self.logger.info(
                            f"Page flip unavailable: driver granted yres_virtual "
                            f"{confirmed[FB_VAR_YRES_VIRTUAL]}, needed {yres * 2}"
                        )
                        return False

                    self.fb.close()
                    self.fb = mmap.mmap(self.fb_dev.fileno(), self.fb_size * 2)
                    self.logger.info("Page flip enabled: two framebuffer halves mapped")
                    return True

                except Exception as e:
                    errno = getattr(e, 'errno', None)
                    self.logger.info(
                        f"Page flip unavailable: {e}"
                        + (f" (errno {errno})" if errno is not None else "")
                    )
                    return False

        EDIT 5 — add _wait_for_vsync

            def _wait_for_vsync(self) -> bool:
                """Block until the start of the vertical blanking interval.

                Returns:
                    True if the wait succeeded. On failure the capability is
                    disabled so it is not retried, and the caller proceeds
                    without synchronisation.
                """
                if not self.fb_dev:
                    return False

                try:
                    fcntl.ioctl(self.fb_dev.fileno(), FBIO_WAITFORVSYNC,
                                struct.pack('I', 0))
                    return True
                except Exception as e:
                    self.vsync_available = False
                    if not self._vsync_failed_logged:
                        self._vsync_failed_logged = True
                        self.logger.info(f"Vertical-blank wait unavailable: {e}")
                    return False

        EDIT 6 — add _pan_display

            def _pan_display(self, index: int) -> bool:
                """Present a framebuffer half by moving the scan-out origin.

                Args:
                    index: 0 or 1 — which half to display.

                Returns:
                    True if the pan succeeded.
                """
                if not self.fb_dev or self._original_var is None:
                    return False

                try:
                    var = list(struct.unpack(FB_VAR_STRUCT, self._original_var))
                    var[FB_VAR_YOFFSET] = index * var[FB_VAR_YRES]
                    # Asks the driver to latch at the next blanking interval.
                    # Not all drivers honour it; correctness does not depend on it.
                    var[FB_VAR_ACTIVATE] = FB_ACTIVATE_VBL
                    fcntl.ioctl(self.fb_dev.fileno(), FBIOPAN_DISPLAY,
                                struct.pack(FB_VAR_STRUCT, *var))
                    return True
                except Exception as e:
                    if not self._pan_failed_logged:
                        self._pan_failed_logged = True
                        self.logger.info(f"Page flip failed, reverting to direct write: {e}")
                    return False

        EDIT 7 — write_to_framebuffer

        Replace ONLY the seek-and-write block that change-66ef59a0 left
        (currently the two lines preceded by the "Single write, no
        synchronisation" comment):

                        self.fb.seek(0)
                        self.fb.write(payload)

        with:

                        if self.page_flip:
                            # Compose into the half the controller is not
                            # scanning, then present it atomically. No
                            # pre-write wait is needed: nothing is reading
                            # this half (display review §4.1, recommendation 4).
                            target = self.buffer_index ^ 1
                            self.fb.seek(target * self.fb_size)
                            self.fb.write(payload)
                            if self._pan_display(target):
                                self.buffer_index = target
                            else:
                                self.page_flip = False
                        else:
                            # Single buffer. Beginning the write at the start
                            # of blanking narrows the window in which the
                            # scan-out can read a partially updated buffer
                            # (recommendation 3).
                            if self.vsync_available:
                                self._wait_for_vsync()
                            self.fb.seek(0)
                            self.fb.write(payload)

        Leave the payload acquisition, the `.length` size check, the
        truncate/pad block, the statistics update and both exception
        handlers exactly as they are.

        EDIT 8 — cleanup

        Before the existing mapping and device close, add:

                    # Restore the virtual resolution and scan-out origin, so
                    # the console is usable after exit.
                    if self._original_var is not None and self.fb_dev:
                        try:
                            fcntl.ioctl(self.fb_dev.fileno(), FBIOPUT_VSCREENINFO,
                                        self._original_var)
                        except Exception as e:
                            self.logger.warning(f"Could not restore screen info: {e}")
                        finally:
                            self._original_var = None

        The restore must not be able to prevent the close that follows.

success_criteria:
  - "python -m py_compile src/gtach/display/rendering/engine.py passes."
  - "pytest tests/ passes with no new failures."
  - "engine.py imports fcntl and struct."
  - "FBIO_WAITFORVSYNC is defined as 0x40044620."
  - "The bare constant 0x4620 does not appear."
  - "_setup_page_flip, _wait_for_vsync and _pan_display all exist with the specified signatures."
  - "_setup_page_flip re-reads FBIOGET_VSCREENINFO after the put and compares against yres * 2."
  - "_initialize_framebuffer logs one INFO line naming the selected presentation mode."
  - "write_to_framebuffer issues no ioctl when page_flip and vsync_available are both False."
  - "A failed pan sets self.page_flip False."
  - "cleanup writes self._original_var back before closing, inside a guard that cannot block the close."
  - "The payload acquisition and truncate/pad path from change-66ef59a0 are unchanged."
  - "No file other than src/gtach/display/rendering/engine.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "engine"
        path: "src/gtach/display/rendering/engine.py"
    classes:
      - name: "DisplayRenderingEngine"
        module: "gtach.display.rendering.engine"
    functions:
      - name: "_initialize_framebuffer"
        module: "gtach.display.rendering.engine"
        signature: "_initialize_framebuffer(self) -> None"
      - name: "_setup_page_flip"
        module: "gtach.display.rendering.engine"
        signature: "_setup_page_flip(self) -> bool"
      - name: "_wait_for_vsync"
        module: "gtach.display.rendering.engine"
        signature: "_wait_for_vsync(self) -> bool"
      - name: "_pan_display"
        module: "gtach.display.rendering.engine"
        signature: "_pan_display(self, index: int) -> bool"
      - name: "write_to_framebuffer"
        module: "gtach.display.rendering.engine"
        signature: "write_to_framebuffer(self) -> bool"
      - name: "cleanup"
        module: "gtach.display.rendering.engine"
        signature: "cleanup(self) -> None"
    constants:
      - name: "FBIOGET_VSCREENINFO"
        module: "gtach.display.rendering.engine"
        type: "int"
      - name: "FBIOPUT_VSCREENINFO"
        module: "gtach.display.rendering.engine"
        type: "int"
      - name: "FBIOPAN_DISPLAY"
        module: "gtach.display.rendering.engine"
        type: "int"
      - name: "FBIO_WAITFORVSYNC"
        module: "gtach.display.rendering.engine"
        type: "int"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-49b21ace-framebuffer-vsync-pageflip.md
  and close the prompt when finished. Leave the issue and change active
  pending test results (ai/task.md §8.2.1).

  The §7.5.1 geometry read on 2026-07-30 cleared this task's gate and
  supplies its facts: 32 bits per pixel, stride 1920, Size 921,600,
  YPanStep 1, and xres_virtual and yres_virtual both 480. YPanStep 1
  means the driver implements panning. yres_virtual 480 means there is
  currently only one frame of storage, which is what _setup_page_flip
  attempts to change.

  Expect _setup_page_flip to fail on this target. The Pi's DPI
  framebuffer is allocated at boot from firmware configuration and the
  driver may refuse to enlarge it. That is a correct and handled outcome,
  not a defect — the vertical-blank fallback is then the operative path
  and is still an improvement. If page flipping is wanted and the ioctl
  refuses, enabling it needs a boot-configuration change on the target,
  which is an operator action outside this change.

  Read the startup log line before drawing any conclusion from an
  on-target observation: which of the three presentation modes was
  selected determines what the observation means.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-49b21ace. |
| 1.1 | 2026-07-30 | Executed by Claude Code. All eight edits applied and all thirteen success criteria met; 86 assertions against an emulated framebuffer driver, all passing; pytest tests/ 11 passed. Three departures from the literal text, two of them necessary and confirmed by reverting them: EDIT 4 must establish the enlarged mapping before closing the old one, or a failed remap leaves the engine with a closed mmap and no frame is ever delivered again; and EDIT 6 must pan from the confirmed post-resize struct, not _original_var, whose yres_virtual describes one frame. The third replaces the `if not self.fb_dev` guards with an open-file test, because the direct-file fallback leaves a closed file bound. The FBIO_WAITFORVSYNC derivation was checked independently and is correct. All recorded in change-49b21ace. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/; the issue and change remain active pending on-target results per ai/task.md §8.2.1. |

---

Copyright (c) 2026 William Watson. MIT License.
