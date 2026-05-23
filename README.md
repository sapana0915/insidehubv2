# FastAPI Boilerplate

A production-ready FastAPI boilerplate with clean architecture, class-based views, permissions, middleware, and database integration.

## Project Structure

```
fastapi-boilerplate/
├── app/
│   ├── core/
│   │   ├── config.py          # Configuration and environment variables
│   │   ├── security.py        # JWT, password hashing, permissions
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── constants.py        # Constants and enums
│   ├── middleware/
│   │   ├── auth.py            # Authentication middleware
│   │   ├── request.py         # Request wrapper (similar to Django DRF)
│   │   └── error_handler.py   # Global error handling
│   ├── database.py            # Database connection and session
│   ├── users/                 # Feature module
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic request/response models
│   │   ├── filters.py         # Query params and filtering logic
│   │   ├── repositories.py    # DB access only
│   │   ├── services.py        # Business rules
│   │   ├── views.py           # Class-based views (like ModelViewSet)
│   │   ├── routers.py         # HTTP endpoints
│   │   └── __init__.py
│   ├── products/              # Another feature module (same structure)
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── filters.py
│   │   ├── repositories.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── routers.py
│   │   └── __init__.py
│   ├── views.py               # Base class-based view (ModelViewSet)
│   ├── main.py                # FastAPI app initialization
│   └── __init__.py
├── migrations/                # Alembic migrations
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_users.py
├── .env.example               # Environment variables example
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker compose setup
├── Dockerfile                 # Docker configuration
└── main.py                    # Entry point
```

## Features

- **Feature-Based Structure**: Each feature (users, products, etc.) in its own folder
- **Class-Based Views**: Similar to Django's ModelViewSet
- **Request Wrapper**: Get authenticated user easily in handlers (like Django DRF)
- **Middleware**: Authentication, error handling, request/response logging
- **Permissions**: Role-based access control (RBAC)
- **Repositories**: Database access abstraction layer
- **Services**: Business logic separation
- **Filters**: Query parameter filtering and validation
- **SQLAlchemy ORM**: Type-safe database models
- **Pydantic**: Request/response validation
- **JWT Authentication**: Secure token-based auth
- **Docker Support**: Development and production containers

## Quick Start

### 1. Clone and Setup

```bash
git clone <url>
cd fastapi-boilerplate
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Setup

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Database Setup

```bash
# Create database tables
alembic upgrade head
```

### 5. Run Server

```bash
uvicorn app.main:app --reload
```

Server will be available at `http://localhost:8000`
Docs available at `http://localhost:8000/docs`

## Usage Examples

### Creating a Feature Module

1. Create feature folder: `app/users/`
2. Add the 7 core files (models.py, schemas.py, etc.)
3. Register router in `app/main.py`

### Class-Based Views

```python
# app/users/views.py
from app.views import ModelViewSet
from .schemas import UserResponse, UserCreate
from .services import UserService

class UserViewSet(ModelViewSet):
    schema = UserResponse
    create_schema = UserCreate
    service = UserService
    tags = ["users"]
    permissions = {
        "list": ["AUTHENTICATED"],
        "retrieve": ["AUTHENTICATED"],
        "create": ["ADMIN"],
        "update": ["ADMIN"],
        "delete": ["ADMIN"],
    }
```

### Accessing Authenticated User

```python
from app.middleware.request import RequestWrapper

@router.get("/profile")
async def get_profile(request: RequestWrapper):
    user = request.user
    return {"user": user}
```

## Docker

### Development

```bash
docker-compose -f docker-compose.yml up -d
```

## Testing

```bash
pytest
pytest --cov=app  # With coverage
```

## License

MIT
