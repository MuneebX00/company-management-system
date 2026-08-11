from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import LeaveStatus
from app.models.company import Company
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.user import User


class LeaveType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A company-defined leave category (e.g. Annual, Sick, Casual)."""

    __tablename__ = "leave_types"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    days_per_year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    company: Mapped[Company] = relationship(lazy="joined")
    requests: Mapped[list[LeaveRequest]] = relationship(back_populates="leave_type")

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_leave_types_company_name"),
        Index("ix_leave_types_company_id", "company_id"),
    )


class LeaveRequest(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A leave request made by an employee and reviewed by an admin/employer."""

    __tablename__ = "leave_requests"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.id", ondelete="RESTRICT"), nullable=False
    )
    leave_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("leave_types.id", ondelete="RESTRICT"), nullable=False
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[LeaveStatus] = mapped_column(
        Enum(LeaveStatus, native_enum=False, length=20, create_constraint=True),
        default=LeaveStatus.PENDING,
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[str | None] = mapped_column(Text)

    company: Mapped[Company] = relationship(lazy="joined")
    employee: Mapped[Employee] = relationship(back_populates="leave_requests", lazy="joined")
    leave_type: Mapped[LeaveType] = relationship(lazy="joined")
    reviewer: Mapped[User | None] = relationship(lazy="joined")

    __table_args__ = (
        Index("ix_leave_requests_company_id", "company_id"),
        Index("ix_leave_requests_employee_id", "employee_id"),
        Index("ix_leave_requests_status", "status"),
    )

    @property
    def employee_name(self) -> str:
        return self.employee.name

    @property
    def leave_type_name(self) -> str:
        return self.leave_type.name
