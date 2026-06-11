# Strategy Playbook — use cases & worked examples

_Companion to `docs/SCANNER_LOGIC.md` (the exact thresholds). This explains WHEN
each strategy fires and shows a worked example with real math. Part A = live in
the engine today. Part B = recommended additions, in build order._

---

## PART A — strategies the engine runs today

### A1. Short put vertical (the proven core)
**Use case:** an underlying you're neutral-to-bullish on, with rich premium
(IV rank ≥ 40%) and no earnings before expiry. You sell fear: collect credit
for agreeing to buy lower.

**Example (KO at $60, IV rank 55%, 40 DTE):**
- Sell 57P / buy 53P (4-wide, adaptive to the $344 max-loss cap).
- Executable credit: short bid $0.95 − long ask $0.20 = **$0.75**.
- Max gain $75 · max loss (4−0.75)×100 = **$325** · POP ~80%.
- EV = 0.80×(0.5×75) − 0.20×min(1.5×75, 325) = 30 − 22.5 = **+$7.5 − $3 fees = +$4.5/ctr**.
- Manage: GTC close at $0.37 (50%); cut if debit hits $1.88 (1.5×); exit 21 DTE.

### A2. Short call vertical (the bearish mirror)
**Use case:** price below its 20/50-day MAs (downtrend) **or** the book is
already long-delta and needs balancing. You collect credit for agreeing to
sell higher.

**Example (XLE at $56 in a downtrend, IVR 48%):**
- Sell 59C / buy 62C: credit $0.65, max loss (3−0.65)×100 = $235, POP ~78%
  (price stays below 59).
- Same management rules. Wins if the downtrend continues, chops, or even
  rallies a little — loses only on a strong rally through $59.

### A3. Iron condor (the neutral default)
**Use case:** no trend (mixed MAs) or book-balance says "don't add direction."
Sell BOTH sides; price just has to stay in the range. Max loss is one side only.

**Example (IWM at $292, IVR 50%, mixed trend):**
- Sell 272P/buy 268P + sell 312C/buy 316C (4-wide each).
- Total credit = put side $0.55 + call side $0.50 = **$1.05**.
- Max loss (4−1.05)×100 = **$295** (one side) · range POP = P(272 < price < 312) ≈ 76%.
- In elevated VIX, the put side goes FURTHER out (85% POP target) than the call —
  put skew means downside premium is richer, so you get paid more for less risk there.

### A4. Event crush IC (scheduled-event vega harvest)
**Use case:** a KNOWN binary event (FOMC) pumps near-dated IV. Sell a
defined-risk IC that expires AFTER the event, ~1 day before; close the day
after, harvesting the IV collapse — not predicting the direction.

**The queued live one (FOMC Jun 17, 2:00pm ET):**
- IWM (primary) or QQQ · Jul-17 expiry · ~12Δ shorts, put-skewed · 3-wide ·
  max loss ≤ $300 · **enter Jun 16, close Jun 18**.
- LIVE only if IV Rank ≥ 40% AND VIX ≥ 18 (no crush to harvest otherwise).
- Why it works: post-decision, IV drops several points in minutes; both sides
  of the IC deflate even if price moves moderately.

### A5. Long-vol watch (the mirror — paper-only)
**Use case:** the opposite setup — IV rank unusually LOW (≤30%) with a known
catalyst (earnings ≤14 days). The market may be UNDER-pricing the move; a
defined-risk strangle is the disciplined "it'll move, direction unknown" play.

**Example:** KO at IVR 18% with earnings in 9 days, ~1σ move priced at ±2.8%.
KO's earnings moves have recently run >4%: flag it. Paper-only — buying
premium is not the core edge; this is awareness, not a default trade.

---

## PART B — recommended additions (build order)

