Created: 2026 July 30

# Display UI and Graphics Efficiency Review — GTach `src/gtach`

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Scope and Method](<#2.0 scope and method>)
[3.0 System Under Review](<#3.0 system under review>)
[4.0 Flicker Analysis](<#4.0 flicker analysis>)
[5.0 Rendering Efficiency](<#5.0 rendering efficiency>)
[6.0 Instrumentation Overhead](<#6.0 instrumentation overhead>)
[7.0 User Interface Findings](<#7.0 user interface findings>)
[8.0 Defects Identified](<#8.0 defects identified>)
[9.0 Recommendations](<#9.0 recommendations>)
[10.0 Verification Required](<#10.0 verification required>)
[Glossary](<#glossary>)
[References](<#references>)
[Version History](<#version history>)

---

## 1.0 Purpose

This document records a static code review of the GTach display subsystem. Two objectives were set: identify improvements to the user interface for a 480×480 circular panel, and identify causes of observed flicker in the RPM display together with graphics efficiency improvements.

No source changes were made. All findings are observations and proposals for collaborative decision.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Scope and Method

### 2.1 Files Examined

- `display/manager.py` — display loop, DIGITAL and RADIAL rendering, options, disconnected, acknowledgement screens
- `display/rendering/engine.py` — surface and framebuffer management
- `display/performance/monitor.py` — per-frame instrumentation
- `display/typography.py` — font cache, size and button constants
- `display/input/touch_coordinator.py` — touch region registry
- `display/models.py` — `RPMBands`, `DisplayConfig`
- `comm/obd.py`, `app.py` — RPM sample rate
- `docs/Debian_boot.txt.md`, `docs/HyperPixel_2"_Round.md`, `docs/pi-setup.md` — hardware configuration

Backup files (`manager_backup.py`, `setup_original_backup.py`) were excluded per standing convention.

### 2.2 Method

Findings were derived from code inspection. Quantitative claims (contrast ratios, pixel-write counts, physical dimensions, geometric error) were calculated rather than estimated; the arithmetic is stated inline so it can be checked.

### 2.3 Limitation

No measurements were taken on target hardware. Flicker causes are ranked by confidence, not by measured contribution. Section 10.0 lists the observations required to confirm the ranking.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 System Under Review

### 3.1 Hardware Path

| Item | Value | Source |
|---|---|---|
| Panel | HyperPixel 2.1 Round, 480×480, 60 Hz, 18-bit colour, 229 ppi | `docs/HyperPixel_2"_Round.md` |
| Driver path | Legacy DPI fbdev (`dtoverlay=hyperpixel2r:disable-touch`, `enable_dpi_lcd=1`) | `docs/Debian_boot.txt.md` |
| KMS | Explicitly not used | `docs/pi-setup.md:106` |
| Host | Raspberry Pi Zero 2W, runs as root under systemd | `docs/pi-setup.md:53` |

### 3.2 Software Path

`DisplayRenderingEngine.initialize()` sets `SDL_VIDEODRIVER=dummy` (`engine.py:92`), calls `pygame.display.init()` but never `set_mode()`, and creates two off-screen surfaces. Output reaches the panel by writing the whole surface to `/dev/fb0` each frame (`engine.py:300-364`).

Consequence: SDL is used only as a software rasteriser and font engine. No SDL presentation path, no page flip, no vertical-blank synchronisation.

### 3.3 Data Rate

| Item | Value | Source |
|---|---|---|
| OBD poll interval | 0.02 s (fast transports) or 0.05 s | `app.py:237` |
| Effective RPM sample rate | 20–50 Hz | derived |
| Frame target | 60 Hz (`fps_limit: 60`) | `config/config.yaml` |

The frame rate exceeds the data rate. Between one and three frames in every group of frames present identical data.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Flicker Analysis

Five mechanisms were identified. They are independent and may all be present.

### 4.1 Unsynchronised Framebuffer Writes — High Confidence

`write_to_framebuffer()` writes 921,600 bytes to `/dev/fb0` with no relationship to the panel scan-out position. The panel refreshes at 60 Hz; the write loop runs at an independent, jittering rate near 60 Hz. The beat between the two produces a tear seam that migrates vertically across the display — the characteristic appearance of which is a horizontal band of flicker rather than a static join.

Contributing detail: `engine.py:344-356` calls `flush()` followed by `sync()` or `os.fsync()` on every frame. On a framebuffer device these calls provide no correctness benefit and lengthen the write window, widening the interval during which the scan-out reads a partially updated buffer.

The legacy Pi fbdev driver supports `FBIO_WAITFORVSYNC` (0x4620) and `FBIOPAN_DISPLAY`. Neither is used. This is the single most likely cause of the reported symptom and the one whose fix is structural rather than cosmetic.

### 4.2 Band Colour Thrash in DIGITAL Mode — High Confidence

`_get_band_colour()` (`manager.py:540-579`) maps the RPM value to a full-screen background colour through hard thresholds with no hysteresis. `_draw_digital_mode()` then fills the entire viewport with that colour.

An engine holding steady near a threshold produces RPM samples that straddle it. At `torque_start = 3000`, samples alternating between 2998 and 3002 alternate the entire 480×480 background between pure blue and pure green at up to 50 Hz. Perceptually this is not a colour change but a full-field flash.

The same mechanism applies at every one of the five band boundaries.

### 4.3 Displayed Value Churn — High Confidence

`_draw_digital_mode()` formats the value as `f"{rpm/1000:.1f}"` (`manager.py:662`). Resolution of the displayed figure is therefore 100 RPM, while the source resolution is 0.25 RPM. Near a rounding boundary — for example 3049 to 3051 — the leading numeral, rendered at 180 px, alternates between `3.0` and `3.1` at the sample rate. There is no smoothing, deadband, or update-rate limit anywhere in the path.

### 4.4 Deliberate 2 Hz Flash — Confirmed by Design, Possible Misattribution

`_get_shift_cue()` (`manager.py:595`) derives a flash phase from `int(time.monotonic() * 2) % 2`, alternating the RADIAL centre disc between `(0,160,0)` and `(10,10,10)` above `caution_start`. This is intended behaviour. Two observations:

1. The phase is computed from wall-clock time and sampled at an irregular frame rate, so the on and off intervals are not equal in practice. The duty cycle appears unstable.
2. If the reported flicker occurs only above the caution threshold, this — not Section 4.1 — is the cause.

### 4.5 Frame-Time Jitter — Medium Confidence

The loop measures elapsed time and sleeps for the remainder of the 16.67 ms budget (`manager.py:436-441`). When a frame exceeds the budget the sleep is skipped, so frames are emitted at irregular intervals. Sections 5.0 and 6.0 establish that the per-frame cost is substantial for a Cortex-A53 executing Python. Irregular presentation interacts with Section 4.1 to make the tear seam move erratically instead of drifting smoothly.

An aggravating factor: at 60 Hz the display thread holds the GIL for a large fraction of each interval, which delays the OBD thread and makes the arrival of samples irregular as well.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Rendering Efficiency

### 5.1 Redundant Full-Frame Copies

Each frame performs, in order:

| Step | Location | Cost |
|---|---|---|
| `back_surface` → `main_surface` blit | `engine.py:293` | 921,600 B copy |
| `main_surface.convert(32, 0)` | `engine.py:321` | 921,600 B allocation and copy |
| `bytes(buffer_data)` | `engine.py:326` | 921,600 B copy |
| `fb.write(...)` | `engine.py:346` | 921,600 B copy |

Four full-frame traversals, one of which allocates a new surface every frame. Three are removable:

- `main_surface` serves no purpose, because the write to the framebuffer immediately follows the blit. A single surface suffices. If two are retained for another reason, exchange the references rather than copying the pixels.
- The `convert()` result should be produced once at initialisation, not per frame.
- `mmap.write()` and `file.write()` accept buffer-protocol objects; passing `surface.get_view('0')` avoids materialising a `bytes` object.

### 5.2 Overdraw

DIGITAL mode writes each pixel 2.58 times per frame:

```
480×480 clear        = 230,400
circle r=244         = 187,027   (π × 244²)
circle r=238         = 177,963   (π × 238²)
                     ---------
total                = 595,390 writes / 230,400 pixels = 2.58×
```

RADIAL mode is worse: the loop clears the back buffer (`manager.py:418`), then `_draw_radial_mode()` clears it again with `surface.fill((0,0,0))` (`manager.py:759`), then draws the r=244 border circle, then the r=232 background circle, then the full 300° headroom donut, then the 60° inert donut, then up to six coloured band donuts over the same area. Approximately 1.16 million pixel writes for a 230,400-pixel display, exceeding 5× overdraw.

### 5.3 Static Content Redrawn Every Frame

In RADIAL mode the following is invariant between frames: the black corners, the border ring, the r=232 background, the headroom arc, the inert bottom arc, the two zone boundary lines, the inner edge ring, seven tick marks, seven numerals rendered through `font.render`, six band boundary marks, and the `RPM × 1000` label. This is the majority of the drawing work, and it is repeated 60 times per second to produce an identical result.

Only three elements vary: the coloured fill arc, the white indicator line, and the centre disc with its label.

### 5.4 Uncached Text Rendering

Every `render_text()` call invokes `font.render(text, True, color)` (`engine.py:269`), which rasterises glyphs with anti-aliasing and allocates a surface. Fonts are cached by size (`typography.py:191`); rendered text surfaces are not cached anywhere.

Per frame this occurs 2 times in DIGITAL mode, 9 times in RADIAL mode, and 6 times in the options menu. The DIGITAL numeral is drawn at 180 px, the most expensive single rasterisation in the application.

The domain of the numeral is small and enumerable: 71 strings (`0.0` to `7.0`) against six text colours. A pre-rendered dictionary would eliminate the cost entirely for a memory outlay of a few hundred kilobytes.

### 5.5 Arc Tessellation

`draw_donut_arc()` uses a fixed `num_points = 60` regardless of the arc's angular extent (`manager.py:736`). A short 20° band segment therefore receives the same 122-vertex polygon as the 300° headroom arc.

The tessellation density is otherwise well chosen and should not be reduced for the long arcs: at r=232 with 5° segments the maximum chord deviation is 232 × (1 − cos 2.5°) = 0.22 px, below one pixel. Scaling the point count with the sweep angle — for example `max(4, int(sweep_deg / 2.5))` — preserves that accuracy while removing most of the vertex work.

### 5.6 Per-Frame Allocation and Import

- `import queue` executes inside the render function on every frame (`manager.py:621`, `manager.py:693`). The module cache makes this cheap but it is not free, and it belongs at module scope.
- `self.logger.debug(f'RPM {rpm:.0f} band colour bg={bg_colour}')` (`manager.py:649`) formats the f-string before the logging call, so the cost is incurred at 60 Hz even when DEBUG is disabled. The same pattern appears at `manager.py:882`.

### 5.7 Frame Rate Selection

A tachometer needle at 30 Hz is not distinguishable from one at 60 Hz at normal shift rates, and the data arrives at 20–50 Hz in any case. Halving the frame rate halves every cost in this section and returns GIL time to the OBD thread.

The stronger form is to render only when the displayed state changes: quantise the RPM to the displayed resolution and skip the frame entirely when the quantised value, band, and mode are unchanged. On a static screen — DISCONNECTED, OPTIONS, ACKNOWLEDGEMENT — this reduces the frame rate to zero.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Instrumentation Overhead

`PerformanceMonitor` is engaged on every frame and its cost is not trivial relative to the frame budget.

### 6.1 Per-Frame Costs

| Operation | Location | Note |
|---|---|---|
| `uuid.uuid4()` for the frame ID | `monitor.py:139` | String allocation per frame |
| Expiry scan of `_active_frames` | `monitor.py:145-150` | Full dictionary comprehension per frame |
| `get_current_metrics()` | `manager.py:446` | Called unconditionally, every frame |
| `psutil.Process().memory_info()` | `monitor.py:411` | Reads `/proc` per frame |

`get_current_metrics()` is invoked to test `metrics.total_frames % 600 == 0` — a value the monitor already holds. The gate should be inside the monitor, or the frame counter should be read directly.

### 6.2 Instrumentation Correctness Defect

`record_frame_end(frame_id)` is called *after* `time.sleep()` (`manager.py:442`). The recorded frame time therefore includes the idle padding and converges on the 16.67 ms target regardless of actual render cost. Two consequences:

1. Reported `frame_time_ms` and `fps` are meaningless as a measure of render load.
2. The dropped-frame test `frame_time > frame_time_target * 1.5` (`monitor.py:181`) can only fire when a frame overruns by more than 50%, and the recorded value it tests is the padded one.

This matters directly to the flicker investigation: the existing telemetry cannot be used to confirm or exclude Section 4.5. `record_frame_end()` must be called before the sleep.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 User Interface Findings

Physical scale for reference: at 229 ppi, 1 mm = 9.02 px.

### 7.1 Legibility — Blue Band Fails Contrast

`_get_band_colour()` pairs each band background with a text colour. Computed WCAG 2.1 contrast ratios:

| Band | Background | Text | Ratio | Assessment |
|---|---|---|---|---|
| Idle | `(0,0,0)` | white | 21.00:1 | Pass |
| Torque approach | `(0,0,255)` | black | **2.44:1** | **Fail** — below the 3:1 large-text minimum |
| Torque | `(0,255,0)` | black | 15.30:1 | Pass |
| Caution | `(255,255,0)` | black | 19.56:1 | Pass |
| Warning | `(255,128,0)` | black | 8.34:1 | Pass |
| Danger | `(255,0,0)` | black | 5.25:1 | Pass |

Pure blue has a relative luminance of 0.0722, close to black. Black text on it is effectively unreadable. White text on the same blue yields 8.59:1. This is a one-line correction with a large legibility return.

### 7.2 Full-Field Colour as the Primary Band Cue

Filling the whole viewport with the band colour is effective peripherally but has three costs: it drives the flicker in Section 4.2, it forces the text colour to change with the band, and at night a full-field yellow or white field at panel brightness is a glare source in the driver's forward field of view. The panel backlight cannot be switched off by software (`docs/HyperPixel_2"_Round.md`).

An annular band indicator — the value on a fixed dark ground, the band expressed in a ring — preserves the peripheral cue, removes the text-contrast coupling, and reduces emitted light. It also makes DIGITAL and RADIAL visually consistent.

### 7.3 Touch Target Dimensions

| Element | Size (px) | Height (mm) | Location |
|---|---|---|---|
| Options menu buttons | 300 × 55 | 6.10 | `manager.py:911-921` |
| Options button separation | 10 | 1.11 | derived from y values |
| Disconnected buttons | 240 × 70 | 7.76 | `manager.py:1345-1346` |
| Update view buttons | 280 × 60 | 6.65 | `manager.py:974-975` |
| `BUTTON_FLOATING` constant | 44 × 44 | 4.88 | `typography.py` |

Common guidance for a device operated by hand places the minimum comfortable target at roughly 9 mm (81 px here), and higher again where the operator is subject to vehicle motion. All four measured elements fall below that figure; the 44 px constant is at less than half.

The 10 px separation between the four options buttons is the more serious of the two problems. A 1.1 mm gap between adjacent 6.1 mm targets makes an adjacent-item mis-tap likely, and two of the four adjacent items — *Clear settings* and *Simulation mode* — are not equivalent in consequence.

Proposal: no more than three targets per screen, target height ≥ 72 px (8 mm), separation ≥ 16 px, and confirmation on *Clear settings*.

### 7.4 Declared Design System Not Applied

`TypographyConstants` declares `BUTTON_CORNER_RADIUS = 6`, `BUTTON_BORDER_WIDTH = 2`, `BUTTON_TOUCH_EXPANSION = 8`, `BUTTON_PRESS_SCALE = 0.95`, and five named button sizes. `DisplayManager` uses none of them: it calls `draw_rect` without a `border_radius` argument and hard-codes button geometry at each site. `TouchEventCoordinator.register_button_region()` takes the drawn rectangle unmodified, so the declared 8 px touch expansion is not applied either.

The result is square-cornered rectangles on a circular panel, geometry duplicated at five call sites, and no visual press feedback anywhere in the main UI.

### 7.5 Centre of the RADIAL Display Carries No Information

The centre disc (r=99, 30,800 px — 13% of the viewport, and the region of highest visual acuity for a centred gaze) displays the fixed string `GTach` (`manager.py:878`). The numeric RPM is not shown in RADIAL mode at all.

`TypographyConstants.FONT_RPM_MEDIUM = 28` is annotated "Gauge mode center readout", which suggests this was the original intent. Placing the numeral in the centre would make RADIAL a superset of DIGITAL and remove the need to treat them as alternative modes.

### 7.6 Mode Change Has No Visible Affordance

DIGITAL and RADIAL are reachable only by horizontal swipe (`manager.py:142-172`). Nothing on either screen indicates that a second mode exists or that swiping does anything. `_render_mode_selector()` (`manager.py:1091`) draws exactly such a control but is never called from any code path.

Two viable resolutions: adopt Section 7.5 and retire the mode distinction, or add a minimal persistent indicator — two small dots below the centre — which both signals the alternative and shows the current position.

### 7.7 Options Screen Uses a Rectangular Layout

Four 300 px full-width bars stacked vertically on a circular panel leave the four corner regions unusable and read as a rectangular dialogue that has been cropped. The circular form is the display's distinguishing property; a layout that ignores it is a missed opportunity as well as inefficient use of area.

### 7.8 Update View Has No Progress Feedback

`_draw_update_view()` renders the string `Checking…` while a worker thread performs the check (`manager.py:958`). `self._update_wheel` is set to `None` and never used as a spinner despite the field name. A network check has indeterminate duration; a static string is indistinguishable from a hung application.

### 7.9 No Day/Night Provision

The palette is fixed at full saturation. At night this is a bright light source directly in the driver's field of view. Whether to address this is a scope decision, not a defect.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Defects Identified

These are behavioural faults, distinct from the efficiency and design observations above.

### 8.1 Connection Status Indicator Is Outside the Visible Area

`_draw_status_indicator()` draws a 5 px radius dot at (20, 20) (`manager.py:1445-1446`). Distance from the display centre:

```
√((240−20)² + (240−20)²) = √(220² + 220²) = 311 px
```

The circular viewport radius is 238 px. The indicator is 73 px outside it and cannot be seen on the panel. It is drawn on every frame in every normal mode.

This is a straightforward consequence of a coordinate chosen for a rectangular display. Suggested relocation: inside the inert bottom arc near (240, 300), or top-centre near (240, 60).

### 8.2 Touch Regions Rebuilt Every Frame — Race Window

`_draw_options_menu()`, `_draw_update_view()`, `_render_disconnected()`, and `_draw_acknowledgement_mode()` each begin with `self.touch_coordinator.clear_regions()` and then re-register their regions (`manager.py:899`, `949`, `1312`, `1222`).

Touch events are delivered on a separate thread through `TouchHandler._handle_touch_event` (`touch.py:83`). `TouchEventCoordinator` guards `_regions` with an `RLock`, so the dictionary cannot be corrupted — but a touch acquiring the lock between the clear and the re-registration observes an empty or partial region set and is discarded. The window recurs 60 times per second.

Registration belongs at mode entry, not in the render path.

### 8.3 Framebuffer Geometry Is Assumed Rather Than Queried

`_initialize_framebuffer()` computes `fb_size = width × height × 4` (`engine.py:121`), assuming 32 bits per pixel and a stride equal to the width. Neither is queried. `docs/Debian_boot.txt.md` sets `dpi_output_format=0x7f216` (an 18-bit 6:6:6 panel format) and does not set `framebuffer_depth`.

If the actual depth or `line_length` differs from the assumption, the mismatch is handled by truncating or zero-padding the buffer (`engine.py:336-341`) and logging at DEBUG level. Truncation or a stride mismatch would produce a skewed or partially blank image, not a clean failure.

`FBIOGET_VSCREENINFO` and `FBIOGET_FSCREENINFO` return the authoritative `bits_per_pixel`, `xres_virtual`, and `line_length`. `utils/terminal.py:50` already demonstrates the ioctl call pattern.

The presence of dedicated `ENOSPC` recovery logic (`engine.py:368-370`) suggests a size mismatch has been encountered on hardware at some point. This warrants confirmation on the target before any other framebuffer change is made.

### 8.4 Event Handling Is Inert

The loop polls the SDL event queue and handles `pygame.QUIT` (`manager.py:404-410`), but `SDL_VIDEODRIVER=dummy` is set and `set_mode()` is never called. No window exists, so no window events are generated. The poll loop and the QUIT path are dead in production. Harmless, but misleading to a future reader.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Recommendations

Ordered by expected benefit relative to implementation risk. Each is independent unless stated.

### 9.1 Priority 1 — Flicker

| # | Action | Addresses | Risk |
|---|---|---|---|
| 1 | Apply exponential smoothing and threshold hysteresis to the RPM value before display. Suggested: EMA with τ ≈ 150 ms for the displayed figure, and ±75 RPM hysteresis on band transitions. | 4.2, 4.3 | Low — confined to `manager.py` |
| 2 | Remove `flush()`, `sync()`, and `os.fsync()` from the per-frame framebuffer write. | 4.1, 5.1 | Low |
| 3 | Issue `FBIO_WAITFORVSYNC` (0x4620) before each framebuffer write. | 4.1 | Low — degrade gracefully if `EINVAL` |
| 4 | Adopt true page flipping: double `yres_virtual` via `FBIOPUT_VSCREENINFO`, mmap both frames, write to the off-screen half, then `FBIOPAN_DISPLAY`. | 4.1 | Medium — depends on 8.3 being resolved first |
| 5 | Derive the shift-cue flash phase from a monotonic frame counter rather than wall-clock time, so the duty cycle is stable. | 4.4 | Low |

Item 1 should be implemented and observed first. It is the cheapest change, and if the flicker is band thrash rather than tearing it resolves the symptom without touching the framebuffer path.

### 9.2 Priority 2 — Rendering Efficiency

| # | Action | Addresses | Risk |
|---|---|---|---|
| 6 | Remove `main_surface`; write `back_surface` to the framebuffer directly. | 5.1 | Low |
| 7 | Perform `convert()` once at initialisation; retain the converted surface. | 5.1 | Low |
| 8 | Write `surface.get_view('0')` to the framebuffer instead of `bytes(buffer)`. | 5.1 | Low |
| 9 | Pre-render the RADIAL static layer once into a cached surface; blit it per frame and draw only the fill arc, indicator, and centre on top. | 5.3, 5.2 | Medium — largest single render saving |
| 10 | Cache rendered text surfaces keyed by `(text, size, colour)`. Pre-render the 71 DIGITAL numerals. | 5.4 | Low |
| 11 | Scale `num_points` in `draw_donut_arc` with the sweep angle. | 5.5 | Low |
| 12 | Reduce `fps_limit` to 30. | 5.7, 4.5 | Low — configuration only |
| 13 | Skip the frame when the quantised RPM, band, and mode are all unchanged. | 5.7 | Medium — must not suppress the intentional flash |
| 14 | Move `import queue` to module scope; guard the two per-frame debug f-strings with `logger.isEnabledFor(DEBUG)`. | 5.6 | Low |

Items 12 and 13 interact with item 5: the flash requires frames even when the RPM is static.

### 9.3 Priority 3 — Instrumentation

| # | Action | Addresses | Risk |
|---|---|---|---|
| 15 | Call `record_frame_end()` before the pacing sleep. | 6.2 | Low — prerequisite for measuring anything |
| 16 | Replace the per-frame `get_current_metrics()` call with a counter test inside the monitor. | 6.1 | Low |
| 17 | Replace the UUID frame ID with a monotonic integer. | 6.1 | Low |
| 18 | Sample `psutil` memory at 1 Hz, not per frame. | 6.1 | Low |

### 9.4 Priority 4 — Defects

| # | Action | Addresses | Risk |
|---|---|---|---|
| 19 | Relocate the status indicator inside the circular viewport. | 8.1 | Low |
| 20 | Register touch regions on mode entry rather than per frame. | 8.2 | Medium — requires a mode-transition hook |
| 21 | Query framebuffer geometry via ioctl; log a mismatch at ERROR, not DEBUG. | 8.3 | Low |
| 22 | Remove or document the inert event-poll block. | 8.4 | Low |

### 9.5 Priority 5 — User Interface

| #   | Action                                                                                                                                                                  | Addresses | Risk                                  |
| --- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------------------------------------- |
| 23  | Change the blue band's text colour to white.                                                                                                                            | 7.1       | Low — one line, large return          |
| 24  | Increase options button height to ≥ 72 px and separation to ≥ 16 px; reduce to three items per screen; add confirmation to *Clear settings*.                            | 7.3       | Low                                   |
| 25  | Place the numeric RPM in the RADIAL centre disc; consider retiring DIGITAL as a separate mode.                                                                          | 7.5, 7.6  | Medium — a design decision, not a fix |
| 26  | Replace the full-field band colour with an annular band indicator on a fixed dark ground.                                                                               | 7.2, 4.2  | Medium — a design decision            |
| 27  | Route all button drawing through a single helper that applies the declared `TypographyConstants` values, including corner radius, touch expansion, and a pressed state. | 7.4       | Medium                                |
| 28  | Add an animated indicator to the update-check view.                                                                                                                     | 7.8       | Low                                   |
| 29  | Consider a dimmed night palette.                                                                                                                                        | 7.9       | Scope decision                        |

Items 25 and 26 change the product's appearance and behaviour. They are proposals for discussion, not corrections.

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Verification Required

The ranking in Section 4.0 rests on inference. The following observations on target hardware would confirm or refute it. All are non-invasive.

### 10.1 Framebuffer Geometry

```bash
# On gtach.local
cat /sys/class/graphics/fb0/bits_per_pixel
cat /sys/class/graphics/fb0/stride
cat /sys/class/graphics/fb0/virtual_size
fbset -i
```

If `bits_per_pixel` is not 32, or `stride` is not 1920, Section 8.3 is an active fault and takes priority over everything else.

### 10.2 Actual Render Cost

Apply recommendation 15 first, then read `frame_time_ms` from the existing periodic log line. Until that change is made, the logged figure does not measure render time.

### 10.3 Flicker Characterisation

Three observations discriminate between the candidate causes:

| Observation | Indicates |
|---|---|
| Flicker is a horizontal band that moves vertically | Tearing — Section 4.1 |
| Flicker is a full-field colour alternation, and occurs only when the RPM is near a band threshold | Band thrash — Section 4.2 |
| Flicker occurs only above `caution_start = 4500` | Intentional flash — Section 4.4 |
| The last digit of the DIGITAL readout alternates while the engine is steady | Value churn — Section 4.3 |

Whether the symptom appears in RADIAL, in DIGITAL, or in both is itself discriminating: Sections 4.2 and 4.3 apply to DIGITAL only, while Section 4.1 applies to every mode including the static screens.

### 10.4 Simulation-Mode Control

Simulation mode drives the RPM from `3000 + 3000·sin(t)` (`manager.py:617`), which sweeps through every band boundary once per 6.28 s. If flicker in simulation mode occurs in bursts synchronised with those crossings, Section 4.2 is confirmed. If it is continuous, Section 4.1 is the more likely cause.

This is the single most informative test available and requires no code change.

[Return to Table of Contents](<#table of contents>)

---

## Glossary

**Damage tracking** — Recording which screen regions changed so that only those are redrawn or transmitted.

**Deadband** — A range of input change that produces no output change, used to suppress oscillation about a threshold.

**EMA** — Exponential moving average. A first-order low-pass filter, `y[n] = αx[n] + (1−α)y[n−1]`.

**Hysteresis** — Making a threshold's position depend on the direction of approach, so that a signal must move past it by a margin before the state changes back.

**Overdraw** — Writing the same pixel more than once while composing a single frame.

**Page flip** — Presenting a completed frame by changing the address the display controller scans from, rather than by overwriting the pixels being scanned.

**Stride / line_length** — Bytes between the start of one framebuffer row and the next. May exceed width × bytes-per-pixel due to alignment padding.

**Tearing** — A visible seam caused by updating a framebuffer while the display controller is reading it, so that one presented frame contains parts of two rendered frames.

**Vertical blank (vblank)** — The interval between the end of one scan-out and the start of the next, during which a framebuffer may be replaced without producing a seam.

[Return to Table of Contents](<#table of contents>)

---

## References

PIMORONI LTD. *HyperPixel 2.1" Round*. [online]. [Accessed 30 July 2026]. Available from: https://shop.pimoroni.com/products/hyperpixel-round

WORLD WIDE WEB CONSORTIUM. *Web Content Accessibility Guidelines (WCAG) 2.1 — Success Criterion 1.4.3 Contrast (Minimum)*. W3C Recommendation, 5 June 2018. [online]. [Accessed 30 July 2026]. Available from: https://www.w3.org/TR/WCAG21/

Contrast ratios in Section 7.1 were computed from the WCAG 2.1 relative-luminance definition. Physical dimensions were derived from the 229 ppi figure in the Pimoroni specification. Framebuffer ioctl constants correspond to the Linux `linux/fb.h` definitions.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026 July 30 | Initial review of `src/gtach` display subsystem: flicker analysis, rendering efficiency, UI findings, and recommendations. |

[Return to Table of Contents](<#table of contents>)

---

Copyright (c) 2026 William Watson. MIT License.
