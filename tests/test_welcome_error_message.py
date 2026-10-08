# Copyright (c) 2026 William Watson
#
# This file is part of GTach.
# GTach is licensed under the MIT License.
# See the LICENSE file in the project root for full license text.

"""WELCOME error message placement and contrast (issue-b0a9cb20).

'Device not available' was drawn in orange on the beige setup
background, a 1.18:1 contrast that made it unreadable on the Pi. It is
now dark red (6.0:1) and centred at y=235, clear of the buttons. These
tests pin both.
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


def _luminance(rgb):
    channels = []
    for v in rgb:
        v = v / 255
        channels.append(v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4)
    r, g, b = channels
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast(a, b):
    la, lb = _luminance(a), _luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


class TestContrast:

    def _colors(self):
        """The palette literal from SetupDisplayManager.__init__."""
        import ast

        source = inspect.getsource(SetupDisplayManager.__init__)
        start = source.index("{", source.index("self.colors = {"))
        end = source.index("}", start) + 1
        return ast.literal_eval(source[start:end])

    def test_error_text_readable_on_background(self):
        colors = self._colors()
        assert _contrast(colors["error_text"], colors["background"]) >= 4.5

    def test_renderer_uses_error_text_colour(self):
        source = inspect.getsource(SetupDisplayManager._render_welcome_screen)
        assert 'self.colors["error_text"]' in source
