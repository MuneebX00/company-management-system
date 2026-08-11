from app.core.roles import RoleName
from tests.conftest import make_user


def test_login_returns_tokens(client, db_session):
    make_user(db_session, "user@test.com", role_name=RoleName.EMPLOYEE)

    response = client.post(
        "/api/v1/auth/login", data={"username": "user@test.com", "password": "Password123!"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["refresh_token"]


def test_login_normalizes_email_case(client, db_session):
    make_user(db_session, "user@test.com", role_name=RoleName.EMPLOYEE)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "USER@TEST.COM", "password": "Password123!"},
    )

    assert response.status_code == 200


def test_login_invalid_password_rejected(client, db_session):
    make_user(db_session, "user@test.com", role_name=RoleName.EMPLOYEE)

    response = client.post(
        "/api/v1/auth/login", data={"username": "user@test.com", "password": "WrongPass1!"}
    )

    assert response.status_code == 401


def test_login_unknown_email_rejected(client, db_session):
    response = client.post(
        "/api/v1/auth/login", data={"username": "nobody@test.com", "password": "Password123!"}
    )

    assert response.status_code == 401


def test_login_inactive_account_forbidden(client, db_session):
    make_user(
        db_session,
        "inactive@test.com",
        role_name=RoleName.EMPLOYEE,
        is_active=False,
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "inactive@test.com", "password": "Password123!"},
    )

    assert response.status_code == 403


def test_me_returns_profile(client, db_session):
    make_user(db_session, "user@test.com", role_name=RoleName.EMPLOYEE)
    login_response = client.post(
        "/api/v1/auth/login", data={"username": "user@test.com", "password": "Password123!"}
    )

    access_token = login_response.json()["access_token"]
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "user@test.com"
    assert body["role"] == "EMPLOYEE"
    assert body["company_name"] == "Acme Corporation"


def test_me_requires_authentication(client, db_session):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_rejects_garbage_token(client, db_session):
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})

    assert response.status_code == 401
