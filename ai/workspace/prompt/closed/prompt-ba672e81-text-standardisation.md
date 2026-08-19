Created: 2026 August 19

# Prompt: Small-Text Font Standardisation and Font-Path Consolidation

---

## Table of Contents

[Prompt](<#prompt>)
[Version History](<#version history>)

---

## Prompt

```yaml
prompt_info:
  id: "prompt-ba672e81"
  task_type: "refactor"
  source_ref: "change-ba672e81"
  target_profile: "claude_code"
  date: "2026-08-19"
  iteration: 1
  coupled_docs:
    change_ref: "change-ba672e81"
    change_iteration: 1

context:
  purpose: >
    Standardise all small-text UI elements (hints, labels, status
    messages, metadata) on GTach's HyperPixel display to a single
    18px size, and eliminate all font-creation code paths that bypass
    FontManager, so that font size and validity are governed from one
    place (typography.py) rather than three.
  integration: >
    Touches the display rendering layer only (src/gtach/display/).
    No OBD, Bluetooth, or systemd-integration behaviour is affected.
    Purely visual/structural change.
  knowledge_references: []
  constraints:
    - "Do not modify FONT_BUTTON, BUTTON_FONT_* constants, or title/heading/body font tiers"
    - "Do not touch device_surfaces.py's duplicate rendering blocks beyond removing their raw pygame.font.Font fallback branches — the blocks' own consolidation is deferred (see ai/task.md) and out of scope"
    - "FontManager's own internal use of pygame.font.Font (custom-font-file-missing → system-default fallback, inside typography.py) is legitimate and must be retained; only caller-side bypasses of FontManager are removed"
    - "All measurement/visual verification is on-device only (root@gtach.local, SDL_VIDEODRIVER=dummy); macOS runtime is not available for this purpose"

specification:
  description: >
    Implements change-ba672e81 in full: (1) typography.py constant
    consolidation, (2) manager.py private font-cache wrapper removal,
    (3) fallback-branch removal in splash.py and device_surfaces.py,
    (4) setup.py accessor updates.
  requirements:
    functional:
      - "Add TypographyConstants.FONT_SMALL_TEXT = 18"
      - "Remove TypographyConstants.FONT_LABEL_SMALL and TypographyConstants.FONT_MINIMAL"
      - "Consolidate get_label_small_font() and get_minimal_font() into a single accessor function returning a font at FONT_SMALL_TEXT (retain one function name, update all call sites, remove the other)"
      - "Harden FontManager.get_font() so it does not return None to callers under normal operation (raise or log-and-use-system-default per implementer's judgement, consistent with existing error-handling conventions in the file)"
      - "Remove DisplayManager._get_cached_font() (manager.py) entirely"
      - "Repoint all 16 former call sites of DisplayManager._get_cached_font() to call FontManager (via get_font_manager().get_font(size) or the appropriate semantic accessor) directly, preserving each site's existing point size except where that site used 16px for a small-text element in scope (those become FONT_SMALL_TEXT)"
      - "Remove the raw pygame.font.Font(None, fallback_size) fallback branch inside SplashScreenRenderer's local _get_cached_font() method (splash.py) — retain the method itself and its font_type-based dispatch"
      - "Remove the six raw pygame.font.Font(None, size) fallback branches in device_surfaces.py (both the fixed-literal block ~lines 160-220 and the scale_factor-derived block ~lines 295-370)"
      - "Update setup.py's four get_minimal_font() call sites to the consolidated accessor"
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance: []

design:
  architecture: "Single-source-of-truth typography constant + single font-creation path (FontManager) enforced by removing alternate paths"
  components:
    - name: "TypographyConstants"
      type: "class"
      purpose: "Central font-size constant definitions"
      interface:
        inputs: []
        outputs:
          type: "class attributes"
          description: "FONT_SMALL_TEXT = 18 replacing FONT_LABEL_SMALL (16) and FONT_MINIMAL (14)"
        raises: []
      logic:
        - "Remove FONT_LABEL_SMALL and FONT_MINIMAL class attributes"
        - "Add FONT_SMALL_TEXT = 18 class attribute"
        - "Update inline comments referencing the removed constants (e.g. splash.py docstring 'FONT_LABEL_SMALL = 16px, was 24px')"
    - name: "FontManager.get_font"
      type: "function"
      purpose: "Sole path for obtaining a validated, cached pygame Font object"
      interface:
        inputs:
          - name: "size"
            type: "int"
            description: "Requested point size, validated against MIN_FONT_SIZE/MAX_FONT_SIZE"
        outputs:
          type: "pygame.font.Font"
          description: "Always a valid Font object; no longer returns None to the caller under normal operation"
        raises:
          - "Implementer's judgement: either raise on unrecoverable failure, or log at ERROR level and construct a last-resort pygame.font.Font(None, size) internally within FontManager itself (not in caller code) so the guarantee holds without pushing fallback logic back out to callers"
      logic:
        - "Review existing exception handling in get_font() (typography.py ~lines 183-220)"
        - "Ensure the caching/validation logic already present is preserved"
        - "Close the code path that currently allows None to propagate to callers"
    - name: "DisplayManager"
      type: "class"
      purpose: "Removal of duplicate font-cache wrapper"
      interface:
        inputs: []
        outputs:
          type: "n/a"
          description: "Structural removal, not a new capability"
        raises: []
      logic:
        - "Delete _get_cached_font(self, size, font_path=None) method (manager.py ~lines 2572-2582)"
        - "At each of the 16 former call sites, replace self._get_cached_font(N) with get_font_manager().get_font(N), or with the pre-existing semantic accessor already imported at the top of manager.py where one exists for that size/purpose"
        - "Where the prior call used 16px for one of the in-scope small-text elements (label_font at line ~1314, slider font at line ~2162), use the new FONT_SMALL_TEXT constant/accessor instead of a literal 16"
        - "_get_plain_font() (manager.py ~2583) may be retained if it serves a distinct, still-needed purpose (SDL default fonts keyed by size per its docstring) — evaluate whether it becomes redundant once _get_cached_font() is removed; if its only caller was _get_cached_font(), remove it too"
    - name: "SplashScreenRenderer"
      type: "class"
      purpose: "Remove fallback branch, keep semantic font_type dispatch"
      interface:
        inputs: []
        outputs:
          type: "n/a"
          description: "Structural removal"
        raises: []
      logic:
        - "In splash.py's local _get_cached_font(self, font_type, fallback_size), remove the pygame.font.Font(None, fallback_size) fallback branch (~line 288) that runs when the typography-manager path fails"
        - "Update the docstring/comment at splash.py ~line 523 referencing 'FONT_LABEL_SMALL = 16px, was 24px' to reference FONT_SMALL_TEXT"
    - name: "Device surfaces rendering"
      type: "module"
      purpose: "Remove fallback branches in both rendering blocks"
      interface:
        inputs: []
        outputs:
          type: "n/a"
          description: "Structural removal"
        raises: []
      logic:
        - "Remove fallback pygame.font.Font(None, 14) at device_surfaces.py lines ~187/190 (type_font)"
        - "Remove fallback pygame.font.Font(None, 12) at lines ~212/214 (signal_font)"
        - "Remove fallback pygame.font.Font(None, body_font_size) at lines ~310/313 and ~331/334 (name_font, type_font in scale_factor block)"
        - "Remove fallback pygame.font.Font(None, signal_font_size) at lines ~365/367"
        - "Do not otherwise restructure these two blocks — their consolidation is a separate, deferred item"
    - name: "Bluetooth setup screen"
      type: "module"
      purpose: "Update accessor references"
      interface:
        inputs: []
        outputs:
          type: "n/a"
          description: "Call-site update"
        raises: []
      logic:
        - "Update get_minimal_font() calls at setup.py lines ~324, ~357, ~429, ~508 to the consolidated accessor name"
  dependencies:
    internal:
      - "typography.py must be modified first; all other files depend on its updated constant/accessor"
    external: []

data_schema:
  entities: []

error_handling:
  strategy: >
    FontManager.get_font() becomes the single point of failure
    handling for font creation. Callers no longer need their own
    fallback branches. Follow the existing logging conventions already
    present in typography.py (self.logger.warning/error patterns).
  exceptions:
    - exception: "pygame.error or equivalent font-load failure"
      condition: "Custom font file (Michroma) unavailable or corrupt"
      handling: "Existing internal fallback within FontManager to pygame.font.Font(None, size) (system default) is retained — this is FontManager's own internal responsibility, not a caller bypass, and is unaffected by this change"
  logging:
    level: "DEBUG"
    format: "Existing f-string debug/error logging conventions already used in typography.py, manager.py, splash.py, device_surfaces.py"

testing:
  unit_tests:
    - scenario: "FontManager.get_font(18) returns a valid Font object"
      expected: "Non-None pygame.font.Font instance"
    - scenario: "TypographyConstants.FONT_LABEL_SMALL and FONT_MINIMAL no longer exist"
      expected: "AttributeError if referenced; confirms removal"
    - scenario: "DisplayManager has no _get_cached_font attribute"
      expected: "AttributeError if referenced; confirms removal"
  edge_cases:
    - "FontManager.get_font() called with a size outside MIN_FONT_SIZE/MAX_FONT_SIZE bounds still clamps and logs a warning as before (this behaviour is unchanged by the hardening — only the None-return path changes)"
  validation:
    - "grep for FONT_LABEL_SMALL, FONT_MINIMAL across src/ returns zero matches (excluding backup files manager_backup.py, setup_original_backup.py, which are out of scope)"
    - "grep for pygame.font.Font(None across src/gtach/display/*.py (excluding typography.py) returns zero matches"
    - "grep for _get_cached_font in manager.py returns zero matches"

deliverable:
  format_requirements:
    - "Save generated code directly to specified paths"
    - "Execute pytest suite for affected test paths on completion; report pass/fail summary"
  files:
    - path: "src/gtach/display/typography.py"
      content: "Modified: FONT_SMALL_TEXT constant added, FONT_LABEL_SMALL/FONT_MINIMAL removed, accessor consolidated, FontManager.get_font() hardened"
    - path: "src/gtach/display/manager.py"
      content: "Modified: _get_cached_font() removed, 16 call sites repointed to FontManager"
    - path: "src/gtach/display/splash.py"
      content: "Modified: fallback branch removed from local _get_cached_font(), stale docstring updated"
    - path: "src/gtach/display/setup_components/rendering/device_surfaces.py"
      content: "Modified: six raw pygame.font.Font fallback branches removed"
    - path: "src/gtach/display/setup.py"
      content: "Modified: four get_minimal_font() call sites updated to consolidated accessor"

success_criteria:
  - "All small-text elements identified in issue-ba672e81 render at 18px on-device"
  - "Zero references to FONT_LABEL_SMALL or FONT_MINIMAL remain in active (non-backup) source files"
  - "Zero references to DisplayManager._get_cached_font remain"
  - "Zero raw pygame.font.Font(None, ...) calls remain outside typography.py"
  - "Existing pytest suite passes with no new failures"

element_registry:
  source: ""
  entries:
    constants:
      - name: "FONT_SMALL_TEXT"
        module: "src/gtach/display/typography.py"
        type: "int (class attribute of TypographyConstants)"

notes: >
  This is a manual Claude Code execution (no AEL loop); tactical_brief
  is not required for this target_profile. Implementer should read
  typography.py, manager.py, splash.py, device_surfaces.py, and
  setup.py in full before starting, given the cross-file call-site
  repointing involved. Regression scope per change-ba672e81:
  any test referencing the retired symbols by name.
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial creation |

---

Copyright (c) 2026 William Watson. MIT License.
