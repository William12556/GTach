Created: 2026 July 30

# Prompt: Validate the Device Store on Load, Coerce the Discovery Timeout, Accumulate the OBD Response, Narrow the Bare Handlers

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
prompt_info:
  id: "prompt-52414414"
  task_type: "debug"
  source_ref: "change-52414414"
  target_profile: "claude_code"
  date: "2026-07-30"
  iteration: 1
  coupled_docs:
    change_ref: "change-52414414"
    change_iteration: 1

context:
  purpose: >
    Four robustness defects in the device-store and pairing pair. A
    devices.yaml without a paired_devices key makes save_device raise
    KeyError, which its own handler swallows, so pairing reports success
    and persists nothing. A non-integer discovery_timeout makes range()
    raise TypeError and returns an empty device list. test_obd_connection
    takes a single socket read where the adjacent method accumulates, so
    a split response fails a working adapter. Three bare except clauses
    catch KeyboardInterrupt and SystemExit.
  integration: >
    Two files: src/gtach/comm/device_store.py and
    src/gtach/comm/pairing.py. Seven edits. Executor is Claude Code; AEL
    is not used.

    Two of the report's own remedies are deliberately extended here, for
    reasons verified against source and recorded in issue-52414414.
    First, the KeyError arises on BOTH branches of save_device — line 104
    and line 107 — not only the primary assignment the report quotes.
    Second, the float discovery_timeout reaches pairing.py:148 as well as
    the range() call, so coercing at the range() call alone is
    insufficient; coerce where the value is read instead.
  knowledge_references: []
  constraints:
    - "Modify only src/gtach/comm/device_store.py and src/gtach/comm/pairing.py."
    - "Do NOT modify src/gtach/utils/config.py. Its device-persistence path is retired by task 7.4.1 and is unrelated to this work."
    - "Do NOT modify src/gtach/comm/sim_bluetooth.py or src/gtach/display/setup_components/bluetooth/interface.py. They call save_device and ignore its return; the widened return is compatible."
    - "Do NOT modify _recv_until_prompt (pairing.py:360-375), _test_basic_communication (pairing.py:377-410) or _classify_device (pairing.py:230-274)."
    - "Do NOT modify the discovery early-exit block at pairing.py:208-215. It was added by change-54eeb2d6."
    - "Do NOT modify get_primary_device, get_all_devices, remove_device or get_device_by_mac in device_store.py."
    - "Do NOT change the devices.yaml file format. The loader is being made to enforce the structure the writer already assumed."
    - "Do NOT add a schema library. Three isinstance tests express the contract."
    - "Type hints on all new and modified signatures; Google-style docstrings; PEP 8."

specification:
  description: >
    Normalise the structure loaded from devices.yaml once at load and
    report persistence success through a bool return; coerce
    discovery_timeout to int at the configuration read and at method
    entry; read the 0100 response through _recv_until_prompt; narrow
    three bare except clauses.
  requirements:
    functional:
      - "After _load_config returns, self.config is a mapping and self.config['paired_devices'] is a mapping, for every possible file content."
      - "save_device succeeds for a devices.yaml that lacks paired_devices, on both the primary and the secondary branch."
      - "save_device returns True when the device was persisted and False when it was not."
      - "_save_config returns True on a successful write and False otherwise, including when YAML is unavailable."
      - "self.discovery_timeout is an int after BluetoothPairing construction for any numeric configuration value."
      - "discover_elm327_devices coerces its effective timeout to int before computing chunks."
      - "The duration argument passed to bluetooth.discover_devices is an int."
      - "test_obd_connection accumulates the 0100 response to the ELM327 prompt rather than taking one read."
      - "No bare except: remains in src/gtach/comm/pairing.py."
    technical:
      language: "Python"
      version: "3.9+ (target runtime 3.11)"
      standards:
        - "Thread-safe if concurrent access"
        - "Comprehensive error handling"
        - "Debug logging with traceback"
        - "Professional docstrings"
  performance:
    - target: "No change. All edits are in setup and pairing paths, none in the OBD polling loop"
      metric: "time"

