Created: 2026 August 19

# Report: `gtach.service` Boot Dependency Reduction

---

## Table of Contents

- [1.0 Summary](<#1.0 summary>)
- [2.0 Changes Made](<#2.0 changes made>)
- [3.0 Verification](<#3.0 verification>)
- [4.0 Judgement Calls and Discrepancies](<#4.0 judgement calls and discrepancies>)
- [5.0 Document Status](<#5.0 document status>)
- [Version History](<#version history>)

---

## 1.0 Summary

Subjectively long device boot time was diagnosed and reduced by restructuring
`bin/gtach.service`'s systemd unit dependencies. GTach's start time (kernel
handoff to `gtach.service` becoming active) fell from approximately 16.25s to
approximately 11.67s, a reduction of approximately 4.6s (28%). No source code
was changed; the change is confined to `bin/gtach.service` and host service
enablement state.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Changes Made

### 2.1 `bin/gtach.service`

`After=` was changed from `multi-user.target bluetooth.service
gtach-boot-splash.service` to `local-fs.target bluetooth.service
gtach-boot-splash.service hyperpixel2r-init.service`.

`multi-user.target` transitively pulled in `webmin.service`, which in turn
required `network-online.target`, which waits on `dhcpcd.service` (DHCP
lease negotiation). This chain accounted for the majority of the delay
between kernel handoff and GTach start, despite GTach having no functional
dependency on any of the three.

An intermediate revision added `network-online.target` to `After=` and
`Wants=network-online.target`, reflecting an initial (later corrected)
assumption that GTach required network availability at startup. This was
superseded within the same session — see §4.1.

### 2.2 Host service state (not repository-tracked)

The following units were disabled and masked on `root@gtach.local`:

- `webmin.service`
- `nfs-server.service`
- `nfs-idmapd.service`
- `rpcbind.service`
- `ModemManager.service`

None were functionally required. `ModemManager.service` was verified before
masking to confirm it does not govern the device's USB Ethernet gadget
interface (`usb0`) — see §4.2. Masking these did not directly shorten
`gtach.service`'s critical path but removed dead weight from general boot
`blame` output.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Verification

Measurements taken via `systemd-analyze`, `systemd-analyze blame`, and
`systemd-analyze critical-chain gtach.service` on `root@gtach.local`, at
each stage of the change.

| Stage | Userspace boot | `gtach.service` start | Critical path |
|---|---|---|---|
| Baseline | 16.374s | ~16.25s | `multi-user.target` → `webmin.service` → `network-online.target` → `dhcpcd.service` (8.325s) |
| After `multi-user.target` removal (network-online.target retained) | 12.276s | ~12.13s | `network-online.target` → `dhcpcd.service` (7.464s) |
| After `network-online.target` removal | 12.141s | ~11.67s | `bluetooth.service` → `bthelper@hci0.service` (gated by `hciuart.service`, 6.399s) |

Final critical chain:

```
gtach.service +15ms
└─ bluetooth.service @11.175s +497ms
   └─ bthelper@hci0.service @11.095s +59ms
      └─ system-bthelper.slice
```

`hciuart.service` (onboard Bluetooth controller UART attach and firmware
upload) is now the dominant cost on GTach's path. This is a fixed hardware
initialization cost and was not pursued further — see §4.3.

Total device boot (`systemd-analyze` top line) fell from 18.407s to
14.156s.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Judgement Calls and Discrepancies

### 4.1 Network dependency reassessment

The initial change retained `network-online.target` on the stated basis
that "GTach requires network availability." Source inspection of `src/`
(pattern search for `requests\.`, `urllib`, `socket\.connect`, `http(s)://`,
`urlopen`) returned zero matches, and `bin/gtach-preflight.sh`'s update
mechanism was confirmed to read a local filesystem marker
(`updates/.install-pending`), not a network resource. The stated
requirement was clarified to mean device-level network availability
(SSH, management access) rather than a `gtach.service` startup
precondition. `network-online.target` was removed from `After=`
accordingly; device network access is unaffected since `dhcpcd.service`,
`sshd`, and `wpa_supplicant` are not otherwise altered.

### 4.2 `ModemManager.service` verification before masking

Because `ModemManager.service` can in principle govern USB-attached network
hardware, its function was confirmed before masking rather than assumed.
`systemctl status` showed it running but failing to bind any device
("couldn't check support for device"), and `ip -brief a` confirmed `usb0`
or `wlan0` are the device's actual network interfaces. This satisfies the
requirement to prefer confirmation over assumption for changes affecting
device connectivity.

### 4.3 `hciuart.service` not addressed

`hciuart.service` (6.399s, BCM43438 UART attach and firmware patch upload)
is now the largest single contributor to `gtach.service`'s start time. It
was assessed as hardware-bound and not a dependency-ordering artifact, and
was left unmodified: the estimated further reduction is small relative to
the effort and risk of altering firmware-upload timing, and this
assessment was accepted rather than pursued.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Document Status

This is a `bin/` script change, trivially exempt from the T03/T02/T04
workflow per `primer.md` §7.0. No issue, change, or prompt document exists
or is required for this change. Git commit is the audit record.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-19 | Initial report. |

---

Copyright (c) 2026 William Watson. MIT License.
