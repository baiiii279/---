from pydantic import BaseModel
from datetime import datetime

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str | None
    role: str
    avatar: str | None
    created_at: datetime

    class Config:
        from_attributes = True

class UpdateProfileRequest(BaseModel):
    email: str | None = None
    avatar: str | None = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
