"""Market data — VIX level, prior close, etc. via yfinance (free)."""
import logging
from dataclasses import dataclass
from typing import Optional

import yfinance as yf

log = logging.getLogger(__name__)


@dataclass
class VIXSnapshot:
    current: float
    prev_close: float

    @property
    def day_change_pct(self) -> float:
        if self.prev_close <= 0:
            return 0.0
        return (self.current - self.prev_close) / self.prev_close


def get_vix() -> Optional[VIXSnapshot]:
    """Fetch current VIX level and previous close. Returns None on failure."""
    try:
        ticker = yf.Ticker("^VIX")
        hist = ticker.history(period="5d", interval="1d")
        if hist.empty or len(hist) < 2:
            return None
        current = float(hist["Close"].iloc[-1])
        prev_close = float(hist["Close"].iloc[-2])
        return VIXSnapshot(current=current, prev_close=prev_close)
    except Exception as e:
        log.error("Could not fetch VIX: %s", e)
        return None


def get_quote(symbol: str) -> Optional[float]:
    """Fetch latest price for a symbol. Returns None on failure."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        price = getattr(info, "last_price", None)
        if price:
            return float(price)
        hist = ticker.history(period="1d", interval="1m")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])
        return None
    except Exception as e:
        log.error("Could not fetch quote for %s: %s", symbol, e)
        return None
