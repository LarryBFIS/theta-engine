"""Phase 5b: Approve/Reject decision plumbing (record-only v1).

Flow:
  poll.py sends a Pushover alert with a signed "Review" link →
  decide.html (GitHub Pages) shows Approve/Reject →
  Cloudflare Worker validates the signature and writes the decision into the
  gist (decisions.json) →
  the next tick (scripts/apply_decisions.py) reads decisions.json and marks the
  matching suggestion accepted/rejected.

v1 is RECORD-ONLY: an accepted suggestion is logged and confirmed, but no order
is placed — you execute in tastytrade yourself. Auto-execution is a later phase.

This module holds the two pure pieces that need to agree across Python (the bot)
and JavaScript (the Worker): the signing scheme, and the rule for applying a
decision to a suggestion. Both are unit-tested in scripts/test_approvals.py.
"""
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Optional

# Length of the hex signature carried in the URL. 16 hex chars = 64 bits, plenty
# to stop forgery of a short-lived, low-value decision link. The Worker must use
# the same length.
TOKEN_LEN = 16


def decision_token(sug_id: str, secret: Optional[str] = None) -> str:
    """HMAC-SHA256(secret, sug_id), hex, truncated to TOKEN_LEN.

    The Cloudflare Worker recomputes this with the same secret and compares,
    so a decision link can't be forged without the shared secret. ``secret``
    defaults to config.DECISION_SECRET (imported lazily so the pure functions
    stay importable without env/config).
    """
    if secret is None:
        from monitor import config
        secret = config.DECISION_SECRET or ""
    digest = hmac.new(secret.encode(), sug_id.encode(), hashlib.sha256).hexdigest()
    return digest[:TOKEN_LEN]


def decide_url(sug_id: str) -> str:
    """Public decision-page URL for one suggestion, with its signature."""
    from monitor import config
    return f"{config.DECIDE_BASE_URL}?id={sug_id}&t={decision_token(sug_id)}"


def apply_decisions(suggestions: list, decisions: dict) -> list:
    """Apply recorded decisions to pending suggestions, in place.

    ``suggestions``: list of Suggestion objects (monitor.trades.Suggestion).
    ``decisions``: {sug_id: {"action": "accept"|"reject", "at": iso}} as written
    by the Worker into the gist.

    Only pending suggestions are touched, so this is idempotent — re-running a
    tick won't re-apply or flip an already-decided suggestion. Returns the list
    of suggestions newly decided this call (for confirmation notifications).
    """
    applied = []
    for s in suggestions:
        if getattr(s, "status", "pending") != "pending":
            continue
        d = decisions.get(s.id)
        if not d:
            continue
        action = (d.get("action") or "").strip().lower()
        if action == "accept":
            s.status = "accepted"
        elif action == "reject":
            s.status = "rejected"
        else:
            continue
        s.decided_at = d.get("at") or datetime.now(timezone.utc).isoformat()
        applied.append(s)
    return applied