design:
  architecture: >
    Structural validation moves from implicit-at-use to explicit-at-load.
    One method owns the contract that devices.yaml must satisfy, and the
    writers depend on it rather than on the file. Type coercion moves to
    the configuration boundary for the same reason: the value is checked
    once where it enters, not at each site that consumes it.
  components:
    - name: "DeviceStore._normalise_config"
      type: "function"
      purpose: "Enforce the structure the writers assume, once, after every load."
      interface:
        inputs: []
        outputs:
          type: "None"
          description: "Mutates self.config in place."
        raises:
          - "None."
      logic:
        - "Replace self.config with {} if it is not a dict, logging the observed type at WARNING."
        - "Replace self.config['paired_devices'] with {} if absent or not a dict, logging at WARNING only when a non-dict value was present."
        - "Replace paired_devices['secondary'] with {} if present and not a dict, logging at WARNING."
    - name: "DeviceStore._load_config"
      type: "function"
      purpose: "Load and then normalise."
      logic:
        - "Call self._normalise_config() as the last statement, outside the try/except, so it runs on every exit path."
    - name: "DeviceStore._save_config"
      type: "function"
      purpose: "Persist, and say whether it persisted."
      interface:
        outputs:
          type: "bool"
          description: "True after os.replace succeeds; False otherwise."
    - name: "DeviceStore.save_device"
      type: "function"
      purpose: "Persist a device without depending on the file's prior shape."
      interface:
        outputs:
          type: "bool"
          description: "True when persisted; False otherwise."
        raises:
          - "None. Wrapped; logs at ERROR."
      logic:
        - "Bind paired = self.config.setdefault('paired_devices', {}) once."
        - "Assign through paired on both branches; use setdefault for the secondary mapping."
        - "Return the result of _save_config on the success path and False from the except."
    - name: "BluetoothPairing.__init__"
      type: "function"
      purpose: "Coerce discovery_timeout where it is read."
      logic:
        - "Wrap the pairing_config.get for discovery_timeout in int()."
    - name: "BluetoothPairing.discover_elm327_devices"
      type: "function"
      purpose: "Normalise a caller-supplied timeout before arithmetic."
      logic:
        - "After the None default is applied, coerce timeout to int, falling back to self.discovery_timeout with a warning if it cannot be coerced."
    - name: "BluetoothPairing.test_obd_connection"
      type: "function"
      purpose: "Read the 0100 response the same way the adjacent method does."
      logic:
        - "Replace the single recv-and-decode with self._recv_until_prompt(sock, timeout=5.0)."
  dependencies:
    internal:
      - "BluetoothPairing._recv_until_prompt — pairing.py:360; called from a second site, not modified."
      - "BluetoothDevice — comm/models.py; unchanged."
    external:
      - "PyYAML — safe_load's return is now type-checked."
      - "PyBluez — discover_devices receives an int duration."

data_schema:
  entities:
    - name: "devices.yaml"
      attributes:
        - name: "paired_devices"
          type: "mapping"
          constraints: "Always present after _load_config. May be empty."
        - name: "paired_devices.primary"
          type: "mapping"
          constraints: "Optional. Keys name, mac_address, device_type, optional last_connected."
        - name: "paired_devices.secondary"
          type: "mapping"
          constraints: "Optional. Keyed by MAC address; each value has the same shape as primary."
      validation:
        - "The top level must be a mapping; anything else is replaced with an empty mapping and logged."
        - "paired_devices must be a mapping; absent or non-mapping is replaced with an empty mapping."
        - "secondary, if present, must be a mapping; otherwise it is replaced and logged."

