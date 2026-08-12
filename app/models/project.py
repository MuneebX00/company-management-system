from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import ProjectStatus
from app.models.company import Company
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.employer import Employer
    from app.models.task import Task
    from app.models.user import User


class ProjectMember(Base):
    """Association between a project and an employee (with an optional role)."""

    __tablename__ = "project_members"

    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("employees.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str | None] = mapped_column(String(100))

    project: Mapped[Project] = relationship(back_populates="members")
    employee: Mapped[Employee] = relationship(back_populates="project_memberships")

    @property
    def employee_name(self) -> str:
        return self.employee.name


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A company project owned/managed by an employer."""

    __tablename__ = "projects"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("employers.id", ondelete="SET NULL")
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, native_enum=False, length=20, create_constraint=True),
        default=ProjectStatus.NOT_STARTED,
        nullable=False,
    )
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)

    company: Mapped[Company] = relationship(lazy="joined")
    owner: Mapped[Employer | None] = relationship(back_populates="projects", lazy="joined")
    creator: Mapped[User] = relationship(lazy="joined")
    members: Mapped[list[ProjectMember]] = relationship(
        back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    tasks: Mapped[list[Task]] = relationship(back_populates="project", passive_deletes=True)

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_projects_company_id_name"),
        Index("ix_projects_company_id", "company_id"),
        Index("ix_projects_owner_id", "owner_id"),
    )

    @property
    def owner_name(self) -> str | None:
        return self.owner.name if self.owner else None

    @property
    def member_count(self) -> int:
        return len(self.members)
