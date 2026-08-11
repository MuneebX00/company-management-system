from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import AttendanceStatus
from app.models.company import Company
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.employee import Employee


class AttendanceRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A single employee's check-in/check-out record for one work date."""

    __tablename__ = "attendance_records"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    hours_worked: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus, native_enum=False, length=20, create_constraint=True),
        default=AttendanceStatus.PRESENT,
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(Text)

    company: Mapped[Company] = relationship(lazy="joined")
    employee: Mapped[Employee] = relationship(back_populates="attendance_records", lazy="joined")

    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_attendance_employee_date"),
        Index("ix_attendance_company_id", "company_id"),
        Index("ix_attendance_employee_id", "employee_id"),
        Index("ix_attendance_work_date", "work_date"),
    )

    @property
    def employee_name(self) -> str:
        return self.employee.name
