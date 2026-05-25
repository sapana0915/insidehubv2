# Architecture Overview

This document explains the architectural decisions and patterns used in this FastAPI boilerplate.

## Design Principles

1. **Feature-Based Structure** - Code organized by business domain, not by layer
2. **Clean Architecture** - Clear separation of concerns across layers
3. **Django DRF Familiarity** - Patterns similar to Django REST Framework
4. **Repository Pattern** - Database access abstraction
5. **Service Layer** - Business logic separation from HTTP layer
6. **Type Safety** - Pydantic and SQLAlchemy for runtime validation

## Layer Architecture

```
HTTP Request
     ↓
┌─────────────────────────────────────┐
│         Routers (routers.py)        │ ← HTTP endpoint handlers
│         Class-Based Views (views.py)│ ← CRUD operations
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│  Services (services.py)             │ ← Business logic, rules
│  Filters (filters.py)               │ ← Query logic
│  Permissions & Auth                 │ ← Authorization layer
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│  Repositories (repositories.py)     │ ← Database abstraction
│  Models (models.py)                 │ ← Data models
└──────────────────┬──────────────────┘
                   ↓
┌─────────────────────────────────────┐
│  Database (SQLAlchemy)              │ ← Data storage
└─────────────────────────────────────┘
```

## Core Concepts

### 1. Routers (HTTP Layer)

**Location**: `app/<feature>/routers.py`

Handles HTTP requests and responses. Uses FastAPI's dependency injection.

```python
@router.post("/", response_model=UserResponse)
async def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return await UserService.create(db, data)
```

**Responsibilities**:
- Define endpoint routes
- Handle request validation
- Call service layer
- Return responses

### 2. Views (Class-Based Views - Optional)

**Location**: `app/views.py` (base), `app/<feature>/views.py` (specific)

Provides ModelViewSet pattern for standard CRUD operations.

```python
class UserViewSet(ModelViewSet):
    schema = UserResponse
    service = UserService
    permissions = {"create": ["ADMIN"]}
```

**Responsibilities**:
- Auto-generate CRUD endpoints
- Apply permissions
- Handle common operations
- Reduce boilerplate

### 3. Services (Business Logic)

**Location**: `app/<feature>/services.py`

Contains all business rules and logic. Can be used by multiple routers.

```python
class UserService:
    @staticmethod
    async def create(db: Session, user_data: UserCreate) -> User:
        # Validation, business rules
        # Calls repositories
        # Returns result
```

**Responsibilities**:
- Implement business rules
- Coordinate repositories
- Handle transactions
- Validate data
- Handle errors

**Important**: Services are stateless and can be called from multiple contexts.

### 4. Repositories (Database Access)

**Location**: `app/<feature>/repositories.py`

All database queries go through repositories. Only repositories directly query the database.

```python
class UserRepository:
    @staticmethod
    def get_by_id(db: Session, id: int) -> User:
        return db.query(User).filter(User.id == id).first()
```

**Responsibilities**:
- Execute database queries
- Handle ORM operations
- Return raw models
- No business logic

**Why**: Makes it easy to swap database implementation, test with fake repos, and centralize query logic.

### 5. Models (Data Models)

**Location**: `app/<feature>/models.py`

SQLAlchemy ORM models representing database tables.

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True)
```

**Responsibilities**:
- Define database schema
- Define relationships
- Add database constraints

### 6. Schemas (Data Validation)

**Location**: `app/<feature>/schemas.py`

Pydantic models for request/response validation.

```python
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
```

**Responsibilities**:
- Validate input data
- Transform data for responses
- Document API contracts
- Type hints for IDE

### 7. Filters (Query Logic)

**Location**: `app/<feature>/filters.py`

Handles query parameters and filtering logic.

```python
class UserFilter(BaseModel):
    email: Optional[str] = None
    is_active: Optional[bool] = None
