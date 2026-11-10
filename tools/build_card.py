"""Render the neofetch-style profile card (dark_mode.svg / light_mode.svg).

Reads assets/portrait-pixels.json and cache/stats.json. Every text run is placed on a
fixed character grid with an explicit textLength, so the columns stay aligned
whatever monospace font the viewer's browser ends up using.
"""
import colorsys
import json
from pathlib import Path

from theme import FONT, THEMES, esc

ROOT = Path(__file__).resolve().parent.parent

FS = 12  # font size
CW = 7.2  # character cell width
LH = 16  # line height
PAD = 26
BAR = 34  # window title bar
PX = 4.4  # size of one portrait pixel
GAP_PX = 28
INFO_COLS = 58

HANDLE = "nicolas@lainocs"


def lift(hex_colour: str, theme_name: str) -> str:
    """On the dark card, lift the darkest tones so the outlines and hair stay visible."""
    if theme_name != "dark":
        return hex_colour
    r, g, b = (int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, sat, v = colorsys.rgb_to_hsv(r, g, b)
    r, g, b = colorsys.hsv_to_rgb(h, sat, 0.22 + 0.78 * v)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def portrait_svg(grid: list, theme_name: str, x0: float, y0: float) -> str:
    """Pixel portrait: horizontal runs of one colour are merged into single rects."""
    rects = []
    for r, row in enumerate(grid):
        c = 0
        while c < len(row):
            col = row[c]
            if col is None:
                c += 1
                continue
            end = c
            while end + 1 < len(row) and row[end + 1] == col:
                end += 1
            rects.append(
                f'<rect x="{x0 + c * PX:.2f}" y="{y0 + r * PX:.2f}" width="{(end - c + 1) * PX + 0.35:.2f}" '
                f'height="{PX + 0.35:.2f}" fill="{lift(col, theme_name)}"/>'
            )
            c = end + 1
    return '<g shape-rendering="crispEdges">' + "".join(rects) + "</g>"


def info_lines(stats: dict) -> list:
    langs = ", ".join(stats.get("languages") or ["TypeScript", "JavaScript"])
    contributions = f"{stats['contributions']:,}"
    return [
        ("head", HANDLE),
        ("kv", "OS", "macOS"),
        ("kv", "Host", "Lainocs (freelance)"),
        ("kv", "Kernel", "Full-stack web developer"),
        ("kv", "Previously", "Escape (YC W23), 2 years"),
        ("kv", "Teaching", "IIM, Paris"),
        ("kv", "Location", "Paris, France"),
        ("blank",),
        ("kv", "Languages.Programming", "TypeScript, JavaScript, Python"),
        ("kv", "Languages.Computer", "HTML, CSS, SQL, GraphQL"),
        ("kv", "Languages.Real", "French, English"),
        ("blank",),
        ("kv", "Stack", "Next.js, React, Tailwind, Node.js, PostgreSQL"),
        ("kv", "Focus", "Web apps, 3D on the web, product UI"),
        ("kv", "Hobbies.Software", "Home lab, Creative coding, Bots"),
        ("kv", "Hobbies.Other", "Cinema, Music, Travel"),
        ("blank",),
        ("section", "Contact"),
        ("kv", "Website", "lainocs.fr"),
        ("kv", "LinkedIn", "nicolasdegarrigues"),
        ("kv", "Malt", "nicolasdegarrigues"),
        ("blank",),
        ("section", "GitHub Stats"),
        ("pair", ("Repos", str(stats["repos"])), ("Followers", str(stats["followers"]))),
        ("pair", ("Contributions", contributions), ("Since", stats["since"])),
        ("kv", "Languages.Top", langs),
    ]


class Canvas:
    def __init__(self, theme: dict):
        self.t = theme
        self.out: list[str] = []
        self.x_off = 0.0

    def text(self, col: float, row: float, s: str, cls: str, y0: float, x_off: float = 0.0) -> None:
        if not s:
            return
        x = PAD + self.x_off + x_off + col * CW
        y = y0 + row * LH
        self.out.append(
            f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" textLength="{len(s) * CW:.1f}" '
            f'lengthAdjust="spacing" xml:space="preserve">{esc(s)}</text>'
        )


def kv_runs(key: str, value: str, width: int):
    """key ..... value, right-aligned to `width` columns."""
    left = key + ":"
    dots = width - len(left) - len(value) - 2
    return [(0, left, "k"), (len(left) + 1, "." * max(dots, 2), "d"), (width - len(value), value, "v")]


def render(theme_name: str, grid: list, stats: dict) -> str:
    t = THEMES[theme_name]
    c = Canvas(t)
    info = info_lines(stats)
    art_w = len(grid[0]) * PX
    art_h = len(grid) * PX
    info_x = art_w + GAP_PX
    body_h = max(art_h, len(info) * LH)
    width = round(PAD * 2 + info_x + INFO_COLS * CW)
    height = round(BAR + PAD + body_h + PAD - 6)
    y0 = BAR + PAD

    # pixel portrait, vertically centred against the info column
    portrait = portrait_svg(grid, theme_name, PAD, y0 + max((len(info) * LH - art_h) / 2, 0) - 6)

    c.x_off = info_x
    for i, item in enumerate(info):
        kind = item[0]
        if kind == "head":
            name = item[1]
            c.text(0, i, name, "h", y0)
            c.text(len(name) + 1, i, "-" * (INFO_COLS - len(name) - 1), "d", y0)
        elif kind == "section":
            title = item[1]
            c.text(0, i, "- ", "d", y0)
            c.text(2, i, title, "h", y0)
            c.text(3 + len(title), i, "-" * (INFO_COLS - len(title) - 3), "d", y0)
        elif kind == "kv":
            for col, s, cls in kv_runs(item[1], item[2], INFO_COLS):
                c.text(col, i, s, cls, y0)
        elif kind == "pair":
            half = (INFO_COLS - 3) // 2
            for j, (k, v) in enumerate(item[1:]):
                off = 0 if j == 0 else half + 3
                for col, s, cls in kv_runs(k, v, half):
                    c.text(off + col, i, s, cls, y0)
                if j == 0:
                    c.text(half + 1, i, "|", "d", y0)

    dots = "".join(
        f'<circle cx="{22 + 16 * n}" cy="{BAR / 2:.0f}" r="5" fill="{col}"/>'
        for n, col in enumerate([t["key"] if theme_name == "dark" else t["accent"], t["accent"], t["dots"]])
    )
    title_x = width / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Nicolas de Garrigues, développeur web full-stack freelance à Paris. macOS, TypeScript, Next.js, PostgreSQL.">
<style>
text {{ font-family: {FONT}; font-size: {FS}px; white-space: pre; }}
.h {{ fill: {t['head']}; font-weight: 700; }}
.k {{ fill: {t['key']}; font-weight: 700; }}
.v {{ fill: {t['value']}; }}
.d {{ fill: {t['dots']}; }}
.bar {{ fill: {t['text']}; font-size: 11px; }}
</style>
<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{t['panel']}" stroke="{t['border']}"/>
<path d="M0.5 {BAR} V12.5 a12 12 0 0 1 12 -12 H{width - 12.5} a12 12 0 0 1 12 12 V{BAR} Z" fill="{t['bg']}" stroke="{t['border']}"/>
{dots}
<text x="{title_x}" y="{BAR / 2 + 4:.0f}" class="bar" text-anchor="middle">{HANDLE}: ~</text>
{portrait}
{chr(10).join(c.out)}
</svg>
"""


def main() -> None:
    stats = json.loads((ROOT / "cache" / "stats.json").read_text(encoding="utf-8"))
    grid = json.loads((ROOT / "assets" / "portrait-pixels.json").read_text(encoding="utf-8"))
    for name in ("dark", "light"):
        (ROOT / f"{name}_mode.svg").write_text(render(name, grid, stats), encoding="utf-8")
    print("card rebuilt")


if __name__ == "__main__":
    main()
