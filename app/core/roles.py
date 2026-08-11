from enum import StrEnum


class RoleName(StrEnum):
    ADMIN_HR = "ADMIN_HR"
    EMPLOYER = "EMPLOYER"
    EMPLOYEE = "EMPLOYEE"


class PermissionCodes:
    """Granular permission codes used by require_permission and role seeding."""

    COMPANY_CREATE = "company.create"
    COMPANY_VIEW = "company.view"
    COMPANY_UPDATE = "company.update"
    COMPANY_DELETE = "company.delete"

    DEPARTMENT_CREATE = "department.create"
    DEPARTMENT_VIEW = "department.view"
    DEPARTMENT_UPDATE = "department.update"
    DEPARTMENT_DELETE = "department.delete"

    EMPLOYEE_CREATE = "employee.create"
    EMPLOYEE_VIEW = "employee.view"
    EMPLOYEE_UPDATE = "employee.update"
    EMPLOYEE_DEACTIVATE = "employee.deactivate"

    EMPLOYER_CREATE = "employer.create"
    EMPLOYER_VIEW = "employer.view"
    EMPLOYER_UPDATE = "employer.update"

    USER_CREATE = "user.create"
    USER_VIEW = "user.view"
    USER_UPDATE = "user.update"
    USER_DEACTIVATE = "user.deactivate"

    ROLE_VIEW = "role.view"
    ROLE_MANAGE = "role.manage"

    ATTENDANCE_CHECK_IN = "attendance.check_in"
    ATTENDANCE_CHECK_OUT = "attendance.check_out"
    ATTENDANCE_VIEW_SELF = "attendance.view_self"
    ATTENDANCE_VIEW_ALL = "attendance.view_all"
    ATTENDANCE_CORRECT = "attendance.correct"

    LEAVE_CREATE = "leave.create"
    LEAVE_VIEW_SELF = "leave.view_self"
    LEAVE_VIEW_ALL = "leave.view_all"
    LEAVE_APPROVE = "leave.approve"

    PAYROLL_VIEW_SELF = "payroll.view_self"
    PAYROLL_VIEW_ALL = "payroll.view_all"
    PAYROLL_CREATE = "payroll.create"
    PAYROLL_GENERATE = "payroll.generate"

    PROJECT_CREATE = "project.create"
    PROJECT_VIEW = "project.view"
    PROJECT_UPDATE = "project.update"
    PROJECT_MEMBER_MANAGE = "project.member_manage"

    TASK_CREATE = "task.create"
    TASK_VIEW = "task.view"
    TASK_UPDATE = "task.update"
    TASK_ASSIGN = "task.assign"

    NOTIFICATION_SEND = "notification.send"
    NOTIFICATION_VIEW = "notification.view"

    AUDIT_VIEW = "audit.view"

    AI_USE = "ai.use"
    AI_VIEW_INSIGHTS = "ai.view_insights"


ALL_PERMISSIONS: list[str] = [
    value for name, value in vars(PermissionCodes).items() if name.isupper()
]

EMPLOYER_PERMISSIONS: list[str] = [
    PermissionCodes.EMPLOYEE_VIEW,
    PermissionCodes.EMPLOYEE_UPDATE,
    PermissionCodes.EMPLOYER_VIEW,
    PermissionCodes.DEPARTMENT_VIEW,
    PermissionCodes.ATTENDANCE_VIEW_ALL,
    PermissionCodes.LEAVE_VIEW_ALL,
    PermissionCodes.LEAVE_APPROVE,
    PermissionCodes.PAYROLL_VIEW_ALL,
    PermissionCodes.PROJECT_CREATE,
    PermissionCodes.PROJECT_VIEW,
    PermissionCodes.PROJECT_UPDATE,
    PermissionCodes.PROJECT_MEMBER_MANAGE,
    PermissionCodes.TASK_CREATE,
    PermissionCodes.TASK_VIEW,
    PermissionCodes.TASK_UPDATE,
    PermissionCodes.TASK_ASSIGN,
    PermissionCodes.NOTIFICATION_SEND,
    PermissionCodes.NOTIFICATION_VIEW,
    PermissionCodes.AI_USE,
]

EMPLOYEE_PERMISSIONS: list[str] = [
    PermissionCodes.EMPLOYEE_VIEW,
    PermissionCodes.ATTENDANCE_CHECK_IN,
    PermissionCodes.ATTENDANCE_CHECK_OUT,
    PermissionCodes.ATTENDANCE_VIEW_SELF,
    PermissionCodes.LEAVE_CREATE,
    PermissionCodes.LEAVE_VIEW_SELF,
    PermissionCodes.PAYROLL_VIEW_SELF,
    PermissionCodes.TASK_VIEW,
    PermissionCodes.TASK_UPDATE,
    PermissionCodes.NOTIFICATION_VIEW,
    PermissionCodes.AI_USE,
]

ROLE_PERMISSIONS: dict[RoleName, list[str]] = {
    RoleName.ADMIN_HR: ALL_PERMISSIONS,
    RoleName.EMPLOYER: EMPLOYER_PERMISSIONS,
    RoleName.EMPLOYEE: EMPLOYEE_PERMISSIONS,
}
