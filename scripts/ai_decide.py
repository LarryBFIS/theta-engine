"""
Phase 5 entry script — called by GitHub Actions every 15 min.

Wires together:
  - Read current positions from gist (where poll.py writes them)
  - Fetch market state
  - Call AI trader (Claude)
  - Push high-confidence actions to Pushover
  - Persist state for dedup

Designed to run AFTER scripts/poll.py so the gist has fresh data.
"""
import os
import sys
import json
import urllib.request
from datetime import datetime, timezone

from monitor.market_state import fetch_market_state
from monitor.ai_trader import decide, should_alert, update_state, load_state
from monitor.notifier import send  # existing module


def fetch_gist_state(gist_id: str, github_token: str) -> dict:
    """Pull last_poll.json from the gist."""
    url = f"https://api.github.com/gists/{gist_id}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {github_token}",
        "Accept": "application/vnd.github+json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        gist = json.loads(resp.read())
    content = gist["files"]["last_poll.json"]["content"]
    return json.loads(content)


def extract_positions(gist_state: dict) -> list:
    """Convert gist position format to ai_trader input format."""
    positions = []
    for p in gist_state.get("positions", []):
        positions.append({
            "symbol": p.get("symbol", p.get("trade_name", "UNKNOWN")),
            "expiry": p.get("expiry"),
            "dte": p.get("dte"),
            "credit": p.get("credit"),
            "current_mid_cost": p.get("cost_mid"),
            "current_worst_cost": p.get("cost_worst"),
            "pct_captured_mid": p.get("pct_captured_mid"),
            "pct_captured_worst": p.get("pct_captured_worst"),
            "pnl_mid": p.get("pnl_mid"),
            "pnl_worst": p.get("pnl_worst"),
            "underlying_price": p.get("underlying_price"),
            "short_strike": p.get("short_strike"),
            "long_strike": p.get("long_strike"),
            "buffer_pct": p.get("buffer_pct"),
            "has_live_quotes": p.get("has_live_quotes", False),
        })
    return positions


def extract_account(gist_state: dict) -> dict:
    """Pull account-level metrics from gist."""
    return {
        "net_liq": gist_state.get("net_liq"),
        "day_pnl": gist_state.get("day_pnl", 0),
        "bpr_used": gist_state.get("bpr_used", 0),
        "bpr_pct": gist_state.get("bpr_pct", 0),
        "cash": gist_state.get("cash"),
        "starting_capital": gist_state.get("starting_capital"),
        "strategy_pnl": gist_state.get("strategy_pnl", 0),
    }


def format_pushover_message(alerts: list, decision: dict) -> tuple:
    """Build Pushover title + body from AI decision."""
    n = len(alerts)
    has_critical = any(a["action"] == "CRITICAL" for a in alerts)

    if has_critical:
        title = f"🚨 CRITICAL: {n} position{'s' if n > 1 else ''}"
        priority = 1  # high priority pushover
    else:
        title = f"⚠️ ACTION: {n} position{'s' if n > 1 else ''}"
        priority = 0  # normal

    body_lines = []
    for a in alerts:
        body_lines.append(f"\n• {a['symbol']} → {a['action']}")
        body_lines.append(f"  {a['reasoning']}")
        if a.get("recommendation"):
            body_lines.append(f"  DO: {a['recommendation']}")

    if decision.get("macro_concerns"):
        body_lines.append(f"\n📊 {decision['macro_concerns']}")

    if decision.get("new_setups_flagged"):
        body_lines.append(f"\n💡 New setup: {decision['new_setups_flagged']}")

    body = "\n".join(body_lines)
    return title, body, priority


def main():
    print(f"[ai_decide] starting at {datetime.now(timezone.utc).isoformat()}")

    # 1. Read gist (poll.py wrote it 2 minutes ago)
    gist_id = os.environ["GIST_ID"]
    github_token = os.environ["GIST_TOKEN"]
    try:
        gist_state = fetch_gist_state(gist_id, github_token)
    except Exception as e:
        print(f"[ai_decide] FAIL gist fetch: {e}", file=sys.stderr)
        sys.exit(0)  # exit clean — don't break workflow

    positions = extract_positions(gist_state)
    account = extract_account(gist_state)

    if not positions:
        print("[ai_decide] no open positions, skipping AI call")
        return

    print(f"[ai_decide] {len(positions)} positions, fetching market state...")

    # 2. Market state
    try:
        market_state = fetch_market_state()
    except Exception as e:
        print(f"[ai_decide] market_state fetch failed (continuing): {e}")
        market_state = {"error": str(e)}

    # 3. Load dedup state
    last_state = load_state()

    # 4. Call Claude
    print("[ai_decide] calling Claude...")
    decision = decide(
        positions=positions,
        market_state=market_state,
        account_state=account,
        last_recommendations=last_state,
    )

    if "error" in decision:
        print(f"[ai_decide] decision error: {decision['error']}", file=sys.stderr)
        return

    print(f"[ai_decide] decision received: {decision.get('market_view', '')[:80]}")
    in_tok = decision.get("_input_tokens", 0)
    out_tok = decision.get("_output_tokens", 0)
    cost_est = (in_tok * 3 / 1_000_000) + (out_tok * 15 / 1_000_000)
    print(f"[ai_decide] tokens in/out: {in_tok}/{out_tok} (~${cost_est:.4f})")

    for pos in decision.get("positions", []):
        print(f"[ai_decide]   {pos['symbol']}: {pos['action']} ({pos.get('confidence', 0):.0%}) — {pos.get('reasoning', '')[:80]}")

    # 5. Determine alerts
    alerts = should_alert(decision, last_state, dedupe_hours=4)

    if alerts:
        print(f"[ai_decide] PUSHING {len(alerts)} alert(s)")
        title, body, priority = format_pushover_message(alerts, decision)
        try:
            send(title=title, message=body, priority=priority)
            print(f"[ai_decide] pushover sent: {title}")
        except Exception as e:
            print(f"[ai_decide] pushover FAIL: {e}", file=sys.stderr)
    else:
        print("[ai_decide] no alerts to push (all HOLD/WATCH or deduped)")

    # 6. Persist state
    update_state(decision)
    print("[ai_decide] state updated, done")


if __name__ == "__main__":
    main()
