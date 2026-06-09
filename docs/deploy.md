# Deploying Bill Buddy

Step-by-step guide for the stack Bill Buddy now uses in production:
**Render (backend) + Vercel (frontend) + Neon (database).**

This document is now both:
- the original deployment recipe
- the ongoing redeploy/maintenance reference for the live app

Estimated first-time setup: **~45 minutes of clicks** on your side.

---

## Status

- [x] Neon Postgres is in use
- [x] Backend is deployed on Render
- [x] Frontend is deployed on Vercel
- [x] CORS is configured to allow the production frontend origin

Exact live URLs are intentionally omitted from source control. Keep those in the hosting dashboards and environment settings.

---

## Prerequisites for a fresh redeploy

- [x] Neon Postgres account with a project + `DATABASE_URL` (see [neon-setup.md](./neon-setup.md))
- [ ] GitHub account
- [ ] Render account (free, no credit card) — sign up at https://render.com
- [ ] Vercel account (free, login with GitHub) — sign up at https://vercel.com

---

## Step 1: Push the repo to GitHub

If you haven't already:

```bash
# In the project root
cd /Users/minhle/Documents/bill-buddy

# Make sure .env is gitignored (it is) — never commit secrets
git status

# Create a new repo on github.com (private is fine), then:
git remote add origin git@github.com:YOUR_USERNAME/bill-buddy.git
git branch -M main
git add .
git commit -m "Prep for Render + Vercel deploy"
git push -u origin main
```

If `git remote add` fails because there's already an `origin`, use `git remote set-url origin git@github.com:YOUR_USERNAME/bill-buddy.git`.

---

## Step 2: Deploy backend to Render

### 2a. Create the Web Service

1. Go to **https://dashboard.render.com**
2. Click **New +** → **Web Service**
3. Connect your GitHub account if you haven't
4. Pick the **bill-buddy** repo
5. Render should detect [render.yaml](../render.yaml) and pre-fill most fields. If not, set them manually:
   - **Name:** `bill-buddy-api`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt && cd backend && alembic upgrade head`
   - **Start Command:** `uvicorn api.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
   - **Plan:** Free
   - **Health Check Path:** `/healthz`

### 2b. Set environment variables

In the Render dashboard → your service → **Environment** tab:

| Key | Value | Notes |
| --- | --- | --- |
| `DATABASE_URL` | Your Neon URL (the `postgresql+psycopg://...` form) | Paste from your local `.env` |
| `JWT_SECRET_KEY` | `(generated)` | Click **Generate** for a 64-char random value |
| `ALLOWED_ORIGINS` | *Leave unset for first deploy* | Defaults to localhost dev. Set it to the Vercel URL in Step 4. |
| `ENV` | `production` | Forces `JWT_SECRET_KEY` to be required |
| `PYTHON_VERSION` | `3.12.7` | Matches `runtime.txt` |

> Why not `ALLOWED_ORIGINS=*`? FastAPI's CORS rejects `*` when `allow_credentials=True` (which we use). We'll set the real Vercel URL after that's deployed. Until then, you can only test the API via `curl` — browser requests from the Vercel UI will fail CORS, which is expected.

### 2c. Deploy

1. Click **Create Web Service** (or **Deploy**)
2. Watch the build log. First build takes ~3-5 minutes.
3. You'll see `alembic upgrade head` apply migrations to Neon (no-op if already migrated).
4. When done, note the URL — looks like `https://bill-buddy-api.onrender.com`

### 2d. Verify

```bash
curl https://bill-buddy-api.onrender.com/healthz
# Expected: {"ok":true,"service":"bill-buddy-api"}
```

If it returns 404 or hangs, check the Render logs. First request after deploy can take ~30s as the free tier wakes.

---

## Step 3: Deploy frontend to Vercel

### 3a. Create the project

1. Go to **https://vercel.com/dashboard**
2. **Add New...** → **Project**
3. Import the **bill-buddy** repo
4. Configure:
   - **Root Directory:** `frontend` (important — click "Edit" next to root directory)
   - **Framework Preset:** Vite (auto-detected)
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `dist` (default)

### 3b. Set environment variables

Before clicking Deploy, expand **Environment Variables** and add:

| Key | Value |
| --- | --- |
| `VITE_API_BASE_URL` | Your Render URL from Step 2d (e.g. `https://bill-buddy-api.onrender.com`) |

