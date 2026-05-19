"""Pushover notifier — sends push notifications to your phone/desktop."""
import logging
from typing import Optional

import requests

from monitor import config

log = logging.getLogger(__name__)

PUSHOVER_URL = "https://api.pushover.net/1/messages.json"

# Pushover priorities: -2 silent, -1 low, 0 normal, 1 high (bypass quiet hours), 2 emergency
PRIORITY_LOW = -1
PRIORITY_NORMAL = 0
PRIORITY_HIGH = 1

# Sound names — see https://pushover.net/api#sounds
SOUND_ALERT = "siren"  # urgent — short strike, max loss
SOUND_SUCCESS = "magic"  # good news — profit target hit
SOUND_REMINDER = "tugboat"  # neutral — 21 DTE, daily summary
SOUND_INFO = "pushover"  # default — VIX spikes etc.


def send(
    title: str,
    message: str,
    priority: int = PRIORITY_NORMAL,
    sound: str = SOUND_INFO,
    url: Optional[str] = None,
    url_title: Optional[str] = None,
) -> bool:
    """Send a Pushover notification. Returns True on success."""
    payload = {
        "token": config.PUSHOVER_APP_TOKEN,
        "user": config.PUSHOVER_USER_KEY,
        "title": title,
        "message": message,
        "priority": priority,
        "sound": sound,
    }
    if url:
        payload["url"] = url
        if url_title:
            payload["url_title"] = url_title

    try:
        r = requests.post(PUSHOVER_URL, data=payload, timeout=10)
        r.raise_for_status()
        body = r.json()
        if body.get("status") == 1:
            log.info("Sent notification: %s", title)
            return True
        log.error("Pushover returned non-1 status: %s", body)
        return False
    except requests.RequestException as e:
        log.error("Pushover request failed: %s", e)
        return False
