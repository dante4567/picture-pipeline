# Testing & Logging Patterns

**Load this when**: Writing tests, setting up logging, debugging

---

## Testing Philosophy

**Testing Pyramid**:
- 70% Unit tests (fast, isolated)
- 20% Integration tests (API + DB)
- 10% End-to-end tests (full workflow)

**Write tests BEFORE implementation** when possible (TDD).

---

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures
├── unit/                    # Unit tests (70%)
│   ├── test_services.py
│   ├── test_models.py
│   └── test_utils.py
├── integration/             # Integration tests (20%)
│   ├── test_api_endpoints.py
│   └── test_database.py
└── e2e/                     # End-to-end tests (10%)
    └── test_workflows.py
```

---

## Pytest Configuration

### pyproject.toml or pytest.ini

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",                    # Verbose
    "--strict-markers",      # Error on unknown markers
    "--tb=short",            # Shorter tracebacks
    "--cov=src",             # Coverage
    "--cov-report=term-missing",
    "--cov-report=html",
]
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "slow: Slow tests",
]
```

---

## Fixtures (conftest.py)

### Database Fixtures

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.main import app
from fastapi.testclient import TestClient

# Test database
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    db = TestingSessionLocal()

    yield db

    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with test database."""
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

### Mock Data Fixtures

```python
@pytest.fixture
def sample_user():
    """Sample user data."""
    return {
        "name": "Test User",
        "email": "test@example.com"
    }

@pytest.fixture
def sample_resource(db_session):
    """Create sample resource in database."""
    from src.models import Resource
    resource = Resource(name="Test Resource")
    db_session.add(resource)
    db_session.commit()
    db_session.refresh(resource)
    return resource
```

---

## Unit Tests

### Testing Services (Business Logic)

```python
import pytest
from src.services import resource_service
from src.schemas import ResourceCreate, ResourceUpdate

@pytest.mark.unit
def test_create_resource(db_session):
    """Test resource creation."""
    # Arrange
    resource_data = ResourceCreate(name="New Resource", description="Test")

    # Act
    result = resource_service.create(db_session, resource_data)

    # Assert
    assert result.id is not None
    assert result.name == "New Resource"
    assert result.description == "Test"

@pytest.mark.unit
def test_get_resource(db_session, sample_resource):
    """Test getting resource by ID."""
    # Act
    result = resource_service.get(db_session, sample_resource.id)

    # Assert
    assert result is not None
    assert result.id == sample_resource.id
    assert result.name == sample_resource.name

@pytest.mark.unit
def test_get_nonexistent_resource(db_session):
    """Test getting resource that doesn't exist."""
    # Act
    result = resource_service.get(db_session, 99999)

    # Assert
    assert result is None

@pytest.mark.unit
def test_update_resource(db_session, sample_resource):
    """Test resource update."""
    # Arrange
    update_data = ResourceUpdate(name="Updated Name")

    # Act
    result = resource_service.update(db_session, sample_resource.id, update_data)

    # Assert
    assert result is not None
    assert result.name == "Updated Name"
    assert result.description == sample_resource.description  # Unchanged

@pytest.mark.unit
def test_delete_resource(db_session, sample_resource):
    """Test resource deletion."""
    # Act
    deleted = resource_service.delete(db_session, sample_resource.id)

    # Assert
    assert deleted is True
    assert resource_service.get(db_session, sample_resource.id) is None
```

### Testing Utils/Helpers

```python
import pytest
from src.utils import slugify, validate_email

@pytest.mark.unit
@pytest.mark.parametrize("input,expected", [
    ("Hello World", "hello-world"),
    ("Test 123", "test-123"),
    ("  spaces  ", "spaces"),
    ("CamelCase", "camelcase"),
])
def test_slugify(input, expected):
    """Test slugify function."""
    assert slugify(input) == expected

@pytest.mark.unit
@pytest.mark.parametrize("email,is_valid", [
    ("test@example.com", True),
    ("invalid", False),
    ("@example.com", False),
    ("test@", False),
])
def test_validate_email(email, is_valid):
    """Test email validation."""
    assert validate_email(email) == is_valid
```

---

## Integration Tests

### Testing API Endpoints

```python
import pytest
from fastapi import status

@pytest.mark.integration
def test_create_resource_endpoint(client):
    """Test POST /resources endpoint."""
    # Arrange
    payload = {
        "name": "Test Resource",
        "description": "Integration test"
    }

    # Act
    response = client.post("/api/v1/resources/", json=payload)

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["description"] == payload["description"]
    assert "id" in data
    assert "created_at" in data

