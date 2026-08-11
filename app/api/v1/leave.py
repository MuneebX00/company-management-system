import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.enums import LeaveStatus
from app.dependencies.database import DbSession
from app.dependencies.rbac import require_any_permission, require_permission
from app.models import Employee, LeaveRequest, LeaveType, User
from app.schemas.leave import (
    LeaveDecision,
    LeaveRequestCreate,
    LeaveRequestResponse,
    LeaveRequestUpdate,
    LeaveTypeCreate,
    LeaveTypeResponse,
    LeaveTypeUpdate,
)
from app.services.leave import (
    approve_request,
    cancel_request,
    check_no_overlap,
    compute_days,
    get_active_leave_type,
    get_scoped_leave_request,
    get_scoped_leave_type,
    reject_request,
)
from app.services.org import employee_scope_expr, get_current_employee
from app.utils.pagination import Page, PageParams, get_page

router = APIRouter()

_ANY_LEAVE_PERMISSIONS = ("leave.create", "leave.view_self", "leave.view_all", "leave.approve")
_EMPTY_DECISION = LeaveDecision()


@router.get(
    "/types",
    response_model=Page[LeaveTypeResponse],
    summary="List leave types in the current company",
)
def list_leave_types(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    current_user: Annotated[User, Depends(require_any_permission(*_ANY_LEAVE_PERMISSIONS))],
) -> Page[LeaveTypeResponse]:
    statement = (
        select(LeaveType)
        .where(LeaveType.company_id == current_user.company_id)
        .order_by(LeaveType.name)
    )
    items, total = get_page(db, statement, params.page, params.page_size)
    return Page[LeaveTypeResponse](
        items=[LeaveTypeResponse.model_validate(item) for item in items],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


@router.get(
    "/types/{leave_type_id}",
    response_model=LeaveTypeResponse,
    summary="Get a leave type in the current company",
)
def get_leave_type(
    leave_type_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_any_permission(*_ANY_LEAVE_PERMISSIONS))],
) -> LeaveTypeResponse:
    return LeaveTypeResponse.model_validate(get_scoped_leave_type(db, current_user, leave_type_id))


@router.post(
    "/types",
    response_model=LeaveTypeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a leave type",
    description="Admin only. Leave types are company-level settings.",
)
def create_leave_type(
    payload: LeaveTypeCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("company.update"))],
) -> LeaveTypeResponse:
    leave_type = LeaveType(company_id=current_user.company_id, **payload.model_dump())
    db.add(leave_type)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Leave type name already exists"
        ) from exc
    db.refresh(leave_type)
    return LeaveTypeResponse.model_validate(leave_type)


@router.patch(
    "/types/{leave_type_id}",
    response_model=LeaveTypeResponse,
    summary="Update a leave type",
)
def update_leave_type(
    leave_type_id: uuid.UUID,
    payload: LeaveTypeUpdate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("company.update"))],
) -> LeaveTypeResponse:
    leave_type = get_scoped_leave_type(db, current_user, leave_type_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(leave_type, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Leave type name already exists"
        ) from exc
    db.refresh(leave_type)
    return LeaveTypeResponse.model_validate(leave_type)


@router.delete(
    "/types/{leave_type_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a leave type",
)
def delete_leave_type(
    leave_type_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("company.update"))],
) -> None:
    leave_type = get_scoped_leave_type(db, current_user, leave_type_id)
    db.delete(leave_type)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Leave type is used by existing requests",
        ) from exc


@router.get(
    "/requests",
    response_model=Page[LeaveRequestResponse],
    summary="List leave requests within the caller's scope",
)
def list_leave_requests(
    db: DbSession,
    params: Annotated[PageParams, Depends()],
    current_user: Annotated[User, Depends(require_any_permission(*_ANY_LEAVE_PERMISSIONS))],
) -> Page[LeaveRequestResponse]:
    statement = (
        select(LeaveRequest)
        .join(Employee, LeaveRequest.employee_id == Employee.id)
        .where(employee_scope_expr(current_user))
        .order_by(LeaveRequest.created_at.desc())
    )
    items, total = get_page(db, statement, params.page, params.page_size)
    return Page[LeaveRequestResponse](
        items=[LeaveRequestResponse.model_validate(item) for item in items],
        page=params.page,
        page_size=params.page_size,
        total=total,
    )


