import uuid
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_access_token
from app.dependencies.database import DbSession
from app.models import User

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

TOKEN_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: Annotated[str, Depends(_oauth2_scheme)], db: DbSession) -> User:
    """Resolve the authenticated user from the bearer access token."""
    try:
        payload = decode_access_token(token)
        user_id = payload.get("user_id")
        if user_id is None:
            raise TOKEN_EXCEPTION
        user = db.get(User, uuid.UUID(user_id))
    except (jwt.InvalidTokenError, ValueError):
        raise TOKEN_EXCEPTION from None

    if user is None:
        raise TOKEN_EXCEPTION
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
