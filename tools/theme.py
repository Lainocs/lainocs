"""Shared palette (lainocs.fr identity) and tiny SVG helpers."""
from html import escape

FONT = "ui-monospace, 'SF Mono', SFMono-Regular, Menlo, Consolas, 'DejaVu Sans Mono', monospace"

THEMES = {
    "dark": {
        "bg": "#16171A",
        "panel": "#1D1E22",
        "border": "#2C2E34",
        "text": "#C9CBD1",
        "value": "#F3F4F6",
        "key": "#D4F25A",
        "head": "#D4F25A",
        "dots": "#4B4E56",
        "art": "#D4F25A",
        "accent": "#A98BD9",
        "pill": "#2D1B3F",
        "button_bg": "#1D1E22",
        "button_fg": "#F3F4F6",
        "button_edge": "#D4F25A",
        "grid": ["#26272D", "#44541C", "#76912A", "#AACB38", "#D4F25A"],
        "pacman": "#D4F25A",
    },
    "light": {
        "bg": "#FFFFFF",
        "panel": "#FAFAF7",
        "border": "#E2E3E7",
        "text": "#3D3F46",
        "value": "#16171A",
        "key": "#2D1B3F",
        "head": "#2D1B3F",
        "dots": "#BDC0C8",
        "art": "#2D1B3F",
        "accent": "#2D1B3F",
        "pill": "#D4F25A",
        "button_bg": "#FFFFFF",
        "button_fg": "#16171A",
        "button_edge": "#2D1B3F",
        "grid": ["#EDEEF1", "#E3EDB5", "#CDE274", "#A9C834", "#7B9610"],
        "pacman": "#2D1B3F",
    },
}


def esc(s: str) -> str:
    return escape(s, quote=True)
