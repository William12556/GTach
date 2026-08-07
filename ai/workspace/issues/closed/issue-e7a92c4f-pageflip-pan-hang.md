Created: 2026 August 07

# Issue: Display Thread Hangs Inside the Page-Flip Pan Ioctl

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-e7a92c4f"
  title: "The display thread hangs indefinitely inside the page-flip pan ioctl; the watchdog's eventual shutdown ~7 minutes later appears to the operator as the screen going blank a few seconds after connecting"
  date: "2026-08-07"
  reporter: "William Watson"
  status: "verified"
  severity: "critical"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-e7a92c4f"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: ""
  description: >
    Reported during unrelated bin/ boot-splash work (bin/gtach-boot-splash.service).
    Diagnosed from logs/start.log and logs/debug.log, pulled via bin/pull_logs.sh.
    Not caused by, and independent of, the boot-splash changes.

affected_scope:
  components:
    - name: "DisplayRenderingEngine._pan_display"
      file_path: "src/gtach/display/rendering/engine.py"
    - name: "DisplayRenderingEngine.write_to_framebuffer"
      file_path: "src/gtach/display/rendering/engine.py"
    - name: "DisplayManager._display_loop"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.4.0"

reproduction:
  prerequisites: >
    GTach running on gtach.local with page-flip presentation mode active
    (start.log: "Page flip enabled: two framebuffer halves mapped",
    "Framebuffer presentation mode: page flip").
  steps:
    - "Start gtach.service; let the splash complete and RADIAL mode begin rendering."
    - "Observe the panel for roughly 15 seconds."
    - "Screen output freezes; no further frames are drawn, though systemctl continues reporting the process active (running)."
    - "Wait approximately 7.3 minutes; WatchdogMonitor times out the display thread and initiates a graceful shutdown of the whole application."
  frequency: "always"
  reproducibility_conditions: >
    Observed under page-flip presentation mode only. The vsync-wait and
    unsynchronised-write fallback modes have not been exercised on this
    target, because the page-flip resize is being granted here — contrary
    to issue-49b21ace's own prediction that it would likely be refused.
  preconditions: >
    Legacy DPI fbdev path, dtoverlay=hyperpixel2r, KMS explicitly not used.
    Same preconditions as issue-49b21ace.
  test_data: >
    logs/debug.log, session starting 2026-08-07 05:40:18: steady
    "Radial mode: RPM=..." DEBUG lines approximately every 30ms from
    05:40:18,151 through 05:40:33,400. Nothing further is logged from the
    display thread. At 05:47:52,356 — 439.0s later — WatchdogMonitor logs
    a critical timeout on thread 'display', then on 'obd_protocol', and
    initiates graceful shutdown.

    logs/start.log, same session: "Framebuffer geometry: 480x480, virtual
    480, 32-bit, stride 1920 (sysfs)"; "Page flip enabled: two framebuffer
    halves mapped"; "Framebuffer presentation mode: page flip".
  error_output: >
    None. No exception, no traceback, nothing at ERROR or WARNING. The
    loop body simply does not return.

behavior:
  expected: >
    The display loop renders and writes a frame at the configured rate
    indefinitely, for the duration of the session.
  actual: >
    The loop body stops returning roughly 15 seconds after the display
    thread starts. thread_manager.update_heartbeat('display')
    (manager.py:701) runs once per iteration, before rendering and before
    write_to_framebuffer() later in the same iteration, so a hang
    anywhere from that point onward silences the heartbeat identically —
    the log evidence narrows the hang no further than "somewhere in this
    iteration's render-and-write step". After WatchdogMonitor's
    439-second observed timeout, it initiates a full application
    shutdown. To the operator this presents as: RPM data displays
    correctly for a few seconds, the screen then goes blank, and it does
    not recover within any timeframe they would plausibly wait before
    concluding the instrument has failed.
  impact: >
    Complete, unrecovered loss of display for the remainder of the
    session in practice. gtach.service's Restart=always / RestartSec=5
    will eventually restart the process, but only after the watchdog's
    ~7-minute shutdown sequence completes, which is far outside any
    window in which the instrument is usable in a moving vehicle.
  workaround: "None. Restarting the service manually recovers the display for another ~15 seconds before the same hang recurs."

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) 6.1.21-v8+, Raspberry Pi Zero 2W"
  dependencies:
    - library: "pygame"
      version: "SDL2, dummy video driver"
  domain: "domain_1"

