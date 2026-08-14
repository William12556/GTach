Created: 2026 August 14

```yaml
change_info:
  id: "change-4ab5ff88"
  title: "Replace the DISCONNECTED screen's Bluetooth Reset button with a Reset button that reboots the Pi"
  date: "2026-08-14"
  author: "William Watson / Claude"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-4ab5ff88"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-4ab5ff88"
  description: >
    hciconfig hci0 reset frequently fails to restore the Bluetooth link;
    only a reboot of the Pi has proven reliable on target. GTach is a
    single-purpose device, so a reboot from this screen costs the
    operator nothing beyond what the ineffective reset already cost.

scope:
  summary: >
    Remove the Bluetooth-adapter-reset path entirely (button label,
    callback chain, hciconfig logic, its tests) and replace the
    DISCONNECTED screen's second button with "Reset", which reboots the
    Pi via a direct /sbin/reboot call. Preserves the existing invariant
    that exactly one module in GTach is permitted to invoke subprocess,
    by replacing that module's sole responsibility rather than adding a
    second one.
  affected_components:
    - name: "DisplayManager"
      file_path: "src/gtach/display/manager.py"
      change_type: "modify"
    - name: "GTachApplication"
      file_path: "src/gtach/app.py"
      change_type: "modify"
    - name: "bluetooth_reset"
      file_path: "src/gtach/utils/bluetooth_reset.py"
      change_type: "delete"
    - name: "pi_reset"
      file_path: "src/gtach/utils/pi_reset.py"
      change_type: "add"
    - name: "test_bluetooth_reset"
      file_path: "tests/test_bluetooth_reset.py"
      change_type: "delete"
    - name: "test_pi_reset"
      file_path: "tests/test_pi_reset.py"
      change_type: "add"
    - name: "test_disconnected_screen"
      file_path: "tests/test_disconnected_screen.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Any change to the Setup button, spinner, cause-line rendering, or button geometry beyond the label/attribute rename."
    - "Any change to gtach.service (User=root already satisfies the reboot call's privilege requirement)."
    - "Sequencing against change-950128c0 (open, unrelated T-Doc whose regression scope names tests/test_bluetooth_reset.py). That file is deleted here; if change-950128c0 executes afterward, its regression list must be read as tests/test_pi_reset.py. Left to William to sequence."

rational:
  problem_statement: >
    The only operator-facing recovery control on the DISCONNECTED screen
    invokes hciconfig hci0 reset, which frequently leaves the Bluetooth
    adapter down. bluetooth_reset.py's own _DOWN outcome string already
    names the correct remedy ("adapter down - reboot required") without
    the screen offering a way to perform it.
  proposed_solution: >
    Replace the button and its callback chain outright: label "Reset",
    region id "disconnected_reset", callback attribute
    "_reset_callback", dispatching to a worker that calls
    /sbin/reboot directly. No Bluetooth-specific recovery logic remains.
  alternatives_considered:
    - option: "Keep hciconfig reset as a first attempt, falling back to reboot only when it fails."
      reason_rejected: "William confirmed only a reboot is effective in the field; a first-attempt hciconfig step would only delay the outcome that already reliably works."
    - option: "Add a second subprocess-permitted module rather than replacing bluetooth_reset.py."
      reason_rejected: "The Bluetooth-reset code has no remaining caller once replaced, so retaining it as dead code contradicts project minimalism and the existing single-module invariant is best kept by transferring its role, not doubling it."
  benefits:
    - "Operator's one available recovery action reliably restores the link, per field observation."
    - "Removes hciconfig-specific logic (down/up sequencing, adapter-state parsing) with no remaining caller."
    - "Preserves the single-subprocess-module invariant under its correct name."
  risks:
    - risk: "A reboot mid-drive is more disruptive than a failed Bluetooth reset (loses the RADIAL gauge for the full boot cycle, not just a few seconds)."
      mitigation: "The button remains operator-initiated only, exactly as the Bluetooth reset was — no automatic trigger on any wedge diagnosis, retry count, or timer."
    - risk: "/sbin/reboot may not exist at that literal path on all Debian variants."
      mitigation: "Confirmed present on Debian GNU/Linux 11 (Bullseye), the deployed OS. No path-resolution fallback is added, per William's explicit choice of the direct path over systemctl reboot or shutdown -r now."

technical_details:
  current_behavior: >
    DisplayManager._register_disconnected_regions registers
    "disconnected_bt_reset" bound to self._bluetooth_reset_callback,
    drawn as "BT Reset". GTachApplication._on_bluetooth_reset dispatches
    a debounced worker calling bluetooth_reset.reset_adapter()
    (hciconfig hci0 reset, with one hciconfig hci0 up retry), writing
    progress and outcome strings that _disconnected_cause merges onto
    the cause line ahead of the transport's own failure cause.
  proposed_behavior: >
    DisplayManager registers "disconnected_reset" bound to
    self._reset_callback, drawn as "Reset". GTachApplication's handler
    dispatches a debounced worker that calls pi_reset.reboot_device(),
    which invokes /sbin/reboot directly. No outcome string is written
    to the cause line: a successful reboot ends the process before any
    such status could be read, and the debounce alone is sufficient to
    prevent a stacked second invocation.
  implementation_approach: >
    Delete bluetooth_reset.py and its test file; add pi_reset.py
    carrying forward the same "only permitted subprocess module"
    invariant, its accompanying test file mirroring the structural
    assertions of the old one (single call site, no shell=True, minimal
    imports, dispatch off the display thread, no automatic invocation).
    Rename the button's region id, callback attribute, and label in
    manager.py; replace the dispatch method and its wiring in app.py;
    update the two attribute references in test_disconnected_screen.py.
  code_changes:
    - component: "DisplayManager"
      file: "src/gtach/display/manager.py"
      change_summary: >
        Rename _bluetooth_reset_callback -> _reset_callback and
        _disconnected_btn_bt_reset -> _disconnected_btn_reset
        (__init__, _register_disconnected_regions,
        _render_disconnected). Rename region id
        "disconnected_bt_reset" -> "disconnected_reset". Change the
        drawn label "BT Reset" -> "Reset" and remove the now-inapplicable
        comment measuring the abbreviated label against the 240 px
        button (the full word fits; no abbreviation is needed).
      functions_affected:
        - "__init__"
        - "_register_disconnected_regions"
        - "_render_disconnected"
      classes_affected:
        - "DisplayManager"
    - component: "GTachApplication"
      file: "src/gtach/app.py"
      change_summary: >
        Replace _on_bluetooth_reset with a reset dispatch method of the
        same shape (debounce Event, daemon worker thread, not
        registered with ThreadManager) calling pi_reset.reboot_device()
        instead of bluetooth_reset.reset_adapter(). Remove
        _bt_reset_status / _bt_reset_lock and the merge branch in
        _disconnected_cause that reads them — no outcome string exists
        to merge once a successful reboot ends the process before it
        could be shown. Update both wiring sites
        (_start_setup_mode, _start_normal_mode) from
        self._display._bluetooth_reset_callback = self._on_bluetooth_reset
        to self._display._reset_callback = self._on_reset_pi.
      functions_affected:
        - "_on_bluetooth_reset (removed; replaced by _on_reset_pi)"
        - "_disconnected_cause"
        - "_start_setup_mode"
        - "_start_normal_mode"
      classes_affected:
        - "GTachApplication"
    - component: "bluetooth_reset"
      file: "src/gtach/utils/bluetooth_reset.py"
      change_summary: "Delete. No remaining caller after this change."
      functions_affected: []
      classes_affected: []
    - component: "pi_reset"
      file: "src/gtach/utils/pi_reset.py"
      change_summary: >
        New module. Sole remaining subprocess call site in GTach.
        reboot_device() resolves /sbin/reboot (fixed path, no PATH
        search — William's explicit choice), invokes it with no
        arguments and no shell=True, and returns a short outcome string
        on every path (never raises), matching bluetooth_reset.py's
        error-handling shape (TimeoutExpired, PermissionError,
        FileNotFoundError, generic Exception).
      functions_affected:
        - "reboot_device"
      classes_affected: []

dependencies:
  internal:
    - component: "test_disconnected_screen.py"
      impact: >
        Two attribute references (_disconnected_btn_bt_reset,
        _bluetooth_reset_callback) must be renamed to match; both
        currently set the attribute to None in host stand-ins unrelated
        to this change's behaviour, so the rename alone is sufficient.
  external: []
  required_changes:
    - change_ref: "change-950128c0"
      relationship: "related"

testing_requirements:
  test_approach: >
    New tests/test_pi_reset.py mirrors test_bluetooth_reset.py's
    structure: TestRebootDevice (every path returns a short string, none
    raises), TestPrivilegedSurfaceIsContained (subprocess appears only
    in pi_reset.py; exactly one call site, in app.py; no shell=True; no
    systemctl/hciuart/rfkill/module operations; minimal imports),
    TestDispatchIsOffThread (single press returns promptly, worker is a
    daemon, not registered with ThreadManager, second press while in
    flight is ignored, callback performs no blocking call).
    tests/test_disconnected_screen.py updated in place for the renamed
    attributes.
  test_cases:
    - scenario: "reboot_device() succeeds."
      expected_result: "Returns a short non-empty outcome string; subprocess.run called once with ['/sbin/reboot'] and no shell=True."
    - scenario: "reboot_device() times out, raises PermissionError, or raises FileNotFoundError."
      expected_result: "Each returns a distinct short outcome string; none raises out of reboot_device."
    - scenario: "Reset button pressed once."
      expected_result: "Worker thread named for reset dispatch starts; caller returns before the worker completes."
    - scenario: "Reset button pressed twice in rapid succession."
      expected_result: "Second press is ignored while the first is in flight; exactly one worker thread exists."
    - scenario: "_register_disconnected_regions with _reset_callback unset."
      expected_result: "Only 'disconnected_setup' is registered; disconnected_btn_reset is None."
    - scenario: "_register_disconnected_regions with _reset_callback set."
      expected_result: "Both regions registered in order; label drawn is 'Reset'."
    - scenario: "grep -rn subprocess src/ after the change."
      expected_result: "Matches only src/gtach/utils/pi_reset.py."
  regression_scope:
    - "tests/test_disconnected_screen.py"
    - "tests/test_pi_reset.py"
  validation_criteria:
    - "pytest tests/test_pi_reset.py tests/test_disconnected_screen.py passes."
    - "grep -rn 'bluetooth_reset\\|_bluetooth_reset_callback\\|disconnected_bt_reset\\|BT Reset' src/ tests/ returns no matches."
    - "grep -rn 'subprocess' src/ shows matches only in src/gtach/utils/pi_reset.py."

implementation:
  implementation_steps:
    - step: "Author T04 prompt from this change document."
      owner: "Claude (Strategic Domain)"
    - step: "Execute prompt via Claude Code."
      owner: "William Watson"
    - step: "Review implementation against this change document and the design invariant."
      owner: "Claude (Strategic Domain)"
    - step: "Deploy and verify a Reset press reboots the Pi on target."
      owner: "William Watson"
  rollback_procedure: >
    git revert the implementation commit; bluetooth_reset.py and its
    test are restored from history, no data or config migration
    involved.
  deployment_notes: >
    No gtach.service change required (User=root already covers the
    reboot call's privilege requirement).

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-8a63d5f1"
      relationship: "supersedes"
    - change_ref: "change-950128c0"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-4ab5ff88"
      relationship: "resolves"

notes: >
  Scope and design decisions confirmed directly with William: full
  removal of the Bluetooth-adapter-reset path (not a fallback), a new
  dedicated module rather than extending bluetooth_reset.py in place,
  and /sbin/reboot invoked directly rather than via systemctl or
  shutdown.

version_history:
  - version: "1.0"
    date: "2026-08-14"
    author: "William Watson / Claude"
    changes:
      - "Initial change document."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

---

Copyright (c) 2026 William Watson. MIT License.
