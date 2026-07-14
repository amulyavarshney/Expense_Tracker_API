# Budgets

User-scoped spending limits per category and calendar period.

## Model

| Field | Type | Notes |
|-------|------|-------|
| `user` | FK → `User` | Owner; set automatically on create |
| `category` | FK → `expenses.Category` | System or user-defined category |
| `amount` | `Decimal(10,2)` | Budget cap; must be > 0 |
| `period` | `weekly` \| `monthly` \| `yearly` | Calendar period for tracking |
| `created_at` / `updated_at` | timestamps | Auto-managed |

One budget per `(user, category, period)` combination.

### Period semantics

- **weekly** — Monday through Sunday of the current week
- **monthly** — first through last day of the current calendar month
- **yearly** — January 1 through December 31 of the current calendar year

## Endpoints

All routes require JWT (`Authorization: Bearer <access_token>`).

| Method | Path | Description |
|--------|------|-------------|
| `GET`, `POST` | `/api/budgets/` | List (paginated) / create |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/budgets/{id}/` | Retrieve / update / delete |

### List query params

| Param | Description |
|-------|-------------|
| `category` | Filter by category slug |
| `period` | Filter by `weekly`, `monthly`, or `yearly` |

### Create / update body

```json
{
  "category": "food",
  "amount": "500.00",
  "period": "monthly"
}
```

`category` is a slug (same as expenses). Responses include read-only usage fields:

- `spent` — total expenses in the current period for that category
- `remaining` — `amount - spent`
- `period_start` / `period_end` — inclusive date bounds for the active period

### Example response

```json
{
  "id": 1,
  "category": "food",
  "category_name": "Food",
  "amount": "500.00",
  "period": "monthly",
  "spent": "125.50",
  "remaining": "374.50",
  "period_start": "2026-07-01",
  "period_end": "2026-07-31",
  "created_at": "2026-07-14T12:00:00Z",
  "updated_at": "2026-07-14T12:00:00Z"
}
```

## Postman

Import the root collection [`EXPENSE_TRACKER_API.postman_collection.json`](../EXPENSE_TRACKER_API.postman_collection.json) and use the **Budgets** folder:

1. Run **Auth → Obtain Token** to set `access_token`.
2. **List Budgets** — `GET /api/budgets/`
3. **Create Budget** — `POST /api/budgets/` (saves `budget_id`)
4. **Retrieve Budget** — `GET /api/budgets/{{budget_id}}/`
5. **Update Budget** — `PATCH /api/budgets/{{budget_id}}/`
6. **Delete Budget** — `DELETE /api/budgets/{{budget_id}}/`
7. **List Budgets with Filters** — `GET /api/budgets/?category=food&period=monthly`

Create a few expenses in the same category to see `spent` and `remaining` update on budget responses.

## Tests

```bash
python manage.py test budgets
```
