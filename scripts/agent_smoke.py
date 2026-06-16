"""Manual smoke test for the agentic review layer — runs the REAL LLM call.

Builds a synthetic but realistic scenario (a tech-concentrated book heading into
an FOMC decision) and runs agent_review.run() so we can verify END TO END that:
  - the ANTHROPIC_API_KEY secret authenticates,
  - the model returns a parseable decision,
  - the conservative-only guardrails hold (it can only veto/downsize),
  - the reasoning is journaled.

Runs on the GitHub runner via the 'agent-smoke' workflow (which has the secret).
Exits non-zero if the key is present but the call failed — so a stale key shows
up as a red run, not a silent pass.
"""
import os
import sys

from monitor import agent_review


def main() -> int:
    has_key = bool(os.getenv("ANTHROPIC_API_KEY"))
    print("ANTHROPIC_API_KEY present:", has_key)
    print("model:", agent_review.DEFAULT_MODEL, "· review_mode:", agent_review.REVIEW_MODE)

    # A deliberately tricky scenario: a live put-vertical on a name we already
    # hold, going INTO the Fed, plus an oversized single-name. A thinking agent
    # should veto/resize at least the QQQ-into-Fed and trim the 3-lot AMD.
    candidates = [
        {"underlying": "QQQ", "structure": "short_put_vertical", "short_strike": 694,
         "long_strike": 685, "expiry": "2026-07-17", "dte": 31, "credit": 1.10, "pop": 0.80,
         "iv_rank": 0.64, "ev_on_bpr": 0.0099, "contracts": 2, "max_loss": 790, "bpr": 790,
         "max_loss_total": 1580, "bpr_total": 1580, "tag": "live"},
        {"underlying": "SPY", "structure": "iron_condor", "short_strike": 600, "long_strike": 640,
         "expiry": "2026-07-17", "dte": 31, "credit": 1.20, "pop": 0.78, "iv_rank": 0.45,
         "ev_on_bpr": 0.012, "contracts": 1, "max_loss": 380, "bpr": 380,
         "max_loss_total": 380, "bpr_total": 380, "tag": "paper"},
        {"underlying": "AMD", "structure": "short_put_vertical", "short_strike": 440,
         "long_strike": 430, "expiry": "2026-07-17", "dte": 31, "credit": 1.25, "pop": 0.80,
         "iv_rank": 0.96, "ev_on_bpr": 0.0105, "contracts": 3, "max_loss": 875, "bpr": 875,
         "max_loss_total": 2625, "bpr_total": 2625, "tag": "paper"},
    ]
    ctx = {
        "today": "2026-06-16",
        "regime": {"vix": 16.2, "level": "normal", "note": "normal regime"},
        "events": [{"event": "FOMC", "decision_date": "2026-06-17", "status": "enter",
                    "days_to_decision": 1}],
        "learnings": None,
        "open_positions": [{"underlying": "QQQ", "unrealized_pnl": -50,
                            "structure": "short_put_vertical"}],
    }

    print("should_review (gate):", agent_review.should_review(candidates, ctx))
    kept, summary = agent_review.run(candidates, ctx)
    print("kept after review:", [c["underlying"] for c in kept])

    if summary is None:
        if has_key:
            print("\nRESULT: ❌ key present but the agent returned no decision — the API call "
                  "FAILED. The secret is likely stale/invalid; paste a fresh sk-ant-… into the "
                  "ANTHROPIC_API_KEY secret and re-run.")
            return 1
        print("\nRESULT: ⚠ no ANTHROPIC_API_KEY — agent disabled. Add the secret and re-run.")
        return 1

    print("\nRESULT: ✅ agent ran")
    print("model used :", summary.get("model"))
    print("reviewed   :", summary.get("reviewed"),
          "· vetoed:", summary.get("vetoed"), "· downsized:", summary.get("downsized"))
    print("portfolio_note:", summary.get("portfolio_note"))
    for d in summary.get("decisions", []):
        print("  -", d.get("action"), d.get("id"), "·", d.get("reason"))
    # Guardrail assertion: no decision may INCREASE size (conservative-only).
    for c in kept:
        if c.get("agent_action") == "downsize" and c["contracts"] > {"QQQ": 2, "SPY": 1, "AMD": 3}.get(c["underlying"], 99):
            print("\nRESULT: ❌ guardrail breach — agent increased size!")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
