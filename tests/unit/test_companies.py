import uuid

from app.core.roles import RoleName
from tests.conftest import auth_header, login, make_company, make_user


def _login_headers(client, email):
    return auth_header(login(client, email))


def test_get_own_company(client, db_session):
    user = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)

    response = client.get("/api/v1/companies", headers=_login_headers(client, user.email))

    assert response.status_code == 200
    assert response.json()["name"] == "Acme Corporation"


def test_admin_gets_company_by_id(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.get(
        f"/api/v1/companies/{admin.company_id}", headers=_login_headers(client, admin.email)
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(admin.company_id)


def test_cross_company_company_lookup_returns_404(client, db_session):
    admin_a = make_user(
        db_session,
        "admin_a@test.com",
        role_name=RoleName.ADMIN_HR,
        company=make_company(db_session, "Company A"),
    )
    company_b = make_company(db_session, "Company B")

    response = client.get(
        f"/api/v1/companies/{company_b.id}", headers=_login_headers(client, admin_a.email)
    )

    assert response.status_code == 404


def test_missing_company_returns_404(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.get(
        f"/api/v1/companies/{uuid.UUID(int=0)}", headers=_login_headers(client, admin.email)
    )

    assert response.status_code == 404


def test_admin_creates_company(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.post(
        "/api/v1/companies",
        json={"name": "Globex", "email": "globex@example.com"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Globex"
    assert response.json()["email"] == "globex@example.com"


def test_duplicate_company_name_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.post(
        "/api/v1/companies",
        json={"name": "Acme Corporation", "email": "acme@example.com"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 409


def test_employee_cannot_create_company(client, db_session):
    employee = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)

    response = client.post(
        "/api/v1/companies",
        json={"name": "Globex", "email": "globex@example.com"},
        headers=_login_headers(client, employee.email),
    )

    assert response.status_code == 403


def test_admin_updates_own_company(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.patch(
        f"/api/v1/companies/{admin.company_id}",
        json={"name": "Acme Corp"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Acme Corp"


def test_admin_cannot_update_other_company(client, db_session):
    admin_a = make_user(
        db_session,
        "admin_a@test.com",
        role_name=RoleName.ADMIN_HR,
        company=make_company(db_session, "Company A"),
    )
    company_b = make_company(db_session, "Company B")

    response = client.patch(
        f"/api/v1/companies/{company_b.id}",
        json={"name": "Hacked"},
        headers=_login_headers(client, admin_a.email),
    )

    assert response.status_code == 404
