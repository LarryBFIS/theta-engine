/**
 * theta-engine — Approve/Reject webhook (Cloudflare Worker).
 *
 * Receives a decision from decide.html, verifies its signature, and records it
 * into the gist (decisions.json). The next bot tick reads that file and marks
 * the matching suggestion accepted/rejected. RECORD-ONLY: no orders are placed.
 *
 * Required Worker secrets / vars (set in the Cloudflare dashboard):
 *   DECISION_SECRET  — same shared secret as the bot's DECISION_SECRET
 *   GIST_TOKEN       — GitHub token with `gist` scope (write access to the gist)
 *   GIST_ID          — the gist id (08e2cb50b3a645e9569617a6298ee987)
 * Optional vars:
 *   DECISIONS_FILE   — filename in the gist (default "decisions.json")
 *   ALLOW_ORIGIN     — CORS origin (default "https://larrybfis.github.io")
 *
 * Signature scheme MUST match monitor/approvals.py:
 *   token = HMAC_SHA256(DECISION_SECRET, suggestion_id) -> hex -> first 16 chars
 */

const TOKEN_LEN = 16;

export default {
  async fetch(request, env) {
    const origin = env.ALLOW_ORIGIN || "https://larrybfis.github.io";
    const cors = {
      "Access-Control-Allow-Origin": origin,
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type",
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors });
    }
    if (request.method !== "POST") {
      return json({ ok: false, error: "POST only" }, 405, cors);
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return json({ ok: false, error: "invalid JSON" }, 400, cors);
    }

    const id = (body.id || "").toString();
    const token = (body.t || "").toString();
    const action = (body.action || "").toString().toLowerCase();

    if (!id || !token) return json({ ok: false, error: "missing id/token" }, 400, cors);
    if (action !== "accept" && action !== "reject") {
      return json({ ok: false, error: "action must be accept|reject" }, 400, cors);
    }

    const expected = await signToken(env.DECISION_SECRET || "", id);
    if (!constantTimeEqual(token, expected)) {
      return json({ ok: false, error: "bad signature" }, 403, cors);
    }

    try {
      await recordDecision(env, id, action);
    } catch (e) {
      return json({ ok: false, error: "gist write failed: " + e.message }, 502, cors);
    }

    return json({ ok: true, id, action }, 200, cors);
  },

  // Reliable scheduling: a Cloudflare Cron Trigger invokes this on a timer and
  // we fire the GitHub `tick` workflow via repository_dispatch. This sidesteps
  // GitHub's unreliable native cron. Requires a GITHUB_DISPATCH_TOKEN secret
  // (classic PAT with `repo` scope) and a Cron Trigger configured on the Worker.
  async scheduled(event, env, ctx) {
    // The cron fires every day in the hour window; the *worker* decides whether
    // to act, so we never depend on Cloudflare's day-of-week interpretation.
    // Only act on weekdays during US market hours (13:00-20:59 UTC).
    const now = new Date();
    const dow = now.getUTCDay();   // 0=Sun .. 6=Sat
    const hour = now.getUTCHours();
    if (dow < 1 || dow > 5 || hour < 13 || hour > 20) {
      console.log("scheduled: outside market window (dow=" + dow + " hour=" + hour + "); skipping");
      return;
    }
    // On a real market tick: (1) fire the GitHub tick, (2) run the deadman watchdog.
    await dispatchTick(env);
    await deadmanCheck(env);
  },
};

async function dispatchTick(env) {
  const token = env.GITHUB_DISPATCH_TOKEN;
  if (!token) {
    console.log("dispatchTick: no GITHUB_DISPATCH_TOKEN set; skipping");
    return;
  }
  const repo = env.DISPATCH_REPO || "LarryBFIS/theta-engine";
  try {
    const res = await fetch(`https://api.github.com/repos/${repo}/dispatches`, {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "User-Agent": "theta-decide-cron",
        "X-GitHub-Api-Version": "2022-11-28",
      },
      body: JSON.stringify({ event_type: "tick" }),
    });
    console.log("dispatchTick: tick dispatch ->", res.status);
  } catch (e) {
    console.log("dispatchTick: failed:", e.message);
  }
}

