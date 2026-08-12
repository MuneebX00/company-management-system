import uuid

from app.core.enums import EmploymentStatus
from app.core.roles import RoleName
from app.models import Employee, Employer
from tests.conftest import auth_header, login, make_company, make_user


def _login_headers(client, email):
    return auth_header(login(client, email))


def _make_employee(db, email, admin, employer_id=None):
    user = make_user(db, email, role_name=RoleName.EMPLOYEE, company=admin.company)
    employee = Employee(
        company_id=admin.company_id,
        user_id=user.id,
        employee_number=f"E{uuid.uuid4().hex[:6]}",
        first_name="Jane",
        last_name="Doe",
        employment_status=EmploymentStatus.ACTIVE,
        employer_id=employer_id,
    )
    db.add(employee)
    db.commit()
    return user, employee


def _make_employer(db, email, admin):
    user = make_user(db, email, role_name=RoleName.EMPLOYER, company=admin.company)
    employer = Employer(
        company_id=admin.company_id,
        user_id=user.id,
        first_name="Grace",
        last_name="Hopper",
    )
    db.add(employer)
    db.commit()
    return user, employer


def _make_project(client, email, name="Website Redesign", **overrides):
    payload = {"name": name, **overrides}
    return client.post("/api/v1/projects", json=payload, headers=_login_headers(client, email))


def _make_task(client, email, project_id, employee_id=None, title="Design landing page"):
    payload = {"project_id": str(project_id), "title": title}
    if employee_id is not None:
        payload["assigned_to"] = str(employee_id)
    return client.post("/api/v1/tasks", json=payload, headers=_login_headers(client, email))


