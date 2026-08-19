Created: 2026 August 19

# Issue: Small-Text Font Standardisation and Font-Path Consolidation

---

## Table of Contents

[Issue](<#issue>)
[Version History](<#version history>)

---

## Issue

```yaml
issue_info:
  id: "issue-ba672e81"
  title: "Small-text font sizes inconsistent across screens; parallel font-creation paths bypass FontManager validation"
  date: "2026-08-19"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "enhancement"
  iteration: 1
  coupled_docs:
    change_ref: "change-ba672e81"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Manual review of the OPTIONS screen identified "Swipe up to return"
    hint text (16px, FONT_LABEL_SMALL) as difficult to read. A code-base
    audit for comparable small-text elements found a second tier at 14px
    (FONT_MINIMAL) and a 12px raw fallback with no typography constant,
    producing three effective small-text sizes with no consistent rule
    for which screen or purpose uses which size. The audit also
    identified that font objects for these elements are created via
    three parallel paths: FontManager (validated, cached), a private
    _get_cached_font() wrapper in manager.py duplicating FontManager
    with its own raw pygame.font.Font fallback, and direct
    pygame.font.Font(None, size) fallback calls in splash.py and
    device_surfaces.py used when FontManager returns None.

affected_scope:
  components:
    - name: "TypographyConstants / FontManager"
      file_path: "src/gtach/display/typography.py"
    - name: "DisplayManager small-text rendering and font cache"
      file_path: "src/gtach/display/manager.py"
    - name: "SplashScreenRenderer font fallback"
      file_path: "src/gtach/display/splash.py"
    - name: "Bluetooth device list rendering"
      file_path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
    - name: "Bluetooth setup screen status/error text"
      file_path: "src/gtach/display/setup.py"
  designs: []
  version: ""

reproduction:
  prerequisites: "On-device or SDL_VIDEODRIVER=dummy visual inspection"
  steps:
    - "Navigate to OPTIONS screen; observe 'Swipe up to return' hint text at 16px"
    - "Navigate to Bluetooth setup screen; observe status/error/scan messages at 14px"
    - "Trigger a FontManager failure path (e.g. missing font cache entry) in device_surfaces.py; observe 12px raw fallback with no typography constant"
  frequency: "always"
  reproducibility_conditions: "Present on every affected screen under normal operation"
  preconditions: ""
  test_data: ""
  error_output: ""

behavior:
  expected: >
    A single, readable small-text size applied consistently to all
    hint, label, status, and metadata text, produced exclusively
    through FontManager.
  actual: >
    Three effective sizes (16px, 14px, 12px) across five files, with
    three independent code paths capable of producing a font object
    for these elements (FontManager, manager.py::_get_cached_font,
    raw pygame.font.Font fallbacks).
  impact: >
    Readability inconsistency across screens (user-reported, low
    severity). No functional defect. Secondary maintainability risk:
    the parallel paths allow size drift to recur even after this
    consolidation, since two of the three paths do not read from
    TypographyConstants.
  workaround: "None required; cosmetic/maintainability issue."

environment:
  python_version: "3.11"
  os: "Debian GNU/Linux 11 (Bullseye)"
  dependencies:
    - library: "pygame"
      version: "2.6.1"
  domain: "domain_1"

analysis:
  root_cause: >
    (1) No single typography rule maps text purpose to size; FONT_LABEL_SMALL
    (16px) and FONT_MINIMAL (14px) were introduced independently for
    different screens without a shared standard. (2) manager.py's
    _get_cached_font() duplicates FontManager rather than calling it,
    and includes its own raw pygame.font.Font fallback. (3) splash.py
    and device_surfaces.py call FontManager first but fall back to raw
    pygame.font.Font(None, size) on a None return, which is defensive
    error handling rather than a sizing policy, but leaves the
    possibility of an ungoverned font object reaching the display.
  technical_notes: >
    device_surfaces.py additionally contains two rendering blocks
    (~lines 160-220 and ~295-370) that appear to duplicate device
    name/type/signal rendering logic using different sizing
    computations (fixed literals vs. scale_factor-derived). This is
    tracked separately in ai/task.md pending calling-context
    investigation and is explicitly out of scope for this issue.
  related_issues: []

resolution:
  assigned_to: "William Watson"
  target_date: ""
  approach: >
    See change-ba672e81 for full technical approach: consolidate
    FONT_LABEL_SMALL and FONT_MINIMAL into a single 18px constant;
    remove manager.py::_get_cached_font() and repoint its 16 call
    sites to FontManager; harden FontManager.get_font() so it cannot
    return None, removing the need for raw pygame.font.Font fallbacks
    in splash.py and device_surfaces.py.
  change_ref: "change-ba672e81"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    Single font-creation path (FontManager only) removes the structural
    condition that allowed size drift and ungoverned fallbacks to
    recur.
  process_improvements: ""

verification_enhanced:
  verification_steps:
    - "On-device visual inspection of all affected screens post-implementation (SSH to root@gtach.local, SDL_VIDEODRIVER=dummy per project convention)"
    - "Code search confirming zero remaining references to FONT_LABEL_SMALL, FONT_MINIMAL, and manager.py::_get_cached_font()"
    - "Code search confirming zero remaining raw pygame.font.Font(None, ...) calls outside typography.py"
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-ba672e81"
  test_refs: []

notes: >
  Scope decided collaboratively across prior discussion: one-tier
  consolidation at 18px (adjustable after on-device testing); full
  elimination of parallel font-creation paths, not a scoped
  elimination limited to small-text call sites. Duplicate-block
  cleanup in device_surfaces.py deferred (see ai/task.md).

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-19"
    author: "Claude"
    changes:
      - "Initial issue creation"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial creation |

---

Copyright (c) 2026 William Watson. MIT License.
