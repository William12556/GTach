Created: 2026 July 29

# Task List

All open work: open triples, items not yet raised as a triple, and
deferred or parked items (governance P00.20). A row is removed once its
outcome is recorded (a closed triple, or an explicit drop).

| ID | Item | Status | References |
| --- | --- | --- | --- |
| `cfa4e617` | Run 1 — dead code removal (audit-71ab3751 E01, W1; decisions D2, D3, D4). Includes the mypy candidates `TouchAction.DRAG` and the unreachable manual-entry screen | Open — prompt awaiting approval | `issue-cfa4e617`, `change-cfa4e617`, `prompt-cfa4e617`; `proposal-71ab3751` |
| `b4f9607a` | Run 2 — communication layer (A01–A07, A09–A12, F03, X01 and B06 comm parts). Includes the discovery-fallback mechanism and the mypy candidate `last_connected` accepts str | Open — prompt awaiting approval | `issue-b4f9607a`, `change-b4f9607a`, `prompt-b4f9607a` |
| `042dd7ff` | Run 3 — application lifecycle, logging, utils (B01–B04, B06, B07, E02–E06, F01, O1). Includes: `[tool.mypy] platform = "linux"`; `--validate-config` without file logging; `Reset outcome` record; log paths under `GTACH_HOME`; `load_engine_profile` DEBUG record; mypy candidate unchecked `get_state_info` | Open — prompt awaiting approval | `issue-042dd7ff`, `change-042dd7ff`, `prompt-042dd7ff` |
| `34781bfe` | Run 4 — setup flow (D01–D04, C01, C02, C08, X01 and A09 display parts, O4, W2). Includes the discovery-fallback user interface and the mypy candidate Optional surface to SetupDisplayManager | Open — awaiting approval of `design-a3b4c5d6` v2.0 and of the prompt; not before device session A | `issue-34781bfe`, `change-34781bfe`, `prompt-34781bfe`; `design-a3b4c5d6` |
| `2550e4ee` | Run 5 — gauge display and touch (C03–C07, C09, F02, O2, O5, A09 display-manager part). Includes `get_font(18)` in `_render_disconnected` and the mypy candidate `rpm_bands` default None | Open — prompt awaiting approval | `issue-2550e4ee`, `change-2550e4ee`, `prompt-2550e4ee` |
| — | Device session A (after runs 1 to 3) and device session B (after run 5), then one version increment (suggested 0.5.0) | Open — follows the runs | `proposal-71ab3751` §7.0 |
| — | `[tool.mypy] python_version = "3.9"` is not selectable in the installed mypy release; the device runs Python 3.9. Decide: pin an older mypy, or raise the value | Open — owner decision | `change-042dd7ff` notes; `pyproject.toml` |
| `821919ce` | Render caching | Deferred — own withdrawal condition met (frames complete well inside budget); not implemented. Re-evaluate with measured frame times after run 5 | `issue-821919ce`, `change-821919ce` |
| `9ed1c77e` | Conditional render (Part 3 only — `fps_limit` reduction and import/f-string housekeeping already shipped) | Deferred — same basis as `821919ce`; not implemented | `issue-9ed1c77e`, `change-9ed1c77e` |
| — | In-car normal use (audit-36b6ea95 Session I); vehicle not yet prepared. General regression check; to be done on the version that follows run 5 | Open — awaiting vehicle | `ai/workspace/test/closed/test-36b6ea95-on-device-verification.md` §4.9 |
| — | New work: automatic recovery from the stuck Bluetooth state. After an out-of-range link loss (2026-10-08 13:45) every reconnect failed with EBUSY ('Device or resource busy') for 2.5 min, including after the adapter was back in range; GTach correctly reported 'bluetooth wedged - reset required', but only a Pi reset restored the link. Scope (e.g. controller reset via btmgmt/hciconfig, or RFCOMM/ACL release, before falling back to operator reset) to be decided | Open — re-test after run 2 with the process's sockets listed during the fault (audit-71ab3751 A01 is one in-process mechanism); T03 not yet raised | `comm/transport.py`, `comm/rfcomm.py`; related `issue-5e7a03c4`; evidence `logs/error.log` 2026-10-08 13:45–13:48 |
| — | Review `ai/workspace/design/` for stale designs and decide per document whether to update, merge or retire it | Open — triage written; per-document decisions pending | `ai/workspace/report/report-71ab3751-design-review.md` |
| — | Close the four open scheduled audits (005f1cf4, 8264c76d, 008e2929, fccd5931) as superseded by audit-71ab3751 §5.0 | Open — owner decision | `ai/workspace/audit/` |
| — | pygame 2.6.1 imports the deprecated `pkg_resources`; setuptools 81 or newer may break the import | Open — monitor; pin `setuptools<81` or upgrade pygame if it breaks | `pyproject.toml` |

---

Copyright (c) 2026 William Watson. MIT License.
