Created: 2026 May 06

# Change: Clear Framebuffer Before Welcome Screen Render on Pi

---

```yaml
change_info:
  id: "change-b2d4f6a8"
  title: "Clear back-buffer on splash completion to eliminate welcome screen flicker on Pi"
  date: "2026-05-06"
  author: "William Watson"
  status: "approved"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-b2d4f6a8"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-b2d4f6a8-pi-welcome-screen-not-cleared.md"
  description: >
    Pi visual test: splash frame persists in framebuffer behind first WELCOME render,
    causing a flicker/ghost at the splash-to-welcome transition.

scope:
  summary: >
    In _draw_splash_mode(), call clear_surface on the back-buffer immediately after
    detecting splash completion and before changing config.mode. This ensures the
    framebuffer holds a clean black frame as the foundation for the first WELCOME render.
  affected_components:
    - name: "DisplayManager._draw_splash_mode"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
  out_of_scope:
    - "SetupDisplayManager render pipeline"
    - "macOS rendering path (no framebuffer; pygame window compositing handles this)"

rational:
  problem_statement: >
    Memory-mapped framebuffer on Pi writes pixels directly; partial renders are
    immediately visible. No clear between splash exit and first WELCOME blit leaves
    the splash frame ghosting behind the WELCOME content.
  proposed_solution: >
    After is_complete() returns True and before resetting the splash or changing mode,
    call self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER) followed by
    self.rendering_engine.swap_buffers() to flush a black frame to the framebuffer.
  alternatives_considered:
    - option: "Clear inside SetupDisplayManager.render()"
      reason_rejected: >
        SetupDisplayManager owns setup rendering, not the transition. Placing the clear
        in DisplayManager keeps ownership clear and avoids coupling.
  benefits:
    - "Clean black frame between splash and welcome eliminates ghost artefact on Pi"
    - "No impact on macOS (pygame window compositing is unaffected by an extra clear)"
  risks:
    - risk: "Brief black frame visible (~1 display loop iteration, ~16ms at 60fps)"
      mitigation: "Imperceptible at 60fps; preferable to the current ghost artefact"

technical_details:
  current_behavior: >
    _draw_splash_mode() detects is_complete(), resets splash, changes config.mode.
    Next loop iteration renders WELCOME over the existing splash back-buffer content.
  proposed_behavior: >
    _draw_splash_mode() detects is_complete(), calls clear_surface(BACK_BUFFER) +
    swap_buffers() to flush black to framebuffer, then resets splash and changes mode.
  implementation_approach: "Two additional lines inside the is_complete() branch of _draw_splash_mode()"
  code_changes:
    - component: "DisplayManager._draw_splash_mode"
      file: "src/gtach/display/manager.py"
      change_summary: >
        After splash_success = self._splash_screen.render(back_surface) block,
        inside the if self._splash_screen.is_complete(): block, insert before reset():
          self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER)
          self.rendering_engine.swap_buffers()
      functions_affected:
        - "_draw_splash_mode"
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
