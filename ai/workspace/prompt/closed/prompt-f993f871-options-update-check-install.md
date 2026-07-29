Created: 2026 June 12

```yaml
prompt_info:
  id: "prompt-f993f871"
  task_type: "code_generation"
  source_ref: "change-f993f871"
  date: "2026-06-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-f993f871"
    change_iteration: 1

context:
  purpose: >
    Add the operator-facing update flow: check for a staged wheel, confirm,
    write the install marker, and restart so the supervisor installs it.
  integration: >
    Four files: new src/gtach/utils/updater.py; modify src/gtach/display/manager.py,
    src/gtach/app.py, and gtach.service. Executor: Claude Code (no AEL).
  constraints:
    - "updater.py must be pure (no pygame, no display imports); only stdlib."
    - "Newer-only: offer a wheel only if its version tuple is strictly greater than installed."
    - "Validate zip integrity before offering a wheel."
    - "The check must run on thread_manager.worker_pool, never inline on the display thread."
    - "Do not change the three existing OPTIONS buttons' behaviour."
    - "Do not add a new DisplayMode; use the _options_view sub-state."
    - "Do not modify gtach-preflight.sh or install.sh."

specification:
  description: "New helper module, OPTIONS sub-state machine, restart callback, unit Restart change."
  requirements:
    functional:
      - "Check scans /opt/gtach/updates/ for the newest valid wheel strictly newer than installed."
      - "Available state offers Install/Cancel; none/error offers Back; pending shows 'Installing on restart…'."
      - "Install writes /opt/gtach/updates/.install-pending and requests a clean restart."
      - "gtach.service relaunches on clean exit (Restart=always)."
    technical:
      language: "Python / systemd unit"
      version: "Python 3.11"
      standards:
        - "Tolerant error handling; no new dependencies."

design:
  architecture: "Pure helper + OPTIONS sub-state machine + app restart callback."
  components:
    - name: "updater"
      type: "module"
      purpose: "Scan, parse, validate, find-available, stage-pending."
      logic:
        - "Create src/gtach/utils/updater.py verbatim from deliverable file 1."
    - name: "DisplayManager"
      type: "class"
      purpose: "OPTIONS menu/update sub-views and handlers."
      logic:
        - "Apply edits 2a–2e from deliverable file 2."
    - name: "GTachApplication"
      type: "class"
      purpose: "Restart request callback."
      logic:
        - "Apply edits 3a–3b from deliverable file 3."
    - name: "gtach.service"
      type: "module"
      purpose: "Relaunch on clean exit."
      logic:
        - "Apply edit 4 from deliverable file 4."
  dependencies:
    internal:
      - "gtach-preflight.sh consumes the marker (already deployed)."

deliverable:
  format_requirements:
    - "Create one file; edit three in place."
  files:
    - path: "src/gtach/utils/updater.py"
      content: |
        #!/usr/bin/env python3
        # Copyright (c) 2026 William Watson
        #
        # This file is part of GTach.
        #
        # GTach is licensed under the MIT License.
        # See the LICENSE file in the project root for full license text.

        """Update discovery helpers for the OPTIONS update screen.

        Pure filesystem logic: scan the drop directory for a wheel strictly newer
        than the installed version, validate zip integrity, and stage the pending
        install marker consumed by gtach-preflight.sh. No display dependencies.
        """

        import logging
        import os
        import zipfile
        from typing import Optional, Tuple

        logger = logging.getLogger(__name__)

        UPDATES_DIR = "/opt/gtach/updates"
        PENDING_MARKER = os.path.join(UPDATES_DIR, ".install-pending")


        def _parse_version_str(s: str) -> Optional[Tuple[int, ...]]:
            try:
                return tuple(int(p) for p in s.strip().split("."))
            except (ValueError, AttributeError):
                return None


        def get_installed_version() -> Optional[Tuple[int, ...]]:
            """Installed wheel version as an int tuple, or None."""
            try:
                from importlib.metadata import version as _pkg_version
                return _parse_version_str(_pkg_version("gtach"))
            except Exception:
                return None


        def parse_wheel_version(filename: str) -> Optional[Tuple[int, ...]]:
            """Extract the version tuple from a wheel filename.

            e.g. 'gtach-0.2.61-py3-none-any.whl' -> (0, 2, 61).
            """
            parts = filename.split("-")
            if len(parts) < 2:
                return None
            return _parse_version_str(parts[1])


        def validate_wheel(path: str) -> bool:
            """True if the file is a complete, readable zip (wheel)."""
            try:
                if not zipfile.is_zipfile(path):
                    return False
                with zipfile.ZipFile(path) as zf:
                    return zf.testzip() is None
            except Exception:
                return False


        def find_available_update() -> Optional[Tuple[str, str]]:
            """Return (filename, version_str) of the newest valid wheel strictly
            newer than the installed version, or None.
            """
            try:
                installed = get_installed_version()
                if installed is None:
                    return None
                if not os.path.isdir(UPDATES_DIR):
                    return None
                best = None  # (version_tuple, filename, raw_version_str)
                for name in os.listdir(UPDATES_DIR):
                    if not name.endswith(".whl"):
                        continue
                    ver = parse_wheel_version(name)
                    if ver is None or ver <= installed:
                        continue
                    if not validate_wheel(os.path.join(UPDATES_DIR, name)):
                        logger.warning(f"Skipping invalid wheel: {name}")
                        continue
                    raw = name.split("-")[1]
                    if best is None or ver > best[0]:
                        best = (ver, name, raw)
                if best is None:
                    return None
                return (best[1], best[2])
            except Exception as e:
                logger.error(f"Update scan error: {e}", exc_info=True)
                return None


        def stage_pending(filename: str) -> bool:
            """Write the install-pending marker for the boot-time supervisor."""
            try:
                os.makedirs(UPDATES_DIR, exist_ok=True)
                with open(PENDING_MARKER, "w", encoding="utf-8") as f:
                    f.write(filename)
                logger.info(f"Staged pending install: {filename}")
                return True
            except Exception as e:
                logger.error(f"Failed to stage pending install: {e}", exc_info=True)
                return False

    - path: "src/gtach/display/manager.py"
      content: |
        EDIT 2a — DisplayManager.__init__, after:
            self._debug_logging_on = False      # Reflects current debug logging state
        add:
            self._restart_callback = None       # Set by app.py: Callable[[], None]
            self._options_view = 'menu'         # 'menu' | 'update'
            self._update_status = 'idle'        # checking|available|none|error|pending
            self._update_wheel = None
            self._update_version = None

        EDIT 2b — _handle_long_press, in the else branch that enters options mode,
        replace:
            else:
                # Enter options mode
                self.config.mode = DisplayMode.OPTIONS
                return TouchAction.NAVIGATION
        with:
            else:
                # Enter options mode
                self._options_view = 'menu'
                self.config.mode = DisplayMode.OPTIONS
                return TouchAction.NAVIGATION

        EDIT 2c — replace the ENTIRE existing _draw_options_mode method (from its
        'def _draw_options_mode(self) -> None:' line through its final
        'except Exception as e:\n            self.logger.error(f"Options display error: {e}")')
        with the following three methods:

            def _draw_options_mode(self) -> None:
                """Draw options interface — menu or update sub-view."""
                try:
                    if self._options_view == 'update':
                        self._draw_update_view()
                    else:
                        self._draw_options_menu()
                except Exception as e:
                    self.logger.error(f"Options display error: {e}")

            def _draw_options_menu(self) -> None:
                """Draw the options menu with four tappable items."""
                self.touch_coordinator.clear_regions()
                self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER, (40, 40, 50))
                self._draw_shift_border((200, 0, 0))

                font = get_title_display_font()
                if font:
                    self.rendering_engine.render_text(
                        RenderTarget.BACK_BUFFER, "Options", font,
                        (255, 255, 255), (240, 55), center=True
                    )

                button_width = 300
                button_height = 55
                center_x = 240
                clear_btn_y = 92
                sim_btn_y = 157
                debug_btn_y = 222
                update_btn_y = 287

                self._options_btn_clear = pygame.Rect(center_x - button_width // 2, clear_btn_y, button_width, button_height)
                self._options_btn_sim = pygame.Rect(center_x - button_width // 2, sim_btn_y, button_width, button_height)
                self._options_btn_debug = pygame.Rect(center_x - button_width // 2, debug_btn_y, button_width, button_height)
                self._options_btn_update = pygame.Rect(center_x - button_width // 2, update_btn_y, button_width, button_height)

                for _btn in (self._options_btn_clear, self._options_btn_sim, self._options_btn_debug, self._options_btn_update):
                    self.rendering_engine.draw_rect(
                        RenderTarget.BACK_BUFFER, (80, 80, 100),
                        (_btn.x, _btn.y, _btn.width, _btn.height)
                    )

                button_font = self._get_cached_font(26)
                if button_font:
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, "Clear settings", button_font, (255, 255, 255), (center_x, clear_btn_y + button_height // 2), center=True)
                    sim_label = "Simulation mode" if self._sim_mode else "Bluetooth"
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, sim_label, button_font, (255, 255, 255), (center_x, sim_btn_y + button_height // 2), center=True)
                    debug_label = "Debug: On" if self._debug_logging_on else "Debug: Off"
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, debug_label, button_font, (255, 255, 255), (center_x, debug_btn_y + button_height // 2), center=True)
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, "Check for updates", button_font, (255, 255, 255), (center_x, update_btn_y + button_height // 2), center=True)

                self.touch_coordinator.register_button_region("clear_settings", self._options_btn_clear, TouchAction.SETTINGS_CHANGE, lambda pos: self._on_clear_settings())
                self.touch_coordinator.register_button_region("simulation_mode", self._options_btn_sim, TouchAction.SETTINGS_CHANGE, lambda pos: self._on_simulation_mode())
                self.touch_coordinator.register_button_region("debug_toggle", self._options_btn_debug, TouchAction.SETTINGS_CHANGE, lambda pos: self._on_debug_toggle())
                self.touch_coordinator.register_button_region("check_updates", self._options_btn_update, TouchAction.SETTINGS_CHANGE, lambda pos: self._on_check_updates())

                small_font = get_label_small_font()
                if small_font:
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, "Long press to return", small_font, (150, 150, 150), (240, 400), center=True)

            def _draw_update_view(self) -> None:
                """Draw the update check / install sub-view."""
                self.touch_coordinator.clear_regions()
                self.rendering_engine.clear_surface(RenderTarget.BACK_BUFFER, (40, 40, 50))
                self._draw_shift_border((200, 0, 0))

                font = get_title_display_font()
                if font:
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, "Update", font, (255, 255, 255), (240, 80), center=True)

                if self._update_status == 'checking':
                    msg = "Checking…"
                elif self._update_status == 'available':
                    msg = f"Available: v{self._update_version}"
                elif self._update_status == 'pending':
                    msg = "Installing on restart…"
                elif self._update_status == 'none':
                    msg = "No update found"
                else:
                    msg = "Check failed"

                status_font = self._get_cached_font(26)
                if status_font:
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, msg, status_font, (255, 255, 255), (240, 180), center=True)

                center_x = 240
                button_width = 280
                button_height = 60
                button_font = self._get_cached_font(26)

                if self._update_status == 'available':
                    install_y = 240
                    cancel_y = 320
                    self._update_btn_install = pygame.Rect(center_x - button_width // 2, install_y, button_width, button_height)
                    self._update_btn_cancel = pygame.Rect(center_x - button_width // 2, cancel_y, button_width, button_height)
                    self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, (0, 120, 0), (self._update_btn_install.x, self._update_btn_install.y, self._update_btn_install.width, self._update_btn_install.height))
                    self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, (80, 80, 100), (self._update_btn_cancel.x, self._update_btn_cancel.y, self._update_btn_cancel.width, self._update_btn_cancel.height))
                    if button_font:
                        self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, "Install", button_font, (255, 255, 255), (center_x, install_y + button_height // 2), center=True)
                        self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, "Cancel", button_font, (255, 255, 255), (center_x, cancel_y + button_height // 2), center=True)
                    self.touch_coordinator.register_button_region("update_install", self._update_btn_install, TouchAction.SETTINGS_CHANGE, lambda pos: self._on_confirm_install())
                    self.touch_coordinator.register_button_region("update_cancel", self._update_btn_cancel, TouchAction.SETTINGS_CHANGE, lambda pos: self._on_cancel_update())
                elif self._update_status in ('none', 'error'):
                    back_y = 300
                    self._update_btn_cancel = pygame.Rect(center_x - button_width // 2, back_y, button_width, button_height)
                    self.rendering_engine.draw_rect(RenderTarget.BACK_BUFFER, (80, 80, 100), (self._update_btn_cancel.x, self._update_btn_cancel.y, self._update_btn_cancel.width, self._update_btn_cancel.height))
                    if button_font:
                        self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, "Back", button_font, (255, 255, 255), (center_x, back_y + button_height // 2), center=True)
                    self.touch_coordinator.register_button_region("update_back", self._update_btn_cancel, TouchAction.SETTINGS_CHANGE, lambda pos: self._on_cancel_update())

                small_font = get_label_small_font()
                if small_font:
                    self.rendering_engine.render_text(RenderTarget.BACK_BUFFER, "Long press to return", small_font, (150, 150, 150), (240, 410), center=True)

        EDIT 2d — add the four handler methods immediately after _on_debug_toggle():

            def _on_check_updates(self) -> None:
                """Enter the update view and start an async check."""
                try:
                    self._options_view = 'update'
                    self._update_status = 'checking'
                    self._update_wheel = None
                    self._update_version = None
                    self.thread_manager.worker_pool.submit(self._run_update_check)
                except Exception as e:
                    self.logger.error(f"Check updates error: {e}", exc_info=True)
                    self._update_status = 'error'

            def _run_update_check(self) -> None:
                """Worker: scan for an available update and set view state."""
                try:
                    from ..utils import updater
                    result = updater.find_available_update()
                    if result is None:
                        self._update_status = 'none'
                    else:
                        self._update_wheel, self._update_version = result
                        self._update_status = 'available'
                except Exception as e:
                    self.logger.error(f"Update check worker error: {e}", exc_info=True)
                    self._update_status = 'error'

            def _on_confirm_install(self) -> None:
                """Stage the pending wheel and request a restart."""
                try:
                    from ..utils import updater
                    if self._update_wheel and updater.stage_pending(self._update_wheel):
                        self._update_status = 'pending'
                        self.logger.info("Update staged — requesting restart")
                        if self._restart_callback is not None:
                            self._restart_callback()
                        else:
                            self.logger.warning("restart_callback not registered")
                    else:
                        self._update_status = 'error'
                except Exception as e:
                    self.logger.error(f"Confirm install error: {e}", exc_info=True)
                    self._update_status = 'error'

            def _on_cancel_update(self) -> None:
                """Return to the options menu."""
                self._options_view = 'menu'
                self._update_status = 'idle'

    - path: "src/gtach/app.py"
      content: |
        EDIT 3a — add this method to GTachApplication, immediately after
        toggle_debug_logging():

            def _request_restart(self) -> None:
                """Request a clean restart; systemd (Restart=always) relaunches,
                and gtach-preflight.sh installs any staged wheel."""
                self.logger.info("Restart requested — stopping for relaunch")
                self._stop_event.set()

        EDIT 3b — at BOTH locations where this line appears (in _start_setup_mode
        and _start_normal_mode):
            self._display._setup_entry_callback = self._re_enter_setup
        add immediately after it (same indentation):
            self._display._restart_callback = self._request_restart

        Note: in _start_setup_mode the callback assignments are inside the
        'if not hasattr(self, "_display") ...' first-creation block, alongside the
        existing _setup_entry_callback / _debug_toggle_callback assignments. Add the
        restart-callback line in the same place at both sites.

    - path: "gtach.service"
      content: |
        EDIT 4 — change the restart policy line:
        Replace:
            Restart=on-failure
        With:
            Restart=always

        Leave RestartSec, StartLimitIntervalSec, StartLimitBurst, and all other
        lines unchanged.

success_criteria:
  - "python -m py_compile src/gtach/utils/updater.py passes."
  - "python -m py_compile src/gtach/display/manager.py passes."
  - "python -m py_compile src/gtach/app.py passes."
  - "updater.py defines get_installed_version, parse_wheel_version, validate_wheel, find_available_update, stage_pending."
  - "_draw_options_mode dispatches to _draw_options_menu / _draw_update_view."
  - "Options menu renders four buttons and registers a 'check_updates' region."
  - "The four update handlers exist; the check is submitted to thread_manager.worker_pool."
  - "app.py defines _request_restart() and sets _restart_callback at both sites."
  - "gtach.service contains Restart=always and no remaining Restart=on-failure."

notes: >
  Executor is Claude Code (no AEL). Invoke from the project root:
  implement workspace/prompt/prompt-f993f871-options-update-check-install.md
```

