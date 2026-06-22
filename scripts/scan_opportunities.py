"""Opportunity scanner — rank the best short-put-vertical setups across a liquid
universe by expected value. This is the "open at the right time" engine.

Edge model (honest): we are NOT predicting direction. We harvest the volatility
risk premium, and only when we're paid for it:
  - only sell when premium is rich (IV rank >= threshold);
  - dodge landmines (earnings before expiry, illiquid names);
  - put the short strike at a sensible probability-of-profit;
  - rank by expected $ return on the capital (BPR) each trade ties up.

The math (norm_cdf, put_pop, choose_strikes, expectancy, rank_opportunities) is
pure and unit-tested in scripts/test_scan_opportunities.py. Only main() touches
the network. Outputs scan/opportunities.json + scan/summary.md.

NOTE: the live-fetch field shapes (market-metrics / option-chains / quotes) need
one real API run to confirm; parsing is defensive and skips anything it can't read.
"""
import json
import logging
import math
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_DIR = REPO_ROOT / "scan"

log = logging.getLogger("scan")

# Last builder reject reason (diagnostics): set by _no() inside the candidate
# builders so the scan reports WHY a name failed, not just "failed filters".
LAST_REJECT = None


def _no(reason):
    """Record the reject reason and return None (builder early-exit helper)."""
    global LAST_REJECT
    LAST_REJECT = reason
    return None

# ── Tunables (env-overridable) ──────────────────────────────────────────
# A curated liquid, optionable universe. Override with SCAN_UNIVERSE="A,B,C".
DEFAULT_UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA", "GLD", "SLV", "TLT", "XLF", "XLE", "XLK",
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "AMD", "TSLA", "NFLX",
    "JPM", "BAC", "WFC", "GS", "V", "MA", "DIS", "KO", "PEP", "WMT", "COST",
    "XOM", "CVX", "PFE", "MRK", "INTC", "CSCO", "ORCL", "CRM", "BA", "CAT",
]
MIN_IV_RANK = float(os.getenv("SCAN_MIN_IV_RANK", "0.40"))   # only rich premium (P4: 0.30->0.40)
DTE_MIN = int(os.getenv("SCAN_DTE_MIN", "30"))
DTE_MAX = int(os.getenv("SCAN_DTE_MAX", "60"))               # P4: 50->60
TARGET_POP = float(os.getenv("SCAN_TARGET_POP", "0.80"))     # ~0.20Δ short put
MIN_POP = float(os.getenv("SCAN_MIN_POP", "0.70"))
MAX_POP = float(os.getenv("SCAN_MAX_POP", "0.90"))
WIDTH_PCT = float(os.getenv("SCAN_WIDTH_PCT", "0.012"))      # spread width ≈ 1.2% of price
MIN_WIDTH = float(os.getenv("SCAN_MIN_WIDTH", "5"))          # preferred floor width ($)
MIN_WIDTH_FLOOR = float(os.getenv("SCAN_MIN_WIDTH_FLOOR", "1"))  # hard floor when account forces narrow
MIN_CREDIT_RATIO = float(os.getenv("SCAN_MIN_CREDIT_RATIO", "0.10"))  # exec credit / width — EXECUTABLE
# pricing runs 5-13% of width at ~20Δ (measured live 6/11); the EV-after-fees
# gate is the true edge filter, this floor just blocks the absurd.
FEES_PER_SPREAD = float(os.getenv("SCAN_FEES_PER_SPREAD", "3.0"))     # est. open+close commissions/fees
MAX_REL_SPREAD = float(os.getenv("SCAN_MAX_REL_SPREAD", "0.20"))      # SHORT-leg bid/ask tightness
MAX_REL_SPREAD_LONG = float(os.getenv("SCAN_MAX_REL_SPREAD_LONG", "0.40"))  # long leg eased (naturally wider OTM)
MIN_OPEN_INTEREST = int(os.getenv("SCAN_MIN_OI", "100"))     # P4: reject thin chains (short leg OI)
MANAGE_FRAC = float(os.getenv("SCAN_MANAGE_FRAC", "0.5"))    # take profit at 50%
STOP_MULT = float(os.getenv("SCAN_STOP_MULT", "1.5"))        # cut losers at 1.5x credit (matches rule)
TOP_N = int(os.getenv("SCAN_TOP_N", "10"))
# Hard size cap. Learning 2026-06-15: the 4-lot positions were nearly the ENTIRE
# realized loss (−$1,182 of −$999 net). Keep size small until edge is proven,
# regardless of how much room the max-loss/BPR caps leave.
MAX_CONTRACTS = int(os.getenv("SCAN_MAX_CONTRACTS", "3"))
# ── P1 safety caps (hard rejects, sized against the live account) ────────
MAX_LOSS_FRAC = float(os.getenv("SCAN_MAX_LOSS_FRAC", "0.10"))   # max loss <= 10% of net liq
BPR_CAP_FRAC = float(os.getenv("SCAN_BPR_CAP_FRAC", "0.50"))     # total BPR utilization ceiling
BPR_TARGET_LOW = float(os.getenv("SCAN_BPR_TARGET_LOW", "0.35")) # target band 35-50% (display only)
# Paper book capital — the $20k sandbox. Picks too big for the live account are
# routed to paper and sized against this (same 10% / 50% rules), so high-value
# trades still get proven before real capital ever touches them.
PAPER_CAPITAL = float(os.getenv("SCAN_PAPER_CAPITAL", "20000"))
# ── Earnings IV-crush (P3b) — the frequency engine ──────────────────────
# Defined-risk iron condor entered the day before earnings, closed the morning
# after: harvests the post-print vol collapse (implied moves overstate realized
# moves more often than not). PAPER-ONLY while it proves itself.
EC_MOVE_MULT = float(os.getenv("SCAN_EC_MOVE_MULT", "1.1"))   # shorts beyond 1.1x the implied move
EC_DTE_MAX = int(os.getenv("SCAN_EC_DTE_MAX", "12"))          # nearest expiry after the event
# Day-trade paper book: 0-1 DTE defined-risk IC on daily-expiry index ETFs,
# opened before noon ET, force-closed by 15:30 same day. PAPER-ONLY.
DAY_UNDERLYINGS = [x.strip().upper() for x in os.getenv("SCAN_DAY_UNDERLYINGS", "SPY,QQQ").split(",") if x.strip()]
DAY_POP = float(os.getenv("SCAN_DAY_POP", "0.86"))     # per-side short target (~14Δ)
DAY_LAST_ENTRY_ET = os.getenv("SCAN_DAY_LAST_ENTRY_ET", "12:00")
DAY_CLOSE_ET = os.getenv("SCAN_DAY_CLOSE_ET", "15:30")
# ── P2 structure-selection knobs ────────────────────────────────────────
# Book directional-bias proxy (NOT true greeks — streaming delta is a LATER TODO):
# each open put-vert counts +1 bull unit, call-vert -1, IC ~0, x contracts x beta.
BOOK_BIAS_BAND = float(os.getenv("SCAN_BOOK_BIAS_BAND", "1.0"))  # |bias| beyond this nudges toward neutral
# IC skew: when defensive (VIX>=elevated), push the short PUT further OTM than the call.
# Per-side POP targets for IC strikes (~12Δ shorts). NOTE: range-POP ≈
# put_pop + call_pop − 1, so per-side targets must be HIGH enough that the
# combined range clears MIN_POP (0.88+0.88−1 = 0.76 ✓; the old 0.80/0.80
# yielded 0.60 and silently rejected every IC).
IC_PUT_POP = float(os.getenv("SCAN_IC_PUT_POP", "0.88"))
IC_CALL_POP = float(os.getenv("SCAN_IC_CALL_POP", "0.88"))
IC_PUT_POP_DEFENSIVE = float(os.getenv("SCAN_IC_PUT_POP_DEF", "0.92"))  # further OTM put in skew