```

**Responsibilities**:
- Define filterable fields
- Parse query parameters
- Build filter conditions

## Cross-Cutting Concerns

### Middleware (`app/middleware/`)

**Request Wrapper** (`request.py`):
- Provides Django DRF-like request object
- Gives access to authenticated user
- Simplifies handler signatures

**Error Handler** (`error_handler.py`):
- Global exception handling
- Standardized error responses
- Logging

### Security (`app/core/security.py`)

- JWT token generation and validation
- Password hashing with bcrypt
- Bearer token authentication

### Exceptions (`app/core/exceptions.py`)

Custom HTTP exceptions with consistent error format:

```python
raise NotFoundException("User")  # → 404 with "User not found"
raise ForbiddenException()       # → 403 with "Not enough permissions"
```

## Data Flow Example

### Create User Request

```
POST /api/v1/users (email, password, etc.)
      ↓
routers.create_user()
      ↓
UserService.create()
      ├→ Validate (email not duplicate)
      ├→ Hash password
      ├→ UserRepository.create()
      │   └→ db.add(user)
      │   └→ db.commit()
      ↓
Response with UserResponse schema
```

### Retrieve User Request

```
GET /api/v1/users/123 (with JWT token)
      ↓
RequestWrapper checks authentication
      ↓
UserViewSet.retrieve()
      ↓
Check permissions
      ↓
UserService.get(123)
      ↓
UserRepository.get_by_id(123)
      ├→ db.query(User).filter(User.id == 123)
      ↓
Response with UserResponse schema
```

## Testing Strategy

- **Repositories**: Mock database, test query logic
- **Services**: Mock repositories, test business logic
- **Routers**: Mock services, test HTTP contracts
- **Integration**: Real database (SQLite), full request/response

See `tests/conftest.py` for test setup.

## Adding a New Feature

1. Create `app/<feature>/` folder
2. Add the 7 files in order: models → schemas → repositories → services → filters → views → routers
3. Register router in `app/main.py`
4. Add tests in `tests/test_<feature>.py`

See `FEATURE_TEMPLATE.md` for detailed guide.

## Performance Considerations

1. **Connection Pooling**: SQLAlchemy handles via `pool_pre_ping`
2. **Async Support**: FastAPI is async-first, services are async-ready
3. **Database Indexes**: Add to frequently filtered fields in models
4. **Pagination**: Standard pattern with `skip` and `limit`
5. **Caching**: Add to services as needed (Redis, in-memory)

## Security Best Practices

1. **Password Hashing**: Bcrypt via passlib ✓
2. **Token Expiration**: JWT includes exp claim ✓
3. **CORS**: Configurable via environment ✓
4. **SQL Injection**: SQLAlchemy ORM prevents it ✓
5. **Authorization**: Permissions system in place ✓
6. **Input Validation**: Pydantic models ✓

## Extending the Framework

### Add Custom Exception

```python
# app/core/exceptions.py
class CustomException(DetailedException):
    def __init__(self, detail: str = "Custom error"):
        super().__init__(status_code=400, detail=detail)
```

### Add Middleware

```python
# In app/main.py
app.add_middleware(MyCustomMiddleware)
```

### Add Permission

```python
# app/core/constants.py
class Permission(str, Enum):
    MY_PERMISSION = "MY_PERMISSION"

# In views.py
permissions = {"action": ["MY_PERMISSION"]}
```

### Add Base Service Method

```python
# app/services.py (new base class)
class BaseService:
    @staticmethod
    async def list_with_filter(db, model, filter_params):
        # Common filtering logic
        pass
```

## When to Use What

| Use Case | Location |
|----------|----------|
| Define endpoints | routers.py |
| Business logic | services.py |
| Database queries | repositories.py |
| Data validation | schemas.py |
| Filtering logic | filters.py |
| CRUD operations | views.py (ModelViewSet) |
| Database tables | models.py |
| Global setup | app/main.py |
| Shared logic | app/core/ |

## Summary

This architecture provides:
- ✓ Clear separation of concerns
- ✓ Familiar patterns (like Django)
- ✓ Easy testing
- ✓ Scalable structure
- ✓ Reusable components
- ✓ Type safety
- ✓ Production-ready
