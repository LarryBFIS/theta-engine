"""Expected-move forecast + scoring loop.

Each scan records the option market's IMPLIED expected move for the core indices — a
deterministic 1-sigma move from spot x IV x sqrt(t) — and later grades it against the
REALIZED move. That measures the volatility risk premium directly: does the market's
implied move usually overshoot reality (so premium-selling is paid), and by how much?
The active AI model + its vol_verdict/market_view are stored alongside each forecast, so
the LLM's read can be scored too (does 'implied_rich' actually precede realized < implied?).

Design: the pure functions (sigma_move / make_forecast / grade / scoreboard) hold all the
logic and take no I/O, so they are trivially unit-tested. tick() wires file I/O and is the
one call the scanner makes. Nothing here ever raises for an operational reason — a bad
read or write just skips, so the scan is never broken by forecasting.
"""
import json
import math
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = REPO_ROOT / "memory" / "forecasts.json"
SCORE_FILE = REPO_ROOT / "memory" / "forecast_scores.json"

# Indices we forecast. Broad index ETFs by default (the names we actually trade).
CORE = [s.strip().upper() for s in
        (os.getenv("FORECAST_INDICES") or "SPY,QQQ,IWM,DIA").split(",") if s.strip()]
# Window over which we measure the move. 7 calendar days ~= one trading week — long
# enough to be meaningful, short enough to accumulate a real sample fast.
HORIZON_DAYS = int(os.getenv("FORECAST_HORIZON_DAYS") or "7")
MAX_ROWS = int(os.getenv("FORECAST_MAX_ROWS") or "500")


def sigma_move(spot, iv, days):
    """The option market's 1-sigma expected move over `days` calendar days.
    `iv` is annualized (0.20 = 20% vol). Returns (abs_move, pct_move as a fraction).
    Uses days/365 to match how option DTE / expected-move is conventionally quoted."""
    if not spot or not iv or not days or days <= 0:
        return 0.0, 0.0
    pct = iv * math.sqrt(days / 365.0)
    return round(spot * pct, 2), round(pct, 4)


def make_forecast(index, spot, iv, model=None, market_view="", vol_verdict=None,
                  horizon=None, today=None):
    """Build one forecast record: the implied 1-sigma move over the horizon, plus the
    AI context (model / vol_verdict / market_view) to be graded when it matures."""
    horizon = horizon or HORIZON_DAYS
    today = today or date.today()
    abs_mv, pct_mv = sigma_move(spot, iv, horizon)
    return {
        "id": uuid.uuid4().hex[:12],
        "index": index,
        "forecast_date": today.isoformat(),
        "target_date": (today + timedelta(days=horizon)).isoformat(),
        "horizon_days": horizon,
        "spot_at_forecast": round(spot, 2),
        "iv": round(iv, 4),
        "implied_move_pct": pct_mv,      # 1-sigma, as a fraction (0.03 = 3%)
        "implied_move_abs": abs_mv,
        "model": model,                  # who produced the accompanying view
        "vol_verdict": vol_verdict,      # implied_rich | implied_cheap | fair | None
        "market_view": (market_view or "")[:280],
        "resolved": False,
    }


def grade(fc, actual_price, today=None):
    """Resolve a matured forecast against the realized price. Returns a NEW dict with the
    outcome fields filled and resolved=True. stayed_in_range = the realized move came in
    within the implied 1-sigma move (the premium-seller's win condition)."""
    today = today or date.today()
    spot0 = fc.get("spot_at_forecast") or 0
    signed = (actual_price / spot0 - 1.0) if spot0 else 0.0
    realized = abs(signed)
    imp = fc.get("implied_move_pct") or 0.0
    out = dict(fc)
    out.update({
        "resolved": True,
        "resolved_at": today.isoformat(),
        "actual_price": round(actual_price, 2),
        "realized_move_pct": round(realized, 4),
        "realized_move_signed": round(signed, 4),
        "stayed_in_range": bool(realized <= imp),
    })
    # If the AI made a vol call, grade it: 'implied_rich' is right when realized < implied
    # (the market overpriced the move); 'implied_cheap' is the opposite.
    vv = fc.get("vol_verdict")
    if vv in ("implied_rich", "implied_cheap"):
        rich_right = realized < imp
        out["vol_call_correct"] = bool(rich_right if vv == "implied_rich" else not rich_right)
    return out


