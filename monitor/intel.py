"""
monitor/intel.py — Daily intel fetcher for theta-engine.

Pulls news, earnings calendar, fundamentals, and macro events for
positions + watchlist. Used by scripts/briefing.py for daily synthesis.
"""

import json
from datetime import datetime, timedelta, date
from pathlib import Path

import feedparser
import yfinance as yf

REPO_ROOT = Path(__file__).resolve().parent.parent


def load_watchlist():
    path = REPO_ROOT / "config" / "watchlist.json"
    with open(path) as f:
        return json.load(f)


def load_positions():
    path = REPO_ROOT / "trades.json"
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data.get("trades", [])
    return data


def get_position_symbols(positions):
    return list({t.get("symbol", "").upper() for t in positions if t.get("symbol")})


def fetch_news(symbol, max_items=3):
    """Yahoo Finance RSS news feed for a ticker."""
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US"
    try:
        feed = feedparser.parse(url)
        items = []
        for entry in feed.entries[:max_items]:
            items.append({
                "title": entry.get("title", "")[:200],
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")[:300],
            })
        return items
    except Exception as e:
        return [{"error": str(e)}]


def fetch_ticker_data(symbol):
    """Price, 52w range, earnings date, fundamentals via yfinance."""
    try:
        t = yf.Ticker(symbol)
        info = t.info or {}

        # Next earnings date (yfinance .calendar returns a dict or DataFrame)
        earnings_date = None
        try:
            cal = t.calendar
            if cal is not None:
                if hasattr(cal, "empty") and not cal.empty:
                    earnings_date = str(cal.iloc[0, 0])[:10]
                elif isinstance(cal, dict) and "Earnings Date" in cal:
                    ed = cal["Earnings Date"]
                    if ed:
                        earnings_date = str(ed[0])[:10] if isinstance(ed, list) else str(ed)[:10]
        except Exception:
            pass

        return {
            "symbol": symbol,
            "price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "previous_close": info.get("previousClose"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "sector": info.get("sector"),
            "market_cap": info.get("marketCap"),
            "next_earnings": earnings_date,
            "trailing_pe": info.get("trailingPE"),
            "implied_volatility_30d": None,  # yfinance doesn't expose this cleanly; placeholder
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def upcoming_macro(macro_dict, days_ahead=45):
    """Return macro events in the next N days."""
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)
    upcoming = []
    for event_type, dates in macro_dict.items():
        for d in dates:
            try:
                event_date = datetime.strptime(d, "%Y-%m-%d").date()
                if today <= event_date <= cutoff:
                    upcoming.append({
                        "type": event_type,
                        "date": d,
                        "days_away": (event_date - today).days,
                    })
            except ValueError:
                continue
    return sorted(upcoming, key=lambda x: x["date"])


def flag_earnings_in_window(ticker_data, window_days=45):
    """List tickers with earnings inside our typical 30-45 DTE trade window."""
    today = date.today()
    cutoff = today + timedelta(days=window_days)
    flagged = []
    for sym, data in ticker_data.items():
        ed = data.get("next_earnings")
        if not ed:
            continue
        try:
            edate = datetime.strptime(ed, "%Y-%m-%d").date()
            if today <= edate <= cutoff:
                flagged.append({
                    "symbol": sym,
                    "earnings_date": ed,
                    "days_away": (edate - today).days,
                })
        except ValueError:
            continue
    return sorted(flagged, key=lambda x: x["days_away"])


def build_intel_payload():
    """Assemble the full intel payload for the daily briefing."""
    watchlist_data = load_watchlist()
    positions = load_positions()
    position_symbols = get_position_symbols(positions)
    watchlist_symbols = [w["symbol"] for w in watchlist_data["watchlist"]]

    all_symbols = list(dict.fromkeys(position_symbols + watchlist_symbols))

    ticker_data = {}
    for sym in all_symbols:
        ticker_data[sym] = fetch_ticker_data(sym)
        ticker_data[sym]["news"] = fetch_news(sym, max_items=3)

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "positions": positions,
        "position_symbols": position_symbols,
        "watchlist": watchlist_data["watchlist"],
        "avoid_list": watchlist_data.get("avoid_list", []),
        "ticker_data": ticker_data,
        "upcoming_macro": upcoming_macro(watchlist_data.get("macro_2026", {})),
        "earnings_in_window": flag_earnings_in_window(ticker_data, window_days=45),
    }


if __name__ == "__main__":
    payload = build_intel_payload()
    print(json.dumps(payload, indent=2, default=str))
