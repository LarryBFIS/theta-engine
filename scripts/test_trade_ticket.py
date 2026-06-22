"""Tests for the trade-ticket builder.

Run without pytest:  python -m scripts.test_trade_ticket
"""
import sys

from scripts.trade_ticket import build_ticket, struct_code


def main() -> int:
    f = []

    # --- put vertical ---
    pv = build_ticket({"underlying": "QQQ", "structure": "short_put_vertical",
                       "short_strike": 694, "long_strike": 685, "expiry": "2026-07-17",
                       "credit": 1.10, "bpr": 790, "max_loss": 790, "contracts": 1, "pop": 0.8})
    if pv["code"] != "VP" or pv["limit"] != 1.10 or pv["manage"]["close_debit"] != 0.55:
        f.append("pv core: {}".format({k: pv[k] for k in ("code", "limit")}))
    if [(l["action"], l["strike"], l["type"]) for l in pv["legs"]] != [("SELL", 694, "P"), ("BUY", 685, "P")]:
        f.append("pv legs: {}".format(pv["legs"]))
    if pv["max_loss_total"] != 790 or pv["manage"]["stop_debit"] != 2.75:
        f.append("pv risk: {} {}".format(pv["max_loss_total"], pv["manage"]["stop_debit"]))

    # --- call vertical ---
    cv = build_ticket({"underlying": "MA", "structure": "short_call_vertical",
                       "short_strike": 520, "long_strike": 525, "expiry": "2026-07-17",
                       "credit": 0.70, "max_loss": 430, "contracts": 2})
    if cv["code"] != "VC":
        f.append("cv code")
    if [(l["action"], l["strike"], l["type"]) for l in cv["legs"]] != [("SELL", 520, "C"), ("BUY", 525, "C")]:
        f.append("cv legs: {}".format(cv["legs"]))
    if cv["max_loss_total"] != 860:   # 430 x 2
        f.append("cv maxloss scaling: {}".format(cv["max_loss_total"]))

    # --- iron condor (4 legs, explicit strikes) ---
    ic = build_ticket({"underlying": "IWM", "structure": "iron_condor",
                       "put_short_strike": 281, "put_long_strike": 279,
                       "call_short_strike": 309, "call_long_strike": 311,
                       "short_strike": 281, "long_strike": 309, "expiry": "2026-07-02",
                       "credit": 0.54, "max_loss": 146, "contracts": 1, "pop": 0.63})
    legs = [(l["action"], l["strike"], l["type"]) for l in ic["legs"]]
    if legs != [("SELL", 281, "P"), ("BUY", 279, "P"), ("SELL", 309, "C"), ("BUY", 311, "C")]:
        f.append("ic legs: {}".format(legs))
    if ic["code"] != "IC" or ic["manage"]["close_debit"] != 0.27:
        f.append("ic core: {} {}".format(ic["code"], ic["manage"]["close_debit"]))

    # --- copy-ready text contains the essentials ---
    t = ic["text"]
    for needle in ("IWM IC ×1", "SELL 281P", "BUY 311C", "$0.54 net credit", "GTC buy-to-close @ $0.27"):
        if needle not in t:
            f.append("text missing '{}': {}".format(needle, t))

    # --- live-cap fit flag (the SPY 703/712 guardrail) ---
    # 9-wide SPY put vert, ~$804 max loss, on a $3,440 account (10% cap = $344) -> busts cap.
    busts = build_ticket({"underlying": "SPY", "structure": "short_put_vertical",
                          "short_strike": 712, "long_strike": 703, "expiry": "2026-07-24",
                          "credit": 0.96, "max_loss": 804, "contracts": 1, "net_liq": 3440})
    if busts["fits_live_cap"] is not False or busts["live_cap"] != 344.0:
        f.append("fit: expected bust, got fits={} cap={}".format(busts["fits_live_cap"], busts["live_cap"]))
    if busts["suggested_width"] != 4:   # int(344/100 + 0.96) = int(4.4) = 4
        f.append("fit suggested_width: {}".format(busts["suggested_width"]))
    if "⚠" not in busts["text"] or "10% live cap" not in busts["text"]:
        f.append("fit warning missing from text: {}".format(busts["text"]))
    # a narrow spread that fits, same account -> no warning
    ok = build_ticket({"underlying": "SPY", "structure": "short_put_vertical",
                       "short_strike": 712, "long_strike": 709, "expiry": "2026-07-24",
                       "credit": 0.40, "max_loss": 260, "contracts": 1, "net_liq": 3440})
    if ok["fits_live_cap"] is not True or "⚠" in ok["text"]:
        f.append("fit: expected OK, got fits={} text={}".format(ok["fits_live_cap"], ok["text"]))
    # no account context -> no claim, no warning
    paper = build_ticket({"underlying": "SPY", "structure": "short_put_vertical",
                          "short_strike": 712, "long_strike": 703, "expiry": "2026-07-24",
                          "credit": 0.96, "max_loss": 804, "contracts": 1})
    if paper["fits_live_cap"] is not None or "⚠" in paper["text"]:
        f.append("fit: expected None w/o net_liq, got {}".format(paper["fits_live_cap"]))

    # --- struct_code ---
    if struct_code("short_put_vertical") != "VP" or struct_code("iron_condor") != "IC" or struct_code("short_call_vertical") != "VC":
        f.append("struct_code")

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("pv ✓ · cv ✓ · ic ✓ · copy-text ✓ · codes ✓")
    print("All trade_ticket tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