// Deadman watchdog: if the bot's last gist poll is stale, fire a Pushover
// emergency. Runs on Cloudflare's reliable cron (already restricted to market
// hours), so it backstops the bot even if GitHub scheduling stalls entirely.
async function deadmanCheck(env) {
  if (!env.PUSHOVER_APP_TOKEN || !env.PUSHOVER_USER_KEY) {
    console.log("deadmanCheck: no Pushover creds; skipping");
    return;
  }
  const url = `https://gist.githubusercontent.com/LarryBFIS/${env.GIST_ID}/raw/last_poll.json?_=${Date.now()}`;
  let lastPoll;
  try {
    const r = await fetch(url, { cf: { cacheTtl: 0 } });
    if (!r.ok) { console.log("deadmanCheck: gist fetch", r.status); return; }
    lastPoll = (await r.json()).last_poll_at;
  } catch (e) {
    console.log("deadmanCheck: gist fetch failed:", e.message);
    return;
  }
  if (!lastPoll) return;
  const ageMin = (Date.now() - new Date(lastPoll).getTime()) / 60000;
  // Alert ONLY within a bounded window after the poll goes stale — mirrors the
  // GitHub deadman. Below staleMin: fine. Above windowMax: this is the NORMAL
  // overnight/weekend gap (the bot only runs market hours; the morning's first
  // poll refreshes it), so alerting just spams a burst every single market open.
  // Single priority-1 ping (bypasses quiet hours) with NO retry/expire, so one
  // genuine stall pages exactly once instead of re-buzzing for an hour.
  const staleMin = parseFloat(env.DEADMAN_STALE_MIN || "60");
  const windowMax = parseFloat(env.DEADMAN_WINDOW_MAX_MIN || "180");
  if (ageMin <= staleMin || ageMin > windowMax) {
    console.log("deadmanCheck: no alert, last poll", Math.round(ageMin), "min ago");
    return;
  }
  console.log("deadmanCheck: STALE", Math.round(ageMin), "min — alerting (once)");
  await fetch("https://api.pushover.net/1/messages.json", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      token: env.PUSHOVER_APP_TOKEN,
      user: env.PUSHOVER_USER_KEY,
      title: "theta-engine: poll stale",
      message: `Last poll ${Math.round(ageMin)} min ago (${lastPoll}). Check the workflows.`,
      priority: "1",
    }),
  });
}

async function signToken(secret, sugId) {
  const enc = new TextEncoder();
  const key = await crypto.subtle.importKey(
    "raw", enc.encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(sugId));
  const hex = [...new Uint8Array(sig)].map((b) => b.toString(16).padStart(2, "0")).join("");
  return hex.slice(0, TOKEN_LEN);
}

function constantTimeEqual(a, b) {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

async function recordDecision(env, id, action) {
  const file = env.DECISIONS_FILE || "decisions.json";
  const gistUrl = "https://api.github.com/gists/" + env.GIST_ID;
  const headers = {
    "Authorization": "Bearer " + env.GIST_TOKEN,
    "Accept": "application/vnd.github+json",
    "User-Agent": "theta-engine-worker",
    "X-GitHub-Api-Version": "2022-11-28",
  };

  // Read existing decisions (if the file exists yet).
  let decisions = {};
  const getRes = await fetch(gistUrl, { headers });
  if (getRes.ok) {
    const gist = await getRes.json();
    const existing = gist.files && gist.files[file];
    if (existing && existing.content) {
      try {
        const parsed = JSON.parse(existing.content);
        decisions = parsed.decisions || {};
      } catch { /* start fresh on parse error */ }
    }
  }

  decisions[id] = { action, at: new Date().toISOString(), source: "pushover-web" };
  const content = JSON.stringify({ schema_version: 1, decisions }, null, 2) + "\n";

  const patchRes = await fetch(gistUrl, {
    method: "PATCH",
    headers,
    body: JSON.stringify({ files: { [file]: { content } } }),
  });
  if (!patchRes.ok) {
    throw new Error("HTTP " + patchRes.status);
  }
}

function json(obj, status, cors) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json", ...cors },
  });
}
