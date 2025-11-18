# Project Memory - Email Agent

## Project Overview
Email-based AI assistant for business brokers that processes inquiries in batches, answers questions using RAG (Retrieval Augmented Generation), and gates sensitive information behind NDAs.

## Key Architectural Decisions

### 1. Monolith Architecture (MVP)
**Decision**: Single monorepo with FastAPI backend + Next.js frontend
**Rationale**:
- Faster development for MVP
- Simpler deployment
- Easy to split into microservices later
- Reduces operational complexity initially

### 2. Batch Processing (Not Real-time)
**Decision**: Process emails in configured time windows (e.g., 9am, 12pm, 4pm)
**Rationale**:
- Mimics human assistant behavior
- Reduces suspicion from leads
- Allows broker review before auto-send
- Prevents instant-reply bot detection

### 3. pgvector in PostgreSQL (Not Separate Vector DB)
**Decision**: Use pgvector extension in main Postgres instance
**Rationale**:
- One less service to manage
- Sufficient for MVP scale (<1000 listings)
- Simpler data consistency (same DB)
- Can migrate to Qdrant/Pinecone later if needed

### 4. Manual Tenant Setup (No Self-Serve Onboarding)
**Decision**: Manually configure each broker in database
**Rationale**:
- MVP targets 1-5 brokers initially
- Faster to market
- Learn requirements before building self-serve
- Gmail API setup requires manual OAuth anyway

