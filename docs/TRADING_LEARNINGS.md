# Trading Learnings — living memory of what actually works

_Honest mechanism note: the engine does **not** yet auto-learn. Its scanner
parameters are fixed constants and nothing reads closed-trade outcomes to
adapt. This file is the bridge: every time we derive an insight from the paper
book or a discussion, it gets recorded here, dated, and tagged **robust** vs
**confounded**. The planned `scripts/learn.py` will eventually consume a
machine-readable version (`memory/learnings.json`) — but until then, THIS file
is the memory, and every future session must read it first and append to it._

**Standing rule (set 2026-06-15):** whenever we discuss a trading insight,
update this file in the same turn and deliver it as a patch. No insight dies in
chat.

**How to read a learning:**
- 🟢 **robust** = direction-independent, mechanical, or repeated → safe to act on.
- 🟡 **confounded** = looks like edge but is mostly market-direction/regime → do
  NOT hardcode as a rule; it will flip when the regime flips.
- Sample sizes are tiny early on. Require ≥20 closes before a learning hardens
  into a parameter change; shrink toward priors until then.

---

## 2026-06-15 — first read of the paper book (30 trades: 8 closed, 22 open)

Realized −$999 on 8 closes (4 wins / 4 losses); open unrealized ≈ −$638;
honest paper P&L incl. est. fees ≈ −$1,814.

### 🟢 L1 — Win/loss asymmetry is mechanically lethal at 50% win rate
- Avg win **+$127**, avg loss **−$376** → losers ≈ **3× winners**.
- Cause: take profit at **50% of credit** but let losers run to **1.5× stop**.
- Math: that payoff needs a **~67%+ win rate** just to break even; 50% loses.
- **Action:** fix the asymmetry — take profit later OR cut losers sooner so
  avg win ≈ avg loss. (Direction-independent → act on it.)

### 🟢 L2 — Size is the damage multiplier
- 2× contracts: 3/4 wins, **+$183**. 4× contracts: 1/4 wins, **−$1,182**.
- Nearly all the loss is the 4-lots (XOM, GLD, MSFT each 4×).
- **Action:** cap per-position size; small account ⇒ 1–2 lots until edge proven.

### 🟢 L3 — Single-names carry idiosyncratic risk the index doesn't
- Single-name closes: **0/4 wins, −$1,506**. Index closes: **4/4, +$507**.
- Key evidence this is *partly* real (not just direction): XOM was a **put**
  vertical (long delta) that still **lost** because energy fell *while the
  market rose*; GLD rose on its own. Single-names diverged from the index in
  **both** directions → genuine structural risk.
- **Action:** prefer index ETFs (SPY/QQQ/IWM); require higher bar for
  single-names; cap concentration (no QQQ ×5).

### 🟡 L4 — "Put verticals win / call verticals & ICs lose" is MOSTLY market direction
- Decomposed by delta: winners were **long-delta** (put verts) in a **rising**
  market; losers were **short-delta** (call verts, call side of ICs) in the same
  rising market. Open book confirms live: put verts **+$282**, call verts
  **−$440**, ICs **−$438**.
- This is **not** structural edge — it's a disguised bullish bet. Hardcoding
  "always sell put verts" = "always be long," which gets punished at a regime
  turn (e.g. a hawkish FOMC).
- **Action:** do NOT hardcode a structure/direction preference. Keep the book
  **delta-balanced**; let IV rank + defined risk drive selection, not recent tape.

### Net takeaway for selection going forward
Trustworthy now (🟢): prefer indices, cap size, cap concentration, fix
asymmetry, stay delta-neutral. Not trustworthy (🟡): any structure preference
inferred from the last few up-weeks.

---

## 2026-06-15 — accounting honesty (dashboard)
- Live hero residual was mislabeled "fees/adj" (read positive; real fees can't
  be). It is **non-strategy holdings (USO) + baseline/interest drift + net fees**
  — relabeled "non-strategy". NOT trading profit.
- Paper P&L was overstating vs real money because open positions ignored the
  commissions still owed. Now nets round-trip fees ($1.25/leg/contract) as an
  explicit "est. fees" line → paper stays conservative (real ≥ paper).
- **Meta-learning:** always reconcile displayed P&L to the account; label
  residuals honestly; never let a number flatter the engine.

---

