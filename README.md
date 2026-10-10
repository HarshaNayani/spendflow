# SpendFlow

Expense approval workflow for small teams. Employees submit expenses, managers approve or reject them with a comment, and admins see a live budget dashboard. AI suggests the category and flags unusual claims. Approved expenses are locked, so every record stays audit-ready.

Built for Nitya Tech Buildathon 1.0. Domain: workflow management with a finance focus (SDG 8 and SDG 12).

## Features

- **Three roles:** employee, manager, admin, with role checks in the React routes and again in every FastAPI route.
- **Approval flow:** submit, review, approve or reject with a comment. A rejected expense goes back to the employee, who can fix and resubmit.
- **Locked after approval:** approved expenses cannot be edited, deleted or decided again (the API returns 403).
- **AI helper (Groq, Llama 3.3 70B):** suggests a category and flags unusual claims with a short reason.
- **AI fallback:** if the AI call fails, times out or returns invalid JSON, the API still answers normally. The form shows "AI is unavailable, please select a category", and the workflow never stops.
- **Rule checks next to the AI:** high amounts and possible duplicates are flagged even without AI.
- **Review rules:** flagged claims appear first in the manager's queue, and nobody can approve their own claim.
- **Admin dashboard:** approved spend, spend by category (pie), budget vs spend this month (bars), flagged expenses.
- **Demo data:** demo users, budgets and expenses are created on first start.

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18 (Vite), Tailwind CSS, Recharts, Axios, React Router |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2 |
| Database | SQLite (default), Postgres via `DATABASE_URL` |
| Auth | JWT (PyJWT), bcrypt password hashing |
| AI | Groq API, `llama-3.3-70b-versatile` |
| Tests | Pytest (14 tests) |
| Hosting | Vercel (frontend), Render (backend) |

## Architecture

```
React app (Vercel)  --REST + JWT-->  FastAPI service (Render)  --->  SQLite / Postgres
                                              |
                                              +--->  Groq API (category + unusual flag)
```

```
spendflow/
├── backend/
│   ├── app/
│   │   ├── main.py          app, CORS, startup (tables + demo data)
│   │   ├── config.py        environment settings
│   │   ├── database.py      engine and session
│   │   ├── models.py        users, expenses, budgets
│   │   ├── schemas.py       Pydantic request and response models
│   │   ├── security.py      password hashing, JWT
│   │   ├── deps.py          current user and role checks
│   │   ├── ai.py            Groq call with safe fallback
│   │   ├── flags.py         rule checks and flag merging
│   │   ├── seed.py          demo data
│   │   └── routers/         auth, expenses, dashboard, ai
│   ├── tests/               pytest suite
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── api.js           Axios client (JWT header, error messages)
    │   ├── context/         AuthContext
    │   ├── components/      Navbar, ProtectedRoute, ExpenseForm, ...
    │   └── pages/           Login, SubmitExpense, MyExpenses, Approvals, Dashboard
    ├── vercel.json
    └── .env.example
```

## Run it locally

You need Python 3.11+ and Node 18+.

**1. Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
# optional: put your free Groq key in .env as GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
```

API docs open at http://localhost:8000/docs. Demo data is created automatically on first start.

**2. Frontend** (new terminal)

```bash
cd frontend
cp .env.example .env               # Windows: copy .env.example .env
npm install
npm run dev
```

Open http://localhost:5173.

## Demo accounts

| Role | Email | Password |
| --- | --- | --- |
| Employee | employee@spendflow.demo | Employee@123 |
| Employee | priya@spendflow.demo | Employee@123 |
| Manager | manager@spendflow.demo | Manager@123 |
| Admin | admin@spendflow.demo | Admin@123 |

Public sign-up always creates an **employee**. Managers and admins come from the seed script, so nobody can promote themselves.

To reset the demo data: `python -m app.seed --reset` (from the `backend` folder).

## 2-minute demo script

1. Log in as **employee**: submit "Cab to the airport" for 1800. Watch the AI suggestion appear.
2. Submit an expense of 90000: it is flagged by the rule check.
3. Log in as **manager**: flagged claims are on top. Approve one, and reject one with a comment.
4. Back as **employee**: read the comment, click "Fix and resubmit". The approved one shows 🔒 locked.
5. Log in as **admin**: see the pie chart, budget vs spend and the flagged list.
6. Optional: remove `GROQ_API_KEY`, restart, and show the form still works with a manual category.

## API overview

| Method | Endpoint | Who | Purpose |
| --- | --- | --- | --- |
| POST | `/auth/register` | Public | Create an employee account |
| POST | `/auth/login` | Public | Get a JWT |
| GET | `/auth/me` | Logged in | Current user |
| POST | `/expenses` | Logged in | Submit an expense (AI and rule checks run) |
| GET | `/expenses/mine` | Logged in | Own expenses |
| PUT | `/expenses/{id}` | Owner | Fix and resubmit (blocked once approved) |
| DELETE | `/expenses/{id}` | Owner | Delete (blocked once approved) |
| GET | `/expenses/pending` | Manager, admin | Approval queue, flagged first |
| PATCH | `/expenses/{id}/decision` | Manager, admin | Approve or reject with a comment |
| GET | `/expenses` | Admin | All expenses (optional `?status=`) |
| GET | `/dashboard/summary` | Admin | Totals, spend by category, budget vs spend, flagged |
| POST | `/ai/categorize` | Logged in | Suggest category and flag (never fails) |

## Run the tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

The tests cover login, role checks, the full approval flow, locking after approval, rejection and resubmission, self-approval blocking, rule-based flags, the AI fallback and the admin dashboard.

## Deploy

**Backend on Render** (Web Service)

1. Push this repo to GitHub, then create a new **Web Service** on Render and pick the repo.
2. Root directory: `backend`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Environment variables: `SECRET_KEY` (long random string), `GROQ_API_KEY` (optional), `CORS_ORIGINS` (your Vercel URL), `PYTHON_VERSION=3.11.9`.
6. Optional: create a free Render Postgres database and set `DATABASE_URL` to its Internal Database URL. Without it, SQLite is used, and demo data is recreated on each restart (the free disk is temporary).

**Frontend on Vercel**

1. Import the repo into Vercel and set the root directory to `frontend` (Vite is detected automatically).
2. Environment variable: `VITE_API_URL` = your Render URL, without a trailing slash.
3. Deploy, then open the Vercel link and log in with a demo account.

Any `*.vercel.app` origin is already allowed by the backend CORS rules. A custom domain needs to be added to `CORS_ORIGINS`.

Render's free instances sleep when idle, so the first request after a pause can take about a minute. Open the backend URL once before a demo.

## Configuration

| Variable | Where | Purpose |
| --- | --- | --- |
| `GROQ_API_KEY` | backend | Enables AI. Empty means AI is off and the fallback is used |
| `SECRET_KEY` | backend | Signs the JWTs. Use a long random value in production |
| `DATABASE_URL` | backend | SQLite by default, or a Postgres URL |
| `CORS_ORIGINS` | backend | Comma-separated allowed frontend origins |
| `SEED_DEMO` | backend | `true` creates demo data when the database is empty |
| `HIGH_AMOUNT_THRESHOLD` | backend | Amount at or above which a claim is flagged (default 50000) |
| `AI_TIMEOUT_SECONDS` | backend | Groq timeout before falling back (default 8) |
| `VITE_API_URL` | frontend | Backend base URL |

## Roadmap

Receipt upload with OCR, email notifications, payment export, multi-level approvals and a per-team budget editor.
