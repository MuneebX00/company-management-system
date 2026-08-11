import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class EmployerCreate(BaseModel):
    user_id: uuid.UUID
    department_id: uuid.UUID | None = None
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)
    hire_date: date | None = None


class EmployerUpdate(BaseModel):
    department_id: uuid.UUID | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)
    hire_date: date | None = None


class EmployerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    department_id: uuid.UUID | None
    department_name: str | None
    user_id: uuid.UUID
    email: str
    first_name: str
    last_name: str
    job_title: str | None
    hire_date: date | None
    created_at: datetime
