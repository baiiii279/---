from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.models import user, paper, reference, task, agent_log, format_template
from app.api import auth, user as user_router
from app.api import references
from app.api import papers
from app.api import agent, admin
from app.api import format_templates

from app.core.security import hash_password

from app.core.security import hash_password

app = FastAPI(title="PaperCraft API")

def _seed_admin():
    """自动创建默认管理员账号"""
    from app.core.database import SessionLocal
    from app.models.user import User
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            if existing.role != "admin":
                existing.role = "admin"
                db.commit()
                print("[init] 已有用户 admin 已提升为管理员")
            return
        db.add(User(username="admin", password_hash=hash_password("admin123"), role="admin"))
        db.commit()
        print("[init] 默认管理员已创建: admin / admin123")
    finally:
        db.close()

def _seed_default_template():
    """创建默认格式模板"""
    from app.core.database import SessionLocal
    from app.models.format_template import FormatTemplate
    from app.services.template_parser import get_default_rules
    db = SessionLocal()
    try:
        existing = db.query(FormatTemplate).filter(FormatTemplate.is_default == True).first()
        if existing:
            return
        db.add(FormatTemplate(
            user_id=None, name="嘉庚学院标准",
            rules=get_default_rules(),
            is_default=True,
        ))
        db.commit()
        print("[init] 默认格式模板已创建: 嘉庚学院标准")
    finally:
        db.close()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(user_router.router)
app.include_router(references.router)
app.include_router(papers.router)
app.include_router(agent.router)
app.include_router(admin.router)
app.include_router(format_templates.router)


@app.on_event("startup")
def init_db():
    Base.metadata.create_all(bind=engine)
    _seed_admin()
    _seed_default_template()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
