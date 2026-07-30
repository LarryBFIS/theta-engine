"""Decision engine — v5.

Critical changes from v4:
  - If any option leg lacks a live quote (bid/ask/mark), the engine refuses
    to recommend CLOSE — it returns HOLD with "marks unavailable" reasoning.
    This eliminates the v4 bug where missing marks defaulted to $0 and
    falsely showed "100% captured".
  - Cost-to-close uses realistic execution prices:
      * To close a short put vertical: BUY the short put at ASK, SELL the long
        put at BID. That's worst-case (guaranteed fill). Mid is best-case.
      * Both numbers surfaced so the user sees the spread cost.
"""
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from monitor import config
from monitor.tastytrade_client import AccountSnapshot, PositionSnapshot
from monitor.trades import Trade

log = logging.getLogger(__name__)

# Actions
ACTION_HOLD = "HOLD"
ACTION_CLOSE = "CLOSE"
ACTION_ROLL = "ROLL"
ACTION_URGENT_CLOSE = "URGENT_CLOSE"

# Urgency levels
URGENCY_LOW = "low"
URGENCY_NORMAL = "normal"
URGENCY_HIGH = "high"


@dataclass
class TradeMetrics:
    trade_id: str
    underlying: str
    dte: int
    short_strike: float
    long_strike: float
    contracts: int

    credit_per_contract: float
    max_profit_total: float
    max_loss_total: float
    bpr_total: float

    # Identity
    expiry: Optional[str] = None

    # Matching
    is_matched: bool = False
    legs_found: int = 0
    has_live_quotes: bool = False  # True only if both legs have bid+ask+mark

    # Position-level data
    short_bid: Optional[float] = None
    short_ask: Optional[float] = None
    short_mark: Optional[float] = None
    long_bid: Optional[float] = None
    long_ask: Optional[float] = None
    long_mark: Optional[float] = None

    # Computed close economics (None if quotes unavailable)
    cost_to_close_mid: Optional[float] = None   # short_mark - long_mark (best case)
    cost_to_close_worst: Optional[float] = None # short_ask - long_bid (guaranteed)
    profit_if_closed_mid: Optional[float] = None
    profit_if_closed_worst: Optional[float] = None
    pct_max_profit_captured_mid: Optional[float] = None

    # Underlying state
    underlying_price: Optional[float] = None
    short_strike_distance_pct: Optional[float] = None
    short_strike_breached: bool = False


@dataclass
class Recommendation:
    trade_id: str
    underlying: str
    action: str
    urgency: str
    reasoning: list[str] = field(default_factory=list)
    alternative: Optional[str] = None
    metrics: Optional[TradeMetrics] = None


# ────────────────────────────────────────────────────────────────────
# OCC option symbol parsing
# ────────────────────────────────────────────────────────────────────
OCC_RE = re.compile(r"^(?P<root>[A-Z]+)\s+(?P<yymmdd>\d{6})(?P<cp>[CP])(?P<strike>\d{8})$")


def _parse_occ(symbol: str) -> Optional[dict]:
    m = OCC_RE.match(symbol.strip())
    if not m:
        return None
    yymmdd = m.group("yymmdd")
    try:
        year = 2000 + int(yymmdd[:2])
        month = int(yymmdd[2:4])
        day = int(yymmdd[4:6])
        expiry = f"{year:04d}-{month:02d}-{day:02d}"
    except ValueError:
        return None
    return {
        "underlying": m.group("root"),
        "expiry": expiry,
        "right": m.group("cp"),
        "strike": int(m.group("strike")) / 1000.0,
    }


def _find_legs(trade: Trade, positions: list[PositionSnapshot]) -> dict:
    short_pos = None
    long_pos = None
    # Match the trade's actual option type — a CALL vertical (bearish) has call legs,
    # a PUT vertical (bullish) has put legs. This used to hard-match "P", so a call
    # spread (e.g. a QQQ short-call vertical) found 0/2 legs and couldn't be priced,
    # falling back to a fake mark = credit. Derive the right from the structure.
    want = "C" if "call" in (trade.structure or "").lower() else "P"
    for p in positions:
        if not p.symbol:
            continue
        parsed = _parse_occ(p.symbol)
        if not parsed:
            continue
        if parsed["underlying"] != trade.underlying:
            continue
        if parsed["expiry"] != trade.expiry:
            continue
        if parsed["right"] != want:
            continue
        if abs(parsed["strike"] - trade.short_strike) < 0.005:
            short_pos = p
        elif abs(parsed["strike"] - trade.long_strike) < 0.005:
            long_pos = p
    return {"short": short_pos, "long": long_pos}