# ── TODO / LATER (logged, not built) ────────────────────────────────────
#  - cross-expiry EV comparison (currently takes the shortest expiry in window)
#  - Greeks/skew-aware strike selection (needs the streaming/greeks API)
#  - correlation / sector exposure caps across the book
#  - r, q (rates/dividends) in the POP model (currently r=q=0)
#  - remove dead _mid() helper
#  - P3 (next patch): macro-event calendar (CPI/FOMC/jobs), event-crush IC,
#    fold monitor/fomc.py's trigger into the opportunities "events" feed,
#    and the no-new-short-vol-within-2-days-of-an-event gate.
#  - book bias is a directional PROXY (signed vertical count × beta), not true
#    option delta — upgrade with streaming greeks when available.
#  - OI gate is a no-op until the quote payload carries open-interest (confirm
#    field name on the first live Actions run).
# A pick is "live-worthy" (route to Approve/Reject for real execution) only if it
# clears these higher bars; everything else is paper-traded to keep proving edge.
LIVE_MIN_EV_ON_BPR = float(os.getenv("SCAN_LIVE_MIN_EV_ON_BPR", "0.018"))
LIVE_MIN_IV_RANK = float(os.getenv("SCAN_LIVE_MIN_IV_RANK", "0.50"))
# New structures (call verticals, iron condors) stay PAPER until they've proven
# out in the paper book for several sessions. Flip SCAN_NEW_STRUCTURES_LIVE=1 to
# allow them to earn a LIVE tag. Put verticals (the proven core) are unaffected.
NEW_STRUCTURES_LIVE = os.getenv("SCAN_NEW_STRUCTURES_LIVE", "0") == "1"
# Long-vol mode — the MIRROR of the premium-sell scan. Instead of selling rich
# premium, flag names where IV rank is unusually LOW (vol is cheap) into a known
# catalyst (earnings) within ~2 weeks — i.e. a coming move the market may be
# UNDER-pricing. These are paper-tagged only: buying premium is not our core edge.
LONGVOL_MAX_IV_RANK = float(os.getenv("SCAN_LONGVOL_MAX_IV_RANK", "0.30"))
LONGVOL_CATALYST_DAYS = int(os.getenv("SCAN_LONGVOL_CATALYST_DAYS", "14"))
# VIX/regime overlay — stand down on NEW live risk during a vol spike / market
# stress. High *stable* IV is rich premium (good to sell); a spiking VIX means
# the market is falling — don't sell into the knife.
VIX_CALM = float(os.getenv("SCAN_VIX_CALM", "15"))
VIX_ELEVATED = float(os.getenv("SCAN_VIX_ELEVATED", "20"))
VIX_STRESS = float(os.getenv("SCAN_VIX_STRESS", "30"))
VIX_SPIKE_DAY = float(os.getenv("SCAN_VIX_SPIKE_DAY", "0.15"))


def market_regime(vix, vix_day_change_pct=None):
    """Classify the vol regime and whether to stand down on new short-premium risk.

    Returns {vix, vix_day_change_pct, level, stand_down, note}. stand_down=True
    (vol stress / spike) demotes LIVE picks to PAPER so we never open real risk
    into a crash; paper tracking continues.
    """
    if vix is None:
        return {"vix": None, "vix_day_change_pct": None, "level": "unknown",
                "stand_down": False, "note": "VIX unavailable — proceeding normally"}
    spiking = (vix_day_change_pct is not None and vix_day_change_pct >= VIX_SPIKE_DAY
               and vix >= VIX_ELEVATED)
    if vix >= VIX_STRESS or spiking:
        level, stand_down = "stress", True
    elif vix >= VIX_ELEVATED:
        level, stand_down = "elevated", False
    elif vix >= VIX_CALM:
        level, stand_down = "normal", False
    else:
        level, stand_down = "calm", False
    chg = "" if vix_day_change_pct is None else " ({:+.0%} day)".format(vix_day_change_pct)
    note = ("vol stress — standing down on new LIVE risk" if stand_down
            else "elevated vol — premium rich, proceed" if level == "elevated"
            else "{} regime".format(level))
    return {
        "vix": round(vix, 2),
        "vix_day_change_pct": round(vix_day_change_pct, 4) if vix_day_change_pct is not None else None,
        "level": level, "stand_down": stand_down, "note": note + chg,
    }


def universe():
    env = os.getenv("SCAN_UNIVERSE")
    return [s.strip().upper() for s in env.split(",") if s.strip()] if env else list(DEFAULT_UNIVERSE)


# ── Pure math ───────────────────────────────────────────────────────────
def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def expected_move(price: float, iv: float, dte: float) -> float:
    """1-sigma move over `dte` days."""
    return price * iv * math.sqrt(max(dte, 0) / 365.0)


def _d2(price, strike, iv, dte):
    t = dte / 365.0
    return (math.log(price / strike) - 0.5 * iv * iv * t) / (iv * math.sqrt(t))


def put_pop(price, strike, iv, dte):
    """Probability a short put expires OTM (a win), lognormal, r=q=0."""
    if not (price > 0 and strike > 0 and iv > 0 and dte > 0):
        return None
    return norm_cdf(_d2(price, strike, iv, dte))


def put_delta_abs(price, strike, iv, dte):
    """|delta| of the put (≈ prob ITM-ish), for reference/display."""
    if not (price > 0 and strike > 0 and iv > 0 and dte > 0):
        return None
    t = dte / 365.0
    d1 = (math.log(price / strike) + 0.5 * iv * iv * t) / (iv * math.sqrt(t))
    return norm_cdf(-d1)


def target_width(price, max_loss_cap=None):
    """Spread width scaled to price, then NARROWED to fit the account's max-loss cap.

    Base width ≈ 1.2% of price (floor MIN_WIDTH). When `max_loss_cap` ($) is given
    (10% of net liq), cap the width so a credit-floor-meeting spread can't exceed
    it: max loss ≤ width×100×(1−MIN_CREDIT_RATIO), so width ≤ cap/(100×(1−ratio)).
    Floored at MIN_WIDTH_FLOOR so small accounts get tradeable narrow spreads
    instead of nothing. (choose_strikes snaps to the nearest real strike.)
    """
    w = max(MIN_WIDTH, round(price * WIDTH_PCT))
    if max_loss_cap and max_loss_cap > 0:
        affordable = max_loss_cap / (100.0 * (1.0 - MIN_CREDIT_RATIO))
        w = min(w, affordable)
    return max(MIN_WIDTH_FLOOR, int(round(w)))


def _leg_quote(q):
    """Validate a leg's quote and return {bid,ask,mid,rel} or None (illiquid/no quote)."""
    if not q:
        return None
    bid, ask = q.get("bid"), q.get("ask")
    if bid is None or ask is None or bid <= 0 or ask < bid:
        return None
    mid = (bid + ask) / 2.0
    return {"bid": bid, "ask": ask, "mid": mid, "rel": (ask - bid) / mid if mid > 0 else 1.0}


def _leg_liquid_long(l):
    """Long (wing) leg liquidity: relative spread OK, OR absolutely tiny spread —
    a $0.05 wing quoted $0.04/$0.10 is 86% relative but trivially fillable."""
    return l["rel"] <= MAX_REL_SPREAD_LONG or (l["ask"] - l["bid"]) <= 0.10


def choose_strikes(put_strikes, price, iv, dte, target_pop=TARGET_POP, width=MIN_WIDTH):
    """Pick (short, long) put strikes: short ≈ target POP, long ≈ short − width."""
    strikes = sorted(set(float(k) for k in put_strikes))
    below = [k for k in strikes if k < price]
    if not below:
        return None
    short = min(below, key=lambda k: abs((put_pop(price, k, iv, dte) or 0.0) - target_pop))
    longs = [k for k in strikes if k < short]
    if not longs:
        return None
    target_long = short - width
    long_ = min(longs, key=lambda k: abs(k - target_long))
    if long_ >= short:
        return None
    return short, long_


def expectancy(credit, bpr, pop, manage_frac=MANAGE_FRAC, stop_mult=STOP_MULT):
    """Expected $/contract under management: win ≈ manage_frac×credit, lose ≈ stop_mult×credit."""
    win = manage_frac * credit * 100.0
    loss = stop_mult * credit * 100.0
    return round(pop * win - (1 - pop) * loss, 2)


def conviction_tag(ev_on_bpr, iv_rank, liquidity):
    """'live' = clears the higher bar for real execution; else 'paper'."""
    liquid_ok = liquidity is None or liquidity >= 2
    if ev_on_bpr >= LIVE_MIN_EV_ON_BPR and iv_rank >= LIVE_MIN_IV_RANK and liquid_ok:
        return "live"
    return "paper"


