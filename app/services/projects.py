"""Business rules and tenant scoping for projects, project members, and tasks."""

import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, false, select
from sqlalchemy.orm import Session

from app.core.roles import RoleName
from app.models import Employee, Project, ProjectMember, Task, User


def _not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


def _may_view_project(current_user: User, project: Project) -> bool:
    if current_user.role.name == RoleName.ADMIN_HR:
        return True
    if current_user.role.name == RoleName.EMPLOYER:
        profile = current_user.employer_profile
        return profile is not None and project.owner_id == profile.id
    return False


def _may_view_task(current_user: User, task: Task) -> bool:
    if current_user.role.name == RoleName.ADMIN_HR:
        return True
    if current_user.role.name == RoleName.EMPLOYER:
        profile = current_user.employer_profile
        return profile is not None and task.project.owner_id == profile.id
    employee = current_user.employee_profile
    return employee is not None and task.assigned_to == employee.id


def get_scoped_project(db: Session, current_user: User, project_id: uuid.UUID) -> Project:
    """Fetch a project, enforcing company and role-level scoping."""
    project = db.get(Project, project_id)
    if project is None or project.company_id != current_user.company_id:
        raise _not_found("Project")
    if not _may_view_project(current_user, project):
        raise _not_found("Project")
    return project


def project_scope_expr(current_user: User):
    """SQLAlchemy boolean expression limiting project queries to the caller's scope."""
    if current_user.role.name == RoleName.ADMIN_HR:
        return Project.company_id == current_user.company_id
    if current_user.role.name == RoleName.EMPLOYER:
        profile = current_user.employer_profile
        if profile is None:
            return false()
        return and_(
            Project.company_id == current_user.company_id,
            Project.owner_id == profile.id,
        )
    return false()


def get_scoped_task(db: Session, current_user: User, task_id: uuid.UUID) -> Task:
    """Fetch a task, enforcing company and role-level scoping."""
    task = db.get(Task, task_id)
    if task is None or task.company_id != current_user.company_id:
        raise _not_found("Task")
    if not _may_view_task(current_user, task):
        raise _not_found("Task")
    return task


def task_scope_expr(current_user: User):
    """SQLAlchemy boolean expression limiting task queries to the caller's scope."""
    if current_user.role.name == RoleName.ADMIN_HR:
        return Task.company_id == current_user.company_id
    if current_user.role.name == RoleName.EMPLOYER:
        profile = current_user.employer_profile
        if profile is None:
            return false()
        return and_(
            Task.company_id == current_user.company_id,
            Task.project_id.in_(select(Project.id).where(Project.owner_id == profile.id)),
        )
    employee = current_user.employee_profile
    if employee is None:
        return false()
    return and_(Task.company_id == current_user.company_id, Task.assigned_to == employee.id)


def get_scoped_project_member(
    db: Session, current_user: User, project: Project, employee_id: uuid.UUID
) -> ProjectMember:
    member = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id, ProjectMember.employee_id == employee_id
        )
    )
    if member is None:
        raise _not_found("Project member")
    return member


def add_project_member(
    db: Session, current_user: User, project: Project, employee: Employee, role: str | None
) -> ProjectMember:
    existing = db.scalar(
        select(ProjectMember).where(
            ProjectMember.project_id == project.id, ProjectMember.employee_id == employee.id
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Employee is already a project member"
        )
    member = ProjectMember(project_id=project.id, employee_id=employee.id, role=role)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_project_member(
    db: Session, current_user: User, project: Project, employee_id: uuid.UUID
) -> None:
    member = get_scoped_project_member(db, current_user, project, employee_id)
    db.delete(member)
    db.commit()
