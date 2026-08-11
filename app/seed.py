"""Development database seeding.

Run with: uv run python -m app.seed

Idempotent. Seeds permission codes and the three roles. In non-production
environments it also creates a default company and an admin account whose
credentials are development-only (configured via SEED_ADMIN_EMAIL /
SEED_ADMIN_PASSWORD).
"""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.roles import ROLE_PERMISSIONS, RoleName
from app.core.security import hash_password
from app.models import Company, Permission, Role, User

logger = logging.getLogger(__name__)


def seed_roles_and_permissions(db: Session) -> None:
    """Create all permissions and the three roles with their permission sets."""
    permissions_by_code: dict[str, Permission] = {}

    for codes in ROLE_PERMISSIONS.values():
        for code in codes:
            if code in permissions_by_code:
                continue
            permission = db.scalar(select(Permission).where(Permission.code == code))
            if permission is None:
                permission = Permission(code=code)
                db.add(permission)
            permissions_by_code[code] = permission

    db.flush()

    for role_name, codes in ROLE_PERMISSIONS.items():
        role = db.scalar(select(Role).where(Role.name == role_name))
        if role is None:
            role = Role(name=role_name, description=f"{role_name} role")
            db.add(role)
        role.permissions = [permissions_by_code[code] for code in codes]

    db.commit()
    logger.info("Seeded roles and permissions")


def seed_dev_company_and_admin(db: Session) -> None:
    """Create a development company and ADMIN_HR account. Dev-only."""
    settings = get_settings()

    company = db.scalar(select(Company).where(Company.name == "Acme Corporation"))
    if company is None:
        company = Company(name="Acme Corporation", email="admin@example.com")
        db.add(company)
        db.flush()
        logger.info("Seeded development company 'Acme Corporation'")

    admin_role = db.scalar(select(Role).where(Role.name == RoleName.ADMIN_HR))
    if admin_role is None:
        raise RuntimeError("ADMIN_HR role not found; run seed_roles_and_permissions first")
    admin = db.scalar(select(User).where(User.email == settings.SEED_ADMIN_EMAIL))
    if admin is None:
        admin = User(
            email=settings.SEED_ADMIN_EMAIL,
            password_hash=hash_password(settings.SEED_ADMIN_PASSWORD),
            role_id=admin_role.id,
            company_id=company.id,
        )
        db.add(admin)
        db.commit()
        logger.warning(
            "Seeded development admin '%s' with password '%s' (dev only)",
            settings.SEED_ADMIN_EMAIL,
            settings.SEED_ADMIN_PASSWORD,
        )


def main() -> None:
    settings = get_settings()
    logging.basicConfig(level=settings.LOG_LEVEL, format="%(levelname)s | %(message)s")

    with SessionLocal() as db:
        seed_roles_and_permissions(db)
        if settings.ENVIRONMENT != "production":
            seed_dev_company_and_admin(db)
        else:
            logger.info("ENVIRONMENT=production; skipping development seed data")

    logger.info("Seeding complete")


if __name__ == "__main__":
    main()
