from typing import Any, ClassVar, Dict, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Query


class BaseFilter(BaseModel):
    """Turns set filter fields into SQLAlchemy WHERE clauses."""

    _lookups: ClassVar[Dict[str, str]] = {}

    def apply(self, query: Query, model: Any) -> Query:
        for field_name, value in self.model_dump(exclude_unset=True).items():
            if value is None:
                continue
            if not hasattr(model, field_name):
                continue
            column = getattr(model, field_name)
            lookup = self._lookups.get(field_name, "eq")
            query = self._apply_lookup(query, column, lookup, value)
        return query

    @staticmethod
    def _apply_lookup(query: Query, column: Any, lookup: str, value: Any) -> Query:
        if lookup == "eq":
            return query.filter(column == value)
        if lookup == "icontains":
            return query.filter(column.ilike(f"%{value}%"))
        if lookup == "gte":
            return query.filter(column >= value)
        if lookup == "lte":
            return query.filter(column <= value)
        if lookup == "in":
            return query.filter(column.in_(value))
        return query.filter(column == value)
