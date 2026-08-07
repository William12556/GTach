#!/usr/bin/env python3
# gen_splash.py — generates bin/boot-splash.png (reference/preview) and
# bin/boot-splash.raw (the actual boot-time asset, written verbatim to
# /dev/fb0 by gtach-boot-splash.service).
#
# Usage:
#   python3 bin/gen_splash.py
#
# Requires Pillow: pip3 install pillow
#
# Copyright (c) 2026 William Watson. MIT License.

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

SIZE = 480
CENTER = SIZE // 2

# Colors sourced from src/gtach/display/graphics/splash_graphics.py
# (AUTOMOTIVE_COLORS / SPLASH_COLORS) so this static splash matches the
# app's own splash screen that follows it.
BACKGROUND = (15, 20, 25)     # dark_background
TITLE = (255, 255, 255)       # text_primary
SUBTITLE = (150, 160, 170)    # text_tertiary

FONT_PATH = (
    "/Applications/FreeCAD.app/Contents/Resources/lib/python3.11/"
    "site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans-Bold.ttf"
)

OUTPUT_DIR = Path(__file__).resolve().parent
PNG_PATH = OUTPUT_DIR / "boot-splash.png"
RAW_PATH = OUTPUT_DIR / "boot-splash.raw"

# Confirmed via `fbset -fb /dev/fb0` on gtach.local:
#   geometry 480 480 480 480 32
#   rgba 8/16,8/8,8/0,8/24
# i.e. 32bpp, no stride padding, byte order per pixel B,G,R,A (r at bit
# offset 16, g at 8, b at 0, a at 24 — little-endian memory order is the
# reverse of that: B first, A last).


def main() -> None:
    img = Image.new("RGB", (SIZE, SIZE), BACKGROUND)
    draw = ImageDraw.Draw(img)

    title_font = ImageFont.truetype(FONT_PATH, 56)
    subtitle_font = ImageFont.truetype(FONT_PATH, 20)

    def centered_text(y, text, font, fill):
        tb = draw.textbbox((0, 0), text, font=font)
        w, h = tb[2] - tb[0], tb[3] - tb[1]
        draw.text((CENTER - w / 2, y - tb[1]), text, font=font, fill=fill)

    centered_text(CENTER - 30, "GTach", title_font, TITLE)
    centered_text(CENTER + 40, "OBD-II TACHOMETER", subtitle_font, SUBTITLE)

    img.save(PNG_PATH)
    print(f"saved: {PNG_PATH} {img.size}")

    # Raw BGRA8888 blob for direct /dev/fb0 writing.
    r, g, b = img.split()
    a = Image.new("L", img.size, 255)
    raw_img = Image.merge("RGBA", (b, g, r, a))
    raw_bytes = raw_img.tobytes()

    expected_size = SIZE * SIZE * 4
    assert len(raw_bytes) == expected_size, (
        f"raw size {len(raw_bytes)} != expected {expected_size}"
    )

    RAW_PATH.write_bytes(raw_bytes)
    print(f"saved: {RAW_PATH} ({len(raw_bytes)} bytes)")


if __name__ == "__main__":
    main()
