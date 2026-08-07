Created: 2026 August 04

# Issue: The Band Is Expressed as a Bright Field Rather Than a Ring, and the Gauge Ground Is Light Grey in a Driver's Forward Field of View

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-5014040c"
  title: "The RPM band is signalled by filling the viewport with the band colour in DIGITAL and by a light-grey r=232 ground in RADIAL; both emit more light than a ring would, and the DIGITAL form couples the readout's text colour to the band"
  date: "2026-08-04"
  reporter: "William Watson"
  status: "closed"
  severity: "medium"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-5014040c"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/display-ui-graphics-review.md v1.0, 2026-07-30.
    Finding §7.2 (Full-Field Colour as the Primary Band Cue), which also
    addresses §4.2 (Band Colour Thrash), with §9.5 recommendation 26.
    Scope is directed by ai/task.md §7.3.14, which resolves the report's
    conditional wording as accepted. Task list reference ai/task.md
    §7.3.11.

affected_scope:
  components:
    - name: "DisplayManager._draw_radial_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager._get_band_colour"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.3.2"

reproduction:
  prerequisites: >
    Source checkout at 0.3.2. Note that this issue is authored against
    the post-378703da tree: see technical_notes, which records that
    change-378703da materially alters what remains to be done here.
  steps:
    - "§7.2 — read manager.py:737 and 745-750. _draw_digital_mode fills a r=238 circle with the colour returned by _get_band_colour, so the whole viewport takes the band colour."
    - "§7.2 — read manager.py:616-673. _get_band_colour returns a (bg_colour, text_colour) pair; the text colour changes with the band, which is the coupling the finding names."
    - "§7.2 — read manager.py:867. In RADIAL the r=232 ground is filled (200, 200, 200), a light grey."
    - "§7.2 — read manager.py:922 and 931. The tick marks and numerals are drawn black, which is legible only against that light ground."
    - "§7.2 — read manager.py:891-896. RADIAL already expresses the band as coloured donut segments between inner_radius 100 and outer_radius 232 — an annulus."
    - "§4.2 — read manager.py:652-670. Hysteresis was added by change-4c038bed, so the alternation the report describes at a threshold no longer occurs. The emitted-light and coupling arguments are unaffected by that fix."
  frequency: "always"
  reproducibility_conditions: >
    Unconditional in structure. The night-glare consequence requires
    darkness and the vehicle, and has not been observed.
  preconditions: "None for the code findings."
  test_data: >
    EMITTED LIGHT, approximated from the fill areas, since the panel
    backlight cannot be switched off in software (report §7.2, citing
    the HyperPixel documentation).

    DIGITAL at caution: a r=238 disc of (255, 255, 0) is 177,900 px at
    relative luminance 0.9278 — effectively the whole panel at near
    maximum output.

    RADIAL today: a r=232 disc of (200, 200, 200) is 169,100 px at
    relative luminance 0.5776, plus the coloured arc over part of it.
    Lower than DIGITAL but still a large, bright, permanently lit field.

    RADIAL with a dark ground, say (16, 16, 16) at luminance 0.0048:
    the same 169,100 px contributes roughly 1% of what the light grey
    does, and the band is carried by the arc annulus, which at full
    sweep is pi * (232^2 - 100^2) * (300/360) = 114,700 px and at idle
    is a small fraction of that.

    These are area-weighted approximations, not photometry. They are
    recorded to show the argument is about a large ratio rather than a
    marginal one, and should not be quoted as measurements.

    WHAT REMAINS AFTER 378703da. Task 7.3.10 retires DIGITAL and
    _draw_digital_mode with it. The full-field band fill at
    manager.py:745-750 is DIGITAL's, and _get_band_colour's only caller
    is DIGITAL's, at manager.py:737. After that change lands:

      - the full-field fill this recommendation exists to replace no
        longer exists;
      - _get_band_colour has no caller, and is retained only because
        this triple was expected to need it (recorded in
        change-378703da scope.out_of_scope);
      - the text_colour half of its return value has no consumer at
        all, including a hypothetical one — the RADIAL readout added by
        378703da is unconditionally white.

    This is the central fact of this issue and is developed in
    technical_notes.
  error_output: "None."

