"""Build an authoritative ledger from tastytrade transaction history.

This replaces the hand-maintained trades.json with a *derived* view computed
from every fill, fee, dividend, and interest payment the broker reports. It is
the source of truth for reconciling account P&L.

Outputs (written to ledger/):
  transactions.json    raw transactions since the experiment start date
  trades.json          orders grouped into trades with realized/unrealized P&L
  reconciliation.json  net-liq P&L broken into explained components + any gap
  summary.md           human-readable summary

Design notes
------------
The functions that do the actual ledger math (group_orders, build_trades,
build_reconciliation) are pure: they take plain dicts/lists and return plain
dicts. Only main() touches the network. That makes the math unit-testable
without API credentials (see scripts/test_build_ledger.py).

A tastytrade transaction's ``net-value`` already incorporates commission and
regulatory/clearing fees, so signed net-value is the authoritative cash impact
of each transaction. We sum signed net-values to get realized P&L per closed
trade and to reconcile the account.
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER_DIR = REPO_ROOT / "ledger"
START_DATE = "2026-05-13"
OPTION_MULTIPLIER_DEFAULT = 100

log = logging.getLogger("build_ledger")


# ────────────────────────────────────────────────────────────────────
# Small helpers
# ────────────────────────────────────────────────────────────────────
def _to_float(value) -> float:
    if value is None or value == "":
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def signed(value, effect) -> float:
    """Return a signed amount: positive for Credit, negative for Debit.

    tastytrade uses ``...-effect`` fields of "Credit" / "Debit" (and "None"
    for zero amounts). We treat Credit as cash in (+) and Debit as cash out (-).
    """
    amount = _to_float(value)
    if amount == 0.0:
        return 0.0
    eff = (effect or "").strip().lower()
    if eff == "debit":
        return -amount
    if eff == "credit":
        return amount
    # No explicit effect — assume the sign is already baked into the value.
    return amount


def net_cash(txn: dict) -> float:
    """Authoritative signed cash impact of a transaction (net of all fees)."""
    return signed(txn.get("net-value"), txn.get("net-value-effect"))


def total_fees(txn: dict) -> float:
    """Sum the fee components of a transaction (always reported as positive)."""
    return (
        _to_float(txn.get("commission"))
        + _to_float(txn.get("regulatory-fees"))
        + _to_float(txn.get("clearing-fees"))
        + _to_float(txn.get("proprietary-index-option-fees"))
    )


def is_trade(txn: dict) -> bool:
    return (txn.get("transaction-type") or "") == "Trade"


def is_opening(txn: dict) -> bool:
    return "open" in (txn.get("transaction-sub-type") or "").lower()


def is_closing(txn: dict) -> bool:
    sub = (txn.get("transaction-sub-type") or "").lower()
    return "close" in sub


# ────────────────────────────────────────────────────────────────────
# Pure ledger math
# ────────────────────────────────────────────────────────────────────
def group_orders(transactions: list[dict]) -> dict:
    """Group trade transactions by order-id.

    Returns: {order_id: {"order_id", "legs": [txn,...], "opening": bool,
                          "underlying", "executed_at", "net_cash"}}
    """
    orders: dict = {}
    for txn in transactions:
        if not is_trade(txn):
            continue
        order_id = str(txn.get("order-id") or txn.get("id"))
        order = orders.setdefault(
            order_id,
            {
                "order_id": order_id,
                "legs": [],
                "opening": is_opening(txn),
                "underlying": txn.get("underlying-symbol") or txn.get("symbol"),
                "executed_at": txn.get("executed-at"),
                "net_cash": 0.0,
            },
        )
        order["legs"].append(txn)
        order["net_cash"] += net_cash(txn)
        # An order is "opening" if any leg opens; mixed orders are rare.
        order["opening"] = order["opening"] or is_opening(txn)
        if (txn.get("executed-at") or "") < (order["executed_at"] or "~"):
            order["executed_at"] = txn.get("executed-at")
    return orders


def build_trades(transactions: list[dict], positions: list[dict]) -> list[dict]:
    """Group orders into trades and compute realized/unrealized P&L.

    A trade = one opening order plus the closing order(s) that buy/sell back
    the same option symbols. Closing transactions are matched to the opening
    trade that holds the matching symbol.

    ``positions`` is the live open-position list used to mark open trades:
    [{"symbol", "quantity" (signed), "mark", "multiplier"}].
    """
    orders = group_orders(transactions)
    opening = [o for o in orders.values() if o["opening"]]
    closing = [o for o in orders.values() if not o["opening"]]
    opening.sort(key=lambda o: o["executed_at"] or "")

    # Index open positions by symbol for marking.
    pos_by_symbol = {p["symbol"]: p for p in positions if p.get("symbol")}

    trades: list[dict] = []
    # Map each opening trade to the set of symbols it still has unmatched.
    for idx, order in enumerate(opening, start=1):
        symbols = {leg.get("symbol") for leg in order["legs"] if leg.get("symbol")}
        trades.append(
            {
                "_symbols": symbols,
                "id": _trade_id(idx, order),
                "underlying": order["underlying"],
                "opened_at": (order["executed_at"] or "")[:10],
                "open_order_id": order["order_id"],
                "open_net_cash": round(order["net_cash"], 2),
                "open_legs": [_leg_view(leg) for leg in order["legs"]],
                "close_orders": [],
                "close_net_cash": 0.0,
                "close_legs": [],
                "closed_at": None,
            }
        )

    # Attribute each closing order to the opening trade holding its symbols.
    for order in closing:
        for leg in order["legs"]:
            sym = leg.get("symbol")
            trade = _find_open_trade_for_symbol(trades, sym)
            if trade is None:
                log.warning("Close leg for %s has no matching open trade", sym)
                continue
            trade["close_legs"].append(_leg_view(leg))
            trade["close_net_cash"] = round(trade["close_net_cash"] + net_cash(leg), 2)
            if order["order_id"] not in trade["close_orders"]:
                trade["close_orders"].append(order["order_id"])
            closed_at = (leg.get("executed-at") or "")[:10]
            if closed_at:
                trade["closed_at"] = closed_at

    # Determine status + P&L for each trade.
    for trade in trades:
        symbols = trade.pop("_symbols")
        open_qty_remaining = any(symbols & set(pos_by_symbol.keys()))
        if open_qty_remaining:
            trade["status"] = "open"
            trade["realized_pnl"] = None
            trade["unrealized_pnl"] = round(
                trade["open_net_cash"] + _mark_to_close_cash(symbols, pos_by_symbol), 2
            )
            trade["cost_to_close_mid"] = round(
                -_mark_to_close_cash(symbols, pos_by_symbol), 2
            )
        else:
            trade["status"] = "closed"
            trade["unrealized_pnl"] = None
            trade["realized_pnl"] = round(
                trade["open_net_cash"] + trade["close_net_cash"], 2
            )
        _enrich_trade(trade)
    return trades


def _find_open_trade_for_symbol(trades: list[dict], symbol: str):
    for trade in trades:
        if symbol in trade["_symbols"]:
            return trade
    return None


def _mark_to_close_cash(symbols: set, pos_by_symbol: dict) -> float:
    """Cash flow from liquidating the open legs at current marks.

    For a signed position q at mark m with multiplier mult, the cash realized
    by closing is q * m * mult (negative for shorts you must buy back).
    """
    cash = 0.0
    for sym in symbols:
        pos = pos_by_symbol.get(sym)
        if not pos or pos.get("mark") is None:
            continue
        q = _to_float(pos.get("quantity"))
        mark = _to_float(pos.get("mark"))
        mult = _to_float(pos.get("multiplier")) or OPTION_MULTIPLIER_DEFAULT
        cash += q * mark * mult
    return cash


def _leg_view(leg: dict) -> dict:
    return {
        "symbol": leg.get("symbol"),
        "action": leg.get("transaction-sub-type") or leg.get("action"),
        "quantity": _to_float(leg.get("quantity")),
        "price": _to_float(leg.get("price")),
        "net_cash": round(net_cash(leg), 2),
        "fees": round(total_fees(leg), 2),
        "executed_at": leg.get("executed-at"),
    }


def _trade_id(idx: int, order: dict) -> str:
    underlying = (order["underlying"] or "UNK").lower()
    return "ledger_{:03d}_{}".format(idx, underlying)


def parse_occ(symbol: str):
    """Parse a fixed-width OCC option symbol, e.g. 'GLD   260618P00395000'.

    Layout: 6-char root (space-padded) + YYMMDD + C/P + strike×1000 (8 digits).
    Returns {underlying, expiry 'YYYY-MM-DD', type 'C'/'P', strike} or None.
    """
    if not symbol or len(symbol) < 21:
        return None
    root = symbol[0:6].strip()
    date = symbol[6:12]
    cp = symbol[12]
    strike_s = symbol[13:21]
    if not (date.isdigit() and strike_s.isdigit() and cp in ("C", "P") and root):
        return None
    return {
        "underlying": root,
        "expiry": "20{}-{}-{}".format(date[0:2], date[2:4], date[4:6]),
        "type": cp,
        "strike": int(strike_s) / 1000.0,
    }


def _enrich_trade(trade: dict) -> None:
    """Add human display fields (strikes, expiry, credit, BPR, close debit) derived
    from the option symbols/prices, so downstream views and the hand-maintained
    trades.json can be auto-synced without parsing OCC symbols themselves."""
    legs = trade.get("open_legs") or []
    short_leg = next((l for l in legs if "sell" in (l.get("action") or "").lower()), None)
    long_leg = next((l for l in legs if "buy" in (l.get("action") or "").lower()), None)
    if not short_leg or not long_leg:
        return
    ps, pl = parse_occ(short_leg.get("symbol")), parse_occ(long_leg.get("symbol"))
    if not ps or not pl:
        return
    contracts = int(abs(_to_float(short_leg.get("quantity"))) or 1)
    credit = round(_to_float(short_leg.get("price")) - _to_float(long_leg.get("price")), 2)
    width = round(abs(ps["strike"] - pl["strike"]), 2)
    trade["underlying"] = trade.get("underlying") or ps["underlying"]
    trade["structure"] = "short_{}_vertical".format("put" if ps["type"] == "P" else "call")
    trade["short_strike"] = ps["strike"]
    trade["long_strike"] = pl["strike"]
    trade["expiry"] = ps["expiry"]
    trade["contracts"] = contracts
    trade["credit_per_contract"] = credit
    trade["width"] = width
    trade["max_profit_total"] = round(credit * 100 * contracts, 2)
    trade["max_loss_total"] = round((width - credit) * 100 * contracts, 2)
    trade["bpr_total"] = trade["max_loss_total"]
    if trade.get("status") == "closed":
        clegs = trade.get("close_legs") or []
        cbuy = next((l for l in clegs if "buy" in (l.get("action") or "").lower()), None)
        csell = next((l for l in clegs if "sell" in (l.get("action") or "").lower()), None)
        if cbuy and csell:
            trade["close_debit_per_contract"] = round(
                _to_float(cbuy.get("price")) - _to_float(csell.get("price")), 2
            )


def build_reconciliation(
    transactions: list[dict],
    trades: list[dict],
    net_liq: float,
    starting_capital: float,
) -> dict:
    """Reconcile account P&L into explained components and surface any gap."""
    realized = sum(t["realized_pnl"] or 0.0 for t in trades if t["status"] == "closed")
    unrealized = sum(t["unrealized_pnl"] or 0.0 for t in trades if t["status"] == "open")

    # Non-trade cash movements: interest, dividends, balance adjustments, etc.
    money_movement = 0.0
    movement_detail: dict = {}
    for txn in transactions:
        if is_trade(txn):
            continue
        ttype = txn.get("transaction-type") or "Other"
        subtype = txn.get("transaction-sub-type") or ""
        key = "{} / {}".format(ttype, subtype).strip(" /")
        cash = net_cash(txn)
        money_movement += cash
        movement_detail[key] = round(movement_detail.get(key, 0.0) + cash, 2)

    fees = round(sum(total_fees(t) for t in transactions), 2)

    strategy_pnl = round(realized + unrealized, 2)
    account_pnl = round(net_liq - starting_capital, 2)
    # Whatever account P&L isn't explained by the tracked experiment strategy or
    # by cash movements. This is NOT an error: it's mostly positions opened
    # BEFORE the ledger start date that were closed within the window (their cost
    # basis lives outside the window, so their P&L can't be attributed to a
    # tracked trade). We surface it as a labeled line rather than an alarm.
    non_strategy_activity = round(account_pnl - strategy_pnl - money_movement, 2)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "starting_capital": round(starting_capital, 2),
        "net_liquidating_value": round(net_liq, 2),
        "account_pnl": account_pnl,
        "strategy_pnl": strategy_pnl,
        "components": {
            "realized_pnl_closed": round(realized, 2),
            "unrealized_pnl_open": round(unrealized, 2),
            "money_movement_net": round(money_movement, 2),
            "non_strategy_activity": non_strategy_activity,
        },
        "money_movement_detail": movement_detail,
        "total_fees_paid": fees,
        "counts": {
            "transactions": len(transactions),
            "trades": len(trades),
            "open_trades": sum(1 for t in trades if t["status"] == "open"),
            "closed_trades": sum(1 for t in trades if t["status"] == "closed"),
        },
    }


def build_summary_md(trades: list[dict], recon: dict) -> str:
    lines = []
    lines.append("# Ledger Summary")
    lines.append("")
    lines.append("_Generated {} from tastytrade transaction history._".format(recon["generated_at"]))
    lines.append("")
    lines.append("## Reconciliation")
    lines.append("")
    lines.append("| Item | Amount |")
    lines.append("|---|---:|")
    lines.append("| Starting capital | ${:,.2f} |".format(recon["starting_capital"]))
    lines.append("| Net liq (now) | ${:,.2f} |".format(recon["net_liquidating_value"]))
    lines.append("| Strategy realized (closed) | ${:+,.2f} |".format(recon["components"]["realized_pnl_closed"]))
    lines.append("| Strategy unrealized (open) | ${:+,.2f} |".format(recon["components"]["unrealized_pnl_open"]))
    lines.append("| **Strategy P&L** | **${:+,.2f}** |".format(recon["strategy_pnl"]))
    lines.append("| Money movement | ${:+,.2f} |".format(recon["components"]["money_movement_net"]))
    lines.append("| Non-strategy activity | ${:+,.2f} |".format(recon["components"]["non_strategy_activity"]))
    lines.append("| **Account P&L** | **${:+,.2f}** |".format(recon["account_pnl"]))
    lines.append("")
    lines.append(
        "_Account P&L = strategy P&L + money movement + non-strategy activity "
        "(pre-ledger positions closed in-window). Total fees paid: ${:,.2f}._".format(recon["total_fees_paid"])
    )
    if recon["money_movement_detail"]:
        lines.append("")
        lines.append("### Money movement detail")
        lines.append("")
        for key, amt in sorted(recon["money_movement_detail"].items()):
            lines.append("- {}: ${:+,.2f}".format(key, amt))
    lines.append("")
    lines.append("## Trades")
    lines.append("")
    lines.append("| ID | Underlying | Opened | Closed | Status | Realized | Unrealized |")
    lines.append("|---|---|---|---|---|---:|---:|")
    for t in trades:
        realized = "${:+,.2f}".format(t["realized_pnl"]) if t["realized_pnl"] is not None else "—"
        unreal = "${:+,.2f}".format(t["unrealized_pnl"]) if t["unrealized_pnl"] is not None else "—"
        lines.append(
            "| {} | {} | {} | {} | {} | {} | {} |".format(
                t["id"], t["underlying"], t["opened_at"] or "—",
                t["closed_at"] or "—", t["status"], realized, unreal,
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_ledger(transactions, trades, recon, summary_md) -> None:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    (LEDGER_DIR / "transactions.json").write_text(
        json.dumps(
            {"start_date": START_DATE, "count": len(transactions), "transactions": transactions},
            indent=2,
            default=str,
        )
        + "\n"
    )
    (LEDGER_DIR / "trades.json").write_text(
        json.dumps({"schema_version": 1, "trades": trades}, indent=2, default=str) + "\n"
    )
    (LEDGER_DIR / "reconciliation.json").write_text(
        json.dumps(recon, indent=2, default=str) + "\n"
    )
    (LEDGER_DIR / "summary.md").write_text(summary_md)


# ────────────────────────────────────────────────────────────────────
# Live data fetch (uses the existing client's OAuth2 + _get plumbing)
# ────────────────────────────────────────────────────────────────────
def fetch_account_number(client) -> str:
    """First account number on this OAuth grant."""
    items = client._get("/customers/me/accounts").get("data", {}).get("items", [])
    if not items:
        raise RuntimeError("No tastytrade accounts found for this OAuth grant")
    account_number = items[0].get("account", {}).get("account-number")
    if not account_number:
        raise RuntimeError("First account item missing account-number: {}".format(items[0]))
    return account_number


def fetch_transactions(client, account_number: str, start_date: str, per_page: int = 250) -> list[dict]:
    """Page through /accounts/{acct}/transactions since ``start_date``.

    Returns raw transaction dicts oldest-first. tastytrade returns newest-first
    and paginates via ``pagination.total-pages`` / ``page-offset``.
    """
    path = "/accounts/{}/transactions".format(account_number)
    all_items: list[dict] = []
    page_offset = 0
    while True:
        payload = client._get(
            path,
            params={"start-date": start_date, "per-page": per_page, "page-offset": page_offset},
        )
        items = payload.get("data", {}).get("items", [])
        all_items.extend(items)

        pagination = payload.get("pagination", {})
        total_pages = pagination.get("total-pages")
        current_offset = pagination.get("page-offset", page_offset)
        if total_pages is not None:
            if current_offset + 1 >= total_pages:
                break
        elif len(items) < per_page:
            break
        page_offset += 1

    all_items.sort(key=lambda t: t.get("executed-at") or "")
    log.info("Fetched %d transactions since %s", len(all_items), start_date)
    return all_items


# ────────────────────────────────────────────────────────────────────
# Live entry point
# ────────────────────────────────────────────────────────────────────
def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
        stream=sys.stdout,
    )
    # Imported here so the pure functions above stay importable without config
    # (which requires env vars) being loaded.
    import requests

    from monitor import config
    from monitor.tastytrade_client import TastytradeClient

    try:
        client = TastytradeClient()
        account_number = fetch_account_number(client)
        log.info("Building ledger for account %s since %s", account_number, START_DATE)

        transactions = fetch_transactions(client, account_number, START_DATE)
        snapshot = client.fetch_snapshot()
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        # Broker transiently unreachable — don't fail the job or overwrite a good
        # ledger with nothing. Skip; the next run rebuilds.
        log.warning("Broker unreachable — skipping ledger rebuild this run: %s", e)
        return 0
    positions = [
        {
            "symbol": p.symbol,
            "quantity": p.quantity,
            "mark": p.mark_or_mid,
            "multiplier": p.multiplier,
        }
        for p in snapshot.positions
        if p.is_option
    ]

    trades = build_trades(transactions, positions)
    recon = build_reconciliation(
        transactions, trades, snapshot.net_liquidating_value, config.STARTING_CAPITAL
    )
    summary_md = build_summary_md(trades, recon)
    write_ledger(transactions, trades, recon, summary_md)

    log.info(
        "Ledger built: %d txns, %d trades (%d open / %d closed). "
        "Account P&L $%+.2f = strategy $%+.2f + money $%+.2f + non-strategy $%+.2f.",
        len(transactions),
        len(trades),
        recon["counts"]["open_trades"],
        recon["counts"]["closed_trades"],
        recon["account_pnl"],
        recon["strategy_pnl"],
        recon["components"]["money_movement_net"],
        recon["components"]["non_strategy_activity"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
