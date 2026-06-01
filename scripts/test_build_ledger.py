"""Self-contained tests for the pure ledger math in build_ledger.

Runs without API credentials or pytest:  python -m scripts.test_build_ledger

The synthetic transaction set mirrors the four tracked trades (SPY, GLD, AMZN,
JPM) plus a deliberately *untracked* closed trade (GOOGL, the "missing
trade_004" scenario) and a weekend interest credit — exactly the kinds of
things that produce the ~$140 reconciliation gap. We assert the ledger finds
the hidden trade and reconciles to zero.
"""
import sys

from scripts.build_ledger import (
    build_reconciliation,
    build_trades,
    net_cash,
)


def opt_symbol(underlying, expiry, cp, strike):
    # OCC-ish symbol, just needs to be unique per leg.
    return "{} {} {}{}".format(underlying, expiry, cp, strike)


def leg(symbol, underlying, subtype, qty, price, net_value, effect, executed_at,
        order_id, commission=1.0, reg=0.04):
    return {
        "transaction-type": "Trade",
        "transaction-sub-type": subtype,
        "order-id": order_id,
        "symbol": symbol,
        "underlying-symbol": underlying,
        "instrument-type": "Equity Option",
        "quantity": qty,
        "price": price,
        "net-value": net_value,
        "net-value-effect": effect,
        "commission": commission,
        "regulatory-fees": reg,
        "clearing-fees": 0.0,
        "executed-at": executed_at,
    }


def vertical_open(underlying, expiry, short_k, long_k, short_net, long_net,
                  date_str, order_id):
    """Sell-to-open short put + buy-to-open long put (a credit spread)."""
    return [
        leg(opt_symbol(underlying, expiry, "P", short_k), underlying,
            "Sell to Open", 1, short_net / 100, short_net, "Credit",
            date_str + "T14:30:00Z", order_id),
        leg(opt_symbol(underlying, expiry, "P", long_k), underlying,
            "Buy to Open", 1, long_net / 100, long_net, "Debit",
            date_str + "T14:30:00Z", order_id),
    ]


def vertical_close(underlying, expiry, short_k, long_k, short_net, long_net,
                   date_str, order_id):
    return [
        leg(opt_symbol(underlying, expiry, "P", short_k), underlying,
            "Buy to Close", 1, short_net / 100, short_net, "Debit",
            date_str + "T15:00:00Z", order_id),
        leg(opt_symbol(underlying, expiry, "P", long_k), underlying,
            "Sell to Close", 1, long_net / 100, long_net, "Credit",
            date_str + "T15:00:00Z", order_id),
    ]


def build_fixture():
    txns = []
    # SPY 721/716p — opened 5/13 credit ~1.00, closed 5/26 debit ~0.58
    txns += vertical_open("SPY", "260618", 721, 716, 763.0, 663.0, "2026-05-13", "466603976")
    txns += vertical_close("SPY", "260618", 721, 716, 342.0, 284.0, "2026-05-26", "470430708")
    # GLD 395/390p — opened 5/18 credit ~0.73, closed 5/29 debit ~0.49
    txns += vertical_open("GLD", "260618", 395, 390, 334.0, 261.0, "2026-05-18", "468508848")
    txns += vertical_close("GLD", "260618", 395, 390, 175.0, 126.0, "2026-05-29", "471594051")
    # GOOGL 180/175p — the UNTRACKED trade_004: opened 5/22, closed 5/27
    txns += vertical_open("GOOGL", "260717", 180, 175, 210.0, 130.0, "2026-05-22", "469000001")
    txns += vertical_close("GOOGL", "260717", 180, 175, 90.0, 45.0, "2026-05-27", "470000002")
    # AMZN 250/245p — opened 5/26 credit ~1.29, still OPEN
    txns += vertical_open("AMZN", "260717", 250, 245, 574.0, 445.0, "2026-05-26", "470366596")
    # JPM 280/270p — opened 5/29 credit ~2.06, still OPEN
    txns += vertical_open("JPM", "260717", 280, 270, 498.0, 292.0, "2026-05-29", "471570454")
    # Weekend interest credit (money movement)
    txns.append({
        "transaction-type": "Money Movement",
        "transaction-sub-type": "Interest",
        "order-id": None,
        "symbol": None,
        "underlying-symbol": None,
        "net-value": 3.40,
        "net-value-effect": "Credit",
        "commission": 0.0,
        "regulatory-fees": 0.0,
        "clearing-fees": 0.0,
        "executed-at": "2026-05-31T00:00:00Z",
    })
    return txns


