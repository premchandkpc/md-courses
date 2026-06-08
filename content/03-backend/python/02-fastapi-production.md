# FastAPI Production Deep Dive


```mermaid
graph LR
    CLI["HTTP<br/>Request"] --> UVICORN["Uvicorn<br/>(ASGI Server)"]
    UVICORN --> ASGI["ASGI<br/>Protocol"]
    ASGI --> FAST["FastAPI<br/>App"]
    FAST --> ROUT["Router<br/>Path Matching"]
    ROUT --> DEP["Dependency<br/>Injection"]
    DEP --> EP["Endpoint<br/>Handler"]
    EP --> MOD["Pydantic<br/>Model Validation"]
    EP --> ASYNC["Async DB /<br/>External API"]
    ASYNC --> RESP["JSON<br/>Response"]
    style CLI fill:#4a8bc2
    style UVICORN fill:#2d5a7b
    style ASGI fill:#3a7ca5
    style FAST fill:#c73e1d
    style ROUT fill:#e8912e
    style DEP fill:#6f42c1
    style EP fill:#3fb950
    style MOD fill:#2d5a7b
    style ASYNC fill:#3a7ca5
    style RESP fill:#e8912e
```

## ASGI Fundamentals


FastAPI is built on ASGI (Asynchronous Server Gateway Interface), the successor to WSGI:

```python
# ASGI application signature
async def application(scope, receive, send):
    """
    scope: dict with connection metadata
    receive: async callable to receive events
    send: async callable to send events
    """
    assert scope["type"] == "http"

    await send({
        "type": "http.response.start",
        "status": 200,
        "headers": [
            (b"content-type", b"application/json"),
        ],
    })
    await send({
        "type": "http.response.body",
        "body": b'{"message": "Hello ASGI"}',
    })

# Lifespan protocol
async def lifespan_app(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                print("Starting up...")
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                print("Shutting down...")
                await send({"type": "lifespan.shutdown.complete"})
                return
```

### ASGI vs WSGI


```python
# WSGI application
def wsgi_app(environ, start_response):
    status = "200 OK"
    headers = [("Content-Type", "application/json")]
    start_response(status, headers)
    return [b'{"message": "Hello WSGI"}']
```

---

## Starlette Internals


### Routing


```python
from starlette.applications import Starlette
from starlette.routing import Route, Mount, WebSocketRoute
from starlette.responses import JSONResponse
from starlette.requests import Request

async def homepage(request):
    return JSONResponse({"page": "home"})

async def user_detail(request):
    user_id = request.path_params["user_id"]
    return JSONResponse({"user_id": user_id})

async def websocket_endpoint(websocket):
    await websocket.accept()
    async for message in websocket.iter_text():
        await websocket.send_text(f"Echo: {message}")

app = Starlette(routes=[
    Route("/", endpoint=homepage),
    Route("/users/{user_id:int}", endpoint=user_detail),
    WebSocketRoute("/ws", endpoint=websocket_endpoint),
    Mount("/static", app=StaticFiles(directory="static")),
])
```

### Middleware


```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware import Middleware
import time

class ProcessTimeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = str(elapsed)
        return response

async def cache_control_middleware(request, call_next):
    response = await call_next(request)
    if request.method == "GET" and response.status_code == 200:
        response.headers["Cache-Control"] = "public, max-age=300"
    return response

app = Starlette(
    routes=[Route("/", endpoint=homepage)],
    middleware=[
        Middleware(ProcessTimeMiddleware),
        Middleware(TrustedHostMiddleware, allowed_hosts=["example.com", "*.example.com"]),
    ]
)
```

---

## Pydantic v2 Deep Dive


### Rust Core (pydantic-core)


Pydantic v2 moved validation to Rust (pydantic-core), providing 5-50x speedups:

```python
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional, Annotated
from pydantic.functional_validators import AfterValidator
import time

class User(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=100)
    email: str
    tags: List[str] = []
    score: Annotated[float, AfterValidator(lambda v: round(v, 2))]

    model_config = {
        "extra": "forbid",
        "frozen": True,
        "validate_default": True,
        "use_enum_values": True,
    }

# Benchmark Pydantic v2 speed
data = {"id": 1, "name": "Alice", "email": "alice@example.com", "tags": ["dev", "ops"], "score": 3.14159}
start = time.perf_counter()
for _ in range(100000):
    user = User(**data)
print(f"Pydantic v2: 100k creations in {time.perf_counter() - start:.3f}s")
```

### Validation and Serialization


