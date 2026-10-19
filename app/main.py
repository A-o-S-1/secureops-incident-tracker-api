from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.config import settings
from app.routers import auth, users, incidents, audit

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alembic is the recommended schema-management path. This fallback makes first-run demos easy.
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="SecureOps Incident Tracker API",
    description="A learning-oriented API for recording and managing synthetic security incidents. It does not detect attacks.",
    version="1.0.0",
    lifespan=lifespan,
)
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["GET","POST","PATCH"], allow_headers=["Authorization","Content-Type"])

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(incidents.router)
app.include_router(audit.router)
