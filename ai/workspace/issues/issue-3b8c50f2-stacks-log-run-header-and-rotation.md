Created: 2026 August 12

# Issue: stacks.log Concatenates Runs Without a Boundary and Has No Size Bound

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-3b8c50f2"
  title: "stacks.log is opened in append mode with no run boundary and no rotation, so dumps from successive process lifetimes concatenate indistinguishably and the file grows without bound while the debug toggle is left on"
  date: "2026-08-12"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: ""
    change_iteration: null

source:
  origin: "code_review"
  test_ref: ""
  description: >
    Raised 2026-08-12 from review of the delivered stacks.log
    capability (change-2ac1c602 iterations 1 and 2) against its first
    real output on gtach.local, and from the implementation report's
    own recorded observation #2.

    The capability works: logs/stacks.log at 10:09 contained 11 dumps
    of four threads each, correctly identifying that obd_protocol was
    parked in rfcomm._write, WatchdogMonitor in Event.wait,
    DisplayManager in write_to_framebuffer, and the main thread in
    app.run. This issue concerns the usability of that record, not its
    production.

affected_scope:
  components:
    - name: "enable_stack_dumps"
      file_path: "src/gtach/main.py"
    - name: "disable_stack_dumps"
      file_path: "src/gtach/main.py"
  designs: []
  version: "0.4.1"

reproduction:
  prerequisites: >
    GTach on gtach.local with debug enabled through the OPTIONS toggle,
    so stack dumps are armed.
  steps:
    - "Enable debug via the OPTIONS toggle; confirm /opt/gtach/stacks.log gains dumps."
    - "Restart the service, or allow a watchdog-triggered restart to occur."
    - "Enable debug again; observe further dumps appended to the same file."
    - "Inspect stacks.log and attempt to determine where one process lifetime ends and the next begins."
  frequency: "always"
  reproducibility_conditions: >
    Deterministic. Follows from the file being opened with mode='a' and
    from faulthandler's output format, neither of which varies.
  preconditions: "Stack dumps armed more than once, in the same process or across restarts."
  test_data: >
    logs/stacks.log (2026-08-12, gtach.local): 6642 bytes, 11 dumps.
    Each dump is introduced by the line "Timeout (0:00:15)!" and lists
    four threads. Measured mean size 604 bytes per dump.

    At the fixed 15 s interval that is 4 dumps per minute, ~2.4 KB per
    minute, ~145 KB per hour, ~3.5 MB per 24 hours of armed operation.

    No line in the file carries a wall-clock time, a PID, or any other
    run identifier. Every dump is introduced by the identical string
    "Timeout (0:00:15)!".

    For contrast, main.py rotates debug.log at start with ten backups
    and a 10 MB cap (_DEBUG_MAX_BYTES, _DEBUG_BACKUPS, issue-6a3b7c52).
    The 09:11-10:09 window produced ten debug.log rotations totalling
    approximately 38 MB. stacks.log has neither mechanism.
  error_output: >
    None. No error is produced; the defect is in the legibility and
    boundedness of the diagnostic record.

behavior:
  expected: >
    A diagnostic record whose entries can be attributed to a specific
    process lifetime, and whose size is bounded on a card-backed
    filesystem.
  actual: >
    enable_stack_dumps opens _STACKS_LOG with mode='a' (main.py:139)
    and writes nothing before arming. faulthandler introduces every
    dump with the identical literal "Timeout (0:00:15)!" and emits no
    timestamp, PID or run identifier of its own. Two consequences:

    1. RUN BOUNDARY ABSENT. Dumps from successive process lifetimes
    concatenate with nothing separating them. After a systemd restart —
    which is precisely the outcome change-2ac1c602 was written to
    produce — the dumps from before and after the restart are
    indistinguishable in the file. This is most acute in exactly the
    scenario the capability exists to diagnose: a watchdog-triggered
    restart, where the operator needs to know which dumps preceded the
    termination and which followed the relaunch.

    2. NO SIZE BOUND. There is no cap and no rotation. Growth is
    modest at ~3.5 MB per 24 hours armed, so this is not urgent, but it
    is unbounded, on a filesystem where debug.log was explicitly
    bounded for the same reason.
  impact: >
    Degrades the diagnostic capability delivered for issue-2ac1c602 at
    the moment it is most needed. The unresolved ~52 s process-wide
    stall is expected to be diagnosed from this file, and if it is
    accompanied by a restart the record cannot be partitioned by run.

    Severity medium: the capability functions, the dumps are correct,
    and dump ordering within a single uninterrupted run is unambiguous.
    Nothing is lost; it is attribution that is missing.
  workaround: >
    Delete or move /opt/gtach/stacks.log before beginning a
    reproduction, so the file contains one run only. Effective but
    manual, and it discards prior evidence.

environment:
  python_version: "3.9"
  os: "Debian Linux (Raspberry Pi OS), Raspberry Pi Zero 2W"
  dependencies:
    - library: "faulthandler (stdlib)"
      version: "n/a"
  domain: "domain_1"

