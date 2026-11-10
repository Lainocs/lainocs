"""One-off: turn assets/portrait.png into assets/portrait-pixels.json.

Run by hand when the portrait changes:  python tools/make_pixels.py
Each cell holds a hex colour (or null for transparent), snapped to a small palette
so the SVG can merge neighbouring pixels into long rectangles.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
COLS = 68
COLOURS = 30


def main() -> None:
    img = Image.open(ROOT / "assets" / "portrait.png").convert("RGBA")
    w, h = img.size
    rows = round(COLS * h / w)
    small = img.resize((COLS, rows), Image.BOX)
    alpha = np.asarray(small.split()[3])
    rgb = Image.new("RGB", small.size, (255, 255, 255))
    rgb.paste(small, mask=small.split()[3])
    pal = rgb.quantize(colors=COLOURS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = pal.getpalette()
    idx = np.asarray(pal)
    grid = [
        [
            None if alpha[r, c] < 110 else "#%02x%02x%02x" % tuple(palette[idx[r, c] * 3 : idx[r, c] * 3 + 3])
            for c in range(COLS)
        ]
        for r in range(rows)
    ]
    (ROOT / "assets" / "portrait-pixels.json").write_text(json.dumps(grid), encoding="utf-8")
    print(f"{COLS}x{rows}, {len({c for row in grid for c in row if c})} colours")


if __name__ == "__main__":
    main()