# ────────────────────────────────────────────────────────────────────
# Metrics
# ────────────────────────────────────────────────────────────────────
def compute_metrics(
    trade: Trade,
    snapshot: AccountSnapshot,
    underlying_price: Optional[float] = None,
) -> TradeMetrics:
    legs = _find_legs(trade, snapshot.positions)
    short_pos = legs["short"]
    long_pos = legs["long"]
    legs_found = sum(1 for p in [short_pos, long_pos] if p is not None)
    is_matched = legs_found == 2

    m = TradeMetrics(
        trade_id=trade.id,
        underlying=trade.underlying,
        dte=trade.dte,
        expiry=trade.expiry,
        short_strike=trade.short_strike,
        long_strike=trade.long_strike,
        contracts=trade.contracts,
        credit_per_contract=trade.credit_per_contract,
        max_profit_total=trade.max_profit_total,
        max_loss_total=trade.max_loss_total,
        bpr_total=trade.bpr_total,
        is_matched=is_matched,
        legs_found=legs_found,
        underlying_price=underlying_price,
    )

    if short_pos:
        m.short_bid = short_pos.bid
        m.short_ask = short_pos.ask
        m.short_mark = short_pos.mark_or_mid
    if long_pos:
        m.long_bid = long_pos.bid
        m.long_ask = long_pos.ask
        m.long_mark = long_pos.mark_or_mid

    # Underlying distance
    if underlying_price:
        # Cushion + breach are direction-aware: a put short is breached when price
        # falls BELOW it; a call short when price rises ABOVE it.
        if "call" in (trade.structure or "").lower():
            m.short_strike_distance_pct = (trade.short_strike - underlying_price) / underlying_price
            m.short_strike_breached = underlying_price > trade.short_strike
        else:
            m.short_strike_distance_pct = (underlying_price - trade.short_strike) / underlying_price
            m.short_strike_breached = underlying_price < trade.short_strike

    # Only compute close economics if we have quotes for BOTH legs
    have_marks = (
        is_matched
        and m.short_mark is not None
        and m.long_mark is not None
    )
    have_quotes = (
        is_matched
        and short_pos and long_pos
        and short_pos.bid is not None and short_pos.ask is not None
        and long_pos.bid is not None and long_pos.ask is not None
    )
    m.has_live_quotes = have_marks  # we'll act on this

    if have_marks:
        # Best case: trade at mid
        cost_mid = m.short_mark - m.long_mark
        m.cost_to_close_mid = cost_mid
        m.profit_if_closed_mid = (trade.credit_per_contract - cost_mid) * 100 * trade.contracts
        m.pct_max_profit_captured_mid = (
            (trade.credit_per_contract - cost_mid) / trade.credit_per_contract
        )

    if have_quotes:
        # Worst case: buy short at ask, sell long at bid
        cost_worst = m.short_ask - m.long_bid
        m.cost_to_close_worst = cost_worst
        m.profit_if_closed_worst = (trade.credit_per_contract - cost_worst) * 100 * trade.contracts

    return m


