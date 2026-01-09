# Security Practices

**Load this when**: Working on authentication, API security, data handling, or deployment

---

## Security Mindset

**Assume breach**: Design systems assuming attackers will find vulnerabilities.

**Defense in depth**: Multiple layers of security, not single points of failure.

**Principle of least privilege**: Grant minimum necessary permissions.

---

## OWASP Top 10 (2021)

The most critical web application security risks:

1. **Broken Access Control**
2. **Cryptographic Failures**
3. **Injection**
4. **Insecure Design**
5. **Security Misconfiguration**
6. **Vulnerable and Outdated Components**
7. **Identification and Authentication Failures**
8. **Software and Data Integrity Failures**
9. **Security Logging and Monitoring Failures**
10. **Server-Side Request Forgery (SSRF)**

---

## 1. Broken Access Control

### Problem
Users accessing resources they shouldn't.

### Prevention

#### Enforce Authorization Checks

```python
from fastapi import Depends, HTTPException

async def verify_resource_owner(
    resource_id: int,
    user = Depends(get_current_user),
    db = Depends(get_db)
):
    """Verify user owns the resource."""
    resource = get_resource(db, resource_id)
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return resource

@router.delete("/resources/{resource_id}")
async def delete_resource(
    resource = Depends(verify_resource_owner)
):
    """Only owner can delete."""
    delete(resource)
    return {"status": "deleted"}
```

#### Role-Based Access Control (RBAC)

```python
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

def require_role(required_role: Role):
    async def check_role(user = Depends(get_current_user)):
        if user.role != required_role:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return check_role

@router.post("/admin/users")
async def create_user(
    user_data: UserCreate,
    admin = Depends(require_role(Role.ADMIN))
):
    """Admin-only endpoint."""
    return create_user(user_data)
```

---

## 2. Cryptographic Failures

### Problem
Sensitive data exposed due to weak or missing encryption.

### Prevention

#### Never Store Passwords in Plaintext

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)
```

#### Use Environment Variables for Secrets

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str                    # JWT signing key
    database_password: str
    api_key: str

    class Config:
        env_file = ".env"

settings = Settings()

# ❌ DON'T
SECRET_KEY = "hardcoded-secret"

# ✅ DO
SECRET_KEY = settings.secret_key
```

#### Encrypt Sensitive Data at Rest

```python
from cryptography.fernet import Fernet

# Generate key (store in environment)
key = Fernet.generate_key()
cipher = Fernet(key)

def encrypt_data(data: str) -> bytes:
    """Encrypt sensitive data."""
    return cipher.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes) -> str:
    """Decrypt sensitive data."""
    return cipher.decrypt(encrypted_data).decode()
```

---

## 3. Injection Attacks

### Problem
Attacker injects malicious code (SQL, NoSQL, OS commands).

### Prevention

#### SQL Injection - Use Parameterized Queries

```python
# ❌ VULNERABLE - Never do this
query = f"SELECT * FROM users WHERE username = '{username}'"

# ✅ SAFE - Use SQLAlchemy ORM
user = db.query(User).filter(User.username == username).first()

# ✅ SAFE - Or parameterized raw SQL
query = text("SELECT * FROM users WHERE username = :username")
result = db.execute(query, {"username": username})
```

#### Command Injection - Avoid os.system()

```python
import subprocess

# ❌ VULNERABLE
os.system(f"ping {user_input}")

# ✅ SAFER - Use subprocess with list
subprocess.run(["ping", "-c", "1", user_input], check=True)

# ✅ BEST - Validate and sanitize input
if not re.match(r'^[\w\.-]+$', user_input):
    raise ValueError("Invalid input")
subprocess.run(["ping", "-c", "1", user_input], check=True)
```

#### NoSQL Injection - Validate Input

```python
# ❌ VULNERABLE
db.collection.find({"username": user_input})

# ✅ SAFE - Validate with Pydantic
from pydantic import BaseModel, validator

class UserQuery(BaseModel):
    username: str

    @validator('username')
    def validate_username(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Invalid username format')
        return v
```

---

## 4. Input Validation

### Always Validate User Input

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., regex=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: Optional[int] = Field(None, ge=0, le=150)

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('must be alphanumeric')
        return v
```

### Sanitize HTML Input

```python
from bleach import clean

def sanitize_html(html: str) -> str:
    """Remove potentially dangerous HTML."""
    allowed_tags = ['p', 'br', 'strong', 'em', 'u']
    return clean(html, tags=allowed_tags, strip=True)
```

---

## 5. Authentication & Authorization

### JWT Token Best Practices

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict) -> str:
    """Create JWT token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> dict:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Token Security

✅ **DO**:
- Use short expiration times (15-30 min)
- Use refresh tokens for long sessions
- Store tokens securely (httpOnly cookies or secure storage)
- Invalidate tokens on logout
- Rotate secrets periodically

❌ **DON'T**:
- Store tokens in localStorage (XSS risk)
- Use weak signing keys
- Put sensitive data in JWT payload (it's visible!)
- Reuse tokens across different apps

---

## 6. Rate Limiting

### Prevent Brute Force and DoS

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(credentials: LoginCredentials):
    """Max 5 login attempts per minute."""
    return authenticate(credentials)
```

---

## 7. CORS Configuration

### Restrict Origins

