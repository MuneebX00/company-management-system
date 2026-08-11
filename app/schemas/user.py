import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.roles import RoleName


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role_code: RoleName

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    role: RoleName
    company_id: uuid.UUID
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime

    @field_validator("role", mode="before")
    @classmethod
    def coerce_role(cls, value: object) -> object:
        if hasattr(value, "name"):
            return value.name
        return value
