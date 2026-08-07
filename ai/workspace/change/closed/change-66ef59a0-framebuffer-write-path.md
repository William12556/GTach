Created: 2026 July 30

# Change: One Copy per Frame, No Forced Synchronisation

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-66ef59a0"
  title: "Write back_surface directly in a fixed 32-bit format via a buffer view; remove the per-frame convert, bytes copy, intermediate blit and forced sync"
  date: "2026-07-30"
  author: "William Watson"
  status: "closed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-66ef59a0"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-66ef59a0"
  description: >
    Resolves issue-66ef59a0. Sourced from
    ai/workspace/report/display-ui-graphics-review.md v1.0
    recommendations 2, 6, 7 and 8. Task list reference ai/task.md §7.3.2.

scope:
  summary: >
    Reduce the per-frame framebuffer path from four full-frame
    traversals to one. Establish the 32-bit surface format at
    initialisation; write back_surface directly through a
    buffer-protocol view; reduce swap_buffers to a no-op that retains its
    interface; remove flush, sync and fsync from the write.
  affected_components:
    - name: "DisplayRenderingEngine.initialize"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine.swap_buffers"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "FBIO_WAITFORVSYNC and FBIOPAN_DISPLAY — recommendations 3 and 4, task 7.3.4. This change leaves the write mechanism as a write."
    - "Querying framebuffer geometry via ioctl and raising the mismatch log level — recommendation 21, task 7.3.3."
    - "Caching the RADIAL static layer or rendered text — recommendations 9 and 10, task 7.3.5."
    - "Reducing fps_limit or skipping unchanged frames — recommendations 12 and 13, task 7.3.6."
    - "Removing swap_buffers from RenderingEngineInterface. The method and its signature are retained."
    - "The ENOSPC recovery path at engine.py:380-402. Retained unchanged."
    - "create_surface, draw_circle, draw_rect, draw_line, blit_surface, render_text and clear_surface."

rational:
  problem_statement: >
    Every frame is traversed four times at 921,600 bytes: the
    swap_buffers blit into main_surface, a convert(32, 0) that allocates
    a new surface, a bytes() materialisation, and the write itself. Three
    are removable without altering what is displayed. The write is then
    followed by flush and sync or fsync, which on a framebuffer device
    provide no correctness benefit and lengthen the interval during which
    the scan-out can read a partially updated buffer.
  proposed_solution: >
    Create back_surface at an explicit 32-bit depth during initialisation
    so no conversion is ever required. Write it directly through
    get_view('0'), which both mmap.write and file.write accept. Reduce
    swap_buffers to a no-op returning True, preserving the interface and
    its caller. Delete the flush, sync and fsync calls.
  alternatives_considered:
    - option: "Keep main_surface and exchange references with back_surface instead of blitting."
      reason_rejected: >
        The report offers this as the fallback if two surfaces are
        retained for another reason. No such reason exists: nothing reads
        main_surface between the blit and the write. A single surface is
        simpler than a correct exchange.
    - option: "Convert once at initialisation and keep the converted surface."
      reason_rejected: >
        This is recommendation 7 read literally, but convert() returns a
        new surface — drawing would continue into the unconverted
        original and the converted copy would never update. Creating the
        surface at the target depth achieves the intent without the trap.
    - option: "Retain bytes() and accept the copy, taking only recommendations 2, 6 and 7."
      reason_rejected: >
        The copy is a full-frame traversal per frame and the buffer
        protocol removes it at no cost in clarity. Retaining it would
        leave a quarter of the identified waste in place.
    - option: "Delete the size-mismatch handling entirely, since §7.5.1 confirmed the geometry matches."
      reason_rejected: >
        The observation confirms the geometry of one device at one moment.
        The ENOSPC recovery path indicates a mismatch has been met on
        hardware before. The check is retained; whether it logs at DEBUG
        or ERROR is recommendation 21's question, not this change's.
  benefits:
    - "Removes three full-frame traversals and one surface allocation per frame."
    - "Removes the forced synchronisation that widens the tear window, addressing the §4.1 contributing factor identified in the report."
    - "Leaves a single clean write for task 7.3.4 to convert into a page flip."
  risks:
    - risk: >
        Creating back_surface at an explicit depth may produce a surface
        whose byte layout differs from the framebuffer's RGBA ordering,
        giving distorted colour.
      mitigation: >
        The panel reports rgba 8/16,8/8,8/0,8/24 — the same layout the
        existing per-frame convert(32, 0) produces, which renders
        correctly today. Assert get_bytesize() == 4 after creation and
        log the surface's bitsize and masks at INFO during
        initialisation, so a mismatch is visible in the log rather than
        only on the panel.
    - risk: >
        get_view('0') requires a contiguous surface; a surface with
        padding between rows would raise.
      mitigation: >
        480 x 4 = 1920 bytes per row with no alignment padding required,
        and the framebuffer's own LineLength is 1920. Catch the exception
        and fall back to the existing bytes path for that frame, logging
        once at ERROR rather than per frame.
    - risk: >
        Removing flush and fsync could leave a write not yet visible to
        the scan-out.
      mitigation: >
        Writes to a memory-mapped framebuffer are visible to the display
        controller as soon as the store completes; there is no cache to
        flush toward the device. This is the report's basis for
        recommendation 2. If the panel shows stale content after the
        change, revert and record the observation — it would indicate a
        driver behaviour the report did not anticipate.
    - risk: >
        swap_buffers becoming a no-op leaves a method that does nothing,
        which a future reader may delete along with its caller.
      mitigation: >
        Retain it with a docstring stating explicitly why it is empty and
        that it exists to satisfy RenderingEngineInterface. Task 7.3.4 may
        give it a role again if page flipping is adopted, which is a
        further reason not to remove it.