## 2026-06-15 — Phase 1 shipped (patch 0052)
- **Outcomes ledger** (`memory/trades_ledger.json`): every close recorded with
  features (asset_class index/sector/single, correlation cluster, structure,
  size, IVR/POP at entry, close_reason, realized P&L, won). Backfills on first
  run. First read already confirms L3: index_etf **5/5 wins**, sector+single
  **0/4** — now captured automatically, not by hand.
- **Concentration caps** in `record_picks` (the position chokepoint): max 1 per
  name, max 3 per correlation cluster, max 8 total open. Directly prevents the
  QQQ ×5 / all-tech stacking that caused the hole.
- **Size cap** in the scanner: `MAX_CONTRACTS=3` — kills the 4-lot blowups that
  were nearly the entire realized loss.
- Unit-tested (cluster/asset classification, all three caps, ledger shape).

## 2026-06-15 — Phase 2 shipped (patch 0053): the loop is closed
- **`scripts/learn.py`** reads the ledger → realized win-rate & expectancy per
  bucket (asset_class / structure / cluster / size) → `memory/learnings.json`
  + a human-readable `memory/learnings.md`. The scanner calls it every run.
- **Scanner consumes it:** each candidate's rank is tilted by its bucket
  multiplier (asset_class × structure × cluster), clamped to [0.4, 1.6].
- **Overfitting discipline (the whole point):** a bucket is inert (×1.00) until
  **n ≥ 20** closes; win-rates are **shrunk** toward the global prior (Beta-
  Binomial, k=10). Verified on the real 9-close ledger: it *sees* index_etf at
  5/5 (+$120 avg) but correctly does **nothing** ("watch n=5 < 20"). It only
  bites once the evidence is real — so the L4 direction-confound can't get
  hardcoded from a few up-weeks.
- Unit-tested (shrinkage, min-sample gate, favor/AVOID, candidate multiplier).
- `scan.yml` now also commits `memory/` so the ledger/learnings persist.

**Status: the autonomous learning loop is live but dormant by design.** It needs
~20+ clean closes under the new caps before any bucket acts. Until then it's
accumulating evidence and showing it, without trading on noise.

## 2026-06-16 — Phase 3 (patch 0054): reconcile the legacy book to caps
- The caps stop NEW concentration but the 25 pre-cap open positions still carried
  the risk (QQQ ×6) and −$1,745 in marks. `scripts/reconcile_paper.py` +
  `reconcile_to_caps()` paper-close the over-cap excess at last mark, keeping the
  best-fitting positions (index first, then better unrealized, then smaller size).
- Honest accounting: reconcile **locks in ~$1.9k of unrealized marks** — it does
  NOT recover money. The value is risk removal (no correlated stack into the Fed),
  a clean within-caps forward test, and ~18 more ledger closes (28 total; brings
  short_put_vertical to 19 — one shy of the n≥20 learner-activation bar).
- Offline/pure (uses stored marks; no API) and idempotent. Unit-tested.
- **Lesson reinforced:** holding a pile of correlated, underwater, rule-breaking
  positions hoping for recovery is the exact gambler behavior we engineer against.
  Cut concentration; don't pray for the mark to come back.

## 2026-06-16 — Phase 4 (patch 0055): the engine now REASONS (agentic LLM)
- Root cause of the −$2,775: between chats the engine was a brain-dead rules
  executor — nothing looked at "6th QQQ into a Fed" and said stop. Fixed by
  wiring an LLM portfolio-risk agent INTO the scan pipeline (`monitor/agent_review.py`).
- Each scan, after the deterministic scanner proposes candidates, Claude reasons
  over the whole picture (candidates + open book + regime + macro calendar +
  these learnings) and returns approve / downsize / veto **with written reasons**,
  journaled to `memory/agent_journal.jsonl`.
- **Bounded authority (defense in depth):** the agent can ONLY make a trade more
  conservative — veto or cut size. It cannot increase size, add trades, change
  live/paper, or override a hard cap; enforced in code (unit-tested). The
  deterministic caps + news/regime/blackout gates remain underneath it.
- **Fail-safe:** no API key / API error / bad reply ⇒ candidates pass unchanged.
  The agent can only help; it can never break the scan.
- Honest: judgment ≠ profit. It catches the dumb/unwise trade; it is not an
  oracle — which is exactly why the hard rails stay.

## 2026-06-16 — Phase 4 verified live + every opportunity now AI-gated (0059)
- Smoke test (agent-smoke workflow) ran the REAL Haiku call on a synthetic
  into-the-Fed concentrated book: vetoed QQQ (event + already-held) and AMD
  (single-name + over cluster/size cap), approved the diversified SPY condor —
  with written reasons, journaled. Key valid, guardrail held. Brain is online.
