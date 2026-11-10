# Profile card tooling

Generates the SVGs shown in the profile README.

| File | Role |
| --- | --- |
| `make_ascii.py` | One-off: turns `assets/portrait.png` into the monochrome ASCII portrait `assets/portrait-ascii.json` |
| `fetch_stats.py` | Reads public GitHub numbers into `cache/stats.json` (needs `GITHUB_TOKEN`) |
| `build_card.py` | `dark_mode.svg` / `light_mode.svg`, the neofetch-style card with an ASCII portrait |
| `build_pacman.py` | `pacman_*.svg`, the animated contribution graph |
| `build_links.py` | `link_*.svg`, the pixel-art buttons |
| `theme.py` | Shared palette (lainocs.fr identity) |

Local run: `pip install requests pillow numpy`, then from `tools/`: `python build_card.py && python build_pacman.py && python build_links.py`.
The GitHub Action in `.github/workflows/profile-card.yml` does it daily.

The card format is inspired by Andrew6rant's profile README. The code here is written from scratch.
