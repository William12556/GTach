Created: 2026 July 30

# Issue: Framebuffer Write Path Performs Four Full-Frame Traversals and Forces a Sync Every Frame

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-66ef59a0"
  title: "write_to_framebuffer copies the frame four times, allocates a converted surface per frame, and calls flush/sync/fsync on a framebuffer device where they provide no benefit"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "performance"
  iteration: 1
  coupled_docs:
    change_ref: "change-66ef59a0"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Recommendation 2 (§9.1) addressing findings §4.1 and §5.1;
    recommendations 6, 7 and 8 (§9.2) addressing finding §5.1.
    Task list reference: ai/task.md §7.3.2.

affected_scope:
  components:
    - name: "DisplayRenderingEngine.initialize"
      file_path: "src/gtach/display/rendering/engine.py"
    - name: "DisplayRenderingEngine.swap_buffers"
      file_path: "src/gtach/display/rendering/engine.py"
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
  designs: []
  version: "0.2.67"

reproduction:
  prerequisites: >
    GTach running on gtach.local. The framebuffer path is exercised on
    every frame in every mode.
  steps:
    - "Read write_to_framebuffer at engine.py:300-378."
    - "Count the full-frame traversals: the swap_buffers blit, the per-frame convert, the bytes() materialisation, and the write itself."
    - "Observe the flush, sync and fsync calls that follow every write."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional. Every frame takes this path regardless of mode or
    content.
  preconditions: "fps_limit 60; 480x480 at 32 bits per pixel; 921,600 bytes per frame."
  test_data: >
    Framebuffer geometry confirmed on target 2026-07-30 per ai/task.md
    §7.5.1: bits_per_pixel 32, stride 1920, Size 921600. The engine's
    fb_size calculation of width x height x 4 matches exactly.
  error_output: "None. No exception is raised; the cost is silent."

