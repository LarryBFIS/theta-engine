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


def main() -> int:
    now_et = datetime.now(ET)
    log.info("Poll triggered at %s ET", now_et.strftime("%Y-%m-%d %H:%M:%S"))

    try:
        trades = load_trades()
        open_trades = [t for t in trades if t.is_open]
        log.info("Loaded %d tracked trades (%d open)", len(trades), len(open_trades))

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
                continue

            title = (
                f"🚨 {trade.underlying}: URGENT CLOSE"
                if rec.action == ACTION_URGENT_CLOSE
                else f"{trade.underlying}: {rec.action}"
            )
            message = format_recommendation(rec)
            sound = notifier.SOUND_ALERT if rec.urgency == URGENCY_HIGH else notifier.SOUND_SUCCESS
            priority = notifier.PRIORITY_HIGH if rec.urgency == URGENCY_HIGH else notifier.PRIORITY_NORMAL
            notifier.send(title=title, message=message, priority=priority, sound=sound)

            sug_id = make_suggestion_id(trade.id, datetime.now(tz=ET))
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
