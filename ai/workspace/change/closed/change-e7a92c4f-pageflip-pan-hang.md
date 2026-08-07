Created: 2026 August 07

# Change: Present the Page-Flip Pan Immediately, Not on the Next Vblank

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-e7a92c4f"
  title: "Present the page-flip pan immediately, not on the next vblank"
  date: "2026-08-07"
  author: "William Watson"
  status: "verified"
  priority: "critical"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-e7a92c4f"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-e7a92c4f"
  description: >
    The display thread hangs indefinitely inside _pan_display's
    FBIOPAN_DISPLAY ioctl roughly 15 seconds into a session, silencing
    the watchdog heartbeat and causing an application shutdown 439
    seconds later that the operator experiences as a blank, unrecovered
    screen.

scope:
  summary: >
    Change _pan_display's activation flag from FB_ACTIVATE_VBL to
    FB_ACTIVATE_NOW, and add a DEBUG-guarded log bracket around the
    ioctl call so a recurrence would pinpoint it with certainty.
  affected_components:
    - name: "DisplayRenderingEngine._pan_display"
      file_path: "src/gtach/display/rendering/engine.py"
      change_type: "modify"
  affected_designs: []
  out_of_scope:
    - "Changing FB_ACTIVATE_VBL's use, if any, outside _pan_display — there is none; it is used only here."
    - "Adding a bounded-wait or timeout wrapper around framebuffer ioctls generally. This change removes the one call site with a known indefinite-block risk rather than building general infrastructure for a risk that is not otherwise present in this file."
    - "Any change to _setup_page_flip, _wait_for_vsync, write_to_framebuffer's branching logic, or cleanup. Only _pan_display's activation flag and its logging change."
    - "Re-verifying issue-49b21ace's own outstanding on-target steps. Left open, tracked separately."

rational:
  problem_statement: >
    _pan_display asks the driver to defer the pan to the next
    vertical-blanking interval (FB_ACTIVATE_VBL). The fbdev API does not
    guarantee this ioctl returns before that interval arrives; on a
    driver that blocks synchronously for it, and where the interrupt
    the driver is waiting on does not reliably fire on this panel's
    legacy DPI configuration, the call blocks forever. Nothing in the
    calling thread can detect or recover from that block, and the
    watchdog's eventual timeout takes 439 seconds — an unusable recovery
    time for an instrument in a moving vehicle.
  proposed_solution: >
    Use FB_ACTIVATE_NOW (apply immediately) instead of FB_ACTIVATE_VBL.
    _pan_display's own docstring already states no synchronisation wait
    is needed here, because nothing reads the off-screen half being
    panned to — page flipping's entire correctness argument rests on
    that fact. FB_ACTIVATE_NOW asks for exactly the behaviour the design
    already relies on and removes the one ioctl in the frame path with a
    plausible unbounded-block characteristic.
  alternatives_considered:
    - option: "Wrap FBIOPAN_DISPLAY in a bounded-wait mechanism (a watchdog timer, a companion thread, or an alarm signal) that can interrupt a stuck ioctl."
      reason_rejected: >
        Materially more complex for a driver-level problem that
        FB_ACTIVATE_NOW plausibly removes outright. Introducing signal-
        or thread-based ioctl cancellation carries its own correctness
        risk (an interrupted ioctl can leave driver state
        inconsistent) and is not justified until FB_ACTIVATE_NOW is
        shown insufficient.
    - option: "Disable page-flip mode entirely and fall back to the vsync-wait or unsynchronised write path."
      reason_rejected: >
        Discards the tear-free presentation page flipping exists to
        provide, for a problem that appears to be one flag value on one
        ioctl call, not a fault in the page-flip mechanism as a whole.
    - option: "Leave FB_ACTIVATE_VBL and add only the diagnostic log bracket, deferring the fix until the hang is directly observed to originate there."
      reason_rejected: >
        The design's own stated rationale already establishes
        FB_ACTIVATE_VBL provides no benefit this code path needs;
        there is no reason to accept its risk for another verification
        cycle when the lower-risk value is available now. The log
        bracket is retained regardless, as a safety net if this
        hypothesis is wrong.
  benefits:
    - "Removes the one ioctl in the per-frame write path with a plausible indefinite-block characteristic."
    - "Matches the code's own documented correctness rationale exactly — FB_ACTIVATE_NOW is not a workaround but the value the existing design argument already implies."
    - "The diagnostic log bracket makes any recurrence immediately attributable, rather than requiring another multi-session log-correlation exercise."
  risks:
    - risk: "FB_ACTIVATE_NOW could reintroduce a visible tear if this driver's immediate-apply path does not itself wait for blanking internally."
      mitigation: >
        Not expected: FB_ACTIVATE_NOW simply omits the request to defer
        to vblank; it does not disable any tear-avoidance the driver
        performs by default. If a tear does appear, it is a distinct,
        separately observable defect from the hang this change targets,
        and issue-49b21ace's degradation chain remains available to
        address it.
    - risk: "The root cause may not be FB_ACTIVATE_VBL at all, and the hang recurs unchanged."
      mitigation: >
        The added log bracket makes this outcome immediately legible on
        the next occurrence — entry logged with no matching exit
        pinpoints the ioctl precisely, either confirming this change's
        premise or ruling it out and redirecting the investigation to
        the next candidate in write_to_framebuffer's remaining logic.