analysis:
  root_cause: >
    SUSPECTED, not yet proven — requires on-target instrumentation to
    confirm; see verification_enhanced below.

    _pan_display (engine.py) issues FBIOPAN_DISPLAY with
    fb_var_screeninfo.activate set to FB_ACTIVATE_VBL (16), which asks
    the driver to latch the flip at the next vertical-blanking interval.
    The fbdev API does not fully specify whether this ioctl call itself
    blocks the caller until that interval arrives, or merely queues the
    request and returns immediately; behaviour is driver-dependent, and
    some legacy fbdev implementations do block synchronously on
    FB_ACTIVATE_VBL. If this panel's legacy DPI overlay does not reliably
    generate the vblank interrupt the driver is waiting on — for whatever
    reason, under whatever conditions — the ioctl can block indefinitely,
    with nothing in the calling code able to detect or time out the
    condition. This matches the observed symptom exactly: no exception,
    no log line, the thread simply never returns from the call.
  technical_notes: >
    _pan_display's own docstring already states no pre-write
    synchronisation wait is needed in page-flip mode, because nothing is
    reading the off-screen half being written to — that is the entire
    correctness argument for page flipping over a single-buffer write.
    FB_ACTIVATE_VBL therefore provides no correctness benefit the
    design's own stated rationale requires; it asks the driver to defer
    the pan to the next vblank for tear-free presentation, which is a
    reasonable request in principle, but one that trades an unbounded
    blocking risk for a benefit the surrounding design does not depend
    on. FB_ACTIVATE_NOW (0) would apply the pan immediately, matching the
    documented rationale and removing the one ioctl in the frame path
    with a plausible indefinite-block characteristic.

    thread_manager.update_heartbeat('display') at manager.py:701 runs
    once per loop iteration, before self.rendering_engine.write_to_framebuffer()
    later in the same iteration (manager.py ~721). This is consistent
    with, but does not by itself prove, a hang specifically inside
    write_to_framebuffer rather than elsewhere in the render step; it is
    the only point in the loop with a known blocking-ioctl candidate.

    issue-49b21ace's own resolution predicted FBIOPUT_VSCREENINFO — the
    resize that establishes page-flip mode — would likely be refused on
    this hardware: "Expect _setup_page_flip to fail on this target. The
    Pi's DPI framebuffer is allocated at boot from firmware
    configuration." That prediction did not hold: start.log confirms the
    resize succeeded and page-flip mode is active. issue-49b21ace's
    on-target verification was left outstanding on the expectation that
    the vsync-wait fallback would be the operative path observed; it was
    not, and this failure mode was accordingly never exercised by that
    verification.
  related_issues:
    - issue_ref: "issue-49b21ace"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Change _pan_display's fb_var_screeninfo.activate value from
    FB_ACTIVATE_VBL to FB_ACTIVATE_NOW, matching the method's own
    documented rationale that no synchronisation wait is required when
    panning to a half nothing is currently reading. Add a DEBUG-guarded
    log bracket immediately around the FBIOPAN_DISPLAY call itself, so
    that if a hang recurs after this change, the next debug.log capture
    shows unambiguously whether execution stopped inside this specific
    ioctl, either confirming or ruling out this root cause with
    certainty. See change-e7a92c4f.
  change_ref: "change-e7a92c4f"
  resolved_date: "2026-08-07"
  resolved_by: "Claude Code, per prompt-e7a92c4f"
  fix_description: >
    _pan_display's activation flag changed from FB_ACTIVATE_VBL to
    FB_ACTIVATE_NOW; a DEBUG-guarded log bracket added immediately
    before and after the FBIOPAN_DISPLAY ioctl call; docstring updated
    to record the rationale and cite this issue. One method, one file,
    +17/-3. See report v0.4.0-e7a92c4f-pageflip-pan-hang.md §1-§2 for
    the full implementation account.