behavior:
  expected: >
    A band cue that is visible peripherally without lighting the whole
    panel, on a ground that does not glare at night, with the readout's
    legibility independent of which band is active.
  actual: >
    Two forms of the same design choice.

    (a) DIGITAL fills the entire r=238 viewport with the band colour
    (manager.py:745-750) and selects the readout's text colour to suit
    it (manager.py:737, 768). The cue is unmissable and the costs are
    those the report names: it drove the §4.2 flicker before hysteresis
    was added, it couples text colour to band, and at night it is a
    full-field light source in the driver's forward view.

    (b) RADIAL does not fill with the band colour — it expresses the
    band as coloured donut segments (manager.py:891-896), which is
    already an annulus. But its ground is (200, 200, 200) light grey
    (manager.py:867), which carries most of the same night-glare cost,
    and its tick marks and numerals are black (manager.py:922, 931) and
    depend on that light ground for legibility.
  impact: >
    At night, a large bright field directly in the driver's forward
    field of view. This is the substantive cost and it cannot be
    mitigated by dimming the backlight, which the panel does not support
    in software.

    Secondarily, in DIGITAL, the readout's text colour is a function of
    the band, so a legibility correction must be made per band —
    which is exactly what change-4c038bed had to do for the blue band
    under recommendation 23.
  workaround: "None."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2"
  domain: "domain_1"

analysis:
  root_cause: >
    A full-field colour is the strongest available peripheral cue and
    was chosen for that reason. The cost — that the strongest cue is
    also the brightest — is only apparent at night, which a bench
    review does not exercise. RADIAL's light-grey ground follows the
    convention of a printed instrument face, where the ground is
    reflective rather than emissive; on an emissive panel the
    convention inverts.
  technical_notes: >
    THIS TRIPLE'S SCOPE IS LARGELY DETERMINED BY 378703da, AND SHRINKS.

    ai/task.md §7.6.1 records 7.3.11 as depending on 7.3.1 (4c038bed),
    which has shipped. It does not record the more consequential
    relationship, which is with 7.3.10 (378703da): that change removes
    _draw_digital_mode, and with it the full-field band fill that
    recommendation 26 exists to replace. §7.3.14 anticipates part of
    this — it requires this change document to state that 7.3.1's
    white-on-blue correction is superseded for the main readout, and to
    note whether _get_band_colour retains a text-colour return value —
    but it does not record that the fill itself disappears.

    The consequence is that this triple is not "replace a full-field
    fill with a ring". After 378703da there is no full-field fill. What
    remains is:

      (1) Replace RADIAL's light-grey (200, 200, 200) ground with a
          fixed dark ground, which is the "fixed dark ground" half of
          recommendation 26 and the half that carries the night-glare
          benefit.
      (2) Re-colour the tick marks and numerals, which are black
          (manager.py:922, 931) and become illegible on a dark ground.
          The report does not mention this; it follows necessarily.
      (3) Strengthen the existing arc annulus into an explicit band
          indicator, since on a dark ground the progressive fill arc
          becomes the sole band cue rather than one cue among several.
      (4) Reduce _get_band_colour to a band colour alone, its
          text_colour return having lost its only consumer.

    ORDERING IS THEREFORE NOT OPTIONAL. If this triple is implemented
    before 378703da it must edit _draw_digital_mode as well, and that
    work is then deleted. ai/task.md §7.6.2 places both at step 9;
    within that step 378703da must precede this change. Recorded here
    because the task list does not say so.

    ON _get_band_colour's RETENTION. change-378703da retains the method
    against this triple's need, and that need is real — items (3) and
    (4) both use it. But it is used differently from how DIGITAL used
    it: DIGITAL asked for a background and a text colour; this triple
    asks for the active band's identity and its colour. The hysteresis
    at manager.py:652-670 is the part that matters and is preserved
    exactly; the palette's second column is what goes.

    RELATIONSHIP TO 7.3.5 AND 7.3.12. Cross-check discrepancy D3
    (ai/workspace/report/task-list-cross-check-discrepancies.md §7.0)
    records that this change alters what 7.3.5's static-layer cache
    considers invariant: a ring whose colour varies with the band
    cannot be cached as static. If 7.3.5 lands first its cache key must
    include the active band index, and this triple must extend it.
    7.3.12 (5012004e) then adds a palette variant to the same key. The
    dark ground introduced here is also the ground the night palette
    varies, so the two interact directly.

    ON §4.2. The report lists recommendation 26 as addressing §4.2
    (band colour thrash) as well as §7.2. §4.2 was already resolved by
    change-4c038bed's hysteresis (manager.py:652-670), which has
    shipped and is closed. This triple does not re-address it. Recorded
    so the coverage claim in ai/task.md §7.3 is not read as leaving
    §4.2 open.
  related_issues:
    - issue_ref: "issue-378703da"
      relationship: "blocked_by"
    - issue_ref: "issue-4c038bed"
      relationship: "related"
    - issue_ref: "issue-5012004e"
      relationship: "blocks"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Replace RADIAL's light-grey ground with a fixed dark ground,
    re-colour the ticks and numerals for it, promote the coloured fill
    arc to the explicit band indicator, and reduce _get_band_colour to
    returning the band index and its colour. See change-5014040c.
  change_ref: "change-5014040c"
  resolved_date: "2026-08-04"
  resolved_by: "Claude Code, per prompt-5014040c (commit 730ae56)"
  fix_description: >
    Six FACE_ constants and BAND_COLOURS relocated to models.py's
    Palette dataclass (day and night instances, per change-5012004e).
    RADIAL ground darkened; ticks and numerals re-coloured for it;
    inline threshold table removed and the arc's leading segment now
    takes its colour from _get_band_colour, which is reduced to index +
    colour. See ai/workspace/report/v0.4.0-triple-implementation-session.md
    §4.3.

    One deviation, recorded in source: BAND_COLOURS index 0 delivered
    as (0, 0, 255) rather than the prompt's specified (0, 0, 0). That
    black was DIGITAL's idle screen background, never an arc colour;
    adopting it would repaint the idle arc segment black on a
    near-black face. The prompt's own "six drawn colours unchanged"
    constraint governs over its EDIT C palette literal.

