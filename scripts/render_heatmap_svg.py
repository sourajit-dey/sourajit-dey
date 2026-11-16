"""Step 5b from Avi Vashishta's guide (18 Jul 2026):
"How I Built an Animated GitHub Profile README".

Render the JSON as the classic 53-week x 7-day calendar of
rounded, colored boxes using a GitHub-ish green ramp:
    PALETTE = ["#161b22", "#0e4429", "#006d32",
               "#26a641", "#39d353", "#69f0a0"]
    # none -> brightest (level 5 is a neon top end)

Reveal it once with a diagonal, line-after-line slide-down
(CSS keyframes that play on load, then freeze — no looping
"glow"), and add a Less->More legend plus a stats footer
(`"9,376 contributions in the last year"` — here, the REAL
total parsed from GitHub). Output: `contrib-heatmap.svg`.

Note on levels: GitHub serves levels 0-4 in the HTML this
script's companion fetcher parses. The guide's palette has
6 entries (index 0 = none, 1-4 = GitHub levels, 5 = a neon
top end). Level 4 maps to index 4 (#39d353); index 5 is kept
in the palette as the guide wrote it but is not used unless
a future source reports a level 5.

STATIC=1: emits a frozen final frame (no animation) for
local screenshot verification, matching the info-card script.
"""

import json
import os
from datetime import date

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "contributions.json")
OUT = os.path.join(BASE, "contrib-heatmap.svg")

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]

CELL = 13
GAP = 3
STEP = CELL + GAP
COLS = 53
ROWS = 7
LEFT = 12
TOP = 28
WIDTH = 860
GRID_W = COLS * STEP - GAP
HEIGHT = TOP + ROWS * STEP + 44
LABEL_FILL = "#8b949e"
TEXT_FILL = "#c9d1d9"


def main():
    static = os.environ.get("STATIC") == "1"
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    days = [
        (date.fromisoformat(d["date"]), d["count"], d["level"])
        for d in data["days"]
    ]
    days.sort()
    start = days[0][0]
    total = data["total_contributions"]

    # Month labels: first week in which each month starts.
    month_at_week = {}
    for d, _, _ in days:
        week = (d - start).days // 7
        key = d.strftime("%Y-%m")
        if key not in month_at_week:
            month_at_week[key] = (week, d.strftime("%b"))

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" '
        f'aria-label="Contribution graph: {total} contributions in '
        f'the last year">'
    )
    parts.append(f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117"/>')
    if not static:
        parts.append(
            "<style>"
            "@keyframes slideDown{from{opacity:0;transform:translateY(-6px)}"
            "to{opacity:1;transform:translateY(0)}}"
            ".cell{opacity:0;animation:slideDown .3s ease-out forwards}"
            "@media (prefers-reduced-motion: reduce){.cell{animation:none;opacity:1}}"
            "</style>"
        )
    # Month labels.
    for week, label in month_at_week.values():
        x = LEFT + week * STEP
        parts.append(
            f'<text x="{x}" y="18" font-family="sans-serif" '
            f'font-size="11" fill="{LABEL_FILL}">{label}</text>'
        )
    # Day cells, diagonal reveal: delay grows with week + row.
    for d, count, level in days:
        offset = (d - start).days
        week, row = divmod(offset, 7)
        x = LEFT + week * STEP
        y = TOP + row * STEP
        fill = PALETTE[min(max(level, 0), 5)]
        delay = (week + row) * 0.02
        cls = "" if static else ' class="cell"'
        style = "" if static else f' style="animation-delay:{delay:.2f}s"'
        title = f"{count} contribution{'s' if count != 1 else ''} on {d.isoformat()}"
        parts.append(
            f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
            f'rx="3" fill="{fill}"{cls}{style}>'
            f"<title>{title}</title></rect>"
        )
    # Less -> More legend.
    lx = WIDTH - 170
    ly = HEIGHT - 22
    parts.append(
        f'<text x="{lx}" y="{ly + 9}" font-family="sans-serif" '
        f'font-size="11" fill="{LABEL_FILL}">Less</text>'
    )
    for i, fill in enumerate(PALETTE[:5]):
        x = lx + 34 + i * (CELL + 3)
        parts.append(
            f'<rect x="{x}" y="{ly}" width="11" height="11" rx="2" '
            f'fill="{fill}"/>'
        )
    parts.append(
        f'<text x="{lx + 34 + 5 * (CELL + 3) + 4}" y="{ly + 9}" '
        f'font-family="sans-serif" font-size="11" '
        f'fill="{LABEL_FILL}">More</text>'
    )
    # Stats footer with the REAL total.
    parts.append(
        f'<text x="{LEFT}" y="{HEIGHT - 13}" font-family="monospace" '
        f'font-size="13" fill="{TEXT_FILL}">{total} contributions '
        f"in the last year</text>"
    )
    parts.append("</svg>")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")
    print(f"[heatmap] wrote {OUT} ({'STATIC' if static else 'animated'}), "
          f"total={total}, days={len(days)}")


if __name__ == "__main__":
    main()