### 5. Trust & Control First
**Decision**: Always allow broker to see and override agent responses
**Rationale**:
- Critical for adoption (brokers won't trust black box)
- Prevents costly mistakes in early stages
- Provides training data for improvement
- Auto-send is opt-in, not default

## Database Schema Summary

### Core Tables
1. **brokers** - Broker accounts (email, password_hash, timezone)
2. **broker_settings** - Per-broker config (batch_windows, auto_send_enabled, calendly_link, nda_url)
3. **listings** - Business listings (code, title, asking_price, revenue, SDE, confidentiality_level)
4. **listing_documents** - PDFs/docs attached to listings (stored in S3)
5. **listing_document_chunks** - Text chunks with embeddings (vector column for RAG)
6. **leads** - Contact information (email, name, type: buyer/seller/other)
7. **ndas** - NDA status tracking (lead_id, listing_id, status, signed_at)
8. **email_threads** - Conversation threads (external_thread_id from Gmail, status, last_agent_action)
9. **email_messages** - Individual emails (direction, from, to, body_text, sent_by: lead/broker/agent)
10. **agent_runs** - LLM execution logs (prompt, response, tools_called, final_action, confidence_score)

### Important Indexes
- `email_threads (broker_id, status)`
- `email_messages (email_thread_id, sent_at)`
- Vector index on `listing_document_chunks (embedding)` using ivfflat

## Tech Stack Rationale

### Backend: FastAPI
- Modern async Python framework
- Automatic OpenAPI docs
- Pydantic validation built-in
- Fast performance
- Easy to integrate with Celery

### Frontend: Next.js 14
- Server components for performance
- App router for modern patterns
- TypeScript for safety
- Easy Vercel deployment

### LLM: OpenAI GPT-4.x
- Best-in-class function calling
- Reliable for production
- Good at following system prompts
- Supports 128k context (enough for conversation history)

### Background Jobs: Celery/RQ
- Proven for Python async tasks
- Cron-like scheduling (batch windows)
- Retry logic built-in
- Monitoring tools available

## Agent Architecture

### System Prompt Strategy
- Emphasize "escalate when uncertain" over "try to answer"
- Explicit rules for NDA gating
- Examples of good vs bad responses
- Clear tool usage instructions

### Tools Available to Agent
1. `identify_listing(email_text)` - Match email to listing using code/title/keywords
2. `get_listing_summary(listing_id)` - Basic public info (price, region, type)
3. `search_listing_knowledge(listing_id, query)` - RAG over documents
4. `get_nda_status(lead_id, listing_id)` - Check if NDA signed
5. `generate_nda_link(lead_id, listing_id)` - Create NDA request URL
6. `get_broker_settings(broker_id)` - Fetch Calendly link, timezone, etc.

### Agent Flow
1. Load email thread context (last 10 messages)
2. Identify listing (if not already known)
3. Determine question type (public info / sensitive / booking / other)
4. Check NDA status if needed
5. Call appropriate tools
6. Generate response
7. Store in agent_runs table
8. Either send immediately (auto_send) or save as draft

### Escalation Triggers
- Question not answerable with available data
- Legal/tax questions
- Angry/complaint emails
- Ambiguous listing match
- LLM confidence score < threshold (e.g., 0.7)

## Code Patterns

### Database Access
- Use SQLAlchemy async ORM
- Models in `backend/app/models/`
- Pydantic schemas for API validation
- Session dependency injection in routes

### API Structure
- Versioned: `/api/v1/...`
- JWT auth on protected routes
- Pydantic request/response models
- Consistent error responses

### Email Processing
- Gmail API with OAuth2 service account
- Custom label "processed" to track handled emails
- Store raw email metadata in JSONB for debugging
- Thread ID matching for conversation continuity

### Document Ingestion Pipeline
1. Upload to S3 (unique path: `brokers/{broker_id}/listings/{listing_id}/...`)
2. Extract text (pymupdf for PDF, python-docx for DOCX)
3. Chunk text (~500-1000 tokens using tiktoken)
4. Generate embeddings (OpenAI text-embedding-3-small)
5. Insert into `listing_document_chunks` with vector column
6. Background job, not blocking API response

## Critical Environment Variables

### Must Have (No Defaults)
- `DATABASE_URL` - Postgres connection
- `OPENAI_API_KEY` - For LLM and embeddings
- `SECRET_KEY` - JWT signing
- `GMAIL_CREDENTIALS_PATH` - OAuth2 credentials
- `S3_ACCESS_KEY` / `S3_SECRET_KEY` - Document storage

### Optional (Have Defaults)
- `REDIS_URL` - defaults to localhost:6379
- `ENVIRONMENT` - defaults to "development"
- `CORS_ORIGINS` - defaults to localhost:3000

## Dependencies

### Backend Core
- `fastapi` - Web framework
- `uvicorn[standard]` - ASGI server
- `sqlalchemy[asyncio]` - ORM
- `asyncpg` - Postgres driver
- `alembic` - Migrations
- `pydantic` - Validation
- `python-jose[cryptography]` - JWT
- `passlib[argon2]` - Password hashing
- `celery[redis]` - Background jobs
- `redis` - Caching and queue

### Backend Integrations
- `openai` - LLM and embeddings
- `google-api-python-client` - Gmail API
- `google-auth-httplib2` - Gmail OAuth
- `boto3` - S3 client
- `pymupdf` - PDF text extraction
- `python-docx` - DOCX parsing
- `tiktoken` - Token counting
- `pgvector` - Vector extension (Python client)

### Backend Dev/Test
- `pytest` - Testing
- `pytest-asyncio` - Async test support
- `httpx` - API testing
- `black` - Code formatting
- `flake8` - Linting

### Frontend Core
- `next` - Framework
- `react` / `react-dom` - UI library
- `typescript` - Type safety
- `tailwindcss` - Styling
- `@radix-ui/*` - Headless components (via shadcn)

### Frontend Utils
- `axios` or `fetch` - API calls
- `date-fns` - Date formatting
- `clsx` / `tailwind-merge` - Class merging
- `zod` - Schema validation

## Lessons Learned (To Be Updated)

### Gmail API Gotchas
- (Will document after implementation)

### Vector Search Performance
- **Implementation**: pgvector with IVFFlat index using cosine distance operator (<->)
- **Index configuration**: lists=100 (optimal for ~10K vectors, rule of thumb: sqrt(num_rows))
- **Embedding format**: String format '[0.1,0.2,...]' for pgvector compatibility
- **Search returns**: Top 3 chunks by default with content, metadata, distance, and similarity (1-distance)
- **Performance**: IVFFlat is good for <1M vectors; can scale to HNSW index later if needed
- **Query pattern**: Raw SQL with SQLAlchemy text() for vector operations
- **Migration**: Created 002_add_vector_index.py to enable pgvector and create index

### LLM Reliability
- (Will document common failure modes)

### Structured Logging
- **Implementation**: JSON-formatted logs using python-json-logger
- **Log Fields**: timestamp, level, service, logger, module, function, line, request_id, broker_id, thread_id, message, extra
- **Context Tracking**: ContextVars for request/broker/thread IDs across async operations
- **Coverage**:
  - All API requests logged with duration and status
  - Celery tasks logged (prerun, postrun, failure)
  - Agent tool calls logged with parameters
  - Exceptions logged with full stack traces
- **Request ID**: UUID generated for each API request, propagated through logs
- **Middleware**: LoggingMiddleware adds request_id header to responses (X-Request-ID)
- **Celery Signals**: task_prerun, task_postrun, task_failure for comprehensive task logging
- **Log Levels**: Configurable via settings.LOG_LEVEL (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Docker Production Configuration
- **Multi-stage builds**: Builder stage (gcc, dependencies) + minimal runtime stage
- **Image sizes**: API/Worker/Beat ~250MB each (optimized with python:3.11-slim)
- **Security**: Non-root user (appuser), minimal dependencies, no unnecessary tools
- **Health checks**: API (30s interval via /health), PostgreSQL (pg_isready), Redis (ping)
- **Service orchestration**: docker-compose.prod.yml with 5 services
- **Environment configs**: .env.prod.example with all required/optional variables
- **Auto-restart**: All services configured with `restart: unless-stopped`
- **Network isolation**: Internal Docker bridge network
- **Persistent volumes**: postgres_data, redis_data
- **Migrations**: Run automatically on API startup
- **Deployment guide**: DEPLOYMENT.md with operations, troubleshooting, security best practices

## Next Steps
See `tasks.md` for current implementation priorities.
