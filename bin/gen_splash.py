#!/usr/bin/env python3
# gen_splash.py — generates bin/boot-splash.png, the static image `fbi`
# displays during the early-boot gap (before GTach's own pygame splash
# can start). Run once on the Mac; commit the resulting PNG, not this
# script's output path assumptions on other machines.
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

OUTPUT_PATH = Path(__file__).resolve().parent / "boot-splash.png"


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

    img.save(OUTPUT_PATH)
    print(f"saved: {OUTPUT_PATH} {img.size}")


if __name__ == "__main__":
    main()
