import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.core.roles import RoleName


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: RoleName
    company_id: uuid.UUID
    company_name: str
    is_active: bool
    last_login_at: datetime | None
