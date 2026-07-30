Created: 2026 July 30

# Prompt: One Copy per Frame, No Forced Synchronisation

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-66ef59a0"
  task_type: "optimization"
  source_ref: "change-66ef59a0"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-66ef59a0"
    change_iteration: 1

context:
  purpose: >
    Reduce the per-frame framebuffer path from four full-frame
    traversals of 921,600 bytes to one, and stop forcing a synchronisation
    the device does not need. The synchronisation lengthens the write
    window, which widens the interval in which the display controller can
    read a partially updated buffer.
  integration: >
    One file: src/gtach/display/rendering/engine.py. Four edits.
    Executor is Claude Code; AEL is not used. Precedes task 7.3.4, which
    replaces the write itself with a page flip — landing this first means
    the page-flip change applies to one clean write rather than four
    traversals.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/rendering/engine.py."
    - "Do NOT add FBIO_WAITFORVSYNC or FBIOPAN_DISPLAY. That is task 7.3.4."
    - "Do NOT add ioctl geometry queries or change the mismatch log level. That is task 7.3.3, which touches the same lines."
    - "Do NOT remove swap_buffers. It is declared on RenderingEngineInterface (interfaces.py:91) and called from DisplayManager._display_loop. Keep the name, signature and return type."
    - "Do NOT remove the size-mismatch truncate/pad behaviour or its DEBUG log. Its severity is 7.3.3's question."
    - "Do NOT remove the ENOSPC recovery path or _attempt_framebuffer_recovery."
    - "Do not change create_surface, clear_surface, draw_circle, draw_rect, draw_line, blit_surface or render_text."
    - "Do not change what is rendered. This change alters the delivery path only."
    - "Add no new dependency. mmap, os and pygame are already imported."
    - "Type hints on public interfaces; Google-style docstrings; PEP 8."

specification:
  description: >
    Create a single 32-bit back_surface at initialisation, write it
    directly through a buffer-protocol view, reduce swap_buffers to a
    documented no-op, and remove flush, sync and fsync from the write.
  requirements:
    functional:
      - "back_surface is created at an explicit 32-bit depth; get_bytesize() returns 4."
      - "main_surface is an alias of back_surface, so both RenderTarget values resolve to the written surface."
      - "swap_buffers returns True without copying pixel data."
      - "write_to_framebuffer obtains a buffer view of back_surface rather than converting and materialising bytes."
      - "The matching write path issues one seek and one write, with no flush, sync or fsync."
      - "A get_view failure falls back to the previous bytes path for that frame and logs at ERROR once, not per frame."
      - "The size-mismatch truncate and pad behaviour is preserved."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Three full-frame traversals and one surface allocation removed per frame"
      metric: "time"

design:
  architecture: >
    One surface, one copy. The frame is composed in back_surface at the
    framebuffer's own format and delivered by a single write of a view
    over its memory. The second surface and every format conversion are
    removed because nothing occurs between composition and delivery.
  components:
    - name: "DisplayRenderingEngine.initialize"
      type: "function"
      purpose: "Establish the framebuffer format once."
      logic:
        - "Replace the two pygame.Surface(surface_size) creations with one: pygame.Surface(surface_size, 0, 32)."
        - "Assign it to self.back_surface and alias self.main_surface = self.back_surface."
        - "Log at INFO: get_bitsize() and get_masks(), so a format mismatch is visible in the log rather than only on the panel."
        - "Leave the pygame.display.init(), pygame.font.init(), SDL_VIDEODRIVER assignment and _initialize_framebuffer call untouched."
    - name: "DisplayRenderingEngine.swap_buffers"
      type: "function"
      purpose: "Retained for interface compatibility; no longer copies."
      interface:
        inputs: []
        outputs:
          type: "bool"
          description: "Always True."
        raises:
          - "None."
      logic:
        - "Return True immediately."
        - "Docstring must state that back_surface is written directly, that no intermediate copy is required, and that the method is retained to satisfy RenderingEngineInterface and its caller in DisplayManager._display_loop."
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      type: "function"
      purpose: "Deliver the composed frame with a single write."
      interface:
        inputs: []
        outputs:
          type: "bool"
          description: "True if the write succeeded."
        raises:
          - "None. Existing OSError and Exception handlers retained."
      logic:
        - "Guard on self.back_surface and self.fb as the method currently guards on main_surface and fb."
        - "Acquire the view: view = self.back_surface.get_view('0')."
        - "On exception, set a once-only flag, log at ERROR with exc_info, and fall back to the previous convert-and-bytes path for that frame."
        - "Compare len(view) against self.fb_size. On mismatch retain the existing DEBUG log and the truncate or pad behaviour, materialising bytes only on that path."
        - "On the matching path: self.fb.seek(0) then self.fb.write(view), for both the mmap and file branches."
        - "Remove flush(), sync() and os.fsync() from both branches."
        - "Retain the statistics update, the OSError handler with its errno 28 branch calling _attempt_framebuffer_recovery, and the general exception handler."
  dependencies:
    internal:
      - "RenderingEngineInterface (display/rendering/interfaces.py) — swap_buffers signature preserved."
      - "DisplayManager._display_loop — calls swap_buffers then write_to_framebuffer; unchanged."
    external:
      - "pygame — Surface.get_view('0') replaces get_buffer() plus bytes()."

