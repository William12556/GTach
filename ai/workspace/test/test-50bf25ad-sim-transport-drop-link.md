Created: 2026 October 09

# Test: SimTransport Observes drop_link

---

## Table of Contents

- [1. Test Information](<#1. test information>)
- [2. Version History](<#2. version history>)

---

## 1. Test Information

```yaml
test_info:
  id: "test-50bf25ad"
  title: "Verify that SimTransport.drop_link is observed and the simulated link reconnects"
  date: "2026-10-09"
  author: "William Watson"
  status: "planned"
  type: "unit"
  priority: "high"
  iteration: 1
  coupled_docs:
    prompt_ref: "prompt-50bf25ad"
    prompt_iteration: 1
    result_ref: ""

source:
  test_target: "SimTransport.drop_link (src/gtach/comm/sim_transport.py)"
  design_refs: []
  change_refs:
    - "change-50bf25ad"
  requirement_refs:
    - "issue-50bf25ad"

scope:
  description: >
    Verifies that a dropped simulated link clears _connected under the
    lock, records the cause, leaves _shutdown clear, and that
    reconnect_indefinitely restores the link. Existing pytest cases are
    the primary evidence; one static check confirms the base class was
    not modified by this change.
  test_objectives:
    - "Confirm is_connected is False after drop_link, with and without a cause."
    - "Confirm _shutdown is not set, so reconnection is permitted."
    - "Confirm the lifecycle link-loss test passes without an xfail marker."
    - "Confirm OBDTransport (transport.py) was not modified by commit 3404125."
  in_scope:
    - "src/gtach/comm/sim_transport.py — SimTransport.drop_link"
    - "tests/test_lifecycle_sim.py — TestLinkLoss"
  out_scope:
    - "OBDTransport.drop_link behaviour beyond being called"
    - "Real RFCOMM transports"
  dependencies:
    - "Development venv with pip install -e .[dev]"

test_environment:
  python_version: "3.9+ (development); 3.11 on target"
  os: "macOS (development)"
  libraries:
    - name: "pytest"
      version: ">=7.0.0"
  test_framework: "pytest"
  test_data_location: "Inline fixtures"

test_cases:
  - case_id: "TC-001"
    description: "drop_link with a cause is observed"
    category: "positive"
    preconditions:
      - "SimTransport connected"
    test_steps:
      - step: "1"
        action: "Call drop_link(cause)"
    inputs:
      - parameter: "cause"
        value: "test cause string"
        type: "str"
    expected_outputs:
      - field: "is_connected"
        expected_value: "False"
        validation: "Equality"
      - field: "recorded cause"
        expected_value: "The supplied cause"
        validation: "Equality"
      - field: "_shutdown"
        expected_value: "Not set"
        validation: "is_set() is False"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: "tests/test_sim_transport.py::test_drop_link_with_cause_is_observed"
      pass_fail_criteria: "All three fields as expected"
    defects: []

  - case_id: "TC-002"
    description: "drop_link without a cause uses the default silent-link cause"
    category: "positive"
    preconditions:
      - "SimTransport connected"
    test_steps:
      - step: "1"
        action: "Call drop_link() with no argument"
    inputs: []
    expected_outputs:
      - field: "recorded cause"
        expected_value: "_SILENT_LINK_CAUSE"
        validation: "Equality"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: "tests/test_sim_transport.py::test_drop_link_without_cause_uses_default"
      pass_fail_criteria: "Default cause recorded"
    defects: []

  - case_id: "TC-003"
    description: "connect succeeds after drop_link"
    category: "positive"
    preconditions:
      - "drop_link has been called"
    test_steps:
      - step: "1"
        action: "Call connect()"
    inputs: []
    expected_outputs:
      - field: "is_connected"
        expected_value: "True"
        validation: "Equality"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: "tests/test_sim_transport.py::test_connect_after_drop_link_reconnects"
      pass_fail_criteria: "Link restored"
    defects: []

  - case_id: "TC-004"
    description: "drop_link before any connect is harmless"
    category: "edge"
    preconditions:
      - "SimTransport never connected"
    test_steps:
      - step: "1"
        action: "Call drop_link()"
    inputs: []
    expected_outputs:
      - field: "exception"
        expected_value: "None raised"
        validation: "Call completes"
      - field: "is_connected"
        expected_value: "False"
        validation: "Equality"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: "tests/test_sim_transport.py::test_drop_link_before_connect_is_harmless"
      pass_fail_criteria: "No exception; state unchanged"
    defects: []

  - case_id: "TC-005"
    description: "Lifecycle link loss is observed and reconnected"
    category: "positive"
    preconditions:
      - "Lifecycle harness running against the simulated transport"
    test_steps:
      - step: "1"
        action: "Run tests/test_lifecycle_sim.py::TestLinkLoss"
      - step: "2"
        action: "grep -n 'xfail' tests/test_lifecycle_sim.py"
    inputs: []
    expected_outputs:
      - field: "TestLinkLoss"
        expected_value: "Both tests pass"
        validation: "pytest exit 0"
      - field: "xfail markers"
        expected_value: "None"
        validation: "grep returns nothing"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: "tests/test_lifecycle_sim.py::TestLinkLoss::test_drop_is_observed_and_link_reconnects; ::test_samples_flow_after_drop_link"
      pass_fail_criteria: "Pass without xfail"
    defects: []

  - case_id: "TC-006"
    description: "Base transport not modified by this change"
    category: "negative"
    preconditions: []
    test_steps:
      - step: "1"
        action: "git show --stat 3404125"
    inputs: []
    expected_outputs:
      - field: "files listed"
        expected_value: "src/gtach/comm/transport.py absent"
        validation: "Inspection"
    postconditions:
      - "Do not use git diff 42d61fc for this check: commit 5ebd823 (change-ac11505d) later edited transport.py"
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "transport.py not in the commit"
    defects: []

  - case_id: "TC-007"
    description: "Optional desk check: simulated Bluetooth link drop reconnects"
    category: "positive"
    preconditions:
      - "Optional; development machine"
    test_steps:
      - step: "1"
        action: "Run gtach --transport simbt --debug and trigger a link drop"
      - step: "2"
        action: "Inspect debug.log"
    inputs: []
    expected_outputs:
      - field: "debug.log"
        expected_value: "'dropped - will attempt to reconnect', then a reconnect, then resumed RPM samples"
        validation: "Log inspection"
    postconditions: []
    execution:
      status: "not_run"
      executed_date: ""
      executed_by: ""
      actual_result: ""
      pass_fail_criteria: "Sequence present in order"
    defects: []

coverage:
  requirements_covered:
    - requirement_ref: "issue-50bf25ad"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006", "TC-007"]
  code_coverage:
    target: "All branches of SimTransport.drop_link"
    achieved: ""
  untested_areas:
    - component: "Concurrent drop_link and connect from separate threads"
      reason: "Not specified by the change; lock ordering is covered only indirectly by the lifecycle harness"

test_execution_summary:
  total_cases: 7
  passed: 0
  failed: 0
  blocked: 0
  skipped: 0
  pass_rate: ""
  execution_time: ""
  test_cycle: "Initial"

defect_summary:
  total_defects: 0
  critical: 0
  high: 0
  medium: 0
  low: 0
  issues: []

verification:
  verified_date: ""
  verified_by: ""
  verification_notes: ""
  sign_off: ""

traceability:
  requirements:
    - requirement_ref: "issue-50bf25ad"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005"]
  designs: []
  changes:
    - change_ref: "change-50bf25ad"
      test_cases: ["TC-001", "TC-002", "TC-003", "TC-004", "TC-005", "TC-006", "TC-007"]

notes: >
  Generated pytest files: tests/test_sim_transport.py (new) and
  tests/test_lifecycle_sim.py (xfail removed), per P06 §1.7.3. Both were
  written during implementation of prompt-50bf25ad; this document records
  them retrospectively. Run: pytest tests/test_sim_transport.py
  tests/test_lifecycle_sim.py::TestLinkLoss -v.

version_history:
  - version: "1.0"
    date: "2026-10-09"
    author: "William Watson"
    changes:
      - "Initial test document for change-50bf25ad."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t05_test"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial test document for change-50bf25ad. |

---

Copyright (c) 2026 William Watson. MIT License.
