"""Learning pass — turn the outcomes ledger into per-bucket realized edge.

The closed-loop memory: paper_trades.py writes every close to
memory/trades_ledger.json; THIS reads it and estimates, per bucket
(asset_class / structure / correlation cluster / size), the realized win rate
and expectancy. The scanner consumes the result to favor what has actually
worked and downweight what hasn't.

Overfitting discipline (this is the whole point — a naive learner would hardcode
8-trade noise and get punished at a regime turn):
  - a bucket is only ACTIONABLE at n >= MIN_SAMPLE closes;
  - win rates are SHRUNK toward the global prior with a pseudo-count (Beta-
    Binomial), so a 3/3 bucket doesn't scream "100%";
  - the rank multiplier is CLAMPED to a narrow band.

Until a bucket clears the sample bar its multiplier is exactly 1.0 — the loop is
built and safe, and it only starts biting once the evidence is real.

Pure logic (shrink_win_rate / bucket_stats / build_learnings /
candidate_multiplier) is unit-tested in scripts/test_learn.py.
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Single source of truth for the classification helpers (no cycle: paper_trades
# never imports learn).
from scripts.paper_trades import cluster_of, asset_class

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = REPO_ROOT / "memory"
LEDGER_FILE = MEMORY_DIR / "trades_ledger.json"
LEARNINGS_FILE = MEMORY_DIR / "learnings.json"
LEARNINGS_MD = MEMORY_DIR / "learnings.md"

log = logging.getLogger("learn")

MIN_SAMPLE = int(os.getenv("LEARN_MIN_SAMPLE", "20"))   # per-bucket closes before it's actionable
SHRINK_K = float(os.getenv("LEARN_SHRINK_K", "10"))     # Beta-Binomial pseudo-count
MULT_LO = float(os.getenv("LEARN_MULT_LO", "0.5"))      # per-bucket multiplier floor
MULT_HI = float(os.getenv("LEARN_MULT_HI", "1.5"))      # per-bucket multiplier ceiling
TOTAL_LO = float(os.getenv("LEARN_TOTAL_LO", "0.4"))    # combined (per-candidate) floor
TOTAL_HI = float(os.getenv("LEARN_TOTAL_HI", "1.6"))    # combined ceiling


def shrink_win_rate(wins, n, prior, k=SHRINK_K):
    """Beta-Binomial shrinkage: pull a small sample's win rate toward the global
    prior. (wins + k*prior) / (n + k). At n>>k -> the raw rate; at n<<k -> prior."""
    if n + k <= 0:
        return prior
    return (wins + k * prior) / (n + k)


def bucket_stats(trades, key):
    """Aggregate closed trades by key(t) -> {value: stats}. Skips key==None."""
    out = {}
    for t in trades:
        v = key(t)
        if v is None:
            continue
        b = out.setdefault(v, {"n": 0, "wins": 0, "losses": 0,
                               "sum_pnl": 0.0, "sum_win": 0.0, "sum_loss": 0.0})
        pnl = float(t.get("realized_pnl") or 0)
        b["n"] += 1
        b["sum_pnl"] += pnl
        if pnl > 0:
            b["wins"] += 1
            b["sum_win"] += pnl
        else:
            b["losses"] += 1
            b["sum_loss"] += pnl
    for b in out.values():
        n = b["n"]
        b["win_rate"] = round(b["wins"] / n, 3) if n else None
        b["avg_pnl"] = round(b["sum_pnl"] / n, 2) if n else None
        b["avg_win"] = round(b["sum_win"] / b["wins"], 2) if b["wins"] else None
        b["avg_loss"] = round(b["sum_loss"] / b["losses"], 2) if b["losses"] else None
        b["total_pnl"] = round(b["sum_pnl"], 2)
        for drop in ("sum_pnl", "sum_win", "sum_loss"):
            b.pop(drop, None)
    return out


def annotate_multiplier(b, prior_wr, min_sample=MIN_SAMPLE, k=SHRINK_K,
                        lo=MULT_LO, hi=MULT_HI):
    """Attach shrunk_win_rate, actionable, multiplier, recommendation to a bucket.
    Returns the multiplier (1.0 when not yet actionable)."""
    n = b["n"]
    sw = shrink_win_rate(b["wins"], n, prior_wr, k)
    b["shrunk_win_rate"] = round(sw, 3)
    if n < min_sample or prior_wr <= 0:
        b["actionable"] = False
        b["multiplier"] = 1.0
        b["recommendation"] = "watch (n={} < {})".format(n, min_sample)
        return 1.0
    mult = max(lo, min(hi, sw / prior_wr))
    b["actionable"] = True
    b["multiplier"] = round(mult, 3)
    if b.get("avg_pnl") is not None and b["avg_pnl"] < 0 and sw < prior_wr:
        b["recommendation"] = "AVOID (neg expectancy; wr {:.0%} < prior {:.0%})".format(sw, prior_wr)
    elif mult > 1.05:
        b["recommendation"] = "favor"
    elif mult < 0.95:
        b["recommendation"] = "downweight"
    else:
        b["recommendation"] = "neutral"
    return b["multiplier"]


DEFAULT_DIMS = {
    "asset_class": lambda t: t.get("asset_class"),
    "structure": lambda t: t.get("structure"),
    "cluster": lambda t: t.get("cluster"),
    "size": lambda t: "{}x".format(int(t.get("contracts") or 1)),
}


def build_learnings(ledger_trades, min_sample=MIN_SAMPLE, k=SHRINK_K, dims=None):
    """Full learnings dict: global prior + per-dimension bucket stats/multipliers."""
    dims = dims or DEFAULT_DIMS
    closed = [t for t in ledger_trades if t.get("realized_pnl") is not None]
    n = len(closed)
    wins = sum(1 for t in closed if (t.get("realized_pnl") or 0) > 0)
    prior_wr = wins / n if n else 0.0
    buckets = {}
    for name, key in dims.items():
        bs = bucket_stats(closed, key)
        for b in bs.values():
            annotate_multiplier(b, prior_wr, min_sample, k)
        buckets[name] = bs
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "params": {"min_sample": min_sample, "shrink_k": k,
                   "mult_lo": MULT_LO, "mult_hi": MULT_HI,
                   "total_lo": TOTAL_LO, "total_hi": TOTAL_HI},
        "global": {"closed": n, "wins": wins, "losses": n - wins,
                   "win_rate": round(prior_wr, 3),
                   "total_pnl": round(sum(float(t.get("realized_pnl") or 0) for t in closed), 2)},
        "buckets": buckets,
    }


def candidate_multiplier(learnings, underlying=None, structure=None,
                         total_lo=TOTAL_LO, total_hi=TOTAL_HI):
    """Combined rank multiplier for a fresh candidate from the learned buckets it
    belongs to (asset_class + structure + cluster). Product of ACTIONABLE bucket
    multipliers, clamped. Returns (multiplier, notes[]). 1.0 if nothing actionable."""
    if not learnings:
        return 1.0, []
    b = learnings.get("buckets", {})
    lookups = []
    if underlying is not None:
        lookups.append(("asset_class", asset_class(underlying)))
        lookups.append(("cluster", cluster_of(underlying)))
    if structure is not None:
        lookups.append(("structure", structure))
    m, notes = 1.0, []
    for dim, val in lookups:
        st = b.get(dim, {}).get(val)
        if st and st.get("actionable"):
            m *= st.get("multiplier", 1.0)
            notes.append("{}={} ×{:.2f}".format(dim, val, st["multiplier"]))
    m = max(total_lo, min(total_hi, m))
    return round(m, 3), notes


def load_learnings(path=None):
    """Read memory/learnings.json, or None if absent/unreadable."""
    p = path or LEARNINGS_FILE
    try:
        return json.loads(Path(p).read_text())
    except (OSError, json.JSONDecodeError):
        return None


def _load_ledger():
    try:
        return json.loads(LEDGER_FILE.read_text()).get("trades", [])
    except (OSError, json.JSONDecodeError):
        return []


def learnings_markdown(L):
    """Human-readable digest — so we can always see WHAT the engine learned and why."""
    g = L.get("global", {})
    out = ["# Engine learnings — realized edge by bucket", "",
           "_Generated {} · from the outcomes ledger. Buckets act on the scanner "
           "only at n ≥ {} closes (shrunk toward the global prior). "
           "Below that they're shown but inert (×1.00)._".format(
               L.get("generated_at"), L.get("params", {}).get("min_sample")),
           "",
           "**Global: {} closed · win rate {:.0%} · realized ${:+.2f}**".format(
               g.get("closed", 0), g.get("win_rate", 0), g.get("total_pnl", 0)), ""]
    for dim, bs in L.get("buckets", {}).items():
        out += ["## {}".format(dim), "",
                "| value | n | win rate | shrunk | avg P&L | total | ×mult | call |",
                "|---|---:|---:|---:|---:|---:|---:|---|"]
        for v, b in sorted(bs.items(), key=lambda kv: -(kv[1].get("total_pnl") or 0)):
            out.append("| {} | {} | {} | {:.0%} | {} | ${:+.0f} | ×{:.2f} | {} |".format(
                v, b["n"],
                "{:.0%}".format(b["win_rate"]) if b["win_rate"] is not None else "—",
                b.get("shrunk_win_rate", 0),
                "${:+.0f}".format(b["avg_pnl"]) if b.get("avg_pnl") is not None else "—",
                b.get("total_pnl") or 0, b.get("multiplier", 1.0), b.get("recommendation", "")))
        out.append("")
    return "\n".join(out) + "\n"


def refresh():
    """Build learnings from the current ledger and persist json + md. Returns the
    learnings dict (or None if the ledger is empty). Safe to call every scan."""
    trades = _load_ledger()
    if not trades:
        return None
    L = build_learnings(trades)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    LEARNINGS_FILE.write_text(json.dumps(L, indent=2, default=str) + "\n")
    LEARNINGS_MD.write_text(learnings_markdown(L))
    return L


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
                        stream=sys.stdout)
    L = refresh()
    if not L:
        log.info("learn: ledger empty — nothing to learn yet")
        return 0
    g = L["global"]
    actionable = sum(1 for bs in L["buckets"].values() for b in bs.values() if b.get("actionable"))
    log.info("learn: %d closed · win rate %.0f%% · %d actionable bucket(s) (min_sample=%d)",
             g["closed"], g["win_rate"] * 100, actionable, L["params"]["min_sample"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
