Created: 2026 October 09

# Report: mypy Strict Clean

---

## Table of Contents

1. [Summary](<#1. summary>)
2. [Baseline and Final Counts](<#2. baseline and final counts>)
3. [Per-Subpackage Results](<#3. per-subpackage results>)
4. [Stub Packages Added](<#4. stub packages added>)
5. [TODO Suppressions](<#5. todo suppressions>)
6. [Deviations](<#6. deviations>)
7. [Items Kept](<#7. items kept>)
8. [Final Checks](<#8. final checks>)
9. [On-Device Verification Outstanding](<#9. on-device verification outstanding>)
10. [Version History](<#version history>)

---

## 1. Summary

prompt-ac11505d (change-ac11505d, issue-ac11505d) is implemented. `mypy src/` now reports **Success: no issues found in 59 source files** under the unchanged strict `[tool.mypy]` settings. The work is in five commits: utils (with the stub packages), core, comm, display, and the top-level app/main. `pytest tests/` gives 561 passed after every step, the same count as before this change. No test file was changed.

[Return to Table of Contents](<#table of contents>)

---

## 2. Baseline and Final Counts

Baseline taken after change-e215a184, before any edit here: **329 errors in 38 files**. Final: **0**.

| Code | Baseline | Final |
|---|---|---|
| no-untyped-def | 109 | 0 |
| assignment | 60 | 0 |
| unreachable | 47 | 0 |
| var-annotated | 25 | 0 |
| no-any-return | 16 | 0 |
| union-attr | 15 | 0 |
| index | 11 | 0 |
| arg-type | 10 | 0 |
| dict-item | 8 | 0 |
| import-untyped | 6 | 0 |
| call-overload | 5 | 0 |
| attr-defined | 4 | 0 |
| func-returns-value | 3 | 0 |
| untyped-decorator | 2 | 0 |
| misc | 2 | 0 |
| list-item | 2 | 0 |
| comparison-overlap | 2 | 0 |
| operator | 1 | 0 |
| has-type | 1 | 0 |

Errors move between files as annotations are added: typing a function body exposes errors that were previously unchecked. For example, setup.py and manager.py each produced new errors part-way through and were cleared in the same step.

[Return to Table of Contents](<#table of contents>)

---

## 3. Per-Subpackage Results

| Step | Commit | Errors before (baseline) | After | Suppressions added |
|---|---|---|---|---|
| utils (+ stubs) | `e5ceb62` | 20 | 0 | 4 |
| core | `dae7d83` | 7 | 0 | 0 |
| comm | `5ebd823` | 59 | 0 | 2 |
| display | `954fb6d` | 223 | 0 | 13 |
| app.py, main.py | `1a2ebee` | 20 | 0 | 1 |

The baseline count for a subpackage includes errors that originated in other modules (for example `import-untyped`, and the `app.py` callback-assignment errors that typing `DisplayManager`'s attributes resolved).

[Return to Table of Contents](<#table of contents>)

---

## 4. Stub Packages Added

Added to `[project.optional-dependencies].dev` in `pyproject.toml`: `types-PyYAML`, `types-pyserial`, `types-psutil`. No runtime dependency changed, and the `ignore_missing_imports` override is unchanged (RPi, hyperpixel2r and bluetooth have no stub packages and were already listed).

[Return to Table of Contents](<#table of contents>)

---

## 5. TODO Suppressions

All 20 `type: ignore` comments in `src/gtach` were added by this change. Each carries an error code and the issue-ac11505d tag. Line numbers are as of commit `1a2ebee`.

| Location | Code | Reason |
|---|---|---|
| `app.py:435` | arg-type | `rendering_engine.main_surface` is `Optional`; `SetupDisplayManager` dereferences it unguarded. |
| `display/input/touch_coordinator.py:311` | attr-defined | `TouchAction.DRAG` does not exist. `handle_touch_move` raises AttributeError for any drag, which its handler logs and turns into None. **Real defect.** |
| `display/setup.py:368` | unreachable | `_render_screen` tests all six `SetupScreen` members before `manual_entry_mode`, so the manual-entry screen can never render. **Real defect.** |
| `display/models.py:235` | assignment | `DisplayConfig.rpm_bands: RPMBands = None`. It should use `default_factory`. |
| `display/models.py:241` | unreachable | The `__post_init__` None-check for the same field. |
| `utils/ack_state.py:257` | no-any-return | `get_state_info` returns `yaml.safe_load` unchecked; a non-mapping file breaks the declared type. |
| `comm/models.py:45` | unreachable | `BluetoothDevice.last_connected` is annotated `Optional[datetime]`, but `__post_init__` accepts a str. |
| `utils/dependencies.py:275` | unreachable | Fallback `return False` after all `DependencyType` members are tested; reachable only with a non-enum value. |
| `display/touch_interface.py:294` | untyped-decorator | `hyperpixel2r.Touch.on_touch` is untyped (no stubs). |
| `display/__init__.py:26` | misc, assignment | `TouchHandler = None` fallback; the import cannot fail. |
| `display/splash.py:26` | misc, assignment | `SplashConfig = None` fallback; the import cannot fail. |
| `utils/config.py:33`, `utils/ack_state.py:30`, `comm/device_store.py:27` | assignment | `yaml = None` fallback; PyYAML is a hard dependency. |
| `display/manager.py:40`, `display/setup.py:27`, `display/splash.py:50`, `display/typography.py:37`, `display/graphics/splash_graphics.py:25`, `display/setup_components/rendering/device_surfaces.py:25` | assignment | `pygame = None` fallback; pygame is a hard dependency. |

The first seven rows are behavioural candidates for follow-up issues. The rest are dead conditional-import fallbacks or untyped third-party code.

[Return to Table of Contents](<#table of contents>)

---

## 6. Deviations

- **Suppression format.** The prescribed one-line form, `# type: ignore[<code>]  # TODO: issue-ac11505d candidate defect - <reason>`, exceeds the 88-column flake8 limit on every line. Each suppression is written as two lines instead: the full `# TODO: issue-ac11505d candidate defect - <reason>` comment on the line above, and `# type: ignore[<code>]  # TODO: issue-ac11505d` on the line itself. Six deeply indented lines also carry `# noqa: E501`.
- **Runtime-identical code edits** (no annotation alone could express them):
  - `OBDTransport.send_command`: three `return self._record_timeout(...)` became the call followed by `return None` (`_record_timeout` returns None; `func-returns-value`).
  - `SetupDisplayManager._render_welcome_screen`: the local `text` is reused for a str after holding a Surface; the str is now `message`.
  - `SystemBluetoothManager` discovery: `assert process.stdin is not None and process.stdout is not None` after `Popen(..., stdin=PIPE, stdout=PIPE)`, and `assert process.stdout is not None` in the reader closure. These hold whenever Popen returns.
  - `typing.cast` where a guard lives in a helper mypy cannot see through: `cast(BinaryIO, self.fb_dev)` after `_fb_dev_usable()` (8 sites in engine.py); `cast(BluetoothPairing, self.pairing)` after `ensure_pairing_initialized()` (2 sites in interface.py); `cast(Callable[[], None], self._reset_callback)` in the lambda registered only when it is set (manager.py). Others: `cast(Path, ...)` on `importlib.resources.files()` results (config.py); `cast(Optional[str], getattr(...))` (app.py `_disconnected_cause`); `cast(int, ...)` (touch_coordinator fallback).
- **`Any` used** where the value is dynamic or heterogeneous: transport handles (socket, `serial.Serial`, Bluetooth socket); `DeviceStore.config` (parsed YAML); engine `payload` and `buffer_data` (pygame BufferProxy, bytes or memoryview); `submit_operation` `*args`/`**kwargs`; touch-coordinator and circular-positioning state dicts (`Dict[str, Any]`); `_retry_interval_callback`'s return (validated where read); `pairing_factory`'s return (BluetoothPairing or the duck-typed SimBluetoothPairing).
- **Assumed element types** for containers that are never written: `AsyncOperationManager.result_queue` (`Dict[str, Any]`), `PerformanceMonitor._font_cache` (`Dict[str, Any]`), and `MockTouchInterface._simulated_events` / `_event_history` (`List[TouchEvent]`).
- **mypy version.** mypy 2.4.0 warns that `python_version = "3.9"` is unsupported and checks with 3.10+ semantics. To confirm the annotations still evaluate on 3.9, every `gtach` module was imported under Python 3.9.25, using a throwaway venv in the session scratchpad (not added to the project): no failures.

[Return to Table of Contents](<#table of contents>)

---

## 7. Items Kept

- No `[tool.mypy]` setting was relaxed; there is no `ignore_errors` and no module-wide ignore.
- `src/gtach/main.py:42` fails flake8 E501 (89 columns). The line already exists in the parent commit and was not changed.
- The nine `pygame`/`yaml` import fallbacks and the two class fallbacks are kept, suppressed, rather than deleted. Deleting them changes import behaviour, which is outside "no runtime change".

[Return to Table of Contents](<#table of contents>)

---

## 8. Final Checks

| Check | Result |
|---|---|
| `mypy src/` | Success: no issues found in 59 source files |
| `pytest tests/` | 561 passed (baseline 561) |
| `python -c 'import gtach.app, gtach.main'` | OK |
| `SDL_VIDEODRIVER=dummy GTACH_HOME=$(mktemp -d) timeout 8 python -m gtach --transport simtcp` | Reached the timeout (exit 124). Same 20 lines of output as before the change; the only traceback is the logged framebuffer `OSError: [Errno 25] Inappropriate ioctl for device`, which is environmental (no /dev/fb0 in the container). |
| flake8 on changed files | Clean except the pre-existing `main.py:42` |
| black / isort on `src/gtach` | Clean |
| `grep -rn 'type: ignore' src/gtach` | 20 matches, each with a code and the issue-ac11505d TODO |

[Return to Table of Contents](<#table of contents>)

---

## 9. On-Device Verification Outstanding

- Deploy to the Pi (`./bin/deploy.sh`) and confirm normal use: service start, splash, gauge with live RPM, OPTIONS screen, touch and swipe, DISCONNECTED screen with retry arc and Reset button, setup flow and pairing.
- Exercise the real hyperpixel2r touch path, which the container cannot run: taps register on the Pi.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-09 | Initial report for prompt-ac11505d. |

---

Copyright (c) 2026 William Watson. MIT License.