# ────────────────────────────────────────────────────────────────────
# Decision engine
# ────────────────────────────────────────────────────────────────────
def make_recommendation(trade: Trade, m: TradeMetrics) -> Recommendation:
    # Unmatched
    if not m.is_matched:
        return Recommendation(
            trade_id=trade.id,
            underlying=trade.underlying,
            action=ACTION_HOLD,
            urgency=URGENCY_LOW,
            reasoning=[
                f"Could not match position in tastytrade ({m.legs_found}/2 legs found)",
                "Trade may have been closed manually, or broker symbol doesn't match expected format",
            ],
            metrics=m,
        )

    # CRITICAL: if marks unavailable, don't fake the math
    if not m.has_live_quotes:
        return Recommendation(
            trade_id=trade.id,
            underlying=trade.underlying,
            action=ACTION_HOLD,
            urgency=URGENCY_LOW,
            reasoning=[
                "⚠️ Live option quotes unavailable — can't compute current close cost",
                "This often happens outside market hours, or if the market-data feed is delayed",
                "Will re-evaluate on next poll. No action recommended in the meantime.",
            ],
            metrics=m,
        )

    # Rule 1: Short strike breached → URGENT CLOSE
    if m.short_strike_breached:
        return Recommendation(
            trade_id=trade.id,
            underlying=trade.underlying,
            action=ACTION_URGENT_CLOSE,
            urgency=URGENCY_HIGH,
            reasoning=[
                f"⚠️ {m.underlying} @ ${m.underlying_price:.2f} is BELOW short strike ${m.short_strike:.0f} (ITM).",
                f"Max loss exposure increasing. Current close: ${m.cost_to_close_mid:.2f} mid / ${m.cost_to_close_worst:.2f} worst.",
                f"{m.dte} DTE remaining; negative delta hurts daily.",
            ],
            alternative=(
                f"Hold and hope. Risk: up to ${trade.max_loss_total:.0f} max loss "
                f"(currently ${-min(m.profit_if_closed_mid or 0, 0):.0f} unrealized)."
            ),
            metrics=m,
        )

    # Rule 2: Profit target hit → CLOSE
    if m.pct_max_profit_captured_mid >= trade.manage_at_pct:
        return Recommendation(
            trade_id=trade.id,
            underlying=trade.underlying,
            action=ACTION_CLOSE,
            urgency=URGENCY_NORMAL,
            reasoning=[
                f"✅ Captured {m.pct_max_profit_captured_mid*100:.0f}% of max profit at mid "
                f"(target {trade.manage_at_pct*100:.0f}%).",
                f"Close cost: ${m.cost_to_close_mid:.2f} mid / ${m.cost_to_close_worst:.2f} worst-case fill.",
                f"Profit if closed: ${m.profit_if_closed_mid:.0f} (mid) to ${m.profit_if_closed_worst:.0f} (worst).",
                f"Closes free ${trade.bpr_total:.0f} BPR for the next setup.",
            ],
            alternative=(
                f"Hold for ${trade.max_profit_total - (m.profit_if_closed_mid or 0):.0f} more "
                f"potential profit but risk ${trade.max_loss_total:.0f} if breached before expiry."
            ),
            metrics=m,
        )

    # Rule 3: 21 DTE → CLOSE or ROLL
    if m.dte <= trade.exit_dte:
        action = ACTION_CLOSE
        reasoning = [
            f"⏰ {m.dte} DTE — at the {trade.exit_dte}-DTE cliff. Gamma risk grows from here.",
            f"Currently {m.pct_max_profit_captured_mid*100:.0f}% captured "
            f"(${m.profit_if_closed_mid:.0f} mid).",
        ]
        alt = None
        if m.short_strike_distance_pct and m.short_strike_distance_pct > 0.03:
            alt = (
                f"ROLL: short strike is {m.short_strike_distance_pct*100:.1f}% OTM — "
                f"candidate to roll to next monthly expiry for additional credit."
            )
        else:
            alt = "Hold to expiry, but the next 21 days carry concentrated gamma risk."
        return Recommendation(
            trade_id=trade.id,
            underlying=trade.underlying,
            action=action,
            urgency=URGENCY_NORMAL,
            reasoning=reasoning,
            alternative=alt,
            metrics=m,
        )

    # Rule 4: Max loss approaching → CLOSE
    if m.profit_if_closed_mid is not None:
        unrealized_loss = -m.profit_if_closed_mid
        loss_threshold = trade.credit_per_contract * trade.contracts * 100 * 1.5
        if unrealized_loss > loss_threshold:
            return Recommendation(
                trade_id=trade.id,
                underlying=trade.underlying,
                action=ACTION_CLOSE,
                urgency=URGENCY_HIGH,
                reasoning=[
                    f"📉 Unrealized loss is ${unrealized_loss:.0f} — >1.5× credit received.",
                    f"Mechanical loss-cutting trigger to avoid the full ${trade.max_loss_total:.0f} max loss.",
                    f"Close cost: ${m.cost_to_close_mid:.2f} mid / ${m.cost_to_close_worst:.2f} worst.",
                ],
                metrics=m,
            )

    # Default: HOLD with informative status
    reasoning = []
    if m.pct_max_profit_captured_mid >= 0.25:
        reasoning.append(
            f"Holding: {m.pct_max_profit_captured_mid*100:.0f}% captured, "
            f"{m.dte} DTE — let theta work."
        )
    elif m.pct_max_profit_captured_mid >= 0:
        reasoning.append(
            f"Holding: trade is profitable but early "
            f"({m.pct_max_profit_captured_mid*100:.0f}% of max). Let it work."
        )
    else:
        loss = -m.profit_if_closed_mid
        reasoning.append(
            f"Holding: unrealized loss is ${loss:.0f} but within tolerance. "
            f"{m.dte} DTE remaining."
        )
    reasoning.append(
        f"Close cost: ${m.cost_to_close_mid:.2f} mid / ${m.cost_to_close_worst:.2f} worst. "
        f"Spread: ${(m.cost_to_close_worst - m.cost_to_close_mid):.2f}."
    )

    return Recommendation(
        trade_id=trade.id,
        underlying=trade.underlying,
        action=ACTION_HOLD,
        urgency=URGENCY_LOW,
        reasoning=reasoning,
        metrics=m,
    )


