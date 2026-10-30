from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException

from .models import Post, PostImage


class PostRepository:
    @staticmethod
    def get_by_id(db: Session, post_id: UUID) -> Post:
        post = (
            db.query(Post)
            .options(selectinload(Post.images), selectinload(Post.author))
            .filter(Post.id == post_id)
            .first()
        )
        if not post:
            raise NotFoundException("Post")
        return post

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 10) -> list:
        return (
            db.query(Post)
            .options(selectinload(Post.images), selectinload(Post.author))
            .order_by(Post.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    @staticmethod
    def create(db: Session, post: Post) -> Post:
        db.add(post)
        db.commit()
        db.refresh(post)
        return PostRepository.get_by_id(db, post.id)

    @staticmethod
    def update(db: Session, post: Post) -> Post:
        db.commit()
        db.refresh(post)
        return PostRepository.get_by_id(db, post.id)

    @staticmethod
    def delete(db: Session, post_id: UUID) -> None:
        post = PostRepository.get_by_id(db, post_id)
        db.delete(post)
        db.commit()

    @staticmethod
    def replace_images(
        db: Session,
        post: Post,
        image_urls: list[str],
        user_id: UUID,
    ) -> None:
        post.images.clear()
        for url in image_urls:
            post.images.append(
                PostImage(image_url=url, user_id=user_id)
            )
