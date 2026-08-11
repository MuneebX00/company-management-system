# Database

## PostgreSQL setup

- Local PostgreSQL 17 on `localhost:5432` (service `postgresql-x64-17` running).
- A dedicated application role `company_app` owns the `company_management` database.

Creation SQL (run as superuser, e.g. `postgres`):

```sql
CREATE ROLE company_app LOGIN PASSWORD '<strong-password>';
CREATE DATABASE company_management OWNER company_app;
```

Connection string used by the app (in `.env`):

```
DATABASE_URL=postgresql+psycopg://company_app:<password>@localhost:5432/company_management
```

The local `pg_hba.conf` uses `trust` for localhost, so no password is actually sent during local development; the password is still required for deployments using `scram-sha-256`.

## Conventions

- **Primary keys**: UUID v4, generated in Python (`uuid4`). No integer PKs.
- **Timestamps**: timezone-aware `TIMESTAMP WITH TIME ZONE` (`DateTime(timezone=True)`); defaults set in Python (`datetime.now(UTC)`).
- **Money**: `Numeric(12, 2)`; all calculations use `decimal.Decimal`.
- **Indexes**: on foreign keys and on frequently-filtered columns (`employee_id`, `company_id`, status/date columns).
- **Unique constraints**: only where globally meaningful (`users.email`). Company-scoped uniqueness (e.g. `employee_number` within a company) uses composite unique constraints `(company_id, field)` — never global unique on company-scoped data.
- **Naming**: `snake_case` tables, plural for tables (`users`, `departments`).

## Current schema (Phase 4)

Applied migrations: `d11ebce71a1d` (baseline) → `75faba76c496` (auth/RBAC) → `ba4e58651ce0` (organization) → `03319d823fe2` (employment status check) → `121ff0cdec62` (attendance & leave).

| Table | Purpose |
| --- | --- |
| `alembic_version` | Alembic revision tracking |
| `companies` | Multi-tenant companies |
| `roles` / `permissions` / `role_permissions` | RBAC matrix (47 permissions, 3 roles) |
| `users` | User accounts (unique email, FK role + company) |
| `refresh_tokens` | Rotating hashed refresh tokens |
| `departments` | Company departments (unique `(company_id, name)`) |
| `employers` | Manager profiles, 1:1 with an EMPLOYER user |
| `employees` | Employee profiles, 1:1 with an EMPLOYEE user |
| `leave_types` | Company leave categories (unique `(company_id, name)`) |
| `leave_requests` | Employee leave requests + review fields |
| `attendance_records` | One record per employee per work date |

### employees

- Unique `user_id` (1:1 with users).
- Unique `(company_id, employee_number)` — employee numbers are only unique within a company.
- `employment_status` is `VARCHAR(20)` with a CHECK constraint (`ck_employees_employment_status`) restricting to `ACTIVE / ON_LEAVE / SUSPENDED / TERMINATED`.
- `employer_id` FK uses `ON DELETE SET NULL` (deleting a manager keeps the employee); other FKs use `ON DELETE RESTRICT`.

### attendance_records

- Unique `(employee_id, work_date)` — at most one record per employee per day.
- `status` is `VARCHAR(20)` with a CHECK constraint restricting to `PRESENT / LATE / ABSENT / HALF_DAY / ON_LEAVE`.
- `hours_worked` is `Numeric(5, 2)`, computed on check-out and recomputed on admin correction.

### leave_requests

- `status` is `VARCHAR(20)` with a CHECK constraint restricting to `PENDING / APPROVED / REJECTED / CANCELLED`.
- `days` is inclusive calendar days: `(end_date - start_date) + 1`.
- `reviewed_by` → `users.id` (the approving/rejecting user); NULL until reviewed.
- Overlap (same employee, PENDING/APPROVED, date-range intersection) is enforced in the service layer.

Planned tables (later phases):

- **Payroll**: `salary_structures`, `payroll_periods`, `payroll_records`, `payslips`
- **Projects**: `projects`, `project_members`, `tasks`
- **System**: `notifications`, `audit_logs`
- **AI**: `ai_insights`, `ai_usage_logs`

## Key relationships (target model)

- `companies 1:N departments`
- `departments 1:N employees`, `departments 1:N employers`
- `employers 1:N employees` (one primary manager per employee)
- `employees 1:N attendance_records`, `1:N leave_requests`
- `companies 1:N leave_types`, `leave_types 1:N leave_requests`
- `companies 1:N projects`, `employers 1:N projects`
- `employees N:M projects` via `project_members`
- `projects 1:N tasks`, `employees 1:N tasks`
- `roles 1:N users`, `users 1:1 employees`, `users 1:1 employers`

## Migration workflow

```
uv run alembic revision --autogenerate -m "message"   # generate
# review alembic/versions/<file>.py
uv run alembic upgrade head                            # apply
```

Status check:

```
uv run alembic current
uv run alembic history
```
