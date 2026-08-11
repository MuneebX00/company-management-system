# Architecture

## Overview

The backend is a layered FastAPI application. Dependencies point inward: HTTP routing depends on services/dependencies, services depend on repositories/models, and models are the domain core.

```
api/v1 (routes + schemas)
    │
    ▼
dependencies (auth, RBAC, tenant scoping)
    │
    ▼
services (business logic)
    │
    ▼
repositories (optional persistence layer)
    │
    ▼
models (SQLAlchemy ORM) ──► PostgreSQL
```

- **api/** — versioned routers (`/api/v1`), request/response validation via Pydantic schemas. Never expose ORM objects directly.
- **dependencies/** — reusable FastAPI dependencies (`get_current_user`, `require_role`, `require_permission`, tenant-scoped resource lookups).
- **services/** — business logic and transaction boundaries. Kept thin where a repository/endpoint can do the job simply.
- **repositories/** — introduced only where they add real value (complex queries, reuse across services); not a blanket layer.
- **models/** — SQLAlchemy 2.x declarative mappings (`Mapped[]`, `mapped_column()`).

## Key decisions

### Sync SQLAlchemy
The prompt proposed async SQLAlchemy as an option. The domain is CRUD-heavy with no high-concurrency I/O bottleneck, so we use **synchronous SQLAlchemy with psycopg 3**. FastAPI runs sync route handlers in a thread pool, so the API stays fully async-capable. This keeps transaction handling, sessions and test fixtures simpler and avoids async pitfalls (blocking calls, session reuse across tasks). Async is introduced only where it provides a real benefit (e.g. future AI streaming endpoints), via `run_in_threadpool` or a dedicated async engine, without restructuring the app.

### Repositories are optional
The prompt asked for a `repositories/` layer. We keep it only where it pays off — most endpoints use services + `Session` directly, avoiding an extra indirection layer that would add boilerplate without value. The package exists so it can be used when queries grow complex.

### UUID primary keys
All primary keys are `UUID` (PostgreSQL-native, generated in Python with `uuid4`). Integer keys are avoided because they leak ordering/counting information and complicate tenant-merged data later.

### Tenant isolation by design
Every company-owned resource carries `company_id`. Authorization dependencies enforce company boundaries at the backend before any access is granted — never relying on the frontend. Initially a user belongs to one company; the `users`/membership model is structured so multi-company membership can be added without a rewrite.

`app/services/org.py` centralizes tenant-scoped lookups (`get_scoped_company/department/employer/employee`) returning 404 for anything outside the caller's company or role scope — including employee records an EMPLOYER or EMPLOYEE is not allowed to see, preventing resource-existence leakage.

### Role scoping for employees
- **ADMIN_HR** — full visibility of every company resource.
- **EMPLOYER** — read/update on employees, but limited to their own team (`employee.employer_id == employer_profile.id`).
- **EMPLOYEE** — read-only self-access (`employee.user_id == current_user.id`).

The same scoping is applied to attendance records and leave requests via
`employee_scope_expr` (list queries join through `Employee`) and the scoped getters in
`app/services/attendance.py` / `app/services/leave.py`. An employer can approve/reject leave only
for their own team; an employee can only see/cancel their own requests.

### Money
Monetary values use `Numeric(12, 2)` via SQLAlchemy `Numeric`, and calculations use `decimal.Decimal`. No floating point anywhere in payroll.

## Environment & configuration

- `app/core/config.py` — Pydantic Settings, loads `.env`, cached via `get_settings()`.
- `.env` is never committed; `.env.example` documents every variable.
- CORS origins, log level, environment and DB URL are all configuration-driven.

## Database sessions

- `app/core/database.py` exposes `engine`, `SessionLocal`, and `Base`.
- `get_db()` is a dependency that yields a session and always closes it (`finally`), so no sessions leak.
- `pool_pre_ping=True` guards against stale pooled connections.

## Error handling

- `app/core/exceptions.py` defines `AppError` subclasses mapped to consistent JSON errors `{code, message}`.
- Raw database exceptions never reach clients; services translate them into domain errors.

## Logging

- `app/core/logging.py` configures a root logger (console + optional rotating file) with a structured key/value format.
- No `print()` anywhere in application code.

## Migration workflow

- Alembic with `app/core/database.py:Base.metadata` as `target_metadata`.
- Autogenerate a revision, review it, then `alembic upgrade head`.
- Never mutate tables manually when a migration is required.

## Testing strategy

- **Unit** tests (FastAPI `TestClient`) cover routes/validation without needing the DB.
- **Integration** tests (`@pytest.mark.integration`) cover DB/API flows against a real PostgreSQL instance.
- DB-session overrides in tests keep unit tests isolated.

## Future phases

1. ~~Auth & RBAC~~ — users/roles/permissions, JWT (access + refresh), Argon2, `require_role`/`require_permission`. **Done.**
2. ~~Organization~~ — companies, departments, employers, employees. **Done.**
3. ~~Attendance & Leave~~ — check-in/out, corrections, leave types, request/approve/reject/cancel. **Done.**
4. Projects/tasks, payroll, notifications, audit logs.
5. AI foundation: provider-agnostic service interfaces (`ai_insights`, `ai_usage_logs`) so providers plug in without restructuring.
