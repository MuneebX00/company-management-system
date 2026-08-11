import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.dependencies.auth import CurrentUser
from app.dependencies.database import DbSession
from app.dependencies.rbac import require_permission
from app.models import Company, User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from app.services.org import get_scoped_company

router = APIRouter()


@router.get(
    "",
    response_model=CompanyResponse,
    summary="Get the current user's company",
    description="Tenant-isolated: always returns the company the user belongs to.",
)
def get_own_company(current_user: CurrentUser) -> CompanyResponse:
    return CompanyResponse.model_validate(current_user.company)


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get a company (own tenant only)",
)
def get_company(
    company_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("company.view"))],
) -> CompanyResponse:
    return CompanyResponse.model_validate(get_scoped_company(db, current_user, company_id))


@router.post(
    "",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new company tenant",
)
def create_company(
    payload: CompanyCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("company.create"))],
) -> CompanyResponse:
    company = Company(**payload.model_dump(exclude_unset=True))
    db.add(company)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Company name already exists"
        ) from exc
    db.refresh(company)
    return CompanyResponse.model_validate(company)


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Update the current user's company",
)
def update_company(
    company_id: uuid.UUID,
    payload: CompanyUpdate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("company.update"))],
) -> CompanyResponse:
    company = get_scoped_company(db, current_user, company_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(company, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Company name already exists"
        ) from exc
    db.refresh(company)
    return CompanyResponse.model_validate(company)
