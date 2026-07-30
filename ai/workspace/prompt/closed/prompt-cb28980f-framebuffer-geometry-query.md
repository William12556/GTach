Created: 2026 July 30

# Prompt: Derive Framebuffer Size from the Device, and Report Disagreement at ERROR

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-cb28980f"
  task_type: "code_generation"
  source_ref: "change-cb28980f"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-cb28980f"
    change_iteration: 1

context:
  purpose: >
    Stop assuming the framebuffer's depth and stride. The engine sizes its
    buffer as width x height x 4 and, where the device disagrees,
    truncates or zero-pads and logs at DEBUG — a level production does not
    emit. The result is a skewed or partially blank panel with no
    diagnostic. Padding is also the wrong correction for a stride
    mismatch: it fixes the byte count while leaving every row after the
    first offset, which renders as a shear.
  integration: >
    One file: src/gtach/display/rendering/engine.py. Four edits.
    Executor is Claude Code; AEL is not used. change-49b21ace is already
    implemented and supplies fcntl, struct, FB_VAR_STRUCT, a working
    FBIOGET_VSCREENINFO call and the _fb_dev_usable guard — reuse them.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/rendering/engine.py."
    - "Do NOT modify _setup_page_flip, _wait_for_vsync or _pan_display. change-49b21ace owns them and its triple is closed."
    - "Do NOT use FBIOGET_FSCREENINFO. struct fb_fix_screeninfo contains unsigned long fields whose size and alignment differ between 32-bit and 64-bit builds; unpacking it needs architecture-dependent offset arithmetic. Read the stride from sysfs instead. This is a deliberate departure from the source report and is recorded in change-cb28980f."
    - "Do NOT change the truncate or pad behaviour. Only the log level, its guard and the counter change."
    - "Do NOT change surface_size, the surfaces, or anything about what is composed."
    - "Do NOT fail initialisation on a geometry disagreement. Log at ERROR and continue — a skewed display is more useful than none."
    - "Do not hard-code fb0. Derive the sysfs node from the basename of self.framebuffer_path."
    - "The geometry query MUST occur before mmap.mmap is called, because _setup_page_flip remaps at twice fb_size and both must see the same value."
    - "Type hints on all new methods; Google-style docstrings; PEP 8."

specification:
  description: >
    Query the device's geometry at initialisation, derive fb_size from
    stride and height, report disagreement with the composed surface at
    ERROR, and raise the write-path size-mismatch log from DEBUG to ERROR
    with a once-only guard and a counter.
  requirements:
    functional:
      - "bits_per_pixel, xres, yres and xres_virtual are read from FBIOGET_VSCREENINFO."
      - "The stride is read from /sys/class/graphics/<node>/stride, falling back to xres_virtual x bits_per_pixel // 8."
      - "fb_size is stride x yres when the query succeeds."
      - "The queried geometry and the stride source are logged at INFO at every start."
      - "A depth other than 32, a resolution differing from surface_size, or a stride differing from xres x bits_per_pixel // 8 is logged at ERROR."
      - "Initialisation continues in every case."
      - "The write-path size mismatch is logged at ERROR, once, and counted."
      - "A non-zero mismatch count is reported at cleanup."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Geometry queried once at initialisation; nothing added to the frame path"
      metric: "time"

