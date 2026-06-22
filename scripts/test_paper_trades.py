"""Tests for the paper-trade book logic.

Run without pytest:  python -m scripts.test_paper_trades
"""
import sys

from scripts.paper_trades import (record_picks, manage_decision, mark_trade, summarize,
                                  cluster_of, asset_class, ledger_record)


def main() -> int:
    f = []

    # --- record_picks: dedup + tag carried ---
    book = {"trades": []}
    picks = [
        {"underlying": "CAT", "short_strike": 775, "long_strike": 770, "expiry": "2026-07-02",
         "credit": 0.83, "bpr": 417, "pop": 0.8, "iv_rank": 0.63, "tag": "live",
         "short_symbol": "CAT 775P", "long_symbol": "CAT 770P"},
        {"underlying": "BA", "short_strike": 205, "long_strike": 200, "expiry": "2026-07-02",
         "credit": 0.82, "bpr": 418, "pop": 0.79, "iv_rank": 0.47, "tag": "paper",
         "short_symbol": "BA 205P", "long_symbol": "BA 200P"},
    ]
    ch = record_picks(book, picks, "2026-06-01")
    if len(book["trades"]) != 2 or len(ch) != 2:
        f.append("record_picks count {}".format(len(book["trades"])))
    if book["trades"][0]["tag"] != "live":
        f.append("tag not carried")
    # re-recording the same picks adds nothing (dedup)
    ch2 = record_picks(book, picks, "2026-06-02")
    if ch2 or len(book["trades"]) != 2:
        f.append("dedup failed: {}".format(ch2))

    # --- manage_decision ---
    # 50% captured -> close win
    a, pnl, why = manage_decision(1.00, 0.50, 30)
    if not (a == "close" and pnl == 50.0 and why == "manage_50pct"):
        f.append("manage 50%: {} {} {}".format(a, pnl, why))
    # stop: debit blows out to 2.6x credit -> close loss
    a, pnl, why = manage_decision(1.00, 2.60, 30)
    if not (a == "close" and pnl == -160.0 and why == "stop_1.5x"):
        f.append("stop: {} {} {}".format(a, pnl, why))
    # hold: small profit, plenty of DTE
    a, pnl, why = manage_decision(1.00, 0.80, 30)
    if a != "hold":
        f.append("should hold: {}".format(a))
    # 21 DTE exit
    a, pnl, why = manage_decision(1.00, 0.70, 20)
    if not (a == "close" and why == "21_dte"):
        f.append("21dte: {} {}".format(a, why))
    # expiry with no marks available -> expire worthless, keep full credit
    a, pnl, why = manage_decision(1.00, None, 0)
    if not (a == "close" and pnl == 100.0 and why == "expired"):
        f.append("expire: {} {} {}".format(a, pnl, why))

    # --- mark_trade: marks + auto-close at target ---
    book2 = {"trades": []}
    record_picks(book2, [picks[0]], "2026-06-01")
    t = book2["trades"][0]
    # marks imply debit 0.40 -> captured 0.43 (>50% of 0.83) -> closes win
    marks = {"CAT 775P": {"mark": 0.60}, "CAT 770P": {"mark": 0.20}}
    reason = mark_trade(t, marks, "2026-06-15")
    if t["status"] != "closed" or reason != "manage_50pct":
        f.append("mark_trade close: {} {}".format(t["status"], reason))
    if t["realized_pnl"] != 40.5:   # 43 gross - 2 legs x $1.25 fees
        f.append("mark realized {}".format(t["realized_pnl"]))

    # open trade that should hold
    book3 = {"trades": []}
    record_picks(book3, [picks[1]], "2026-06-01")
    t3 = book3["trades"][0]
    mark_trade(t3, {"BA 205P": {"mark": 0.70}, "BA 200P": {"mark": 0.20}}, "2026-06-10")  # debit .50, captured .32 <50%
    if t3["status"] != "open" or t3["unrealized_pnl"] != 32.0:
        f.append("hold mark: {} {}".format(t3["status"], t3.get("unrealized_pnl")))

    # --- summarize ---
    s = summarize(book2)  # 1 closed win
    if not (s["closed"] == 1 and s["wins"] == 1 and s["realized_pnl"] == 40.5 and s["win_rate"] == 1.0):
        f.append("summarize: {}".format(s))

    # --- contracts scaling: 3-lot scales unrealized AND realized 3x ---
    book4 = {"trades": []}
    record_picks(book4, [dict(picks[0], contracts=3)], "2026-06-01")
    t4 = book4["trades"][0]
    if t4.get("contracts") != 3:
        f.append("contracts not recorded: {}".format(t4.get("contracts")))
    reason4 = mark_trade(t4, {"CAT 775P": {"mark": 0.60}, "CAT 770P": {"mark": 0.20}}, "2026-06-15")
    if reason4 != "manage_50pct" or t4["realized_pnl"] != 121.5:   # 43x3 - 2x3x1.25 fees
        f.append("contracts scaling: {} {}".format(reason4, t4.get("realized_pnl")))

    # --- event-crush management: hold pre-close-date, force close on it ---
    from scripts.paper_trades import manage_decision_event, trade_symbols
    a1 = manage_decision_event(1.00, 0.80, 5, "2026-06-11", "2026-06-12")
    if a1[0] != "hold":
        f.append("event: should hold before close_date: {}".format(a1))
    a2 = manage_decision_event(1.00, 0.80, 4, "2026-06-12", "2026-06-12")
    if not (a2[0] == "close" and a2[2] == "event_close" and a2[1] == 20.0):
        f.append("event: should event_close on date: {}".format(a2))
    a3 = manage_decision_event(1.00, 0.45, 5, "2026-06-11", "2026-06-12")
    if not (a3[0] == "close" and a3[2] == "manage_50pct"):
        f.append("event: 50% capture still closes early: {}".format(a3))
    # NO 21-dte rule for event trades (dte 5 + small profit -> hold)
    a4 = manage_decision_event(1.00, 0.80, 5, "2026-06-11", "2026-06-20")
    if a4[0] != "hold":
        f.append("event: 21-dte rule must NOT apply: {}".format(a4))

    # --- 4-leg IC marking ---
    ic = {"underlying": "IWM", "structure": "iron_condor", "short_strike": 272, "long_strike": 312,
          "expiry": "2026-07-17", "opened_credit": 1.00, "contracts": 2, "status": "open",
          "close_date": "2026-06-12",
          "symbols": {"put_short": "IWM 272P", "put_long": "IWM 268P",
                      "call_short": "IWM 312C", "call_long": "IWM 316C"}}
    if sorted(trade_symbols(ic)) != sorted(["IWM 272P", "IWM 268P", "IWM 312C", "IWM 316C"]):
        f.append("trade_symbols IC wrong")
    icmarks = {"IWM 272P": {"mark": 0.30}, "IWM 268P": {"mark": 0.10},
               "IWM 312C": {"mark": 0.25}, "IWM 316C": {"mark": 0.05}}
    r = mark_trade(ic, icmarks, "2026-06-12")   # debit (0.2+0.2)=0.40, captured 0.60 >=50% -> manage_50pct
    if r != "manage_50pct" or ic["realized_pnl"] != 110.0:   # 60x2 - 4x2x1.25 fees
        f.append("IC mark/close wrong: {} {}".format(r, ic.get("realized_pnl")))

    # --- concentration caps (Phase 1) ---
    # us_tech cluster cap = 3: a 4th tech name in one batch is blocked.
    book5 = {"trades": []}
    tech = [{"underlying": u, "short_strike": 100, "long_strike": 95, "expiry": "2026-07-17",
             "credit": 0.5, "structure": "short_put_vertical"} for u in ("AAPL", "MSFT", "NVDA", "AMD")]
    record_picks(book5, tech, "2026-06-01")
    if len([t for t in book5["trades"] if t["status"] == "open"]) != 3:
        f.append("cluster cap: expected 3 us_tech, got {}".format(len(book5["trades"])))

    # max per name = 1: same underlying twice (distinct strikes) -> only one opens.
    book6 = {"trades": []}
    dup = [dict(picks[0], short_strike=775, long_strike=770),
           dict(picks[0], short_strike=780, long_strike=775)]   # both CAT, distinct sigs
    record_picks(book6, dup, "2026-06-01")
    if len([t for t in book6["trades"] if t["status"] == "open"]) != 1:
        f.append("per-name cap: expected 1, got {}".format(len(book6["trades"])))

    # total-open cap honored via override.
    book7 = {"trades": []}
    many = [{"underlying": u, "short_strike": 50, "long_strike": 45, "expiry": "2026-07-17",
             "credit": 0.4, "structure": "short_put_vertical"}
            for u in ("XOM", "GLD", "TLT", "JPM", "PFE", "DIS")]   # all different clusters
    record_picks(book7, many, "2026-06-01", caps={"max_open": 4, "max_per_cluster": 9})
    if len([t for t in book7["trades"] if t["status"] == "open"]) != 4:
        f.append("max_open cap: expected 4, got {}".format(len(book7["trades"])))

    # --- classification helpers ---
    # QQQ is tech-concentrated, NOT a broad index — buckets as single_name/us_tech.
    if cluster_of("QQQ") != "us_tech" or asset_class("QQQ") != "single_name":
        f.append("classify QQQ: {} / {}".format(cluster_of("QQQ"), asset_class("QQQ")))
    if cluster_of("XOM") != "energy" or asset_class("XOM") != "single_name":
        f.append("classify XOM: {} / {}".format(cluster_of("XOM"), asset_class("XOM")))
    if asset_class("GLD") != "sector_etf":
        f.append("classify GLD: {}".format(asset_class("GLD")))

    # --- ledger record shape ---
    lr = ledger_record({"id": "x", "underlying": "SPY", "structure": "short_put_vertical",
                        "contracts": 2, "opened_credit": 1.0, "iv_rank": 0.6, "pop": 0.8,
                        "realized_pnl": 97.0, "close_reason": "manage_50pct", "closed_at": "2026-06-10"})
    if not (lr["asset_class"] == "index_etf" and lr["cluster"] == "us_index"
            and lr["won"] is True and lr["realized_pnl"] == 97.0):
        f.append("ledger_record: {}".format(lr))

    # --- reconcile_to_caps: trims over-cap opens at their marks, keeps best ---
    from scripts.paper_trades import reconcile_to_caps
    book8 = {"trades": []}
    # 5 QQQ tech opens (cluster cap 3 / name cap 1) with marks; index SPY kept first
    mk = lambda u, s, l, cr, dbt, unp, idx: {
        "underlying": u, "structure": "short_put_vertical", "short_strike": s, "long_strike": l,
        "expiry": "2026-07-17", "opened_credit": cr, "current_debit": dbt, "unrealized_pnl": unp,
        "contracts": 1, "status": "open", "id": "p_{}".format(idx)}
    book8["trades"] = [
        mk("QQQ", 100, 95, 1.0, 1.5, -50, 1),
        mk("AMD", 100, 95, 1.0, 1.2, -20, 2),
        mk("MSFT", 100, 95, 1.0, 1.1, -10, 3),
        mk("INTC", 100, 95, 1.0, 2.0, -100, 4),   # us_tech 4th -> must close (worst)
        mk("SPY", 100, 95, 1.0, 0.6, 40, 5),       # index -> always kept
    ]
    closed8 = reconcile_to_caps(book8, "2026-06-16", caps={"max_per_name": 1, "max_per_cluster": 3, "max_open": 8})
    open_left = [t for t in book8["trades"] if t["status"] == "open"]
    if len(open_left) != 4 or len(closed8) != 1:
        f.append("reconcile counts: open {} closed {}".format(len(open_left), len(closed8)))
    if closed8 and closed8[0]["underlying"] != "INTC":
        f.append("reconcile should drop worst tech (INTC): {}".format(closed8[0]["underlying"]))
    if closed8 and closed8[0]["close_reason"] != "reconcile_caps":
        f.append("reconcile reason: {}".format(closed8[0].get("close_reason")))
    # realized = (1.0 - 2.0)*100*1 - 2 legs*1.25 = -100 - 2.50
    if closed8 and closed8[0]["realized_pnl"] != -102.5:
        f.append("reconcile realized: {}".format(closed8[0]["realized_pnl"]))
    # idempotent: second pass closes nothing
    if reconcile_to_caps(book8, "2026-06-16", caps={"max_per_name": 1, "max_per_cluster": 3, "max_open": 8}):
        f.append("reconcile not idempotent")

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("record/dedup ✓ · manage rules ✓ · mark+auto-close ✓ · summary ✓")
    print("All paper_trades tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
