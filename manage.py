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
        "models.py": '''from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from app.database import Base


class {ModelClass}(Base):
    """TODO: Update this model with your fields."""
    __tablename__ = "{table_name}"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
''',
        "schemas.py": '''from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class {ModelClass}Base(BaseModel):
    """Base schema for {ModelClass}."""
    pass


class {ModelClass}Create({ModelClass}Base):
    """Schema for creating {ModelClass}."""
    pass


class {ModelClass}Update(BaseModel):
    """Schema for updating {ModelClass}."""
    pass


class {ModelClass}Response({ModelClass}Base):
    """Response schema for {ModelClass}."""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
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
        update_data = obj_in.dict(exclude_unset=True)
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
        "services.py": '''from sqlalchemy.orm import Session
from .repositories import {ModelClass}Repository
from .schemas import {ModelClass}Create, {ModelClass}Update


class {ModelClass}Service:
    """Business logic layer for {ModelClass}."""

    @staticmethod
    async def get(db: Session, id: int):
        return {ModelClass}Repository.get_by_id(db, id)

    @staticmethod
    async def list(db: Session, skip: int = 0, limit: int = 100):
        return {ModelClass}Repository.list_all(db, skip, limit)

    @staticmethod
    async def create(db: Session, data: {ModelClass}Create):
        from .models import {ModelClass}
        obj = {ModelClass}(**data.dict())
        return {ModelClass}Repository.create(db, obj)

    @staticmethod
    async def update(db: Session, id: int, data: {ModelClass}Update):
        obj = {ModelClass}Repository.get_by_id(db, id)
        if not obj:
            return None
        return {ModelClass}Repository.update(db, obj, data)

    @staticmethod
    async def delete(db: Session, id: int) -> bool:
        return {ModelClass}Repository.delete(db, id)
''',
        "filters.py": '''from typing import Optional
from pydantic import BaseModel


class {ModelClass}Filter(BaseModel):
    """Query filters for {ModelClass}."""
    pass
''',
        "views.py": '''from app.views import ModelViewSet
from .schemas import {ModelClass}Response, {ModelClass}Create
from .services import {ModelClass}Service


class {ModelClass}ViewSet(ModelViewSet):
    """Class-based views for {ModelClass}."""
    schema = {ModelClass}Response
    create_schema = {ModelClass}Create
    service = {ModelClass}Service
    tags = ["{app_name}"]

    permissions = {{
        "list": [],
        "retrieve": [],
        "create": ["AUTHENTICATED"],
        "update": ["AUTHENTICATED"],
        "delete": ["ADMIN"],
    }}
''',
        "routers.py": '''from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from .schemas import {ModelClass}Create, {ModelClass}Response
from .services import {ModelClass}Service

router = APIRouter(prefix="/{app_name}", tags=["{app_name}"])


@router.get("", response_model=list[{ModelClass}Response])
async def list_{app_name}(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """List all {app_name}."""
    return await {ModelClass}Service.list(db, skip, limit)


@router.get("/{{id}}", response_model={ModelClass}Response)
async def get_{app_name}(
    id: int,
    db: Session = Depends(get_db),
):
    """Get a specific {app_name}."""
    return await {ModelClass}Service.get(db, id)


@router.post("", response_model={ModelClass}Response)
async def create_{app_name}(
    data: {ModelClass}Create,
    db: Session = Depends(get_db),
):
    """Create a new {app_name}."""
    return await {ModelClass}Service.create(db, data)


@router.put("/{{id}}", response_model={ModelClass}Response)
async def update_{app_name}(
    id: int,
    data: {ModelClass}Create,
    db: Session = Depends(get_db),
):
    """Update a {app_name}."""
    return await {ModelClass}Service.update(db, id, data)


@router.delete("/{{id}}")
async def delete_{app_name}(
    id: int,
    db: Session = Depends(get_db),
):
    """Delete a {app_name}."""
    success = await {ModelClass}Service.delete(db, id)
    return {{"deleted": success}}
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

    print(f"\n✓ App '{app_name}' created successfully!")
    print(f"\nNext steps:")
    print(f"1. Update models.py with your fields")
    print(f"2. Register the router in app/main.py:")
    print(f"   from app.{app_name}.routers import router as {app_name}_router")
    print(f"   app.include_router({app_name}_router, prefix=settings.API_V1_STR)")
    print(f"3. Run: python manage.py makemigrations auto")
    print(f"4. Run: python manage.py migrate")


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
