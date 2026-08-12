# API

Base path: `/api/v1`. JSON, REST. Swagger: http://127.0.0.1:8000/docs.

## Conventions

- **Responses** are Pydantic response models — ORM objects are never serialized directly.
- **Errors** are consistent: `{"detail": ...}` for HTTPException, `{"code", "message"}` for app errors (future).
- **Pagination** (`Page[T]`): `?page=1&page_size=20` returns `{items, page, page_size, total}`.
- **Auth**: `Authorization: Bearer <access_token>` on protected endpoints.

## Endpoints (Phase 5)

### Health

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/health` | no | `{"status": "ok"}` |
| GET | `/health/db` | no | DB round-trip check |

### Auth

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/auth/register` | `user.create` (ADMIN_HR) | Create user in admin's company (201) |
| POST | `/auth/login` | no | OAuth2 password form `username`/`password` → tokens |
| POST | `/auth/refresh` | no | Rotate refresh token → new token pair |
| POST | `/auth/logout` | bearer | Revoke refresh token (204) |
| GET | `/auth/me` | bearer | Current user profile (role, company) |

### Users

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/users` | `user.view` | List users in current company (paginated) |
| GET | `/users/{id}` | `user.view` | Get user in current company (404 cross-company) |

### Companies

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/companies` | bearer | Current user's own company (tenant-isolated) |
| GET | `/companies/{id}` | `company.view` | Get company (404 if not own tenant) |
| POST | `/companies` | `company.create` | Create a new company tenant (409 dup name) |
| PATCH | `/companies/{id}` | `company.update` | Update own company (409 dup name) |

### Departments

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/departments` | `department.view` | List departments in current company (paginated) |
| GET | `/departments/{id}` | `department.view` | Get department (404 cross-company) |
| POST | `/departments` | `department.create` | Create department (409 dup name) |
| PATCH | `/departments/{id}` | `department.update` | Update department |
| DELETE | `/departments/{id}` | `department.delete` | Delete if no employees/employers (409 otherwise) |

### Employers

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/employers` | `employer.view` | List employers in current company (paginated) |
| GET | `/employers/{id}` | `employer.view` | Get employer (404 cross-company) |
| POST | `/employers` | `employer.create` | Create profile for an EMPLOYER user (400 wrong role, 409 dup) |
| PATCH | `/employers/{id}` | `employer.update` | Update employer profile |

### Employees

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/employees` | `employee.view` | List employees in caller's scope (see note) |
| GET | `/employees/me` | bearer | Current user's own employee profile (404 if none) |
| GET | `/employees/{id}` | `employee.view` | Get employee in scope (404 out of scope/cross-company) |
| POST | `/employees` | `employee.create` | Create profile for an EMPLOYEE user (409 dup number) |
| PATCH | `/employees/{id}` | `employee.update` | Update employee in scope (409 dup number) |

**Employee list/get scope**: ADMIN_HR sees all company employees; EMPLOYER sees only employees
where `employer_id == their profile`; EMPLOYEE sees only themselves. Out-of-scope access returns 404.

### Attendance

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/attendance/check-in` | `attendance.check_in` | Check in for today (409 if already checked in) |
| POST | `/attendance/check-out` | `attendance.check_out` | Check out, computes `hours_worked` (409 if not checked in) |
| GET | `/attendance` | `view_self` or `view_all` | List records in caller's scope, `?from_date&to_date` |
| GET | `/attendance/{id}` | `view_self` or `view_all` | Get record in scope (404 out of scope) |
| PATCH | `/attendance/{id}` | `attendance.correct` | Admin: fix timestamps/status, recompute hours |

Attendance list/get is role-scoped (same rule as employees): admin all, employer team, employee self.

### Leave

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/leave/types` | any leave perm | List company leave types (paginated) |
| GET | `/leave/types/{id}` | any leave perm | Get leave type (404 cross-company) |
| POST | `/leave/types` | `company.update` | Admin: create leave type (409 dup name) |
| PATCH | `/leave/types/{id}` | `company.update` | Admin: update leave type |
| DELETE | `/leave/types/{id}` | `company.update` | Admin: delete (409 if referenced by requests) |
| GET | `/leave/requests` | `view_self` or `view_all` | List requests in caller's scope (paginated) |
| GET | `/leave/requests/{id}` | any leave perm | Get request in scope (404 out of scope) |
| POST | `/leave/requests` | `leave.create` | Create request (409 on overlap with pending/approved) |
| PATCH | `/leave/requests/{id}` | any leave perm | Owner edits own pending request (recomputes days) |
| POST | `/leave/requests/{id}/approve` | `leave.approve` | Approve (409 if not pending); employer limited to team |
| POST | `/leave/requests/{id}/reject` | `leave.approve` | Reject (409 if not pending); employer limited to team |
| POST | `/leave/requests/{id}/cancel` | any leave perm | Owner or manager cancels a pending request |

**Leave rules**: `days = (end - start) + 1`; overlapping PENDING/APPROVED requests for the same
employee are rejected with 409; only PENDING requests can be updated/approved/rejected/cancelled.

### Projects

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/projects` | `project.view` | List projects in caller's scope (paginated) |
| GET | `/projects/{id}` | `project.view` | Get project in scope (404 out of scope/cross-company) |
| POST | `/projects` | `project.create` | Create project (409 dup name) |
| PATCH | `/projects/{id}` | `project.update` | Update project (name/status/owner/dates) |
| DELETE | `/projects/{id}` | `project.update` | Delete project (cascades tasks + members, 204) |
| POST | `/projects/{id}/members` | `project.member_manage` | Add employee as member (409 dup, 404 foreign employee) |
| GET | `/projects/{id}/members` | `project.view` | List project members |
| DELETE | `/projects/{id}/members/{employee_id}` | `project.member_manage` | Remove a member (204) |

**Project scope**: ADMIN_HR sees all company projects; EMPLOYER sees only projects they own
(`owner_id == their profile`); employees have no `project.view` permission. Out-of-scope → 404.

### Tasks

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/tasks` | `task.view` | List tasks in caller's scope (paginated) |
| GET | `/tasks/{id}` | `task.view` | Get task in scope (404 out of scope) |
| POST | `/tasks` | `task.create` | Create task in a project (404 foreign project/assignee) |
| PATCH | `/tasks/{id}` | `task.update` | Update task; sets/clears `completed_at` on DONE |
| POST | `/tasks/{id}/assign` | `task.assign` | Assign task to an employee in scope |

**Task scope**: ADMIN_HR sees all company tasks; EMPLOYER sees tasks in projects they own;
EMPLOYEE sees only tasks assigned to them. Employees may only update `status`/`description`
of their own tasks (403 otherwise); completing a task sets `completed_at`.

## Tenant isolation

All Phase 3 read/write operations are scoped to the caller's company via
`app/services/org.py`. Cross-company lookups (and out-of-role-scope employee access) return 404,
never 403, to avoid leaking resource existence.

## Example login

```
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin@example.com&password=Admin123!
```

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "token_type": "bearer"
}
```

## Example authenticated call

```
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

## Example register

```
POST /api/v1/auth/register
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{ "email": "emp1@example.com", "password": "Password123!", "role_code": "EMPLOYEE" }
```

## Example create employee

```
POST /api/v1/employees
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "user_id": "<EMPLOYEE user id>",
  "department_id": "<department id>",
  "employer_id": "<employer id>",
  "employee_number": "E001",
  "first_name": "Jane",
  "last_name": "Doe",
  "job_title": "Software Engineer",
  "employment_status": "ACTIVE"
}
```

Later phases add payroll, notifications and AI endpoints.
