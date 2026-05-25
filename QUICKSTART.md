# Quick Start Guide

Get the FastAPI boilerplate running in 5 minutes.

## Prerequisites

- Python 3.9+
- PostgreSQL (or use Docker)
- pip or conda

## Setup

### 1. Clone & Enter Directory

```bash
cd fastapi-boilerplate
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Database

**Option A: Using Docker (Recommended)**

```bash
docker-compose up -d
```

Wait for PostgreSQL to start, then in the project directory:

```bash
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

**Option B: Local PostgreSQL**

Update `.env`:
```
DATABASE_URL=postgresql://your_user:your_password@localhost:5432/fastapi_db
```

Then create tables:
```bash
python -c "from app.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

### 5. Run Server

```bash
python main.py
```

Or with auto-reload:
```bash
uvicorn app.main:app --reload
```

## Test It

### Open API Docs
http://localhost:8000/docs

### Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "user",
    "password": "password123",
    "full_name": "User Name"
  }'
```

### Login

```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

### Run Tests

```bash
pytest
pytest -v  # Verbose
pytest --cov=app  # With coverage
```

## Key Features to Explore

1. **RequestWrapper** - Access authenticated user in handlers
   - See `app/middleware/request.py`

2. **Class-Based Views** - Similar to Django ModelViewSet
   - See `app/views.py` and `app/users/views.py`

3. **Permissions** - Role-based access control
   - See `app/users/views.py` for permission example

4. **Repositories** - Database access abstraction
   - See `app/users/repositories.py`

5. **Services** - Business logic layer
   - See `app/users/services.py`

## Create a New Feature

Use the template in `FEATURE_TEMPLATE.md`:

```bash
mkdir app/products
# Create models.py, schemas.py, repositories.py, services.py, routers.py
# Register router in app/main.py
```

## Project Structure

```
app/
├── core/              # Config, security, exceptions
├── middleware/        # Auth, request wrapper, error handling
├── users/            # Example feature (models, schemas, services, etc.)
├── views.py          # Base ModelViewSet class
├── database.py       # DB connection
└── main.py           # FastAPI app

tests/                # Test suite
requirements.txt      # Dependencies
docker-compose.yml    # Docker setup
```

## Troubleshooting

### "Cannot connect to database"
- Check PostgreSQL is running
- Verify DATABASE_URL in .env
- Use Docker: `docker-compose up -d`

### "ModuleNotFoundError: No module named 'app'"
- Ensure you're running from the project root
- Check virtual environment is activated

### Tests failing
- Run `pytest -v` to see detailed errors
- Check test database exists
- Use `pytest --tb=short` for shorter tracebacks

## Next Steps

1. Read `FEATURE_TEMPLATE.md` to create new features
2. Explore `app/users/` for a complete example
3. Check `app/core/security.py` for JWT customization
4. Update `app/core/config.py` for environment variables

## Documentation

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **Pydantic**: https://docs.pydantic.dev/
- **JWT**: https://python-jose.readthedocs.io/

Enjoy building! 🚀
