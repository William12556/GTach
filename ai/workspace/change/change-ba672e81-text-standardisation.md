Created: 2026 August 19

# Change: Small-Text Font Standardisation and Font-Path Consolidation

---

## Table of Contents

[Change](<#change>)
[Version History](<#version history>)

---

## Change

```yaml
change_info:
  id: "change-ba672e81"
  title: "Consolidate small-text typography to one 18px tier; eliminate parallel font-creation paths"
  date: "2026-08-19"
  author: "Claude"
  status: "proposed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-ba672e81"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-ba672e81"
  description: >
    Consolidate the two small-text typography tiers (FONT_LABEL_SMALL
    16px, FONT_MINIMAL 14px) plus an ungoverned 12px raw fallback into
    a single 18px constant, and eliminate all font-creation paths that
    bypass FontManager.

scope:
  summary: >
    Typography constant consolidation in typography.py; removal of
    manager.py's private font-cache wrapper with repointing of its 16
    call sites; hardening of FontManager.get_font() to eliminate None
    returns; removal of raw pygame.font.Font fallback branches in
    splash.py and device_surfaces.py that exist only to handle those
    None returns.
  affected_components:
    - name: "TypographyConstants"
      file_path: "src/gtach/display/typography.py"
      change_type: "modify"
    - name: "FontManager.get_font"
      file_path: "src/gtach/display/typography.py"
      change_type: "modify"
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "SplashScreenRenderer"
      file_path: "src/gtach/display/splash.py"
      change_type: "modify"
    - name: "Bluetooth device list rendering"
      file_path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      change_type: "modify"
    - name: "Bluetooth setup screen"
      file_path: "src/gtach/display/setup.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "device_surfaces.py duplicate rendering blocks (~lines 160-220 vs ~295-370) — deferred, tracked in ai/task.md"
    - "Button font tier (FONT_BUTTON, BUTTON_FONT_* constants) — unaffected, out of scope"
    - "Title/heading/body font tiers — unaffected, out of scope"
    - "Borderline 18px disconnection-cause text (manager.py, _render_disconnected) — already at target size, not modified, but should be reviewed for consistency once new constant lands"

rational:
  problem_statement: >
    Small text renders at three different sizes (16px, 14px, 12px)
    across five files with no documented rule distinguishing them, and
    is produced through three independent code paths, only one of
    which (FontManager) enforces MIN_FONT_SIZE/MAX_FONT_SIZE
    validation and caching discipline. This allows visual
    inconsistency and permits future size drift to recur even after a
    one-time fix.
  proposed_solution: >
    Replace FONT_LABEL_SMALL and FONT_MINIMAL with a single
    FONT_SMALL_TEXT constant at 18px in TypographyConstants. Remove
    manager.py::_get_cached_font() entirely; call FontManager directly
    at all 16 of its former call sites, using FONT_SMALL_TEXT wherever
    the call site previously used 16px. Harden
    FontManager.get_font() so it always returns a valid Font object
    (raising or logging a fatal condition instead of returning None on
    unrecoverable failure), removing the structural need for raw
    pygame.font.Font fallback branches in splash.py and
    device_surfaces.py, which are then deleted.
  alternatives_considered:
    - option: "Two-tier consolidation (distinct primary/secondary small sizes)"
      reason_rejected: "William confirmed no meaningful distinction exists between current tiers; one-tier chosen."
    - option: "Scoped font-path elimination (small-text call sites only)"
      reason_rejected: "William elected full elimination for code correctness; manager.py::_get_cached_font() is removed entirely rather than leaving it in place for title/heading/body sizes."
  benefits:
    - "Single, readable small-text size across all screens"
    - "Single font-creation path; eliminates possibility of future silent size drift via fallback code"
    - "Removes an ungoverned 12px size point below the documented MIN_FONT_SIZE intent"
  risks:
    - risk: "Hardening FontManager.get_font() to never return None changes error-handling behaviour at 16 call sites in manager.py plus existing call sites in splash.py and device_surfaces.py; a font-load failure that was previously silently masked by a raw fallback will now surface (by design, per problem_statement), which could change on-device behaviour under a font-file-missing condition not previously exercised in testing."
      mitigation: "Verify on-device (root@gtach.local) after implementation; confirm Michroma font file presence is unaffected by this change (font *availability* is unchanged, only *failure handling* is changed)."
    - risk: "18px may still be judged too small or too large after on-device viewing; W. Watson has explicitly flagged this as a starting value subject to adjustment."
      mitigation: "Single named constant (FONT_SMALL_TEXT) makes future adjustment a one-line change."

technical_details:
  current_behavior: >
    FONT_LABEL_SMALL (16px) and FONT_MINIMAL (14px) are separate
    TypographyConstants values used inconsistently across screens.
    manager.py::_get_cached_font(size) duplicates FontManager.get_font()
    with a private cache and its own raw pygame.font.Font(None, size)
    fallback, called at 16 sites for sizes ranging 16-72px. splash.py
    and device_surfaces.py call FontManager first, falling back to raw
    pygame.font.Font(None, size) if it returns None.
  proposed_behavior: >
    A single FONT_SMALL_TEXT = 18 constant replaces FONT_LABEL_SMALL
    and FONT_MINIMAL. All font objects for these display elements, and
    all font objects previously produced by manager.py's private cache,
    are obtained exclusively through FontManager. FontManager.get_font()
    is guaranteed to return a valid Font object or raise/log a fatal
    condition; it does not return None to callers under normal
    operation.
  implementation_approach: >
    1. typography.py: add FONT_SMALL_TEXT = 18; remove FONT_LABEL_SMALL
       and FONT_MINIMAL; update get_label_small_font()/get_minimal_font()
       call sites (retain one accessor function, remove the other, or
       alias per implementer's judgement — single accessor preferred).
       Review FontManager.get_font() to remove/replace the code path
       that can return None; ensure the pygame.font.Font(None, size)
       system-default fallback inside FontManager itself (the
       legitimate internal fallback when a custom font file is
       unavailable) is retained, since that is FontManager's own
       responsibility, not a caller bypassing it.
    2. manager.py: delete _get_cached_font() method (lines ~2572-2610).
       Repoint all 16 call sites to FontManager.get_font() (or the
       relevant semantic accessor) directly, preserving each call
       site's existing size value except where that value was
       FONT_LABEL_SMALL/16px for a small-text element in scope, which
       becomes FONT_SMALL_TEXT.
    3. splash.py: remove the raw pygame.font.Font(None, fallback_size)
       fallback branch inside _get_cached_font() (this is a
       differently-scoped, differently-signatured method from
       manager.py's — retain the method, remove only the fallback
       branch that exists to handle FontManager returning None).
    4. device_surfaces.py: remove raw pygame.font.Font(None, size)
       fallback branches at all six call sites (both the fixed-literal
       block and the scale_factor-derived block — see out_of_scope
       note on the duplicate-block question itself, which is deferred;
       the fallback removal applies to both blocks as they exist
       today).
    5. setup.py: update get_minimal_font() call sites to the
       consolidated accessor.
  code_changes:
    - component: "TypographyConstants"
      file: "src/gtach/display/typography.py"
      change_summary: "Replace FONT_LABEL_SMALL (16) and FONT_MINIMAL (14) with FONT_SMALL_TEXT (18); consolidate accessor function"
      functions_affected:
        - "get_label_small_font"
        - "get_minimal_font"
      classes_affected:
        - "TypographyConstants"
    - component: "FontManager"
      file: "src/gtach/display/typography.py"
      change_summary: "Harden get_font() to eliminate None return path to callers"
      functions_affected:
        - "get_font"
      classes_affected:
        - "FontManager"
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: "Remove _get_cached_font() private wrapper; repoint 16 call sites to FontManager directly"
      functions_affected:
        - "_get_cached_font"
        - "_get_plain_font"
      classes_affected:
        - "DisplayManager"
    - component: "SplashScreenRenderer"
      file: "src/gtach/display/splash.py"
      change_summary: "Remove raw pygame.font.Font fallback branch in local _get_cached_font()"
      functions_affected:
        - "_get_cached_font"
      classes_affected: []
    - component: "Device surfaces rendering"
      file: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      change_summary: "Remove raw pygame.font.Font fallback branches (6 sites); update size references to FONT_SMALL_TEXT where applicable"
      functions_affected: []
      classes_affected: []
    - component: "Bluetooth setup screen"
      file: "src/gtach/display/setup.py"
      change_summary: "Update font accessor call sites to consolidated FONT_SMALL_TEXT accessor"
      functions_affected: []
      classes_affected: []
  data_changes: []
  interface_changes:
    - interface: "TypographyConstants.FONT_LABEL_SMALL, TypographyConstants.FONT_MINIMAL"
      change_type: "signature"
      details: "Both constants removed; replaced by TypographyConstants.FONT_SMALL_TEXT"
      backward_compatible: "no"
    - interface: "DisplayManager._get_cached_font"
      change_type: "contract"
      details: "Method removed entirely"
      backward_compatible: "no"

dependencies:
  internal:
    - component: "typography.py"
      impact: "Source of truth for the new constant; must be modified first"
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    On-device visual verification per project convention (SSH to
    root@gtach.local, SDL_VIDEODRIVER=dummy authoritative measurement
    environment) plus static code search confirming removal of retired
    symbols.
  test_cases:
    - scenario: "OPTIONS screen 'Swipe up to return' hint"
      expected_result: "Renders at 18px, visually consistent with other small text"
    - scenario: "Update view 'Swipe up to return' hint"
      expected_result: "Renders at 18px"
    - scenario: "Bluetooth setup status/error/scan messages"
      expected_result: "Render at 18px (previously 14px)"
    - scenario: "Bluetooth device list RSSI and device-type text"
      expected_result: "Render at 18px (previously 16px/14px/12px depending on path)"
    - scenario: "FontManager.get_font() under simulated failure"
      expected_result: "No longer silently returns None; raises or logs a fatal condition per hardened implementation"
  regression_scope:
    - "tests/test_typography.py (if present) or equivalent typography unit tests"
    - "Any test referencing FONT_LABEL_SMALL, FONT_MINIMAL, or DisplayManager._get_cached_font by name"
  validation_criteria:
    - "Zero remaining references to FONT_LABEL_SMALL, FONT_MINIMAL, manager.py::_get_cached_font"
    - "Zero remaining raw pygame.font.Font(None, ...) calls outside typography.py's own FontManager implementation"

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Add FONT_SMALL_TEXT constant and consolidate accessor in typography.py; harden FontManager.get_font()"
      owner: "Claude Code"
    - step: "Remove DisplayManager._get_cached_font(); repoint 16 call sites in manager.py"
      owner: "Claude Code"
    - step: "Remove fallback branch in splash.py's local _get_cached_font()"
      owner: "Claude Code"
    - step: "Remove fallback branches in device_surfaces.py (6 sites)"
      owner: "Claude Code"
    - step: "Update setup.py call sites"
      owner: "Claude Code"
    - step: "On-device visual verification"
      owner: "William Watson"
  rollback_procedure: "git revert of the implementing commit(s); no data migration involved"
  deployment_notes: "Deploy to root@gtach.local per standard process; verify visually before closing issue"

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes: []
  related_issues:
    - issue_ref: "issue-ba672e81"
      relationship: "resolves"

notes: >
  FONT_SMALL_TEXT = 18 is a starting value per explicit instruction;
  may be revised after on-device testing without requiring this
  change's reopening if the revision is a single-constant value
  change (trivial exemption may apply per P03 §1.4.12 if criteria
  met at that time).

version_history:
  - version: "1.0"
    date: "2026-08-19"
    author: "Claude"
    changes:
      - "Initial change document creation"

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial creation |

---

Copyright (c) 2026 William Watson. MIT License.
