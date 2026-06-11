"""Paper-trade book — track the scanner's picks with real P&L, zero risk.

Each scan, every ranked pick is recorded here as a hypothetical short put
vertical (deduped by underlying/strikes/expiry). On each run we mark the open
paper trades at live option marks and apply the same management rules as the
real book (take profit at 50% of credit, exit at 21 DTE, expire worthless),
logging realized + open P&L. This proves the edge BEFORE a dollar is risked,
and it's what the live executor will plug into (live-tagged picks route to real
orders; the rest keep paper-trading).

Pure logic (record_picks / manage_decision / mark_trade) is unit-tested in
scripts/test_paper_trades.py; only main() touches the network.
"""
import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PAPER_DIR = REPO_ROOT / "paper"
BOOK_FILE = PAPER_DIR / "book.json"
SCAN_FILE = REPO_ROOT / "scan" / "opportunities.json"

BOOK_SCHEMA = 2        # bump to wipe a book written by buggy older logic
import os
# Real-money fidelity: tastytrade ~$1/contract/leg to open + regulatory both
# ways; ~$1.25 per leg per contract round-trip. Deducted from every realized.
FEE_PER_LEG = float(os.getenv("PAPER_FEE_PER_LEG", "1.25"))
MANAGE_FRAC = 0.5      # take profit at 50% of credit
EXIT_DTE = 21         # hard exit
STOP_DEBIT_MULT = 1.5  # cut at 1.5x credit (debit to close >= 2.5x credit)

log = logging.getLogger("paper")


def _sig(t):
    return "{}_{:g}_{:g}_{}".format(t.get("underlying"), t.get("short_strike"),
                                    t.get("long_strike"), t.get("expiry"))


def record_picks(book, picks, today):
    """Add new picks as open paper trades (deduped by signature). Returns changes[].

    Dedup against EVERY trade ever recorded — not just open ones. A pick that
    already closed must not reappear and re-open on the next scan; that churn was
    inflating the book with phantom repeat-wins.
    """
    trades = book.setdefault("trades", [])
    known_sigs = {_sig(t) for t in trades}
    changes = []
    for p in picks:
        sig = _sig(p)
        if sig in known_sigs:
            continue
        n = len(trades) + 1
        trades.append({
            "id": "paper_{:04d}_{}".format(n, (p.get("underlying") or "x").lower()),
            "sig": sig,
            "underlying": p.get("underlying"),
            "structure": p.get("structure", "short_put_vertical"),
            "short_strike": p.get("short_strike"),
            "long_strike": p.get("long_strike"),
            "short_symbol": p.get("short_symbol"),
            "long_symbol": p.get("long_symbol"),
            "symbols": p.get("symbols"),         # 4-leg map for iron condors
            "expiry": p.get("expiry"),
            "credit": p.get("credit"),
            "bpr": p.get("bpr"),
            "pop": p.get("pop"),
            "iv_rank": p.get("iv_rank"),
            "tag": p.get("tag", "paper"),
            "contracts": int(p.get("contracts") or 1),
            "event": p.get("event"),
            "close_date": p.get("close_date"),   # event-crush: force close on this date
            "day_trade": p.get("day_trade"),
            "close_after_et": p.get("close_after_et"),
            "opened_at": today,
            # Real-money fidelity: open at the EXECUTABLE credit (cross the
            # spread), never the flattering mid — real fills can only match or beat this.
            "opened_credit": p.get("credit") or p.get("mid_credit"),
            "status": "open",
            "realized_pnl": None,
            "unrealized_pnl": None,
            "current_debit": None,
            "close_reason": None,
        })
        known_sigs.add(sig)
        changes.append("opened {} {:g}/{:g}p [{}]".format(
            p.get("underlying"), p.get("short_strike"), p.get("long_strike"), p.get("tag", "paper")))
    return changes


def manage_decision(opened_credit, current_debit, dte):
    """Return (action, realized_pnl_per_contract_$ or None).

    Mirrors the real rules: take profit at 50% captured, cut at 1.5x credit loss,
    hard exit at 21 DTE, expire worthless at/after expiry.
    """
    if current_debit is not None:
        captured = opened_credit - current_debit  # per share
        if captured >= MANAGE_FRAC * opened_credit:
            return "close", round(captured * 100, 2), "manage_50pct"
        if (current_debit - opened_credit) >= STOP_DEBIT_MULT * opened_credit:
            return "close", round(captured * 100, 2), "stop_1.5x"
    if dte is not None and dte <= 0:
        realized = round((opened_credit - (current_debit if current_debit is not None else 0)) * 100, 2)
        return "close", realized, "expired"
    if dte is not None and dte <= EXIT_DTE:
        if current_debit is not None:
            return "close", round((opened_credit - current_debit) * 100, 2), "21_dte"
    return "hold", None, None