@pytest.mark.integration
def test_get_resource_endpoint(client, sample_resource):
    """Test GET /resources/{id} endpoint."""
    # Act
    response = client.get(f"/api/v1/resources/{sample_resource.id}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == sample_resource.id
    assert data["name"] == sample_resource.name

@pytest.mark.integration
def test_get_nonexistent_resource_endpoint(client):
    """Test GET /resources/{id} with invalid ID."""
    # Act
    response = client.get("/api/v1/resources/99999")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.integration
def test_update_resource_endpoint(client, sample_resource):
    """Test PATCH /resources/{id} endpoint."""
    # Arrange
    payload = {"name": "Updated Name"}

    # Act
    response = client.patch(f"/api/v1/resources/{sample_resource.id}", json=payload)

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Name"

@pytest.mark.integration
def test_delete_resource_endpoint(client, sample_resource):
    """Test DELETE /resources/{id} endpoint."""
    # Act
    response = client.delete(f"/api/v1/resources/{sample_resource.id}")

    # Assert
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Verify deletion
    get_response = client.get(f"/api/v1/resources/{sample_resource.id}")
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.integration
def test_list_resources_endpoint(client, db_session):
    """Test GET /resources endpoint with pagination."""
    # Arrange - create multiple resources
    from src.models import Resource
    for i in range(5):
        resource = Resource(name=f"Resource {i}")
        db_session.add(resource)
    db_session.commit()

    # Act
    response = client.get("/api/v1/resources/?skip=0&limit=3")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 3
```

### Testing Authentication

```python
@pytest.mark.integration
def test_protected_endpoint_without_auth(client):
    """Test accessing protected endpoint without token."""
    response = client.get("/api/v1/protected")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.integration
def test_protected_endpoint_with_auth(client, auth_token):
    """Test accessing protected endpoint with valid token."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = client.get("/api/v1/protected", headers=headers)
    assert response.status_code == status.HTTP_200_OK
```

---

## Mocking

### Mocking External APIs

```python
from unittest.mock import patch, MagicMock

@pytest.mark.unit
@patch('src.services.litellm.completion')
def test_llm_service(mock_completion):
    """Test LLM service with mocked litellm."""
    # Arrange
    mock_completion.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content="Mocked response"))]
    )

    # Act
    from src.services import llm_service
    result = llm_service.generate("test prompt")

    # Assert
    assert result == "Mocked response"
    mock_completion.assert_called_once()

@pytest.mark.unit
@patch('src.services.requests.get')
def test_external_api_call(mock_get):
    """Test external API call with mocked response."""
    # Arrange
    mock_get.return_value.json.return_value = {"data": "test"}
    mock_get.return_value.status_code = 200

    # Act
    from src.services import external_service
    result = external_service.fetch_data()

    # Assert
    assert result["data"] == "test"
```

---

## End-to-End Tests

### Complete Workflow Tests

```python
@pytest.mark.e2e
def test_complete_resource_workflow(client):
    """Test complete CRUD workflow."""
    # Create
    create_response = client.post(
        "/api/v1/resources/",
        json={"name": "Workflow Test"}
    )
    assert create_response.status_code == 201
    resource_id = create_response.json()["id"]

    # Read
    get_response = client.get(f"/api/v1/resources/{resource_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Workflow Test"

    # Update
    update_response = client.patch(
        f"/api/v1/resources/{resource_id}",
        json={"name": "Updated"}
    )
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated"

    # Delete
    delete_response = client.delete(f"/api/v1/resources/{resource_id}")
    assert delete_response.status_code == 204

    # Verify deleted
    get_after_delete = client.get(f"/api/v1/resources/{resource_id}")
    assert get_after_delete.status_code == 404
```

---

## Running Tests

```bash
# All tests
pytest

# Specific markers
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Specific file
pytest tests/unit/test_services.py

# Specific test
pytest tests/unit/test_services.py::test_create_resource

# With coverage
pytest --cov=src --cov-report=html

# Verbose
pytest -v

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Run in parallel
pytest -n auto
```

---

## Test Coverage

### Minimum Coverage Targets

- Overall: 80%
- New code: 90%
- Critical paths: 100%

### Check Coverage

```bash
pytest --cov=src --cov-report=term-missing

# Generate HTML report
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

---

## Logging

### Structured Logging with structlog

```python
import structlog

# Configure (in main.py or __init__.py)
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

# Use in code
logger = structlog.get_logger()

# Log with context
logger.info(
    "request_processed",
    user_id=123,
    endpoint="/api/resources",
    duration_ms=45,
    status_code=200
)

logger.error(
    "database_error",
    error=str(e),
    query="SELECT * FROM resources",
    traceback=traceback.format_exc()
)
```

### Log Levels

- **DEBUG**: Detailed diagnostic info (off in production)
- **INFO**: General informational messages
- **WARNING**: Warning messages, non-critical issues
- **ERROR**: Error messages, exceptions
- **CRITICAL**: Critical failures

### What to Log

✅ **DO Log**:
- Request/response (method, path, status, duration)
- Database queries (slow queries)
- External API calls
- Errors and exceptions with context
- Important business events
- Performance metrics

❌ **DON'T Log**:
- Passwords or secrets
- Full credit card numbers
- Personal information (PII)
- Full request/response bodies (use IDs instead)

### Example Logging in Routes

```python
from fastapi import APIRouter
import structlog

router = APIRouter()
logger = structlog.get_logger()

@router.post("/resources/")
async def create_resource(resource: ResourceCreate):
    logger.info("create_resource_started", resource_name=resource.name)

    try:
        result = resource_service.create(db, resource)
        logger.info(
            "create_resource_success",
            resource_id=result.id,
            resource_name=result.name
        )
        return result
    except Exception as e:
        logger.error(
            "create_resource_failed",
            error=str(e),
            resource_name=resource.name,
            traceback=traceback.format_exc()
        )
        raise
```

---

## Test Data Management

### Factories (using factory_boy)

```python
import factory
from src.models import Resource

class ResourceFactory(factory.Factory):
    class Meta:
        model = Resource

    name = factory.Faker('company')
    description = factory.Faker('text', max_nb_chars=200)

# Usage in tests
resource = ResourceFactory()
resources = ResourceFactory.create_batch(10)
```

### Fixtures vs Factories

**Fixtures**: Fixed, predictable test data
```python
@pytest.fixture
def admin_user():
    return User(name="Admin", role="admin")
```

**Factories**: Generate varied test data
```python
user = UserFactory()  # Different data each time
```

---

## Async Tests

### Testing Async Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_service.process()
    assert result is not None
```

---

## Test Organization Best Practices

### AAA Pattern (Arrange, Act, Assert)

```python
def test_example():
    # Arrange - Set up test data
    user = User(name="Test")

    # Act - Execute the code being tested
    result = user.get_display_name()

    # Assert - Verify the result
    assert result == "Test"
```

### One Assertion Per Test (Generally)

❌ **Bad**:
```python
def test_user():
    user = create_user()
    assert user.name == "Test"
    assert user.email == "test@example.com"
    assert user.is_active == True
```

✅ **Good**:
```python
def test_user_name():
    user = create_user()
    assert user.name == "Test"

def test_user_email():
    user = create_user()
    assert user.email == "test@example.com"

def test_user_is_active():
    user = create_user()
    assert user.is_active == True
```

### Test Names Should Be Descriptive

✅ **Good**:
```python
def test_create_resource_with_invalid_name_raises_validation_error()
def test_get_resource_returns_404_when_not_found()
def test_update_resource_updates_only_provided_fields()
```

❌ **Bad**:
```python
def test_resource()
def test_get()
def test_update()
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
        with:
          file: ./coverage.xml
```

---

## Quick Checklist

When adding new functionality:

- [ ] Write tests FIRST (TDD) if possible
- [ ] Test happy path
- [ ] Test error cases
- [ ] Test edge cases
- [ ] Mock external dependencies
- [ ] Add logging with context
- [ ] Check test coverage (aim for 80%+)
- [ ] Run tests locally before committing
- [ ] Tests pass in CI/CD

---

## Common Patterns

### Test Database Cleanup

```python
@pytest.fixture(autouse=True)
def cleanup_db(db_session):
    """Clean up database after each test."""
    yield
    db_session.rollback()
```

### Temporary Files

```python
import tempfile

def test_file_processing():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.txt"
        file_path.write_text("test content")
        # Test logic here
    # tmpdir automatically cleaned up
```

### Environment Variables in Tests

```python
@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-key")
    monkeypatch.setenv("DEBUG", "true")
```

---

## Debugging Tests

```bash
# Print stdout
pytest -s

# Drop into debugger on failure
pytest --pdb

# Verbose output
pytest -vv

# Show local variables on failure
pytest -l --tb=long
```

---

This covers 90% of testing scenarios you'll encounter. Reference this document when writing tests!
