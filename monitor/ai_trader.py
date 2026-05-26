"""
AI Trader — Phase 5 decision engine.

Takes current positions + market state + news + recent history,
calls Claude Sonnet 4.6, returns structured trading decisions.

This is the brain. Every 15-min poll feeds it context, it decides
if the user needs to act.
"""
import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

import anthropic


SYSTEM_PROMPT = """You are an active short-premium options trader managing a small account (~$3,500 net liq) on tastytrade for Jay Vekaria.

ACCOUNT RULES (firm):
- Defined-risk preferred (verticals, iron condors) but naked allowed under new playbook
- Manage at 50% of max profit mechanically
- 21 DTE hard exit — close or roll, no exceptions
- Cut losers at 1.5x credit unrealized loss
- POP minimum 68% on entry
- Up to 80% BPR utilization
- Max 3-4 concurrent positions
- Uncorrelated underlyings for diversification (SPY+QQQ+IWM all correlate 0.85-0.95, NOT diversified)

YOUR ROLE:
Review current positions + market state + news every 15 minutes during market hours.
Decide if Jay needs to ACT NOW or HOLD.

You are NOT a passive analyst — you are the trader. Be decisive. State the action.
Don't say "consider" or "you might want to" — say "close GLD" or "hold".

ALERT THRESHOLDS (critical: don't spam — only push if material):
- CRITICAL: short strike breached, assignment risk, blow-through max loss imminent
- ACTION: profit target hit (50%+), 21 DTE reached, IV crush opportunity ready, news event needs response
- WATCH: position deteriorating but not actionable yet (log only, no push)
- HOLD: everything fine (log only, no push)

VOICE: tastytrade native. Use BPR, POP, P50, DTE, short put vertical, manage at 50%, roll, etc.
LENGTH: Reasoning is 1-2 sentences max. Specific recommendation is 1 sentence.
NEVER: hedge with "maybe", "consider", "you might"

OUTPUT FORMAT: Valid JSON only, matching this schema exactly:
{
  "timestamp": "ISO 8601 UTC",
  "market_view": "1-2 sentences on current market regime and what matters today",
  "positions": [
    {
      "symbol": "SPY 721/716p",
      "action": "HOLD" | "WATCH" | "ACTION" | "CRITICAL",
      "confidence": 0.0-1.0,
      "reasoning": "1-2 sentence explanation",
      "recommendation": "exactly what to do or null if HOLD/WATCH"
    }
  ],
  "macro_concerns": "any market-wide concerns Jay should know about, or null",
  "new_setups_flagged": "ONLY if exceptional opportunity, else null. Format: 'TICKER structure brief reasoning'"
}

No prose outside JSON. No markdown code blocks. Just the JSON object."""


def build_user_prompt(
    positions: List[Dict[str, Any]],
    market_state: Dict[str, Any],
    account_state: Dict[str, Any],
    recent_news: List[Dict[str, Any]],
    last_recommendations: Dict[str, Any],
    economic_calendar: List[Dict[str, Any]] = None,
) -> str:
    """Build the user-side context bundle for Claude."""
    return f"""CURRENT TIME (UTC): {datetime.now(timezone.utc).isoformat()}

ACCOUNT STATE:
{json.dumps(account_state, indent=2)}

OPEN POSITIONS:
{json.dumps(positions, indent=2)}

MARKET STATE:
{json.dumps(market_state, indent=2)}

RECENT NEWS (last 1 hour, position-relevant + macro):
{json.dumps(recent_news, indent=2) if recent_news else "No fresh news this cycle."}

LAST RECOMMENDATIONS (avoid duplicate alerts within 4h):
{json.dumps(last_recommendations, indent=2) if last_recommendations else "No prior recommendations this session."}

ECONOMIC CALENDAR (next 5 days):
{json.dumps(economic_calendar, indent=2) if economic_calendar else "Calendar not loaded this cycle."}

Analyze. Output JSON decision per the system prompt format. No prose."""