def build_candidate(underlying, expiry, dte, short, long_, short_q, long_q,
                    price, iv, iv_rank, liquidity=None, earnings_date=None,
                    short_symbol=None, long_symbol=None):
    """Assemble + score a short-put-vertical candidate using EXECUTABLE prices,
    or None if it fails the liquidity/credit/POP/EV filters.

    short_q / long_q are quote dicts {bid, ask, mark}. Credit is what you'd
    actually collect opening the spread: SELL the short put at the BID, BUY the
    long put at the ASK — not the mid. EV is net of estimated round-trip fees.
    """
    s, l = _leg_quote(short_q), _leg_quote(long_q)
    if not s or not l:
        return _no("pv: no/invalid leg quote")
    # Liquidity: short leg tight (MAX_REL_SPREAD); long leg eased (wider OTM is
    # normal and is fully paid for in exec_credit) + an open-interest floor.
    if s["rel"] > MAX_REL_SPREAD or not _leg_liquid_long(l):
        return _no("pv: spread short {:.0%}/long {:.0%}".format(s["rel"], l["rel"]))
    if not _oi_ok(short_q):
        return _no("pv: open interest below floor")
    width = round(short - long_, 2)
    exec_credit = round(s["bid"] - l["ask"], 2)   # realistic fill
    mid_credit = round(s["mid"] - l["mid"], 2)    # for reference
    if exec_credit <= 0 or width <= 0:
        return _no("pv: exec credit {:.2f} <= 0".format(exec_credit))
    if exec_credit / width < MIN_CREDIT_RATIO:
        return _no("pv: credit/width {:.2f} < {:.2f}".format(exec_credit / width, MIN_CREDIT_RATIO))
    pop = put_pop(price, short, iv, dte)
    if pop is None or not (MIN_POP <= pop <= MAX_POP):
        return _no("pv: pop {} outside {:.0%}-{:.0%}".format(
            "{:.0%}".format(pop) if pop is not None else "n/a", MIN_POP, MAX_POP))
    bpr = round((width - exec_credit) * 100.0, 2)
    if bpr <= 0:
        return _no("pv: bpr <= 0")
    max_loss = bpr   # a vertical's max loss == its BPR
    ev = round(expectancy_capped(exec_credit, pop, max_loss) - FEES_PER_SPREAD, 2)
    if ev <= 0:
        return _no("pv: EV {:+.2f} <= 0 after fees".format(ev))
    ev_on_bpr = round(ev / bpr, 4)
    return {
        "underlying": underlying,
        "structure": "short_put_vertical",
        "expiry": expiry,
        "dte": dte,
        "short_strike": short,
        "long_strike": long_,
        "short_symbol": short_symbol,
        "long_symbol": long_symbol,
        "width": width,
        "credit": exec_credit,
        "mid_credit": mid_credit,
        "fees_est": FEES_PER_SPREAD,
        "bpr": bpr,
        "max_loss": max_loss,
        "pop": round(pop, 3),
        "short_delta": round(put_delta_abs(price, short, iv, dte) or 0.0, 3),
        "short_spread_pct": round(s["rel"], 3),
        "credit_to_bpr": round(exec_credit * 100.0 / bpr, 3),
        "ev_per_contract": ev,
        "ev_on_bpr": ev_on_bpr,
        "iv": round(iv, 4),
        "iv_rank": round(iv_rank, 3),
        "underlying_price": round(price, 2),
        "liquidity": liquidity,
        "earnings_date": earnings_date,
        "tag": conviction_tag(ev_on_bpr, iv_rank, liquidity),
    }


def _oi_ok(q):
    """P4 liquidity floor on open interest. Pass if OI unknown (field not yet in
    the quote payload — confirm on first live run); reject only if known and thin."""
    if not q:
        return False
    oi = q.get("open_interest", q.get("oi"))
    if oi is None:
        return True
    try:
        return float(oi) >= MIN_OPEN_INTEREST
    except (TypeError, ValueError):
        return True


def choose_call_strikes(call_strikes, price, iv, dte, target_pop=TARGET_POP, width=MIN_WIDTH):
    """Pick (short, long) CALL strikes: short ≈ target POP above spot, long ≈ short + width."""
    strikes = sorted(set(float(k) for k in call_strikes))
    above = [k for k in strikes if k > price]
    if not above:
        return None
    short = min(above, key=lambda k: abs((call_pop(price, k, iv, dte) or 0.0) - target_pop))
    longs = [k for k in strikes if k > short]
    if not longs:
        return None
    long_ = min(longs, key=lambda k: abs(k - (short + width)))
    if long_ <= short:
        return None
    return short, long_


def build_call_vertical(underlying, expiry, dte, short, long_, short_q, long_q,
                        price, iv, iv_rank, liquidity=None, earnings_date=None,
                        short_symbol=None, long_symbol=None):
    """Short CALL vertical (mirror of the put builder). SELL short call at BID, BUY
    long call at ASK. Wins if price stays BELOW the short call. EV net of fees."""
    s, l = _leg_quote(short_q), _leg_quote(long_q)
    if not s or not l:
        return _no("cv: no/invalid leg quote")
    if s["rel"] > MAX_REL_SPREAD or not _leg_liquid_long(l) or not _oi_ok(short_q):
        return _no("cv: liquidity (spread/OI)")
    width = round(long_ - short, 2)
    exec_credit = round(s["bid"] - l["ask"], 2)
    mid_credit = round(s["mid"] - l["mid"], 2)
    if exec_credit <= 0 or width <= 0 or exec_credit / width < MIN_CREDIT_RATIO:
        return _no("cv: credit {:.2f} / width {:.2f} below floor".format(exec_credit, width))
    pop = call_pop(price, short, iv, dte)
    if pop is None or not (MIN_POP <= pop <= MAX_POP):
        return _no("cv: pop {} outside band".format("{:.0%}".format(pop) if pop is not None else "n/a"))
    max_loss = max_loss_vertical(width, exec_credit)
    bpr = max_loss
    if bpr <= 0:
        return _no("cv: bpr <= 0")
    ev = round(expectancy_capped(exec_credit, pop, max_loss) - FEES_PER_SPREAD, 2)
    if ev <= 0:
        return _no("cv: EV {:+.2f} <= 0 after fees".format(ev))
    ev_on_bpr = round(ev / bpr, 4)
    return {
        "underlying": underlying, "structure": "short_call_vertical",
        "expiry": expiry, "dte": dte, "short_strike": short, "long_strike": long_,
        "short_symbol": short_symbol, "long_symbol": long_symbol, "width": width,
        "credit": exec_credit, "mid_credit": mid_credit, "fees_est": FEES_PER_SPREAD,
        "bpr": bpr, "max_loss": max_loss, "pop": round(pop, 3),
        "short_delta": round(call_delta_abs(price, short, iv, dte) or 0.0, 3),
        "short_spread_pct": round(s["rel"], 3),
        "credit_to_bpr": round(exec_credit * 100.0 / bpr, 3),
        "ev_per_contract": ev, "ev_on_bpr": ev_on_bpr,
        "iv": round(iv, 4), "iv_rank": round(iv_rank, 3), "underlying_price": round(price, 2),
        "liquidity": liquidity, "earnings_date": earnings_date,
        "tag": conviction_tag(ev_on_bpr, iv_rank, liquidity),
    }


def build_iron_condor(underlying, expiry, dte, put_short, put_long, call_short, call_long,
                      pq_s, pq_l, cq_s, cq_l, price, iv, iv_rank,
                      liquidity=None, earnings_date=None, symbols=None):
    """Iron condor = short put vertical + short call vertical, same expiry.
    total credit = both executable credits; range-bound POP via the lognormal model;
    max loss = (single-side width − total credit) × 100 (only one side can breach)."""
    ps, pl, cs, cl = (_leg_quote(pq_s), _leg_quote(pq_l), _leg_quote(cq_s), _leg_quote(cq_l))
    if not all((ps, pl, cs, cl)):
        return _no("ic: missing leg quote")
    # gate the two SHORT legs (premium drivers) on spread + OI
    if ps["rel"] > MAX_REL_SPREAD or cs["rel"] > MAX_REL_SPREAD:
        return _no("ic: short-leg spread too wide")
    if not (_oi_ok(pq_s) and _oi_ok(cq_s)):
        return _no("ic: open interest below floor")
    put_width = round(put_short - put_long, 2)
    call_width = round(call_long - call_short, 2)
    width = max(put_width, call_width)            # equal wings assumed; use the larger
    put_credit = round(ps["bid"] - pl["ask"], 2)
    call_credit = round(cs["bid"] - cl["ask"], 2)
    total_credit = round(put_credit + call_credit, 2)
    if put_credit <= 0 or call_credit <= 0 or width <= 0:
        return _no("ic: a side has no exec credit")
    if total_credit / width < MIN_CREDIT_RATIO:
        return _no("ic: credit/width {:.2f} < {:.2f}".format(total_credit / width, MIN_CREDIT_RATIO))
    pop = ic_range_pop(price, put_short, call_short, iv, dte)
    if pop is None or not (MIN_POP <= pop <= MAX_POP):
        return _no("ic: range pop {} outside band".format("{:.0%}".format(pop) if pop is not None else "n/a"))
    max_loss = max_loss_ic(width, total_credit)
    bpr = max_loss
    if bpr <= 0:
        return _no("ic: bpr <= 0")
    ev = round(expectancy_capped(total_credit, pop, max_loss) - FEES_PER_SPREAD, 2)
    if ev <= 0:
        return _no("ic: EV {:+.2f} <= 0 after fees".format(ev))
    ev_on_bpr = round(ev / bpr, 4)
    symbols = symbols or {}
    return {
        "underlying": underlying, "structure": "iron_condor",
        "expiry": expiry, "dte": dte,
        "put_short_strike": put_short, "put_long_strike": put_long,
        "call_short_strike": call_short, "call_long_strike": call_long,
        # legacy fields so the dashboard/paper book (built for verticals) still render
        "short_strike": put_short, "long_strike": call_short,
        "symbols": symbols, "width": width,
        "credit": total_credit, "put_credit": put_credit, "call_credit": call_credit,
        "fees_est": FEES_PER_SPREAD, "bpr": bpr, "max_loss": max_loss, "pop": round(pop, 3),
        "put_short_delta": round(put_delta_abs(price, put_short, iv, dte) or 0.0, 3),
        "call_short_delta": round(call_delta_abs(price, call_short, iv, dte) or 0.0, 3),
        "credit_to_bpr": round(total_credit * 100.0 / bpr, 3),
        "ev_per_contract": ev, "ev_on_bpr": ev_on_bpr,
        "iv": round(iv, 4), "iv_rank": round(iv_rank, 3), "underlying_price": round(price, 2),
        "liquidity": liquidity, "earnings_date": earnings_date,
        "tag": conviction_tag(ev_on_bpr, iv_rank, liquidity),
    }


