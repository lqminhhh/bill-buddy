# Bill Buddy

Bill Buddy is a deployed full-stack app for tracking shared trip expenses. It lets a group create trips, add members, record expenses, view balances, generate settlement suggestions, and share a public edit link with friends who do not need accounts.

[Demo Video](https://github.com/user-attachments/assets/d5b64d77-c972-4fc3-9e10-12ce908f0689)

## Features

- Create trips with a trip name and currency
- Add all trip members and mark exactly one member as yourself
- Sign up, sign in, and stay authenticated with JWT
- View only your own trips when signed in
- Share a trip via a link so other people can view and add/edit expenses without signing up
- Add expenses with description, amount, date, payer, participants, and optional notes
- Edit expenses
- Delete expenses
- View per-member balances, paid totals, shares, and net amounts
- View final settlement suggestions in plain language
- Open a dedicated trip summary page
- View total spending, total expenses, total members, highest spender, highest share, and member who owes the most
- Filter expense history by payer
- Export expense history to an Excel-friendly CSV file

## Stack

| Layer | Technology |
| --- | --- |
| Backend | FastAPI, SQLAlchemy, Alembic, Pydantic, bcrypt, JWT |
| Frontend | React, Vite, TypeScript, Tailwind CSS v4, shadcn/ui, TanStack Query |
| Database | Neon Postgres |
| Hosting | Render (API), Vercel (frontend) |

## Project Structure

```text
bill-buddy/
├── README.md
├── docs/
│   ├── project-plan.md
│   ├── deploy.md
│   └── neon-setup.md
├── assets/
│   └── demo-video.mov
├── backend/
│   ├── alembic/
│   ├── api/
│   ├── init_db.py
│   ├── schema.sql
│   └── utils/
├── frontend/
│   ├── public/
│   └── src/
├── requirements.txt
├── requirements-dev.txt
├── render.yaml
├── Procfile
└── pytest.ini
```

## Local Development

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install backend dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

3. Start the backend:

```bash
uvicorn api.main:app --reload --app-dir backend
```

4. Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

5. Open:

```text
http://localhost:5173
```

The frontend dev server proxies `/api` to the backend on port `8000`.

## Environment Variables

Backend:

- `DATABASE_URL`: Neon/Postgres connection string in production; defaults to local SQLite in dev if unset
- `JWT_SECRET_KEY`: required in production
- `ALLOWED_ORIGINS`: comma-separated frontend origins for CORS

Frontend:

- `VITE_API_BASE_URL`: required in production; leave unset in local dev to use the Vite proxy

See [.env.example](./.env.example) for sample values.

## Testing

Backend:

```bash
source .venv/bin/activate
pytest
```

Frontend:

```bash
cd frontend
npm run build
```

## Deployment

The app is deployed on:

- Render for the FastAPI backend
- Vercel for the React frontend
- Neon for Postgres

For setup and redeploy steps, use [docs/deploy.md](./docs/deploy.md). The handoff and roadmap live in [docs/project-plan.md](./docs/project-plan.md).

## Notes

- The current README replaces the older Flask-era description.
- Some Flask-era reference files still exist under `backend/` but are no longer part of the runtime path.

## Contact

- Project owner: Minh Le
- For questions or feedback, open an issue in this repository.
