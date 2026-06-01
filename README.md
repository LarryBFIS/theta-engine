# theta-engine

An autonomous, self-monitoring options-trading engine for a tastytrade account,
running entirely on **GitHub Actions** (free) with a **Cloudflare Worker** for
the approve/reject webhook and reliable scheduling.

It runs a disciplined short-premium strategy (short put verticals), polls the
broker on a timer, applies mechanical management rules + an AI decision layer,
alerts to your phone via **Pushover**, keeps an **authoritative ledger** derived
from broker transactions, and publishes live status pages.

> **Mission:** 6-month experiment (2026-05-13 → 2026-11-13), grow $3,389.91 by
> 100%. Mechanical rules: max 3–4 positions, 35–50% BPR utilization, manage at
> 50%, 21 DTE hard exit, cut at 1.5× credit, never hold through earnings.

> **Safety:** the engine is **read-only against the broker — it never places
> orders.** It tells you what to do; you execute (or tap Approve/Reject, which
> is *recorded only* — see Phase 5b).

## How it works

`/.github/workflows/tick.yml` runs the core loop (cron during market hours, plus
`repository_dispatch` from the Cloudflare cron, plus manual `workflow_dispatch`):

1. **apply_decisions** — read Approve/Reject decisions from the gist, mark suggestions.
2. **poll** — pull account + positions + live option quotes; push a full snapshot to the gist.
3. **ai_decide** — Claude reviews positions vs. rules; pushes high-confidence alerts (with a "Review" deep link).
4. **build_ledger** — rebuild the authoritative ledger from every broker transaction.
5. **summary** — conditional "where you stand" Pushover (a few times/day).
6. commit any changed state back to the repo.

Other workflows: `deadman.yml` (stale-watchdog alert), `briefing.yml` (daily AM
briefing), `position_news.yml` (hourly RSS news scan).

## Layout

```
theta-engine/
├── scripts/
│   ├── poll.py              # one poll cycle (entry)
│   ├── ai_decide.py         # Claude decision layer (entry)
│   ├── build_ledger.py      # derive ledger/ from broker transactions (entry)
│   ├── apply_decisions.py   # apply Approve/Reject decisions (entry)
│   ├── summary.py, briefing.py, position_news.py
│   └── test_build_ledger.py, test_approvals.py   # credential-free unit tests
├── monitor/
│   ├── config.py            # env vars + thresholds
│   ├── tastytrade_client.py # OAuth2 REST client + live quotes
│   ├── decisions.py, rules.py, ai_trader.py      # rule + AI logic
│   ├── approvals.py         # signed decision links + apply logic (Phase 5b)
│   ├── gist.py, notifier.py, trades.py, market_state.py, ...
├── ledger/                  # GENERATED each tick (do not hand-edit)
│   ├── transactions.json    # every fill/fee/movement since experiment start
│   ├── trades.json          # orders grouped into trades w/ realized+unrealized
│   ├── reconciliation.json  # strategy P&L vs account P&L breakdown
│   └── summary.md
├── trades.json              # hand/auto-tracked trades w/ POP/BPR metadata
├── dashboard.html, roadmap.html, ledger.html, decide.html   # GitHub Pages
├── cloudflare/worker.js     # approve/reject webhook + scheduling cron
└── .github/workflows/
```

## Live pages (GitHub Pages)

- Dashboard: https://larrybfis.github.io/theta-engine/dashboard.html
- Roadmap:   https://larrybfis.github.io/theta-engine/roadmap.html
- Ledger:    https://larrybfis.github.io/theta-engine/ledger.html
- Decide:    https://larrybfis.github.io/theta-engine/decide.html (opened from Pushover)

## Secrets (GitHub repo → Settings → Secrets → Actions)

| Secret | Purpose |
|---|---|
| `TASTYTRADE_CLIENT_SECRET`, `TASTYTRADE_REFRESH_TOKEN` | OAuth2 broker access |
| `PUSHOVER_USER_KEY`, `PUSHOVER_APP_TOKEN` | phone alerts |
| `ANTHROPIC_API_KEY` | AI decision layer |
| `GIST_ID`, `GIST_TOKEN` | live-state gist |
| `STARTING_CAPITAL` | experiment baseline (3389.91) |
| `DECISION_SECRET` | signs Approve/Reject links (matches the Worker) |

## Phase 5b — Approve/Reject (record-only)

Actionable alerts include a **Review →** button → `decide.html` → the Cloudflare
Worker (`cloudflare/worker.js`) verifies a signed token and writes the decision
to the gist → the next tick records it and confirms via Pushover. **No order is
placed** — you execute in tastytrade. Setup + reliable-scheduling cron: see
[`cloudflare/README.md`](cloudflare/README.md).

## Local testing

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in credentials
python -m scripts.poll
python -m scripts.build_ledger
python -m scripts.test_build_ledger   # no credentials needed
python -m scripts.test_approvals      # no credentials needed
```

## License

MIT.
