from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.middleware.error_handler import setup_exception_handlers
from app.users.routers import router as users_router
from app.users.views import UserViewSet

app = FastAPI(
    title="FastAPI Boilerplate",
    description="A production-ready FastAPI boilerplate",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(UserViewSet().router, prefix=f"{settings.API_V1_STR}/users")


@app.get("/")
def root():
    return {
        "message": "Welcome to FastAPI Boilerplate",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    checks = {"database": False, "redis": False}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    try:
        import redis

        client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        checks["redis"] = client.ping()
    except Exception:
        pass

    healthy = all(checks.values())
    body = {"status": "healthy" if healthy else "unhealthy", "checks": checks}
    if not healthy:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=body)
    return body