technical_details:
  current_behavior: >
    initialize (engine.py:68-115) creates main_surface and back_surface
    with pygame.Surface(surface_size), whose depth follows the display
    default. swap_buffers (engine.py:286-298) blits back_surface into
    main_surface. write_to_framebuffer (engine.py:300-378) converts
    main_surface with convert(32, 0), calls get_buffer(), materialises it
    with bytes(), truncates or zero-pads on size mismatch with a DEBUG
    log, writes, then calls flush() and sync() or os.fsync().
  proposed_behavior: >
    initialize creates back_surface at an explicit 32-bit depth and drops
    main_surface. swap_buffers returns True without copying.
    write_to_framebuffer takes a buffer view of back_surface, checks its
    length against fb_size, writes it, and returns. No conversion, no
    materialisation, no synchronisation.
  implementation_approach: >
    Four edits in src/gtach/display/rendering/engine.py.

    EDIT 1 — initialize. Replace the two surface creations with a single
    back_surface created at an explicit 32-bit depth:

        self.back_surface = pygame.Surface(surface_size, 0, 32)
        self.main_surface = self.back_surface

    main_surface is aliased rather than removed so that any incidental
    reader — get_surface, _get_target_surface, RenderTarget.MAIN_SURFACE
    — continues to resolve. Log the realised depth at INFO:
    back_surface.get_bitsize() and get_masks().

    EDIT 2 — swap_buffers. Replace the blit with an immediate True and a
    docstring recording why the method is empty: back_surface is written
    to the framebuffer directly, so no intermediate copy is required. The
    method is retained to satisfy RenderingEngineInterface
    (interfaces.py:91) and its caller in DisplayManager._display_loop.

    EDIT 3 — write_to_framebuffer, buffer acquisition. Replace the
    convert-and-materialise block with a view:

        view = self.back_surface.get_view('0')

    On exception, fall back to the previous bytes path for that frame and
    log at ERROR, guarded so it is logged once rather than per frame.

    EDIT 4 — write_to_framebuffer, write and synchronisation. Compare
    view.length against self.fb_size and retain the existing DEBUG log
    and truncate/pad behaviour on mismatch, materialising to bytes only
    on that path. On the matching path write the view directly. Remove
    flush(), sync() and os.fsync() from both the mmap and file branches.
    Retain the seek(0), the statistics update, the OSError handler with
    its ENOSPC branch and the general exception handler.
  code_changes:
    - component: "DisplayRenderingEngine"
      file: "src/gtach/display/rendering/engine.py"
      change_summary: >
        Single 32-bit back_surface created at initialisation with
        main_surface aliased to it; swap_buffers reduced to a no-op;
        framebuffer write takes a buffer view and performs no
        synchronisation.
      functions_affected:
        - "initialize"
        - "swap_buffers"
        - "write_to_framebuffer"
      classes_affected:
        - "DisplayRenderingEngine"
  data_changes: []
  interface_changes:
    - interface: "RenderingEngineInterface.swap_buffers"
      change_type: "contract"
      details: >
        Signature and return type unchanged. The method no longer copies;
        it returns True. No caller requires modification.
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "DisplayManager._display_loop"
      impact: "Calls swap_buffers then write_to_framebuffer. Neither call site changes."
    - component: "RenderTarget.MAIN_SURFACE consumers via _get_target_surface"
      impact: "main_surface is aliased to back_surface, so both targets resolve to the same surface. Any draw addressed to MAIN_SURFACE now lands on the surface that is written, which is the intended behaviour."
  external:
    - library: "pygame"
      version_change: "none"
      impact: "Surface.get_view('0') is used in place of get_buffer() plus bytes()."
  required_changes:
    - change_ref: "change-49b21ace"
      relationship: "blocks"

