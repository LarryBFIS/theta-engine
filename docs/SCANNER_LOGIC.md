# Opportunity Scanner — Exact Logic Spec

_Reverse-engineered directly from `scripts/scan_opportunities.py` (and
`monitor/news_risk.py`, `monitor/market_data.py`). Describes behavior **as
implemented**, with exact numbers. Anything not built is marked
**NOT IMPLEMENTED**._

> **Deployment note:** the premium-sell core + both shields are **live on `main`**.
> The **long-vol mode** (§3b, §9) and its dashboard panel ship in **patch 0033 / 0031**
> (pending push at time of writing). Everything else here is running now.

All thresholds are module constants, each overridable by an env var (shown in
parentheses). Defaults below are what runs if the env var is unset.

---

## 1. Universe — which tickers, how the list is built

- **Hardcoded list of 40 liquid, optionable symbols** (`DEFAULT_UNIVERSE`):
  - ETFs: `SPY, QQQ, IWM, DIA, GLD, SLV, TLT, XLF, XLE, XLK`
  - Mega/large-cap equities: `AAPL, MSFT, AMZN, GOOGL, META, NVDA, AMD, TSLA, NFLX, JPM, BAC, WFC, GS, V, MA, DIS, KO, PEP, WMT, COST, XOM, CVX, PFE, MRK, INTC, CSCO, ORCL, CRM, BA, CAT`
- **Override:** env `SCAN_UNIVERSE="A,B,C"` replaces the whole list (comma-separated, upper-cased).
- **No dynamic selection** — the list is static. No volume/market-cap screening to build it. **NOT IMPLEMENTED.**

## 2. Data sources

| Data | Source | Function |
|---|---|---|
| Equity price | tastytrade `GET /market-data/by-type?equity=` → `mark`, else `last`, else `(bid+ask)/2` | `fetch_equity_prices` |
| IV (index) | tastytrade `GET /market-metrics?symbols=` → `implied-volatility-index` | `fetch_metrics` |
| **IV RANK** | `/market-metrics` → `implied-volatility-index-rank` (falls back to `tw-…` then `tos-…`). If value > 1.5 it's divided by 100 (percent→fraction). | `fetch_metrics` |
| Earnings date | `/market-metrics` → `earnings.expected-report-date` | `fetch_metrics` |
| Liquidity rating | `/market-metrics` → `liquidity-rating` (falls back to `liquidity-rank`) | `fetch_metrics` |
| Option chain | tastytrade `GET /option-chains/{sym}/nested` | `fetch_chain_expiration` |
| Option leg quotes | `TastytradeClient.fetch_option_quotes` (`/market-data/by-type?equity-option=`) → `{bid, ask, mark}` | `main` |
| VIX (regime shield) | `yfinance ^VIX` — current close + prior close | `monitor.market_data.get_vix` |
| News (news shield) | Yahoo Finance RSS (`feeds.finance.yahoo.com/rss/...`) via `feedparser` | `monitor.news_risk.fetch_headlines` |

All fetches are wrapped defensively; a name with missing metrics/price/chain/quotes is **skipped** (recorded in `skipped{}`), never guessed.

## 3. Structures

### 3a. Premium-sell (the core, live)
- **Short put vertical ONLY** (`structure: "short_put_vertical"`). Sell a put near target POP, buy a further-OTM put `width` below it.
- **Put side only.** There is no call-side logic, no directional switch. **Call verticals: NOT IMPLEMENTED.**
- **Iron condors: NOT IMPLEMENTED.** (The FOMC alert *suggests* an IC to you manually, but the scanner never builds/scores one.)

