import os
import re
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.reference import UserReference
from app.models.user import User
from app.schemas.reference import ReferenceRequest, ReferenceResponse
from sqlalchemy import text
from app.api.auth import get_current_user

router = APIRouter(prefix="/api/user/references", tags=["references"])

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "references"


def _ensure_upload_dir(user_id: int) -> Path:
    d = UPLOAD_DIR / str(user_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _extract_text_docx(path: Path) -> str:
    from docx import Document
    doc = Document(str(path))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _extract_text_pdf(path: Path) -> str:
    import pdfplumber
    with pdfplumber.open(str(path)) as pdf:
        pages = [p.extract_text() for p in pdf.pages if p.extract_text()]
    return "\n".join(pages)


def _parse_title(text: str) -> str:
    """取第一段非空行作为标题，最多 100 字符"""
    for line in text.strip().splitlines():
        line = line.strip()
        if line and len(line) > 3:
            return line[:100]
    return "未命名文献"


def _parse_abstract(text: str, title: str) -> str:
    """去掉标题行后取前 500 字符作为摘要"""
    body = text.strip()
    if body.startswith(title):
        body = body[len(title):].strip()
    return body[:500] if body else ""


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}


@router.get("", response_model=list[ReferenceResponse])
def list_references(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UserReference).filter(UserReference.user_id == current_user.id).all()


@router.get("/{ref_id}", response_model=ReferenceResponse)
def get_reference(ref_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(UserReference).filter(UserReference.id == ref_id, UserReference.user_id == current_user.id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="文献不存在")
    return ref


@router.post("", response_model=ReferenceResponse)
def create_reference(req: ReferenceRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = UserReference(user_id=current_user.id, **req.model_dump())
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


@router.post("/upload", response_model=ReferenceResponse)
def upload_reference(file: UploadFile = File(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件格式: {ext}，仅支持 PDF、Word、TXT")

    user_dir = _ensure_upload_dir(current_user.id)
    file_path = user_dir / f"{Path(file.filename).stem}_{os.urandom(4).hex()}{ext}"

    content_bytes = file.file.read()
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    # 提取文本
    text = ""
    if ext == ".pdf":
        text = _extract_text_pdf(file_path)
    elif ext in (".docx", ".doc"):
        if ext == ".doc":
            try:
                text = _extract_text_docx(file_path)
            except Exception:
                text = ""
        else:
            text = _extract_text_docx(file_path)
    elif ext == ".txt":
        text = content_bytes.decode("utf-8", errors="replace")

    title = _parse_title(text) if text else file.filename
    abstract = _parse_abstract(text, title) if text else ""

    # 确保 full_text 列存在
    try:
        db.execute(text("ALTER TABLE user_references ADD COLUMN full_text LONGTEXT NULL"))
        db.commit()
    except Exception:
        db.rollback()

    ref = UserReference(
        user_id=current_user.id,
        title=title,
        abstract=abstract or None,
        full_text=text or None,
        url=str(file_path),
    )
    db.add(ref)
    db.commit()
    db.refresh(ref)
    return ref


@router.delete("/{ref_id}")
def delete_reference(ref_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ref = db.query(UserReference).filter(UserReference.id == ref_id, UserReference.user_id == current_user.id).first()
    if not ref:
        raise HTTPException(status_code=404, detail="文献不存在")
    if ref.url and os.path.isfile(ref.url):
        os.remove(ref.url)
    db.delete(ref)
    db.commit()
    return {"message": "ok"}
