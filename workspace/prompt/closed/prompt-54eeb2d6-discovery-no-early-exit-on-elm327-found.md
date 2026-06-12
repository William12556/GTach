Created: 2026 June 12

```yaml
prompt_info:
  id: "prompt-54eeb2d6"
  task_type: "code_generation"
  source_ref: "change-54eeb2d6"
  date: "2026-06-12"
  iteration: 1
  coupled_docs:
    change_ref: "change-54eeb2d6"
    change_iteration: 1

context:
  purpose: >
    End ELM327 discovery promptly once a confirmed adapter is found, instead of
    running the full discovery timeout.
  integration: >
    One function modified: BluetoothPairing.discover_elm327_devices in
    src/gtach/comm/pairing.py. Executor: Claude Code (no AEL).
  constraints:
    - "Targeted mode only — do not alter behaviour when show_all_devices is True."
    - "No change to method signature, return type, progress reporting, or cancellation."
    - "Early exit triggers on DeviceType.HIGHLY_LIKELY_ELM327 only, not POSSIBLY_COMPATIBLE."

specification:
  description: >
    Add a guarded early-exit break to the chunk loop in discover_elm327_devices.
  requirements:
    functional:
      - "In targeted mode, the chunk loop breaks once any accumulated device is HIGHLY_LIKELY_ELM327."
      - "Full-survey mode (show_all_devices=True) runs the complete timeout unchanged."
      - "Final progress_callback(1.0) and the return path run unchanged after the break."
    technical:
      language: "Python"
      version: "3.9"
      standards:
        - "Existing logging patterns."
        - "No interface change."

design:
  architecture: "Single-function targeted edit; no structural change."
  components:
    - name: "BluetoothPairing.discover_elm327_devices"
      type: "function"
      purpose: "Add early-exit on confirmed ELM327 classification in targeted mode."
      logic:
        - "Locate the chunk loop `for chunk in range(chunks):` in discover_elm327_devices."
        - "Immediately after the chunk-level try/except (the two `except ... break` blocks) and before the dedent to `# Final progress update`, at the chunk-loop body indentation, insert the early-exit block from the deliverable."
        - "Use d.device_classification (set on each BluetoothDevice at construction)."
  dependencies:
    internal:
      - "src/gtach/display/setup_models.py — DeviceType (already imported in pairing.py)"

error_handling:
  strategy: "No new error paths; pure read of accumulated devices list."
  logging:
    level: "INFO"
    format: "existing"

testing:
  unit_tests: []
  edge_cases:
    - "Only POSSIBLY_COMPATIBLE devices present: no early exit; full timeout runs."
    - "show_all_devices=True: no early exit regardless of classification."
    - "Cancellation mid-scan: existing cancel break unaffected."
  validation:
    - "Targeted discovery ends in the chunk where the adapter is confirmed."
    - "discover_all_devices (delegates with show_all_devices=True) unchanged."

deliverable:
  format_requirements:
    - "Edit src/gtach/comm/pairing.py in place."
  files:
    - path: "src/gtach/comm/pairing.py"
      content: |
        In BluetoothPairing.discover_elm327_devices, the chunk loop ends with these
        two except blocks:

                except bluetooth.BluetoothError as e:
                    self.logger.error(f"Bluetooth discovery error: {e}")
                    break
                except Exception as e:
                    self.logger.error(f"Unexpected discovery error: {e}")
                    break

        Immediately after them (same 16-space indentation, still inside the
        `for chunk in range(chunks):` loop, before the dedent to
        `# Final progress update`), insert:

                # Early exit: stop scanning once a confirmed ELM327 adapter is
                # found (targeted discovery only; full survey runs full timeout).
                if not show_all_devices and any(
                    d.device_classification == DeviceType.HIGHLY_LIKELY_ELM327
                    for d in devices
                ):
                    self.logger.info("Confirmed ELM327 device found — ending discovery early")
                    break

        Make no other changes.

success_criteria:
  - "discover_elm327_devices breaks early in targeted mode on a HIGHLY_LIKELY_ELM327 device."
  - "show_all_devices mode and POSSIBLY_COMPATIBLE-only cases retain full-timeout behaviour."
  - "Method signature and return type unchanged."
  - "python -m py_compile src/gtach/comm/pairing.py passes."

notes: >
  Executor is Claude Code (no AEL). Invoke from the project root:
  implement workspace/prompt/prompt-54eeb2d6-discovery-no-early-exit-on-elm327-found.md
```

```yaml
tactical_brief: |
  Executor: Claude Code. Implement change-54eeb2d6: early-exit for ELM327 discovery.

  FILE: src/gtach/comm/pairing.py
  FUNCTION: BluetoothPairing.discover_elm327_devices

  The `for chunk in range(chunks):` loop ends with two except blocks:

      except bluetooth.BluetoothError as e:
          self.logger.error(f"Bluetooth discovery error: {e}")
          break
      except Exception as e:
          self.logger.error(f"Unexpected discovery error: {e}")
          break

  Insert immediately AFTER those blocks, at the same 16-space indentation (still
  inside the chunk loop, before the dedent to `# Final progress update`):

      # Early exit: stop scanning once a confirmed ELM327 adapter is
      # found (targeted discovery only; full survey runs full timeout).
      if not show_all_devices and any(
          d.device_classification == DeviceType.HIGHLY_LIKELY_ELM327
          for d in devices
      ):
          self.logger.info("Confirmed ELM327 device found — ending discovery early")
          break

  No other changes. DeviceType is already imported. Verify:
  python -m py_compile src/gtach/comm/pairing.py.
```

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-12 | Initial prompt document. |

---

Copyright (c) 2026 William Watson. MIT License.
