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
from datetime import date, datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_DIR = REPO_ROOT / "scan"

log = logging.getLogger("scan")

# ── Tunables (env-overridable) ──────────────────────────────────────────
# A curated liquid, optionable universe. Override with SCAN_UNIVERSE="A,B,C".
DEFAULT_UNIVERSE = [
    "SPY", "QQQ", "IWM", "DIA", "GLD", "SLV", "TLT", "XLF", "XLE", "XLK",
    "AAPL", "MSFT", "AMZN", "GOOGL", "META", "NVDA", "AMD", "TSLA", "NFLX",
    "JPM", "BAC", "WFC", "GS", "V", "MA", "DIS", "KO", "PEP", "WMT", "COST",
    "XOM", "CVX", "PFE", "MRK", "INTC", "CSCO", "ORCL", "CRM", "BA", "CAT",
]
MIN_IV_RANK = float(os.getenv("SCAN_MIN_IV_RANK", "0.30"))   # only rich premium
DTE_MIN = int(os.getenv("SCAN_DTE_MIN", "30"))
DTE_MAX = int(os.getenv("SCAN_DTE_MAX", "50"))
TARGET_POP = float(os.getenv("SCAN_TARGET_POP", "0.80"))     # ~0.20Δ short put
MIN_POP = float(os.getenv("SCAN_MIN_POP", "0.70"))
MAX_POP = float(os.getenv("SCAN_MAX_POP", "0.90"))
WIDTH_PCT = float(os.getenv("SCAN_WIDTH_PCT", "0.012"))      # spread width ≈ 1.2% of price
MIN_WIDTH = float(os.getenv("SCAN_MIN_WIDTH", "5"))          # floor width ($)
MIN_CREDIT_RATIO = float(os.getenv("SCAN_MIN_CREDIT_RATIO", "0.15"))  # exec credit / width
FEES_PER_SPREAD = float(os.getenv("SCAN_FEES_PER_SPREAD", "3.0"))     # est. open+close commissions/fees
MAX_REL_SPREAD = float(os.getenv("SCAN_MAX_REL_SPREAD", "0.20"))      # leg bid/ask tightness (liquidity gate)
MANAGE_FRAC = float(os.getenv("SCAN_MANAGE_FRAC", "0.5"))    # take profit at 50%
STOP_MULT = float(os.getenv("SCAN_STOP_MULT", "1.5"))        # cut losers at 1.5x credit (matches rule)
TOP_N = int(os.getenv("SCAN_TOP_N", "10"))
# A pick is "live-worthy" (route to Approve/Reject for real execution) only if it
# clears these higher bars; everything else is paper-traded to keep proving edge.
LIVE_MIN_EV_ON_BPR = float(os.getenv("SCAN_LIVE_MIN_EV_ON_BPR", "0.018"))
LIVE_MIN_IV_RANK = float(os.getenv("SCAN_LIVE_MIN_IV_RANK", "0.50"))
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


def target_width(price):
    """Spread width scaled to price (so $5 isn't noise on an $800 name)."""
    return max(MIN_WIDTH, round(price * WIDTH_PCT))


def _leg_quote(q):
    """Validate a leg's quote and return {bid,ask,mid,rel} or None (illiquid/no quote)."""
    if not q:
        return None
    bid, ask = q.get("bid"), q.get("ask")
    if bid is None or ask is None or bid <= 0 or ask < bid:
        return None
    mid = (bid + ask) / 2.0
    return {"bid": bid, "ask": ask, "mid": mid, "rel": (ask - bid) / mid if mid > 0 else 1.0}


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
        return None
    # Liquidity gate on the SHORT leg (the premium driver); the long leg's wider
    # relative spread is normal and is already fully paid for in exec_credit below.
    if s["rel"] > MAX_REL_SPREAD:
        return None
    width = round(short - long_, 2)
    exec_credit = round(s["bid"] - l["ask"], 2)   # realistic fill
    mid_credit = round(s["mid"] - l["mid"], 2)    # for reference
    if exec_credit <= 0 or width <= 0:
        return None
    if exec_credit / width < MIN_CREDIT_RATIO:
        return None
    pop = put_pop(price, short, iv, dte)
    if pop is None or not (MIN_POP <= pop <= MAX_POP):
        return None
    bpr = round((width - exec_credit) * 100.0, 2)
    if bpr <= 0:
        return None
    ev = round(expectancy(exec_credit, bpr, pop) - FEES_PER_SPREAD, 2)
    if ev <= 0:
        return None
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


def rank_opportunities(candidates, top_n=TOP_N):
    """Best expected return on capital first; tie-break on IV rank then POP."""
    return sorted(
        candidates,
        key=lambda c: (c["ev_on_bpr"], c["iv_rank"], c["pop"]),
        reverse=True,
    )[:top_n]


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
    """Return (expiration_date, dte, {strike_price: put_option_symbol}) in the DTE window."""
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
                puts = {}
                for s in exp.get("strikes", []):
                    k = _f(s.get("strike-price"))
                    put_sym = s.get("put")
                    if k and put_sym:
                        puts[k] = put_sym
                best = (exp.get("expiration-date"), dte, puts)
    return best


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

    candidates, skipped = [], {}
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
        expiry, dte, puts = exp
        if m["earnings_date"] and today <= m["earnings_date"] <= (expiry or "9999"):
            skipped[sym] = "earnings {} before expiry".format(m["earnings_date"])
            continue
        sel = choose_strikes(list(puts.keys()), price, m["iv"], dte, width=target_width(price))
        if not sel:
            skipped[sym] = "no strikes"
            continue
        short, long_ = sel
        quotes = client.fetch_option_quotes([puts[short], puts[long_]])
        sm = quotes.get(puts[short])
        lm = quotes.get(puts[long_])
        if not sm or not lm:
            skipped[sym] = "no option quotes"
            continue
        cand = build_candidate(sym, expiry, dte, short, long_, sm, lm,
                               price, m["iv"], m["iv_rank"], m.get("liquidity"), m.get("earnings_date"),
                               short_symbol=puts[short], long_symbol=puts[long_])
        if cand:
            candidates.append(cand)
        else:
            skipped[sym] = "failed filters"

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

    ranked = rank_opportunities(candidates)
    _apply_news_gate(ranked)        # single-name shield: veto picks with a pending catalyst
    regime = _market_regime_now()   # market-wide shield: stand down in a vol spike
    _apply_regime(ranked, regime)
    log.info("market regime: %s", regime["note"])
    _write(ranked, candidates, skipped, regime, long_vol)
    _alert_live([c for c in ranked if c.get("tag") == "live"])
    if regime.get("stand_down"):
        _alert_regime(regime)
    log.info("Scan done: %d candidates, top %d ranked, %d skipped, %d long-vol",
             len(candidates), len(ranked), len(skipped), len(long_vol))
    return 0


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


def _write(ranked, candidates, skipped, regime=None, long_vol=None):
    SCAN_DIR.mkdir(parents=True, exist_ok=True)
    long_vol = long_vol or []
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "regime": regime or {},
        "params": {"min_iv_rank": MIN_IV_RANK, "dte_min": DTE_MIN, "dte_max": DTE_MAX,
                   "target_pop": TARGET_POP, "width_pct": WIDTH_PCT, "min_width": MIN_WIDTH,
                   "longvol_max_iv_rank": LONGVOL_MAX_IV_RANK, "longvol_catalyst_days": LONGVOL_CATALYST_DAYS},
        "top": ranked,
        "long_vol": long_vol,
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
