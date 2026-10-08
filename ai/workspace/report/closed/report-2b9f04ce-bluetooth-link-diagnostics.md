Created: 2026 August 12

# Report: Bluetooth Link Diagnostics — Session Record for Later Investigation

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Headline Finding](<#2.0 headline finding>)
- [3.0 Environment](<#3.0 environment>)
- [4.0 Timeline of Evidence](<#4.0 timeline of evidence>)
- [5.0 Established Facts](<#5.0 established facts>)
- [6.0 Ruled Out](<#6.0 ruled out>)
- [7.0 Open Hypotheses](<#7.0 open hypotheses>)
- [8.0 Diagnostics for the Next Session](<#8.0 diagnostics for the next session>)
- [9.0 Command Reference](<#9.0 command reference>)
- [10.0 Impact on Active T-Docs](<#10.0 impact on active t-docs>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Record of the 2026-08-12 on-target Bluetooth investigation on
`gtach.local`, written so a later session can resume without repeating
the work. It states what is established, what has been eliminated, what
remains hypothesis, and what to run next.

Scope is the Bluetooth link only. GTach code defects found during the
session are recorded in their own T-Docs and are referenced rather than
restated.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Headline Finding

**GTach's link-loss handling works. The reconnection it attempts is
blocked by a host-level Bluetooth fault, not by application code.**

At 15:27 the full chain fired in order for the first time — display
detection, transport teardown, and resumption of retries — and every
subsequent connect attempt failed with `[Errno 16] EBUSY` on a
controller that had been passing traffic five seconds earlier.

Two distinct populations of `EBUSY` were observed during the session and
must not be conflated:

| | Cause | Cleared by |
|---|---|---|
| Population A | `hciuart` failing to attach the chip | Cold power cycle |
| Population B | Loss of an established link | Not yet cleared |

Population A is understood and fixed. **Population B is the open
problem**, and it is now reproducible on demand.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Environment

| Element | Value |
|---|---|
| Client | `gtach.local`, Raspberry Pi Zero 2W, BD `B8:27:EB:C4:D7:A7`, name `gtach` |
| Client controller | Broadcom BCM43430A1 over UART, HCI 4.2, firmware via `SYN43430A1.hcd` |
| Server | `ELM327-Emulator.local`, Raspberry Pi 4, BD `DC:A6:32:54:AD:77` |
| Server service | `elm327-emulator.service`, active running |
| Server profile | Serial Port (SPP, `0x1101`) on RFCOMM channel 1 |
| Adapter reported | `ELM327 v1.5` |
| GTach | v0.4.1 |

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Timeline of Evidence

### 4.1 Morning — population A

Persistent `[Errno 16]` on every connect attempt including the first of
a fresh process. Established by `hcitool con` that an ACL to
`DC:A6:32:54:AD:77` existed in **state 9 (`BT_CLOSED`)** with its handle
unreaped; `hcitool dcc` timed out; `hciconfig hci0 down` succeeded and
`hciconfig hci0 up` returned `ETIMEDOUT`, leaving the controller unable
to initialise.

The condition survived a warm reboot — `stacks.log` headers show pid 720
at 14:52:37 then pid 671 at 14:56:32, a decreasing pid, with identical
failures resuming immediately on the new run.

Root cause established later: `hciuart.service` was not attaching the
chip. `journalctl -u hciuart` shows `Initialization timed out` at
15:11:44. A **cold power cycle** resolved it; the boot at 15:12:57
completed `Device setup complete` and `hciconfig -a` then reported
`UP RUNNING`, `Name: 'gtach'`, zero errors.

### 4.2 Afternoon — a working link

Pairing performed. `bluetoothctl info` reported `Paired: yes`,
`Trusted: yes`, `Connected: yes`, with the Serial Port UUID present.
RPM went live. `debug.log.1` records 181 successful `RX:` responses
including the adapter identifying itself as `ELM327 v1.5`.

### 4.3 15:27 — population B, the reproducible case

Emulator stopped deliberately, to exercise the link-loss path.

```
15:27:21.754  DisplayManager INFO  Link lost — no data for 2.0s
15:27:25.096  RFCOMMTransport INFO Link to RFCOMM device
                DC:A6:32:54:AD:77 on channel 1 dropped -
                will attempt to reconnect
15:27:25.388  RFCOMMTransport INFO Link lost - resuming reconnection
                attempts in 5.0 seconds
15:27:30.402  RFCOMMTransport ERROR Failed to connect ... [Errno 16]
                Device or resource busy (bluetooth link busy - may need reset)
15:27:35.413  ... same
15:27:40.415  ... same
15:27:45.430  ... same
15:28:00.440  ... channel 1: timed out
15:28:05.462  ... [Errno 16] (bluetooth wedged - reset required)
```

Five seconds separate a clean local socket close from the first `EBUSY`.
Restarting the emulator did not restore the link.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Established Facts

1. **The GTach link-loss chain is verified.** All three mechanisms of
   `change-9c2f41d8` fired, in order, at 15:27:21–15:27:25: sustained
   read timeouts marked the transport down, `drop_link` closed the link
   without setting the shutdown event, and the supervising loop resumed
   retrying. This path had never executed before, there having been no
   link to lose since the change was deployed.

2. **`EBUSY` follows link loss on a healthy controller.** The controller
   was passing traffic at 15:26:53 and refusing connections by 15:27:30.
   No controller fault, no `hciuart` failure, and no reboot intervened.

3. **The server side is healthy and correctly configured.**
   `sdptool browse local` on the emulator shows Serial Port on RFCOMM
   channel 1; `elm327-emulator.service` is active running; `hcitool con`
   and `rfcomm` on the emulator both show nothing held.

4. **`hciuart` cannot be restarted reliably on a live system.**
   `systemctl restart hciuart` produced `Initialization timed out`.
   Only a cold power cycle recovered the chip. A warm `reboot` does not
   remove power from the BCM43430A1 and did not clear population A.

5. **The pairing is not bonded.**
   `/var/lib/bluetooth/B8:27:EB:C4:D7:A7/DC:A6:32:54:AD:77/info`
   contains `[General]` and `[DeviceID]` but **no `[LinkKey]` section**,
   while `bluetoothctl` reports `Paired: yes`. `[General]` and
   `[DeviceID]` are written for any device merely seen or connected. The
   absence of a link key indicates an unbonded "just works" SPP
   connection that is not persisted.

6. **The emulator holds no reciprocal record.** Its paired list contains
   two Macs and a device named `NCC 1701`; `B8:27:EB:C4:D7:A7` is
   absent. The `bluetoothctl trust` run there used the emulator's own
   address by mistake and returned `not available`; it must be run
   against `B8:27:EB:C4:D7:A7`.

7. **GTach reports the condition correctly throughout.** The classified
   causes delivered by `change-5e7a03c4` — `bluetooth link busy - may
   need reset`, escalating to `bluetooth wedged - reset required` — are
   accurate descriptions of the observed state.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Ruled Out

| Hypothesis | Evidence against |
|---|---|
| A surviving second GTach process holding the socket | `pgrep -a gtach` returned one pid matching systemd's `Main PID` |
| GTach connecting to its own adapter address | `hciconfig -a` — client `B8:27:EB:C4:D7:A7`, server `DC:A6:32:54:AD:77`; different |
| The emulator holding the RFCOMM channel | `hcitool con` empty and `rfcomm` silent on the emulator |
| The emulator not serving SPP | `sdptool browse local` shows Serial Port on channel 1 |
| The ELM327 service not running | `systemctl list-units` shows it active running |
| A GTach defect in link-loss detection | The full chain fired correctly at 15:27:21–15:27:25 |
| A GTach defect in reconnection logic | Retries resumed at the correct 5.0 s cadence and continued indefinitely |
| Serial console contending for the BT UART | Console is on `serial0` (mini-UART); `hciattach` uses `/dev/serial1` |
| Missing Bluetooth firmware | `BCM43430A1.raspberrypi,model-zero-2-w.hcd` resolves and flashed successfully |
| `dtoverlay=disable-bt` set | Not present in `/boot/config.txt` |

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Open Hypotheses

Ordered by how well each fits the evidence.

### 7.1 Kernel-side RFCOMM/ACL teardown on remote disappearance

The local socket is now closed correctly on link loss — `drop_link`
calls `_discard_handle_locked`, which closes the socket. If the kernel
does not reap the `hci_conn` when the remote vanishes without a clean
disconnect, the next connect to the same `(bdaddr, channel)` collides
and returns `EBUSY`. This matches the morning's directly observed
`state 9 (BT_CLOSED)` handle and the five-second interval between socket
close and first refusal.

**Test:** run `hcitool con` on `gtach.local` immediately after stopping
the emulator, and again 30 s later. A lingering handle confirms it.

### 7.2 Absence of a bond preventing re-authentication

The connection is unbonded (fact 5). A first connection may be accepted
"just works" while a reconnection to a device the controller now
considers previously-authenticated is refused, with no agent present to
answer. This would not explain `EBUSY` specifically, which is why it is
second rather than first, but the missing link key is a real defect in
the setup and must be eliminated before anything else is trusted.

**Test:** establish a genuine bond, then repeat the drop.

### 7.3 Controller firmware degradation on abnormal disconnection

The BCM43430A1 may enter a state on abrupt peer loss from which it
cannot open a new RFCOMM channel to the same address, without reporting
a controller-level fault. Population A showed this chip is capable of
wedging in ways `hciconfig` cannot clear.

**Test:** after reproducing, try `hciconfig hci0 reset` and check
whether connection becomes possible. This is precisely the action
`change-8a63d5f1` proposes to put behind a button; the result decides
whether that button is worth having.

[Return to Table of Contents](<#table of contents>)

---

## 8.0 Diagnostics for the Next Session

Run in order. Stop when one of them explains the condition.

1. Establish a bonded pairing and confirm it on disk.
   Remove the existing record, re-pair, then verify a `[LinkKey]`
   section exists on **both** hosts. Do not proceed until it does.

2. With RPM live, capture the baseline: `hcitool con` on `gtach.local`.

3. Stop the emulator. Within 10 s run `hcitool con` again. Record
   whether a handle to `DC:A6:32:54:AD:77` remains and in what state.
   **This single observation discriminates hypothesis 7.1.**

4. Wait 60 s. Repeat `hcitool con`. Record whether the handle is reaped
   on a timer.

5. Attempt `hciconfig hci0 reset`, then observe whether GTach's next
   retry succeeds. This tests 7.3 and decides `change-8a63d5f1`.

6. If the handle lingers and `reset` does not clear it, capture
   `btmon` across a reproduction. That is the authoritative view of what
   the controller is being asked and what it answers.

7. Restart the emulator only after the above, so that recovery is not
   conflated with reaping.

[Return to Table of Contents](<#table of contents>)

---

## 9.0 Command Reference

Corrected for the versions on these hosts; two commands used during the
session were rejected by `bluetoothctl` and are noted.

```bash
# Controller health — expect UP RUNNING and a Name line
hciconfig -a

# Active links and their state (state 9 = BT_CLOSED)
hcitool con

# Pairing, as reported by the daemon
bluetoothctl devices Paired          # NOT `paired-devices`, removed
bluetoothctl info <REMOTE_BD>

# Pairing, as persisted on disk — the authoritative check
grep -c LinkKey /var/lib/bluetooth/<LOCAL_BD>/<REMOTE_BD>/info

# Server-side service records
sdptool browse local                 # on the emulator

# Trust — must name the REMOTE address, not the local adapter
bluetoothctl trust B8:27:EB:C4:D7:A7   # run ON the emulator
bluetoothctl trust DC:A6:32:54:AD:77   # run ON gtach.local

# Attach service
systemctl status hciuart.service -l --no-pager
journalctl -u hciuart -n 50 --no-pager
```

**Recovery, in ascending order of severity.** Note that only the last
has been observed to work on this hardware:

```bash
hciconfig hci0 reset               # untested against population B
systemctl restart hciuart          # observed to FAIL: Initialization timed out
# cold power cycle                 # observed to WORK for population A
```

[Return to Table of Contents](<#table of contents>)

---

## 10.0 Impact on Active T-Docs

| T-Doc | Status after this session |
|---|---|
| `issue-9c2f41d8` | Detection, teardown and retry resumption **verified on target** at 15:27. Reconnection success remains unverified, blocked by the host condition, not by GTach. |
| `issue-5e7a03c4` | Iteration 2 verified in part: the drop cause was populated where it was previously blank, and escalation to the wedge diagnosis occurred at 15:28:05. |
| `issue-4f1e82b7` | Not assessed this session; the arc's behaviour during a blocked connect was not observed. |
| `issue-8a63d5f1` | Its value now hinges on diagnostic step 5. If `hciconfig hci0 reset` clears population B, the button is worth building; if not, it addresses only population A, which a power cycle already covers. |
| `issue-2ac1c602` | Unchanged. No watchdog critical timeout has occurred since 2026-08-12 07:40:03. The restarts observed this session were reboots and redeploys. |

**Recommendation.** Do not close `issue-9c2f41d8` on the strength of
15:27 alone. The three mechanisms it delivered are proven; the outcome
they exist to produce — a restored link — has never been observed. Close
it when a reconnection succeeds.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-12 | Initial report. Records the 2026-08-12 Bluetooth investigation: two distinct EBUSY populations, the cold-power-cycle recovery of the attach failure, verification of GTach's link-loss chain, the unbonded pairing, and the diagnostics to run next. |

---

Copyright (c) 2026 William Watson. MIT License.
