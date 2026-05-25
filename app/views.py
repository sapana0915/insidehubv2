from typing import List, Optional, Dict, Any, Type
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from app.database import get_db
from app.middleware.request import get_request_wrapper, RequestWrapper
from app.core.exceptions import ForbiddenException
from sqlalchemy.orm import Session


class ModelViewSet:
    """
    Base class-based view similar to Django's ModelViewSet.
    Automatically provides CRUD endpoints.
    """

    schema: Type[BaseModel]
    create_schema: Optional[Type[BaseModel]] = None
    service = None
    tags: List[str] = []
    permissions: Dict[str, List[str]] = {}

    def __init__(self):
        self.router = APIRouter(tags=self.tags)
        self._register_routes()

    def _register_routes(self):
        self.router.get("", response_model=List[self.schema])(self.list)
        self.router.get("/{id}", response_model=self.schema)(self.retrieve)
        self.router.post("", response_model=self.schema)(self.create)
        self.router.put("/{id}", response_model=self.schema)(self.update)
        self.router.patch("/{id}", response_model=self.schema)(self.partial_update)
        self.router.delete("/{id}")(self.destroy)

    def _check_permission(self, action: str, request: RequestWrapper):
        """Check if user has permission for action"""
        required_permissions = self.permissions.get(action, [])
        if not required_permissions:
            return

        user_role = request.get_user_role()
        if user_role not in required_permissions:
            raise ForbiddenException(f"Not permitted to {action}")

    async def list(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        request: RequestWrapper = Depends(get_request_wrapper),
        db: Session = Depends(get_db),
    ) -> List[Dict[str, Any]]:
        self._check_permission("list", request)
        return await self.service.list(db, skip=skip, limit=limit)

    async def retrieve(
        self,
        id: int,
        request: RequestWrapper = Depends(get_request_wrapper),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        self._check_permission("retrieve", request)
        return await self.service.get(db, id)

    async def create(
        self,
        data: BaseModel,
        request: RequestWrapper = Depends(get_request_wrapper),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        self._check_permission("create", request)
        schema = self.create_schema or self.schema
        return await self.service.create(db, data)

    async def update(
        self,
        id: int,
        data: BaseModel,
        request: RequestWrapper = Depends(get_request_wrapper),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        self._check_permission("update", request)
        return await self.service.update(db, id, data)

    async def partial_update(
        self,
        id: int,
        data: BaseModel,
        request: RequestWrapper = Depends(get_request_wrapper),
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        self._check_permission("update", request)
        return await self.service.partial_update(db, id, data)

    async def destroy(
        self,
        id: int,
        request: RequestWrapper = Depends(get_request_wrapper),
        db: Session = Depends(get_db),
    ) -> Dict[str, str]:
        self._check_permission("delete", request)
        await self.service.delete(db, id)
        return {"message": "Deleted successfully"}
