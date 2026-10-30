from typing import Any, ClassVar, Dict, Optional
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Query

from app.core.filters import BaseFilter


class PostFilter(BaseFilter):
    """Filter parameters for post list."""

    _lookups: ClassVar[Dict[str, str]] = {
        "title": "icontains",
        "category": "eq",
    }

    title: Optional[str] = None
    category: Optional[str] = None
    author_id: Optional[UUID] = None
    search: Optional[str] = None

    def apply(self, query: Query, model: Any) -> Query:
        query = super().apply(query, model)
        if self.search:
            term = f"%{self.search.strip()}%"
            query = query.filter(or_(model.title.ilike(term), model.content.ilike(term)))
        return query
