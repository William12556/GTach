Created: 2026 June 11

```yaml
prompt_info:
  id: "prompt-1f4754d3"
  task_type: "code_generation"
  source_ref: "change-1f4754d3"
  date: "2026-06-11"
  iteration: 1
  coupled_docs:
    change_ref: "change-1f4754d3"
    change_iteration: 1

context:
  purpose: >
    Deliver auto-start on boot plus a supervised, recoverable on-device update
    path executed before the application launches.
  integration: >
    Two new deploy files in the repo root (gtach.service, gtach-preflight.sh),
    a Linux-branch extension to install.sh, and one guarded method in
    GTachApplication. Executor: Claude Code (no AEL).
  constraints:
    - "Preflight must always exit 0; ExecStartPre uses the '-' prefix."
    - "Boot-time install must be non-interactive: venv pip, --force-reinstall --no-deps, no sudo, no network."
    - "Do not modify the application's display, transport, or config logic."
    - "app.py change is limited to one new method and one call site at the end of start()."
    - "Assume install.sh runs as root on the Pi (existing deploy convention)."

specification:
  description: >
    Create the systemd unit and boot supervisor, register them via install.sh,
    and add the Tier 2 health signal that clears the probation marker on healthy
    startup.
  requirements:
    functional:
      - "gtach starts on boot via systemd."
      - "A staged, marked wheel is validated and installed before launch."
      - "A wheel that fails to reach healthy startup is rolled back to previous.whl after threshold attempts."
      - "A corrupt wheel is rejected without affecting the running install."
      - "The application removes /opt/gtach/.update-probation on successful startup."
    technical:
      language: "Python / Bash / systemd unit"
      version: "Python 3.11"
      standards:
        - "Tolerant error handling in the application hook (never raise)."
        - "Preflight robust to missing files and malformed marker contents."

design:
  architecture: >
    Supervisor/application split. systemd runs the preflight (install + rollback)
    before launching the app. The app signals health by clearing the probation
    marker. Probation threshold 2 sits below StartLimitBurst 3 so rollback fires
    before systemd abandons the unit.
  components:
    - name: "gtach.service"
      type: "module"
      purpose: "systemd unit: auto-start with boot-time preflight."
      logic:
        - "Create file gtach.service in the repo root with the exact content in deliverable file 1."
    - name: "gtach-preflight.sh"
      type: "module"
      purpose: "Boot hook: rollback then pending install. Always exits 0."
      logic:
        - "Create file gtach-preflight.sh in the repo root with the exact content in deliverable file 2."
        - "Make it executable (the install.sh step installs it with mode 0755 on the Pi)."
    - name: "install.sh"
      type: "module"
      purpose: "Register the unit and preflight, seed the wheel, enable the service."
      logic:
        - "Within the existing 'if [ \"$OS\" = \"Linux\" ]; then' post-install block, before the 'Run gtach with:' echo, insert the registration block in deliverable file 3."
        - "Do not alter the macOS branch or any other logic."
    - name: "GTachApplication._clear_update_probation"
      type: "function"
      purpose: "Clear the probation marker on healthy startup (Linux deploy only)."
      logic:
        - "Add the method in deliverable file 4 to the GTachApplication class, placed immediately after start()."
        - "Call self._clear_update_probation() as the final statement of the start() try block, after the mode-dispatch if/elif/else and before 'except Exception as e:'."
  dependencies:
    internal:
      - "src/gtach/app.py — GTachApplication.start"
    external:
      - "systemd; pip in /opt/gtach/venv"

error_handling:
  strategy: >
    Preflight isolates every fallible step and always exits 0. The application
    hook swallows all exceptions and logs at debug level.
  logging:
    level: "INFO"
    format: "existing application logging; preflight logs to stdout (journald)"

testing:
  unit_tests: []
  edge_cases:
    - "No pending marker, no probation marker: preflight is a no-op."
    - "Malformed probation contents: treated as 0."
    - "Pending marker present but wheel file missing: logged, marker cleared."
    - "Corrupt wheel: rejected on zip validation; install unchanged."
  validation:
    - "systemctl enable gtach succeeds; unit starts on reboot."
    - "Healthy update clears the probation marker on first good startup."
    - "Crash-looping update reverts to previous.whl."

deliverable:
  format_requirements:
    - "Create the two new files verbatim; edit install.sh and app.py in place."
  files:
    - path: "gtach.service"
      content: |
        [Unit]
        Description=GTach OBD-II Tachometer
        After=multi-user.target bluetooth.service
        StartLimitIntervalSec=60
        StartLimitBurst=3

        [Service]
        Type=simple
        User=root
        WorkingDirectory=/opt/gtach
        ExecStartPre=-/opt/gtach/gtach-preflight.sh
        ExecStart=/opt/gtach/venv/bin/gtach
        Restart=on-failure
        RestartSec=5

        [Install]
        WantedBy=multi-user.target
    - path: "gtach-preflight.sh"
      content: |
        #!/bin/bash
        # gtach-preflight.sh — systemd ExecStartPre hook (runs as root). Always exits 0.
        # Tier 2 rollback then pending-wheel install, before the application launches.

        INSTALL_DIR="/opt/gtach"
        UPDATES_DIR="$INSTALL_DIR/updates"
        VENV="$INSTALL_DIR/venv"
        PENDING="$UPDATES_DIR/.install-pending"
        PROBATION="$INSTALL_DIR/.update-probation"
        INSTALLED="$INSTALL_DIR/installed.whl"
        PREVIOUS="$INSTALL_DIR/previous.whl"
        THRESHOLD=2

        log() { echo "[gtach-preflight] $*"; }

        install_wheel() {
            # Dedicated non-interactive path: no sudo, no prompts, no network.
            "$VENV/bin/pip" install --force-reinstall --no-deps "$1" >/dev/null 2>&1
        }

        valid_wheel() {
            "$VENV/bin/python" - "$1" <<'PY' 2>/dev/null
        import sys, zipfile
        p = sys.argv[1]
        sys.exit(0 if zipfile.is_zipfile(p) and zipfile.ZipFile(p).testzip() is None else 1)
        PY
        }

        # Step 1 — rollback check
        if [ -f "$PROBATION" ]; then
            count="$(cat "$PROBATION" 2>/dev/null)"
            case "$count" in (''|*[!0-9]*) count=0;; esac
            if [ "$count" -ge "$THRESHOLD" ]; then
                log "probation exceeded ($count) — rolling back"
                if [ -f "$PREVIOUS" ] && install_wheel "$PREVIOUS"; then
                    cp -f "$PREVIOUS" "$INSTALLED"
                    log "rolled back to previous wheel"
                else
                    log "ERROR: rollback unavailable or failed"
                fi
                rm -f "$PROBATION"
                exit 0
            fi
            echo "$((count + 1))" > "$PROBATION"
            log "probation attempt $((count + 1))"
        fi

        # Step 2 — pending install
        if [ -f "$PENDING" ]; then
            wheel_name="$(cat "$PENDING" 2>/dev/null)"
            wheel_path="$UPDATES_DIR/$wheel_name"
            if [ -n "$wheel_name" ] && [ -f "$wheel_path" ]; then
                if valid_wheel "$wheel_path"; then
                    [ -f "$INSTALLED" ] && cp -f "$INSTALLED" "$PREVIOUS"
                    if install_wheel "$wheel_path"; then
                        cp -f "$wheel_path" "$INSTALLED"
                        echo 0 > "$PROBATION"
                        log "installed $wheel_name; probation started"
                    else
                        log "ERROR: install failed — restoring previous"
                        [ -f "$PREVIOUS" ] && install_wheel "$PREVIOUS" && cp -f "$PREVIOUS" "$INSTALLED"
                    fi
                else
                    log "ERROR: $wheel_name failed zip validation — skipping"
                fi
                rm -f "$wheel_path"
            else
                log "pending marker present but wheel missing"
            fi
            rm -f "$PENDING"
        fi

        exit 0
    - path: "install.sh"
      content: |
        Insert the following block inside the existing `if [ "$OS" = "Linux" ]; then`
        post-install section, BEFORE the `echo "Run gtach with:"` line. Leave the
        macOS branch and all other logic unchanged:

            # ---- systemd service + boot-time update supervisor ----
            SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
            echo "==> Registering systemd service and update supervisor"
            install -m 0644 "$SCRIPT_DIR/gtach.service" /etc/systemd/system/gtach.service
            install -m 0755 "$SCRIPT_DIR/gtach-preflight.sh" "$INSTALL_DIR/gtach-preflight.sh"
            mkdir -p "$INSTALL_DIR/updates"
            cp -f "$WHEEL_PATH" "$INSTALL_DIR/installed.whl"
            systemctl daemon-reload
            systemctl enable gtach
            echo "    Service 'gtach' enabled. Start now with: systemctl start gtach"
    - path: "src/gtach/app.py"
      content: |
        1. In GTachApplication.start(), insert this call as the final statement of
           the try block, immediately after the mode-dispatch if/elif/else and
           before `except Exception as e:`:

               self._clear_update_probation()

        2. Add this method to GTachApplication, immediately after start():

            def _clear_update_probation(self) -> None:
                """Remove the update-probation marker on healthy startup.

                Signals the boot-time supervisor that the current install reached
                successful startup, so a newly applied wheel is not rolled back.
                Linux deployment only; tolerant of all errors.
                """
                try:
                    import os
                    import sys
                    if sys.platform.startswith('linux'):
                        marker = "/opt/gtach/.update-probation"
                        if os.path.exists(marker):
                            os.remove(marker)
                            self.logger.info("Cleared update probation marker — startup healthy")
                except Exception as e:
                    self.logger.debug(f"Could not clear probation marker: {e}")

success_criteria:
  - "gtach.service and gtach-preflight.sh exist in the repo root with the specified content."
  - "install.sh Linux branch registers the unit, installs the preflight (0755), creates updates/, seeds installed.whl, daemon-reload, enables gtach."
  - "app.py defines _clear_update_probation() and calls it at the end of start()'s try block."
  - "No other application logic is modified."
  - "Bash syntax valid: bash -n gtach-preflight.sh and bash -n install.sh pass."

notes: >
  Executor is Claude Code (no AEL). Invoke from the project root:
  implement workspace/prompt/prompt-1f4754d3-systemd-autostart-update.md
```