technical_details:
  current_behavior: >
    _pan_display sets fb_var_screeninfo.activate to FB_ACTIVATE_VBL (16)
    before issuing FBIOPAN_DISPLAY. This can block the calling thread
    indefinitely on drivers that implement VBL activation synchronously,
    with no caller-side detection or recovery.
  proposed_behavior: >
    _pan_display sets fb_var_screeninfo.activate to FB_ACTIVATE_NOW (0).
    The pan is requested to apply immediately rather than deferred to
    the next vblank. A DEBUG-guarded log line brackets the FBIOPAN_DISPLAY
    call (entry and exit), using the same isEnabledFor(logging.DEBUG)
    guard pattern already used elsewhere in this file, so the addition
    costs nothing when debug logging is off.
  implementation_approach: >
    Single-constant change plus a logging addition, confined entirely to
    _pan_display in src/gtach/display/rendering/engine.py. No signature,
    call-site, or control-flow change.
  code_changes:
    - component: "DisplayRenderingEngine._pan_display"
      file: "src/gtach/display/rendering/engine.py"
      change_summary: >
        var[FB_VAR_ACTIVATE] = FB_ACTIVATE_VBL becomes
        var[FB_VAR_ACTIVATE] = FB_ACTIVATE_NOW. The comment explaining
        the flag is rewritten to describe why NOW is used, replacing
        the previous VBL rationale. A DEBUG-guarded log line is added
        immediately before and after the fcntl.ioctl(..., FBIOPAN_DISPLAY, ...)
        call.
      functions_affected:
        - "_pan_display"
      classes_affected:
        - "DisplayRenderingEngine"
  data_changes: []
  interface_changes: []

dependencies:
  internal:
    - component: "DisplayManager._display_loop"
      impact: >
        None directly — call site and return contract of write_to_framebuffer
        and _pan_display are unchanged. The dependency is behavioural:
        this change is what is expected to let the loop keep returning
        and keep calling update_heartbeat('display') every iteration.
  external: []
  required_changes: []

testing_requirements:
  test_approach: >
    Off-target: confirm the constant change and log bracket are present
    and syntactically correct, and that no existing test asserts the old
    FB_ACTIVATE_VBL value. On-target: extended-duration run per
    issue-e7a92c4f's verification_enhanced steps — this defect's
    mechanism (a driver-level blocking ioctl) cannot be reproduced or
    disproven off-target, as issue-49b21ace's own emulated-driver tests
    already noted for the related page-flip work.
  test_cases:
    - scenario: "pytest tests/ against the modified file."
      expected_result: "No new failures. No existing test references FB_ACTIVATE_VBL by value in a way this change would break."
    - scenario: "grep for FB_ACTIVATE_VBL in engine.py after the change."
      expected_result: "No remaining reference within _pan_display; the constant definition itself may remain unused or be removed per the prompt's literal instruction."
  regression_scope:
    - "src/gtach/display/rendering/engine.py — _pan_display only."
  validation_criteria:
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."
    - "The 30-minute on-target run in issue-e7a92c4f's verification_enhanced completes with no WatchdogMonitor timeout."

implementation:
  effort_estimate: ""
  implementation_steps:
    - step: "Apply the single-file edit via prompt-e7a92c4f."
      owner: "Claude Code"
    - step: "Deploy to gtach.local and run the extended on-target verification."
      owner: "William Watson"
  rollback_procedure: >
    Revert the one-line constant change (FB_ACTIVATE_NOW back to
    FB_ACTIVATE_VBL) and remove the log bracket. No other file or state
    is touched.
  deployment_notes: >
    Standard build/deploy path (bin/build.sh, bin/deploy.sh or
    bin/install.sh). No new dependency, no systemd or boot-configuration
    change.

verification:
  implemented_date: "2026-08-07"
  implemented_by: "Claude Code, per prompt-e7a92c4f"
  verification_date: "2026-08-07"
  verified_by: "William Watson"
  test_results: >
    Confirmed on-target via direct log analysis of a gtach.local session
    (bin/pull_logs.sh, 2026-08-07 07:05:42 onward, page-flip mode active
    per start.log): zero WatchdogMonitor WARNING/ERROR/CRITICAL lines;
    38,373 pan-bracket entries and 38,373 exits, exactly paired — no
    hang occurred. Two further sessions across two reboots observed
    directly by the operator, reported normal, without a log capture.
    Full account: report v0.4.0-e7a92c4f-pageflip-pan-hang.md §7; same
    evidence recorded in issue-e7a92c4f verification.
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-49b21ace"
      relationship: "modifies code change-49b21ace introduced"
  related_issues:
    - issue_ref: "issue-e7a92c4f"
      relationship: "resolves"
    - issue_ref: "issue-49b21ace"
      relationship: "related"

notes: >
  Executor is Claude Code; AEL is not used, per explicit instruction.
  See prompt-e7a92c4f.

version_history:
  - version: "1.0"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-e7a92c4f."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status approved -> verified. Implementation and verification recorded per report v0.4.0-e7a92c4f-pageflip-pan-hang.md §7. Closing per P00 §1.1.14.4."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-07 | Initial change document coupled to issue-e7a92c4f. |
| 1.1 | 2026-08-07 | Verified and closed — on-target log evidence confirms the fix. |

---

Copyright (c) 2026 William Watson. MIT License.
