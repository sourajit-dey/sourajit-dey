"""Avi Vashishta's 9 Nov 2026 redesign, copied for sourajit-dey:
"I Redesigned My GitHub Profile README With Animated SVG Cards"
(https://www.avivashishta.com/blog/github-profile-readme-animated-svg-cards)

One Python script, render_readme_cards.py, draws ALL cards from
real data/contributions.json (total, months, streak, busiest day,
graph) — no invented numbers. The GitHub Action runs it daily and
commits the SVGs. STATIC=1 emits the frozen final frame for
screenshots. Animations are off under prefers-reduced-motion.
Cards are timed top to bottom: hero, blue graph, bars, tiles,
then repo cards.

Cards (all 860 wide, except tiles 278 = 32.5% of 860):
  cards/hero.svg          name rising line by line, blue shine sweep
                          across "Soura" (SMIL gradientTransform),
                          ASCII portrait printing in row by row
                          (the user's chosen 200x106 colour ASCII,
                          embedded and scaled — see note below),
                          one line about him.
  cards/heatmap-blue.svg  53x7 contribution graph in brand blue,
                          popping in square by square, left to right.
  cards/activity.svg      monthly bars growing up from the baseline,
                          best month (Aug, 49) in blue with its number
                          popping in, plus streak / active days /
                          busiest day stats.
  cards/build.svg         tile: 4 featured repos -> his repos tab.
  cards/brand.svg         tile: 20 blog posts -> self-hosting blog.
  cards/learn.svg         tile: 27 active days -> DSA practice repo.
                          Tiles count up from zero via 18 SMIL <set>
                          frames, ring pulses, arrow nudges.
  cards/repo-*.svg        one card per featured repo (4, 2x2 grid
                          in the README). Name + language + updated
                          date only — no star counts, because only
                          forest-monitor's star count (1) was visible
                          on the repo page and the others were not.

REAL NUMBERS (data/contributions.json, fetched 2026-11-16, no token):
  total 150, best day 19 on 2026-08-20, last contribution 2026-10-24,
  longest streak 4 days, 27 of 366 days active.
  Monthly: Nov 0, Dec 0, Jan 2, Feb 4, Mar 3, Apr 23, May 33, Jun 15,
  Jul 8, Aug 49, Sep 2, Oct 11, Nov 0.
REAL REPOS (github.com/sourajit-dey?tab=repositories, read 2026-11-16):
  Ai-healthcare (JavaScript, updated Mar 26 2026),
  DSA-Question-Practice (Java, Apr 17 2026),
  forest-monitor (Python, Aug 20 2026),
  habit-tracker (Dart, Jan 30 2026).
  The repos tab lists 15 repos on the first page; no total repo
  count is claimed anywhere, so the BUILD tile counts the 4
  FEATURED repos shown below it, not "all repos".
BLOG POSTS: 20 published on selfhostingbeginners.blogspot.com
  (Post 20, Proxmox, published 2026-11-15 — from the user's own log).

DEPARTURES / ADAPTATIONS (recorded, not silent):
  - Hero ASCII: Avi's hero embeds a monochrome ASCII portrait.
    This one embeds the user's chosen COLOUR 200x106 ASCII
    (sourajit-dey-ascii.svg, md5 fe273220c5df767d038f5c990c4fbd86),
    scaled 0.27x to 324x286 inside the 860x340 hero. At that size
    it reads as a small colour portrait, not as readable glyphs —
    the full-size ASCII is also kept in the repo root.
  - Colour scheme: Avi's redesign is paper/ink (light). This copy
    keeps the dark GitHub palette (#0d1117) of the terminal profile,
    so the hero matches the ASCII (dark background) and GitHub dark
    mode. The blue accent (#58a6ff) is Avi's brand blue.
  - Tiles: Avi's BUILD / BRAND / LEARN are HIS worlds. These are
    sourajit-dey's real worlds with real links (see above). Tile
    links live in README.md (<a><img>), not inside the SVGs —
    links inside an SVG loaded as <img> are inert on GitHub.
  - Fonts: Avi embeds Instrument Serif + Geist (~18KB / <10KB).
    Those fonts are not on this machine, so this script subsets
    the LOCAL system fonts instead — DejaVu Serif (name) and
    Liberation Sans (body) — with pyftsubset, embedded as base64
    WOFF. If fontTools is missing, it falls back to a
    Georgia,serif / system sans stack and says so in the output.
  - Layout: the redesign REPLACES the terminal layout in the new
    README.md (as Avi did). The terminal trio
    (sourajit-dey-ascii.svg, info-card.svg, contrib-heatmap.svg
    green) is kept in the repo root for reference, not referenced
    by the new README.
  - Privacy / minimal (user corrections, HARD): name + Aspiring AI
    Engineer + building real AI systems + tech stack + repos only.
    No internship target date/place, no Project A/B plans or eval
    metrics, no roadmap/gates, no CGPA, no financial condition, no
    college/semester details, no full bio/goals section.
    Self-hosting/blog is only the BRAND tile + a small link at the
    bottom, NOT the hero. AI Engineer is the hero identity.

Usage:
  python scripts/render_readme_cards.py
  STATIC=1 python scripts/render_readme_cards.py   # frozen frames
  CARDS_DIR=verification/static-cards STATIC=1 python scripts/render_readme_cards.py
"""

