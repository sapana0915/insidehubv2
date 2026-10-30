from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import hash_password, verify_password
from .models import User
from .repositories import UserRepository
from .schemas import UserCreate, UserUpdate


class UserService:
    model = User

    @staticmethod
    def get(db: Session, user_id: UUID) -> User:
        return UserRepository.get_by_id(db, user_id)

    @staticmethod
    def list(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        filters: Any = None,
        request: Any = None,
        viewset: Any = None,
    ) -> list:
        query = db.query(User)
        if filters:
            query = filters.apply(query, User)
        if viewset and viewset.scope_list_to_owner(request):
            column = getattr(User, viewset.owner_field)
            uid = viewset._get_user_id(request)
            query = query.filter(column == uid)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, user_data: UserCreate) -> User:
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
    def update(db: Session, user_id: UUID, user_data: UserUpdate) -> User:
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
    def partial_update(db: Session, user_id: UUID, user_data: UserUpdate) -> User:
        return UserService.update(db, user_id, user_data)

    @staticmethod
    def delete(db: Session, user_id: UUID) -> None:
        UserRepository.delete(db, user_id)

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User:
        user = UserRepository.get_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid credentials")
        if not user.is_active:
            raise UnauthorizedException("User is inactive")
        return user