behavior:
  expected: >
    A completed frame reaches the panel with one copy into the
    framebuffer and no synchronisation the device does not require.
  actual: >
    Four faults on the same path.

    (a) Forced synchronisation per frame — engine.py:346-356. After each
    write the code calls flush(), then sync() on the mmap or os.fsync on
    the file descriptor. On a framebuffer device these provide no
    correctness benefit; the write is already visible to the scan-out.
    They lengthen the write window, which widens the interval during
    which the display controller reads a partially updated buffer. The
    report identifies this as a contributing factor to the tear seam
    described in §4.1.

    (b) Redundant main_surface — engine.py:286-298 and 321. swap_buffers
    blits back_surface into main_surface, and write_to_framebuffer then
    immediately reads main_surface. The intermediate serves no purpose
    because nothing happens between the blit and the write. That is a
    921,600-byte copy per frame for no effect.

    (c) Per-frame surface conversion — engine.py:321.
    self.main_surface.convert(32, 0) allocates a new surface and copies
    the whole frame into it, every frame. The target format is fixed at
    initialisation and does not change.

    (d) Per-frame bytes materialisation — engine.py:324-333.
    bytes(buffer_data) copies the frame again to produce an immutable
    bytes object. Both mmap.write and file.write accept buffer-protocol
    objects, so the copy is avoidable.

    Together these are four full-frame traversals of 921,600 bytes each
    where one suffices, plus a surface allocation per frame, on a
    Cortex-A53 executing Python.
  impact: >
    Fault (a) bears directly on the flicker investigation: it widens the
    window in which the scan-out can read a partially written buffer.
    Faults (b), (c) and (d) are pure overhead in the frame budget. The
    report ranks all four as low risk, and (b), (c) and (d) as removable
    without any change to what is displayed.
  workaround: "None. The path is unconditional."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    The write path was built defensively for a device whose format was
    not known with confidence, so it converts and re-materialises the
    frame on every pass rather than establishing the format once. The
    double-buffer structure was carried over from a design that presents
    through SDL; with the dummy driver and a direct framebuffer write
    there is no presentation step between the two surfaces, so the second
    surface has no role. The synchronisation calls appear to have been
    added for durability, which is meaningful for a file and meaningless
    for a memory-mapped display device.
  technical_notes: >
    §7.5.1 has since removed the uncertainty that motivated the
    defensive path: bits_per_pixel is 32 and stride is 1920, exactly the
    engine's assumption.

    The size-mismatch handling at engine.py:335-341 truncates or
    zero-pads the buffer and logs at DEBUG. It operates on a bytes object
    and cannot slice a buffer-protocol view, so removing the bytes
    materialisation requires that path to be reconsidered rather than
    merely deleted. Recommendation 21 (task 7.3.3) separately proposes
    raising that log to ERROR; the two changes touch the same lines and
    7.3.2 should leave the severity question to 7.3.3.

    swap_buffers is declared on RenderingEngineInterface
    (display/rendering/interfaces.py:91) and is called from
    DisplayManager._display_loop. Removing main_surface must therefore
    keep the method and its signature, not delete it.

    Surfaces are created with pygame.Surface(surface_size)
    (engine.py:103-104), whose depth follows the display default. Creating
    back_surface at an explicit 32-bit depth removes the need to convert
    at all, which is a stronger form of recommendation 7 than converting
    once and retaining the result.

    The ENOSPC recovery path at engine.py:366-372 suggests a size
    mismatch was encountered on hardware at some point. It is retained.
  related_issues:
    - issue_ref: "issue-49b21ace"
      relationship: "blocks"
    - issue_ref: "issue-cb28980f"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Remove the per-frame synchronisation; write back_surface directly and
    reduce swap_buffers to a no-op; establish the 32-bit surface format
    once at initialisation; write a buffer-protocol view rather than a
    materialised bytes object. See change-66ef59a0.
  change_ref: "change-66ef59a0"
  resolved_date: "2026-07-30"
  resolved_by: "Claude Code, per prompt-66ef59a0"
  fix_description: >
    Four edits to src/gtach/display/rendering/engine.py, as specified, plus
    one correction to the specification itself — recorded below and in
    change-66ef59a0 verification.test_results.

    initialize now creates one surface, pygame.Surface(surface_size, 0, 32),
    assigns it to back_surface and aliases main_surface to it, and logs the
    resulting bitsize and masks at INFO. swap_buffers is a documented no-op
    returning True, retained because RenderingEngineInterface declares it
    and DisplayManager._display_loop calls it. write_to_framebuffer guards
    on back_surface, takes a buffer-protocol view via get_view('0'), and
    issues one seek and one write with no flush, sync or fsync. The
    size-mismatch DEBUG log and the truncate/pad behaviour are retained,
    materialising bytes only on that path, as is the ENOSPC branch calling
    _attempt_framebuffer_recovery. __init__ gained _view_fallback_logged so
    a view failure logs once rather than per frame.

    Correction to the specification. The prompt specifies
    `actual_size = len(payload)`. pygame.BufferProxy, which get_view('0')
    returns, does not implement __len__ — its size is exposed as .length.
    Written literally, the line raises TypeError on every frame; the
    exception is caught by the method's own general handler, which
    increments framebuffer_errors, logs at ERROR and returns False, so no
    frame is ever written and the panel stays blank. This was confirmed by
    running the verification suite against a build carrying the prompt's
    literal text: 34 of 50 assertions fail, with zero seeks and zero writes
    reaching the framebuffer. The size is therefore taken from .length when
    present, falling back to len() for the bytes and memoryview objects the
    fallback path produces. The prompt's stated requirement — compare the
    view length against fb_size — is met; only the expression differs.

verification:
  verified_date: "2026-07-30"
  verified_by: "Claude Code"
  test_results: >
    Development platform only (macOS, Python 3.11.14, pygame 2.6.1, SDL
    dummy driver). On-target verification is outstanding and this issue is
    left active pending it, per ai/task.md §8.2.1.

    Fifty assertions against the real DisplayRenderingEngine, all passing.
    See change-66ef59a0 verification.test_results for the full record.

    The colour-fidelity check is the one that matters most for an issue
    whose failure mode is visible on the panel: for the same drawing
    operations, the bytes delivered by the new 32-bit surface are identical
    to those the old main_surface.convert(32, 0) path produced, and both
    report masks (16711680, 65280, 255, 0) — XRGB8888. The delivered image
    is therefore unchanged, which is what the change requires.

    pytest tests/ — 11 passed. The suite is no longer empty: tests/
    acquired conftest.py and tests/utils/test_rwlock.py in commit ed1dea1,
    so this criterion is now met rather than vacuous. No test in it
    exercises the rendering engine, so it is a regression check on
    unrelated code rather than evidence for this change.
  closure_notes: ""

