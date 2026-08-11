import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.dependencies.database import DbSession
from app.dependencies.rbac import require_permission
from app.models import Department, Employee, Employer, User
from app.schemas.department import (
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
)
from app.services.org import get_scoped_department
from app.utils.pagination import Page, PageParams, get_page

router = APIRouter()


@router.get(
    "",
    response_model=Page[DepartmentResponse],
    summary="List departments in the current company",
)
def list_departments(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    current_user: Annotated[User, Depends(require_permission("department.view"))],
) -> Page[DepartmentResponse]:
    statement = (
        select(Department)
        .where(Department.company_id == current_user.company_id)
        .order_by(Department.name)
    )
    items, total = get_page(db, statement, params.page, params.page_size)
    return Page[DepartmentResponse](
        items=[DepartmentResponse.model_validate(item) for item in items],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


@router.get(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Get a department in the current company",
)
def get_department(
    department_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("department.view"))],
) -> DepartmentResponse:
    department = get_scoped_department(db, current_user, department_id)
    return DepartmentResponse.model_validate(department)


@router.post(
    "",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a department",
)
def create_department(
    payload: DepartmentCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("department.create"))],
) -> DepartmentResponse:
    department = Department(
        company_id=current_user.company_id, **payload.model_dump(exclude_unset=True)
    )
    db.add(department)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department name already exists in this company",
        ) from exc
    db.refresh(department)
    return DepartmentResponse.model_validate(department)


@router.patch(
    "/{department_id}",
    response_model=DepartmentResponse,
    summary="Update a department",
)
def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("department.update"))],
) -> DepartmentResponse:
    department = get_scoped_department(db, current_user, department_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(department, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department name already exists in this company",
        ) from exc
    db.refresh(department)
    return DepartmentResponse.model_validate(department)


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an empty department",
)
def delete_department(
    department_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("department.delete"))],
) -> None:
    department = get_scoped_department(db, current_user, department_id)
    employee_count = db.scalar(
        select(func.count()).select_from(Employee).where(Employee.department_id == department.id)
    )
    employer_count = db.scalar(
        select(func.count()).select_from(Employer).where(Employer.department_id == department.id)
    )
    if employee_count or employer_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a department that has employees or employers",
        )
    db.delete(department)
    db.commit()
