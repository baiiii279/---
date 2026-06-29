from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.models import user, paper, reference, task, agent_log
from app.api import auth, user as user_router
from app.api import references
from app.api import papers
from app.api import agent, admin

app = FastAPI(title="PaperCraft API")

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


@app.on_event("startup")
def init_db():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
