# Bill Buddy — Project Plan

End-to-end roadmap and **handoff document** for Bill Buddy: a multi-user web app for tracking shared trip expenses, evolved from a Flask MVP into a FastAPI + React app deployed for free on Render + Vercel + Neon.

This file is the single source of truth for what's been built, what's pending, and the key decisions made along the way. If you're a new contributor (human or AI) picking this up, read this top-to-bottom first.

---

## Current state — June 2026

**Phases 1–4 complete. Phase 5 Piece 1 (auth + share links) complete locally. Phase 5 Pieces 2 & 3 (Render + Vercel deployment) are next.**

What works right now, locally:
- FastAPI backend with 34 endpoints, talking to Neon Postgres via SQLAlchemy + Alembic
- JWT-based auth: signup, login, /me, owner-isolated trip access
- Share-link sharing: anyone with a `/api/share/{token}` URL can view + add/edit expenses, no signup required
- React + Vite + TypeScript + Tailwind + shadcn/ui frontend with emerald theme and system dark mode
- 65 backend tests passing (25 pure-math + 23 trip API + 10 auth + 7 share)

Live: nowhere yet. Local dev only.

---

## Target architecture

```
Browser
   │
   ├──► Vercel  ─────────────► React + Vite + TypeScript + Tailwind + shadcn/ui
   │                                    │
   │                                    │ (HTTPS, JSON, Bearer token in localStorage)
   ▼                                    ▼
Render free web service  ──────► FastAPI + SQLAlchemy + Alembic + JWT (HS256)
                                          │
                                          ▼
                              Neon (free Postgres)
```

**Cost target:** $0/month. Custom domain optional (~$10/yr).

---

## Tech stack (final, as built)

| Layer | Choice | Notes |
| --- | --- | --- |
| Backend framework | FastAPI 0.136 | |
| ORM | SQLAlchemy 2.0 | |
| Migrations | Alembic 1.18 | |
| Validation | Pydantic v2 (2.13) | EmailStr requires `email-validator` |
| Password hashing | `bcrypt` 5.x **(direct, not via passlib)** | passlib 1.7 is incompatible with bcrypt 5; we use `bcrypt.hashpw` / `bcrypt.checkpw` directly. See [backend/api/auth.py](../backend/api/auth.py). |
| JWT | `python-jose[cryptography]` | HS256, 7-day expiry |
| HTTP server | uvicorn `[standard]` | Procfile uses uvicorn directly, not gunicorn |
| Frontend framework | React 19 + Vite 8 + TypeScript | |
| Styling | Tailwind v4 (`@tailwindcss/vite`) + shadcn (Nova preset) | Emerald primary, Geist font, Lucide icons, `--radius: 0.875rem` |
| Data fetching | TanStack Query 5 | |
| Routing | React Router 7 | |
| HTTP client | axios with request/response interceptors | Auto-adds Bearer header, handles 401 globally |
| Auth storage | `localStorage` | Acceptable for hobby app; revisit if XSS surface grows |
| Backend host | Render free web | Sleeps after 15 min idle, ~30s cold start |
| Frontend host | Vercel Hobby | Free, no sleep |
| Database | Neon Postgres free | Scales compute to zero after 5 min, ~1s wake |

---

## Repository layout

