Created: 2026 August 20

# Third-Party Attribution — HyperPixel 2r Driver

---

## Table of Contents

[1.0 Purpose](<#1.0 purpose>)
[2.0 Vendored Files](<#2.0 vendored files>)
[3.0 Source](<#3.0 source>)
[4.0 License](<#4.0 license>)
[5.0 Provenance](<#5.0 provenance>)
[Version History](<#version history>)

---

## 1.0 Purpose

This directory contains unmodified, compiled build output from Pimoroni's
`hyperpixel2r` driver repository, vendored into GTach so that `pi-install.sh`
can install the HyperPixel 2.1 Round display driver directly, without a live
dependency on the upstream repository at appliance setup time. None of the
files in this directory are authored by the GTach project.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Vendored Files

| File | Purpose | Original path on device |
|---|---|---|
| `hyperpixel2r.dtbo` | Compiled device-tree overlay for the HyperPixel 2.1 Round DPI display | `/boot/overlays/hyperpixel2r.dtbo` |
| `hyperpixel2r-init` | Driver initialisation binary, run by `hyperpixel2r-init.service` | `/usr/bin/hyperpixel2r-init` |
| `hyperpixel2r-rotate` | Display/touch rotation utility (unused by GTach; vendored for completeness) | `/usr/bin/hyperpixel2r-rotate` |
| `hyperpixel2r-init.service` | systemd unit that runs `hyperpixel2r-init` at boot; `gtach.service` depends on it | `/etc/systemd/system/hyperpixel2r-init.service` |

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Source

Origin repository: [github.com/pimoroni/hyperpixel2r](https://github.com/pimoroni/hyperpixel2r)

Companion touch-input library (not vendored; referenced for license
corroboration only): [github.com/pimoroni/hyperpixel2r-python](https://github.com/pimoroni/hyperpixel2r-python)

The exact upstream commit that produced these binaries was not recorded at
build time. Files were extracted from a working GTach installation rather
than built from source — see §5.0.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 License

MIT, inferred. The `pimoroni/hyperpixel2r` repository does not carry a
visible `LICENSE` file as of the date of this notice. MIT terms are inferred
from the following corroborating sources, not from the source repository
itself:

- The companion repository, `pimoroni/hyperpixel2r-python`, carries an
  explicit MIT license: [github.com/pimoroni/hyperpixel2r-python/blob/master/LICENSE](https://github.com/pimoroni/hyperpixel2r-python/blob/master/LICENSE)
- The `hyperpixel2r` PyPI package (the Python touch driver, distinct from
  but published alongside these binaries) lists "License: MIT License
  (MIT)", Author: Philip Howard: [pypi.org/project/hyperpixel2r](https://pypi.org/project/hyperpixel2r/)
- Pimoroni's published repositories are consistently MIT-licensed.

MIT License reference text: [opensource.org/license/mit](https://opensource.org/license/mit)

This inference is not a confirmation from Pimoroni or from the source
repository. If stricter certainty is required, contact Pimoroni directly
before further redistribution.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Provenance

Extracted from `root@gtach.local` via `bin/vendor-hyperpixel2r.sh`, from a
device running GTach v0.4.3, Debian GNU/Linux 11 (Bullseye), aarch64. Files
are unmodified binary/compiled artifacts specific to this architecture and
OS revision.

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---|---|---|
| 0.1 | 2026-08-20 | Initial notice — four artifacts vendored from gtach.local |

---

This NOTICE file: Copyright (c) 2026 William Watson. MIT License.
The binaries described herein: Copyright Pimoroni Ltd / Philip Howard, MIT License (inferred — see §4.0).
