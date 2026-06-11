"""Tests for the opportunity scanner's pure math + ranking.

Run without pytest:  python -m scripts.test_scan_opportunities
"""
import sys

from scripts.scan_opportunities import (
    norm_cdf, expected_move, put_pop, put_delta_abs,
    choose_strikes, expectancy, build_candidate, rank_opportunities,
    long_vol_candidate, rank_long_vol,
    call_pop, ic_range_pop, max_loss_vertical, max_loss_ic, expectancy_capped,
    size_for_caps, trend_from_mas, choose_structure, book_directional_bias,
    build_call_vertical, build_iron_condor,
)


def approx(a, b, tol=1e-3):
    return a is not None and abs(a - b) <= tol


def main() -> int:
    f = []

    # norm_cdf known values
    if not approx(norm_cdf(0), 0.5):
        f.append("norm_cdf(0)")
    if not approx(norm_cdf(1.645), 0.95, 1e-3):
        f.append("norm_cdf(1.645)~0.95 got {}".format(norm_cdf(1.645)))

    # expected move: 100 @ 20% IV over 1yr = ~20
    if not approx(expected_move(100, 0.20, 365), 20.0, 1e-6):
        f.append("expected_move 1yr")

    # put_pop: ATM ~0.5 (slightly under due to drift term); deep OTM short -> high POP
    p_atm = put_pop(100, 100, 0.3, 30)
    if not (0.45 < p_atm < 0.55):
        f.append("ATM pop {}".format(p_atm))
    p_far = put_pop(100, 80, 0.3, 30)   # short put well below spot
    p_near = put_pop(100, 97, 0.3, 30)
    if not (p_far > p_near > 0.5):
        f.append("pop monotonic {} {}".format(p_far, p_near))
    if put_pop(100, 100, 0, 30) is not None:
        f.append("pop guards zero iv")

    # delta sanity: short put further OTM has smaller |delta|
    if not (put_delta_abs(100, 97, 0.3, 30) > put_delta_abs(100, 80, 0.3, 30)):
        f.append("delta monotonic")

    # choose_strikes: target POP ~0.8 picks a strike below spot with width ~5
    strikes = [80, 85, 90, 92, 94, 95, 96, 97, 98, 99, 100, 101, 102]
    sel = choose_strikes(strikes, 100, 0.30, 35, target_pop=0.80, width=5)
    if not sel:
        f.append("choose_strikes none")
    else:
        short, long_ = sel
        # short ~0.80 POP (=92 on this ladder); long = nearest strike to short-5 (=85)
        if not (short == 92 and long_ == 85):
            f.append("choose_strikes picked {}/{}".format(short, long_))
        if not approx(put_pop(100, short, 0.30, 35), 0.80, 0.06):
            f.append("short POP off target: {}".format(put_pop(100, short, 0.30, 35)))

    # expectancy: positive when POP high, negative when POP low
    if not (expectancy(1.0, 400, 0.80) > 0):
        f.append("expectancy +")
    if not (expectancy(1.0, 400, 0.40) < 0):
        f.append("expectancy -")

    # build_candidate: EXECUTABLE credit = short_bid - long_ask (not mid).
    # short {bid1.50,ask1.60,mid1.55}, long {bid0.46,ask0.50,mid0.48}: exec credit
    # 1.00 → credit/width 0.20 clears the P4 floor; both legs tight (rel ≤0.20).
    good = build_candidate("SPY", "2026-07-17", 35, 92.0, 87.0,
                           {"bid": 1.50, "ask": 1.60, "mark": 1.55},
                           {"bid": 0.46, "ask": 0.50, "mark": 0.48},
                           price=100.0, iv=0.30, iv_rank=0.55)
    if not good:
        f.append("build_candidate good returned None")
    else:
        if good["credit"] != 1.00:   # 1.50 - 0.50 executable, NOT the 1.07 mid
            f.append("exec credit wrong: {} (mid was {})".format(good["credit"], good.get("mid_credit")))
        if good["mid_credit"] != 1.07:   # 1.55 - 0.48
            f.append("mid_credit wrong: {}".format(good["mid_credit"]))
        if good["bpr"] != 400.0:     # (5 - 1.00)*100
            f.append("bpr wrong: {}".format(good["bpr"]))
        if not (good["ev_per_contract"] > 0 and 0.70 <= good["pop"] <= 0.90):
            f.append("metrics off: {}".format(good))
    # thin executable credit -> rejected (bid 0.40 - ask 0.35 = 0.05)
    thin = build_candidate("X", "2026-07-17", 35, 92.0, 87.0,
                           {"bid": 0.40, "ask": 0.45, "mark": 0.42},
                           {"bid": 0.30, "ask": 0.35, "mark": 0.32}, 100.0, 0.30, 0.55)
    if thin is not None:
        f.append("thin exec credit should be rejected")
    # liquidity gate: wide bid/ask on short leg -> rejected
    wide = build_candidate("X", "2026-07-17", 35, 92.0, 87.0,
                           {"bid": 1.00, "ask": 2.00, "mark": 1.50},   # rel spread 0.67
                           {"bid": 0.40, "ask": 0.50, "mark": 0.45}, 100.0, 0.30, 0.55)
    if wide is not None:
        f.append("wide bid/ask should be rejected (liquidity)")
    # missing quote -> rejected
    if build_candidate("X", "2026-07-17", 35, 92.0, 87.0, None,
                       {"bid": 0.4, "ask": 0.5, "mark": 0.45}, 100.0, 0.30, 0.55) is not None:
        f.append("missing quote should be rejected")

    # width-by-price scaling (no cap)
    from scripts.scan_opportunities import target_width
    if target_width(865) != 10 or target_width(100) != 5:
        f.append("target_width: {} / {}".format(target_width(865), target_width(100)))
    # adaptive width: narrow to fit a max-loss cap. $344 cap, ratio 0.20 ->
    # affordable = 344/(100*0.8) = 4.3 -> 4-wide (vs the 5-wide base).
    if target_width(100, max_loss_cap=344) != 4:
        f.append("adaptive width @344 cap: {}".format(target_width(100, max_loss_cap=344)))
    # tiny cap forces down to the hard floor (1)
    if target_width(50, max_loss_cap=100) != 1:
        f.append("adaptive width @100 cap floor: {}".format(target_width(50, max_loss_cap=100)))

    # eased long-leg gate: long-leg rel 0.22 (>0.20, <0.40) now PASSES the build
    long022 = build_candidate("SPY", "2026-07-17", 35, 92.0, 87.0,
                              {"bid": 1.50, "ask": 1.60, "mark": 1.55},
                              {"bid": 0.40, "ask": 0.50, "mark": 0.45},  # rel 0.222
                              price=100.0, iv=0.30, iv_rank=0.55)
    if long022 is None:
        f.append("eased long-leg gate: long rel 0.22 should now build")

    # ranking: higher ev_on_bpr first
    cands = [
        {"ev_on_bpr": 0.05, "iv_rank": 0.4, "pop": 0.8, "underlying": "A"},
        {"ev_on_bpr": 0.12, "iv_rank": 0.6, "pop": 0.8, "underlying": "B"},
        {"ev_on_bpr": 0.09, "iv_rank": 0.9, "pop": 0.8, "underlying": "C"},
    ]
    order = [c["underlying"] for c in rank_opportunities(cands, top_n=3)]
    if order != ["B", "C", "A"]:
        f.append("rank order {}".format(order))

    # VIX regime overlay
    from scripts.scan_opportunities import market_regime, _apply_regime, _write
    if market_regime(12, 0.0)["level"] != "calm" or market_regime(12, 0.0)["stand_down"]:
        f.append("calm VIX")
    if market_regime(24, 0.02)["level"] != "elevated" or market_regime(24, 0.02)["stand_down"]:
        f.append("elevated-stable should NOT stand down (rich premium)")
    if not market_regime(34, 0.0)["stand_down"]:
        f.append("VIX>=stress should stand down")
    if not market_regime(23, 0.25)["stand_down"]:
        f.append("VIX spike (+25% day) should stand down")
    if market_regime(None, None)["stand_down"]:
        f.append("unknown VIX must not stand down")
    # stand-down demotes LIVE -> PAPER
    picks = [{"tag": "live", "underlying": "X"}, {"tag": "paper", "underlying": "Y"}]
    _apply_regime(picks, market_regime(34, 0.0))
    if picks[0]["tag"] != "paper" or picks[0].get("demoted") != "vol stress":
        f.append("stand-down should demote LIVE->PAPER: {}".format(picks))

    # ── long-vol mode (mirror of premium-sell) ──
    today = "2026-06-10"
    # cheap IV (20%) + earnings in 5 days -> candidate, paper-tagged, strangle
    lv = long_vol_candidate("ABC", 0.20, "2026-06-15", 100.0, today, iv=0.40)
    if not lv:
        f.append("long_vol: cheap IV + near catalyst should flag")
    else:
        if lv["tag"] != "paper" or lv["structure"] != "long_strangle":
            f.append("long_vol tag/structure wrong: {}".format(lv))
        if lv["days_to_catalyst"] != 5 or lv["expected_move_pct"] is None:
            f.append("long_vol fields wrong: {}".format(lv))
    # rich IV (60%) -> not a long-vol setup (vol not cheap)
    if long_vol_candidate("ABC", 0.60, "2026-06-15", 100.0, today, iv=0.40) is not None:
        f.append("long_vol: rich IV must be rejected")
    # catalyst too far (30 days) -> rejected
    if long_vol_candidate("ABC", 0.20, "2026-07-10", 100.0, today, iv=0.40) is not None:
        f.append("long_vol: far catalyst must be rejected")
    # no earnings -> rejected
    if long_vol_candidate("ABC", 0.20, None, 100.0, today, iv=0.40) is not None:
        f.append("long_vol: no catalyst must be rejected")
    # earnings already passed -> rejected
    if long_vol_candidate("ABC", 0.20, "2026-06-05", 100.0, today, iv=0.40) is not None:
        f.append("long_vol: past catalyst must be rejected")
    # ranking: cheaper vol first
    lvs = [long_vol_candidate("HI", 0.28, "2026-06-14", 50, today, iv=0.5),
           long_vol_candidate("LO", 0.10, "2026-06-14", 50, today, iv=0.5)]
    order = [c["underlying"] for c in rank_long_vol(lvs)]
    if order != ["LO", "HI"]:
        f.append("long_vol rank order: {}".format(order))

    # ── P2: call POP mirrors put POP; IC range POP ──
    # short call ABOVE spot wins if price stays below -> high POP far OTM
    if not (call_pop(100, 120, 0.3, 30) > call_pop(100, 103, 0.3, 30) > 0.5):
        f.append("call_pop monotonic")
    # put + call POP at same distance ~ symmetric-ish; IC range pop = pp+cp-1
    pp, cp = put_pop(100, 92, 0.3, 35), call_pop(100, 108, 0.3, 35)
    if not approx(ic_range_pop(100, 92, 108, 0.3, 35), max(0.0, pp + cp - 1.0), 1e-6):
        f.append("ic_range_pop != pp+cp-1")
    if not (0.55 < ic_range_pop(100, 92, 108, 0.3, 35) < 0.85):
        f.append("ic range pop band: {}".format(ic_range_pop(100, 92, 108, 0.3, 35)))

    # ── P2: max-loss + capped expectancy ──
    if max_loss_vertical(5, 0.75) != 425.0:
        f.append("max_loss_vertical")
    if max_loss_ic(5, 1.60) != 340.0:                 # (5 - 1.60)*100
        f.append("max_loss_ic")
    # loss capped at structural max: 1.5×0.75×100=112.5 < 425 -> uses 112.5
    ev1 = expectancy_capped(0.75, 0.80, 425.0)
    if not approx(ev1, 0.80 * 37.5 - 0.20 * 112.5, 1e-6):
        f.append("expectancy_capped uncapped-by-maxloss: {}".format(ev1))
    # narrow IC where 1.5×credit > max loss -> loss capped at max loss
    ev2 = expectancy_capped(1.60, 0.75, 340.0)        # 1.5×160=240 < 340 -> 240
    if not approx(ev2, 0.75 * 80.0 - 0.25 * 240.0, 1e-6):
        f.append("expectancy_capped (cap path): {}".format(ev2))

    # ── P1: sizing against caps (hard rejects) ──
    # net liq 3438, 10% cap = $343.8, BPR ceiling 50% = $1719, used 0
    # vertical max loss $425 > $343.8 -> SKIP (return 0)
    if size_for_caps(425.0, 425.0, 3438.16, 0.0) != 0:
        f.append("size: 425 max-loss should breach 10% cap -> 0")
    # small trade: max loss $200, bpr $200 -> fits; sized by min(343//200, 1719//200)=1
    if size_for_caps(200.0, 200.0, 3438.16, 0.0) != 1:
        f.append("size: small trade should allow 1")
    # tiny trade $50/$50 -> loss cap allows 6 (343//50), bpr allows many -> 6
    if size_for_caps(50.0, 50.0, 3438.16, 0.0) != 6:
        f.append("size: $50 risk should allow 6: {}".format(size_for_caps(50.0, 50.0, 3438.16, 0.0)))
    # BPR already near ceiling: used 1700 of 1719 -> only $19 room, bpr 200 -> 0
    if size_for_caps(100.0, 200.0, 3438.16, 1700.0) != 0:
        f.append("size: BPR ceiling breach -> 0")
    # unknown net liq -> 1 (caps unenforced, stays paper downstream)
    if size_for_caps(425.0, 425.0, None, 0.0) != 1:
        f.append("size: unknown net liq -> 1")

    # ── P2: trend + structure selection ──
    if trend_from_mas(110, 105, 100) != "bullish": f.append("trend bullish")
    if trend_from_mas(90, 95, 100) != "bearish":   f.append("trend bearish")
    if trend_from_mas(100, 100, 100) != "mixed":   f.append("trend mixed")
    if choose_structure("bullish", 0.0) != "short_put_vertical": f.append("struct bull->put")
    if choose_structure("bearish", 0.0) != "short_call_vertical": f.append("struct bear->call")
    if choose_structure("mixed", 0.0) != "iron_condor": f.append("struct mixed->IC")
    # book already long-delta (+3) + bullish would add more long delta -> neutralize to IC
    if choose_structure("bullish", 3.0) != "iron_condor": f.append("struct book-balance->IC")
    # book delta proxy: 2 open put-verts (+) and 1 call-vert (-) => +1
    bias = book_directional_bias([
        {"status": "open", "structure": "short_put_vertical", "contracts": 1},
        {"status": "open", "structure": "short_put_vertical", "contracts": 1},
        {"status": "open", "structure": "short_call_vertical", "contracts": 1},
        {"status": "closed", "structure": "short_put_vertical", "contracts": 9},
    ])
    if bias != 1.0:
        f.append("book_directional_bias: {}".format(bias))

    # ── P2: build a short CALL vertical + an IRON CONDOR end-to-end ──
    cv = build_call_vertical("SPY", "2026-07-17", 35, 108.0, 113.0,
                             {"bid": 1.50, "ask": 1.60, "mark": 1.55},
                             {"bid": 0.46, "ask": 0.50, "mark": 0.48},
                             price=100.0, iv=0.30, iv_rank=0.55)
    if not cv or cv["structure"] != "short_call_vertical":
        f.append("call vertical build failed: {}".format(cv))
    elif not (cv["credit"] == 1.00 and cv["bpr"] == 400.0 and 0.70 <= cv["pop"] <= 0.90):
        f.append("call vertical metrics: {}".format(cv))
    # IC with ~12Δ shorts (88/112) -> range POP 0.805 (EV>0 needs >~0.75); 5-wide
    ic = build_iron_condor("SPY", "2026-07-17", 35, 88.0, 83.0, 112.0, 117.0,
                           {"bid": 0.70, "ask": 0.78, "mark": 0.74},   # put short
                           {"bid": 0.12, "ask": 0.18, "mark": 0.15},   # put long
                           {"bid": 0.70, "ask": 0.78, "mark": 0.74},   # call short
                           {"bid": 0.12, "ask": 0.18, "mark": 0.15},   # call long
                           price=100.0, iv=0.30, iv_rank=0.55)
    if not ic or ic["structure"] != "iron_condor":
        f.append("iron condor build failed: {}".format(ic))
    else:
        # total = (0.70-0.18)×2 = 1.04; maxloss=(5-1.04)*100=396; range POP ~0.805
        if not approx(ic["credit"], 1.04, 1e-9):
            f.append("IC total credit: {}".format(ic["credit"]))
        if ic["max_loss"] != 396.0:
            f.append("IC max loss: {}".format(ic["max_loss"]))
        if not (0.75 <= ic["pop"] <= 0.85):
            f.append("IC range pop band: {}".format(ic["pop"]))

    # _write smoke test (catches NameErrors like the WIDTH bug)
    import tempfile, json as _json
    from pathlib import Path
    import scripts.scan_opportunities as S
    S.SCAN_DIR = Path(tempfile.mkdtemp())
    try:
        S._write([good], [good], {"KO": "iv_rank 12%"}, market_regime(18, 0.01))
        op = _json.loads((S.SCAN_DIR / "opportunities.json").read_text())
        if "regime" not in op or "width_pct" not in op["params"]:
            f.append("_write payload missing regime/width_pct")
    except Exception as e:  # noqa: BLE001
        f.append("_write raised: {}".format(e))

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("choose_strikes ->", sel, "short POP ~", round(put_pop(100, sel[0], 0.30, 35), 2))
    print("sample candidate ->", {k: good[k] for k in ("underlying", "credit", "bpr", "pop", "ev_per_contract", "ev_on_bpr")})
    print("All scan_opportunities tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