```yaml
tactical_brief: |
  Executor: Claude Code. Implement four changes for change-1f4754d3 (systemd
  auto-start + Tier 2 update rollback). Use the exact content in §deliverable.

  NEW FILE 1: gtach.service (repo root) — systemd unit. Verbatim from deliverable
  file "gtach.service". Key fields: After=multi-user.target bluetooth.service;
  StartLimitIntervalSec=60; StartLimitBurst=3; User=root;
  WorkingDirectory=/opt/gtach; ExecStartPre=-/opt/gtach/gtach-preflight.sh;
  ExecStart=/opt/gtach/venv/bin/gtach; Restart=on-failure; RestartSec=5;
  WantedBy=multi-user.target.

  NEW FILE 2: gtach-preflight.sh (repo root) — verbatim from deliverable file
  "gtach-preflight.sh". Always exits 0. Step 1 rollback: if /opt/gtach/.update-probation
  >= 2, reinstall previous.whl and exit; else increment. Step 2 install: if
  /opt/gtach/updates/.install-pending present, validate zip, copy installed.whl
  -> previous.whl, pip install --force-reinstall --no-deps the staged wheel, on
  success set installed.whl and probation=0, on failure restore previous; always
  clear marker and staged wheel. Verify: bash -n gtach-preflight.sh.

  EDIT install.sh: inside the existing `if [ "$OS" = "Linux" ]; then` post-install
  block, before `echo "Run gtach with:"`, insert the registration block from
  deliverable file "install.sh" (install unit to /etc/systemd/system/, preflight
  to /opt/gtach/ at 0755, mkdir updates/, cp wheel to installed.whl,
  daemon-reload, enable gtach). Do not touch the macOS branch. Verify: bash -n install.sh.

  EDIT src/gtach/app.py: add method _clear_update_probation() (verbatim from
  deliverable file "src/gtach/app.py") immediately after start(), and call
  self._clear_update_probation() as the last statement of the start() try block,
  before `except Exception as e:`. No other changes.
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-11 | Initial prompt document. |

---

Copyright (c) 2026 William Watson. MIT License.
