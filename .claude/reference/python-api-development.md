# Python API Development Reference

**Load this when**: Working on API endpoints, routes, request/response handling

---

## Tech Stack

- **Framework**: FastAPI or Flask
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Validation**: Pydantic models
- **Authentication**: JWT tokens
- **API Client**: litellm for LLM calls

---

## Project Structure

```
src/
├── api/
│   ├── routes/          # API endpoints
│   │   ├── __init__.py
│   │   ├── health.py    # Health check
│   │   └── [resource].py
│   ├── models/          # SQLAlchemy models
│   ├── schemas/         # Pydantic schemas
│   ├── dependencies.py  # Dependency injection
│   └── main.py         # FastAPI app
└── services/           # Business logic
```

---

## API Endpoint Pattern

### Basic Endpoint Structure

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..schemas import ResourceCreate, ResourceResponse
from ..services import resource_service

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])

@router.post("/", response_model=ResourceResponse, status_code=201)
async def create_resource(
    resource: ResourceCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new resource.

    - **resource**: Resource data
    - Returns: Created resource with ID
    """
    return resource_service.create(db, resource)

@router.get("/{resource_id}", response_model=ResourceResponse)
async def get_resource(
    resource_id: int,
    db: Session = Depends(get_db)
):
    """Get resource by ID."""
    resource = resource_service.get(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")
    return resource
```

---

## Pydantic Schemas

### Always separate Create/Update/Response schemas

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ResourceBase(BaseModel):
    """Shared properties"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

class ResourceCreate(ResourceBase):
    """Properties required for creation"""
    pass

class ResourceUpdate(BaseModel):
    """Properties that can be updated (all optional)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None

class ResourceResponse(ResourceBase):
    """Properties returned to client"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode
```

---

## Database Models

### SQLAlchemy Model Pattern

```python
from sqlalchemy import Column, Integer, String, DateTime, func
from ..database import Base

class Resource(Base):
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

---

## Service Layer Pattern

### Keep business logic in services, not routes

```python
from sqlalchemy.orm import Session
from ..models import Resource
from ..schemas import ResourceCreate, ResourceUpdate

class ResourceService:
    def create(self, db: Session, resource: ResourceCreate) -> Resource:
        """Create new resource."""
        db_resource = Resource(**resource.dict())
        db.add(db_resource)
        db.commit()
        db.refresh(db_resource)
        return db_resource

    def get(self, db: Session, resource_id: int) -> Resource | None:
        """Get resource by ID."""
        return db.query(Resource).filter(Resource.id == resource_id).first()

    def list(self, db: Session, skip: int = 0, limit: int = 100) -> list[Resource]:
        """List resources with pagination."""
        return db.query(Resource).offset(skip).limit(limit).all()

    def update(self, db: Session, resource_id: int, resource: ResourceUpdate) -> Resource | None:
        """Update resource."""
        db_resource = self.get(db, resource_id)
        if not db_resource:
            return None

        update_data = resource.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_resource, field, value)

        db.commit()
        db.refresh(db_resource)
        return db_resource

    def delete(self, db: Session, resource_id: int) -> bool:
        """Delete resource."""
        db_resource = self.get(db, resource_id)
        if not db_resource:
            return False

        db.delete(db_resource)
        db.commit()
        return True

resource_service = ResourceService()
```

---

## Error Handling

### Use FastAPI HTTPException

```python
from fastapi import HTTPException, status

# 400 Bad Request
raise HTTPException(
    status_code=status.HTTP_400_BAD_REQUEST,
    detail="Invalid input data"
)

# 404 Not Found
raise HTTPException(
    status_code=status.HTTP_404_NOT_FOUND,
    detail="Resource not found"
)

# 409 Conflict
raise HTTPException(
    status_code=status.HTTP_409_CONFLICT,
    detail="Resource already exists"
)

# 500 Internal Server Error (let FastAPI handle these)
# Don't catch generic exceptions unless logging
```

---

## LLM Integration (litellm)

### Always use litellm, never direct API calls

```python
from litellm import completion, embedding
import os

# Chat completion
response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
    api_base=os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
)

# Embeddings
embedding_response = embedding(
    model="text-embedding-3-small",
    input=["text to embed"],
    api_base=os.getenv("LITELLM_BASE_URL", "http://localhost:4000")
)
```

---

## Environment Variables

### Always use .env, never hardcode

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    litellm_base_url: str = "http://localhost:4000"
    api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## API Standards

### REST Conventions

- **GET** `/resources` - List all (with pagination)
- **GET** `/resources/{id}` - Get single resource
- **POST** `/resources` - Create new resource
- **PUT** `/resources/{id}` - Full update (replace)
- **PATCH** `/resources/{id}` - Partial update (preferred)
- **DELETE** `/resources/{id}` - Delete resource

### Status Codes

- `200 OK` - Successful GET, PUT, PATCH
- `201 Created` - Successful POST
- `204 No Content` - Successful DELETE
- `400 Bad Request` - Invalid input
- `404 Not Found` - Resource doesn't exist
- `409 Conflict` - Duplicate/conflict
- `500 Internal Server Error` - Server error

### Response Format

```json
{
  "data": { /* resource data */ },
  "meta": {
    "timestamp": "2026-01-08T23:50:00Z"
  }
}
```

For lists:
```json
{
  "data": [ /* array of resources */ ],
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

---

## Security

### Input Validation

- ✅ Use Pydantic schemas for all inputs
- ✅ Validate string lengths, formats, ranges
- ✅ Sanitize user inputs (SQL injection prevention)
- ✅ Use parameterized queries (SQLAlchemy does this)

### Authentication

- ✅ Use JWT tokens
- ✅ Validate tokens on protected endpoints
- ✅ Use dependency injection for auth

```python
from fastapi import Depends, HTTPException, Header

async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")

    token = authorization.split(" ")[1]
    # Validate JWT token here
    return decoded_user

@router.get("/protected")
async def protected_route(user = Depends(verify_token)):
    return {"user": user}
```

---

## Testing

### Test Structure

```python
import pytest
from fastapi.testclient import TestClient
from ..main import app

client = TestClient(app)

def test_create_resource():
    response = client.post(
        "/api/v1/resources/",
        json={"name": "Test Resource", "description": "Test"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Resource"
    assert "id" in data

def test_get_resource_not_found():
    response = client.get("/api/v1/resources/99999")
    assert response.status_code == 404
```

---

## Common Patterns

### Pagination

```python
from typing import Optional

@router.get("/", response_model=list[ResourceResponse])
async def list_resources(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return resource_service.list(db, skip=skip, limit=limit)
```

### Filtering

```python
@router.get("/", response_model=list[ResourceResponse])
async def list_resources(
    name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Resource)
    if name:
        query = query.filter(Resource.name.ilike(f"%{name}%"))
    if status:
        query = query.filter(Resource.status == status)
    return query.all()
```

### Async Database Operations

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_resources(db: AsyncSession):
    result = await db.execute(select(Resource))
    return result.scalars().all()
```

---

## Gotchas

❌ **Don't**: Mix business logic in routes
✅ **Do**: Put logic in service layer

❌ **Don't**: Use generic Exception catching
✅ **Do**: Use specific HTTPException with proper status codes

❌ **Don't**: Return SQLAlchemy models directly
✅ **Do**: Use Pydantic response schemas

❌ **Don't**: Hardcode API keys or URLs
✅ **Do**: Use environment variables

❌ **Don't**: Call OpenAI/Anthropic/Groq directly
✅ **Do**: Use litellm for all LLM calls

---

## Quick Checklist

When adding a new API endpoint:

- [ ] Create Pydantic schemas (Create, Update, Response)
- [ ] Create SQLAlchemy model (if new resource)
- [ ] Create service methods (business logic)
- [ ] Create route with proper HTTP method
- [ ] Add docstrings
- [ ] Add input validation
- [ ] Handle errors with HTTPException
- [ ] Write tests (happy path + error cases)
- [ ] Update API documentation (auto-generated by FastAPI)
