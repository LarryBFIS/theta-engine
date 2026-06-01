"""Poll entry: one cycle of evaluating tracked trades and pushing alerts.

v5 flow:
  1. Load tracked trades
  2. Pull account snapshot WITH live option quotes (positions + market data)
  3. Compute metrics per trade (uses live bid/ask/mark)
  4. Generate recommendation (HOLD if quotes unavailable — no fake CLOSE)
  5. Send Pushover + log suggestion (only for actionable recs)
  6. Push full diagnostic snapshot to Gist
"""
import logging
import sys
from datetime import datetime

from pytz import timezone as tz

from monitor import config, gist, notifier
from monitor.approvals import decide_url
from monitor.profit_guard import profit_protection_signal
from monitor.decisions import (
    ACTION_HOLD,
    ACTION_URGENT_CLOSE,
    URGENCY_HIGH,
    compute_metrics,
    format_recommendation,
    make_recommendation,
)
from monitor.market_data import get_quote
from monitor.tastytrade_client import TastytradeClient
from monitor.trades import (
    Suggestion,
    append_suggestion,
    load_suggestions,
    load_trades,
    make_suggestion_id,
)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("poll")

ET = tz("America/New_York")


def _days_held(trade) -> int:
    try:
        opened = datetime.strptime(trade.opened_at[:10], "%Y-%m-%d").date()
        return (datetime.now(tz=ET).date() - opened).days
    except Exception:  # noqa: BLE001
        return None


def _alerted_today(suggestions, trade_id, action) -> bool:
    today = datetime.now(tz=ET).date().isoformat()
    return any(
        s.trade_id == trade_id and s.action == action and (s.timestamp or "")[:10] == today
        for s in suggestions
    )


def main() -> int:
    now_et = datetime.now(ET)
    log.info("Poll triggered at %s ET", now_et.strftime("%Y-%m-%d %H:%M:%S"))

    try:
        trades = load_trades()
        open_trades = [t for t in trades if t.is_open]
        log.info("Loaded %d tracked trades (%d open)", len(trades), len(open_trades))
        existing_suggestions = load_suggestions()

        client = TastytradeClient()
        snapshot = client.fetch_snapshot()
        log.info(
            "Snapshot: net_liq=$%.2f day_pnl=$%+.2f positions=%d",
            snapshot.net_liquidating_value,
            snapshot.day_pnl,
            len(snapshot.positions),
        )

        trade_results = []
        for trade in open_trades:
            underlying_price = get_quote(trade.underlying)
            m = compute_metrics(trade, snapshot, underlying_price=underlying_price)
            rec = make_recommendation(trade, m)
            trade_results.append({"trade": trade, "metrics": m, "recommendation": rec})

            captured_str = (
                f"{m.pct_max_profit_captured_mid*100:.0f}%"
                if m.pct_max_profit_captured_mid is not None else "n/a"
            )
            cost_str = (
                f"${m.cost_to_close_mid:.2f}/${m.cost_to_close_worst:.2f}"
                if m.cost_to_close_mid is not None and m.cost_to_close_worst is not None else "n/a"
            )
            log.info(
                "%s: action=%s captured=%s cost_mid/worst=%s dte=%d quotes=%s",
                trade.id, rec.action, captured_str, cost_str, m.dte, m.has_live_quotes,
            )

            if rec.action == ACTION_HOLD:
                # Early take-profit: banked decent profit (<50%) but holding risks giving it back.
                fired, reasons = profit_protection_signal(
                    m.pct_max_profit_captured_mid, m.dte,
                    m.short_strike_distance_pct, m.short_strike_breached,
                    days_held=_days_held(trade),
                )
                if (fired and m.has_live_quotes
                        and not _alerted_today(existing_suggestions, trade.id, "PROTECT_PROFITS")):
                    captured = m.pct_max_profit_captured_mid or 0.0
                    message = "Captured {:.0%} (below the 50% target) — consider closing now:\n- {}".format(
                        captured, "\n- ".join(reasons))
                    notifier.send(
                        title="💰 {}: take profits early".format(trade.underlying),
                        message=message,
                        priority=notifier.PRIORITY_NORMAL,
                        sound=notifier.SOUND_SUCCESS,
                    )
                    sug = Suggestion(
                        id=make_suggestion_id(trade.id, datetime.now(tz=ET)),
                        trade_id=trade.id,
                        timestamp=datetime.now(tz=ET).isoformat(),
                        action="PROTECT_PROFITS",
                        urgency="normal",
                        reasoning=reasons,
                        metrics_snapshot={
                            "pct_captured": captured,
                            "dte": m.dte,
                            "short_strike_breached": m.short_strike_breached,
                        },
                    )
                    append_suggestion(sug)
                    existing_suggestions.append(sug)  # avoid duplicate alert within this run
                continue

            title = (
                f"🚨 {trade.underlying}: URGENT CLOSE"
                if rec.action == ACTION_URGENT_CLOSE
                else f"{trade.underlying}: {rec.action}"
            )
            message = format_recommendation(rec)
            sound = notifier.SOUND_ALERT if rec.urgency == URGENCY_HIGH else notifier.SOUND_SUCCESS
            priority = notifier.PRIORITY_HIGH if rec.urgency == URGENCY_HIGH else notifier.PRIORITY_NORMAL

            # Phase 5b: attach a signed Approve/Reject deep link to this alert.
            sug_id = make_suggestion_id(trade.id, datetime.now(tz=ET))
            notifier.send(
                title=title, message=message, priority=priority, sound=sound,
                url=decide_url(sug_id), url_title="Review → Approve/Reject",
            )

            suggestion = Suggestion(
                id=sug_id,
                trade_id=trade.id,
                timestamp=datetime.now(tz=ET).isoformat(),
                action=rec.action,
                urgency=rec.urgency,
                reasoning=rec.reasoning,
                alternative=rec.alternative,
                metrics_snapshot={
                    "cost_to_close_mid": m.cost_to_close_mid,
                    "cost_to_close_worst": m.cost_to_close_worst,
                    "profit_if_closed_mid": m.profit_if_closed_mid,
                    "profit_if_closed_worst": m.profit_if_closed_worst,
                    "pct_max_profit_captured_mid": m.pct_max_profit_captured_mid,
                    "dte": m.dte,
                    "underlying_price": m.underlying_price,
                    "short_strike_breached": m.short_strike_breached,
                    "has_live_quotes": m.has_live_quotes,
                    "net_liq": snapshot.net_liquidating_value,
                    "day_pnl": snapshot.day_pnl,
                },
            )
            append_suggestion(suggestion)

        gist.push_state(
            trigger="poll",
            timestamp_et=now_et,
            snapshot=snapshot,
            trade_results=trade_results,
        )
        return 0
    except Exception as e:
        log.exception("Poll failed: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
