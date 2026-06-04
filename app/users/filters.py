from typing import ClassVar, Dict, Optional

from app.core.filters import BaseFilter


class UserFilter(BaseFilter):
    """Filter parameters for user list."""

    _lookups: ClassVar[Dict[str, str]] = {
        "email": "icontains",
        "username": "icontains",
    }

    email: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
