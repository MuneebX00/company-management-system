import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.roles import RoleName
from app.core.security import hash_password
from app.main import app
from app.models import Company, Role, User
from app.seed import seed_roles_and_permissions


def _test_database_url() -> str:
    override = os.getenv("TEST_DATABASE_URL")
    if override:
        return override
    base = get_settings().DATABASE_URL
    return base.rsplit("/", 1)[0] + "/company_management_test"


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(_test_database_url())
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_roles_and_permissions(session)
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(
        bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False
    )
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def make_company(db: Session, name: str = "Acme Corporation") -> Company:
    company = db.scalar(select(Company).where(Company.name == name))
    if company is None:
        company = Company(name=name, email=f"{name.lower().replace(' ', '')}@example.com")
        db.add(company)
        db.commit()
    return company


def make_user(
    db: Session,
    email: str,
    password: str = "Password123!",
    role_name: RoleName = RoleName.EMPLOYEE,
    company: Company | None = None,
    is_active: bool = True,
) -> User:
    company = company or make_company(db)
    role = db.scalar(select(Role).where(Role.name == role_name))
    user = User(
        email=email,
        password_hash=hash_password(password),
        role_id=role.id,
        company_id=company.id,
        is_active=is_active,
    )
    db.add(user)
    db.commit()
    return user


def login(client: TestClient, email: str, password: str = "Password123!"):
    return client.post("/api/v1/auth/login", data={"username": email, "password": password})


def auth_header(response) -> dict[str, str]:
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
