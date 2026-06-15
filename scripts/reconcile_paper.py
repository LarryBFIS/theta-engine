"""One-time reconcile of the paper book to the concentration caps.

The caps (patch 0052) stop NEW over-concentration but don't touch positions
opened before they existed. This paper-closes the excess at each position's last
mark — keeping the best-fitting positions (index ETFs first, then better current
unrealized, then smaller size) — so the forward test runs from a clean,
within-caps book. Closed positions feed the outcomes ledger (so the learner
reaches its activation threshold sooner).

Pure / offline: uses the marks already on book.json — no tastytrade call needed
(works even when the API is unreachable). Idempotent: re-running closes nothing.

Run:  python -m scripts.reconcile_paper
"""
import logging
import sys
from datetime import date, datetime, timezone

from scripts.paper_trades import (BOOK_FILE, PAPER_DIR, _load, reconcile_to_caps,
                                  append_ledger, summarize, _write_summary,
                                  MAX_PER_NAME, MAX_PER_CLUSTER, MAX_OPEN)

log = logging.getLogger("reconcile")


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    today = date.today().isoformat()
    book = _load(BOOK_FILE, None)
    if not book or not book.get("trades"):
        log.info("No paper book found — nothing to reconcile.")
        return 0

    before = summarize(book)
    closed = reconcile_to_caps(book, today)
    if not closed:
        log.info("Paper book already within caps (max %d/name, %d/cluster, %d total) — nothing to close.",
                 MAX_PER_NAME, MAX_PER_CLUSTER, MAX_OPEN)
        return 0

    append_ledger([t for t in book["trades"] if t.get("status") == "closed"])
    book["updated_at"] = datetime.now(timezone.utc).isoformat()
    book["summary"] = summarize(book)
    after = book["summary"]
    PAPER_DIR.mkdir(parents=True, exist_ok=True)
    BOOK_FILE.write_text(__import__("json").dumps(book, indent=2, default=str) + "\n")
    _write_summary(book, after)

    realized_locked = round(sum(float(t.get("realized_pnl") or 0) for t in closed), 2)
    log.info("Reconciled paper book to caps (%d/name, %d/cluster, %d total):",
             MAX_PER_NAME, MAX_PER_CLUSTER, MAX_OPEN)
    for t in sorted(closed, key=lambda x: float(x.get("realized_pnl") or 0)):
        log.info("  closed %-6s %-20s %sx  realized %+8.2f",
                 t.get("underlying"), t.get("structure"), t.get("contracts"),
                 float(t.get("realized_pnl") or 0))
    log.info("Closed %d positions · locked in %+.2f (was unrealized marks).",
             len(closed), realized_locked)
    log.info("Book: %d open / %d closed  (was %d / %d)  · realized now %+.2f",
             after["open"], after["closed"], before["open"], before["closed"], after["realized_pnl"])
    log.info("Commit:  git add paper/ memory/ && git commit -m 'reconcile paper book to caps' && git push origin main")
    return 0


if __name__ == "__main__":
    sys.exit(main())
