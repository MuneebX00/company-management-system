import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import AttendanceStatus


class AttendanceUpdate(BaseModel):
    work_date: date | None = None
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    status: AttendanceStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def _validate_window(self):
        if (
            self.check_in_at is not None
            and self.check_out_at is not None
            and self.check_out_at < self.check_in_at
        ):
            raise ValueError("check_out_at must not be before check_in_at")
        return self


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    employee_id: uuid.UUID
    employee_name: str
    work_date: date
    check_in_at: datetime | None
    check_out_at: datetime | None
    hours_worked: Decimal | None
    status: AttendanceStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AttendanceListQuery(BaseModel):
    from_date: date | None = None
    to_date: date | None = None