### B1. IV/RV ratio test (the true "is premium rich?" check)
**What:** IV rank says "high for this name's past year." IV/RV asks the better
question: is implied vol rich **versus what the stock actually moves**?
Require IV ≥ ~1.2× the 20-day realized vol.
**Use case it fixes:** a stock at IV rank 60% whose realized vol has risen just
as much — you'd collect "rich-looking" premium that's actually fair. IV/RV
filters those out.
**Example:** CAT shows IV 32%, IV rank 58%. Realized 20-day vol = 31% →
IV/RV = 1.03 → **skip** (no premium edge despite the rank). MRK shows IV 28%,
RV 19% → 1.47 → **sell** (you're paid 47% over what it moves).

### B2. POP calibration loop (the self-correcting book)
**What:** every closed paper trade logs model-POP vs. actual outcome. If
"80% POP" trades only win 70% over a rolling window, the engine widens its
strikes / discounts its own model automatically.
**Use case it fixes:** model drift — our lognormal POP ignores skew and fat
tails; this measures the real-world error and corrects it with data instead
of theory.
**Example:** after 30 closed paper trades, the 78–82% POP bucket shows 22 wins
(73%). Engine recalibrates: to get a TRUE 80%, target model-POP 85% → strikes
move further OTM → EV math now uses honest probabilities.

### B3. Per-name dedup + max-concurrent cap
**What:** never a second spread on the same underlying; cap total open
positions (e.g. 4) and per-sector exposure.
**Use case it fixes:** the scanner loves whatever is rich — if tech IV is
pumped it will happily flag NVDA, AMD, and QQQ together; one sector selloff
hits all three at once. (Your real June book had GLD twice — same lesson.)
**Example:** open book = GLD put vert + IWM IC + AMD put vert. Scan ranks AMD
again #1 and NVDA #2 → AMD blocked (dup), NVDA blocked (tech already via AMD),
#3 XLE passes.

### B4. Ex-dividend filter (assignment-risk dodge)
**What:** skip call-side structures (call verts, ICs) when an ex-dividend date
falls before expiry and the short call could go ITM.
**Use case it fixes:** short ITM calls get assigned the day before ex-div
(the holder wants the dividend) — you wake up short 100 shares plus owing the
dividend. Small accounts can't absorb that.
**Example:** XOM IC, short 118C, ex-div in 12 days, XOM rallies to 119 →
assignment risk. With the filter: the scan sees ex-div < expiry → builds the
put-vertical version instead, or skips.

### B5. Time-of-day execution window
**What:** only flag entries 10:00–15:30 ET; never in the first/last 30 min.
**Use case it fixes:** at the open, spreads are garbage — "executable credit"
computed at 9:32 is fiction; fills come back worse. At the close, you can't
manage what goes wrong.
**Example:** 9:35 scan shows GS put spread "credit $1.10" on a $0.40-wide
quote. By 10:15 the same spread quotes $0.85 at a $0.10-wide market — the
honest number. The window makes paper = real.

### B6. Term-structure check (sell the right expiry)
**What:** compare front vs. back-month IV. Normal = upward sloping (contango).
Inverted (backwardation) = the market is pricing a near-term event.
**Use case it fixes:** the scanner currently takes the shortest 30–60 DTE
expiry blindly. If July IV is 35% but August is 28%, July is where the
premium is — sell July. Inversion is also an event warning (cross-check the
earnings/event gates).
**Example:** IWM pre-FOMC: Jun-26 IV 31%, Jul-17 IV 26%, Aug 24% → inverted →
the event-crush logic (A4) applies; for a normal trade, prefer the expiry
with the richest IV per day of risk.

### B7. Absolute-spread floor
**What:** in addition to the 20% relative gate, reject quotes wider than
~$0.10 absolute when the option price is under ~$0.50.
**Use case it fixes:** a $0.30 option quoted $0.25/$0.35 passes the relative
test math but is a coin-flip fill; slippage eats the whole edge on cheap legs.
**Example:** SLV long leg quoted $0.04/$0.12 (mid $0.08, rel 100% — caught) vs
$0.28/$0.36 (rel 25%... but $0.08 wide on a $0.32 option = a third of the
premium). The absolute floor catches the second one.

### B8. Fractional Kelly sizing (later — needs track record)
**What:** size positions by measured edge ÷ variance (½-Kelly), instead of
flat caps. Strictly AFTER the paper book has ≥50 closed trades of honest
history — Kelly with a guessed edge is how accounts die.
**Example:** paper book shows true 76% win rate, avg win $38, avg loss $95 →
edge per trade ≈ 0.76×38 − 0.24×95 = +$6.1; Kelly fraction ≈ 4.7%; half-Kelly
≈ 2.3% of capital risked per trade ($80 on $3.4k) — interestingly SMALLER
than the current 10% cap, which is the point: math-sized, not vibes-sized.

---

## Build order (proposed)
1. **B1 IV/RV** + **B3 dedup/caps** + **B5 time window** — one patch, biggest honesty/edge gain.
2. **B4 ex-div** + **B7 absolute spread** — small adds to the same gates.
3. **B6 term structure** — needs an extra chain call per name.
4. **B2 calibration** — switches on automatically once the paper book has data.
5. **B8 Kelly** — only after ≥50 honest closed paper trades.
