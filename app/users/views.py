from app.views import ModelViewSet
from .schemas import UserResponse, UserCreate, UserUpdate
from .services import UserService


class UserViewSet(ModelViewSet):
    schema = UserResponse
    create_schema = UserCreate
    service = UserService
    tags = ["users"]

    permissions = {
        "list": ["AUTHENTICATED", "ADMIN"],
        "retrieve": ["AUTHENTICATED"],
        "create": [],  # Public registration
        "update": ["AUTHENTICATED"],
        "delete": ["ADMIN"],
    }
