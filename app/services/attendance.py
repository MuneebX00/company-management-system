"""Business rules and tenant scoping for attendance records."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import AttendanceStatus
from app.core.roles import RoleName
from app.models import AttendanceRecord, Employee, User
from app.services.org import get_current_employee


def _now() -> datetime:
    return datetime.now(UTC)


def _compute_hours(check_in_at: datetime, check_out_at: datetime) -> Decimal:
    if check_out_at < check_in_at:
        return Decimal("0.00")
    seconds = (check_out_at - check_in_at).total_seconds()
    return Decimal(str(round(seconds / 3600, 2)))


def check_in(db: Session, current_user: User) -> AttendanceRecord:
    employee = get_current_employee(db, current_user)
    today = date.today()

    record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.work_date == today,
        )
    )
    if record is not None and record.check_in_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already checked in for today"
        )

    if record is None:
        record = AttendanceRecord(
            company_id=employee.company_id,
            employee_id=employee.id,
            work_date=today,
            check_in_at=_now(),
            status=AttendanceStatus.PRESENT,
        )
        db.add(record)
    else:
        record.check_in_at = _now()

    db.commit()
    db.refresh(record)
    return record


def check_out(db: Session, current_user: User) -> AttendanceRecord:
    employee = get_current_employee(db, current_user)
    today = date.today()

    record = db.scalar(
        select(AttendanceRecord).where(
            AttendanceRecord.employee_id == employee.id,
            AttendanceRecord.work_date == today,
        )
    )
    if record is None or record.check_in_at is None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Not checked in for today")
    if record.check_out_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Already checked out for today"
        )

    record.check_out_at = _now()
    record.hours_worked = _compute_hours(record.check_in_at, record.check_out_at)
    db.commit()
    db.refresh(record)
    return record


def get_scoped_attendance(
    db: Session, current_user: User, record_id: uuid.UUID
) -> AttendanceRecord:
    record = db.get(AttendanceRecord, record_id)
    if record is None or record.company_id != current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found"
        )
    employee = record.employee
    if not _may_view_employee_record(current_user, employee):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Attendance record not found"
        )
    return record


def _may_view_employee_record(current_user: User, employee: Employee) -> bool:
    if current_user.role.name == RoleName.ADMIN_HR:
        return True
    if current_user.role.name == RoleName.EMPLOYER:
        profile = current_user.employer_profile
        return profile is not None and employee.employer_id == profile.id
    return employee.user_id == current_user.id
