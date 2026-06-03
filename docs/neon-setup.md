# Neon Postgres setup

Steps to point the FastAPI app at a free Neon Postgres database.

## 1. Create the Neon account + project

1. Sign up at https://neon.tech (free tier, no credit card).
2. Create a project — name it `bill-buddy`.
3. Default database name will be something like `neondb`. You can rename it in the Neon dashboard if you want `bill_buddy_dev`.
4. From the project dashboard, click **Connection string** and copy the value. It looks like:
   ```
   postgresql://USER:PASSWORD@ep-xxxxxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

## 2. Convert the connection string for psycopg3

SQLAlchemy + psycopg3 expects the `+psycopg` dialect prefix. Replace `postgresql://` with `postgresql+psycopg://`:

```
postgresql+psycopg://USER:PASSWORD@ep-xxxxxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

## 3. Add it to your local `.env`

Create `.env` at the project root (it is gitignored):

```
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@ep-xxxxxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

Load the env file in your shell with one of:

```bash
# Option A: export inline before each command
export $(grep -v '^#' .env | xargs)

# Option B: use a tool like direnv
direnv allow
```

## 4. Run the initial migration against Neon

```bash
source .venv/bin/activate
cd backend
alembic upgrade head
```

You should see `Running upgrade  -> d426f66146cd, initial`. The four tables are now created in Neon.

## 5. Verify the FastAPI app talks to Neon

```bash
uvicorn api.main:app --port 8000
curl http://localhost:8000/api/trips    # should return []
```

The Neon DB starts empty — your local SQLite data is not migrated.

## 6. (Optional) Move local SQLite data into Neon

If you want your existing trips/expenses copied over, the simplest path is a one-off Python script using SQLAlchemy. We can write that in Phase 3 or skip — most users start fresh.

## Reverting to local SQLite

Just `unset DATABASE_URL` (or comment it out in `.env`). The app falls back to `bill_buddy.db` in the project root.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `psycopg.OperationalError: could not connect` | Check `?sslmode=require` is in the URL. Neon requires SSL. |
| `ModuleNotFoundError: psycopg` | `pip install -r requirements.txt` to get psycopg[binary]. |
| `alembic` can't find `alembic.ini` | Run from `backend/` directory, or pass `-c backend/alembic.ini`. |
| Neon connection drops after idle | Free tier scales compute to zero after 5 min idle — first request after wakes it in ~1s. Normal. |
