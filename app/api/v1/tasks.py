import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.enums import TaskStatus
from app.core.roles import RoleName
from app.dependencies.database import DbSession
from app.dependencies.rbac import require_permission
from app.models import Task, User
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.org import get_scoped_employee
from app.services.projects import get_scoped_project, get_scoped_task, task_scope_expr
from app.utils.pagination import Page, PageParams, get_page

router = APIRouter()

_EMPLOYEE_EDITABLE_FIELDS = {"status", "description"}


class TaskAssign(BaseModel):
    assigned_to: uuid.UUID = Field(...)


def _validate_assignee(db: DbSession, current_user: User, employee_id: uuid.UUID | None) -> None:
    if employee_id is not None:
        get_scoped_employee(db, current_user, employee_id)


def _sync_completed_at(task: Task, updates: dict) -> None:
    if "status" in updates:
        if updates["status"] == TaskStatus.DONE:
            task.completed_at = datetime.now(UTC)
        else:
            task.completed_at = None


@router.get(
    "",
    response_model=Page[TaskResponse],
    summary="List tasks within the caller's scope",
)
def list_tasks(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    current_user: Annotated[User, Depends(require_permission("task.view"))],
) -> Page[TaskResponse]:
    statement = select(Task).where(task_scope_expr(current_user)).order_by(Task.created_at.desc())
    items, total = get_page(db, statement, params.page, params.page_size)
    return Page[TaskResponse](
        items=[TaskResponse.model_validate(item) for item in items],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
def create_task(
    payload: TaskCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("task.create"))],
) -> TaskResponse:
    project = get_scoped_project(db, current_user, payload.project_id)
    _validate_assignee(db, current_user, payload.assigned_to)
    assigner = current_user.employer_profile
    task = Task(
        company_id=current_user.company_id,
        project_id=project.id,
        created_by=current_user.id,
        assigned_by=assigner.id if assigner else None,
        title=payload.title,
        description=payload.description,
        assigned_to=payload.assigned_to,
        priority=payload.priority,
        due_date=payload.due_date,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task)


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a task within the caller's scope",
)
def get_task(
    task_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("task.view"))],
) -> TaskResponse:
    return TaskResponse.model_validate(get_scoped_task(db, current_user, task_id))


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="Employees may update only the status and description of their own tasks.",
)
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("task.update"))],
) -> TaskResponse:
    task = get_scoped_task(db, current_user, task_id)
    updates = payload.model_dump(exclude_unset=True)

    if current_user.role.name == RoleName.EMPLOYEE:
        disallowed = set(updates) - _EMPLOYEE_EDITABLE_FIELDS
        if disallowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employees may only update status and description",
            )

    if updates.get("assigned_to") is not None:
        _validate_assignee(db, current_user, updates["assigned_to"])
    _sync_completed_at(task, updates)
    for field, value in updates.items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task)


@router.post(
    "/{task_id}/assign",
    response_model=TaskResponse,
    summary="Assign a task to an employee",
)
def assign_task(
    task_id: uuid.UUID,
    payload: TaskAssign,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("task.assign"))],
) -> TaskResponse:
    task = get_scoped_task(db, current_user, task_id)
    _validate_assignee(db, current_user, payload.assigned_to)
    assigner = current_user.employer_profile
    task.assigned_to = payload.assigned_to
    task.assigned_by = assigner.id if assigner else None
    db.commit()
    db.refresh(task)
    return TaskResponse.model_validate(task)
