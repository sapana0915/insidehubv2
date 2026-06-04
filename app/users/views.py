from app.views import ModelViewSet
from .filters import UserFilter
from .models import User
from .schemas import UserCreate, UserResponse, UserUpdate
from .services import UserService


class UserViewSet(ModelViewSet):
    schema = UserResponse
    create_schema = UserCreate
    update_schema = UserUpdate
    filter_class = UserFilter
    service = UserService
    model = User
    tags = ["users-crud"]

    permissions = {
        "list": ["AUTHENTICATED", "ADMIN"],
        "retrieve": ["AUTHENTICATED"],
        "create": ["ADMIN"],
        "update": ["AUTHENTICATED"],
        "delete": ["ADMIN"],
    }
