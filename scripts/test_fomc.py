"""Tests for the FOMC trade-trigger logic (window/phase/dedup/message).

Run without pytest:  python -m scripts.test_fomc
"""
import sys
from dataclasses import dataclass
from datetime import datetime

from monitor import fomc


def et(y, mo, d, h, mi=0):
    # phase() reads only wall-clock fields (.date/.time/.weekday), so a naive
    # datetime standing in for ET local time is sufficient and keeps the test
    # dependency-free. DST handling lives in poll.py, which passes a real
    # ET-localized now into phase().
    return datetime(y, mo, d, h, mi)


@dataclass
class Sug:
    trade_id: str
    action: str


def main() -> int:
    f = []

    # ── phase() window + market-hours + DST-aware ──
    if fomc.phase(et(2026, 6, 16, 10, 0)) != "setup":
        f.append("Jun16 10:00 should be setup")
    if fomc.phase(et(2026, 6, 17, 10, 0)) != "setup":
        f.append("Jun17 10:00 (pre-2pm) should be setup")
    if fomc.phase(et(2026, 6, 17, 13, 59)) != "setup":
        f.append("Jun17 13:59 should still be setup")
    if fomc.phase(et(2026, 6, 17, 14, 0)) != "done":
        f.append("Jun17 14:00 should flip to done")
    if fomc.phase(et(2026, 6, 17, 15, 30)) != "done":
        f.append("Jun17 15:30 should be done")
    if fomc.phase(et(2026, 6, 16, 8, 0)) is not None:
        f.append("Jun16 08:00 pre-market must be None")
    if fomc.phase(et(2026, 6, 16, 16, 30)) is not None:
        f.append("Jun16 16:30 after close must be None")
    if fomc.phase(et(2026, 6, 15, 11, 0)) is not None:
        f.append("Jun15 (before window) must be None")
    if fomc.phase(et(2026, 6, 18, 11, 0)) is not None:
        f.append("Jun18 (after window) must be None")

    # ── action mapping ──
    if fomc.action_for("setup") != "FOMC_IC_SETUP" or fomc.action_for("done") != "FOMC_DONE":
        f.append("action_for mapping wrong")

    # ── dedup ──
    sugs = [Sug(fomc.TRADE_ID, "FOMC_IC_SETUP")]
    if not fomc.already_fired(sugs, "FOMC_IC_SETUP"):
        f.append("already_fired should be True for sent setup")
    if fomc.already_fired(sugs, "FOMC_DONE"):
        f.append("already_fired should be False for not-yet-sent done")
    if fomc.already_fired([Sug("other", "FOMC_IC_SETUP")], "FOMC_IC_SETUP"):
        f.append("already_fired must match TRADE_ID, not just action")

    # ── message: setup ──
    title, msg = fomc.build_message("setup")
    if title != "FOMC IC SETUP":
        f.append("setup title wrong: {}".format(title))
    for needle in ("harvest the FOMC IV crush", "IV Rank >= 40", "Jul-17 chain",
                   "10-12 delta", "max loss <= $300", "Close Jun 18"):
        if needle not in msg:
            f.append("setup msg missing: {}".format(needle))

    # ── message: done ──
    dt, dmsg = fomc.build_message("done")
    if dt != "FOMC DONE":
        f.append("done title wrong: {}".format(dt))
    if "stand down" not in dmsg:
        f.append("done msg missing stand-down line")

    # ── live enrichment renders price + IV rank (fraction -> %) ──
    _, m2 = fomc.build_message("setup", {"IWM": {"price": 211.34, "iv_rank": 0.45}})
    if "IWM $211.34" not in m2 or "IV Rank 45%" not in m2:
        f.append("live enrichment not rendered: {}".format(m2))
    _, m3 = fomc.build_message("done", {"IWM": {"price": 210.0}})
    if "IWM $210.00" not in m3:
        f.append("partial live (price only) not rendered")

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("phase/window/DST ✓ · dedup ✓ · setup+done messages ✓ · live enrichment ✓")
    print("All fomc tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
