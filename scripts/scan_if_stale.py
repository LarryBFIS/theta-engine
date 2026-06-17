"""Scan watchdog — refresh the opportunity scan if it's stale during market hours.

GitHub's *scheduled* scan triggers fire erratically (we watched scans get skipped
on a live trading day, leaving the dashboard showing yesterday's board). The
*tick* fires reliably (Cloudflare repository_dispatch every ~10 min), so it calls
this each run: if the last scan is older than SCAN_MAX_AGE_MIN AND the US market is
open, run a fresh scan. Belt to the cron's suspenders — the board never goes stale
on a trading day, so the auto-tickets always sit on fresh data.

A scan failure here is non-fatal (logged, returns 0) so it never breaks the tick.
The staleness + market-hours logic is pure and unit-tested.
"""
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_FILE = REPO_ROOT / "scan" / "opportunities.json"
MAX_AGE_MIN = int(os.getenv("SCAN_MAX_AGE_MIN", "25"))

log = logging.getLogger("scan_watchdog")


def is_market_hours(now_et):
    """US equity regular session: Mon-Fri 09:30-16:00 ET. Holidays aren't modeled
    — a scan on a holiday simply finds nothing and is harmless."""
    if now_et.weekday() >= 5:
        return False
    mins = now_et.hour * 60 + now_et.minute
    return (9 * 60 + 30) <= mins <= (16 * 60)


def minutes_since(generated_at, now_utc):
    """Age in minutes of an ISO timestamp; treat missing/unparseable as very stale."""
    if not generated_at:
        return 1e9
    try:
        g = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
        if g.tzinfo is None:
            g = g.replace(tzinfo=timezone.utc)
        return (now_utc - g).total_seconds() / 60.0
    except (ValueError, TypeError):
        return 1e9


def should_scan(generated_at, now_et, now_utc, max_age_min=MAX_AGE_MIN):
    """(go, reason). Scan only when the market is open AND the last scan is stale."""
    if not is_market_hours(now_et):
        return False, "market closed"
    age = minutes_since(generated_at, now_utc)
    if age < max_age_min:
        return False, "fresh ({:.0f}m < {}m)".format(age, max_age_min)
    return True, "stale ({:.0f}m >= {}m)".format(age, max_age_min)


def _now_et():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("America/New_York"))
    except Exception:  # noqa: BLE001 — fallback assumes EDT
        return datetime.now(timezone.utc) - timedelta(hours=4)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    gen = None
    try:
        gen = json.loads(SCAN_FILE.read_text()).get("generated_at")
    except (OSError, json.JSONDecodeError):
        gen = None
    now_utc, now_et = datetime.now(timezone.utc), _now_et()
    go, why = should_scan(gen, now_et, now_utc)
    if not go:
        log.info("scan watchdog: skip (%s)", why)
        return 0
    log.info("scan watchdog: %s -> running fresh scan", why)
    try:
        from scripts.scan_opportunities import main as scan_main
        rc = scan_main()
        log.info("scan watchdog: scan finished rc=%s", rc)
    except Exception as e:  # noqa: BLE001 — never break the tick on a scan error
        log.warning("scan watchdog: scan failed (non-fatal): %s", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