def reasoning_for(c, trend=None, book_bias=None):
    """Plain-English why-string for an opportunity (P5)."""
    st = c.get("structure")
    name = {"short_put_vertical": "short put vertical",
            "short_call_vertical": "short call vertical",
            "iron_condor": "iron condor"}.get(st, st)
    if st == "iron_condor":
        why = "neutral — defined-risk both sides"
        if book_bias:
            why = "neutral (book bias {:+.0f} → balance)".format(book_bias)
        strikes = "{:g}/{:g}p + {:g}/{:g}c".format(
            c.get("put_short_strike", 0), c.get("put_long_strike", 0),
            c.get("call_short_strike", 0), c.get("call_long_strike", 0))
    elif st == "short_call_vertical":
        why = "bearish lean" if trend == "bearish" else "book balance (reduce long delta)"
        strikes = "{:g}/{:g}c".format(c.get("short_strike", 0), c.get("long_strike", 0))
    else:
        why = "bullish lean" if trend == "bullish" else "rich premium"
        strikes = "{:g}/{:g}p".format(c.get("short_strike", 0), c.get("long_strike", 0))
    n = c.get("contracts", 1)
    return (
        "{name} {strikes} ×{n} — {why}. Edge: IV rank {ivr:.0%}, EV ${ev:+.0f}/ctr "
        "({evb:+.1%} on BPR). POP {pop:.0%} · credit ${cr:.2f} · max loss ${ml:.0f} · "
        "BPR ${bpr:.0f} · {dte} DTE. Manage: take 50% / cut 1.5× / exit 21 DTE / no earnings."
    ).format(name=name, strikes=strikes, n=n, why=why, ivr=c.get("iv_rank", 0),
             ev=c.get("ev_per_contract", 0), evb=c.get("ev_on_bpr", 0), pop=c.get("pop", 0),
             cr=c.get("credit", 0), ml=c.get("max_loss", c.get("bpr", 0)),
             bpr=c.get("bpr", 0) * n, dte=c.get("dte", 0))


def rank_opportunities(candidates, top_n=TOP_N):
    """Best expected return on capital first; tie-break on IV rank then POP.

    Uses `rank_score` (ev_on_bpr × learned bucket multiplier) when present, so the
    learning loop can favor/downweight buckets; falls back to raw ev_on_bpr."""
    return sorted(
        candidates,
        key=lambda c: (c.get("rank_score", c["ev_on_bpr"]), c["iv_rank"], c["pop"]),
        reverse=True,
    )[:top_n]


# ── P2: multi-structure math (call verticals, iron condors) ─────────────
def call_pop(price, strike, iv, dte):
    """P a short CALL expires OTM (price stays BELOW the short strike) = a win."""
    if not (price > 0 and strike > 0 and iv > 0 and dte > 0):
        return None
    return norm_cdf(-_d2(price, strike, iv, dte))


def call_delta_abs(price, strike, iv, dte):
    """|delta| of the call (for reference/strike picking)."""
    if not (price > 0 and strike > 0 and iv > 0 and dte > 0):
        return None
    t = dte / 365.0
    d1 = (math.log(price / strike) + 0.5 * iv * iv * t) / (iv * math.sqrt(t))
    return norm_cdf(d1)


def ic_range_pop(price, put_short, call_short, iv, dte):
    """P(price finishes BETWEEN the short strikes) — the iron-condor win prob.

    = P(above short put) + P(below short call) − 1  (overlap of the two wins).
    """
    pp = put_pop(price, put_short, iv, dte)
    cp = call_pop(price, call_short, iv, dte)
    if pp is None or cp is None:
        return None
    return max(0.0, pp + cp - 1.0)


def max_loss_vertical(width, credit, contracts=1):
    """$ max loss of a vertical = (width − credit) × 100 × contracts."""
    return round((width - credit) * 100.0 * contracts, 2)


def max_loss_ic(width, total_credit, contracts=1):
    """$ max loss of an iron condor — only ONE side can be breached, so it's
    (single-side width − TOTAL credit) × 100 × contracts (assumes equal wings)."""
    return round((width - total_credit) * 100.0 * contracts, 2)


def expectancy_capped(credit, pop, max_loss_per_ct):
    """EV $/contract under management. win = 50% of credit; loss = the smaller of
    1.5× credit or the structural max loss (so narrow spreads aren't over-penalized)."""
    win = MANAGE_FRAC * credit * 100.0
    loss = min(STOP_MULT * credit * 100.0, max_loss_per_ct)
    return round(pop * win - (1 - pop) * loss, 2)


