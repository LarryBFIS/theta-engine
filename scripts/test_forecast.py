"""Unit tests for monitor.forecast — pure logic + the tick() file loop (no network).

Run: python -m scripts.test_forecast
"""
import json
import math
import tempfile
from datetime import date, timedelta
from pathlib import Path

from monitor import forecast


def _close(a, b, eps=1e-6):
    return abs(a - b) <= eps


def test_sigma_move():
    absmv, pct = forecast.sigma_move(700.0, 0.20, 7)
    exp_pct = 0.20 * math.sqrt(7 / 365.0)
    assert _close(pct, round(exp_pct, 4)), pct
    assert _close(absmv, round(700.0 * exp_pct, 2)), absmv
    # degenerate inputs never blow up
    assert forecast.sigma_move(0, 0.2, 7) == (0.0, 0.0)
    assert forecast.sigma_move(700, None, 7) == (0.0, 0.0)
    assert forecast.sigma_move(700, 0.2, 0) == (0.0, 0.0)
    print("ok sigma_move")


def test_make_forecast():
    fc = forecast.make_forecast("SPY", 760.0, 0.16, model="kimi-k3",
                                market_view="calm", vol_verdict="implied_rich",
                                horizon=7, today=date(2026, 9, 2))
    assert fc["index"] == "SPY" and fc["resolved"] is False
    assert fc["forecast_date"] == "2026-09-02" and fc["target_date"] == "2026-09-09"
    assert fc["spot_at_forecast"] == 760.0 and fc["vol_verdict"] == "implied_rich"
    assert 0 < fc["implied_move_pct"] < 0.1
    print("ok make_forecast")


def test_grade_in_and_out_of_range():
    fc = forecast.make_forecast("QQQ", 700.0, 0.20, model="claude-haiku-4-5",
                                vol_verdict="implied_rich", horizon=7, today=date(2026, 9, 2))
    imp_abs = fc["implied_move_abs"]  # ~ 700 * 0.20*sqrt(7/365)
    # realized move well inside the implied 1-sigma -> stayed_in_range, rich call correct
    g_in = forecast.grade(fc, 700.0 + imp_abs * 0.4, today=date(2026, 9, 9))
    assert g_in["stayed_in_range"] is True and g_in["resolved"] is True
    assert g_in["vol_call_correct"] is True
    # realized move blows past implied -> out of range, rich call WRONG
    g_out = forecast.grade(fc, 700.0 + imp_abs * 2.0, today=date(2026, 9, 9))
    assert g_out["stayed_in_range"] is False
    assert g_out["vol_call_correct"] is False
    # implied_cheap flips the vol-call grading
    fc_cheap = dict(fc, vol_verdict="implied_cheap")
    assert forecast.grade(fc_cheap, 700.0 + imp_abs * 2.0)["vol_call_correct"] is True
    print("ok grade")


def test_scoreboard():
    rows = [
        {"resolved": True, "model": "kimi-k3", "index": "SPY", "stayed_in_range": True,
         "implied_move_pct": 0.03, "realized_move_pct": 0.01, "vol_verdict": "implied_rich",
         "vol_call_correct": True},
        {"resolved": True, "model": "kimi-k3", "index": "SPY", "stayed_in_range": False,
         "implied_move_pct": 0.03, "realized_move_pct": 0.05, "vol_verdict": "implied_rich",
         "vol_call_correct": False},
        {"resolved": False, "model": "kimi-k3", "index": "QQQ"},
    ]
    sb = forecast.scoreboard(rows)
    assert sb["resolved"] == 2 and sb["pending"] == 1
    assert sb["overall"]["n"] == 2 and sb["overall"]["in_range_rate"] == 0.5
    assert sb["overall"]["vol_call_accuracy"] == 0.5
    # implied_minus_realized = mean(0.03,0.03) - mean(0.01,0.05) = 0.03 - 0.03 = 0.0
    assert _close(sb["overall"]["implied_minus_realized"], 0.0)
    assert sb["by_model"]["kimi-k3"]["n"] == 2
    print("ok scoreboard")


def test_tick_end_to_end(tmp=None):
    # Redirect the module's file paths to a temp dir.
    d = Path(tempfile.mkdtemp())
    forecast.LOG_FILE = d / "forecasts.json"
    forecast.SCORE_FILE = d / "scores.json"
    forecast.CORE = ["SPY", "QQQ"]

    day1 = date(2026, 9, 2)
    prices1 = {"SPY": 760.0, "QQQ": 700.0}
    metrics1 = {"SPY": {"iv": 0.16}, "QQQ": {"iv": 0.20}}
    agent1 = {"model": "kimi-k3", "market_view": "calm", "vol_verdict": "implied_rich"}
    forecast.tick(prices1, metrics1, agent1, today=day1)

    data = json.loads(forecast.LOG_FILE.read_text())
    assert len(data["forecasts"]) == 2, data
    assert all(not f["resolved"] for f in data["forecasts"])

    # same day again -> no duplicate forecasts
    forecast.tick(prices1, metrics1, agent1, today=day1)
    data = json.loads(forecast.LOG_FILE.read_text())
    assert len(data["forecasts"]) == 2, "should not double-log same index same day"

    # 8 days later: SPY moved +1% (inside implied), QQQ moved +6% (outside) -> resolve both
    day2 = day1 + timedelta(days=8)
    prices2 = {"SPY": 760.0 * 1.01, "QQQ": 700.0 * 1.06}
    metrics2 = {"SPY": {"iv": 0.17}, "QQQ": {"iv": 0.19}}
    agent2 = {"model": "claude-haiku-4-5", "market_view": "hot", "vol_verdict": "implied_cheap"}
    board = forecast.tick(prices2, metrics2, agent2, today=day2)

    data = json.loads(forecast.LOG_FILE.read_text())
    resolved = [f for f in data["forecasts"] if f["resolved"]]
    pending = [f for f in data["forecasts"] if not f["resolved"]]
    assert len(resolved) == 2, "both day1 forecasts should now be resolved"
    assert len(pending) == 2, "day2 should have logged 2 fresh forecasts"
    spy = next(f for f in resolved if f["index"] == "SPY")
    qqq = next(f for f in resolved if f["index"] == "QQQ")
    assert spy["stayed_in_range"] is True, spy
    assert qqq["stayed_in_range"] is False, qqq
    assert board["overall"]["n"] == 2 and board["overall"]["in_range_rate"] == 0.5
    print("ok tick end-to-end")


if __name__ == "__main__":
    test_sigma_move()
    test_make_forecast()
    test_grade_in_and_out_of_range()
    test_scoreboard()
    test_tick_end_to_end()
    print("\nALL FORECAST TESTS PASSED")
