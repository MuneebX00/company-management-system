import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    project_id: uuid.UUID
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    assigned_to: uuid.UUID | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: date | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assigned_to: uuid.UUID | None = None
    due_date: date | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    project_id: uuid.UUID
    project_name: str
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    assigned_to: uuid.UUID | None
    assignee_name: str | None
    assigned_by: uuid.UUID | None
    created_by: uuid.UUID
    due_date: date | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
