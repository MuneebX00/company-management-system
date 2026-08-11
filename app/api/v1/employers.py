import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.core.roles import RoleName
from app.dependencies.database import DbSession
from app.dependencies.rbac import require_permission
from app.models import Employer, User
from app.schemas.employer import EmployerCreate, EmployerResponse, EmployerUpdate
from app.services.org import (
    get_company_user,
    get_scoped_department,
    get_scoped_employer,
    require_user_role,
)
from app.utils.pagination import Page, PageParams, get_page

router = APIRouter()


@router.get(
    "",
    response_model=Page[EmployerResponse],
    summary="List employers in the current company",
)
def list_employers(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    current_user: Annotated[User, Depends(require_permission("employer.view"))],
) -> Page[EmployerResponse]:
    statement = (
        select(Employer)
        .where(Employer.company_id == current_user.company_id)
        .order_by(Employer.last_name, Employer.first_name)
    )
    items, total = get_page(db, statement, params.page, params.page_size)
    return Page[EmployerResponse](
        items=[EmployerResponse.model_validate(item) for item in items],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


@router.get(
    "/{employer_id}",
    response_model=EmployerResponse,
    summary="Get an employer in the current company",
)
def get_employer(
    employer_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("employer.view"))],
) -> EmployerResponse:
    employer = get_scoped_employer(db, current_user, employer_id)
    return EmployerResponse.model_validate(employer)


@router.post(
    "",
    response_model=EmployerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an employer profile for an EMPLOYER user",
)
def create_employer(
    payload: EmployerCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("employer.create"))],
) -> EmployerResponse:
    user = get_company_user(db, payload.user_id, current_user.company_id)
    require_user_role(user, RoleName.EMPLOYER, "Employer")

    if db.scalar(select(Employer).where(Employer.user_id == user.id)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="User already has an employer profile"
        )

    employer = Employer(
        company_id=current_user.company_id,
        user_id=user.id,
        **payload.model_dump(exclude={"user_id"}, exclude_unset=True),
    )
    if payload.department_id is not None:
        get_scoped_department(db, current_user, payload.department_id)

    db.add(employer)
    db.commit()
    db.refresh(employer)
    return EmployerResponse.model_validate(employer)


@router.patch(
    "/{employer_id}",
    response_model=EmployerResponse,
    summary="Update an employer profile",
)
def update_employer(
    employer_id: uuid.UUID,
    payload: EmployerUpdate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("employer.update"))],
) -> EmployerResponse:
    employer = get_scoped_employer(db, current_user, employer_id)
    if payload.department_id is not None:
        get_scoped_department(db, current_user, payload.department_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(employer, field, value)
    db.commit()
    db.refresh(employer)
    return EmployerResponse.model_validate(employer)
