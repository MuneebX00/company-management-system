# Company Management System — Backend

Role-based Company Management System backend built with FastAPI, SQLAlchemy 2.x and PostgreSQL.

## Status

Phase 5 (Projects & Tasks) complete — projects owned by employers, member management, and tasks with assignment, status/priority tracking and completion timestamps. Project and task visibility is role-scoped (admin sees all, employers see their own projects/team, employees see only tasks assigned to them), and deleting a project cascades to its tasks and members. This builds on Phase 4 (Attendance & Leave), Phase 3 (Company & Organization): companies, departments, employer and employee profiles with backend-enforced tenant isolation and role-based scoping, plus Phase 2 (Authentication & RBAC).
Later phases add payroll, notifications, audit and AI foundations.

## Tech stack

- Python 3.13
- FastAPI + Uvicorn
- Pydantic v2 / Pydantic Settings
- SQLAlchemy 2.x (sync, `Mapped[]` / `mapped_column()`)
- Alembic migrations
- PostgreSQL 17 with psycopg 3
- Argon2id password hashing, PyJWT (HS256) access tokens
- pytest / httpx for tests
- Ruff (lint) + mypy (types) via uv

## Requirements

- Windows
- [uv](https://docs.astral.sh/uv/) installed
- PostgreSQL (local, e.g. 17) running on `localhost:5432`
- pgAdmin 4 (optional, for inspection)

## Local setup

1. Clone/enter the project directory.
2. Install dependencies and create the virtual environment:

   ```powershell
   uv sync
   ```

3. Create the application database and role (see below).
4. Copy `.env.example` to `.env` and adjust values:

   ```powershell
   Copy-Item .env.example .env
   ```

## PostgreSQL setup

A PostgreSQL 17 instance is expected on `localhost:5432`. Connect as the superuser (e.g. `postgres`) and run:

```sql
CREATE ROLE company_app LOGIN PASSWORD 'change-me-strong-password';
CREATE DATABASE company_management OWNER company_app;
```

Or, if you prefer the superuser for development, simply create the database:

```sql
CREATE DATABASE company_management;
```

Then set `DATABASE_URL` in `.env` accordingly:

```
DATABASE_URL=postgresql+psycopg://company_app:<PASSWORD>@localhost:5432/company_management
```

## Environment variables

See `.env.example` for the full list. Never commit `.env`.

| Variable | Description | Example |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string (psycopg 3) | `postgresql+psycopg://company_app:pass@localhost:5432/company_management` |
| `ENVIRONMENT` | `development`, `test` or `production` | `development` |
| `LOG_LEVEL` | Python logging level | `INFO` |
| `CORS_ORIGINS` | JSON array of allowed origins | `["http://localhost:3000"]` |
| `SECRET_KEY` | JWT signing key (generate a long random value) | `change-me` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | Development-only admin seed credentials | `admin@example.com` / `Admin123!` |

## Seeding

Roles (`ADMIN_HR`, `EMPLOYER`, `EMPLOYEE`), their permissions, a development company and admin account are created idempotently with:

```powershell
uv run python -m app.seed
```

The admin credentials come from `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` and are **development-only** — seeding of sample data is skipped when `ENVIRONMENT=production`.

## Alembic commands

Run migrations from the project root:

```powershell
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
```

Review generated migrations before applying them.

## Running the backend

```powershell
uv run uvicorn app.main:app --reload
```

- Swagger UI: http://127.0.0.1:8000/docs
- OpenAPI JSON: http://127.0.0.1:8000/openapi.json
- Health: http://127.0.0.1:8000/api/v1/health
- Database health: http://127.0.0.1:8000/api/v1/health/db

### Smoke-testing auth

```powershell
uv run python -m app.seed                      # seed roles + dev admin
# POST /api/v1/auth/login  username=admin@example.com  password=Admin123!
# Use the returned access_token as `Authorization: Bearer <token>` on:
#   GET  /api/v1/auth/me
#   GET  /api/v1/users
#   POST /api/v1/auth/register  (admin only)
```

## Running tests

```powershell
uv run pytest
```

Run lint and type checks:

```powershell
uv run ruff check .
uv run mypy app
```

## Project structure

```
app/
├── main.py               # FastAPI application entry point
├── api/v1/               # Versioned API routes
│   ├── router.py         # Aggregates all v1 routers
│   ├── health.py         # Health endpoints
│   ├── auth.py           # Register/login/refresh/logout/me
│   ├── users.py          # Company-scoped user management
│   ├── companies.py      # Company CRUD (tenant-isolated)
│   ├── departments.py    # Department CRUD
│   ├── employers.py      # Manager profiles (1:1 EMPLOYER users)
│   ├── employees.py      # Employee profiles + role-scoped visibility
│   ├── attendance.py     # Check-in/out, corrections
│   ├── leave.py          # Leave types + request workflow
│   ├── projects.py       # Projects + member management
│   └── tasks.py          # Tasks + assignment
├── core/                 # Config, logging, database, exceptions, security, roles, enums
├── models/               # SQLAlchemy models (company, department, employer, employee, project, task, ...)
├── schemas/              # Pydantic schemas
├── services/             # Business logic (auth, org tenant-scoping, projects)
├── dependencies/         # get_current_user, require_role/permission, session
├── seed.py               # Idempotent dev seeding
├── middleware/
└── utils/
tests/
├── unit/
└── integration/
alembic/                  # Migrations
docs/                     # Design documentation
```

## Architecture overview

- **Layered**: `api` (HTTP) → `dependencies`/`services` (logic) → `models` (ORM). Repositories are only introduced where they add real value.
- **Sync SQLAlchemy**: the domain is CRUD-heavy and does not need async I/O; FastAPI runs sync endpoints in a thread pool. Async is introduced only where it provides a real benefit.
- **Tenant isolation**: company-scoped resources carry `company_id`; authorization enforces company boundaries at the backend (Phase 5 complete). Employee/attendance/leave/project/task visibility is further scoped by role: admin sees all, employers see their team, employees see only themselves.
- **Money**: `Numeric(12, 2)` — no floating point for monetary values (Phase 7).

See `docs/architecture.md` and `docs/database.md` for details.