error_handling:
  strategy: >
    Every new path degrades to the previous behaviour. A view that cannot
    be obtained falls back to the bytes path. A size mismatch retains its
    existing handling. No exception type is introduced.
  exceptions:
    - exception: "Exception"
      condition: "get_view('0') fails — for example a non-contiguous surface."
      handling: "Log once at ERROR with exc_info; use the convert-and-bytes path for that frame. Do not log per frame."
    - exception: "OSError"
      condition: "Write fails; errno 28 indicates no space left on device."
      handling: "Existing handler retained, including the _attempt_framebuffer_recovery call."
    - exception: "Exception"
      condition: "Any other write failure."
      handling: "Existing handler retained: increment framebuffer_errors, log at ERROR, return False."
  logging:
    level: "ERROR"
    format: "self.logger.error(f'...: {e}', exc_info=True)"

testing:
  unit_tests:
    - scenario: "Initialise and inspect back_surface."
      expected: "get_bytesize() == 4 and get_bitsize() == 32."
    - scenario: "Initialise and compare main_surface with back_surface."
      expected: "The same object."
    - scenario: "Call swap_buffers."
      expected: "Returns True; no pixel copy occurs."
    - scenario: "Draw a known pattern and write to a temporary file standing in for the device."
      expected: "The file holds exactly fb_size bytes matching the surface buffer."
    - scenario: "Count calls on a mock framebuffer during one write."
      expected: "One seek, one write, no flush, no sync, no fsync."
    - scenario: "Force get_view to raise, then write two frames."
      expected: "Both frames written via the fallback; exactly one ERROR logged."
    - scenario: "fb_size larger than the view length."
      expected: "Existing zero-pad behaviour preserved."
    - scenario: "fb_size smaller than the view length."
      expected: "Existing truncate behaviour preserved."
    - scenario: "OSError errno 28 during write."
      expected: "_attempt_framebuffer_recovery called; False returned."
  edge_cases:
    - "back_surface is None — guard returns False as the current main_surface guard does."
    - "self.fb is None because framebuffer initialisation failed — guard returns False."
    - "Mock rendering mode with pygame unavailable — initialize returns True early and creates no surface; write_to_framebuffer must not raise."
    - "A draw addressed to RenderTarget.MAIN_SURFACE — resolves to the aliased surface and is therefore visible, which is the intended behaviour."
  validation:
    - "grep confirms no flush, sync or fsync in write_to_framebuffer."
    - "The on-target panel shows correct colour in every mode."

