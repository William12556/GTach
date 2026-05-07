Created: 2026 May 06

# Issue: Welcome Screen Not Cleared Before Render on Pi

---

## Table of Contents

- [1.0 Issue Information](<#1.0 issue information>)
- [2.0 Source](<#2.0 source>)
- [3.0 Affected Scope](<#3.0 affected scope>)
- [4.0 Reproduction](<#4.0 reproduction>)
- [5.0 Behavior](<#5.0 behavior>)
- [6.0 Environment](<#6.0 environment>)
- [7.0 Analysis](<#7.0 analysis>)
- [Version History](<#version history>)

---

```yaml
issue_info:
  id: "issue-b2d4f6a8"
  title: "Welcome screen not cleared on Pi — flicker between splash and welcome"
  date: "2026-05-06"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Pi visual test. After splash completes, the WELCOME screen appears to flicker —
    splash frame persists briefly behind first WELCOME render. Not observed on macOS
    (pygame window mode vs memory-mapped framebuffer on Pi).

affected_scope:
  components:
    - name: "DisplayManager._draw_splash_mode"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayRenderingEngine"
      file_path: "src/gtach/display/rendering.py"
    - name: "SetupDisplayManager.render"
      file_path: "src/gtach/display/setup.py"
  designs: []
  version: "current"

reproduction:
  prerequisites: "GTach installed on Pi (root@gtach.local)"
  steps:
    - "ssh root@gtach.local 'gtach --debug 2>&1 | tee /opt/gtach/gtach-debug.log'"
    - "Observe display at splash-to-welcome transition (~4s after start)"
  frequency: "always"
  reproducibility_conditions: "Pi framebuffer mode only (not reproducible on macOS pygame window)"
  preconditions: ""
  test_data: >
    Log confirms: SplashScreen completed after 4.01s, DisplayManager INFO Splash completed
    - entering setup mode, immediately followed by SetupDisplayManager DEBUG Using cached
    render for WELCOME. No clear_surface call between splash exit and first WELCOME render.
  error_output: ""

behavior:
  expected: "Clean transition from splash to welcome — no ghost of splash frame visible"
  actual: >
    Splash frame persists in framebuffer behind first WELCOME blit. Appears as flicker
    or overlap between splash and welcome screen on Pi display.
  impact: >
    Visual artefact at startup. Functional operation unaffected but user experience degraded.
    Pi-specific: framebuffer is not double-buffered in the same way as a pygame window;
    partial renders are visible immediately.
  workaround: "None"

environment:
  python_version: "3.9"
  os: "Raspberry Pi OS Debian 12"
  dependencies:
    - library: "pygame"
      version: "current"
  domain: "display"

analysis:
  root_cause: >
    When _draw_splash_mode() detects splash completion and sets config.mode to
    _post_splash_mode (setup mode), it resets the splash screen but does not call
    rendering_engine.clear_surface(RenderTarget.BACK_BUFFER) before handing off.
    On the next display loop iteration, _render_setup_mode() calls
    setup_manager.render(back_surface), which blits the cached WELCOME surface onto
    whatever was already in the back buffer (the last splash frame). On macOS the
    pygame window compositing masks this; on Pi the memory-mapped framebuffer exposes it.
    The cached WELCOME render may also not fill the entire 480x480 surface if it only
    blits WELCOME content over existing pixels.
  technical_notes: >
    Candidate fix: in _draw_splash_mode(), call
    self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER) immediately after
    detecting is_complete() before resetting the splash and changing mode.
    Alternative: ensure SetupDisplayManager.render() fills the entire surface before
    blitting any component. Both approaches need verification on Pi.
    Not a trivial change — requires understanding of rendering pipeline and cached render
    behaviour in SetupDisplayManager.
  related_issues:
    - issue_ref: "issue-f1a3c5e7"
      relationship: "related — both are splash/welcome transition defects"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial issue — Pi visual test observation |

---

Copyright (c) 2026 William Watson. MIT License.
