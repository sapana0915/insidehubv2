from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.middleware.error_handler import setup_exception_handlers
from app.users.routers import router as users_router
from app.database import Base, engine

# Create tables
Base.metadata.create_all(bind=engine)

# Initialize app
app = FastAPI(
    title="FastAPI Boilerplate",
    description="A production-ready FastAPI boilerplate",
    version="1.0.0",
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include routers
app.include_router(users_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {
        "message": "Welcome to FastAPI Boilerplate",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
