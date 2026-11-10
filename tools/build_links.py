"""Pixel-art link buttons: link_<name>_<theme>.svg (palette follows theme.py)."""
from pathlib import Path

from theme import FONT, THEMES

ROOT = Path(__file__).resolve().parent.parent

W, H, PX = 280, 44, 4  # px = size of one "pixel"

# 7x7 icons
ICONS = {
    "portfolio": [  # a little browser window
        "1111111",
        "1000001",
        "1111111",
        "1000001",
        "1011101",
        "1000001",
        "1111111",
    ],
    "linkedin": [  # "in"
        "0000000",
        "1011010",
        "0011101",
        "1011001",
        "1011001",
        "1011001",
        "0000000",
    ],
    "malt": [  # "M"
        "0000000",
        "1100011",
        "1110111",
        "1101011",
        "1100011",
        "1100011",
        "0000000",
    ],
}

BUTTONS = {
    "portfolio": "PORTFOLIO",
    "linkedin": "LINKEDIN",
    "malt": "MALT",
}


def corner_path(w: int, h: int, s: int) -> str:
    """Rectangle whose corners are cut in one stair step (pixel-art look)."""
    return (
        f"M{s} 0 H{w - s} V{s} H{w} V{h - s} H{w - s} V{h} H{s} V{h - s} H0 V{s} H{s} Z"
    )


def render(name: str, label: str, theme_name: str) -> str:
    t = THEMES[theme_name]
    icon = ICONS[name]
    cells = []
    ix, iy = 22, (H - 7 * PX) // 2
    for r, row in enumerate(icon):
        for c, ch in enumerate(row):
            if ch == "1":
                cells.append(
                    f'<rect x="{ix + c * PX}" y="{iy + r * PX}" width="{PX}" height="{PX}" fill="{t["button_edge"]}"/>'
                )
    shadow = corner_path(W - 4, H - 4, 4)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{label.title()}" shape-rendering="crispEdges">
<g transform="translate(4 4)"><path d="{shadow}" fill="{t['button_edge']}" opacity=".35"/></g>
<path d="{corner_path(W - 4, H - 4, 4)}" fill="{t['button_bg']}" stroke="{t['button_edge']}" stroke-width="2"/>
{chr(10).join(cells)}
<text x="{(W - 4) / 2 + 14}" y="{H / 2 + 1:.0f}" text-anchor="middle" dominant-baseline="middle" font-family="{FONT}" font-size="14" font-weight="700" letter-spacing="2" fill="{t['button_fg']}" style="shape-rendering:auto">{label}</text>
</svg>
"""


def main() -> None:
    for name, label in BUTTONS.items():
        for theme in ("dark", "light"):
            (ROOT / f"link_{name}_{theme}.svg").write_text(render(name, label, theme), encoding="utf-8")
    print("buttons rebuilt")


if __name__ == "__main__":
    main()
