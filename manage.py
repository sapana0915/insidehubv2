#!/usr/bin/env python
"""
FastAPI management CLI tool for database migrations, app creation, and other utilities.
Similar to Django's manage.py
"""
import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from alembic.config import Config
from alembic import command
from app.database import engine, Base
from app.core.config import settings


def init_alembic():
    """Initialize Alembic if not already initialized."""
    alembic_dir = Path("alembic")
    if not alembic_dir.exists():
        print("Initializing Alembic...")
        command.init(Config(), "alembic")
        print("✓ Alembic initialized")


def makemigrations(args):
    """Create a new migration file."""
    message = args.message or "auto"
    print(f"Creating migration: {message}")

    try:
        init_alembic()
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.revision(config, autogenerate=True, message=message)
        print(f"✓ Migration created: {message}")
    except Exception as e:
        print(f"✗ Error creating migration: {e}")
        sys.exit(1)


def migrate(args):
    """Run pending migrations."""
    print("Running migrations...")

    try:
        init_alembic()
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

        # Get the revision to migrate to (default: head)
        revision = args.revision or "head"
        command.upgrade(config, revision)
        print(f"✓ Migrations applied up to: {revision}")
    except Exception as e:
        print(f"✗ Error running migrations: {e}")
        sys.exit(1)


def migrate_down(args):
    """Rollback to a previous migration."""
    revision = args.revision or "-1"
    print(f"Rolling back to: {revision}")

    try:
        init_alembic()
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.downgrade(config, revision)
        print(f"✓ Rolled back to: {revision}")
    except Exception as e:
        print(f"✗ Error rolling back: {e}")
        sys.exit(1)


def create_app(args):
    """Create a new feature app."""
    app_name = args.name

    if not app_name:
        print("✗ App name is required")
        sys.exit(1)

    app_dir = Path(f"app/{app_name}")

    if app_dir.exists():
        print(f"✗ App '{app_name}' already exists")
        sys.exit(1)

    # Create app directory
    app_dir.mkdir(parents=True)
    (app_dir / "__init__.py").touch()

    # Create all required files
    files = {
        "models.py": '''from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class {ModelClass}(Base):
    __tablename__ = "{table_name}"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
''',
        "schemas.py": '''from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class {ModelClass}Base(BaseModel):
    name: str


class {ModelClass}Create({ModelClass}Base):
    pass


class {ModelClass}Update(BaseModel):
    name: Optional[str] = None


class {ModelClass}Response({ModelClass}Base):
    model_config = ConfigDict(from_attributes=True)

    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
''',
        "repositories.py": '''from sqlalchemy.orm import Session
from .models import {ModelClass}


class {ModelClass}Repository:
    """Database access layer for {ModelClass}."""

    @staticmethod
    def get_by_id(db: Session, id: int) -> {ModelClass}:
        return db.query({ModelClass}).filter({ModelClass}.id == id).first()

    @staticmethod
    def list_all(db: Session, skip: int = 0, limit: int = 100):
        return db.query({ModelClass}).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, obj: {ModelClass}) -> {ModelClass}:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    @staticmethod
    def update(db: Session, db_obj: {ModelClass}, obj_in) -> {ModelClass}:
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def delete(db: Session, id: int) -> bool:
        db_obj = db.query({ModelClass}).filter({ModelClass}.id == id).first()
        if db_obj:
            db.delete(db_obj)
            db.commit()
            return True
        return False
''',
        "services.py": '''from typing import Any

from sqlalchemy.orm import Session

from .models import {ModelClass}
from .repositories import {ModelClass}Repository
from .schemas import {ModelClass}Create, {ModelClass}Update


class {ModelClass}Service:
    model = {ModelClass}

    @staticmethod
    def get(db: Session, id: int):
        return {ModelClass}Repository.get_by_id(db, id)

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 100, filters: Any = None, request: Any = None, viewset: Any = None):
        query = db.query({ModelClass})
        if filters:
            query = filters.apply(query, {ModelClass})
        if viewset and viewset.owner_field and request and not viewset._is_admin(request):
            column = getattr({ModelClass}, viewset.owner_field)
            query = query.filter(column == viewset._get_user_id(request))
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, data: {ModelClass}Create):
        payload = data.model_dump()
        obj = {ModelClass}(**payload)
        return {ModelClass}Repository.create(db, obj)

    @staticmethod
    def update(db: Session, id: int, data: {ModelClass}Update):
        obj = {ModelClass}Repository.get_by_id(db, id)
        return {ModelClass}Repository.update(db, obj, data)

    @staticmethod
    def partial_update(db: Session, id: int, data: {ModelClass}Update):
        return {ModelClass}Service.update(db, id, data)

    @staticmethod
    def delete(db: Session, id: int) -> None:
        {ModelClass}Repository.delete(db, id)
''',
        "filters.py": '''from typing import ClassVar, Dict, Optional

from app.core.filters import BaseFilter


class {ModelClass}Filter(BaseFilter):
    _lookups: ClassVar[Dict[str, str]] = {{"name": "icontains"}}

    name: Optional[str] = None
''',
        "views.py": '''from app.views import ModelViewSet
from .filters import {ModelClass}Filter
from .models import {ModelClass}
from .schemas import {ModelClass}Create, {ModelClass}Response, {ModelClass}Update
from .services import {ModelClass}Service


class {ModelClass}ViewSet(ModelViewSet):
    schema = {ModelClass}Response
    create_schema = {ModelClass}Create
    update_schema = {ModelClass}Update
    filter_class = {ModelClass}Filter
    service = {ModelClass}Service
    model = {ModelClass}
    owner_field = "owner_id"
    tags = ["{app_name}"]

    permissions = {{
        "list": ["AUTHENTICATED"],
        "retrieve": ["AUTHENTICATED"],
        "create": ["AUTHENTICATED"],
        "update": ["AUTHENTICATED"],
        "delete": ["ADMIN"],
    }}
''',
        "routers.py": '''from .views import {ModelClass}ViewSet

router = {ModelClass}ViewSet().router
''',
    }

    # Convert app_name to PascalCase for class name
    model_class = "".join(word.capitalize() for word in app_name.split("_"))
    table_name = app_name.lower()

    # Create files with substituted values
    for filename, content in files.items():
        file_path = app_dir / filename
        formatted_content = content.format(
            ModelClass=model_class,
            app_name=app_name,
            table_name=table_name,
        )
        file_path.write_text(formatted_content)
        print(f"  ✓ Created {filename}")

    # Create test file
    test_file = Path("tests") / f"test_{app_name}.py"
    test_content = f'''import pytest
from httpx import AsyncClient
from app.main import app
from app.database import SessionLocal


@pytest.mark.asyncio
async def test_{app_name}_list():
    """Test listing {app_name}."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/{app_name}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
'''
    test_file.write_text(test_content)
    print(f"  ✓ Created test_{app_name}.py")

    _register_app_in_main(app_name)
    _register_models_in_alembic(app_name)
    _register_models_in_celery(app_name)

    print(f"\n✓ App '{app_name}' created successfully!")
    print(f"\nNext steps:")
    print(f"1. Adjust models.py / schemas.py if needed")
    print(f"2. Run: python manage.py makemigrations auto")
    print(f"3. Run: python manage.py migrate")