import base64
import io
import json
import os
import re
import xml.sax.saxutils as sax

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "contributions.json")
ASCII = os.path.join(BASE, "sourajit-dey-ascii.svg")
CARDS_DIR = os.environ.get("CARDS_DIR") or os.path.join(BASE, "cards")

BG = "#0d1117"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
BRIGHT = "#e6edf3"
BLUE = "#58a6ff"
GREEN = "#39d353"
GREEN_DARK = "#26a641"

BLUE_PALETTE = ["#161b22", "#0e2a4a", "#1f6feb", "#388bfd", "#58a6ff", "#79c0ff"]

REPOS = [
    ("Ai-healthcare", "JavaScript", "#f1e05a", "Updated Mar 26, 2026"),
    ("DSA-Question-Practice", "Java", "#b07219", "Updated Apr 17, 2026"),
    ("forest-monitor", "Python", "#3572A5", "Updated Aug 20, 2026"),
    ("habit-tracker", "Dart", "#00B4AB", "Updated Jan 30, 2026"),
]

TILES = [
    # (file, word, number, label, sub, link)
    ("build.svg", "BUILD", 4, "featured repos", "AI · DSA · Python · apps",
     "https://github.com/sourajit-dey?tab=repositories"),
    ("brand.svg", "BRAND", 20, "blog posts", "@aitoday_hub · self-hosting blog",
     "https://selfhostingbeginners.blogspot.com"),
    ("learn.svg", "LEARN", 27, "active days", "DSA practice · Java",
     "https://github.com/sourajit-dey/DSA-Question-Practice"),
]


def esc(s):
    return sax.escape(str(s))


