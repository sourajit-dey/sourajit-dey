"""Step 5a from Avi Vashishta's guide (18 Jul 2026):
"How I Built an Animated GitHub Profile README".

You don't need the GraphQL API or a personal access token.
GitHub serves your contribution calendar as public HTML at
`https://github.com/users/<username>/contributions` — the same
fragment the profile page itself uses. Fetch it with `requests`,
parse the day cells with BeautifulSoup, and write
`data/contributions.json` with raw days plus derived stats
(current streak, longest streak, best day, monthly totals).

Page structure as served on 2026-11-16 (verified by curl):
  - <h2> "150 contributions in the last year" (cross-check total)
  - <td class="ContributionCalendar-day" data-date="YYYY-MM-DD"
    data-level="0..4" id="contribution-day-component-W-D">
  - <tool-tip for="contribution-day-component-W-D">
    "19 contributions on August 20th." / "No contributions on …"

No token, no JavaScript, no invented numbers: the JSON total
must equal the sum of the parsed days and the page's own total.
"""

import json
import os
import re
import sys
from collections import defaultdict
from datetime import date

import requests
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "data", "contributions.json")
USERNAME = "sourajit-dey"
URL = f"https://github.com/users/{USERNAME}/contributions"


def parse_count(text):
    text = (text or "").strip()
    if text.startswith("No contributions"):
        return 0
    m = re.match(r"(\d+) contribution", text)
    return int(m.group(1)) if m else None


def streaks(days):
    """days: list of (date, count) sorted ascending.
    current_streak: consecutive contributing days ending on the most
    recent contributing day. longest_streak: longest such run."""
    by_date = dict(days)
    sorted_dates = sorted(by_date)
    longest = run = 0
    prev = None
    for d in sorted_dates:
        if by_date[d] > 0 and prev is not None and (d - prev).days == 1:
            run += 1
        elif by_date[d] > 0:
            run = 1
        else:
            run = 0
        longest = max(longest, run)
        prev = d
    # Current streak: walk backwards from the last contributing day.
    last_active = max((d for d, c in days if c > 0), default=None)
    current = 0
    if last_active is not None:
        d = last_active
        while by_date.get(d, 0) > 0:
            current += 1
            d = date.fromordinal(d.toordinal() - 1)
    return current, longest, last_active


def main():
    resp = requests.get(
        URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    page_total = None
    h2 = soup.find("h2", id="js-contribution-activity-description")
    if h2:
        m = re.search(r"(\d+)\s+contributions", h2.get_text())
        page_total = int(m.group(1)) if m else None

    tips = {}
    for tip in soup.find_all("tool-tip"):
        target = tip.get("for")
        if target:
            tips[target] = tip.get_text(strip=True)

    days = []
    for cell in soup.find_all("td", class_="ContributionCalendar-day"):
        d = date.fromisoformat(cell["data-date"])
        level = int(cell.get("data-level", 0))
        count = parse_count(tips.get(cell.get("id", ""), ""))
        if count is None:
            print(f"[fetch] WARNING: no tooltip count for {d}, "
                  f"using level as fallback (level={level})")
            count = level  # last-resort fallback, never silent
        days.append((d, count, level))

    days.sort()
    total = sum(c for _, c, _ in days)
    if page_total is not None and total != page_total:
        print(f"[fetch] WARNING: parsed total {total} != "
              f"page total {page_total}")
    else:
        print(f"[fetch] total verified: {total} contributions "
              f"(page says {page_total})")

    monthly = defaultdict(int)
    for d, c, _ in days:
        monthly[d.strftime("%Y-%m")] += c
    best = max(days, key=lambda x: x[1])
    current, longest, last_active = streaks([(d, c) for d, c, _ in days])

    data = {
        "username": USERNAME,
        "source_url": URL,
        "from": days[0][0].isoformat() if days else None,
        "to": days[-1][0].isoformat() if days else None,
        "total_contributions": total,
        "page_total_contributions": page_total,
        "current_streak_days": current,
        "longest_streak_days": longest,
        "last_contribution_date": (
            last_active.isoformat() if last_active else None
        ),
        "best_day": {
            "date": best[0].isoformat(),
            "contributions": best[1],
        },
        "monthly_totals": dict(sorted(monthly.items())),
        "days": [
            {"date": d.isoformat(), "count": c, "level": lv}
            for d, c, lv in days
        ],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"[fetch] wrote {OUT}: {len(days)} days, total={total}, "
          f"current_streak={current}, longest={longest}, "
          f"best={best[1]} on {best[0]}")


if __name__ == "__main__":
    main()
