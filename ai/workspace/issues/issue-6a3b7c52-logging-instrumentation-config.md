Created: 2026 August 05

# Issue: The Debug Log Never Rotates and the Performance Monitor Measures Against a Frame Rate the Application No Longer Uses

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-6a3b7c52"
  title: "RotatingFileHandler silently overrides mode='w' to 'a' when maxBytes is set, so debug.log has never truncated and its 100 MB rotation threshold has never been reached; and PerformanceMonitor is constructed with a hardcoded target_fps=60 because the display configuration is not yet loaded at that point, so every dropped-frame figure at 30 Hz is wrong"
  date: "2026-08-05"
  reporter: "William Watson"
  status: "open"
  severity: "low"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-6a3b7c52"
    change_iteration: 1

source:
  origin: "user_report"
  test_ref: "logs/debug.log, on-target sessions 2026-08-05"
  description: >
    Fault (a) was found on 2026-08-05 while reading the pulled logs, and
    the operator specified the wanted behaviour on the same date: a
    10 MB cap, rotation at start, ten versions kept. Fault (b) was found
    while confirming that the fps_limit reduction had taken effect, when
    the startup line reporting the monitor's target proved to be
    hardcoded and to have misled that analysis. Both recorded in
    ai/task.md §9.11.7.4.

affected_scope:
  components:
    - name: "setup_logging"
      file_path: "src/gtach/main.py"
    - name: "DisplayManager._initialize_components"
      file_path: "src/gtach/display/manager.py"
    - name: "DisplayManager.__init__"
      file_path: "src/gtach/display/manager.py"
  designs: []
  version: "0.3.3"

reproduction:
  prerequisites: "Source checkout at 0.3.3, or the deployed build."
  steps:
    - "(a) — read main.py:46-49. The handler is RotatingFileHandler(_DEBUG_LOG, mode='w', maxBytes=_DEBUG_MAX_BYTES, backupCount=0)."
    - "(a) — read CPython's RotatingFileHandler.__init__: 'if maxBytes > 0: mode = 'a''. The mode argument is discarded."
    - "(a) — restart the application and observe that debug.log retains its previous content. The comment above the handler says 'truncated at boot'; it is not."
    - "(a) — observe _DEBUG_MAX_BYTES = 100 MB at main.py:25, against a file that reached 43 MB across several sessions. Rotation has never fired."
    - "(b) — read manager.py:169. PerformanceMonitor(target_fps=60), a literal."
    - "(b) — read manager.py:136 and 139. _initialize_components() is called before _load_config(), so self.config does not exist when the monitor is constructed. That is why the literal is there."
    - "(b) — read monitor.py:42, 50, 74-75. target_fps sets frame_time_target, the history deque's maxlen and both alert thresholds."
    - "(b) — with fps_limit at 30, observe the startup line 'Performance monitoring started (target: 60 FPS)'."
  frequency: "always"
  reproducibility_conditions: "Both unconditional."
  preconditions: "None."
  test_data: >
    (a) VERIFIED AGAINST CPYTHON, not inferred. A minimal reproduction
    was run: a RotatingFileHandler opened with mode='w' and
    maxBytes=100 MB over a file containing prior content left that
    content in place, and handler.mode read 'a'. The relevant source
    comment explains the choice — truncating would defeat rotation by
    discarding previous runs — so this is deliberate CPython behaviour
    and the mode='w' in main.py is simply dead.

    CONSEQUENCE, measured. debug.log reached 43 MB spanning three
    sessions and had to be segmented by timestamp for every analysis in
    ai/task.md §9.11. One session's file also carried a ~4 KB block of
    NUL bytes from an unclean shutdown, which is recoverable only
    because the surrounding content survived — with truncation it would
    have been the whole file.

    (b) WHAT target_fps GOVERNS, at 60 against an actual 30:

      monitor.py:42  frame_time_target = 1/60 = 16.67 ms, not 33.3
      monitor.py:50  _frame_history maxlen = 600, so the "last 10
                     seconds" window is 20 seconds
      monitor.py:74  min_fps alert = 48, not 24
      monitor.py:75  max_frame_time_ms alert = 20.0, not 40.0

    The dropped-frame test at monitor.py:181 compares against
    frame_time_target, so at 30 Hz it reports a drop for any frame over
    25 ms when the real deadline is 50 ms. Every dropped-frame figure
    read at 30 Hz is wrong, and the §9.11.6 baseline of 297 samples was
    read in that state — the frame times are sound, being direct
    measurements, but any drop count derived from them is not.

    (b) THE ORDERING IS THE CAUSE, not carelessness. manager.py:136
    calls _initialize_components(), which constructs the monitor at
    :169; manager.py:139 then calls _load_config(), which is the first
    thing to set self.config. A literal was the only value available.

    THE STARTUP LINE MISLED AN ANALYSIS. On 2026-08-05 the line
    'Performance monitoring started (target: 60 FPS)' was cited as
    evidence that fps_limit had not taken effect on the target. It was
    not evidence of anything; the measured 'Performance: 60.0 FPS'
    samples were. Recorded because a diagnostic that reports a constant
    is worse than one that reports nothing.
  error_output: >
    None for either. (a) produces an oversized file; (b) produces a
    plausible wrong number.

