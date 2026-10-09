Created: 2026 October 07

# On-Device Verification Guide: audit-36b6ea95 Remediation

---

## Table of Contents

- [1. Purpose and Scope](<#1. purpose and scope>)
- [2. Preparation](<#2. preparation>)
- [3. Automated Checks](<#3. automated checks>)
- [4. Manual Steps](<#4. manual steps>)
- [5. Recording Results](<#5. recording results>)
- [6. Results Sheet](<#6. results sheet>)
- [7. Version History](<#7. version history>)

---

## 1. Purpose and Scope

1.1 This guide covers the 21 pending steps in `ai/task.md`, section "On-Device Verification Outstanding (audit-36b6ea95)".

1.2 The work is split between two parts:

- `bin/gtach-verify-36b6ea95.sh` covers everything observable from files and systemd: logs, configuration, packaging, unit hardening, stack dumps and stop timing.
- Section 4 covers what needs a person: touch, pairing, power cycles, emulator control and visual checks. Each manual step ends with a script run that collects the evidence.

1.3 Sessions are ordered by risk. Deployment and touch come first, because later steps depend on them. The soak test comes last.

1.4 No on-device step is needed for 70789d75, e4ee50fd or the Phase 4 lifecycle test. cd5ec050 needs only normal use (session 4.9).

[Return to Table of Contents](<#table of contents>)

---

## 2. Preparation

2.1 On the Mac, start from the repository root with a clean `main` at or after `4125e6a`:

```bash
cd ~/Documents/GitHub/GTach
git pull
```

2.2 Have the following ready:

- the ELM327 emulator at `ELM327-Emulator.local`, with a way to stop and start it and to make `0100` answer `NO DATA` (vehicle off);
- physical access to the Pi's power supply;
- a terminal with root ssh to `gtach.local`.

2.3 Copy the script to the Pi once. It stays in `/tmp` until the Pi reboots, so copy it again after each reboot:

```bash
scp bin/gtach-verify-36b6ea95.sh root@gtach.local:/tmp/
```

2.4 Note the local time at the start of each session. Several checks filter logs from a given time with `--since`.

[Return to Table of Contents](<#table of contents>)

---

## 3. Automated Checks

### 3.1 Commands

| Purpose                      | Command (on the Mac, from the repository root)                                            |
| ---------------------------- | ----------------------------------------------------------------------------------------- |
| Copy the script to the Pi    | `scp bin/gtach-verify-36b6ea95.sh root@gtach.local:/tmp/`                                 |
| Run; log window = this boot  | `ssh root@gtach.local 'bash /tmp/gtach-verify-36b6ea95.sh'`                               |
| Run over the whole log files | `ssh root@gtach.local 'bash /tmp/gtach-verify-36b6ea95.sh --since all'`                   |
| Run from a given time        | `ssh root@gtach.local 'bash /tmp/gtach-verify-36b6ea95.sh --since "2026-10-08 09:00:00"'` |
| Include the stop-time test   | `ssh root@gtach.local 'bash /tmp/gtach-verify-36b6ea95.sh --stop-test'`                   |
| Copy the reports back        | `scp 'root@gtach.local:/tmp/gtach-verify-*.txt' ai/workspace/test/`                       |

### 3.2 Behaviour

- The script is read-only unless `--stop-test` is given. That option stops the service, times the stop, starts it again and checks it is active after 20 s. The display is interrupted for about 30 s.
- The invalid-configuration test validates a temporary copy in `/tmp`. The real `config.yaml` is not modified.
- Each run writes `/tmp/gtach-verify-<timestamp>.txt` and ends with a summary of PASS, FAIL, INFO, SKIP and MANUAL lines.
- The default log window starts at boot time. Records written before NTP synchronisation may carry earlier timestamps and fall outside it, so use `--since all` when in doubt.

### 3.3 Check map

| Check | Issue | Covers task.md step |
|---|---|---|
| C0 | — | Service active |
| C1 | b9ee7428 | No exit or restart this boot (after a cold boot) |
| C2 | 269871a0 | error.log present; older records survive |
| C3a/C3b | 860fd5f7, e9216e17, fbe7e98a | No `obd_protocol` stall; no watchdog, thread-exit or shutdown records |
| C4 | 907de6de | Counts of init failures, link drops and closed-connection causes (evidence only) |
| C5a/b/c | 5fbff586 | `--validate-config` valid; `fps_limit: 0` rejected; no invalid values at load |
| C5d | 5fbff586 | `ack_state.yaml` at its new location |
| C6 | 453f0a80 | `devices.yaml` present with a paired MAC address |
| C7a/b/c | 52653cd6 | `[pi]` extra installed; `pip check` clean; no mock fallback |
| C8a/b | 52653cd6 | Unit directives; `systemd-analyze security` summary |
| C9 | 674bec49 | At most one SetupManager thread per stack dump in stacks.log (supplementary; Session E uses the log-based setup thread check) |
| C10 | 52653cd6, d140121d | Stop time below 25 s; active after restart (`--stop-test`) |

[Return to Table of Contents](<#table of contents>)

---

## 4. Manual Steps

### 4.1 Session A: Deploy, First Boots and Touch

Issues: 52653cd6, 5fbff586, 453f0a80, 674bec49.

1. Deploy from the Mac:

   ```bash
   cd ~/Documents/GitHub/GTach
   ./bin/deploy.sh
   ```

2. Watch the display through startup:
   - The service starts and the display appears.
   - Touch responds: tap through to OPTIONS and back. 
2. The acknowledgement screen is expected once, because its state file has moved. Acknowledge it. 
3. Confirm that the paired adapter connects without re-pairing (453f0a80). 
4. Confirm that settings from the existing `config.yaml` apply: palette, mode and engine profile as configured (5fbff586). 
5. Confirm that the gauge is unchanged for the current profile (674bec49). For the Abarth (redline 6000), the scale ends at 7000. 
6. Reboot the Pi with `ssh root@gtach.local reboot`. Confirm that the acknowledgement screen does not appear again. 
7. Copy the script again and run it (section 3.1). 
8. Expected results: C0, C5a–C5d, C6, C7a–C7c and C8a pass.

### 4.2 Session B: Service Stop Time

Issues: 52653cd6, d140121d.

1. Stop time at idle: run the script with `--stop-test`. C10 and C10b should pass.
2. Stop during discovery (d140121d):
   1. Start a device scan on the display: Setup, then discovery.
   2. While the scan is running, run this from the Mac:

      ```bash
      ssh root@gtach.local 'time systemctl stop gtach; systemctl start gtach'
      ```

   3. Pass if `real` is well under 30 s.
3. Run this and record the "Overall exposure" line (C8b):

   ```bash
   ssh root@gtach.local 'systemd-analyze security gtach --no-pager | tail -1'
   ```

### 4.3 Session C: Cold Boot Clock Step

Issue: b9ee7428.

1. Power off the Pi at the supply, wait more than 1 minute, then power on with Wi-Fi available.
2. Wait about 5 minutes so that NTP has synchronised.
3. Copy the script again and run it.
4. Pass if C1 passes: no 'Succeeded' or 'Scheduled restart' lines for gtach this boot, and NRestarts=0. The clock-sync lines in the report confirm that a time step took place.

### 4.4 Session D: error.log with Debug Off

Issue: 269871a0.

1. Confirm that Debug is off: OPTIONS shows "Debug: Off". Debug is off after every service start.
2. Note the time. Make the adapter unavailable for 30 s: stop the emulator or switch off its Bluetooth. Then restore it.
3. Restart the service from the Mac:

   ```bash
   ssh root@gtach.local 'systemctl restart gtach'
   ```

4. Run the script with `--since "<time noted>"`, then run it again with `--since all`.
5. Pass if:
   - C2 lists the link-loss event with a traceback in the window;
   - the earlier records (the 'first' timestamp of the oldest file) still exist after the restart.

### 4.5 Session E: Setup Screens and Responsiveness

Issues: e9216e17, fbe7e98a, 674bec49, 4005360c, 1a8f40ea. Requires 0.4.7 or later (`change-1a8f40ea`).

#### 4.5.1 Screen Flow

| Screen | Reached by | Buttons |
|---|---|---|
| CURRENT_DEVICE | DISCONNECTED → Setup, adapter paired | Continue, New Setup |
| WELCOME (one button) | Setup with no adapter paired | Start Setup |
| WELCOME (two buttons) | CURRENT_DEVICE → Continue failing (adapter off); shows "Device not available" | Start Setup, Cancel |
| DISCOVERY | Start Setup | Cancel (→ WELCOME) |
| DEVICE_LIST | Scan finished | Device rows (signal bars), Back, Retry |
| PAIRING | Device row tapped | Continue (success); Retry, Back (failure) |

- New Setup deletes the stored pairing from `devices.yaml`. It is not used in this session.
- Cancel on WELCOME leaves setup and returns to normal operation with the stored adapter.
- Start Setup keeps the stored pairing; a failed pairing does not lose the adapter.

#### 4.5.2 Commands

Each command prints the Mac time and the Pi time first, so results can be placed on a timeline.

| Purpose | Command (Mac, repository root) |
|---|---|
| Emulator off | `date '+%F %T'; ssh root@ELM327-Emulator.local 'date "+%F %T"; systemctl stop elm327-emulator.service'` |
| Emulator on | `date '+%F %T'; ssh root@ELM327-Emulator.local 'date "+%F %T"; systemctl start elm327-emulator.service'` |
| Setup thread check | see below |
| Restart check | `date '+%F %T'; ssh root@gtach.local 'date "+%F %T"; systemctl show -p NRestarts -p ActiveEnterTimestamp gtach'` |

Setup thread check (674bec49). Each SetupManager start and exit is logged; the last column is the number of setup threads running after each line and must never exceed 1. Debug must be on, because these records are written to `debug.log` only.

```bash
date '+%F %T'; ssh root@gtach.local 'date "+%F %T"; grep -hE "Starting Bluetooth setup|Thread setup exited" /opt/gtach/debug.log | awk "/Starting/{n++} /exited/{n--} {print \$1, \$2, \$5, n}" | tail -12'
```

The watchdog records the exit a few seconds after the thread ends; run the check about 10 s after a screen change.

#### 4.5.3 Steps

| Step | Action | Emulator | Pass criterion | Issue |
|---|---|---|---|---|
| E0 | Restart check (note NRestarts). Turn Debug on (OPTIONS → "Debug: On"); note the time. RPM shown. | On | — | — |
| E1 | Emulator off. When DISCONNECTED appears, tap Setup → CURRENT_DEVICE → Continue. | Off | Display responsive while the check runs; WELCOME shows "Device not available" with Start Setup and Cancel until the next tap. | fbe7e98a, 674bec49 |
| E2 | Setup thread check. | Off | Last count 1. | 674bec49 |
| E3 | Tap Cancel on WELCOME (→ DISCONNECTED). After 10 s, setup thread check. | Off | Last count 0. | 674bec49 |
| E4 | DISCONNECTED → Setup → Continue (fails) → WELCOME. For one minute, alternate Start Setup (WELCOME) and Cancel (DISCOVERY). | Off | Every tap responds; no restart (restart check). | e9216e17 |
| E5 | Setup thread check while still in setup. | Off | Count never above 1. | 674bec49 |
| E6 | Emulator on. On WELCOME tap Start Setup; wait for DEVICE_LIST (tap Retry once if the emulator is not listed). | On | Signal bars shown beside devices. | 4005360c |
| E7 | Tap ELM327-Emulator → PAIRING → Continue on success. | On | Pairing completes; display responsive; RPM returns. | fbe7e98a |
| E8 | After 10 s, setup thread check. | On | Last count 0. | 674bec49 |
| E9 | Request five stack dumps, one per command, while RPM is shown: `date '+%F %T'; ssh root@gtach.local 'date "+%F %T"; kill -USR1 $(systemctl show -p MainPID --value gtach); sleep 1; grep -c "^=== gtach" /opt/gtach/stacks.log'`. Then turn Debug off and send one more. Restart check. | On | The count rises by one per request; NRestarts unchanged from E0. | 1a8f40ea |
| E10 | Run the script with `--since "<E0 time>"`; copy the report back; pull logs. | On | C3b passes. | All |

Record the outputs of E2, E3, E5, E8 and E9 in section 6.

### 4.6 Session F: OBD Initialisation Paths

Issue: 907de6de.

1. Note the time and turn Debug on, because INFO-level link records go only to `debug.log`.
2. Vehicle off:
   1. Set the emulator so that `0100` answers `NO DATA`. Leave it for 1 minute.
   2. Check the retry spacing:

      ```bash
      ssh root@gtach.local 'grep -hE "Initialization failed|No valid 0100" /opt/gtach/debug.log | tail -6'
      ```

   3. Pass if the timestamps are about 2 s apart and there is no initialisation-success record.
3. Emulator stopped:
   1. Return the emulator to normal, let GTach connect, then stop the emulator process (socket closed).
   2. Pass if DISCONNECTED shows 'adapter closed the connection'.
4. Start the emulator again and confirm that GTach reconnects. Turn Debug off.
5. Run the script with `--since "<time noted>"`. C4 lists the supporting records; C3b should pass.

### 4.7 Session G: Soak

Issue: 860fd5f7.

1. Note the start time. Run for several hours with Debug off.
2. During the run, repeat the following at irregular intervals:
   - several link losses: move out of range or switch off emulator Bluetooth;
   - adapter power cycles;
   - emulator restarts.
3. At the end, run the script with `--since "<start time>"`.
4. Pass if C3a and C3b pass (no 'appears unresponsive' for `obd_protocol`, no unexpected shutdown) and NRestarts in the context block is 0.

### 4.8 Session H: Development Host (Mac) — Not Required

Dropped 2026-10-08. Both steps are covered by automated tests run before every deployment, and by results on the Pi:

- 860fd5f7 (simtcp SIGTERM): `tests/test_lifecycle_sim.py::test_sigterm_ends_simtcp_process`; on the Pi, `systemctl stop` completed in 0.5 s (C10) and 0.41 s during discovery (Session B).
- 4005360c (simbt discovery after Cancel): `tests/test_low_defects.py::TestSimPairingCancelIsPerRun`; real discovery after a Cancel passed on the Pi (Session E).

### 4.9 Session I: Normal Use

Issue: cd5ec050. Use the tachometer normally for a drive or an emulator session. Pass if no regression is observed.

[Return to Table of Contents](<#table of contents>)

---

## 5. Recording Results

5.1 Copy each script report back to `ai/workspace/test/` (section 3.1). The file names carry timestamps, so reports do not overwrite each other.

5.2 Fill in the results sheet in section 6. Alternatively, report the results and the report file names in the session, and the planner will update:

- the `verification` block of each issue;
- the Status column in `ai/task.md`;
- issue closure under P00.14, once all steps for an issue pass.

5.3 For a FAIL, keep the report and copy back the relevant logs:

```bash
scp 'root@gtach.local:/opt/gtach/{error,debug,start,stacks}.log*' ai/workspace/test/
```

[Return to Table of Contents](<#table of contents>)

---

## 6. Results Sheet

| Session | Issue | Step | Result | Date | Report file / note |
|---|---|---|---|---|---|
| A | 52653cd6 | Deploy; service starts; touch works | | | |
| A | 5fbff586 | Existing config settings apply | | | |
| A | 5fbff586 | Acknowledgement once, then remembered | | | |
| A | 453f0a80 | Paired adapter used without re-pairing | | | |
| A | 674bec49 | Gauge unchanged for current profile | | | |
| A | 5fbff586 | `--validate-config`; `fps_limit: 0` rejected (C5a, C5b) | | | |
| A | 52653cd6 | No mock fallback (C7c) | | | |
| B | 52653cd6 | Directives listed; stop < 30 s (C8a, C10) | | | |
| B | d140121d | Stop during discovery well under 30 s | | | |
| C | b9ee7428 | Cold boot: no restart (C1) | | | |
| D | 269871a0 | Event with traceback; earlier records survive (C2) | | | |
| E | e9216e17 | WELCOME Setup/Cancel 1 min responsive (C3b) | | | |
| E | fbe7e98a | DISCONNECTED → Setup → pairing → Continue responsive | | | |
| E | 674bec49 | Setup thread count never above 1; 0 after Cancel and after pairing (E2, E3, E5, E8) | | | |
| E | 1a8f40ea | SIGUSR1 with debug on and off: one dump per request, no restart (E9) | | | |
| E | 674bec49 | 'Device not available' after failed Continue | | | |
| E | 4005360c | Signal bars on DEVICE_LIST | | | |
| F | 907de6de | Vehicle off: no init success; retry every 2 s | | | |
| F | 907de6de | Emulator stopped: 'adapter closed the connection' | | | |
| G | 860fd5f7 | Soak: no `obd_protocol` stall; no unexpected shutdown (C3a, C3b) | | | |
| H | 860fd5f7 | simtcp SIGTERM exits within seconds | Not required (automated test) | 2026-10-08 | Section 4.8 |
| H | 4005360c | simbt discovery after Cancel | Not required (automated test) | 2026-10-08 | Section 4.8 |
| I | cd5ec050 | Normal use; no regression | | | |

[Return to Table of Contents](<#table of contents>)

---

## 7. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-10-07 | Initial guide for the 21 pending on-device steps of audit-36b6ea95, with `bin/gtach-verify-36b6ea95.sh`. |
| 1.1 | 2026-10-07 | Session E uses on-request stack dumps (SIGUSR1) after `change-fe755cfd`. Session A passed; results recorded in `ai/task.md`. |
| 1.2 | 2026-10-07 | Section 4.5 rewritten: actual screen flow, single step sequence E0-E10, log-based setup thread check, timestamped commands, SIGUSR1 safety check for `change-1a8f40ea`. |
| 1.3 | 2026-10-08 | Session H marked not required: both steps covered by automated tests and Pi results. |
| 1.4 | 2026-10-08 | Verification complete except Session I (in-car use, vehicle not prepared; tracked in `ai/task.md`). Results in the closed issue documents and report-36b6ea95 §7. |

---

Copyright (c) 2026 William Watson. MIT License.
