# theta-engine

A notification service that monitors your tastytrade options positions and pushes alerts to your phone via [Pushover](https://pushover.net) when something needs your attention. Runs on **GitHub Actions** — completely free.

Built for the "I don't have time to watch markets, but I want to know when to act" workflow.

## What it does

GitHub Actions runs two scheduled workflows:

- **Poll workflow** — every 15 min during US market hours (Mon-Fri 9:30 AM – 4 PM ET). Pulls account state, evaluates rules, fires Pushover notifications on any trigger.
- **Summary workflow** — 4x per market day (10 AM, 12 PM, 2 PM, 4 PM ET). Sends a "where you stand" snapshot regardless of triggers.

You will *not* be notified about routine price moves, normal theta progress, or anything else that isn't actionable.

### Rules that fire alerts

| Rule | When |
|------|------|
| Short strike touched | Underlying near/below short put strike (or near/above short call strike) |
| Profit target hit | ≥50% of credit captured on a short option |
| Max loss approaching | Unrealized loss exceeds ~1.5× credit |
| 21 DTE reached | Any open option hits 21 days to expiry |
| VIX spike | VIX > 22 or up ≥20% on the day |
| Daily account loss | Account down ≥2% on the day |

## Setup

After pushing the code to your GitHub repo, set these **5 repository secrets**:

Go to **your repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `TASTYTRADE_USERNAME` | Your tastytrade login |
| `TASTYTRADE_PASSWORD` | Your tastytrade password |
| `PUSHOVER_USER_KEY` | 30-char user key from pushover.net |
| `PUSHOVER_APP_TOKEN` | API token of your Pushover application |
| `STARTING_CAPITAL` | Account net liq at experiment start (e.g. `3389.91`) |

That's it. The workflows are already in `.github/workflows/` and start running on the next scheduled time.

### Verify it works

Go to **your repo → Actions tab**. You should see two workflows. Click one → **Run workflow** (manual trigger) → wait ~30 sec → check your phone for a Pushover notification.

## Project layout

```
theta-engine/
├── scripts/
│   ├── poll.py                   # One polling cycle (GitHub Actions entry)
│   └── summary.py                # One summary push (GitHub Actions entry)
├── monitor/
│   ├── config.py                 # Env vars + thresholds (tune here)
│   ├── tastytrade_client.py      # API wrapper
│   ├── market_data.py            # VIX/quotes via yfinance
│   ├── notifier.py               # Pushover sender
│   ├── rules.py                  # All trigger logic
│   └── state.py                  # In-memory cooldown state
├── .github/workflows/
│   ├── poll.yml                  # Cron: */15 13-21 * * 1-5 (UTC)
│   └── summary.yml               # Cron: 0 14,16,18,20 * * 1-5 (UTC)
├── main.py                       # Optional: local always-on scheduler
├── requirements.txt
├── .env.example                  # For local testing only
└── .gitignore
```

## Tuning rules

All thresholds live in `monitor/config.py`:

| Setting | Default | What it does |
|---------|---------|--------------|
| `PROFIT_TARGET_PCT` | 0.50 | Fire profit-target alert at this fraction of max profit |
| `SHORT_STRIKE_BUFFER_PCT` | 0.005 | Fire short-strike alert when within 0.5% of strike |
| `VIX_SPIKE_LEVEL` | 22.0 | Absolute VIX for spike alert |
| `VIX_SPIKE_PCT` | 0.20 | Day-over-day VIX move for spike alert |
| `DAILY_LOSS_PCT` | 0.02 | Trigger daily-loss alert at this drawdown |

Edit, commit, push — GitHub Actions picks up the new values on the next run.

## Cost

| Component | Cost |
|---|---|
| GitHub Actions | **Free** (~440 min/month used, 2,000 included free) |
| Pushover | $5 one-time per platform (already paid) |
| tastytrade API | Free |
| yfinance | Free |

**Running cost: $0/month** after Pushover one-time fee.

## Local testing (optional)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in credentials
python -m scripts.poll      # single poll
python -m scripts.summary   # single summary
python main.py              # continuous scheduler
```

## Known limitations (v1)

- **No persistent cooldown state** — duplicates possible across runs. Easy to add later via committed `state.json` or a Gist.
- **DST drift** — GitHub Actions cron is UTC. During EST (Nov–March), summary times shift 1 hour earlier ET. Adjust `.github/workflows/summary.yml` to fix.
- **Rough max-loss heuristic** — uses a P&L proxy. Good enough for alerts.
- **Single account** — uses first account from tastytrade login.

## Security notes

- All credentials live as GitHub Actions secrets — never in code or git
- The service is read-only — it never places orders
- If you leak a credential, rotate it immediately

## Roadmap

- **Phase 2:** Claude API enrichment of notification bodies
- **Phase 3:** Web dashboard (close-now P&L, max profit/loss potential, grouped by expiry)
- **Phase 4:** WSB/SwaggyStocks sentiment screening layer

## License

MIT.
