#### By sampark bhol

# Credit Approval System - Django & Celery

This project is a complete backend-only credit approval system  , it is fully containerized using Docker and features asynchronous task processing with Celery for data ingestion.

---

## Features
- **Fully Dockerized:** The entire application (Django, PostgreSQL, Redis, Celery) runs in a multi-container Docker setup.
- **Asynchronous Data Ingestion:** Uses Celery and Redis to load data from Excel files in the background without blocking the main application.
- **RESTful API:** Provides 5 secure and logical API endpoints for managing customers and loans.
- **Clean Architecture:** Follows a clean code philosophy by separating business logic (in a `services.py` module) from the API views.
- **PostgreSQL Database:** Uses a robust PostgreSQL database for reliable data storage.

---

## Tech Stack
- **Backend:** Django, Django Rest Framework
- **Database:** PostgreSQL
- **Asynchronous Tasks:** Celery
- **Message Broker:** Redis
- **Containerization:** Docker & Docker Compose
- **Data Handling:** Pandas, openpyxl

---

## Project Structure
```text
credit_approval_system/
├── .env
├── .env.example
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── src/
    ├── api/
    │   ├── management/
    │   │   └── commands/
    │   │       └── ingest_data.py
    │   ├── migrations/
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── models.py
    │   ├── serializers.py
    │   ├── services.py
    │   ├── tasks.py
    │   ├── tests.py
    │   ├── urls.py
    │   └── views.py
    ├── core/
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── celery.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── customer_data.xlsx
    ├── loan_data.xlsx
    └── manage.py
```

---

## Setup and Installation

### Prerequisites
- **Docker** and **Docker Compose** (Docker Desktop for Windows/Mac includes both)
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/SamparkBhol/Credit-Approval-System.git
cd Credit-Approval-System
```

### 2. Create Your Environment File
Create a `.env` file in the root directory. You can copy the example file:
```bash
# On Windows PowerShell
copy .env.example .env

# On Mac/Linux
cp .env.example .env
```

Now, **edit the `.env` file** and add a `SECRET_KEY`.

1. Go to [https://djecrety.ir/](https://djecrety.ir/) to generate a new key.  
2. Paste it into your `.env` file:

```env
SECRET_KEY='your-new-key-goes-here'
```

Leave all other database and Redis settings as they are—they are configured to work inside Docker.

### 3. Add Data Files
Place your `customer_data.xlsx` and `loan_data.xlsx` files inside the `src/` directory.

### 4. Build and Run the Application
This single command will build the Docker images, install dependencies, and start all containers:
```bash
docker-compose up --build -d
```

### 5. Initialize the Database
Run these commands to apply migrations and ingest data:
```bash
# 1. Create migration files
docker-compose exec web python manage.py makemigrations api

# 2. Apply migrations
docker-compose exec web python manage.py migrate

# 3. Ingest Excel data asynchronously
docker-compose exec web python manage.py ingest_data
```

Check Celery worker logs to confirm successful ingestion:
```bash
docker-compose logs -f worker
```
(Look for “Successfully ingested...” messages. Press `Ctrl+C` to exit.)

---

## API Endpoints
All endpoints are available at:  
`http://localhost:8000/api/`

---

### 1. Register a New Customer
**Endpoint:** `POST /api/register/`

**Body:**
```json
{
  "first_name": "Test",
  "last_name": "User",
  "age": 25,
  "monthly_income": 60000,
  "phone_number": 9876543210
}
```

**PowerShell Example:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/register/ -Method POST -ContentType "application/json" -Body '{"first_name": "Test", "last_name": "User", "age": 25, "monthly_income": 60000, "phone_number": 9876543210}'
```

**Success Response (201 Created):**
```json
{
  "customer_id": 301,
  "name": "Test User",
  "age": 25,
  "monthly_income": "60000.00",
  "approved_limit": "2200000.00",
  "phone_number": 9876543210
}
```

---

### 2. Check Loan Eligibility
**Endpoint:** `POST /api/check-eligibility/`

**Body:**
```json
{
  "customer_id": 1,
  "loan_amount": 100000,
  "interest_rate": 10.5,
  "tenure": 12
}
```

**PowerShell Example:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/check-eligibility/ -Method POST -ContentType "application/json" -Body '{"customer_id": 1, "loan_amount": 100000, "interest_rate": 10.5, "tenure": 12}' | Select-Object -ExpandProperty Content
```

**Success Response (200 OK):**
```json
{
  "customer_id": 1,
  "approval": false,
  "interest_rate": 10.5,
  "corrected_interest_rate": null,
  "tenure": 12,
  "monthly_installment": 0.0
}
```

---

### 3. Create a New Loan
**Endpoint:** `POST /api/create-loan/`

**Body:** (Same as check eligibility)
```json
{
  "customer_id": 1,
  "loan_amount": 100000,
  "interest_rate": 10.5,
  "tenure": 12
}
```

**PowerShell Example:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/create-loan/ -Method POST -ContentType "application/json" -Body '{"customer_id": 1, "loan_amount": 100000, "interest_rate": 10.5, "tenure": 12}' | Select-Object -ExpandProperty Content
```

**Success Response (if approved):**
```json
{
  "loan_id": 1234,
  "customer_id": 1,
  "loan_approved": true,
  "message": "Loan approved and created successfully.",
  "monthly_installment": 8815.23
}
```

**Success Response (if not approved):**
```json
{
  "loan_id": null,
  "customer_id": 1,
  "loan_approved": false,
  "message": "Loan not approved. Customer not eligible.",
  "monthly_installment": null
}
```

---

### 4. View a Specific Loan
**Endpoint:** `GET /api/view-loan/<loan_id>/`

**PowerShell Example:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/view-loan/5930/ | Select-Object -ExpandProperty Content
```

**Success Response (200 OK):**
```json
{
  "loan_id": 5930,
  "customer": {
    "customer_id": 14,
    "first_name": "Adaline",
    "last_name": "Diaz",
    "phone_number": 9519253076,
    "age": 65
  },
  "loan_amount": "900000.00",
  "interest_rate": "8.20",
  "monthly_installment": "15344.00",
  "tenure": 129
}
```

---

### 5. View All Loans for a Customer
**Endpoint:** `GET /api/view-loans/<customer_id>/`

**PowerShell Example:**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/api/view-loans/14/ | Select-Object -ExpandProperty Content
```

**Success Response (200 OK):**
```json
[
  {
    "loan_id": 5930,
    "loan_amount": "900000.00",
    "interest_rate": "8.20",
    "monthly_installment": "15344.00",
    "repayments_left": 25
  },
  {
    "loan_id": 8279,
    "loan_amount": "700000.00",
    "interest_rate": "16.32",
    "monthly_installment": "28701.00",
    "repayments_left": 0
  },
  {
    "loan_id": 5592,
    "loan_amount": "800000.00",
    "interest_rate": "13.19",
    "monthly_installment": "21773.00",
    "repayments_left": 0
  },
  {
    "loan_id": 8870,
    "loan_amount": "700000.00",
    "interest_rate": "10.20",
    "monthly_installment": "233333.00",
    "repayments_left": 0
  }
]
```
