import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.roles import RoleName
from app.dependencies.auth import CurrentUser
from app.dependencies.database import DbSession
from app.dependencies.rbac import require_permission
from app.models import Employee, User
from app.schemas.employee import (
    EmployeeCreate,
    EmployeeResponse,
    EmployeeUpdate,
)
from app.services.org import (
    check_employee_number_available,
    employee_scope_condition,
    get_company_user,
    get_scoped_department,
    get_scoped_employee,
    get_scoped_employer,
    require_user_role,
)
from app.utils.pagination import Page, PageParams, get_page

router = APIRouter()


@router.get(
    "",
    response_model=Page[EmployeeResponse],
    summary="List employees within the caller's scope",
    description="Admin sees all company employees; employers see their team; "
    "employees see themselves.",
)
def list_employees(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    current_user: Annotated[User, Depends(require_permission("employee.view"))],
) -> Page[EmployeeResponse]:
    statement = (
        select(Employee)
        .where(employee_scope_condition(current_user))
        .order_by(Employee.last_name, Employee.first_name)
    )
    items, total = get_page(db, statement, params.page, params.page_size)
    return Page[EmployeeResponse](
        items=[EmployeeResponse.model_validate(item) for item in items],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


@router.get(
    "/me",
    response_model=EmployeeResponse,
    summary="Get the current user's employee profile",
)
def get_my_employee(db: DbSession, current_user: CurrentUser) -> EmployeeResponse:
    employee = db.scalar(select(Employee).where(Employee.user_id == current_user.id))
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Employee profile not found"
        )
    return EmployeeResponse.model_validate(employee)


@router.get(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Get an employee within the caller's scope",
)
def get_employee(
    employee_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("employee.view"))],
) -> EmployeeResponse:
    employee = get_scoped_employee(db, current_user, employee_id)
    return EmployeeResponse.model_validate(employee)


@router.post(
    "",
    response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an employee profile for an EMPLOYEE user",
)
def create_employee(
    payload: EmployeeCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("employee.create"))],
) -> EmployeeResponse:
    user = get_company_user(db, payload.user_id, current_user.company_id)
    require_user_role(user, RoleName.EMPLOYEE, "Employee")

    if db.scalar(select(Employee).where(Employee.user_id == user.id)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already has an employee profile"
        )

    check_employee_number_available(db, current_user.company_id, payload.employee_number)

    if payload.department_id is not None:
        get_scoped_department(db, current_user, payload.department_id)
    if payload.employer_id is not None:
        get_scoped_employer(db, current_user, payload.employer_id)

    employee = Employee(
        company_id=current_user.company_id,
        user_id=user.id,
        **payload.model_dump(exclude={"user_id"}),
    )
    db.add(employee)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee number already exists in this company",
        ) from exc
    db.refresh(employee)
    return EmployeeResponse.model_validate(employee)


@router.patch(
    "/{employee_id}",
    response_model=EmployeeResponse,
    summary="Update an employee within the caller's scope",
)
def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeUpdate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("employee.update"))],
) -> EmployeeResponse:
    employee = get_scoped_employee(db, current_user, employee_id)

    if payload.department_id is not None:
        get_scoped_department(db, current_user, payload.department_id)
    if payload.employer_id is not None:
        get_scoped_employer(db, current_user, payload.employer_id)
    if payload.employee_number is not None:
        check_employee_number_available(
            db, current_user.company_id, payload.employee_number, exclude_id=employee.id
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee number already exists in this company",
        ) from exc
    db.refresh(employee)
    return EmployeeResponse.model_validate(employee)
