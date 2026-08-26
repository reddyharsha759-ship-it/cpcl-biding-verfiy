# GeM Bid Compliance Verification Platform

Automated AI-powered multi-pillar compliance verification platform for Government e-Marketplace (GeM) tenders.

## 🚀 Features (Phase 1)

- **SQLAlchemy 2.0 Async Data Layer:** Domain models with PostgreSQL UUID primary keys, JSONB payloads, and relationship mappings.
- **Pydantic v2 Validation Schemas:** Robust validation for GSTIN, PAN, Udyam registration, verification jobs, and compliance audit logs.
- **Auditability & Cryptographic Integrity:** SHA-256 payload hashing on all 6 verification pillars (`GST`, `UDYAM`, `PAN`, `MII`, `DEBARMENT`, `OEM`).
- **Async Migrations:** Alembic setup configured for asyncpg.
- **Containerization:** Docker Compose orchestrating PostgreSQL 16, Redis 7, FastAPI API service, and Celery worker.

## 📦 Project Structure

```
├── alembic/                  # Database migration scripts
│   ├── versions/
│   │   └── 0001_initial_schema.py
│   ├── env.py
│   └── script.py.mako
├── app/
│   ├── api/                  # API endpoints and routes
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   └── health.py
│   │       └── router.py
│   ├── core/                 # Core configs, DB, Celery
│   │   ├── config.py
│   │   ├── database.py
│   │   └── celery_app.py
│   ├── models/               # Domain models & Pydantic schemas
│   │   ├── domain.py
│   │   └── schemas.py
│   └── main.py               # FastAPI application entrypoint
├── tests/                    # Unit and integration tests
│   ├── conftest.py
│   ├── test_api_health.py
│   └── test_domain_and_schemas.py
├── docker-compose.yml        # Docker composition
├── Dockerfile                # API & Celery worker container
├── pyproject.toml            # Dependencies and project metadata
└── .env.example              # Environment variable template
```

## 🛠️ Quick Start

### 1. Local Environment Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Or on Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -e ".[dev]"

# Copy environment variables
cp .env.example .env
```

### 2. Running with Docker Compose

```bash
docker-compose up --build
```

### 3. Running Database Migrations

```bash
alembic upgrade head
```

### 4. Running Tests

```bash
pytest
```
