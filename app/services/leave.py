"""Business rules and tenant scoping for leave types and leave requests."""

import uuid
from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import LeaveStatus
from app.core.roles import RoleName
from app.models import LeaveRequest, LeaveType, User


def _not_found(resource: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{resource} not found")


def compute_days(start_date: date, end_date: date) -> int:
    return (end_date - start_date).days + 1


def get_scoped_leave_type(db: Session, current_user: User, leave_type_id: uuid.UUID) -> LeaveType:
    leave_type = db.get(LeaveType, leave_type_id)
    if leave_type is None or leave_type.company_id != current_user.company_id:
        raise _not_found("Leave type")
    return leave_type


def get_active_leave_type(db: Session, current_user: User, leave_type_id: uuid.UUID) -> LeaveType:
    leave_type = get_scoped_leave_type(db, current_user, leave_type_id)
    if not leave_type.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Leave type is inactive"
        )
    return leave_type


def get_scoped_leave_request(
    db: Session, current_user: User, request_id: uuid.UUID
) -> LeaveRequest:
    request = db.get(LeaveRequest, request_id)
    if request is None or request.company_id != current_user.company_id:
        raise _not_found("Leave request")
    employee = request.employee
    if current_user.role.name == RoleName.ADMIN_HR:
        return request
    if current_user.role.name == RoleName.EMPLOYER:
        profile = current_user.employer_profile
        if profile is not None and employee.employer_id == profile.id:
            return request
    if employee.user_id == current_user.id:
        return request
    raise _not_found("Leave request")


def check_no_overlap(
    db: Session,
    employee_id: uuid.UUID,
    start_date: date,
    end_date: date,
    exclude_id: uuid.UUID | None = None,
) -> None:
    statement = select(LeaveRequest).where(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.APPROVED]),
        LeaveRequest.start_date <= end_date,
        LeaveRequest.end_date >= start_date,
    )
    if exclude_id is not None:
        statement = statement.where(LeaveRequest.id != exclude_id)
    if db.scalar(statement) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Request overlaps an existing leave request",
        )


def approve_request(
    db: Session, request: LeaveRequest, reviewer: User, note: str | None
) -> LeaveRequest:
    if request.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot approve a {request.status} request",
        )
    request.status = LeaveStatus.APPROVED
    request.reviewed_by = reviewer.id
    request.reviewed_at = datetime.now(UTC)
    request.decision_note = note
    db.commit()
    db.refresh(request)
    return request


def reject_request(
    db: Session, request: LeaveRequest, reviewer: User, note: str | None
) -> LeaveRequest:
    if request.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reject a {request.status} request",
        )
    request.status = LeaveStatus.REJECTED
    request.reviewed_by = reviewer.id
    request.reviewed_at = datetime.now(UTC)
    request.decision_note = note
    db.commit()
    db.refresh(request)
    return request


def cancel_request(db: Session, request: LeaveRequest, current_user: User) -> LeaveRequest:
    if request.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot cancel a {request.status} request",
        )
    is_manager = current_user.role.name in (RoleName.ADMIN_HR, RoleName.EMPLOYER)
    is_owner = request.employee.user_id == current_user.id
    if not (is_manager or is_owner):
        raise _not_found("Leave request")
    request.status = LeaveStatus.CANCELLED
    db.commit()
    db.refresh(request)
    return request
