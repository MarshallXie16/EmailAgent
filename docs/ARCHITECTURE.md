# Architecture Overview

## System Architecture

The Email Agent is built as a monolithic application with clear separation of concerns, designed for easy transition to microservices if needed.

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│                    Dashboard, Settings, Listings                 │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS/REST
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────────┐   │
│  │   API v1    │  │   Models    │  │      Services        │   │
│  │  Endpoints  │──│ (SQLAlchemy)│──│  - Gmail             │   │
│  │             │  │             │  │  - S3                │   │
│  └─────────────┘  └─────────────┘  │  - OpenAI            │   │
│                                     │  - Agent             │   │
│                                     │  - DocProcessor      │   │
│                                     └──────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
   ┌──────────┐   ┌──────────┐   ┌────────────┐
   │PostgreSQL│   │  Redis   │   │   Gmail    │
   │+pgvector │   │  Queue   │   │    API     │
   └──────────┘   └──────────┘   └────────────┘
         ▲               ▲
         │               │
         └───────┬───────┘
                 ▼
         ┌──────────────┐
         │    Celery    │
         │   Workers    │
         │ - Email Poll │
         │ - Batch Send │
         │ - Embeddings │
         └──────────────┘
```

## Core Components

### 1. API Layer (`app/api/`)

RESTful endpoints organized by resource:

- **auth.py**: Authentication (login, token refresh)
- **brokers.py**: Broker profile management
- **settings.py**: Broker settings (batch windows, auto-send)
- **listings.py**: Listings CRUD
- **leads.py**: Lead management
- **threads.py**: Email thread viewing

All endpoints:
- Use JWT authentication (except login)
- Return consistent JSON responses
- Include proper error handling
- Are fully async for performance

### 2. Models Layer (`app/models/`)

SQLAlchemy ORM models representing database tables:

- **Broker**: User accounts with settings
- **Listing**: Business listings with documents
- **Lead**: Contact information
- **EmailThread**: Conversation threads
- **EmailMessage**: Individual emails
- **AgentRun**: LLM execution logs
- **NDA**: NDA tracking

All models use:
- UUID for primary keys (except junction tables)
- Timestamps (created_at, updated_at)
- Enums for status fields
- Proper foreign key relationships

### 3. Services Layer (`app/services/`)

Business logic separated from API controllers:

#### GmailService
- OAuth2 authentication
- Email polling (fetch unprocessed)
- Email parsing (headers + body)
- Email sending (with threading)
- Label management

#### S3Service
- File upload/download
- Signed URL generation
- File existence checking

#### OpenAIService
- Chat completions (with function calling)
- Embeddings (single and batch)
- Token usage tracking

#### DocumentProcessor
- PDF text extraction (PyMuPDF)
- DOCX text extraction
- Token-based chunking
- Metadata preservation

#### AgentService
- LLM orchestration
- Tool execution
- Confidence scoring
- Action determination (answer/escalate/nda/meeting)

### 4. Workers Layer (`app/workers/`)

Celery background tasks:

- **poll_gmail**: Fetch new emails every N minutes
- **run_batch**: Process emails in configured time windows
- **ingest_document**: Extract text and generate embeddings

## Data Flow

### Email Processing Flow

```
1. Gmail API (Celery)
   └─> poll_gmail()
       └─> Fetch unprocessed messages
           └─> Parse email
               └─> Create/update Lead
                   └─> Create EmailThread
                       └─> Create EmailMessage
                           └─> Mark as "processed" in Gmail

2. Batch Processing (Celery Beat)
   └─> run_batch_for_broker()
       └─> Query open threads
           └─> For each thread:
               ├─> Load conversation history
               ├─> Call AgentService.generate_response()
               │   ├─> Build context (messages + tools)
               │   ├─> Call OpenAI with function calling
               │   ├─> Execute tools (identify listing, check NDA, etc.)
               │   └─> Generate final response
               ├─> Create AgentRun record
               ├─> If auto_send_enabled:
               │   └─> GmailService.send_email()
               └─> Else:
                   └─> Save as draft for broker review
```

### Document Ingestion Flow

```
1. Upload Document
   └─> POST /api/v1/listings/{id}/documents
       └─> S3Service.upload_file()
           └─> Trigger Celery task: ingest_document()

2. Background Processing
   └─> ingest_document(document_id)
       ├─> S3Service.download_file()
       ├─> DocumentProcessor.process_document()
       │   ├─> Extract text (PDF/DOCX)
       │   └─> Chunk text (1000 tokens, 200 overlap)
       ├─> OpenAIService.create_embeddings_batch()
       └─> Insert chunks with vectors into DB
```

### Agent Decision Flow

```
1. Receive email in thread
2. Agent analyzes content
3. Tool execution:
   ├─> identify_listing() → Match to listing
   ├─> get_listing_summary() → Basic info
   ├─> get_nda_status() → Check if signed
   └─> Conditional:
       ├─> If sensitive question + no NDA:
       │   └─> generate_nda_link()
       ├─> If high intent:
       │   └─> get_broker_settings() for Calendly
       └─> If uncertain:
           └─> Escalate to broker
4. Generate response
5. Store in agent_runs
6. Send or draft based on settings
```

## Design Patterns

### 1. Dependency Injection

Database sessions are injected via FastAPI's `Depends()`:

```python
@router.get("/listings")
async def get_listings(
    db: AsyncSession = Depends(get_db),
    current_broker: Broker = Depends(get_current_broker),
):
    ...
