from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import EmploymentStatus
from app.models.company import Company
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.attendance import AttendanceRecord
    from app.models.department import Department
    from app.models.employer import Employer
    from app.models.leave import LeaveRequest
    from app.models.user import User


class Employee(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """An employee profile linked 1:1 to an EMPLOYEE user account."""

    __tablename__ = "employees"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="RESTRICT")
    )
    employer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("employers.id", ondelete="SET NULL")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    employee_number: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(150))
    hire_date: Mapped[date | None] = mapped_column(Date)
    employment_status: Mapped[EmploymentStatus] = mapped_column(
        Enum(EmploymentStatus, native_enum=False, length=20, create_constraint=True),
        default=EmploymentStatus.ACTIVE,
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(String(50))

    company: Mapped[Company] = relationship(lazy="joined")
    department: Mapped[Department | None] = relationship(lazy="joined")
    employer: Mapped[Employer | None] = relationship(lazy="joined")
    user: Mapped[User] = relationship(back_populates="employee_profile", lazy="joined")
    attendance_records: Mapped[list[AttendanceRecord]] = relationship(back_populates="employee")
    leave_requests: Mapped[list[LeaveRequest]] = relationship(back_populates="employee")

    __table_args__ = (
        UniqueConstraint("company_id", "employee_number", name="uq_employees_company_number"),
        Index("ix_employees_company_id", "company_id"),
        Index("ix_employees_department_id", "department_id"),
        Index("ix_employees_employer_id", "employer_id"),
    )

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None

    @property
    def manager_name(self) -> str | None:
        return f"{self.employer.first_name} {self.employer.last_name}" if self.employer else None

    @property
    def email(self) -> str:
        return self.user.email
