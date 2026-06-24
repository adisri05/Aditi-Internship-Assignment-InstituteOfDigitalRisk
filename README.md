# Transaction Ranking Service

A transaction processing and ranking service built using **FastAPI**. The system accepts user transactions, maintains aggregated user summaries, prevents duplicate requests, and generates a fair leaderboard based on user activity.

---

## Features

* FastAPI backend with REST APIs
* Request validation using Pydantic
* Duplicate request prevention using idempotency keys
* Atomic database updates
* User summary aggregation
* Fair ranking algorithm
* Simple frontend for testing APIs
* Automated API tests

---

## Project Structure

```text
assignment/
│
├── backend/
│   ├── app.py              # API routes
│   ├── models.py           # Request and response schemas
│   ├── database.py         # Database initialization
│   ├── repository.py       # Database operations
│   └── ranking.py          # Ranking logic
│
├── frontend/
│   ├── index.html          # UI
│   ├── style.css
│   └── script.js
│
├── tests/
│   └── test_api.py         # API tests
│
├── requirements.txt
└── README.md
```

---

# How To Run The Project

## 1. Clone the repository

```bash
git clone <repository-url>
cd assignment
```

## 2. Create and activate a virtual environment (optional but recommended)

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Start the backend server

```bash
python -m uvicorn backend.app:app --reload
```

The server will start at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## 5. Run the frontend

Open the following file directly in your browser:

```text
frontend/index.html
```

The frontend communicates with the backend running on port `8000`.

---

# API Documentation

---

## 1. Create Transaction

### Endpoint

```http
POST /transaction
```

### Description

Accepts a transaction request, stores it, updates the user's summary, and returns the transaction details along with the updated summary.

### Request Body

```json
{
  "requestId": "req-001",
  "userId": "alice",
  "amount": 100,
  "type": "purchase"
}
```

### Allowed Transaction Types

* `purchase`
* `refund`
* `bonus`

### Successful Response

```json
{
  "duplicate": false,
  "transaction": {
    "requestId": "req-001",
    "userId": "alice",
    "amount": 100,
    "type": "purchase"
  },
  "summary": {
    "userId": "alice",
    "totalPoints": 100,
    "transactionCount": 1
  }
}
```

---

## 2. Get User Summary

### Endpoint

```http
GET /summary/{userId}
```

### Example

```http
GET /summary/alice
```

### Description

Returns aggregated statistics for a user.

### Example Response

```json
{
  "userId": "alice",
  "totalPoints": 100,
  "transactionCount": 1,
  "purchaseCount": 1,
  "refundCount": 0,
  "bonusCount": 0,
  "lastTransactionAt": "2026-06-24T12:00:00"
}
```

---

## 3. Get Rankings

### Endpoint

```http
GET /ranking
```

### Description

Returns all users ordered by their calculated ranking score.

### Example Response

```json
[
  {
    "rank": 1,
    "userId": "bob",
    "score": 124.5
  },
  {
    "rank": 2,
    "userId": "alice",
    "score": 118.0
  }
]
```

---

# Request Validation

Validation is implemented using **Pydantic**.

Each transaction request must contain:

| Field     | Requirement                        |
| --------- | ---------------------------------- |
| requestId | Required and unique                |
| userId    | Must follow allowed pattern        |
| amount    | Positive and within allowed limit  |
| type      | Must be purchase, refund, or bonus |

Invalid requests are automatically rejected with a:

```http
422 Unprocessable Entity
```

Examples of invalid requests:

* Negative amount
* Missing fields
* Invalid user ID format
* Unsupported transaction type

---

# How Duplicate Requests Are Prevented

Duplicate processing is prevented using **idempotency keys**.

Each transaction contains a unique:

```text
requestId
```

The database schema enforces:

```sql
request_id TEXT UNIQUE NOT NULL
```

### Flow

1. Client submits a transaction with a `requestId`.
2. Backend attempts to insert the transaction.
3. If the `requestId` already exists:

   * The database rejects the insert.
   * The backend catches the error.
   * The original transaction is returned.
   * `duplicate: true` is included in the response.

### Example

First request:

```json
{
  "requestId": "req-001"
}
```

Response:

```json
{
  "duplicate": false
}
```

Second request with the same ID:

```json
{
  "requestId": "req-001"
}
```

Response:

```json
{
  "duplicate": true
}
```

This ensures that retries or accidental double submissions never increase points more than once.

---

# Data Consistency

The backend performs transaction insertion and summary updates inside a single database transaction.

Typical flow:

```text
BEGIN IMMEDIATE
→ Insert transaction
→ Update user summary
→ COMMIT
```

If any step fails:

```text
ROLLBACK
```

This guarantees:

* No partial updates
* Consistent summaries
* Safe concurrent writes
* Atomic operations

---

# How Ranking Is Calculated

The leaderboard is intentionally designed to be fair and resistant to abuse.

The final score considers multiple factors instead of only raw points.

### Factors Included

### Positive Factors

* Total points earned
* Number of purchases
* Healthy transaction activity

### Negative Factors

* Refund transactions
* Excessive bonus usage
* Suspiciously high transaction frequency

Example scoring concept:

```text
score =
    total_points
  + purchase_bonus
  + activity_bonus
  - refund_penalty
  - abuse_penalty
```

### Abuse Prevention

Users cannot easily manipulate rankings by:

* Repeatedly submitting bonus transactions
* Spamming many tiny transactions
* Excessively refunding purchases

This keeps the leaderboard more representative of genuine activity.

---

# Running Tests

Execute all tests using:

```bash
pytest
```

Example:

```bash
pytest tests/
```

---

# Assumptions and Trade-Offs

* SQLite is used for simplicity and easy local evaluation.
* Authentication and authorization are not included.
* No rate limiting is implemented.
* Rankings are recalculated on request.
* SQLite can be replaced with PostgreSQL in production.

---

# Future Improvements

* PostgreSQL support
* Authentication and authorization
* Rate limiting
* Audit logging
* Background jobs for ranking updates
* Caching using Redis
* Docker deployment

---

# Tech Stack

* FastAPI
* Python
* SQLite
* Pydantic
* HTML
* CSS
* JavaScript
* Pytest

---
