Created: 2026 August 07

# Prompt: Compensate 8 px Vertical Shift in Framebuffer Write

---

## Table of Contents

- [1. Prompt](<#1. prompt>)
- [2. Version History](<#2. version history>)

---

## 1. Prompt

```yaml
prompt_info:
  id: "prompt-a4f27c91"
  task_type: "debug"
  source_ref: "change-a4f27c91"
  target_profile: "claude_code"
  date: "2026-08-07"
  iteration: 1
  coupled_docs:
    change_ref: "change-a4f27c91"
    change_iteration: 1

context:
  purpose: >
    The composed 480x480 frame is displayed approximately 8 px higher
    than the HyperPixel 2.1 Round panel's active area, established by
    on-target diagnostic isolation (issue-a4f27c91) to originate below
    GTach's framebuffer-write boundary rather than in application draw
    logic. This prompt compensates the measured offset at that single
    boundary.
  integration: >
    DisplayRenderingEngine.write_to_framebuffer is the sole point where
    every rendered frame — RADIAL, OPTIONS, ACKNOWLEDGEMENT, splash,
    disconnected, setup — passes before reaching /dev/fb0. A fix here
    applies uniformly without touching any caller or any draw call site.
  knowledge_references:
    - "ai/workspace/issues/issue-a4f27c91-vertical-shift-compensation.md"
    - "ai/workspace/change/change-a4f27c91-vertical-shift-compensation.md"
    - "ai/workspace/design/design-c9d0e1f2-component_display_rendering_engine.md"
  constraints:
    - "Modify only src/gtach/display/rendering/engine.py (implementation) and its paired test file (tests, per existing project layout)."
    - "No change to DisplayManager, any draw call site, touch coordinate mapping, TouchEventCoordinator, or config.yaml."
    - "No change to /boot/config.txt or any dpi_timings value — explicitly out of scope per change-a4f27c91."
    - "The adjustment must be a no-op fallback (write the original, unmodified payload) if shift_bytes is zero, negative, or exceeds the payload length — never raise."
    - "Total bytes written to the framebuffer must remain exactly self.fb_size in every case; only content, not length, changes."
    - "Both the single-buffer write branch and the page-flip write branch in write_to_framebuffer must receive the identical row-shifted payload; do not add the shift to only one branch."

specification:
  description: >
    In DisplayRenderingEngine (src/gtach/display/rendering/engine.py),
    add a named constant VERTICAL_OFFSET_PX = 8 and a row-shift step in
    write_to_framebuffer that prepends VERTICAL_OFFSET_PX rows of zero
    bytes to the payload about to be written and drops the same number
    of rows from its end, so the visible image is displayed
    VERTICAL_OFFSET_PX pixels lower on the physical panel without
    changing total payload size.
  requirements:
    functional:
      - "Add VERTICAL_OFFSET_PX as a constant (class-level on DisplayRenderingEngine, consistent with the existing display_center / display_safe_radius / display_max_radius constants set in __init__, or as a module-level constant alongside FB_VAR_* — match the file's existing style). Value: 8. Comment must cite issue-a4f27c91 and state it is a measured physical offset for this deployment target, not a general panel-model constant."
      - "In write_to_framebuffer, after the existing size-reconciliation block (the block handling actual_size != self.fb_size) and before the existing page_flip/single-buffer write branches, compute row_bytes from self.fb_line_length if it is greater than zero, otherwise from self.surface_size[0] * 4."
      - "Compute shift_bytes = row_bytes * VERTICAL_OFFSET_PX."
      - "If 0 < shift_bytes < len(payload): replace payload with (bytes(shift_bytes) + payload[:-shift_bytes]), preserving total length. If payload is not already a bytes/bytearray at this point (e.g. still a BufferProxy from the get_view('0') fast path), materialise it with bytes(payload) before slicing — this is required regardless of whether the earlier size-reconciliation branch already materialised it, since that branch is only taken on a size mismatch."
      - "If shift_bytes is 0, negative, or >= len(payload): leave payload unmodified and proceed to the existing write logic exactly as today."
      - "Both the page_flip branch (self.fb.seek(target * self.fb_size); self.fb.write(payload)) and the single-buffer branch (self.fb.seek(0); self.fb.write(payload)) must write the same possibly-shifted payload variable — do not duplicate the shift logic per branch; compute it once above the branch dispatch."
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Thread-safe: the shift computation and payload replacement occur inside the existing `with self._lock:` block already present in write_to_framebuffer — do not introduce a second lock or move the logic outside it."
        - "Comprehensive error handling: wrap the shift computation in a way consistent with the method's existing try/except structure — a failure to compute or apply the shift must not prevent the existing (unshifted) write from proceeding. Falling through to the existing behavioural fallback (write the original payload) on any exception in this new block satisfies this."
        - "Debug logging with traceback: log at INFO or DEBUG level (not ERROR — this is expected, successful behaviour, not a fault) the first time the shift is applied per session, consistent with the existing pattern of one-time informational logging elsewhere in this file (e.g. self._view_fallback_logged, self._size_mismatch_logged)."
        - "Professional docstrings: update write_to_framebuffer's docstring to note the vertical offset compensation and reference issue-a4f27c91."
  performance:
    - target: "Per-frame overhead of the row-shift"
      metric: "One bytes() materialisation and one byte-string concatenation of self.fb_size bytes per frame when VERTICAL_OFFSET_PX is nonzero — equivalent order of cost to the existing size-mismatch fallback path already present in this method, which already performs a comparable bytes() materialisation. No new per-frame overhead is introduced beyond what the existing fallback path already demonstrates is acceptable at 60 FPS on this target."

design:
  architecture: >
    Single-point compensation at the hardware-output boundary, matching
    the existing pattern in this file where all hardware-specific
    handling (stride, bits-per-pixel, size mismatch, page flip, vsync)
    is confined to DisplayRenderingEngine rather than distributed across
    callers.
  components:
    - name: "DisplayRenderingEngine.VERTICAL_OFFSET_PX"
      type: "constant"
      purpose: "Named, single-source value for the measured vertical panel offset, in pixels."
      interface:
        inputs: []
        outputs:
          type: "int"
          description: "8"
        raises: []
      logic:
        - "Defined once; referenced only inside write_to_framebuffer."
    - name: "DisplayRenderingEngine.write_to_framebuffer (modified)"
      type: "function"
      purpose: "Existing method; extended to apply the row-shift compensation before writing to hardware."
      interface:
        inputs: []
        outputs:
          type: "bool"
          description: "True if write successful — return contract unchanged from the current implementation."
        raises: []
      logic:
        - "Existing: obtain payload via get_view('0') or convert()-based fallback."
        - "Existing: reconcile payload length against self.fb_size (pad/truncate on mismatch)."
        - "NEW: compute row_bytes and shift_bytes; if valid, replace payload with the zero-prefixed, tail-dropped version."
        - "Existing: dispatch to page_flip or single-buffer write branch, using the (possibly shifted) payload."
        - "Existing: update self._stats, return True; existing exception handling for OSError and general Exception unchanged."
  dependencies:
    internal: []
    external: []

data_schema:
  entities: []

error_handling:
  strategy: >
    The row-shift step must never be able to turn a successful write
    into a failed one. Any exception raised while computing or applying
    the shift is caught locally and the method proceeds with the
    original, unshifted payload — the same behaviour as before this
    change. The method's existing outer try/except (OSError and general
    Exception around the write itself) is unchanged and unaffected.
  exceptions:
    - exception: "Exception (broad, local to the new shift block only)"
      condition: "Any failure computing row_bytes, shift_bytes, or constructing the shifted payload."
      handling: "Log once at DEBUG or INFO (not ERROR — the existing write still proceeds correctly with the fallback), then continue with the original unshifted payload."
  logging:
    level: "INFO for the one-time confirmation that the shift is active; DEBUG or INFO for the local fallback case above."
    format: "Match the existing f-string logger calls in this file."

testing:
  unit_tests:
    - scenario: "write_to_framebuffer is called with a payload where row 0 (the first row_bytes bytes) is a distinguishable non-zero pattern and VERTICAL_OFFSET_PX is 8."
      expected: "The bytes captured by the mock framebuffer's write() begin with row_bytes * 8 zero bytes, followed by the original payload's bytes[0 : fb_size - row_bytes*8]."
    - scenario: "Total length of the bytes written to the mock framebuffer."
      expected: "Equals self.fb_size exactly, unchanged from pre-change behaviour."
    - scenario: "self.page_flip is True; write_to_framebuffer is called."
      expected: "The mock framebuffer's seek() is called with target * self.fb_size (existing behaviour) and write() receives the same shifted payload as the single-buffer case."
    - scenario: "self.fb_line_length is 0 (geometry query failed at init) — row_bytes falls back to surface_size[0] * 4."
      expected: "Shift is computed and applied using the fallback row_bytes value; no exception."
    - scenario: "VERTICAL_OFFSET_PX temporarily monkeypatched to a value >= payload length (boundary/defensive case)."
      expected: "Original unshifted payload is written; no exception raised."
  edge_cases:
    - "Payload length exactly equal to shift_bytes (degenerate: entire frame would be zeroed) — must fall through to the unmodified-payload path per the shift_bytes >= len(payload) guard."
    - "self.fb is the direct-file-write fallback object (use_mmap False) rather than an mmap — the shift logic must be agnostic to which object self.fb is, since both support .seek()/.write()."
  validation:
    - "pytest tests/ passes, count increased by exactly the new test cases added, zero regressions in existing cases."
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths."
    - "Do not create new files beyond the modified implementation file and its corresponding test file — locate the existing test file for DisplayRenderingEngine / write_to_framebuffer under tests/ and extend it; do not create a parallel test file if one already covers this class."
  files:
    - path: "src/gtach/display/rendering/engine.py"
      content: "Modified: VERTICAL_OFFSET_PX constant added; write_to_framebuffer extended with the row-shift compensation as specified above."
    - path: "tests/ (existing file covering DisplayRenderingEngine.write_to_framebuffer — locate before writing; do not guess a path)"
      content: "Extended: five test cases per the testing section above, added to the existing test class/module for this component."

success_criteria:
  - "python -m py_compile src/gtach/display/rendering/engine.py passes."
  - "VERTICAL_OFFSET_PX is defined exactly once in src/gtach/display/rendering/engine.py, with a comment citing issue-a4f27c91."
  - "Both the page_flip and single-buffer write branches in write_to_framebuffer write an identical payload variable — grep for 'self.fb.write(' in src/gtach/display/rendering/engine.py: both call sites reference the same local variable name, and that variable is assigned the shifted-or-fallback payload exactly once, above the branch dispatch."
  - "No occurrence of the string 'dpi_timings' or path '/boot/config.txt' appears anywhere in the diff produced by this prompt (grep the diff, not the repository — the strings legitimately exist elsewhere in the repository, e.g. docs/pi-setup.md and this T-Doc triple itself)."
  - "No file under src/gtach/ other than src/gtach/display/rendering/engine.py appears in the diff produced by this prompt."
  - "pytest tests/ passes, with the count of passing tests strictly greater than the pre-change baseline by the number of new test cases added, and zero failures."
  - "The method's return type and signature (write_to_framebuffer(self) -> bool) are unchanged — grep confirms exactly one definition, matching this signature, in the file."

element_registry:
  source: ""
  entries:
    modules: []
    classes:
      - name: "DisplayRenderingEngine"
        module: "src/gtach/display/rendering/engine.py"
    functions:
      - name: "write_to_framebuffer"
        module: "src/gtach/display/rendering/engine.py"
        signature: "def write_to_framebuffer(self) -> bool"
    constants:
      - name: "VERTICAL_OFFSET_PX"
        module: "src/gtach/display/rendering/engine.py"
        type: "int"

tactical_brief: ""

notes: >
  This prompt targets Claude Code (target_profile: claude_code), so
  tactical_brief is intentionally empty per T04 schema — it is not
  consumed by this profile. The measured offset (8 px) comes from
  issue-a4f27c91's on-target crosshair diagnostic; on-target
  verification against the physical panel after this change is still
  required and is out of scope for this prompt's own success_criteria,
  which are limited to what can be confirmed from source and from
  pytest. See issue-a4f27c91 verification_enhanced for the physical
  verification steps to be run separately after deployment.

version_history:
  - version: "1.0"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Initial prompt document, coupled to change-a4f27c91."
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-07 | Initial prompt document, coupled to change-a4f27c91. |

---

Copyright (c) 2026 William Watson. MIT License.
