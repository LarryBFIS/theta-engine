"""
scripts/briefing.py — Daily intel briefing entry point.

Pulls intel payload, sends to Anthropic API for synthesis,
saves briefing to repo, pushes to Pushover.
"""

import json
import os
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from monitor.intel import build_intel_payload  # noqa: E402

import anthropic  # noqa: E402
import requests  # noqa: E402

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
PUSHOVER_USER_KEY = os.environ.get("PUSHOVER_USER_KEY")
PUSHOVER_APP_TOKEN = os.environ.get("PUSHOVER_APP_TOKEN")
STARTING_CAPITAL = float(os.environ.get("STARTING_CAPITAL", "3389.91"))

SYSTEM_PROMPT = """You are a Wall-Street-grade options strategist for a small account ($3,400 net liq) running a 30-day short-premium experiment.

Owner's rules (non-negotiable):
- Defined-risk only (verticals, no naked)
- 30-60 DTE preferred (45 DTE sweet spot)
- POP >= 70%, credit >= $1.00 on 5-wide minimum
- Manage at 50% of max profit mechanically
- 21 DTE hard exit
- Max 3 concurrent positions
- BPR utilization 35-50% of net liq
- AVOID earnings inside trade window
- Penalize high IV (>50% = blowup risk territory)
- Large-cap preferred

Voice: tastytrade native (BPR, POP, P50, manage at 50%, DTE, short put vertical).
Concise. No fluff. Direct.

Task: Given today's intel payload, produce a daily briefing under 1200 characters total.

Output structure (use these exact headers):

TAKEAWAY: [one sentence — what's the day's big picture?]

POSITIONS: [any news/catalysts hitting open trades? If nothing material: "No material news."]

TOP 3 SETUPS:
1. TICKER — short put vertical, suggested expiry & delta. Why now (1 sentence).
2. ...
3. ...

AVOID TODAY: [tickers with recent bearish catalysts, earnings in window, or blowup risk — comma-separated with 2-word reason each]

KEY DATES: [macro/earnings inside next 30 days that matter]

If you cannot recommend 3 setups (e.g. broad market mess), recommend fewer and say why."""


def synthesize_briefing(payload):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Today's intel payload:\n\n{json.dumps(payload, indent=2, default=str)}\n\nGenerate today's briefing.",
        }],
    )
    return message.content[0].text


def push_to_pushover(title, message):
    if not (PUSHOVER_USER_KEY and PUSHOVER_APP_TOKEN):
        print("Pushover not configured, skipping push")
        return
    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_APP_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "title": title,
            "message": message[:1024],
            "priority": 0,
        },
        timeout=15,
    )
    response.raise_for_status()


def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    print("Building intel payload...")
    payload = build_intel_payload()
    print(f"  - {len(payload['ticker_data'])} tickers")
    print(f"  - {len(payload['upcoming_macro'])} macro events ahead")
    print(f"  - {len(payload['earnings_in_window'])} earnings inside 45 days")

    print("\nSynthesizing briefing via Claude...")
    briefing = synthesize_briefing(payload)

    print("\n=== BRIEFING ===\n")
    print(briefing)
    print("\n================\n")

    # Save to repo
    briefing_dir = REPO_ROOT / "briefings"
    briefing_dir.mkdir(exist_ok=True)
    today_str = date.today().isoformat()
    (briefing_dir / f"{today_str}.txt").write_text(briefing)
    print(f"Saved to briefings/{today_str}.txt")

    # Push to phone
    push_to_pushover(f"Theta Engine Briefing {today_str}", briefing)
    print("Pushed to Pushover ✓")


if __name__ == "__main__":
    main()
