from fastapi import APIRouter

from app.api.v1 import (
    attendance,
    auth,
    companies,
    departments,
    employees,
    employers,
    health,
    leave,
    users,
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(departments.router, prefix="/departments", tags=["departments"])
api_router.include_router(employers.router, prefix="/employers", tags=["employers"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["attendance"])
api_router.include_router(leave.router, prefix="/leave", tags=["leave"])