analysis:
  root_cause: >
    CONFIRMED from source. enable_stack_dumps (main.py:103-147) opens
    _STACKS_LOG with mode='a' and proceeds directly to
    faulthandler.enable and faulthandler.dump_traceback_later. It
    writes no header. faulthandler's dump format is fixed and carries
    no timestamp or process identity. There is no rotation logic
    anywhere for this file, in contrast to the explicit rotate-at-start
    treatment given to debug.log in setup_logging.

    The append mode is itself correct and should be retained: the
    alternative, mode='w', would discard the previous run's dumps at
    the moment of relaunch, which is worse than failing to delimit
    them.
  technical_notes: >
    A per-dump timestamp is NOT the correct remedy and should not be
    pursued. faulthandler offers no timestamp option, so any such
    facility would have to be a Python-side timer writing marker lines
    to the same file. That timer would be a Python thread, subject to
    the very stall the file exists to capture, so its markers would be
    absent from exactly the window that needs them. The entire value of
    faulthandler here is that its timer runs in C and is immune to that
    stall; a Python-side companion would forfeit that property.

    Nor is a per-dump timestamp necessary. The diagnostic content of a
    dump is which frame each thread is parked in, which is
    time-independent — the 2026-08-12 dumps identified four thread
    positions without a single clock reading. Localisation in time is
    already adequate from the fixed 15 s cadence combined with the
    bracketing entries in debug.log: dump N can be placed to within
    ±15 s by counting from a known anchor.

    What is genuinely missing is an anchor per arming event, written
    once, at a moment when no stall can be in progress — because the
    process is by definition running normally when the operator enables
    the toggle. A header line written inside enable_stack_dumps before
    arming has that property and cannot be lost to a stall.

    One hazard to design around: arming happens on every OPTIONS
    toggle-on, not only at process start. Rotating on every arm would
    let a few toggle cycles discard the evidence just captured.
    Rotation must therefore be once per process lifetime, while the
    header is written on every arm.
  related_issues:
    - issue_ref: "issue-2ac1c602"
      relationship: >
        Parent capability. Iterations 1 and 2 of change-2ac1c602
        introduced stacks.log and made its arming follow the runtime
        debug toggle. That issue remains active pending a reproduction
        of the ~52 s stall, which this file is intended to diagnose.
    - issue_ref: "issue-6a3b7c52"
      relationship: >
        Established the rotate-at-start treatment and size cap for
        debug.log that stacks.log lacks, and the reasoning that applies
        here.

resolution:
  assigned_to: ""
  target_date: ""
  approach: >
    Two corrections in enable_stack_dumps, both in src/gtach/main.py.

    1. RUN HEADER. Before arming, write a single line to the open file
    identifying the process:

      === gtach <version> pid <pid> armed <ISO-8601 local time> ===

    Written on every arm, including re-arms within the same process, so
    that each contiguous block of dumps is attributable. This executes
    while the process is running normally and cannot be lost to a
    stall. It also supplies the PID, which is independently useful:
    a changed PID in a later header IS the systemd restart that
    issue-2ac1c602's verification step 3 requires evidence of.

    2. ROTATE ONCE PER PROCESS. On the first arm of a process
    lifetime, and only the first, rotate an existing non-empty
    stacks.log to stacks.log.1, shifting existing backups, keeping
    three. Mirrors setup_logging's rotate-at-start treatment of
    debug.log, done by hand because faulthandler requires a raw file
    object rather than a logging handler. A module-level flag records
    whether rotation has occurred, so repeated OPTIONS toggling within
    one run appends to the same file rather than churning backups.

    Append mode is retained. mode='w' is rejected: it would discard the
    previous run's dumps at relaunch, which is the opposite of what is
    wanted.
  change_ref: ""
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
    Any app-owned log file should be given a run boundary and a size
    bound at the point it is introduced. debug.log received both;
    stacks.log received neither, because it is written by faulthandler
    rather than by the logging module and so did not inherit the
    treatment applied to logging handlers.
  process_improvements: >
    A diagnostic capability should be reviewed against its own first
    real output before its parent issue is closed. Both defects here
    were visible in the first 6642 bytes stacks.log produced.

verification_enhanced:
  verification_steps:
    - "Confirm by source reading that enable_stack_dumps opens _STACKS_LOG in append mode and writes nothing before arming. [DONE.]"
    - "Confirm that logs/stacks.log contains no timestamp, PID or run identifier, and that every dump is introduced by the identical literal. [DONE.]"
    - "Confirm that no rotation or size cap exists for _STACKS_LOG, in contrast to _DEBUG_MAX_BYTES and _DEBUG_BACKUPS. [DONE.]"
    - "After the fix: enable debug via OPTIONS, confirm a header line appears carrying the current PID, and that dumps follow it."
    - "After the fix: disable and re-enable debug within one run; confirm a second header appears and that no rotation occurred."
    - "After the fix: restart the service and enable debug; confirm the prior file was rotated to stacks.log.1 and the new file opens with a header carrying the NEW pid."
    - "After the fix: confirm stacks.log.4 is never created."
  verification_results: >
    First three steps complete, as recorded in test_data and root_cause
    above. Remaining steps require the fix to exist.

traceability:
  design_refs: []
  change_refs: []
  test_refs: []

notes: >
  A per-dump timestamp was considered and deliberately rejected. The
  reasoning is recorded in analysis.technical_notes so that it is not
  revisited as an oversight: any Python-side timestamp source would
  stall in precisely the window it is needed, forfeiting the property
  that makes faulthandler valuable here.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-08-12"
    author: "William Watson"
    changes:
      - "Initial issue document from review of the delivered stacks.log capability against its first real output on gtach.local."
      - "Two defects recorded: no run boundary in an append-mode file whose dumps carry no identifying information, and no rotation or size cap."
      - "Growth rate measured from the 2026-08-12 file: 604 bytes per dump, ~145 KB per hour armed."
      - "Records the deliberate rejection of a per-dump timestamp, and the hazard that rotation must be once per process rather than once per arm."

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
| 1.0 | 2026-08-12 | Initial issue document. stacks.log concatenates process lifetimes without a boundary and has no size bound. Confirmed from source and from the file's first real output. |

---

Copyright (c) 2026 William Watson. MIT License.
