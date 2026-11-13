# Report — Design Document Review (71ab3751)

Created: 2026 November 11

## Table of Contents

- [1.0 Summary](#10-summary)
- [2.0 Method and Limits](#20-method-and-limits)
- [3.0 Dispositions](#30-dispositions)
- [4.0 Recommendations](#40-recommendations)
- [Version History](#version-history)

---

## 1.0 Summary

- This report covers the `ai/task.md` row "Review `ai/workspace/design/` for stale designs".
- 30 design documents were triaged. One was updated in this session (`a3b4c5d6`, v2.0, awaiting approval).
- Proposed dispositions: retire 4, merge 2 pairs, correct a status line in 4, refresh 15 once after run 5, no action for 4 (one of these is also the kept half of a merge pair).
- No design file was moved, merged or deleted. Each disposition needs the owner's decision.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Method and Limits

- **Evidence:** the `document_info` block of each design (`source_file`, `version`, `date`, `status`) compared with the file layout of `src/gtach/` at commit `94ce959b`.
- **Limit:** the document bodies were not read, except `a3b4c5d6`. A disposition of "refresh" therefore states that the document predates the present source, not that a specific statement in it is wrong.
- **Confidence:** high where the named source file does not exist or the status line contradicts the source; medium for the merge direction of the two duplicate pairs; low for the extent of drift in documents marked "refresh".
- **Verification:** read the body of each "retire" and "merge" candidate before acting on it.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Dispositions

### 3.1 Retire

| Design | Evidence | Note |
|---|---|---|
| `d4e5f6a7` component_comm_bluetooth_manager | `source_file` `comm/bluetooth.py` does not exist; `BluetoothManager` was replaced by `OBDTransport` and its subclasses | Superseded by `b1c2d3e4` and `c2d3e4f5` |
| `c3d4e5f6` component_core_async_sync_bridge | `core/thread.py` defines no bridge class | Describes a component that is not in the source |
| `g1h2i3j4` gesture_reference | Identifier is not hexadecimal; describes gestures whose code is removed by change-cfa4e617 | Retire after run 1 |
| `e1f2a3b4` component_display_performance_monitor | `source_file` `display/performance.py` does not exist (now `display/performance/monitor.py`); 4.5 kB | Retire, or rewrite as a short note after run 1 reduces the monitor |

### 3.2 Merge

| Keep | Fold in, then retire | Evidence |
|---|---|---|
| `a6b7c8d9` device store (v1.1, 2026-10-07) | `f6a7b8c9` (v1.0, 2025-12-29) | Same component; `a6b7c8d9` is the later document |
| `f5a6b7c8` OBD protocol (2026-03-24) | `e5f6a7b8` (2025-12-29) | Same component; `f5a6b7c8` postdates the transport redesign |

### 3.3 Correct the Status Line

These documents state "New — does not exist in current source" for code that exists.

| Design | Source that exists |
|---|---|
| `b1c2d3e4` component_comm_transport | `comm/transport.py` |
| `c2d3e4f5` component_comm_rfcomm_transport | `comm/rfcomm.py` |
| `d3e4f5a6` component_comm_tcp_transport | `comm/tcp_transport.py` |
| `e4f5a6b7` component_comm_serial_transport | `comm/serial_transport.py` |

`f5a6b7c8` carries a similar transitional status ("replace BluetoothManager dependency with OBDTransport"), which is complete in the source.

### 3.4 Refresh Once, After Run 5

| Design | Evidence |
|---|---|
| `gtach-master` | v0.2.0, 2025-12-29; application is at 0.4.13 |
| `2c6b8e4d` domain_display, `4f8a2b1c` domain_core, `9a1f3c7e` domain_utils | v1.0, 2025-12-29 |
| `7d3e9f5a` domain_comm | v2.0, 2026-03-24; predates the October changes |
| `a1b2c3d4` thread manager, `b2c3d4e5` watchdog | v1.0, 2025-12-29; both modules changed in October |
| `b8c9d0e1` display manager | v1.0, 2025-12-29; `manager.py` has grown to 2,690 lines |
| `c9d0e1f2` rendering engine | `source_file` `display/rendering.py` does not exist (now `display/rendering/engine.py`) |
| `d0e1f2a3` touch coordinator | `source_file` `display/input.py` does not exist (now `display/input/touch_coordinator.py`); run 1 removes most of the described surface |
| `c5d6e7f8` platform detector | run 1 reduces `utils/platform.py` |
| `a7b8c9d0` bluetooth device, `f2a3b4c5` splash, `d6e7f8a9` terminal restorer, `e7f8a9b0` dependency validator | v1.0, 2025-12-29 |

### 3.5 No Action

| Design | Evidence |
|---|---|
| `a3b4c5d6` setup manager | v2.0 written in this session; awaiting approval |
| `a6b7c8d9` device store | v1.1, 2026-10-07 |
| `b4c5d6e7` config manager | v2.0, 2026-10-07 |
| `f8a9b0c1` home | v2.0, 2026-10-07 |

Runs 1 and 3 change the configuration schema and the device-store interface slightly; `a6b7c8d9` and `b4c5d6e7` then need a one-line update each, which the change documents list under design updates.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Recommendations

1. **Now:** retire `d4e5f6a7` and `c3d4e5f6` to `design/closed/`, and correct the four status lines of 3.3. These are document changes and need no issue.
2. **After run 1:** retire `g1h2i3j4`; decide `e1f2a3b4`.
3. **Before run 2:** merge the two duplicate pairs, so that runs 2 and 4 cite one design each.
4. **After run 5:** refresh the documents of 3.4 in one planner session against the final source, starting with the master and the four domain designs. Refreshing earlier would be repeated after each run.
5. **Trade-off:** retiring instead of rewriting loses the 2025 rationale in those files; it stays available in git history.

The `ai/task.md` row stays open until the owner has decided these points.

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial review (metadata triage) |

---

Copyright (c) 2026 William Watson. MIT License.