error_handling:
  strategy: >
    Structural faults are corrected at load with a WARNING rather than
    raised, because a device store is not worth failing startup over.
    Write faults are reported to the caller through a bool as well as
    logged, because the caller is the only party that can tell the
    operator. No handler catches BaseException.
  exceptions:
    - exception: "Exception"
      condition: "Any failure inside save_device."
      handling: "logger.error; return False."
    - exception: "Exception"
      condition: "Any failure inside _save_config."
      handling: "logger.error; return False."
    - exception: "TypeError, ValueError"
      condition: "A supplied timeout that cannot be coerced to int."
      handling: "logger.warning; fall back to self.discovery_timeout."
    - exception: "Exception"
      condition: "Socket close in pair_device and test_obd_connection, and shutdown in __del__."
      handling: "Pass, as now — but catching Exception rather than BaseException."
  logging:
    level: "WARNING"
    format: "self.logger.warning(f'...: {value!r}')"

testing:
  unit_tests:
    - scenario: "devices.yaml containing an empty document; save_device(is_primary=True)."
      expected: "Returns True; the reloaded file carries paired_devices.primary."
    - scenario: "devices.yaml carrying an unrelated top-level key; save_device."
      expected: "Returns True; the unrelated key survives the write."
    - scenario: "devices.yaml lacking paired_devices; save_device(is_primary=False)."
      expected: "Returns True; the device appears under paired_devices.secondary keyed by MAC."
    - scenario: "devices.yaml containing 'paired_devices: null'."
      expected: "Normalised to a mapping; save_device succeeds rather than raising TypeError."
    - scenario: "devices.yaml whose top level is a YAML list."
      expected: "WARNING logged; self.config becomes {}; save_device succeeds."
    - scenario: "_save_config patched to raise."
      expected: "save_device returns False."
    - scenario: "A well-formed devices.yaml."
      expected: "get_primary_device and get_all_devices return exactly what they returned before the change."
    - scenario: "discovery_timeout 30.5."
      expected: "self.discovery_timeout == 30 and isinstance(..., int)."
    - scenario: "discovery_timeout '30'."
      expected: "self.discovery_timeout == 30."
    - scenario: "discovery_timeout 'abc'."
      expected: "The block's except fires; all five timeouts take defaults; a warning is logged."
    - scenario: "discover_elm327_devices(timeout=30.5)."
      expected: "Runs; range() receives an int."
    - scenario: "Observe the duration keyword at the bluetooth.discover_devices call."
      expected: "An int."
    - scenario: "Stub socket delivering '41 0', '0 BE 3F', 'A8 13>' across three recv calls."
      expected: "test_obd_connection returns True."
    - scenario: "Stub socket delivering '41 00 BE 3F A8 13>' in one recv."
      expected: "test_obd_connection returns True, as before the change."
    - scenario: "Stub socket delivering 'NO DATA>'."
      expected: "test_obd_connection returns True."
    - scenario: "Stub socket delivering nothing."
      expected: "test_obd_connection returns False, as before the change."
  edge_cases:
    - "YAML unavailable — __init__ takes the branch at device_store.py:37-41 and never calls _load_config. _save_config returns False in that state, so save_device honestly reports that nothing was persisted."
    - "devices.yaml exists but is unreadable — the except at device_store.py:70-74 seeds the structure; _normalise_config then finds it already correct."
    - "A device whose mac_address is None on the secondary branch — the mapping accepts a None key. Pre-existing behaviour; not changed here."
    - "discovery_timeout smaller than chunk_duration — chunks is held at 1 by the existing max(1, ...) at pairing.py:132."
    - "_recv_until_prompt returns a str, so the .decode call must be removed, not retained."
  validation:
    - "grep confirms no bare 'except:' remains in pairing.py."
    - "grep confirms self.config['paired_devices'] is never indexed in save_device without setdefault."

