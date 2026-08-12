from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.company import Company
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.department import Department
    from app.models.employee import Employee
    from app.models.project import Project
    from app.models.task import Task
    from app.models.user import User


class Employer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A manager/employer profile linked 1:1 to an EMPLOYER user account."""

    __tablename__ = "employers"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("departments.id", ondelete="RESTRICT")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, unique=True
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    job_title: Mapped[str | None] = mapped_column(String(150))
    hire_date: Mapped[date | None] = mapped_column(Date)

    company: Mapped[Company] = relationship(lazy="joined")
    department: Mapped[Department | None] = relationship(lazy="joined")
    user: Mapped[User] = relationship(back_populates="employer_profile", lazy="joined")
    managed_employees: Mapped[list[Employee]] = relationship(back_populates="employer")
    projects: Mapped[list[Project]] = relationship(back_populates="owner")
    assigned_tasks: Mapped[list[Task]] = relationship(back_populates="assigner")

    __table_args__ = (Index("ix_employers_company_id", "company_id"),)

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def department_name(self) -> str | None:
        return self.department.name if self.department else None

    @property
    def email(self) -> str:
        return self.user.email