```
bill-buddy/
├── README.md                            # original Flask-era README, somewhat stale
├── docs/
│   ├── project-plan.md                  # THIS FILE — the source of truth
│   ├── neon-setup.md                    # Neon signup + connection string steps
│   └── deploy.md                        # (TBD) deploy walkthrough for Render + Vercel
├── .env.example                         # JWT_SECRET_KEY, DATABASE_URL, ALLOWED_ORIGINS
├── .env                                 # gitignored; contains real Neon URL + secrets
├── Procfile                             # `web: uvicorn api.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
├── render.yaml                          # (TBD) Render IaC for one-click deploy
├── pytest.ini                           # testpaths=tests, pythonpath=backend
├── requirements.txt                     # production deps
├── requirements-dev.txt                 # +pytest, +httpx
├── tests/
│   ├── conftest.py                      # `unauth_client`, `client` (pre-authed) fixtures
│   ├── test_calculations.py             # 25 pure-math tests
│   ├── test_api.py                      # 23 owner-authed trip/expense tests
│   ├── test_auth.py                     # 10 auth flow tests
│   └── test_share.py                    # 7 share-link tests
├── backend/
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py                       # loads DATABASE_URL via dotenv, render_as_batch on SQLite
│   │   └── versions/
│   │       ├── d426f66146cd_initial.py
│   │       └── 16a104b94ab5_add_users_and_trip_ownership.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI app, CORS, mount routers, /healthz
│   │   ├── database.py                  # engine, SessionLocal, Base, get_db, dotenv load
│   │   ├── models.py                    # User, Trip, Member, Expense, ExpenseParticipant
│   │   ├── schemas.py                   # Pydantic models (~20)
│   │   ├── auth.py                      # bcrypt hash/verify + JWT encode/decode + share token gen
│   │   ├── dependencies.py              # get_current_user, get_owned_trip, get_shared_trip, etc.
│   │   ├── serializers.py               # serialize_expense() helper
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── auth.py                  # /api/auth/{signup,login,me}
│   │       ├── trips.py                 # /api/trips/... + shared helpers used by share router
│   │       ├── expenses.py              # /api/expenses/{id}
│   │       └── share.py                 # /api/share/{token}/... (public)
│   └── utils/                           # framework-agnostic helpers
│       ├── calculations.py              # split math, settlement minimization (pure)
│       ├── helpers.py                   # parse_money_to_cents, format_cents
│       └── db.py                        # NO LONGER USED (Flask-era raw sqlite3)
└── frontend/
    ├── index.html                       # contains dark-mode-before-paint script
    ├── package.json
    ├── vite.config.ts                   # Tailwind plugin, @/ alias, /api proxy → :8000
    ├── tsconfig.app.json                # @/* paths, ignoreDeprecations: "6.0"
    ├── components.json                  # shadcn config
    └── src/
        ├── App.tsx                      # QueryClient + AuthProvider + Routes + Toaster
        ├── main.tsx
        ├── index.css                    # shadcn theme (customized: emerald primary)
        ├── api/
        │   ├── types.ts                 # All TS interfaces matching Pydantic schemas
        │   ├── client.ts                # axios + interceptors + api.* methods + api.share.*
        │   ├── auth-storage.ts          # localStorage helpers for token + user
        │   └── queryKeys.ts             # centralized TanStack Query key registry
        ├── contexts/
        │   └── AuthContext.tsx          # login/signup/logout state, mounts on app
        ├── hooks/
        │   ├── useAuth.ts
        │   ├── useTrips.ts              # owner trips
        │   ├── useExpenses.ts           # owner expenses
        │   ├── useTripDerived.ts        # owner balances/settlements/summary
        │   ├── useSharedTrip.ts         # share-token equivalents
        │   └── useMembers.ts            # add/remove + extractApiErrorMessage helper
        ├── components/
        │   ├── Layout.tsx               # header with logo + nav + user email + logout
        │   ├── RequireAuth.tsx          # protected route wrapper
        │   ├── ExpenseForm.tsx          # shared add/edit form
        │   ├── ShareTripDialog.tsx      # copy link + rotate token
        │   └── ui/                      # 13 shadcn primitives
        ├── lib/
        │   ├── utils.ts                 # shadcn cn()
        │   └── format.ts                # formatCents, parseAmountToCents, todayIso
        └── pages/
            ├── LoginPage.tsx
            ├── SignupPage.tsx
            ├── TripsListPage.tsx
            ├── CreateTripPage.tsx
            ├── TripDetailPage.tsx      # opens ShareTripDialog
            ├── TripSummaryPage.tsx
            ├── AddExpensePage.tsx
            ├── EditExpensePage.tsx
            ├── ShareTripPage.tsx        # public viewer
            ├── ShareAddExpensePage.tsx
            ├── ShareEditExpensePage.tsx
            └── PlaceholderPage.tsx      # 404 fallback
