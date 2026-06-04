from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.constants import UserRole
from app.core.security import create_access_token
from app.database import get_db
from .schemas import Token, UserCreate, UserLogin, UserResponse
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
            "user_id": user.id,
            "email": user.email,
            "role": role,
        },
    )
    return {"access_token": access_token, "token_type": "bearer"}
