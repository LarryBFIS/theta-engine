# Approve/Reject webhook — setup (one-time, ~10 min)

This is the receiver for the **Approve / Reject** buttons. When you tap a choice
on the decision page, it calls this Cloudflare Worker, which records your
decision into the gist. The next bot tick reads it and confirms via Pushover.

**Record-only:** approving does NOT place an order. It logs your decision and
reminds you to execute in tastytrade. (Auto-execution is a later phase.)

```
Pushover "Review →"  →  decide.html  →  Cloudflare Worker  →  gist decisions.json  →  next tick
```

---

## Step 1 — Pick a shared secret

Make up a long random string (e.g. mash the keyboard, 30+ chars). Call it your
`DECISION_SECRET`. You'll paste the **same value** in two places below. This is
what stops a stranger from forging Approve/Reject on your account.

## Step 2 — Add it as a GitHub repo secret

GitHub → your repo → **Settings → Secrets and variables → Actions → New repository secret**

| Name | Value |
|---|---|
| `DECISION_SECRET` | the string from Step 1 |

(Optional) Only if your GitHub Pages URL differs from the default
`https://larrybfis.github.io/theta-engine/decide.html`, also add
`DECIDE_BASE_URL` with the correct URL.

## Step 3 — Create the Cloudflare Worker

1. Sign up / log in at <https://dash.cloudflare.com> (free).
2. **Workers & Pages → Create → Create Worker**. Name it e.g. `theta-decide`.
3. **Deploy** the starter, then **Edit code**.
4. Delete the sample code, paste the entire contents of [`worker.js`](./worker.js), **Deploy**.

## Step 4 — Set the Worker's secrets/variables

In the Worker → **Settings → Variables and Secrets**, add:

| Name | Type | Value |
|---|---|---|
| `DECISION_SECRET` | Secret | same string as Step 1 |
| `GIST_TOKEN` | Secret | a GitHub token with **gist** scope (the same value as your repo's `GIST_TOKEN` secret) |
| `GIST_ID` | Variable | `08e2cb50b3a645e9569617a6298ee987` |
| `ALLOW_ORIGIN` | Variable | `https://larrybfis.github.io` *(optional; this is the default)* |

Click **Deploy** again after adding them.

> Need a GitHub token? GitHub → **Settings (your account) → Developer settings →
> Personal access tokens → Tokens (classic) → Generate**, tick the **gist** scope.

## Step 5 — Point the page at your Worker

1. Copy your Worker's URL (looks like `https://theta-decide.<your-subdomain>.workers.dev`).
2. In `decide.html`, replace the `WORKER_URL` placeholder near the bottom with it.
3. Commit + push `decide.html`.

## Step 6 — Test it

1. Open `https://<your-worker-url>` directly in a browser → you should see
   `{"ok":false,"error":"POST only"}`. That means it's live.
2. Next time the bot sends an actionable alert, tap **Review →**, then **Approve**.
   Within ~10 minutes the next tick sends a `✓ ACCEPTED` Pushover confirmation
   and marks the suggestion `accepted` in `suggestions.json`.

---

## How the signature works (for reference)

`token = HMAC_SHA256(DECISION_SECRET, suggestion_id)` → hex → first 16 chars.
The bot (`monitor/approvals.py`) builds the link; the Worker recomputes and
compares. Known-answer test (secret `hunter2`, id `sug_abc`) →
`bfe87ed0b6d67b51` in both Python and the Worker. If you ever change the scheme,
update both and the test in `scripts/test_approvals.py`.
