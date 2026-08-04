Created: 2026 August 04

# Prompt: Draw the Gauge Face Once, Cache the Glyphs, Tessellate to the Arc

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-821919ce"
  task_type: "implementation"
  source_ref: "change-821919ce"
  target_profile: "claude_code"
  date: "2026-08-04"
  iteration: 1
  coupled_docs:
    change_ref: "change-821919ce"
    change_iteration: 1

context:
  purpose: >
    Twenty-seven of the thirty-one primitives in a RADIAL frame, and
    eight of its nine text rasterisations, produce an identical result
    sixty times a second. Every donut arc is built as a 122-vertex
    polygon whether it spans 20 degrees or 300.
  integration: >
    Two files: src/gtach/display/manager.py and
    src/gtach/display/rendering/engine.py. Executor is Claude Code; AEL
    is not used.

    GATE — DO NOT SKIP. ai/task.md §8.1 records that this triple depends
    on the §7.5.3 frame_time_ms baseline, which is collected in the §8.4
    observation session and has NOT been taken. The documents were
    authored ahead of it by instruction; the code must not be. Before
    implementing, confirm the baseline exists and that RADIAL render
    cost is a material fraction of the 16.67 ms budget. If it is not,
    STOP and report — this change carries medium risk for a benefit that
    would not exist.

    THREE INDEPENDENT PARTS. Land them as three commits in the order
    given: tessellation, text cache, static layer. Only the third
    carries the assumptions.

    CORRECTNESS BAR. This change must be invisible. A rendered frame
    must be pixel-identical to the pre-change implementation at matched
    inputs. Anything else is a defect in this change, not an
    improvement.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/display/manager.py and src/gtach/display/rendering/engine.py."
    - "Do NOT provide an invalidate() method for the static layer. Invalidation is by key comparison only — a caller that must remember to invalidate is a defect waiting to be filed (cross-check D3 §7.4 step 3)."
    - "Do NOT omit the palette or active-band members from the key, even though neither varies yet. They are there so change-5014040c and change-5012004e extend the key's VALUES and not its STRUCTURE."
    - "Do NOT make the text cache unbounded. An unbounded memo on a long-running embedded process is a leak."
    - "Do NOT change fps_limit or add frame skipping. That is task 7.3.6."
    - "Do NOT touch the framebuffer write path in engine.py. Changes 66ef59a0 and 49b21ace own it."
    - "Do NOT draw the fill arc, the indicator line, the centre disc or the centre readout into the cached layer. They vary per frame."
    - "Do NOT reduce tessellation density on the long arcs. The 2.5-degree segment figure preserves sub-pixel accuracy and must be kept."
    - "Type hints preserved; Google-style docstrings; PEP 8."

specification:
  description: >
    Scale draw_donut_arc's vertex count with sweep. Memoise rendered
    text surfaces in the rendering engine. Pre-render the RADIAL
    invariant layer into a keyed cached surface and blit it per frame.
  requirements:
    functional:
      - "draw_donut_arc uses max(4, int(abs(sweep_deg) / 2.5)) points."
      - "Chord deviation at r=232 remains below 1 px for every sweep drawn."
      - "render_text returns a cached surface for a repeated (text, font, colour)."
      - "The text cache is bounded with a defined eviction policy."
      - "_draw_radial_mode blits a cached static layer and draws only the fill arc, indicator, centre disc and readout on top."
      - "The static layer is rebuilt when its key changes and at no other time."
      - "The key includes viewport geometry, the six RPMBands thresholds, the palette identity and the active band index."
      - "A rendered frame is pixel-identical to the pre-change implementation at matched inputs."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "Frame time reduced against the §7.5.3 baseline. Primitives per frame 31 -> 5; text rasterisations 9 -> 0 in the steady state; 20-degree arc vertices 122 -> 8"
      metric: "time"
    - target: "One additional 921,600-byte surface. Total surface memory approximately 2.7 MB"
      metric: "memory"

