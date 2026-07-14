# Expense Tracker API

Production-ready Django REST API for personal expense tracking — JWT auth, categories, budgets, multi-currency, receipts, OpenAPI docs, Docker, and a live demo UI.

**Live demo:** [amulyavarshney.github.io/expense-tracker](https://amulyavarshney.github.io/expense-tracker/)  
**Source:** [github.com/amulyavarshney/expense-tracker-api](https://github.com/amulyavarshney/expense-tracker-api)

> Demo mode runs fully in the browser (no backend required). Turn off Demo mode and point Settings at a running API (`http://127.0.0.1:8000/api`) to use the live backend.

## Features

- **JWT authentication** — register, access + refresh tokens
- **Expense CRUD** — create, list, retrieve, update, delete (user-scoped)
- **Categories** — system defaults (`food`, `transport`, `entertainment`, `other`) plus user-defined categories with full CRUD
- **Budgets** — weekly / monthly / yearly budgets with spent / remaining
- **Filtering** — category, currency, start/end date (inclusive end date)
- **Reports** — total spend and per-category summary (grouped by currency when mixed)
- **Multi-currency** — ISO 4217 codes per expense
- **Receipts** — optional file upload per expense (max 5 MB)
- **OpenAPI** — interactive docs at `/api/docs/`
- **Health check** — `GET /api/health/`
- **Docker** — Dockerfile + docker-compose (SQLite or PostgreSQL)
- **Demo UI** — static app in [`docs/`](docs/) deployed to GitHub Pages

## Quick start (API)

```bash
git clone https://github.com/amulyavarshney/expense-tracker-api.git
cd expense-tracker-api
cp .env.example .env
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

API base URL: `http://127.0.0.1:8000/api/`  
Swagger UI: `http://127.0.0.1:8000/api/docs/`

### Local demo UI

Open [`docs/index.html`](docs/index.html) in a browser, or serve the folder:

```bash
cd docs && python -m http.server 5500
```

Then visit `http://127.0.0.1:5500`. Use Demo mode, or disable it and set API base to `http://127.0.0.1:8000/api`.

## Settings

| Module | Use case |
|--------|----------|
| `expense_tracker.settings` | Auto-selects via `ENV` (`dev` default, `prod` for production) |
| `expense_tracker.settings.dev` | Local development |
| `expense_tracker.settings.prod` | Production hardening |

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `dev` | Settings profile |
| `SECRET_KEY` | (dev fallback) | Django secret key |
| `DEBUG` | `True` (dev) / `False` (prod) | Debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hosts |
| `DATABASE_URL` | — | PostgreSQL URL; omit for SQLite |
| `CORS_ALLOWED_ORIGINS` | includes localhost + `https://amulyavarshney.github.io` | Allowed browser origins |

See [`.env.example`](.env.example) for the full list.

## Authentication (JWT)

```http
POST /api/auth/register/
{"username": "alice", "email": "alice@example.com", "password": "securepass1"}

POST /api/auth/token/
{"username": "alice", "password": "securepass1"}

POST /api/auth/token/refresh/
{"refresh": "<refresh_token>"}
```

Authenticated requests:

```
Authorization: Bearer <access_token>
```

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health/` | Health check (public) |
| `POST` | `/api/auth/register/` | Create account |
| `POST` | `/api/auth/token/` | Obtain JWT pair |
| `POST` | `/api/auth/token/refresh/` | Refresh access token |
| `GET`, `POST` | `/api/categories/` | List / create categories |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/categories/{id}/` | Category detail (system = read-only) |
| `GET`, `POST` | `/api/expenses/` | List / create expenses |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/expenses/{id}/` | Expense detail |
| `GET` | `/api/expenses/total/` | Total spend |
| `GET` | `/api/expenses/summary/` | Totals by category |
| `GET`, `POST` | `/api/budgets/` | List / create budgets |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/budgets/{id}/` | Budget detail |
| `GET` | `/api/schema/` | OpenAPI schema |
| `GET` | `/api/docs/` | Swagger UI |

### Query filters (list, total, summary)

| Param | Format | Description |
|-------|--------|-------------|
| `category` | slug | Filter by category |
| `currency` | `USD`, `EUR`, … | Filter by currency |
| `start_date` | `YYYY-MM-DD` | On or after |
| `end_date` | `YYYY-MM-DD` | On or before (inclusive) |

## Docker

```bash
docker compose up --build
# PostgreSQL:
docker compose --profile postgres up --build
```

## Testing

```bash
python manage.py test
```

## Postman

Import [`EXPENSE_TRACKER_API.postman_collection.json`](EXPENSE_TRACKER_API.postman_collection.json). Run **Obtain Token**, then set the `access_token` collection variable.

## Project layout

```
accounts/          # Register + JWT routes
expenses/          # Expenses, categories, reports
budgets/           # Budget CRUD + spend tracking
expense_tracker/   # Project settings (base/dev/prod)
docs/              # Static demo UI (GitHub Pages source)
```

## License

MIT — see [LICENSE](LICENSE).
