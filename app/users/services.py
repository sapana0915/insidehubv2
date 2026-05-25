from sqlalchemy.orm import Session
from .repositories import UserRepository
from .models import User
from .schemas import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password
from app.core.exceptions import ConflictException, UnauthorizedException


class UserService:
    @staticmethod
    async def get(db: Session, user_id: int) -> User:
        return UserRepository.get_by_id(db, user_id)

    @staticmethod
    async def list(db: Session, skip: int = 0, limit: int = 10) -> list:
        return UserRepository.list_all(db, skip=skip, limit=limit)

    @staticmethod
    async def create(db: Session, user_data: UserCreate) -> User:
        existing_user = UserRepository.get_by_email(db, user_data.email)
        if existing_user:
            raise ConflictException("Email already registered")

        existing_username = UserRepository.get_by_username(db, user_data.username)
        if existing_username:
            raise ConflictException("Username already taken")

        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            hashed_password=hash_password(user_data.password),
        )
        return UserRepository.create(db, user)

    @staticmethod
    async def update(db: Session, user_id: int, user_data: UserUpdate) -> User:
        user = UserRepository.get_by_id(db, user_id)

        if user_data.email and user_data.email != user.email:
            existing = UserRepository.get_by_email(db, user_data.email)
            if existing:
                raise ConflictException("Email already registered")
            user.email = user_data.email

        if user_data.username and user_data.username != user.username:
            existing = UserRepository.get_by_username(db, user_data.username)
            if existing:
                raise ConflictException("Username already taken")
            user.username = user_data.username

        if user_data.full_name:
            user.full_name = user_data.full_name

        if user_data.password:
            user.hashed_password = hash_password(user_data.password)

        return UserRepository.update(db, user)

    @staticmethod
    async def partial_update(db: Session, user_id: int, user_data: UserUpdate) -> User:
        return await UserService.update(db, user_id, user_data)

    @staticmethod
    async def delete(db: Session, user_id: int) -> None:
        UserRepository.delete(db, user_id)

    @staticmethod
    async def authenticate(db: Session, email: str, password: str) -> User:
        user = UserRepository.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        if not user.is_active:
            raise UnauthorizedException("User is inactive")
        return user
