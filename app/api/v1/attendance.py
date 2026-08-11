import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies.database import DbSession
from app.dependencies.rbac import require_any_permission, require_permission
from app.models import AttendanceRecord, Employee, User
from app.schemas.attendance import AttendanceListQuery, AttendanceResponse, AttendanceUpdate
from app.services.attendance import _compute_hours, check_in, check_out, get_scoped_attendance
from app.services.org import employee_scope_expr
from app.utils.pagination import Page, PageParams, get_page

router = APIRouter()

_VIEW_PERMISSIONS = ("attendance.view_self", "attendance.view_all")


@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=201,
    summary="Check in for today",
    description="Creates today's attendance record (409 if already checked in).",
)
def check_in_today(
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("attendance.check_in"))],
) -> AttendanceResponse:
    return AttendanceResponse.model_validate(check_in(db, current_user))


@router.post(
    "/check-out",
    response_model=AttendanceResponse,
    status_code=201,
    summary="Check out for today",
    description="Closes today's record and computes hours worked (409 if not checked in).",
)
def check_out_today(
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("attendance.check_out"))],
) -> AttendanceResponse:
    return AttendanceResponse.model_validate(check_out(db, current_user))


@router.get(
    "",
    response_model=Page[AttendanceResponse],
    summary="List attendance records within the caller's scope",
)
def list_attendance(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    query: Annotated[AttendanceListQuery, Depends()],
    current_user: Annotated[User, Depends(require_any_permission(*_VIEW_PERMISSIONS))],
) -> Page[AttendanceResponse]:
    statement = (
        select(AttendanceRecord)
        .join(Employee, AttendanceRecord.employee_id == Employee.id)
        .where(employee_scope_expr(current_user))
    )
    if query.from_date is not None:
        statement = statement.where(AttendanceRecord.work_date >= query.from_date)
    if query.to_date is not None:
        statement = statement.where(AttendanceRecord.work_date <= query.to_date)
    statement = statement.order_by(
        AttendanceRecord.work_date.desc(), AttendanceRecord.check_in_at.desc()
    )
    items, total = get_page(db, statement, params.page, params.page_size)
    return Page[AttendanceResponse](
        items=[AttendanceResponse.model_validate(item) for item in items],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


@router.get(
    "/{record_id}",
    response_model=AttendanceResponse,
    summary="Get an attendance record within the caller's scope",
)
def get_attendance(
    record_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_any_permission(*_VIEW_PERMISSIONS))],
) -> AttendanceResponse:
    return AttendanceResponse.model_validate(get_scoped_attendance(db, current_user, record_id))


@router.patch(
    "/{record_id}",
    response_model=AttendanceResponse,
    summary="Correct an attendance record",
    description="Admin only. Adjusts timestamps/status and recomputes hours worked.",
)
def correct_attendance(
    record_id: uuid.UUID,
    payload: AttendanceUpdate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("attendance.correct"))],
) -> AttendanceResponse:
    record = get_scoped_attendance(db, current_user, record_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    if record.check_in_at is not None and record.check_out_at is not None:
        record.hours_worked = _compute_hours(record.check_in_at, record.check_out_at)
    elif record.check_in_at is None or record.check_out_at is None:
        record.hours_worked = None
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A record already exists for this employee and date",
        ) from exc
    db.refresh(record)
    return AttendanceResponse.model_validate(record)
