from app.core.roles import RoleName
from tests.conftest import auth_header, login, make_company, make_user


def _login_headers(client, email):
    return auth_header(login(client, email))


def test_admin_lists_users_in_own_company(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    make_user(db_session, "emp1@test.com", role_name=RoleName.EMPLOYEE)
    make_user(db_session, "emp2@test.com", role_name=RoleName.EMPLOYEE)

    response = client.get("/api/v1/users", headers=_login_headers(client, admin.email))

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    assert {item["email"] for item in body["items"]} == {
        "admin@test.com",
        "emp1@test.com",
        "emp2@test.com",
    }


def test_admin_gets_user_in_own_company(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employee = make_user(db_session, "emp1@test.com", role_name=RoleName.EMPLOYEE)

    response = client.get(
        f"/api/v1/users/{employee.id}", headers=_login_headers(client, admin.email)
    )

    assert response.status_code == 200
    assert response.json()["email"] == "emp1@test.com"


def test_employee_cannot_list_users(client, db_session):
    employee = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)

    response = client.get("/api/v1/users", headers=_login_headers(client, employee.email))

    assert response.status_code == 403


def test_employer_cannot_list_users(client, db_session):
    employer = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)

    response = client.get("/api/v1/users", headers=_login_headers(client, employer.email))

    assert response.status_code == 403


def test_cross_company_access_prevented(client, db_session):
    admin_a = make_user(
        db_session,
        "admin_a@test.com",
        role_name=RoleName.ADMIN_HR,
        company=make_company(db_session, "Company A"),
    )
    admin_b = make_user(
        db_session,
        "admin_b@test.com",
        role_name=RoleName.ADMIN_HR,
        company=make_company(db_session, "Company B"),
    )

    response = client.get(
        f"/api/v1/users/{admin_b.id}", headers=_login_headers(client, admin_a.email)
    )

    assert response.status_code == 404


def test_get_missing_user_returns_404(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.get(
        f"/api/v1/users/{'00000000-0000-0000-0000-000000000000'}",
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 404
