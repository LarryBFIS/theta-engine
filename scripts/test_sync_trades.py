"""Tests for sync_trades.merge_ledger_into_trades and build_ledger enrichment.

Run without pytest:  python -m scripts.test_sync_trades

Verifies the auto-discovery loop: a brand-new broker trade gets appended, a
tracked trade the ledger shows closed gets marked closed (with hand metadata
preserved), and re-running changes nothing (idempotent).
"""
import sys

from scripts.build_ledger import parse_occ, build_trades
from scripts.sync_trades import merge_ledger_into_trades


def main() -> int:
    failures = []

    # --- OCC parser ---
    p = parse_occ("GLD   260717P00390000")
    if not p or p["strike"] != 390.0 or p["type"] != "P" or p["expiry"] != "2026-07-17" or p["underlying"] != "GLD":
        failures.append("parse_occ GLD wrong: {}".format(p))
    if parse_occ("SPY 260618 P721") is not None:
        failures.append("parse_occ should reject non-OCC strings")

    # --- enrichment via build_trades on realistic OCC symbols ---
    def leg(sym, action, price, net, eff):
        return {"transaction-type": "Trade", "transaction-sub-type": action,
                "order-id": "OPEN1", "symbol": sym, "underlying-symbol": "GLD",
                "quantity": 1, "price": price, "net-value": net, "net-value-effect": eff,
                "executed-at": "2026-06-01T18:00:00Z"}
    txns = [
        leg("GLD   260717P00390000", "Sell to Open", 4.76, 474.87, "Credit"),
        leg("GLD   260717P00385000", "Buy to Open", 3.83, 384.12, "Debit"),
    ]
    pos = [
        {"symbol": "GLD   260717P00390000", "quantity": -1, "mark": 4.80, "multiplier": 100},
        {"symbol": "GLD   260717P00385000", "quantity": 1, "mark": 3.85, "multiplier": 100},
    ]
    lt = build_trades(txns, pos)[0]
    if lt.get("short_strike") != 390.0 or lt.get("long_strike") != 385.0:
        failures.append("enrich strikes wrong: {}/{}".format(lt.get("short_strike"), lt.get("long_strike")))
    if lt.get("credit_per_contract") != 0.93:
        failures.append("enrich credit wrong: {}".format(lt.get("credit_per_contract")))
    if lt.get("max_profit_total") != 93.0 or lt.get("bpr_total") != 407.0:
        failures.append("enrich max_profit/bpr wrong: {}/{}".format(lt.get("max_profit_total"), lt.get("bpr_total")))
    lt["open_order_id"] = "472016142"  # build_trades uses order-id 'OPEN1'; set realistic for sync test

    # --- merge: new trade appended ---
    hand = {"schema_version": 2, "trades": [
        {"id": "trade_005_jpm_280_270", "underlying": "JPM", "status": "open",
         "open_order_id": "471570454", "short_strike": 280, "long_strike": 270,
         "pop_at_open": 0.74, "notes": "hand metadata"},
    ]}
    ledger = [
        {"open_order_id": "471570454", "status": "open", "short_strike": 280, "long_strike": 270,
         "underlying": "JPM"},  # already tracked, still open -> no change
        dict(lt),  # the new GLD -> should be appended
    ]
    hand, changes = merge_ledger_into_trades(hand, ledger)
    ids = [t["id"] for t in hand["trades"]]
    new = next((t for t in hand["trades"] if t["underlying"] == "GLD" and t["status"] == "open"), None)
    if new is None:
        failures.append("new GLD trade not appended")
    elif new["id"] != "trade_006_gld_390_385":
        failures.append("new id wrong: {}".format(new["id"]))
    elif new.get("credit_per_contract") != 0.93 or new.get("bpr_total") != 407.0:
        failures.append("new trade fields not carried: {}".format(new))
    if any("added" in c for c in changes) is False:
        failures.append("expected an 'added' change, got {}".format(changes))

    # hand metadata preserved on the existing JPM trade
    jpm = next(t for t in hand["trades"] if t["id"] == "trade_005_jpm_280_270")
    if jpm.get("pop_at_open") != 0.74 or jpm.get("notes") != "hand metadata":
        failures.append("existing hand metadata not preserved")

    # --- merge: a tracked trade now closed in the ledger ---
    ledger2 = [
        {"open_order_id": "471570454", "status": "closed", "short_strike": 280, "long_strike": 270,
         "underlying": "JPM", "closed_at": "2026-06-05", "realized_pnl": 88.0,
         "close_debit_per_contract": 1.18, "close_orders": ["999"]},
    ]
    hand, changes2 = merge_ledger_into_trades(hand, ledger2)
    jpm = next(t for t in hand["trades"] if t["id"] == "trade_005_jpm_280_270")
    if jpm.get("status") != "closed" or jpm.get("realized_pnl") != 88.0:
        failures.append("JPM not marked closed correctly: {}".format(jpm))
    if jpm.get("pop_at_open") != 0.74:
        failures.append("closing wiped hand metadata")

    # --- idempotent: running again changes nothing ---
    _, changes3 = merge_ledger_into_trades(hand, ledger2)
    if changes3:
        failures.append("expected no changes on re-run, got {}".format(changes3))

    # --- self-heal a FALSE close: ledger shows open, trades.json wrongly closed ---
    healh = {"schema_version": 2, "trades": [
        {"id": "trade_011_spy_712_703", "underlying": "SPY", "status": "closed",
         "open_order_id": "477674903", "short_strike": 712, "long_strike": 703,
         "closed_at": "2026-06-22", "realized_pnl": 0.0, "pop_at_open": 0.8},
    ]}
    healledger = [
        {"open_order_id": "477674903", "status": "open", "short_strike": 712,
         "long_strike": 703, "underlying": "SPY"},
    ]
    healh, healchg = merge_ledger_into_trades(healh, healledger)
    spy = healh["trades"][0]
    if spy.get("status") != "open" or spy.get("closed_at") is not None or spy.get("realized_pnl") is not None:
        failures.append("false-close not healed: {}".format(spy))
    if spy.get("pop_at_open") != 0.8:
        failures.append("re-open wiped hand metadata")
    if not any("re-opened" in c for c in healchg):
        failures.append("expected a 're-opened' change, got {}".format(healchg))

    if failures:
        print("FAILED:")
        for f in failures:
            print("  - " + f)
        return 1
    print("Discovered + appended:", [c for c in changes if "added" in c])
    print("Closed on later sync:", changes2)
    print("Idempotent re-run:", changes3 or "no changes ✓")
    print("All sync_trades tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
