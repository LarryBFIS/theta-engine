"""Tastytrade API client — OAuth2 + market data quotes.

Critical fixes from v4:

1. Positions endpoint returns metadata only (no live marks).
   We now also call /market-data/by-type to fetch live bid/ask/mark for each
   option leg, then merge those into the position objects.

2. The 'quantity' field is unsigned. The direction lives in
   'quantity-direction' = "Short" or "Long". We use that to sign the quantity
   so downstream code can distinguish bought vs sold positions correctly.

3. We surface bid AND ask — not just mark — so decision logic can reason about
   bid-ask spread (closing a short put means paying the ASK to buy it back,
   not the mid).
"""
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests

from monitor import config

log = logging.getLogger(__name__)

API_BASE = "https://api.tastyworks.com"
# (connect, read) timeouts. Connect a touch more generous since the GitHub
# runner -> api.tastyworks.com hop occasionally stalls.
DEFAULT_TIMEOUT = (10, 30)
# Retry transient network errors so a single slow connect doesn't fail a tick.
MAX_RETRIES = 3
RETRY_BACKOFF = (1, 3, 6)
ACCESS_TOKEN_LIFETIME_MIN = 15
REFRESH_BEFORE_MIN = 2

OPTION_INSTRUMENT_TYPES = {"Equity Option", "Future Option"}


@dataclass
class PositionSnapshot:
    """A normalized view of one open position."""

    symbol: str
    underlying: str
    instrument_type: str
    quantity: float  # signed: positive for long, negative for short
    average_open_price: float
    multiplier: int
    expires_at: Optional[datetime]
    realized_day_gain: float
    unrealized_day_gain: float
    cost_effect: str

    # Live quote data (None if quote fetch failed)
    bid: Optional[float] = None
    ask: Optional[float] = None
    mark: Optional[float] = None
    last: Optional[float] = None
    quote_age_seconds: Optional[float] = None

    raw: object = field(repr=False, default=None)

    @property
    def is_option(self) -> bool:
        return self.instrument_type in OPTION_INSTRUMENT_TYPES

    @property
    def is_short(self) -> bool:
        return self.quantity < 0

    @property
    def has_quote(self) -> bool:
        return self.mark is not None or (self.bid is not None and self.ask is not None)

    @property
    def mark_or_mid(self) -> Optional[float]:
        """Best estimate of current value. Prefer mark; fall back to bid/ask mid."""
        if self.mark is not None:
            return self.mark
        if self.bid is not None and self.ask is not None:
            return (self.bid + self.ask) / 2
        return None


@dataclass
class AccountSnapshot:
    account_number: str
    net_liquidating_value: float
    cash_balance: float
    derivative_buying_power: float
    equity_buying_power: float
    realized_day_gain: float
    unrealized_day_gain: float
    positions: list[PositionSnapshot]

    @property
    def day_pnl(self) -> float:
        return self.realized_day_gain + self.unrealized_day_gain