# ── P1: position sizing against the live account (hard caps) ────────────
def size_for_caps(max_loss_1ct, bpr_1ct, net_liq, used_bpr,
                  max_loss_frac=MAX_LOSS_FRAC, bpr_cap_frac=BPR_CAP_FRAC):
    """Contracts that keep max loss ≤ max_loss_frac×net_liq AND total BPR ≤
    bpr_cap_frac×net_liq. Returns 0 if even ONE contract breaches either cap
    (caller must SKIP). Returns 1 with caps un-enforced only if net_liq is unknown.
    """
    if not net_liq or net_liq <= 0:
        return 1            # no account context; downstream keeps it PAPER (caps unvalidated)
    loss_cap = max_loss_frac * net_liq
    bpr_room = bpr_cap_frac * net_liq - (used_bpr or 0.0)
    if max_loss_1ct > loss_cap or bpr_1ct > bpr_room:
        return 0            # 1 contract already breaches a hard cap -> skip the trade
    n_loss = int(loss_cap // max_loss_1ct) if max_loss_1ct > 0 else 999
    n_bpr = int(bpr_room // bpr_1ct) if bpr_1ct > 0 else 999
    return max(1, min(n_loss, n_bpr))


# ── P2: structure selection (trend + book balance + skew) ───────────────
def trend_from_mas(price, ma20, ma50):
    """Simple trend filter from price vs 20/50-day moving averages."""
    if price is None or ma20 is None or ma50 is None:
        return "mixed"
    if price > ma20 and ma20 >= ma50:
        return "bullish"
    if price < ma20 and ma20 <= ma50:
        return "bearish"
    return "mixed"


def book_directional_bias(open_trades, betas=None):
    """Beta-weighted directional bias of the open book (proxy, not true greeks).

    +1 unit per open short-put-vertical (long delta), −1 per short-call-vertical,
    0 for iron condors, scaled by contracts and beta-to-SPY (default 1.0).
    Positive = book is net long-delta. (True option delta is a LATER/streaming TODO.)
    """
    betas = betas or {}
    bias = 0.0
    for t in open_trades or []:
        if t.get("status") != "open":
            continue
        struct = (t.get("structure") or "")
        sign = 1.0 if "put" in struct else (-1.0 if "call" in struct else 0.0)
        ctr = float(t.get("contracts") or 1)
        beta = float(betas.get(t.get("underlying"), 1.0))
        bias += sign * ctr * beta
    return round(bias, 2)


def choose_structure(trend, book_bias=0.0, band=BOOK_BIAS_BAND):
    """Pick a structure: trend lean, then nudge toward neutral if the book is
    already skewed one way. bullish→put vert, bearish→call vert, mixed→IC.
    If adding the trend structure would worsen an already-large book bias, default
    to the neutral IC instead."""
    base = {"bullish": "short_put_vertical",
            "bearish": "short_call_vertical"}.get(trend, "iron_condor")
    if book_bias is not None:
        # book already long-delta and we'd add MORE long delta (put vert) -> neutralize
        if book_bias > band and base == "short_put_vertical":
            return "iron_condor"
        # book already short-delta and we'd add MORE short delta (call vert) -> neutralize
        if book_bias < -band and base == "short_call_vertical":
            return "iron_condor"
    return base


# ── Earnings IV-crush helpers ────────────────────────────────────────────
def crush_strikes(put_strikes, call_strikes, price, implied_move, mult=EC_MOVE_MULT):
    """Short strikes just beyond mult x the implied move (puts below, calls above).
    Returns (put_short, call_short) or None if the chain can't reach."""
    if not implied_move or implied_move <= 0:
        return None
    lo, hi = price - mult * implied_move, price + mult * implied_move
    puts = sorted(float(k) for k in put_strikes if float(k) <= lo)
    calls = sorted(float(k) for k in call_strikes if float(k) >= hi)
    if not puts or not calls:
        return None
    return puts[-1], calls[0]


# ── Long-vol mode (mirror of the premium-sell scan) ─────────────────────
def _days_until(date_iso, today_iso):
    """Whole days from today to a YYYY-MM-DD date, or None if unparseable."""
    try:
        return (date.fromisoformat(date_iso[:10]) - date.fromisoformat(today_iso[:10])).days
    except (ValueError, TypeError):
        return None


def long_vol_candidate(underlying, iv_rank, earnings_date, price, today,
                       iv=None, max_iv_rank=LONGVOL_MAX_IV_RANK,
                       catalyst_days=LONGVOL_CATALYST_DAYS):
    """Flag a LONG-volatility setup: cheap IV (low IV rank) into a near catalyst.

    The disciplined "price will move, direction unknown" play — buy a defined-risk
    strangle when vol is cheap AND a known event (earnings within ~catalyst_days)
    is likely to produce a move the market may be under-pricing. Returns a
    candidate dict or None. Paper-tagged: long premium is not our core edge.
    """
    if iv_rank is None or iv_rank > max_iv_rank:
        return None
    days = _days_until(earnings_date, today) if earnings_date else None
    if days is None or days < 0 or days > catalyst_days:
        return None
    exp_move = exp_move_pct = None
    if iv and price:
        em = expected_move(price, iv, max(days, 1))   # ~1σ move by the catalyst
        if em is not None:
            exp_move = round(em, 2)
            exp_move_pct = round(em / price, 4)
    return {
        "underlying": underlying,
        "structure": "long_strangle",   # buy OTM call + put; debit, defined risk
        "iv_rank": round(iv_rank, 3),
        "iv": round(iv, 4) if iv else None,
        "price": price,
        "earnings_date": earnings_date,
        "days_to_catalyst": days,
        "expected_move": exp_move,
        "expected_move_pct": exp_move_pct,
        "tag": "paper",                  # long premium is NOT our edge — track only
        "rationale": "IV rank {:.0%} (cheap) into earnings in {}d — market may be "
                     "under-pricing the move".format(iv_rank, days),
    }


def rank_long_vol(cands):
    """Cheapest vol into the soonest catalyst first."""
    return sorted(cands, key=lambda c: (c["iv_rank"], c["days_to_catalyst"]))


# ── Live data fetch (defensive; uses the client's OAuth2 + _get) ────────
def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def fetch_metrics(client, symbols):
    """{symbol: {iv, iv_rank, liquidity, earnings_date}} from /market-metrics."""
    out = {}
    try:
        data = client._get("/market-metrics", params={"symbols": ",".join(symbols)})
        items = data.get("data", {}).get("items", [])
    except Exception as e:  # noqa: BLE001
        log.warning("market-metrics fetch failed: %s", e)
        return out
    for it in items:
        sym = it.get("symbol")
        if not sym:
            continue
        iv_rank = _f(it.get("implied-volatility-index-rank")
                     or it.get("tw-implied-volatility-index-rank")
                     or it.get("tos-implied-volatility-index-rank"))
        if iv_rank is not None and iv_rank > 1.5:
            iv_rank = iv_rank / 100.0  # normalize percent -> fraction
        earnings = (it.get("earnings") or {}).get("expected-report-date")
        out[sym] = {
            "iv": _f(it.get("implied-volatility-index")),
            "iv_rank": iv_rank,
            "liquidity": it.get("liquidity-rating") or it.get("liquidity-rank"),
            "earnings_date": earnings,
        }
    return out


def fetch_equity_prices(client, symbols):
    out = {}
    try:
        data = client._get("/market-data/by-type", params={"equity": ",".join(symbols)})
        items = data.get("data", {}).get("items", [])
    except Exception as e:  # noqa: BLE001
        log.warning("equity price fetch failed: %s", e)
        return out
    for it in items:
        sym = it.get("symbol")
        mark = _f(it.get("mark")) or _f(it.get("last"))
        if mark is None:
            bid, ask = _f(it.get("bid")), _f(it.get("ask"))
            mark = (bid + ask) / 2 if (bid and ask) else None
        if sym and mark:
            out[sym] = mark
    return out


def fetch_chain_expiration(client, symbol, dte_min=DTE_MIN, dte_max=DTE_MAX):
    """Return (expiration_date, dte, puts{strike:sym}, calls{strike:sym}) in the DTE window."""
    try:
        data = client._get("/option-chains/{}/nested".format(symbol))
        items = data.get("data", {}).get("items", [])
    except Exception as e:  # noqa: BLE001
        log.warning("chain fetch failed for %s: %s", symbol, e)
        return None
    expirations = items[0].get("expirations", []) if items else []
    best = None
    for exp in expirations:
        dte = int(_f(exp.get("days-to-expiration")) or -1)
        if dte_min <= dte <= dte_max:
            if best is None or dte < best[1]:
                puts, calls = {}, {}
                for s in exp.get("strikes", []):
                    k = _f(s.get("strike-price"))
                    if not k:
                        continue
                    if s.get("put"):
                        puts[k] = s["put"]
                    if s.get("call"):
                        calls[k] = s["call"]
                best = (exp.get("expiration-date"), dte, puts, calls)
    return best


def fetch_trend(symbol):
    """(ma20, ma50) from daily closes via yfinance, or (None, None) on failure.
    Defensive: a miss just yields a 'mixed' trend (-> neutral IC default)."""
    try:
        import yfinance as yf
        hist = yf.Ticker(symbol).history(period="3mo", interval="1d")
        closes = hist["Close"].dropna()
        if len(closes) < 50:
            return None, None
        return float(closes.tail(20).mean()), float(closes.tail(50).mean())
    except Exception as e:  # noqa: BLE001
        log.warning("trend fetch failed for %s: %s", symbol, e)
        return None, None


def account_context(client):
    """(net_liq, used_bpr, book_bias) for sizing + structure balance.

    net_liq from the live snapshot; used_bpr + directional bias from the tracked
    open book (trades.json). All defensive — a miss yields (None, 0, 0) so the
    scan still runs (sizing then can't validate caps and everything stays PAPER).
    """
    net_liq = None
    try:
        net_liq = client.fetch_snapshot().net_liquidating_value
    except Exception as e:  # noqa: BLE001
        log.warning("account snapshot failed (sizing will stay paper): %s", e)
    open_trades = []
    try:
        book = json.loads((REPO_ROOT / "trades.json").read_text())
        open_trades = [t for t in book.get("trades", []) if t.get("status") == "open"]
    except Exception:  # noqa: BLE001
        pass
    used_bpr = round(sum(float(t.get("bpr_total") or 0) for t in open_trades), 2)
    bias = book_directional_bias(open_trades)
    return net_liq, used_bpr, bias


def _build_for_structure(client, structure, sym, expiry, dte, price, iv, m,
                         puts, calls, width, defensive=False):
    """Pick strikes + fetch quotes + build the chosen structure. Falls back to a
    put vertical (the proven core) if the chosen structure can't be built."""
    ivr, liq, earn = m["iv_rank"], m.get("liquidity"), m.get("earnings_date")

    def _pv():
        sel = choose_strikes(list(puts.keys()), price, iv, dte, width=width)
        if not sel:
            return None
        s, l = sel
        q = client.fetch_option_quotes([puts[s], puts[l]])
        if not (q.get(puts[s]) and q.get(puts[l])):
            return None
        return build_candidate(sym, expiry, dte, s, l, q[puts[s]], q[puts[l]],
                               price, iv, ivr, liq, earn, short_symbol=puts[s], long_symbol=puts[l])

    def _cv():
        if not calls:
            return None
        sel = choose_call_strikes(list(calls.keys()), price, iv, dte, width=width)
        if not sel:
            return None
        s, l = sel
        q = client.fetch_option_quotes([calls[s], calls[l]])
        if not (q.get(calls[s]) and q.get(calls[l])):
            return None
        return build_call_vertical(sym, expiry, dte, s, l, q[calls[s]], q[calls[l]],
                                   price, iv, ivr, liq, earn, short_symbol=calls[s], long_symbol=calls[l])

    def _ic():
        if not (puts and calls):
            return None
        # IC skew: push the short PUT further OTM (higher POP / lower delta) in defensive regimes.
        put_pop_t = IC_PUT_POP_DEFENSIVE if defensive else IC_PUT_POP
        psel = choose_strikes(list(puts.keys()), price, iv, dte, target_pop=put_pop_t, width=width)
        csel = choose_call_strikes(list(calls.keys()), price, iv, dte, target_pop=IC_CALL_POP, width=width)
        if not (psel and csel):
            return None
        ps_, pl_ = psel
        cs_, cl_ = csel
        legs = [puts[ps_], puts[pl_], calls[cs_], calls[cl_]]
        q = client.fetch_option_quotes(legs)
        if not all(q.get(x) for x in legs):
            return None
        return build_iron_condor(sym, expiry, dte, ps_, pl_, cs_, cl_,
                                 q[puts[ps_]], q[puts[pl_]], q[calls[cs_]], q[calls[cl_]],
                                 price, iv, ivr, liq, earn,
                                 symbols={"put_short": puts[ps_], "put_long": puts[pl_],
                                          "call_short": calls[cs_], "call_long": calls[cl_]})

    cand = {"short_put_vertical": _pv, "short_call_vertical": _cv, "iron_condor": _ic}.get(structure, _pv)()
    if cand is None and structure != "short_put_vertical":
        cand = _pv()   # fall back to the proven core
    return cand


def earnings_crush_pass(client, metrics, prices, today):
    """Build earnings IV-crush iron condors for names reporting within ~1 day.

    Enter today (day before / day of the print), close the next day; shorts just
    beyond 1.1x the implied move; sized against the $20k paper book; PAPER tag
    forced. Returns candidate dicts ready for the paper book.
    """
    out = []
    for sym, m in metrics.items():
        ed = m.get("earnings_date")
        days = _days_until(ed, today) if ed else None
        if days is None or not (0 <= days <= 1):
            continue
        price, iv = prices.get(sym), m.get("iv")
        if not price or not iv:
            continue
        exp = fetch_chain_expiration(client, sym, dte_min=1, dte_max=EC_DTE_MAX)
        if not exp:
            continue
        expiry, dte, puts, calls = exp
        if expiry and ed and str(expiry) < str(ed):
            continue   # must expire AFTER the event
        em = expected_move(price, iv, dte)
        sel = crush_strikes(puts.keys(), calls.keys(), price, em)
        if not sel:
            continue
        ps_, cs_ = sel
        w = target_width(price, max_loss_cap=MAX_LOSS_FRAC * PAPER_CAPITAL)
        pl_c = [k for k in puts if k < ps_]
        cl_c = [k for k in calls if k > cs_]
        if not pl_c or not cl_c:
            continue
        pl_ = min(pl_c, key=lambda k: abs(k - (ps_ - w)))
        cl_ = min(cl_c, key=lambda k: abs(k - (cs_ + w)))
        legs = [puts[ps_], puts[pl_], calls[cs_], calls[cl_]]
        q = client.fetch_option_quotes(legs)
        if not all(q.get(x) for x in legs):
            continue
        cand = build_iron_condor(sym, expiry, dte, ps_, pl_, cs_, cl_,
                                 q[puts[ps_]], q[puts[pl_]], q[calls[cs_]], q[calls[cl_]],
                                 price, iv, m.get("iv_rank") or 0.0, m.get("liquidity"), ed,
                                 symbols={"put_short": puts[ps_], "put_long": puts[pl_],
                                          "call_short": calls[cs_], "call_long": calls[cl_]})
        if not cand:
            log.info("crush %s rejected: %s", sym, LAST_REJECT)
            continue
        n = size_for_caps(cand["max_loss"], cand["bpr"], PAPER_CAPITAL, 0.0)
        if n == 0:
            continue
        n = min(n, MAX_CONTRACTS)   # hard size cap (Learning 2026-06-15)
        close_date = (date.fromisoformat(ed[:10]) + timedelta(days=1)).isoformat()
        cand.update({
            "tag": "paper", "event": "earnings", "sized_for": "paper",
            "contracts": n,
            "max_loss_total": round(cand["max_loss"] * n, 2),
            "bpr_total": round(cand["bpr"] * n, 2),
            "enter_date": today, "close_date": close_date,
            "reasoning": ("Earnings IV-crush: {} reports {}. Implied move ±${:.2f} ({:.1%}); "
                          "IC shorts beyond 1.1x the move ({:g}p/{:g}c), {:g}-wide, credit ${:.2f}, "
                          "max loss ${:.0f} x{}. Enter today, close {} — harvest the post-print vol "
                          "collapse. PAPER (proving the crush edge).").format(
                sym, ed, em, em / price, ps_, cs_, w, cand["credit"], cand["max_loss"], n, close_date),
        })
        out.append(cand)
    return out


def day_trade_pass(client, prices, metrics, today):
    """0-1 DTE iron condors on SPY/QQQ for the day-trade paper book.

    Only before DAY_LAST_ENTRY_ET; shorts at ~DAY_POP per side; force-closed by
    DAY_CLOSE_ET via the paper book's day_trade rule. PAPER tag always.
    """
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("America/New_York")).strftime("%H:%M")
    except Exception:  # noqa: BLE001
        return []
    if now >= DAY_LAST_ENTRY_ET:
        return []
    out = []
    for sym in DAY_UNDERLYINGS:
        price = prices.get(sym)
        iv = (metrics.get(sym) or {}).get("iv")
        if not price or not iv:
            continue
        exp = fetch_chain_expiration(client, sym, dte_min=0, dte_max=1)
        if not exp:
            continue
        expiry, dte, puts, calls = exp
        d = max(dte, 1)
        psel = choose_strikes(list(puts.keys()), price, iv, d, target_pop=DAY_POP, width=2)
        csel = choose_call_strikes(list(calls.keys()), price, iv, d, target_pop=DAY_POP, width=2)
        if not (psel and csel):
            continue
        ps_, pl_ = psel
        cs_, cl_ = csel
        legs = [puts[ps_], puts[pl_], calls[cs_], calls[cl_]]
        q = client.fetch_option_quotes(legs)
        if not all(q.get(x) for x in legs):
            continue
        cand = build_iron_condor(sym, expiry, dte, ps_, pl_, cs_, cl_,
                                 q[puts[ps_]], q[puts[pl_]], q[calls[cs_]], q[calls[cl_]],
                                 price, iv, (metrics.get(sym) or {}).get("iv_rank") or 0.0,
                                 None, None,
                                 symbols={"put_short": puts[ps_], "put_long": puts[pl_],
                                          "call_short": calls[cs_], "call_long": calls[cl_]})
        if not cand:
            log.info("day-trade %s rejected: %s", sym, LAST_REJECT)
            continue
        n = size_for_caps(cand["max_loss"], cand["bpr"], PAPER_CAPITAL, 0.0)
        if n == 0:
            continue
        n = min(n, MAX_CONTRACTS)   # hard size cap (Learning 2026-06-15)
        cand.update({"tag": "paper", "sized_for": "paper", "day_trade": True,
                     "close_after_et": DAY_CLOSE_ET, "contracts": n,
                     "max_loss_total": round(cand["max_loss"] * n, 2),
                     "bpr_total": round(cand["bpr"] * n, 2),
                     "reasoning": ("DAY TRADE (paper): {} 0-1DTE iron condor, shorts ~{:.0f}Δ "
                                   "({:g}p/{:g}c), credit ${:.2f} x{}, max loss ${:.0f}. Opened before "
                                   "{} ET, force-closed by {} ET — intraday theta harvest. NOTE: marked "
                                   "every 10 min; intraday spikes between marks aren't seen.").format(
                         sym, (1 - DAY_POP) * 100, ps_, cs_, cand["credit"], n,
                         cand["max_loss"], DAY_LAST_ENTRY_ET, DAY_CLOSE_ET)})
        out.append(cand)
    return out


def main() -> int:
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
                        stream=sys.stdout)
    from monitor.tastytrade_client import TastytradeClient

    syms = universe()
    log.info("Scanning %d underlyings (IV rank >= %.0f%%, DTE %d-%d, target POP %.0f%%)",
             len(syms), MIN_IV_RANK * 100, DTE_MIN, DTE_MAX, TARGET_POP * 100)
    client = TastytradeClient()
    metrics = fetch_metrics(client, syms)
    prices = fetch_equity_prices(client, syms)
    today = date.today().isoformat()

    # P1: account context for sizing/caps + P2 book-balance; regime up front for IC skew.
    net_liq, used_bpr, book_bias = account_context(client)
    regime = _market_regime_now()
    defensive = bool(regime.get("stand_down")) or regime.get("level") in ("elevated", "stress")
    log.info("account: net_liq=%s used_bpr=%.0f book_bias=%s · regime: %s",
             net_liq, used_bpr or 0.0, book_bias, regime.get("note"))

    # P3: macro events — the queued FOMC IV-crush IC + the pre-event blackout gate.
    from monitor import macro_calendar
    iv_ranks = {s: (metrics.get(s) or {}).get("iv_rank") for s in ("IWM", "QQQ")}
    events = []
    ev = macro_calendar.event_crush_opportunity(today, vix=regime.get("vix"), iv_ranks=iv_ranks)
    if ev:
        events.append(ev)
    blackout = macro_calendar.in_blackout(today, days_before=2)
    if blackout:
        log.info("macro blackout: scheduled event within 2 days — no NEW non-event LIVE short-vol")

    candidates, skipped = [], {}
    paper_used_bpr = 0.0   # BPR reserved inside the $20k paper book this scan
    for sym in syms:
        m = metrics.get(sym)
        price = prices.get(sym)
        if not m or m.get("iv") is None or m.get("iv_rank") is None or not price:
            skipped[sym] = "no metrics/price"
            continue
        if m["iv_rank"] < MIN_IV_RANK:
            skipped[sym] = "iv_rank {:.0%}".format(m["iv_rank"])
            continue
        exp = fetch_chain_expiration(client, sym)
        if not exp:
            skipped[sym] = "no expiry in window"
            continue
        expiry, dte, puts, calls = exp
        if m["earnings_date"] and today <= m["earnings_date"] <= (expiry or "9999"):
            skipped[sym] = "earnings {} before expiry".format(m["earnings_date"])
            continue
        # P2: structure selection — trend lean, nudged toward neutral by book balance.
        ma20, ma50 = fetch_trend(sym)
        trend = trend_from_mas(price, ma20, ma50)
        structure = choose_structure(trend, book_bias)
        # Width sized to the PAPER book's cap (the $20k sandbox can carry natural,
        # high-value spreads); live replication is gated by the live sizing below.
        cand = _build_for_structure(client, structure, sym, expiry, dte, price, m["iv"], m,
                                    puts, calls,
                                    target_width(price, max_loss_cap=MAX_LOSS_FRAC * PAPER_CAPITAL),
                                    defensive)
        if not cand:
            skipped[sym] = "failed: {}".format(LAST_REJECT or "filters")
            continue
        # P1: size against the LIVE account first; if even 1 contract breaches the
        # live caps, route it to the $20k PAPER book (sized for paper) instead of
        # skipping — high-value trades still get proven on paper.
        n = size_for_caps(cand["max_loss"], cand["bpr"], net_liq, used_bpr)
        if n > 0:
            cand["sized_for"] = "live"
        else:
            n = size_for_caps(cand["max_loss"], cand["bpr"], PAPER_CAPITAL, paper_used_bpr)
            if n == 0:
                skipped[sym] = "exceeds even paper caps"
                continue
            cand["sized_for"] = "paper"
            if cand["tag"] == "live":
                cand["tag"], cand["demoted"] = "paper", "exceeds live caps — sized for $20k paper book"
        n = min(n, MAX_CONTRACTS)   # hard size cap (Learning 2026-06-15)
        cand["contracts"] = n
        cand["max_loss_total"] = round(cand["max_loss"] * n, 2)
        cand["bpr_total"] = round(cand["bpr"] * n, 2)
        cand["trend"] = trend
        cand["sized_capped"] = net_liq is not None
        # Safety: can't validate caps without the account, OR a not-yet-proven new
        # structure -> keep it PAPER regardless of conviction (paper-validate first).
        if cand["tag"] == "live":
            if not cand["sized_capped"]:
                cand["tag"], cand["demoted"] = "paper", "caps unvalidated (no account)"
            elif cand["structure"] != "short_put_vertical" and not NEW_STRUCTURES_LIVE:
                cand["tag"], cand["demoted"] = "paper", "new structure — paper-validating"
        cand["reasoning"] = reasoning_for(cand, trend, book_bias)
        candidates.append(cand)
        if cand.get("sized_for") == "paper":
            paper_used_bpr += cand["bpr_total"]
        elif net_liq:
            used_bpr += cand["bpr_total"]

    # Long-vol pass — reuses the metrics/prices already fetched (no extra calls).
    long_vol = []
    for sym in syms:
        m = metrics.get(sym)
        if not m:
            continue
        lv = long_vol_candidate(sym, m.get("iv_rank"), m.get("earnings_date"),
                                prices.get(sym), today, iv=m.get("iv"))
        if lv:
            long_vol.append(lv)
    long_vol = rank_long_vol(long_vol)

    # P3b: earnings IV-crush pass — paper-only 1-day holds (the frequency engine).
    try:
        crush = earnings_crush_pass(client, metrics, prices, today)
    except Exception as e:  # noqa: BLE001 — never fail the scan on the crush pass
        log.warning("earnings-crush pass failed: %s", e)
        crush = []
    candidates.extend(crush)
    try:
        day = day_trade_pass(client, prices, metrics, today)
    except Exception as e:  # noqa: BLE001
        log.warning("day-trade pass failed: %s", e)
        day = []
    candidates.extend(day)
    for c in crush:
        events.append({"type": "event", "event": "earnings", "label": "Earnings IV-crush IC",
                       "underlyings": [c["underlying"]], "structure": "iron_condor",
                       "expiry": c["expiry"], "enter_date": c["enter_date"],
                       "close_date": c["close_date"], "status": "enter", "tag": "paper",
                       "reasoning": c["reasoning"]})

    # Phase 2: fold in learned realized edge. Refresh learnings from the outcomes
    # ledger and tilt each candidate's rank by its bucket multiplier (asset_class ×
    # structure × cluster). Inert until a bucket clears the sample bar (×1.00), so
    # this never acts on noise. Never fail the scan on a learn error.
    learnings = None
    try:
        from scripts import learn
        learnings = learn.refresh()
        for c in candidates:
            mult, notes = learn.candidate_multiplier(
                learnings, underlying=c.get("underlying"), structure=c.get("structure"))
            c["learn_multiplier"] = mult
            if notes:
                c["learn_notes"] = notes
            c["rank_score"] = round(c["ev_on_bpr"] * mult, 6)
    except Exception as e:  # noqa: BLE001
        log.warning("learning pass failed (ranking falls back to raw EV): %s", e)

    ranked = rank_opportunities(candidates)

    # Agentic review (Phase 4): an LLM portfolio-risk pass that reasons over the
    # whole picture and can ONLY make trades more conservative (veto / downsize),
    # never riskier. No-op without ANTHROPIC_API_KEY; never fails the scan. The
    # deterministic safety gates below still apply on top (defense in depth).
    agent_summary = None
    try:
        from monitor import agent_review
        ranked, agent_summary = agent_review.run(ranked, {
            "today": today, "regime": regime, "events": events, "learnings": learnings,
            "open_positions": _paper_open_positions(),
        })
    except Exception as e:  # noqa: BLE001
        log.warning("agent review skipped: %s", e)

    # Jay's rule: every surfaced opportunity must pass the full agentic reasoning,
    # and a LIVE recommendation requires the agent's explicit sign-off. Tag each
    # pick with whether the agent reviewed it; demote any LIVE pick the agent did
    # not approve (or couldn't review) to PAPER — never recommend live without AI.
    reviewed = agent_summary is not None
    for c in ranked:
        approved = c.get("agent_action") in ("approve", "downsize")
        c["agent_reviewed"] = bool(reviewed and "agent_action" in c)
        if c.get("tag") == "live" and not approved:
            c["tag"] = "paper"
            c["demoted"] = "awaiting AI approval" if not reviewed else "AI did not approve"

    _apply_news_gate(ranked)        # single-name shield: veto picks with a pending catalyst
    _apply_regime(ranked, regime)   # market-wide shield (regime computed up front)
    if blackout:                    # P3 pre-event gate: no NEW non-event LIVE within 2d of an event
        for c in ranked:
            if c.get("tag") == "live":
                c["tag"], c["demoted"] = "paper", "pre-event blackout (<=2d to macro event)"
    # Auto-ticket: attach a ready-to-send order spec (legs + limit + sizing + the
    # 50%/1.5x/21-DTE management plan) to every surfaced opportunity, so a pick can
    # be entered in one glance instead of hand-built leg by leg.
    try:
        from scripts import trade_ticket
        for c in ranked:
            c.setdefault("net_liq", net_liq)   # so the ticket can flag live-cap fit
            c["ticket"] = trade_ticket.build_ticket(c)
    except Exception as e:  # noqa: BLE001 — never fail the scan on ticket rendering
        log.warning("ticket build failed: %s", e)
    _write(ranked, candidates, skipped, regime, long_vol, events, learnings, agent_summary)
    _alert_live([c for c in ranked if c.get("tag") == "live"])
    if regime.get("stand_down"):
        _alert_regime(regime)
    log.info("Scan done: %d candidates, top %d ranked, %d skipped, %d long-vol, %d events",
             len(candidates), len(ranked), len(skipped), len(long_vol), len(events))
    return 0


