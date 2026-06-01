"""Tests for the opportunity scanner's pure math + ranking.

Run without pytest:  python -m scripts.test_scan_opportunities
"""
import sys

from scripts.scan_opportunities import (
    norm_cdf, expected_move, put_pop, put_delta_abs,
    choose_strikes, expectancy, build_candidate, rank_opportunities,
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

    # build_candidate: well-formed credit spread (short ~0.80 POP) passes; junk fails
    good = build_candidate("SPY", "2026-07-17", 35, 92.0, 87.0,
                           short_mark=1.30, long_mark=0.45, price=100.0,
                           iv=0.30, iv_rank=0.55)
    if not good or good["credit"] != 0.85 or good["bpr"] != 415.0:
        f.append("build_candidate good: {}".format(good))
    elif not (good["ev_per_contract"] > 0 and 0.70 <= good["pop"] <= 0.90):
        f.append("build_candidate metrics off: {}".format(good))
    # credit too thin relative to width -> rejected
    thin = build_candidate("X", "2026-07-17", 35, 92.0, 87.0, 0.40, 0.30, 100.0, 0.30, 0.55)
    if thin is not None:
        f.append("thin credit should be rejected")

    # ranking: higher ev_on_bpr first
    cands = [
        {"ev_on_bpr": 0.05, "iv_rank": 0.4, "pop": 0.8, "underlying": "A"},
        {"ev_on_bpr": 0.12, "iv_rank": 0.6, "pop": 0.8, "underlying": "B"},
        {"ev_on_bpr": 0.09, "iv_rank": 0.9, "pop": 0.8, "underlying": "C"},
    ]
    order = [c["underlying"] for c in rank_opportunities(cands, top_n=3)]
    if order != ["B", "C", "A"]:
        f.append("rank order {}".format(order))

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
