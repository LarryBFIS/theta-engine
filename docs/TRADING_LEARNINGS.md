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

## Backlog (build order)
1. ✅ `memory/trades_ledger.json` — done (0052).
2. ✅ Static guards: per-name + cluster + total-open caps, size cap — done (0052).
   _Still TODO: feed the PAPER book's directional bias into structure selection
   (today only the live book's bias is used) for a true delta-balance guard._
3. `scripts/learn.py` (nightly) — realized win-rate & EV per bucket from the
   ledger → `memory/learnings.json`, with min-sample (N≥20) + shrinkage guards.
4. Scanner reads `memory/learnings.json` and adjusts selection/sizing; writes a
   human-readable changelog of what it learned and why.
