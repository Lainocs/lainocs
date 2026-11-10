"""Render the neofetch-style profile card (dark_mode.svg / light_mode.svg).

Reads assets/portrait-ascii.json and cache/stats.json. Every text run is placed on a
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
ART_CW = 4.9  # the portrait uses a finer grid than the text
ART_LH = 10.4
ART_FS = 8.2
GAP_PX = 28
INFO_COLS = 58

HANDLE = "nicolas@lainocs"


def lift(hex_colour: str, theme_name: str) -> str:
    """Adapt a portrait colour to the card: lift the shadows on dark, deepen the lights on light."""
    r, g, b = (int(hex_colour[i : i + 2], 16) / 255 for i in (1, 3, 5))
    h, sat, v = colorsys.rgb_to_hsv(r, g, b)
    if theme_name == "dark":
        v = 0.42 + 0.58 * v
    else:
        v = min(v, 0.82)
        sat = min(1.0, sat * 1.2)
    r, g, b = colorsys.hsv_to_rgb(h, sat, v)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def art_line(line: str, colours: list, theme_name: str) -> str:
    """One portrait row as <tspan> runs sharing a colour."""
    runs: list[list[str]] = []
    for ch, col in zip(line, colours):
        col = lift(col, theme_name)
        if runs and runs[-1][1] == col:
            runs[-1][0] += ch
        else:
            runs.append([ch, col])
    return "".join(
        f'<tspan fill="{col}">{esc(text)}</tspan>' if text.strip() else esc(text) for text, col in runs
    )


def info_lines(stats: dict) -> list:
    langs = ", ".join(stats.get("languages") or ["TypeScript", "JavaScript"])
    contributions = f"{stats['contributions']:,}"
    return [
        ("head", HANDLE),
        ("kv", "OS", "macOS"),
        ("kv", "Host", "Lainocs (freelance)"),
        ("kv", "Kernel", "Full-stack web developer"),
        ("kv", "Previously", "Escape (YC W23), 2 years"),
        ("kv", "Location", "Paris, Bangkok, Seoul"),
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
        ("kv", "Email", "contact@lainocs.fr"),
        ("kv", "Email.Personal", "ndegarrigues@gmail.com"),
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


def render(theme_name: str, art: dict, stats: dict) -> str:
    t = THEMES[theme_name]
    c = Canvas(t)
    info = info_lines(stats)
    lines = art["rows"]
    art_w = max(len(l) for l in lines) * ART_CW
    art_h = len(lines) * ART_LH
    info_x = art_w + GAP_PX
    body_h = max(art_h, len(info) * LH)
    width = round(PAD * 2 + info_x + INFO_COLS * CW)
    height = round(BAR + PAD + body_h + PAD - 6)
    y0 = BAR + PAD

    # portrait on its own finer grid, vertically centred against the info column
    art_top = y0 + max((len(info) * LH - art_h) / 2, 0) - 6
    portrait = "\n".join(
        f'<text x="{PAD}" y="{art_top + (i + 1) * ART_LH:.1f}" class="a" textLength="{len(line) * ART_CW:.1f}" '
        f'lengthAdjust="spacing" xml:space="preserve">{art_line(line, art["colors"][i], theme_name)}</text>'
        for i, line in enumerate(lines)
        if line.strip()
    )

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
.a {{ font-size: {ART_FS}px; }}
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
    art = json.loads((ROOT / "assets" / "portrait-ascii.json").read_text(encoding="utf-8"))
    for name in ("dark", "light"):
        (ROOT / f"{name}_mode.svg").write_text(render(name, art, stats), encoding="utf-8")
    print("card rebuilt")


if __name__ == "__main__":
    main()
