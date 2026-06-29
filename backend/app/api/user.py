from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UpdateProfileRequest, ChangePasswordRequest, UserProfileResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/user", tags=["user"])


@router.put("/profile")
def update_profile(req: UpdateProfileRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if req.email is not None:
        current_user.email = req.email
    if req.avatar is not None:
        current_user.avatar = req.avatar
    db.commit()
    return {"message": "ok"}


@router.put("/password")
def change_password(req: ChangePasswordRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(req.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    current_user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"message": "ok"}
