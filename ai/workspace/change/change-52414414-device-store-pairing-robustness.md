Created: 2026 July 30

# Change: Validate the Device Store on Load, Coerce the Discovery Timeout, Accumulate the OBD Response, Narrow the Bare Handlers

---

## Table of Contents

- [1. Change Information](<#1. change information>)
- [2. Version History](<#2. version history>)

---

## 1. Change Information

```yaml
change_info:
  id: "change-52414414"
  title: "Normalise the loaded devices.yaml structure and report save failure through a bool return; coerce discovery_timeout to int at the configuration read; use _recv_until_prompt in test_obd_connection; narrow three bare except clauses"
  date: "2026-07-30"
  author: "William Watson"
  status: "proposed"
  priority: "medium"
  iteration: 1
  coupled_docs:
    issue_ref: "issue-52414414"
    issue_iteration: 1

source:
  type: "issue"
  reference: "issue-52414414"
  description: >
    Resolves issue-52414414. Sourced from
    ai/workspace/report/core-comm-utils-code-review.md v1.0 findings
    §3.4, §3.5, §5.6 and §5.7, and §7.0 recommendations #4 and #5. Task
    list reference ai/task.md §7.4.4.

scope:
  summary: >
    Four corrections across two files. In comm/device_store.py, validate
    the structure loaded from devices.yaml once at load rather than
    assuming it at each assignment, and give save_device a bool return so
    a failed persist is visible to the caller. In comm/pairing.py, coerce
    discovery_timeout to int where it is read from configuration, read
    the 0100 response through the existing _recv_until_prompt helper
    rather than a single recv, and narrow three bare except clauses to
    except Exception.
  affected_components:
    - name: "DeviceStore._normalise_config"
      file_path: "src/gtach/comm/device_store.py"
      change_type: "add"
    - name: "DeviceStore._load_config"
      file_path: "src/gtach/comm/device_store.py"
      change_type: "modify"
    - name: "DeviceStore._save_config"
      file_path: "src/gtach/comm/device_store.py"
      change_type: "modify"
    - name: "DeviceStore.save_device"
      file_path: "src/gtach/comm/device_store.py"
      change_type: "modify"
    - name: "BluetoothPairing.__init__"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
    - name: "BluetoothPairing.discover_elm327_devices"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
    - name: "BluetoothPairing.pair_device"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
    - name: "BluetoothPairing.test_obd_connection"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
    - name: "BluetoothPairing.__del__"
      file_path: "src/gtach/comm/pairing.py"
      change_type: "modify"
  affected_designs:
    - design_ref: "design-a6b7c8d9-component_comm_device_store"
      sections:
        - "Configuration loading and persistence"
  out_of_scope:
    - "The two save_device call sites — comm/sim_bluetooth.py:211 and display/setup_components/bluetooth/interface.py:330. Both ignore the return value today and continue to compile unchanged. Having them act on it is a separate change in files this triple does not declare. The primary cause of the silent failure is removed here regardless; the bool return is the signal, not the whole remedy."
    - "lookup_timeout at pairing.py:55, passed positionally to bluetooth.lookup_name at pairing.py:493 where PyBluez also expects an int. No report finding covers it. Recorded so it is not rediscovered."
    - "pairing.py:148 divides self.discovery_timeout rather than the effective timeout the caller supplied, so an explicit timeout argument does not shorten the per-chunk duration. A latent inconsistency, not a report finding, and not corrected here."
    - "ConfigManager's parallel device-persistence path. It is retired by task 7.4.1 under the §7.5.4 decision recorded in ai/task.md §7.4.8; nothing in this change touches utils/config.py."
    - "DeviceStore.remove_device (device_store.py:165-187). Its del at device_store.py:171 is reached only through a truthy .get chain at device_store.py:169, so paired_devices is necessarily present. No change required."
    - "The transport check-then-act race, §5.3 — task 7.4.5, gated on ai/task.md §7.5.5."
    - "Discovery early-exit behaviour, corrected under change-54eeb2d6 at pairing.py:208-215. Untouched."

rational:
  problem_statement: >
    Four robustness defects in the device-store and pairing pair. A
    devices.yaml lacking a paired_devices key makes save_device raise
    KeyError at device_store.py:104 and 107; the method's own except
    Exception swallows it and returns None, so pairing reports success
    and persists nothing. A non-integer discovery_timeout makes
    range(chunks) raise TypeError at pairing.py:134 and returns an empty
    device list. test_obd_connection takes one read at pairing.py:451
    where _test_basic_communication accumulates, so a split response
    fails a working adapter. Three bare except clauses at pairing.py:348,
    478 and 573 catch KeyboardInterrupt and SystemExit.
  proposed_solution: >
    Validate the loaded structure once, in a new _normalise_config called
    at the end of _load_config, and use setdefault at both assignment
    sites so save_device cannot depend on it. Return bool from
    _save_config and from save_device. Coerce discovery_timeout to int at
    pairing.py:53 and normalise the caller-supplied timeout in
    discover_elm327_devices. Replace the single recv at pairing.py:451
    with _recv_until_prompt. Change the three bare except clauses to
    except Exception.
  alternatives_considered:
    - option: "Apply the report's remedy verbatim — setdefault at the primary assignment only."
      reason_rejected: >
        The report quotes device_store.py:104 alone. device_store.py:107
        indexes the same absent key on the secondary branch and raises
        identically. A fix confined to the quoted line leaves half the
        method broken.
    - option: "Coerce only at the range() call, as §7.0 recommendation #5 states."
      reason_rejected: >
        That corrects pairing.py:132 and 134 but leaves pairing.py:148,
        where a float self.discovery_timeout is divided and passed as the
        duration argument to bluetooth.discover_devices, which expects an
        int. Coercing at pairing.py:53 corrects both sites and is fewer
        lines.
    - option: "Validate devices.yaml against a schema."
      reason_rejected: >
        The file has four leaf fields and one nesting level. A schema
        library is disproportionate; three isinstance tests express the
        same contract in the same place.
    - option: "Raise from save_device rather than returning False."
      reason_rejected: >
        Both existing callers are inside broader try blocks that would
        convert the exception into a logged failure, which is what
        happens today. A bool is a signal the caller can act on without
        being obliged to.
    - option: "Leave save_device returning None and rely on the log."
      reason_rejected: >
        The report's specific complaint is that there is "no signal to
        the caller that pairing was not saved". A log line is not a
        signal to a caller.
    - option: "Reuse _test_basic_communication's read loop by inlining it at pairing.py:451."
      reason_rejected: >
        _recv_until_prompt already exists at pairing.py:360 for exactly
        this and is what §5.6 asks for. Inlining would produce a third
        read pattern in a file that is meant to end this change with one.
  benefits:
    - "A device the pairing flow reports as paired is present in devices.yaml afterwards, for every shape of pre-existing file."
    - "The failure that does remain — an unwritable file — is reported to the caller instead of only to the log."
    - "Discovery runs for any timeout value the YAML admits, and the value reaching PyBluez is an int at both sites."
    - "A working adapter whose response arrives in fragments passes verification."
    - "A Ctrl-C during shutdown is no longer swallowed by comm/pairing.py."
    - "comm/pairing.py ends the change with one read pattern and one exception convention."
  risks:
    - risk: >
        _normalise_config discards a devices.yaml whose top level is not
        a mapping, losing data.
      mitigation: >
        The only way to reach that state is a file that is already
        unusable — a list, a scalar, or corrupt YAML. The current code
        raises AttributeError or KeyError on it. Normalisation logs at
        WARNING with the observed type before replacing, so the event is
        visible in the log and the file itself is only overwritten on the
        next successful save.
    - risk: >
        Coercing at pairing.py:53 puts int() inside the block whose
        except at pairing.py:58 falls back to all five default timeouts,
        so a non-numeric discovery_timeout now discards the other four.
      mitigation: >
        That is the existing behaviour of that block for any failure
        within it, and the fallback values are the same defaults the
        gets already supply. The warning at pairing.py:59 names the
        cause. Accepted rather than restructured, because restructuring
        the block is a larger change than the finding warrants.
    - risk: >
        _recv_until_prompt calls sock.settimeout at pairing.py:362,
        overriding the 10.0 s set at pairing.py:431.
      mitigation: >
        The socket is closed at pairing.py:477 immediately after, in the
        finally block, so no later operation depends on the old value.
        Verified against source rather than assumed.
    - risk: >
        _recv_until_prompt returns str, so retaining the .decode call at
        pairing.py:451 would raise AttributeError.
      mitigation: >
        The prompt removes the .decode explicitly and a test asserts the
        return type at that site.
    - risk: >
        Widening save_device's return type breaks a caller.
      mitigation: >
        Both call sites ignore the return today —
        comm/sim_bluetooth.py:211 and
        display/setup_components/bluetooth/interface.py:330. A widened
        return is backward compatible; a validation criterion asserts
        neither file is modified.

technical_details:
  current_behavior: >
    DeviceStore._load_config assigns self.config = yaml.safe_load(f) or {}
    at device_store.py:64 with no structural check. save_device indexes
    self.config['paired_devices'] at device_store.py:104 and 107, catches
    the resulting KeyError at device_store.py:114, logs it and returns
    None. _save_config returns None whether or not it wrote.

    BluetoothPairing reads discovery_timeout at pairing.py:53 without
    coercion; discover_elm327_devices computes chunks at pairing.py:132
    and calls range(chunks) at pairing.py:134; the same value is divided
    and passed as duration at pairing.py:148.

    test_obd_connection issues one sock.recv(1024).decode(...) at
    pairing.py:451 and tests the result at pairing.py:453.

    pairing.py:348, 478 and 573 are bare except clauses.
  proposed_behavior: >
    The structure loaded from devices.yaml always carries a
    paired_devices mapping by the time save_device runs, and save_device
    reports whether the device was persisted. discovery_timeout is an int
    from construction onward, and an explicitly supplied timeout is
    normalised at entry. test_obd_connection accumulates to the ELM327
    prompt. The three handlers catch Exception.
  implementation_approach: >
    Seven edits across two files.

    src/gtach/comm/device_store.py

    EDIT 1 — add _normalise_config, a private method that replaces a
    non-mapping self.config with an empty dict, ensures
    self.config['paired_devices'] is a mapping, and ensures
    paired_devices['secondary'] is a mapping when present. Each
    replacement logs at WARNING with the type observed.

    EDIT 2 — call _normalise_config at the end of _load_config, after
    the try/except, so it runs on every exit including the error path.

    EDIT 3 — _save_config returns bool: True after os.replace succeeds,
    False on exception, and False when YAML is unavailable, since in that
    state nothing is persisted by design.

    EDIT 4 — save_device returns bool. Bind
    paired = self.config.setdefault('paired_devices', {}) once, assign
    through it on both branches, use setdefault for the secondary
    mapping, return the result of _save_config on success and False from
    the except.

    src/gtach/comm/pairing.py

    EDIT 5 — wrap the discovery_timeout read at pairing.py:53 in int().

    EDIT 6 — in discover_elm327_devices, normalise the effective timeout
    to int after the None default is applied, falling back to
    self.discovery_timeout with a warning if the supplied value cannot be
    coerced.

    EDIT 7 — replace the single recv at pairing.py:451 with
    _recv_until_prompt, removing the .decode call, and narrow the bare
    except clauses at pairing.py:348, 478 and 573 to except Exception.
  code_changes:
    - component: "DeviceStore"
      file: "src/gtach/comm/device_store.py"
      change_summary: >
        Validate the loaded structure once at load; assign through
        setdefault; report persistence success through a bool return.
      functions_affected:
        - "_normalise_config"
        - "_load_config"
        - "_save_config"
        - "save_device"
      classes_affected:
        - "DeviceStore"
    - component: "BluetoothPairing"
      file: "src/gtach/comm/pairing.py"
      change_summary: >
        Coerce discovery_timeout at the configuration read and at method
        entry; accumulate the 0100 response to the ELM327 prompt; narrow
        three bare except clauses.
      functions_affected:
        - "__init__"
        - "discover_elm327_devices"
        - "pair_device"
        - "test_obd_connection"
        - "__del__"
      classes_affected:
        - "BluetoothPairing"
  data_changes:
    - entity: "config/devices.yaml"
      change_type: "validation"
      details: >
        No schema change. The loader now enforces the structure the
        writer already assumed: a top-level mapping carrying a
        paired_devices mapping, which may carry primary and a secondary
        mapping. Existing well-formed files load identically.
  interface_changes:
    - interface: "DeviceStore.save_device"
      change_type: "signature"
      details: "Return type None -> bool. True when the device was persisted; False otherwise."
      backward_compatible: "yes"
    - interface: "DeviceStore._save_config"
      change_type: "signature"
      details: "Return type None -> bool. Private; both call sites are inside the class."
      backward_compatible: "yes"

dependencies:
  internal:
    - component: "BluetoothPairing._recv_until_prompt"
      impact: "Called from a second site. The method is unchanged; only test_obd_connection changes to use it."
    - component: "comm/sim_bluetooth.py and display/setup_components/bluetooth/interface.py"
      impact: "Call save_device and ignore its return. Unmodified; the widened return is compatible. Acting on it is recorded as out of scope."
    - component: "task 7.4.1 (394c3bbb)"
      impact: "None. That triple retires the ConfigManager device path in utils/config.py; this change touches neither that file nor that path."
  external:
    - library: "PyYAML"
      version_change: "none"
      impact: "safe_load's return is now type-checked rather than assumed to be a mapping."
    - library: "PyBluez"
      version_change: "none"
      impact: "discover_devices receives an int duration for every admissible configuration value."
  required_changes: []

testing_requirements:
  test_approach: >
    Unit tests on the development platform. DeviceStore is tested against
    real temporary files, since the fault is in file handling. Pairing is
    tested against a stub socket, since the faults are in type handling
    and read framing and neither needs Bluetooth. ai/task.md §8.2 already
    names DeviceStore as a target of the minimal pytest suite, covering
    "malformed config handling, once authored"; these are those tests.
  test_cases:
    - scenario: "devices.yaml containing an empty document; save_device with is_primary True."
      expected_result: "Returns True. The reloaded file carries paired_devices.primary."
    - scenario: "devices.yaml containing an unrelated top-level key; save_device."
      expected_result: "Returns True. The unrelated key survives."
    - scenario: "devices.yaml lacking paired_devices; save_device with is_primary False."
      expected_result: "Returns True and the device appears under paired_devices.secondary keyed by MAC — the branch the report does not cite."
    - scenario: "devices.yaml containing 'paired_devices: null'."
      expected_result: "The loader replaces the null with a mapping; save_device succeeds rather than raising TypeError."
    - scenario: "devices.yaml whose top level is a list."
      expected_result: "Logged at WARNING; self.config becomes an empty mapping; save_device succeeds."
    - scenario: "_save_config raises."
      expected_result: "save_device returns False."
    - scenario: "A well-formed devices.yaml, unchanged."
      expected_result: "Loads and saves identically to the pre-change behaviour; get_primary_device and get_all_devices return the same objects."
    - scenario: "discovery_timeout 30.5 in configuration."
      expected_result: "self.discovery_timeout is the int 30; discover_elm327_devices runs and raises no TypeError."
    - scenario: "discovery_timeout '30' as a string."
      expected_result: "self.discovery_timeout is the int 30."
    - scenario: "discovery_timeout 'abc'."
      expected_result: "The block's except fires; all five timeouts take their defaults; a warning is logged."
    - scenario: "discover_elm327_devices called with timeout=30.5 explicitly."
      expected_result: "Runs; the value used for range() is an int."
    - scenario: "The duration argument observed at the bluetooth.discover_devices call."
      expected_result: "An int for every admissible discovery_timeout."
    - scenario: "Stub socket returning the 0100 response in three fragments, the last containing '>'."
      expected_result: "test_obd_connection returns True."
    - scenario: "Stub socket returning '41 00 BE 3F A8 13>' in one fragment."
      expected_result: "test_obd_connection returns True, as before the change."
    - scenario: "Stub socket returning 'NO DATA>'."
      expected_result: "test_obd_connection returns True."
    - scenario: "Stub socket returning nothing until the deadline."
      expected_result: "test_obd_connection returns False, as before the change."
    - scenario: "Inspect the return of the read at the 0100 site."
      expected_result: "A str. No .decode call remains at that site."
  regression_scope:
    - "pytest tests/ — no new failures."
    - "Manual on target: complete a pairing on gtach.local or ELM327-Emulator.local and confirm config/devices.yaml carries the device after restart."
    - "Manual on target: run discovery with the default integer discovery_timeout and confirm the early-exit behaviour from change-54eeb2d6 is unaffected."
    - "Manual on target: run the OBD verification step and confirm it still reports success for a working adapter."
  validation_criteria:
    - "python -m py_compile src/gtach/comm/device_store.py src/gtach/comm/pairing.py passes."
    - "No bare 'except:' remains in src/gtach/comm/pairing.py."
    - "self.config['paired_devices'] is not indexed without a setdefault or a prior guard anywhere in device_store.py."
    - "save_device and _save_config are annotated -> bool."
    - "The only recv site in test_obd_connection is the _recv_until_prompt call."
    - "_recv_until_prompt, _test_basic_communication and _classify_device are byte-identical to their current text."
    - "get_primary_device, get_all_devices, remove_device and get_device_by_mac are byte-identical to their current text."
    - "src/gtach/utils/config.py is unmodified."
    - "src/gtach/comm/sim_bluetooth.py and src/gtach/display/setup_components/bluetooth/interface.py are unmodified."
    - "No file other than src/gtach/comm/device_store.py and src/gtach/comm/pairing.py is modified."

implementation:
  implementation_steps:
    - step: "EDIT 1 — add DeviceStore._normalise_config."
      owner: "Claude Code"
    - step: "EDIT 2 — call it at the end of _load_config."
      owner: "Claude Code"
    - step: "EDIT 3 — _save_config returns bool."
      owner: "Claude Code"
    - step: "EDIT 4 — save_device assigns through setdefault on both branches and returns bool."
      owner: "Claude Code"
    - step: "EDIT 5 — coerce discovery_timeout at the configuration read."
      owner: "Claude Code"
    - step: "EDIT 6 — normalise the effective timeout in discover_elm327_devices."
      owner: "Claude Code"
    - step: "EDIT 7 — accumulate the 0100 response and narrow the three bare except clauses."
      owner: "Claude Code"
    - step: "Compile check and run the existing suite."
      owner: "Claude Code"
    - step: "Unit tests against temporary files and a stub socket."
      owner: "Claude Code"
    - step: "Deploy to gtach.local; complete a pairing and confirm persistence across a restart."
      owner: "William Watson"
  rollback_procedure: >
    Two files, one commit. git revert restores the previous behaviour.
    devices.yaml written under this change is readable by the previous
    code, since the structure is unchanged, so no data migration is
    involved in either direction.
  deployment_notes: >
    The persistence fault is only observable with a devices.yaml that
    lacks the key. To exercise it on target, truncate the file to zero
    length before pairing rather than deleting it — deleting it takes the
    else-branch at device_store.py:65-69, which already seeds the key and
    does not reproduce the fault.

verification:
  implemented_date: ""
  implemented_by: ""
  verification_date: ""
  verified_by: ""
  test_results: ""
  issues_found: []

traceability:
  design_updates: []
  related_changes:
    - change_ref: "change-54eeb2d6"
      relationship: "related"
  related_issues:
    - issue_ref: "issue-52414414"
      relationship: "resolves"

notes: >
  Task 7.4.4 in ai/task.md §7.4, released in v0.3.0 (§8.3). Per §8.2.1
  this change is left active when the code lands, pending a passing T06
  result; only prompt-52414414 closes on implementation.

  ai/task.md §7.5.5 gates task 7.4.5, not this one. Nothing here requires
  a live-device observation.

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial change document coupled to issue-52414414."
      - "Records why the report's stated remedies for §3.4 and §3.5 are each extended: both save_device branches raise, and the float reaches pairing.py:148 as well as the range() call."
      - "Records the two save_device call sites and lookup_timeout as out of scope."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t02_change"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial change document coupled to issue-52414414. Extends the report's remedies for §3.4 and §3.5 with recorded reasons, and records the out-of-scope boundary against task 7.4.1. |

---

Copyright (c) 2026 William Watson. MIT License.
