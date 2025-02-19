# Expense Tracker API

## Introduction

This is a simple API for tracking expenses. Users can log their expenses, retrieve their expenses with filtering options, and calculate total expenses for a given period.

## Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd expense_tracker
```

### 2. Create a virtual environment and activate it

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install the dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create a superuser

```bash
python manage.py createsuperuser
```

### 6. Run the server

```bash
python manage.py runserver
```

## API Endpoints

### 1. Create and Retrieve Expenses

- **URL:** `/api/expenses/`
- **Method:** `GET`, `POST`

### 2. Calculate Total Expenses

- **URL:** `/api/expenses/total/`
- **Method:** `GET`

## Filters

- `category`: Filter by expense category
- `start_date`: Filter expenses from this date (format: `YYYY-MM-DD`)
- `end_date`: Filter expenses up to this date (format: `YYYY-MM-DD`)
```

### Push to GitHub

1. Initialize the repository if you haven't already:

    ```bash
    git init
    git add .
    git commit -m "Initial commit"
    ```

2. Create a new repository on GitHub and follow the instructions to push your code:

    ```bash
    git remote add origin <repository-url>
    git push -u origin main
    ```