prevention:
  preventive_measures: >
    A per-frame path should establish invariant state at initialisation
    rather than re-deriving it each pass. Synchronisation primitives
    should be justified against the device they act on; flush and fsync
    are meaningful for durable storage and not for a framebuffer.
  process_improvements: >
    Where a defensive path exists because a hardware property was
    unknown, the property should be measured and the defence removed or
    justified, rather than carried indefinitely.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."
    - "The strings 'convert(32, 0)' and 'bytes(buffer_data)' no longer appear in write_to_framebuffer."
    - "No flush, sync or fsync call remains in write_to_framebuffer."
    - "write_to_framebuffer reads back_surface, not main_surface."
    - "swap_buffers retains its signature and returns True."
    - "back_surface reports get_bytesize() == 4 after initialisation."
    - "On gtach.local: the display renders correctly in DIGITAL, RADIAL, OPTIONS, DISCONNECTED and ACKNOWLEDGEMENT modes with no colour distortion, skew or blanking."
    - "On gtach.local: read frame_time_ms from the periodic log line and compare against the §7.5.3 baseline. A reduction is expected."
  verification_results: >
    Five of the eight steps PASS, one is met in substance but not as
    written, and two require gtach.local.

    PASS — python -m py_compile src/gtach/display/rendering/engine.py.

    QUALIFIED — "the strings 'convert(32, 0)' and 'bytes(buffer_data)' no
    longer appear in write_to_framebuffer". They do still appear, and
    necessarily so: prompt-66ef59a0 specifies that a get_view failure falls
    back to the previous convert-and-bytes path for that frame, and its
    EDIT 3 replacement text contains both strings inside that fallback.
    This step and the prompt cannot both be satisfied literally. The intent
    — that the per-frame path no longer converts the surface or
    materialises the frame into bytes — is met: on the normal path the
    payload written is the BufferProxy itself, asserted by spying on the
    write call and observing its argument type. The strings survive only on
    a degraded path that does not execute unless get_view raises.

    PASS — no flush, sync or fsync call remains in write_to_framebuffer,
    confirmed both by AST inspection of the method and by counting calls on
    a framebuffer double: exactly one seek and one write, zero flush, zero
    sync, and fileno never requested, on both the mmap and file branches.

    PASS — write_to_framebuffer reads back_surface, not main_surface.

    PASS — swap_buffers retains its signature, returns True, and contains
    no blit; pixel data is byte-identical across a call.

    PASS — back_surface reports get_bytesize() == 4 and get_bitsize() == 32
    after initialisation, and main_surface is back_surface.

    OUTSTANDING — on gtach.local, correct rendering in DIGITAL, RADIAL,
    OPTIONS, DISCONNECTED and ACKNOWLEDGEMENT modes with no colour
    distortion, skew or blanking. Off-target evidence in favour: the bytes
    delivered are identical to those the pre-change path produced for the
    same drawing, with identical channel masks.

    OUTSTANDING — on gtach.local, read frame_time_ms and compare against
    the ai/task.md §7.5.3 baseline. That baseline reading has itself not
    been taken yet — it is the outstanding step of the closed triple
    0b00759c — so this comparison has no reference point until it is.

traceability:
  design_refs: []
  change_refs:
    - "change-66ef59a0"
  test_refs: []

notes: >
  This is task 7.3.2 in ai/task.md §7.3 and part of step 4 in the
  recommended authoring order (§7.6.2). It ships in v0.4.0 alongside the
  remaining framebuffer work.

  Recommendation 2 is the flicker-relevant part of this triple and the
  report groups it under Priority 1. Recommendations 6, 7 and 8 are
  Priority 2 efficiency items grouped here because they modify the same
  method and would otherwise conflict.

  Sequencing: 7.3.2 precedes 7.3.4, which replaces the write itself with
  a page flip. Landing the efficiency work first means the page-flip
  change applies to a single clean write path rather than to four
  traversals.

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
      - "Initial issue document from display-ui-graphics-review.md recommendations 2, 6, 7 and 8."
  - version: "1.1"
    date: "2026-07-30"
    author: "Claude Code"
    changes:
      - "Status open -> resolved. change-66ef59a0 implemented; resolution date, executor and fix description recorded."
      - "Recorded a correction to the prompt's specification: len(payload) raises TypeError on a pygame.BufferProxy, which would have failed every frame silently; the size is taken from .length."
      - "Recorded five of eight verification steps as PASS, one as QUALIFIED and two as OUTSTANDING pending gtach.local."
      - "Recorded that verification step 2 cannot be satisfied literally, the prompt's own fallback path requiring the two strings it forbids; the per-frame path meets its intent."
      - "Recorded that pytest tests/ now passes 11 tests rather than collecting zero, tests/ having been populated in commit ed1dea1."
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
| 1.0 | 2026-07-30 | Initial issue document from display-ui-graphics-review.md recommendations 2, 6, 7 and 8. |
| 1.1 | 2026-07-30 | Status open → resolved; fix description and per-step verification recorded, including a correction to the prompt's `len(payload)` specification. Left active pending on-target results. |
| 1.2 | 2026-08-07 | Status resolved → closed. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