deliverable:
  format_requirements:
    - "Edit src/gtach/display/rendering/engine.py in place. Create no new file."
    - "Make the four edits below and change nothing else."
  files:
    - path: "src/gtach/display/rendering/engine.py"
      content: |
        EDIT 1 — initialize (method begins engine.py:68)

        Replace these two lines (currently engine.py:103-104):

                    # Create surfaces
                    self.main_surface = pygame.Surface(surface_size)
                    self.back_surface = pygame.Surface(surface_size)

        with:

                    # Single surface at the framebuffer's own depth. Creating it
                    # at 32 bits removes the per-frame convert(32, 0) entirely:
                    # converting returns a NEW surface, so converting once and
                    # keeping the result would leave drawing going to the
                    # unconverted original (display review §5.1, recommendation 7).
                    self.back_surface = pygame.Surface(surface_size, 0, 32)

                    # main_surface is retained as an alias so RenderTarget.MAIN_SURFACE
                    # and get_surface() continue to resolve. There is no second
                    # buffer: nothing happens between composition and the write,
                    # so the intermediate copy had no purpose (recommendation 6).
                    self.main_surface = self.back_surface

                    self.logger.info(
                        f"Surface format: {self.back_surface.get_bitsize()}-bit, "
                        f"masks={self.back_surface.get_masks()}"
                    )

        EDIT 2 — swap_buffers (method begins engine.py:286)

        Replace the whole method with:

            def swap_buffers(self) -> bool:
                """No-op retained for interface compatibility.

                back_surface is written to the framebuffer directly, so there
                is no intermediate surface to swap into. The method is kept
                because it is declared on RenderingEngineInterface
                (interfaces.py:91) and called from
                DisplayManager._display_loop; removing it would be an
                interface change for no benefit (display review §5.1,
                recommendation 6).

                Returns:
                    True always.
                """
                return True

        EDIT 3 — write_to_framebuffer, buffer acquisition

        Replace the guard and the convert-and-materialise block (currently
        engine.py:314-333):

                        if not self.main_surface:
                            return False

                        if not self.fb:
                            return False

                        # Convert surface to proper format
                        converted_surface = self.main_surface.convert(32, 0)
                        buffer_data = converted_surface.get_buffer()

                        # Convert to bytes for writing
                        try:
                            buffer_bytes = bytes(buffer_data)
                        except (TypeError, ValueError):
                            try:
                                buffer_bytes = buffer_data.raw
                            except AttributeError:
                                buffer_bytes = buffer_data

                        actual_size = len(buffer_bytes)

        with:

                        if not self.back_surface:
                            return False

                        if not self.fb:
                            return False

                        # A buffer-protocol view over the surface's own memory.
                        # mmap.write and file.write both accept it, so the frame
                        # is not materialised into a bytes object first
                        # (recommendation 8).
                        payload = None
                        try:
                            payload = self.back_surface.get_view('0')
                        except Exception as e:
                            if not getattr(self, '_view_fallback_logged', False):
                                self._view_fallback_logged = True
                                self.logger.error(
                                    f"Surface view unavailable, falling back to a per-frame "
                                    f"copy: {e}", exc_info=True
                                )

                        if payload is None:
                            converted_surface = self.back_surface.convert(32, 0)
                            buffer_data = converted_surface.get_buffer()
                            try:
                                payload = bytes(buffer_data)
                            except (TypeError, ValueError):
                                try:
                                    payload = buffer_data.raw
                                except AttributeError:
                                    payload = buffer_data

                        actual_size = len(payload)

        Add the flag to __init__ alongside the other framebuffer state
        (near engine.py:47):

                self._view_fallback_logged = False

        EDIT 4 — write_to_framebuffer, mismatch handling and write

        Replace the mismatch block and both write branches (currently
        engine.py:335-356):

                        # Handle size mismatches
                        if actual_size != self.fb_size:
                            self.logger.debug(f"Buffer size mismatch: {actual_size} vs {self.fb_size}")
                            if actual_size > self.fb_size:
                                buffer_bytes = buffer_bytes[:self.fb_size]
                            elif actual_size < self.fb_size:
                                buffer_bytes = buffer_bytes + b'\x00' * (self.fb_size - actual_size)

                        # Write to framebuffer
                        if self.use_mmap:
                            self.fb.seek(0)
                            self.fb.write(buffer_bytes)
                            self.fb.flush()
                            try:
                                self.fb.sync()
                            except AttributeError:
                                os.fsync(self.fb_dev.fileno())
                        else:
                            self.fb.seek(0)
                            self.fb.write(buffer_bytes)
                            self.fb.flush()
                            os.fsync(self.fb.fileno())

        with:

                        # Size mismatch: materialise, then truncate or pad as
                        # before. Behaviour and log level are unchanged here —
                        # raising the level is recommendation 21 (task 7.3.3).
                        if actual_size != self.fb_size:
                            self.logger.debug(f"Buffer size mismatch: {actual_size} vs {self.fb_size}")
                            payload = bytes(payload)
                            if actual_size > self.fb_size:
                                payload = payload[:self.fb_size]
                            else:
                                payload = payload + b'\x00' * (self.fb_size - actual_size)

                        # Single write, no synchronisation. flush/sync/fsync give
                        # no correctness benefit on a framebuffer device and
                        # lengthen the window in which the scan-out can read a
                        # partially updated buffer (display review §4.1,
                        # recommendation 2).
                        self.fb.seek(0)
                        self.fb.write(payload)

        The mmap and file branches become identical, so the use_mmap
        conditional is no longer needed on the write path. Leave the
        use_mmap attribute itself in place — _initialize_framebuffer,
        _attempt_framebuffer_recovery and cleanup all still use it.

        Leave untouched: the statistics update that follows, the
        `except OSError` handler including its errno 28 branch, and the
        final `except Exception` handler.

