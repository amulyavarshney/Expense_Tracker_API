# Expense Tracker API

## Introduction

The Expense Tracker API is a Django-based application that allows users to log and manage their expenses. This RESTful API enables users to create new expense entries, retrieve their logged expenses with various filtering options, and calculate the total expenses for a specified period. The application ensures that users can only access their own expense data, providing a secure way to manage personal finances.

### Features

- **User Authentication**: Secure user authentication to ensure that only registered users can log and retrieve their expenses.
- **Create Expense**: Users can create new expense records by specifying the category and amount.
- **Retrieve Expenses**: Users can retrieve their expenses and filter the results by category, start date, and end date.
- **Calculate Total Expenses**: Users can calculate the total amount spent over a specified period.
- **Data Security**: Users are restricted to accessing only their own expense data.

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

### Usage

- **Authenticate**: Obtain a token by logging in with your credentials.
- **Create Expense**: Use the `/api/expenses/` endpoint to create new expense entries.
- **Retrieve Expenses**: Use the `/api/expenses/` endpoint to retrieve and filter your expenses.
- **Calculate Total Expenses**: Use the `/api/expenses/total/` endpoint to calculate the total expenses for a specified period.

### Postman Collection

A Postman collection is provided to help you get started quickly with the API. Download the [Expense Tracker API Postman Collection](Expense_Tracker_API.postman_collection.json) and import it into Postman to interact with the API endpoints.

### Dependencies

- Django
- Django REST Framework

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

### License

This project is licensed under the MIT License.