import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import LeaveStatus


def _validate_date_window(start_date: date | None, end_date: date | None) -> None:
    if start_date is not None and end_date is not None and end_date < start_date:
        raise ValueError("end_date must not be before start_date")


class LeaveTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    days_per_year: int = Field(default=15, ge=1, le=365)
    description: str | None = Field(default=None, max_length=500)


class LeaveTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    days_per_year: int | None = Field(default=None, ge=1, le=365)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class LeaveTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    days_per_year: int
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LeaveRequestCreate(BaseModel):
    leave_type_id: uuid.UUID
    start_date: date
    end_date: date
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _validate_window(self):
        _validate_date_window(self.start_date, self.end_date)
        return self


class LeaveRequestUpdate(BaseModel):
    leave_type_id: uuid.UUID | None = None
    start_date: date | None = None
    end_date: date | None = None
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _validate_window(self):
        _validate_date_window(self.start_date, self.end_date)
        return self


class LeaveDecision(BaseModel):
    note: str | None = Field(default=None, max_length=2000)


class LeaveRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str
    leave_type_id: uuid.UUID
    leave_type_name: str
    start_date: date
    end_date: date
    days: int
    status: LeaveStatus
    reason: str | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    decision_note: str | None
    created_at: datetime
    updated_at: datetime
