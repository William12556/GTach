#!/usr/bin/env python3
# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
#
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""Tests for DisplayRenderingEngine.write_to_framebuffer.

Covers the vertical offset compensation added by change-a4f27c91: the
payload written to the framebuffer is shifted down VERTICAL_OFFSET_PX
rows, at constant total length, in both the page-flip and single-buffer
branches, with a no-op fallback when the shift cannot be applied.

The engine is constructed directly rather than via initialize(), so no
framebuffer device is opened and no display mode is set. SDL runs under
the dummy video driver set in tests/conftest.py, so the pygame surfaces
here are real memory with no window behind them — get_view('0') returns
a genuine BufferProxy, which is the path the production fast path takes.
"""

import logging

import pygame
import pytest

from gtach.display.rendering.engine import DisplayRenderingEngine


SURFACE_W = 32
SURFACE_H = 32
BYTES_PER_PIXEL = 4
ROW_BYTES = SURFACE_W * BYTES_PER_PIXEL
FB_SIZE = ROW_BYTES * SURFACE_H


class FakeFramebuffer:
    """Records seek/write calls the way mmap and a file object both would."""

    def __init__(self):
        self.seeks = []
        self.writes = []

    def seek(self, offset):
        self.seeks.append(offset)

    def write(self, data):
        # Materialise at capture time: the production fast path may hand
        # a buffer view straight through, and the test needs the bytes.
        self.writes.append(bytes(data))
        return len(self.writes[-1])


@pytest.fixture
def engine():
    """An engine wired to a fake framebuffer, single-buffer mode."""
    pygame.init()
    eng = DisplayRenderingEngine()
    eng.surface_size = (SURFACE_W, SURFACE_H)
    eng.back_surface = pygame.Surface((SURFACE_W, SURFACE_H), depth=32)
    # Every byte non-zero, so prepended padding is unambiguous.
    eng.back_surface.fill((0x11, 0x22, 0x33))
    eng.fb = FakeFramebuffer()
    eng.fb_size = FB_SIZE
    eng.fb_line_length = ROW_BYTES
    eng.fb_bits_per_pixel = 32
    eng.page_flip = False
    eng.vsync_available = False
    yield eng
    pygame.quit()


def original_payload(eng):
    """The bytes write_to_framebuffer would have written before the change."""
    return bytes(eng.back_surface.get_view('0'))


def test_payload_is_shifted_down_by_the_offset(engine):
    """Scenario 1: padding rows are prepended and the tail is dropped."""
    expected_before = original_payload(engine)
    shift = ROW_BYTES * DisplayRenderingEngine.VERTICAL_OFFSET_PX
    assert expected_before[:ROW_BYTES] != bytes(ROW_BYTES), \
        "fixture must present a non-zero first row for this test to discriminate"

    assert engine.write_to_framebuffer() is True

    written = engine.fb.writes[0]
    assert written[:shift] == bytes(shift)
    assert written[shift:] == expected_before[:FB_SIZE - shift]


def test_total_written_length_is_unchanged(engine):
    """Scenario 2: only content moves, never the byte count."""
    assert engine.write_to_framebuffer() is True

    assert len(engine.fb.writes) == 1
    assert len(engine.fb.writes[0]) == engine.fb_size


def test_page_flip_branch_writes_the_same_shifted_payload(engine, monkeypatch):
    """Scenario 3: the page-flip branch seeks to its half and shifts too."""
    single_buffer_bytes = None
    assert engine.write_to_framebuffer() is True
    single_buffer_bytes = engine.fb.writes[0]

    flip = DisplayRenderingEngine()
    flip.surface_size = (SURFACE_W, SURFACE_H)
    flip.back_surface = engine.back_surface
    flip.fb = FakeFramebuffer()
    flip.fb_size = FB_SIZE
    flip.fb_line_length = ROW_BYTES
    flip.page_flip = True
    flip.buffer_index = 0
    monkeypatch.setattr(flip, '_pan_display', lambda index: True)

    assert flip.write_to_framebuffer() is True

    target = 1  # buffer_index 0 ^ 1
    assert flip.fb.seeks == [target * FB_SIZE]
    assert flip.fb.writes[0] == single_buffer_bytes
    assert flip.buffer_index == target


def test_row_bytes_falls_back_to_surface_width_when_stride_unknown(engine):
    """Scenario 4: fb_line_length of 0 uses surface_size[0] * 4."""
    expected_before = original_payload(engine)
    engine.fb_line_length = 0
    shift = SURFACE_W * BYTES_PER_PIXEL * DisplayRenderingEngine.VERTICAL_OFFSET_PX

    assert engine.write_to_framebuffer() is True

    written = engine.fb.writes[0]
    assert written[:shift] == bytes(shift)
    assert written[shift:] == expected_before[:FB_SIZE - shift]
    assert len(written) == engine.fb_size


def test_oversized_offset_writes_the_unshifted_payload(engine, monkeypatch):
    """Scenario 5: an offset at or beyond the payload is a no-op, not a fault."""
    expected_before = original_payload(engine)
    monkeypatch.setattr(engine, 'VERTICAL_OFFSET_PX', SURFACE_H + 1)

    assert engine.write_to_framebuffer() is True

    assert engine.fb.writes[0] == expected_before
    assert len(engine.fb.writes[0]) == engine.fb_size


def test_offset_exactly_equal_to_the_payload_is_a_no_op(engine, monkeypatch):
    """Edge case: a whole-frame shift would zero the frame; guard rejects it."""
    expected_before = original_payload(engine)
    monkeypatch.setattr(engine, 'VERTICAL_OFFSET_PX', SURFACE_H)

    assert engine.write_to_framebuffer() is True

    assert engine.fb.writes[0] == expected_before


def test_shift_is_agnostic_to_the_framebuffer_object(engine, tmp_path):
    """Edge case: works against the direct-file fallback, not just mmap."""
    expected_before = original_payload(engine)
    shift = ROW_BYTES * DisplayRenderingEngine.VERTICAL_OFFSET_PX
    path = tmp_path / "fb0"
    path.write_bytes(bytes(FB_SIZE))
    engine.use_mmap = False
    with open(path, 'r+b') as fh:
        engine.fb = fh
        assert engine.write_to_framebuffer() is True

    written = path.read_bytes()
    assert len(written) == FB_SIZE
    assert written[:shift] == bytes(shift)
    assert written[shift:] == expected_before[:FB_SIZE - shift]


def test_compensation_is_announced_once_per_session(engine, caplog):
    """The one-time INFO log fires on the first shifted frame only."""
    with caplog.at_level(logging.INFO, logger='DisplayRenderingEngine'):
        engine.write_to_framebuffer()
        engine.write_to_framebuffer()

    announcements = [r for r in caplog.records
                     if 'Vertical offset compensation active' in r.getMessage()]
    assert len(announcements) == 1
    assert announcements[0].levelno == logging.INFO