deliverable:
  format_requirements:
    - "Edit both files in place. Create no new file."
    - "Apply the seven edits below. Change nothing else."
  files:
    - path: "src/gtach/comm/device_store.py"
      content: |
        EDIT 1 — add _normalise_config

        Place it immediately after _load_config (currently
        device_store.py:52-74).

            def _normalise_config(self) -> None:
                """Enforce the structure the writers assume.

                yaml.safe_load returns whatever the file contains. An
                empty file, a partially written file or a hand edit can
                produce a mapping with no 'paired_devices' key, a null
                value under that key, or a top level that is not a
                mapping at all. save_device previously indexed into
                self.config['paired_devices'] directly and raised
                KeyError, which its own handler swallowed — so pairing
                reported success and persisted nothing (core review
                §3.4, recommendation #4).

                The contract is enforced once here rather than at each
                assignment site.
                """
                if not isinstance(self.config, dict):
                    self.logger.warning(
                        f"devices.yaml top level is {type(self.config).__name__}, "
                        f"expected mapping — using an empty store"
                    )
                    self.config = {}

                paired = self.config.get('paired_devices')
                if not isinstance(paired, dict):
                    if paired is not None:
                        self.logger.warning(
                            f"paired_devices is {type(paired).__name__}, "
                            f"expected mapping — replacing"
                        )
                    self.config['paired_devices'] = {}

                secondary = self.config['paired_devices'].get('secondary')
                if secondary is not None and not isinstance(secondary, dict):
                    self.logger.warning(
                        f"paired_devices.secondary is {type(secondary).__name__}, "
                        f"expected mapping — replacing"
                    )
                    self.config['paired_devices']['secondary'] = {}

        EDIT 2 — call it from _load_config

        _load_config currently ends with the except block at
        device_store.py:70-74. Add the call as the last statement of the
        method, at method-body indentation so it runs on every exit path
        including the error path:

                except Exception as e:
                    self.logger.error(f"Failed to load device config: {e}")
                    self.config = {
                        'paired_devices': {}
                    }

                # Runs on every exit path, including the error path above.
                self._normalise_config()

        EDIT 3 — _save_config returns bool

        Change the signature at device_store.py:76 from -> None to
        -> bool, and:

          - return False in the YAML-unavailable branch, after the
            existing debug log, because nothing was persisted
          - return True after os.replace succeeds
          - return False from the except

        Do not change the temp-file-and-replace mechanism.

        EDIT 4 — save_device assigns through setdefault and returns bool

        Change the signature at device_store.py:90 from -> None to
        -> bool. Replace the assignment block currently at
        device_store.py:103-111:

                    if is_primary:
                        self.config['paired_devices']['primary'] = device_data
                    else:
                        # Add to secondary devices
                        if 'secondary' not in self.config['paired_devices']:
                            self.config['paired_devices']['secondary'] = {}
                        self.config['paired_devices']['secondary'][device.mac_address] = device_data

                    self._save_config()
                    self.logger.info(f"Saved {'primary' if is_primary else 'secondary'} device: {device.name}")

        with:

                    # setdefault rather than direct indexing: a devices.yaml
                    # that exists but carries no paired_devices key raised
                    # KeyError here, on BOTH branches, and the except below
                    # swallowed it (core review §3.4, recommendation #4).
                    paired = self.config.setdefault('paired_devices', {})

                    if is_primary:
                        paired['primary'] = device_data
                    else:
                        paired.setdefault('secondary', {})[device.mac_address] = device_data

                    saved = self._save_config()
                    if saved:
                        self.logger.info(f"Saved {'primary' if is_primary else 'secondary'} device: {device.name}")
                    else:
                        self.logger.error(f"Device {device.name} was not persisted")
                    return saved

        and change the except at device_store.py:114-115 to return False
        after its existing log line. Update the docstring to state what
        the return value means.
    - path: "src/gtach/comm/pairing.py"
      content: |
        EDIT 5 — coerce discovery_timeout where it is read

        Replace pairing.py:53:

                    self.discovery_timeout = pairing_config.get('discovery_timeout', 30)

        with:

                    # int() at the read, not at the range() call. The value
                    # reaches two sites — range(chunks) below and the
                    # duration argument to bluetooth.discover_devices — and
                    # PyBluez expects an int at the second as well
                    # (core review §3.5, recommendation #5).
                    self.discovery_timeout = int(pairing_config.get('discovery_timeout', 30))

        A non-numeric value now raises inside the existing try, whose
        except at pairing.py:58 falls back to all five default timeouts
        and logs a warning. That is the block's existing behaviour for
        any failure within it and is accepted.

        EDIT 6 — normalise the effective timeout at method entry

        Replace pairing.py:118-120 in discover_elm327_devices:

                # Use configured or provided timeout
                if timeout is None:
                    timeout = self.discovery_timeout

        with:

                # Use configured or provided timeout. A caller may pass a
                # float — discover_all_devices declares timeout: int = 30
                # but nothing enforces it — and range() below requires an
                # int (core review §3.5).
                if timeout is None:
                    timeout = self.discovery_timeout
                else:
                    try:
                        timeout = int(timeout)
                    except (TypeError, ValueError):
                        self.logger.warning(
                            f"Non-numeric discovery timeout {timeout!r} — "
                            f"using {self.discovery_timeout}s"
                        )
                        timeout = self.discovery_timeout

        Leave pairing.py:131-134 as they are. With both reads coerced,
        chunks is an int and range() is correct.

        EDIT 7a — accumulate the 0100 response

        Replace pairing.py:450-451 in test_obd_connection:

                        sock.send(b'0100\r')  # Request supported PIDs
                        response = sock.recv(1024).decode('utf-8', errors='ignore')

        with:

                        sock.send(b'0100\r')  # Request supported PIDs
                        # Accumulate to the ELM327 '>' prompt rather than
                        # taking one read. A response split across reads
                        # failed both tests below, reporting failure for an
                        # adapter that answered correctly (core review §5.6).
                        # _recv_until_prompt returns str, so no decode.
                        response = self._recv_until_prompt(sock, timeout=5.0)

        Leave the '41 00' and 'NO DATA' tests at pairing.py:453
        unchanged. _test_basic_communication does not send ATS0, so
        spaces remain enabled and '41 00' is the correct spaced form —
        note that comm/obd.py does send ATS0, so the two paths see
        differently formatted responses and this test must not be
        aligned with obd.py's.

        EDIT 7b — narrow the three bare except clauses

        At pairing.py:348, pairing.py:478 and pairing.py:573, change

                    except:
                        pass

        to

                    except Exception:
                        pass

        preserving each site's indentation. The first two guard
        sock.close(); the third guards self.shutdown() in __del__ — the
        report describes all three as socket-close paths, which is
        correct for the first two only. All three are narrowed.

