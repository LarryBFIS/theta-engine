"""Agentic review — an LLM portfolio-risk pass over the scanner's candidates.

This is the layer that makes the engine *reason* instead of only executing fixed
rules. After the deterministic scanner proposes candidates, an LLM (Claude) looks
at the whole picture — the candidates, the open book, the vol regime, the macro
calendar, and the engine's own learnings — and makes a judgment call on each:
approve, downsize, or veto, WITH written reasoning that is journaled for audit.

Authority is deliberately bounded (defense in depth):
  - the agent can ONLY make a trade more conservative — veto it, or cut its size.
    It can never increase size, add trades, or relax a hard cap. The deterministic
    safety rails (caps, max-loss, regime/news/blackout gates) remain underneath.
  - it never touches live vs paper tagging — that stays with the engine's gates.
  - everything it decides is appended to memory/agent_journal.jsonl.

Fail-safe: no ANTHROPIC_API_KEY, an API error, or an unparseable reply all result
in the candidates passing through UNCHANGED (the engine proceeds on its rules).
The agent can only ever help; it can never break the scan.

Pure helpers (cand_id / parse_decisions / apply_decisions) are unit-tested in
scripts/test_agent_review.py; only run()/_call_claude touch the network.
"""
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from scripts.paper_trades import cluster_of, asset_class

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = REPO_ROOT / "memory"
JOURNAL_FILE = MEMORY_DIR / "agent_journal.jsonl"

log = logging.getLogger("agent")

# Default to the cheapest capable model for a frequent job; override with AGENT_MODEL.
# Cost (per 1M tok): Haiku $1/$5 · Sonnet $3/$15 · Opus $5/$25. Haiku is plenty for
# a bounded approve/veto/resize judgment and keeps the bill to pennies/month.
DEFAULT_MODEL = os.getenv("AGENT_MODEL", "claude-haiku-4-5")
MAX_TOKENS = int(os.getenv("AGENT_MAX_TOKENS", "1800"))
# When to spend tokens on a review. "live_or_event" (default) only calls the LLM
# when a live trade is on the table OR a macro event is near — routine paper-only
# scans cost $0. "always" reviews whenever there are candidates; "off" disables.
REVIEW_MODE = os.getenv("AGENT_REVIEW_MODE", "live_or_event")


def should_review(candidates, ctx, mode=None):
    """Cost gate: decide whether this scan is worth an LLM call. In 'live_or_event'
    (default) we only spend tokens when a live trade is on the table or a macro
    event is within ~2 days — routine paper-only scans cost nothing."""
    mode = mode or REVIEW_MODE
    if mode == "off" or not candidates:
        return False
    if mode == "always":
        return True
    # live_or_event
    if any((c.get("tag") == "live") for c in candidates):
        return True
    for e in (ctx.get("events") or []):
        d = e.get("days_to_decision")
        if e.get("status") in ("enter", "closing") or (isinstance(d, (int, float)) and d <= 2):
            return True
    return False


def cand_id(c):
    """Stable id the model echoes back to map a decision to a candidate."""
    return "{}|{}|{:g}/{:g}".format(
        c.get("underlying"), c.get("structure"),
        c.get("short_strike") or 0, c.get("long_strike") or 0)