- **Standing rule (Jay, 2026-06-16):** every surfaced opportunity must pass the
  full agentic reasoning before it appears. Implemented: agent REVIEW_MODE now
  defaults to "always" (every scan with candidates is reviewed), and a LIVE
  recommendation requires the agent's explicit approval — un-approved/unreviewed
  picks are demoted to PAPER ("never recommend live without AI sign-off").
- Dashboards show each opportunity's AI verdict (🧠 AI approved/trimmed/not-
  reviewed + reason on hover). Cost at always-on Haiku ≈ $1-2.50/mo.

## 2026-06-17 — first LIVE managed trade + productivity build (0061)
- First live trade executed end-to-end through chat: IWM iron condor (×2,
  re-centered to ~20Δ, GTC 50% close armed). Live record stands at +$64.96
  realized (6 closes, 67% win) + 2 open (SLV put vert, IWM IC). Friction was the
  problem: ~6 round trips to build one ticket (skew + size fixes by hand).
- **Auto-ticket builder** (`scripts/trade_ticket.py`): every scanned opportunity
  now carries a ready-to-send order — exact legs, net-credit limit, sizing, max
  loss, copy-ready text, and the 50%/1.5x/21-DTE management orders. Surfaced on
  both dashboards (📋 line; full legs on hover). Turns a 6-step build into review-
  and-send. Unit-tested.
- **Productivity roadmap (agreed):** (1) auto-ticket [done], (2) reliable scans
  via the tick trigger + watchdog [next], (3) auto-arm management orders at entry,
  (4) widen funnel (post-blackout scan, earnings crush, CPI/jobs, more structures).
  Honest caveat: efficiency can't manufacture edge that isn't there at low vol —
  it ensures we *capture* edge instantly when it appears, and never on stale data.

## 2026-06-17 — productivity #2: scan reliability (0062)
- Root cause of the stale board: GitHub *scheduled* scan triggers fire
  erratically (scans skipped on a live trading day). Fix: the *tick* (reliable
  Cloudflare dispatch, ~10 min) now runs a **scan watchdog** (`scan_if_stale.py`)
  — if the scan is older than 25 min during market hours, it runs a fresh scan
  before the tick's paper step, then the tick commits it. Cron stays primary;
  the tick is the backstop. Non-fatal (a scan error never breaks the tick).
  Pure staleness/market-hours logic unit-tested. Worst-case cost ≈ a scan every
  ~25 min during the session (Haiku agent ≈ a few \$/mo).

## 2026-06-22 — 🟢 Broad index (SPY/IWM) >> big tech (data-confirmed, patch 0064)
- Jay's observation, verified against the ledger: **broad index is the sweet spot,
  big tech is a trap.**
  - **SPY/IWM:** live 3/3 (+$104) · paper 6/6 (+$642) → **9/9, 100% win, +$746.**
  - **Big tech (us_tech: QQQ + tech single-names):** live 0/1 · paper 4/22 →
    **~17% win, −$2,704.**
- Caveats (act on signal, not noise): much of the tech loss came from the pre-cap
  concentration blowup, and tech was high-beta/trending this window (murders short
  premium). Small live sample. So it's a strong *current* edge + sound rationale
  (index = diversified, mean-reverting, lower gap risk; tech = concentrated,
  high-beta, idiosyncratic), not an eternal law. The learner + agent already lean
  this way (agent cited "us_tech 24% win rate" when vetoing tech).
- Shipped: an **opportunities filter toggle (ALL ↔ SPY/IWM)** on both dashboards so
  Jay can focus on the proven core. (Selection-side: consider down-weighting/curbing
  us_tech once the learner is fully active — a future build.)

## Backlog (build order)
1. ✅ `memory/trades_ledger.json` — done (0052).
2. ✅ Static guards: per-name + cluster + total-open caps, size cap — done (0052).
3. ✅ `scripts/learn.py` + scanner consumption — done (0053).
4. _Next:_ feed the PAPER book's directional bias into structure selection
   (today only the live book's bias is used) for a true delta-balance guard.
5. _Next:_ surface `memory/learnings.md` on the dashboards / works page so the
   "what the engine learned" story is visible.
6. _Later:_ once a bucket is actionable, let a strongly-negative bucket hard-demote
   LIVE→PAPER (today learnings only soft-tilt the ranking, never hard-block).