verification:
  verified_date: "2026-08-05"
  verified_by: "Claude Code (development-platform script); William Watson (gtach.local)"
  test_results: >
    Development-platform script (report §4.3) proved the band-index
    sequence identical to the pre-change implementation across rising
    and falling sweeps at 10 RPM steps, hysteresis asymmetry included,
    against the real pre-change source pulled from git — not
    hand-written expectations. No band-index alternation under a
    +/-50 RPM oscillation about a threshold. Arc shows blue, green and
    yellow at 5000 RPM rather than one colour.
  closure_notes: >
    William confirmed on 2026-08-07 that GTach is functioning correctly
    on gtach.local. One open finding remains, recorded rather than
    resolved: the WCAG 3:1 band-fill contrast this issue's own
    verification_steps calls for is arithmetically unsatisfiable
    alongside the fixed palette values both this change and 5012004e
    specify (task.md §9.8.5 item 3; measured day blue 2.21:1, night
    blue 1.55:1, FACE_TRACK 1.67:1, FACE_EDGE 2.02:1, FACE_LINE 2.76:1,
    against every other pair passing including day tick 14.55:1). The
    constants were implemented as specified rather than silently
    altered, since both prompts forbid changing them. Resolution
    requires a design decision — a lighter blue, a lighter ground, or
    dropping the 3:1 bar for band fills — not further implementation.
    Not a blocker to this triple's closure; the same open question is
    recorded on issue-5012004e.

