"""Summary entry: 4×/day snapshot push.

Sends portfolio summary + pushes full diagnostic state to Gist.
"""
import logging
import sys
from datetime import datetime

from pytz import timezone as tz

from monitor import config, gist, notifier
from monitor.decisions import (
    ACTION_HOLD,
    compute_metrics,
    format_summary,
    make_recommendation,
)
from monitor.market_data import get_quote
from monitor.tastytrade_client import TastytradeClient
from monitor.trades import load_trades

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("summary")

ET = tz("America/New_York")


def main() -> int:
    now_et = datetime.now(ET)
    log.info("Summary triggered at %s ET", now_et.strftime("%Y-%m-%d %H:%M:%S"))

    try:
        trades = load_trades()
        open_trades = [t for t in trades if t.is_open]

        client = TastytradeClient()
        snapshot = client.fetch_snapshot()

        metrics_list = []
        action_flags = []
        trade_results = []
        for trade in open_trades:
            up = get_quote(trade.underlying)
            m = compute_metrics(trade, snapshot, underlying_price=up)
            metrics_list.append(m)
            rec = make_recommendation(trade, m)
            trade_results.append({"trade": trade, "metrics": m, "recommendation": rec})
            if rec.action != ACTION_HOLD:
                action_flags.append(f"{trade.underlying} → {rec.action}")

        # Build title
        time_str = now_et.strftime("%-I:%M %p ET")
        title = f"📊 Portfolio · {time_str}"
        if action_flags:
            title = f"⚡ ACTION · {time_str}"

        body = format_summary(metrics_list, snapshot)
        if action_flags:
            body += "\n\n⚡ Actionable now:\n" + "\n".join(f"• {a}" for a in action_flags)

        notifier.send(
            title=title,
            message=body,
            priority=notifier.PRIORITY_NORMAL,
            sound=notifier.SOUND_REMINDER,
        )

        # Push diagnostic snapshot to Gist
        gist.push_state(
            trigger="summary",
            timestamp_et=now_et,
            snapshot=snapshot,
            trade_results=trade_results,
        )
        return 0
    except Exception as e:
        log.exception("Summary failed: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