def open_positions():
    # Live marks for the two open trades. Short put marked higher than long.
    return [
        {"symbol": opt_symbol("AMZN", "260717", "P", 250), "quantity": -1, "mark": 5.10, "multiplier": 100},
        {"symbol": opt_symbol("AMZN", "260717", "P", 245), "quantity": 1, "mark": 4.17, "multiplier": 100},
        {"symbol": opt_symbol("JPM", "260717", "P", 280), "quantity": -1, "mark": 4.50, "multiplier": 100},
        {"symbol": opt_symbol("JPM", "260717", "P", 270), "quantity": 1, "mark": 2.58, "multiplier": 100},
    ]


def approx(a, b, tol=0.01):
    return abs(a - b) <= tol


def main() -> int:
    txns = build_fixture()
    positions = open_positions()
    trades = build_trades(txns, positions)

    failures = []

    # Expect 5 trades total.
    if len(trades) != 5:
        failures.append("expected 5 trades, got {}".format(len(trades)))

    by_underlying = {t["underlying"]: t for t in trades}

    # SPY: closed. realized = (763-663) open + (-342+284) close, net of fees in net_value.
    spy = by_underlying.get("SPY")
    if not spy or spy["status"] != "closed":
        failures.append("SPY should be closed")
    else:
        expected = (763.0 - 663.0) + (-342.0 + 284.0)
        if not approx(spy["realized_pnl"], expected):
            failures.append("SPY realized {} != {}".format(spy["realized_pnl"], expected))

    # GOOGL: the untracked closed trade must be discovered.
    googl = by_underlying.get("GOOGL")
    if not googl or googl["status"] != "closed":
        failures.append("GOOGL (untracked trade_004) should be discovered and closed")

    # AMZN + JPM open with unrealized P&L = open credit - cost to close at mark.
    amzn = by_underlying.get("AMZN")
    if not amzn or amzn["status"] != "open":
        failures.append("AMZN should be open")
    else:
        # open net 574-445=129; close at mark: short -5.10*100, long +4.17*100
        expected_unreal = 129.0 + ((-1 * 5.10 * 100) + (1 * 4.17 * 100))
        if not approx(amzn["unrealized_pnl"], expected_unreal):
            failures.append("AMZN unrealized {} != {}".format(amzn["unrealized_pnl"], expected_unreal))

    jpm = by_underlying.get("JPM")
    if not jpm or jpm["status"] != "open":
        failures.append("JPM should be open")

    # Reconciliation: set net_liq so the ledger SHOULD reconcile to zero.
    starting = 3389.91
    realized = sum(t["realized_pnl"] or 0.0 for t in trades if t["status"] == "closed")
    unrealized = sum(t["unrealized_pnl"] or 0.0 for t in trades if t["status"] == "open")
    money = sum(net_cash(t) for t in txns if t.get("transaction-type") != "Trade")
    net_liq = starting + realized + unrealized + money

    recon = build_reconciliation(txns, trades, net_liq, starting)
    # No pre-ledger positions in the fixture, so non-strategy activity must be ~0.
    if not approx(recon["components"]["non_strategy_activity"], 0.0):
        failures.append("non_strategy_activity {} should be ~0".format(recon["components"]["non_strategy_activity"]))
    if not approx(recon["strategy_pnl"], realized + unrealized):
        failures.append("strategy_pnl {} != {}".format(recon["strategy_pnl"], realized + unrealized))
    if not approx(recon["components"]["money_movement_net"], 3.40):
        failures.append("money movement {} != 3.40".format(recon["components"]["money_movement_net"]))

    print("Trades discovered:")
    for t in trades:
        print("  {:>16}  {:>6}  {:<7} realized={} unrealized={}".format(
            t["id"], t["underlying"], t["status"], t["realized_pnl"], t["unrealized_pnl"]))
    print("")
    print("Account P&L     : ${:+.2f}".format(recon["account_pnl"]))
    print("  strategy P&L  : ${:+.2f}".format(recon["strategy_pnl"]))
    print("    realized    : ${:+.2f}".format(recon["components"]["realized_pnl_closed"]))
    print("    unrealized  : ${:+.2f}".format(recon["components"]["unrealized_pnl_open"]))
    print("  money mvmt    : ${:+.2f}".format(recon["components"]["money_movement_net"]))
    print("  non-strategy  : ${:+.2f}".format(recon["components"]["non_strategy_activity"]))
    print("")

    if failures:
        print("FAILED:")
        for f in failures:
            print("  - " + f)
        return 1
    print("All ledger math tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