### 3c. Deploy

1. Click **Deploy**. First build takes ~1 minute.
2. Note the Vercel URL — looks like `https://bill-buddy-xyz.vercel.app`

---

## Step 4: Lock down CORS

Now that you know the Vercel URL, set Render's `ALLOWED_ORIGINS` to it specifically.

1. Render dashboard → your service → **Environment**
2. Edit `ALLOWED_ORIGINS`
3. New value: `https://bill-buddy-xyz.vercel.app` (your real Vercel URL)
4. Save changes — Render redeploys automatically (~1 minute)

---

## Step 5: End-to-end test

Open your Vercel URL in a browser:

1. You should see the login page (auth context redirects unauthed users)
2. Click "Get started" → enter email + password (≥8 chars)
3. You should land on the empty trips list
4. Create a trip with 2-3 members
5. Click into it, copy the share link from the **Share** button
6. Open the share link in an incognito window
7. From the incognito window, add an expense
8. Switch back to your authed tab — refresh — the expense should appear

If any step fails, check:
- **Render logs** for backend errors
- **Browser console** for frontend errors (often a CORS mismatch)
- That `VITE_API_BASE_URL` and `ALLOWED_ORIGINS` URLs match exactly (no trailing slash differences)

---

## Ongoing deploy workflow

After the app is live, the normal release path is:

1. Push code to GitHub
2. Merge to `main`
3. Vercel auto-deploys the frontend
4. Render auto-deploys the backend
5. Render runs Alembic migrations during the build
6. Smoke-test signup/login, trip creation, and a share link

For backend-only env changes like `ALLOWED_ORIGINS` or `JWT_SECRET_KEY`, update the Render dashboard and let it redeploy.

For frontend-only env changes like `VITE_API_BASE_URL`, update the Vercel project settings and redeploy there.

---

## Optional: Reduce cold starts

Render free tier sleeps your service after 15 minutes of idle traffic, causing a ~30s wake-up on the next visit.

**Workarounds:**
1. **Accept it** — fine for personal/hobby use.
2. **External pinger** — UptimeRobot's free tier can hit `/healthz` every 5 min. (Note: Render's free tier ToS technically frown on this if abused.)
3. **Pay $7/mo** for the Starter plan (no sleep).

For a $0 hobby app, Option 1 is recommended.

---

## Common issues

| Symptom | Fix |
| --- | --- |
| `502 Bad Gateway` on first visit | Cold start — wait 30s, refresh. |
| CORS error in browser console | Check `ALLOWED_ORIGINS` exactly matches the Vercel URL (no trailing slash). |
| `401 Unauthorized` on every request | `JWT_SECRET_KEY` was rotated and old tokens are invalid. Sign out, sign back in. |
| `psycopg.OperationalError` in Render logs | `DATABASE_URL` is wrong, or Neon is asleep waking up. Wait, retry. |
| Build fails on `alembic upgrade head` | Connection string format wrong. Ensure it's `postgresql+psycopg://...?sslmode=require`. |
| Frontend route 404s on direct visit (e.g. `/share/abc`) | Make sure [frontend/vercel.json](../frontend/vercel.json) is committed — provides SPA fallback. |
| Render keeps redeploying | Check the **Deploys** tab. Auto-deploy from `main` branch is on by default — push to a branch if you want to test before deploying. |

---

## Updating after deploy

Any push to `main` triggers automatic redeploys on both Render and Vercel. To deploy a feature:

```bash
git checkout -b feature/something
# ... make changes ...
git commit -am "Add something"
git push origin feature/something
# Open a PR on GitHub, merge to main → auto-deploy
```

For schema changes, **always** generate an Alembic migration locally and commit it. Render's build command runs `alembic upgrade head` automatically, so no manual DB intervention should be needed.

---

## When to revisit

- **App grows beyond ~100 active users** — pay $7/mo on Render for no-sleep, $19/mo on Neon for more compute.
- **You add file uploads (receipt OCR)** — wire in Cloudflare R2 (10 GB free, no egress fees).
- **You want a custom domain** — buy from Namecheap/Cloudflare (~$10/yr), point it at Vercel + Render.
- **You add AI features** — see Phase 7 in [project-plan.md](./project-plan.md). Plan a BYOK or quota model since Claude API isn't free.
