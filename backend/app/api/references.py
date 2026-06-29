from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.reference import UserReference
from app.models.user import User
from app.schemas.reference import ReferenceRequest, ReferenceResponse
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/user/references", tags=["references"])


@router.get("", response_model=list[ReferenceResponse])
def list_references(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UserReference).filter(UserReference.user_id == current_user.id).all()


@router.post("", response_model=ReferenceResponse)
def create_reference(req: ReferenceRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = UserReference(user_id=current_user.id, **req.model_dump())
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


@router.delete("/{ref_id}")
def delete_reference(ref_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(UserReference).filter(UserReference.id == ref_id, UserReference.user_id == current_user.id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="文献不存在")
    db.delete(ref)
    db.commit()
    return {"message": "ok"}
