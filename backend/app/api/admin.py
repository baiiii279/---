from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.paper import Paper
from app.models.agent_log import AgentLog
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


@router.get("/users")
def list_users(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
               admin: User = Depends(_require_admin), db: Session = Depends(get_db)):
    total = db.query(User).count()
    users = db.query(User).offset((page-1)*size).limit(size).all()
    return {"total": total, "page": page, "size": size, "items": users}


@router.get("/papers")
def list_all_papers(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                    status: str = None, admin: User = Depends(_require_admin), db: Session = Depends(get_db)):
    q = db.query(Paper)
    if status:
        q = q.filter(Paper.status == status)
    total = q.count()
    papers = q.offset((page-1)*size).limit(size).all()
    return {"total": total, "page": page, "size": size, "items": papers}


@router.delete("/papers/{paper_id}")
def admin_delete_paper(paper_id: int, admin: User = Depends(_require_admin), db: Session = Depends(get_db)):
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    db.delete(paper)
    db.commit()
    return {"message": "ok"}


@router.get("/stats")
def stats(admin: User = Depends(_require_admin), db: Session = Depends(get_db)):
    return {
        "users": db.query(User).count(),
        "papers": db.query(Paper).count(),
    }


@router.get("/logs")
def list_logs(user_id: int = None, paper_id: int = None, status: str = None,
              page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
              admin: User = Depends(_require_admin), db: Session = Depends(get_db)):
    q = db.query(AgentLog)
    total = q.count()
    logs = q.order_by(AgentLog.id.desc()).offset((page-1)*size).limit(size).all()
    return {"total": total, "page": page, "size": size, "items": logs}
