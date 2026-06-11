"""Tests for the macro event calendar (real FOMC Jun-17 2026 + crush trigger).

Run without pytest:  python -m scripts.test_macro_calendar
"""
import sys

from monitor import macro_calendar as mc


def main() -> int:
    f = []

    fomc = next((e for e in mc.EVENTS if e["type"] == "FOMC"), None)
    if not fomc or fomc["decision_date"] != "2026-06-17" or fomc["decision_time_et"] != "14:00":
        f.append("FOMC event missing/incorrect: {}".format(fomc))

    if not any(e["type"] == "FOMC" for e in mc.upcoming_events("2026-06-10", within_days=10)):
        f.append("FOMC should be upcoming within 10d of Jun 10")
    if mc.upcoming_events("2026-06-10", within_days=5):
        f.append("FOMC (7d out) should NOT be within 5d window")
    if (mc.next_event("2026-06-10") or {}).get("decision_date") != "2026-06-17":
        f.append("next_event wrong")
    if mc.in_blackout("2026-06-10", days_before=2):
        f.append("Jun 10 (7d out) should NOT be in 2-day blackout")
    if not mc.in_blackout("2026-06-16", days_before=2):
        f.append("Jun 16 (1d before decision) SHOULD be in blackout")
    if not mc.in_blackout("2026-06-17", days_before=2):
        f.append("Jun 17 (decision day) SHOULD be in blackout")

    q = mc.event_crush_opportunity("2026-06-10", vix=22, iv_ranks={"IWM": 0.55})
    if not q or q["status"] != "queued" or q["tag"] != "paper":
        f.append("Jun 10 should be queued/paper (too early): {}".format(q and (q['status'], q['tag'])))
    if q and (q["structure"] != "iron_condor" or q["underlyings"] != ["IWM", "QQQ"]
              or q["expiry"] != "2026-07-17" or q["max_loss_cap"] != 300):
        f.append("crush opp params wrong: {}".format(q))

    e_live = mc.event_crush_opportunity("2026-06-16", vix=22, iv_ranks={"IWM": 0.55, "QQQ": 0.30})
    if not e_live or e_live["status"] != "enter" or e_live["tag"] != "live" or not e_live["live_ok"]:
        f.append("Jun 16 vix22/ivr55 should be enter+LIVE: {}".format(e_live and (e_live['status'], e_live['tag'])))

    e_lowvix = mc.event_crush_opportunity("2026-06-16", vix=15, iv_ranks={"IWM": 0.55})
    if not e_lowvix or e_lowvix["tag"] != "paper" or e_lowvix["live_ok"]:
        f.append("Jun 16 vix15 should stay paper (VIX<18)")

    e_lowivr = mc.event_crush_opportunity("2026-06-16", vix=22, iv_ranks={"IWM": 0.30, "QQQ": 0.20})
    if not e_lowivr or e_lowivr["tag"] != "paper" or e_lowivr["live_ok"]:
        f.append("Jun 16 ivr30 should stay paper (IVR<40%)")

    if mc.event_crush_opportunity("2026-06-19") is not None:
        f.append("Jun 19 (past close) should be None")
    cl = mc.event_crush_opportunity("2026-06-18", vix=22, iv_ranks={"IWM": 0.55})
    if not cl or cl["status"] != "closing" or (cl["tag"] != "paper" and cl["live_ok"]):
        f.append("Jun 18 should be 'closing' (not live): {}".format(cl and cl['status']))

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("FOMC calendar ✓ · upcoming/blackout ✓ · crush lifecycle (queued→enter→closing) ✓ · LIVE conditions ✓")
    print("All macro_calendar tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