```yaml
tactical_brief: |
  Executor: Claude Code. Implement change-f993f871: OPTIONS update check/install.
  Four files; use deliverable contents verbatim.

  NEW: src/gtach/utils/updater.py — verbatim from deliverable file
  "src/gtach/utils/updater.py". Pure stdlib helpers: get_installed_version (via
  importlib.metadata), parse_wheel_version, validate_wheel (zipfile), 
  find_available_update (newest valid wheel strictly newer than installed; tuple
  compare), stage_pending (writes /opt/gtach/updates/.install-pending).

  EDIT src/gtach/display/manager.py (deliverable EDITS 2a–2d):
    2a __init__: add _restart_callback=None, _options_view='menu',
       _update_status='idle', _update_wheel=None, _update_version=None after the
       _debug_logging_on line.
    2b _handle_long_press: on entering OPTIONS, set self._options_view='menu'
       before setting self.config.mode = DisplayMode.OPTIONS.
    2c Replace the whole _draw_options_mode with three methods: _draw_options_mode
       (dispatch on _options_view), _draw_options_menu (four buttons at
       y=92/157/222/287, height 55; 4th = "Check for updates" -> _on_check_updates),
       _draw_update_view (state machine: checking/available/none/error/pending with
       Install+Cancel or Back).
    2d Add _on_check_updates (submit _run_update_check to thread_manager.worker_pool),
       _run_update_check (worker; from ..utils import updater; find_available_update),
       _on_confirm_install (updater.stage_pending then self._restart_callback()),
       _on_cancel_update (back to menu) — after _on_debug_toggle().

  EDIT src/gtach/app.py (deliverable EDITS 3a–3b):
    3a Add _request_restart() (sets self._stop_event) after toggle_debug_logging().
    3b At both sites with self._display._setup_entry_callback = self._re_enter_setup,
       add self._display._restart_callback = self._request_restart.

  EDIT gtach.service (deliverable EDIT 4): Restart=on-failure -> Restart=always.

  Verify: python -m py_compile src/gtach/utils/updater.py src/gtach/display/manager.py src/gtach/app.py
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-12 | Initial prompt document. |

---

Copyright (c) 2026 William Watson. MIT License.
