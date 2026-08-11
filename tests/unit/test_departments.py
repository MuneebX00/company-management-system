import uuid

from sqlalchemy import select

from app.core.roles import RoleName
from app.models import Department, Employee
from tests.conftest import auth_header, login, make_company, make_user


def _login_headers(client, email):
    return auth_header(login(client, email))


def _create_department(client, admin_email, name="Engineering"):
    response = client.post(
        "/api/v1/departments",
        json={"name": name, "description": "Builds things"},
        headers=_login_headers(client, admin_email),
    )
    assert response.status_code == 201
    return response.json()


def test_empty_department_list(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.get("/api/v1/departments", headers=_login_headers(client, admin.email))

    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_admin_creates_department(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)

    response = client.post(
        "/api/v1/departments",
        json={"name": "Engineering", "description": "Builds things"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Engineering"
    assert response.json()["is_active"] is True


def test_duplicate_department_name_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    _create_department(client, admin.email)

    response = client.post(
        "/api/v1/departments",
        json={"name": "Engineering"},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 409


def test_employer_can_view_departments(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    department = _create_department(client, admin.email)
    employer = make_user(db_session, "mgr@test.com", role_name=RoleName.EMPLOYER)

    response = client.get("/api/v1/departments", headers=_login_headers(client, employer.email))

    assert response.status_code == 200
    assert response.json()["total"] == 1
    assert response.json()["items"][0]["id"] == department["id"]


def test_employee_cannot_view_departments(client, db_session):
    employee = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)

    response = client.get("/api/v1/departments", headers=_login_headers(client, employee.email))

    assert response.status_code == 403


def test_cross_company_department_returns_404(client, db_session):
    admin_a = make_user(
        db_session,
        "admin_a@test.com",
        role_name=RoleName.ADMIN_HR,
        company=make_company(db_session, "Company A"),
    )
    company_b = make_company(db_session, "Company B")
    other = db_session.scalar(select(Department).where(Department.company_id == company_b.id))
    if other is None:
        other = Department(company_id=company_b.id, name="Other Dept")
        db_session.add(other)
        db_session.commit()

    response = client.get(
        f"/api/v1/departments/{other.id}", headers=_login_headers(client, admin_a.email)
    )

    assert response.status_code == 404


def test_admin_updates_department(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    department = _create_department(client, admin.email)

    response = client.patch(
        f"/api/v1/departments/{department['id']}",
        json={"name": "Product Engineering", "is_active": False},
        headers=_login_headers(client, admin.email),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Product Engineering"
    assert response.json()["is_active"] is False


def test_delete_empty_department_succeeds(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    department = _create_department(client, admin.email)

    response = client.delete(
        f"/api/v1/departments/{department['id']}", headers=_login_headers(client, admin.email)
    )

    assert response.status_code == 204
    assert (
        client.get(
            f"/api/v1/departments/{department['id']}", headers=_login_headers(client, admin.email)
        ).status_code
        == 404
    )


def test_delete_department_with_employees_returns_409(client, db_session):
    admin = make_user(db_session, "admin@test.com", role_name=RoleName.ADMIN_HR)
    department = _create_department(client, admin.email)
    employee_user = make_user(db_session, "emp@test.com", role_name=RoleName.EMPLOYEE)
    db_session.add(
        Employee(
            company_id=admin.company_id,
            department_id=uuid.UUID(department["id"]),
            user_id=employee_user.id,
            employee_number="E001",
            first_name="Jane",
            last_name="Doe",
        )
    )
    db_session.commit()

    response = client.delete(
        f"/api/v1/departments/{department['id']}", headers=_login_headers(client, admin.email)
    )

    assert response.status_code == 409