design:
  architecture: >
    The device is the authority on its own geometry. The engine reads it
    once at start, sizes its buffer from it, and reports any disagreement
    between what the device provides and what the engine composes at a
    level the operator will see.
  components:
    - name: "DisplayRenderingEngine._query_framebuffer_geometry"
      type: "function"
      purpose: "Read the device's authoritative geometry."
      interface:
        inputs: []
        outputs:
          type: "Optional[Dict[str, int]]"
          description: "Keys xres, yres, xres_virtual, bits_per_pixel, line_length. None if the query could not be made."
        raises:
          - "None. All failures are caught and reported as None."
      logic:
        - "Return None unless self._fb_dev_usable()."
        - "Read FBIOGET_VSCREENINFO and unpack with the existing FB_VAR_STRUCT."
        - "Take xres, yres, xres_virtual and bits_per_pixel by index."
        - "Stride: read the text of /sys/class/graphics/<node>/stride where <node> is os.path.basename(self.framebuffer_path); int() it."
        - "On any failure reading sysfs, derive line_length = xres_virtual * bits_per_pixel // 8 and note the fallback."
        - "Log at INFO: the four values, the stride, and which stride source was used."
        - "Return the dict. On exception log at WARNING and return None."
    - name: "DisplayRenderingEngine._initialize_framebuffer"
      type: "function"
      purpose: "Open, query, size, map, then select a presentation mode."
      logic:
        - "Open self.fb_dev first, before fb_size is fixed."
        - "Call _query_framebuffer_geometry()."
        - "If geometry is not None: fb_size = line_length * yres; store fb_line_length and fb_bits_per_pixel."
        - "If geometry is None: retain the existing surface_size[0] * surface_size[1] * 4 assumption and log at WARNING."
        - "Then check for disagreement and log at ERROR — see the three conditions in the deliverable."
        - "Then map, then select the presentation mode exactly as the current code does. Do not alter that block."
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      type: "function"
      purpose: "Report a size mismatch at a level production emits."
      logic:
        - "Replace self.logger.debug with self.logger.error, guarded by self._size_mismatch_logged so it fires once."
        - "Increment self._size_mismatch_count on every occurrence."
        - "Include the stride and depth in the message so the line is self-contained."
        - "Leave the truncate and pad behaviour exactly as it is."
    - name: "DisplayRenderingEngine.cleanup"
      type: "function"
      purpose: "Report the accumulated mismatch count."
      logic:
        - "If self._size_mismatch_count is non-zero, log it once at ERROR before the existing teardown."
  dependencies:
    internal:
      - "change-49b21ace — supplies fcntl, struct, FB_VAR_STRUCT, FBIOGET_VSCREENINFO and _fb_dev_usable. Not modified."
      - "change-66ef59a0 — supplies the write path containing the mismatch log."
    external: []

data_schema:
  entities:
    - name: "geometry"
      attributes:
        - name: "xres"
          type: "int"
          constraints: "FB_VAR index 0."
        - name: "yres"
          type: "int"
          constraints: "FB_VAR index 1."
        - name: "xres_virtual"
          type: "int"
          constraints: "FB_VAR index 2."
        - name: "bits_per_pixel"
          type: "int"
          constraints: "FB_VAR index 6."
        - name: "line_length"
          type: "int"
          constraints: "Bytes per row. From sysfs, or derived."
      validation:
        - "On the current target: xres 480, yres 480, xres_virtual 480, bits_per_pixel 32, line_length 1920, giving fb_size 921600 — identical to the previous assumption."

error_handling:
  strategy: >
    A geometry disagreement is reported, not fatal. A failed query
    degrades to the current assumption. The write-path diagnostic is
    raised in level but suppressed after the first occurrence so it cannot
    flood at the frame rate.
  exceptions:
    - exception: "OSError"
      condition: "FBIOGET_VSCREENINFO fails."
      handling: "Log at WARNING; return None; the assumption stands and initialisation continues."
    - exception: "OSError, ValueError"
      condition: "sysfs stride unreadable or non-numeric."
      handling: "Derive from xres_virtual x bits_per_pixel // 8; log the fallback at INFO."
    - exception: "Exception"
      condition: "Any other failure in the query."
      handling: "Log at WARNING with exc_info; return None."
  logging:
    level: "INFO for the geometry itself; ERROR for a disagreement; WARNING when the query could not be made"
    format: "self.logger.error(...) once, guarded by self._size_mismatch_logged"

