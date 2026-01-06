# Lyftr AI Backend

![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Multi--Stage-2496ED?style=flat-square)
![Status](https://img.shields.io/badge/Build-Passing-success?style=flat-square)

A production-grade, containerized webhook ingestion service designed for reliability, observability, and strict security.

## Overview

This service implements a robust "WhatsApp-like" message ingestion system. It is engineered to handle high-throughput webhook events with **exactly-once processing guarantees** and **defensive security practices**.

### Key Features
- **Defensive Security**: HMAC-SHA256 signature verification is performed *before* payload parsing to prevent DoS attacks on the JSON parser.
- **Idempotency**: Database-level constraints ensure that retried webhooks (common in distributed systems) are handled gracefully without data duplication.
- **Observability**: 
  - **Structured JSON Logs**: Machine-parsable logs with `latency_ms` and `request_id` for easy integration with aggregators (Datadog/Splunk).
  - **Prometheus Metrics**: Exposes `http_requests_total` and `webhook_requests_total` for real-time monitoring.
- **12-Factor App**: Fully containerized with strict separation of config (env vars) and code.

---

## Quick Start

### Prerequisites
- Docker Desktop (or Docker Engine + Compose)

### 1. Build and Run
The project uses a **Makefile** for convenience, but standard Docker commands work natively.

```bash
# Option A: Using Make (Linux/Mac/WSL)
make up

# Option B: Using Docker Compose directly (Windows PowerShell)
docker compose up -d --build
````

The API will be available at: `http://localhost:8000`

### 2\. Verify Health

Ensure the service is ready and connected to the database:

```bash
curl -f http://localhost:8000/health/ready
# Response: {"status": "ready"}
```

### 3\. Run Test Suite

Execute the integration tests *inside* the isolated container environment:

```bash
# Option A
make test

# Option B
docker compose run --rm api pytest -v tests/
```

### 4\. Stop Service

```bash
docker compose down -v
```

-----

## API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/webhook` | Ingests a new message. Requires `X-Signature` header. |
| `GET` | `/messages` | Lists messages. Supports pagination (`limit`, `offset`) and filtering. |
| `GET` | `/stats` | Returns analytical aggregates (top senders, total count). |
| `GET` | `/metrics` | Prometheus-formatted metrics for scraping. |
| `GET` | `/health/live` | Liveness probe (Kubernetes style). |
| `GET` | `/health/ready` | Readiness probe (Checks DB connectivity). |

### Example: Consuming /messages

Pagination and filtering are built-in:

```http
GET /messages?limit=10&offset=0&from=+919876543210&since=2025-01-01T00:00:00Z
```

-----

## Architectural Decisions

This project follows **Clean Architecture** principles to ensure maintainability and testability.

### 1\. Security & The "Fail Fast" Principle

**Decision:** Implement HMAC verification as a dependency that runs **before** Pydantic validation.

  - **Why:** Parsing JSON is computationally expensive compared to hashing. By verifying the signature on the raw bytes first, we drop malicious requests immediately. This protects the CPU from being exhausted by large, invalid JSON payloads.
  - **Implementation:** Used `hmac.compare_digest` to prevent timing attacks.

### 2\. Storage & Idempotency

**Decision:** Enforce uniqueness at the Database Layer, not the Application Layer.

  - **Why:** Distributed locks (like Redis) add complexity and potential race conditions.
  - **Implementation:** The SQLite table uses `message_id` as the `PRIMARY KEY`. When a duplicate comes in, the app catches the `sqlite3.IntegrityError` and returns `200 OK`. This satisfies the requirement to be idempotent without inserting duplicate rows.

### 3\. Repository Pattern

**Decision:** Isolate all SQL logic in `app/storage.py`.

  - **Why:** The API Controller (`main.py`) should focus on HTTP logic (status codes, headers), while the Storage layer focuses on Data Logic. This Separation of Concerns makes it easy to swap SQLite for PostgreSQL in the future without rewriting the API.

### 4\. Performance Optimization

**Decision:** Add an Index on the Timestamp column.

  - **Why:** The `/messages` endpoint requires sorting by time (`ORDER BY ts ASC`). Without an index (`CREATE INDEX idx_messages_ts`), performance would degrade to O(N log N) as the dataset grows. The index keeps retrieval fast.

-----

## Project Structure

```text
lyftr-assignment/
├── app/
│   ├── config.py          # Pydantic Settings (12-factor config)
│   ├── logging_utils.py   # Custom JSON Log Formatter
│   ├── main.py            # FastAPI Entrypoint & Middleware
│   ├── metrics.py         # Prometheus Metrics Logic
│   ├── models.py          # Data Contracts (Pydantic Schemas)
│   └── storage.py         # SQLite Repository Layer
├── tests/                 # Integration Tests
├── Dockerfile             # Multi-stage build (Builder -> Slim Runtime)
├── docker-compose.yml     # Orchestration & Volume Mapping
└── Makefile               # Task Automation
```

-----

## Setup Used

  - **Environment:** Windows 11 + Docker Desktop + VS Code
  - **AI Usage:** - **GitHub Copilot**: Used for boilerplate code generation (Pydantic models, SQL queries).
      - **ChatGPT**: Used for validating Docker multi-stage build best practices and generating edge-case test scenarios for HMAC verification.

-----
Built as a POC for CyberSec for my profile
-----