behavior:
  expected: >
    A debug log bounded in size, whose content belongs to the session
    being diagnosed, retaining enough history to investigate a restart.
    A performance monitor that measures against the frame rate in use.
  actual: >
    (a) debug.log appends across every restart and rotates at 100 MB,
    which has never been reached. Its own comment and its own mode
    argument both say it truncates at boot; neither is true.

    (b) The monitor is built with target_fps=60 regardless of
    configuration, because the configuration is not loaded until three
    lines after it is constructed.
  impact: >
    (a) Diagnosis is harder than it should be — every analysis of these
    logs has had to establish which session a line belongs to. The file
    is also a continuous write to the SD card, which is one of two
    candidate causes for the sluggishness recorded in ai/task.md §9.12
    and not yet distinguished from the other.

    (b) Any dropped-frame or FPS-alert figure read at 30 Hz is wrong,
    and the reported target actively misleads. Directly measured frame
    times are unaffected.
  workaround: >
    (a) Delete debug.log on the target between sessions.
    (b) Ignore the dropped-frame count and read frame_time_ms.

environment:
  python_version: "3.9 on target; 3.11 development"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W, gtach.local"
  dependencies:
    - library: "CPython logging.handlers"
      version: "stdlib"
  domain: "domain_1"

analysis:
  root_cause: >
    (a) A stdlib API that discards an argument rather than rejecting it.
    The author wrote mode='w' meaning "start each run clean" and
    maxBytes meaning "and do not grow without bound"; the two are
    mutually exclusive in RotatingFileHandler and it resolves the
    conflict silently in favour of the second. Nothing warns, and the
    comment above the call records the intent rather than the effect.

    (b) An initialisation order in which a component that needs
    configuration is built before configuration is read. The literal is
    a symptom; the ordering is the cause, and any later attempt to make
    the monitor configurable without addressing the ordering would meet
    the same wall.
  technical_notes: >
    THE OPERATOR'S SPECIFICATION for (a), given 2026-08-05: cap at
    10 MB, rotate at start, keep ten versions.

    That is a rotate-on-start design rather than a truncate-on-start
    one, and the distinction matters on this device. GTach runs under
    systemd with Restart=always; truncating would erase the evidence of
    a crash at precisely the moment the application restarted because of
    one. Rotating preserves the previous run as debug.log.1.

    STORAGE. Eleven files at 10 MB is 110 MB maximum. At the observed
    rate — roughly 1.8 KB/s with debug on at 30 Hz — 10 MB is about
    ninety minutes and the full set about sixteen hours.

    CRASH-LOOP SAFETY, checked rather than assumed. Rotating at start
    could in principle consume all ten slots in a restart loop.
    bin/gtach.service sets StartLimitIntervalSec=60 and
    StartLimitBurst=3, so systemd stops after three rapid starts. Ten
    slots survives that comfortably.

    FOR (b), THE FIX IS ORDERING. PerformanceMonitor takes target_fps in
    its constructor and offers no way to change it afterwards
    (monitor.py has no setter; target_fps is consumed at :42, :50 and
    :74-75 during __init__). So the monitor must be constructed after
    _load_config rather than reconfigured. Nothing runs between the two
    calls at manager.py:136 and :139, and _load_config sets self.config
    on every path including its fallbacks, so moving the construction is
    safe.

    NOT IN SCOPE — THE SLUGGISHNESS. ai/task.md §9.12 records the target
    becoming slow to respond, including to a reboot command, while the
    adapter was absent. Two candidate causes are recorded there —
    continuous SD writes from this log, and kernel-level Bluetooth
    retry against a missing device — and they have not been
    distinguished. This change reduces the first without establishing
    that it was the cause. It is not a fix for §9.12 and must not be
    recorded as one.
  related_issues:
    - issue_ref: "issue-bd8f95b7"
      relationship: "related"
    - issue_ref: "issue-0b00759c"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Set the debug handler to a 10 MB cap with ten backups, drop the dead
    mode argument, and roll over once at startup when the file has
    content. Move the PerformanceMonitor construction to after
    _load_config and pass config.fps_limit. See change-6a3b7c52.
  change_ref: "change-6a3b7c52"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    Where a stdlib constructor may discard an argument, assert the
    resulting state rather than trusting the call. handler.mode would
    have shown 'a' at any point in the last several months.

    A comment that states intent beside a call that does not achieve it
    is worse than no comment: it satisfies the reader who checks.

    A component that needs configuration should be constructed after
    configuration is available, or take it later. Passing a literal
    because the value is not yet loaded encodes an initialisation
    accident as a behaviour.
  process_improvements: >
    A diagnostic that reports a constant regardless of state — the
    'target: 60 FPS' line — is worse than one that reports nothing,
    because it is quoted as evidence. It was, on 2026-08-05.