### 3b. Long-vol mode (mirror; paper-only; patch 0033)
- Flags `structure: "long_strangle"` candidates — but only as a **watch list**, always `tag: "paper"`. It does **not** pick strikes or price the strangle; it only flags the underlying + expected move. Strike selection for long-vol: **NOT IMPLEMENTED** (intentionally — it's a heads-up, not an order).

## 4. Filters & thresholds (premium-sell)

Applied in this order; first failure skips the name:

1. **Metrics/price present** — else skip `"no metrics/price"`.
2. **IV-rank floor:** `iv_rank < MIN_IV_RANK (0.30)` → skip. _(`SCAN_MIN_IV_RANK`)_
3. **DTE window:** chain must have an expiration with `DTE_MIN (30) ≤ DTE ≤ DTE_MAX (50)`. Picks the **shortest** expiry in that window. _(`SCAN_DTE_MIN`, `SCAN_DTE_MAX`)_
4. **Earnings-before-expiry:** if `today ≤ earnings_date ≤ expiry` → skip `"earnings … before expiry"`.
5. **Strike selection** (`choose_strikes`): short = strike below spot whose POP is closest to `TARGET_POP (0.80)`; long = nearest strike to `short − width`. _(`SCAN_TARGET_POP`)_
   - **Width** (`target_width`): `max(MIN_WIDTH ($5), round(price × WIDTH_PCT (0.012)))` → ≈1.2% of spot, floored at $5. _(`SCAN_MIN_WIDTH`, `SCAN_WIDTH_PCT`)_
6. **Liquidity gate (short leg only):** short-leg relative spread `(ask−bid)/mid` must be `≤ MAX_REL_SPREAD (0.20)`. The long leg is **not** spread-gated. _(`SCAN_MAX_REL_SPREAD`)_
   - **Open-interest / volume gating: NOT IMPLEMENTED.** Liquidity is the bid/ask spread test above, plus tastytrade's `liquidity-rating` (used only in conviction, §6).
7. **Executable credit:** `credit = short.bid − long.ask` (cross the spread, not the mid). Reject if `credit ≤ 0`.
8. **Credit-to-width floor:** reject if `credit / width < MIN_CREDIT_RATIO (0.15)`. _(`SCAN_MIN_CREDIT_RATIO`)_
9. **POP band:** reject unless `MIN_POP (0.70) ≤ POP ≤ MAX_POP (0.90)`. _(`SCAN_MIN_POP`, `SCAN_MAX_POP`)_
10. **BPR positive:** `bpr = (width − credit) × 100`; reject if `≤ 0`.
11. **Positive expectancy:** reject if `ev_per_contract ≤ 0` (EV is net of fees, §5).

**Capital/risk caps:**
- **BPR is computed per spread** (`(width−credit)×100`) but there is **no portfolio-level BPR cap** in the scanner. **NOT IMPLEMENTED.**
- **Per-position max-loss cap** (e.g. "≤ $300"): the max loss *equals* BPR, but it is **not enforced as a filter**. **NOT IMPLEMENTED.** (Sizing/limits live in your execution rules, not the scanner.)
- **Position sizing: NOT IMPLEMENTED.** Everything is scored per 1 contract.

## 5. Scoring — exact expectancy & ranking formula

Per candidate, all in dollars per 1 contract:

```
win_amount  = MANAGE_FRAC (0.50) × credit × 100      # take profit at 50% of credit
loss_amount = STOP_MULT  (1.50) × credit × 100       # cut loser at 1.5× credit
expectancy  = POP × win_amount − (1 − POP) × loss_amount
ev_per_contract = expectancy − FEES_PER_SPREAD (3.0) # est. round-trip fees
ev_on_bpr   = ev_per_contract / bpr
```
_(env: `SCAN_MANAGE_FRAC`, `SCAN_STOP_MULT`, `SCAN_FEES_PER_SPREAD`)_

- **POP** = `norm_cdf(d2)`, lognormal, **r = q = 0** (no rates/dividends).
  `d2 = (ln(price/strike) − 0.5·iv²·t) / (iv·√t)`, `t = dte/365`.
- **Ranking** (`rank_opportunities`): sort **descending** by the tuple
  `(ev_on_bpr, iv_rank, pop)`, keep the top `TOP_N (10)`. _(`SCAN_TOP_N`)_

## 6. Conviction — LIVE vs PAPER (`conviction_tag`)

A pick is tagged **`live`** (eligible for real execution) **only if ALL three hold**:
```
ev_on_bpr ≥ LIVE_MIN_EV_ON_BPR (0.018)
iv_rank   ≥ LIVE_MIN_IV_RANK   (0.50)
liquidity is None  OR  liquidity ≥ 2     # tastytrade liquidity-rating
```
Otherwise **`paper`**. _(env: `SCAN_LIVE_MIN_EV_ON_BPR`, `SCAN_LIVE_MIN_IV_RANK`)_

Note the asymmetry: the **scan floor** to appear at all is IV-rank ≥ 0.30, but to go **LIVE** it must be IV-rank ≥ 0.50.

A LIVE tag can be **demoted to PAPER** afterward by either shield (§7).

## 7. Shields

### 7a. News gate (`_apply_news_gate` → `monitor.news_risk.assess_symbol`)
Runs on **every ranked pick**. For each underlying:
- Fetch up to **8** recent Yahoo RSS headlines.
- **Recency filter:** ignore headlines older than `max_age_days = 4`.
- **Keyword severity** (substring, lowercased), highest tier wins:
  - **Tier 3 → veto** (max_severity 3): `bankruptcy, chapter 11, going concern, default, fraud, "sec ", investigation, probe, subpoena, halt(ed), delist, restate, guidance cut, slashes guidance, plunge, fda reject, rejected, recall, warning letter, data breach, hacked, ceo resign, cfo resign, accounting, going private`
  - **Tier 2 → caution** (severity 2): `downgrade, cut to, lawsuit, sued, settlement, fine(d), misses, warns, warning, layoff, resign, step down, short seller, guidance, slash, profit warning, strike`
  - **Tier 1 → clear** (severity 1, informational): `earnings, upgrade, price target, analyst, merger, acquisition, buyout, dividend, split, forecast, outlook, report`
- **Level mapping:** severity `0/1 → clear`, `2 → caution`, `3 → veto`.
- **Action:** if `level == "veto"` **and** pick is `live` → demote to `paper` (`demoted: "news veto"`). `caution`/`clear` are recorded (`news_risk` field) but do **not** demote.
- **Optional AI escalation:** only if `SCAN_AI_NEWS_GATE=1` **and** `ANTHROPIC_API_KEY` set. Asks `claude-haiku-4-5` for one word (VETO/CAUTION/CLEAR); can **only escalate** the deterministic verdict, never relax it. **Default: OFF** (`SCAN_AI_NEWS_GATE=0`).

### 7b. VIX regime overlay (`market_regime` + `_market_regime_now`)
Fetches VIX (current + day change). Thresholds _(env-overridable)_:
- `VIX_CALM = 15`, `VIX_ELEVATED = 20`, `VIX_STRESS = 30`, `VIX_SPIKE_DAY = 0.15`

| Condition | level | stand_down |
|---|---|---|
| `vix ≥ 30` **OR** (`day_change ≥ +15%` **AND** `vix ≥ 20`) | `stress` | **TRUE** |
| `20 ≤ vix < 30` | `elevated` | false |
| `15 ≤ vix < 20` | `normal` | false |
| `vix < 15` | `calm` | false |
| VIX unavailable | `unknown` | false (proceed) |

- **On `stand_down`:** every `live` pick is demoted to `paper` (`demoted: "vol stress"`) and a Pushover "Vol stress — standing down" alert fires. Paper tracking continues.
- Rationale baked in: high **stable** IV = rich premium (sell it); a **spiking** VIX = falling market (don't sell into the knife).

## 8. Event awareness

- **Earnings: YES.** Pulled per name from `/market-metrics` and used to **skip** any name whose earnings fall on/before the chosen expiry (§4.4). It is *also* the catalyst trigger for long-vol mode (§3b).
- **CPI / FOMC / macro calendar: NOT IMPLEMENTED in the scanner.** The scanner has no CPI or FOMC date awareness. (FOMC is handled **separately** by the poll's FOMC trigger — `monitor/fomc.py`, patch 0033 — which is *not* part of this scanner.)

## 9. Output schema — `scan/opportunities.json`

Top-level keys written by `_write`:
```jsonc
{
  "generated_at": "<UTC ISO8601>",
  "regime": { "vix", "vix_day_change_pct", "level", "stand_down", "note" },
  "params": { "min_iv_rank", "dte_min", "dte_max", "target_pop",
              "width_pct", "min_width",
              "longvol_max_iv_rank", "longvol_catalyst_days" },
  "top":            [ <ranked premium-sell candidates, ≤ TOP_N> ],
  "long_vol":       [ <long-vol watch items> ],          // patch 0033
  "all_candidates": [ <every candidate that passed filters, unranked> ],
  "skipped":        { "<SYM>": "<reason>", ... }
}
```

**Each `top[]` candidate** (`build_candidate`):
`underlying, structure ("short_put_vertical"), expiry, dte, short_strike, long_strike, short_symbol, long_symbol, width, credit (executable), mid_credit, fees_est, bpr, pop, short_delta, short_spread_pct, credit_to_bpr, ev_per_contract, ev_on_bpr, iv, iv_rank, underlying_price, liquidity, earnings_date, tag ("live"|"paper")` — plus `news_risk{level,hits}` and `demoted` if a shield acted.

**Each `long_vol[]` item** (`long_vol_candidate`):
`underlying, structure ("long_strangle"), iv_rank, iv, price, earnings_date, days_to_catalyst, expected_move, expected_move_pct, tag ("paper"), rationale`.

**Also writes** `scan/summary.md` (human-readable table + a "Long-vol watch" section).

**What the dashboard reads** (`dashboard.html` / `paper.html` `loadFeed`):
- ⚡ OPPORTUNITIES panel ← `top[]`: uses `underlying, structure, short_strike, long_strike, tag, credit, pop, iv_rank, ev_per_contract`; panel timestamp ← `generated_at`.
- 🌊 LONG-VOL WATCH panel ← `long_vol[]`: uses `underlying, iv_rank, days_to_catalyst, expected_move_pct` _(panel ships in patch 0031)_.
- The dashboard does **not** currently surface `regime`, `all_candidates`, or `skipped` (they're in the JSON for diagnostics).

## 10. Hardcoded / stubbed / TODO

- **Field shapes unconfirmed:** module docstring flags that the `/market-metrics`, `/option-chains`, and quote field names "need one real API run to confirm" — parsing is defensive and silently skips anything unreadable.
- **POP model:** lognormal with **r = q = 0** (ignores interest & dividends). No vega/theta/gamma modeling.
- **Single expiry pick:** takes the *shortest* expiry in the 30–50 DTE window; doesn't compare across expiries.
- **`liquidity ≥ 2`** assumes tastytrade's rating scale; if the field is absent (`None`) the liquidity check passes by default.
- **Dead code:** `_mid()` helper is defined but unused.
- **Not built (explicitly):** iron condors · call verticals · open-interest/volume gate · portfolio BPR cap · per-position max-loss cap · position sizing · CPI/FOMC calendar awareness · long-vol strike selection. All **NOT IMPLEMENTED.**
- **Greeks/skew-aware strike selection: NOT IMPLEMENTED** (strikes chosen by POP-to-target only).
- **Correlation / sector exposure caps: NOT IMPLEMENTED.**
- **AI news gate default OFF** (`SCAN_AI_NEWS_GATE=0`).