@router.get(
    "/requests/{request_id}",
    response_model=LeaveRequestResponse,
    summary="Get a leave request within the caller's scope",
)
def get_leave_request(
    request_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_any_permission(*_ANY_LEAVE_PERMISSIONS))],
) -> LeaveRequestResponse:
    return LeaveRequestResponse.model_validate(
        get_scoped_leave_request(db, current_user, request_id)
    )


@router.post(
    "/requests",
    response_model=LeaveRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a leave request",
    description="Employees request leave; overlapping pending/approved requests are rejected.",
)
def create_leave_request(
    payload: LeaveRequestCreate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("leave.create"))],
) -> LeaveRequestResponse:
    employee = get_current_employee(db, current_user)
    leave_type = get_active_leave_type(db, current_user, payload.leave_type_id)
    days = compute_days(payload.start_date, payload.end_date)
    check_no_overlap(db, employee.id, payload.start_date, payload.end_date)

    request = LeaveRequest(
        company_id=employee.company_id,
        employee_id=employee.id,
        leave_type_id=leave_type.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        days=days,
        reason=payload.reason,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return LeaveRequestResponse.model_validate(request)


@router.patch(
    "/requests/{request_id}",
    response_model=LeaveRequestResponse,
    summary="Update an own pending leave request",
)
def update_leave_request(
    request_id: uuid.UUID,
    payload: LeaveRequestUpdate,
    db: DbSession,
    current_user: Annotated[User, Depends(require_any_permission(*_ANY_LEAVE_PERMISSIONS))],
) -> LeaveRequestResponse:
    request = get_scoped_leave_request(db, current_user, request_id)
    if request.employee.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave request not found")
    if request.status != LeaveStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot update a {request.status} request",
        )

    if payload.leave_type_id is not None:
        get_active_leave_type(db, current_user, payload.leave_type_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(request, field, value)
    request.days = compute_days(request.start_date, request.end_date)
    check_no_overlap(
        db, request.employee_id, request.start_date, request.end_date, exclude_id=request.id
    )

    db.commit()
    db.refresh(request)
    return LeaveRequestResponse.model_validate(request)


@router.post(
    "/requests/{request_id}/approve",
    response_model=LeaveRequestResponse,
    summary="Approve a leave request",
    description="Admin sees all; employers approve within their team.",
)
def approve_leave_request(
    request_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("leave.approve"))],
    payload: LeaveDecision = _EMPTY_DECISION,
) -> LeaveRequestResponse:
    request = get_scoped_leave_request(db, current_user, request_id)
    return LeaveRequestResponse.model_validate(
        approve_request(db, request, current_user, payload.note)
    )


@router.post(
    "/requests/{request_id}/reject",
    response_model=LeaveRequestResponse,
    summary="Reject a leave request",
    description="Admin sees all; employers reject within their team.",
)
def reject_leave_request(
    request_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("leave.approve"))],
    payload: LeaveDecision = _EMPTY_DECISION,
) -> LeaveRequestResponse:
    request = get_scoped_leave_request(db, current_user, request_id)
    return LeaveRequestResponse.model_validate(
        reject_request(db, request, current_user, payload.note)
    )


@router.post(
    "/requests/{request_id}/cancel",
    response_model=LeaveRequestResponse,
    summary="Cancel a pending leave request",
    description="The requesting employee, or any manager, may cancel a pending request.",
)
def cancel_leave_request(
    request_id: uuid.UUID,
    db: DbSession,
    current_user: Annotated[User, Depends(require_any_permission(*_ANY_LEAVE_PERMISSIONS))],
) -> LeaveRequestResponse:
    request = get_scoped_leave_request(db, current_user, request_id)
    return LeaveRequestResponse.model_validate(cancel_request(db, request, current_user))