success_criteria:
  - "python -m py_compile src/gtach/comm/device_store.py src/gtach/comm/pairing.py passes."
  - "pytest tests/ passes with no new failures."
  - "DeviceStore._normalise_config exists and is called as the last statement of _load_config."
  - "save_device and _save_config are annotated -> bool and return bool on every path."
  - "save_device contains no direct self.config['paired_devices'] index; both branches go through the setdefault-bound local."
  - "save_device succeeds against a devices.yaml lacking paired_devices, on both branches."
  - "self.discovery_timeout is an int after construction."
  - "range() in discover_elm327_devices receives an int for every admissible configuration and every caller-supplied timeout."
  - "test_obd_connection contains no sock.recv call; the 0100 response comes from _recv_until_prompt."
  - "No .decode call remains at the 0100 read site."
  - "No bare 'except:' remains anywhere in src/gtach/comm/pairing.py."
  - "_recv_until_prompt, _test_basic_communication and _classify_device are byte-identical to their current text."
  - "get_primary_device, get_all_devices, remove_device and get_device_by_mac are byte-identical to their current text."
  - "The discovery early-exit block at pairing.py:208-215 is byte-identical to its current text."
  - "src/gtach/utils/config.py, src/gtach/comm/sim_bluetooth.py and src/gtach/display/setup_components/bluetooth/interface.py are unmodified."
  - "No file other than src/gtach/comm/device_store.py and src/gtach/comm/pairing.py is modified."