class TastytradeClient:
    """OAuth2 REST client + market data quotes."""

    def __init__(self):
        self._access_token: Optional[str] = None
        self._access_token_expires_at: Optional[datetime] = None

    # ────────────────────────────────────────────────────────────────
    # Auth
    # ────────────────────────────────────────────────────────────────
    @staticmethod
    def _request_with_retries(method: str, url: str, **kwargs):
        """requests wrapper that retries transient network errors (timeouts /
        connection resets) with backoff, so a single slow hop to tastytrade
        doesn't fail the whole tick. HTTP error statuses are NOT retried here."""
        kwargs.setdefault("timeout", DEFAULT_TIMEOUT)
        last_exc = None
        for attempt in range(MAX_RETRIES):
            try:
                return requests.request(method, url, **kwargs)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_exc = e
                wait = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                log.warning(
                    "tastytrade %s %s network error (attempt %d/%d): %s — retrying in %ds",
                    method, url, attempt + 1, MAX_RETRIES, e.__class__.__name__, wait,
                )
                time.sleep(wait)
        raise last_exc

    def _refresh_access_token(self) -> str:
        log.info("Refreshing tastytrade OAuth2 access token")
        r = self._request_with_retries(
            "POST",
            f"{API_BASE}/oauth/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": config.TASTYTRADE_REFRESH_TOKEN,
                "client_secret": config.TASTYTRADE_CLIENT_SECRET,
            },
        )
        if not r.ok:
            log.error("OAuth2 refresh failed: %s %s — %s", r.status_code, r.reason, r.text[:500])
        r.raise_for_status()
        data = r.json()
        token = data.get("access_token")
        if not token:
            raise RuntimeError(f"No access_token in OAuth2 response: {data}")
        expires_in = int(data.get("expires_in", ACCESS_TOKEN_LIFETIME_MIN * 60))
        self._access_token = token
        self._access_token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return token

    def _get_token(self) -> str:
        if self._access_token and self._access_token_expires_at:
            remaining = self._access_token_expires_at - datetime.now(timezone.utc)
            if remaining > timedelta(minutes=REFRESH_BEFORE_MIN):
                return self._access_token
        return self._refresh_access_token()

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._get_token()}",
            "Accept": "application/json",
            "User-Agent": "theta-engine/1.0",
        }

    # ────────────────────────────────────────────────────────────────
    # REST primitives
    # ────────────────────────────────────────────────────────────────
    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{API_BASE}{path}"
        r = self._request_with_retries("GET", url, headers=self._headers(), params=params)
        if not r.ok:
            log.error("GET %s failed: %s %s — %s", path, r.status_code, r.reason, r.text[:500])
        r.raise_for_status()
        return r.json()

    @staticmethod
    def _to_float(value) -> float:
        if value is None or value == "":
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _to_float_or_none(value) -> Optional[float]:
        """Like _to_float but returns None for missing values instead of 0."""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_dt(value: Any) -> Optional[datetime]:
        if not value or not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    # ────────────────────────────────────────────────────────────────
    # Market data: fetch quotes for symbols
    # ────────────────────────────────────────────────────────────────
    def fetch_option_quotes(self, symbols: list[str]) -> dict[str, dict]:
        """Fetch live quotes for option symbols via /market-data/by-type.

        Returns: dict mapping symbol -> {bid, ask, mark, last, updated_at}
        """
        if not symbols:
            return {}

        try:
            # tastytrade's by-type endpoint accepts comma-separated symbols per asset type
            data = self._get(
                "/market-data/by-type",
                params={"equity-option": ",".join(symbols)},
            )
            items = data.get("data", {}).get("items", [])
        except Exception as e:
            log.error("Failed to fetch option quotes: %s", e)
            return {}

        result: dict[str, dict] = {}
        for item in items:
            sym = item.get("symbol", "")
            if not sym:
                continue
            result[sym] = {
                "bid": self._to_float_or_none(item.get("bid")),
                "ask": self._to_float_or_none(item.get("ask")),
                "mark": self._to_float_or_none(item.get("mark")),
                "last": self._to_float_or_none(item.get("last")),
                "updated_at": item.get("updated-at"),
            }
        log.info("Fetched live quotes for %d/%d option symbols", len(result), len(symbols))
        return result

    # ────────────────────────────────────────────────────────────────
    # Main snapshot fetch
    # ────────────────────────────────────────────────────────────────
    def fetch_snapshot(self) -> AccountSnapshot:
        """Pull account + balances + positions + LIVE option quotes."""
        # 1. List accounts
        accounts_data = self._get("/customers/me/accounts").get("data", {})
        items = accounts_data.get("items", [])
        if not items:
            raise RuntimeError("No tastytrade accounts found for this OAuth grant")
        account_number = items[0].get("account", {}).get("account-number")
        if not account_number:
            raise RuntimeError(f"First account item missing account-number: {items[0]}")

        # 2. Balances
        balances = self._get(f"/accounts/{account_number}/balances").get("data", {})

        # 3. Positions (metadata only; no marks)
        positions_payload = self._get(f"/accounts/{account_number}/positions").get("data", {})
        positions_raw = positions_payload.get("items", [])
        positions = [self._normalize_position(p) for p in positions_raw]

        # 4. Fetch live quotes for any option positions and merge marks in
        option_symbols = [p.symbol for p in positions if p.is_option and p.symbol]
        if option_symbols:
            quotes = self.fetch_option_quotes(option_symbols)
            for p in positions:
                q = quotes.get(p.symbol)
                if q:
                    p.bid = q["bid"]
                    p.ask = q["ask"]
                    p.mark = q["mark"]
                    p.last = q["last"]

        return AccountSnapshot(
            account_number=account_number,
            net_liquidating_value=self._to_float(balances.get("net-liquidating-value")),
            cash_balance=self._to_float(balances.get("cash-balance")),
            derivative_buying_power=self._to_float(balances.get("derivative-buying-power")),
            equity_buying_power=self._to_float(balances.get("equity-buying-power")),
            realized_day_gain=self._to_float(balances.get("realized-day-gain")),
            unrealized_day_gain=self._to_float(balances.get("unrealized-day-gain")),
            positions=positions,
        )

    def _normalize_position(self, p: dict) -> PositionSnapshot:
        """Normalize a single position. Crucially, signs the quantity using
        quantity-direction ('Short' → negative, 'Long' → positive)."""
        raw_qty = self._to_float(p.get("quantity"))
        direction = (p.get("quantity-direction") or "Long").strip().lower()
        signed_qty = -raw_qty if direction == "short" else raw_qty

        return PositionSnapshot(
            symbol=p.get("symbol", ""),
            underlying=p.get("underlying-symbol", ""),
            instrument_type=str(p.get("instrument-type", "")),
            quantity=signed_qty,
            average_open_price=self._to_float(p.get("average-open-price")),
            multiplier=int(self._to_float(p.get("multiplier")) or 1),
            expires_at=self._parse_dt(p.get("expires-at")),
            realized_day_gain=self._to_float(p.get("realized-day-gain")),
            unrealized_day_gain=self._to_float(p.get("unrealized-day-gain")),
            cost_effect=str(p.get("cost-effect", "")),
            raw=p,
        )
