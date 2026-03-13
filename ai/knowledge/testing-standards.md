Created: 2026 March 05

# Testing Standards

Operational decision rules for Strategic Domain execution of P06 (Test). Consult before creating test documents, selecting test types, or executing validation sequences.

---

## Table of Contents

[Test Type Selection](<#test type selection>)
[Progressive Validation Sequence](<#progressive validation sequence>)
[Coupling Verification](<#coupling verification>)
[Test Isolation Requirements](<#test isolation requirements>)
[Script Lifecycle Rules](<#script lifecycle rules>)
[Constraint Summary](<#constraint summary>)
[Version History](<#version history>)

---

## Test Type Selection

Apply these rules when determining test type per P06 §1.7.16.

| Condition | Required Test Type |
|---|---|
| New component implemented | Unit (mandatory) |
| Component interacts with another component | Integration |
| Full application deployment verification | System |
| Requirement acceptance required | Acceptance |
| Any code change | Regression (full permanent suite) |
| NFR validation required | Performance |

**Rules:**

- Unit tests are mandatory for every component. No exceptions.
- Do not create integration tests as a substitute for unit tests.
- System and acceptance tests execute on target deployment platform only — never on development platform.
- Performance tests execute on target deployment platform only.
- Platform definitions are in project design documents (P06 §1.7.17).

[Return to Table of Contents](<#table of contents>)

---

## Progressive Validation Sequence

Sequence is mandatory and must not be reordered or skipped per P06 §1.7.15.

```
Stage 1: Targeted     → verify specific fix (ephemeral script)
Stage 2: Integration  → verify no ripple effects (component subdirectories)
Stage 3: Regression   → verify full suite passes (all permanent tests)
```

**Rules:**

- Do not proceed to Stage 2 until Stage 1 passes.
- Do not proceed to Stage 3 until Stage 2 passes.
- Do not initiate document closure until Stage 3 passes.
- A Stage 1 or Stage 2 failure creates a new issue via P04. Do not proceed with validation.
- Regression validation is required before every document closure, regardless of change scope.

[Return to Table of Contents](<#table of contents>)

---

## Coupling Verification

Verify before test execution and before document closure per P06 §1.7.12.

**Before test execution:**

- Test `coupled_docs.prompt_ref` references a valid prompt UUID.
- Test iteration number equals source prompt iteration number.
- If mismatch: do not execute. Resolve iteration synchronization first.

**Before result document creation:**

- Result `coupled_docs.test_ref` references the parent test UUID.
- Result iteration number equals parent test iteration number.

**Before document closure:**

- All coupled documents (prompt, test, result) share the same iteration number.
- No orphaned documents exist in the coupled set.
- Bidirectional links are verifiable: prompt ↔ test ↔ result.

**Rule:** Coupling violations block workflow progression. Do not proceed until resolved.

[Return to Table of Contents](<#table of contents>)

---

## Test Isolation Requirements

Apply when generating pytest files per P06 §1.7.8 and §1.7.9.

**External dependencies** (network, database, hardware, filesystem, system services):

- Mock all external dependencies in unit tests without exception.
- Use `unittest.mock` (`Mock`, `patch`, `MagicMock`) to isolate at interface boundaries.
- Integration tests on target platform may use actual subsystems where explicitly required.

**Filesystem operations:**

- Use `tempfile.mkdtemp()` for tests that create or modify files.
- Clean up in `tearDown` via `shutil.rmtree()`.

**Global state and singletons:**

- Save state in `setUp`, restore in `tearDown`.

**Test independence:**

- Tests must not depend on execution order.
- Tests must produce consistent results across repeated runs.

[Return to Table of Contents](<#table of contents>)

---

## Script Lifecycle Rules

Apply when managing ephemeral validation scripts per P06 §1.7.10 and §1.7.11.

**Ephemeral scripts:**

- Location: `tests/` root level only.
- Naming: `test_validation_<issue_uuid>.py`.
- Purpose: Targeted validation of a specific fix.
- Must be removed after Stage 3 regression validation passes and document closure is initiated.
- Must not be committed to the permanent regression suite.

**Permanent tests:**

- Location: `tests/<component>/` subdirectories only.
- Never deleted unless the functionality they test is removed.
- Always included in regression validation.

**Rule:** An ephemeral script that persists beyond document closure is a lifecycle violation.

[Return to Table of Contents](<#table of contents>)

---

## Constraint Summary

| Constraint | Rule |
|---|---|
| Unit tests | Mandatory for every component |
| System/acceptance/performance tests | Target platform only |
| Progressive validation | Stages 1→2→3 in order, no skipping |
| Document closure | Requires Stage 3 regression pass |
| Coupling mismatch | Blocks workflow; resolve before proceeding |
| External dependencies in unit tests | Always mocked |
| Ephemeral scripts | Removed at document closure |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-03-05 | Initial document; operational decision rules for P06 execution |

---

Copyright (c) 2025 William Watson. This work is licensed under the MIT License.