def _paper_open_positions():
    """Open positions in the paper book — context for the agentic review."""
    try:
        book = json.loads((REPO_ROOT / "paper" / "book.json").read_text())
        return [t for t in book.get("trades", []) if t.get("status") == "open"]
    except Exception:  # noqa: BLE001
        return []


def _open_sigs():
    """Signatures of positions already being tracked (so we don't re-alert them)."""
    try:
        book = json.loads((REPO_ROOT / "paper" / "book.json").read_text())
        return {"{}_{:g}_{:g}_{}".format(t.get("underlying"), t.get("short_strike"),
                                         t.get("long_strike"), t.get("expiry"))
                for t in book.get("trades", []) if t.get("status") == "open"}
    except Exception:  # noqa: BLE001
        return set()


def _market_regime_now():
    """Fetch VIX and classify the regime (graceful if VIX is unavailable)."""
    try:
        from monitor.market_data import get_vix
        v = get_vix()
        if not v:
            return market_regime(None, None)
        return market_regime(v.current, v.day_change_pct)
    except Exception as e:  # noqa: BLE001
        log.warning("regime fetch failed: %s", e)
        return market_regime(None, None)


def _apply_regime(ranked, regime):
    """In a vol-stress regime, demote every LIVE pick to PAPER (no new real risk)."""
    if not regime.get("stand_down"):
        return
    for c in ranked:
        if c.get("tag") == "live":
            c["tag"] = "paper"
            c["demoted"] = "vol stress"
    log.info("regime stand-down (%s): all LIVE picks demoted to PAPER", regime.get("level"))


