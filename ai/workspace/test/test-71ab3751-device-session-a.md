# Device Session A: Runs 1 to 3 (71ab3751)

Created: 2026 November 11

## Table of Contents

- [1.0 Purpose and Scope](#10-purpose-and-scope)
- [2.0 Preparation](#20-preparation)
- [3.0 Commands](#30-commands)
- [4.0 Steps](#40-steps)
- [5.0 Results Sheet](#50-results-sheet)
- [Version History](#version-history)

---

## 1.0 Purpose and Scope

- This procedure verifies runs 1 to 3 of `proposal-71ab3751` on the Pi with the ELM327 emulator, as device session A in proposal §7.0. It is the gate before run 4.
- It covers `change-cfa4e617` (run 1, no behaviour change expected), `change-b4f9607a` (run 2) and `change-042dd7ff` (run 3).
- Steps are ordered so that no step depends on a later one. The step that reboots the Pi (A10) is last.
- Not covered on the device, because they cannot be provoked on demand; unit tests cover them:
  - the exit status after a startup failure or a watchdog exit (B04);
  - the watchdog record for a stalled non-critical thread (B07);
  - a late OBD reply (A12);
  - a serial unplug (A02), unless a USB ELM327 is available.

[Return to Table of Contents](#table-of-contents)

---

## 2.0 Preparation

- A clean `main` on the Mac that contains run 3 (`2cffdae`).
- The emulator at `ELM327-Emulator.local`, controllable over root ssh.
- Root ssh to `gtach.local`, and access to the Pi's touch screen.
- Note the Pi time at the start of each step; the log checks filter by it.

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
| Pi time | `ssh root@gtach.local 'date "+%F %T"'` |
| Socket count | `ssh root@gtach.local 'ls -l /proc/$(systemctl show -p MainPID --value gtach)/fd \| grep -c socket'` |
| Restart count | `ssh root@gtach.local 'systemctl show -p NRestarts -p ActiveEnterTimestamp gtach'` |

`Emulator radio off` and `on` assume that `bluetoothctl` controls the emulator's adapter. If they do not, use your usual way of making the emulator undiscoverable.

[Return to Table of Contents](#table-of-contents)

---

## 4.0 Steps

### 4.1 A1: Deploy and Startup (Runs 1 and 3)

1. Deploy:

   ```
   cd ~/Documents/GitHub/GTach
   git pull
   ./bin/deploy.sh
   ```

2. Watch the display through the splash screen. The gauge appears and RPM is shown.
3. Check run 1 (no change expected):
   - a long press on the gauge toggles the palette;
   - swipes reach OPTIONS and return;
   - OPTIONS buttons respond.
4. Check start.log:

   ```
   ssh root@gtach.local 'grep -c "importlib.resources failed" /opt/gtach/start.log; grep "Startup complete" /opt/gtach/start.log'
   ```

5. **Pass:**
   - the display, touch and palette behave as before;
   - the count is `0`, so the Python 3.9 engine-profile fault is fixed;
   - one "Startup complete" line is present.

### 4.2 A2: Validation Command Has No Side Effects (Run 3, G01)

1. Record start.log and the debug log files:

   ```
   ssh root@gtach.local 'sha256sum /opt/gtach/start.log; ls -l /opt/gtach/debug.log*'
   ```

2. Run the validation:

   ```
   ssh root@gtach.local '/opt/gtach/venv/bin/gtach --validate-config; echo "exit $?"'
   ```

3. Repeat the command of item 1.
4. **Pass:**
   - item 2 prints "Config valid:" and `exit 0`;
   - the checksum and the debug.log file list are identical before and after.

### 4.3 A3: Debug Toggle (Run 3, O1)

1. On the display, set OPTIONS → "Debug: On". Note the Pi time.
2. Wait 10 s, then count the debug.log lines:

   ```
   ssh root@gtach.local 'grep -c "" /opt/gtach/debug.log'
   ```

3. Wait 10 s and repeat item 2.
4. **Pass:**
   - the count grows between items 2 and 3;
   - `grep "Debug logging enabled" /opt/gtach/debug.log` finds the line.
5. Leave Debug on for steps A4 to A10.

### 4.4 A4: Link Loss, Refused Connects, Reconnect (Run 2, A03 and A04)

1. Note the Pi time. Run `Emulator off`.
2. The display shows DISCONNECTED with a cause line. Note the cause text.
3. Wait 90 s, so that more than six connect attempts are refused. Note the cause text again.
4. Run `Emulator on`. The link and RPM return.
5. **Pass:**
   - after 90 s the cause is not "bluetooth wedged - reset required" (A03);
   - a cause line is shown as soon as DISCONNECTED appears (A04);
   - GTach reconnects without operator action.

### 4.5 A5: Setup During a Connect Attempt (Run 2, A01; Run 3, B02)

1. Run `Socket count` while RPM is shown. Note the number.
2. Run `Emulator off`. Wait for DISCONNECTED.
3. Run `Emulator on`, and tap Setup on the display within about 2 s, while GTach is reconnecting.
4. CURRENT_DEVICE appears. Wait 15 s, then run `Socket count` again.
5. Tap Continue.
6. Check the probe, the ATZ path and EBUSY:

   ```
   ssh root@gtach.local 'grep -E "adapter_pre_initialised|Skipping ATZ" /opt/gtach/debug.log | tail -3; grep -c "Device or resource busy" /opt/gtach/error.log'
   ```

7. **Pass:**
   - Continue completes setup and RPM returns, with no "Device not available";
   - the socket count in item 4 is not higher than in item 1;
   - the last record reads `adapter_pre_initialised=False` and there is no new "Skipping ATZ" record (B02 interim: ATZ is always sent until run 4);
   - the EBUSY count has not increased since step A4.
8. The race in item 3 depends on timing. If RPM returned before the tap reached the display, repeat items 2 to 5 up to three times and record how many attempts were made.

### 4.6 A6: Discovery Duration and Fallback (Run 2, A06, A07 and D1)

1. With the emulator on, open OPTIONS → "Clear settings" → "Clear". This removes the stored adapter and opens WELCOME. Note the Pi time, then tap Start Setup.
2. Wait for DEVICE_LIST, tap ELM327-Emulator, and let pairing finish. RPM returns.
3. Read the scan duration and the OBD start:

   ```
   ssh root@gtach.local 'grep -E "Starting .*discovery|Discovery complete|hcitool returned|adapter_pre_initialised" /opt/gtach/debug.log | tail -6'
   ```

4. Run `Emulator radio off`. Open OPTIONS → "Clear settings" → "Clear" again, note the Pi time, and tap Start Setup.
5. Let one scan finish. Note what the display shows:
   - DEVICE_LIST with other named Bluetooth devices: the fallback works;
   - DISCOVERY repeating: no named device was in range. Run 4 changes this behaviour.
6. Run the command of item 3 again.
7. Run `Emulator radio on`. Tap Cancel if DISCOVERY is shown, or Retry if DEVICE_LIST is shown. Start a scan, pair ELM327-Emulator again, and wait for RPM. No adapter is stored at this point, so setup cannot be left without pairing.
8. **Pass:**
   - with the emulator on, discovery ends early once the emulator is found;
   - with the radio off, one scan completes in under about 100 s;
   - no "hcitool returned" warning appears unless the adapter was busy;
   - after pairing, `adapter_pre_initialised=False` (B02 interim).

   Record both durations. The fallback outcome is an observation, not a pass criterion.

### 4.7 A7: Vehicle Off (Run 2, A05)

1. Note the Pi time. Set the emulator so that `0100` answers `NO DATA`, in your usual way. Leave it for 2 minutes.
2. Check error.log from the noted time:

   ```
   ssh root@gtach.local 'grep -E "Vehicle not answering|Initialization failed|Traceback" /opt/gtach/error.log | tail -6'
   ```

3. Return the emulator to normal. RPM returns. Check:

   ```
   ssh root@gtach.local 'grep "Vehicle answered 0100" /opt/gtach/debug.log | tail -1'
   ```

4. **Pass:**
   - item 2 shows "Vehicle not answering" WARNING records at least 60 s apart, about two for the 2 minutes;
   - item 2 shows no "Initialization failed" and no traceback from this window;
   - item 3 finds one recovery record.

### 4.8 A8: Exit Status on Stop (Run 3, B04)

1. Stop the service and read its result:

   ```
   ssh root@gtach.local 'systemctl stop gtach; systemctl show -p Result -p ExecMainStatus gtach; systemctl start gtach'
   ```

2. **Pass:** `Result=success` and `ExecMainStatus=0`. The display returns after the start.

### 4.9 A9: Simulated Bluetooth Session (Run 2, A10; Run 3, B01)

1. Record the real device store:

   ```
   ssh root@gtach.local 'sha256sum /opt/gtach/config/devices.yaml'
   ```

2. Stop the service and start a simulated session in a separate terminal on the Mac. It runs in the foreground until stopped with Ctrl-C:

   ```
   ssh -t root@gtach.local 'systemctl stop gtach; cd /opt/gtach; /opt/gtach/venv/bin/gtach --transport simbt --debug'
   ```

3. On the display, complete setup with one of the simulated devices. Simulated pairing fails about one time in five; tap Retry if it does.
4. Re-enter setup: OPTIONS → "Clear settings" → "Clear". Complete setup again.
5. Stop the session with Ctrl-C in its terminal, then check the files and restart the service:

   ```
   ssh root@gtach.local 'sha256sum /opt/gtach/config/devices.yaml; ls -l /opt/gtach/config/devices-sim.yaml; grep -cE "Starting device discovery for" /opt/gtach/debug.log; systemctl start gtach'
   ```

6. **Pass:**
   - the devices.yaml checksum is unchanged (A10);
   - `devices-sim.yaml` exists;
   - the hcitool count is `0`, so the re-entered setup used the simulated back end (B01).
7. Confirm that the restarted service reconnects to the real adapter without setup.

### 4.10 A10: Reset Outcome (Run 3) — Reboots the Pi

1. Confirm OPTIONS shows "Debug: On"; set it if the restart in A9 turned it off.
2. Run `Emulator off`. On DISCONNECTED, tap Reset. The Pi reboots.
3. After the Pi is back (about 1 minute), run `Emulator on`, then check:

   ```
   ssh root@gtach.local 'grep "Reset outcome" /opt/gtach/debug.log.1 | tail -1; grep "/sbin/reboot returned" /opt/gtach/error.log | tail -1'
   ```

4. **Pass:**
   - the Pi rebooted;
   - either no outcome record was written before the process ended, or the record reads "reboot initiated";
   - a "/sbin/reboot returned" warning, if present, names the return code. Record it, because it decides the earlier 2026-10-09 observation.

### 4.11 A11: Collect Evidence

1. Copy the logs back:

   ```
   scp 'root@gtach.local:/opt/gtach/{error,debug,start}.log*' ai/workspace/test/
   ```

2. Run `Restart count`. Record NRestarts.
3. Turn Debug off on the display.

[Return to Table of Contents](#table-of-contents)

---

## 5.0 Results Sheet

| Step | Change | Check | Result | Note |
|---|---|---|---|---|
| A1 | cfa4e617 | Display, touch, palette unchanged | | |
| A1 | 042dd7ff | No importlib.resources failure; startup complete | | |
| A2 | 042dd7ff | `--validate-config` leaves logs untouched | | |
| A3 | 042dd7ff | Debug toggle writes debug.log | | |
| A4 | b4f9607a | No wedge cause after refusals; cause shown; reconnect | | |
| A5 | b4f9607a | No leaked socket; Continue succeeds; no EBUSY | | Attempts: |
| A5 | 042dd7ff | ATZ sent after the probe path | | |
| A6 | b4f9607a | Scan durations: emulator on / radio off | | |
| A6 | b4f9607a | Fallback observation | | |
| A6 | 042dd7ff | ATZ sent after pairing | | |
| A7 | b4f9607a | Vehicle off: rate-limited WARNING, no traceback, recovery record | | |
| A8 | 042dd7ff | Stop: Result=success, status 0 | | |
| A9 | b4f9607a | devices.yaml unchanged; devices-sim.yaml used | | |
| A9 | 042dd7ff | Re-entered setup uses the simulated back end | | |
| A10 | 042dd7ff | Reset: reboot; outcome record and return code | | |
| A11 | — | NRestarts | | |

[Return to Table of Contents](#table-of-contents)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-11-11 | Initial procedure for device session A (runs 1 to 3 of proposal-71ab3751). |

---

Copyright (c) 2026 William Watson. MIT License.
