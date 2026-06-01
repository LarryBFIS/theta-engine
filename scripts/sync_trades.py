"""Auto-sync the hand-maintained trades.json from the broker-truth ledger.

Runs every tick (after build_ledger). The ledger (ledger/trades.json) is derived
from every broker transaction, so it always reflects reality. This script:
  - APPENDS any broker trade not yet in trades.json (matched by open_order_id),
    with strikes/credit/BPR derived by build_ledger's enrichment;
  - marks a tracked trade CLOSED when the ledger shows it closed;
  - PRESERVES existing trades' hand-entered metadata (POP, manage rules, notes).

This removes the last manual step: you no longer hand-edit trades.json when you
open or close a position — the bot reconciles it from the broker each tick.

Pure stdlib (no network/config); the merge logic is unit-tested in
scripts/test_sync_trades.py.
"""
import json
import logging
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TRADES_FILE = REPO_ROOT / "trades.json"
LEDGER_TRADES = REPO_ROOT / "ledger" / "trades.json"

log = logging.getLogger("sync_trades")


def _num(x):
    """Int if whole (390.0 -> 390), else float; pass through None."""
    if x is None:
        return None
    f = float(x)
    return int(f) if f == int(f) else f


def _next_id(trades: list, underlying: str, short, long_) -> str:
    nums = []
    for t in trades:
        m = re.match(r"trade_(\d+)_", t.get("id", "") or "")
        if m:
            nums.append(int(m.group(1)))
    n = (max(nums) if nums else 0) + 1
    s = int(short) if short is not None else 0
    l = int(long_) if long_ is not None else 0
    return "trade_{:03d}_{}_{}_{}".format(n, (underlying or "unk").lower(), s, l)


def _apply_close(ht: dict, lt: dict) -> None:
    ht["status"] = "closed"
    ht["closed_at"] = lt.get("closed_at")
    ht["realized_pnl"] = lt.get("realized_pnl")
    if lt.get("close_debit_per_contract") is not None:
        ht["close_debit_per_contract"] = lt.get("close_debit_per_contract")
    close_orders = lt.get("close_orders") or []
    if close_orders:
        ht["close_order_id"] = str(close_orders[0])


def _hand_from_ledger(lt: dict, trades: list) -> dict:
    short, long_ = lt.get("short_strike"), lt.get("long_strike")
    ht = {
        "id": _next_id(trades, lt.get("underlying", "UNK"), short, long_),
        "underlying": lt.get("underlying"),
        "structure": lt.get("structure", "short_put_vertical"),
        "short_strike": _num(short),
        "long_strike": _num(long_),
        "expiry": lt.get("expiry"),
        "contracts": lt.get("contracts", 1),
        "opened_at": lt.get("opened_at"),
        "open_order_id": str(lt.get("open_order_id")) if lt.get("open_order_id") else None,
        "credit_per_contract": lt.get("credit_per_contract"),
        "max_profit_total": lt.get("max_profit_total"),
        "max_loss_total": lt.get("max_loss_total"),
        "bpr_total": lt.get("bpr_total"),
        "status": lt.get("status", "open"),
        "notes": "auto-synced from ledger",
    }
    if lt.get("status") == "closed":
        _apply_close(ht, lt)
    return ht


def merge_ledger_into_trades(hand: dict, ledger_trades: list):
    """Reconcile hand trades with the ledger. Returns (hand, changes[]).

    Only enriched ledger trades (those with a parsed short_strike) are synced —
    unmatched/pre-window close-only entries are skipped. Idempotent: matching an
    already-tracked, already-closed trade does nothing.
    """
    trades = hand.setdefault("trades", [])
    by_order = {str(t.get("open_order_id")): t for t in trades if t.get("open_order_id")}
    changes = []
    for lt in ledger_trades:
        oid = str(lt.get("open_order_id") or "")
        if not oid or lt.get("short_strike") is None:
            continue  # skip un-enriched / pre-window close-only entries
        ht = by_order.get(oid)
        if ht is None:
            new = _hand_from_ledger(lt, trades)
            trades.append(new)
            by_order[oid] = new
            changes.append("added " + new["id"])
        elif lt.get("status") == "closed" and ht.get("status") != "closed":
            _apply_close(ht, lt)
            changes.append("closed " + (ht.get("id") or oid))
    return hand, changes


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
        stream=sys.stdout,
    )
    if not LEDGER_TRADES.exists():
        log.info("no ledger/trades.json yet; skipping sync")
        return 0
    ledger_trades = json.loads(LEDGER_TRADES.read_text()).get("trades", [])
    hand = (
        json.loads(TRADES_FILE.read_text())
        if TRADES_FILE.exists()
        else {"schema_version": 2, "trades": []}
    )
    hand, changes = merge_ledger_into_trades(hand, ledger_trades)
    if changes:
        TRADES_FILE.write_text(json.dumps(hand, indent=2) + "\n")
        log.info("trades.json synced: %s", "; ".join(changes))
    else:
        log.info("trades.json already in sync with the ledger")
    return 0


if __name__ == "__main__":
    sys.exit(main())
