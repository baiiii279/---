from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.paper import Paper
from app.models.reference import PaperReference
from app.models.task import Task
from app.models.agent_log import AgentLog
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


@router.get("/users")
def list_users(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    keyword: str = Query(None, description="搜索用户名或邮箱"),
    admin: User = Depends(_require_admin), db: Session = Depends(get_db),
):
    q = db.query(User)
    if keyword:
        q = q.filter(User.username.like(f"%{keyword}%") | User.email.like(f"%{keyword}%"))
    total = q.count()
    users = q.order_by(User.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"total": total, "page": page, "size": size, "items": users}


@router.put("/users/{user_id}/role")
def change_user_role(
    user_id: int, role: str = Query(..., regex="^(user|admin)$"),
    admin: User = Depends(_require_admin), db: Session = Depends(get_db),
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="不能修改自己的角色")
    target = db.query(User).get(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    target.role = role
    db.commit()
    return {"message": f"用户 {target.username} 角色已变更为 {role}"}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: User = Depends(_require_admin), db: Session = Depends(get_db),
):
    if admin.id == user_id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")
    target = db.query(User).get(user_id)
    if not target:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 级联删除关联数据
    paper_ids = [p.id for p in db.query(Paper).filter(Paper.user_id == user_id).all()]
    if paper_ids:
        db.query(PaperReference).filter(PaperReference.paper_id.in_(paper_ids)).delete(synchronize_session=False)
        task_ids = [t.id for t in db.query(Task).filter(Task.paper_id.in_(paper_ids)).all()]
        if task_ids:
            db.query(AgentLog).filter(AgentLog.task_id.in_(task_ids)).delete(synchronize_session=False)
        db.query(Task).filter(Task.paper_id.in_(paper_ids)).delete(synchronize_session=False)
        db.query(Paper).filter(Paper.user_id == user_id).delete(synchronize_session=False)
    db.query(User).filter(User.id == user_id).delete()
    db.commit()
    return {"message": f"用户 {target.username} 已删除"}


@router.get("/papers")
def list_all_papers(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    status: str = None, admin: User = Depends(_require_admin), db: Session = Depends(get_db),
):
    q = db.query(Paper)
    if status:
        q = q.filter(Paper.status == status)
    total = q.count()
    papers = q.order_by(Paper.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"total": total, "page": page, "size": size, "items": papers}


@router.delete("/papers/{paper_id}")
def admin_delete_paper(
    paper_id: int,
    admin: User = Depends(_require_admin), db: Session = Depends(get_db),
):
    paper = db.query(Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    # 先删除关联的任务和日志
    task_ids = [t.id for t in db.query(Task).filter(Task.paper_id == paper_id).all()]
    if task_ids:
        db.query(AgentLog).filter(AgentLog.task_id.in_(task_ids)).delete(synchronize_session=False)
        db.query(Task).filter(Task.paper_id == paper_id).delete(synchronize_session=False)
    # 再删除论文
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
def list_logs(
    user_id: int = Query(None), paper_id: int = Query(None),
    level: str = Query(None, regex="^(info|warn|error)$"),
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    admin: User = Depends(_require_admin), db: Session = Depends(get_db),
):
    q = db.query(AgentLog)
    # 如果有 paper_id 筛选，通过 Task 表关联
    if paper_id:
        task_ids = [t.id for t in db.query(Task).filter(Task.paper_id == paper_id).all()]
        if task_ids:
            q = q.filter(AgentLog.task_id.in_(task_ids))
        else:
            q = q.filter(False)
    if user_id:
        # 通过 paper -> task 关联筛选用户相关的日志
        user_paper_ids = [p.id for p in db.query(Paper).filter(Paper.user_id == user_id).all()]
        if user_paper_ids:
            user_task_ids = [t.id for t in db.query(Task).filter(Task.paper_id.in_(user_paper_ids)).all()]
            if user_task_ids:
                q = q.filter(AgentLog.task_id.in_(user_task_ids))
            else:
                q = q.filter(False)
    if level:
        q = q.filter(AgentLog.level == level)
    total = q.count()
    logs = q.order_by(AgentLog.id.desc()).offset((page - 1) * size).limit(size).all()
    return {"total": total, "page": page, "size": size, "items": logs}
