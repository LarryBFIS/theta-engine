"""News risk-gate — a shield, not a predictor.

Before the scanner lets a setup go LIVE, this checks recent headlines on the
underlying for a pending catalyst that could whipsaw a short-premium position in
the next ~30 days (earnings miss, downgrade, lawsuit, SEC probe, FDA reject,
halt, bankruptcy, etc.). It does NOT try to predict direction — it only vetoes
or flags danger.

Backbone is deterministic keyword-severity scoring (free, fast, unit-tested).
An optional Claude pass adds nuance when ANTHROPIC_API_KEY is set and
SCAN_AI_NEWS_GATE=1; it can only ESCALATE risk (never clear a deterministic
veto), and falls back silently on any error.

Levels: 'clear' (trade it) · 'caution' (flag) · 'veto' (don't go LIVE).
"""
import logging
import os
from datetime import datetime, timezone

log = logging.getLogger("news_risk")

# Severity tiers (substring match, lowercased). Tier 3 = veto, Tier 2 = caution.
TIER3 = [
    "bankruptcy", "chapter 11", "going concern", "default", "fraud", "sec ",
    "investigation", "probe", "subpoena", "halt", "halted", "delist", "restate",
    "guidance cut", "slashes guidance", "plunge", "fda reject", "rejected",
    "recall", "warning letter", "data breach", "hacked", "ceo resign", "cfo resign",
    "accounting", "going private",
]
TIER2 = [
    "downgrade", "cut to", "lawsuit", "sued", "settlement", "fine", "fined",
    "misses", "warns", "warning", "layoff", "resign", "step down", "short seller",
    "guidance", "slash", "profit warning", "strike",
]
TIER1 = [
    "earnings", "upgrade", "price target", "analyst", "merger", "acquisition",
    "buyout", "dividend", "split", "forecast", "outlook", "report",
]
LEVEL_BY_SEV = {0: "clear", 1: "clear", 2: "caution", 3: "veto"}
_ORDER = {"clear": 0, "caution": 1, "veto": 2}


def severity(text):
    """Return (severity 0-3, matched_keyword|None) for one headline."""
    t = (text or "").lower()
    for kw in TIER3:
        if kw in t:
            return 3, kw
    for kw in TIER2:
        if kw in t:
            return 2, kw
    for kw in TIER1:
        if kw in t:
            return 1, kw
    return 0, None


def assess(symbol, headlines, max_age_days=4):
    """Deterministic verdict from recent headlines.

    headlines: [{title, ts}] where ts is an epoch seconds (0 = unknown -> treated
    as recent). Returns {symbol, level, max_severity, hits[]}.
    """
    cutoff = datetime.now(timezone.utc).timestamp() - max_age_days * 86400
    hits, top = [], 0
    for h in headlines or []:
        ts = h.get("ts") or 0
        if ts and ts < cutoff:
            continue
        sev, kw = severity(h.get("title", ""))
        if sev >= 2:
            hits.append({"title": (h.get("title", "") or "")[:140], "severity": sev, "keyword": kw})
        top = max(top, sev)
    return {"symbol": symbol, "level": LEVEL_BY_SEV[top], "max_severity": top, "hits": hits[:5]}


def escalate(a, b):
    """Return the more severe of two levels (risk only goes up)."""
    return a if _ORDER.get(a, 0) >= _ORDER.get(b, 0) else b


def fetch_headlines(symbol, max_items=8):
    """Recent Yahoo Finance RSS headlines for a symbol: [{title, ts}]."""
    try:
        import calendar
        import feedparser
        url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
        feed = feedparser.parse(url)
        out = []
        for e in feed.entries[:max_items]:
            out.append({
                "title": e.get("title", ""),
                "ts": calendar.timegm(e.published_parsed) if e.get("published_parsed") else 0,
            })
        return out
    except Exception as e:  # noqa: BLE001
        log.warning("news fetch failed for %s: %s", symbol, e)
        return []


def ai_assess(symbol, headlines):
    """Optional Claude verdict ('clear'|'caution'|'veto') or None on any failure.

    Used only when SCAN_AI_NEWS_GATE=1 and ANTHROPIC_API_KEY is set. Can only
    escalate the deterministic verdict, never relax it.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not headlines:
        return None
    titles = "\n".join("- " + (h.get("title", "") or "") for h in headlines[:8])
    prompt = (
        f"You are a risk filter for SELLING ~30-day option premium on {symbol}.\n"
        f"Recent headlines:\n{titles}\n\n"
        "Reply with ONE word only — VETO if there's a pending binary catalyst "
        "(earnings before expiry, M&A, FDA/legal/regulatory decision) or severe "
        "deterioration that makes selling premium dangerous; CAUTION if elevated "
        "but manageable; CLEAR otherwise."
    )
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=os.environ.get("SCAN_AI_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=8,
            messages=[{"role": "user", "content": prompt}],
        )
        word = (msg.content[0].text or "").strip().lower()
        for lvl in ("veto", "caution", "clear"):
            if lvl in word:
                return lvl
    except Exception as e:  # noqa: BLE001
        log.warning("ai_assess failed for %s: %s", symbol, e)
    return None


def assess_symbol(symbol, max_items=8, use_ai=None):
    """Full gate: fetch headlines -> deterministic verdict -> optional AI escalation."""
    headlines = fetch_headlines(symbol, max_items)
    verdict = assess(symbol, headlines)
    if use_ai is None:
        use_ai = os.getenv("SCAN_AI_NEWS_GATE", "0") == "1"
    if use_ai:
        ai = ai_assess(symbol, headlines)
        if ai:
            verdict["ai_level"] = ai
            verdict["level"] = escalate(verdict["level"], ai)
    return verdict
