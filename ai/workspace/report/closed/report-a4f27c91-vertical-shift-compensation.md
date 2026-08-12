Created: 2026 August 07

# Report: Compensate 8 px Vertical Shift in Framebuffer Write — Implementation of prompt-a4f27c91

---

## Table of Contents

- [1. Summary](<#1. summary>)
- [2. What Was Changed](<#2. what was changed>)
- [3. Tests](<#3. tests>)
- [4. Success Criteria](<#4. success criteria>)
- [5. Findings and Observations](<#5. findings and observations>)
- [6. What Was Deliberately Not Done](<#6. what was deliberately not done>)
- [7. What Only the Target Can Answer](<#7. what only the target can answer>)
- [8. T-Doc Disposition](<#8. t-doc disposition>)
- [9. Version History](<#9. version history>)

---

## 1. Summary

`prompt-a4f27c91-vertical-shift-compensation.md` was implemented in full. Two
files:

- `src/gtach/display/rendering/engine.py` — +49 / −0
- `tests/display/rendering/test_engine.py` — new, 8 test cases

Three things changed in the implementation:

**(a) A named constant.** `DisplayRenderingEngine.VERTICAL_OFFSET_PX = 8`,
class-level, with a comment citing `issue-a4f27c91` and stating explicitly that
this is a measured physical offset for this deployment target's panel and
overlay, not a general constant for the HyperPixel 2.1 Round model.

**(b) A row-shift step in `write_to_framebuffer`.** Placed after the existing
size-reconciliation block and above the branch dispatch, so both write branches
consume the same `payload` variable. It computes `row_bytes` from
`self.fb_line_length` when positive and `self.surface_size[0] * 4` otherwise,
then `shift_bytes = row_bytes * VERTICAL_OFFSET_PX`, and when
`0 < shift_bytes < payload_size` replaces the payload with
`bytes(shift_bytes) + payload[:-shift_bytes]`. Length is preserved exactly.

**(c) A no-op fallback and one-time logging.** Any exception in the new block is
caught locally at INFO and the original unshifted payload is written; an
out-of-range or zero `shift_bytes` skips the block entirely. Two one-time flags,
`_vertical_shift_logged` and `_vertical_shift_failed_logged`, were added to
`__init__` alongside the existing `_size_mismatch_logged` / `_view_fallback_logged`
pattern.

The signature, return contract, `with self._lock:` scope, and the method's outer
`OSError` / `Exception` handlers are unchanged.

[Return to Table of Contents](<#table of contents>)

---

## 2. What Was Changed

### 2.1 `src/gtach/display/rendering/engine.py`

The constant is class-level (line 73) rather than module-level. The prompt
allowed either, and class-level is what `VERTICAL_OFFSET_PX`'s access pattern
wants: it is read as `self.VERTICAL_OFFSET_PX`, so a test — or a future
per-panel override — can shadow it on one instance without touching module
state, which is exactly what the prompt's boundary scenario requires.

The shift block, inside the existing lock and the existing `try`:

```python
                try:
                    row_bytes = (self.fb_line_length if self.fb_line_length > 0
                                 else self.surface_size[0] * 4)
                    shift_bytes = row_bytes * self.VERTICAL_OFFSET_PX
                    payload_size = getattr(payload, 'length', None)
                    if payload_size is None:
                        payload_size = len(payload)

                    if 0 < shift_bytes < payload_size:
                        if not isinstance(payload, (bytes, bytearray)):
                            payload = bytes(payload)
                        payload = bytes(shift_bytes) + payload[:-shift_bytes]
                        ...
```

`payload_size` uses the same `getattr(payload, 'length', None)` idiom the method
already uses at the size-reconciliation step, because on the fast path `payload`
is a `pygame.BufferProxy`, which has no `__len__` — calling `len()` on it raises
`TypeError`. Had the new block used bare `len()`, every frame would have taken
the new local `except`, logged once, and silently written unshifted: the change
would have appeared to work and done nothing. The `isinstance` materialisation
guard is there for the same reason — `BufferProxy` does not slice.

The docstring records the compensation, the length-preservation property, the
fact that it applies to both branches, and the `issue-a4f27c91` reference.

### 2.2 `tests/display/rendering/test_engine.py`

The prompt instructed me to locate the existing test file for this class and not
create a parallel one. There is none: `tests/` contained only `conftest.py` and
`tests/utils/test_rwlock.py`, and nothing anywhere in `tests/` referenced
`DisplayRenderingEngine` or `write_to_framebuffer`. So this is the class's first
test file, created at the path mirroring the source tree, which is the layout
`tests/utils/test_rwlock.py` already establishes. No `__init__.py` was added,
matching `tests/utils/`.

The tests construct the engine directly and never call `initialize()`, so no
framebuffer device is opened and no display mode is set. `back_surface` is a
real 32×32 32-bit `pygame.Surface` under the dummy SDL driver that
`tests/conftest.py` already selects — so `get_view('0')` returns a genuine
`BufferProxy` and the tests exercise the production fast path rather than a
bytes-shaped stand-in. That is what makes them capable of catching the
`len()`-on-`BufferProxy` trap described above; a test that fed in plain `bytes`
would pass against a broken implementation.

[Return to Table of Contents](<#table of contents>)

---

## 3. Tests

`pytest tests/` — **19 passed, 0 failed** (baseline 11, +8 new). No environment
is installed on this machine, so the suite ran from a throwaway scratchpad venv
(`pytest`, `pyserial`, `pygame`, `pyyaml`, `psutil`) with `PYTHONPATH=src` and
`addopts` cleared, since the `pyproject.toml` default adds `--cov` flags that
need `pytest-cov`. Nothing was installed into the project tree.

The eight cases — the prompt's five scenarios, its two edge cases, and the
logging assertion the standards section asks for:

| # | Test | Asserts |
|---|---|---|
| 1 | `test_payload_is_shifted_down_by_the_offset` | Written bytes begin with `row_bytes * 8` zeros, then the original payload's first `fb_size − shift` bytes. The fixture's first row is asserted non-zero first, so the test cannot pass vacuously. |
| 2 | `test_total_written_length_is_unchanged` | Exactly one write, of exactly `fb_size` bytes. |
| 3 | `test_page_flip_branch_writes_the_same_shifted_payload` | `seek(target * fb_size)`, `buffer_index` advances, and the bytes written are **byte-identical** to the single-buffer case. |
| 4 | `test_row_bytes_falls_back_to_surface_width_when_stride_unknown` | `fb_line_length = 0` → shift computed from `surface_size[0] * 4`; correct content, no exception. |
| 5 | `test_oversized_offset_writes_the_unshifted_payload` | Offset beyond the payload → original payload, full length, returns `True`. |
| 6 | `test_offset_exactly_equal_to_the_payload_is_a_no_op` | The degenerate whole-frame case the `>=` guard exists for. |
| 7 | `test_shift_is_agnostic_to_the_framebuffer_object` | Runs against a real `open(..., 'r+b')` file, not a mock, covering the `use_mmap = False` fallback object. |
| 8 | `test_compensation_is_announced_once_per_session` | Two frames produce exactly one INFO announcement, at INFO not ERROR. |

**The local exception fallback was verified separately**, ephemerally rather than
as a committed test, since the prompt's testing section does not enumerate it:
with `surface_size` set to `None` and `fb_line_length` at 0, the row-bytes
computation raises `TypeError`. Result: one INFO line ("Vertical offset
compensation unavailable, writing the frame unshifted: 'NoneType' object is not
subscriptable"), the full-length **unshifted** payload written, `True` returned,
the flag set so a second frame logs nothing, and the second frame written
correctly. The error-handling contract — the shift can never turn a successful
write into a failed one — holds.

`python -m py_compile src/gtach/display/rendering/engine.py` passes.

[Return to Table of Contents](<#table of contents>)

---

## 4. Success Criteria

| Criterion | Status |
|---|---|
| `py_compile` passes | Met |
| `VERTICAL_OFFSET_PX` defined exactly once, comment cites `issue-a4f27c91` | Met — one definition at line 73 |
| Both branches write the same variable, assigned once above the dispatch | Met — both call sites are `self.fb.write(payload)`; `payload` is assigned by the single shift block above the branch, and test 3 asserts byte-identity across branches |
| No `dpi_timings` / `/boot/config.txt` in the diff | Met — zero matches in the diff |
| No file under `src/gtach/` other than `engine.py` in the diff | Met |
| `pytest tests/` passes, count up by the number of new cases, zero failures | Met — 11 → 19, +8 |
| `write_to_framebuffer(self) -> bool` unchanged, exactly one definition | Met |

[Return to Table of Contents](<#table of contents>)

---

## 5. Findings and Observations

**5.1 The compensation zeroes the bottom 8 rows and discards the top 8.** This
is inherent to a fixed-length shift and is what the prompt specifies, but it is
worth stating plainly: the topmost 8 px of every composed frame is now never
displayed, and the bottom 8 px of the panel shows black. On a round panel those
rows are the extreme top and bottom chords, outside `display_safe_radius` (200)
and outside `display_max_radius` (220) — 240 − 220 = 20 px of margin, so nothing
the draw code deliberately places should be lost. If the on-target check finds
clipping, the alternative is a hardware-side fix in display timings, which
`change-a4f27c91` puts explicitly out of scope.

**5.2 A `BufferProxy` trap sits in this method, and the block is now the second
place to step around it.** `payload` reaches the new code as a `BufferProxy` on
the fast path — no `__len__`, no slicing. The existing code already carries a
comment about this at the `actual_size` computation. The new block needs both
mitigations, and would fail silently-but-successfully without them (§2.1). Any
future edit inserted into this method between `get_view('0')` and the write needs
the same care; the third occurrence probably justifies a small helper.

**5.3 Per-frame cost is one materialisation plus one concatenation of `fb_size`
bytes — now on every frame, not just on mismatch.** The prompt argues this is
the same order of cost as the existing size-mismatch fallback and therefore
acceptable. The distinction worth recording is that the mismatch path is an
exception path, while this runs on all ~921,600 bytes of every frame. At 480×480
32-bit that is roughly 1.8 MB of allocation and copying per frame. Whether that
matters is a measurement question for the target, and it interacts with the frame
pacing work in `change-9ed1c77e`. If it proves material, the shift can be done
without a copy by writing the zero rows and the payload slice as two writes into
the mmap, or by composing into an offset region of the surface instead — both are
larger changes than this prompt authorises.

**5.4 This is the first test coverage `DisplayRenderingEngine` has had.** The
fixture and `FakeFramebuffer` in the new file are reusable for the rest of the
class (`_pan_display`, `_setup_page_flip`, the size-mismatch path), none of which
is covered today.

**5.5 The report path diverges from convention.** Every prior report lives in
`ai/workspace/report/` with a `v0.4.0-<uuid>-<name>.md` name. This one was
written to `ai/workspace/report-a4f27c91-vertical-shift-compensation.md` because
that is the path the task specified literally. Moving it to
`ai/workspace/report/v0.4.0-a4f27c91-vertical-shift-compensation.md` would
restore the convention; say the word.

**5.6 The working tree also carries the uncommitted `prompt-e7a92c4f` change** to
the same file (`_pan_display`, `FB_ACTIVATE_NOW`). `git diff --stat` therefore
reports 66 insertions for `engine.py`, of which 17 belong to that earlier prompt
and 49 to this one. Both are confined to `engine.py`, so no success criterion is
affected, but the two changes will need separating if they are to be committed
independently.

[Return to Table of Contents](<#table of contents>)

---

## 6. What Was Deliberately Not Done

- **No `DisplayManager`, draw call site, touch mapping, `TouchEventCoordinator`,
  or `config.yaml` change** — per constraint. The compensation sits at the single
  hardware-output boundary, so RADIAL, OPTIONS, ACKNOWLEDGEMENT, splash,
  disconnected, and setup are all corrected without any caller knowing.
- **No `/boot/config.txt` or `dpi_timings` change** — explicitly out of scope per
  `change-a4f27c91`; verified absent from the diff.
- **No touch-coordinate compensation.** If the panel's active area is displaced
  relative to the framebuffer, the touch digitiser's mapping may be displaced by
  the same 8 px. This change moves the image, not the touch map, so the two are
  now offset from each other by 8 px where before they agreed. Whether that is
  perceptible is an on-target question; it is out of scope here and worth an
  issue of its own if the physical check shows it.
- **No committed test for the local exception fallback** — not enumerated in the
  prompt's testing section; verified ephemerally instead (§3).
- **No second lock, and nothing moved outside the existing `with self._lock:`** —
  per constraint.

[Return to Table of Contents](<#table of contents>)

---

## 7. What Only the Target Can Answer

The 8 px value comes from `issue-a4f27c91`'s on-target crosshair diagnostic. What
source and pytest can confirm — that exactly 8 rows of padding are prepended,
that length is preserved, that both branches agree, and that failure degrades to
the old behaviour — is confirmed. What they cannot confirm is that 8 is the right
number, or that the composed frame now aligns with the panel's active area. There
is no framebuffer device on macOS, so `write_to_framebuffer`'s hardware path only
ever runs against a fake here.

Physical verification per `issue-a4f27c91` `verification_enhanced`, on
gtach.local, after deployment. Two things to watch beyond simple alignment: that
the bottom 8 rows of black are not visible as a band on the round bezel, and that
no draw content is clipped from the top (§5.1).

[Return to Table of Contents](<#table of contents>)

---

## 8. T-Doc Disposition

| T-Doc | Disposition |
|---|---|
| `prompt-a4f27c91-vertical-shift-compensation.md` | **Closed** — moved to `ai/workspace/prompt/closed/` |
| `issue-a4f27c91` | **Active** — pending physical verification on gtach.local |
| `change-a4f27c91` | **Active** — pending the same |

[Return to Table of Contents](<#table of contents>)

---

## 9. Version History

| Version | Date | Description |
|---|---|---|
| 1.0 | 2026-08-07 | Implementation report for prompt-a4f27c91. |

---

Copyright (c) 2026 William Watson. MIT License.
