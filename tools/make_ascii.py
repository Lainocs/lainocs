"""One-off: turn assets/portrait.png into assets/portrait-ascii.json.

Run by hand when the portrait changes:  python tools/make_ascii.py

Two monochrome versions, one per card theme: on the light card dense characters are
dark pixels (ink on paper); on the dark card they are bright pixels (light on dark).
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
COLS = 72
CHAR_ASPECT = 0.47  # cell width / cell height of the card's art grid
RAMP = " .:-=+*#%@"  # light -> dense


def main() -> None:
    img = Image.open(ROOT / "assets" / "portrait.png").convert("RGBA")
    w, h = img.size
    img = img.crop((0, 0, w, int(h * 0.74)))  # the head, no shirt
    w, h = img.size
    rows = round(COLS * h / w * CHAR_ASPECT)

    alpha = np.asarray(img.split()[3], dtype=float) / 255.0
    flat = Image.new("RGBA", img.size, (255, 255, 255, 255))
    lum = np.asarray(Image.alpha_composite(flat, img).convert("L"), dtype=float) / 255.0

    ys = np.linspace(0, h, rows + 1).astype(int)
    xs = np.linspace(0, w, COLS + 1).astype(int)
    dark = np.zeros((rows, COLS))
    bright = np.zeros((rows, COLS))
    empty = np.zeros((rows, COLS), dtype=bool)
    for r in range(rows):
        for c in range(COLS):
            sl = (slice(ys[r], ys[r + 1]), slice(xs[c], xs[c + 1]))
            empty[r, c] = alpha[sl].mean() < 0.5
            block = lum[sl]
            # mixing the mean with the darkest pixels keeps thin outlines alive
            dark[r, c] = 1.0 - (0.55 * block.mean() + 0.45 * np.percentile(block, 8))
            bright[r, c] = 0.7 * block.mean() + 0.3 * np.percentile(block, 92)

    def normalise(grid: np.ndarray, gamma: float) -> np.ndarray:
        inside = grid[~empty]
        lo, hi = np.percentile(inside, 3), np.percentile(inside, 97)
        out = np.clip((grid - lo) / (hi - lo), 0, 1) ** gamma
        out[empty] = 0.0
        return out

    def to_lines(ink: np.ndarray) -> list[str]:
        return [
            "".join(RAMP[min(int(v * (len(RAMP) - 1) + 0.5), len(RAMP) - 1)] if v > 0.04 else " " for v in row)
            for row in ink
        ]

    art = {
        "light": to_lines(normalise(dark, 1.5)),
        "dark": to_lines(normalise(bright, 1.2)),
    }
    (ROOT / "assets" / "portrait-ascii.json").write_text(json.dumps(art), encoding="utf-8")
    print(f"{COLS}x{rows}")


if __name__ == "__main__":
    main()
