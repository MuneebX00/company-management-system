import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.models import RefreshToken, User


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Return the user if credentials are valid and the account is active."""
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None or not verify_password(password, user.password_hash):
        return None
    return user


def build_access_token(user: User) -> str:
    return create_access_token(user.id, user.role.name, user.company_id)


def issue_refresh_token(db: Session, user: User) -> str:
    """Create a new refresh token for a user and persist its hash."""
    settings = get_settings()
    raw_token = _generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    db.commit()
    return raw_token


def _get_token_record(db: Session, raw_token: str) -> RefreshToken | None:
    return db.scalar(select(RefreshToken).where(RefreshToken.token_hash == _hash_token(raw_token)))


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, str] | None:
    """Validate a refresh token, revoke it and issue a replacement."""
    record = _get_token_record(db, raw_token)
    if record is None:
        return None
    if record.revoked_at is not None or record.expires_at <= datetime.now(UTC):
        return None

    user = record.user
    record.revoked_at = datetime.now(UTC)
    db.add(record)

    settings = get_settings()
    new_raw_token = _generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=_hash_token(new_raw_token),
            expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    db.commit()
    return user, new_raw_token


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    """Revoke a refresh token if it exists and is not already revoked."""
    record = _get_token_record(db, raw_token)
    if record is None or record.revoked_at is not None:
        return
    record.revoked_at = datetime.now(UTC)
    db.commit()


def record_login(db: Session, user: User) -> None:
    user.last_login_at = datetime.now(UTC)
    db.commit()