# ---------------------------------------------------------------- fonts
def embed_fonts(chars):
    """Subset local system fonts with pyftsubset, embed as base64 WOFF.
    Returns (css, ok). Falls back to font stacks if fontTools is absent."""
    try:
        from fontTools import subset
    except ImportError:
        print("[cards] fontTools not available — using system font stacks, "
              "no embedded fonts (deviation from Avi's embedded WOFF)")
        return [], False
    css = []
    for name, path, family in [
        ("Serif", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", "Serif"),
        ("SerifBold", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", "Serif"),
        ("Sans", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "Sans"),
        ("SansBold", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", "Sans"),
    ]:
        if not os.path.exists(path):
            print(f"[cards] font file missing: {path} — skipping {name}")
            continue
        opts = subset.Options()
        opts.flavor = "woff"
        font = subset.load_font(path, opts)
        sub = subset.Subsetter(options=opts)
        sub.populate(text="".join(sorted(set(chars))))
        sub.subset(font)
        buf = io.BytesIO()
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        weight = "700" if "Bold" in name else "400"
        css.append((family, weight,
            f"@font-face{{font-family:'{family}';font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff');}}"))
        print(f"[cards] embedded {name}: {len(b64)//1024} KB base64")
    return css, True


def motion_css(static):
    """Shared animation CSS; empty in STATIC mode, plus the
    prefers-reduced-motion guard Avi uses."""
    if static:
        return ""
    return (
        "<style>"
        "@keyframes rise{from{opacity:0;transform:translateY(10px)}"
        "to{opacity:1;transform:translateY(0)}}"
        ".rise{opacity:0;animation:rise .6s ease-out forwards}"
        "@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
        ".bar{transform:scaleY(0);transform-origin:bottom;"
        "transform-box:fill-box;animation:grow .5s ease-out forwards}"
        "@keyframes pop{from{opacity:0;transform:scale(.4)}"
        "to{opacity:1;transform:scale(1)}}"
        ".cell{opacity:0;transform:scale(.4);transform-box:fill-box;"
        "animation:pop .25s ease-out forwards}"
        "@keyframes pulse{0%,100%{opacity:.35}50%{opacity:1}}"
        ".ring{animation:pulse 2.4s ease-in-out infinite}"
        "@keyframes nudge{0%,100%{transform:translateX(0)}"
        "50%{transform:translateX(4px)}}"
        ".arrow{animation:nudge 1.6s ease-in-out infinite}"
        "@media (prefers-reduced-motion: reduce){"
        ".rise,.bar,.cell{animation:none;opacity:1;transform:none}"
        ".ring,.arrow{animation:none}}"
        "</style>"
    )


def font_css(*families):
    """Only the @font-face rules a card actually uses, so a tile
    does not carry the 23 KB serif it never renders."""
    if not families:
        return "".join(c for _f, _w, c in FONT_CSS)
    return "".join(c for f, w, c in FONT_CSS
                   if (f, w) in families or f in families)


FONT_CSS = []


# ---------------------------------------------------------------- hero
def ascii_rows_for_hero(static):
    """Extract the 106 row <text> elements + clipPaths from the chosen
    colour ASCII, rename clip-N -> hclip-N, drop the cursor rects.
    In STATIC mode the rows are emitted without clip/animate."""
    with open(ASCII, encoding="utf-8") as f:
        src = f.read()
    clips = re.findall(r'<clipPath id="clip-(\d+)">.*?</clipPath>', src)
    rows = re.findall(
        r'<text x="0" y="(\d+)" xml:space="preserve" clip-path="url\(#clip-(\d+)\)">(.*?)</text>',
        src, re.S)
    assert len(rows) == 106, f"expected 106 ASCII rows, got {len(rows)}"
    out = []
    for y, n, inner in rows:
        if static:
            out.append(
                f'<text x="0" y="{y}" xml:space="preserve">{inner}</text>')
        else:
            out.append(
                f'<clipPath id="hclip-{n}"><rect x="0" y="{int(y) - 10}" '
                f'width="0" height="10">'
                f'<animate attributeName="width" from="0" to="1200" '
                f'dur="0.6s" begin="{int(n) * 0.05:.2f}s" fill="freeze"/>'
                f"</rect></clipPath>"
            )
            out.append(
                f'<text x="0" y="{y}" xml:space="preserve" '
                f'clip-path="url(#hclip-{n})">{inner}</text>')
    return "".join(out)


def hero(data, static):
    total = data["total_contributions"]
    active = sum(1 for d in data["days"] if d["count"] > 0)
    best = data["best_day"]
    shine = "" if static else (
        '<animateTransform attributeName="gradientTransform" type="translate" '
        'values="-1.5 0; 1.5 0; 1.5 0" keyTimes="0;0.35;1" dur="4s" '
        'repeatCount="indefinite"/>'
    )
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="860" height="340" '
        f'viewBox="0 0 860 340" role="img" aria-label="Soura, Aspiring AI Engineer">',
        f'<rect width="860" height="340" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        "<defs>",
        '<linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">'
        '<stop offset="0" stop-color="#e6edf3"/>'
        '<stop offset="0.5" stop-color="#58a6ff"/>'
        '<stop offset="1" stop-color="#e6edf3"/>'
        f"{shine}</linearGradient></defs>",
        font_css(("Serif", "700"), ("Serif", "400"), ("Sans", "400")), motion_css(static),
        # ASCII portrait, printing in row by row, scaled 0.27x.
        '<g class="ascii" transform="translate(24,26) scale(0.27)">',
        # NOTE: scoped to .ascii — an unscoped text{font-size:10px} rule
        # would override the font-size attributes of the name/stats text.
        '<style>.ascii text{font-family:monospace;font-size:10px;}</style>',
        ascii_rows_for_hero(static),
        "</g>",
        # Name, rising line by line, shine sweep across "Soura".
        f'<text x="380" y="118" font-family="Serif, Georgia, serif" '
        f'font-size="64" font-weight="700" fill="url(#shine)" '
        f'class="rise" style="animation-delay:0.15s">Soura</text>',
        f'<text x="382" y="152" font-family="monospace" font-size="20" '
        f'fill="{BLUE}" class="rise" style="animation-delay:0.45s">'
        f"sourajit-dey</text>",
        f'<text x="382" y="192" font-family="Sans, sans-serif" font-size="22" '
        f'fill="{BRIGHT}" class="rise" style="animation-delay:0.75s">'
        f"Aspiring AI Engineer</text>",
        f'<text x="382" y="222" font-family="Sans, sans-serif" font-size="16" '
        f'fill="{MUTED}" class="rise" style="animation-delay:1.05s">'
        f"building real AI systems</text>",
        f'<line x1="382" y1="248" x2="836" y2="248" stroke="{BORDER}"/>',
        f'<text x="382" y="282" font-family="monospace" font-size="14" '
        f'fill="{TEXT}" class="rise" style="animation-delay:1.35s">'
        f"{total} contributions · {active} active days</text>",
        f'<text x="382" y="308" font-family="monospace" font-size="14" '
        f'fill="{TEXT}" class="rise" style="animation-delay:1.6s">'
        f"best day {best['contributions']} on 20 Aug 2026</text>",
        "</svg>",
    ]
    # In static mode the rise class has no CSS, so text is visible.
    return "\n".join(parts)


# ------------------------------------------------------- blue heatmap
def heatmap_blue(data, static):
    days = sorted(data["days"], key=lambda d: d["date"])
    total = data["total_contributions"]
    from datetime import date
    start = date.fromisoformat(days[0]["date"])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="860" height="184" '
        f'viewBox="0 0 860 184" role="img" aria-label="Contribution graph: '
        f'{total} contributions in the last year">',
        f'<rect width="860" height="184" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        font_css(("Sans", "400")), motion_css(static),
    ]
    month_at_week = {}
    for d in days:
        dt = date.fromisoformat(d["date"])
        week = (dt - start).days // 7
        key = dt.strftime("%Y-%m")
        if key not in month_at_week:
            month_at_week[key] = (week, dt.strftime("%b"))
    for week, label in month_at_week.values():
        parts.append(
            f'<text x="{12 + week * 16}" y="18" font-family="sans-serif" '
            f'font-size="11" fill="{MUTED}">{label}</text>')
    for d in days:
        dt = date.fromisoformat(d["date"])
        offset = (dt - start).days
        week, row = divmod(offset, 7)
        x, y = 12 + week * 16, 28 + row * 16
        fill = BLUE_PALETTE[min(max(d["level"], 0), 5)]
        delay = week * 0.025 + row * 0.008
        cls = "" if static else ' class="cell"'
        style = "" if static else f' style="animation-delay:{delay:.2f}s"'
        parts.append(
            f'<rect x="{x}" y="{y}" width="13" height="13" rx="3" '
            f'fill="{fill}"{cls}{style}>'
            f"<title>{d['count']} contributions on {d['date']}</title></rect>")
    lx, ly = 860 - 170, 184 - 22
    parts.append(
        f'<text x="{lx}" y="{ly + 9}" font-family="sans-serif" font-size="11" '
        f'fill="{MUTED}">Less</text>')
    for i, fill in enumerate(BLUE_PALETTE[:5]):
        parts.append(
            f'<rect x="{lx + 34 + i * 16}" y="{ly}" width="11" height="11" '
            f'rx="2" fill="{fill}"/>')
    parts.append(
        f'<text x="{lx + 34 + 5 * 16 + 4}" y="{ly + 9}" font-family="sans-serif" '
        f'font-size="11" fill="{MUTED}">More</text>')
    parts.append(
        f'<text x="12" y="171" font-family="monospace" font-size="13" '
        f'fill="{TEXT}">{total} contributions in the last year</text>')
    parts.append("</svg>")
    return "\n".join(parts)


# ------------------------------------------------------- monthly bars
def activity(data, static):
    months = data["monthly_totals"]
    keys = sorted(months)  # 2025-11 .. 2026-11
    from datetime import date
    labels = [date.fromisoformat(k + "-01").strftime("%b") for k in keys]
    values = [months[k] for k in keys]
    best_i = values.index(max(values))
    best = max(values)
    W, H = 860, 250
    base_y, max_h = 190, 130
    bw, gap, left = 44, 18, 36
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="Monthly contributions">',
        f'<rect width="{W}" height="{H}" rx="8" fill="{BG}" stroke="{BORDER}"/>',
        font_css(("Sans", "700"), ("Sans", "400")), motion_css(static),
        f'<text x="24" y="30" font-family="Sans, sans-serif" font-size="15" '
        f'font-weight="700" fill="{BRIGHT}">Contributions per month</text>',
        f'<line x1="{left}" y1="{base_y}" x2="{W - 24}" y2="{base_y}" '
        f'stroke="{BORDER}"/>',
    ]
    for i, (lab, v) in enumerate(zip(labels, values)):
        x = left + i * (bw + gap)
        h = round(v / best * max_h) if best else 0
        y = base_y - h
        fill = BLUE if i == best_i else GREEN_DARK
        cls = "" if static else ' class="bar"'
        style = "" if static else f' style="animation-delay:{0.2 + i * 0.07:.2f}s"'
        parts.append(
            f'<rect x="{x}" y="{y}" width="{bw}" height="{h}" rx="4" '
            f'fill="{fill}"{cls}{style}/>')
        if i == best_i:
            parts.append(
                f'<text x="{x + bw / 2}" y="{y - 8}" text-anchor="middle" '
                f'font-family="monospace" font-size="14" font-weight="700" '
                f'fill="{BLUE}" class="rise" style="animation-delay:1.2s">'
                f"{v}</text>")
        parts.append(
            f'<text x="{x + bw / 2}" y="{base_y + 18}" text-anchor="middle" '
            f'font-family="sans-serif" font-size="11" fill="{MUTED}">{lab}</text>')
    best_date = data["best_day"]["date"]
    stats = (f"Longest streak {data['longest_streak_days']} days  ·  "
             f"Active days {sum(1 for d in data['days'] if d['count'] > 0)}  ·  "
             f"Busiest day {data['best_day']['contributions']} on 20 Aug 2026")
    parts.append(
        f'<text x="24" y="232" font-family="monospace" font-size="13" '
        f'fill="{TEXT}">{stats}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


# ---------------------------------------------------------------- tiles
def countup_texts(x, y, value, delay, static):
    """18 SMIL <set> frames counting 0 -> value, then freezing on value."""
    if static:
        return (f'<text x="{x}" y="{y}" font-family="Sans, sans-serif" '
                f'font-size="40" font-weight="700" fill="{BRIGHT}">{value}</text>')
    step = 0.09
    out = []
    for i in range(18):
        v = round(value * i / 17)
        begin = delay + i * step
        dur = step if i < 17 else "indefinite"
        out.append(
            f'<text x="{x}" y="{y}" font-family="Sans, sans-serif" '
            f'font-size="40" font-weight="700" fill="{BRIGHT}" '
            f'visibility="hidden">{v}'
            f'<set attributeName="visibility" to="visible" '
            f'begin="{begin:.2f}s" dur="{dur if isinstance(dur, str) else f"{dur:.2f}s"}" '
            f'fill="freeze"/>'
            + (f'<set attributeName="visibility" to="hidden" '
               f'begin="{begin + step:.2f}s" fill="freeze"/>' if i < 17 else "")
            + "</text>")
    return "".join(out)


def tile(word, value, label, sub, static, delay=0.2):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="278" height="150" '
        f'viewBox="0 0 278 150" role="img" aria-label="{word}: {value} {label}">',
        f'<rect x="0.5" y="0.5" width="277" height="149" rx="8" fill="{BG}" '
        f'stroke="{BORDER}"/>',
        font_css(("Sans", "700"), ("Sans", "400")), motion_css(static),
        # pulsing ring, top right
        f'<circle cx="242" cy="30" r="16" fill="none" stroke="{BLUE}" '
        f'stroke-width="2" class="ring"/>',
        f'<circle cx="242" cy="30" r="5" fill="{BLUE}"/>',
        f'<text x="20" y="34" font-family="monospace" font-size="13" '
        f'font-weight="700" fill="{BLUE}">{word}</text>',
        countup_texts(20, 88, value, delay, static),
        f'<text x="20" y="114" font-family="Sans, sans-serif" font-size="14" '
        f'fill="{TEXT}">{esc(label)}</text>',
        f'<text x="20" y="136" font-family="Sans, sans-serif" font-size="12" '
        f'fill="{MUTED}">{esc(sub)}</text>',
        # Arrow drawn as a path, not the "→" character: the character
        # rendered as tofu in the local renderer (missing glyph), while
        # a path renders everywhere.
        f'<path d="M244 130 h14 M254 124 l6 6 -6 6" stroke="{BLUE}" '
        f'stroke-width="2" fill="none" stroke-linecap="round" '
        f'stroke-linejoin="round" class="arrow"/>',
        "</svg>",
    ]
    return "\n".join(parts)


