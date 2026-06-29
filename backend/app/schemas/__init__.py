from app.schemas.auth import RegisterRequest, LoginRequest, AuthResponse
from app.schemas.user import UserProfileResponse, UpdateProfileRequest, ChangePasswordRequest
from app.schemas.paper import CreatePaperRequest, PaperResponse, UpdatePaperRequest
from app.schemas.reference import ReferenceRequest, ReferenceResponse
from app.schemas.task import FeedbackRequest, TaskResponse

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "AuthResponse",
    "UserProfileResponse",
    "UpdateProfileRequest",
    "ChangePasswordRequest",
    "CreatePaperRequest",
    "PaperResponse",
    "UpdatePaperRequest",
    "ReferenceRequest",
    "ReferenceResponse",
    "FeedbackRequest",
    "TaskResponse",
]
