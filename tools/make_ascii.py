"""One-off: turn assets/portrait.png into assets/portrait-ascii.json.

Run by hand when the portrait changes:  python tools/make_ascii.py

Every cell of the output is a character plus a colour: the character carries the
shading and the outlines, the colour is the average colour of the drawing there.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
COLS = 72
CHAR_ASPECT = 0.47  # cell width / cell height of the card art grid
RAMP = " .:-=+*#%@"  # light -> dense
COLOURS = 18


def main() -> None:
    img = Image.open(ROOT / "assets" / "portrait.png").convert("RGBA")
    w, h = img.size
    img = img.crop((0, 0, w, int(h * 0.88)))  # the head and a bit of shoulders
    w, h = img.size
    rows = round(COLS * h / w * CHAR_ASPECT)

    alpha = np.asarray(img.split()[3], dtype=float) / 255.0
    flat = Image.new("RGBA", img.size, (255, 255, 255, 255))
    flat = Image.alpha_composite(flat, img).convert("RGB")
    rgb = np.asarray(flat, dtype=float)
    lum = np.asarray(flat.convert("L"), dtype=float) / 255.0

    ys = np.linspace(0, h, rows + 1).astype(int)
    xs = np.linspace(0, w, COLS + 1).astype(int)
    ink = np.zeros((rows, COLS))
    mean_rgb = np.zeros((rows, COLS, 3))
    empty = np.zeros((rows, COLS), dtype=bool)
    for r in range(rows):
        for c in range(COLS):
            sl = (slice(ys[r], ys[r + 1]), slice(xs[c], xs[c + 1]))
            empty[r, c] = alpha[sl].mean() < 0.5
            block = lum[sl]
            # mixing the mean with the darkest pixels keeps thin outlines alive
            ink[r, c] = 1.0 - (0.55 * block.mean() + 0.45 * np.percentile(block, 8))
            mean_rgb[r, c] = rgb[sl].reshape(-1, 3).mean(axis=0)

    inside = ink[~empty]
    lo, hi = np.percentile(inside, 3), np.percentile(inside, 97)
    ink = np.clip((ink - lo) / (hi - lo), 0, 1)

    # inside the figure the lightest character is already a visible '-'
    lines = []
    for r in range(rows):
        lines.append(
            "".join(" " if empty[r, c] else RAMP[3 + round(ink[r, c] * (len(RAMP) - 4))] for c in range(COLS))
        )

    strip = Image.fromarray(mean_rgb.astype("uint8"))
    pal = strip.quantize(colors=COLOURS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    palette = pal.getpalette()
    idx = np.asarray(pal)
    colours = [
        ["#%02x%02x%02x" % tuple(palette[i * 3 : i * 3 + 3]) for i in row] for row in idx
    ]
    (ROOT / "assets" / "portrait-ascii.json").write_text(
        json.dumps({"rows": lines, "colors": colours}), encoding="utf-8"
    )
    print(f"{COLS}x{rows}")


if __name__ == "__main__":
    main()