design:
  architecture: >
    Work whose inputs have not changed is not repeated. The inputs are
    named in a tuple and compared; nothing has to remember to invalidate
    anything. Two later changes will alter what those inputs are worth
    without altering what they are.
  components:
    - name: "DisplayManager._radial_layer_key"
      type: "function"
      purpose: "Name everything the invariant layer depends on."
      interface:
        outputs:
          type: "tuple"
          description: "Compared by equality; any difference forces a rebuild."
      logic:
        - "Return (outer_radius, inner_radius, centre, thresholds tuple, palette identity, active band index)."
        - "outer_radius, inner_radius and centre are the constants at manager.py:818-821. They are fixed today; they are in the key because they are what the layer is drawn against, and a future viewport change must not silently reuse a stale surface."
        - "thresholds: the six RPMBands fields, which drive the tick and boundary-mark positions."
        - "palette identity: getattr(self, '_palette', None) and its .name if present, else a constant. change-5012004e supplies it; this must not fail before then."
        - "active band index: self._active_band, which _get_band_colour maintains (manager.py:670)."
    - name: "DisplayManager._build_radial_static_layer"
      type: "function"
      purpose: "Draw the twenty-seven invariant primitives onto a fresh surface."
      interface:
        outputs:
          type: "pygame.Surface"
      logic:
        - "Create a surface of the display size."
        - "Draw, in the existing order: the corner fill, the border ring, the r=232 ground, the headroom arc, the inert arc, the zone boundary lines, the inner edge ring, the seven tick marks, the seven numerals, the six band boundary marks and the 'RPM x 1000' label."
        - "Draw NOTHING that depends on the current RPM."
    - name: "DisplayManager._draw_radial_mode"
      type: "function"
      purpose: "Blit the layer, then draw what varies."
      logic:
        - "Drain the queue and condition the RPM exactly as today."
        - "Compute the key; rebuild if it differs; blit."
        - "Draw the fill arc, the indicator line, the centre disc and the centre readout."
    - name: "DisplayRenderingEngine.render_text"
      type: "function"
      purpose: "Rasterise once per distinct input."
      logic:
        - "Key on (text, id(font), colour). pygame Font objects are not hashable by value; FontManager caches them by size (typography.py:191) so identity is stable for the process. This is deliberate — do not attempt to hash the font itself."
        - "Bounded dict; evict oldest on overflow."
  dependencies:
    internal:
      - "change-0b00759c — shipped. Supplies the frame_time_ms this change is judged by."
      - "_get_band_colour — maintains self._active_band, a key member."
      - "_get_shift_cue — supplies the centre disc's colour. Unmodified; the disc is drawn on top of the layer."
    external:
      - "pygame.Surface.blit and pygame.Surface.copy."

error_handling:
  strategy: >
    A cache failure must degrade to the current behaviour, not to a
    blank screen. If the layer cannot be built, draw the frame the old
    way and log it — a slow gauge is better than no gauge on a vehicle.
  exceptions:
    - exception: "Exception"
      condition: "_build_radial_static_layer fails."
      handling: "Log at ERROR with a traceback, set the cached layer to None, and fall through to drawing every primitive directly for that frame. The next frame retries."
    - exception: "Exception"
      condition: "render_text's cache lookup or insertion fails."
      handling: "Fall back to calling font.render directly. The cache is an optimisation and must never be the reason text does not appear."
    - exception: "Exception"
      condition: "Anything else in _draw_radial_mode."
      handling: "Existing handler at manager.py:989-990. Unchanged."
  logging:
    level: "ERROR on a build failure; DEBUG on a rebuild, so the rebuild frequency is observable"
    format: "self.logger.debug(f'Radial static layer rebuilt, key={key}')"

testing:
  unit_tests:
    - scenario: "A RADIAL frame at RPM 3000, rendered by the pre-change and post-change implementations."
      expected: "Pixel-identical. Compare surface buffers directly."
    - scenario: "The same across RPM 0, 999, 1000, 3000, 4500, 5500, 5800, 7000."
      expected: "Pixel-identical at every value."
    - scenario: "Two consecutive frames at the same RPM."
      expected: "_build_radial_static_layer called exactly once."
    - scenario: "Sixty frames at varying RPM within one band."
      expected: "Built once."
    - scenario: "A frame after self.config.rpm_bands is replaced."
      expected: "Rebuilt."
    - scenario: "A frame after self._active_band changes."
      expected: "Rebuilt."
    - scenario: "A frame after a simulated palette change — set a _palette attribute with a different name."
      expected: "Rebuilt. This asserts the key member responds before change-5012004e exists."
    - scenario: "_radial_layer_key with no _palette attribute present."
      expected: "Does not raise; returns a stable value."
    - scenario: "_build_radial_static_layer forced to raise."
      expected: "The frame still renders, by the direct path; an ERROR is logged."
    - scenario: "render_text with the same arguments twice."
      expected: "font.render called once."
    - scenario: "render_text with the same string in two colours."
      expected: "font.render called twice; two distinct surfaces."
    - scenario: "render_text with 500 distinct strings against a cache bounded at 256."
      expected: "Size stays at or below the bound; the earliest entries are evicted."
    - scenario: "render_text when the cache raises internally, forced."
      expected: "Text still renders via the direct path."
    - scenario: "draw_donut_arc with sweeps of 300, 60, 20 and 0.5 degrees."
      expected: "120, 24, 8 and the floor of 4 points."
    - scenario: "Chord deviation computed at r=232 for each of those point counts."
      expected: "< 1 px in every case."
    - scenario: "Arc pixels before and after Part 3, at each band."
      expected: "Identical except for sub-pixel edge antialiasing; assert a bounded per-pixel difference rather than exact equality."
    - scenario: "Ten thousand frames with varying RPM."
      expected: "Surface count and memory stable; no growth in the cache beyond its bound."
  edge_cases:
    - "The first frame after startup: no cached layer exists, so the key comparison misses and the layer is built. Assert this rather than assuming the initial value compares unequal."
    - "self._active_band before _get_band_colour has ever run — it is initialised in __init__; confirm it exists before the key reads it."
    - "A key member that is an unhashable type would break a dict-based cache but not tuple equality. The cache here is a single surface plus its key, compared by ==, so unhashable members are safe. Do not convert it to a dict keyed by the tuple without checking that."
    - "Two fonts of the same size obtained from FontManager: id() is stable because the manager caches by size, but a font obtained by any other route would have a different id and cache separately. Correct, if slightly wasteful; note it."
    - "The centre readout string domain is 71 values ('0.0' to '7.0'), so the cache reaches a steady state within seconds. No eager pre-render is required."
  validation:
    - "grep confirms no invalidate() method exists for the static layer."
    - "grep confirms the fill arc, indicator, centre disc and readout are not drawn inside _build_radial_static_layer."
    - "git diff confirms the framebuffer write path in engine.py is unmodified."

