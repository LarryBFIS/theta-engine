"""Load/save trades.json and suggestions.json — the persistent trade ledger.

trades.json: tracked positions with metadata (POP/max profit/BPR at open) that
isn't recoverable from the broker API. Edited manually when you open a new
trade. Committed to the repo so it survives ephemeral GitHub Actions runs.

suggestions.json: append-only log of every recommendation the bot has made.
Each entry captures the trade state at the moment of recommendation. Used for
performance analysis (which suggestions did you accept? how did those compare
to the rejected ones?).
"""
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)

TRADES_FILE = Path("trades.json")
SUGGESTIONS_FILE = Path("suggestions.json")


@dataclass
class Trade:
    """A tracked trade. Mirrors trades.json schema."""

    id: str
    underlying: str
    structure: str  # e.g., "short_put_vertical"
    short_strike: float
    long_strike: float
    expiry: str  # ISO date "YYYY-MM-DD"
    contracts: int
    opened_at: str  # ISO date
    credit_per_contract: float
    max_profit_total: float
    max_loss_total: float
    bpr_total: float
    pop_at_open: float
    p50_at_open: float
    manage_at_pct: float
    exit_dte: int
    status: str  # "open", "closed", "expired", "rolled"
    notes: str = ""
    closed_at: Optional[str] = None
    realized_pnl: Optional[float] = None
    open_order_id: Optional[str] = None
    close_order_id: Optional[str] = None
    close_debit_per_contract: Optional[float] = None
    open_legs: Optional[list] = None
    close_legs: Optional[list] = None

    @property
    def is_open(self) -> bool:
        return self.status == "open"

    @property
    def expiry_date(self) -> datetime:
        return datetime.strptime(self.expiry, "%Y-%m-%d").replace(tzinfo=timezone.utc)

    @property
    def dte(self) -> int:
        delta = self.expiry_date - datetime.now(timezone.utc)
        return max(delta.days, 0)


@dataclass
class Suggestion:
    """A single recommendation entry in the ledger."""

    id: str
    trade_id: str
    timestamp: str  # ISO datetime
    action: str  # "CLOSE", "HOLD", "ROLL", "URGENT_CLOSE"
    urgency: str  # "low", "normal", "high"
    reasoning: list[str]
    metrics_snapshot: dict  # state at recommendation time
    alternative: Optional[str] = None
    status: str = "pending"  # "pending", "accepted", "rejected", "expired", "superseded"
    decided_at: Optional[str] = None


def load_trades() -> list[Trade]:
    """Load tracked trades from trades.json. Returns empty list if missing."""
    if not TRADES_FILE.exists():
        log.warning("trades.json not found; no trades tracked")
        return []
    with TRADES_FILE.open() as f:
        data = json.load(f)
    return [Trade(**t) for t in data.get("trades", [])]


def save_trades(trades: list[Trade]) -> None:
    """Persist trade list to trades.json."""
    payload = {"schema_version": 1, "trades": [asdict(t) for t in trades]}
    TRADES_FILE.write_text(json.dumps(payload, indent=2, default=str) + "\n")


def load_suggestions() -> list[Suggestion]:
    """Load suggestion ledger from suggestions.json."""
    if not SUGGESTIONS_FILE.exists():
        return []
    with SUGGESTIONS_FILE.open() as f:
        data = json.load(f)
    return [Suggestion(**s) for s in data.get("suggestions", [])]


def append_suggestion(suggestion: Suggestion) -> None:
    """Append a new suggestion to the ledger and write back."""
    existing = load_suggestions()
    existing.append(suggestion)
    payload = {"schema_version": 1, "suggestions": [asdict(s) for s in existing]}
    SUGGESTIONS_FILE.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    log.info("Logged suggestion %s for %s: %s", suggestion.id, suggestion.trade_id, suggestion.action)


def make_suggestion_id(trade_id: str, timestamp: datetime) -> str:
    """Generate a stable suggestion ID."""
    return f"sug_{timestamp.strftime('%Y%m%dT%H%M%S')}_{trade_id}"
