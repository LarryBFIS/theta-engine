"""Centralized configuration loaded from environment.

In GitHub Actions, env vars come from repository secrets.
For local testing, copy .env.example to .env and fill in values.
"""
import os

from dotenv import load_dotenv

load_dotenv()  # no-op if .env doesn't exist (e.g. in GitHub Actions)


def _required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it as a GitHub Actions secret or in your local .env file."
        )
    return value


# ────────────────────────────────────────────────────────────────────
# Tastytrade OAuth2 credentials
# ────────────────────────────────────────────────────────────────────
# Get these from https://my.tastytrade.com → Manage → My Profile → API → OAuth Applications
TASTYTRADE_CLIENT_SECRET = _required("TASTYTRADE_CLIENT_SECRET")
TASTYTRADE_REFRESH_TOKEN = _required("TASTYTRADE_REFRESH_TOKEN")

# ────────────────────────────────────────────────────────────────────
# Pushover credentials
# ────────────────────────────────────────────────────────────────────
PUSHOVER_USER_KEY = _required("PUSHOVER_USER_KEY")
PUSHOVER_APP_TOKEN = _required("PUSHOVER_APP_TOKEN")

# ────────────────────────────────────────────────────────────────────
# Experiment baseline
# ────────────────────────────────────────────────────────────────────
STARTING_CAPITAL = float(os.getenv("STARTING_CAPITAL", "3438.16"))

# ────────────────────────────────────────────────────────────────────
# Misc
# ────────────────────────────────────────────────────────────────────
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
STATE_PATH = os.getenv("STATE_PATH", "/tmp/state.json")

# ────────────────────────────────────────────────────────────────────
# Optional: push state snapshots to a GitHub Gist for external visibility
# (e.g. so Claude can read live state in future chats without you pasting)
# ────────────────────────────────────────────────────────────────────
GIST_ID = os.getenv("GIST_ID", "")
GIST_TOKEN = os.getenv("GIST_TOKEN", "")

# ────────────────────────────────────────────────────────────────────
# Phase 5b: Approve/Reject UX
# ────────────────────────────────────────────────────────────────────
# Shared secret used to sign per-suggestion decision links so a random actor
# can't forge an Approve/Reject. Must match the DECISION_SECRET set on the
# Cloudflare Worker. Empty = feature effectively off (links still render but
# the worker rejects them).
DECISION_SECRET = os.getenv("DECISION_SECRET", "")
# Public GitHub Pages decision page the Pushover "Review" button opens.
DECIDE_BASE_URL = os.getenv(
    "DECIDE_BASE_URL", "https://larrybfis.github.io/theta-engine/decide.html"
)
# Filename the Worker writes decisions into, inside the existing gist.
DECISIONS_GIST_FILE = os.getenv("DECISIONS_GIST_FILE", "decisions.json")

# ────────────────────────────────────────────────────────────────────
# Rule thresholds — tune these without touching the code
# ────────────────────────────────────────────────────────────────────
PROFIT_TARGET_PCT = float(os.getenv("PROFIT_TARGET_PCT", "0.50"))
SHORT_STRIKE_BUFFER_PCT = float(os.getenv("SHORT_STRIKE_BUFFER_PCT", "0.005"))
MAX_LOSS_RATIO = float(os.getenv("MAX_LOSS_RATIO", "1.5"))
VIX_SPIKE_LEVEL = float(os.getenv("VIX_SPIKE_LEVEL", "22.0"))
VIX_SPIKE_PCT = float(os.getenv("VIX_SPIKE_PCT", "0.20"))
DAILY_LOSS_PCT = float(os.getenv("DAILY_LOSS_PCT", "0.02"))
TWENTY_ONE_DTE = int(os.getenv("TWENTY_ONE_DTE", "21"))

# ────────────────────────────────────────────────────────────────────
# Cooldown periods (minutes) — prevents notification spam from the same rule.
# Note: in v1 with no persistent state across GitHub Actions runs,
# cross-run cooldown isn't enforced. Within-run cooldown still works.
# ────────────────────────────────────────────────────────────────────
COOLDOWN_MINUTES = {
    "short_strike_touched": 60,
    "profit_target_hit": 240,
    "max_loss_warning": 30,
    "twenty_one_dte": 1440,
    "vix_spike": 60,
    "daily_loss": 60,
    "daily_summary": 60,
}
