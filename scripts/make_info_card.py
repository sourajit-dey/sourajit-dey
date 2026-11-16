"""Step 4 from Avi Vashishta's guide (18 Jul 2026):
"How I Built an Animated GitHub Profile README".

`make_info_card.py` hand-authors a small SVG that looks like
the output of the `neofetch` command: a title bar, then
colored key/value rows — `Now`, `Prev`, `Stack`, `Highlights`.
Keep the content here and *not* in the contribution graph; the
graph already covers your GitHub stats, so the card is for the
story numbers can't tell.

Each line fades and slides in on a short stagger so the panel
looks like it's printing next to the portrait. A `STATIC=1` env
var emits a frozen frame for local Quick Look previews.

CONTENT — minimal / privacy, per the user:
  Only sourajit-dey, Aspiring AI Engineer, "building real AI
  systems — not wrappers", and the tech stack already on his
  live GitHub profile. No internship target, no Project A/B,
  no CGPA, no college/semester, no roadmap, no bio/goals.

One deliberate deviation from the guide's key names: the guide
uses `Prev` (previous role). sourajit-dey has no previous role
to list, and inventing one would be false, so that row is
`Focus` instead. Everything else — title bar, key/value rows,
staggered fade-in, STATIC=1 — follows the guide.

Output: info-card.svg (490 wide, to match the README table:
370 + 490 = 860, the heatmap width).
"""

import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "info-card.svg")

WIDTH = 490
HEIGHT = 210
BG = "#0d1117"
BORDER = "#30363d"
KEY_FILL = "#39d353"
VAL_FILL = "#c9d1d9"
TITLE_FILL = "#58a6ff"

ROWS = [
    ("Now", "Aspiring AI Engineer"),
    ("Focus", "Building real AI systems — not wrappers"),
    ("Stack", "Python • Java • JavaScript • Node.js"),
    ("", "MongoDB • MERN"),
    ("Highlights", "Check my repos to see what"),
    ("", "I've actually built"),
]


def esc(s):
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def main():
    static = os.environ.get("STATIC") == "1"
    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        f'aria-label="About sourajit-dey">'
    )
    if not static:
        parts.append(
            "<style>"
            "@keyframes fadeSlide{from{opacity:0;transform:translateY(4px)}"
            "to{opacity:1;transform:translateY(0)}}"
            ".line{opacity:0;animation:fadeSlide .45s ease-out forwards}"
            "@media (prefers-reduced-motion: reduce){.line{animation:none;opacity:1}}"
            "</style>"
        )
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{HEIGHT - 1}" '
        f'rx="6" fill="{BG}" stroke="{BORDER}"/>'
    )
    # Title bar: three dots + neofetch-style title.
    parts.append(
        f'<circle cx="20" cy="20" r="5" fill="#ff5f56"/>'
        f'<circle cx="38" cy="20" r="5" fill="#ffbd2e"/>'
        f'<circle cx="56" cy="20" r="5" fill="#27c93f"/>'
    )
    parts.append(
        f'<text x="76" y="24" font-family="monospace" font-size="13" '
        f'fill="{TITLE_FILL}">sourajit-dey@github ~ $ neofetch</text>'
    )
    parts.append(
        f'<line x1="12" y1="36" x2="{WIDTH - 12}" y2="36" '
        f'stroke="{BORDER}"/>'
    )
    y = 64
    for i, (key, val) in enumerate(ROWS):
        delay = 0.15 + i * 0.18
        cls = "" if static else ' class="line"'
        style = "" if static else f' style="animation-delay:{delay:.2f}s"'
        if key:
            parts.append(
                f'<text x="20" y="{y}" font-family="monospace" '
                f'font-size="13" fill="{KEY_FILL}"{cls}{style}>'
                f"{esc(key)}: </text>"
            )
            # Value starts after the key; estimate key width at ~8px/char.
            vx = 20 + (len(key) + 2) * 8
            parts.append(
                f'<text x="{vx}" y="{y}" font-family="monospace" '
                f'font-size="13" fill="{VAL_FILL}"{cls}{style}>'
                f"{esc(val)}</text>"
            )
        else:
            parts.append(
                f'<text x="20" y="{y}" font-family="monospace" '
                f'font-size="13" fill="{VAL_FILL}"{cls}{style}>'
                f"{esc(val)}</text>"
            )
        y += 24
    parts.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")
    print(f"[info] wrote {OUT} ({'STATIC' if static else 'animated'})")


if __name__ == "__main__":
    main()
