"""
Phase 5 entry script — called by GitHub Actions every 15 min.

Wires together:
  - Read current trades from gist (where poll.py writes them)
  - Fetch market state
  - Call AI trader (Claude)
  - Push high-confidence actions to Pushover
  - Persist state for dedup
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


def build_symbol(t: dict) -> str:
    """Construct human-readable symbol from trade fields."""
    underlying = t.get("underlying", "?")
    short = t.get("short_strike", "?")
    long = t.get("long_strike", "?")
    structure = t.get("structure", "")
    # Short put vertical → "SPY 721/716p"
    suffix = "p" if "put" in structure else ("c" if "call" in structure else "")
    return f"{underlying} {short}/{long}{suffix}"


def extract_positions(gist_state: dict) -> list:
    """Convert gist trade format to ai_trader input format. Filters out closed/unmatched trades."""
    positions = []
    for t in gist_state.get("trades", []):
        metrics = t.get("metrics", {})
        # Skip if not active in broker (likely closed)
        if not metrics.get("is_matched", False):
            continue
        cost = metrics.get("cost_to_close", {})
        positions.append({
            "symbol": build_symbol(t),
            "expiry": t.get("expiry"),
            "dte": metrics.get("dte"),
            "credit": t.get("credit_per_contract"),
            "current_mid_cost": cost.get("mid"),
            "current_worst_cost": cost.get("worst_case"),
            "max_profit": t.get("max_profit_total"),
            "max_loss": t.get("max_loss_total"),
            "bpr": t.get("bpr_total"),
            "underlying_price": metrics.get("underlying_price"),
            "short_strike": t.get("short_strike"),
            "long_strike": t.get("long_strike"),
            "short_strike_distance_pct": metrics.get("short_strike_distance_pct"),
            "short_strike_breached": metrics.get("short_strike_breached"),
            "has_live_quotes": metrics.get("has_live_quotes", False),
            "opened_at": t.get("opened_at"),
            "exit_dte_rule": t.get("exit_dte", 21),
            "manage_at_pct_rule": t.get("manage_at_pct", 0.5),
        })
    return positions


def extract_account(gist_state: dict) -> dict:
    """Pull account-level metrics from gist."""
    acct = gist_state.get("account", {})
    return {
        "net_liq": acct.get("net_liquidating_value"),
        "day_pnl": acct.get("day_pnl", 0),
        "cash": acct.get("cash_balance"),
        "derivative_bp": acct.get("derivative_buying_power"),
        "starting_capital": acct.get("starting_capital"),
        "cumulative_pnl": acct.get("cumulative_pnl", 0),
        "cumulative_pct": acct.get("cumulative_pct", 0),
        "last_poll_at": gist_state.get("last_poll_at"),
    }


def format_pushover_message(alerts: list, decision: dict) -> tuple:
    """Build Pushover title + body from AI decision."""
    n = len(alerts)
    has_critical = any(a["action"] == "CRITICAL" for a in alerts)
    if has_critical:
        title = f"CRITICAL: {n} position{'s' if n > 1 else ''}"
        priority = 1
    else:
        title = f"ACTION: {n} position{'s' if n > 1 else ''}"
        priority = 0
    body_lines = []
    for a in alerts:
        body_lines.append(f"\n• {a['symbol']} → {a['action']}")
        body_lines.append(f"  {a['reasoning']}")
        if a.get("recommendation"):
            body_lines.append(f"  DO: {a['recommendation']}")
    if decision.get("macro_concerns"):
        body_lines.append(f"\n{decision['macro_concerns']}")
    if decision.get("new_setups_flagged"):
        body_lines.append(f"\nNew setup: {decision['new_setups_flagged']}")
    return title, "\n".join(body_lines), priority


def main():
    print(f"[ai_decide] starting at {datetime.now(timezone.utc).isoformat()}")
    gist_id = os.environ["GIST_ID"]
    github_token = os.environ["GIST_TOKEN"]
    try:
        gist_state = fetch_gist_state(gist_id, github_token)
    except Exception as e:
        print(f"[ai_decide] FAIL gist fetch: {e}", file=sys.stderr)
        sys.exit(0)

    positions = extract_positions(gist_state)
    account = extract_account(gist_state)

    print(f"[ai_decide] gist last_poll_at: {account.get('last_poll_at')}")
    print(f"[ai_decide] account: net_liq=${account.get('net_liq')}, cum_pnl=${account.get('cumulative_pnl')}")
    print(f"[ai_decide] trades in gist: {len(gist_state.get('trades', []))}, active (matched): {len(positions)}")

    if not positions:
        print("[ai_decide] no active positions, skipping AI call")
        return

    for p in positions:
        print(f"[ai_decide]   {p['symbol']} dte={p['dte']} mid_cost={p['current_mid_cost']}")

    try:
        market_state = fetch_market_state()
    except Exception as e:
        print(f"[ai_decide] market_state fetch failed (continuing): {e}")
        market_state = {"error": str(e)}

    last_state = load_state()

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

    print(f"[ai_decide] market_view: {decision.get('market_view', '')[:100]}")
    in_tok = decision.get("_input_tokens", 0)
    out_tok = decision.get("_output_tokens", 0)
    cost_est = (in_tok * 3 / 1_000_000) + (out_tok * 15 / 1_000_000)
    print(f"[ai_decide] tokens in/out: {in_tok}/{out_tok} (~${cost_est:.4f})")

    for pos in decision.get("positions", []):
        print(f"[ai_decide]   {pos['symbol']}: {pos['action']} ({pos.get('confidence', 0):.0%}) — {pos.get('reasoning', '')[:80]}")

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

    update_state(decision)
    print("[ai_decide] state updated, done")


if __name__ == "__main__":
    main()
