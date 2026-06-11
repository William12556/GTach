# Fiat_Holder_MK2 — Reverse Engineering Reference

Created: 2026 June 11

---

## Table of Contents

1. [Overview](<#1-overview>)
2. [Source Mesh Metadata](<#2-source-mesh-metadata>)
3. [Coordinate Reference](<#3-coordinate-reference>)
4. [Feature Inventory](<#4-feature-inventory>)
   - 4.1 [Base Plate](<#41-base-plate>)
   - 4.2 [Post](<#42-post>)
   - 4.3 [Cantilever Snap Arms](<#43-cantilever-snap-arms>)
   - 4.4 [Top Bore](<#44-top-bore>)
5. [Surface Area Distribution](<#5-surface-area-distribution>)
6. [Inferred Function](<#6-inferred-function>)
7. [Measurement Confidence Notes](<#7-measurement-confidence-notes>)
8. [Version History](<#8-version-history>)

---

## 1 Overview

Object name: `Fiat_Holder_MK2`
Source file: `Fiat_Holder_MK2.stl` (imported as `Mesh::Feature` in FreeCAD)
Analysis date: 2026-06-11
Analysis method: Geometric probing via FreeCAD Python API (`mesh.BoundBox`, `mesh.crossSections`, `mesh.Topology`, least-squares circle fits). No parametric solid available.

The object is a single solid body: an oval flange plate carrying a central obround post with two cantilever snap arms and a top bore.

[Return to Table of Contents](<#table-of-contents>)

---

## 2 Source Mesh Metadata

| Property | Value |
|---|---|
| Mesh type | `Mesh::Feature` |
| Points | 813 |
| Faces | 1648 |
| Edges | 2507 |
| Volume | 23 681.9 mm³ |
| Surface area | 13 254.8 mm² |
| Tessellation density | Coarse. Limits precision of radius and bore fits. |

[Return to Table of Contents](<#table-of-contents>)

---

## 3 Coordinate Reference

The mesh is **not origin-centred**. All raw coordinates carry a positive X offset.

| Axis | Raw min | Raw max | Span | Body centre (raw) |
|---|---|---|---|---|
| X | 47.56 mm | 111.73 mm | 64.17 mm | 79.64 mm |
| Y | −25.73 mm | 24.90 mm | 50.64 mm | −0.41 mm |
| Z | 0.00 mm | 41.00 mm | 41.00 mm | 20.50 mm |

**Origin offset** (raw → normalised): subtract X₀ = 79.64, Y₀ = −0.41. Z sits naturally on the XY plane (Z_min = 0).

Normalised coordinates are used in feature descriptions below unless stated otherwise.

[Return to Table of Contents](<#table-of-contents>)

---

## 4 Feature Inventory

### 4.1 Base Plate

Flat oval (stadium / racetrack) slab. Parallel top and bottom faces.

| Dimension | Value | Confidence |
|---|---|---|
| Length (X) | 64.17 mm | High |
| Width (Y) | 50.64 mm | High |
| Thickness (Z) | 8.00 mm | High — plate top confirmed at Z = 8.00 across full footprint |
| Plan form | Oval / stadium | High — racetrack profile confirmed by cross-section |

The plate footprint is constant from Z = 0 to Z = 8. At Z > 8 the cross-section steps inward to the post profile.

[Return to Table of Contents](<#table-of-contents>)

---

### 4.2 Post

Obround (racetrack) prismatic column rising from the plate top surface.

| Dimension | Value | Confidence |
|---|---|---|
| Length (X) | 31.91 mm | High |
| Width (Y, nominal) | 18.50 mm | High — confirmed constant Z 12–20 |
| Height above plate | 33.00 mm (Z 8 to 41) | High |
| Total height (inc. plate) | 41.00 mm | High |
| Post X centre (normalised) | 0.00 — coincides with plate centre | High |
| Post Y centre (normalised) | 0.00 | High |
| Top face | Flat at Z = 41.00 mm with rounded perimeter edge | High |

[Return to Table of Contents](<#table-of-contents>)

---

### 4.3 Cantilever Snap Arms

Two symmetric arms, one on each ±Y face of the post. Each arm is a wedge-shaped projection (double-ramp barb) freed from the post body by a pair of relief slots. The Z profile is symmetric — a "pitched roof" — making this a **releasable (separable) cantilever snap-fit**.

| Dimension | Value | Confidence |
|---|---|---|
| Arm span (X, normalised) | ≈ 11.4 mm (−5.6 to +5.8 from post X-centre) | Medium |
| Barb projection beyond post wall | ≈ 1.0–1.1 mm per side | Medium |
| Post nominal Y half-width | 9.25 mm | High |
| Ridge peak Ymax (normalised, +Y arm) | ≈ 10.37 mm | Medium |
| Ridge peak Z (above plate top) | ≈ 20 mm (raw Z ≈ 28) | Medium |
| Relief slot X positions (raw) | 74.0 mm and 85.4 mm | Medium |
| Relief slot span | ≈ 11.4 mm | Medium |

**Y-span profile by Z band, +Y arm (raw coordinates):**

| Z band | Ymax (raw) | Notes |
|---|---|---|
| Z 12–20 | 8.84 mm | Nominal post wall, no arm |
| Z 20–24 | 8.84–9.20 mm | Arm base, ramp rising |
| Z 26–30 | 9.96 mm | **Ridge — maximum projection** |
| Z 30–34 | 9.63 mm | Ramp falling |
| Z 36–38 | 8.84 mm | Returns to post wall |

The two barb faces are the **insertion ramp** (lower face, cams the arm inward on entry) and the **retention face** (upper face, resists withdrawal).

[Return to Table of Contents](<#table-of-contents>)

---

### 4.4 Top Bore

A circular bore in the top face of the post, offset toward the +X end of the post.

| Dimension | Value | Confidence |
|---|---|---|
| Bore centre X (normalised) | ≈ +9.7 mm from post X-centre | Low–Medium |
| Bore centre Y (normalised) | ≈ 0.0 mm | Medium |
| Diameter | ≈ 5.9–6.6 mm (two independent fits) | Low |
| Depth | Unresolved — blind vs through ambiguous at this mesh density | — |

> **Note:** Circle fits on this bore produced residual standard deviations of 0.24–0.48 mm against a radius of ~6 mm. The mesh is too coarse for a reliable bore measurement. Diameter and depth should be verified against the physical part or the original CAD source.

[Return to Table of Contents](<#table-of-contents>)

---

## 5 Surface Area Distribution

Area by Z band, indicating where material is concentrated:

| Z band (mm) | Surface area (mm²) | Notes |
|---|---|---|
| 0–5 | 5 832 | Base plate — large flat faces and perimeter |
| 5–10 | 2 027 | Plate top and step transition to post |
| 10–15 | 1 688 | Post walls |
| 15–20 | 77 | Post walls (minimal — nearly pure prism) |
| 20–25 | 284 | Post walls and snap arm bases |
| 25–31 | 1 915 | **Snap arm zone** — peak area from barb surfaces |
| 31–36 | 757 | Post walls above arms |
| 36–41 | 674 | Post top cap and bore rim |

Surface orientation split: ~52% vertical walls, ~20% upward-facing (+Z), ~20% downward-facing (−Z).

[Return to Table of Contents](<#table-of-contents>)

---

## 6 Inferred Function

The geometry is consistent with a **flanged snap-fit insert**: the oval plate acts as a seating flange; the obround post inserts into a mating aperture; the cantilever snap arms retain the post axially once seated; the top bore accepts a fastener or spindle.

This is stated as geometric inference only. No claim of fitness for purpose is made.

[Return to Table of Contents](<#table-of-contents>)

---

## 7 Measurement Confidence Notes

- **High confidence:** bounding box, plate thickness, post X/Y span, overall height. Directly read from vertex extrema.
- **Medium confidence:** snap arm ridge position and projection. Only 2 points sampled at the ridge Z band due to mesh coarseness.
- **Low confidence:** top bore diameter and depth. Circle fits are sensitive to the small number of rim vertices.
- **Unresolved:** bore depth (blind vs through); exact fillet radii on post edges and plate perimeter; thread form in bore (if any).

[Return to Table of Contents](<#table-of-contents>)

---

## 8 Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-06-11 | Initial document. Consolidated from exploratory scratch files generated during FreeCAD mesh analysis session. |

---

Copyright (c) 2026 William Watson. MIT License.
