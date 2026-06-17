# GTach CLI Commands

## Mac — Build and Deploy

### Full deploy

Builds the wheel, stops the service, transfers all deploy files, installs, and restarts.

```shell
cd ~/Documents/GitHub/GTach && ./bin/deploy.sh
```

### Stage update for in-app install

Builds and transfers the wheel to the Pi drop directory. Use 'Check for updates'
in the GTach OPTIONS screen to install.

```shell
cd ~/Documents/GitHub/GTach && ./bin/deploy.sh --stage
```

### Transfer deploy files only (no build)

```shell
cd ~/Documents/GitHub/GTach && scp bin/install.sh gtach.service bin/gtach-preflight.sh root@gtach.local:/opt/gtach/
```

---

## Mac — Retrieve logs from Pi

### Startup log (written on every boot)

```shell
cd ~/Documents/GitHub/GTach/log && scp root@gtach.local:/opt/gtach/start.log .
```

### Debug log (written when debug is active)

```shell
cd ~/Documents/GitHub/GTach/log && scp root@gtach.local:/opt/gtach/debug.log .
```

---

## Mac — Retrieve ELM327 emulator logs

```shell
cd ~/Documents/GitHub/GTach/log && scp root@ELM327-Emulator.local:/opt/elm327/elm.log .
```

```shell
cd ~/Documents/GitHub/GTach/log && scp root@ELM327-Emulator.local:/opt/elm327/bt-server.log .
```

---

## Pi — Service control

```shell
systemctl start gtach
systemctl stop gtach
systemctl restart gtach
systemctl status gtach
```

### View live service output

```shell
journalctl -u gtach -f
```

---

## Pi — Manual launch (bypasses systemd)

Stop the service first to avoid two instances running simultaneously.

```shell
systemctl stop gtach
cd /opt/gtach && /opt/gtach/venv/bin/gtach --transport rfcomm
```

### With debug logging active from start

```shell
systemctl stop gtach
cd /opt/gtach && /opt/gtach/venv/bin/gtach --transport rfcomm --debug
```

### Simulate (no OBD adapter)

```shell
systemctl stop gtach
cd /opt/gtach && /opt/gtach/venv/bin/gtach --transport simbt
```

Log files are written to `/opt/gtach/start.log` and `/opt/gtach/debug.log` regardless
of launch method. The `--debug` flag activates `debug.log` from startup; the OPTIONS
screen debug toggle can activate it at runtime.

---

## Pi — Manual install (without deploy.sh)

```shell
cd /opt/gtach && /opt/gtach/install.sh /tmp/gtach-X.Y.Z-py3-none-any.whl
```