verification:
  verified_date: "2026-08-07"
  verified_by: "William Watson"
  test_results: >
    Three sessions on gtach.local, two reboots between them, roughly 15
    minutes of continuous operation observed directly ("operation looks
    normal"). logs/debug.log pulled via bin/pull_logs.sh for the most
    recent session (2026-08-07 07:05:42 onward; start.log confirms
    page-flip mode active). Direct log analysis: zero WatchdogMonitor
    WARNING/ERROR/CRITICAL lines anywhere in the file; 38,373
    "Panning to buffer" entries and 38,373 "Panned to buffer" exits —
    exactly equal, no unmatched bracket anywhere, meaning no hang
    occurred in that session. No shutdown/cleanup marker present, so
    the capture was taken while the process was still healthy. Full
    breakdown in report v0.4.0-e7a92c4f-pageflip-pan-hang.md §7.

    The 30-minute continuous-duration verification step was not met as
    originally specified (~15 minutes observed); accepted as sufficient
    given the original hang's onset was ~15 seconds — the observed run
    exceeds that by two orders of magnitude — and given the paired-
    bracket count is a stronger, more direct signal than duration alone.
    The first two of the three sessions (both reboots) rest on direct
    operator observation rather than a log capture, since
    logs/debug.log retains only the most recent run.
  closure_notes: >
    Verified and closed. Moved to ai/workspace/issues/closed/ per P00
    §1.1.14.4.

prevention:
  preventive_measures: >
    An ioctl on a hot path a watchdog depends on for liveness should not
    be issued with an activation mode carrying a plausible indefinite-block
    characteristic unless that characteristic has been confirmed absent
    for the specific driver in use — FB_ACTIVATE_VBL's blocking behaviour
    here was inferred from general fbdev semantics rather than confirmed
    for this panel's legacy DPI driver.
  process_improvements: >
    A prior issue's resolution notes that predict which fallback path
    will be taken on a given target should be re-checked against the
    actual startup log at the first opportunity in any later debugging
    session touching the same code, rather than carried forward as an
    unstated assumption.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/display/rendering/engine.py passes."
    - "pytest tests/ passes with no new failures."
    - "On gtach.local, confirm start.log still reports 'Framebuffer presentation mode: page flip' — this change does not alter mode selection."
    - "With debug logging enabled, confirm the new bracket log lines around FBIOPAN_DISPLAY appear and are paired (entry then exit) on every frame for the duration of a run."
    - "Run GTach connected to the emulator for at least 30 minutes continuously (roughly 4x the previous hang's onset). Confirm RPM debug lines or the periodic performance INFO line continue without a gap."
    - "Confirm no WatchdogMonitor WARNING, ERROR, or CRITICAL line appears in logs/debug.log or logs/start.log for that session."
    - "Repeat across at least one full reboot cycle, since the hang was reproducible across the two most recent sessions prior to this fix."
    - "If the hang recurs despite this change: the bracket log lines confirm or rule out FBIOPAN_DISPLAY as the blocking call, redirecting the investigation."
  verification_results: >
    2026-08-07: Verified via direct log analysis of a gtach.local session
    captured with bin/pull_logs.sh (2026-08-07 07:05:42 onward, page-flip
    mode confirmed active). Zero WatchdogMonitor WARNING/ERROR/CRITICAL
    lines in the file; 38,373 pan-bracket entries and 38,373 exits,
    exactly paired, no unmatched entry anywhere — the direct signature
    of no hang occurring across the entire session. No shutdown marker
    present, confirming the capture reflects a still-healthy running
    process rather than a post-mortem state.

    Two further sessions (both after a reboot) were observed directly
    by the operator without a log capture and reported normal; only the
    third session above has log evidence. The 30-minute continuous-run
    step was not met literally (~15 minutes observed) but is accepted
    as sufficient given the two-orders-of-magnitude margin over the
    original ~15-second hang onset, and given the paired-bracket count
    is direct evidence rather than an inference from absence of symptoms
    over time. Full account: report v0.4.0-e7a92c4f-pageflip-pan-hang.md
    §7.

traceability:
  design_refs: []
  change_refs:
    - "change-e7a92c4f"
  test_refs: []

notes: >
  logs/start.log and logs/debug.log referenced above were captured via
  bin/pull_logs.sh on 2026-08-07 and are the evidentiary basis for this
  issue. They are operational artefacts under logs/, not committed
  T-Doc evidence, and should be retained locally by the reporter through
  the verification step above.

  This issue is unrelated to, and was found independently of, the bin/
  boot-splash work (bin/gtach-boot-splash.service, bin/install.sh,
  bin/deploy.sh, bin/quiet-boot.sh) in progress in the same session.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Initial issue document from on-target log analysis (logs/debug.log, logs/start.log, session 2026-08-07 05:40)."
  - version: "1.1"
    date: "2026-08-07"
    author: "William Watson"
    changes:
      - "Status open -> verified. Resolution and verification recorded: change-e7a92c4f implemented via prompt-e7a92c4f, confirmed via direct log analysis of a gtach.local session (38,373 paired pan-bracket entries/exits, zero WatchdogMonitor events). Closing per P00 §1.1.14.4."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-07 | Initial issue document from on-target log analysis. |
| 1.1 | 2026-08-07 | Verified and closed — direct log evidence from gtach.local confirms the fix (change-e7a92c4f). |

---

Copyright (c) 2026 William Watson. MIT License.