def _register_app_in_main(app_name: str):
    main_path = Path("app/main.py")
    content = main_path.read_text()
    import_line = f"from app.{app_name}.routers import router as {app_name}_router"
    include_line = (
        f'app.include_router({app_name}_router, prefix=f"{{settings.API_V1_STR}}/{app_name}")'
    )
    if import_line not in content:
        marker = "from app.users.views import UserViewSet"
        content = content.replace(marker, f"{marker}\n{import_line}")
    if include_line not in content:
        marker = 'app.include_router(UserViewSet().router, prefix=f"{settings.API_V1_STR}/users")'
        content = content.replace(marker, f"{marker}\n{include_line}")
    main_path.write_text(content)
    print(f"  ✓ Registered router in app/main.py")


def _register_models_in_alembic(app_name: str):
    env_path = Path("alembic/env.py")
    content = env_path.read_text()
    import_line = f"from app.{app_name}.models import *  # noqa: F401, F403"
    if import_line not in content:
        marker = "from app.users.models import User  # noqa: F401"
        content = content.replace(marker, f"{marker}\n{import_line}")
        env_path.write_text(content)
        print(f"  ✓ Registered models in alembic/env.py")


def _register_models_in_celery(app_name: str):
    celery_path = Path("app/celery_app.py")
    content = celery_path.read_text()
    import_line = f"from app.{app_name}.models import *  # noqa: F401, F403"
    if import_line not in content:
        marker = "from app.users.models import User  # noqa: F401"
        content = content.replace(marker, f"{marker}\n{import_line}")
        celery_path.write_text(content)
        print(f"  ✓ Registered models in app/celery_app.py")


def show_migrations(args):
    """Show migration history."""
    print("Migration history:")

    try:
        init_alembic()
        config = Config("alembic.ini")
        config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
        command.history(config)
    except Exception as e:
        print(f"✗ Error showing migrations: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="FastAPI Management Tool (similar to Django's manage.py)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # makemigrations command
    makemig_parser = subparsers.add_parser(
        "makemigrations",
        help="Create a new database migration"
    )
    makemig_parser.add_argument(
        "message",
        nargs="?",
        default="auto",
        help="Migration message (default: auto)"
    )
    makemig_parser.set_defaults(func=makemigrations)

    # migrate command
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Apply pending migrations"
    )
    migrate_parser.add_argument(
        "--revision",
        "-r",
        help="Target revision (default: head)"
    )
    migrate_parser.set_defaults(func=migrate)

    # migrate down command
    down_parser = subparsers.add_parser(
        "migrate-down",
        help="Rollback migrations"
    )
    down_parser.add_argument(
        "--revision",
        "-r",
        default="-1",
        help="Target revision to rollback to (default: -1)"
    )
    down_parser.set_defaults(func=migrate_down)

    # create app command
    create_parser = subparsers.add_parser(
        "createapp",
        help="Create a new feature app"
    )
    create_parser.add_argument(
        "name",
        help="Name of the new app (e.g., products, orders)"
    )
    create_parser.set_defaults(func=create_app)

    # show migrations command
    show_parser = subparsers.add_parser(
        "showmigrations",
        help="Show migration history"
    )
    show_parser.set_defaults(func=show_migrations)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
