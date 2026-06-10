"""FOMC trade-trigger alert for the 10-minute poll.

During the FOMC meeting window (Jun 16-17, 2026, market hours, ET/DST-aware)
the poll fires a one-shot Pushover nudge to sell an IWM/QQQ iron condor and
harvest the post-announcement IV crush. The decision lands ~2:00pm ET on day
two; after that the message switches to a confirm/stand-down check.

Dedup is one alert PER PHASE per session (setup + done = at most two), persisted
through the suggestions ledger (committed every tick), so the 10-min poll won't
re-fire it.

Pure logic (phase detection, dedup test, message building) lives here and is
unit-tested in scripts/test_fomc.py; only poll.py touches the network/notifier.
"""
from datetime import date, time

# Event window, America/New_York. FOMC decision is released ~2:00pm ET on day 2.
DAY1 = date(2026, 6, 16)
DAY2 = date(2026, 6, 17)
DECISION_TIME = time(14, 0)        # 2:00pm ET on DAY2 — the IV crush hits here
MKT_OPEN = time(9, 30)
MKT_CLOSE = time(16, 0)

# Synthetic trade id so the alerts dedup through the existing suggestions ledger.
TRADE_ID = "fomc_2026_06"
ACTION_SETUP = "FOMC_IC_SETUP"
ACTION_DONE = "FOMC_DONE"


def _is_market_hours(now_et) -> bool:
    """Weekday RTH 9:30-16:00 ET. now_et must be an ET-localized datetime."""
    if now_et.weekday() >= 5:      # Sat/Sun
        return False
    return MKT_OPEN <= now_et.time() <= MKT_CLOSE


def phase(now_et):
    """Return 'setup', 'done', or None for the given ET-localized datetime.

    setup = inside the window, before the day-2 decision (sell into the crush).
    done  = day 2 after 2:00pm ET (event passed — confirm or stand down).
    """
    d = now_et.date()
    if d not in (DAY1, DAY2) or not _is_market_hours(now_et):
        return None
    if d == DAY1:
        return "setup"
    return "done" if now_et.time() >= DECISION_TIME else "setup"


def action_for(ph) -> str:
    return ACTION_SETUP if ph == "setup" else ACTION_DONE


def already_fired(suggestions, action) -> bool:
    """True if this FOMC action was already sent (dedup across the session)."""
    return any(
        getattr(s, "trade_id", None) == TRADE_ID and getattr(s, "action", None) == action
        for s in suggestions
    )


def _live_lines(live):
    """Render 'IWM $xxx.xx · IV Rank xx%' lines for whatever data we could pull."""
    lines = []
    for sym in ("IWM", "QQQ"):
        d = (live or {}).get(sym) or {}
        px, ivr = d.get("price"), d.get("iv_rank")
        if px is None and ivr is None:
            continue
        parts = []
        if px is not None:
            parts.append("${:.2f}".format(px))
        if ivr is not None:
            parts.append("IV Rank {:.0f}%".format(ivr * 100))
        lines.append("{} {}".format(sym, " · ".join(parts)))
    return lines


def build_message(ph, live=None):
    """Return (title, message) for the given phase. `live` is optional enrichment:
    {"IWM": {"price": float, "iv_rank": fraction}, "QQQ": {...}}."""
    extra = _live_lines(live)
    if ph == "setup":
        body = ["Sell IWM (primary) or QQQ Jul-17 iron condor to harvest the FOMC IV crush."]
        if extra:
            body += [""] + extra
        body += [
            "",
            "Checklist:",
            "1. IV Rank >= 40 on tastytrade",
            "2. Pull IWM Jul-17 chain",
            "3. ~10-12 delta shorts both sides",
            "4. Size wing so max loss <= $300",
            "5. Close Jun 18",
        ]
        return "FOMC IC SETUP", "\n".join(body)

    body = ["FOMC DONE - if IV Rank still >=40 AND tape stable, fire the IC; else stand down."]
    if extra:
        body += [""] + extra
    return "FOMC DONE", "\n".join(body)