prevention:
  preventive_measures: >
    A design intended for a reflective surface does not transfer to an
    emissive one without re-examining which elements are light and which
    are dark. The light-grey instrument face is correct on paper and
    wrong on a panel that cannot be dimmed.

    A colour pairing returned as a tuple invites both halves to be used;
    when one half loses its consumer the tuple survives and misleads.
  process_improvements: >
    The dependency this issue records on 378703da was not in the task
    list, and would have been discovered only when an implementer found
    _draw_digital_mode already deleted. Dependencies between triples
    that arise from one triple deleting another's subject matter are
    worth looking for explicitly when a plan contains retirements.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/manager.py passes."
    - "The r=232 ground is a dark colour; (200, 200, 200) does not appear as a fill in _draw_radial_mode."
    - "Tick marks and numerals are legible against the new ground: WCAG contrast computed for each, all >= 4.5:1."
    - "The band is discernible from the arc annulus alone at every band, tested by rendering one frame per band."
    - "_get_band_colour returns the band index and a single colour; no call site expects a text colour."
    - "The hysteresis behaviour of _get_band_colour is identical to the pre-change implementation across a rising and falling sweep."
    - "The centre readout added by 378703da remains white and legible against all four _get_shift_cue fills."
    - "The shift border (manager.py:866) and the inert bottom arc are unaffected."
    - "No reference to _draw_digital_mode remains — it must already be absent, 378703da having landed first."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-5014040c"
  test_refs: []

notes: >
  This is task 7.3.11 in ai/task.md §7.3 and step 9 in the recommended
  authoring order (§7.6.2). Released in v0.4.0 (§8.5).

  issue_info.type is enhancement per ai/task.md §7.2: §7.2 is a display
  §7.x user interface proposal. Severity medium — a night-glare source
  in a driver's forward field of view is a real ergonomic cost, but
  nothing malfunctions.

  Scope is directed by ai/task.md §7.3.14: the annular indicator on a
  fixed dark ground is accepted, not conditional. Two of §7.3.14's three
  requirements are answered in technical_notes — 7.3.1's white-on-blue
  correction is superseded because the readout it applied to is gone
  with DIGITAL, and _get_band_colour does not retain a text-colour
  return value.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-04"
    author: "William Watson"
    changes:
      - "Initial issue document from display-ui-graphics-review.md finding §7.2 with §9.5 recommendation 26, scoped to ai/task.md §7.3.14."
      - "Recorded the governing finding: after change-378703da retires DIGITAL, the full-field band fill this recommendation exists to replace no longer exists, and the triple's remaining content is RADIAL's light-grey ground, the tick and numeral colours that depend on it, the arc annulus becoming the sole band cue, and _get_band_colour losing its text-colour return."
      - "Recorded that 378703da must precede this change, which ai/task.md §7.6.2 does not state."
      - "Recorded that §4.2 was already closed by change-4c038bed's hysteresis and is not re-addressed here."
      - "Recorded the D3 cache-key obligation toward 7.3.5 and the interaction with 7.3.12's night palette, which varies the ground this change introduces."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status open -> closed. change-5014040c implemented 2026-08-04 (730ae56); band-index sequence proved identical to pre-change source across rising/falling sweeps. One documented deviation: BAND_COLOURS[0] delivered as blue rather than the specified black, justified in source."
      - "Recorded the open contrast-criterion finding (task.md §9.8.5 item 3) as unresolved by design decision, not by implementation gap. Not a blocker."
      - "Closed on William's confirmation that GTach functions correctly on gtach.local. Moved to ai/workspace/issues/closed/."

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
| 1.0 | 2026-08-04 | Initial issue document from display review finding §7.2 with recommendation 26. Records that change-378703da removes the full-field fill this recommendation targets, restating the triple's scope as RADIAL's ground, tick and numeral colours, the arc annulus, and `_get_band_colour`'s return shape. |
| 1.1 | 2026-08-07 | Status open → closed. Resolution and verification recorded (commit 730ae56); the arithmetically-unsatisfiable contrast criterion recorded as an open design question, not a defect. Closed on William's confirmation that GTach functions correctly on gtach.local. |

---

Copyright (c) 2026 William Watson. MIT License.