def _alert_regime(regime):
    try:
        from monitor import notifier
        notifier.send(
            title="⚠️ Vol stress — standing down",
            message="VIX {} {} · no new LIVE setups until vol settles (paper tracking continues).".format(
                regime.get("vix"),
                "({:+.0%} day)".format(regime["vix_day_change_pct"]) if regime.get("vix_day_change_pct") is not None else ""),
            priority=notifier.PRIORITY_NORMAL,
        )
    except Exception as e:  # noqa: BLE001
        log.warning("regime alert failed: %s", e)


def _apply_news_gate(ranked):
    """Check recent news on each ranked pick; flag risk and demote LIVE->PAPER on a veto."""
    try:
        from monitor.news_risk import assess_symbol
    except Exception as e:  # noqa: BLE001
        log.warning("news gate unavailable: %s", e)
        return
    for c in ranked:
        try:
            v = assess_symbol(c["underlying"])
        except Exception as e:  # noqa: BLE001
            log.warning("news gate failed for %s: %s", c.get("underlying"), e)
            continue
        c["news_risk"] = {"level": v["level"], "hits": v.get("hits", [])}
        if v["level"] == "veto" and c.get("tag") == "live":
            c["tag"] = "paper"
            c["demoted"] = "news veto"
            log.info("news veto: %s demoted LIVE->PAPER (%s)", c["underlying"],
                     v["hits"][0]["keyword"] if v.get("hits") else "catalyst")