def manage_decision_event(opened_credit, current_debit, dte, today, close_date):
    """Management for event-crush holds: NO 21-DTE rule (these are short-dated by
    design). Take 50% early, stop at 1.5x, force close at marks on/after the
    close date, expire if somehow held to expiry."""
    if current_debit is not None:
        captured = opened_credit - current_debit
        if captured >= MANAGE_FRAC * opened_credit:
            return "close", round(captured * 100, 2), "manage_50pct"
        if (current_debit - opened_credit) >= STOP_DEBIT_MULT * opened_credit:
            return "close", round(captured * 100, 2), "stop_1.5x"
        if close_date and today >= close_date:
            return "close", round(captured * 100, 2), "event_close"
    if dte is not None and dte <= 0:
        realized = round((opened_credit - (current_debit if current_debit is not None else 0)) * 100, 2)
        return "close", realized, "expired"
    return "hold", None, None


def trade_symbols(t):
    """All option symbols a paper trade needs marks for (2-leg vertical or 4-leg IC)."""
    if t.get("symbols"):
        return [v for v in t["symbols"].values() if v]
    return [x for x in (t.get("short_symbol"), t.get("long_symbol")) if x]


def _mark_of(q):
    q = q or {}
    return q.get("mark") if q.get("mark") is not None else _mid(q)


def _exec_buy(q):
    """Cost to BUY a leg back: the ASK (fallback mark/mid) — conservative."""
    q = q or {}
    return q.get("ask") if q.get("ask") is not None else _mark_of(q)


def _exec_sell(q):
    """Proceeds SELLING a leg: the BID (fallback mark/mid) — conservative."""
    q = q or {}
    return q.get("bid") if q.get("bid") is not None else _mark_of(q)


def mark_trade(trade, marks, today, now_hhmm=None):
    """Update one open paper trade with current marks + management. Mutates trade."""
    current_debit = None
    ctr = int(trade.get("contracts") or 1)   # scale per-contract P&L by position size
    syms = trade.get("symbols")
    # Real-money fidelity: cost-to-close at EXECUTABLE prices (buy back shorts at
    # the ask, sell longs at the bid) — real exits match or beat this.
    if syms:   # iron condor: debit = (put spread) + (call spread)
        ps = _exec_buy(marks.get(syms.get("put_short")))
        pl = _exec_sell(marks.get(syms.get("put_long")))
        cs = _exec_buy(marks.get(syms.get("call_short")))
        cl = _exec_sell(marks.get(syms.get("call_long")))
        if None not in (ps, pl, cs, cl):
            current_debit = round((ps - pl) + (cs - cl), 2)
    else:      # two-leg vertical
        short_mark = _exec_buy(marks.get(trade.get("short_symbol")))
        long_mark = _exec_sell(marks.get(trade.get("long_symbol")))
        if short_mark is not None and long_mark is not None:
            current_debit = round(short_mark - long_mark, 2)
    if current_debit is not None:
        trade["current_debit"] = current_debit
        trade["unrealized_pnl"] = round((trade["opened_credit"] - current_debit) * 100 * ctr, 2)
    dte = _dte(trade.get("expiry"), today)
    if (trade.get("day_trade") and now_hhmm and current_debit is not None
            and now_hhmm >= (trade.get("close_after_et") or "15:30")):
        # Day trade: force close same day at executable prices.
        action, realized, reason = "close", round((trade["opened_credit"] - current_debit) * 100, 2), "day_close"
    elif trade.get("close_date"):
        action, realized, reason = manage_decision_event(
            trade["opened_credit"], current_debit, dte, today, trade["close_date"])
    else:
        action, realized, reason = manage_decision(trade["opened_credit"], current_debit, dte)
    if action == "close":
        trade["status"] = "closed"
        trade["closed_at"] = today
        legs = 4 if syms else 2
        fees = round(FEE_PER_LEG * legs * ctr, 2)
        trade["fees"] = fees
        trade["realized_pnl"] = round(realized * ctr - fees, 2) if realized is not None else realized
        trade["unrealized_pnl"] = None
        trade["close_reason"] = reason
        return reason
    return None


def summarize(book):
    trades = book.get("trades", [])
    closed = [t for t in trades if t.get("status") == "closed"]
    opent = [t for t in trades if t.get("status") == "open"]
    realized = round(sum(t.get("realized_pnl") or 0 for t in closed), 2)
    unreal = round(sum(t.get("unrealized_pnl") or 0 for t in opent), 2)
    wins = sum(1 for t in closed if (t.get("realized_pnl") or 0) > 0)
    return {
        "trades": len(trades), "open": len(opent), "closed": len(closed),
        "wins": wins, "losses": len(closed) - wins,
        "win_rate": round(wins / len(closed), 3) if closed else None,
        "realized_pnl": realized, "open_unrealized_pnl": unreal,
        "total_pnl": round(realized + unreal, 2),
    }


# ── helpers ──────────────────────────────────────────────────────────────
def _mid(q):
    b, a = q.get("bid"), q.get("ask")
    return (b + a) / 2 if (b is not None and a is not None) else None


def _dte(expiry, today):
    if not expiry:
        return None
    try:
        d0 = date.fromisoformat(today)
        d1 = date.fromisoformat(expiry[:10])
        return (d1 - d0).days
    except ValueError:
        return None