def decide(
    positions: List[Dict[str, Any]],
    market_state: Dict[str, Any],
    account_state: Dict[str, Any],
    recent_news: List[Dict[str, Any]] = None,
    last_recommendations: Dict[str, Any] = None,
    economic_calendar: List[Dict[str, Any]] = None,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 1500,
) -> Dict[str, Any]:
    """
    Main decision function. Call this every 15 min after position poll.

    Returns parsed JSON decision dict, or error dict if API/parsing fails.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "error": "ANTHROPIC_API_KEY not set",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    client = anthropic.Anthropic(api_key=api_key)

    user_prompt = build_user_prompt(
        positions=positions,
        market_state=market_state,
        account_state=account_state,
        recent_news=recent_news or [],
        last_recommendations=last_recommendations or {},
        economic_calendar=economic_calendar,
    )

    try:
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = msg.content[0].text.strip()

        # Defensive: strip code fences if model adds them despite instructions
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()

        decision = json.loads(text)
        decision["_model"] = model
        decision["_input_tokens"] = msg.usage.input_tokens
        decision["_output_tokens"] = msg.usage.output_tokens
        return decision

    except json.JSONDecodeError as e:
        return {
            "error": f"JSON parse failed: {e}",
            "raw_response": text[:500],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "error": f"API call failed: {e}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def should_alert(decision: Dict[str, Any], last_state: Dict[str, Any], dedupe_hours: int = 4) -> List[Dict[str, Any]]:
    """
    Determine which positions should trigger Pushover alerts.

    Rules:
    - CRITICAL: always alert (even if recent duplicate)
    - ACTION: alert if no same-action push for this symbol in last `dedupe_hours`
    - WATCH/HOLD: never alert

    Returns list of positions that should be pushed.
    """
    if "error" in decision:
        return []

    alerts = []
    now_iso = datetime.now(timezone.utc).isoformat()

    for pos in decision.get("positions", []):
        symbol = pos.get("symbol")
        action = pos.get("action", "HOLD")

        if action == "CRITICAL":
            alerts.append(pos)
            continue

        if action != "ACTION":
            continue  # HOLD/WATCH = no push

        # Dedup ACTION alerts
        last = last_state.get(symbol, {})
        last_action = last.get("action")
        last_time = last.get("timestamp")

        if last_action == "ACTION" and last_time:
            try:
                last_dt = datetime.fromisoformat(last_time.replace("Z", "+00:00"))
                hours_since = (datetime.now(timezone.utc) - last_dt).total_seconds() / 3600
                if hours_since < dedupe_hours:
                    continue  # Skip — duplicate within window
            except Exception:
                pass  # If parse fails, alert anyway

        alerts.append(pos)

    return alerts


def update_state(decision: Dict[str, Any], state_path: str = "state/last_recommendation.json"):
    """Persist current decision state for dedup logic on next run."""
    if "error" in decision:
        return

    state = {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "market_view": decision.get("market_view"),
    }
    for pos in decision.get("positions", []):
        symbol = pos.get("symbol")
        if symbol:
            state[symbol] = {
                "action": pos.get("action"),
                "confidence": pos.get("confidence"),
                "timestamp": decision.get("timestamp"),
                "reasoning": pos.get("reasoning"),
            }

    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)


def load_state(state_path: str = "state/last_recommendation.json") -> Dict[str, Any]:
    """Load last recommendation state for dedup."""
    if not os.path.exists(state_path):
        return {}
    try:
        with open(state_path) as f:
            return json.load(f)
    except Exception:
        return {}


if __name__ == "__main__":
    # Smoke test with synthetic data
    test_positions = [
        {
            "symbol": "GLD 395/390p",
            "expiry": "2026-06-18",
            "dte": 23,
            "credit": 0.73,
            "current_mid_cost": 0.67,
            "pct_captured": 8.2,
            "underlying_price": 416.99,
            "short_strike": 395,
            "buffer_pct": 5.3,
        },
    ]
    test_market = fetch_market_state() if False else {"vix": {"level": 16.5}, "market_regime": "neutral"}
    test_account = {"net_liq": 3486, "day_pnl": 0, "bpr_used": 799, "bpr_pct": 23}

    decision = decide(
        positions=test_positions,
        market_state=test_market,
        account_state=test_account,
    )
    print(json.dumps(decision, indent=2))
