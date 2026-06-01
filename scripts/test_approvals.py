"""Tests for the Approve/Reject pure logic.

Run without pytest:  python -m scripts.test_approvals

Covers the two pieces that must agree across Python and the Cloudflare Worker
(token signing) and the idempotent decision-application rule.
"""
import sys
from dataclasses import dataclass
from typing import Optional

from monitor.approvals import apply_decisions, decision_token


@dataclass
class FakeSuggestion:
    id: str
    trade_id: str
    status: str = "pending"
    action: str = "CLOSE"
    decided_at: Optional[str] = None


def main() -> int:
    failures = []

    # --- token: deterministic, secret-dependent, fixed length ---
    t1 = decision_token("sug_abc", secret="hunter2")
    t2 = decision_token("sug_abc", secret="hunter2")
    t3 = decision_token("sug_abc", secret="different")
    t4 = decision_token("sug_xyz", secret="hunter2")
    if t1 != t2:
        failures.append("token not deterministic")
    if len(t1) != 16:
        failures.append(f"token length {len(t1)} != 16")
    if t1 == t3:
        failures.append("token did not change with secret")
    if t1 == t4:
        failures.append("token did not change with suggestion id")
    # Known-answer vector so the Worker can be checked against the same value.
    expected = "bfe87ed0b6d67b51"
    if t1 != expected:
        failures.append(f"token KAT mismatch: {t1} != {expected} (update Worker if scheme changed)")

    # --- apply_decisions: accept/reject/idempotent/unknown ---
    sugs = [
        FakeSuggestion(id="s1", trade_id="t1"),
        FakeSuggestion(id="s2", trade_id="t2"),
        FakeSuggestion(id="s3", trade_id="t3", status="accepted"),  # already decided
        FakeSuggestion(id="s4", trade_id="t4"),
    ]
    decisions = {
        "s1": {"action": "accept", "at": "2026-06-01T13:00:00Z"},
        "s2": {"action": "reject", "at": "2026-06-01T13:01:00Z"},
        "s3": {"action": "reject", "at": "2026-06-01T13:02:00Z"},  # must be ignored (not pending)
        "s4": {"action": "bogus"},  # unknown action ignored
    }
    applied = apply_decisions(sugs, decisions)

    by_id = {s.id: s for s in sugs}
    if by_id["s1"].status != "accepted":
        failures.append("s1 should be accepted")
    if by_id["s1"].decided_at != "2026-06-01T13:00:00Z":
        failures.append("s1 decided_at not set")
    if by_id["s2"].status != "rejected":
        failures.append("s2 should be rejected")
    if by_id["s3"].status != "accepted":
        failures.append("s3 (already accepted) must not flip to rejected")
    if by_id["s4"].status != "pending":
        failures.append("s4 (bogus action) must stay pending")
    if {s.id for s in applied} != {"s1", "s2"}:
        failures.append(f"applied set wrong: {sorted(s.id for s in applied)}")

    # Idempotency: a second pass applies nothing new.
    again = apply_decisions(sugs, decisions)
    if again:
        failures.append(f"second pass should apply nothing, got {[s.id for s in again]}")

    if failures:
        print("FAILED:")
        for f in failures:
            print("  - " + f)
        return 1
    print("token KAT:", t1)
    print(f"apply_decisions: {len(applied)} applied (s1 accepted, s2 rejected); idempotent ✓")
    print("All approvals tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
