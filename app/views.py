import inspect
from typing import Any, Dict, List, Optional, Type

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, create_model
from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenException, NotFoundException
from app.core.filters import BaseFilter
from app.database import get_db
from app.middleware.request import RequestWrapper, get_request_wrapper


class ModelViewSet:
    """
    Class-based CRUD views (Django ModelViewSet-style).
    Sync handlers; schemas bound per subclass for body validation.
    """

    schema: Type[BaseModel]
    create_schema: Optional[Type[BaseModel]] = None
    update_schema: Optional[Type[BaseModel]] = None
    filter_class: Optional[Type[BaseFilter]] = None
    service = None
    model = None
    tags: List[str] = []
    permissions: Dict[str, List[str]] = {}
    owner_field: Optional[str] = None

    def __init__(self):
        self.router = APIRouter(tags=self.tags)
        self._register_routes()

    def _register_routes(self):
        self.router.add_api_route("", self._make_list(), methods=["GET"], response_model=List[self.schema])
        self.router.add_api_route("/{id}", self._make_retrieve(), methods=["GET"], response_model=self.schema)
        self.router.add_api_route("", self._make_create(), methods=["POST"], response_model=self.schema)
        self.router.add_api_route("/{id}", self._make_update(), methods=["PUT"], response_model=self.schema)
        self.router.add_api_route("/{id}", self._make_partial_update(), methods=["PATCH"], response_model=self.schema)
        self.router.add_api_route("/{id}", self._make_destroy(), methods=["DELETE"])

    def _normalize_role(self, role: Optional[str]) -> str:
        return (role or "").strip().lower()

    def _is_admin(self, request: RequestWrapper) -> bool:
        return self._normalize_role(request.get_user_role()) == "admin"

    def _check_permission(self, action: str, request: RequestWrapper):
        required = self.permissions.get(action, [])
        if not required:
            return
        if request._user is None:
            raise ForbiddenException(f"Not permitted to {action}")
        user_role = self._normalize_role(request.get_user_role())
        for perm in required:
            key = perm.strip().upper()
            if key == "AUTHENTICATED":
                return
            if key.lower() == user_role:
                return
        raise ForbiddenException(f"Not permitted to {action}")

    def _get_user_id(self, request: RequestWrapper) -> int:
        payload = request.user
        uid = payload.get("user_id") or payload.get("sub")
        return int(uid)

    def _get_owned_or_404(self, db: Session, obj_id: int, request: RequestWrapper):
        obj = self.service.get(db, obj_id)
        if (
            self.owner_field
            and self.model
            and not self._is_admin(request)
            and getattr(obj, self.owner_field, None) != self._get_user_id(request)
        ):
            raise NotFoundException(self.model.__name__)
        return obj

    def _stamp_owner(self, data: BaseModel, request: RequestWrapper) -> BaseModel:
        if not self.owner_field:
            return data
        payload = data.model_dump()
        payload[self.owner_field] = self._get_user_id(request)
        return data.__class__(**payload)

    def _make_list(self):
        viewset = self
        FilterModel = self._filter_query_model()

        if FilterModel is not None:

            def list_items(
                skip: int = Query(0, ge=0),
                limit: int = Query(10, ge=1, le=100),
                filters: FilterModel = Depends(),  # type: ignore[valid-type]
                request: RequestWrapper = Depends(get_request_wrapper),
                db: Session = Depends(get_db),
            ):
                viewset._check_permission("list", request)
                raw = filters.model_dump(exclude_unset=True)
                cleaned = {k: v for k, v in raw.items() if v is not None}
                filter_obj = viewset.filter_class(**cleaned) if cleaned else None
                return viewset.service.list(
                    db,
                    skip=skip,
                    limit=limit,
                    filters=filter_obj,
                    request=request,
                    viewset=viewset,
                )

            return list_items

        def list_items(
            skip: int = Query(0, ge=0),
            limit: int = Query(10, ge=1, le=100),
            request: RequestWrapper = Depends(get_request_wrapper),
            db: Session = Depends(get_db),
        ):
            viewset._check_permission("list", request)
            return viewset.service.list(
                db,
                skip=skip,
                limit=limit,
                filters=None,
                request=request,
                viewset=viewset,
            )

        return list_items

    def _filter_query_model(self) -> Optional[Type[BaseModel]]:
        if not self.filter_class:
            return None
        fields = {}
        for name, field in self.filter_class.model_fields.items():
            annotation = Optional[field.annotation]  # type: ignore[valid-type]
            fields[name] = (annotation, None)
        return create_model(f"{self.__class__.__name__}QueryParams", **fields)

    def _make_retrieve(self):
        viewset = self

        def retrieve(
            id: int,
            request: RequestWrapper = Depends(get_request_wrapper),
            db: Session = Depends(get_db),
        ):
            viewset._check_permission("retrieve", request)
            return viewset._get_owned_or_404(db, id, request)

        return retrieve

    def _make_create(self):
        viewset = self
        BodySchema = self.create_schema or self.schema

        def create(
            data: BodySchema,  # type: ignore[valid-type]
            request: RequestWrapper = Depends(get_request_wrapper),
            db: Session = Depends(get_db),
        ):
            viewset._check_permission("create", request)
            stamped = viewset._stamp_owner(data, request)
            return viewset.service.create(db, stamped)

        create.__annotations__["data"] = BodySchema
        return create

    def _make_update(self):
        viewset = self
        BodySchema = self.update_schema or self.create_schema or self.schema

        def update(
            id: int,
            data: BodySchema,  # type: ignore[valid-type]
            request: RequestWrapper = Depends(get_request_wrapper),
            db: Session = Depends(get_db),
        ):
            viewset._check_permission("update", request)
            viewset._get_owned_or_404(db, id, request)
            return viewset.service.update(db, id, data)

        update.__annotations__["data"] = BodySchema
        return update

    def _make_partial_update(self):
        viewset = self
        BodySchema = self.update_schema or self.create_schema or self.schema

        def partial_update(
            id: int,
            data: BodySchema,  # type: ignore[valid-type]
            request: RequestWrapper = Depends(get_request_wrapper),
            db: Session = Depends(get_db),
        ):
            viewset._check_permission("update", request)
            viewset._get_owned_or_404(db, id, request)
            return viewset.service.partial_update(db, id, data)

        partial_update.__annotations__["data"] = BodySchema
        return partial_update

    def _make_destroy(self):
        viewset = self

        def destroy(
            id: int,
            request: RequestWrapper = Depends(get_request_wrapper),
            db: Session = Depends(get_db),
        ):
            viewset._check_permission("delete", request)
            viewset._get_owned_or_404(db, id, request)
            viewset.service.delete(db, id)
            return {"message": "Deleted successfully"}

        return destroy
