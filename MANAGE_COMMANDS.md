# Management Commands Guide

The `manage.py` file provides Django-like management commands for FastAPI.

## Database Migrations

### Create a Migration

```bash
python manage.py makemigrations "add user fields"
```

This uses Alembic to auto-generate a migration based on model changes.

**Options:**
- `message` - Migration description (default: "auto")

### Run Migrations

```bash
python manage.py migrate
```

Apply all pending migrations up to the latest version.

**Options:**
- `--revision` / `-r` - Target specific revision (default: "head")

Example:
```bash
# Run up to specific revision
python manage.py migrate --revision abc123def
```

### Rollback Migrations

```bash
python manage.py migrate-down
```

Rollback one migration by default.

**Options:**
- `--revision` / `-r` - Target revision to rollback to (default: "-1")

Examples:
```bash
# Rollback one step
python manage.py migrate-down

# Rollback multiple steps
python manage.py migrate-down --revision -3

# Rollback to specific revision
python manage.py migrate-down --revision abc123def
```

### View Migration History

```bash
python manage.py showmigrations
```

Display all migrations and their status.

## Creating Apps (Feature Modules)

```bash
python manage.py createapp products
```

Creates a complete feature module with all required files:

**Generated Files:**
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic request/response models
- `repositories.py` - Database access layer
- `services.py` - Business logic
- `filters.py` - Query parameter filters
- `views.py` - Class-based views
- `routers.py` - HTTP endpoints
- `tests/test_products.py` - Test file

### File Structure

```
app/
└── products/
    ├── __init__.py
    ├── models.py          # SQLAlchemy models
    ├── schemas.py         # Pydantic schemas
    ├── repositories.py    # Database access
    ├── services.py        # Business logic
    ├── filters.py         # Query filters
    ├── views.py           # Class-based views
    └── routers.py         # HTTP endpoints
```

### After Creating App

1. **Update models.py** with your fields
2. **Register router** in `app/main.py`:
   ```python
   from app.products.routers import router as products_router
   
   app.include_router(products_router, prefix=settings.API_V1_STR)
   ```
3. **Create migration**:
   ```bash
   python manage.py makemigrations "add products table"
   ```
4. **Apply migration**:
   ```bash
   python manage.py migrate
   ```

## Examples

### Common Workflow

```bash
# 1. Create new feature
python manage.py createapp products

# 2. Edit models.py with your fields
# 3. Create migration
python manage.py makemigrations "add products feature"

# 4. Review generated migration file
# 5. Apply migration
python manage.py migrate

# 6. Register router in app/main.py
# 7. Start server
python main.py
```

### Multiple Features

```bash
# Create several features
python manage.py createapp products
python manage.py createapp orders
python manage.py createapp customers

# Create combined migration
python manage.py makemigrations "add products, orders, customers"

# Apply all at once
python manage.py migrate
```

### Rollback and Retry

```bash
# Made a mistake? Rollback
python manage.py migrate-down

# See migration history
python manage.py showmigrations

# Create new migration
python manage.py makemigrations "fix schema issue"

# Apply fix
python manage.py migrate
```

## Advanced Usage

### Target Specific Revision

```bash
# Migrate to specific revision
python manage.py migrate --revision 5e123fa45d7

# Downgrade to before that revision
python manage.py migrate-down --revision 5e123fa45d6
```

### Generated Files

The generated `models.py` template includes:
```python
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

All files follow the boilerplate patterns and are ready to customize.

## Troubleshooting

### "Alembic not initialized"

If you get this error, the command will auto-initialize:
```bash
python manage.py makemigrations
# Initializes Alembic automatically
```

### "Cannot connect to database"

Ensure PostgreSQL is running and `.env` has correct DATABASE_URL:
```bash
# Check connection
psql $DATABASE_URL
```

### "Migration conflicts"

If migrations conflict, create a new migration:
```bash
python manage.py makemigrations "resolve conflicts"
```

### View Alembic Config

The `alembic.ini` file contains Alembic configuration. Key sections:
- `sqlalchemy.url` - Set automatically from DATABASE_URL
- `script_location` - Location of migrations folder
- `version_path_separator` - Path separator for migrations

## Environment Setup

Create `.env` file from template:
```bash
cp .env.example .env
```

Update with your values:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/db
```

## Related Commands

### Start Server

```bash
python main.py
# or
uvicorn app.main:app --reload
```

### Run Tests

```bash
pytest
pytest -v --cov=app
```

### Create Superuser (Future Enhancement)

```bash
# Future: python manage.py createsuperuser
```

## Help

```bash
python manage.py --help
python manage.py makemigrations --help
python manage.py createapp --help
```
