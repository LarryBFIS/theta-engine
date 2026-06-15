"""Tests for the learning pass.

Run without pytest:  python -m scripts.test_learn
"""
import sys

from scripts.learn import (shrink_win_rate, bucket_stats, annotate_multiplier,
                           build_learnings, candidate_multiplier)


def _trade(asset_class, structure, cluster, pnl, contracts=1):
    return {"asset_class": asset_class, "structure": structure, "cluster": cluster,
            "contracts": contracts, "realized_pnl": pnl}


def main() -> int:
    f = []

    # --- shrinkage: small sample pulled toward prior; large sample ~= raw ---
    if not abs(shrink_win_rate(3, 3, 0.5, k=10) - (3 + 5) / 13) < 1e-9:
        f.append("shrink small: {}".format(shrink_win_rate(3, 3, 0.5, 10)))
    if not shrink_win_rate(80, 100, 0.5, k=10) > 0.74:   # 85/110 ≈ 0.77, near raw 0.80
        f.append("shrink large: {}".format(shrink_win_rate(80, 100, 0.5, 10)))

    # --- bucket_stats: counts, win rate, avgs ---
    trades = [_trade("index_etf", "short_put_vertical", "us_index", 100),
              _trade("index_etf", "short_put_vertical", "us_index", -50),
              _trade("single_name", "iron_condor", "us_tech", -200)]
    bs = bucket_stats(trades, lambda t: t["asset_class"])
    if bs["index_etf"]["n"] != 2 or bs["index_etf"]["wins"] != 1 or bs["index_etf"]["avg_pnl"] != 25.0:
        f.append("bucket index: {}".format(bs["index_etf"]))
    if bs["single_name"]["avg_pnl"] != -200.0 or bs["single_name"]["win_rate"] != 0.0:
        f.append("bucket single: {}".format(bs["single_name"]))

    # --- not actionable below min_sample -> multiplier stays 1.0 ---
    b = dict(bs["single_name"])
    m = annotate_multiplier(b, prior_wr=0.5, min_sample=20)
    if m != 1.0 or b["actionable"] is not False:
        f.append("thin bucket should be inert: {}".format(b))

    # --- end-to-end: a clearly losing single-name bucket becomes AVOID, index favored ---
    led = []
    # 24 index put verticals: 18 wins (+120) / 6 losses (-150)  -> strong
    for i in range(18):
        led.append(_trade("index_etf", "short_put_vertical", "us_index", 120))
    for i in range(6):
        led.append(_trade("index_etf", "short_put_vertical", "us_index", -150))
    # 24 single-name trades: 6 wins (+100) / 18 losses (-300)   -> weak
    for i in range(6):
        led.append(_trade("single_name", "short_put_vertical", "us_tech", 100))
    for i in range(18):
        led.append(_trade("single_name", "short_put_vertical", "us_tech", -300))
    L = build_learnings(led, min_sample=20)
    idx = L["buckets"]["asset_class"]["index_etf"]
    sgl = L["buckets"]["asset_class"]["single_name"]
    if not (idx["actionable"] and idx["multiplier"] > 1.0):
        f.append("index should be favored: {}".format(idx))
    if not (sgl["actionable"] and sgl["multiplier"] < 1.0 and "AVOID" in sgl["recommendation"]):
        f.append("single_name should be AVOID: {}".format(sgl))

    # --- candidate_multiplier: index pick boosted, tech single-name penalized ---
    mi, ni = candidate_multiplier(L, underlying="SPY", structure="short_put_vertical")
    ms, ns = candidate_multiplier(L, underlying="AAPL", structure="short_put_vertical")
    if not (mi > 1.0 and ms < 1.0):
        f.append("candidate mult: index {} ({}) vs single {} ({})".format(mi, ni, ms, ns))

    # --- no learnings / empty -> neutral 1.0 ---
    if candidate_multiplier(None, underlying="SPY")[0] != 1.0:
        f.append("None learnings should be neutral")

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("shrinkage ✓ · buckets ✓ · min-sample gate ✓ · favor/AVOID ✓ · candidate mult ✓")
    print("All learn tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
