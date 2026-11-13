# Proposal — Autonomous Release Run to v1.0.0 (f8d0064b)

Created: 2026 November 13

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 Scope and Assumptions](#20-scope-and-assumptions)
- [3.0 Delegated Approval](#30-delegated-approval)
- [4.0 Work Packages](#40-work-packages)
- [5.0 Execution Protocol](#50-execution-protocol)
- [6.0 Release Gate](#60-release-gate)
- [7.0 Decisions Required](#70-decisions-required)
- [8.0 Risks](#80-risks)
- [9.0 Post-Run Handoff](#90-post-run-handoff)
- [10.0 Session Prompt](#100-session-prompt)
- [References](#references)
- [Version History](#version-history)

---

## 1.0 Summary

- **Objective:** one Claude Code cloud session (model Claude Fable 5.2, acting as worker and reviewer) disposes of every row in `ai/task.md` and brings GTach to a release-candidate state for v1.0.0.
- **Authority:** the owner's approval is delegated to the session for its duration (§3.0). The governance lifecycle still applies in full: issue, change and prompt T-Docs for every `src/` change, closure, task register, traceability.
- **Limit:** the cloud session cannot reach `gtach.local` or `ELM327-Emulator.local`. All human testing on the Pi, including on-device validation (governance P15.17), is done by the owner after the run (§9.0); the session never waits for it. The session therefore ends at a release candidate, not a tagged release.
- **Auditing:** the release-readiness audit is the last work package before release preparation (WP7), so that it covers every change made in the run.
- **Execution profile:** P13.3 Option C (Claude Code, manual invocation), `target_profile: claude_code`, no engine.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Scope and Assumptions

### 2.1 In Scope

- The seven rows of `ai/task.md` at commit `3f47c3e9` (§4.0).
- Defects the session discovers while working. Each is added to `ai/task.md` and resolved in the same run, subject to the severity rule in WP7.
- A release-readiness audit and the release preparation needed to reach the gate in §6.0.

### 2.2 Out of Scope

- New features, redesign, or extension of design scope. Scope extension is decided by the owner, not by the session.
- Display geometry, font sizing and framebuffer decisions. These require measurement on the Pi (on-device measurement is authoritative).
- Git tags, GitHub releases, deployment to the Pi, and pushes to `main` (unless decision D5 says otherwise).
- Changes to the AI-G&O framework files (`ai/engine/`, `ai/governance/`, `ai/profiles/`, `ai/core/`, `ai/webui/`). Framework changes are made in the framework repository first.

### 2.3 Starting State (verified 2026-11-13)

- No active issue, change or prompt T-Docs; all prior triples are closed.
- Last recorded full suite: 780 passed (`report-76ef5387`). Version `0.5.0`.
- `.claude/settings.json` and `.claude/hooks/run-tests.sh` do not exist; the mandatory validation hook (P00.18) is not provisioned (decision D8).
- Earlier cloud sessions installed the project with `pip install -e .[dev]` on Python 3.13 and ran pygame under `SDL_VIDEODRIVER=dummy` without problems. The device runs Python 3.9.
- `ai/workspace/proposal/` and `ai/workspace/report/` are git-tracked, so the session can read this proposal and its reports persist.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Delegated Approval

- **Grant:** for this session only, every governance step that requires human approval or acceptance (P00.9, P04.1, P13.3, P00.14.4, P02.8) is treated as approved by the owner. This is the exemption from `governance.md` granted on 2026-11-13.
- **Not granted:** the exemption does not remove any lifecycle step. Every T-Doc is still created, coupled, iterated and closed per governance. It does not authorise scope extension, framework changes, tags, releases or deployment.
- **Record:** each delegated approval is recorded with `python ai/engine/src/approve.py <uuid> <stage>` (decision D4). This proposal is the written authority; reports cite it as `proposal-f8d0064b`.
- **Escalation:** an item that needs a decision outside this grant is recorded in the run log and in `ai/task.md` (Status `Parked`, with the decision needed), and the session continues with the next item.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Work Packages

Order: WP0 → WP1 → WP2 → WP3 → WP5 → WP4 → WP7 → WP8.

- WP4 (design refresh) follows the task-register work, so that it is done once against the source as it then stands.
- WP7 (audit) is the last work package before release preparation. It audits the whole release scope, including the changes of this run and the refreshed designs. Its remediation triples update the affected designs per P04.3.

| WP | `ai/task.md` row | Disposition (default) | Triple |
|---|---|---|---|
| WP0 | — | Environment and baseline | No |
| WP1 | mypy `python_version = "3.9"` | Keep the 3.9 target; pin mypy (D9) | No (`pyproject.toml`) |
| WP2 | `821919ce`, `9ed1c77e` | Explicit drop (D6) | No (T-Docs already closed) |
| WP3 | pygame `pkg_resources` / setuptools ≥81 | Investigate; minimal guard if needed | Only if `src/` changes |
| WP4 | Design review | Apply the dispositions of `report-71ab3751-design-review` | No (`ai/workspace/` documents) |
| WP5 | Stuck Bluetooth recovery | Deferred to after 1.0 (D3) | No, unless D3 is reversed |
| WP6 | In-car normal use | Remains `Deferred`; owner action (D2) | No |
| WP7 | — | Release-readiness audit (T08) and remediation | Yes, per finding |
| WP8 | — | Release preparation | No (`pyproject.toml`, notes, docs) |

### 4.1 WP0 — Environment and Baseline

- `pip install -e .[dev]`; run `pytest tests/`, `python -m mypy src/`, `flake8` and `black --check` on `src/` and `tests/`. Record the counts in the run log as the baseline.
- If a Python 3.9 interpreter is available, run the suite under it as well. If not, record that.
- A failing baseline is the first defect; it is raised and fixed before other work.

### 4.2 WP1 — mypy Target

- Determine the newest mypy release that still accepts `python_version = "3.9"`, from the mypy changelog or by test.
- Pin the `dev` extra to that bound and confirm `python -m mypy src/` is clean with the 3.9 target.
- If no workable pin exists, record the evidence and park the row for the owner (raising the target loses the check that matters on the device).

### 4.3 WP2 — Render Caching and Conditional Render

- Both triples are closed; both withdrawal conditions are met (frames complete inside budget). Remove the two rows as an explicit drop and record the outcome in the run report. Re-evaluation would need on-device frame times and a new issue.

### 4.4 WP3 — setuptools and `pkg_resources`

- Establish which setuptools version the Pi install path produces (`bin/install.sh`, `bin/pi-install.sh`, Python 3.9 venv) and whether `import pygame` fails with setuptools ≥81.
- If the install path can reach setuptools ≥81, add the smallest guard (for example `setuptools<81` in the Pi install step) and verify `import pygame`. If it cannot, record the evidence and drop the row.
- `bin/` changes are exempt from the triple; a `src/` change is not.

### 4.5 WP4 — Design Documents

- Apply `ai/workspace/report/report-71ab3751-design-review.md` §4.0: retire 4, merge 2 pairs, correct 4 status lines, refresh 15 against the source as it stands after WP5.
- Read each document body before retiring or merging it. Retired documents move to `ai/workspace/design/closed/`.
- A refresh corrects factual drift (file paths, class and function names, status, behaviour now in the source). It does not redesign. Each refreshed document gets a version increment and a Version History row citing `proposal-f8d0064b`.
- Update `ai/workspace/trace/trace-traceability-matrix-master.md` for every triple of this run and for the retired and merged designs.
- Then move `report-71ab3751-design-review.md` to `report/closed/` and remove the row.

### 4.6 WP5 — Stuck Bluetooth Recovery (default: Deferred)

- `comm/transport.py` states a design constraint from issue-5e7a03c4: the transport reports faults and never acts on the host (no adapter reset, rfkill cycle, hciuart restart or shell invocation). Automatic recovery reverses that constraint.
- The fault has not been reproduced (device sessions A and B), and no recovery can be verified without the device.
- Default: the row stays, with Status `Deferred — after 1.0; reverses the issue-5e7a03c4 host-action constraint; needs owner design decision and device reproduction`.

### 4.7 WP7 — Release-Readiness Audit

- Runs after all other work packages except WP8. No audit is performed earlier in the run.
- Strategic audit (P02.9.1) of `src/gtach/`, `bin/`, `pyproject.toml`, `README.md`, `docs/`, `CLAUDE.md` and `ai/context.md`, written as `ai/workspace/audit/audit-<uuid>-release-readiness.md` (T08).
- Scope: defects, release blockers, packaging faults, and documentation that contradicts the source. Not style preferences, refactoring or feature ideas.
- Severity rule (D11):
  - Critical and high: raised as triples and fixed in this run.
  - Medium and low: fixed in this run only when they meet the P04.12 trivial criteria or are document-only; otherwise added to `ai/task.md` as `Deferred — after 1.0`.
  - Any finding that needs display geometry, font sizing or hardware behaviour to be measured: `Deferred` to the owner's device session.
- After remediation of source code, a follow-up audit pass (P02.8.2) confirms closure; then the audit closes and moves to `audit/closed/`.

### 4.8 WP8 — Release Preparation

- Set `version` in `pyproject.toml` per D1.
- Write `releases/RELEASE_NOTES_v1.0.0.md` in the format of the existing release notes, covering changes since the last release notes file, from git history and closed reports.
- Update `README.md` (Version History; anything WP7 found inaccurate).
- Build with `python -m build`; install the wheel into a clean venv; run `gtach --version` and `gtach --validate-config`. Attempt a headless run with a simulated transport and record the result; a platform-related failure in the cloud is recorded, not fixed.
- No tag, no `bin/release.sh`, no deployment.

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Execution Protocol

### 5.1 Per Triple (every `src/` change)

1. Generate the UUID (`python3 -c "import uuid; print(uuid.uuid4().hex[:8])"`) and check it against `ai/` with `rg` for collisions.
2. Read the templates (T06, T07, T03). Write the issue, then the change (with impact analysis and maintenance classification), then the prompt (`target_profile: claude_code`, no `tactical_brief`). Couple them per P03.7, P04.2 and P13.2.
3. Record delegated approvals: `approve.py <uuid> change`, then `approve.py <uuid> prompt`. Re-approve after any edit of an approved document.
4. Implement. Add permanent tests in `tests/`, named by behaviour, with the covered UUIDs in the module docstring (P15.3).
5. Validate progressively (P15.15): the new tests alone, then the affected modules, then the full suite. Also `python -m mypy src/`, and `flake8` and `black --check` on the changed files.
6. Review: start a separate review subagent with a fresh context. Give it the change document and the diff only, and ask for a SHIP or REVISE verdict with evidence. At most three REVISE cycles; then treat the item as BLOCKED: increment issue and change iterations together (P03.7), record, and continue with other work.
7. Write `ai/workspace/report/report-<uuid>-<name>.md` with test counts and the review verdict.
8. Close: move the prompt to `prompt/closed/`. Close the issue and change (status `closed` and `verified`) and move them to `closed/`, unless verification needs the device. In that case, leave them active with status `implemented`, and set the `ai/task.md` row to `Active — awaiting device verification`. Record `approve.py <uuid> accept` when the manifest defines that stage.
9. Update the traceability matrix and `ai/task.md`. Commit and push.

### 5.2 Commits

- Conventional commits citing the UUID, for example `fix: <summary> (<uuid>)`. Each commit ends with the session's attribution trailers.
- At least one commit per triple step (documents, implementation, closure). `approve.py` creates its own commits.
- Push after every completed triple and work package, so that work survives an interruption.

### 5.3 Run Log and Resumption

- Keep `ai/workspace/report/report-f8d0064b-run-log.md`: one row per work package and triple, with status, commit and notes. Update and commit it after every step.
- On any resumption (after a usage limit, a restart or a new session), read the run log and `git log` first, and continue from the first unfinished step. Never redo a committed step.

### 5.4 Document Conventions

- GitHub Flavored Markdown that renders on GitHub and in Obsidian. Layout as in `README.md`: unnumbered H1, `Created: <year> <month> <day>` line for new documents, flat Table of Contents, numbered sections, `---` separators, `[Return to Table of Contents](#table-of-contents)` after each top-level section except Version History, Version History table, and `Copyright (c) 2026 William Watson. MIT License.` after a final `---`.
- GFM heading slugs for all links. No wikilinks and no angle-bracket anchors.
- Neutral, factual language; no claims of fitness for purpose.

### 5.5 Stop Conditions

- Stop an item, record it and continue with the next when the item needs a decision outside §3.0, needs device measurement, or is BLOCKED.
- Stop WP8 if the full suite is not green; report the state instead.
- Never wait for human or device testing. Items that need it are recorded for the owner's test session after the run (§9.0).
- End the run with the final report (§6.0) in every case.

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Release Gate

The session declares the release candidate ready only when all of the following hold:

| # | Check | Evidence |
|---|---|---|
| G1 | Full `pytest tests/` passes; no new xfail or skip without a recorded reason | Run report |
| G2 | `python -m mypy src/` clean with `python_version = "3.9"` | Run report |
| G3 | No new `flake8` or `black` findings in files changed by this run | Run report |
| G4 | No active issue, change or prompt T-Doc, except those awaiting device verification | `ai/workspace/` listing |
| G5 | Every `ai/task.md` row is either removed with a recorded outcome, or `Deferred`/`Parked` with a stated reason and owner action | `ai/task.md` |
| G6 | Release-readiness audit closed, with no open critical or high finding | `audit/closed/` |
| G7 | Wheel and sdist build; the wheel installs in a clean venv; `gtach --version` reports the new version | Run report |
| G8 | Release notes, README and version agree | Files |

Final deliverable: `ai/workspace/report/report-f8d0064b-v1-release-run.md`, with the gate table, the list of triples, the remaining `ai/task.md` rows, and the owner's on-device checklist (§9.0). If the session works on a branch, it opens a pull request whose description summarises the report.

[Return to Table of Contents](#table-of-contents)

---

## 7.0 Decisions Required

D1 to D4 were accepted by the owner on 2026-11-13. D5 to D11 apply as the stated defaults unless the owner changes them before the run.

| # | Decision | Default (recommended) | Alternative |
|---|---|---|---|
| D1 | Version at the end of the run | `1.0.0rc1` in `pyproject.toml`; the owner sets `1.0.0` and tags after on-device acceptance | `1.0.0` directly; a defect found on the device then needs `1.0.1` |
| D2 | Hardware gate for v1.0.0 | Bench test on the Pi with the emulator before the tag; in-car test after 1.0 | In-car test required before the tag (blocked until the vehicle is prepared) |
| D3 | Stuck Bluetooth recovery | Deferred to after 1.0 (§4.6) | Implement now: design update, triple, mocked tests, device verification later |
| D4 | Recording delegated approvals | `approve.py` for change, prompt and accept | Not recorded; reports cite this proposal only |
| D5 | Branch | Session branch and pull request; the owner merges | Push directly to `main` |
| D6 | Rows `821919ce`, `9ed1c77e` | Explicit drop | Keep as `Deferred` after 1.0 |
| D7 | Existing `black`/`flake8` debt in untouched files | Out of scope; one `ai/task.md` row, `Deferred` | One mechanical formatting triple (large diff, harder review) |
| D8 | Validation hook (P00.18) | Not provisioned; the hook assumes `tests/<component>/`, while GTach tests are flat. The run executes P15.15 manually. One `ai/task.md` row | Provision an adapted hook in this run |
| D9 | mypy target | Keep 3.9; pin mypy | Raise the target to the oldest version mypy accepts |
| D10 | T03 prompts | Created for every triple (lifecycle completeness; overwatch coupling checks) | Omitted; the change document serves as the task |
| D11 | Audit findings below high | Fixed only if trivial or document-only; otherwise `Deferred` | Fix all findings in this run |

[Return to Table of Contents](#table-of-contents)

---

## 8.0 Risks

| Risk | Effect | Mitigation |
|---|---|---|
| Worker reviews its own work | Defects pass review | Review subagent with a fresh context per triple; the owner reviews the pull request |
| Cloud runs Python 3.13; device runs 3.9 | 3.9-incompatible code passes in the cloud | mypy 3.9 target (D9); a 3.9 interpreter if available; device bench test |
| No hardware access | Hardware-facing changes unverified | Device-dependent triples stay active; owner checklist (§9.0) |
| Usage limits stop the session | Run halts mid-step | Run log and per-step commits (§5.3). Auto-continue after a limit reset is documented for Claude Code Desktop and the CLI [1][2]; behaviour in a cloud session was not verified. A weekly limit does not reset within the run |
| Large volume of changes | Owner review burden | One commit series per triple, one report per triple, final summary |
| Scope growth through audit findings | Run does not converge | Severity rule (D11); scope extension excluded (§2.2) |

[Return to Table of Contents](#table-of-contents)

---

## 9.0 Post-Run Handoff

Owner actions after the session. All human testing on the Pi is done here, in one session:

1. Review the final report and the pull request; merge.
2. Deploy the release candidate: `./bin/deploy.sh`.
3. Bench test on the Pi with `ELM327-Emulator.local`: start-up, connection, live RPM, link loss and restore, setup flow, options screens; plus every item the final report lists as awaiting device verification.
4. Close the device-pending triples, or raise issues for failures.
5. Set `version = "1.0.0"`, rebuild, push, and run `./bin/release.sh`.
6. In-car test after 1.0 (D2).

[Return to Table of Contents](#table-of-contents)

---

## 10.0 Session Prompt

Paste into a new Claude Code cloud session on `William12556/GTach`, model Claude Fable 5.2, after this proposal is committed and pushed.

```text
You are the worker and reviewer for GTach in a single autonomous run.
Plan: ai/workspace/proposal/proposal-f8d0064b-v1-release-autonomous-run.md
(read it completely first, then CLAUDE.md, README.md,
ai/governance/software-engineering/governance.md, ai/task.md and the
templates in ai/governance/software-engineering/templates/).

Authority: for this session, the owner's approval is delegated to you
as described in proposal §3.0. Every governance lifecycle step still
applies. In particular, every src/ change gets an issue, change and
prompt T-Doc with one UUID, and each is closed and moved to closed/
per proposal §5.1.

Objective: dispose of every ai/task.md row and reach the release gate
in proposal §6.0, following the work-package order in §4.0 and the
decisions in §7.0. Defects you discover go into ai/task.md and are
resolved in this run under the severity rule of WP7. Run the
release-readiness audit (WP7) last, after all other work packages and
before release preparation (WP8).

Never wait for human or device testing. All testing on the Pi is done
by the owner after this run; record items that need it in the final
report.

Constraints: no scope extension, no display geometry or font sizing
changes, no framework (ai/engine, ai/governance, ai/profiles) changes,
no tags, releases or deployment. This environment cannot reach
gtach.local or ELM327-Emulator.local.

Resumption: keep ai/workspace/report/report-f8d0064b-run-log.md current
and push after every completed step. If this session is resumed, read
the run log and git log first and continue from the first unfinished
step.

Finish with ai/workspace/report/report-f8d0064b-v1-release-run.md and,
if you are on a branch, a pull request summarising it.
```

[Return to Table of Contents](#table-of-contents)

---

## References

[1] ANTHROPIC, 2026. *What's new, week 33* [online]. Claude Code documentation. Available from: https://code.claude.com/docs/en/whats-new/2026-w33 [Accessed 13 November 2026].

[2] DEVELOPERSDIGEST, 2026. *Claude Code error: session limit reached* [online]. Available from: https://www.developersdigest.tech/errors/claude-code/session-limit-reached [Accessed 13 November 2026].

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-13 | Initial proposal for owner review |
| 1.1 | 2026-11-13 | D1 to D4 accepted; §1.0, §4.0, §4.5, §4.7: audit moved to the last work package before release preparation; §5.5, §9.0, §10.0: all human testing on the Pi after the run, the session never waits for it |

---

Copyright (c) 2026 William Watson. MIT License.
