"""
Market state fetcher for Phase 5 AI trader.

Pulls VIX, major indices, sector ETFs, and trend data via yfinance.
Output is a clean dict suitable for Claude API context bundle.
"""
import yfinance as yf
from datetime import datetime
from typing import Dict, Any


# Symbols we care about for short-premium options trading context
INDICES = ["^VIX", "SPY", "QQQ", "IWM"]
SECTORS = {
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "XLV": "Healthcare",
    "XLI": "Industrials",
    "XLP": "Consumer Staples",
    "XLY": "Consumer Discretionary",
}


def fetch_ticker_snapshot(symbol: str) -> Dict[str, Any]:
    """Fetch single ticker: current price, daily change, 5-day trend."""
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="5d", interval="1d")
        if hist.empty:
            return {"symbol": symbol, "error": "no data"}

        last = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else last
        five_day_open = float(hist["Open"].iloc[0])

        day_change_pct = ((last - prev) / prev) * 100 if prev else 0
        five_day_change_pct = ((last - five_day_open) / five_day_open) * 100 if five_day_open else 0

        return {
            "symbol": symbol,
            "price": round(last, 2),
            "day_change_pct": round(day_change_pct, 2),
            "5d_change_pct": round(five_day_change_pct, 2),
        }
    except Exception as e:
        return {"symbol": symbol, "error": str(e)}


def fetch_market_state() -> Dict[str, Any]:
    """
    Build full market state bundle.

    Returns:
        {
          "timestamp": "ISO timestamp",
          "vix": {"level": 16.5, "day_change_pct": 2.3},
          "indices": {"SPY": {...}, "QQQ": {...}, "IWM": {...}},
          "sectors": {"XLK": {"name": "Technology", "5d_change_pct": -1.2, ...}, ...},
          "market_regime": "risk_on|risk_off|neutral"
        }
    """
    state = {
        "timestamp": datetime.utcnow().isoformat(),
        "indices": {},
        "sectors": {},
    }

    # VIX (separate handling — it's the most important single signal)
    vix_snap = fetch_ticker_snapshot("^VIX")
    state["vix"] = {
        "level": vix_snap.get("price", 0),
        "day_change_pct": vix_snap.get("day_change_pct", 0),
        "5d_change_pct": vix_snap.get("5d_change_pct", 0),
    }

    # Major indices
    for sym in ["SPY", "QQQ", "IWM"]:
        state["indices"][sym] = fetch_ticker_snapshot(sym)

    # Sectors
    for sym, name in SECTORS.items():
        snap = fetch_ticker_snapshot(sym)
        snap["sector_name"] = name
        state["sectors"][sym] = snap

    # Simple market regime heuristic
    vix_level = state["vix"]["level"]
    spy_5d = state["indices"].get("SPY", {}).get("5d_change_pct", 0)

    if vix_level > 20 or spy_5d < -2:
        regime = "risk_off"
    elif vix_level < 14 and spy_5d > 1:
        regime = "risk_on"
    else:
        regime = "neutral"

    state["market_regime"] = regime
    return state


if __name__ == "__main__":
    import json
    print(json.dumps(fetch_market_state(), indent=2))
