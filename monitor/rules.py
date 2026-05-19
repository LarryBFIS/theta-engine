"""Rules engine — evaluates trigger conditions and fires Pushover notifications.

Each rule:
1. Reads from the AccountSnapshot
2. Decides if a notification should fire
3. Checks cooldown to avoid spamming
4. Sends via notifier
5. Marks state.fired
"""
import logging
import re
from typing import Optional

from monitor import config, notifier
from monitor.market_data import get_vix
from monitor.state import State
from monitor.tastytrade_client import AccountSnapshot, PositionSnapshot

log = logging.getLogger(__name__)


def _position_key(p: PositionSnapshot, suffix: str) -> str:
    """Stable key for a position so cooldowns survive restarts."""
    return f"{suffix}::{p.symbol}"


def _parse_option_strike(symbol: str) -> Optional[float]:
    """Extract strike price from an OCC-style option symbol.

    Example: "SPY   260618P00721000" -> 721.0
    Format: <root> <YYMMDD> <C|P> <strike*1000 padded to 8 digits>
    """
    if not symbol:
        return None
    # Match the trailing 8-digit strike (in thousandths)
    m = re.search(r"([CP])(\d{8})$", symbol.strip())
    if not m:
        return None
    try:
        return int(m.group(2)) / 1000.0
    except ValueError:
        return None


def _is_option(p: PositionSnapshot) -> bool:
    itype = (p.instrument_type or "").lower()
    return "option" in itype


def _is_short(p: PositionSnapshot) -> bool:
    return p.quantity < 0


def _max_profit_per_contract(p: PositionSnapshot) -> float:
    """For a short option position, max profit = credit received (per contract).

    Note: this is approximate. For complex multi-leg positions, the platform
    has the real number — we estimate from the open price.
    """
    return abs(p.average_open_price) * p.multiplier


def _current_value_per_contract(p: PositionSnapshot) -> float:
    """Current mark-to-market value (per contract, abs)."""
    if p.mark_price is None:
        return 0.0
    return abs(p.mark_price) * p.multiplier


# ───────────────────────── Rules ─────────────────────────


def rule_short_strike_touched(snapshot: AccountSnapshot, state: State, get_quote_fn=None) -> None:
    """Alert when underlying price approaches or breaches the short strike of a short option."""
    if get_quote_fn is None:
        from monitor.market_data import get_quote as get_quote_fn

    for p in snapshot.positions:
        if not _is_option(p) or not _is_short(p):
            continue

        strike = _parse_option_strike(p.symbol)
        if not strike:
            continue

        is_put = "P" in p.symbol[-9:-8] if len(p.symbol) >= 9 else False
        underlying_price = get_quote_fn(p.underlying)
        if underlying_price is None:
            continue

        buffer = strike * config.SHORT_STRIKE_BUFFER_PCT

        # For a short put: trouble = price drops near or below strike
        # For a short call: trouble = price rises near or above strike
        triggered = False
        if is_put and underlying_price <= strike + buffer:
            triggered = True
        elif not is_put and underlying_price >= strike - buffer:
            triggered = True

        if not triggered:
            continue

        key = _position_key(p, "short_strike_touched")
        if not state.cooldown_ok(key, config.COOLDOWN_MINUTES["short_strike_touched"]):
            continue

        breached = (is_put and underlying_price <= strike) or (not is_put and underlying_price >= strike)
        label = "BREACHED" if breached else "approaching"

        title = f"Short strike {label}: {p.underlying}"
        body = (
            f"{p.underlying} at ${underlying_price:.2f}, short strike ${strike:.2f}.\n"
            f"Position P&L day: ${p.day_pnl:+.2f}\n"
            f"DTE: {p.dte}\n"
            f"Consider: roll down/out for credit, or close to limit damage."
        )

        if notifier.send(title, body, priority=notifier.PRIORITY_HIGH, sound=notifier.SOUND_ALERT):
            state.mark_fired(key)


def rule_profit_target_hit(snapshot: AccountSnapshot, state: State) -> None:
    """Alert when a short option position has captured ~50% of credit (close it!)."""
    for p in snapshot.positions:
        if not _is_option(p) or not _is_short(p):
            continue

        credit = _max_profit_per_contract(p)
        current = _current_value_per_contract(p)
        if credit <= 0:
            continue

        # Capture % = (credit - current) / credit
        capture_pct = (credit - current) / credit

        if capture_pct < config.PROFIT_TARGET_PCT:
            continue

        key = _position_key(p, "profit_target_hit")
        if not state.cooldown_ok(key, config.COOLDOWN_MINUTES["profit_target_hit"]):
            continue

        captured_dollars = (credit - current) * abs(p.quantity)
        title = f"Profit target hit: {p.underlying}"
        body = (
            f"{p.symbol} has captured {capture_pct:.0%} of max credit.\n"
            f"Profit so far: ${captured_dollars:+.2f}\n"
            f"Close now to bank the win. Your GTC at 50% should fill imminently — confirm in tastytrade."
        )

        if notifier.send(title, body, priority=notifier.PRIORITY_HIGH, sound=notifier.SOUND_SUCCESS):
            state.mark_fired(key)


