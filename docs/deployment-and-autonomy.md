# FlightDeck Alpha — Deployment & Autonomy Runbook

End-to-end plan to ship the app to a single public URL, run it autonomously
during the judging window, and survive the Alpaca AI Trading Agents Hackathon
deadline (**September 4, 2026**) without babysitting. The hackathon is an
**online submission**, so the deployed URL and the public GitHub repo are
both required deliverables — not optional extras.

The previous version of this doc described a Render + Vercel split. The
code has since been refactored: a single multi-stage `Dockerfile` builds the
Vite SPA, installs the Alpaca CLI, and runs the FastAPI process. One image,
one URL, one persistent volume for the SQLite audit log. This rewrite
reflects that reality and folds the online-submission flow into the same
plan.

## Stack summary

- **Single container**: `Dockerfile` (multi-stage: Node 20 build for the SPA,
  Go 1.23 build for the Alpaca CLI, Python 3.12 slim runtime). Uvicorn serves
  both the FastAPI app (`/api/*`, `/health`) and the built Vite SPA from the
  same origin, so judges see one `https://<app>.fly.dev` URL.
- **Backend**: FastAPI on Python 3.12, served by `uvicorn`. SQLite at
  `backend/flightdeck_alpha.db` locally, `/data/flightdeck_alpha.db` on the
  deployed Fly machine. Talks to Alpaca paper trading via `alpaca-py` 0.42.0.
- **Frontend**: React + Vite + TypeScript. Vite dev server proxies `/api` and
  `/health` to the backend during local dev. In production the SPA is a
  static bundle served by FastAPI from `STATIC_DIR=/app/static`.
- **Audit store**: SQLite, same file as the runtime. Replay view reads from
  `audit_runs` / `system_runs`.
- **Autonomy**: a built-in `asyncio` scheduler (`backend/app/scheduler.py`)
  wakes up on a fixed cadence (default 15 minutes), runs scan + monitor
  cycles during market hours only, and writes audit events. No external cron
  service is required, but the existing API endpoints can still be poked by
  an external cron if we want belt-and-braces.

We use **Fly.io** because it gives us one URL, one Dockerfile, free
shared-cpu VMs, free 1 GB persistent volumes, and `https://<app>.fly.dev`
out of the box — which is exactly what the hackathon submission form wants
for the "Hosted demo application" field.

## 0. Pre-flight: secrets hygiene (do this first)

The local working tree currently contains a populated `.env` with what look
like live Alpaca paper keys. Treat them as compromised for the public repo
even though Alpaca paper keys do not move real money:

1. **Delete** `/.env` from the working tree. It is git-ignored, but it should
   not exist at all.
2. **Rotate** the Alpaca paper API key + secret from the Alpaca dashboard
   (paper account -> "View" -> "Regenerate"). Keep the new values only on
   Fly as secrets; never paste them into chat, screenshots, or git history.
3. **Rotate** the Gemini API key from Google AI Studio and store the new
   value on Fly.
4. Confirm `.gitignore` already blocks `.env`, `flightdeck_alpha.db`,
   `.venv`, `__pycache__`, and `node_modules/`. It does — keep it that way.
5. After the first deploy, run `git status` from a clean clone and
   confirm no `.env`, no `*.db`, no `*.sqlite*` files are tracked.

Skipping this step is the single biggest way a hackathon submission gets
disqualified for "credentials leak." It takes five minutes and removes a
whole category of risk.

## 1. Repository prep (30 minutes)

These steps happen **once** before deployment. The order matters because
secrets leak if you do it wrong.

1. Verify `.gitignore` excludes `.env`, `flightdeck_alpha.db`, `.venv`,
   `node_modules`, `__pycache__`, and `frontend/dist`. Open `.gitignore`
   and check; if any are missing, add them now. (They already are as of
   the latest code review.)
2. Delete `backend/flightdeck_alpha.db` from the working tree if it has
   any rows. The DB will be recreated on the Fly machine. Keep the local
   copy for development if you want, but it must not be committed.
3. Add a top-level `LICENSE` file (MIT is fine) and a `SECURITY.md` saying
   "issues: github.com/<you>/<repo>/security".
