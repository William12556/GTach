# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""WELCOME error message placement (issue-b0a9cb20).

'Device not available' was drawn centred at y=440, under the Cancel
button and outside the round display's 200 px safe radius, and was not
visible on the Pi. These tests pin the new position geometrically.
"""

import inspect
import math

from gtach.display.setup import SetupDisplayManager

CENTRE = (240, 240)
SAFE_RADIUS = 200
TEXT_HEIGHT = 20
TEXT_HALF_WIDTH = 100  # generous for 'Device not available' at the small size

# (x, y, w, h) as drawn in _render_welcome_screen.
TWO_BUTTON = [(110, 270, 260, 75), (110, 360, 260, 75)]
ONE_BUTTON = [(110, 330, 260, 90)]


def _message_band():
    y = SetupDisplayManager._WELCOME_MESSAGE_Y
    half_h = TEXT_HEIGHT // 2
    return (240 - TEXT_HALF_WIDTH, y - half_h, 2 * TEXT_HALF_WIDTH, TEXT_HEIGHT)


def _intersects(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah


class TestPlacement:

    def test_band_inside_safe_radius(self):
        x, y, w, h = _message_band()
        for cx, cy in [(x, y), (x + w, y), (x, y + h), (x + w, y + h)]:
            assert math.hypot(cx - CENTRE[0], cy - CENTRE[1]) <= SAFE_RADIUS

    def test_clear_of_buttons_in_both_layouts(self):
        band = _message_band()
        for rect in TWO_BUTTON + ONE_BUTTON:
            assert not _intersects(band, rect), rect

    def test_below_the_description(self):
        _, y, _, _ = _message_band()
        assert y >= 208

    def test_renderer_uses_the_constant(self):
        source = inspect.getsource(SetupDisplayManager._render_welcome_screen)
        assert "self._WELCOME_MESSAGE_Y" in source
        assert "440" not in source
