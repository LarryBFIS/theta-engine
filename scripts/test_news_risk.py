"""Tests for the news risk-gate (deterministic backbone).

Run without pytest:  python -m scripts.test_news_risk
"""
import sys
from datetime import datetime, timezone

from monitor.news_risk import severity, assess, escalate


def main() -> int:
    f = []
    now = datetime.now(timezone.utc).timestamp()

    # severity tiers
    if severity("Company files for bankruptcy")[0] != 3:
        f.append("bankruptcy should be tier3")
    if severity("Analyst downgrades AMZN")[0] != 2:
        f.append("downgrade should be tier2")
    if severity("Q2 earnings preview")[0] != 1:
        f.append("earnings should be tier1")
    if severity("New product color announced")[0] != 0:
        f.append("benign should be tier0")

    # assess: a tier-3 headline -> veto
    v = assess("XYZ", [{"title": "SEC investigation into XYZ accounting", "ts": now}])
    if v["level"] != "veto" or not v["hits"]:
        f.append("tier3 -> veto: {}".format(v))

    # tier-2 -> caution
    v = assess("XYZ", [{"title": "XYZ cut to sell by analyst", "ts": now}])
    if v["level"] != "caution":
        f.append("tier2 -> caution: {}".format(v))

    # only benign -> clear
    v = assess("XYZ", [{"title": "XYZ unveils new ad campaign", "ts": now}])
    if v["level"] != "clear":
        f.append("benign -> clear: {}".format(v))

    # stale severe headline (old) is ignored
    old = now - 30 * 86400
    v = assess("XYZ", [{"title": "XYZ bankruptcy filing", "ts": old}], max_age_days=4)
    if v["level"] != "clear":
        f.append("stale severe should be ignored: {}".format(v))

    # ts unknown (0) treated as recent -> counts
    v = assess("XYZ", [{"title": "XYZ halted on news", "ts": 0}])
    if v["level"] != "veto":
        f.append("ts=0 should count as recent: {}".format(v))

    # escalate: risk only goes up
    if escalate("clear", "veto") != "veto" or escalate("veto", "clear") != "veto":
        f.append("escalate veto")
    if escalate("caution", "clear") != "caution":
        f.append("escalate caution>clear")

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("severity tiers ✓ · veto/caution/clear ✓ · recency filter ✓ · escalation ✓")
    print("All news_risk tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
