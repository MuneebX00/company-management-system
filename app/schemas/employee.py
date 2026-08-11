import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import EmploymentStatus


class EmployeeCreate(BaseModel):
    user_id: uuid.UUID
    department_id: uuid.UUID | None = None
    employer_id: uuid.UUID | None = None
    employee_number: str = Field(min_length=1, max_length=50)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)
    hire_date: date | None = None
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE
    phone: str | None = Field(default=None, max_length=50)


class EmployeeUpdate(BaseModel):
    department_id: uuid.UUID | None = None
    employer_id: uuid.UUID | None = None
    employee_number: str | None = Field(default=None, min_length=1, max_length=50)
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)
    employment_status: EmploymentStatus | None = None
    phone: str | None = Field(default=None, max_length=50)


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    department_id: uuid.UUID | None
    department_name: str | None
    employer_id: uuid.UUID | None
    manager_name: str | None
    user_id: uuid.UUID
    email: str
    employee_number: str
    first_name: str
    last_name: str
    job_title: str | None
    hire_date: date | None
    employment_status: EmploymentStatus
    phone: str | None
    created_at: datetime
