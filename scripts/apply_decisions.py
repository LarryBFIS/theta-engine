"""Apply Approve/Reject decisions recorded by the Cloudflare Worker.

Runs once per tick (before polling). Reads the gist's decisions.json (written by
the Worker when you tap Approve/Reject), marks the matching suggestions in
suggestions.json as accepted/rejected, and sends a Pushover confirmation.

RECORD-ONLY (v1): an accepted suggestion is logged and confirmed — no broker
order is placed. You execute the trade in tastytrade yourself. Auto-execution is
a deliberately separate, later phase.

Reading the gist uses the public raw URL (no token needed); only the Worker can
*write* to it (it holds GIST_TOKEN), so the bot trusts the gist's contents.
"""
import logging
import sys
from datetime import datetime

import requests

from monitor import config, notifier
from monitor.approvals import apply_decisions
from monitor.trades import load_suggestions, save_suggestions

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-7s %(name)s · %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("apply_decisions")


def fetch_decisions() -> dict:
    """Pull {sug_id: {action, at}} from the gist's decisions file.

    Returns {} if the gist or file doesn't exist yet (nothing decided).
    """
    if not config.GIST_ID:
        log.info("GIST_ID not set; skipping decisions")
        return {}
    url = (
        f"https://gist.githubusercontent.com/LarryBFIS/{config.GIST_ID}"
        f"/raw/{config.DECISIONS_GIST_FILE}?_={int(datetime.now().timestamp())}"
    )
    try:
        r = requests.get(url, timeout=15)
        if r.status_code == 404:
            log.info("No decisions file in gist yet")
            return {}
        r.raise_for_status()
        data = r.json()
    except (requests.RequestException, ValueError) as e:
        log.warning("Could not fetch/parse decisions: %s", e)
        return {}
    return data.get("decisions", data) if isinstance(data, dict) else {}


def confirm(suggestion) -> None:
    verb = "ACCEPTED" if suggestion.status == "accepted" else "REJECTED"
    do = ""
    if suggestion.status == "accepted":
        do = " — place the close in tastytrade (record-only mode)"
    notifier.send(
        title=f"✓ {verb}: {suggestion.trade_id}",
        message=f"{suggestion.action} recorded{do}",
        priority=notifier.PRIORITY_NORMAL,
        sound=notifier.SOUND_SUCCESS if suggestion.status == "accepted" else notifier.SOUND_REMINDER,
    )


def main() -> int:
    decisions = fetch_decisions()
    if not decisions:
        return 0

    suggestions = load_suggestions()
    applied = apply_decisions(suggestions, decisions)
    if not applied:
        log.info("Decisions present but no pending suggestions matched")
        return 0

    save_suggestions(suggestions)
    for s in applied:
        log.info("Recorded %s for %s (%s)", s.status, s.trade_id, s.id)
        try:
            confirm(s)
        except Exception as e:  # noqa: BLE001 — never fail a tick on a notify error
            log.warning("Confirmation push failed for %s: %s", s.id, e)
    log.info("Applied %d decision(s)", len(applied))
    return 0


if __name__ == "__main__":
    sys.exit(main())
