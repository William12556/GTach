Created: 2026 May 06

# Prompt: Clear Framebuffer on Splash Completion

---

```yaml
prompt_info:
  id: "prompt-b2d4f6a8"
  task_type: "code_generation"
  source_ref: "change-b2d4f6a8"
  date: "2026-05-06"
  iteration: 1
  coupled_docs:
    change_ref: "change-b2d4f6a8"
    change_iteration: 1
```

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Task: clear framebuffer on splash completion to fix Pi welcome flicker (b2d4f6a8).

  FILE: src/gtach/display/manager.py

  In method _draw_splash_mode(), locate the block:
    if self._splash_screen.is_complete():

  Immediately BEFORE the existing try: self._splash_screen.reset() block,
  INSERT these two lines:
    self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER)
    self.rendering_engine.swap_buffers()

  The insertion point is after the if/elif/else chain that sets self.config.mode
  and logs the transition, and before the try/except that calls _splash_screen.reset().

  DO NOT modify any other method or file.

  VERIFY:
    python -c "import ast; ast.parse(open('src/gtach/display/manager.py').read())"
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
