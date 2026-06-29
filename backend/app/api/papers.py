from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.paper import Paper
from app.models.reference import PaperReference
from app.models.user import User
from app.schemas.paper import CreatePaperRequest, PaperResponse, UpdatePaperRequest
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("", response_model=PaperResponse)
def create_paper(req: CreatePaperRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = Paper(user_id=current_user.id, topic=req.topic, template=req.template)
    db.add(paper)
    db.flush()

    for ref_id in req.reference_ids:
        db.add(PaperReference(paper_id=paper.id, reference_id=ref_id))

    db.commit()
    db.refresh(paper)
    return paper


@router.get("", response_model=list[PaperResponse])
def list_papers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Paper).filter(Paper.user_id == current_user.id).order_by(Paper.created_at.desc()).all()


@router.get("/{paper_id}", response_model=PaperResponse)
def get_paper(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    return paper


@router.put("/{paper_id}")
def update_paper(paper_id: int, req: UpdatePaperRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    if req.title is not None:
        paper.title = req.title
    if req.outline is not None:
        paper.outline = req.outline
    if req.content is not None:
        paper.content = req.content
    db.commit()
    return {"message": "ok"}


@router.delete("/{paper_id}")
def delete_paper(paper_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id, Paper.user_id == current_user.id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    db.delete(paper)
    db.commit()
    return {"message": "ok"}