```

---

## API endpoint inventory (34 routes)

### Public
- `GET /healthz` — health check
- `POST /api/auth/signup` — email + password, returns `{access_token, user}`
- `POST /api/auth/login` — same shape

### Owner-authenticated (`Authorization: Bearer <JWT>` required)
- `GET /api/auth/me`
- `GET /api/trips` — only the user's trips
- `POST /api/trips` — body includes members[]; share_token auto-generated
- `GET /api/trips/{trip_id}`
- `DELETE /api/trips/{trip_id}` — 204
- `POST /api/trips/{trip_id}/rotate-share-token` — invalidates old link
- `POST /api/trips/{trip_id}/members` — 409 if duplicate is_self
- `DELETE /api/trips/{trip_id}/members/{member_id}` — 409 if member paid for any expense
- `POST /api/trips/{trip_id}/expenses`
- `GET /api/trips/{trip_id}/expenses?payer_id=&from=&to=`
- `GET /api/trips/{trip_id}/balances`
- `GET /api/trips/{trip_id}/settlements`
- `GET /api/trips/{trip_id}/summary`
- `GET /api/trips/{trip_id}/expenses.csv`
- `GET /api/expenses/{expense_id}`
- `PATCH /api/expenses/{expense_id}` — partial update
- `DELETE /api/expenses/{expense_id}`

### Share-token (public, no auth — auth is the URL itself)
- `GET /api/share/{token}` — trip detail
- `GET /api/share/{token}/expenses`
- `POST /api/share/{token}/expenses`
- `PATCH /api/share/{token}/expenses/{expense_id}`
- `DELETE /api/share/{token}/expenses/{expense_id}`
- `POST /api/share/{token}/members`
- `GET /api/share/{token}/balances`
- `GET /api/share/{token}/settlements`
- `GET /api/share/{token}/summary`
- `GET /api/share/{token}/expenses.csv`

**Owner-only actions deliberately NOT mirrored on share routes:** delete trip, rotate share token, delete member. Casual share-link users can edit data but can't structurally change the trip.

---

## Environment variables

### Backend (FastAPI)
| Var | Required? | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Prod yes / Dev no | SQLAlchemy URL. Format: `postgresql+psycopg://USER:PWD@HOST/DB?sslmode=require`. Dev falls back to local SQLite at project root. |
| `JWT_SECRET_KEY` | Prod yes / Dev no | Signs JWTs. Generate: `python -c 'import secrets; print(secrets.token_hex(32))'`. In dev a fixed placeholder is used. |
| `ALLOWED_ORIGINS` | Optional | Comma-separated. Defaults to `http://localhost:5173,http://127.0.0.1:5173`. In prod, set to your Vercel URL. |
| `PORT` | Render auto-sets | Used by uvicorn. |
| `FLASK_ENV=production` or `ENV=production` | Recommended | Makes `JWT_SECRET_KEY` strictly required (raises if missing). |

### Frontend (Vite)
| Var | Required? | Purpose |
| --- | --- | --- |
| `VITE_API_BASE_URL` | Prod yes | Render URL like `https://bill-buddy-api.onrender.com`. Empty in dev (uses Vite proxy). |

---

## Key design decisions and gotchas

1. **bcrypt direct, not passlib.** Passlib 1.7.4 (last release 2020) checks `bcrypt.__about__.__version__` on first use, which doesn't exist in bcrypt 5. We dropped passlib and call `bcrypt.hashpw` / `bcrypt.checkpw` directly. See [backend/api/auth.py](../backend/api/auth.py). The 72-byte password limit is handled by `_encode_password` which slices at the boundary — standard practice.

2. **`test.local` is rejected by EmailStr** as a reserved TLD. Tests use `example.com` addresses.

3. **`render_as_batch=True` for SQLite migrations** is in `alembic/env.py`. The actual migration files were generated against Postgres so they use plain `op.create_foreign_key` — running migrations against SQLite would fail. Tests don't hit this path because they use `Base.metadata.create_all` instead of Alembic.