testing:
  unit_tests:
    - scenario: "480 x 480, 32 bits, stride 1920."
      expected: "fb_size 921600; no ERROR; geometry logged at INFO."
    - scenario: "16 bits per pixel reported."
      expected: "ERROR naming the depth; fb_size from the reported stride; initialisation continues."
    - scenario: "Stride 2048 against xres 480 at 32 bits."
      expected: "ERROR identifying the stride disagreement; fb_size 2048 x 480."
    - scenario: "Reported resolution differs from surface_size."
      expected: "ERROR naming both values; initialisation continues."
    - scenario: "sysfs stride unreadable."
      expected: "Stride derived; fallback source logged at INFO."
    - scenario: "FBIOGET_VSCREENINFO raises."
      expected: "Query returns None; assumption retained; WARNING logged."
    - scenario: "framebuffer_path is /dev/fb1."
      expected: "/sys/class/graphics/fb1/stride is the path read."
    - scenario: "Three mismatched writes."
      expected: "Exactly one ERROR; count reaches 3; truncate or pad applied each time."
    - scenario: "cleanup with a non-zero count."
      expected: "The total is reported once."
  edge_cases:
    - "yres reported as 0 — guard so fb_size is never 0; fall back to the assumption and log at ERROR."
    - "line_length smaller than xres x bpp // 8 — physically impossible; log at ERROR and use the assumption."
    - "Direct-file fallback in force so fb_dev was closed — _fb_dev_usable returns False and the query is skipped."
    - "Mock rendering mode with pygame unavailable — no device, no query, no exception."
  validation:
    - "The query call appears before mmap.mmap in _initialize_framebuffer."
    - "_setup_page_flip is byte-identical to its current text."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/rendering/engine.py in place. Create no new file."
    - "Apply the four edits below. Change nothing else."
  files:
    - path: "src/gtach/display/rendering/engine.py"
      content: |
        EDIT 1 — constants and state

        Add to the FB_VAR index block that change-49b21ace established
        (currently FB_VAR_YRES 1, FB_VAR_YRES_VIRTUAL 3, FB_VAR_YOFFSET 5,
        FB_VAR_ACTIVATE 21):

            FB_VAR_XRES = 0
            FB_VAR_XRES_VIRTUAL = 2
            FB_VAR_BITS_PER_PIXEL = 6

        Add to __init__ alongside the existing framebuffer state:

                # Geometry as reported by the device (change-cb28980f)
                self.fb_line_length = 0
                self.fb_bits_per_pixel = 0
                self._size_mismatch_logged = False
                self._size_mismatch_count = 0

        EDIT 2 — add _query_framebuffer_geometry, immediately before
        _initialize_framebuffer

            def _query_framebuffer_geometry(self) -> Optional[Dict[str, int]]:
                """Read the device's authoritative geometry.

                The engine has assumed 32 bits per pixel and a stride equal
                to width x 4. The device reports both; this reads them so a
                disagreement is detected rather than rendered
                (display review §8.3, recommendation 21).

                The stride comes from sysfs rather than FBIOGET_FSCREENINFO.
                struct fb_fix_screeninfo contains unsigned long fields whose
                size and alignment differ between 32- and 64-bit builds, so
                unpacking it needs architecture-dependent offset arithmetic;
                the sysfs attribute is the same value as stable text.

                Returns:
                    Geometry dict, or None if the device could not be queried.
                """
                if not self._fb_dev_usable():
                    return None

                try:
                    var = struct.unpack(FB_VAR_STRUCT, fcntl.ioctl(
                        self.fb_dev.fileno(), FBIOGET_VSCREENINFO,
                        bytes(struct.calcsize(FB_VAR_STRUCT))
                    ))

                    geometry = {
                        'xres': var[FB_VAR_XRES],
                        'yres': var[FB_VAR_YRES],
                        'xres_virtual': var[FB_VAR_XRES_VIRTUAL],
                        'bits_per_pixel': var[FB_VAR_BITS_PER_PIXEL],
                    }

                    node = os.path.basename(self.framebuffer_path)
                    stride_source = 'sysfs'
                    try:
                        with open(f'/sys/class/graphics/{node}/stride', 'r') as f:
                            geometry['line_length'] = int(f.read().strip())
                    except (OSError, ValueError):
                        stride_source = 'derived'
                        geometry['line_length'] = (
                            geometry['xres_virtual'] * geometry['bits_per_pixel'] // 8
                        )

                    self.logger.info(
                        f"Framebuffer geometry: {geometry['xres']}x{geometry['yres']}, "
                        f"virtual {geometry['xres_virtual']}, "
                        f"{geometry['bits_per_pixel']}-bit, "
                        f"stride {geometry['line_length']} ({stride_source})"
                    )
                    return geometry

                except Exception as e:
                    self.logger.warning(
                        f"Framebuffer geometry query failed, using assumed "
                        f"dimensions: {e}", exc_info=True
                    )
                    return None

        Ensure Optional and Dict are imported from typing — Optional and
        Tuple already are; add Dict if absent.

        EDIT 3 — _initialize_framebuffer

        Replace the opening of the method. Currently:

                try:
                    # Calculate framebuffer size (RGBA32)
                    self.fb_size = self.surface_size[0] * self.surface_size[1] * 4

                    # Try memory-mapped approach first
                    try:
                        self.fb_dev = open(self.framebuffer_path, 'r+b')
                        self.fb = mmap.mmap(self.fb_dev.fileno(), self.fb_size)

        with:

                try:
                    # Assumed size, replaced below if the device can be queried.
                    self.fb_size = self.surface_size[0] * self.surface_size[1] * 4

                    # Try memory-mapped approach first
                    try:
                        self.fb_dev = open(self.framebuffer_path, 'r+b')

                        # Query BEFORE mapping: _setup_page_flip remaps at
                        # twice fb_size, so both must see the same value.
                        geometry = self._query_framebuffer_geometry()
                        if geometry:
                            self.fb_bits_per_pixel = geometry['bits_per_pixel']
                            self.fb_line_length = geometry['line_length']

                            if geometry['yres'] > 0 and geometry['line_length'] > 0:
                                self.fb_size = geometry['line_length'] * geometry['yres']

                            expected_stride = (
                                geometry['xres'] * geometry['bits_per_pixel'] // 8
                            )
                            if geometry['bits_per_pixel'] != 32:
                                self.logger.error(
                                    f"Framebuffer depth is {geometry['bits_per_pixel']}-bit; "
                                    f"the engine composes 32-bit surfaces. Colour will be wrong."
                                )
                            if (geometry['xres'], geometry['yres']) != tuple(self.surface_size):
                                self.logger.error(
                                    f"Framebuffer is {geometry['xres']}x{geometry['yres']} but "
                                    f"the composed surface is {self.surface_size[0]}x"
                                    f"{self.surface_size[1]}. The image will not fill the panel."
                                )
                            if geometry['line_length'] != expected_stride:
                                self.logger.error(
                                    f"Framebuffer stride is {geometry['line_length']} but "
                                    f"{expected_stride} was expected for {geometry['xres']} px "
                                    f"at {geometry['bits_per_pixel']}-bit. Rows will shear; "
                                    f"zero-padding corrects the byte count but not the offset."
                                )
                        else:
                            self.logger.warning(
                                f"Framebuffer geometry unavailable; assuming "
                                f"{self.surface_size[0]}x{self.surface_size[1]} at 32-bit "
                                f"({self.fb_size} bytes)"
                            )

                        self.fb = mmap.mmap(self.fb_dev.fileno(), self.fb_size)

        Leave the rest of the method exactly as it is — the use_mmap
        assignment, the except branch with the direct-file fallback, the
        presentation-mode block and the outer except.

        EDIT 4 — write_to_framebuffer and cleanup

        Replace the mismatch log line. Currently:

                        if actual_size != self.fb_size:
                            self.logger.debug(f"Buffer size mismatch: {actual_size} vs {self.fb_size}")

        with:

                        if actual_size != self.fb_size:
                            self._size_mismatch_count += 1
                            if not self._size_mismatch_logged:
                                self._size_mismatch_logged = True
                                # Raised from DEBUG: production runs at INFO, so
                                # the previous level meant a visible fault had no
                                # visible diagnostic (recommendation 21).
                                self.logger.error(
                                    f"Buffer size mismatch: {actual_size} vs {self.fb_size} "
                                    f"(stride {self.fb_line_length}, "
                                    f"{self.fb_bits_per_pixel}-bit). Padding or truncating; "
                                    f"the image may be skewed. Further occurrences suppressed."
                                )

        Leave the truncate and pad lines that follow exactly as they are.

        In cleanup, before the existing teardown, add:

                    if self._size_mismatch_count:
                        self.logger.error(
                            f"Framebuffer size mismatched on "
                            f"{self._size_mismatch_count} frames this session"
                        )

