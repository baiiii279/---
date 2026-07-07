import os
import tempfile
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.format_template import FormatTemplate
from app.models.user import User
from app.api.auth import get_current_user
from app.services.template_parser import parse_template, rules_to_text

router = APIRouter(prefix="/api/format-templates", tags=["format-templates"])


@router.get("")
def list_templates(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """获取当前用户可用模板（自己的 + 默认模板）"""
    templates = db.query(FormatTemplate).filter(
        (FormatTemplate.user_id == current_user.id) | (FormatTemplate.is_default == True)
    ).order_by(FormatTemplate.is_default.desc(), FormatTemplate.created_at.desc()).all()
    return [{"id": t.id, "name": t.name, "is_default": t.is_default, "created_at": str(t.created_at)[:19]} for t in templates]


@router.post("/upload")
def upload_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传docx模板，自动解析格式规则"""
    if not file.filename.endswith('.docx'):
        raise HTTPException(status_code=400, detail="仅支持 .docx 文件")
    # 保存临时文件
    suffix = '.docx'
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name
    try:
        rules_dict = parse_template(tmp_path)
        rules_text = rules_to_text(rules_dict)
        template = FormatTemplate(
            user_id=current_user.id,
            name=name,
            rules=rules_text,
            is_default=False,
        )
        db.add(template)
        db.commit()
        db.refresh(template)
        return {"id": template.id, "name": template.name, "rules": rules_text, "created_at": str(template.created_at)[:19]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"模板解析失败: {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = db.query(FormatTemplate).filter(
        FormatTemplate.id == template_id,
        FormatTemplate.user_id == current_user.id,
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权删除")
    if template.is_default:
        raise HTTPException(status_code=400, detail="不能删除默认模板")
    db.delete(template)
    db.commit()
    return {"message": "ok"}