def _constitution(learnings):
    """The agent's standing mandate — durable principles, not per-trade parameters."""
    lines = [
        "You are the PORTFOLIO-RISK AGENT for an autonomous options premium-selling bot.",
        "Your job is judgment the fixed rules can't encode: catch the trade that is",
        "technically allowed but unwise. You are a risk manager, not a salesman.",
        "",
        "MANDATE / PRINCIPLES:",
        "- We harvest the volatility risk premium; we do NOT predict direction.",
        "- Survival first. A small account compounds only if it avoids ruin.",
        "- Diversify: correlated positions are ONE bet sized up, not many bets.",
        "- Respect events: do not add directional short-vol into a scheduled macro",
        "  event (FOMC/CPI/jobs) — that is uncompensated event risk.",
        "- Prefer index ETFs over single names (idiosyncratic gap risk).",
        "- Keep size small until edge is proven; never let one loss be catastrophic.",
        "- When in doubt, do less. Vetoing a marginal trade is a valid, good outcome.",
        "",
        "AUTHORITY (hard limits — you CANNOT exceed these):",
        "- You may ONLY make a trade more conservative: 'approve', 'downsize'",
        "  (fewer contracts), or 'veto'. You may NOT increase size, add trades,",
        "  change live/paper status, or override any cap. Those are enforced in code.",
    ]
    if learnings and learnings.get("global"):
        g = learnings["global"]
        lines += ["", "ENGINE LEARNINGS (realized, from our own book):",
                  "- {} closed trades, {:.0%} win rate, realized ${:+.0f}.".format(
                      g.get("closed", 0), g.get("win_rate", 0), g.get("total_pnl", 0))]
        for dim, bs in (learnings.get("buckets") or {}).items():
            for v, b in bs.items():
                if b.get("actionable"):
                    lines.append("- {} '{}': {}".format(dim, v, b.get("recommendation")))
    lines += ["",
              "OUTPUT: strict JSON only, no prose outside it:",
              '{"portfolio_note": "<=2 sentences on overall book risk",',
              ' "decisions": [{"id": "<echo the candidate id>",',
              '   "action": "approve|downsize|veto",',
              '   "contracts": <int, only if downsize>,',
              '   "reason": "<one concise sentence>"}]}',
              "Include every candidate id exactly once."]
    return "\n".join(lines)


def _book_summary(open_positions):
    """Compact view of the current open paper book for context."""
    if not open_positions:
        return {"open": 0}
    from collections import Counter
    names = Counter((p.get("underlying") or "").upper() for p in open_positions)
    clusters = Counter(cluster_of(p.get("underlying")) for p in open_positions)
    unreal = round(sum(float(p.get("unrealized_pnl") or 0) for p in open_positions), 2)
    return {"open": len(open_positions), "unrealized_pnl": unreal,
            "by_name": dict(names), "by_cluster": dict(clusters)}


def _user_message(candidates, ctx):
    """The situation the agent reasons over."""
    reg = ctx.get("regime") or {}
    payload = {
        "today": ctx.get("today"),
        "vix": reg.get("vix"), "regime": reg.get("level"), "regime_note": reg.get("note"),
        "macro_events": [{"event": e.get("event"), "decision_date": e.get("decision_date"),
                          "status": e.get("status")} for e in (ctx.get("events") or [])],
        "open_book": _book_summary(ctx.get("open_positions") or []),
        "caps": {"max_per_name": 1, "max_per_cluster": 3, "max_open": 8, "max_contracts": 3},
        "candidates": [{
            "id": cand_id(c), "underlying": c.get("underlying"),
            "asset_class": asset_class(c.get("underlying")), "cluster": cluster_of(c.get("underlying")),
            "structure": c.get("structure"), "dte": c.get("dte"),
            "short_strike": c.get("short_strike"), "long_strike": c.get("long_strike"),
            "credit": c.get("credit"), "pop": c.get("pop"), "iv_rank": c.get("iv_rank"),
            "ev_on_bpr": c.get("ev_on_bpr"), "contracts": c.get("contracts"),
            "max_loss_total": c.get("max_loss_total"), "tag": c.get("tag"),
        } for c in candidates],
    }
    return ("Review these candidate option trades and return your JSON decision for "
            "each. Be conservative — veto anything that adds correlated risk, fights "
            "an upcoming event, or is a marginal single-name.\n\n"
            + json.dumps(payload, indent=2, default=str))


def parse_decisions(text):
    """Defensively extract the decision JSON from the model reply."""
    if not text:
        return {"decisions": []}
    s, e = text.find("{"), text.rfind("}")
    if s < 0 or e < 0 or e <= s:
        return {"decisions": []}
    try:
        d = json.loads(text[s:e + 1])
    except json.JSONDecodeError:
        return {"decisions": []}
    if not isinstance(d.get("decisions"), list):
        d["decisions"] = []
    return d


