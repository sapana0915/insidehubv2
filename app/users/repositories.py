from uuid import UUID

from sqlalchemy.orm import Session
from .models import User
from app.core.exceptions import NotFoundException


class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise NotFoundException("User")
        return user

    @staticmethod
    def get_by_email(db: Session, email: str) -> User:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> User:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 10) -> list:
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User) -> User:
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user_id: UUID) -> None:
        user = UserRepository.get_by_id(db, user_id)
        db.delete(user)
        db.commit()
