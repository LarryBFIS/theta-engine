"""Tests for the profit-protection early-exit signal.

Run without pytest:  python -m scripts.test_profit_guard
"""
import sys

from monitor.profit_guard import profit_protection_signal as sig


def main() -> int:
    f = []

    # Below the capture floor -> never fire.
    fire, _ = sig(0.10, 40, 0.05, False)
    if fire:
        f.append("fired below MIN_CAPTURE")

    # At/over the 50% target -> mechanical rule handles it, don't fire.
    fire, _ = sig(0.55, 40, 0.05, False)
    if fire:
        f.append("fired at/above manage target")

    # Banked 30%, comfortable distance, lots of DTE, slow -> hold (no risk factor).
    fire, _ = sig(0.30, 40, 0.06, False, days_held=10)
    if fire:
        f.append("fired with no risk factor")

    # Banked 30% but only 20 DTE -> fire (gamma).
    fire, r = sig(0.30, 20, 0.06, False, days_held=10)
    if not fire or not any("expiry" in x for x in r):
        f.append("should fire on low DTE: {}".format(r))

    # Banked 30%, near the short strike -> fire.
    fire, r = sig(0.30, 40, 0.01, False, days_held=10)
    if not fire or not any("short strike" in x for x in r):
        f.append("should fire near strike: {}".format(r))

    # Banked 30%, breached short strike -> fire.
    fire, r = sig(0.30, 40, -0.02, True, days_held=10)
    if not fire or not any("breached" in x for x in r):
        f.append("should fire on breach: {}".format(r))

    # Fast capture: 35% in 3 days -> fire (front-loaded).
    fire, r = sig(0.35, 40, 0.06, False, days_held=3)
    if not fire or not any("front-loaded" in x for x in r):
        f.append("should fire on fast capture: {}".format(r))

    # Same capture but slow (35% over 10d) and no other risk -> hold.
    fire, r = sig(0.35, 40, 0.06, False, days_held=10)
    if fire:
        f.append("should not fire on slow capture w/ no risk: {}".format(r))

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("Profit-guard: floor/target gating ✓ · DTE/strike/breach/velocity triggers ✓")
    print("All profit_guard tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
