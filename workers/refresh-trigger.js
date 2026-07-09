/*
 * theta-refresh-trigger — a tiny Cloudflare Worker that lets the dashboard's
 * "⟳ REFRESH" button fire the GitHub `refresh` workflow.
 *
 * WHY a Worker: the dashboard is a public page, so it can't hold a GitHub token
 * (it would be stolen and auto-revoked). The token lives here, as a Worker secret,
 * and the Worker forwards a one-shot workflow_dispatch to GitHub. The browser only
 * ever talks to this Worker — never to GitHub directly.
 *
 * ─── 2-minute setup ────────────────────────────────────────────────────────────
 * 1. Create a GitHub token (fine-grained PAT):
 *      github.com → Settings → Developer settings → Fine-grained tokens → Generate
 *      - Repository access: ONLY  larrybfis/theta-engine
 *      - Permissions:  Actions → Read and write   (nothing else)
 *      - Expiration: your call (you'll re-paste it when it lapses)
 *    Copy the token (starts with github_pat_...).
 *
 * 2. Deploy this Worker:
 *      Cloudflare dashboard → Workers & Pages → Create → Worker → paste this file → Deploy.
 *      (Or add it as a new route on your existing decision Worker.)
 *
 * 3. Give the Worker the token as a SECRET (not a plain var):
 *      Worker → Settings → Variables and Secrets → Add → name: GH_TOKEN → paste the PAT → Encrypt.
 *
 * 4. Copy the Worker URL (e.g. https://theta-refresh-trigger.<you>.workers.dev) and
 *    paste it into REFRESH_ENDPOINT at the top of dashboard.html AND paper.html, then push.
 *
 * 5. (Recommended) Cap abuse: Cloudflare → your Worker → Settings → add a Rate Limiting
 *    rule, e.g. 6 requests/minute per IP. The button only triggers a data refresh
 *    (no trades, no secrets exposed), so worst case is wasted Actions minutes — the
 *    rate limit removes even that.
 * ────────────────────────────────────────────────────────────────────────────────
 */

const OWNER = "larrybfis";
const REPO = "theta-engine";
const WORKFLOW = "refresh.yml";
const REF = "main";

const CORS = {
  "Access-Control-Allow-Origin": "*",       // tighten to your Pages origin if you like
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") return new Response(null, { headers: CORS });
    if (request.method !== "POST") {
      return new Response("POST only", { status: 405, headers: CORS });
    }
    if (!env.GH_TOKEN) {
      return json({ ok: false, error: "GH_TOKEN secret not set on the Worker" }, 500);
    }
    const gh = await fetch(
      `https://api.github.com/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${env.GH_TOKEN}`,
          Accept: "application/vnd.github+json",
          "X-GitHub-Api-Version": "2022-11-28",
          "User-Agent": "theta-refresh-trigger",
        },
        body: JSON.stringify({ ref: REF }),
      }
    );
    // GitHub returns 204 No Content on a successful dispatch.
    const ok = gh.status === 204;
    return json({ ok, github_status: gh.status }, ok ? 200 : 502);
  },
};

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { ...CORS, "Content-Type": "application/json" },
  });
}