def rule_max_loss_warning(snapshot: AccountSnapshot, state: State) -> None:
    """Alert when a short option position is approaching max loss (rough proxy via P&L)."""
    for p in snapshot.positions:
        if not _is_option(p) or not _is_short(p):
            continue

        # Rough heuristic: if unrealized loss exceeds 1.5x the credit received, flag it
        # (For a 5-wide spread with $1 credit: $4 max loss; 1.5x credit = $1.50 loss = ~37% to max)
        credit = _max_profit_per_contract(p)
        if credit <= 0:
            continue

        loss_per_contract = max(-p.unrealized_day_gain / max(abs(p.quantity), 1), 0)
        # Convert loss to multiples of credit
        if loss_per_contract < credit * 1.5:
            continue

        key = _position_key(p, "max_loss_warning")
        if not state.cooldown_ok(key, config.COOLDOWN_MINUTES["max_loss_warning"]):
            continue

        title = f"Max loss approaching: {p.underlying}"
        body = (
            f"{p.symbol} unrealized loss day: ${p.unrealized_day_gain:.2f}\n"
            f"DTE: {p.dte}\n"
            f"Consider closing to limit damage, or rolling for credit if DTE > 21."
        )

        if notifier.send(title, body, priority=notifier.PRIORITY_HIGH, sound=notifier.SOUND_ALERT):
            state.mark_fired(key)


def rule_twenty_one_dte(snapshot: AccountSnapshot, state: State) -> None:
    """Alert when any open option position hits 21 DTE — tastytrade mechanical exit."""
    for p in snapshot.positions:
        if not _is_option(p):
            continue
        if p.dte is None or p.dte > config.TWENTY_ONE_DTE:
            continue

        key = _position_key(p, "twenty_one_dte")
        if not state.cooldown_ok(key, config.COOLDOWN_MINUTES["twenty_one_dte"]):
            continue

        title = f"21 DTE reached: {p.underlying}"
        body = (
            f"{p.symbol} is now at {p.dte} DTE.\n"
            f"Tastytrade rule of thumb: close mechanically regardless of P&L.\n"
            f"Day P&L: ${p.day_pnl:+.2f}\n"
            f"Open trade ticket to close."
        )

        if notifier.send(title, body, priority=notifier.PRIORITY_NORMAL, sound=notifier.SOUND_REMINDER):
            state.mark_fired(key)


def rule_vix_spike(snapshot: AccountSnapshot, state: State) -> None:
    """Alert on VIX level breakout or large day-over-day move."""
    vix = get_vix()
    if not vix:
        return

    triggered = vix.current >= config.VIX_SPIKE_LEVEL or vix.day_change_pct >= config.VIX_SPIKE_PCT
    if not triggered:
        return

    key = "vix_spike"
    if not state.cooldown_ok(key, config.COOLDOWN_MINUTES["vix_spike"]):
        return

    title = f"VIX at {vix.current:.1f} ({vix.day_change_pct:+.1%})"
    body = (
        f"VIX moved through {config.VIX_SPIKE_LEVEL} or jumped {config.VIX_SPIKE_PCT:.0%}+ today.\n"
        f"IV expansion = premium-selling opportunity. Consider new short premium setups."
    )

    if notifier.send(title, body, priority=notifier.PRIORITY_LOW, sound=notifier.SOUND_INFO):
        state.mark_fired(key)


def rule_daily_account_loss(snapshot: AccountSnapshot, state: State) -> None:
    """Alert if account is down more than DAILY_LOSS_PCT today."""
    if snapshot.net_liquidating_value <= 0:
        return

    day_pnl_pct = snapshot.day_pnl / snapshot.net_liquidating_value
    if day_pnl_pct > -config.DAILY_LOSS_PCT:
        return

    key = "daily_account_loss"
    if not state.cooldown_ok(key, config.COOLDOWN_MINUTES["daily_loss"]):
        return

    title = f"Account down {abs(day_pnl_pct):.1%} today"
    body = (
        f"Net liq: ${snapshot.net_liquidating_value:,.2f}\n"
        f"Day P&L: ${snapshot.day_pnl:+,.2f}\n"
        f"Review open positions and consider defensive adjustments."
    )

    if notifier.send(title, body, priority=notifier.PRIORITY_HIGH, sound=notifier.SOUND_ALERT):
        state.mark_fired(key)


def send_daily_summary(snapshot: AccountSnapshot, state: State) -> None:
    """End-of-day summary — total P&L, open positions, key facts. Always fires once per day."""
    key = "daily_summary"
    if not state.cooldown_ok(key, config.COOLDOWN_MINUTES["daily_summary"]):
        return

    net_pnl = snapshot.net_liquidating_value - config.STARTING_CAPITAL
    pnl_pct = (net_pnl / config.STARTING_CAPITAL) * 100 if config.STARTING_CAPITAL > 0 else 0

    title = f"Daily summary: ${snapshot.day_pnl:+,.2f} today"
    lines = [
        f"Net liq: ${snapshot.net_liquidating_value:,.2f}",
        f"Experiment P&L: ${net_pnl:+,.2f} ({pnl_pct:+.2f}%)",
        f"Open positions: {len(snapshot.positions)}",
    ]
    for p in snapshot.positions[:5]:
        dte_str = f"{p.dte}d" if p.dte is not None else ""
        lines.append(f"  · {p.symbol[:20]} {dte_str} ${p.day_pnl:+.2f}")

    body = "\n".join(lines)
    if notifier.send(title, body, priority=notifier.PRIORITY_LOW, sound=notifier.SOUND_REMINDER):
        state.mark_fired(key)


# ───────────────────────── Orchestration ─────────────────────────


def run_all_rules(snapshot: AccountSnapshot, state: State) -> None:
    """Evaluate every rule against the current snapshot. Catches per-rule errors so
    one failing rule doesn't kill the others."""
    rules = [
        ("short_strike_touched", rule_short_strike_touched),
        ("profit_target_hit", rule_profit_target_hit),
        ("max_loss_warning", rule_max_loss_warning),
        ("twenty_one_dte", rule_twenty_one_dte),
        ("vix_spike", rule_vix_spike),
        ("daily_account_loss", rule_daily_account_loss),
    ]
    for name, fn in rules:
        try:
            fn(snapshot, state)
        except Exception as e:
            log.exception("Rule %s raised: %s", name, e)
