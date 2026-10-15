Created: 2026 October 15

# GTach Scheduled Daily Audit — 2026-10-15 (audit-fccd5931)

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Method](<#2.0 method>)
- [3.0 Activity Summary](<#3.0 activity summary>)
- [4.0 Finding F1: Refused Connects Still Count Toward the Wedge Threshold](<#4.0 finding f1: refused connects still count toward the wedge threshold>)
- [5.0 Finding F2: Wall-Clock Step Test Cannot Detect a Frozen Sweep](<#5.0 finding f2: wall-clock step test cannot detect a frozen sweep>)
- [6.0 Observations](<#6.0 observations>)
- [7.0 Changes Reviewed Without Finding](<#7.0 changes reviewed without finding>)
- [8.0 Recommendations](<#8.0 recommendations>)
- [Version History](<#version history>)

---

## 1.0 Purpose

This audit reviews code changes committed to William12556/GTach between 2026-10-14 01:03 UTC and 2026-10-15 01:03 UTC for defects.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Method

- The anonymous `git clone` failed with an authentication prompt. The repository is private, which the GitHub MCP search result confirms (`"private":true`).
- The review therefore used the GitHub MCP tools: `list_commits` for the window, `get_commit` for per-commit file statistics, `get_file_contents` at the commit SHA for every changed code-bearing file, `list_tags`, `search_code`, `list_issues` and `list_pull_requests`.
- `get_commit` returned file statistics without patch text. Changed code-bearing files were read in full at the post-change revision; pre-change text was inferred from the commit messages and in-file comments.
- Documentation (`*.md`) changes were counted, not reviewed.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Activity Summary

| Repository | Commits | File changes | Insertions | Deletions | New tags |
|---|---|---|---|---|---|
| William12556/GTach | 14 | 40 | 993 | 112 | 0 |

File changes by extension: `.md` 23, `.py` 9, `.yaml` 6, `.toml` 1, `.txt` 1.

Code-bearing commits: `0e3212f` (transport ECONNREFUSED, Setup Complete hold), `c6e915d` (test module alias rename), `a039165` (remove `_global_performance_manager`), `33bed49` (version 0.4.10 to 0.4.12), `bb29226` (engine `api_key_keychain`), `370ffda` (`ai/config.yaml` role bindings), `ae1ea9f` (SimTransport monotonic sweep). The remaining commits are approvals (`ai/approvals.yaml`) or documentation.

Open issues: 0. Open pull requests: 0.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Finding F1: Refused Connects Still Count Toward the Wedge Threshold

- **Classification:** Confirmed. **Severity:** Low.
- **Location:** `src/gtach/comm/transport.py`, `OBDTransport.connect`, commit `0e3212f`.
- **Evidence:** The change excludes ECONNREFUSED from the escalation condition only:

```python
with self._lock:
    self._consecutive_connect_failures += 1
    failures = self._consecutive_connect_failures
...
if (
    self._ADAPTER_CHECKS
    and failures >= self._MAX_CONSECUTIVE_CONNECT_FAILURES
    and cause != "no bluetooth controller"
    and cause != _CONNECT_FAULT_CAUSES[_errno.ECONNREFUSED]
    and _bluetooth_adapter_present()
):
    cause = _WEDGED_LINK_CAUSE
```

- **Defect:** Every refused connect still increments `_consecutive_connect_failures`, and the counter latches until a success. The commit's own rationale is that a refusing peer proves the controller works. After six or more refusals, the first non-refused failure (for example ETIMEDOUT or EHOSTDOWN when the adapter goes out of range) immediately reports `bluetooth wedged - reset required`, which is the misdiagnosis the change set out to prevent.
- **Test gap:** `test_refused_connects_do_not_escalate` exercises only an uninterrupted run of refusals and does not cover a refusal run followed by a different errno.
- **Impact:** A diagnostic string on the DISCONNECTED screen. Reconnection behaviour is unaffected.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Finding F2: Wall-Clock Step Test Cannot Detect a Frozen Sweep

- **Classification:** Confirmed. **Severity:** Low.
- **Location:** `tests/test_sim_transport.py`, `test_rpm_sweep_ignores_wall_clock_steps`, commit `ae1ea9f`.
- **Evidence:** The mock returns 1000.0 at construction and 1030.0 at the query, then asserts the same value as the t = 0 test:

```python
result = transport.send_command("010C")
assert result == "41 0C 39 08"
```

- **Defect:** At t = 30 s the formula `800 + 2850 * (1 + sin(t * 2π / 60))` evaluates `sin(π) ≈ 0`, giving 3650 RPM, the same value as t = 0. The assertion therefore also passes if the elapsed time is ignored entirely. No wall-clock step is simulated either: `time.time` raises if called, which only duplicates `test_rpm_sweep_uses_monotonic_clock`. The test's name claims coverage it does not provide.
- **Impact:** Test quality only. The production change (`time.time()` to `time.monotonic()` in `__init__` and `_compute_rpm_response`) is correct.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Observations

- The repository is private. The validated anonymous-clone method no longer works for this repository. Future runs should use the GitHub MCP tools directly, or the clone needs credentials.
- `sim_transport.py` keeps two stale comments outside the changed lines: `_handle_command` says "~12s period", and `_compute_rpm_response` says the sweep "begins near minimum at launch". The period is 60 s, and the sweep starts at the 3650 RPM midpoint because `sin(0) = 0`. These comments are not defects in this window's change.
- `test_setup_complete_hold.py` patches `setup_mod.time.monotonic` and `setup_mod.time.sleep`, which is the global `time` module. `monkeypatch` restores both, so the patch is safe in a serial run.

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Changes Reviewed Without Finding

- `src/gtach/display/setup.py` (`0e3212f`): The COMPLETE hold uses a `time.monotonic()` deadline and keeps the heartbeat running. The shutdown flag is re-checked every 0.05 s, and `on_complete` is skipped on a shutdown during the hold. COMPLETE is terminal (`break`), so `complete_since` needs no reset.
- `tests/test_setup_complete_hold.py` (`0e3212f`, `c6e915d`): Renaming the alias to `setup_mod` correctly avoids pytest's `setup_module` xunit hook. The assertions match the implementation.
- `src/gtach/display/performance/__init__.py` (`a039165`): `_global_performance_manager` was removed. `search_code` finds the symbol only in Markdown documents, with no remaining code references.
- `ai/engine/src/providers.py` (`bb29226`): `_keychain_secret` runs `security` with an argument list (no shell), a 10 s timeout and `check=False`. It maps the timeout, OSError and decode failures to `ConfigError` without exception chaining and never places the secret in a message. Key-source precedence (env, then Keychain, then the unset-env error) matches the docstring.
- `src/gtach/comm/sim_transport.py` (`ae1ea9f`): The elapsed-time origin and the read now both use `time.monotonic()`. No other `time.time()` use remains in the file.
- `pyproject.toml`, `ai/config.yaml`, `ai/approvals.yaml`: These are version, configuration and approval-record changes with no executable logic.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Recommendations

1. F1: Exclude refusals from the wedge evidence by not incrementing `_consecutive_connect_failures`, or by resetting it, when the cause is the ECONNREFUSED cause. Add a test for six refusals followed by one ETIMEDOUT, which should report `connection timed out`.
2. F2: Assert a value that differs from t = 0 (for example t = 15 s, 6500 RPM, `41 0C 65 90`), or replace the test with one that steps a mocked `time.time` backward while `monotonic` advances.
3. Update the period and starting-point comments in `sim_transport.py` when that file is next edited.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-15 | Initial scheduled daily audit. |

Copyright (c) 2026 William Watson. MIT License.
