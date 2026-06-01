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
    if t["realized_pnl"] != 43.0:
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
    if not (s["closed"] == 1 and s["wins"] == 1 and s["realized_pnl"] == 43.0 and s["win_rate"] == 1.0):
        f.append("summarize: {}".format(s))

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
