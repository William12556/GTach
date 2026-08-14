Created: 2026 August 14

# Report: Deploy Reboot Addition and Boot-Splash Install Fix

---

## Table of Contents

- [1.0 Purpose](<#1.0 purpose>)
- [2.0 Background](<#2.0 background>)
- [3.0 Root Cause](<#3.0 root cause>)
- [4.0 Changes Applied](<#4.0 changes applied>)
- [5.0 Verification](<#5.0 verification>)
- [6.0 Commit Record](<#6.0 commit record>)
- [Version History](<#version history>)

---

## 1.0 Purpose

Records a conversational fix to `bin/deploy.sh` and `bin/install.sh`.
Both files are deployment tooling under `bin/`, not `src/`; per
`primer.md` §7.0, change documentation scope applies to `src/` changes
only, so no `issue`/`change`/`prompt` T-Doc triple was created. This
report exists at the requester's instruction as a standalone record.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Background

The requester reported that GTach never restarted after a normal
deploy — a manual Pi reboot was always required. The first hypothesis
was that `deploy.sh` simply lacked a reboot step, since
`gtach.service`'s `After=gtach-boot-splash.service` is ordering-only
and does not pull `gtach-boot-splash.service` in when `gtach` is
started directly via `systemctl start gtach`. `gtach-boot-splash.service`
performs the `KD_GRAPHICS` switch on `tty1` that stops `fbcon` from
compositing onto `/dev/fb0`; skipping it leaves `fbcon` active and able
to interfere with GTach's direct framebuffer renderer.

A reboot was added to `deploy.sh` on that basis. The requester then
reported the Pi still did not reboot after the change.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Root Cause

A full `./bin/deploy.sh` run was captured and read end to end. Output
stopped immediately after:

```
==> Registering boot splash
install: '/opt/gtach/boot-splash.raw' and '/opt/gtach/boot-splash.raw' are the same file
```

`install.sh` is copied to and executed from `$INSTALL_DIR` (`/opt/gtach`)
on the Pi, so `SCRIPT_DIR` (derived from `dirname "$0"`) resolves to the
same path as `$INSTALL_DIR`. The boot-splash copy step ran
unconditionally:

```bash
install -m 0644 "$SCRIPT_DIR/boot-splash.raw" "$INSTALL_DIR/boot-splash.raw"
```

Source and destination were therefore the same file. The `install`
command refuses this and exits non-zero. `install.sh` has `set -e`, so
it aborted at that line — before `systemctl daemon-reload`,
`systemctl enable gtach`, and `systemctl enable gtach-boot-splash` ever
ran. `deploy.sh` also has `set -e`; the non-zero return from the
`ssh ... install.sh` call aborted `deploy.sh` in turn, before
`systemctl start gtach` and before the newly-added reboot lines.

This — not merely a missing reboot — was the actual cause of GTach
failing to restart reliably after deployment: the systemd unit files
were frequently never (re-)enabled or reloaded on the Pi.

The equivalent copy step for `gtach-preflight.sh`, two lines above,
already guarded against this exact collision:

```bash
if [ "$SCRIPT_DIR/gtach-preflight.sh" != "$INSTALL_DIR/gtach-preflight.sh" ]; then
    install -m 0755 "$SCRIPT_DIR/gtach-preflight.sh" "$INSTALL_DIR/gtach-preflight.sh"
else
    chmod 0755 "$INSTALL_DIR/gtach-preflight.sh"
fi
```

`boot-splash.raw` lacked the equivalent guard.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Changes Applied

### 4.1 `bin/deploy.sh`

Added a reboot after the existing `systemctl start gtach` step, in full
deploy mode only (`--stage` mode is unaffected):

```bash
echo "==> Starting GTach service..."
ssh "$PI" "systemctl start gtach"

echo "==> Rebooting Pi..."
ssh "$PI" "reboot" || true

echo ""
echo "✓ Deployed v$VERSION to Pi. Pi is rebooting."
```

The `systemctl start gtach` call is retained as a pre-check per the
requester's instruction, even though the following reboot makes the
service's running state at that moment immaterial.

### 4.2 `bin/install.sh`

Guarded the `boot-splash.raw` copy step with the same same-file check
already used for `gtach-preflight.sh`:

```bash
echo "==> Registering boot splash"
install -m 0644 "$SCRIPT_DIR/gtach-boot-splash.service" /etc/systemd/system/gtach-boot-splash.service
if [ "$SCRIPT_DIR/boot-splash.raw" != "$INSTALL_DIR/boot-splash.raw" ]; then
    install -m 0644 "$SCRIPT_DIR/boot-splash.raw" "$INSTALL_DIR/boot-splash.raw"
else
    chmod 0644 "$INSTALL_DIR/boot-splash.raw"
fi
```

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Verification

1. Manual `ssh root@gtach.local "reboot"` confirmed the reboot mechanism
   itself was sound (`Connection to gtach.local closed by remote host`,
   the expected signature of a reboot dropping the SSH session).
2. `ssh root@gtach.local "systemd-inhibit --list"` showed one `delay`-mode
   inhibitor (`ModemManager`), which postpones but does not block
   shutdown — ruled out as the cause.
3. A full `./bin/deploy.sh` run was captured and read in full, isolating
   the `install` same-file failure as the point of abort.
4. After applying both fixes, the requester re-ran `./bin/deploy.sh` and
   confirmed the fix worked: the install step completed, the service
   started, and the Pi rebooted with GTach running afterward — with no
   manual reboot required.

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Commit Record

Both files were edited directly in the local working tree via Filesystem
MCP tools, with human approval given per proposed change before each
edit. No T-Doc triple applies (`bin/`, not `src/`). Commit is the sole
audit record, per the trivial-change precedent in `primer.md` §7.0.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-14 | Initial report. Records the addition of a post-deploy Pi reboot to `bin/deploy.sh` and the same-file collision fix to the `boot-splash.raw` install step in `bin/install.sh`, which was the actual root cause of GTach failing to restart reliably after deployment. Fix confirmed working by the requester after re-running `./bin/deploy.sh`. |

---

Copyright (c) 2026 William Watson. MIT License.
