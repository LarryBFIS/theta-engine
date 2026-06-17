"""Tests for the scan watchdog (pure logic).

Run without pytest:  python -m scripts.test_scan_if_stale
"""
import sys
from datetime import datetime, timezone

from scripts.scan_if_stale import is_market_hours, minutes_since, should_scan


def main() -> int:
    f = []

    # --- market hours (ET, naive datetimes are fine for the pure check) ---
    # Tue 2026-06-16 11:00 ET = open
    if not is_market_hours(datetime(2026, 6, 16, 11, 0)):
        f.append("11:00 Tue should be open")
    # Tue 09:15 ET = pre-open
    if is_market_hours(datetime(2026, 6, 16, 9, 15)):
        f.append("09:15 should be closed")
    # Tue 16:30 ET = after close
    if is_market_hours(datetime(2026, 6, 16, 16, 30)):
        f.append("16:30 should be closed")
    # Sat = weekend
    if is_market_hours(datetime(2026, 6, 20, 12, 0)):
        f.append("Saturday should be closed")
    # edge: exactly 09:30 open, 16:00 close
    if not is_market_hours(datetime(2026, 6, 16, 9, 30)):
        f.append("09:30 should be open")
    if not is_market_hours(datetime(2026, 6, 16, 16, 0)):
        f.append("16:00 should be open")

    # --- minutes_since ---
    now = datetime(2026, 6, 16, 15, 0, tzinfo=timezone.utc)
    if abs(minutes_since("2026-06-16T14:30:00+00:00", now) - 30) > 0.01:
        f.append("minutes_since 30m: {}".format(minutes_since("2026-06-16T14:30:00+00:00", now)))
    if minutes_since(None, now) < 1e8:
        f.append("missing ts -> very stale")
    if minutes_since("garbage", now) < 1e8:
        f.append("bad ts -> very stale")
    if abs(minutes_since("2026-06-16T14:00:00Z", now) - 60) > 0.01:   # Z suffix
        f.append("Z-suffix parse")

    # --- should_scan ---
    et_open = datetime(2026, 6, 16, 11, 0)
    et_closed = datetime(2026, 6, 16, 20, 0)
    # stale + open -> scan
    go, why = should_scan("2026-06-16T14:30:00Z", et_open, datetime(2026, 6, 16, 15, 30, tzinfo=timezone.utc), max_age_min=25)
    if not go:
        f.append("stale+open should scan: {}".format(why))
    # fresh + open -> skip
    go, why = should_scan("2026-06-16T15:20:00Z", et_open, datetime(2026, 6, 16, 15, 30, tzinfo=timezone.utc), max_age_min=25)
    if go:
        f.append("fresh+open should skip: {}".format(why))
    # stale but market closed -> skip
    go, why = should_scan("2026-06-15T14:30:00Z", et_closed, datetime(2026, 6, 16, 15, 30, tzinfo=timezone.utc), max_age_min=25)
    if go:
        f.append("stale+closed should skip: {}".format(why))
    # no prior scan + open -> scan
    go, why = should_scan(None, et_open, datetime(2026, 6, 16, 15, 30, tzinfo=timezone.utc), max_age_min=25)
    if not go:
        f.append("no-scan+open should scan: {}".format(why))

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("market-hours ✓ · age ✓ · should_scan (stale/fresh/closed/missing) ✓")
    print("All scan_if_stale tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
