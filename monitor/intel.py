"""Intel layer — news, market metrics, Claude synthesis.

Sources:
  - Yahoo Finance RSS for per-ticker news (free, no key)
  - tastytrade /market-metrics for IV rank / percentile
  - Anthropic API (claude-sonnet-4) for synthesis

Outputs a daily briefing string ready for Pushover.
"""
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional

import requests

from monitor import config

log = logging.getLogger(__name__)

YAHOO_RSS = "https://feeds.finance.yahoo.com/rss/2.0/headline"
ANTHROPIC_API = "https://api.anthropic.com/v1/messages"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"
ANTHROPIC_VERSION = "2023-06-01"


@dataclass
class NewsItem:
    title: str
    url: str
    published: str
    summary: str = ""


@dataclass
class MarketMetric:
    ticker: str
    iv_rank: Optional[float] = None
    iv_percentile: Optional[float] = None
    implied_volatility: Optional[float] = None


# ────────────────────────────────────────────────────────────────────
# News fetch (Yahoo Finance RSS — free, no auth)
# ────────────────────────────────────────────────────────────────────
def fetch_news_yahoo(ticker: str, max_items: int = 10) -> list[NewsItem]:
    """Pull recent news headlines for a ticker via Yahoo Finance RSS."""
    try:
        r = requests.get(
            YAHOO_RSS,
            params={"s": ticker, "region": "US", "lang": "en-US"},
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0 theta-engine/1.0"},
        )
        r.raise_for_status()
        root = ET.fromstring(r.text)
        items = []
        for item in root.findall(".//item")[:max_items]:
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            pub = (item.findtext("pubDate") or "").strip()
            desc = (item.findtext("description") or "").strip()
            if title:
                items.append(NewsItem(title=title, url=link, published=pub, summary=desc))
        log.info("Fetched %d news items for %s", len(items), ticker)
        return items
    except Exception as e:
        log.error("Failed to fetch Yahoo news for %s: %s", ticker, e)
        return []


# ────────────────────────────────────────────────────────────────────
# Market metrics (IV rank etc.) via tastytrade
# ────────────────────────────────────────────────────────────────────
def fetch_market_metrics(client, tickers: list[str]) -> dict[str, MarketMetric]:
    """Fetch IV rank / percentile for tickers via tastytrade /market-metrics."""
    if not tickers:
        return {}
    try:
        data = client._get(
            "/market-metrics",
            params={"symbols": ",".join(tickers)},
        )
        items = data.get("data", {}).get("items", [])
    except Exception as e:
        log.error("Failed to fetch market metrics: %s", e)
        return {}

    to_float = client._to_float_or_none
    result: dict[str, MarketMetric] = {}
    for item in items:
        sym = item.get("symbol")
        if not sym:
            continue
        result[sym] = MarketMetric(
            ticker=sym,
            iv_rank=to_float(item.get("implied-volatility-index-rank")),
            iv_percentile=to_float(item.get("implied-volatility-percentile")),
            implied_volatility=to_float(item.get("implied-volatility-index")),
        )
    log.info("Fetched market metrics for %d/%d tickers", len(result), len(tickers))
    return result


# ────────────────────────────────────────────────────────────────────
# Anthropic synthesis
# ────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a sharp, concise options trading desk strategist briefing a tastytrade options trader.

The trader runs short-premium defined-risk strategies (mostly put credit spreads). They use tastytrade voice: BPR, POP, P50, DTE, manage at 50%, gamma risk, IV rank, roll, etc.

Your job: read their open positions and today's news/metrics, then write a 4-6 sentence briefing that surfaces ONLY what matters for their book TODAY.

