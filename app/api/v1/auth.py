import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.roles import RoleName
from app.core.security import hash_password
from app.dependencies.auth import CurrentUser
from app.dependencies.database import DbSession
from app.dependencies.rbac import require_permission
from app.models import Role, User
from app.schemas.auth import (
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserMeResponse,
)
from app.schemas.user import UserCreate, UserResponse
from app.services.auth import (
    authenticate_user,
    build_access_token,
    issue_refresh_token,
    record_login,
    revoke_refresh_token,
    rotate_refresh_token,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user account",
    description="Admin/HR only. Creates a user within the current admin's company.",
)
def register(
    payload: UserCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("user.create"))],
) -> UserResponse:
    role = db.scalar(select(Role).where(Role.name == payload.role_code))
    if role is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown role")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        role_id=role.id,
        company_id=current_user.company_id,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from exc

    db.refresh(user)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in with email and password",
    description="OAuth2 password flow. Returns access and refresh tokens.",
)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
) -> TokenResponse:
    user = authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")

    record_login(db, user)
    return TokenResponse(
        access_token=build_access_token(user),
        refresh_token=issue_refresh_token(db, user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for new tokens",
    description="Rotates the refresh token: the presented token is revoked and a new one issued.",
)
def refresh(payload: RefreshRequest, db: DbSession) -> TokenResponse:
    rotated = rotate_refresh_token(db, payload.refresh_token)
    if rotated is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    user, new_refresh_token = rotated
    return TokenResponse(
        access_token=build_access_token(user),
        refresh_token=new_refresh_token,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a refresh token",
)
def logout(payload: LogoutRequest, db: DbSession, current_user: CurrentUser) -> None:
    revoke_refresh_token(db, payload.refresh_token)
    logger.info("User %s logged out", current_user.id)


@router.get(
    "/me",
    response_model=UserMeResponse,
    summary="Get current user profile",
)
def me(current_user: CurrentUser) -> UserMeResponse:
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        role=RoleName(current_user.role.name),
        company_id=current_user.company_id,
        company_name=current_user.company.name,
        is_active=current_user.is_active,
        last_login_at=current_user.last_login_at,
    )