def test_admin_creates_project(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = _make_project(client, admin.email)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "NOT_STARTED"
    assert body["member_count"] == 0
    assert body["owner_name"] is None


def test_duplicate_project_name_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    _make_project(client, admin.email)

    response = _make_project(client, admin.email)

    assert response.status_code == 409


def test_employee_cannot_create_project(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)

    response = _make_project(client, emp_user.email)

    assert response.status_code == 403


def test_employer_creates_and_manages_own_project(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, employer = _make_employer(db_session, "mgr@test.com", admin)

    create = _make_project(
        client, emp_user.email, owner_id=str(employer.id), start_date="2026-08-01"
    )
    assert create.status_code == 201
    project = create.json()
    assert project["owner_id"] == str(employer.id)
    assert project["owner_name"] == "Grace Hopper"

    listed = client.get("/api/v1/projects", headers=_login_headers(client, emp_user.email))
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    fetched = client.get(
        f"/api/v1/projects/{project['id']}",
        headers=_login_headers(client, emp_user.email),
    )
    assert fetched.status_code == 200


def test_employer_cannot_view_admin_owned_project(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    mgr_user, _ = _make_employer(db_session, "mgr@test.com", admin)
    project = _make_project(client, admin.email).json()

    response = client.get(
        f"/api/v1/projects/{project['id']}",
        headers=_login_headers(client, mgr_user.email),
    )

    assert response.status_code == 404


def test_cross_company_project_returns_404(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    other = make_company(db_session, "Globex")
    stranger = make_user(
        db_session, "stranger@test.com", role_name=RoleName.ADMIN_HR, company=other
    )
    project = _make_project(client, admin.email).json()

    response = client.get(
        f"/api/v1/projects/{project['id']}",
        headers=_login_headers(client, stranger.email),
    )

    assert response.status_code == 404


def test_admin_updates_project(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    project = _make_project(client, admin.email).json()

    response = client.patch(
        f"/api/v1/projects/{project['id']}",
        json={"status": "IN_PROGRESS"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


def test_project_delete_removes_tasks(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    project = _make_project(client, admin.email).json()
    task = _make_task(client, admin.email, project["id"]).json()

    deleted = client.delete(
        f"/api/v1/projects/{project['id']}",
        headers=_login_headers(client, admin.email),
    )
    assert deleted.status_code == 204

    gone = client.get(f"/api/v1/tasks/{task['id']}", headers=_login_headers(client, admin.email))
    assert gone.status_code == 404


def test_add_and_list_and_remove_project_members(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, employee = _make_employee(db_session, "emp@test.com", admin)
    project = _make_project(client, admin.email).json()

    added = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"employee_id": str(employee.id), "role": "Developer"},
        headers=_login_headers(client, admin.email),
    )
    assert added.status_code == 201
    assert added.json()["employee_name"] == "Jane Doe"

    duplicate = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"employee_id": str(employee.id)},
        headers=_login_headers(client, admin.email),
    )
    assert duplicate.status_code == 409

    listed = client.get(
        f"/api/v1/projects/{project['id']}/members",
        headers=_login_headers(client, admin.email),
    )
    assert listed.status_code == 200
    assert listed.json()[0]["role"] == "Developer"

    removed = client.delete(
        f"/api/v1/projects/{project['id']}/members/{employee.id}",
        headers=_login_headers(client, admin.email),
    )
    assert removed.status_code == 204


def test_employee_cannot_manage_members(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, employee = _make_employee(db_session, "emp@test.com", admin)
    project = _make_project(client, admin.email).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"employee_id": str(employee.id)},
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 403


def test_add_foreign_company_member_returns_404(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    other = make_company(db_session, "Globex")
    foreign_emp = make_user(
        db_session, "foreign@test.com", role_name=RoleName.EMPLOYEE, company=other
    )
    Employee(
        company_id=other.id,
        user_id=foreign_emp.id,
        employee_number="F1",
        first_name="Sara",
        last_name="Lee",
        employment_status=EmploymentStatus.ACTIVE,
    )
    db_session.commit()
    project = _make_project(client, admin.email).json()

    response = client.post(
        f"/api/v1/projects/{project['id']}/members",
        json={"employee_id": str(foreign_emp.id)},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 404


def test_employer_creates_task_for_team_member(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    mgr_user, employer = _make_employer(db_session, "mgr@test.com", admin)
    emp_user, employee = _make_employee(db_session, "emp@test.com", admin, employer_id=employer.id)
    project = _make_project(client, mgr_user.email, owner_id=str(employer.id)).json()

    response = _make_task(client, mgr_user.email, project["id"], employee_id=employee.id)

    assert response.status_code == 201
    body = response.json()
    assert body["project_name"] == "Website Redesign"
    assert body["assignee_name"] == "Jane Doe"
    assert body["priority"] == "MEDIUM"
    assert body["assigned_by"] == str(employer.id)


def test_employer_cannot_create_task_in_foreign_project(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    mgr_user, _ = _make_employer(db_session, "mgr@test.com", admin)
    project = _make_project(client, admin.email).json()

    response = _make_task(client, mgr_user.email, project["id"])

    assert response.status_code == 404


def test_employer_cannot_assign_outside_team(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    mgr_user, employer = _make_employer(db_session, "mgr@test.com", admin)
    _, other_employee = _make_employee(db_session, "other@test.com", admin)
    project = _make_project(client, mgr_user.email, owner_id=str(employer.id)).json()

    response = _make_task(client, mgr_user.email, project["id"], employee_id=other_employee.id)

    assert response.status_code == 404


def test_employee_sees_only_own_tasks(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, employee = _make_employee(db_session, "emp@test.com", admin)
    other_user, other_employee = _make_employee(db_session, "other@test.com", admin)
    project = _make_project(client, admin.email).json()
    _make_task(client, admin.email, project["id"], employee_id=employee.id)
    _make_task(client, admin.email, project["id"], employee_id=other_employee.id)

    listed = client.get("/api/v1/tasks", headers=_login_headers(client, emp_user.email))

    assert listed.status_code == 200
    assert listed.json()["total"] == 1


def test_employee_updates_own_task_status(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, employee = _make_employee(db_session, "emp@test.com", admin)
    project = _make_project(client, admin.email).json()
    task = _make_task(client, admin.email, project["id"], employee_id=employee.id).json()

    response = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"status": "DONE"},
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 200
    assert response.json()["status"] == "DONE"
    assert response.json()["completed_at"] is not None


def test_employee_cannot_change_own_task_title(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, employee = _make_employee(db_session, "emp@test.com", admin)
    project = _make_project(client, admin.email).json()
    task = _make_task(client, admin.email, project["id"], employee_id=employee.id).json()

    response = client.patch(
        f"/api/v1/tasks/{task['id']}",
        json={"title": "Renamed"},
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 403


def test_employee_cannot_view_unassigned_task(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, _ = _make_employee(db_session, "emp@test.com", admin)
    project = _make_project(client, admin.email).json()
    task = _make_task(client, admin.email, project["id"]).json()

    response = client.get(
        f"/api/v1/tasks/{task['id']}", headers=_login_headers(client, emp_user.email)
    )

    assert response.status_code == 404


def test_assign_task_endpoint(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    mgr_user, employer = _make_employer(db_session, "mgr@test.com", admin)
    _, employee = _make_employee(db_session, "emp@test.com", admin, employer_id=employer.id)
    project = _make_project(client, mgr_user.email, owner_id=str(employer.id)).json()
    task = _make_task(client, mgr_user.email, project["id"]).json()
    assert task["assigned_to"] is None

    response = client.post(
        f"/api/v1/tasks/{task['id']}/assign",
        json={"assigned_to": str(employee.id)},
        headers=_login_headers(client, mgr_user.email),
    )

    assert response.status_code == 200
    assert response.json()["assigned_to"] == str(employee.id)


def test_employee_cannot_assign_tasks(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    emp_user, employee = _make_employee(db_session, "emp@test.com", admin)
    project = _make_project(client, admin.email).json()
    task = _make_task(client, admin.email, project["id"], employee_id=employee.id).json()

    response = client.post(
        f"/api/v1/tasks/{task['id']}/assign",
        json={"assigned_to": str(employee.id)},
        headers=_login_headers(client, emp_user.email),
    )

    assert response.status_code == 403
