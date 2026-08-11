import uuid

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


def _make_leave_type(client, admin_email, name="Annual"):
    response = client.post(
        "/api/v1/leave/types",
        json={"name": name, "days_per_year": 15, "description": "Yearly leave"},
        headers=_login_headers(client, admin_email),
    )
    assert response.status_code == 201
    return response.json()


def _make_request(client, emp_user, leave_type_id, start="2026-08-01", end="2026-08-03"):
    return client.post(
        "/api/v1/leave/requests",
        json={
            "leave_type_id": str(leave_type_id),
            "start_date": start,
            "end_date": end,
            "reason": "Family time",
        },
        headers=_login_headers(client, emp_user.email),
    )


def test_admin_creates_leave_type(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.post(
        "/api/v1/leave/types",
        json={"name": "Annual", "days_per_year": 15},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 201
    assert response.json()["days_per_year"] == 15
    assert response.json()["is_active"] is True


def test_duplicate_leave_type_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    _make_leave_type(client, admin.email)

    response = client.post(
        "/api/v1/leave/types",
        json={"name": "Annual", "days_per_year": 15},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 409


def test_employee_cannot_create_leave_type(client, db_session):
    emp_user, _ = _make_employee(
        db_session,
        "emp@test.com",
        make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR),
    )

    response = client.post(
        "/api/v1/leave/types",
        json={"name": "Annual", "days_per_year": 15},
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 403


def test_employee_creates_leave_request(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)

    response = _make_request(client, emp_user, leave_type["id"])

    assert response.status_code == 201
    body = response.json()
    assert body["days"] == 3
    assert body["status"] == "PENDING"
    assert body["leave_type_name"] == "Annual"
    assert body["employee_name"] == "Jane Doe"


def test_overlapping_leave_request_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    headers = _login_headers(client, emp_user.email)
    assert _make_request(client, emp_user, leave_type["id"]).status_code == 201

    response = client.post(
        "/api/v1/leave/requests",
        json={
            "leave_type_id": str(leave_type["id"]),
            "start_date": "2026-08-03",
            "end_date": "2026-08-05",
            "reason": "Trip",
        },
        headers=headers,
    )

    assert response.status_code == 409


def test_adjacent_leave_requests_allowed(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    headers = _login_headers(client, emp_user.email)
    assert _make_request(client, emp_user, leave_type["id"]).status_code == 201

    response = client.post(
        "/api/v1/leave/requests",
        json={
            "leave_type_id": str(leave_type["id"]),
            "start_date": "2026-08-04",
            "end_date": "2026-08-05",
            "reason": "More time",
        },
        headers=headers,
    )

    assert response.status_code == 201


def test_invalid_date_window_returns_422(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)

    response = _make_request(
        client, emp_user, leave_type["id"], start="2026-08-05", end="2026-08-01"
    )

    assert response.status_code == 422


def test_inactive_leave_type_returns_400(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email, name="Sick")
    client.patch(
        f"/api/v1/leave/types/{leave_type['id']}",
        json={"is_active": False},
        headers=_login_headers(client, admin.email),
    )

    response = _make_request(client, emp_user, leave_type["id"])

    assert response.status_code == 400


def test_admin_approves_leave_request(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    request = _make_request(client, emp_user, leave_type["id"]).json()

    response = client.post(
        f"/api/v1/leave/requests/{request['id']}/approve",
        json={"note": "Approved"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "APPROVED"
    assert body["decision_note"] == "Approved"
    assert body["reviewed_at"] is not None


def test_approve_non_pending_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    request = _make_request(client, emp_user, leave_type["id"]).json()
    admin_headers = _login_headers(client, admin.email)
    client.post(f"/api/v1/leave/requests/{request['id']}/approve", headers=admin_headers)

    response = client.post(f"/api/v1/leave/requests/{request['id']}/approve", headers=admin_headers)

    assert response.status_code == 409


def test_employer_approves_team_member_leave(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    team_user, team_emp = _make_employee(db_session, "team@test.com", admin)
    mgr_user, _ = _make_employer(db_session, "mgr@test.com", admin, team=[(team_user, team_emp)])
    leave_type = _make_leave_type(client, admin.email)
    request = _make_request(client, team_user, leave_type["id"]).json()

    response = client.post(
        f"/api/v1/leave/requests/{request['id']}/approve",
        headers=_login_headers(client, mgr_user.email),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"


def test_employer_cannot_approve_other_team_leave(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    team_user, team_emp = _make_employee(db_session, "team@test.com", admin)
    other_user, _ = _make_employee(db_session, "other@test.com", admin)
    mgr_user, _ = _make_employer(db_session, "mgr@test.com", admin, team=[(team_user, team_emp)])
    leave_type = _make_leave_type(client, admin.email)
    other_request = _make_request(client, other_user, leave_type["id"]).json()

    response = client.post(
        f"/api/v1/leave/requests/{other_request['id']}/approve",
        headers=_login_headers(client, mgr_user.email),
    )

    assert response.status_code == 404


def test_employee_cannot_approve_leave(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    request = _make_request(client, emp_user, leave_type["id"]).json()

    response = client.post(
        f"/api/v1/leave/requests/{request['id']}/approve",
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 403


def test_admin_rejects_leave_request(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    request = _make_request(client, emp_user, leave_type["id"]).json()

    response = client.post(
        f"/api/v1/leave/requests/{request['id']}/reject",
        json={"note": "Not enough coverage"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"


def test_employee_cancels_own_pending_request(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    request = _make_request(client, emp_user, leave_type["id"]).json()

    response = client.post(
        f"/api/v1/leave/requests/{request['id']}/cancel",
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_cancel_approved_request_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    request = _make_request(client, emp_user, leave_type["id"]).json()
    client.post(
        f"/api/v1/leave/requests/{request['id']}/approve",
        headers=_login_headers(client, admin.email),
    )

    response = client.post(
        f"/api/v1/leave/requests/{request['id']}/cancel",
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 409


def test_employee_updates_own_pending_request(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    request = _make_request(client, emp_user, leave_type["id"]).json()

    response = client.patch(
        f"/api/v1/leave/requests/{request['id']}",
        json={"start_date": "2026-09-01", "end_date": "2026-09-02"},
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 200
    assert response.json()["days"] == 2
    assert response.json()["start_date"] == "2026-09-01"


def test_employee_cannot_update_others_request(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1_user, _ = _make_employee(db_session, "emp1@test.com", admin)
    emp2_user, _ = _make_employee(db_session, "emp2@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    other_request = _make_request(client, emp2_user, leave_type["id"]).json()

    response = client.patch(
        f"/api/v1/leave/requests/{other_request['id']}",
        json={"reason": "Hacked"},
        headers=_login_headers(client, emp1_user.email),
    )

    assert response.status_code == 404


def test_employee_sees_only_own_requests(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1_user, _ = _make_employee(db_session, "emp1@test.com", admin)
    emp2_user, _ = _make_employee(db_session, "emp2@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    _make_request(client, emp1_user, leave_type["id"])
    _make_request(client, emp2_user, leave_type["id"])

    response = client.get("/api/v1/leave/requests", headers=_login_headers(client, emp1_user.email))

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_admin_sees_all_requests(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp1_user, _ = _make_employee(db_session, "emp1@test.com", admin)
    emp2_user, _ = _make_employee(db_session, "emp2@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    _make_request(client, emp1_user, leave_type["id"])
    _make_request(client, emp2_user, leave_type["id"])

    response = client.get("/api/v1/leave/requests", headers=_login_headers(client, admin.email))

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_employer_sees_only_team_requests(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    team_user, team_emp = _make_employee(db_session, "team@test.com", admin)
    other_user, _ = _make_employee(db_session, "other@test.com", admin)
    mgr_user, _ = _make_employer(db_session, "mgr@test.com", admin, team=[(team_user, team_emp)])
    leave_type = _make_leave_type(client, admin.email)
    _make_request(client, team_user, leave_type["id"])
    _make_request(client, other_user, leave_type["id"])

    response = client.get("/api/v1/leave/requests", headers=_login_headers(client, mgr_user.email))

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_employee_can_list_leave_types(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    _make_leave_type(client, admin.email)

    response = client.get("/api/v1/leave/types", headers=_login_headers(client, emp_user.email))

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_delete_leave_type_with_requests_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    leave_type = _make_leave_type(client, admin.email)
    _make_request(client, emp_user, leave_type["id"])

    response = client.delete(
        f"/api/v1/leave/types/{leave_type['id']}",
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 409


def test_cross_company_leave_type_returns_404(client, db_session):
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
    foreign_type = _make_leave_type(client, admin_b.email)

    response = client.get(
        f"/api/v1/leave/types/{foreign_type['id']}",
        headers=_login_headers(client, admin_a.email),
    )

    assert response.status_code == 404


def test_cross_company_request_returns_404(client, db_session):
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
    leave_type_b = _make_leave_type(client, admin_b.email)
    request_b = _make_request(client, emp_b_user, leave_type_b["id"]).json()

    response = client.get(
        f"/api/v1/leave/requests/{request_b['id']}",
        headers=_login_headers(client, admin_a.email),
    )

    assert response.status_code == 404
