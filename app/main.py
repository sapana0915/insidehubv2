from pathlib import Path

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.middleware.error_handler import setup_exception_handlers
from app.posts.routers import router as posts_router
from app.posts.views import PostViewSet
from app.users.routers import router as users_router
from app.users.views import UserViewSet

app = FastAPI(
    title="InsideHub API",
    description="Blogs, photos and travel stories, organised by category.",
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

# Explicit routers go first so paths like /users/me and /posts/categories
# are matched before the viewsets' /{id} routes.
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(posts_router, prefix=settings.API_V1_STR)
app.include_router(UserViewSet().router, prefix=f"{settings.API_V1_STR}/users")
app.include_router(PostViewSet().router, prefix=f"{settings.API_V1_STR}/posts")

Path(settings.MEDIA_DIR).mkdir(parents=True, exist_ok=True)
app.mount(settings.MEDIA_URL, StaticFiles(directory=settings.MEDIA_DIR), name="media")


@app.get("/")
def root():
    return {
        "message": "Welcome to the InsideHub",
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
