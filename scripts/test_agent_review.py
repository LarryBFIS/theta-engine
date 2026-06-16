"""Tests for the agentic review layer (pure helpers — no network).

Run without pytest:  python -m scripts.test_agent_review
"""
import sys

from monitor.agent_review import cand_id, parse_decisions, apply_decisions


def _c(u, struct, s, l, ctr, max_loss=200.0, bpr=200.0):
    return {"underlying": u, "structure": struct, "short_strike": s, "long_strike": l,
            "contracts": ctr, "max_loss": max_loss, "bpr": bpr,
            "max_loss_total": max_loss * ctr, "bpr_total": bpr * ctr}


def main() -> int:
    f = []

    # --- parse_decisions: extracts JSON even with surrounding prose ---
    txt = 'Here is my review.\n{"portfolio_note":"ok","decisions":[{"id":"X","action":"veto","reason":"r"}]} thanks'
    p = parse_decisions(txt)
    if p.get("portfolio_note") != "ok" or len(p["decisions"]) != 1:
        f.append("parse ok: {}".format(p))
    # garbage -> empty, never throws
    if parse_decisions("no json here").get("decisions") != []:
        f.append("parse garbage")
    if parse_decisions("").get("decisions") != []:
        f.append("parse empty")

    # --- veto removes the candidate ---
    cands = [_c("QQQ", "short_put_vertical", 694, 685, 2),
             _c("SPY", "short_put_vertical", 600, 595, 1)]
    qid, sid = cand_id(cands[0]), cand_id(cands[1])
    kept, log = apply_decisions(cands, {"decisions": [
        {"id": qid, "action": "veto", "reason": "tech cluster + Fed"}]})
    if len(kept) != 1 or kept[0]["underlying"] != "SPY":
        f.append("veto keep: {}".format([c["underlying"] for c in kept]))
    if cands[0].get("agent_action") != "veto":
        f.append("veto tag missing")

    # --- downsize reduces size + recomputes totals ---
    cands = [_c("QQQ", "short_put_vertical", 694, 685, 3, max_loss=790, bpr=790)]
    kept, log = apply_decisions(cands, {"decisions": [
        {"id": cand_id(cands[0]), "action": "downsize", "contracts": 1, "reason": "too big"}]})
    c = kept[0]
    if not (c["contracts"] == 1 and c["max_loss_total"] == 790 and c["bpr_total"] == 790):
        f.append("downsize totals: {}".format(c))

    # --- HARD RULE: agent cannot INCREASE size (conservative-only) ---
    cands = [_c("SPY", "short_put_vertical", 600, 595, 1, max_loss=400, bpr=400)]
    apply_decisions(cands, {"decisions": [
        {"id": cand_id(cands[0]), "action": "downsize", "contracts": 9, "reason": "bigger"}]})
    if cands[0]["contracts"] != 1:
        f.append("agent must NOT increase size: {}".format(cands[0]["contracts"]))

    # --- unknown id ignored; approve keeps everything ---
    cands = [_c("IWM", "short_put_vertical", 200, 195, 2)]
    kept, log = apply_decisions(cands, {"decisions": [
        {"id": "does-not-exist", "action": "veto", "reason": "x"},
        {"id": cand_id(cands[0]), "action": "approve", "reason": "fine"}]})
    if len(kept) != 1 or kept[0].get("agent_action") != "approve":
        f.append("approve/unknown: {} {}".format(len(kept), kept[0].get("agent_action")))

    if f:
        print("FAILED:")
        for x in f:
            print("  - " + x)
        return 1
    print("parse ✓ · veto ✓ · downsize ✓ · no-size-increase ✓ · approve/unknown ✓")
    print("All agent_review tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
