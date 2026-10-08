Created: 2026 October 07

# Issue: Wall-Clock Step Triggers Watchdog Shutdown

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-b9ee7428"
  title: "Heartbeat, recovery and shutdown timing use time.time(); a forward clock step of more than 45 s makes the display thread appear stalled and the watchdog shuts the application down"
  date: "2026-10-07"
  reporter: "William Watson"
  status: "closed"
  severity: "high"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-b9ee7428"
    change_iteration: 1

source:
  origin: "monitoring"
  test_ref: ""
  description: >
    Observed on gtach.local on 2026-10-07 while verifying audit-36b6ea95
    and recorded as audit finding B13 (high, audit version 1.1). The
    journal for the current boot shows the service starting at a restored
    clock time and exiting cleanly at the moment the clock was corrected.

affected_scope:
  components:
    - name: "ThreadManager.register_thread / update_heartbeat / _restart_thread / shutdown"
      file_path: "src/gtach/core/thread.py"
    - name: "WatchdogMonitor._check_thread_health / _handle_warning_timeout / _handle_recovery_timeout / get_thread_health_status"
      file_path: "src/gtach/core/watchdog.py"
    - name: "ThreadHealth (last_warning_time, last_recovery_time defaults)"
      file_path: "src/gtach/core/watchdog.py"
  designs: []
  version: "0.4.3"

reproduction:
  prerequisites: >
    Pi Zero 2W (no RTC) running GTach under systemd, booting with network
    access so that NTP corrects the clock restored at boot.
  steps:
    - "Power the Pi off and leave it off for longer than 45 s."
    - "Power it on with Wi-Fi available."
    - "Run: journalctl -u gtach -b -o short-precise --no-pager"
  frequency: "always (on every boot where the clock is stepped forward by more than 45 s after GTach starts)"
  reproducibility_conditions: >
    Deterministic given a forward wall-clock step larger than
    critical_timeout (45 s, app.py:59) after heartbeats have been
    stamped. Reproducible in a unit test by advancing time.time().
  test_data: >
    journalctl -u gtach -b -o short-precise, 2026-10-07:

      Oct 02 14:52:25.934 systemd: Starting GTach OBD-II Tachometer...
      Oct 02 14:52:25.949 systemd: Started GTach OBD-II Tachometer.
      Oct 07 07:18:29.490 gtach[807]: stty: 'standard input': Inappropriate ioctl for device
      Oct 07 07:18:29.831 systemd: gtach.service: Succeeded.
      Oct 07 07:18:29.833 systemd: Consumed 10.004s CPU time.
      Oct 07 07:18:35.012 systemd: Scheduled restart job, restart counter is at 1.

    The process ran for seconds (10 s CPU) while the wall clock advanced
    about 4 days 16 hours. Exit status 0 ("Succeeded") identifies the
    graceful path, not the os._exit(1) paths.

    Source:

      thread.py:130,146,268  heartbeats stamped with time.time()
      watchdog.py:157,175    time_since_heartbeat = time.time() - last_heartbeat
      watchdog.py:98         critical_threads = {'display'}
      watchdog.py:249-253    critical thread past critical_timeout →
                             _initiate_graceful_shutdown
      app.py:59-60           critical_timeout=45.0,
                             shutdown_callback=self._watchdog_shutdown
  error_output: "None recorded (issue-269871a0)."

behavior:
  expected: >
    Thread liveness is judged by elapsed time, unaffected by changes to
    the wall clock.
  actual: >
    INFERRED FROM EVIDENCE, MECHANISM CONFIRMED IN SOURCE. After the
    clock step every heartbeat appears about 400,000 s old. The display
    thread, the only critical thread, exceeds critical_timeout on the
    next watchdog check, the watchdog initiates a graceful shutdown, the
    process exits 0, and systemd restarts it after RestartSec=5. The
    exact coincidence of clock step and exit is inferred from the
    journal timestamps; a monotonic-timestamped journal query can
    confirm it.

    CONFIRMED IN SOURCE. A backward step makes heartbeats appear to be in
    the future; time_since_heartbeat is negative and every thread is
    reported healthy until the clock catches up, so a genuine stall in
    that window goes undetected.

    CONFIRMED IN SOURCE. ThreadManager.shutdown computes its remaining
    budget from time.time() (thread.py:335,359,394); a step during
    shutdown distorts per-thread join timeouts.
  impact: >
    One restart and about 10 s without RPM indication on every boot with
    network access. Any later NTP step above 45 s causes the same. A
    backward step suspends stall detection.
  workaround: "None."

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies: []
  domain: "domain_1"

