from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

from .constants import CATEGORY_SLUGS

MAX_IMAGES_PER_POST = 12


def _validate_category(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    slug = value.strip().lower()
    if slug not in CATEGORY_SLUGS:
        raise ValueError(f"category must be one of: {', '.join(sorted(CATEGORY_SLUGS))}")
    return slug


class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    category: str

    @field_validator("category")
    @classmethod
    def check_category(cls, value: str) -> str:
        return _validate_category(value)


class PostCreate(PostBase):
    author_id: Optional[UUID] = None
    images: Optional[List[str]] = Field(default=None, max_length=MAX_IMAGES_PER_POST)


class PostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)
    category: Optional[str] = None
    images: Optional[List[str]] = Field(default=None, max_length=MAX_IMAGES_PER_POST)

    @field_validator("category")
    @classmethod
    def check_category(cls, value: Optional[str]) -> Optional[str]:
        return _validate_category(value)


class PostImageResponse(BaseModel):
    id: UUID
    image_url: str
    user_id: UUID

    class Config:
        from_attributes = True


class PostAuthor(BaseModel):
    id: UUID
    username: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: UUID
    title: str
    content: str
    category: str
    author_id: UUID
    author: Optional[PostAuthor] = None
    images: List[PostImageResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    slug: str
    name: str
    description: str


class UploadResponse(BaseModel):
    url: str