```python
from pydantic import BaseModel, field_validator, model_validator, field_serializer
from datetime import datetime
from typing import Any

class Transaction(BaseModel):
    amount: float
    currency: str = "USD"
    timestamp: datetime
    metadata: dict[str, Any] = {}

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v > 1_000_000:
            raise ValueError("Amount exceeds limit")
        return round(v, 2)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v):
        if len(v) != 3:
            raise ValueError("Currency must be ISO 4217 format")
        return v.upper()

    @model_validator(mode="after")
    def validate_transaction(self):
        if self.currency == "BTC" and self.amount > 100:
            raise ValueError("BTC transactions limited to 100")
        return self

    @field_serializer("timestamp")
    def serialize_timestamp(self, dt: datetime) -> str:
        return dt.isoformat()

    @field_serializer("amount")
    def serialize_amount(self, v: float) -> float:
        return round(v, 2)

try:
    Transaction(amount=-10, currency="USD", timestamp=datetime.now())
except ValidationError as e:
    print(e.errors())
```

### Nested Models and Complex Types


```python
from pydantic import BaseModel
from typing import List, Optional, Union
from enum import Enum

class AddressType(str, Enum):
    HOME = "home"
    WORK = "work"
    BILLING = "billing"

class Address(BaseModel):
    type: AddressType
    street: str
    city: str
    country: str
    postal_code: str
    is_primary: bool = False

class ContactInfo(BaseModel):
    email: str
    phone: Optional[str] = None
    addresses: List[Address] = []

class Employee(BaseModel):
    id: int
    name: str
    department: str
    contact: ContactInfo
    manager_id: Optional[int] = None
    reports: List[int] = []

    model_config = {"json_schema_extra": {"example": {
        "id": 1,
        "name": "John",
        "department": "Engineering",
        "contact": {
            "email": "john@example.com",
            "addresses": [{"type": "home", "street": "123 Main", "city": "NYC", "country": "US", "postal_code": "10001"}]
        }
    }}}

data = {
    "id": 1,
    "name": "Alice Smith",
    "department": "Engineering",
    "contact": {
        "email": "alice@example.com",
        "phone": "+1-555-0100",
        "addresses": [
            {"type": "work", "street": "456 Tech Blvd", "city": "San Francisco", "country": "US", "postal_code": "94105", "is_primary": True}
        ]
    },
    "reports": [2, 3]
}

emp = Employee(**data)
print(emp.model_dump_json(indent=2))
print(emp.model_dump(by_alias=True))
```

### JSON Schema Generation


```python
from pydantic import BaseModel, Field
from typing import Annotated
import json

class PaginatedRequest(BaseModel):
    page: Annotated[int, Field(ge=1, le=1000)] = 1
    per_page: Annotated[int, Field(ge=1, le=100)] = 20
    sort_by: str = "created_at"
    sort_order: str = "desc"

    model_config = {
        "json_schema_extra": {
            "description": "Paginated list request parameters",
            "x-example": {"page": 1, "per_page": 20, "sort_by": "name", "sort_order": "asc"}
        }
    }

class ErrorResponse(BaseModel):
    code: int
    message: str
    details: dict | None = None

schema = PaginatedRequest.model_json_schema()
print(json.dumps(schema, indent=2))
```

---

## FastAPI Application Structure


### Dependency Injection


```python
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from typing import Annotated, AsyncGenerator
from contextlib import asynccontextmanager
import asyncpg

# Database dependency
class DatabasePool:
    def __init__(self):
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            user="postgres",
            password="secret",
            database="app",
            host="localhost",
            min_size=5,
            max_size=20,
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def get_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        async with self.pool.acquire() as conn:
            yield conn

db = DatabasePool()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.disconnect()

app = FastAPI(lifespan=lifespan)
```

### Dependency Hierarchy


```python
from fastapi import Depends, FastAPI, HTTPException, Request
from typing import Annotated
import hashlib
import hmac
import time

class AuthService:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def verify_token(self, token: str) -> dict:
        try:
            parts = token.split(".")
            payload = parts[1]
            expected_sig = hmac.new(
                self.secret_key.encode(), payload.encode(), hashlib.sha256
            ).hexdigest()
            if parts[2] != expected_sig:
                raise ValueError("Invalid signature")
            return {"user_id": int(payload.split(":")[0])}
        except (IndexError, ValueError):
            raise HTTPException(status_code=401, detail="Invalid token")

auth_service = AuthService(secret_key="super-secret")

async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing authorization")
    token = authorization.replace("Bearer ", "")
    return auth_service.verify_token(token)

async def require_admin(user: Annotated[dict, Depends(get_current_user)]):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin required")
    return user

async def pagination_params(
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    return {"page": page, "per_page": per_page, "offset": (page - 1) * per_page}

@ app.get("/users/me")
async def get_current_user_profile(
    user: Annotated[dict, Depends(get_current_user)]
):
    return {"user_id": user["user_id"]}

@ app.get("/admin/dashboard")
async def admin_dashboard(
    admin: Annotated[dict, Depends(require_admin)],
    pagination: Annotated[dict, Depends(pagination_params)],
):
    return {"admin": admin, "pagination": pagination}
```