success_criteria:
  - "python -m py_compile src/gtach/display/rendering/engine.py passes."
  - "pytest tests/ passes with no new failures."
  - "_query_framebuffer_geometry exists and returns Optional[Dict[str, int]]."
  - "It is called in _initialize_framebuffer before mmap.mmap."
  - "FBIOGET_FSCREENINFO does not appear anywhere in the file."
  - "The sysfs path is built from os.path.basename(self.framebuffer_path), not hard-coded to fb0."
  - "fb_size is assigned from line_length x yres when the query succeeds."
  - "Three separate ERROR conditions exist: depth, resolution, stride."
  - "Initialisation continues after any of them."
  - "The write-path mismatch is logged at ERROR, guarded by _size_mismatch_logged, and counted in _size_mismatch_count."
  - "The truncate and pad behaviour is unchanged."
  - "_setup_page_flip, _wait_for_vsync and _pan_display are byte-identical to their current text."
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
      - name: "_query_framebuffer_geometry"
        module: "gtach.display.rendering.engine"
        signature: "_query_framebuffer_geometry(self) -> Optional[Dict[str, int]]"
      - name: "_initialize_framebuffer"
        module: "gtach.display.rendering.engine"
        signature: "_initialize_framebuffer(self) -> None"
      - name: "write_to_framebuffer"
        module: "gtach.display.rendering.engine"
        signature: "write_to_framebuffer(self) -> bool"
      - name: "_fb_dev_usable"
        module: "gtach.display.rendering.engine"
        signature: "_fb_dev_usable(self) -> bool"
    constants:
      - name: "FB_VAR_XRES"
        module: "gtach.display.rendering.engine"
        type: "int"
      - name: "FB_VAR_XRES_VIRTUAL"
        module: "gtach.display.rendering.engine"
        type: "int"
      - name: "FB_VAR_BITS_PER_PIXEL"
        module: "gtach.display.rendering.engine"
        type: "int"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-cb28980f-framebuffer-geometry-query.md
  and close the prompt when finished. Leave the issue and change active
  pending test results (ai/task.md §8.2.1).

  On the current target the derived fb_size is identical to the assumed
  one — stride 1920 x yres 480 = 921,600 — so no behavioural change is
  expected. The visible effect is a geometry line in the startup log. If
  an ERROR appears instead, the device disagrees with an assumption the
  engine has been making silently, and that is the finding.

  This task's role has changed since it was planned. §7.6.1 recorded
  7.3.4 as depending on it for the geometry facts; the manual §7.5.1
  observation supplied them first and 7.3.4 is already implemented. This
  is therefore defensive hardening and a log-level correction rather than
  a prerequisite. The observation confirms one device at one moment; the
  query confirms it at every start on every device.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-cb28980f. |
| 1.1 | 2026-07-30 | Executed by Claude Code. All four edits applied; 70 assertions against a faked ioctl and sysfs surface, all passing; pytest tests/ 11 passed. One criterion is met in substance only: "FBIOGET_FSCREENINFO does not appear anywhere in the file" cannot hold, because EDIT 2's own docstring names the ioctl in explaining why sysfs is used instead — the ioctl is not used, and no such constant or call exists. One addition beyond EDIT 3: a stride below xres x bpp // 8 is reported at ERROR and not trusted to size the mapping, which edge_cases requires but the code block did not implement; under the literal text such a device gets a half-size buffer and every frame truncated to half the panel. Both recorded in change-cb28980f. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/; the issue and change remain active pending on-target results per ai/task.md §8.2.1. |

---

Copyright (c) 2026 William Watson. MIT License.