# ------------------------------------------------------------ repo cards
def repo_card(name, lang, dot, updated, static):
    slug = name.lower().replace("_", "-")
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="110" '
        f'viewBox="0 0 420 110" role="img" aria-label="Repository {name}">',
        f'<rect x="0.5" y="0.5" width="419" height="109" rx="8" fill="{BG}" '
        f'stroke="{BORDER}"/>',
        font_css(("Sans", "400")), motion_css(static),
        f'<text x="20" y="36" font-family="monospace" font-size="16" '
        f'font-weight="700" fill="{BLUE}" class="rise" '
        f'style="animation-delay:0.1s">{esc(name)}</text>',
        f'<text x="20" y="62" font-family="Sans, sans-serif" font-size="13" '
        f'fill="{TEXT}" class="rise" style="animation-delay:0.3s">'
        f"github.com/sourajit-dey/{esc(name)}</text>",
        f'<circle cx="26" cy="88" r="5" fill="{dot}"/>',
        f'<text x="38" y="92" font-family="Sans, sans-serif" font-size="12" '
        f'fill="{MUTED}">{esc(lang)}</text>',
        f'<text x="150" y="92" font-family="Sans, sans-serif" font-size="12" '
        f'fill="{MUTED}">{esc(updated)}</text>',
        "</svg>",
    ]
    return "\n".join(parts)