### Routing and Path Operations


```python
from fastapi import APIRouter, FastAPI, Path, Query, Body, HTTPException, status
from typing import Annotated

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@ router.get("/")
async def list_users(
    pagination: Annotated[dict, Depends(pagination_params)],
    search: Annotated[str | None, Query(max_length=100)] = None,
):
    """List users with pagination and search."""
    users = [
        {"id": i, "name": f"User {i}"}
        for i in range(pagination["offset"], pagination["offset"] + pagination["per_page"])
    ]
    if search:
        users = [u for u in users if search.lower() in u["name"].lower()]
    return {"items": users, "total": 1000, "page": pagination["page"]}

@ router.get("/{user_id}")
async def get_user(
    user_id: Annotated[int, Path(ge=1, le=1000000)],
):
    """Get a specific user by ID."""
    return {"id": user_id, "name": f"User {user_id}"}

@ router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: Annotated[User, Body()],
):
    """Create a new user."""
    return {"id": 123, **user.model_dump()}

@ router.put("/{user_id}")
async def update_user(
    user_id: Annotated[int, Path()],
    user: Annotated[User, Body()],
):
    """Update an existing user."""
    return {"id": user_id, **user.model_dump()}

@ router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: Annotated[int, Path()]):
    """Delete a user."""
    return None

app.include_router(router)
```

---

## Async Patterns


### SQLAlchemy Async


```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import select, text
from typing import AsyncGenerator

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/db"
engine = create_async_engine(DATABASE_URL, echo=True, pool_size=10, max_overflow=20)
async_session = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()

@ app.get("/async/users")
async def get_users(session: Annotated[AsyncSession, Depends(get_session)]):
    result = await session.execute(select(User).limit(10))
    users = result.scalars().all()
    return users

@ app.post("/async/users")
async def create_user(user_data: User, session: Annotated[AsyncSession, Depends(get_session)]):
    user = User(**user_data.model_dump())
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
```

### asyncpg Direct Usage


```python
import asyncpg
from typing import AsyncGenerator

class DatabaseManager:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            self.dsn,
            min_size=10,
            max_size=50,
            command_timeout=5,
            max_inactive_connection_lifetime=300,
        )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()

    async def fetch(self, query: str, *args) -> list:
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> asyncpg.Record | None:
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute(self, query: str, *args) -> str:
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def execute_many(self, query: str, args: list[tuple]) -> None:
        async with self.pool.acquire() as conn:
            await conn.executemany(query, args)

db = DatabaseManager("postgresql://user:pass@localhost/db")
```

### HTTP Clients


```python
import httpx
import asyncio
from typing import AsyncGenerator

class HTTPClient:
    def __init__(self, base_url: str, timeout: float = 10.0):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def get_json(self, path: str, **params) -> dict:
        response = await self.client.get(path, params=params)
        response.raise_for_status()
        return response.json()

    async def post_json(self, path: str, data: dict = None) -> dict:
        response = await self.client.post(path, json=data)
        response.raise_for_status()
        return response.json()

    async def stream_events(self, path: str) -> AsyncGenerator[dict, None]:
        async with self.client.stream("GET", path) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield json.loads(line[6:])

async def concurrent_requests():
    urls = [
        "https://api.github.com/repos/python/cpython",
        "https://api.github.com/repos/fastapi/fastapi",
        "https://api.github.com/repos/pydantic/pydantic",
    ]
    async with httpx.AsyncClient() as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
    return [r.json()["stargazers_count"] for r in responses]
```

### Background Tasks


```python
from fastapi import BackgroundTasks, FastAPI
from typing import Callable
import asyncio
import logging

logger = logging.getLogger(__name__)

class BackgroundTaskManager:
    def __init__(self):
        self._tasks = set()

    def add_task(self, coro):
        task = asyncio.create_task(self._run_and_log(coro))
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _run_and_log(self, coro):
        try:
            await coro
        except Exception as e:
            logger.error(f"Background task failed: {e}", exc_info=True)

    async def shutdown(self):
        if self._tasks:
            for task in self._tasks:
                task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)

task_manager = BackgroundTaskManager()

async def send_email(to: str, subject: str, body: str):
    await asyncio.sleep(2)  # Simulate email sending
    logger.info(f"Email sent to {to}: {subject}")

@app.post("/notify")
async def notify_user(email: str, message: str):
    task_manager.add_task(send_email(email, "Notification", message))
    return {"status": "queued"}

@app.on_event("shutdown")
async def shutdown():
    await task_manager.shutdown()
```

