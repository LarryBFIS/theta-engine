# Investor Profile — Jay Vekaria

_The engine's living memory of you as an investor. Honest mechanism note:
there is no hidden ML model training on these chats — this document + the
repo + chat history ARE the memory. It gets updated as we work together, and
every future session reads it first. Corrections welcome any time._

## Vision (the north star)
1. **Now:** the engine finds/sizes/times/monitors; paper-trades autonomously at
   real quotes; Jay executes manually and approves anything LIVE.
2. **Next:** paper book proves the edge over several sessions (honest fills,
   real win rate). Engine earns trust trade by trade.
3. **End state:** 100% automated trading with real money — guardrailed
   (max-loss caps, BPR ceiling, kill switch, event blackouts), with Jay
   supervising rather than executing.

## Goals & risk posture
- **Goal:** +100% on ~$3,438 baseline by Nov 13, 2026 (aggressive; accepted).
- Comfortable with BPR utilization up to ~50%; hard cap 10% of net liq risked
  per position.
- Wants the bot to be "a very smart active trader," not a passive screener —
  but **never** auto-executing real money without explicit approval (today).

## Style & preferences (learned from sessions)
- **Honesty over hype — explicitly demanded.** Called out the inflated paper
  book immediately; insisted paper P&L must equal what real money would do
  ("no bullshit"). Conservative/executable fills preferred over flattering mids.
- Premium seller by conviction (tastytrade school: ~45 DTE, manage at 50%,
  21-DTE exit, defined risk). Open to long-vol only as a disciplined,
  catalyst-driven exception.
- Asked unprompted whether to buy a BTC straddle after a drop — accepted "no"
  when shown the IV-crush logic. Learns fast from one explanation; wants the
  *why*, not just the call.
- Numbers-literate: caught the opening-liquidity reconciliation gap himself
  (current − P&L ≠ baseline). Verify totals before he does.
- Non-coder; applies patches via terminal carefully. Keep instructions exact,
  one block, with the cd first. Other repos exist on his machine — never
  assume the cwd.
- Wants dashboards visual, complete, and identical between live and paper.
  Losses red, profits green — found it himself when wrong.
- Communication: concise, direct, no fluff; will say "fix it" and expects
  ownership end-to-end.

## Current standing instructions
- Pushover ping on every paper-trade open (with ticket numbers) so he can
  choose to replicate manually.
- Every live trade idea goes through chat for sizing before he clicks.
- New structures (call verts, ICs) stay paper until proven.
- FOMC Jun-17 IC is the queued live candidate (enter Jun 16, conditions:
  IVR ≥ 40%, VIX ≥ 18).

## Open questions to learn next
- Drawdown tolerance in dollars (what loss in a week would make him stand down?)
- Preference between fewer/larger vs more/smaller positions as capital grows.
- Sectors he refuses to trade (none stated yet).
- When automation comes: daily loss limit and kill-switch criteria he wants.