4. **Share routes are `/api/share/{token}/...` — they don't 401.** The token IS the credential. The interceptor in [src/api/client.ts](../frontend/src/api/client.ts) checks the URL and skips the 401 → /login redirect for share routes.

5. **Owner check is a 404, not 403.** When user A tries to access user B's trip, they get 404, not 403. Prevents existence leakage of other users' trip IDs.

6. **CORS uses `allow_origins=[...]`, not `allow_origin_regex` or `*`.** With `allow_credentials=True`, wildcards aren't allowed. Add specific origins via `ALLOWED_ORIGINS` env var.

7. **Pydantic schema `created_at: datetime`** means SQLAlchemy serializes ISO 8601 (`"2026-06-03T17:03:00"`). The Flask era stored the raw SQLite string. Frontend code expects ISO 8601.

8. **`backend/init_db.py`, `backend/schema.sql`, `backend/utils/db.py` are dead code** kept for now in case of reference. Safe to delete in a cleanup pass.

9. **FastAPI default error envelope `{"detail": "..."}`** is preserved (the plan originally called for a custom `{error: {code, message}}` envelope; we kept the default for ecosystem compatibility with Axios/TanStack Query).

10. **No frontend tests yet.** Backend has 65 tests. Frontend has type checks only. A future polish task.

---

## Phase 1 — FastAPI backend skeleton ✅

Built a parallel FastAPI app returning JSON, no DB changes. Reused `utils/calculations.py` and `utils/helpers.py` via shared import path.

**Final delta:** `backend/api/__init__.py`, `backend/api/main.py`, `backend/api/schemas.py`. Two read-only endpoints (`GET /api/trips`, `GET /api/trips/{trip_id}`). `/docs` Swagger UI working. 25 existing tests still pass.

## Phase 2 — Postgres + SQLAlchemy + Alembic ✅

Moved from raw `sqlite3` to SQLAlchemy 2.0 + Alembic. Created Neon Postgres project, applied initial migration. Endpoints now use ORM sessions.

**Final delta:** `backend/api/database.py`, `backend/api/models.py`, `backend/alembic/`, initial migration `d426f66146cd_initial.py`. Local SQLite stamped at head so Alembic doesn't try to recreate. `.env.example` documents `DATABASE_URL` format.

## Phase 3 — Full JSON API ✅

Every Flask feature reimplemented as a JSON endpoint. Flask code removed.

**Final delta:** 14 owner endpoints; CORS middleware; 23 integration tests using `TestClient` with isolated SQLite per test; removed `backend/app.py`, `frontend/templates/`, `frontend/static/style.css`; updated `Procfile` to uvicorn; pruned Flask deps from `requirements.txt`.

**Deviation from plan:** Custom error envelope skipped — kept FastAPI default `{"detail": "..."}`.

## Phase 4 — React frontend ✅

Built a React + Vite + TypeScript + Tailwind + shadcn UI from scratch, mirroring the Flask app's pages.

**Style choices the user picked:**
- Friendly/playful vibe (rounded corners, soft shadows)
- Emerald green accent
- System-following dark mode
- Comfortable density

**Final delta:** New `frontend/` directory. shadcn Nova preset (Geist font, Lucide icons), customized to emerald primary + `--radius: 0.875rem` + system dark mode via script in `index.html`. Pages built directly with shadcn — Lovable workflow skipped (Path B chosen). All flows working end-to-end against localhost FastAPI.

**Deviation from plan:** No Lovable. Pages duplicated for share-token mode in Phase 5 (could be refactored later).

## Phase 5 Piece 1 — Auth + share links ✅

**Sharing model chosen:** Share link (Option B in the original three-way fork). Anyone with the link can view + add/edit expenses, no signup. Friends-on-a-trip use case.