def _alert_live(live):
    """Pushover digest of high-conviction picks for you to open (+ set GTC 50%)."""
    if not live:
        return
    open_sigs = _open_sigs()
    fresh = [c for c in live
             if "{}_{:g}_{:g}_{}".format(c["underlying"], c["short_strike"],
                                         c["long_strike"], c["expiry"]) not in open_sigs]
    if not fresh:
        return
    lines = ["{} {:g}/{:g}p · ${:.2f} cr · POP {:.0%} · IVR {:.0%} · BPR ${:.0f}".format(
        c["underlying"], c["short_strike"], c["long_strike"], c["credit"],
        c["pop"], c["iv_rank"], c["bpr"]) for c in fresh]
    try:
        from monitor import notifier
        notifier.send(
            title="📈 {} setup{} to open".format(len(fresh), "s" if len(fresh) > 1 else ""),
            message="Open these + set GTC close at 50%:\n" + "\n".join(lines),
            priority=notifier.PRIORITY_NORMAL,
        )
    except Exception as e:  # noqa: BLE001 — never fail the scan on a notify error
        log.warning("scan alert failed: %s", e)


def _mid(q):
    b, a = q.get("bid"), q.get("ask")
    return (b + a) / 2 if (b is not None and a is not None) else None


def _write(ranked, candidates, skipped, regime=None, long_vol=None, events=None,
           learnings=None, agent=None):
    SCAN_DIR.mkdir(parents=True, exist_ok=True)
    long_vol = long_vol or []
    # Compact learnings summary for the dashboards (full detail in memory/learnings.*).
    learn_summary = None
    if learnings:
        learn_summary = {"global": learnings.get("global", {}),
                         "min_sample": learnings.get("params", {}).get("min_sample"),
                         "actionable": [
                             {"dim": dim, "value": v, "multiplier": b.get("multiplier"),
                              "recommendation": b.get("recommendation"), "n": b.get("n")}
                             for dim, bs in learnings.get("buckets", {}).items()
                             for v, b in bs.items() if b.get("actionable")]}
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "regime": regime or {},
        "params": {"min_iv_rank": MIN_IV_RANK, "dte_min": DTE_MIN, "dte_max": DTE_MAX,
                   "target_pop": TARGET_POP, "width_pct": WIDTH_PCT, "min_width": MIN_WIDTH,
                   "longvol_max_iv_rank": LONGVOL_MAX_IV_RANK, "longvol_catalyst_days": LONGVOL_CATALYST_DAYS},
        "top": ranked,
        "long_vol": long_vol,
        "events": events or [],   # P3 macro-event / FOMC crush setups
        "learnings": learn_summary,   # Phase 2: realized edge by bucket (null until data)
        "agent": agent,           # Phase 4: LLM portfolio-risk review (null if disabled)
        "all_candidates": candidates,
        "skipped": skipped,
    }
    (SCAN_DIR / "opportunities.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

    reg = " · regime: {}".format(regime["note"]) if regime and regime.get("note") else ""
    lines = ["# Opportunity scan", "",
             "_Generated {} · short put verticals ranked by expected return on BPR{}._".format(payload["generated_at"], reg),
             "", "| # | Trade | Tag | DTE | Credit | BPR | POP | Cr/BPR | EV/ctr | EV/BPR | IVR |",
             "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for i, c in enumerate(ranked, 1):
        lines.append("| {} | {} {:g}/{:g}p | {} | {} | ${:.2f} | ${:.0f} | {:.0%} | {:.0%} | ${:+.0f} | {:.1%} | {:.0%} |".format(
            i, c["underlying"], c["short_strike"], c["long_strike"], c.get("tag", "paper").upper(),
            c["dte"], c["credit"], c["bpr"], c["pop"], c["credit_to_bpr"], c["ev_per_contract"],
            c["ev_on_bpr"], c["iv_rank"]))
    if not ranked:
        lines.append("| — | _no setups passed filters_ | | | | | | | | | |")

    # Macro events — scheduled-event crush setups (e.g. the queued FOMC IC).
    if events:
        lines += ["", "## Macro events · scheduled-event crush setups",
                  "", "| Event | Setup | Status | Tag | Enter | Close | Notes |",
                  "|---|---|---|---|---|---|---|"]
        for e in events:
            lines.append("| {} | {} {} {} | {} | {} | {} | {} | {} |".format(
                e.get("event", ""), "/".join(e.get("underlyings", [])), e.get("structure", ""),
                e.get("expiry", ""), e.get("status", ""), e.get("tag", "").upper(),
                e.get("enter_date", ""), e.get("close_date", ""), e.get("reasoning", "")))

    # Long-vol watch — cheap IV into a near catalyst (paper / awareness only).
    lines += ["", "## Long-vol watch · cheap IV into a catalyst (paper only)",
              "", "| Underlying | IVR | Earnings | In | ~1σ move | Note |",
              "|---|---:|---|---:|---:|---|"]
    for c in long_vol:
        em = "{:.1%}".format(c["expected_move_pct"]) if c.get("expected_move_pct") is not None else "—"
        lines.append("| {} | {:.0%} | {} | {}d | {} | {} |".format(
            c["underlying"], c["iv_rank"], c.get("earnings_date") or "—",
            c["days_to_catalyst"], em, c["rationale"]))
    if not long_vol:
        lines.append("| — | _no cheap-IV catalysts in window_ | | | | |")
    (SCAN_DIR / "summary.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