Rules:
- Start with the most important thing. No preamble like "Here's your briefing" or "Today, ..."
- Be concrete: name catalysts (FOMC, CPI, earnings), name underlyings, name dollar amounts and percentages.
- Connect catalysts to specific positions: "NVDA earnings AMC = SPY vol event — watch your SPY 721/716p open Wed."
- If a position is in trouble (breached, near 21 DTE, IV expanding hard), say so plainly.
- If nothing material, say so in one sentence. Don't fill space.
- Mention IV rank shifts if material (>10 point move) or if rank is extreme (<20 or >60).
- No headers, no bullet lists unless absolutely needed. Prose. Mobile-readable.
"""


def synthesize_briefing(
    positions_summary: str,
    news_blob: str,
    market_metrics_summary: str,
    api_key: str,
    extra_context: str = "",
) -> str:
    """Call Anthropic API to synthesize a daily briefing."""
    user_prompt_parts = [
        "OPEN POSITIONS:",
        positions_summary,
        "",
        "RECENT NEWS (last 24h):",
        news_blob,
        "",
        "IV METRICS:",
        market_metrics_summary,
    ]
    if extra_context:
        user_prompt_parts.extend(["", "ADDITIONAL CONTEXT:", extra_context])
    user_prompt_parts.extend(["", "Write the briefing now."])
    user_prompt = "\n".join(user_prompt_parts)

    r = requests.post(
        ANTHROPIC_API,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "content-type": "application/json",
        },
        json={
            "model": ANTHROPIC_MODEL,
            "max_tokens": 600,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=30,
    )
    if not r.ok:
        log.error("Anthropic API call failed: %s — %s", r.status_code, r.text[:500])
    r.raise_for_status()
    data = r.json()
    blocks = data.get("content", [])
    text = "\n".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
    log.info("Anthropic synthesis: %d chars, stop_reason=%s", len(text), data.get("stop_reason"))
    return text


# ────────────────────────────────────────────────────────────────────
# Prompt formatters
# ────────────────────────────────────────────────────────────────────
def format_positions_for_prompt(snapshot, trade_results) -> str:
    lines = []
    a = snapshot
    pnl = a.net_liquidating_value - config.STARTING_CAPITAL
    pnl_pct = pnl / config.STARTING_CAPITAL if config.STARTING_CAPITAL else 0
    lines.append(
        f"Account: net liq ${a.net_liquidating_value:,.0f} "
        f"(started ${config.STARTING_CAPITAL:,.0f}, P&L ${pnl:+,.0f} / {pnl_pct*100:+.1f}%)"
    )
    for tr in trade_results:
        t = tr["trade"]
        m = tr["metrics"]
        if m.pct_max_profit_captured_mid is not None:
            captured = f"{m.pct_max_profit_captured_mid*100:+.0f}%"
        else:
            captured = "n/a"
        if m.profit_if_closed_mid is not None:
            profit = f"${m.profit_if_closed_mid:+.0f}"
        else:
            profit = "n/a"
        if m.underlying_price and m.short_strike_distance_pct is not None:
            underlying = f"${m.underlying_price:.2f} ({m.short_strike_distance_pct*100:.1f}% OTM)"
        else:
            underlying = "n/a"
        lines.append(
            f"  - {t.underlying} {int(t.short_strike)}/{int(t.long_strike)}p exp {t.expiry}, "
            f"{m.dte}d, credit ${t.credit_per_contract:.2f}, "
            f"underlying {underlying}, "
            f"P&L if closed: {profit} ({captured} captured), "
            f"max loss ${t.max_loss_total:.0f}"
        )
    return "\n".join(lines)


def format_news_for_prompt(news_by_ticker: dict[str, list[NewsItem]]) -> str:
    lines = []
    total = 0
    for ticker, items in news_by_ticker.items():
        if not items:
            continue
        lines.append(f"\n[{ticker}]")
        for item in items[:6]:
            lines.append(f"  - {item.title}")
            total += 1
    if not lines:
        return "(no recent news found)"
    return "\n".join(lines)


def format_metrics_for_prompt(metrics: dict[str, MarketMetric]) -> str:
    if not metrics:
        return "(market metrics unavailable)"
    lines = []
    for sym, m in metrics.items():
        iv = f"{m.implied_volatility*100:.1f}%" if m.implied_volatility is not None else "n/a"
        rank = f"{m.iv_rank*100:.0f}" if m.iv_rank is not None else "n/a"
        pct = f"{m.iv_percentile*100:.0f}" if m.iv_percentile is not None else "n/a"
        lines.append(f"{sym}: IV {iv} · IV rank {rank} · IV percentile {pct}")
    return "\n".join(lines)
