from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.config import assert_production_safe, settings
from backend.routers import resume, jobs, match, users, agent, interview, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast on insecure SECRET_KEY / wildcard CORS when not in DEBUG.
    assert_production_safe()
    # Database schema is managed by Alembic (see backend/alembic). Do NOT call
    # Base.metadata.create_all here — that would bypass migrations.
    yield
    print("🛑 Application shutdown.")


app = FastAPI(
    title="Career Platform API",
    description="AI-powered career assistant — job search, resume analysis, semantic matching",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — restricted to the configured allow-list (no wildcard in production).
_cors_origins = settings.parse_cors_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(users.router)
app.include_router(resume.router)
app.include_router(jobs.router)
app.include_router(match.router)
app.include_router(agent.router)
app.include_router(interview.router)
app.include_router(auth.router)

@app.get("/")
def health():
    return {"status": "healthy"}
