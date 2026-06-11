"""Tests for the paper-trade book logic.

Run without pytest:  python -m scripts.test_paper_trades
"""
import sys

from scripts.paper_trades import record_picks, manage_decision, mark_trade, summarize


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