---

## Production Middleware


```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
import time
import uuid

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.example.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Request-ID"],
    max_age=3600,
)

# Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["api.example.com", "*.example.com", "localhost"],
)

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        method = request.method
        path = request.url.path
        status = response.status_code
        logger.info(f"{method} {path} {status} {elapsed:.4f}s")
        return response

app.add_middleware(RequestIDMiddleware)
app.add_middleware(MetricsMiddleware)
```

### Logging Configuration


```python
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)
logger.propagate = False
```

### Metrics with Prometheus


```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response
import time

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active",
    "Number of active HTTP requests",
)

class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        method = request.method
        endpoint = request.url.path
        ACTIVE_REQUESTS.inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
            REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=response.status_code).inc()
            return response
        finally:
            elapsed = time.perf_counter() - start
            REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(elapsed)
            ACTIVE_REQUESTS.dec()

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    # ... same logic using class-based middleware above
    pass

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### Tracing with OpenTelemetry


```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

span_processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
)
trace.get_tracer_provider().add_span_processor(span_processor)

# Auto-instrumentation
FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument(engine=engine)

# Manual tracing
@app.get("/traced")
async def traced_endpoint():
    with tracer.start_as_current_span("database_query") as span:
        span.set_attribute("db.system", "postgresql")
        span.set_attribute("db.query", "SELECT * FROM users")
        result = await execute_query()
        span.set_attribute("db.row_count", len(result))
    return result
```

---

## API Design


### Versioning


```python
from fastapi import APIRouter, FastAPI
from fastapi.responses import JSONResponse

# URL-based versioning
v1_router = APIRouter(prefix="/api/v1", tags=["v1"])
v2_router = APIRouter(prefix="/api/v2", tags=["v2"])

@v1_router.get("/users")
async def list_users_v1():
    return {"users": [{"id": 1, "name": "User"}], "version": "v1"}

@v2_router.get("/users")
async def list_users_v2():
    return {"items": [{"id": 1, "name": "User", "email": "user@example.com"}], "version": "v2"}

app.include_router(v1_router)
app.include_router(v2_router)

# Header-based versioning
async def version_middleware(request: Request, call_next):
    version = request.headers.get("Accept-Version", "v1")
    request.state.api_version = version
    return await call_next(request)
```

### Error Handling


```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request.headers.get("X-Request-ID"),
            }
        },
    )

@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )

@app.exception_handler(Exception)
async def general_error_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )
```

### Pagination


```python
from fastapi import Query
from typing import Annotated, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool

class CursorPaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
    previous_cursor: str | None
    has_more: bool

# Offset-based pagination
async def paginate(query, page: int, per_page: int):
    total = await query.count()
    items = await query.offset((page - 1) * per_page).limit(per_page).fetch()
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
        has_next=(page * per_page) < total,
        has_prev=page > 1,
    )

# Cursor-based pagination
async def cursor_paginate(query, cursor: str | None, limit: int):
    if cursor:
        decoded = decode_cursor(cursor)
        items = await query.filter(id > decoded).limit(limit + 1).fetch()
    else:
        items = await query.limit(limit + 1).fetch()

    has_more = len(items) > limit
    items = items[:limit]
    next_cursor = encode_cursor(items[-1].id) if has_more and items else None

    return CursorPaginatedResponse(
        items=items,
        next_cursor=next_cursor,
        previous_cursor=None,
        has_more=has_more,
    )
```

### Rate Limiting


```python
import time
from collections import defaultdict
from fastapi import FastAPI, Request, HTTPException

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()

    def consume(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False

class RateLimiter:
    def __init__(self):
        self._buckets: dict[str, TokenBucket] = {}

    def check(self, key: str, rate: float, capacity: int) -> bool:
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(rate, capacity)
        return self._buckets[key].consume()

rate_limiter = RateLimiter()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    key = f"ip:{client_ip}"

    if not rate_limiter.check(key, rate=10, capacity=20):
        raise HTTPException(status_code=429, detail="Too many requests")

    return await call_next(request)

# Per-endpoint rate limiting
@app.get("/expensive")
async def expensive_endpoint(request: Request):
    key = f"endpoint:expensive:{request.client.host}"
    if not rate_limiter.check(key, rate=1, capacity=1):
        raise HTTPException(status_code=429, detail="Rate limit: 1 request per second")
    return {"data": "expensive computation"}
```

---

## Authentication


### JWT Implementation


```python
from datetime import datetime, timedelta, timezone
from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from passlib.context import CryptContext

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class JWTService:
    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: dict):
        return JWTService.create_access_token(data, expires_delta=timedelta(days=7))

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

