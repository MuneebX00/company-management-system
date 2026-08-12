import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import ProjectStatus


def _validate_date_window(start_date: date | None, end_date: date | None) -> None:
    if start_date is not None and end_date is not None and end_date < start_date:
        raise ValueError("end_date must not be before start_date")


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    owner_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def _validate_window(self):
        _validate_date_window(self.start_date, self.end_date)
        return self


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    status: ProjectStatus | None = None
    owner_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def _validate_window(self):
        _validate_date_window(self.start_date, self.end_date)
        return self


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    owner_id: uuid.UUID | None
    owner_name: str | None
    created_by: uuid.UUID
    start_date: date | None
    end_date: date | None
    member_count: int
    created_at: datetime
    updated_at: datetime


class ProjectMemberAdd(BaseModel):
    employee_id: uuid.UUID
    role: str | None = Field(default=None, max_length=100)


class ProjectMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str
    role: str | None
