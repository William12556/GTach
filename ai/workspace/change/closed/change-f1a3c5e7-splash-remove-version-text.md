Created: 2026 May 06

# Change: Remove Version Text from Automotive Splash Mode

---

```yaml
change_info:
  id: "change-f1a3c5e7"
  title: "Remove version text render call from automotive splash mode block"
  date: "2026-05-06"
  author: "William Watson"
  status: "approved"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-f1a3c5e7"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-f1a3c5e7-splash-version-text-displayed.md"
  description: >
    Visual test confirmed version string "v1.0.0" rendered on splash automotive mode.
    Requirement: automotive splash shows title only.

scope:
  summary: "Remove one call to _draw_version_text() from the automotive mode else-block in _render_graphics()"
  affected_components:
    - name: "SplashScreen._render_graphics"
      file_path: "src/gtach/display/splash.py"
      change_type: "modify"
  out_of_scope:
    - "_draw_version_text method definition — must remain"
    - "_version_text field — must remain"
    - "text_only and minimal mode render paths — must remain unchanged"

rational:
  problem_statement: "Version text visible on splash contrary to minimalist automotive design."
  proposed_solution: "Delete the self._draw_version_text(...) call from the automotive else-block."
  alternatives_considered:
    - option: "Set _version_text to empty string"
      reason_rejected: "Breaks text_only and minimal modes that legitimately display version"
  benefits:
    - "Automotive splash is clean: title + progress gauge + border only"
  risks:
    - risk: "None — trivial single-line deletion"
      mitigation: "N/A"

technical_details:
  current_behavior: "automotive mode calls _draw_version_text(surface, center_x, center_y + 105)"
  proposed_behavior: "automotive mode does not render version text"
  implementation_approach: "Delete one line from the automotive else-block in _render_graphics()"
  code_changes:
    - component: "SplashScreen._render_graphics"
      file: "src/gtach/display/splash.py"
      change_summary: "Remove: self._draw_version_text(surface, center_x, center_y + 105)"
      functions_affected:
        - "_render_graphics"
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-05-06 | Initial change document |

---

Copyright (c) 2026 William Watson. MIT License.
