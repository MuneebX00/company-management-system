from enum import StrEnum


class EmploymentStatus(StrEnum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    SUSPENDED = "SUSPENDED"
    TERMINATED = "TERMINATED"


class AttendanceStatus(StrEnum):
    PRESENT = "PRESENT"
    LATE = "LATE"
    ABSENT = "ABSENT"
    HALF_DAY = "HALF_DAY"
    ON_LEAVE = "ON_LEAVE"


class LeaveStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class ProjectStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TaskStatus(StrEnum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"