**Backend:**
- `User` model with email (unique, indexed) + bcrypt password_hash
- `Trip.owner_user_id` (FK to users, CASCADE) + `Trip.share_token` (unique, indexed, 22-char URL-safe random)
- Migration `16a104b94ab5_add_users_and_trip_ownership.py` applied to Neon
- New routers: `auth.py` (signup/login/me), `share.py` (public via token)
- Existing trips/expenses routers refactored to require auth + verify ownership via dependencies
- 17 new tests covering signup, login, owner isolation, share-link flows, token rotation

**Frontend:**
- AuthContext with login/signup/logout, token in localStorage, verifies token on mount via `/me`
- Axios request interceptor adds `Authorization: Bearer <token>`
- Axios response interceptor handles 401: clears storage, redirects to `/login`, but **skips share routes** (which legitimately don't auth)
- `RequireAuth` wraps protected routes; unauthenticated users redirect to `/login` preserving the original path
- `LoginPage` + `SignupPage` with inline validation
- Header shows user email + logout when authed; "Sign in / Get started" when not
- `ShareTripDialog` (Copy / Rotate) on trip detail page
- Public viewer pages: `ShareTripPage`, `ShareAddExpensePage`, `ShareEditExpensePage` using `useSharedTrip` hooks
- Banner on share pages explaining "you're viewing via a share link — no account needed"

**Bug encountered during build:** Passlib + bcrypt 5 incompatibility. Fix: dropped passlib, use bcrypt directly.

---

## Phase 5 Piece 2 — Deploy backend to Render 🔜

**User action required:** sign up at https://render.com (free, no card). Push code to GitHub.

**Code prep (assistant's job, done before user clicks):**
- [ ] Add `render.yaml` (IaC for one-click deploy)
- [ ] Confirm `Procfile` start command works
- [ ] Document build command: `pip install -r requirements.txt && cd backend && alembic upgrade head`
- [ ] Document env vars to set in Render dashboard
- [ ] Add a `runtime.txt` or pin Python version in `render.yaml`
- [ ] Make sure `/healthz` is the health-check path Render hits
- [ ] Make sure `JWT_SECRET_KEY` is loaded properly from env (already done in auth.py)
- [ ] Sanity-check that gunicorn isn't needed (uvicorn alone is fine for free tier with 1 worker)
- [ ] Write `docs/deploy.md` with step-by-step

**User-facing dashboard steps (covered in `docs/deploy.md`):**
1. Push current repo to GitHub
2. Render dashboard → New → Web Service → connect GitHub
3. Render auto-detects `render.yaml` (or set Build + Start manually)
4. Set env vars: `DATABASE_URL`, `JWT_SECRET_KEY`, `ALLOWED_ORIGINS=*` temporarily
5. Deploy. Note the URL.
6. Test: `curl https://<your-url>.onrender.com/healthz`

**Exit criteria:** `https://your-app.onrender.com/api/auth/signup` works from curl.

## Phase 5 Piece 3 — Deploy frontend to Vercel 🔜

**User action required:** sign up at https://vercel.com (free, login with GitHub).

**Code prep:**
- [ ] Add `frontend/vercel.json` with SPA fallback rewrites (so `/share/abc` works on direct visit)
- [ ] Document Vercel project settings (root directory = `frontend`)
- [ ] Document `VITE_API_BASE_URL` env var setting

**User-facing dashboard steps:**
1. Vercel dashboard → New Project → Import Git Repo → pick bill-buddy
2. **Root Directory:** `frontend`
3. Framework: auto-detected as Vite
4. Env var: `VITE_API_BASE_URL` = Render URL from Piece 2
5. Deploy. Note the Vercel URL.
6. Back in Render, update `ALLOWED_ORIGINS` to the Vercel URL
7. End-to-end test: sign up via Vercel URL, create trip, share link to a private/incognito window

**Exit criteria:** End-to-end signup → trip creation → share-link flow works on the live URLs.

---

## Phase 6 — Polish & nice-to-haves (post-deploy)

Pick from this list once Phase 5 is live and stable.

- [ ] Email verification on signup (Resend)
- [ ] Password reset flow
- [ ] Google OAuth login option
- [ ] Soft-delete trips/expenses (restore from trash)
- [ ] Date-range and participant filters on expense list
- [ ] Pagination on expense list (currently renders all rows)
- [ ] Expense categories (food / transport / lodging / activities)
- [ ] Custom split modes: exact amount per person, percentage split
- [ ] Multi-currency on a single trip with FX rates
- [ ] PWA conversion: `manifest.json`, service worker, "Add to Home Screen"
- [ ] Receipt image upload to Cloudflare R2
- [ ] Sentry error tracking wired up
- [ ] GitHub Actions CI running pytest + frontend type check on every PR
- [ ] Frontend tests (Vitest + React Testing Library) — currently only type checks
- [ ] Refactor: extract a `<TripDetailView>` presentational component so owner and share pages share UI instead of duplicating

## Phase 7 — AI features (optional, post-launch)

All use the Claude API.

- [ ] **Receipt OCR**: photo → vision model → structured expense (Claude Sonnet)
- [ ] **Natural-language expense entry**: "John paid $45 for sushi, split with me and Alice"
- [ ] **Itemized split**: OCR'd receipt items → user assigns each to specific people
- [ ] **Smart categorization**: auto-tag description (Claude Haiku for cost)
- [ ] **Anomaly flagging**: detect outlier amounts at add time
- [ ] **"Why do I owe this?" chatbot**: contextual Q&A over a trip
- [ ] **Trip recap generator**: shareable summary at trip end

Funding model: BYOK (user provides their own Anthropic key), or daily quota, or paid tier.

---

## Running locally

```bash
# Backend
source .venv/bin/activate
uvicorn api.main:app --reload --app-dir backend

# Frontend (in another terminal)
cd frontend
npm run dev
```

Open http://localhost:5173. The Vite dev proxy forwards `/api` to FastAPI on port 8000.

`.env` at project root provides `DATABASE_URL` (Neon) and optionally `JWT_SECRET_KEY` (defaults to a dev placeholder).

## Running tests

```bash
# Backend
source .venv/bin/activate
pytest                              # 65 tests

# Frontend
cd frontend
npx tsc --noEmit                    # type check
npm run build                       # production build
```

## Common operations

```bash
# Apply pending migrations
cd backend && alembic upgrade head

# Generate a new migration after model changes
cd backend && alembic revision --autogenerate -m "describe change"

# Reset Neon DB (DESTRUCTIVE)
cd backend && alembic downgrade base && alembic upgrade head

# Boot a one-off Python shell with models loaded
source .venv/bin/activate
python -c "from api.database import SessionLocal; from api.models import *; db = SessionLocal()"
```

---

## Open questions / decisions to revisit

- **JWT storage**: localStorage works but is XSS-vulnerable. If we ever introduce user-generated rich content, switch to `httpOnly` cookie + CSRF tokens.
- **Custom domain**: ~$10/yr. Defer until app has real users.
- **Cold-start mitigation on Render free**: 30s cold start hurts UX. Options: UptimeRobot ping every 5 min (gray-area on Render's free tier TOS), accept it, or pay $7/mo.
- **Member ↔ User linking**: currently members are name-only. Could be linked to real User accounts later (Option C from the original three-way fork) for stronger collaboration semantics.
- **CSV export from frontend**: currently a direct link to `/api/share/{token}/expenses.csv`. For authed routes it builds a URL without the token in the header — works because exports.csv is also CORS-enabled. Watch for browser cookie behavior in prod.

---

## Reference

- Neon dashboard: https://neon.tech
- Render dashboard: https://dashboard.render.com
- Vercel dashboard: https://vercel.com/dashboard
- FastAPI docs: https://fastapi.tiangolo.com
- shadcn/ui components: https://ui.shadcn.com/docs/components
- TanStack Query v5: https://tanstack.com/query/v5
- Local setup notes: [docs/neon-setup.md](./neon-setup.md)
- Deployment walkthrough (in progress): [docs/deploy.md](./deploy.md)