```

### 2. Repository Pattern (Implicit)

Services encapsulate data access:

```python
# Bad: Controller directly queries DB
listings = await db.execute(select(Listing)...)

# Good: Service method handles query
listings = await listing_service.get_broker_listings(broker_id)
```

### 3. Service Layer Pattern

Business logic separated from API layer:

```python
# API endpoint delegates to service
agent_service = AgentService(db)
response = await agent_service.generate_response(...)
```

### 4. Factory Pattern

Tool execution dynamically dispatched:

```python
result = await agent.execute_tool(tool_name, arguments, broker_id)
```

## Security Architecture

### Authentication Flow

```
1. User logs in with email/password
   └─> POST /api/v1/auth/login
       ├─> Verify credentials (Argon2)
       ├─> Generate access token (JWT, 30min)
       ├─> Generate refresh token (JWT, 7days)
       └─> Return tokens

2. Subsequent requests
   └─> Include: Authorization: Bearer <access_token>
       ├─> Extract token from header
       ├─> Verify signature
       ├─> Extract broker_id from payload
       └─> Load broker from DB

3. Token refresh
   └─> POST /api/v1/auth/refresh
       ├─> Verify refresh token
       └─> Issue new access + refresh tokens
```

### Data Isolation

All queries filtered by `broker_id`:

```python
listings = await db.execute(
    select(Listing).where(Listing.broker_id == current_broker.id)
)
```

No global admin access in MVP.

### Input Validation

Pydantic schemas validate all inputs:

```python
class ListingCreate(BaseModel):
    code: str
    title: str
    asking_price: Optional[Decimal] = None
    ...
```

## Performance Considerations

### Async Throughout

- FastAPI async endpoints
- SQLAlchemy async engine
- Async database queries
- Non-blocking I/O

### Connection Pooling

SQLAlchemy manages connection pool:

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
)
```

### Caching Strategy (Future)

Redis ready for:
- Listing summaries
- NDA status
- Broker settings
- Embedding cache

### Vector Search Optimization

pgvector with IVFFlat index:

```sql
CREATE INDEX ON listing_document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

## Scalability Path

### Current (MVP)

- Single FastAPI instance
- Single Postgres instance
- Single Redis instance
- Multiple Celery workers (same machine)

### Future (Scale)

1. **Horizontal API scaling**:
   - Multiple FastAPI instances behind load balancer
   - Stateless design enables this

2. **Database optimization**:
   - Read replicas for queries
   - Write master for updates
   - Connection pooling tuning

3. **Worker scaling**:
   - Dedicated Celery workers per task type
   - Separate queues (email_poll, batch_process, embeddings)

4. **Microservices split** (if needed):
   - Email service (Gmail polling)
   - Agent service (LLM + tools)
   - Document service (ingestion)
   - API gateway

## Error Handling

### Levels

1. **Application errors**: Logged and returned as JSON
2. **Database errors**: Rolled back, logged, returned as 500
3. **External API errors**: Retried (Celery), logged, escalated to broker
4. **Validation errors**: Returned as 422 with details

### Retry Strategy

Celery tasks retry on failure:

```python
@celery.task(bind=True, max_retries=3)
def poll_gmail(self):
    try:
        ...
    except Exception as e:
        self.retry(exc=e, countdown=60)  # Retry after 1min
```

## Monitoring & Observability

### Logging

Structured JSON logs:

```python
logger.info(
    "Agent run completed",
    extra={
        "thread_id": thread_id,
        "confidence": confidence,
        "action": final_action,
        "tools_used": [t["name"] for t in tools_called],
    },
)
```

### Metrics (Future)

- Request latency (p50, p95, p99)
- Error rates by endpoint
- Agent confidence scores
- Email processing time
- Token usage and costs

### Health Checks

- `/health`: API liveness
- Database connectivity
- Redis connectivity
- Celery worker status

## Technology Choices

### Why FastAPI?

- **Async native**: Non-blocking I/O
- **Auto docs**: OpenAPI/Swagger
- **Type safety**: Pydantic validation
- **Performance**: One of the fastest Python frameworks
- **Modern**: Python 3.11+ features

### Why PostgreSQL + pgvector?

- **Single database**: Relational + vector data
- **Mature**: Proven at scale
- **pgvector**: Fast similarity search
- **Cost**: No separate vector DB service

### Why Celery?

- **Battle-tested**: 10+ years in production
- **Features**: Retries, scheduling, monitoring
- **Flexible**: Multiple queue backends
- **Python-native**: Easy integration

### Why OpenAI?

- **Function calling**: Best-in-class for tools
- **Reliability**: Production-grade
- **Context**: 128k tokens (enough for email history)
- **Embeddings**: High-quality vectors

## Configuration Management

### Environment Variables

All config via `.env`:

```
DATABASE_URL=...
REDIS_URL=...
OPENAI_API_KEY=...
GMAIL_CREDENTIALS_PATH=...
```

### Settings Class

Pydantic Settings with validation:

```python
class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    ...
```

### Environment-specific

- `ENVIRONMENT=development`: Verbose logging, CORS relaxed
- `ENVIRONMENT=production`: Error logging only, strict CORS

## Testing Strategy

- **Unit tests**: Services, utilities (mocked externals)
- **Integration tests**: API endpoints (test database)
- **E2E tests**: Full flows (staging environment)
- **Coverage target**: 70%+

See `docs/TESTING.md` for details.
