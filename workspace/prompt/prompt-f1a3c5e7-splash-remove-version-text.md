Created: 2026 May 06

# Prompt: Remove Version Text from Automotive Splash Mode

---

```yaml
prompt_info:
  id: "prompt-f1a3c5e7"
  task_type: "code_generation"
  source_ref: "change-f1a3c5e7"
  date: "2026-05-06"
  iteration: 1
  coupled_docs:
    change_ref: "change-f1a3c5e7"
    change_iteration: 1
```

---

## 8.0 Tactical Brief

```yaml
tactical_brief: |
  Task: remove version text from automotive splash mode (f1a3c5e7).

  FILE: src/gtach/display/splash.py

  In method _render_graphics(), locate the automotive else-block
  (the block that calls _draw_title_text, _draw_progress_indicator,
  _draw_version_text, _draw_border in sequence).

  DELETE this one line from that block:
    self._draw_version_text(surface, center_x, center_y + 105)

  DO NOT:
  - Remove the _draw_version_text method definition
  - Remove the _version_text field
  - Touch text_only or minimal mode blocks

  VERIFY:
    python -c "import ast; ast.parse(open('src/gtach/display/splash.py').read())"
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial prompt |

---

Copyright (c) 2026 William Watson. MIT License.
