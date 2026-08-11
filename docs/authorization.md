# Authorization (RBAC)

## Model

- **users** → one **role** (`users.role_id`).
- **roles** have many **permissions** via `role_permissions` (many-to-many).
- Endpoints enforce access with reusable dependencies, never inline role checks scattered through code.

## Dependencies

`app/dependencies/auth.py`:

- `get_current_user` — resolves the authenticated user from the bearer token (401 on bad/missing token, 403 on inactive account).

`app/dependencies/rbac.py`:

- `require_roles(*roles)` — the user must hold one of the given roles, else 403.
- `require_permission(code)` — the user's role must grant the permission code, else 403.

Usage pattern (B008-safe `Annotated` style):

```python
from typing import Annotated
from fastapi import Depends
from app.dependencies.rbac import require_permission


def create_user(
    payload: UserCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("user.create"))],
) -> UserResponse: ...
```

## Roles

| Role | Purpose | Permissions |
| --- | --- | --- |
| `ADMIN_HR` | Organization, HR, payroll, compliance | All permissions |
| `EMPLOYER` | Department/team/project management, attendance oversight, leave approval, read-only payroll | Employer subset (no user/company/role management) |
| `EMPLOYEE` | Self-service | Self-scoped subset (own attendance, leave, payroll, tasks) |

Permission codes live as constants in `app/core/roles.py` (`PermissionCodes`), with the role→permission mapping in `ROLE_PERMISSIONS`. Seeding (`app/seed.py`) is idempotent and derives from the same constants, so code and database never drift.

## Tenant isolation

Every company-owned resource carries `company_id`. Company boundary checks are **enforced in the backend**:

- `GET /api/v1/users/{id}` loads the user, then returns 404 unless `user.company_id == current_user.company_id`.
- `GET /api/v1/users` filters by the current user's company.
- Changing an ID in the URL to another company's resource returns 404 (not 403) to avoid revealing that the resource exists.

This pattern is centralized in `app/services/org.py` for Phase 3 resources (companies, departments, employers, employees). `get_scoped_company/department/employer/employee` return 404 for any lookup outside the caller's tenant; `employee_scope_condition`/`get_scoped_employee` additionally enforce role-level data scoping:

- **ADMIN_HR** — all company employees.
- **EMPLOYER** — only employees whose `employer_id` matches the caller's employer profile.
- **EMPLOYEE** — only their own record.

## Principle

- Role-level checks: `require_roles(...)`.
- Complex/overlapping capabilities: `require_permission(...)`.
- Data scoping: company equality checks in the endpoint/service layer, centralized per resource.
