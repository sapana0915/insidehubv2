from app.views import ModelViewSet

from .filters import PostFilter
from .models import Post
from .schemas import PostCreate, PostResponse, PostUpdate
from .services import PostService


class PostViewSet(ModelViewSet):
    schema = PostResponse
    create_schema = PostCreate
    update_schema = PostUpdate
    filter_class = PostFilter
    service = PostService
    model = Post
    tags = ["posts-crud"]
    owner_field = "author_id"
    owner_actions = ("update", "delete")

    permissions = {
        "list": [],
        "retrieve": [],
        "create": ["AUTHENTICATED"],
        "update": ["AUTHENTICATED"],
        "delete": ["AUTHENTICATED", "ADMIN"],
    }
