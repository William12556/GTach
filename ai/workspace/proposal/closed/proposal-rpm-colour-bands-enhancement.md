# GTach RPM Colour Band Enhancement Proposal

Created: 2026 April 23

> **Status: Closed — obsolete (2026-11-11).** Implemented through issue/change 3f7a1b9c and since superseded by later changes. This document is retained as a historical record only; the current source is authoritative. Known divergences:
>
> - Band 2 is blue (torque approach), not black (`models.py` `DAY_PALETTE` / `NIGHT_PALETTE`).
> - The 2 Hz redline pulse (§2.3, §5.4) is not present; the later shift-cue flash was removed with the rim (issue-950128c0).
> - Thresholds are set by engine profile selection only; no per-threshold `display.rpm_bands` override exists (§2.2).
> - `abarth_595_turismo` `redline_rpm` is 6500, not 6000 (`assets/engine_profiles.yaml`).
> - Day/night palettes (change-5012004e) and the band-coloured centre disc (change-64d8d8fc) are not described here.

---

## Table of Contents

- [1.0 Overview](<#1.0 overview>)
- [2.0 Proposed Changes](<#2.0 proposed changes>)
- [3.0 Engine Profile Example — Abarth 595 Turismo 1.4T](<#3.0 engine profile example — abarth 595 turismo 1.4t>)
- [4.0 Design Scope Impact](<#4.0 design scope impact>)
- [5.0 Requirements Impact](<#5.0 requirements impact>)
- [6.0 Operator Safety Notice](<#6.0 operator safety notice>)
- [7.0 Governance Pathway](<#7.0 governance pathway>)
- [Version History](<#version history>)

---

## 1.0 Overview

This proposal documents a set of enhancements to the GTach RPM colour band display system. The current implementation (REQ c3d4e5f6) uses four fixed, hard-coded colour bands. This proposal extends that design to six configurable bands with operator-selectable engine profiles, an operator safety acknowledgement requirement, and an additional display cue at redline.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Proposed Changes

### 2.1 Six-Band Colour Scheme

Replace the existing four fixed bands with six bands as follows:

| Band | Colour | Semantic |
|------|--------|----------|
| 1 | Blue (dim) | Idle — below useful torque range |
| 2 | Black | Below optimal torque range |
| 3 | Green | Optimal torque range |
| 4 | Yellow | Caution — approaching power peak |
| 5 | Orange | Warning — near redline |
| 6 | Red | Danger — at or above redline |

The colour progression provides an intuitive, unambiguous visual gradient from cold/idle through optimal use to danger.

### 2.2 Configurable RPM Thresholds

All six band boundaries shall be user-configurable via the YAML configuration file. Default values are loaded from the selected engine profile (see §2.5).

Configuration structure (proposed):

```yaml
display:
  rpm_bands:
    idle_max: 999         # Blue → Black transition
    torque_start: 3000    # Black → Green transition
    caution_start: 4500   # Green → Yellow transition
    warning_start: 5500   # Yellow → Orange transition
    danger_start: 5800    # Orange → Red transition; pulse begins here
    redline_rpm: 6000     # Red band onset; effective engine redline
```

Validation rules:
- All thresholds must be positive integers.
- Values must be strictly ascending: `idle_max < torque_start < caution_start < warning_start < danger_start < redline_rpm`.
- Invalid ordering produces a configuration warning and falls back to built-in defaults.
- Values must not exceed 15000 RPM (existing system ceiling).

### 2.3 Redline Pulse Effect

When RPM reaches `danger_start`, the background shall alternate between orange and a darker shade at 2 Hz. When RPM reaches `redline_rpm`, the background shall alternate between red and a darker shade (e.g. dark red / maroon) at 2 Hz. The pulse begins at `danger_start` — before redline — to provide an advance warning cue.

Implementation note: the pulse shall be implemented as a time-based toggle within the display rendering loop using `pygame.time.get_ticks()`. No additional thread is required.

### 2.4 Operator Safety Acknowledgement

On first run and after any change to RPM threshold configuration, the application shall display a one-time acknowledgement screen requiring the operator to confirm:

> **Notice:** The RPM band thresholds displayed by this application are configurable. It is the sole responsibility of the operator to verify that these thresholds accurately reflect the engine specifications of their vehicle. Incorrect settings may fail to warn of over-revving. Refer to your vehicle's owner manual or manufacturer's specifications.

- Acknowledgement requires a deliberate touch gesture (visible confirm button).
- Acknowledgement state is persisted to a separate state file, independent of the YAML configuration file. Resetting or regenerating the configuration does not invalidate the acknowledgement.
- The screen is not skippable.
- The screen does **not** appear on every startup — only on first run and after threshold or profile changes.

### 2.5 Engine Profile List

RPM threshold defaults shall be drawn from a built-in engine profile list rather than fixed constants. The operator selects a profile on first run or via configuration; the profile populates the threshold defaults.

- Profiles are stored in a YAML file (e.g. `engine_profiles.yaml`) shipped with the application.
- The profile file is loaded at application startup. Re-loading is available via setup mode; runtime dynamic reload is deferred.
- A mechanism shall be provided to add or update profiles without modifying application source code (i.e. via the profile YAML file).
- The operator may override individual thresholds after selecting a profile.
- The acknowledgement screen is triggered whenever a new profile is selected or thresholds are manually changed.

Initial profile list (minimum):

| Profile ID | Description |
|------------|-------------|
| abarth_595_turismo | Abarth 595 Turismo 1.4T (165 hp) |
| generic_turbo_4cyl | Generic turbocharged 4-cylinder |
| generic_na_4cyl | Generic naturally aspirated 4-cylinder |

### 2.6 Idle Band — RPM-Based Only

The idle band (blue, 0–999 RPM) is determined solely by RPM value. Detecting vehicle speed via OBD PID 0x0D would require polling a second PID, exposing a second data value through OBDProtocol, and combining two data sources in the band logic. The idle RPM range is a sufficient proxy for a stationary/unloaded engine. This complexity is not warranted.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Engine Profile Example — Abarth 595 Turismo 1.4T

The following specifications for the Abarth 595 Turismo 1.4T-Jet serve as the reference example and the default shipped profile. Operators must verify thresholds for their own vehicle.

### 3.1 Engine Specifications (Abarth 595 Turismo)

| Parameter | Value |
|-----------|-------|
| Displacement | 1,368 cc (1.4 L) |
| Configuration | Inline 4, turbocharged (Garrett) |
| Peak power | 165 hp @ 5,500 RPM |
| Peak torque | 230 N·m @ 3,000 RPM |
| Effective redline | ~6,000 RPM |
| Optimal torque RPM range | ~3,000–5,500 RPM |

Sources: PistonHeads Abarth 595 buying guide; Abarth official specifications; community technical data (Fiat 500 USA Forum).

### 3.2 Proposed Default Band Thresholds for Abarth 595 Turismo

| Band | Colour | RPM Range | Rationale |
|------|--------|-----------|-----------|
| 1 | Blue | 0–999 | Idle: below usable torque |
| 2 | Black | 1000–2999 | Sub-torque: engine warm but not loaded |
| 3 | Green | 3000–4499 | Optimal: torque peak available, within normal driving range |
| 4 | Yellow | 4500–5499 | Caution: approaching power peak, acceptable for brief periods |
| 5 | Orange | 5500–5799 | Warning: approaching redline; pulse onset at `danger_start` |
| 6 | Red | 5800+ | Danger: at or above effective redline (`redline_rpm`) |

> **Operator notice:** These thresholds are derived from published specifications for the Abarth 595 Turismo. They are not verified values. The operator is responsible for confirming all thresholds against their vehicle's documentation before use.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Design Scope Impact

### 4.1 Requirements — Direct Changes

| Requirement ID | Change |
|----------------|--------|
| c3d4e5f6 | Revise: fixed four-band model → configurable six-band model with engine profile selection; update acceptance criteria |
| a7b8c9d0 | Extend: add `rpm_bands` sub-section and `engine_profile` field to configuration schema |

### 4.2 New Functional Behaviour

- Engine profile list and selection mechanism (new REQ)
- Operator acknowledgement screen — first run and post-config-change (new REQ)
- Redline pulse at 2 Hz (new REQ)
- Configuration validation for band ordering (extend existing validation)

### 4.3 Design Documents — Affected

| Document | Section Affected |
|----------|-----------------|
| design-gtach-master.md | §9.1.3 DisplayConfig entity; §13.4 Display Mode Flow |
| design-2c6b8e4d-domain_display.md | Band rendering logic; acknowledgement state |
| design-c9d0e1f2-component_display_rendering_engine.md | Colour band lookup; pulse state |
| design-b4c5d6e7-component_utils_config_manager.md | `rpm_bands` schema; profile loading; threshold validation |

### 4.4 Scope Assessment

Moderate scope extension. Core architecture unchanged. Changes confined to display rendering and configuration domains. No transport, threading, or OBD protocol changes required.

The acknowledgement screen and profile selection introduce new transient display states not currently in the state machine (§13.4 of master design). These states must be added.

The engine profile YAML file is a new data artefact requiring a defined location, format, and load path.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Requirements Impact

### 5.1 REQ c3d4e5f6 — RPM Colour Bands (Revise)

Current: four fixed bands (black / green / yellow / red), hard-coded thresholds, not user-configurable.

Proposed: six bands (blue / black / green / yellow / orange / red), operator-configurable thresholds via YAML, `danger_start` and `redline_rpm` as distinct values, defaults loaded from selected engine profile, validation enforces strictly ascending order, pulse begins at `danger_start` and continues through `redline_rpm` band at 2 Hz.

### 5.2 New REQ — Engine Profile List

Application shall ship a YAML engine profile file containing at minimum three profiles. Operator selects a profile on first run. Profile thresholds populate the configuration defaults. The profile file shall be updatable without modifying application source code.

### 5.3 New REQ — Operator Threshold Acknowledgement

Application shall present a safety notice on first run and after any threshold or profile change, requiring deliberate touch confirmation. Acknowledgement state persisted to a separate state file, independent of the YAML configuration. Not triggered on every startup.

### 5.4 New REQ — Redline Pulse

When RPM reaches `danger_start`, the background shall pulse at 2 Hz. Pulse continues when RPM enters the red band (`redline_rpm`). Pulse colour reflects the active band (orange pulse in danger band; red pulse in redline band).

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Operator Safety Notice

The following notice is proposed for the application acknowledgement screen and user-facing documentation:

---

**RPM Band Threshold Safety Notice**

GTach displays RPM warning bands based on configurable threshold values. These values are set by the operator and are not automatically derived from the vehicle.

**It is the sole responsibility of the operator to:**
- Verify that the configured RPM thresholds match their vehicle's engine specifications.
- Consult the vehicle manufacturer's documentation or a qualified technician.
- Ensure the thresholds reflect the correct redline, torque peak, and safe operating ranges for their engine.

Incorrect thresholds may result in the application failing to warn of potentially damaging over-revving conditions.

The developer of this application accepts no liability for damage arising from incorrect threshold configuration.

---

[Return to Table of Contents](<#table of contents>)

---

## 7.0 Governance Pathway

Full governance protocol required. Multiple source files affected; requirements must be updated; new display states must be designed; new data artefact (engine profile YAML) introduced.

Proposed workflow:

1. **Approve this proposal** (human)
2. **Update REQ c3d4e5f6** and add new requirements to `requirements-gtach-master.md`
3. **Create T03 Issue** — enhancement type, covering all proposed changes
4. **Create T02 Change** — referencing the T03 issue
5. **Update design documents** — master, domain_display, component_rendering_engine, component_config_manager
6. **Create T04 Prompt(s)** — one per component if context budget requires splitting
7. **Execute via Claude Code (Tactical Domain)**
8. **Update traceability matrix**
9. **Test and close**

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-04-23 | Initial proposal draft |
| 0.2 | 2026-04-23 | §3.0 renamed to Abarth 595 Turismo; §3.1 updated to Turismo specs (165 hp, 230 N·m @ 3,000 RPM, 6,000 RPM redline); §3.2 band thresholds revised; YAML defaults in §2.2 updated to match |
| 0.3 | 2026-04-23 | Resolved all open questions: acknowledgement on first run and post-config-change only (§2.4); engine profile list added with update mechanism (§2.5); pulse cadence confirmed 2 Hz (§2.3); idle band RPM-based only with rationale (§2.6); §8.0 Open Questions removed |
| 0.4 | 2026-04-23 | Removed author attribution from version history |
| 0.5 | 2026-04-23 | Added `redline_rpm` as distinct field from `danger_start`; pulse now begins at `danger_start`; acknowledgement state moved to separate state file; profile YAML load/reload behaviour clarified; §3.2 and §5.x updated accordingly |
| 0.6 | 2026-11-11 | Closed as obsolete; added closure status and divergences from current implementation |

---

Copyright (c) 2026 William Watson. MIT License.
