from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.constants import UserRole
from app.core.security import create_access_token
from app.database import get_db
from app.middleware.request import RequestWrapper, get_request_wrapper
from app.posts.models import Post
from .schemas import PublicUserResponse, Token, UserCreate, UserLogin, UserResponse, UserUpdate
from .services import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user."""
    return UserService.create(db, user_data)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user and get access token."""
    user = UserService.authenticate(db, credentials.email, credentials.password)
    role = UserRole.ADMIN.value if user.is_admin else UserRole.USER.value
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "user_id": str(user.id),
            "email": user.email,
            "role": role,
        },
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def read_me(
    request: RequestWrapper = Depends(get_request_wrapper),
    db: Session = Depends(get_db),
):
    """Get the currently authenticated user."""
    return UserService.get(db, request.get_user_id())


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserUpdate,
    request: RequestWrapper = Depends(get_request_wrapper),
    db: Session = Depends(get_db),
):
    """Update the currently authenticated user."""
    return UserService.partial_update(db, request.get_user_id(), data)


@router.get("/{user_id}/profile", response_model=PublicUserResponse)
def read_profile(user_id: UUID, db: Session = Depends(get_db)):
    """Public profile of a user (no email or account flags)."""
    user = UserService.get(db, user_id)
    post_count = db.query(func.count(Post.id)).filter(Post.author_id == user.id).scalar() or 0
    return PublicUserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        created_at=user.created_at,
        post_count=post_count,
    )
