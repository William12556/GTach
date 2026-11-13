# Traceability Matrix

Created: 2025 December 27

## Table of Contents

- [1.0 Status of This Matrix](#10-status-of-this-matrix)
- [2.0 Functional Requirements](#20-functional-requirements)
- [3.0 Non-Functional Requirements](#30-non-functional-requirements)
- [4.0 Component Mapping](#40-component-mapping)
- [5.0 Design Document Cross-Reference](#50-design-document-cross-reference)
- [6.0 Retired and Merged Designs](#60-retired-and-merged-designs)
- [7.0 Test Coverage](#70-test-coverage)
- [8.0 Changes and Audits](#80-changes-and-audits)
- [9.0 Bidirectional Navigation](#90-bidirectional-navigation)
- [Version History](#version-history)

---

## 1.0 Status of This Matrix

- Sections 4.0 to 8.0 link design documents, source and tests as they stand at the end of run `f8d0064b` (2026-11-13).
- Sections 2.0 and 3.0 (requirement rows) are not populated. `requirements-gtach-master.md` predates the present source in several places (for example a macOS development mode and layout switching by swipe), so a requirement-level mapping needs a requirements review first. This is recorded in `ai/task.md`.
- Closed issue, change and prompt documents before this run are traced through their shared UUID in `ai/workspace/{issues,change,prompt}/closed/` and through the UUIDs cited in test module docstrings (governance P15.3); they are not listed here.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Functional Requirements

| ID | Requirement | Design | Code | Test | Status |
|---|---|---|---|---|---|
| — | Not populated (see §1.0) | | | | |

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Non-Functional Requirements

| ID | Requirement | Target | Design | Code | Test | Status |
|---|---|---|---|---|---|---|
| — | Not populated (see §1.0) | | | | | |

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Component Mapping

| Component | Design | Source | Tests |
|---|---|---|---|
| `GTachApplication`, CLI, logging | `design-gtach-master` §7.0, §11.0 | `src/gtach/app.py`, `src/gtach/main.py` | `test_lifecycle_sim.py`, `test_lifecycle_logging_utils.py`, `test_logging_policy.py`, `test_error_log.py`, `test_stack_dump_handler.py`, `test_stack_dump_toggle.py`, `test_stacks_log_rotation.py`, `test_package_import.py` |
| `ThreadManager` | `design-a1b2c3d4` | `src/gtach/core/thread.py` | `test_thread_lifecycle.py`, `test_callbacks_outside_locks.py` |
| `WatchdogMonitor` | `design-b2c3d4e5` | `src/gtach/core/watchdog.py` | `test_watchdog_lock_discipline.py`, `test_watchdog_process_termination.py`, `test_monotonic_watchdog_timing.py` |
| `OBDTransport`, `select_transport` | `design-b1c2d3e4` | `src/gtach/comm/transport.py` | `test_connect_error_classification.py`, `test_comm_layer_defects.py`, `test_reconnect_path.py`, `test_link_loss_recovery.py`, `test_response_alignment.py`, `test_transport_heartbeat.py` |
| `RFCOMMTransport` | `design-c2d3e4f5` | `src/gtach/comm/rfcomm.py` | `test_connect_error_classification.py`, `test_reconnect_path.py` |
| `TCPTransport` | `design-d3e4f5a6` | `src/gtach/comm/tcp_transport.py` | `test_comm_layer_defects.py`, `test_response_alignment.py` |
| `SerialTransport` | `design-e4f5a6b7` | `src/gtach/comm/serial_transport.py` | `test_comm_layer_defects.py`, `test_response_alignment.py` |
| `SimTransport`, `SimBluetoothPairing` | `design-7d3e9f5a` §4.0 | `src/gtach/comm/sim_transport.py`, `src/gtach/comm/sim_bluetooth.py` | `test_sim_transport.py`, `test_lifecycle_sim.py`, `test_task_register_fixes.py` |
| `OBDProtocol` | `design-f5a6b7c8` | `src/gtach/comm/obd.py` | `test_engine_off_state.py`, `test_obd_settle.py`, `test_response_alignment.py` |
| `DeviceStore` | `design-a6b7c8d9` | `src/gtach/comm/device_store.py` | `test_device_store_shared.py` |
| `BluetoothDevice` | `design-a7b8c9d0` | `src/gtach/comm/models.py` | `test_bluetooth_device_conversion.py` |
| `BluetoothPairing` | `design-7d3e9f5a` §4.0, `design-a3b4c5d6` | `src/gtach/comm/pairing.py`, `src/gtach/comm/system_bluetooth.py` | `test_setup_flow.py`, `test_obd_verify_busy_retry.py`, `test_medium_defects.py` |
| `DisplayManager`, `TouchHandler` | `design-b8c9d0e1` | `src/gtach/display/manager.py`, `src/gtach/display/touch.py` | `test_disconnected_screen.py`, `test_engine_off_state.py`, `test_gauge_display_touch.py`, `test_rpm_signal_conditioning.py`, `test_touch_dispatch.py`, `test_setup_and_gauge.py` |
| `DisplayRenderingEngine` | `design-c9d0e1f2` | `src/gtach/display/rendering/` | `tests/display/rendering/` |
| `TouchEventCoordinator` | `design-d0e1f2a3` | `src/gtach/display/input/` | `test_touch_dispatch.py`, `test_callbacks_outside_locks.py` |
| `SplashScreen` | `design-f2a3b4c5` | `src/gtach/display/splash.py`, `src/gtach/display/graphics/` | `test_monotonic_durations.py` |
| `SetupDisplayManager` and setup components | `design-a3b4c5d6` | `src/gtach/display/setup.py`, `src/gtach/display/setup_components/`, `src/gtach/display/setup_models.py`, `src/gtach/display/async_operations.py` | `test_setup_flow.py`, `test_setup_complete_hold.py`, `test_setup_lock_order.py`, `test_device_list_focus.py`, `test_session_b_findings.py`, `test_welcome_error_message.py` |
| Touch interface, performance monitor, typography, models | `design-2c6b8e4d` §4.0 | `src/gtach/display/touch_interface.py`, `src/gtach/display/performance/`, `src/gtach/display/typography.py`, `src/gtach/display/models.py` | `test_performance_instrumentation.py`, `test_gauge_display_touch.py` |
| `ConfigStore` | `design-b4c5d6e7` | `src/gtach/utils/config.py` | `test_config_store.py` |
| `gtach_home` | `design-f8a9b0c1` | `src/gtach/utils/home.py` | `test_config_store.py`, `test_lifecycle_logging_utils.py` |
| `PlatformDetector` | `design-c5d6e7f8` | `src/gtach/utils/platform.py` | `test_platform_detection.py` |
| `TerminalRestorer` | `design-d6e7f8a9` | `src/gtach/utils/terminal.py` | `test_lifecycle_logging_utils.py` |
| `DependencyValidator` | `design-e7f8a9b0` | `src/gtach/utils/dependencies.py` | `test_lifecycle_logging_utils.py`, `test_platform_detection.py` |
| `wait_for_event`, updater, `reboot_device`, stack dump, acknowledgement state | `design-9a1f3c7e` §4.0 | `src/gtach/utils/waits.py`, `updater.py`, `pi_reset.py`, `stack_dump.py`, `ack_state.py` | `test_monotonic_waits.py`, `test_update_version_ordering.py`, `test_lifecycle_logging_utils.py`, `test_pi_reset.py`, `test_stack_dump_handler.py` |
| Packaging and scripts | `design-gtach-master` §5.0 | `pyproject.toml`, `bin/` | `test_packaging_and_scripts.py`, `test_package_import.py` |

Test paths without a directory are in `tests/`.

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Design Document Cross-Reference

| Design document | Tier | Version | Code |
|---|---|---|---|
| `design-gtach-master` | 1 | 3.0 | `src/gtach/` |
| `design-4f8a2b1c-domain_core` | 2 | 2.0 | `src/gtach/core/` |
| `design-7d3e9f5a-domain_comm` | 2 | 3.0 | `src/gtach/comm/` |
| `design-2c6b8e4d-domain_display` | 2 | 2.0 | `src/gtach/display/` |
| `design-9a1f3c7e-domain_utils` | 2 | 2.0 | `src/gtach/utils/` |
| `design-a1b2c3d4-component_core_thread_manager` | 3 | 2.0 | `core/thread.py` |
| `design-b2c3d4e5-component_core_watchdog_monitor` | 3 | 2.0 | `core/watchdog.py` |
| `design-b1c2d3e4-component_comm_transport` | 3 | 2.0 | `comm/transport.py` |
| `design-c2d3e4f5-component_comm_rfcomm_transport` | 3 | 2.0 | `comm/rfcomm.py` |
| `design-d3e4f5a6-component_comm_tcp_transport` | 3 | 2.0 | `comm/tcp_transport.py` |
| `design-e4f5a6b7-component_comm_serial_transport` | 3 | 2.0 | `comm/serial_transport.py` |
| `design-f5a6b7c8-component_comm_obd_protocol` | 3 | 2.0 | `comm/obd.py` |
| `design-a6b7c8d9-component_comm_device_store` | 3 | 1.2 | `comm/device_store.py` |
| `design-a7b8c9d0-component_comm_bluetooth_device` | 3 | 2.0 | `comm/models.py` |
| `design-b8c9d0e1-component_display_manager` | 3 | 2.0 | `display/manager.py`, `display/touch.py` |
| `design-c9d0e1f2-component_display_rendering_engine` | 3 | 2.0 | `display/rendering/` |
| `design-d0e1f2a3-component_display_touch_coordinator` | 3 | 2.0 | `display/input/` |
| `design-f2a3b4c5-component_display_splash_screen` | 3 | 2.0 | `display/splash.py`, `display/graphics/` |
| `design-a3b4c5d6-component_display_setup_manager` | 3 | 2.2 | `display/setup.py`, `display/setup_components/` |
| `design-b4c5d6e7-component_utils_config_manager` | 3 | 2.1 | `utils/config.py` |
| `design-f8a9b0c1-component_utils_home` | 3 | 2.1 | `utils/home.py` |
| `design-c5d6e7f8-component_utils_platform_detector` | 3 | 2.0 | `utils/platform.py` |
| `design-d6e7f8a9-component_utils_terminal_restorer` | 3 | 2.0 | `utils/terminal.py` |
| `design-e7f8a9b0-component_utils_dependency_validator` | 3 | 2.0 | `utils/dependencies.py` |

[Return to Table of Contents](#table-of-contents)

---

## 6.0 Retired and Merged Designs

Moved to `ai/workspace/design/closed/` on 2026-11-13 (`report-71ab3751-design-review`, `proposal-f8d0064b` §4.5).

| Design document | Disposition | Successor |
|---|---|---|
| `design-d4e5f6a7-component_comm_bluetooth_manager` | Retired; `BluetoothManager` is not in the source | `design-b1c2d3e4`, `design-c2d3e4f5` |
| `design-c3d4e5f6-component_core_async_sync_bridge` | Retired; the component is not in the source | — |
| `design-g1h2i3j4-gesture_reference` | Retired; described removed gestures | `design-b8c9d0e1` §6.0 |
| `design-e1f2a3b4-component_display_performance_monitor` | Retired | `design-2c6b8e4d` §4.2 |
| `design-f6a7b8c9-component_comm_device_store` | Merged (superseded) | `design-a6b7c8d9` |
| `design-e5f6a7b8-component_comm_obd_protocol` | Merged; its §6.3 is §5.0 of the successor | `design-f5a6b7c8` |

[Return to Table of Contents](#table-of-contents)

---

## 7.0 Test Coverage

- The suite is `tests/` (flat, with `tests/display/rendering/`). Each module's docstring cites the issue and change UUIDs it covers.
- Line coverage is reported by `pytest` (`--cov=src`); the figure of the last run is in the report of that run.

[Return to Table of Contents](#table-of-contents)

---

## 8.0 Changes and Audits

Triples and audits of run `f8d0064b`. Earlier work: see §1.0.

| UUID | Type | Title | Design updated | Code | Test | Status |
|---|---|---|---|---|---|---|
| `bce0d69a` | Audit | Release-readiness audit; 14 findings; remediation `c41037ea`, `b2077e6` (P04.12), `55bdbd1` | `design-9a1f3c7e` §4.3 | `src/gtach/utils/updater.py`, `src/gtach/comm/obd.py`, `bin/release.sh` | `test_update_version_ordering.py`, `test_rpm_reply_decoding.py`, `test_release_script.py` | Closed (`audit/closed/`) |
| `c41037ea` | Issue, change, prompt | Update check orders pre-release versions (audit-bce0d69a H01) | `design-9a1f3c7e` §4.3 | `src/gtach/utils/updater.py` | `tests/test_update_version_ordering.py` | Closed, verified by unit tests |

[Return to Table of Contents](#table-of-contents)

---

## 9.0 Bidirectional Navigation

- **Forward (design → code → test):** §4.0, by row.
- **Backward (test → code → design):** §4.0, by the Tests column; each test module's docstring names the issue and change it covers, and each change document names its design updates.
- **Requirement ↔ design:** not populated (§1.0).

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2025-12-27 | Initial skeleton |
| 2.0 | 2026-11-13 | Component mapping, design cross-reference, retired and merged designs, and the change table of run f8d0064b (proposal-f8d0064b WP4). Requirement rows not populated; reason recorded. Links converted to GitHub slugs |

---

Copyright (c) 2026 William Watson. MIT License.
