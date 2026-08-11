from app.core.roles import RoleName
from tests.conftest import auth_header, login, make_company, make_user


def _login_headers(client, email):
    return auth_header(login(client, email))


def _create_department(client, admin_email):
    response = client.post(
        "/api/v1/departments",
        json={"name": "Engineering"},
        headers=_login_headers(client, admin_email),
    )
    assert response.status_code == 201
    return response.json()


def _create_employer(client, db_session, admin, employer_user, department_id=None):
    payload = {
        "user_id": str(employer_user.id),
        "first_name": "Grace",
        "last_name": "Hopper",
        "job_title": "Team Lead",
    }
    if department_id:
        payload["department_id"] = str(department_id)
    return client.post(
        "/api/v1/employers", json=payload, headers=_login_headers(client, admin.email)
    )


def test_admin_creates_employer(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employer_user = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)

    response = _create_employer(client, db_session, admin, employer_user)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "mgr@test.com"
    assert body["first_name"] == "Grace"
    assert body["last_name"] == "Hopper"


def test_employer_requires_employer_role(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employee_user = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)

    response = _create_employer(client, db_session, admin, employee_user)

    assert response.status_code == 400


def test_employer_user_must_be_in_same_company(client, db_session):
    admin = make_user(
        db_session,
        "admin@test.com",
        role_name=RoleName.ADMIN_HR,
        company=make_company(db_session, "Company A"),
    )
    foreign_user = make_user(
        db_session,
        "mgr_b@test.com",
        role_name=RoleName.EMPLOYER,
        company=make_company(db_session, "Company B"),
    )

    response = _create_employer(client, db_session, admin, foreign_user)

    assert response.status_code == 404


def test_duplicate_employer_profile_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employer_user = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)
    assert _create_employer(client, db_session, admin, employer_user).status_code == 201

    response = _create_employer(client, db_session, admin, employer_user)

    assert response.status_code == 409


def test_employer_department_must_be_in_same_company(client, db_session):
    admin = make_user(
        db_session,
        "admin@test.com",
        role_name=RoleName.ADMIN_HR,
        company=make_company(db_session, "Company A"),
    )
    employer_user = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)
    admin2 = make_user(
        db_session,
        "admin_c@test.com",
        role_name=RoleName.ADMIN_HR,
        company=make_company(db_session, "Company C"),
    )
    other_department = _create_department(client, admin2.email)

    response = client.post(
        "/api/v1/employers",
        json={
            "user_id": str(employer_user.id),
            "department_id": other_department["id"],
            "first_name": "Grace",
            "last_name": "Hopper",
        },
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 404


def test_employee_cannot_create_employer(client, db_session):
    employee = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)

    response = client.post(
        "/api/v1/employers",
        json={
            "user_id": str(employee.id),
            "first_name": "Grace",
            "last_name": "Hopper",
        },
        headers=_login_headers(client, employee.email),
    )

    assert response.status_code == 403


def test_employer_can_list_employers(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employer_user = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)
    assert _create_employer(client, db_session, admin, employer_user).status_code == 201

    response = client.get("/api/v1/employers", headers=_login_headers(client, employer_user.email))

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["email"] == "mgr@test.com"


def test_admin_updates_employer(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employer_user = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)
    employer = _create_employer(client, db_session, admin, employer_user).json()

    response = client.patch(
        f"/api/v1/employers/{employer['id']}",
        json={"job_title": "Engineering Director"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 200
    assert response.json()["job_title"] == "Engineering Director"


def test_cross_company_employer_returns_404(client, db_session):
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
    employer_user_b = make_user(
        db_session,
        "mgr_b@test.com",
        role_name=RoleName.EMPLOYER,
        company=admin_b.company,
    )
    foreign_employer = _create_employer(client, db_session, admin_b, employer_user_b).json()

    response = client.get(
        f"/api/v1/employers/{foreign_employer['id']}", headers=_login_headers(client, admin_a.email)
    )

    assert response.status_code == 404
