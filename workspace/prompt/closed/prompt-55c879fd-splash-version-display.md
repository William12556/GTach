Created: 2026 June 12

```yaml
prompt_info:
  id: "prompt-55c879fd"
  task_type: "code_generation"
  source_ref: "change-55c879fd"
  date: "2026-06-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-55c879fd"
    change_iteration: 1

context:
  purpose: >
    Display the installed wheel version on the splash screen and fix the stale
    --version argparse literal, both reading from importlib.metadata.
  integration: >
    Two files modified: src/gtach/display/splash.py (SplashScreen) and
    src/gtach/main.py (parse_arguments). Executor: Claude Code (no AEL).
  constraints:
    - "Use importlib.metadata.version('gtach') only — do not read __version__ or pyproject.toml."
    - "Guard every importlib.metadata call with try/except; never raise on failure."
    - "Do not change font, typography, colour, or any other rendering detail."
    - "Do not modify any branch of _render_graphics other than the automotive else-branch."
    - "Do not modify manager_backup.py."

specification:
  description: "Three isolated edits — no structural changes."
  requirements:
    functional:
      - "Splash automotive mode displays the installed version below the progress gauge."
      - "Version string format: 'v{version}' (e.g. 'v0.2.61'). Fallback: 'v?.?.?'."
      - "gtach --version outputs 'GTach {version}'. Fallback: 'GTach'."
    technical:
      language: "Python"
      version: "3.11"
      standards:
        - "importlib.metadata is stdlib; no new dependencies."
        - "PackageNotFoundError guarded at every call site."

design:
  architecture: "Three isolated edits; no structural change."
  components:
    - name: "SplashScreen.__init__"
      type: "function"
      purpose: "Populate _version_text from installed package metadata."
      logic:
        - "Replace the line `self._version_text = 'v1.0.0'  # Placeholder version` with the block in deliverable file 1a."

    - name: "SplashScreen._render_graphics"
      type: "function"
      purpose: "Display version text in automotive mode."
      logic:
        - "In the automotive else-branch, after `self._draw_progress_indicator(surface, center_x, center_y + 20)` and before `self._draw_border(surface, width, height)`, insert the call in deliverable file 1b."

    - name: "parse_arguments"
      type: "function"
      purpose: "Return correct installed version from --version."
      logic:
        - "Replace the --version add_argument line with the block in deliverable file 2."

  dependencies:
    internal: []
    external:
      - "importlib.metadata (stdlib, Python 3.8+)"

deliverable:
  format_requirements:
    - "Edit both files in place."
  files:
    - path: "src/gtach/display/splash.py"
      content: |
        EDIT 1a — in SplashScreen.__init__:

        Replace:
            self._version_text = "v1.0.0"  # Placeholder version

        With:
            try:
                from importlib.metadata import version as _pkg_version
                self._version_text = f"v{_pkg_version('gtach')}"
            except Exception:
                self._version_text = "v?.?.?"

        EDIT 1b — in SplashScreen._render_graphics, automotive else-branch:

        After:
                self._draw_progress_indicator(surface, center_x, center_y + 20)

        Insert:
                self._draw_version_text(surface, center_x, center_y + 110)

        The line `self._draw_border(surface, width, height)` must remain as the
        final call in the automotive branch.

    - path: "src/gtach/main.py"
      content: |
        EDIT 2 — in parse_arguments():

        Replace:
            parser.add_argument('--version', action='version', version='GTach 0.2.0')

        With:
            try:
                from importlib.metadata import version as _pkg_version
                _ver = f'GTach {_pkg_version("gtach")}'
            except Exception:
                _ver = 'GTach'
            parser.add_argument('--version', action='version', version=_ver)

success_criteria:
  - "python -m py_compile src/gtach/display/splash.py passes."
  - "python -m py_compile src/gtach/main.py passes."
  - "SplashScreen.__init__ no longer contains the literal 'v1.0.0'."
  - "_render_graphics automotive else-branch calls _draw_version_text at center_y + 110."
  - "parse_arguments --version no longer contains the literal '0.2.0'."

notes: >
  Executor is Claude Code (no AEL). Invoke from the project root:
  implement workspace/prompt/prompt-55c879fd-splash-version-display.md
```

```yaml
tactical_brief: |
  Executor: Claude Code. Implement change-55c879fd: installed version on splash
  and fixed --version. Three edits only.

  FILE 1: src/gtach/display/splash.py

  Edit 1a — SplashScreen.__init__:
  Replace:
      self._version_text = "v1.0.0"  # Placeholder version
  With:
      try:
          from importlib.metadata import version as _pkg_version
          self._version_text = f"v{_pkg_version('gtach')}"
      except Exception:
          self._version_text = "v?.?.?"

  Edit 1b — SplashScreen._render_graphics, automotive else-branch:
  After:
          self._draw_progress_indicator(surface, center_x, center_y + 20)
  Insert:
          self._draw_version_text(surface, center_x, center_y + 110)
  _draw_border must remain the last call in the automotive branch.

  FILE 2: src/gtach/main.py

  Edit 2 — parse_arguments():
  Replace:
      parser.add_argument('--version', action='version', version='GTach 0.2.0')
  With:
      try:
          from importlib.metadata import version as _pkg_version
          _ver = f'GTach {_pkg_version("gtach")}'
      except Exception:
          _ver = 'GTach'
      parser.add_argument('--version', action='version', version=_ver)

  Verify: python -m py_compile src/gtach/display/splash.py &&
          python -m py_compile src/gtach/main.py
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-12 | Initial prompt document. |

---

Copyright (c) 2026 William Watson. MIT License.