# ---------------------------------------------------------------- main
def main():
    static = os.environ.get("STATIC") == "1"
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    # Characters used across all cards, for font subsetting.
    all_text = (
        "Soura sourajit-dey Aspiring AI Engineer building real AI systems "
        "0123456789 contributions active days best day on Aug 20 2026 "
        "Contributions per month Longest streak Busiest day "
        "Nov Dec Jan Feb Mar Apr May Jun Jul Aug Sep Oct Less More "
        "BUILD BRAND LEARN featured repos blog posts @aitoday_hub "
        "self-hosting blog DSA practice Java AI Python apps "
        "Ai-healthcare DSA-Question-Practice forest-monitor habit-tracker "
        "JavaScript Dart Updated Mar Apr Aug Jan 26 2026 "
        "github.com/sourajit-dey/ →·—"
    )
    global FONT_CSS
    FONT_CSS, ok = embed_fonts(all_text)
    os.makedirs(CARDS_DIR, exist_ok=True)
    out = {}
    out["hero.svg"] = hero(data, static)
    out["heatmap-blue.svg"] = heatmap_blue(data, static)
    out["activity.svg"] = activity(data, static)
    for fname, word, value, label, sub, _link in TILES:
        out[fname] = tile(word, value, label, sub, static)
    for name, lang, dot, updated in REPOS:
        slug = "repo-" + name.lower().replace("_", "-") + ".svg"
        out[slug] = repo_card(name, lang, dot, updated, static)
    for fname, svg in out.items():
        path = os.path.join(CARDS_DIR, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg + "\n")
        print(f"[cards] wrote {path} ({len(svg)//1024} KB, "
              f"{'STATIC' if static else 'animated'}, fonts_embedded={ok})")
    # Honest checks.
    for fname, svg in out.items():
        assert "<script" not in svg, f"{fname} contains <script>"
        assert svg.startswith("<svg"), fname
    total = data["total_contributions"]
    assert str(total) in out["hero.svg"] and str(total) in out["heatmap-blue.svg"]
    print(f"[cards] all {len(out)} cards valid, 0 <script>, total={total}")


if __name__ == "__main__":
    main()