deliverable:
  format_requirements:
    - "Edit the two files in place. Create no new file."
    - "Three commits, in the order given, so any part can be reverted alone."
  files:
    - path: "src/gtach/display/manager.py"
      content: |
        PART 3 FIRST — the tessellation. Smallest, independent, lowest
        risk.

        In draw_donut_arc (manager.py:839-860), replace:

                num_points = 60

        with:

                # Scale the vertex count with the arc's extent. A fixed
                # 60 gave a 20-degree band segment the same 122-vertex
                # polygon as the 300-degree headroom arc. At r=232 a
                # 2.5-degree segment deviates from the true arc by
                # 232 * (1 - cos 1.25 deg) = 0.055 px, so accuracy is
                # preserved on the long arcs (display review §5.5,
                # recommendation 11).
                sweep_deg = abs(math.degrees(end_angle_rad - start_angle_rad))
                num_points = max(4, int(sweep_deg / 2.5))

        Change nothing else in the function.

        PART 1 LAST — the keyed static layer.

        (a) In __init__, add:

                self._radial_static_layer = None
                self._radial_layer_cached_key = None

        (b) _radial_layer_key:

            def _radial_layer_key(self) -> tuple:
                """Everything the invariant gauge layer depends on.

                Compared by equality on every frame; any difference
                rebuilds the layer. The palette and active-band members
                do not vary yet — change-5012004e and change-5014040c
                supply them — and are present so those changes extend
                this key's values rather than its structure
                (cross-check D3 §7.4 steps 1 and 2).
                """
                bands = self.config.rpm_bands
                palette = getattr(self, '_palette', None)
                return (
                    232, 100, (240, 240),
                    (bands.idle_max, bands.torque_start,
                     bands.caution_start, bands.warning_start,
                     bands.danger_start, bands.redline_rpm),
                    getattr(palette, 'name', 'fixed'),
                    getattr(self, '_active_band', 0),
                )

        (c) _build_radial_static_layer: create a surface of the display
        size and draw, in the existing order and with the existing
        code, everything from the corner fill at manager.py:864 through
        the 'RPM x 1000' label at 969-972, OMITTING:

              - the coloured fill arc loop (manager.py:891-896)
              - the white indicator line (956-964)
              - the centre disc (974-977)
              - the centre readout (979-985)

        Note that _draw_shift_border (manager.py:866) draws the border
        ring in the shift-cue colour, which VARIES with RPM. It must
        NOT go into the static layer. Draw it per frame with the other
        varying primitives. The report's §5.3 list says "the border
        ring" is invariant; it is not, and that is a correction to the
        report worth making in a comment.

        (d) _draw_radial_mode becomes:

              - drain the queue and condition the RPM, unchanged;
              - clamp, unchanged;
              - get the surface, unchanged;
              - key = self._radial_layer_key(); rebuild if it differs;
              - blit the layer at (0, 0);
              - draw _draw_shift_border in the shift-cue colour;
              - draw the fill arc loop;
              - draw the indicator line;
              - draw the centre disc and readout.

        Wrap the build in try/except: on failure log at ERROR, set the
        layer to None, and draw every primitive directly for that
        frame.
    - path: "src/gtach/display/rendering/engine.py"
      content: |
        PART 2 — the text surface cache.

        In __init__, add:

            # Rendered text surfaces, keyed by (text, id(font), colour).
            # Fonts are cached by size in typography.py:191; rendered
            # surfaces were not cached anywhere, so every call
            # rasterised glyphs afresh — nine times per RADIAL frame,
            # eight of them for strings that never change
            # (display review §5.4, recommendation 10).
            self._text_cache = {}
            self._text_cache_order = []
            self._text_cache_limit = 256

        In render_text, around the font.render call at engine.py:269:

            key = (text, id(font), tuple(color))
            surface = self._text_cache.get(key)
            if surface is None:
                surface = font.render(text, True, color)
                self._text_cache[key] = surface
                self._text_cache_order.append(key)
                if len(self._text_cache_order) > self._text_cache_limit:
                    oldest = self._text_cache_order.pop(0)
                    self._text_cache.pop(oldest, None)

        Wrap the whole cache interaction so a failure falls back to
        font.render directly — text must appear even if the cache does
        not work.

        id(font) rather than font: pygame Font objects are not hashable
        by value. FontManager caches by size so the identity is stable
        for the process lifetime. Record this in a comment; it is the
        kind of thing that looks like a bug to the next reader.

        Do not touch anything else in this file. In particular the
        framebuffer write path, which changes 66ef59a0 and 49b21ace
        own, is out of scope.