```python
from fastapi.middleware.cors import CORSMiddleware

# ❌ DANGEROUS - Don't allow all origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Never use in production!
)

# ✅ SAFE - Specify allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://myapp.com",
        "https://www.myapp.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

---

## 8. Secure Headers

### Add Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware import Middleware

middleware = [
    Middleware(
        TrustedHostMiddleware,
        allowed_hosts=["example.com", "*.example.com"]
    )
]

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## 9. File Upload Security

### Validate File Uploads

```python
from fastapi import UploadFile
import magic

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_file(file: UploadFile):
    """Validate uploaded file."""
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="File type not allowed")

    # Check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    # Verify actual file type (not just extension)
    file_type = magic.from_buffer(contents, mime=True)
    if not file_type.startswith(('image/', 'application/pdf')):
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Reset file pointer
    await file.seek(0)
    return file

@app.post("/upload")
async def upload_file(file: UploadFile = Depends(validate_file)):
    """Upload with validation."""
    # Save file securely
    safe_filename = secure_filename(file.filename)
    file_path = UPLOAD_DIR / safe_filename
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"filename": safe_filename}
```

---

## 10. Logging & Monitoring

### Security Event Logging

```python
import structlog

logger = structlog.get_logger()

# Log security events
def log_security_event(event_type: str, **kwargs):
    logger.warning(
        "security_event",
        event_type=event_type,
        timestamp=datetime.utcnow().isoformat(),
        **kwargs
    )

# Usage
log_security_event(
    "failed_login_attempt",
    username=username,
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent")
)

log_security_event(
    "unauthorized_access",
    user_id=user.id,
    resource=resource_id,
    action="delete"
)
```

### What to Log

✅ **DO Log**:
- Failed login attempts
- Authorization failures
- Suspicious patterns
- Admin actions
- Data access/modifications
- Configuration changes

❌ **DON'T Log**:
- Passwords (even hashed!)
- API keys or tokens
- Credit card numbers
- SSN or personal ID numbers

---

## 11. Dependency Security

### Keep Dependencies Updated

```bash
# Check for vulnerabilities
pip install safety
safety check

# Or use pip-audit
pip install pip-audit
pip-audit
```

### Pin Dependency Versions

```python
# requirements.txt
fastapi==0.104.1      # Pin exact versions
pydantic==2.5.0
sqlalchemy==2.0.23

# Not:
fastapi>=0.104.1      # Can introduce breaking changes
```

---

## 12. API Security

### API Keys

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    """Verify API key."""
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@router.get("/api/data")
async def get_data(api_key: str = Depends(verify_api_key)):
    """Protected endpoint."""
    return {"data": "secret"}
```

### Request Size Limits

```python
from fastapi import Request, HTTPException

MAX_REQUEST_SIZE = 1024 * 1024  # 1MB

@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    if request.headers.get("content-length"):
        if int(request.headers["content-length"]) > MAX_REQUEST_SIZE:
            raise HTTPException(status_code=413, detail="Request too large")
    return await call_next(request)
```

---

## 13. Database Security

### Connection Security

```python
# Use SSL for database connections
DATABASE_URL = "postgresql://user:pass@host:5432/db?sslmode=require"
```

### Least Privilege

```sql
-- Create app user with limited permissions
CREATE USER app_user WITH PASSWORD 'secure_password';
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user;

-- Don't grant DROP, CREATE, ALTER
```

---

## 14. Environment-Specific Security

### Development vs Production

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    debug: bool = False
    environment: str = "production"

    # Different settings per environment
    cors_origins: list[str] = ["https://prod.com"]

    class Config:
        env_file = ".env"

settings = Settings()

# In production
assert settings.environment == "production"
assert settings.debug == False
```

---

## Security Checklist

When deploying to production:

- [ ] All secrets in environment variables (never committed)
- [ ] HTTPS enabled (TLS/SSL certificates)
- [ ] CORS configured (no wildcard origins)
- [ ] Rate limiting enabled
- [ ] Security headers added
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (ORM or parameterized queries)
- [ ] Authentication implemented
- [ ] Authorization checks on protected resources
- [ ] Passwords hashed (bcrypt/argon2)
- [ ] File upload validation
- [ ] Logging enabled (no sensitive data)
- [ ] Dependencies updated and audited
- [ ] Database connections encrypted
- [ ] Error messages don't leak sensitive info
- [ ] Debug mode disabled

---

## Common Vulnerabilities to Avoid

### Information Disclosure

```python
# ❌ DON'T expose internal errors
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return {"error": str(exc), "traceback": traceback.format_exc()}

# ✅ DO return generic messages
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error("Internal error", error=str(exc), traceback=traceback.format_exc())
    return {"error": "Internal server error"}
```

### Timing Attacks

```python
import hmac

# ❌ VULNERABLE to timing attacks
if user_token == expected_token:
    return True

# ✅ SAFE - constant time comparison
if hmac.compare_digest(user_token, expected_token):
    return True
```

### Mass Assignment

```python
# ❌ DANGEROUS - user could set is_admin=True
@router.patch("/users/{user_id}")
async def update_user(user_id: int, user_data: dict):
    update_user(user_id, **user_data)  # Accepts ANY field!

# ✅ SAFE - only allow specific fields
class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    # is_admin NOT included

@router.patch("/users/{user_id}")
async def update_user(user_id: int, user_data: UserUpdate):
    update_user(user_id, user_data)  # Only allowed fields
```

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Python Security Best Practices](https://snyk.io/blog/python-security-best-practices/)

---

**Security is not a feature, it's a requirement. Build it in from the start.**
