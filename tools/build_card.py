"""Render the neofetch-style profile card (dark_mode.svg / light_mode.svg).

Reads assets/ascii-art.txt and cache/stats.json. Every text run is placed on a
fixed character grid with an explicit textLength, so the columns stay aligned
whatever monospace font the viewer's browser ends up using.
"""
import json
from pathlib import Path

from theme import FONT, THEMES, esc

ROOT = Path(__file__).resolve().parent.parent

FS = 12  # font size
CW = 7.2  # character cell width
LH = 16  # line height
PAD = 26
BAR = 34  # window title bar
ART_COLS = 52
GAP = 3
INFO_COLS = 58

HANDLE = "nicolas@lainocs"


def info_lines(stats: dict) -> list:
    langs = ", ".join(stats.get("languages") or ["TypeScript", "JavaScript"])
    contributions = f"{stats['contributions']:,}"
    return [
        ("head", HANDLE),
        ("kv", "OS", "Linux (CachyOS), Windows"),
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
        ("kv", "Hobbies.Software", "Self-hosting, Discord bots, Three.js"),
        ("kv", "Hobbies.Other", "Cinema, Guitar, Fighting games"),
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

    def text(self, col: float, row: float, s: str, cls: str, y0: float) -> None:
        if not s:
            return
        x = PAD + col * CW
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


def render(theme_name: str, art: list[str], stats: dict) -> str:
    t = THEMES[theme_name]
    c = Canvas(t)
    info = info_lines(stats)
    body_rows = max(len(art), len(info))
    width = round(PAD * 2 + (ART_COLS + GAP + INFO_COLS) * CW)
    height = round(BAR + PAD + body_rows * LH + PAD - 6)
    y0 = BAR + PAD

    # ASCII portrait, vertically centred against the info column
    art_off = max((len(info) - len(art)) // 2, 0)
    for i, line in enumerate(art):
        c.text(0, art_off + i, line, "a", y0)

    info_col = ART_COLS + GAP
    for i, item in enumerate(info):
        kind = item[0]
        if kind == "head":
            name = item[1]
            c.text(info_col, i, name, "h", y0)
            c.text(info_col + len(name) + 1, i, "-" * (INFO_COLS - len(name) - 1), "d", y0)
        elif kind == "section":
            title = item[1]
            c.text(info_col, i, "- ", "d", y0)
            c.text(info_col + 2, i, title, "h", y0)
            c.text(info_col + 3 + len(title), i, "-" * (INFO_COLS - len(title) - 3), "d", y0)
        elif kind == "kv":
            for col, s, cls in kv_runs(item[1], item[2], INFO_COLS):
                c.text(info_col + col, i, s, cls, y0)
        elif kind == "pair":
            half = (INFO_COLS - 3) // 2
            for j, (k, v) in enumerate(item[1:]):
                off = 0 if j == 0 else half + 3
                for col, s, cls in kv_runs(k, v, half):
                    c.text(info_col + off + col, i, s, cls, y0)
                if j == 0:
                    c.text(info_col + half + 1, i, "|", "d", y0)

    dots = "".join(
        f'<circle cx="{22 + 16 * n}" cy="{BAR / 2:.0f}" r="5" fill="{col}"/>'
        for n, col in enumerate([t["key"] if theme_name == "dark" else t["accent"], t["accent"], t["dots"]])
    )
    title_x = width / 2
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Nicolas de Garrigues, développeur web full-stack freelance à Paris. Linux, TypeScript, Next.js, PostgreSQL.">
<style>
text {{ font-family: {FONT}; font-size: {FS}px; white-space: pre; }}
.a {{ fill: {t['art']}; }}
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
{chr(10).join(c.out)}
</svg>
"""


def main() -> None:
    art = (ROOT / "assets" / "ascii-art.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    stats = json.loads((ROOT / "cache" / "stats.json").read_text(encoding="utf-8"))
    for name in ("dark", "light"):
        (ROOT / f"{name}_mode.svg").write_text(render(name, art, stats), encoding="utf-8")
    print("card rebuilt")


if __name__ == "__main__":
    main()