def _load(path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return default


def _notify_opens(new_trades):
    """Pushover ping for every paper trade the engine just opened, with the same
    ticket numbers you'd see on tastytrade — so you can replicate it live if you
    want. Defensive: a notify failure never fails the paper run."""
    try:
        from monitor import notifier
        lines = []
        for t in new_trades:
            st = (t.get("structure") or "")
            code = ("IC" if "condor" in st else "VC" if "call" in st else "VP")
            lines.append("{} {} {:g}/{:g}{} ×{} · ${:.2f} cr · POP {} · [{}]".format(
                t.get("underlying"), code, t.get("short_strike") or 0, t.get("long_strike") or 0,
                "p/c" if code == "IC" else ("c" if code == "VC" else "p"),
                int(t.get("contracts") or 1), t.get("opened_credit") or 0,
                "{:.0%}".format(t["pop"]) if t.get("pop") is not None else "—",
                (t.get("tag") or "paper").upper()))
        notifier.send(
            title="📋 Paper: {} trade{} opened".format(len(new_trades), "s" if len(new_trades) > 1 else ""),
            message="Engine opened (paper, at live quotes):\n" + "\n".join(lines)
                    + "\n\nWant to replicate one live? Bring it to chat and we'll size it together.",
            priority=notifier.PRIORITY_NORMAL,
            sound=notifier.SOUND_INFO,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("paper open notify failed: %s", e)


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
                        stream=sys.stdout)
    today = date.today().isoformat()
    book = _load(BOOK_FILE, {"schema_version": BOOK_SCHEMA, "trades": []})
    if book.get("schema_version") != BOOK_SCHEMA:
        # Old book came from the churn-prone v1 logic (phantom repeat wins).
        # Start clean rather than carry forward poisoned numbers.
        log.warning("Paper book schema %s != %s — resetting to a clean book.",
                    book.get("schema_version"), BOOK_SCHEMA)
        book = {"schema_version": BOOK_SCHEMA, "trades": []}

    scan = _load(SCAN_FILE, {})
    picks = scan.get("top", [])
    n_before = len(book.get("trades", []))
    changes = record_picks(book, picks, today) if picks else []
    new_trades = book["trades"][n_before:]
    if new_trades:
        _notify_opens(new_trades)

    # Mark + manage open paper trades at live option marks.
    open_trades = [t for t in book["trades"] if t.get("status") == "open"]
    symbols = [s for t in open_trades for s in trade_symbols(t)]
    marks = {}
    if symbols:
        try:
            from monitor.tastytrade_client import TastytradeClient
            marks = TastytradeClient().fetch_option_quotes(sorted(set(symbols)))
        except Exception as e:  # noqa: BLE001
            log.warning("paper marks fetch failed: %s", e)
    try:
        from zoneinfo import ZoneInfo
        now_hhmm = datetime.now(ZoneInfo("America/New_York")).strftime("%H:%M")
    except Exception:  # noqa: BLE001
        now_hhmm = None
    closed_now = []
    for t in open_trades:
        reason = mark_trade(t, marks, today, now_hhmm)
        if reason:
            closed_now.append("{} -> {}".format(t["id"], reason))

    summary = summarize(book)
    book["updated_at"] = datetime.now(timezone.utc).isoformat()
    book["summary"] = summary
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    BOOK_FILE.write_text(json.dumps(book, indent=2, default=str) + "\n")
    _write_summary(book, summary)

    log.info("Paper book: %d trades (%d open / %d closed) · realized $%+.2f · open $%+.2f%s%s",
             summary["trades"], summary["open"], summary["closed"],
             summary["realized_pnl"], summary["open_unrealized_pnl"],
             "; opened: " + ", ".join(changes) if changes else "",
             "; closed: " + ", ".join(closed_now) if closed_now else "")
    return 0


def _write_summary(book, s):
    lines = ["# Paper-trade book", "",
             "_Shadow P&L of the scanner's picks — zero risk, proving the edge. "
             "Updated {}._".format(book.get("updated_at")), "",
             "**{} trades · {} open / {} closed · win rate {} · realized ${:+.2f} · open ${:+.2f} · total ${:+.2f}**".format(
                 s["trades"], s["open"], s["closed"],
                 "{:.0%}".format(s["win_rate"]) if s["win_rate"] is not None else "—",
                 s["realized_pnl"], s["open_unrealized_pnl"], s["total_pnl"]),
             "", "| ID | Trade | Tag | Status | Credit | Realized | Unreal | Reason |",
             "|---|---|---|---|---:|---:|---:|---|"]
    for t in book.get("trades", []):
        lines.append("| {} | {} {:g}/{:g}p | {} | {} | ${:.2f} | {} | {} | {} |".format(
            t.get("id", ""), t.get("underlying", ""), t.get("short_strike", 0), t.get("long_strike", 0),
            (t.get("tag") or "").upper(), t.get("status", ""), t.get("opened_credit") or 0,
            "${:+.0f}".format(t["realized_pnl"]) if t.get("realized_pnl") is not None else "—",
            "${:+.0f}".format(t["unrealized_pnl"]) if t.get("unrealized_pnl") is not None else "—",
            t.get("close_reason") or ""))
    (PAPER_DIR / "summary.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
