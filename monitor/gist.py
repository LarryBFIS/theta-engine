"""Push diagnostic state snapshots to a GitHub Gist.

Captures the bot's full decision-making state after each poll/summary:
  - Account state (net liq, P&L)
  - Per-trade metrics (mid + worst-case close costs, %captured at mid)
  - Per-trade recommendation with reasoning
  - Raw position data including bid/ask/mark from the live quote fetch

Set GIST_ID and GIST_TOKEN as repo secrets to enable. Silently no-ops if
those aren't both set, so the rest of the system keeps working.
"""
import json
import logging
from typing import Optional

import requests

from monitor import config

log = logging.getLogger(__name__)

GIST_API = "https://api.github.com/gists"


def _build_snapshot(
    trigger: str,
    timestamp_et,
    snapshot,
    trade_results: list,
) -> dict:
    starting = config.STARTING_CAPITAL
    current = snapshot.net_liquidating_value
    cum_pnl = current - starting

    trades_block = []
    for tr in trade_results:
        trade = tr["trade"]
        m = tr["metrics"]
        rec = tr["recommendation"]
        trades_block.append({
            "id": trade.id,
            "underlying": trade.underlying,
            "structure": trade.structure,
            "short_strike": trade.short_strike,
            "long_strike": trade.long_strike,
            "expiry": trade.expiry,
            "contracts": trade.contracts,
            "opened_at": trade.opened_at,
            "credit_per_contract": trade.credit_per_contract,
            "max_profit_total": trade.max_profit_total,
            "max_loss_total": trade.max_loss_total,
            "bpr_total": trade.bpr_total,
            "manage_at_pct": trade.manage_at_pct,
            "exit_dte": trade.exit_dte,
            "metrics": {
                "is_matched": m.is_matched,
                "legs_found": m.legs_found,
                "has_live_quotes": m.has_live_quotes,
                "underlying_price": m.underlying_price,
                "short_strike_distance_pct": m.short_strike_distance_pct,
                "short_strike_breached": m.short_strike_breached,
                "dte": m.dte,
                "short_leg": {
                    "bid": m.short_bid,
                    "ask": m.short_ask,
                    "mark": m.short_mark,
                },
                "long_leg": {
                    "bid": m.long_bid,
                    "ask": m.long_ask,
                    "mark": m.long_mark,
                },
                "cost_to_close": {
                    "mid": _round(m.cost_to_close_mid, 4),
                    "worst_case": _round(m.cost_to_close_worst, 4),
                },
                "profit_if_closed": {
                    "mid": _round(m.profit_if_closed_mid, 2),
                    "worst_case": _round(m.profit_if_closed_worst, 2),
                },
                "pct_max_profit_captured_mid": _round(m.pct_max_profit_captured_mid, 4),
            },
            "recommendation": {
                "action": rec.action,
                "urgency": rec.urgency,
                "reasoning": rec.reasoning,
                "alternative": rec.alternative,
            },
        })

    return {
        "version": 2,
        "last_poll_at": timestamp_et.isoformat() if timestamp_et else None,
        "trigger": trigger,
        "account": {
            "net_liquidating_value": current,
            "day_pnl": snapshot.day_pnl,
            "cash_balance": snapshot.cash_balance,
            "derivative_buying_power": snapshot.derivative_buying_power,
            "starting_capital": starting,
            "cumulative_pnl": round(cum_pnl, 2),
            "cumulative_pct": round(cum_pnl / starting, 4) if starting else 0,
        },
        "trades": trades_block,
        "raw_positions": [
            {
                "symbol": p.symbol,
                "underlying": p.underlying,
                "instrument_type": p.instrument_type,
                "quantity": p.quantity,
                "average_open_price": p.average_open_price,
                "bid": p.bid,
                "ask": p.ask,
                "mark": p.mark,
                "last": p.last,
                "is_option": p.is_option,
                "is_short": p.is_short,
            }
            for p in snapshot.positions
        ],
    }


def _round(value, places):
    return round(value, places) if value is not None else None


def push_state(
    trigger: str,
    timestamp_et,
    snapshot,
    trade_results: list,
) -> bool:
    if not config.GIST_ID or not config.GIST_TOKEN:
        log.info("Gist not configured; skipping push")
        return False

    payload = _build_snapshot(trigger, timestamp_et, snapshot, trade_results)
    content = json.dumps(payload, indent=2, default=str)

    try:
        r = requests.patch(
            f"{GIST_API}/{config.GIST_ID}",
            headers={
                "Authorization": f"Bearer {config.GIST_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            json={"files": {"last_poll.json": {"content": content}}},
            timeout=15,
        )
        r.raise_for_status()
        log.info("Pushed state snapshot to gist %s", config.GIST_ID)
        return True
    except requests.RequestException as e:
        log.error("Failed to push to gist: %s", e)
        return False
