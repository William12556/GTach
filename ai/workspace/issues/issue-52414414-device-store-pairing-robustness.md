Created: 2026 July 30

# Issue: Pairing Silently Fails to Persist on a Malformed Device File; Discovery Crashes on a Non-Integer Timeout; a Split OBD Response Fails the Verification Step

---

## Table of Contents

- [1. Issue Information](<#1. issue information>)
- [2. Version History](<#2. version history>)

---

## 1. Issue Information

```yaml
issue_info:
  id: "issue-52414414"
  title: "DeviceStore.save_device raises KeyError on a devices.yaml without a paired_devices key and swallows it; range() receives a float when discovery_timeout is non-integer; test_obd_connection reads once where _test_basic_communication accumulates; three bare except clauses in comm/pairing.py"
  date: "2026-07-30"
  reporter: "William Watson"
  status: "open"
  severity: "medium"
  type: "defect"
  iteration: 1
  coupled_docs:
    change_ref: "change-52414414"
    change_iteration: 1

source:
  origin: "code_review"
  test_ref: ""
  description: >
    ai/workspace/report/core-comm-utils-code-review.md v1.0, 2026-07-30.
    Finding §3.4 with §7.0 recommendation #4; finding §3.5 with §7.0
    recommendation #5; finding §5.6 and finding §5.7, whose remedies are
    stated inside the findings themselves because §7.0 is a selective
    list that omits them. The report's own numbering is preserved so
    coverage remains auditable after the report closes (ai/task.md
    §7.6.4). Task list reference ai/task.md §7.4.4.

affected_scope:
  components:
    - name: "DeviceStore._load_config"
      file_path: "src/gtach/comm/device_store.py"
    - name: "DeviceStore.save_device"
      file_path: "src/gtach/comm/device_store.py"
    - name: "BluetoothPairing.__init__"
      file_path: "src/gtach/comm/pairing.py"
    - name: "BluetoothPairing.discover_elm327_devices"
      file_path: "src/gtach/comm/pairing.py"
    - name: "BluetoothPairing.test_obd_connection"
      file_path: "src/gtach/comm/pairing.py"
    - name: "BluetoothPairing.pair_device"
      file_path: "src/gtach/comm/pairing.py"
    - name: "BluetoothPairing.__del__"
      file_path: "src/gtach/comm/pairing.py"
  designs:
    - design_ref: "design-a6b7c8d9-component_comm_device_store"
    - design_ref: "design-f6a7b8c9-component_comm_device_store"
  version: "0.2.67"

reproduction:
  prerequisites: >
    A GTach installation with config/devices.yaml present. For §3.5, a
    config.yaml carrying bluetooth.pairing.discovery_timeout. For §5.6, a
    paired ELM327 adapter or ELM327-Emulator.local.
  steps:
    - "#4 §3.4 — write an empty config/devices.yaml, or one whose top-level mapping lacks a paired_devices key. Run pairing to completion and observe that the device is reported as paired but is absent from the file afterwards."
    - "#4 §3.4 — read device_store.py:64: self.config = yaml.safe_load(f) or {}. For an empty file safe_load returns None and self.config becomes {}. For a file with other keys, self.config carries those keys and no paired_devices."
    - "#4 §3.4 — read device_store.py:104 and 107. Both index self.config['paired_devices'] without a guard, so both raise KeyError."
    - "#4 §3.4 — read device_store.py:114-115: the surrounding except Exception logs the KeyError at ERROR and returns None. save_device is declared -> None, so the caller has no return value to test and no exception to catch."
    - "#5 §3.5 — set bluetooth.pairing.discovery_timeout to 30.5 in config.yaml. pairing.py:53 reads it with no coercion. pairing.py:132 evaluates 30.5 // 4, giving the float 7.0, and pairing.py:134 calls range(7.0), which raises TypeError."
    - "§5.6 — compare pairing.py:451 with pairing.py:360-375. test_obd_connection issues one sock.recv(1024) and parses the result immediately; _recv_until_prompt accumulates until the ELM327 '>' prompt or a timeout."
    - "§5.7 — read pairing.py:348, 478 and 573. Each is a bare except:."
  frequency: "always"
  reproducibility_conditions: >
    §3.4 requires a devices.yaml that exists but lacks the key, which
    arises from an empty file, a partially written file, a hand edit, or
    a truncated write. It cannot arise from _load_config's own
    else-branch, which seeds the key at device_store.py:66-68.

    §3.5 requires a non-integer discovery_timeout in configuration. The
    default of 30 at pairing.py:53 is an int and does not trigger it.

    §5.6 is intermittent by nature: it manifests only when the adapter's
    response to 0100 is delivered across more than one read, which is
    more likely with slower adapters and on a congested RFCOMM link.

    §5.7 is unconditional but harmless unless a signal arrives during the
    guarded call.
  preconditions: >
    Raspberry Pi Zero 2W target. config/devices.yaml is the live device
    store used by the pairing flow; ConfigManager's parallel device
    subsystem is retired under task 7.4.1 and is not involved here.
  test_data: >
    Second read of §3.4 against source. The report's heading spans
    device_store.py:103-110, but its quoted code and its prose — "this
    line raises KeyError" — identify only the primary assignment at
    device_store.py:104, and its recommendation is a single setdefault.
    The secondary branch at
    device_store.py:107 — "if 'secondary' not in self.config['paired_devices']"
    — indexes the same missing key and raises identically. Both branches
    of the is_primary test are affected, not one.

    §3.5 arithmetic, recomputed. With discovery_timeout 30.5 and
    chunk_duration 4, 30.5 // 4 evaluates to 7.0, a float, and
    range(7.0) raises TypeError. The float also reaches a second site the
    report does not name: pairing.py:148 passes
    duration=min(chunk_duration, self.discovery_timeout // chunks) to
    bluetooth.discover_devices. With chunks an int and discovery_timeout
    a float that expression is a float, and PyBluez expects an integer
    duration. Coercing only at the range() call, which is the report's
    stated remedy, leaves that site unfixed.
  error_output: >
    §3.4 — "Failed to save device <name>: 'paired_devices'", logged at
    ERROR by device_store.py:115, then normal return.

    §3.5 — TypeError: 'float' object cannot be interpreted as an integer,
    raised at pairing.py:134 and caught by the discovery-wide handler at
    pairing.py:223, which logs "Discovery failed" and returns an empty
    device list.

behavior:
  expected: >
    A device that the pairing flow reports as paired is present in
    config/devices.yaml afterwards, or the caller is told it is not.
    Discovery runs for any configured timeout value that the schema
    admits. The OBD verification step succeeds whenever the adapter
    answers, whether or not the answer arrives in one read. Exception
    handlers catch exceptions and not control-flow signals.
  actual: >
    Four faults, grouped because they are the robustness defects of the
    device-store and pairing pair and share a file set.

    (a) #4, §3.4 — silent persistence failure. device_store.py:103-109
    assigns into self.config['paired_devices'] on both branches without
    creating the key. _load_config at device_store.py:64 assigns whatever
    the file contains, so a devices.yaml lacking the key produces a
    self.config lacking it. The resulting KeyError is caught by the
    method's own except Exception at device_store.py:114, logged, and
    discarded. save_device returns None either way, so a caller cannot
    distinguish a save from a failure.

    (b) #5, §3.5 — TypeError on a non-integer timeout. pairing.py:53
    reads discovery_timeout from YAML with no coercion. pairing.py:132
    computes chunks = max(1, timeout // chunk_duration) and pairing.py:134
    calls range(chunks). A float timeout makes chunks a float and range
    raises. The same float additionally reaches
    bluetooth.discover_devices at pairing.py:148.

    (c) §5.6 — inconsistent response read. _test_basic_communication
    (pairing.py:377-410) reads through _recv_until_prompt
    (pairing.py:360-375), which accumulates until '>' appears or the
    deadline passes. test_obd_connection (pairing.py:412-486) instead
    issues a single sock.recv(1024) at pairing.py:451 and tests the
    result for '41 00' or 'NO DATA' at pairing.py:453. A response split
    across reads fails both tests and the verification step reports
    failure for an adapter that answered correctly.

    (d) §5.7 — bare except clauses. pairing.py:348, 478 and 573 use a
    bare except:, which catches BaseException and therefore
    KeyboardInterrupt and SystemExit as well.
  impact: >
    (a) is the operator-visible one. Pairing appears to succeed, the
    application restarts, DeviceStore.get_primary_device returns None,
    and app.py:91 routes the user back into setup. The cause is one line
    in a log the operator is not reading.

    (b) crashes discovery outright for a configuration the YAML schema
    accepts. The failure is total — an empty device list — and looks
    identical to no adapter being present.

    (c) turns an adapter that works into one that appears not to, at the
    exact point in setup where the operator is deciding whether the
    hardware is faulty.

    (d) is low impact given the guarded operations, but it can swallow
    a Ctrl-C during shutdown and leave the process running.
  workaround: >
    (a) Delete config/devices.yaml. _load_config's else-branch then seeds
    paired_devices and writes the file (device_store.py:65-69).
    (b) Set discovery_timeout to an integer.
    (c) Retry the verification step.
    (d) None required.

environment:
  python_version: "3.11"
  os: "Debian Linux (Raspberry Pi OS) 6.1.21-v8+, Raspberry Pi Zero 2W"
  dependencies:
    - library: "PyYAML"
      version: "any; imported conditionally at device_store.py:20-25"
    - library: "PyBluez"
      version: "any; falls back to comm.system_bluetooth at pairing.py:23-32"
  domain: "domain_1"

analysis:
  root_cause: >
    (a) and (b) share a shape: a value read from an external file is used
    without being checked against the structure or type the code
    requires. In (a) the file is devices.yaml and the assumption is a
    key; in (b) it is config.yaml and the assumption is an int. Neither
    read site validates, and in (a) a broad exception handler converts
    the resulting failure into silence.

    (c) is an incomplete refactor. _recv_until_prompt was introduced to
    fix exactly this class of fault, and one of the two call sites that
    needed it was not converted.

    (d) is a convention that predates the codebase's current
    error-handling style; the same file already uses except Exception at
    pairing.py:373 and 386.
  technical_notes: >
    THREE CORRECTIONS TO THE SOURCE REPORT, each found by reading
    src/gtach at 0.2.67.

    (1) §3.4 understates the extent. Its heading spans
    device_store.py:103-110, but the code it quotes and the prose that
    follows identify only the primary assignment at device_store.py:104,
    and §7.0 recommendation #4 prescribes a single setdefault. The
    secondary branch at device_store.py:107 indexes the same absent key
    and raises the same KeyError, so both arms of the is_primary test
    fail. A fix applied to the quoted line alone would leave the
    secondary path broken.

    (2) §3.5's remedy is incomplete. The report proposes
    "chunks = max(1, int(timeout) // chunk_duration)". That corrects
    pairing.py:132 and 134 but not pairing.py:148, where
    self.discovery_timeout — still a float — is divided and passed as
    the duration argument to bluetooth.discover_devices. Coercing at the
    configuration read, pairing.py:53, corrects both sites at once and
    is the smaller change.

    (3) §5.7 mischaracterises one of the three. pairing.py:348 and
    pairing.py:478 are socket-close paths, as the report says.
    pairing.py:573 is in __del__ and guards self.shutdown(), not a
    close. All three should be narrowed, but the third is not a
    socket-close path and the report's description does not cover it.

    OBSERVATION, NOT CLAIMED BY THIS TRIPLE. The same
    no-coercion pattern applies to lookup_timeout at pairing.py:55,
    which is passed positionally to bluetooth.lookup_name at
    pairing.py:493, where PyBluez also expects an integer. No report
    finding covers it and it is recorded in change-52414414 under
    out_of_scope rather than silently fixed.

    NOTE ON §5.6's REMEDY. _recv_until_prompt calls sock.settimeout at
    pairing.py:362, so substituting it at pairing.py:451 replaces the
    10.0 s timeout set at pairing.py:431 for the remainder of the
    socket's life. The socket is closed immediately afterwards at
    pairing.py:477, so nothing later depends on the old value. It also
    returns a decoded str, so the .decode call at pairing.py:451 must be
    removed rather than retained.

    NOTE ON THE '41 00' TEST. _test_basic_communication sends ATZ, ATE0
    and ATSP0 (pairing.py:390, 398, 402) but does not send ATS0, so
    spaces remain enabled and '41 00' is the correct spaced form.
    Accumulating more data does not disturb that test. This was checked
    rather than assumed, because comm/obd.py does send ATS0
    (obd.py:125) and the two paths therefore see differently formatted
    responses.
  related_issues:
    - issue_ref: "issue-54eeb2d6"
      relationship: "related"

resolution:
  assigned_to: "Claude Code"
  target_date: ""
  approach: >
    Seed and validate paired_devices in DeviceStore._load_config, use
    setdefault at both assignment sites in save_device, and give
    save_device a bool return so a caller can tell. Coerce
    discovery_timeout to int at the configuration read and normalise the
    caller-supplied timeout in discover_elm327_devices. Replace the
    single recv in test_obd_connection with _recv_until_prompt. Narrow
    the three bare except clauses to except Exception. See
    change-52414414.
  change_ref: "change-52414414"
  resolved_date: ""
  resolved_by: ""
  fix_description: ""

verification:
  verified_date: ""
  verified_by: ""
  test_results: ""
  closure_notes: ""

prevention:
  preventive_measures: >
    A structure loaded from a file is validated at the point of load,
    not assumed at each point of use. A broad except around a write path
    must not be the only report of that write's failure; the caller is
    told. A helper introduced to correct a read pattern is applied to
    every site with that pattern in the same change.
  process_improvements: >
    The minimal pytest suite planned in ai/task.md §8.2 lists DeviceStore
    as a target covering "malformed config handling, once authored".
    This triple is what makes that test meaningful, and the T05 for it
    should assert on save_device's return value rather than on the log.

verification_enhanced:
  verification_steps:
    - "python -m py_compile src/gtach/comm/device_store.py src/gtach/comm/pairing.py passes."
    - "Unit test: construct DeviceStore against a temp file containing an empty document; call save_device and confirm it returns True and that paired_devices.primary is present in the reloaded file."
    - "Unit test: same against a file containing an unrelated top-level key; confirm the unrelated key survives the save."
    - "Unit test: same with is_primary False; confirm the secondary branch also succeeds — the branch the report does not cite."
    - "Unit test: construct DeviceStore against a file containing 'paired_devices: null'; confirm the loader replaces the null with a mapping rather than raising TypeError on assignment."
    - "Unit test: make _save_config raise; confirm save_device returns False rather than None."
    - "Unit test: set discovery_timeout to 30.5 and confirm discover_elm327_devices runs and does not raise TypeError."
    - "Unit test: confirm self.discovery_timeout is an int after construction for YAML values 30, 30.5 and '30'."
    - "Unit test: pass timeout=30.5 explicitly to discover_elm327_devices and confirm it runs."
    - "Unit test: confirm the duration argument passed to bluetooth.discover_devices is an int for a float discovery_timeout."
    - "Unit test: stub a socket that returns the 0100 response in three fragments; confirm test_obd_connection returns True."
    - "Unit test: stub a socket that returns 'NO DATA>' in one fragment; confirm test_obd_connection still returns True."
    - "grep confirms no bare 'except:' remains in src/gtach/comm/pairing.py."
    - "On gtach.local or ELM327-Emulator.local: complete a pairing and confirm config/devices.yaml carries the device afterwards."
  verification_results: ""

traceability:
  design_refs:
    - "design-a6b7c8d9-component_comm_device_store"
    - "design-f6a7b8c9-component_comm_device_store"
  change_refs:
    - "change-52414414"
  test_refs: []

notes: >
  This is task 7.4.4 in ai/task.md §7.4 and part of step 5 in the
  recommended authoring order (§7.6.2). Released in v0.3.0 (§8.3).

  issue_info.type is defect per ai/task.md §7.2 as extended in v6.0, and
  per the discharge step recorded in
  ai/workspace/report/task-list-cross-check-discrepancies.md §5.4 item 2:
  §3.4 and §3.5 are the highest-severity contributors and both are
  defects, so the mixed-type rule takes defect.

  ai/task.md §7.5.5 gates task 7.4.5, not this task. Nothing here depends
  on a live-device observation, and all four faults are demonstrable
  against stubs.

  Per §8.2.1 this issue is left active when the code lands, pending a
  passing T06 result.

loop_context:
  was_loop_execution: false
  blocked_at_iteration: 0
  failure_mode: ""
  last_review_feedback: ""

version_history:
  - version: "1.0"
    date: "2026-07-30"
    author: "William Watson"
    changes:
      - "Initial issue document from core-comm-utils-code-review.md findings §3.4, §3.5, §5.6 and §5.7 with §7.0 recommendations #4 and #5."
      - "Recorded three corrections to the source report: §3.4 affects both branches of save_device, not only the primary assignment; §3.5's stated remedy leaves the float at pairing.py:148 unfixed; §5.7's third bare except is in __del__ and is not a socket-close path."
      - "Recorded lookup_timeout as a related but unclaimed observation rather than fixing it silently."

metadata:
  copyright: "Copyright (c) 2026 William Watson. MIT License."
  template_version: "1.0"
  schema_type: "t03_issue"
```

[Return to Table of Contents](<#table of contents>)

---

## 2. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-07-30 | Initial issue document from core-comm-utils-code-review.md findings §3.4, §3.5, §5.6 and §5.7 with §7.0 recommendations #4 and #5. Records three corrections to the source report and one unclaimed related observation. |

---

Copyright (c) 2026 William Watson. MIT License.