success_criteria:
  - "python -m py_compile src/gtach/display/manager.py src/gtach/display/rendering/engine.py passes."
  - "pytest tests/ passes with no new failures."
  - "A rendered RADIAL frame is pixel-identical to the pre-change implementation at every tested RPM."
  - "_build_radial_static_layer is called once across consecutive frames at an unchanged key."
  - "The key includes viewport geometry, the six thresholds, the palette identity and the active band index."
  - "No invalidate() method exists for the static layer."
  - "_draw_shift_border is drawn per frame and is NOT in the static layer."
  - "The fill arc, indicator line, centre disc and readout are not in the static layer."
  - "render_text calls font.render once per distinct (text, font, colour)."
  - "The text cache does not exceed its bound under 500 distinct strings."
  - "A forced failure in either cache still renders the frame."
  - "draw_donut_arc yields 120, 24 and 8 points for 300, 60 and 20 degree sweeps."
  - "The framebuffer write path in engine.py is byte-identical to its current text."
  - "No file other than the two named above is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "manager"
        path: "src/gtach/display/manager.py"
      - name: "engine"
        path: "src/gtach/display/rendering/engine.py"
    classes:
      - name: "DisplayManager"
        module: "gtach.display.manager"
      - name: "DisplayRenderingEngine"
        module: "gtach.display.rendering.engine"
    functions:
      - name: "_radial_layer_key"
        module: "gtach.display.manager"
        signature: "_radial_layer_key(self) -> tuple"
      - name: "_build_radial_static_layer"
        module: "gtach.display.manager"
        signature: "_build_radial_static_layer(self) -> Optional[pygame.Surface]"
      - name: "_draw_radial_mode"
        module: "gtach.display.manager"
        signature: "_draw_radial_mode(self) -> None"
      - name: "draw_donut_arc"
        module: "gtach.display.manager"
        signature: "draw_donut_arc(color, start_angle_rad, end_angle_rad)"
      - name: "render_text"
        module: "gtach.display.rendering.engine"
        signature: "render_text(self, target, text, font, color, position, center=False)"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-821919ce-render-caching.md
  and close the prompt T-Doc when finished. Leave the issue and change
  T-Docs active pending test results (ai/task.md §8.2.1).

  CHECK THE GATE FIRST. The §7.5.3 baseline must exist and must show
  render cost to be material. This prompt was authored ahead of that
  measurement by instruction; executing it ahead of the measurement is
  the case ai/task.md §8.1 warns against.

  Two things in this task will look right and be wrong. The first is
  putting _draw_shift_border into the static layer — the report's §5.3
  lists the border ring as invariant and it is not, because its colour
  comes from _get_shift_cue. The second is a key that omits the palette
  and band members because neither varies yet; the whole purpose of the
  keyed design is that the two later changes extend the key's values
  and not its shape.

  The pixel-identity requirement is the real acceptance test. A caching
  refactor that changes the output has not optimised the renderer, it
  has replaced it.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-04 | Initial prompt document coupled to change-821919ce. |

---

Copyright (c) 2026 William Watson. MIT License.