analysis:
  root_cause: >
    Elapsed-time measurement uses the wall clock. The Pi Zero 2W has no
    RTC; it boots with the last saved time and NTP steps it later. The
    display layer already uses time.monotonic() for link-loss detection
    (manager.py:890,961); core/ does not.
  technical_notes: >
    time.monotonic() on Linux is CLOCK_MONOTONIC: unaffected by steps,
    starting near zero at boot. That second property is a trap for the
    fix. ThreadHealth.last_warning_time and last_recovery_time default to
    0.0. With wall-clock time, `now - 0.0` is always large. With
    monotonic time shortly after boot, `now - 0.0` is the system uptime:
    _handle_warning_timeout (`> 30.0`) would suppress the first warning
    until 30 s of uptime, and _handle_recovery_timeout (`< 10.0`) would
    skip recovery until 10 s of uptime. These defaults must become
    "never" (float('-inf')) when the clock source changes.

    ThreadInfo.creation_time (default_factory=time.time) is used only in
    __hash__ as an identity component and is not elapsed-time arithmetic.

    Remaining time.time() uses in display/ (touch timing, splash,
    setup-state interaction timing) are audit finding C16 (low) and are
    not part of this issue.
  related_issues:
    - issue_ref: "issue-269871a0"
      relationship: "related. The reason the shutdown left no record."
    - issue_ref: "issue-5a9dc15e"
      relationship: "related. Established the watchdog lock discipline that must be preserved."
    - issue_ref: "issue-2ac1c602"
      relationship: "related. Established watchdog process termination and the critical/advisory tiers."

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Use time.monotonic() for every heartbeat stamp, every elapsed-time
    comparison in the watchdog, and the shutdown budget in ThreadManager.
    Change the ThreadHealth "last" defaults to float('-inf'). Update the
    test helper that ages heartbeats and add a regression test that steps
    time.time() forward and asserts no shutdown.
  change_ref: "change-b9ee7428"
  resolved_date: "2026-10-08"
  resolved_by: "change-b9ee7428"
  fix_description: "Heartbeat stamps, all watchdog elapsed-time checks and the ThreadManager shutdown budget now use time.monotonic(), and ThreadHealth's last-warning and last-recovery defaults are float('-inf'), so a wall-clock step no longer changes watchdog decisions (commit 29bdebedc0343da5eb20ddf25ca4b5e5c4c9c66a)."

verification:
  verified_date: "2026-10-08"
  verified_by: "William Watson"
  test_results: "Session C (2026-10-07): cold boot; NTP stepped the clock ~13 min forward at 37 s; no exit or restart of gtach (verify script C1). Repeated on 2026-10-08 13:48 boot."
  closure_notes: "Closed at audit-36b6ea95 close-out after on-device verification."

prevention:
  preventive_measures: >
    Elapsed-time arithmetic uses time.monotonic(); time.time() is
    reserved for timestamps shown to people or written to files.
  process_improvements: >
    On-device tests should include a cold boot with network access, not
    only service restarts.

verification_enhanced:
  verification_steps:
    - "Confirm from source that heartbeats and watchdog comparisons use time.time(). [DONE.]"
    - "Confirm with: journalctl -b -o short-monotonic --no-pager | grep -E 'gtach\\[|gtach\\.service|timesyncd|Time has been changed|Synchroni[sz]ed' that the exit follows the clock correction within about one watchdog interval."
    - "After the fix: power-cycle the Pi with Wi-Fi available and confirm no gtach.service 'Succeeded'/'Scheduled restart' entries for the boot."
    - "After the fix: confirm a deliberately stalled display thread still triggers the watchdog (unit test)."
  verification_results: "All verification steps complete; see verification.test_results."

traceability:
  design_refs: []
  change_refs:
    - "change-b9ee7428"
  test_refs: []

notes: >
  Audit reference: audit-36b6ea95 B13 and Section 6.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-10-07"
    author: "William Watson"
    changes:
      - "Initial issue document from on-device observation during audit-36b6ea95 verification."
  - version: "1.1"
    date: "2026-10-07"
    author: "Claude Code"
    changes:
      - "Fix implemented in 29bdebedc0343da5eb20ddf25ca4b5e5c4c9c66a; awaiting on-device verification."
  - version: "1.2"
    date: "2026-10-08"
    author: "William Watson"
    changes:
      - "On-device verification complete; closed at audit-36b6ea95 close-out."

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
| 1.0 | 2026-10-07 | Initial issue document. Wall-clock step causes watchdog shutdown; monotonic-default trap recorded. |
| 1.1 | 2026-10-07 | Fix implemented in 29bdebedc0343da5eb20ddf25ca4b5e5c4c9c66a; awaiting on-device verification. |
| 1.2 | 2026-10-08 | On-device verification complete; closed at audit-36b6ea95 close-out. |

---

Copyright (c) 2026 William Watson. MIT License.
