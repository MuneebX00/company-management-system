from app.core.roles import RoleName
from tests.conftest import auth_header, login, make_user


def _admin_headers(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    return auth_header(login(client, admin.email))


def test_register_creates_user_in_admin_company(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "emp1@example.com", "password": "Password123!", "role_code": "EMPLOYEE"},
        headers=auth_header(login(client, admin.email)),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "emp1@example.com"
    assert body["role"] == "EMPLOYEE"
    assert body["company_id"] == str(admin.company_id)
    assert "password" not in body


def test_register_requires_user_create_permission(client, db_session):
    employer = make_user(db_session, "employer@test.com", role_name=RoleName.EMPLOYER)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "emp1@example.com", "password": "Password123!", "role_code": "EMPLOYEE"},
        headers=auth_header(login(client, employer.email)),
    )

    assert response.status_code == 403


def test_register_duplicate_email_conflicts(client, db_session):
    headers = _admin_headers(client, db_session)
    payload = {"email": "dup@example.com", "password": "Password123!", "role_code": "EMPLOYEE"}

    first = client.post("/api/v1/auth/register", json=payload, headers=headers)
    second = client.post("/api/v1/auth/register", json=payload, headers=headers)

    assert first.status_code == 201
    assert second.status_code == 409


def test_register_requires_authentication(client, db_session):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "emp1@example.com", "password": "Password123!", "role_code": "EMPLOYEE"},
    )

    assert response.status_code == 401


def test_register_requires_min_password_length(client, db_session):
    headers = _admin_headers(client, db_session)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "emp1@example.com", "password": "short", "role_code": "EMPLOYEE"},
        headers=headers,
    )

    assert response.status_code == 422


def test_register_unknown_role_rejected(client, db_session):
    headers = _admin_headers(client, db_session)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "emp1@example.com", "password": "Password123!", "role_code": "SUPERUSER"},
        headers=headers,
    )

    assert response.status_code == 422