def _agg(rows):
    n = len(rows)
    if not n:
        return {"n": 0}
    in_range = sum(1 for r in rows if r.get("stayed_in_range"))
    imp = sum(r.get("implied_move_pct", 0) or 0 for r in rows) / n
    real = sum(r.get("realized_move_pct", 0) or 0 for r in rows) / n
    d = {
        "n": n,
        "in_range_rate": round(in_range / n, 3),          # how often move stayed within implied 1-sigma
        "avg_implied_move_pct": round(imp, 4),
        "avg_realized_move_pct": round(real, 4),
        "implied_minus_realized": round(imp - real, 4),   # +ve = market overprices the move (premium edge)
    }
    vc = [r for r in rows if "vol_call_correct" in r]
    if vc:
        d["vol_call_n"] = len(vc)
        d["vol_call_accuracy"] = round(sum(1 for r in vc if r.get("vol_call_correct")) / len(vc), 3)
    return d


def scoreboard(forecasts):
    """Aggregate resolved forecasts into overall + per-model + per-index scorecards."""
    res = [r for r in (forecasts or []) if r.get("resolved")]
    by_model, by_index = {}, {}
    for r in res:
        by_model.setdefault(r.get("model") or "unknown", []).append(r)
        by_index.setdefault(r.get("index") or "?", []).append(r)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "resolved": len(res),
        "pending": len([r for r in (forecasts or []) if not r.get("resolved")]),
        "overall": _agg(res),
        "by_model": {k: _agg(v) for k, v in sorted(by_model.items())},
        "by_index": {k: _agg(v) for k, v in sorted(by_index.items())},
    }


def _load(path, default):
    try:
        return json.loads(path.read_text())
    except Exception:  # noqa: BLE001 — missing/corrupt file -> start fresh
        return default


def tick(prices, metrics, agent_summary=None, today=None):
    """Called once per scan. Using THIS scan's live spots (no extra network): (1) resolve
    any matured, unresolved forecast we now have a price for, (2) log at most one new
    forecast per core index per day, (3) rewrite the scoreboard. Returns the scoreboard or
    None. Never raises — a failure just skips this tick."""
    try:
        today = today or date.today()
        data = _load(LOG_FILE, {"forecasts": []})
        fcs = data.get("forecasts", []) if isinstance(data, dict) else []
        cur = dict(prices or {})
        summary = agent_summary or {}
        model = summary.get("model")
        market_view = summary.get("market_view", "")
        vol_verdict = summary.get("vol_verdict")

        # 1) resolve matured, still-open forecasts against this scan's live spot
        for fc in fcs:
            if fc.get("resolved") or fc.get("target_date", "9999") > today.isoformat():
                continue
            px = cur.get(fc.get("index"))
            if px:
                graded = grade(fc, px, today=today)
                fc.clear()
                fc.update(graded)

        # 2) log at most one new forecast per index per day
        logged_today = {(fc.get("index"), fc.get("forecast_date")) for fc in fcs}
        for idx in CORE:
            spot = cur.get(idx)
            iv = (metrics.get(idx) or {}).get("iv") if metrics else None
            if not spot or not iv or (idx, today.isoformat()) in logged_today:
                continue
            fcs.append(make_forecast(idx, spot, iv, model, market_view, vol_verdict, today=today))

        fcs = fcs[-MAX_ROWS:]
        data["forecasts"] = fcs
        board = scoreboard(fcs)
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        LOG_FILE.write_text(json.dumps(data, indent=2) + "\n")
        SCORE_FILE.write_text(json.dumps(board, indent=2) + "\n")
        return board
    except Exception:  # noqa: BLE001 — forecasting must never break the scan
        return None