verification_enhanced:
  verification_steps:
    - "python -m py_compile on both modified files passes."
    - "handler.mode is 'a' and this is documented as expected rather than intended."
    - "_DEBUG_MAX_BYTES is 10 MB and backupCount is 10."
    - "Starting with a non-empty debug.log rotates it: the previous content appears in debug.log.1 and debug.log begins empty."
    - "Starting with no debug.log present does not raise and creates one."
    - "Starting with an empty debug.log does not rotate, so a restart before any output does not consume a slot."
    - "Eleven consecutive starts leave debug.log plus .1 to .10 and no .11."
    - "Writing past 10 MB in one session rotates within the session."
    - "start.log's behaviour is unchanged — still truncated at boot."
    - "PerformanceMonitor is constructed with config.fps_limit."
    - "With fps_limit 30 the startup line reports 30 FPS."
    - "frame_time_target is 1/fps_limit and the dropped-frame threshold follows it."
    - "With fps_limit absent from configuration the monitor falls back to the DisplayConfig default without raising."
    - "The display loop, the frame bracketing and should_log_periodic behave as before."
  verification_results: ""

traceability:
  design_refs: []
  change_refs:
    - "change-6a3b7c52"
  test_refs: []

notes: >
  Raised under P04 from the operator's specification of 2026-08-05 and
  from two findings recorded in ai/task.md §9.11.7.4. Not a numbered
  item of either code review.

  issue_info.type is defect: both behaviours differ from what their own
  code says they do. Severity low — neither affects the displayed
  reading, and (b) affects only a derived diagnostic figure. Grouped on
  the change-d32ccc49 pattern: two small faults, two files, neither
  dependent on the other.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-05"
    author: "William Watson"
    changes:
      - "Initial issue document grouping the debug log's failure to rotate and the performance monitor's hardcoded frame-rate target."
      - "Recorded that RotatingFileHandler's override of mode='w' was verified against CPython by reproduction rather than inferred, and that the behaviour is deliberate."
      - "Recorded that the operator specified rotate-at-start rather than truncate-at-start, and why that matters under systemd Restart=always: truncation would erase the evidence of the crash that caused the restart."
      - "Recorded the crash-loop check against bin/gtach.service's StartLimitBurst=3, which caps how many slots a restart loop can consume."
      - "Recorded that the monitor's hardcoded target is caused by initialisation order — _initialize_components runs before _load_config — and that the monitor offers no reconfiguration, so the construction must move rather than be corrected in place."
      - "Recorded that the 'target: 60 FPS' startup line misled an analysis on 2026-08-05, having been cited as evidence of the running frame rate when it reports a constant."
      - "Recorded explicitly that this change is NOT a fix for the sluggishness of §9.12, whose two candidate causes remain undistinguished."

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
| 1.0 | 2026-08-05 | Initial issue document grouping the non-rotating debug log and the hardcoded performance-monitor target, with the CPython behaviour verified by reproduction and the initialisation ordering identified as the cause of the second. |

---

Copyright (c) 2026 William Watson. MIT License.