success_criteria:
  - "python -m py_compile src/gtach/display/rendering/engine.py passes."
  - "pytest tests/ passes with no new failures."
  - "initialize creates exactly one pygame.Surface and it is 32-bit."
  - "main_surface is back_surface — `engine.main_surface is engine.back_surface` is True after initialisation."
  - "swap_buffers returns True and contains no blit call."
  - "write_to_framebuffer calls self.back_surface.get_view('0')."
  - "The strings 'flush()', '.sync()' and 'os.fsync' do not appear in write_to_framebuffer."
  - "write_to_framebuffer contains exactly one self.fb.write call on the matching path."
  - "The size-mismatch DEBUG log and the truncate/pad behaviour are still present."
  - "_attempt_framebuffer_recovery is still reachable from the errno 28 branch."
  - "__init__ defines self._view_fallback_logged."
  - "No file other than src/gtach/display/rendering/engine.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "engine"
        path: "src/gtach/display/rendering/engine.py"
      - name: "interfaces"
        path: "src/gtach/display/rendering/interfaces.py"
    classes:
      - name: "DisplayRenderingEngine"
        module: "gtach.display.rendering.engine"
      - name: "RenderingEngineInterface"
        module: "gtach.display.rendering.interfaces"
      - name: "RenderTarget"
        module: "gtach.display.rendering.interfaces"
    functions:
      - name: "initialize"
        module: "gtach.display.rendering.engine"
        signature: "initialize(self, surface_size: Tuple[int, int], framebuffer_path: str = '/dev/fb0') -> bool"
      - name: "swap_buffers"
        module: "gtach.display.rendering.engine"
        signature: "swap_buffers(self) -> bool"
      - name: "write_to_framebuffer"
        module: "gtach.display.rendering.engine"
        signature: "write_to_framebuffer(self) -> bool"
    constants:
      - name: "fb_size"
        module: "gtach.display.rendering.engine"
        type: "int"

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-66ef59a0-framebuffer-write-path.md
  and close the prompt when finished. Leave the issue and change active
  pending test results (ai/task.md §8.2.1).

  A rendering fault from this change is immediately visible on the panel —
  distorted colour, a skewed image or a blank display — so on-target
  confirmation is quick. Take it before proceeding to task 7.3.4.

  The framebuffer geometry was confirmed on target on 2026-07-30
  (ai/task.md §7.5.1): 32 bits per pixel, stride 1920, size 921,600,
  matching the engine's width x height x 4 assumption exactly. The
  size-mismatch path should therefore never be taken on this hardware; it
  is retained because the ENOSPC recovery logic indicates a mismatch has
  been encountered before.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-66ef59a0. |
| 1.1 | 2026-07-30 | Executed by Claude Code. All four edits applied and all twelve success criteria met, the pytest criterion now passing rather than vacuous. EDIT 3's `actual_size = len(payload)` required correction: pygame.BufferProxy has no `__len__`, so the literal text writes no frame at all — the size is taken from `.length`. EDIT 1's comment naming RenderTarget.MAIN_SURFACE was written as RenderTarget.MAIN, the actual enum member. Both recorded in change-66ef59a0. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/; the issue and change remain active pending on-target results per ai/task.md §8.2.1. |

---

Copyright (c) 2026 William Watson. MIT License.
