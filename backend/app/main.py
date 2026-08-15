"""
FastAPI application entry point for the AI-PR Review Agent.
"""
from contextlib import asynccontextmanager
# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
from app.api import health_router, webhooks_router, hitl_router, reviews_router
from app.database.postgres import init_tiger_schema, close_db_connection
from app.core.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager.
    - Startup: initialize database schema (runs migrations).
    - Shutdown: gracefully close DB connections.
    """
    # Startup
    print("🚀 Starting AI-PR Review Agent...")
    await init_tiger_schema()
    print("✅ Database initialized")
    yield  # Application runs here
    # Shutdown
    await close_db_connection()
    print("👋 Database connections closed")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware — in production, restrict to your frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(webhooks_router)
app.include_router(hitl_router)
app.include_router(reviews_router)


# Optional: root endpoint
@app.get("/")
async def root():
    return {"message": "AI-PR Review Agent API", "docs": "/docs"}