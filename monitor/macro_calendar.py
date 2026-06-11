"""Macro event calendar — REAL hardcoded dates, manually maintained.

Drives two things in the scanner:
  1. EVENT-CRUSH opportunities — a defined-risk (skewed) iron condor expiring
     AFTER a scheduled macro event, entered ~1 day before and closed the day
     after, to harvest the post-event IV/vega crush.
  2. A pre-event gate — don't surface a NON-event short-vol initiation as LIVE
     within ~2 trading days of a scheduled event (unless it IS the crush setup).

Only REAL, confirmed dates go here (no stubs). The queued live trade is the
Jun-17 2026 FOMC IWM/QQQ iron condor. CPI/JOBS slots are left EMPTY rather than
guessed — add real dates as they're confirmed.

Pure date logic; unit-tested in scripts/test_macro_calendar.py.
"""
from datetime import date

# Confirmed macro events (America/New_York). decision_date = the release/decision day.
EVENTS = [
    {"type": "FOMC", "label": "FOMC rate decision",
     "meeting_days": ["2026-06-16", "2026-06-17"],
     "decision_date": "2026-06-17", "decision_time_et": "14:00"},
    # CPI / JOBS (NFP): add confirmed real dates here, e.g.
    #   {"type": "CPI",  "label": "CPI report",   "decision_date": "YYYY-MM-DD", "decision_time_et": "08:30"},
    #   {"type": "JOBS", "label": "Jobs report",  "decision_date": "YYYY-MM-DD", "decision_time_et": "08:30"},
]

# The queued, pre-specified event-crush trade for the Jun-17 2026 FOMC.
FOMC_IC_TRIGGER = {
    "event": "FOMC",
    "decision_date": "2026-06-17",
    "decision_time_et": "14:00",
    "underlyings": ["IWM", "QQQ"],   # IWM primary
    "structure": "iron_condor",
    "expiry": "2026-07-17",          # Jul-17, expires AFTER the event
    "short_delta": 0.12,             # ~12Δ shorts
    "put_skew": True,                # push the short PUT further OTM than the call
    "wing_width": 3,                 # 3-wide
    "max_loss_cap": 300,             # max loss <= $300
    "enter_date": "2026-06-16",      # enter ~1 day before
    "close_date": "2026-06-18",      # close the day after
    "live_conditions": {"iv_rank_min": 0.40, "vix_min": 18},
}


def _days_until(d_iso, today_iso):
    try:
        return (date.fromisoformat(d_iso[:10]) - date.fromisoformat(today_iso[:10])).days
    except (ValueError, TypeError):
        return None


def upcoming_events(today_iso, within_days=10):
    """Events whose decision is in [today, today+within_days], soonest first."""
    out = []
    for e in EVENTS:
        d = _days_until(e["decision_date"], today_iso)
        if d is not None and 0 <= d <= within_days:
            out.append(dict(e, days_until=d))
    return sorted(out, key=lambda e: e["days_until"])


def next_event(today_iso):
    up = upcoming_events(today_iso, within_days=365)
    return up[0] if up else None


def in_blackout(today_iso, days_before=2):
    """True if a scheduled macro event decision is within `days_before` days
    (today inclusive) — don't open NEW non-event short-vol LIVE this close in."""
    for e in EVENTS:
        d = _days_until(e["decision_date"], today_iso)
        if d is not None and 0 <= d <= days_before:
            return True
    return False


def _live_ok(vix, iv_ranks):
    """LIVE only if VIX >= vix_min AND at least one underlying's IV rank >= iv_rank_min."""
    cond = FOMC_IC_TRIGGER["live_conditions"]
    vix_ok = vix is not None and vix >= cond["vix_min"]
    ranks = [r for r in (iv_ranks or {}).values() if r is not None]
    ivr_ok = any(r >= cond["iv_rank_min"] for r in ranks) if ranks else False
    return bool(vix_ok and ivr_ok)


def event_crush_opportunity(today_iso, vix=None, iv_ranks=None):
    """The queued FOMC iron-condor crush trade as an opportunity dict, or None
    once it's past the close date. Status: 'queued' (>1d before enter),
    'enter' (within the enter window), 'closing' (close day), 'past' (None).
    LIVE-eligible only inside the enter window AND when conditions are met — it
    never flags 'open now' more than ~1-2 days early.
    """
    t = FOMC_IC_TRIGGER
    d_dec = _days_until(t["decision_date"], today_iso)
    d_close = _days_until(t["close_date"], today_iso)
    if d_close is None or d_close < 0:
        return None   # event passed
    d_enter = _days_until(t["enter_date"], today_iso)
    if d_enter is not None and d_enter > 1:
        status = "queued"            # still more than ~1 day before the enter date
    elif d_dec is not None and d_dec >= 0:
        status = "enter"             # in the enter window (enter date .. decision)
    else:
        status = "closing"           # after the decision, on/at the close date
    live_ok = (status == "enter") and _live_ok(vix, iv_ranks)
    cond = t["live_conditions"]
    reasoning = (
        "FOMC IV/vega crush — sell a put-skewed iron condor on {u} ({exp}, ~{d:.0f}Δ shorts, "
        "{w}-wide, max loss ≤${ml}). Enter {en}, close {cl}. Harvest the vol collapse after the "
        "{dd} 2:00pm ET decision. LIVE only if IV Rank ≥{ivr:.0%} AND VIX ≥{vx} (currently {status})."
    ).format(u="/".join(t["underlyings"]), exp=t["expiry"], d=t["short_delta"] * 100,
             w=t["wing_width"], ml=t["max_loss_cap"], en=t["enter_date"], cl=t["close_date"],
             dd=t["decision_date"], ivr=cond["iv_rank_min"], vx=cond["vix_min"], status=status)
    return {
        "type": "event", "event": "FOMC", "label": "FOMC IV-crush iron condor",
        "underlyings": t["underlyings"], "structure": "iron_condor", "expiry": t["expiry"],
        "short_delta": t["short_delta"], "put_skew": t["put_skew"], "wing_width": t["wing_width"],
        "max_loss_cap": t["max_loss_cap"], "enter_date": t["enter_date"],
        "close_date": t["close_date"], "decision_date": t["decision_date"],
        "decision_time_et": t["decision_time_et"], "days_to_decision": d_dec,
        "status": status, "live_conditions": cond,
        "vix": vix, "live_ok": live_ok,
        "tag": "live" if live_ok else "paper",
        "reasoning": reasoning,
    }
