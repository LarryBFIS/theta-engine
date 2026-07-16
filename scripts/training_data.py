"""Model-ready training data — the first brick toward a model of our own.

Every closed trade in the outcomes ledger becomes ONE clean row (features at entry
-> realized outcome + label) in memory/training_data.jsonl, and a progress rollup
for the dashboard's Model-Build panel goes to memory/training_status.json.

We are not training anything yet; this makes the data clean and model-ready as it
accumulates, so that when there's enough it's zero-cleanup to:
  1. train a gradient-boosted ranker on (features -> won / realized_pnl), then
  2. fine-tune an LLM on the journaled reasoned decisions.

Pure stdlib; safe to run every scan (idempotent — rebuilds from the ledger).
"""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LEDGER = REPO_ROOT / "memory" / "trades_ledger.json"         # paper outcomes (the learner's memory)
LIVE_LEDGER = REPO_ROOT / "ledger" / "trades.json"          # real broker-truth closes
JOURNAL = REPO_ROOT / "memory" / "agent_journal.jsonl"
OUT_DATA = REPO_ROOT / "memory" / "training_data.jsonl"
OUT_STATUS = REPO_ROOT / "memory" / "training_status.json"

log = logging.getLogger("training_data")

FIRST_MODEL_TARGET = 300     # closed trades to train a first gradient-boosted ranker
LLM_TARGET = 2000            # reasoned AI decisions to fine-tune an LLM

# Entry features the model would learn from (the label is realized_pnl / won).
FEATURES = ["underlying", "asset_class", "cluster", "structure", "contracts",
            "credit", "iv_rank", "pop", "tag", "event", "opened_at", "closed_at",
            "close_reason", "fees"]


def _days_held(opened, closed):
    try:
        return (datetime.fromisoformat(closed[:10]) - datetime.fromisoformat(opened[:10])).days
    except Exception:  # noqa: BLE001
        return None


def _live_rows():
    """Real broker-truth CLOSED trades — every position ever actually traded. Fewer
    entry features than the paper ledger (no IV rank/POP recorded at open), but the
    outcome label is real money. Off-strategy ignored orders (e.g. SLV) are excluded."""
    if not LIVE_LEDGER.exists():
        return []
    try:
        from scripts.paper_trades import asset_class, cluster_of
        from scripts.sync_trades import IGNORE_ORDER_IDS
        trades = json.loads(LIVE_LEDGER.read_text()).get("trades", [])
    except Exception:  # noqa: BLE001
        return []
    rows = []
    for t in trades:
        if t.get("status") != "closed":
            continue
        if str(t.get("open_order_id")) in IGNORE_ORDER_IDS:
            continue  # off-strategy — excluded everywhere, training included
        u = (t.get("underlying") or "").upper()
        rows.append({
            "source": "live",
            "underlying": u, "asset_class": asset_class(u), "cluster": cluster_of(u),
            "structure": t.get("structure"), "contracts": t.get("contracts"),
            "credit": t.get("credit_per_contract"), "iv_rank": t.get("iv_rank"),
            "pop": t.get("pop_at_open"), "tag": "live", "event": None,
            "opened_at": t.get("opened_at"), "closed_at": t.get("closed_at"),
            "close_reason": t.get("close_reason"), "fees": None,
            "days_held": _days_held(t.get("opened_at") or "", t.get("closed_at") or ""),
            "realized_pnl": t.get("realized_pnl"),
            "won": (t.get("realized_pnl") or 0) > 0,
        })
    return rows


def build():
    ledger = []
    if LEDGER.exists():
        try:
            ledger = json.loads(LEDGER.read_text()).get("trades", [])
        except Exception:  # noqa: BLE001
            ledger = []

    rows = []
    for t in ledger:
        row = {k: t.get(k) for k in FEATURES}
        row["source"] = "paper"
        row["days_held"] = _days_held(t.get("opened_at") or "", t.get("closed_at") or "")
        row["realized_pnl"] = t.get("realized_pnl")     # regression label
        row["won"] = bool(t.get("won"))                 # classification label
        rows.append(row)

    # Every real broker-truth close too — all the data we've ever had.
    rows.extend(_live_rows())

    OUT_DATA.parent.mkdir(parents=True, exist_ok=True)
    OUT_DATA.write_text("\n".join(json.dumps(r, default=str) for r in rows) + ("\n" if rows else ""))

    # Count reasoned AI decisions — the corpus for an eventual LLM fine-tune.
    decisions = 0
    if JOURNAL.exists():
        for line in JOURNAL.read_text().splitlines():
            try:
                decisions += len(json.loads(line).get("decisions", []))
            except Exception:  # noqa: BLE001
                pass

    wins = sum(1 for r in rows if r["won"])
    by_bucket, by_source = {}, {}
    for r in rows:
        b = r.get("asset_class") or "?"
        d = by_bucket.setdefault(b, {"n": 0, "wins": 0})
        d["n"] += 1
        d["wins"] += 1 if r["won"] else 0
        by_source[r.get("source") or "?"] = by_source.get(r.get("source") or "?", 0) + 1

    status = {
        "records": len(rows),
        "wins": wins,
        "losses": len(rows) - wins,
        "win_rate": round(wins / len(rows), 3) if rows else 0.0,
        "reasoned_decisions": decisions,
        "by_source": by_source,
        "by_asset_class": by_bucket,
        "milestones": [
            {"name": "Collect trade outcomes", "target": FIRST_MODEL_TARGET,
             "have": len(rows), "done": len(rows) >= FIRST_MODEL_TARGET},
            {"name": "Train first ranker (gradient-boosted)", "target": FIRST_MODEL_TARGET,
             "have": len(rows), "done": False},
            {"name": "Fine-tune our LLM (reasoned decisions)", "target": LLM_TARGET,
             "have": decisions, "done": False},
        ],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    OUT_STATUS.write_text(json.dumps(status, indent=2) + "\n")
    log.info("training data: %d rows · %d reasoned decisions", len(rows), decisions)
    return status


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    s = build()
    print("training rows:", s["records"], "· reasoned decisions:", s["reasoned_decisions"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
