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
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.core.enums import TaskPriority, TaskStatus
from app.models.company import Company
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.employer import Employer
    from app.models.project import Project
    from app.models.user import User


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A unit of work within a project, optionally assigned to an employee."""

    __tablename__ = "tasks"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("employees.id", ondelete="SET NULL")
    )
    assigned_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("employers.id", ondelete="SET NULL")
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, native_enum=False, length=20, create_constraint=True),
        default=TaskStatus.TODO,
        nullable=False,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, native_enum=False, length=20, create_constraint=True),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    company: Mapped[Company] = relationship(lazy="joined")
    project: Mapped[Project] = relationship(back_populates="tasks", lazy="joined")
    assignee: Mapped[Employee | None] = relationship(back_populates="tasks", lazy="joined")
    assigner: Mapped[Employer | None] = relationship(back_populates="assigned_tasks", lazy="joined")
    creator: Mapped[User] = relationship(lazy="joined")

    __table_args__ = (
        Index("ix_tasks_company_id", "company_id"),
        Index("ix_tasks_project_id", "project_id"),
        Index("ix_tasks_assigned_to", "assigned_to"),
        Index("ix_tasks_status", "status"),
    )

    @property
    def project_name(self) -> str:
        return self.project.name

    @property
    def assignee_name(self) -> str | None:
        return self.assignee.name if self.assignee else None