4. Push the project:

   ```powershell
   git init
   git add .
   git commit -m "Initial FlightDeck Alpha submission"
   git remote add origin https://github.com/<you>/flightdeck-alpha.git
   git push -u origin main
   ```

The hackathon submission form needs a **public GitHub URL**. The repo also
has to be the source of truth so a judge can clone and run it; the deployed
URL is the convenience, not the substitute.

## 2. Fly.io app setup (45 minutes)

We deploy a single Fly app named `flightdeck-alpha`. The repo already ships
`Dockerfile` and `fly.toml`, so the configuration is mostly declarative.

1. Sign in to `flyctl`:

   ```powershell
   fly auth signup            # or `fly auth login` if you already have an account
   ```

   No credit card is required for the free plan (three shared VMs + a 1 GB
   volume), which is enough for a 7-day hackathon.
2. Launch the app from the repo root (this reads `fly.toml`):

   ```powershell
   fly launch --no-deploy --copy-config
   ```

   When prompted, accept the default app name `flightdeck-alpha` (or change
   it and update `fly.toml`'s `app = "..."` line accordingly). Region: `iad`
   is already pinned in `fly.toml` — keep it unless you have a strong
   reason.
3. Create the persistent volume for the SQLite audit log:

   ```powershell
   fly volumes create flightdeck_alpha_data --size 1 --region iad
   ```

   The `[[mounts]]` block in `fly.toml` already binds this volume to
   `/data`. Without the volume, every redeploy wipes the audit log and the
   Replay page is empty after the first deploy.
4. Set the secrets. These are the values that must never be committed:

   ```powershell
   fly secrets set `
     ALPACA_API_KEY=<fresh paper key> `
     ALPACA_SECRET_KEY=<fresh paper secret> `
     GEMINI_API_KEY=<key>
   ```

   Use the **new** keys from step 0 — never the ones in the local `.env`.
   `fly secrets set` overwrites the env block in `fly.toml` for matching
   names; `fly.toml` already sets the non-secret defaults
   (`ALPACA_PAPER=true`, `ALPACA_TRADING_BASE_URL`, etc.) so the deploy is
   deterministic.
5. Optionally flip the autonomous scheduler on. By default `fly.toml`
   sets `SCHEDULER_ENABLED=false` so the first deploy is read-only and
   easy to debug. When the paper account is wired up and you want the
   cockpit to accumulate audit data on its own:

   ```powershell
   fly secrets set SCHEDULER_ENABLED=true
   fly deploy
   ```

   The scheduler runs `POST /api/scan` and `POST /api/monitor/run`
   internally on the configured cadence (default every 15 minutes,
   market-hours only, US equity session in UTC).
6. Deploy:

   ```powershell
   fly deploy
   ```

   The first deploy takes ~3-5 minutes because Fly builds the Docker image
   on its remote builder. Subsequent deploys are faster if the build cache
   is warm.
7. After the deploy finishes, Fly prints the public URL:
   `https://flightdeck-alpha.fly.dev`. Open it and confirm the cockpit
   loads.

## 3. Operating concerns during the judging window

### 3.1 Free-tier realities

The Fly free plan gives us three shared VMs and a 1 GB volume. The app is
configured to always keep one machine running (`min_machines_running = 1`)
and the SQLite audit DB lives on the persistent volume, so redeploys do
not wipe state. Clock-skew on `MONITOR_ACTION_COOLDOWN_HOURS` is a real
concern on shared VMs; do not depend on sub-minute timing for the judging
demo.

### 3.2 Scheduler behavior

When `SCHEDULER_ENABLED=true`:

- The scheduler wakes up every `SCHEDULER_INTERVAL_MINUTES` (default 15).
- Each cycle calls `POST /api/scan` and `POST /api/monitor/run` against
  the local FastAPI process (`http://127.0.0.1:8000`).
- Cycles that fall outside the US equity market window (13:00-20:30 UTC)
  are skipped when `SCHEDULER_MARKET_HOURS_ONLY=true` (the default).
- Each cycle emits a `scheduler_scan` and a `scheduler_monitor` row to
  `agent_events`, so the Replay page shows the scheduler is live.
- The scheduler is started by the FastAPI `lifespan` startup hook and
  stopped cleanly on shutdown, so rolling deploys do not leak tasks.

When the scheduler is off (the default), use the manual endpoints from
section 4 for the demo video.

### 3.3 Known risks

- **Alpaca paper rate limit.** The scanner pulls option chains for one
  symbol at a time. With a 15-minute cadence and 11 symbols in the
  universe, we are well under the 200 req/min limit. If a judge hammers
  the cockpit UI, you can read the 429 and back off; the API client
  already raises `AlpacaCredentialError` for missing creds, but rate
  limits raise generic `Exception`s which surface as 502.
- **DB disk fills up.** Audit log grows roughly 5 KB per cycle. A 1 GB
  persistent volume holds ~200k cycles — about 8 years at 15-min
  cadence. Not a real risk for a 7-day hackathon, but `VACUUM` once a
  week if paranoid. The volume size is set by
  `fly volumes create ... --size 1`.
- **Cold-start latency.** First request after Fly free VMs wake takes
  5-10s. With `auto_stop_machines = "off"` this should not happen, but
  if it does, hit `/health` once before the demo video to warm the
  process. Tell judges in the demo video that the first click can be a
  cold start; subsequent clicks are instant.
- **Time zone bugs.** The scanner uses `datetime.now(tz=UTC)` and the
  market-open check uses Alpaca's `is_open` clock — not local time. The
  submission does not need to be tweaked for IST vs EST.

## 4. End-to-end smoke test

Before recording the demo, run the following from your laptop, end-to-end
against the deployed URL. Every step should return 200 and the responses
should be identical to a local run.

```powershell
$env:API = "https://flightdeck-alpha.fly.dev"

# 1. Health
Invoke-RestMethod "$API/health"
# Expected: { status: ok, app: "FlightDeck Alpha", paper_mode: True, demo_mode: ... }

# 2. Settings
Invoke-RestMethod "$API/api/settings"
# Expected: alpaca_credentials_configured: True, scheduler_enabled: True (if you turned it on)

# 3. Account
Invoke-RestMethod "$API/api/account"

# 4. Scan
$scan = Invoke-RestMethod -Method Post "$API/api/scan" -ContentType 'application/json' -Body '{"limit":3}'
$top = $scan.candidates[0]

# 5. Propose
$prop = Invoke-RestMethod -Method Post "$API/api/proposals" -ContentType 'application/json' -Body (@{
  symbol = $top.symbol; direction = $top.direction; max_debit = 1500
} | ConvertTo-Json)
$pid = $prop.proposal_id

# 6. Dry-run execute
Invoke-RestMethod -Method Post "$API/api/trades/execute/$pid?dry_run=true"

# 7. Real paper execute (only if proposal was accepted)
if ($prop.accepted) {
  Invoke-RestMethod -Method Post "$API/api/trades/execute/$pid?dry_run=false"
}

# 8. Monitor with CLI proof
Invoke-RestMethod -Method Post "$API/api/monitor/run?sync_orders=true&cli_proof=true&execute_closes=false"

# 9. Audit
Invoke-RestMethod "$API/api/audit/runs?limit=10"
```

If every step returns 200, the deployed app is identical in behavior to a
local run. The Cockpit, Replay, Positions, Risk, and Settings pages should
all reflect those runs.

## 5. Online submission flow (lablab)

The hackathon submission is **online**. There is no in-person booth and no
emailed deliverable; judges download from the lablab form. The form asks
for exactly the fields below, so this section doubles as a copy-paste
checklist.

### 5.1 Submission fields

| Field | Value |
|---|---|
| Project title | `FlightDeck Alpha` |
| Short description | Use the draft from `docs/submission-tracker.md`. |
| Long description | One-paragraph product story + tech stack. |
| Tags | Alpaca, Trading API, MCP, CLI, AI agents, Options trading, Paper trading, Risk management, FastAPI, React. |
| Cover image | Render of the cockpit dashboard. See `docs/social-plan.md`. |
| Video presentation | YouTube / Loom link from the demo recording. |
| Slide presentation | Public link to the exported deck (Google Slides, PDF, or SlideShare). |
| Public GitHub repository | `https://github.com/<you>/flightdeck-alpha` |
| Hosted demo application | `https://flightdeck-alpha.fly.dev` |
| Alpaca paper trading account ID | The `PA...` string for the fresh $100k paper account wired into Fly. |
| Social post links | 3-5 links from `docs/social-plan.md`. |

### 5.2 Submission order of operations

Do these in order on submission day — reordering is a common way to break a
last-minute submission.

1. **Fresh paper account** is created and funded to $100,000 in the Alpaca
   dashboard. Copy the new `ALPACA_API_KEY` + `ALPACA_SECRET_KEY` into
   `fly secrets set ...` (do **not** put them in `fly.toml`). Confirm
   `GET /api/account` on the deployed URL shows `status: ACTIVE` and an
   equity of $100,000.
2. **Deploy** is live and the smoke test above has been run within the last
   30 minutes. The cockpit loads in an incognito window with no console
   errors.
3. **Demo video** has been recorded against the deployed URL (not localhost)
   and uploaded to YouTube / Loom. The video walks through cockpit -> scan
   -> proposal -> risk gate -> paper order -> audit replay, all on the
   hosted URL. Confirm the link is public (open it in an incognito window).
4. **Slide deck** is exported and uploaded (Google Slides public link or
   PDF). No speaker notes required, but the ten-slide outline in
   `docs/submission-tracker.md` should be visible.
5. **Cover image** is the cockpit dashboard screenshot with the deployed
   URL visible in the browser chrome. PNG or JPG, 1280x720 minimum.
6. **One-page write-up** is in `docs/one-page-writeup.md` and covers AI
   logic, risk gates, and Alpaca infrastructure implementation (CLI proof,
   paper endpoint, options orders). Copy the URL of the raw markdown (or
   a rendered PDF) into the submission form's "Additional links" field if
   the form has one.
7. **Public GitHub repo** has the latest commit pushed. Open the repo URL
   in an incognito window and confirm `README.md`, `LICENSE`, and
   `SECURITY.md` are visible. Confirm no `.env`, no `*.db`, no `*.sqlite*`,
   and no key-shaped strings (`AK...`, `PK...`, `sk-...`, `AIza...`) are
   in any committed file.
8. **Submit** on lablab. After submitting, the form gives you a submission
   edit URL — save it. If the judges ask for a fix during the window, you
   can re-edit the submission form without re-submitting from scratch.
9. **Post 3-5 social updates** with the deployed URL, the GitHub URL, and
   one short clip from the demo video. Use the templates in
   `docs/social-plan.md`. Save the URLs for the lablab form.

### 5.3 What to paste where

- **Public GitHub URL**: the `https://github.com/<you>/flightdeck-alpha`
  URL, not the SSH one. Open it in an incognito window and confirm it is
  public before pasting.
- **Hosted demo URL**: the `https://flightdeck-alpha.fly.dev` URL, **with
  the scheme**. lablab sometimes strips the scheme; paste it explicitly.
- **Alpaca paper account ID**: the `PA...` string visible in the Alpaca
  dashboard URL when you are logged into the paper account. Do **not**
  paste the API key — judges only need the account ID.
- **Video URL**: the share URL (e.g. `https://youtu.be/<id>` or
  `https://www.loom.com/share/<id>`), not the edit URL.

### 5.4 Submission-day failure modes

- **The hosted URL is asleep / cold-started**: Fly free shared VMs do not
  auto-stop because of the `auto_stop_machines = "off"` line in
  `fly.toml`, but if the app crashes, Fly will restart it within ~30
  seconds. To check, hit `https://flightdeck-alpha.fly.dev/health` once
  before you start the smoke test. The first click on the cockpit can
  take a few seconds; that is normal.
- **The form rejects the GitHub URL because it says "private"**: that
  usually means the repo is unverified on your lablab account, or the
  link was wrong. Open it in an incognito window to confirm; if it 404s,
  fix the link before submitting.
- **The deployed URL returns 502**: tail the logs first,
  `fly logs -a flightdeck-alpha`, and look for the last Python traceback.
  Common causes: missing secrets (`ALPACA_API_KEY`), wrong region for the
  Alpaca data endpoint, or the persistent volume not being attached.
  All three are recoverable without a redeploy.
- **Demo video link is private**: paste the share URL, not the edit URL,
  and re-confirm in an incognito window. Judges will not ask for
  re-sharing — they will simply mark the video as missing.
- **Submission edits are needed mid-window**: keep the edit URL from
  lablab. Edits are not flagged and do not reset your place in the queue.

## 6. What to do if something breaks mid-hackathon

- **A trade misbehaves**: the monitor's `take_profit` and `stop_loss` are
  computed off `cost_basis` from the live position, not off the proposal.
  If a trade goes wildly wrong, log into Alpaca, close the position
  manually, and write a follow-up `monitor_action` agent_event to keep
  the audit honest.
- **The market closes mid-demo**: `AlpacaGateway` already returns the live
  `is_open` flag, and the risk gate blocks proposals when the market is
  closed. Just narrate "the gate would now block this proposal because
  the market is closed" and run the proposal flow in `DEMO_MODE=true`
  instead. The demo switch is `DEMO_MODE=true` in `.env`, no code
  change.
- **The agent fires too many trades**: bump `MAX_OPEN_OPTION_TRADES` to 2
  and `MAX_SAME_UNDERLYING_TRADES` to 1, redeploy via `fly deploy`. The
  next cycle will respect the new limit because the risk gate reads the
  value at evaluation time, not at proposal time.
- **You need a hard stop**: set `MAX_TOTAL_PREMIUM_PCT=0.0` via
  `fly secrets set MAX_TOTAL_PREMIUM_PCT=0.0`. The risk gate will reject
  every proposal with `max_total_premium_deployed_exceeded` until you
  raise the limit again. This is the kill switch.
- **The deployed URL is down**: `fly logs -a flightdeck-alpha` first, then
  `fly status` to see the machine state, then `fly deploy` to re-roll.
  The persistent volume survives redeploys, so the audit log is intact.
- **lablab rejects a field on submission**: read the field hint carefully;
  the "Hosted demo application" field wants the deployed URL **with
  scheme**, the "Public GitHub repository" field wants the **https://**
  URL, and the "Alpaca paper trading account ID" wants the `PA...`
  string, not the API key.

## 7. Capturing proof for the submission

For the **video** and **one-pager**, capture the following artifacts and
store them in `docs/evidence/`:

1. The Alpaca paper account dashboard page (start balance $100,000) —
   screenshot only the account ID and equity.
2. The output of `GET /api/audit/runs?limit=5` — the JSON of the last 5
   runs.
3. The output of `POST /api/monitor/run?cli_proof=true` — proves the
   CLI integration is live.
4. A frame from the Replay page for the most recent run — proves the
   audit trail is end-to-end.
5. The first filled paper order ID, both in the UI and in the order
   response.
6. `fly status -a flightdeck-alpha` output showing the machine is
   `running` and the volume is `attached` — proves the deployment is
   live, not a cached screenshot.

These six artifacts, plus the hosted app URL, satisfy the judging
criteria for **Technology implementation**, **AI logic**, **Risk gates**,
and **Alpaca infrastructure implementation** simultaneously.

## 8. What to delete before final commit

To make the public repo clean:

- `backend/flightdeck_alpha.db` (do not commit your local DB; the Fly
  machine has its own on the persistent volume).
- Any `.env` (verify `.gitignore` blocks it; the repo does).
- `backend/.pytest_cache/`, `__pycache__/`, and the local `.venv` folder.
- The `node_modules` folder (already ignored) and `frontend/dist`
  (already ignored).
- Any test fixtures that embed real account IDs.

A clean `git status` before pushing is the single best defense against
leaking a paper API key. The Alpaca paper keys do not trade real money,
but lablab judges will notice and it is a low-trust signal.

## 9. Quick-reference command sheet

```powershell
# Build, test, and deploy
docker build -t flightdeck-alpha:dev .           # local sanity check
fly auth login
fly launch --no-deploy --copy-config            # first time only
fly volumes create flightdeck_alpha_data --size 1 --region iad
fly secrets set ALPACA_API_KEY=... ALPACA_SECRET_KEY=... GEMINI_API_KEY=...
fly secrets set SCHEDULER_ENABLED=true           # when ready to run autonomously
fly deploy

# Operate
fly status -a flightdeck-alpha
fly logs -a flightdeck-alpha
fly ssh console -a flightdeck-alpha              # for ad-hoc DB inspection

# Submit
# 1. Open https://lablab.ai/.../submit in an incognito window.
# 2. Paste the fields from section 5.1 above.
# 3. Save the edit URL.
# 4. Post 3-5 social updates from docs/social-plan.md.
```
