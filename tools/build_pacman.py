"""Pac-Man eats the contribution graph (pacman_dark.svg / pacman_light.svg).

Pac-Man sweeps the calendar column by column; every cell with activity vanishes
as he passes, and the board resets when the loop restarts. Pure SMIL, so it
animates inside a README <img> with no script.
"""
import json
from datetime import date
from pathlib import Path

from theme import FONT, THEMES

ROOT = Path(__file__).resolve().parent.parent

CELL = 11
STEP = 14  # cell pitch
R = 6.2  # pac-man radius
SPEED = 0.045  # seconds per cell
HOLD = 2.2  # pause before the loop restarts
PAD_X = 26
TOP = 46
WIDTH = 860


def grid(calendar):
    """Place days on a Sunday-first week grid -> {(col,row): level}."""
    cells = {}
    col = 0
    for d, level, *_ in calendar:
        y, m, dd = map(int, d.split("-"))
        row = (date(y, m, dd).weekday() + 1) % 7  # Sunday = 0
        if row == 0 and cells:
            col += 1
        cells[(col, row)] = level
    return cells, col + 1


def mouth(open_deg: float) -> str:
    import math

    a = math.radians(open_deg)
    x, y = R * math.cos(a), R * math.sin(a)
    return f"M0 0 L{x:.2f} {-y:.2f} A{R} {R} 0 1 0 {x:.2f} {y:.2f} Z"


def render(theme_name: str, stats: dict) -> str:
    t = THEMES[theme_name]
    cells, cols = grid(stats["calendar"])
    width_grid = cols * STEP
    x0 = (WIDTH - width_grid) / 2 + (STEP - CELL) / 2
    height = TOP + 7 * STEP + 22

    # path: down column 0, up column 1, ...
    order = []
    for c in range(cols):
        rows = range(7) if c % 2 == 0 else range(6, -1, -1)
        order += [(c, r) for r in rows]
    total = len(order) * SPEED
    loop = total + HOLD
    time_at = {pos: i * SPEED for i, pos in enumerate(order)}

    def center(c, r):
        return x0 + c * STEP + CELL / 2, TOP + r * STEP + CELL / 2

    rects = []
    for (c, r), level in sorted(cells.items()):
        x = x0 + c * STEP
        y = TOP + r * STEP
        fill = t["grid"][level]
        base = f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL}" height="{CELL}" rx="2.5" fill="{fill}"'
        if level == 0:
            rects.append(base + "/>")
            continue
        k_eat = time_at[(c, r)] / loop
        k_back = total / loop
        rects.append(
            base
            + f'><animate attributeName="opacity" calcMode="discrete" values="1;0;1" '
            f'keyTimes="0;{k_eat:.5f};{k_back:.5f}" dur="{loop:.2f}s" repeatCount="indefinite"/></rect>'
        )

    pts = [center(c, r) for c, r in order]
    path = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    label = f"{stats['contributions']:,} contributions in the last year"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}" role="img" aria-label="Pac-Man eating the GitHub contribution graph: {label}">
<style>text {{ font-family: {FONT}; font-size: 12px; fill: {t['text']}; }}</style>
<text x="{PAD_X}" y="22">{label}</text>
<text x="{WIDTH - PAD_X}" y="22" text-anchor="end" opacity=".7">Pac-Man is hungry</text>
{chr(10).join(rects)}
<g>
<path fill="{t['pacman']}">
<animate attributeName="d" dur="0.28s" repeatCount="indefinite" values="{mouth(38)};{mouth(2)};{mouth(38)}"/>
</path>
<animateMotion dur="{loop:.2f}s" repeatCount="indefinite" rotate="auto" calcMode="linear" keyPoints="0;1;1" keyTimes="0;{total / loop:.5f};1" path="{path}"/>
</g>
</svg>
"""


def main() -> None:
    stats = json.loads((ROOT / "cache" / "stats.json").read_text(encoding="utf-8"))
    for name in ("dark", "light"):
        (ROOT / f"pacman_{name}.svg").write_text(render(name, stats), encoding="utf-8")
    print("pacman rebuilt")


if __name__ == "__main__":
    main()