jwt_service = JWTService()

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    return jwt_service.decode_token(credentials.credentials)

@app.post("/token")
async def login(username: str, password: str):
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = jwt_service.create_access_token(
        data={"sub": user["id"], "role": user["role"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = jwt_service.create_refresh_token({"sub": user["id"]})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

@app.post("/refresh")
async def refresh_token(refresh_token: str):
    payload = jwt_service.decode_token(refresh_token)
    new_token = jwt_service.create_access_token(
        data={"sub": payload["sub"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": new_token, "token_type": "bearer"}
```

### OAuth2 with Social Providers


```python
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request

config = Config(".env")
oauth = OAuth(config)

oauth.register(
    name="google",
    client_id="google-client-id",
    client_secret="google-client-secret",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="github",
    client_id="github-client-id",
    client_secret="github-client-secret",
    access_token_url="https://github.com/login/oauth/access_token",
    access_token_params=None,
    authorize_url="https://github.com/login/oauth/authorize",
    authorize_params=None,
    client_kwargs={"scope": "user:email"},
)

@app.get("/auth/{provider}/login")
async def oauth_login(request: Request, provider: str):
    redirect_uri = request.url_for("oauth_callback", provider=provider)
    return await oauth.create_client(provider).authorize_redirect(request, redirect_uri)

@app.get("/auth/{provider}/callback")
async def oauth_callback(request: Request, provider: str):
    token = await oauth.create_client(provider).authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        user_info = await oauth.create_client(provider).userinfo(token=token)
    return {"user": user_info}
```

---

## Performance Optimization


### Profiling FastAPI


```python
from fastapi import FastAPI, Request
from pyinstrument import Profiler
from pyinstrument.renderers import HTMLRenderer
import time

app = FastAPI()

@app.middleware("http")
async def profile_middleware(request: Request, call_next):
    if request.headers.get("X-Profile") == "1":
        profiler = Profiler()
        profiler.start()
        response = await call_next(request)
        profiler.stop()
        html = profiler.output(HTMLRenderer())
        with open(f"profiles/{time.time()}.html", "w") as f:
            f.write(html)
        response.headers["X-Profile-Saved"] = "true"
    else:
        response = await call_next(request)
    return response

# Context manager for manual profiling
import contextlib

@contextlib.contextmanager
def profile_endpoint(name: str):
    profiler = Profiler()
    profiler.start()
    yield
    profiler.stop()
    print(f"Profile for {name}:")
    profiler.print()
```

### Database Connection Pooling


```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool, QueuePool, AsyncAdaptedQueuePool

# Connection pool tuning
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    pool_size=20,           # Number of connections to maintain
    max_overflow=10,         # Additional connections allowed beyond pool_size
    pool_pre_ping=True,      # Verify connections before using
    pool_recycle=3600,       # Recycle connections after 1 hour
    pool_use_lifo=True,      # Use LIFO for better cache locality
    echo_pool=True,          # Log pool events
)

# For serverless/FAAS, use NullPool
serverless_engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    poolclass=NullPool,      # Don't maintain a persistent pool
)

# Pool metrics
from sqlalchemy import event

@event.listens_for(engine.sync_engine, "connect")
def connect(dbapi_connection, connection_record):
    print(f"New connection established")

@event.listens_for(engine.sync_engine, "checkout")
def checkout(dbapi_connection, connection_record, connection_proxy):
    print(f"Connection checked out from pool")

@event.listens_for(engine.sync_engine, "checkin")
def checkin(dbapi_connection, connection_record):
    print(f"Connection returned to pool")
```

### Response Caching


```python
from functools import lru_cache
from fastapi import FastAPI, Response
from aiocache import Cache, cached
from aiocache.serializers import JsonSerializer
import hashlib

# In-memory LRU
@lru_cache(maxsize=128)
def expensive_computation(param: int) -> dict:
    result = sum(i ** 2 for i in range(param))
    return {"input": param, "result": result, "computed": True}

@app.get("/compute/{param}")
async def compute(param: int):
    return expensive_computation(param)

# Distributed caching with Redis
cache = Cache(Cache.REDIS, endpoint="localhost", port=6379, serializer=JsonSerializer())

@cached(ttl=300, cache=Cache.REDIS, key_builder=lambda f, *a, **kw: f"users:{a[0]}")
async def get_user_from_db(user_id: int):
    # Simulated database query
    return {"id": user_id, "name": f"User {user_id}"}

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    return await get_user_from_db(user_id)
```

### Async vs Sync Endpoints


```python
import asyncio
import time
from fastapi import FastAPI
from concurrent.futures import ThreadPoolExecutor
import anyio

executor = ThreadPoolExecutor(max_workers=4)

# Sync endpoint blocks the event loop
@app.get("/sync")
def sync_endpoint():
    time.sleep(1)
    return {"type": "sync"}

# Async endpoint releases the GIL during I/O
@app.get("/async")
async def async_endpoint():
    await asyncio.sleep(1)
    return {"type": "async"}

# Sync CPU-bound work offloaded to thread pool
@app.get("/cpu-intensive")
async def cpu_intensive():
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(executor, expensive_cpu_work)
    return {"result": result}

def expensive_cpu_work():
    return sum(i ** 2 for i in range(10_000_000))

# Using anyio for cross-backend compatibility
@app.get("/anyio")
async def anyio_endpoint():
    async with anyio.create_task_group() as tg:
        async def worker(n):
            await anyio.sleep(n)
            print(f"Worker {n} done")
        tg.start_soon(worker, 1)
        tg.start_soon(worker, 2)
```

---

## Testing


### httpx TestClient


```python
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import pytest
import pytest_asyncio

app = FastAPI()

# Sync test client
client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_user():
    response = client.post(
        "/users",
        json={"name": "Alice", "email": "alice@example.com"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alice"

def test_unauthorized():
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization"
```

### Async TestClient


```python
@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    response = await async_client.get("/async/endpoint")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_concurrent_requests(async_client):
    async def make_request():
        return await async_client.get("/async/endpoint")

    results = await asyncio.gather(*[make_request() for _ in range(10)])
    assert all(r.status_code == 200 for r in results)
```

### Dependency Overrides


```python
from typing import Annotated

# Production dependency
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session

# Override for testing
_test_db = []

async def get_test_db():
    yield _test_db

app.dependency_overrides[get_db_session] = get_test_db

@pytest.mark.asyncio
async def test_with_overrides():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/users")
        assert response.status_code == 200

# Clear overrides after test
app.dependency_overrides.clear()
```

### Fixtures


```python
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, patch

@pytest.fixture
def sample_user() -> dict:
    return {
        "id": 1,
        "name": "Alice Smith",
        "email": "alice@example.com",
        "role": "user",
    }

@pytest.fixture
def admin_user() -> dict:
    return {
        "id": 2,
        "name": "Admin",
        "email": "admin@example.com",
        "role": "admin",
    }

@pytest_asyncio.fixture
async def mock_db_session():
    """Creates a mock database session with fake data."""
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock query results
    mock_result = AsyncMock()
    mock_result.scalars.return_value.all.return_value = [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
    mock_session.execute.return_value = mock_result

    yield mock_session

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Setup and teardown for each test."""
    await setup_test_db()
    yield
    await teardown_test_db()

@pytest.fixture(scope="session")
def db_engine():
    """Database engine shared across all tests."""
    engine = create_async_engine("sqlite+aiosqlite:///test.db")
    yield engine
    engine.dispose()
```

### Performance Tests


```python
import time
import statistics

def test_endpoint_performance():
    client = TestClient(app)
    times = []

    for _ in range(100):
        start = time.perf_counter()
        response = client.get("/fast")
        elapsed = time.perf_counter() - start
        times.append(elapsed)

    avg = statistics.mean(times)
    p99 = sorted(times)[int(len(times) * 0.99)]
    print(f"Average: {avg:.4f}s, P99: {p99:.4f}s")
    assert avg < 0.1
    assert p99 < 0.5

@pytest.mark.asyncio
async def test_async_performance():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        tasks = [client.get("/fast") for _ in range(50)]
        start = time.perf_counter()
        responses = await asyncio.gather(*tasks)
        total_time = time.perf_counter() - start

    throughput = len(responses) / total_time
    print(f"Throughput: {throughput:.0f} req/s")
    assert throughput > 100
```


## Common Failures


### Failure: Connection Pool Exhaustion


- **Symptoms**: Database timeouts, slow queries, HTTP 503s. `psycopg2.pool.PoolError: pool exhausted` in logs.
- **Root Cause**: Database connection pool size too small for concurrent requests. Connections not returned to pool (missing `await conn.close()` or not using context managers). Starved by long-running queries.
- **Detection**: `db_pool_available` metric hits 0. Connection wait time increases. SQL `active_connections` spikes.
- **Recovery**: 1) Increase pool size temporarily. 2) Kill long-running queries. 3) Restart service. 4) Add connection pooling middleware (pgbouncer).
- **Prevention**: Always use `async with` context manager for connections. Set pool size based on `max_connections * pool_overflow`. Monitor `pool_size` and `pool_available`. Use RDS Proxy or pgbouncer.
- **Production Story**: A migration added an endpoint that made 50 sequential DB queries without async concurrency. Under 100 concurrent requests, each connection held for 3s. Pool of 20 was exhausted in < 1s. Fix: batched queries into single request and used `async with` for all connections.

### Failure: Slow JSON Validation on Request Body


- **Symptoms**: High CPU, slow request handling for endpoints with large request bodies. Pydantic validation dominates CPU profile.
- **Root Cause**: Pydantic v1 validation is CPU-intensive for large nested models. Each request is re-validated even if same schema.
- **Detection**: CPU profile shows `pydantic.main.BaseModel.__init__` at top. Request duration correlates with body size.
- **Recovery**: 1) Use `orm_mode` to skip validation on DB reads. 2) Cache validated models. 3) Switch to Pydantic v2 (5-10x faster).
- **Prevention**: Use Pydantic v2 which has Rust-based validation. Use `model_validate()` instead of `model_validate()` on cached data. Limit request body size. Use fast streaming validators for large payloads.

## Related

- [Readme](/02-data-engineering/README.md)
- [Data Governance](/02-data-engineering/data-quality-governance/01-data-governance.md)
- [Airflow Dagster](/02-data-engineering/orchestration/01-airflow-dagster.md)
- [Apache Spark](/02-data-engineering/processing/01-apache-spark.md)
- [Apache Flink](/02-data-engineering/processing/02-apache-flink.md)
- [Columnar Storage](/02-data-engineering/storage-formats/01-columnar-storage.md)

---

## Interactive Component: Python Coroutine State Machine

<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.state-machine-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px}.state-demo{text-align:center}.state-display{font-size:18px;font-family:monospace;padding:16px;border-radius:4px;margin:16px 0;color:#0b0e14;font-weight:bold;min-height:50px;display:flex;align-items:center;justify-content:center;border:2px solid currentColor}.state-created{background:#9333ea;border-color:#7e22ce}.state-suspended{background:#fbbf24;border-color:#f59e0b}.state-running{background:#00d4ff;border-color:#0099cc;color:#0b0e14}.state-done{background:#34d399;border-color:#22c55e}.state-buttons{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:16px}.state-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.state-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="state-machine-title">Python Async/Await Coroutine States</div>
  <div class="state-demo">
    <div class="state-display state-created" id="state-display">CREATED</div>
    <div class="state-buttons">
      <button class="state-button" onclick="setState('CREATED', pyAsyncStateMap)">Created (def async)</button>
      <button class="state-button" onclick="setState('SUSPENDED', pyAsyncStateMap)">Suspended (await)</button>
      <button class="state-button" onclick="setState('RUNNING', pyAsyncStateMap)">Running (resumed)</button>
      <button class="state-button" onclick="setState('DONE', pyAsyncStateMap)">Done (completed)</button>
    </div>
  </div>
  <script>
    const pyAsyncStateMap = {
      'CREATED': { label: 'CREATED', class: 'state-created' },
      'SUSPENDED': { label: 'SUSPENDED', class: 'state-suspended' },
      'RUNNING': { label: 'RUNNING', class: 'state-running' },
      'DONE': { label: 'DONE', class: 'state-done' }
    };
    function setState(state, sm) {
      const display = document.getElementById('state-display');
      const info = sm[state];
      display.textContent = info.label;
      display.className = 'state-display ' + info.class;
    }
  </script>
</div>


---

## Interactive Component: Python Thread State Machine

<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.state-machine-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px}.state-demo{text-align:center}.state-display{font-size:18px;font-family:monospace;padding:16px;border-radius:4px;margin:16px 0;color:#0b0e14;font-weight:bold;min-height:50px;display:flex;align-items:center;justify-content:center;border:2px solid currentColor}.state-start{background:#9333ea;border-color:#7e22ce}.state-active{background:#34d399;border-color:#22c55e}.state-running{background:#00d4ff;border-color:#0099cc;color:#0b0e14}.state-blocked{background:#fbbf24;border-color:#f59e0b}.state-stopped{background:#ef4444;border-color:#dc2626}.state-buttons{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin-top:16px}.state-button{padding:8px 16px;border:1px solid #00d4ff;background:#1e3a5f;color:#00d4ff;border-radius:4px;cursor:pointer;font-family:monospace;font-size:12px;transition:all 0.2s}.state-button:hover{background:#2a5a8f;box-shadow:0 0 8px #00d4ff}</style>
  <div class="state-machine-title">Python Thread State Machine</div>
  <div class="state-demo">
    <div class="state-display state-start" id="state-display">START</div>
    <div class="state-buttons">
      <button class="state-button" onclick="setState('START', pyThreadStateMap)">Start (created)</button>
      <button class="state-button" onclick="setState('ACTIVE', pyThreadStateMap)">Active (queued)</button>
      <button class="state-button" onclick="setState('RUNNING', pyThreadStateMap)">Running (GIL owned)</button>
      <button class="state-button" onclick="setState('BLOCKED', pyThreadStateMap)">Blocked (I/O)</button>
      <button class="state-button" onclick="setState('STOPPED', pyThreadStateMap)">Stopped (done)</button>
    </div>
  </div>
  <script>
    const pyThreadStateMap = {
      'START': { label: 'START', class: 'state-start' },
      'ACTIVE': { label: 'ACTIVE', class: 'state-active' },
      'RUNNING': { label: 'RUNNING', class: 'state-running' },
      'BLOCKED': { label: 'BLOCKED', class: 'state-blocked' },
      'STOPPED': { label: 'STOPPED', class: 'state-stopped' }
    };
    function setState(state, sm) {
      const display = document.getElementById('state-display');
      const info = sm[state];
      display.textContent = info.label;
      display.className = 'state-display ' + info.class;
    }
  </script>
</div>


---

## Interactive Component: Python GIL Contention Metrics

<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.obs-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px}.obs-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:12px}.obs-card{padding:12px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px;display:flex;flex-direction:column;align-items:center;transition:all 0.3s}.obs-card:hover{border-color:#00d4ff;box-shadow:0 0 8px rgba(0, 212, 255, 0.3)}.obs-label{color:#a3aab8;font-family:monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}.obs-value{font-family:monospace;font-size:20px;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px}.obs-unit{color:#a3aab8;font-family:monospace;font-size:10px;text-transform:uppercase}.metric-healthy{color:#34d399}.metric-warning{color:#fbbf24}.metric-critical{color:#ef4444}</style>
  <div class="obs-title">Python GIL Contention Observability</div>
  <div class="obs-grid">
    <div class="obs-card">
      <div class="obs-label">Active Threads</div>
      <div class="obs-value metric-healthy">8</div>
      <div class="obs-unit">threads</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">GIL Contention</div>
      <div class="obs-value metric-warning">67</div>
      <div class="obs-unit">%</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Lock Wait Time</div>
      <div class="obs-value metric-critical">245</div>
      <div class="obs-unit">ms</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Switch Events</div>
      <div class="obs-value metric-warning">1,892</div>
      <div class="obs-unit">count</div>
    </div>
  </div>
</div>


---

## Interactive Component: Python Memory Observability

<div style="padding:16px;background:#0b0e14;border:1px solid #1e2a3a;border-radius:8px">
  <style>.obs-title{color:#00d4ff;font-family:monospace;font-size:14px;font-weight:bold;margin-bottom:16px}.obs-grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:12px}.obs-card{padding:12px;background:#1a2332;border:1px solid #1e3a5f;border-radius:4px;display:flex;flex-direction:column;align-items:center;transition:all 0.3s}.obs-card:hover{border-color:#00d4ff;box-shadow:0 0 8px rgba(0, 212, 255, 0.3)}.obs-label{color:#a3aab8;font-family:monospace;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px}.obs-value{font-family:monospace;font-size:20px;font-weight:bold;margin-bottom:4px;letter-spacing:0.5px}.obs-unit{color:#a3aab8;font-family:monospace;font-size:10px;text-transform:uppercase}.metric-healthy{color:#34d399}.metric-warning{color:#fbbf24}.metric-critical{color:#ef4444}</style>
  <div class="obs-title">Python Memory Profiling</div>
  <div class="obs-grid">
    <div class="obs-card">
      <div class="obs-label">RSS (Resident)</div>
      <div class="obs-value metric-warning">342</div>
      <div class="obs-unit">MB</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">VMS (Virtual)</div>
      <div class="obs-value metric-healthy">458</div>
      <div class="obs-unit">MB</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">Objects Tracked</div>
      <div class="obs-value metric-healthy">127K</div>
      <div class="obs-unit">count</div>
    </div>
    <div class="obs-card">
      <div class="obs-label">RefCount Cycles</div>
      <div class="obs-value metric-healthy">89</div>
      <div class="obs-unit">runs</div>
    </div>
  </div>
</div>