testing_requirements:
  test_approach: >
    Unit tests against DisplayRenderingEngine on the development platform
    with SDL_VIDEODRIVER=dummy and a temporary file standing in for the
    framebuffer device, plus on-target visual confirmation across every
    display mode.
  test_cases:
    - scenario: "Initialise the engine and inspect back_surface."
      expected_result: "get_bytesize() returns 4; get_bitsize() returns 32."
    - scenario: "Initialise the engine and compare main_surface with back_surface."
      expected_result: "The same object; no second surface is allocated."
    - scenario: "Call swap_buffers."
      expected_result: "Returns True; no pixel data is copied."
    - scenario: "Draw a known pattern, write to a temporary file standing in for /dev/fb0, and read it back."
      expected_result: "The file contains exactly fb_size bytes matching the surface's buffer."
    - scenario: "Write a frame and count the calls made on the framebuffer object."
      expected_result: "One seek and one write. No flush, sync or fsync."
    - scenario: "Force get_view to raise and write a frame."
      expected_result: "The bytes fallback is taken, the frame is still written, and one ERROR is logged rather than one per frame."
    - scenario: "Set fb_size to a value larger than the view length and write."
      expected_result: "Existing pad behaviour is preserved; the frame is written at fb_size bytes."
    - scenario: "Set fb_size smaller than the view length and write."
      expected_result: "Existing truncate behaviour is preserved."
    - scenario: "Raise OSError with errno 28 during write."
      expected_result: "_attempt_framebuffer_recovery is called, as before."
  regression_scope:
    - "tests/display/ once populated."
    - "Manual on target: DIGITAL, RADIAL, OPTIONS, DISCONNECTED, ACKNOWLEDGEMENT and SPLASH render with correct colour, no skew and no blanking."
    - "Manual on target: the shift border and band colours are unchanged from v0.2.67."
  validation_criteria:
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."
    - "No flush, sync or fsync call remains in write_to_framebuffer."
    - "The strings 'convert(32, 0)' and 'bytes(buffer_data)' do not appear on the matching write path."
    - "write_to_framebuffer reads back_surface."
    - "swap_buffers retains its signature and returns True."
    - "No file other than engine.py is modified."

