from pydantic import BaseModel, Field
from datetime import datetime


def _mask_key(key: str | None) -> str | None:
    """遮蔽 API Key，只显示前 5 后 4 位"""
    if not key or len(key) < 10:
        return key
    return key[:5] + "****" + key[-4:]


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str | None
    role: str
    avatar: str | None
    api_key: str | None = None
    api_base: str | None = None
    created_at: datetime

    @classmethod
    def from_user(cls, user):
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            avatar=user.avatar,
            api_key=_mask_key(user.api_key),
            api_base=user.api_base,
            created_at=user.created_at,
        )

    class Config:
        from_attributes = True


class UpdateProfileRequest(BaseModel):
    email: str | None = None
    avatar: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=50)


class UpdateApiKeyRequest(BaseModel):
    api_key: str
    api_base: str = "https://api.deepseek.com"
