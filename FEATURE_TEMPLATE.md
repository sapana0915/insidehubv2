# Creating a New Feature Module

This guide helps you create a new feature following the boilerplate structure.

## Step 1: Create Feature Folder

```bash
mkdir app/<feature_name>
touch app/<feature_name>/__init__.py
```

## Step 2: Create Core Files

### models.py
Define SQLAlchemy models for your feature:

```python
from sqlalchemy import Column, Integer, String
from app.database import Base

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    price = Column(Float)
```

### schemas.py
Define Pydantic schemas for request/response validation:

```python
from pydantic import BaseModel

class ProductCreate(BaseModel):
    name: str
    price: float

class ProductResponse(BaseModel):
    id: int
    name: str
    price: float
```

### repositories.py
Define database access layer:

```python
from sqlalchemy.orm import Session
from .models import Product

class ProductRepository:
    @staticmethod
    def get_by_id(db: Session, id: int) -> Product:
        return db.query(Product).filter(Product.id == id).first()
```

### services.py
Define business logic:

```python
from sqlalchemy.orm import Session
from .repositories import ProductRepository
from .schemas import ProductCreate

class ProductService:
    @staticmethod
    async def get(db: Session, id: int):
        return ProductRepository.get_by_id(db, id)
    
    @staticmethod
    async def create(db: Session, data: ProductCreate):
        product = Product(**data.dict())
        return ProductRepository.create(db, product)
```

### filters.py
Define query parameter filters:

```python
from typing import Optional
from pydantic import BaseModel

class ProductFilter(BaseModel):
    name: Optional[str] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
```

### views.py (Optional)
Define class-based views if using ModelViewSet:

```python
from app.views import ModelViewSet
from .schemas import ProductResponse, ProductCreate
from .services import ProductService

class ProductViewSet(ModelViewSet):
    schema = ProductResponse
    create_schema = ProductCreate
    service = ProductService
    tags = ["products"]
```

### routers.py
Define HTTP endpoints:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from .schemas import ProductCreate, ProductResponse
from .services import ProductService

router = APIRouter(prefix="/products", tags=["products"])

@router.post("", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db)
):
    return await ProductService.create(db, data)
```

## Step 3: Register in Main App

In `app/main.py`:

```python
from app.products.routers import router as products_router

app.include_router(products_router, prefix=settings.API_V1_STR)
```

## Step 4: Create Tests

In `tests/test_products.py`:

```python
def test_create_product(client):
    response = client.post(
        "/api/v1/products",
        json={"name": "Widget", "price": 9.99}
    )
    assert response.status_code == 200
```

## File Structure Summary

```
app/
└── <feature_name>/
    ├── __init__.py
    ├── models.py        # SQLAlchemy models
    ├── schemas.py       # Pydantic schemas
    ├── repositories.py  # Database access
    ├── services.py      # Business logic
    ├── filters.py       # Query filters
    ├── views.py         # Class-based views (optional)
    └── routers.py       # HTTP endpoints
```

## Permissions

Restrict endpoints by adding permissions dict to views:

```python
class ProductViewSet(ModelViewSet):
    permissions = {
        "list": [],  # Public
        "retrieve": [],  # Public
        "create": ["AUTHENTICATED"],  # Login required
        "update": ["ADMIN"],  # Admin only
        "delete": ["ADMIN"],
    }
```

## Accessing User

In any router, use RequestWrapper to access authenticated user:

```python
from app.middleware.request import get_request_wrapper, RequestWrapper

@router.get("/my-products")
async def get_my_products(request: RequestWrapper = Depends(get_request_wrapper)):
    user_id = request.get_user_id()
    # Get user's products
```