# ────────────────────────────────────────────────────────────────────
# Formatting
# ────────────────────────────────────────────────────────────────────
def format_recommendation(rec: Recommendation) -> str:
    m = rec.metrics
    lines: list[str] = []

    if rec.action == ACTION_URGENT_CLOSE:
        lines.append(f"🚨 URGENT: CLOSE {m.underlying} {int(m.short_strike)}/{int(m.long_strike)}p")
    elif rec.action == ACTION_CLOSE:
        lines.append(f"🎯 CLOSE {m.underlying} {int(m.short_strike)}/{int(m.long_strike)}p")
    elif rec.action == ACTION_ROLL:
        lines.append(f"🔄 ROLL {m.underlying} {int(m.short_strike)}/{int(m.long_strike)}p")
    else:
        lines.append(f"✓ HOLD {m.underlying} {int(m.short_strike)}/{int(m.long_strike)}p")

    lines.append("")
    if m.has_live_quotes:
        lines.append(f"Close cost (mid): ${m.cost_to_close_mid:.2f}")
        lines.append(f"Close cost (worst): ${m.cost_to_close_worst:.2f}")
        lines.append(f"Captured (mid): {m.pct_max_profit_captured_mid*100:.0f}% (${m.profit_if_closed_mid:.0f})")
    else:
        lines.append("Quotes unavailable — see reasoning below")
    lines.append(f"Expiry: {m.expiry or '?'} · DTE: {m.dte} · BPR: ${m.bpr_total:.0f}")
    if m.underlying_price:
        lines.append(f"{m.underlying} @ ${m.underlying_price:.2f}")

    lines.append("")
    lines.append("Why:")
    for r in rec.reasoning:
        lines.append(f"• {r}")

    if rec.alternative:
        lines.append("")
        lines.append(f"Alt: {rec.alternative}")

    return "\n".join(lines)


def format_summary(metrics_list: list[TradeMetrics], snapshot: AccountSnapshot) -> str:
    starting = config.STARTING_CAPITAL
    current = snapshot.net_liquidating_value
    total_pnl = current - starting
    total_pct = total_pnl / starting if starting else 0

    lines: list[str] = []
    lines.append(f"Net liq: ${current:,.0f} ({total_pct*100:+.1f}% vs start)")
    lines.append(f"Today P&L: ${snapshot.day_pnl:+,.0f}")
    total_bpr = sum(m.bpr_total for m in metrics_list)
    lines.append(f"BPR used: ${total_bpr:.0f} ({total_bpr/current*100:.0f}% of net liq)")
    lines.append("")

    for m in metrics_list:
        if not m.is_matched:
            lines.append(f"⚠️ {m.underlying} {int(m.short_strike)}/{int(m.long_strike)}p — position not found")
            continue
        if not m.has_live_quotes:
            lines.append(f"⏳ {m.underlying} {int(m.short_strike)}/{int(m.long_strike)}p — quotes unavailable ({m.dte}d)")
            continue
        captured_pct = m.pct_max_profit_captured_mid * 100
        lines.append(
            f"{m.underlying} {int(m.short_strike)}/{int(m.long_strike)}p: "
            f"{captured_pct:+.0f}% (${m.profit_if_closed_mid:+.0f}) · {m.dte}d"
        )

    return "\n".join(lines)
