import uuid

from app.core.roles import RoleName
from tests.conftest import auth_header, login, make_company, make_user


def _login_headers(client, email):
    return auth_header(login(client, email))


def _create_employee(
    client,
    admin,
    employee_user,
    employee_number="E001",
    department_id=None,
    employer_id=None,
):
    payload = {
        "user_id": str(employee_user.id),
        "employee_number": employee_number,
        "first_name": "Jane",
        "last_name": "Doe",
        "job_title": "Software Engineer",
    }
    if department_id:
        payload["department_id"] = str(department_id)
    if employer_id:
        payload["employer_id"] = str(employer_id)
    return client.post(
        "/api/v1/employees", json=payload, headers=_login_headers(client, admin.email)
    )


def test_admin_creates_employee(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employee_user = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)

    response = _create_employee(client, admin, employee_user)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "emp@test.com"
    assert body["employment_status"] == "ACTIVE"
    assert body["first_name"] == "Jane"
    assert body["last_name"] == "Doe"


def test_duplicate_employee_number_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1 = make_user(db_session, "emp1@test.com", role_name=RoleName.EMPLOYEE)
    emp2 = make_user(db_session, "emp2@test.com", role_name=RoleName.EMPLOYEE)
    assert _create_employee(client, admin, emp1).status_code == 201

    response = _create_employee(client, admin, emp2, employee_number="E001")

    assert response.status_code == 409


def test_employee_requires_employee_role(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employer_user = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)

    response = _create_employee(client, admin, employer_user)

    assert response.status_code == 400


def test_employee_user_must_be_in_same_company(client, db_session):
    admin = make_user(
        db_session,
        "admin@test.com",
        role_name=RoleName.ADMIN_HR,
        company=make_company(db_session, "Company A"),
    )
    foreign_user = make_user(
        db_session,
        "emp_b@test.com",
        role_name=RoleName.EMPLOYEE,
        company=make_company(db_session, "Company B"),
    )

    response = _create_employee(client, admin, foreign_user)

    assert response.status_code == 404


def test_duplicate_employee_profile_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employee_user = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)
    assert _create_employee(client, admin, employee_user).status_code == 201

    response = _create_employee(client, admin, employee_user, employee_number="E002")

    assert response.status_code == 409


def test_admin_sees_all_employees(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1 = make_user(db_session, "emp1@test.com", role_name=RoleName.EMPLOYEE)
    emp2 = make_user(db_session, "emp2@test.com", role_name=RoleName.EMPLOYEE)
    assert _create_employee(client, admin, emp1, "E001").status_code == 201
    assert _create_employee(client, admin, emp2, "E002").status_code == 201

    response = client.get("/api/v1/employees", headers=_login_headers(client, admin.email))

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_employee_sees_only_self(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1 = make_user(db_session, "emp1@test.com", role_name=RoleName.EMPLOYEE)
    emp2 = make_user(db_session, "emp2@test.com", role_name=RoleName.EMPLOYEE)
    assert _create_employee(client, admin, emp1, "E001").status_code == 201
    assert _create_employee(client, admin, emp2, "E002").status_code == 201

    response = client.get("/api/v1/employees", headers=_login_headers(client, emp1.email))

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["employee_number"] == "E001"


def test_employer_sees_only_own_team(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employer_user = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)
    employer = _create_employer_profile(client, db_session, admin, employer_user).json()

    team_member = make_user(db_session, "team@test.com", role_name=RoleName.EMPLOYEE)
    other = make_user(db_session, "other@test.com", role_name=RoleName.EMPLOYEE)
    team_response = _create_employee(
        client, admin, team_member, "E001", employer_id=uuid.UUID(employer["id"])
    )
    assert team_response.status_code == 201
    assert _create_employee(client, admin, other, "E002").status_code == 201

    response = client.get("/api/v1/employees", headers=_login_headers(client, employer_user.email))

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["employee_number"] == "E001"
    assert response.json()["items"][0]["manager_name"] == "Grace Hopper"


def test_employer_cannot_view_other_teams_employee(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employer_user = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)
    _create_employer_profile(client, db_session, admin, employer_user)

    other = make_user(db_session, "other@test.com", role_name=RoleName.EMPLOYEE)
    other_profile = _create_employee(client, admin, other, "E002").json()

    response = client.get(
        f"/api/v1/employees/{other_profile['id']}",
        headers=_login_headers(client, employer_user.email),
    )

    assert response.status_code == 404


def test_employee_gets_own_profile(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employee_user = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)
    assert _create_employee(client, admin, employee_user).status_code == 201

    response = client.get(
        "/api/v1/employees/me", headers=_login_headers(client, employee_user.email)
    )

    assert response.status_code == 200
    assert response.json()["email"] == "emp@test.com"


def test_admin_updates_employee(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employee_user = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)
    employee = _create_employee(client, admin, employee_user).json()

    response = client.patch(
        f"/api/v1/employees/{employee['id']}",
        json={"job_title": "Senior Engineer", "employment_status": "ON_LEAVE"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 200
    assert response.json()["job_title"] == "Senior Engineer"
    assert response.json()["employment_status"] == "ON_LEAVE"


def test_employee_cannot_update_others(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1 = make_user(db_session, "emp1@test.com", role_name=RoleName.EMPLOYEE)
    emp2 = make_user(db_session, "emp2@test.com", role_name=RoleName.EMPLOYEE)
    assert _create_employee(client, admin, emp1, "E001").status_code == 201
    other = _create_employee(client, admin, emp2, "E002").json()

    response = client.patch(
        f"/api/v1/employees/{other['id']}",
        json={"job_title": "Hacked"},
        headers=_login_headers(client, emp1.email),
    )

    assert response.status_code == 403


def test_employer_can_update_team_member(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    employer_user = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)
    employer = _create_employer_profile(client, db_session, admin, employer_user).json()

    team_member = make_user(db_session, "team@test.com", role_name=RoleName.EMPLOYEE)
    member_profile = _create_employee(
        client, admin, team_member, "E001", employer_id=uuid.UUID(employer["id"])
    ).json()

    response = client.patch(
        f"/api/v1/employees/{member_profile['id']}",
        json={"job_title": "Lead Engineer"},
        headers=_login_headers(client, employer_user.email),
    )

    assert response.status_code == 200
    assert response.json()["job_title"] == "Lead Engineer"


def test_update_employee_number_conflict_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1 = make_user(db_session, "emp1@test.com", role_name=RoleName.EMPLOYEE)
    emp2 = make_user(db_session, "emp2@test.com", role_name=RoleName.EMPLOYEE)
    assert _create_employee(client, admin, emp1, "E001").status_code == 201
    emp2_profile = _create_employee(client, admin, emp2, "E002").json()

    response = client.patch(
        f"/api/v1/employees/{emp2_profile['id']}",
        json={"employee_number": "E001"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 409


def test_cross_company_employee_returns_404(client, db_session):
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
    employee_user_b = make_user(
        db_session,
        "emp_b@test.com",
        role_name=RoleName.EMPLOYEE,
        company=admin_b.company,
    )
    foreign_employee = _create_employee(client, admin_b, employee_user_b).json()

    response = client.get(
        f"/api/v1/employees/{foreign_employee['id']}",
        headers=_login_headers(client, admin_a.email),
    )

    assert response.status_code == 404


def _create_employer_profile(client, db_session, admin, employer_user):
    return client.post(
        "/api/v1/employers",
        json={
            "user_id": str(employer_user.id),
            "first_name": "Grace",
            "last_name": "Hopper",
        },
        headers=_login_headers(client, admin.email),
    )