def apply_decisions(candidates, parsed):
    """Apply the agent's decisions, ENFORCING conservative-only authority in code.
    Returns (kept_candidates, decision_log). Pure — no network."""
    by_id = {cand_id(c): c for c in candidates}
    kept = list(candidates)
    decision_log = []
    for d in parsed.get("decisions", []):
        c = by_id.get(d.get("id"))
        if not c:
            continue
        action = (d.get("action") or "approve").lower()
        reason = (d.get("reason") or "")[:240]
        if action == "veto":
            c["agent_action"], c["agent_reason"] = "veto", reason
            if c in kept:
                kept.remove(c)
            decision_log.append({"id": d["id"], "action": "veto", "reason": reason})
        elif action in ("downsize", "resize"):
            cur = int(c.get("contracts") or 1)
            try:
                req = int(d.get("contracts"))
            except (TypeError, ValueError):
                req = cur
            new = max(1, min(req, cur))     # HARD RULE: never above current size
            if new < cur:
                c["contracts"] = new
                c["max_loss_total"] = round((c.get("max_loss") or 0) * new, 2)
                c["bpr_total"] = round((c.get("bpr") or 0) * new, 2)
                c["agent_action"], c["agent_reason"] = "downsize", reason
                decision_log.append({"id": d["id"], "action": "downsize",
                                     "from": cur, "to": new, "reason": reason})
            else:
                c["agent_action"], c["agent_reason"] = "approve", reason
                decision_log.append({"id": d["id"], "action": "approve", "reason": reason})
        else:
            c["agent_action"], c["agent_reason"] = "approve", reason
            decision_log.append({"id": d["id"], "action": "approve", "reason": reason})
    return kept, decision_log


def _call_claude(system, user, model=None, max_tokens=MAX_TOKENS, timeout=45):
    """One Anthropic Messages call; returns the text. Raises on missing key/error."""
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"],
                                 timeout=timeout)
    resp = client.messages.create(
        model=model or DEFAULT_MODEL, max_tokens=max_tokens,
        system=system, messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")


def _journal(entry):
    try:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        with JOURNAL_FILE.open("a") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
    except OSError as e:
        log.warning("agent journal write failed: %s", e)


def run(candidates, ctx):
    """LLM portfolio review. Returns (kept_candidates, summary_or_None). Never
    raises for an operational reason — disabled/erroring -> candidates unchanged."""
    if not candidates:
        return candidates, None
    if not os.getenv("ANTHROPIC_API_KEY"):
        log.info("agent review disabled (no ANTHROPIC_API_KEY) — passing %d through", len(candidates))
        return candidates, None
    ctx = ctx or {}
    if not should_review(candidates, ctx):
        log.info("agent review skipped (mode=%s, no live/event trigger) — $0 this scan", REVIEW_MODE)
        return candidates, None
    system = _constitution(ctx.get("learnings"))
    user = _user_message(candidates, ctx)
    try:
        text = _call_claude(system, user)
    except Exception as e:  # noqa: BLE001 — never break the scan on the agent
        log.warning("agent review call failed (candidates pass unchanged): %s", e)
        return candidates, None
    parsed = parse_decisions(text)
    kept, decision_log = apply_decisions(candidates, parsed)
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": DEFAULT_MODEL,
        "portfolio_note": parsed.get("portfolio_note", ""),
        "reviewed": len(candidates), "vetoed": sum(1 for d in decision_log if d["action"] == "veto"),
        "downsized": sum(1 for d in decision_log if d["action"] == "downsize"),
        "decisions": decision_log,
    }
    _journal(summary)
    log.info("agent: reviewed %d · vetoed %d · downsized %d · note: %s",
             summary["reviewed"], summary["vetoed"], summary["downsized"],
             summary["portfolio_note"][:120])
    return kept, summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print(_constitution(None))
