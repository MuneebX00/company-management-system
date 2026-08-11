from app.core.roles import RoleName
from tests.conftest import make_user


def test_refresh_rotates_refresh_token(client, db_session):
    make_user(db_session, "user@test.com", role_name=RoleName.EMPLOYEE)
    login_body = client.post(
        "/api/v1/auth/login", data={"username": "user@test.com", "password": "Password123!"}
    ).json()
    old_refresh = login_body["refresh_token"]

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"] != old_refresh


def test_refresh_rejects_invalid_token(client, db_session):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})

    assert response.status_code == 401


def test_refresh_rejects_replayed_rotated_token(client, db_session):
    make_user(db_session, "user@test.com", role_name=RoleName.EMPLOYEE)
    login_body = client.post(
        "/api/v1/auth/login", data={"username": "user@test.com", "password": "Password123!"}
    ).json()
    old_refresh = login_body["refresh_token"]

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    replay = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

    assert first.status_code == 200
    assert replay.status_code == 401


def test_logout_revokes_refresh_token(client, db_session):
    make_user(db_session, "user@test.com", role_name=RoleName.EMPLOYEE)
    login_body = client.post(
        "/api/v1/auth/login", data={"username": "user@test.com", "password": "Password123!"}
    ).json()
    access = login_body["access_token"]
    refresh = login_body["refresh_token"]

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert logout_response.status_code == 204

    refresh_response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert refresh_response.status_code == 401
