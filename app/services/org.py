import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, false, select
from sqlalchemy.orm import Session

from app.core.roles import RoleName
from app.models import Company, Department, Employee, Employer, User


def _not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


def get_scoped_company(db: Session, current_user: User, company_id: uuid.UUID) -> Company:
    """Return a company only if it belongs to the current user."""
    company = db.get(Company, company_id)
    if company is None or company.id != current_user.company_id:
        raise _not_found("Company")
    return company


def get_scoped_department(db: Session, current_user: User, department_id: uuid.UUID) -> Department:
    department = db.get(Department, department_id)
    if department is None or department.company_id != current_user.company_id:
        raise _not_found("Department")
    return department


def get_scoped_employer(db: Session, current_user: User, employer_id: uuid.UUID) -> Employer:
    employer = db.get(Employer, employer_id)
    if employer is None or employer.company_id != current_user.company_id:
        raise _not_found("Employer")
    return employer


def get_scoped_employee(db: Session, current_user: User, employee_id: uuid.UUID) -> Employee:
    """Fetch an employee, enforcing company and role-level scoping."""
    employee = db.get(Employee, employee_id)
    if employee is None or employee.company_id != current_user.company_id:
        raise _not_found("Employee")
    if not _may_view_employee(current_user, employee):
        raise _not_found("Employee")
    return employee


def _may_view_employee(current_user: User, employee: Employee) -> bool:
    if current_user.role.name == RoleName.ADMIN_HR:
        return True
    if current_user.role.name == RoleName.EMPLOYER:
        profile = current_user.employer_profile
        return profile is not None and employee.employer_id == profile.id
    return employee.user_id == current_user.id


def employee_scope_condition(current_user: User):
    """SQLAlchemy boolean expression limiting employee queries to the user's scope."""
    if current_user.role.name == RoleName.ADMIN_HR:
        return Employee.company_id == current_user.company_id
    if current_user.role.name == RoleName.EMPLOYER:
        profile = current_user.employer_profile
        if profile is None:
            return false()
        return and_(
            Employee.company_id == current_user.company_id,
            Employee.employer_id == profile.id,
        )
    return and_(Employee.company_id == current_user.company_id, Employee.user_id == current_user.id)


def get_company_user(db: Session, user_id: uuid.UUID, company_id: uuid.UUID) -> User:
    """Return a user that belongs to the given company, else 404."""
    user = db.get(User, user_id)
    if user is None or user.company_id != company_id:
        raise _not_found("User")
    return user


def require_user_role(user: User, role: RoleName, label: str) -> None:
    if user.role.name != role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{label} profile requires a {role} user account",
        )


def get_current_employee(db: Session, current_user: User) -> Employee:
    """Return the current user's employee profile, or 404 if they have none."""
    employee = db.scalar(select(Employee).where(Employee.user_id == current_user.id))
    if employee is None:
        raise _not_found("Employee profile")
    return employee


def employee_scope_expr(current_user: User):
    """Boolean SQLAlchemy expression over Employee selecting records the user may access.

    ADMIN_HR: all employees in the company.
    EMPLOYER: employees managed by the caller's employer profile.
    EMPLOYEE: the caller's own profile.
    """
    if current_user.role.name == RoleName.ADMIN_HR:
        return Employee.company_id == current_user.company_id
    if current_user.role.name == RoleName.EMPLOYER:
        profile = current_user.employer_profile
        if profile is None:
            return false()
        return and_(
            Employee.company_id == current_user.company_id,
            Employee.employer_id == profile.id,
        )
    return and_(Employee.company_id == current_user.company_id, Employee.user_id == current_user.id)


def check_employee_number_available(
    db: Session, company_id: uuid.UUID, employee_number: str, exclude_id: uuid.UUID | None = None
) -> None:
    statement = select(Employee).where(
        Employee.company_id == company_id, Employee.employee_number == employee_number
    )
    if exclude_id is not None:
        statement = statement.where(Employee.id != exclude_id)
    if db.scalar(statement) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Employee number '{employee_number}' already exists",
        )
