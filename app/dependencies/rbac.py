from fastapi import HTTPException, status

from app.core.roles import RoleName
from app.dependencies.auth import CurrentUser


def require_roles(*roles: RoleName):
    """Dependency factory requiring the current user to hold one of the roles."""

    def _require(current_user: CurrentUser) -> CurrentUser:
        if current_user.role.name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return _require


def require_permission(code: str):
    """Dependency factory requiring the current user's role to hold a permission."""

    def _require(current_user: CurrentUser) -> CurrentUser:
        granted = {permission.code for permission in current_user.role.permissions}
        if code not in granted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return _require


def require_any_permission(*codes: str):
    """Dependency factory requiring the current user's role to hold any of the permissions."""

    def _require(current_user: CurrentUser) -> CurrentUser:
        granted = {permission.code for permission in current_user.role.permissions}
        if not codes or not any(code in granted for code in codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions"
            )
        return current_user

    return _require
