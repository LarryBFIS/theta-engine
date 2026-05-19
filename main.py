"""Entry point — schedules the polling loop and daily summary.

Runs:
- Every 15 min during market hours (Mon-Fri, 9:30 AM - 4:00 PM ET): evaluate all rules
- Once daily at 4:05 PM ET: send daily summary

Logs to stdout — Fly.io captures these automatically.
"""
import logging
import signal
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone as tz

from monitor import config, notifier
from monitor.rules import run_all_rules, send_daily_summary
from monitor.state import State
from monitor.tastytrade_client import TastytradeClient

# ─────────────── Logging setup ───────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("main")

# ─────────────── Singletons ───────────────
client = TastytradeClient()
state = State(config.STATE_PATH)
ET = tz("America/New_York")


def poll_and_evaluate() -> None:
    """Pull snapshot and run all rules."""
    now_et = datetime.now(ET)
    log.info("Polling at %s ET", now_et.strftime("%H:%M:%S"))
    try:
        snapshot = client.fetch_snapshot()
        log.info(
            "Snapshot: net_liq=$%.2f day_pnl=$%+.2f positions=%d",
            snapshot.net_liquidating_value,
            snapshot.day_pnl,
            len(snapshot.positions),
        )
        run_all_rules(snapshot, state)
    except Exception as e:
        log.exception("Poll failed: %s", e)


def daily_summary() -> None:
    """Send end-of-day summary."""
    log.info("Sending daily summary")
    try:
        snapshot = client.fetch_snapshot()
        send_daily_summary(snapshot, state)
    except Exception as e:
        log.exception("Daily summary failed: %s", e)


def startup_announcement() -> None:
    """Notify on first boot so you know the service is alive."""
    if state.get("startup_announced"):
        return
    notifier.send(
        title="Tastytrade monitor online",
        message=(
            "Notification service is running.\n"
            "Polling every 15 min during market hours.\n"
            "Daily summary at 4:05 PM ET."
        ),
        priority=notifier.PRIORITY_LOW,
        sound=notifier.SOUND_INFO,
    )
    state.set("startup_announced", True)


def main() -> None:
    log.info("Starting tastytrade-monitor (timezone=%s)", config.TIMEZONE)

    startup_announcement()

    # Sanity check — do one poll on startup so we know the API works
    log.info("Initial poll on startup...")
    poll_and_evaluate()

    scheduler = BlockingScheduler(timezone=ET)

    # Poll every 15 min during market hours (Mon-Fri, 9:30-15:59 ET).
    # Cron expression: minute=*/15, hour=9-15, day_of_week=mon-fri
    scheduler.add_job(
        poll_and_evaluate,
        CronTrigger(day_of_week="mon-fri", hour="9-15", minute="*/15", timezone=ET),
        id="poll",
        name="Poll tastytrade and evaluate rules",
        max_instances=1,
        coalesce=True,
    )

    # Scheduled summaries 4x/day during market hours: 10 AM, 12 PM, 2 PM, 4 PM ET.
    # These fire regardless of triggers — informational "where you stand" pushes.
    # Note: state.cooldown enforces per-summary spacing so we don't double-push if the
    # service restarts mid-day.
    SUMMARY_HOURS = [10, 12, 14, 16]  # 10am, 12pm, 2pm, 4pm ET
    for h in SUMMARY_HOURS:
        scheduler.add_job(
            daily_summary,
            CronTrigger(day_of_week="mon-fri", hour=h, minute=0, timezone=ET),
            id=f"summary_{h:02d}",
            name=f"Summary push at {h:02d}:00 ET",
            max_instances=1,
        )

    # Graceful shutdown
    def shutdown(_signum, _frame):
        log.info("Shutting down...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    log.info("Scheduler started. Press Ctrl+C to stop.")
    scheduler.start()


if __name__ == "__main__":
    main()
