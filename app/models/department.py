from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.company import Company
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.employer import Employer


class Department(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A department owned by a company. Holds employers and employees."""

    __tablename__ = "departments"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500))
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    company: Mapped[Company] = relationship(lazy="joined")
    employees: Mapped[list[Employee]] = relationship(
        back_populates="department", cascade="all, delete-orphan"
    )
    employers: Mapped[list[Employer]] = relationship(back_populates="department")

    __table_args__ = (
        UniqueConstraint("company_id", "name", name="uq_departments_company_name"),
        Index("ix_departments_company_id", "company_id"),
    )
