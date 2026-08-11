import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.dependencies.auth import CurrentUser
from app.dependencies.database import DbSession
from app.dependencies.rbac import require_permission
from app.models import User
from app.schemas.user import UserResponse
from app.utils.pagination import Page, PageParams, get_page

router = APIRouter()


def _get_company_user(db: DbSession, current_user: CurrentUser, user_id: uuid.UUID) -> User:
    user = db.get(User, user_id)
    if user is None or user.company_id != current_user.company_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get(
    "",
    response_model=Page[UserResponse],
    summary="List users in the current company",
)
def list_users(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    current_user: Annotated[User, Depends(require_permission("user.view"))],
) -> Page[UserResponse]:
    statement = (
        select(User)
        .where(User.company_id == current_user.company_id)
        .order_by(User.created_at.desc())
    )
    items, total = get_page(db, statement, params.page, params.page_size)
    return Page[UserResponse](
        items=[UserResponse.model_validate(user) for user in items],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user within the current company",
)
def get_user(
    user_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("user.view"))],
) -> UserResponse:
    return UserResponse.model_validate(_get_company_user(db, current_user, user_id))
