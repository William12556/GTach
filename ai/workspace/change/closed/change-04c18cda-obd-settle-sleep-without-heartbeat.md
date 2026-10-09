Created: 2026 October 09

# Change: Interruptible OBD Settle With Heartbeats

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-04c18cda"
  title: "Bound the pre-initialised settle in OBDProtocol._initialize_protocol with heartbeats and an early exit on stop"
  date: "2026-10-09"
  author: "William Watson"
  status: "closed"
  priority: "low"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-04c18cda"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-04c18cda"
  description: "Resolves issue-04c18cda."

scope:
  summary: "Replace the 1.5 s time.sleep in the adapter_pre_initialised branch with a sliced wait on shutdown_event that heartbeats after each slice; remove the strict xfail marker."
  affected_components:
    - name: "OBDProtocol._initialize_protocol"
      file_path: "src/gtach/comm/obd.py"
      change_type: "modify"
    - name: "TestWatchdogQuiet.test_no_obd_unresponsive_warning"
      file_path: "tests/test_lifecycle_sim.py"
      change_type: "modify"
    - name: "Settle regression tests"
      file_path: "tests/test_obd_settle.py"
      change_type: "add"
  affected_designs: []
  out_of_scope:
    - "The settle duration (1.5 s) and whether the settle is needed at all."
    - "The ATZ branch and every other heartbeat site in obd.py."
    - "WatchdogMonitor timeouts."

rational:
  problem_statement: >
    See issue-04c18cda. The adapter_pre_initialised branch calls
    time.sleep(1.5) (obd.py:156 at ba661d4). The only earlier heartbeat
    is the one at the top of _initialize_protocol, so the thread is
    silent for 1.5 s, and a stop request during the settle waits the
    full 1.5 s. The settle runs only on the first initialisation:
    _protocol_loop resets _adapter_initialised on disconnect, so
    re-initialisation takes the ATZ branch.
  proposed_solution: >
    Add class constants _PRE_INIT_SETTLE_S: float = 1.5 and
    _SETTLE_SLICE_S: float = 0.5. Replace time.sleep(1.5) with a loop
    bounded by time.monotonic(): while time remains, call
    self.shutdown_event.wait(min(self._SETTLE_SLICE_S, remaining)); if
    it returns True, log at DEBUG and return False; otherwise call
    self.thread_manager.update_heartbeat('obd_protocol'). The DEBUG
    message uses the constant. Remove the strict xfail marker from
    TestWatchdogQuiet.test_no_obd_unresponsive_warning.
  alternatives_considered:
    - option: "shutdown_event.wait(1.5) with a heartbeat before it (issue-04c18cda resolution.approach)."
      reason_rejected: "Leaves a 1.5 s heartbeat gap, above the 1.0 s warning_timeout used by the xfail test, which would still fail. Corrected here."
    - option: "Remove the settle."
      reason_rejected: "The settle exists for the emulator to accept a new RFCOMM connection after setup; removing it is a behaviour change not evidenced here."
  benefits:
    - "Largest heartbeat gap on this path falls from 1.5 s to 0.5 s."
    - "A stop during the settle ends within one slice."
  risks:
    - risk: "Returning False on stop changes the caller path."
      mitigation: "_protocol_loop already treats False as a failed initialisation and waits on shutdown_event, which is set, so the loop exits at once."

technical_details:
  current_behavior: "time.sleep(1.5) between heartbeats; shutdown_event ignored during the settle."
  proposed_behavior: "1.5 s settle in slices of at most 0.5 s with a heartbeat after each; returns False within one slice of shutdown_event being set."
  implementation_approach: "Local edit to one branch of _initialize_protocol plus two class constants."
  code_changes:
    - component: "OBDProtocol"
      file: "src/gtach/comm/obd.py"
      change_summary: "Sliced, interruptible settle with heartbeats."
      functions_affected:
        - "_initialize_protocol"
      classes_affected:
        - "OBDProtocol"
  data_changes: []
  interface_changes:
    - interface: "OBDProtocol private constants"
      change_type: "contract"
      details: "Adds _PRE_INIT_SETTLE_S and _SETTLE_SLICE_S."
      backward_compatible: "yes"

dependencies:
  internal: []
  external: []
  required_changes:
    - change_ref: "change-50bf25ad"
      relationship: "blocked_by. Both remove a strict xfail in tests/test_lifecycle_sim.py; the watchdog fixture calls drop_link, whose effect in simulation changes with change-50bf25ad."

testing_requirements:
  test_approach: "Remove the xfail; add focused unit tests."
  test_cases:
    - scenario: "tests/test_lifecycle_sim.py::TestWatchdogQuiet::test_no_obd_unresponsive_warning without the xfail marker."
      expected_result: "Passes."
    - scenario: "OBDProtocol on a connected SimTransport with adapter_pre_initialised=True; record update_heartbeat('obd_protocol') times during one _initialize_protocol call."
      expected_result: "Returns True; no gap between successive heartbeats exceeds 0.6 s."
    - scenario: "Set shutdown_event from another thread 0.2 s into the settle."
      expected_result: "_initialize_protocol returns False within 0.7 s of the call; no ATE0 is sent."
  regression_scope:
    - "tests/test_lifecycle_sim.py"
    - "Full tests/ suite."
  validation_criteria:
    - "pytest tests/ passes."

implementation:
  effort_estimate: "1 hour"
  implementation_steps:
    - step: "Edit obd.py; add tests/test_obd_settle.py; remove the xfail marker."
      owner: "worker (Claude Code)"
  rollback_procedure: "Revert the commit."
  deployment_notes: "Human verification: first connection after setup on the Pi still initialises (settle unchanged at 1.5 s)."

verification:
  implemented_date: "2026-10-09"
  implemented_by: "Claude Code (commit 1a36ed0)"
  verification_date: "2026-10-09"
  verified_by: "William Watson"
  test_results: "test-04c18cda passed (6/6); first OBD connection after setup on gtach.local initialised with no watchdog warning."
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-860fd5f7"
      relationship: "related. Bounded heartbeat gaps per command."
    - change_ref: "change-50bf25ad"
      relationship: "blocked_by"
  related_issues:
    - issue_ref: "issue-04c18cda"
      relationship: "resolves"

notes: "Deviates from the issue's proposed approach; see alternatives_considered. Line numbers are from ba661d4."

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial change document resolving issue-04c18cda iteration 1."
  - version: "1.1"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Implemented, verified by test-04c18cda, closed."

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
| 1.0 | 2026-10-09 | Initial change document resolving issue-04c18cda iteration 1. |
| 1.1 | 2026-10-09 | Implemented, verified by test-04c18cda, closed. |

---

Copyright (c) 2026 William Watson. MIT License.
