import uuid
from datetime import date

from app.core.enums import EmploymentStatus
from app.core.roles import RoleName
from app.models import Employee, Employer
from tests.conftest import auth_header, login, make_company, make_user


def _login_headers(client, email):
    return auth_header(login(client, email))


def _make_employee(db, email, admin):
    user = make_user(db, email, role_name=RoleName.EMPLOYEE, company=admin.company)
    employee = Employee(
        company_id=admin.company_id,
        user_id=user.id,
        employee_number=f"E{uuid.uuid4().hex[:6]}",
        first_name="Jane",
        last_name="Doe",
        employment_status=EmploymentStatus.ACTIVE,
    )
    db.add(employee)
    db.commit()
    return user, employee


def _make_employer(db, email, admin, team=None):
    user = make_user(db, email, role_name=RoleName.EMPLOYER, company=admin.company)
    employer = Employer(
        company_id=admin.company_id,
        user_id=user.id,
        first_name="Grace",
        last_name="Hopper",
    )
    db.add(employer)
    db.commit()
    for _emp_user, emp in team or []:
        emp.employer_id = employer.id
    db.commit()
    return user, employer


def test_employee_checks_in(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)

    response = client.post(
        "/api/v1/attendance/check-in", headers=_login_headers(client, emp_user.email)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "PRESENT"
    assert body["work_date"] == str(date.today())
    assert body["check_in_at"] is not None


def test_double_check_in_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    headers = _login_headers(client, emp_user.email)
    assert client.post("/api/v1/attendance/check-in", headers=headers).status_code == 201

    response = client.post("/api/v1/attendance/check-in", headers=headers)

    assert response.status_code == 409


def test_check_out_without_check_in_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)

    response = client.post(
        "/api/v1/attendance/check-out", headers=_login_headers(client, emp_user.email)
    )

    assert response.status_code == 409


def test_check_out_computes_hours(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    headers = _login_headers(client, emp_user.email)
    assert client.post("/api/v1/attendance/check-in", headers=headers).status_code == 201

    response = client.post("/api/v1/attendance/check-out", headers=headers)

    assert response.status_code == 201
    assert response.json()["check_out_at"] is not None
    assert float(response.json()["hours_worked"]) >= 0


def test_double_check_out_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    headers = _login_headers(client, emp_user.email)
    client.post("/api/v1/attendance/check-in", headers=headers)
    assert client.post("/api/v1/attendance/check-out", headers=headers).status_code == 201

    response = client.post("/api/v1/attendance/check-out", headers=headers)

    assert response.status_code == 409


def test_check_in_requires_employee_profile(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.post(
        "/api/v1/attendance/check-in", headers=_login_headers(client, admin.email)
    )

    assert response.status_code == 404


def test_employer_cannot_check_in(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    _make_employee(db_session, "emp@test.com", admin)
    employer = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)

    response = client.post(
        "/api/v1/attendance/check-in", headers=_login_headers(client, employer.email)
    )

    assert response.status_code == 403


def test_employee_lists_only_own_attendance(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1_user, _ = _make_employee(db_session, "emp1@test.com", admin)
    emp2_user, _ = _make_employee(db_session, "emp2@test.com", admin)
    client.post("/api/v1/attendance/check-in", headers=_login_headers(client, emp1_user.email))
    client.post("/api/v1/attendance/check-in", headers=_login_headers(client, emp2_user.email))

    response = client.get("/api/v1/attendance", headers=_login_headers(client, emp1_user.email))

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_employee_cannot_view_other_attendance(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1_user, _ = _make_employee(db_session, "emp1@test.com", admin)
    emp2_user, _ = _make_employee(db_session, "emp2@test.com", admin)
    client.post("/api/v1/attendance/check-in", headers=_login_headers(client, emp1_user.email))
    record2 = client.post(
        "/api/v1/attendance/check-in", headers=_login_headers(client, emp2_user.email)
    ).json()

    response = client.get(
        f"/api/v1/attendance/{record2['id']}", headers=_login_headers(client, emp1_user.email)
    )

    assert response.status_code == 404


def test_employer_sees_only_team_attendance(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    team_user, team_emp = _make_employee(db_session, "team@test.com", admin)
    other_user, _ = _make_employee(db_session, "other@test.com", admin)
    mgr_user, _ = _make_employer(db_session, "mgr@test.com", admin, team=[(team_user, team_emp)])
    client.post("/api/v1/attendance/check-in", headers=_login_headers(client, team_user.email))
    client.post("/api/v1/attendance/check-in", headers=_login_headers(client, other_user.email))

    response = client.get("/api/v1/attendance", headers=_login_headers(client, mgr_user.email))

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_admin_lists_all_attendance(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1_user, _ = _make_employee(db_session, "emp1@test.com", admin)
    emp2_user, _ = _make_employee(db_session, "emp2@test.com", admin)
    client.post("/api/v1/attendance/check-in", headers=_login_headers(client, emp1_user.email))
    client.post("/api/v1/attendance/check-in", headers=_login_headers(client, emp2_user.email))

    response = client.get("/api/v1/attendance", headers=_login_headers(client, admin.email))

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_admin_corrects_attendance(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    record = client.post(
        "/api/v1/attendance/check-in", headers=_login_headers(client, emp_user.email)
    ).json()

    response = client.patch(
        f"/api/v1/attendance/{record['id']}",
        json={"status": "LATE", "notes": "late by 30 minutes"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "LATE"
    assert response.json()["notes"] == "late by 30 minutes"


def test_employee_cannot_correct_attendance(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    record = client.post(
        "/api/v1/attendance/check-in", headers=_login_headers(client, emp_user.email)
    ).json()

    response = client.patch(
        f"/api/v1/attendance/{record['id']}",
        json={"status": "LATE"},
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 403


def test_cross_company_attendance_returns_404(client, db_session):
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
    emp_b_user, _ = _make_employee(db_session, "emp_b@test.com", admin_b)
    record_b = client.post(
        "/api/v1/attendance/check-in", headers=_login_headers(client, emp_b_user.email)
    ).json()

    response = client.get(
        f"/api/v1/attendance/{record_b['id']}", headers=_login_headers(client, admin_a.email)
    )

    assert response.status_code == 404


def test_date_range_filter(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    client.post("/api/v1/attendance/check-in", headers=_login_headers(client, emp_user.email))

    response = client.get(
        "/api/v1/attendance?from_date=2000-01-01&to_date=2000-01-02",
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0
