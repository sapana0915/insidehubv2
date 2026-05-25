from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class Permission(str, Enum):
    AUTHENTICATED = "AUTHENTICATED"
    ADMIN = "ADMIN"
    USER = "USER"
    GUEST = "GUEST"
