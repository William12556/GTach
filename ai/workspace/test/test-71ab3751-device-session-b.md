# Device Session B: Runs 4 and 5 (71ab3751)

Created: 2026 November 12

## Table of Contents

- [1.0 Purpose and Scope](#10-purpose-and-scope)
- [2.0 Preparation](#20-preparation)
- [3.0 Commands](#30-commands)
- [4.0 Steps](#40-steps)
- [5.0 Results Sheet](#50-results-sheet)
- [Version History](#version-history)

---

## 1.0 Purpose and Scope

- This procedure verifies runs 4 and 5 of `proposal-71ab3751` on the Pi with the ELM327 emulator, as device session B in proposal §7.0.
- It covers `change-34781bfe` (run 4, setup flow) and `change-2550e4ee` (run 5, gauge display and touch). It also observes the discovery fallback of `change-b4f9607a`, which session A could not test.
- The planner reads the evidence from the pulled logs. Display observations are asked for only where the logs cannot show them.
- Not covered:
  - the in-car test, which is deferred;
  - faults that cannot be provoked on demand: a touch-interface failure at start (C04), the setup-manager race (C05) and a lost touch-up (C07). Unit tests cover these.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Preparation

- A clean `main` on the Mac that contains run 5 (`afe7423`).
- The emulator at `ELM327-Emulator.local`, controllable over root ssh.
- A phone whose Bluetooth can be made discoverable (for B5). On most phones, keeping the Bluetooth settings screen open makes it discoverable.
- Note the Mac time at the start of each step.

[Return to Table of Contents](#table-of-contents)

---

## 3.0 Commands

All commands run on the Mac from `~/Documents/GitHub/GTach`.

| Name | Command |
|---|---|
| Emulator off | `ssh root@ELM327-Emulator.local 'systemctl stop elm327-emulator.service'` |
| Emulator on | `ssh root@ELM327-Emulator.local 'systemctl start elm327-emulator.service'` |
| Emulator radio off | `ssh root@ELM327-Emulator.local 'bluetoothctl power off'` |
| Emulator radio on | `ssh root@ELM327-Emulator.local 'bluetoothctl power on'` |
| Pull logs | `./bin/pull_logs.sh` |

Turning the emulator's radio off also drops the link, so GTach shows DISCONNECTED. OPTIONS is then not reachable; setup is entered with Setup on the DISCONNECTED screen.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Steps

Set OPTIONS → "Debug: On" after B1 and leave it on until B9. Most of the evidence is written to debug.log only.

### 4.1 B1: Deploy and Startup

1. Deploy:

   ```
   cd ~/Documents/GitHub/GTach
   git pull
   ./bin/deploy.sh
   ```

2. **Display:** the gauge shows RPM. Set OPTIONS → "Debug: On".
3. Run `Pull logs`.

**Pass:** RPM shown; no ERROR or traceback in error.log from the start.

### 4.2 B2: Setup End to End (Run 4)

1. **Display:** OPTIONS → "Clear settings" → "Clear". WELCOME appears. Tap Start Setup.
2. **Display:** on DEVICE_LIST, tap ELM327-Emulator. On PAIRING, note whether a Continue button appears.
3. **Display:** wait for RPM.
4. Run `Pull logs`.

**Pass:**
- one scan is started;
- no Continue button is shown on PAIRING (C01);
- after pairing, the OBD session starts with `adapter_pre_initialised=True` and "Skipping ATZ". This completes B02 with run 4's `adapter_reset_in_session`.

### 4.3 B3: Stored Device and the Probe (Run 4, C08)

1. Run `Emulator off`. **Display:** wait for DISCONNECTED, then tap Setup. CURRENT_DEVICE appears.
2. Run `Emulator on`, then **Display:** tap Continue at once. While "checking" is in progress, note whether New Setup is shown, and tap where it was.
3. **Display:** wait for RPM.
4. Run `Pull logs`.

**Pass:**
- New Setup is not shown, and a tap in its place does nothing, while the probe runs;
- the probe succeeds and setup completes;
- the stored device is not removed;
- the OBD session starts with `adapter_pre_initialised=False`, because the probe sends no ATZ.

### 4.4 B4: Cancel During a Scan (Run 4, X01)

1. **Display:** OPTIONS → "Clear settings" → "Clear" → Start Setup. Within 2 s, tap Cancel.
2. **Display:** WELCOME appears. Wait 45 s without touching the display; note whether any text or screen change appears.
3. **Display:** tap Start Setup, pair ELM327-Emulator, and wait for RPM.
4. Run `Pull logs`.

**Pass:**
- the display stays on WELCOME for 45 s with no "No devices found" text and no screen change;
- the log shows one discovery cancellation, and any late completion logged as ignored.

### 4.5 B5: Empty Scan and Fallback (Run 4, D01; Run 2, D1)

1. Run `Emulator radio off`. **Display:** on DISCONNECTED tap Setup, then New Setup, then Start Setup. Keep the phone's Bluetooth **hidden**: Bluetooth on, but not on its settings screen.
2. **Display:** after the scan (about 36 s), note the screen. Wait a further 60 s and note whether a new scan starts.
3. Make the phone discoverable: open its Bluetooth settings screen and keep it open. **Display:** tap Retry.
4. **Display:** after the scan, note the screen and the text above the list.
5. Close the phone's Bluetooth screen. Run `Emulator radio on`. **Display:** tap Retry, pair ELM327-Emulator, and wait for RPM.
6. Run `Pull logs`.

**Pass:**
- item 2: DEVICE_LIST shows "No devices found" with Back and Retry, and no new scan starts on its own;
- item 4: DEVICE_LIST lists the phone (and any other named device) with "No ELM327 found - showing all devices";
- item 5: the emulator is found and pairing completes.

If the phone is not listed in item 4, the scan did not see it: record this as not observed. It does not fail the step.

### 4.6 B6: Touch (Run 5, C06)

1. **Display:** on the gauge, swipe slowly, taking about 2 s, in the direction that opens OPTIONS.
2. **Display:** on OPTIONS, press and hold a button for about 2 s, for example "Debug"; release without moving. Note what happens. If it was the Debug button, set it back to On.
3. **Display:** return to the gauge. Press and hold an empty part of the gauge for about 2 s without moving.
4. **Display:** long press again to restore the original palette.
5. Run `Pull logs`.

**Pass:**
- item 1 opens OPTIONS and does not change the palette;
- item 2 performs the button's action once and does not change the palette;
- item 3 changes the palette.

### 4.7 B7: Disconnected Screen and Clear Settings (Run 5)

1. Run `Emulator off`. **Display:** on DISCONNECTED, note whether the cause line is legible and fits within the circle.
2. Run `Emulator on`. Wait for RPM.
3. **Display:** OPTIONS → "Clear settings" → "Clear". Then pair ELM327-Emulator again and wait for RPM.
4. Run `Pull logs`.

**Pass:**
- the cause line is legible at its new size (20 px) and fits;
- Clear settings removes the stored device without an error;
- setup and pairing then complete.

### 4.8 B8: Simulated Session (Run 4)

1. In a second terminal window:

   ```
   ssh -t root@gtach.local 'systemctl stop gtach; cd /opt/gtach; /opt/gtach/venv/bin/gtach --transport simbt --debug'
   ```

2. **Display:** Start Setup. On DEVICE_LIST, note the text above the list. Pair a simulated device and wait for the gauge.
3. Press Ctrl-C in the second window. In the first window:

   ```
   ssh root@gtach.local 'systemctl start gtach'
   ```

4. **Display:** the normal gauge returns without setup.
5. Run `Pull logs`.

**Pass:**
- the simulated session completes setup;
- the text above the list reads "No ELM327 found - showing all devices". This is the known effect recorded in `ai/task.md`; observe it, it is not a defect of run 4;
- the normal service reconnects without setup.

### 4.9 B9: End of Session

1. **Display:** set OPTIONS → "Debug: Off".
2. Run `Pull logs` for the last time.

### 4.10 Notes from the Session (2026-11-12)

- `deploy.sh` reboots the Pi. After each boot the first connect fails with "no bluetooth controller" and succeeds 5 s later.
- B3: the probe took 0.9 s, so whether New Setup was hidden could not be observed. Unit tests cover the guard.
- B5: hcitool saw named devices in range even with the phone hidden, so "No devices found" could not be produced. Unit tests cover that state.
- B8: the simulated session opened on CURRENT_DEVICE, because `devices-sim.yaml` still held a simulated device from session A.
- Six findings outside runs 4 and 5 are recorded in `ai/task.md`.

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Results Sheet

Session run on 2026-11-12, 08:02 to 09:57, with GTach 0.4.15 (`main` at the run 5 merge).

| Step | Change | Check | Result | Note |
|---|---|---|---|---|
| B1 | 34781bfe, 2550e4ee | Startup; no error | Pass | Startup 08:02:35. Boot-time first-connect failure and a misleading "Vehicle not answering (None)" record noted (`ai/task.md`) |
| B2 | 34781bfe | One scan; no Continue on PAIRING; ATZ skipped after pairing | Pass | No Continue seen. Each scan started by a tap only. `adapter_pre_initialised=True` and "Skipping ATZ" at 08:36:13. First OBD check after pairing reset (ECONNRESET); Retry passed |
| B3 | 34781bfe | New Setup not offered during the probe; probe completes; ATZ sent | Pass / not observable | Probe 08:40:10 to 08:40:11 (0.9 s), succeeded; stored device kept; `adapter_pre_initialised=False`. New Setup visibility not observable in 0.9 s |
| B4 | 34781bfe | Cancel during scan: WELCOME unchanged for 45 s | Pass | Three cancels (two in the 2 s delay, one during a scan); each completion ignored; WELCOME unchanged |
| B5 | 34781bfe | Empty scan: "No devices found", no rescan | Pass / not observable | No rescan in 2 min 42 s. Empty list not producible: named devices always in range |
| B5 | b4f9607a, 34781bfe | Fallback: phone listed with notice | Pass | 09:39:36: two named devices offered, notice set. Scan 58 s. Notice text truncated to "No ELM327 fo…" (`ai/task.md`) |
| B6 | 2550e4ee | Slow swipe navigates; held button presses; long press at rest toggles palette | Pass | Swipe 9.98 s/232 px opened OPTIONS; hold on Debug 4.47 s toggled Debug; holds of 2.93 s and 1.43 s at rest toggled the palette |
| B7 | 2550e4ee | Cause line legible; Clear settings works | Pass | Cause line readable and fits; Clear settings 09:50:33; setup completed 09:50:58 |
| B8 | 34781bfe | Simulated session completes; notice as expected | Pass | Opened on CURRENT_DEVICE (stored simulated device); notice shown; simulated failure, Retry on PAIRING retried the pairing; setup 09:54:40 |
| B9 | — | Logs collected | Done | Debug off; logs in `logs/` |

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-12 | Initial procedure for device session B (runs 4 and 5 of proposal-71ab3751). |
| 1.1 | 2026-11-12 | Session run; results and notes recorded. |

---

Copyright (c) 2026 William Watson. MIT License.