implementation:
  implementation_steps:
    - step: "EDIT 1 — create a single 32-bit back_surface at initialisation and alias main_surface to it; log the realised depth and masks."
      owner: "Claude Code"
    - step: "EDIT 2 — reduce swap_buffers to a documented no-op."
      owner: "Claude Code"
    - step: "EDIT 3 — acquire a buffer view with a guarded bytes fallback."
      owner: "Claude Code"
    - step: "EDIT 4 — write the view and remove the synchronisation calls."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Deploy to gtach.local; confirm every mode renders correctly and record frame_time_ms against the §7.5.3 baseline."
      owner: "William Watson"
  rollback_procedure: >
    Single file, single commit. git revert restores the previous
    behaviour. No data, configuration or interface migration is involved.
  deployment_notes: >
    A rendering fault from this change is immediately visible on the
    panel — distorted colour, a skewed image or a blank display — so
    on-target confirmation is quick and unambiguous. Take it before
    proceeding to 7.3.4.

verification:
  implemented_date: "2026-07-30"
  implemented_by: "Claude Code, per prompt-66ef59a0"
  verification_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Development platform only: macOS, Python 3.11.14, pygame 2.6.1, SDL
    dummy video driver, a temporary file and a counting double standing in
    for /dev/fb0. On-target verification is outstanding; this change is
    left active pending it per ai/task.md §8.2.1.

    All four edits applied. Eleven of the twelve success criteria are met
    outright; the twelfth, pytest, now passes rather than being vacuous.
    Fifty assertions against the real DisplayRenderingEngine, all passing.

    ONE CORRECTION TO THE SPECIFICATION WAS REQUIRED. EDIT 3 specifies
    `actual_size = len(payload)`. pygame.BufferProxy, the type get_view('0')
    returns, does not implement __len__ — it exposes .length instead.
    Written literally the line raises TypeError, which
    write_to_framebuffer's own general handler catches: framebuffer_errors
    increments, an ERROR is logged, False is returned, and no frame is ever
    delivered. The panel would be blank with only a repeated
    "Framebuffer write failed: object of type
    'pygame.bufferproxy.BufferProxy' has no len()" in the log. This is not
    a judgement call: the verification suite was run against a build
    carrying the prompt's literal text and 34 of 50 assertions fail, with
    the framebuffer double recording zero seeks and zero writes. The
    implementation takes the size from .length when the attribute is
    present and falls back to len() for the bytes or memoryview the
    fallback path produces, so both payload kinds are handled and the
    stated requirement — compare the view length against fb_size — is met.
    The fallback path passes in the literal build precisely because bytes
    does implement __len__, which is why the defect would have surfaced
    only on the normal per-frame path.

    A second, cosmetic correction: EDIT 1's comment text names
    RenderTarget.MAIN_SURFACE, which is not a member of that enum — the
    member is RenderTarget.MAIN (interfaces.py:21). The comment was written
    with the correct name so it does not mislead a later reader. The
    prompt's edge_cases entry carries the same slip.

    Evidence by test case.

    Surface format: back_surface reports get_bytesize() == 4 and
    get_bitsize() == 32; main_surface is back_surface, and get_surface
    returns that same object for both RenderTarget.MAIN and
    RenderTarget.BACK_BUFFER; __init__ defines _view_fallback_logged False.

    swap_buffers returns True, contains no blit, and leaves the surface
    bytes identical across a call.

    The write: one seek, one write, zero flush, zero sync, and fileno never
    requested — so no fsync could have occurred — on both the mmap and the
    file branch. The framebuffer content equals the surface view byte for
    byte, and a real file on disk holds exactly fb_size bytes matching it.
    Spying on the write argument confirms its type is BufferProxy, so the
    frame is delivered without being materialised.

    get_view failure: with a surface subclass whose get_view raises, two
    consecutive frames are both written through the convert-and-bytes
    fallback, exactly one ERROR is logged across the pair,
    _view_fallback_logged latches True, and the delivered bytes match
    convert(32, 0).get_buffer().

    Size mismatch: with fb_size 1024 bytes larger, the frame is preserved
    and the remainder zero-filled; with fb_size 2048 smaller, the payload
    is truncated to fb_size. Both log "Buffer size mismatch" at DEBUG, and
    both still issue exactly one write.

    ENOSPC: an OSError with errno 28 returns False, calls
    _attempt_framebuffer_recovery once, and increments framebuffer_errors.

    Guards: back_surface None returns False; fb None returns False; in mock
    rendering mode with pygame_available False, initialize returns True,
    creates no surface, and write_to_framebuffer returns False without
    raising.

    Colour fidelity — the check that matters most, since a format error is
    a visible fault rather than a silent one. For the same drawing
    operations, the bytes produced by the new 32-bit surface are identical
    to those produced by the pre-change main_surface.convert(32, 0) path,
    and both report masks (16711680, 65280, 255, 0), XRGB8888. The
    delivered image is unchanged.

    Aliasing was audited against every caller rather than assumed safe.
    Every rendering call in display/manager.py targets
    RenderTarget.BACK_BUFFER — no caller uses RenderTarget.MAIN. The one
    live reference to main_surface outside the engine is app.py:191, which
    passes it to SetupDisplayManager as its default surface;
    setup.py:186 uses `target_surface or self.surface`, and manager.py:508
    always passes the back buffer explicitly, so the stored reference is a
    fallback only. Before this change that fallback was actively unsafe —
    anything drawn to main_surface was overwritten by the next
    swap_buffers blit — so aliasing removes a latent hazard rather than
    creating one. manager.py:491-492, which clears the back buffer and then
    calls swap_buffers, produces the same black frame as before.

    pytest tests/ — 11 passed. This criterion is no longer vacuous: tests/
    acquired conftest.py and tests/utils/test_rwlock.py in commit ed1dea1.
    None of those tests exercises the rendering engine, so they are a
    regression check on unrelated code, not evidence for this change. The
    regression_scope entry naming tests/display/ still has no module to
    run.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-49b21ace"
      relationship: "blocks"
    - change_ref: "change-cb28980f"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-66ef59a0"
      relationship: "resolves"

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-66ef59a0."
  - version: "1.1"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status proposed -> implemented. Recorded implementation date, executor, verification date and development-platform test results."
      - "Recorded a required correction to prompt-66ef59a0 EDIT 3: len(payload) raises TypeError on a pygame.BufferProxy, so the literal specification writes no frame at all; demonstrated by running the suite against a literal build, which fails 34 of 50 with zero writes."
      - "Recorded a cosmetic correction: the prompt names RenderTarget.MAIN_SURFACE, which is not a member of that enum."
      - "Recorded the colour-fidelity result: the new 32-bit surface produces bytes identical to the pre-change convert(32, 0) output, with identical masks."
      - "Recorded the caller audit establishing that aliasing main_surface to back_surface breaks no consumer and removes a latent hazard at app.py:191."
      - "Recorded that pytest tests/ now passes 11 tests rather than collecting zero."
      - "Left active pending on-target test results per ai/task.md §8.2.1."
  - version: "1.2"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status implemented -> closed. Source re-check confirms the fix present and unchanged. Closed on William's confirmation that GTach functions correctly on gtach.local."

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
| 1.0 | 2026-07-30 | Initial change document coupled to issue-66ef59a0. |
| 1.1 | 2026-07-30 | Status proposed → implemented; development-platform test results recorded, including a required correction to EDIT 3's `len(payload)` and the caller audit for the main_surface alias. Left active pending on-target results. |
| 1.2 | 2026-08-07 | Status implemented → closed. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
