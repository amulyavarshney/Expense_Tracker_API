# Expense Tracker API

A production-ready Django REST API for logging personal expenses, with JWT authentication, filtering, aggregates, OpenAPI docs, and Docker support.

## Features

- **JWT authentication** — register, obtain access/refresh tokens
- **Expense CRUD** — create, list, retrieve, update, delete (user-scoped)
- **Filtering** — by category, start/end date (inclusive end date)
- **Reports** — total spend and per-category summary
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

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (dev fallback) | Django secret key |
| `DEBUG` | `True` | Enable debug mode |
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
| `GET`, `POST` | `/api/expenses/` | List (paginated) / create expenses |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/expenses/{id}/` | Retrieve / update / delete expense |
| `GET` | `/api/expenses/total/` | Total spend (filtered) |
| `GET` | `/api/expenses/summary/` | Totals grouped by category |
| `GET` | `/api/schema/` | OpenAPI schema |
| `GET` | `/api/docs/` | Swagger UI |

### Query filters (list, total, summary)

| Param | Format | Description |
|-------|--------|-------------|
| `category` | `food`, `transport`, `entertainment`, `other` | Filter by category |
| `start_date` | `YYYY-MM-DD` | Expenses on or after this date |
| `end_date` | `YYYY-MM-DD` | Expenses on or before this date (inclusive) |

Invalid date formats return `400 Bad Request`.

### Create expense body

```json
{
  "category": "food",
  "amount": "15.00",
  "description": "Lunch at cafe"
}
```

`amount` must be greater than zero.

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
