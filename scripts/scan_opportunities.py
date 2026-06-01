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
WIDTH = float(os.getenv("SCAN_WIDTH", "5"))                  # spread width ($)
MIN_CREDIT_RATIO = float(os.getenv("SCAN_MIN_CREDIT_RATIO", "0.15"))  # credit/width
MANAGE_FRAC = float(os.getenv("SCAN_MANAGE_FRAC", "0.5"))    # take profit at 50%
STOP_MULT = float(os.getenv("SCAN_STOP_MULT", "1.5"))        # cut losers at 1.5x credit (matches rule)
TOP_N = int(os.getenv("SCAN_TOP_N", "10"))


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


def choose_strikes(put_strikes, price, iv, dte, target_pop=TARGET_POP, width=WIDTH):
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


def build_candidate(underlying, expiry, dte, short, long_, short_mark, long_mark,
                    price, iv, iv_rank, liquidity=None, earnings_date=None):
    """Assemble + score one short-put-vertical candidate, or None if it fails filters."""
    credit = round(short_mark - long_mark, 2)
    width = round(short - long_, 2)
    if credit <= 0 or width <= 0:
        return None
    if credit / width < MIN_CREDIT_RATIO:
        return None
    pop = put_pop(price, short, iv, dte)
    if pop is None or not (MIN_POP <= pop <= MAX_POP):
        return None
    bpr = round((width - credit) * 100.0, 2)
    if bpr <= 0:
        return None
    ev = expectancy(credit, bpr, pop)
    if ev <= 0:
        return None
    return {
        "underlying": underlying,
        "structure": "short_put_vertical",
        "expiry": expiry,
        "dte": dte,
        "short_strike": short,
        "long_strike": long_,
        "width": width,
        "credit": credit,
        "bpr": bpr,
        "pop": round(pop, 3),
        "short_delta": round(put_delta_abs(price, short, iv, dte) or 0.0, 3),
        "credit_to_bpr": round(credit * 100.0 / bpr, 3),
        "ev_per_contract": ev,
        "ev_on_bpr": round(ev / bpr, 4),
        "iv": round(iv, 4),
        "iv_rank": round(iv_rank, 3),
        "underlying_price": round(price, 2),
        "liquidity": liquidity,
        "earnings_date": earnings_date,
    }


def rank_opportunities(candidates, top_n=TOP_N):
    """Best expected return on capital first; tie-break on IV rank then POP."""
    return sorted(
        candidates,
        key=lambda c: (c["ev_on_bpr"], c["iv_rank"], c["pop"]),
        reverse=True,
    )[:top_n]


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
        sel = choose_strikes(list(puts.keys()), price, m["iv"], dte)
        if not sel:
            skipped[sym] = "no strikes"
            continue
        short, long_ = sel
        quotes = client.fetch_option_quotes([puts[short], puts[long_]])
        sm = quotes.get(puts[short], {})
        lm = quotes.get(puts[long_], {})
        short_mark = sm.get("mark") or _mid(sm)
        long_mark = lm.get("mark") or _mid(lm)
        if short_mark is None or long_mark is None:
            skipped[sym] = "no option marks"
            continue
        cand = build_candidate(sym, expiry, dte, short, long_, short_mark, long_mark,
                               price, m["iv"], m["iv_rank"], m.get("liquidity"), m.get("earnings_date"))
        if cand:
            candidates.append(cand)
        else:
            skipped[sym] = "failed filters"

    ranked = rank_opportunities(candidates)
    _write(ranked, candidates, skipped)
    log.info("Scan done: %d candidates, top %d ranked, %d skipped",
             len(candidates), len(ranked), len(skipped))
    return 0


def _mid(q):
    b, a = q.get("bid"), q.get("ask")
    return (b + a) / 2 if (b is not None and a is not None) else None


def _write(ranked, candidates, skipped):
    SCAN_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "params": {"min_iv_rank": MIN_IV_RANK, "dte_min": DTE_MIN, "dte_max": DTE_MAX,
                   "target_pop": TARGET_POP, "width": WIDTH},
        "top": ranked,
        "all_candidates": candidates,
        "skipped": skipped,
    }
    (SCAN_DIR / "opportunities.json").write_text(json.dumps(payload, indent=2, default=str) + "\n")

    lines = ["# Opportunity scan", "",
             "_Generated {} · short put verticals ranked by expected return on BPR._".format(payload["generated_at"]),
             "", "| # | Trade | DTE | Credit | BPR | POP | Cr/BPR | EV/ctr | EV/BPR | IVR |",
             "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for i, c in enumerate(ranked, 1):
        lines.append("| {} | {} {:g}/{:g}p | {} | ${:.2f} | ${:.0f} | {:.0%} | {:.0%} | ${:+.0f} | {:.1%} | {:.0%} |".format(
            i, c["underlying"], c["short_strike"], c["long_strike"], c["dte"], c["credit"],
            c["bpr"], c["pop"], c["credit_to_bpr"], c["ev_per_contract"], c["ev_on_bpr"], c["iv_rank"]))
    if not ranked:
        lines.append("| — | _no setups passed filters_ | | | | | | | | |")
    (SCAN_DIR / "summary.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    sys.exit(main())
