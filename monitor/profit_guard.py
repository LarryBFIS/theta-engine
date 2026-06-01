"""Profit-protection signal — tell me to take profits EARLY (before the 50% target)
when holding longer risks giving the gains back.

The mechanical rule closes winners at 50% of credit. But sometimes you've banked
a good chunk fast and the remaining premium isn't worth the risk of a reversal.
This fires when meaningful profit is captured (>= MIN_CAPTURE) but still below the
50% target AND something now threatens it:
  - the underlying has breached / is hugging the short strike (delta risk up),
  - few days left (gamma rising into expiry),
  - profit came in fast (front-loaded; little left to squeeze).

Pure + tunable (env-overridable); unit-tested in scripts/test_profit_guard.py.
"""
import os


def _f(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


MIN_CAPTURE = _f("PROFIT_GUARD_MIN_CAPTURE", 0.25)       # need at least this much banked
MANAGE_TARGET = _f("PROFIT_GUARD_MANAGE_TARGET", 0.50)   # 50% is handled mechanically/GTC
EARLY_DTE = int(_f("PROFIT_GUARD_EARLY_DTE", 25))        # gamma rising under this
NEAR_STRIKE_PCT = _f("PROFIT_GUARD_NEAR_STRIKE_PCT", 0.015)  # within 1.5% of short strike
FAST_PER_DAY = _f("PROFIT_GUARD_FAST_PER_DAY", 0.06)     # captured/day this fast = front-loaded


def profit_protection_signal(captured, dte, distance_pct, breached, days_held=None):
    """Return (fire: bool, reasons: list[str]).

    Fires only in the 'banked but below 50%' zone, and only when a risk factor
    threatens the open profit. Args come straight from poll metrics:
      captured     = pct_max_profit_captured_mid (0-1)
      dte          = days to expiry
      distance_pct = how far underlying sits above the short strike (small = risky)
      breached     = underlying at/through the short strike
      days_held    = days since open (for profit velocity)
    """
    reasons = []
    if captured is None or captured < MIN_CAPTURE or captured >= MANAGE_TARGET:
        return False, reasons
    if breached:
        reasons.append("underlying breached the short strike")
    elif distance_pct is not None and 0 <= distance_pct <= NEAR_STRIKE_PCT:
        reasons.append("underlying within {:.1%} of the short strike".format(distance_pct))
    if dte is not None and dte <= EARLY_DTE:
        reasons.append("{}d to expiry — gamma/whipsaw risk rising".format(dte))
    if days_held and days_held > 0 and (captured / days_held) >= FAST_PER_DAY:
        reasons.append("captured {:.0%} in {}d — front-loaded, little left to squeeze".format(captured, days_held))
    return (len(reasons) > 0), reasons
