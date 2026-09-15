"""
ESPN Fantasy Football - Median Bonus Win/Loss Tracker

Fetches the current week's live scores from your ESPN fantasy league,
calculates the median score, and generates an HTML page showing who
is currently above/below median (i.e., who's on track for the bonus
win or bonus loss).

This is meant to be run automatically (e.g. via GitHub Actions) every
10-15 minutes during game windows, and outputs index.html which is
served by GitHub Pages.
"""

import os
import statistics
from datetime import datetime, timezone
from espn_api.football import League

# ---- Configuration (pulled from environment variables / GitHub Secrets) ----
LEAGUE_ID = int(os.environ["LEAGUE_ID"])
YEAR = int(os.environ["YEAR"])
ESPN_S2 = os.environ["ESPN_S2"]
SWID = os.environ["SWID"]

OUTPUT_FILE = "index.html"


def get_current_scores(league: League):
    """Return a list of (team_name, score) tuples for the current live week."""
    box_scores = league.box_scores()
    scores = []
    for game in box_scores:
        # Some weeks (e.g. bye weeks) may have a missing home or away team
        if game.home_team:
            scores.append((game.home_team.team_name, game.home_score))
        if game.away_team:
            scores.append((game.away_team.team_name, game.away_score))
    return scores


def build_html(scores, median, week, updated_at):
    # Sort numerically, highest score first
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)

    rows = ""
    for team_name, score in sorted_scores:
        if score > median:
            badge = '<span class="badge win">Bonus Win</span>'
            row_class = "above"
        elif score < median:
            badge = '<span class="badge loss">Bonus Loss</span>'
            row_class = "below"
        else:
            badge = '<span class="badge tie">Tied at Median</span>'
            row_class = "tie"

        rows += f"""
        <tr class="{row_class}">
            <td>{team_name}</td>
            <td class="score">{score:.2f}</td>
            <td>{badge}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Fantasy Football Median Tracker - Week {week}</title>
<style>
    body {{
        font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif;
        background: #0f1115;
        color: #e6e6e6;
        max-width: 700px;
        margin: 40px auto;
        padding: 0 20px;
    }}
    h1 {{
        font-size: 1.5rem;
        margin-bottom: 0;
    }}
    .subtitle {{
        color: #9aa0a6;
        margin-top: 4px;
        margin-bottom: 20px;
        font-size: 0.9rem;
    }}
    .median-box {{
        background: #1b1e26;
        border: 1px solid #2a2e38;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 24px;
        font-size: 1.1rem;
    }}
    .median-box strong {{
        color: #7fd1a8;
        font-size: 1.4rem;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        background: #1b1e26;
        border-radius: 10px;
        overflow: hidden;
    }}
    th, td {{
        padding: 12px 14px;
        text-align: left;
    }}
    th {{
        background: #23272f;
        font-size: 0.8rem;
        text-transform: uppercase;
        color: #9aa0a6;
    }}
    td.score {{
        font-variant-numeric: tabular-nums;
        font-weight: 600;
    }}
    tr.above td.score {{ color: #7fd1a8; }}
    tr.below td.score {{ color: #e08585; }}
    .badge {{
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }}
    .badge.win {{ background: rgba(127,209,168,0.15); color: #7fd1a8; }}
    .badge.loss {{ background: rgba(224,133,133,0.15); color: #e08585; }}
    .badge.tie {{ background: rgba(200,200,120,0.15); color: #cfcf7a; }}
    .footer {{
        margin-top: 20px;
        font-size: 0.75rem;
        color: #666b73;
        text-align: center;
    }}
</style>
</head>
<body>
    <h1>Median Bonus Tracker</h1>
    <div class="subtitle">Week {week} &middot; live scores</div>

    <div class="median-box">
        Current median score: <strong>{median:.2f}</strong>
    </div>

    <table>
        <thead>
            <tr>
                <th>Team</th>
                <th>Score</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>

    <div class="footer">Last updated {updated_at} UTC &middot; auto-refreshes every ~15 min</div>
</body>
</html>
"""
    return html


def main():
    league = League(league_id=LEAGUE_ID, year=YEAR, espn_s2=ESPN_S2, swid=SWID)
    scores = get_current_scores(league)

    if not scores:
        print("No scores found (bye week or offseason?). Skipping HTML update.")
        return

    values = [s for _, s in scores]
    median = statistics.median(values)
    week = league.current_week
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")

    html = build_html(scores, median, week, updated_at)

    with open(OUTPUT_FILE, "w") as f:
        f.write(html)

    print(f"Updated {OUTPUT_FILE}: week {week}, median {median:.2f}, {len(scores)} teams")


if __name__ == "__main__":
    main()
