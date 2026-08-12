import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies.database import DbSession
from app.dependencies.rbac import require_permission
from app.models import Project, User
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberAdd,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.org import get_scoped_employee, get_scoped_employer
from app.services.projects import (
    add_project_member,
    get_scoped_project,
    project_scope_expr,
    remove_project_member,
)
from app.utils.pagination import Page, PageParams, get_page

router = APIRouter()


@router.get(
    "",
    response_model=Page[ProjectResponse],
    summary="List projects within the caller's scope",
)
def list_projects(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    current_user: Annotated[User, Depends(require_permission("project.view"))],
) -> Page[ProjectResponse]:
    statement = select(Project).where(project_scope_expr(current_user)).order_by(Project.name)
    items, total = get_page(db, statement, params.page, params.page_size)
    return Page[ProjectResponse](
        items=[ProjectResponse.model_validate(item) for item in items],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    description="Admins and employers create projects; employers own their own projects.",
)
def create_project(
    payload: ProjectCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("project.create"))],
) -> ProjectResponse:
    if payload.owner_id is not None:
        get_scoped_employer(db, current_user, payload.owner_id)
    project = Project(
        company_id=current_user.company_id,
        created_by=current_user.id,
        **payload.model_dump(),
    )
    db.add(project)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Project name already exists"
        ) from exc
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project within the caller's scope",
)
def get_project(
    project_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("project.view"))],
) -> ProjectResponse:
    return ProjectResponse.model_validate(get_scoped_project(db, current_user, project_id))


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
)
def update_project(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("project.update"))],
) -> ProjectResponse:
    project = get_scoped_project(db, current_user, project_id)
    updates = payload.model_dump(exclude_unset=True)
    if updates.get("owner_id") is not None:
        get_scoped_employer(db, current_user, updates["owner_id"])
    for field, value in updates.items():
        setattr(project, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Project name already exists"
        ) from exc
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Deletes the project and its tasks and member links.",
)
def delete_project(
    project_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("project.update"))],
) -> None:
    project = get_scoped_project(db, current_user, project_id)
    db.delete(project)
    db.commit()


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add an employee to a project",
)
def add_member(
    project_id: uuid.UUID,
    payload: ProjectMemberAdd,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("project.member_manage"))],
) -> ProjectMemberResponse:
    project = get_scoped_project(db, current_user, project_id)
    employee = get_scoped_employee(db, current_user, payload.employee_id)
    member = add_project_member(db, current_user, project, employee, payload.role)
    return ProjectMemberResponse.model_validate(member)


@router.get(
    "/{project_id}/members",
    response_model=list[ProjectMemberResponse],
    summary="List members of a project",
)
def list_members(
    project_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("project.view"))],
) -> list[ProjectMemberResponse]:
    project = get_scoped_project(db, current_user, project_id)
    return [ProjectMemberResponse.model_validate(member) for member in project.members]


@router.delete(
    "/{project_id}/members/{employee_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an employee from a project",
)
def remove_member(
    project_id: uuid.UUID,
    employee_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("project.member_manage"))],
) -> None:
    project = get_scoped_project(db, current_user, project_id)
    remove_project_member(db, current_user, project, employee_id)
