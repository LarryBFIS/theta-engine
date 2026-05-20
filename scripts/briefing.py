"""Daily intel briefing entry point.

Flow:
  1. Load tracked open trades
  2. Fetch account snapshot + live option quotes (same as poll)
  3. Compute per-trade metrics (real P&L if closed)
  4. Fetch news headlines for each underlying (Yahoo RSS, last 24h)
  5. Fetch IV rank/percentile from tastytrade /market-metrics
  6. Send context to Claude (Anthropic API) for synthesis
  7. Push briefing via Pushover

Runs once per weekday at 8 AM ET premarket.
"""
import logging
import os
import sys
from datetime import datetime

from pytz import timezone as tz

from monitor import config, intel, notifier
from monitor.decisions import compute_metrics
from monitor.market_data import get_quote
from monitor.tastytrade_client import TastytradeClient
from monitor.trades import load_trades

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("briefing")

ET = tz("America/New_York")


def main() -> int:
    now_et = datetime.now(ET)
    log.info("Briefing triggered at %s ET", now_et.strftime("%Y-%m-%d %H:%M:%S"))

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        log.error("ANTHROPIC_API_KEY not set in environment; cannot synthesize")
        return 1

    try:
        # 1. Load positions
        open_trades = [t for t in load_trades() if t.is_open]
        if not open_trades:
            log.info("No open trades; skipping briefing")
            return 0
        log.info("%d open trade(s)", len(open_trades))

        # 2. Snapshot + live quotes
        client = TastytradeClient()
        snapshot = client.fetch_snapshot()
        log.info("Snapshot: net_liq=$%.2f", snapshot.net_liquidating_value)

        # 3. Per-trade metrics
        trade_results = []
        for trade in open_trades:
            underlying_price = get_quote(trade.underlying)
            m = compute_metrics(trade, snapshot, underlying_price=underlying_price)
            trade_results.append({"trade": trade, "metrics": m})

        tickers = sorted({t.underlying for t in open_trades})

        # 4. News per underlying
        news_by_ticker = {t: intel.fetch_news_yahoo(t, max_items=10) for t in tickers}

        # 5. IV metrics
        metrics = intel.fetch_market_metrics(client, tickers)

        # 6. Build context + synthesize
        positions_summary = intel.format_positions_for_prompt(snapshot, trade_results)
        news_blob = intel.format_news_for_prompt(news_by_ticker)
        metrics_summary = intel.format_metrics_for_prompt(metrics)

        log.info("Calling Claude for synthesis...")
        briefing = intel.synthesize_briefing(
            positions_summary=positions_summary,
            news_blob=news_blob,
            market_metrics_summary=metrics_summary,
            api_key=api_key,
            extra_context=f"Today is {now_et.strftime('%A %B %d, %Y')}.",
        )
        log.info("Briefing generated (%d chars)", len(briefing))
        print("\n" + "=" * 60)
        print(briefing)
        print("=" * 60 + "\n")

        # 7. Push
        date_str = now_et.strftime("%a %b %-d")
        title = f"📊 Pre-market briefing · {date_str}"
        notifier.send(
            title=title,
            message=briefing,
            priority=notifier.PRIORITY_NORMAL,
            sound=notifier.SOUND_SUCCESS,
        )
        log.info("Pushed briefing to Pushover")
        return 0

    except Exception as e:
        log.exception("Briefing failed: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
