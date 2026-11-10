"""One-off: turn a portrait photo into assets/portrait-ascii.json.

    python tools/make_ascii.py PHOTO --crop x0,y0,x1,y1 [--rect x0,y0,x1,y1]

--crop  region kept (pixels of the original photo)
--rect  rough box around the person, inside the crop, used to cut the background (GrabCut)
--view  region actually drawn (inside the crop); the cut-out works better on a wide crop
--bg    box that is certainly background (fixes leftovers of the cut-out), repeatable

Needs opencv-python, pillow and numpy. The photo itself is not stored in the repo.
Two monochrome versions come out, one per card theme: on the light card dense
characters are dark pixels (ink on paper); on the dark card they are bright pixels.
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
COLS = 100
CHAR_ASPECT = 4.2 / 8.9  # must match the art grid in build_card.py


def build_ramp(steps: int = 16) -> str:
    """Pick characters whose ink coverage rises evenly, measured on a real monospace font."""
    from PIL import Image, ImageDraw, ImageFont

    font = None
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/Library/Fonts/Courier New.ttf",
    ):
        try:
            font = ImageFont.truetype(path, 24)
            break
        except OSError:
            continue
    if font is None:
        return " .,:;-~=+*?#%&@"
    scores = {}
    for ch in "".join(chr(c) for c in range(32, 127)):
        im = Image.new("L", (20, 32), 0)
        ImageDraw.Draw(im).text((2, 2), ch, font=font, fill=255)
        scores[ch] = np.asarray(im, dtype=float).mean()
    ordered = sorted(scores, key=scores.get)
    top = scores[ordered[-1]]
    ramp = []
    for i in range(steps):
        target = top * i / (steps - 1)
        best = min((c for c in ordered if c not in ramp), key=lambda c: abs(scores[c] - target))
        ramp.append(best)
    return "".join(sorted(ramp, key=scores.get))


RAMP = build_ramp()  # light -> dense


def box(text: str) -> tuple[int, int, int, int]:
    x0, y0, x1, y1 = (int(v) for v in text.split(","))
    return x0, y0, x1, y1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("--crop", required=True, type=box)
    ap.add_argument("--rect", type=box)
    ap.add_argument("--view", type=box)
    ap.add_argument("--bg", type=box, action="append", default=[])
    ap.add_argument("--debug", help="write the cut-out preview here")
    args = ap.parse_args()

    img = cv2.imread(args.photo)
    x0, y0, x1, y1 = args.crop
    img = img[y0:y1, x0:x1]
    scale = 700 / img.shape[1]
    img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    h, w = img.shape[:2]

    # cut the person out of the background
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    if args.rect:
        rx0, ry0, rx1, ry1 = (int((v - o) * scale) for v, o in zip(args.rect, (x0, y0, x0, y0)))
        mask[ry0:ry1, rx0:rx1] = cv2.GC_PR_FGD
        for bx0, by0, bx1, by1 in args.bg:
            mask[max(0, int((by0 - y0) * scale)) : max(0, int((by1 - y0) * scale)), max(0, int((bx0 - x0) * scale)) : max(0, int((bx1 - x0) * scale))] = cv2.GC_BGD
        cv2.grabCut(img, mask, None, np.zeros((1, 65)), np.zeros((1, 65)), 8, cv2.GC_INIT_WITH_MASK)
    person = np.isin(mask, (cv2.GC_FGD, cv2.GC_PR_FGD)).astype(np.uint8)
    person = cv2.morphologyEx(person, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    person = cv2.morphologyEx(person, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    if args.view:
        vx0, vy0, vx1, vy1 = (int((v - o) * scale) for v, o in zip(args.view, (x0, y0, x0, y0)))
        img, person = img[vy0:vy1, vx0:vx1], person[vy0:vy1, vx0:vx1]
        h, w = img.shape[:2]

    if args.debug:
        prev = img.copy()
        prev[person == 0] = (prev[person == 0] * 0.15).astype(np.uint8)
        cv2.imwrite(args.debug, prev)

    # local contrast so the face keeps its relief
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
    blur = cv2.GaussianBlur(gray, (0, 0), 3)
    gray = np.clip(cv2.addWeighted(gray, 1.8, blur, -0.8, 0), 0, 255).astype(float) / 255.0

    rows = round(COLS * h / w * CHAR_ASPECT)
    ys = np.linspace(0, h, rows + 1).astype(int)
    xs = np.linspace(0, w, COLS + 1).astype(int)
    lum = np.zeros((rows, COLS))
    empty = np.zeros((rows, COLS), dtype=bool)
    for r in range(rows):
        for c in range(COLS):
            sl = (slice(ys[r], ys[r + 1]), slice(xs[c], xs[c + 1]))
            empty[r, c] = person[sl].mean() < 0.5
            lum[r, c] = gray[sl].mean()

    def normalise(grid: np.ndarray, gamma: float) -> np.ndarray:
        inside = grid[~empty]
        lo, hi = np.percentile(inside, 2), np.percentile(inside, 98)
        out = np.clip((grid - lo) / (hi - lo), 0, 1) ** gamma
        out[empty] = 0.0
        return out

    def to_lines(ink: np.ndarray) -> list[str]:
        return [
            "".join(RAMP[min(int(v * (len(RAMP) - 1) + 0.5), len(RAMP) - 1)] if v > 0.04 else " " for v in row).rstrip()
            for row in ink
        ]

    art = {
        "light": to_lines(normalise(1.0 - lum, 1.2)),
        "dark": to_lines(normalise(lum, 1.1)),
    }
    (ROOT / "assets" / "portrait-ascii.json").write_text(json.dumps(art), encoding="utf-8")
    print(f"{COLS}x{rows}")


if __name__ == "__main__":
    main()
