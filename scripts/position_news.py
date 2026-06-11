"""
scripts/position_news.py — Hourly news scan for current positions.

For each position symbol:
1. Fetches Yahoo Finance RSS news
2. Filters for material headlines (earnings, downgrade, lawsuit, FDA, etc.)
3. Skips headlines already pushed (state in state/position_news_seen.json)
4. Pushes new material news to Pushover
"""

import calendar
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import feedparser
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = REPO_ROOT / "state" / "position_news_seen.json"
TRADES_FILE = REPO_ROOT / "trades.json"
NEWS_FEED_FILE = REPO_ROOT / "news" / "feed.json"

PUSHOVER_USER = os.environ.get("PUSHOVER_USER_KEY")
PUSHOVER_TOKEN = os.environ.get("PUSHOVER_APP_TOKEN")

MATERIAL_KEYWORDS = [
    "earnings", "guidance", "outlook", "forecast", "miss", "beat", "raises", "cuts",
    "warns", "warning", "preannounce",
    "downgrade", "upgrade", "price target", "analyst",
    "lawsuit", "sued", "settles", "settlement", "fine", "fined", "violation",
    "sec ", "investigation", "probe", "subpoena", "fraud", "indictment",
    "fda", "approval", "rejected", "recall", "warning letter",
    "breach", "hack", "outage", "cyber",
    "merger", "acquisition", "buyout", "spin-off", "takeover",
    "bankruptcy", "chapter 11", "default",
    "dividend", "split", "buyback",
    "layoff", "restructur", "shutdown", "closing",
    "ceo", "cfo", "resign", "step down", "fired",
    "halt", "suspended", "delisted",
    "federal reserve", "fomc",
]


def load_seen():
    if not STATE_FILE.exists():
        return {"items": {}}
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"items": {}}


def save_seen(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def prune_old(state, days=2):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    kept = {}
    for k, v in state.get("items", {}).items():
        try:
            seen_at = datetime.fromisoformat(v["seen_at"].replace("Z", "+00:00"))
            if seen_at > cutoff:
                kept[k] = v
        except (KeyError, ValueError):
            continue
    state["items"] = kept
    return state


def hash_headline(title, link):
    return hashlib.md5(f"{title}|{link}".encode()).hexdigest()


def load_position_symbols():
    """Underlyings of currently OPEN positions — BOTH books: the real tracked
    trades (trades.json) AND the engine's open paper trades (paper/book.json),
    so news coverage follows everything the engine is actively holding."""
    syms = set()
    sources = [TRADES_FILE, REPO_ROOT / "paper" / "book.json"]
    for path in sources:
        if not path.exists():
            continue
        try:
            with open(path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        trades = data.get("trades", data) if isinstance(data, dict) else data
        for t in trades:
            if not isinstance(t, dict):
                continue
            if t.get("status") and t.get("status") != "open":
                continue
            sym = (t.get("underlying") or t.get("symbol") or "").upper()
            if sym:
                syms.add(sym)
    return sorted(syms)


def write_feed(all_items):
    """Write a recent-headlines feed (newest first) for the dashboard right rail."""
    items = sorted(all_items, key=lambda x: x.get("ts", 0), reverse=True)[:40]
    NEWS_FEED_FILE.parent.mkdir(parents=True, exist_ok=True)
    NEWS_FEED_FILE.write_text(json.dumps(
        {"generated_at": datetime.now(timezone.utc).isoformat(), "items": items},
        indent=2,
    ) + "\n")


def fetch_news(symbol, max_items=10):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "")[:400],
                "published": entry.get("published", ""),
                "ts": calendar.timegm(entry.published_parsed) if entry.get("published_parsed") else 0,
            })
        return items
    except Exception as e:
        print(f"  [{symbol}] Error fetching news: {e}", file=sys.stderr)
        return []


def is_material(item):
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    for keyword in MATERIAL_KEYWORDS:
        if keyword in text:
            return keyword
    return None


def push_alert(symbol, items, triggering_keyword):
    if not (PUSHOVER_USER and PUSHOVER_TOKEN):
        print(f"  [{symbol}] Pushover not configured, skipping push")
        return False

    title = f"News on {symbol} ({triggering_keyword})"
    body_lines = [f"- {item['title']}" for item in items[:3]]
    body = "\n\n".join(body_lines)

    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": PUSHOVER_TOKEN,
            "user": PUSHOVER_USER,
            "title": title[:250],
            "message": body[:1024],
            "priority": 0,
            "url": items[0].get("link", "") if items else "",
            "url_title": "Read story" if items else "",
        },
        timeout=15,
    )
    response.raise_for_status()
    print(f"  [{symbol}] Pushed alert: {len(items)} items, trigger '{triggering_keyword}'")
    return True


def main():
    symbols = load_position_symbols()
    if not symbols:
        print("No positions found in trades.json - nothing to scan.")
        return

    print(f"Scanning news for {len(symbols)} positions: {', '.join(symbols)}\n")

    state = load_seen()
    state = prune_old(state)
    alerts_pushed = 0
    feed_items = []   # everything fetched, for the dashboard right-rail feed

    for symbol in symbols:
        items = fetch_news(symbol)
        if not items:
            print(f"  [{symbol}] no news in feed")
            continue

        new_material = []
        triggering = None

        for item in items:
            keyword = is_material(item)
            feed_items.append({
                "symbol": symbol,
                "title": item["title"][:200],
                "link": item["link"],
                "published": item["published"],
                "ts": item.get("ts", 0),
                "material": bool(keyword),
            })
            h = hash_headline(item["title"], item["link"])
            if h in state["items"]:
                continue
            if keyword:
                new_material.append(item)
                if not triggering:
                    triggering = keyword
                state["items"][h] = {
                    "symbol": symbol,
                    "title": item["title"][:200],
                    "seen_at": datetime.now(timezone.utc).isoformat(),
                    "keyword": keyword,
                }

        if new_material:
            push_alert(symbol, new_material, triggering)
            alerts_pushed += 1
        else:
            print(f"  [{symbol}] no new material news")

    save_seen(state)
    write_feed(feed_items)
    print(f"\nDone. {alerts_pushed} alert(s) pushed. {len(feed_items)} headlines in feed. "
          f"State has {len(state['items'])} tracked.")


if __name__ == "__main__":
    main()
