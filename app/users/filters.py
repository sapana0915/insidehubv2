from typing import Optional
from pydantic import BaseModel


class UserFilter(BaseModel):
    """Filter parameters for user list"""
    email: Optional[str] = None
    username: Optional[str] = None
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None
