"""Trade ticket — turn a scored candidate into a ready-to-send order spec.

The scanner produces candidates with executable strikes + credit; this renders
each into (a) a structured order (legs + limit + sizing) and (b) a one-line,
copy-ready ticket string with the management plan — so a live pick can be entered
in a single glance instead of hand-built leg by leg (the friction we hit on the
first live IWM iron condor).

Pure logic; unit-tested in scripts/test_trade_ticket.py.
"""


def struct_code(structure):
    s = (structure or "").lower()
    if "condor" in s:
        return "IC"
    if "call" in s:
        return "VC"
    if "put" in s:
        return "VP"
    return (s[:3] or "?").upper()


def _legs(c, code, n, exp):
    """(action, strike, P/C) tuples for the structure, longs paired with shorts."""
    if code == "IC":
        ps = c.get("put_short_strike", c.get("short_strike"))
        pl = c.get("put_long_strike")
        cs = c.get("call_short_strike", c.get("long_strike"))
        cl = c.get("call_long_strike")
        raw = [("SELL", ps, "P"), ("BUY", pl, "P"), ("SELL", cs, "C"), ("BUY", cl, "C")]
    elif code == "VC":
        raw = [("SELL", c.get("short_strike"), "C"), ("BUY", c.get("long_strike"), "C")]
    else:  # VP / default
        raw = [("SELL", c.get("short_strike"), "P"), ("BUY", c.get("long_strike"), "P")]
    return [(a, k, t) for (a, k, t) in raw if k is not None]


def _text(under, code, legs, exp, n, credit, close_debit, max_loss):
    legstr = " / ".join("{} {:g}{}".format(a, k, t) for (a, k, t) in legs)
    return ("{u} {code} ×{n} — {legs} ({exp}) @ ${cr:.2f} net credit. "
            "Max loss ${ml:.0f}. After fill: GTC buy-to-close @ ${cd:.2f} (50%)."
            ).format(u=under, code=code, n=n, legs=legstr, exp=exp,
                     cr=credit, ml=max_loss, cd=close_debit)


def build_ticket(c):
    """Ready-to-send order spec from a scored candidate. Returns a dict with the
    structured legs, the net-credit limit, sizing, max loss, the copy-ready text,
    and the management orders (50% profit target / 1.5x stop / 21-DTE exit)."""
    n = int(c.get("contracts") or 1)
    exp = c.get("expiry")
    code = struct_code(c.get("structure"))
    legs = _legs(c, code, n, exp)
    credit = round(float(c.get("credit") or 0), 2)
    close_debit = round(credit * 0.5, 2)          # buy-to-close at 50% of credit
    stop_debit = round(credit * 2.5, 2)           # 1.5x credit loss => debit 2.5x credit
    max_loss_total = c.get("max_loss_total")
    if max_loss_total is None:
        max_loss_total = round(float(c.get("max_loss") or c.get("bpr") or 0) * n, 2)
    return {
        "underlying": c.get("underlying"),
        "code": code,
        "order_type": "Net Credit",
        "limit": credit,
        "contracts": n,
        "expiry": exp,
        "legs": [{"action": a, "qty": n, "expiry": exp, "strike": k, "type": t}
                 for (a, k, t) in legs],
        "credit_total": round(credit * 100 * n, 2),
        "max_loss_total": max_loss_total,
        "bpr_total": c.get("bpr_total") or round(float(c.get("bpr") or 0) * n, 2),
        "pop": c.get("pop"),
        "tag": c.get("tag"),
        "manage": {"profit_target_pct": 50, "close_debit": close_debit,
                   "stop_debit": stop_debit, "exit_dte": 21},
        "text": _text(c.get("underlying"), code, legs, exp, n, credit, close_debit, max_loss_total),
    }