element_registry:
  source: ""
  entries:
    modules:
      - name: "device_store"
        path: "src/gtach/comm/device_store.py"
      - name: "pairing"
        path: "src/gtach/comm/pairing.py"
      - name: "models"
        path: "src/gtach/comm/models.py"
    classes:
      - name: "DeviceStore"
        module: "gtach.comm.device_store"
      - name: "BluetoothPairing"
        module: "gtach.comm.pairing"
      - name: "BluetoothDevice"
        module: "gtach.comm.models"
    functions:
      - name: "_normalise_config"
        module: "gtach.comm.device_store"
        signature: "_normalise_config(self) -> None"
      - name: "_load_config"
        module: "gtach.comm.device_store"
        signature: "_load_config(self) -> None"
      - name: "_save_config"
        module: "gtach.comm.device_store"
        signature: "_save_config(self) -> bool"
      - name: "save_device"
        module: "gtach.comm.device_store"
        signature: "save_device(self, device: BluetoothDevice, is_primary: bool = True) -> bool"
      - name: "discover_elm327_devices"
        module: "gtach.comm.pairing"
        signature: "discover_elm327_devices(self, timeout: int = None, progress_callback=None, device_found_callback=None, show_all_devices: bool = False) -> List[BluetoothDevice]"
      - name: "_recv_until_prompt"
        module: "gtach.comm.pairing"
        signature: "_recv_until_prompt(self, sock, timeout: float = 5.0) -> str"
      - name: "test_obd_connection"
        module: "gtach.comm.pairing"
        signature: "test_obd_connection(self, device: BluetoothDevice, status_callback=None) -> bool"
    constants: []

notes: >
  Executor is Claude Code; AEL is not used, so no tactical_brief is
  required (ai/task.md §7.2, governance P09 §1.10.2). Invoke from the
  project root:
  implement ai/workspace/prompt/prompt-52414414-device-store-pairing-robustness.md
  and close the prompt when finished. Leave the issue and change active
  pending test results (ai/task.md §8.2.1).

  To reproduce the persistence fault on target, truncate
  config/devices.yaml to zero length before pairing. Deleting the file
  takes the else-branch at device_store.py:65-69, which already seeds
  the key, so deletion does not reproduce it.

  ai/task.md §8.2 lists DeviceStore in the minimal pytest suite as
  covering "malformed config handling, once authored". The unit tests
  written for this prompt are those tests and should be placed so the
  later T05 can adopt them.

  ai/task.md §7.5.5 gates task 7.4.5, not this one. Nothing here needs a
  live device.
```

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial prompt document coupled to change-52414414. |
| 1.1 | 2026-07-31 | Executed by Claude Code. All seven edits applied and all sixteen success criteria met, with no departure from the deliverable text required. 70 assertions against a real DeviceStore over real files and the real pairing methods against stub sockets, all passing; pytest tests/ 11 passed. Each of the four faults was demonstrated before and after: save_device returned None and persisted nothing, now returns True and persists; a float timeout attempted zero discovery chunks and logged "'float' object cannot be interpreted as an integer", now attempts seven with an int duration; a 0100 response split across three reads returned False, now True; three bare except clauses became none. One correction to the issue's wording is recorded in change-52414414 — the KeyError was logged at ERROR, so it was invisible to the caller rather than invisible in the log. The unit tests were NOT persisted into tests/, this document permitting no file outside the two named; that needs its own T04 prompt, and tests/ is now a live suite to adopt them into. Closed per P00 §1.1.14.4 and moved to ai/workspace/prompt/closed/; the issue and change remain active pending on-target results per ai/task.md §8.2.1. |

---

Copyright (c) 2026 William Watson. MIT License.
