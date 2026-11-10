"""One-off: turn assets/portrait.png into assets/ascii-art.txt.

Run by hand when the portrait changes:  python tools/make_ascii.py
Dense characters = ink. The SVG builder decides which theme draws light or dark ink.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
COLS = 52
RAMP = " .:-=+*#%@"  # light -> dense
CHAR_ASPECT = 0.52  # a terminal cell is roughly twice as tall as it is wide


def main() -> None:
    img = Image.open(ROOT / "assets" / "portrait.png").convert("RGBA")
    # flatten transparency onto white so the background reads as empty
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    img = Image.alpha_composite(bg, img).convert("L")
    img = ImageOps.equalize(img)  # spread the mid-tones so skin, glasses and beard stay readable

    w, h = img.size
    img = img.crop((0, 0, w, int(h * 0.74)))  # keep the face, drop most of the shirt
    w, h = img.size
    rows = round(COLS * h / w * CHAR_ASPECT)
    img = img.resize((COLS, rows), Image.LANCZOS)
    a = np.asarray(img, dtype=float) / 255.0  # 1 = white
    ink = np.clip(1.0 - a, 0, 1) ** 1.25  # 1 = darkest
    # the portrait background is pure white: keep it fully empty
    ink[a > 0.995] = 0.0

    lines = []
    for row in ink:
        line = "".join(RAMP[min(int(v * (len(RAMP) - 1) + 0.5), len(RAMP) - 1)] for v in row)
        lines.append(line.rstrip())
    (ROOT / "assets" / "ascii-art.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{COLS}x{rows}")


if __name__ == "__main__":
    main()
