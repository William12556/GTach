Created: 2026 May 27

# Gesture Reference

---

## Table of Contents

- [1.0 Document Information](<#1.0 document information>)
- [2.0 Purpose](<#2.0 purpose>)
- [3.0 Gesture Inventory](<#3.0 gesture inventory>)
- [4.0 Gesture-to-Action Mapping](<#4.0 gesture-to-action mapping>)
- [5.0 Implementation Status](<#5.0 implementation status>)
- [6.0 Detection Parameters](<#6.0 detection parameters>)
- [Version History](<#version history>)

---

## 1.0 Document Information

```yaml
document_info:
  document_id: "design-g1h2i3j4-gesture_reference"
  tier: 3
  domain: "Display"
  component: "TouchHandler / NavigationGestureHandler"
  parent: "design-2c6b8e4d-domain_display.md"
  source_files:
    - "src/gtach/display/touch.py"
    - "src/gtach/display/navigation_gestures.py"
  version: "1.1"
  date: "2026-05-27"
```

### 1.1 Related Documents

- [design-2c6b8e4d-domain_display.md](<design-2c6b8e4d-domain_display.md>) — Display domain
- [design-b8c9d0e1-component_display_manager.md](<design-b8c9d0e1-component_display_manager.md>) — DisplayManager (mode transitions)
- [design-d0e1f2a3-component_display_touch_coordinator.md](<design-d0e1f2a3-component_display_touch_coordinator.md>) — TouchEventCoordinator
- [design-a3b4c5d6-component_display_setup_manager.md](<design-a3b4c5d6-component_display_setup_manager.md>) — Setup wizard touch interactions

### 1.2 Status Key

| Symbol | Meaning |
|--------|---------|
| ✅ | Implemented — active in `touch.py` |
| 🔶 | Designed — specified; not yet implemented |
| ❌ | Not designed — no specification exists |

### 1.3 Naming Note

The display mode previously labelled `SETTINGS` is renamed `OPTIONS` in this design. The source code currently uses `DisplayMode.SETTINGS`; that identifier will be updated in a future source change.

[Return to Table of Contents](<#table of contents>)

---

## 2.0 Purpose

This document provides a single reference for all touch gestures in GTach: what gestures exist, which display modes they apply to, what action each gesture triggers, and whether that gesture is currently implemented.

The active touch handler is `touch.py` (`TouchHandler`). The `NavigationGestureHandler` in `navigation_gestures.py` is instantiated but bypassed at runtime; its gesture definitions are recorded here as designed-but-unimplemented.

Edge swipe (swipe originating at the screen edge) is not distinguished from a standard swipe. Both are treated as a single swipe gesture.

[Return to Table of Contents](<#table of contents>)

---

## 3.0 Gesture Inventory

### 3.1 Recognised Gesture Types

| Gesture | Direction / Duration | Detection Criteria | Status |
|---------|---------------------|--------------------|--------|
| Swipe horizontal | Left or right | `abs(dx) ≥ 100px`, short duration | ✅ |
| Long press | Any position | Duration `≥ 1.0s` | ✅ |
| Swipe up | Upward | `abs(dy) ≥ 80px`, velocity `≥ 200px/s` | 🔶 |
| Swipe down | Downward | `abs(dy) ≥ 80px`, velocity `≥ 200px/s` | 🔶 |
| Tap | Any position | `distance < threshold`, short duration | 🔶 |

### 3.2 Detection Notes

- Swipe threshold in `touch.py`: `100px` (horizontal only).
- Swipe threshold in `navigation_gestures.py`: `80px` (all directions); velocity threshold `200px/s`.
- Long press threshold: configurable via `DisplayConfig.touch_long_press` (default `1.0s`).
- Left and right swipes produce the same action in the current implementation — no directional distinction.
- Edge swipe is not a separate gesture type. Origin position is not considered during swipe classification.

[Return to Table of Contents](<#table of contents>)

---

## 4.0 Gesture-to-Action Mapping

### 4.1 Diagram

```mermaid
flowchart TD
    GESTURE[Touch Gesture] --> TYPE{Gesture Type}

    TYPE -->|Swipe Left ✅| SL[Swipe Left]
    TYPE -->|Swipe Right ✅| SR[Swipe Right]
    TYPE -->|Long Press ✅| LP[Long Press]
    TYPE -->|Swipe Up 🔶| SU[Swipe Up]
    TYPE -->|Swipe Down 🔶| SD[Swipe Down]

    SL --> SL_MODE{Current Mode}
    SL_MODE -->|DIGITAL ✅| SL_D[→ RADIAL]
    SL_MODE -->|RADIAL ✅| SL_R[→ DIGITAL]

    SR --> SR_MODE{Current Mode}
    SR_MODE -->|DIGITAL ✅| SR_D[→ RADIAL]
    SR_MODE -->|RADIAL ✅| SR_R[→ DIGITAL]

    LP --> LP_MODE{Current Mode}
    LP_MODE -->|DIGITAL ✅| LP_D[→ OPTIONS]
    LP_MODE -->|RADIAL ✅| LP_R[→ OPTIONS]
    LP_MODE -->|OPTIONS ✅| LP_S[→ DIGITAL]

    SU --> SU_MODE{Current Mode}
    SU_MODE -->|SETUP / DEVICE_LIST 🔶| SU_SET[Scroll device list up]

    SD --> SD_MODE{Current Mode}
    SD_MODE -->|SETUP / DEVICE_LIST 🔶| SD_SET[Scroll device list down]
```

### 4.2 Tabular Reference

| Gesture | Mode | Action | Status |
|---------|------|--------|--------|
| Swipe left | DIGITAL | → RADIAL | ✅ |
| Swipe left | RADIAL | → DIGITAL | ✅ |
| Swipe right | DIGITAL | → RADIAL | ✅ |
| Swipe right | RADIAL | → DIGITAL | ✅ |
| Long press | DIGITAL | → OPTIONS | ✅ |
| Long press | RADIAL | → OPTIONS | ✅ |
| Long press | OPTIONS | → DIGITAL | ✅ |
| Swipe up | SETUP / DEVICE_LIST | Scroll device list up | 🔶 |
| Swipe down | SETUP / DEVICE_LIST | Scroll device list down | 🔶 |

### 4.3 OPTIONS Screen Actions

OPTIONS is reached via long press from DIGITAL or RADIAL. It presents a menu; actions are triggered by tap on the relevant item.

| Action | Behaviour | Status |
|--------|-----------|--------|
| Clear settings | Clears stored device; transitions to SETUP | 🔶 |
| Simulation mode | Enables session-only sim mode; transitions to DIGITAL | 🔶 |
| *(future options)* | Reserved | — |

Long press exits OPTIONS and returns to DIGITAL.

### 4.4 DISCONNECTED Screen Actions

When no OBD connection is available, the DISCONNECTED screen presents two on-screen affordances (not hidden gestures).

| On-screen Action | Behaviour | Status |
|-----------------|-----------|--------|
| Setup | Clears stored device; transitions to SETUP | 🔶 |
| Simulate | Enables session-only sim mode; transitions to DIGITAL | 🔶 |

### 4.5 Observations

- Swipe left and swipe right are functionally identical in the current implementation — both toggle DIGITAL ↔ RADIAL.
- OPTIONS screen actions (§4.3) and DISCONNECTED screen affordances (§4.4) are unimplemented; their visual layout is not yet specified.
- Sim mode is session-only — it does not persist across restarts.

[Return to Table of Contents](<#table of contents>)

---

## 5.0 Implementation Status

### 5.1 Active Touch Path

The live gesture handling resides in `src/gtach/display/touch.py` (`TouchHandler._process_touch`). It implements:

- Horizontal swipe detection via `abs(dx) ≥ 100px`
- Long press detection via `duration ≥ touch_long_press` (default `1.0s`)
- Direct mode switching — no intermediary gesture handler

`NavigationGestureHandler` is instantiated in `DisplayManager.__init__` but its `cancel_gesture()` method is the only call made from the active touch path; gesture routing through it does not occur.

### 5.2 Unimplemented Items Requiring Design Decisions

| Item | Gap |
|------|-----|
| OPTIONS screen rendering and tap routing | Screen content unspecified; no implementation |
| DISCONNECTED screen on-screen affordances | Visual layout unspecified; no implementation |
| Swipe up / down on SETUP / DEVICE_LIST | Specified; not wired in `touch.py` |
| Left vs right swipe distinction | Both map to same toggle; directional behaviour unspecified |
| `DisplayMode.SETTINGS` rename to `OPTIONS` | Design uses OPTIONS; source still uses `SETTINGS` |

[Return to Table of Contents](<#table of contents>)

---

## 6.0 Detection Parameters

| Parameter | Source | Value | Notes |
|-----------|--------|-------|-------|
| Horizontal swipe threshold | `touch.py` | `100px` | Hard-coded |
| Long press duration | `DisplayConfig.touch_long_press` | `1.0s` | Configurable |
| Swipe threshold (designed) | `GestureConfig.swipe_threshold` | `80px` | `navigation_gestures.py` |
| Velocity threshold (designed) | `GestureConfig.velocity_threshold` | `200px/s` | `navigation_gestures.py` |
| Max gesture time (designed) | `GestureConfig.max_gesture_time` | `1.0s` | `navigation_gestures.py` |

[Return to Table of Contents](<#table of contents>)

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2026-05-27 | Initial document. |
| 1.1 | 2026-05-27 | Removed edge swipe as distinct gesture type. Renamed SETTINGS → OPTIONS. Added OPTIONS screen actions (clear settings, sim mode). Added DISCONNECTED screen on-screen affordances. Sim mode defined as session-only. |

---

Copyright (c) 2026 William Watson. MIT License.
