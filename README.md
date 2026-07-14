# Expense Tracker API

A production-ready Django REST API for logging personal expenses, with JWT authentication, filtering, aggregates, OpenAPI docs, and Docker support.

## Features

- **JWT authentication** — register, obtain access/refresh tokens
- **Expense CRUD** — create, list, retrieve, update, delete (user-scoped)
- **Categories** — system defaults plus user-defined categories
- **Filtering** — by category slug, start/end date (inclusive end date)
- **Reports** — total spend and per-category summary
- **Multi-currency** — ISO 4217 currency codes per expense; totals/summary grouped by currency when mixed
- **Receipts** — optional receipt file upload per expense
- **OpenAPI** — interactive docs at `/api/docs/`
- **Health check** — `GET /api/health/`
- **Docker** — Dockerfile and docker-compose for local deployment

## Quick start

### 1. Clone and enter the project

```bash
git clone <repository-url>
cd Expense_Tracker_API
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set SECRET_KEY and other values as needed
```

### 3. Install dependencies

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Migrate and run

```bash
python manage.py migrate
python manage.py runserver
```

API base URL: `http://127.0.0.1:8000/api/`

## Settings

Configuration is split into `expense_tracker/settings/`:

| Module | Use case |
|--------|----------|
| `expense_tracker.settings` | Auto-selects via `ENV` (`dev` default, `prod` for production) |
| `expense_tracker.settings.dev` | Local development (`DEBUG=True` by default) |
| `expense_tracker.settings.prod` | Production hardening (`DEBUG=False` by default) |

`manage.py`, `wsgi.py`, and `asgi.py` default to `expense_tracker.settings`. Set `ENV=prod` or `DJANGO_SETTINGS_MODULE=expense_tracker.settings.prod` for production deployments.

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENV` | `dev` | Settings profile when using `expense_tracker.settings` |
| `DJANGO_SETTINGS_MODULE` | `expense_tracker.settings` | Override to pin a specific settings module |
| `SECRET_KEY` | (dev fallback) | Django secret key |
| `DEBUG` | `True` (dev) / `False` (prod) | Enable debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated hosts |
| `DATABASE_URL` | — | PostgreSQL URL; omit for SQLite |
| `SQLITE_DB_PATH` | `db.sqlite3` | SQLite file path (Docker uses `/data/db.sqlite3`) |
| `CORS_ALLOWED_ORIGINS` | — | Comma-separated allowed origins |

## Authentication (JWT)

### Register

```http
POST /api/auth/register/
Content-Type: application/json

{"username": "alice", "email": "alice@example.com", "password": "securepass1"}
```

### Obtain tokens

```http
POST /api/auth/token/
Content-Type: application/json

{"username": "alice", "password": "securepass1"}
```

Response includes `access` and `refresh` tokens.

### Refresh access token

```http
POST /api/auth/token/refresh/
Content-Type: application/json

{"refresh": "<refresh_token>"}
```

### Authenticated requests

Include the access token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

## API endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health/` | Health check (public) |
| `POST` | `/api/auth/register/` | Create account (public) |
| `POST` | `/api/auth/token/` | Obtain JWT pair (public) |
| `POST` | `/api/auth/token/refresh/` | Refresh access token (public) |
| `GET`, `POST` | `/api/categories/` | List system + user categories / create custom category |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/categories/{id}/` | Retrieve / update / delete category (system categories: read-only) |
| `GET`, `POST` | `/api/expenses/` | List (paginated) / create expenses |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/expenses/{id}/` | Retrieve / update / delete expense |
| `GET` | `/api/expenses/total/` | Total spend (filtered) |
| `GET` | `/api/expenses/summary/` | Totals grouped by category |
| `GET` | `/api/schema/` | OpenAPI schema |
| `GET` | `/api/docs/` | Swagger UI |

### Query filters (list, total, summary)

| Param | Format | Description |
|-------|--------|-------------|
| `category` | category slug (e.g. `food`, `transport`, or a custom slug) | Filter by category |
| `currency` | 3-letter ISO code (e.g. `USD`, `EUR`) | Filter by currency |
| `start_date` | `YYYY-MM-DD` | Expenses on or after this date |
| `end_date` | `YYYY-MM-DD` | Expenses on or before this date (inclusive) |

Invalid date formats return `400 Bad Request`.

### Categories

System defaults (`food`, `transport`, `entertainment`, `other`) are seeded automatically. Users can add custom categories:

```http
GET /api/categories/
Authorization: Bearer <access_token>
```

```http
POST /api/categories/
Authorization: Bearer <access_token>
Content-Type: application/json

{"name": "Groceries", "slug": "groceries"}
```

`slug` is optional on create (derived from `name`). System category slugs cannot be reused.

Retrieve, update, or delete a category by id. System categories (`is_system: true`) can be retrieved but not updated or deleted.

```http
GET /api/categories/{id}/
PATCH /api/categories/{id}/
DELETE /api/categories/{id}/
Authorization: Bearer <access_token>
```

Deleting a category that is referenced by expenses returns `400 Bad Request`.

### Create expense body

JSON (`Content-Type: application/json`):

```json
{
  "category": "food",
  "amount": "15.00",
  "currency": "USD",
  "description": "Lunch at cafe"
}
```

Multipart (`Content-Type: multipart/form-data`) for receipt upload:

| Field | Type | Required |
|-------|------|----------|
| `category` | text | yes |
| `amount` | text | yes |
| `currency` | text | no (defaults to `USD`) |
| `description` | text | no |
| `receipt` | file | no |

`category` is a slug referencing a system or user-defined category. Responses also include `category_name`.

`amount` must be greater than zero. `currency` must be a 3-letter uppercase ISO 4217 code (e.g. `USD`, `EUR`); defaults to `USD`.

`receipt` is optional (max 5 MB). Uploaded files are stored under `media/receipts/YYYY/MM/`. In `DEBUG` mode, receipt URLs are served at `/media/...`.

### Multi-currency totals and summary

When all matching expenses share one currency, responses include that currency:

```json
{"total_expenses": 55.0, "currency": "USD"}
```

```json
{"currency": "USD", "by_category": [{"category": "food", "category_name": "Food", "total": 25.0, "count": 2}]}
```

When multiple currencies are present, totals and summaries are grouped by currency:

```json
{"by_currency": [{"currency": "USD", "total": 25.0}, {"currency": "EUR", "total": 30.0}]}
```

```json
{"by_currency": [{"currency": "USD", "by_category": [...]}, {"currency": "EUR", "by_category": [...]}]}
```

Use the `currency` query filter to scope list, total, and summary endpoints to a single currency.

## Docker

### SQLite (default)

```bash
docker compose up --build
```

### PostgreSQL

```bash
# In .env, set:
# DATABASE_URL=postgresql://expense_user:expense_pass@db:5432/expense_tracker

docker compose --profile postgres up --build
```

## Testing

```bash
python manage.py test
```

## Postman

Import [`EXPENSE_TRACKER_API.postman_collection.json`](EXPENSE_TRACKER_API.postman_collection.json). The collection uses Bearer JWT auth — run **Obtain Token** first, then set the `access_token` collection variable.

## License

MIT License — see [LICENSE](LICENSE).
