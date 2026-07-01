"""
monitor/positions_sync.py — Reconcile trades.json with broker positions.

Reads live broker positions from the gist (which the bot updates every poll),
compares to trades.json, auto-adds new trades, marks closed trades.

Eliminates the need to manually edit trades.json when opening positions.
The bot detects them automatically within the next sync cycle.
"""

import json
import re
import time
from datetime import date
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
TRADES_FILE = REPO_ROOT / "trades.json"
GIST_URL = "https://gist.githubusercontent.com/LarryBFIS/08e2cb50b3a645e9569617a6298ee987/raw/last_poll.json"


def load_trades():
    if not TRADES_FILE.exists():
        return {"schema_version": 1, "trades": []}
    with open(TRADES_FILE) as f:
        return json.load(f)


def save_trades(data):
    with open(TRADES_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_broker_positions():
    """Pull live position state from the gist."""
    response = requests.get(f"{GIST_URL}?t={int(time.time())}", timeout=15)
    response.raise_for_status()
    data = response.json()
    return data.get("positions", data.get("trades", []))


def parse_strikes_string(strikes_str):
    """Parse '721/716p' style into structured strike data."""
    if not strikes_str:
        return None
    match = re.match(r'(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)([pc]?)', str(strikes_str).strip().lower())
    if not match:
        return None
    return {
        'short_strike': int(float(match.group(1))),
        'long_strike': int(float(match.group(2))),
        'option_type': 'put' if 'p' in match.group(3) else 'call',
    }


def get_field(pos, *candidates):
    """Defensive field lookup — try multiple field name variants."""
    for name in candidates:
        v = pos.get(name)
        if v not in (None, "", "—", "-"):
            return v
    return None


def normalize_expiry(exp):
    if not exp:
        return ""
    exp = str(exp)
    return exp[:10] if len(exp) >= 10 else exp


def trade_sig(underlying, short, long_strike, expiry):
    return f"{underlying.upper()}_{int(short)}_{int(long_strike)}_{normalize_expiry(expiry)}"


def next_trade_id(existing_trades, underlying, short, long_strike):
    nums = []
    for t in existing_trades:
        m = re.match(r'trade_(\d+)_', t.get('id', ''))
        if m:
            nums.append(int(m.group(1)))
    next_num = (max(nums) if nums else 0) + 1
    return f"trade_{next_num:03d}_{underlying.lower()}_{int(short)}_{int(long_strike)}"


def normalize_position(pos):
    """Convert broker position to trades.json schema. Returns None if unparseable."""
    underlying = get_field(pos, 'symbol', 'underlying', 'ticker')
    if not underlying:
        return None

    short_strike = get_field(pos, 'short_strike', 'short')
    long_strike = get_field(pos, 'long_strike', 'long')

    if not (short_strike and long_strike):
        strikes_str = get_field(pos, 'strikes', 'strikes_display')
        parsed = parse_strikes_string(strikes_str)
        if parsed:
            short_strike = parsed['short_strike']
            long_strike = parsed['long_strike']
            opt_type = parsed['option_type']
        else:
            return None
    else:
        opt_type = get_field(pos, 'option_type', 'type') or 'put'

    expiry = normalize_expiry(get_field(pos, 'expiry', 'expiration', 'exp'))
    credit = get_field(pos, 'credit', 'credit_per_contract', 'opening_credit')
    bpr = get_field(pos, 'bpr_total', 'bpr', 'bp_effect', 'max_loss')
    contracts = get_field(pos, 'contracts', 'qty', 'quantity') or 1

    return {
        "underlying": underlying.upper(),
        "structure": f"short_{opt_type}_vertical",
        "short_strike": int(float(short_strike)),
        "long_strike": int(float(long_strike)),
        "expiry": expiry,
        "contracts": int(contracts),
        "credit_per_contract": float(credit) if credit else None,
        "bpr_total": float(bpr) if bpr else None,
    }


def sync():
    print("=== POSITIONS SYNC ===")
    print("Fetching broker state from gist...")

    try:
        broker_positions = fetch_broker_positions()
    except Exception as e:
        print(f"  ERROR fetching gist: {e}")
        return

    print(f"  Found {len(broker_positions)} broker positions.\n")

    data = load_trades()
    trades = data.setdefault("trades", [])

    open_sigs = {}
    closed_sigs = set()
    for t in trades:
        if not (t.get("short_strike") and t.get("long_strike")):
            continue
        sig = trade_sig(t["underlying"], t["short_strike"], t["long_strike"], t["expiry"])
        if t.get("status") == "open":
            open_sigs[sig] = t
        elif t.get("status") == "closed":
            closed_sigs.add(sig)

    broker_sigs = set()
    added = 0

    for pos in broker_positions:
        normalized = normalize_position(pos)
        if not normalized:
            print(f"  ? UNRECOGNIZED position format. Available fields: {sorted(pos.keys())}")
            print(f"    Paste this output to Claude to fix the field mapping.")
            continue

        sig = trade_sig(
            normalized["underlying"],
            normalized["short_strike"],
            normalized["long_strike"],
            normalized["expiry"],
        )
        broker_sigs.add(sig)

        if sig in open_sigs:
            print(f"  = TRACKED: {normalized['underlying']} {normalized['short_strike']}/{normalized['long_strike']} exp {normalized['expiry']}")
            continue

        if sig in closed_sigs:
            # The transaction ledger already booked this position CLOSED, but the
            # gist snapshot still shows it (snapshots lag a poll or two after a fill).
            # Do NOT re-add it — that created order-id-less phantom "open" duplicates
            # that the ledger could never reconcile. Ledger is the source of truth.
            print(f"  ~ SNAPSHOT LAG: {normalized['underlying']} {normalized['short_strike']}/{normalized['long_strike']} already closed in ledger — not re-adding")
            continue

        new_id = next_trade_id(trades, normalized['underlying'], normalized['short_strike'], normalized['long_strike'])
        credit = normalized.get('credit_per_contract')
        width = abs(normalized['short_strike'] - normalized['long_strike'])

        new_trade = {
            "id": new_id,
            "underlying": normalized["underlying"],
            "structure": normalized["structure"],
            "short_strike": normalized["short_strike"],
            "long_strike": normalized["long_strike"],
            "expiry": normalized["expiry"],
            "contracts": normalized["contracts"],
            "opened_at": date.today().isoformat(),
            "credit_per_contract": credit,
            "max_profit_total": int(credit * 100) if credit else None,
            "max_loss_total": int((width - credit) * 100) if credit else None,
            "bpr_total": normalized.get("bpr_total"),
            "pop_at_open": None,
            "p50_at_open": None,
            "manage_at_pct": 0.50,
            "exit_dte": 21,
            "status": "open",
            "notes": f"Auto-synced from broker on {date.today().isoformat()}",
        }
        trades.append(new_trade)
        added += 1
        print(f"  + ADDED: {new_id} (credit {credit}, BPR {normalized.get('bpr_total')})")

    # Closes are intentionally NOT marked from snapshot absence. A trade missing
    # from a single positions snapshot does NOT mean it closed — freshly-opened
    # positions (especially in the 24-hour session) are routinely absent for a poll
    # or two, which used to flip live trades to "closed" and vanish them from the
    # dashboard. Close detection is owned by sync_trades, which closes a trade only
    # when the broker-truth transaction ledger shows actual closing transactions.
    missing = [t["id"] for sig, t in open_sigs.items() if sig not in broker_sigs]
    if missing:
        print(f"  (not in snapshot — left OPEN for the ledger to confirm: {', '.join(missing)})")

    if added:
        save_trades(data)
        print(f"\nSaved trades.json: +{added} added (closes handled by the ledger sync).")
    else:
        print("\nNo changes needed — already in sync.")


if __name__ == "__main__":
    sync()
