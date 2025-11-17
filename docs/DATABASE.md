# Database Schema Documentation

## Entity-Relationship Diagram

```
┌──────────────┐      ┌──────────────────┐
│   Brokers    │──────│ BrokerSettings   │
│              │ 1:1  │                  │
└──────┬───────┘      └──────────────────┘
       │ 1:N
       ├─────────────┬────────────────┬───────────────┐
       │             │                │               │
       ▼             ▼                ▼               ▼
┌──────────┐  ┌────────────┐  ┌───────────┐  ┌────────────────┐
│ Listings │  │   Leads    │  │EmailThread│  │   (other)      │
│          │  │            │  │           │  │                │
└────┬─────┘  └─────┬──────┘  └─────┬─────┘  └────────────────┘
     │ 1:N          │ 1:N           │ 1:N
     ├──────┐       │               │
     ▼      ▼       │               ▼
┌─────────┐ ┌───┐  │      ┌──────────────┐
│ListingDo│ │NDA│  │      │EmailMessages │
│c        │ │   │◄─┤      │              │
└────┬────┘ └───┘  │      └──────────────┘
     │ 1:N         │               │
     ▼             │               │ 1:N
┌──────────────┐   │               ▼
│ListingDocChu │   │      ┌─────────────┐
│nk (pgvector) │   │      │ AgentRuns   │
└──────────────┘   │      │             │
                   │      └─────────────┘
                   │
                   └─► (EmailThread references Listing + Lead)
```

## Tables

### 1. brokers

User accounts for business brokers.

**Columns**:
- `id` (UUID, PK): Unique broker identifier
- `name` (VARCHAR): Broker's full name
- `email` (VARCHAR, UNIQUE): Login email
- `password_hash` (VARCHAR): Argon2 hashed password
- `timezone` (VARCHAR): Broker's timezone (e.g., "America/New_York")
- `created_at` (TIMESTAMP): Account creation time
- `updated_at` (TIMESTAMP): Last update time

**Indexes**:
- PRIMARY KEY on `id`
- UNIQUE INDEX on `email`

**Relationships**:
- 1:1 with `broker_settings`
- 1:N with `listings`, `leads`, `email_threads`

**Sample Row**:
```sql
id: 550e8400-e29b-41d4-a716-446655440000
name: "John Broker"
email: "john@brokers.com"
password_hash: "$argon2id$v=19$m=..."
timezone: "America/New_York"
created_at: 2024-01-01 00:00:00
updated_at: 2024-01-15 10:30:00
```

### 2. broker_settings

Configuration settings per broker.

**Columns**:
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `broker_id` (UUID, FK → brokers.id): Owner broker
- `auto_send_enabled` (BOOLEAN): Auto-send emails without draft review
- `batch_windows` (JSONB): Array of {start, end} time windows
- `calendly_link` (TEXT): Meeting booking URL
- `default_nda_url` (TEXT): NDA form URL
- `llm_model` (VARCHAR): OpenAI model name (optional)

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `broker_id`
- FOREIGN KEY `broker_id` → `brokers.id` (CASCADE DELETE)

**Sample Row**:
```sql
id: 1
broker_id: 550e8400-e29b-41d4-a716-446655440000
auto_send_enabled: false
batch_windows: [
  {"start": "09:00", "end": "09:30"},
  {"start": "14:00", "end": "14:30"}
]
calendly_link: "https://calendly.com/john-broker/30min"
default_nda_url: "https://example.com/nda-form"
llm_model: "gpt-4-turbo-preview"
```

### 3. listings

Business listings managed by brokers.

**Columns**:
- `id` (UUID, PK): Unique listing ID
- `broker_id` (UUID, FK → brokers.id): Owner broker
- `code` (VARCHAR): Listing code (e.g., "ABC123")
- `title` (VARCHAR): Listing title
- `status` (ENUM): `active`, `pending`, `sold`, `archived`
- `asking_price` (NUMERIC(15,2)): Asking price
- `revenue` (NUMERIC(15,2)): Annual revenue
- `sde` (NUMERIC(15,2)): Seller's Discretionary Earnings
- `location_region` (TEXT): General location (city, state)
- `confidentiality_level` (ENUM): `low`, `medium`, `high`
- `short_description` (TEXT): Public description
- `notes` (TEXT): Internal broker notes
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `broker_id`
- INDEX on `(status, broker_id)` for filtered queries
- INDEX on `code`
- FOREIGN KEY `broker_id` → `brokers.id` (CASCADE DELETE)

**Constraints**:
- UNIQUE (`broker_id`, `code`)

**Sample Row**:
```sql
id: 650e8400-e29b-41d4-a716-446655440000
broker_id: 550e8400-e29b-41d4-a716-446655440000
code: "SF-CAFE-001"
title: "Specialty Coffee Shop - Downtown"
status: "active"
asking_price: 450000.00
revenue: 750000.00
sde: 150000.00
location_region: "San Francisco, CA"
confidentiality_level: "high"
short_description: "High-traffic location with loyal customer base..."
notes: "Seller motivated, will consider financing"
created_at: 2024-01-01 00:00:00
updated_at: 2024-01-15 14:20:00
```

### 4. listing_documents

Documents attached to listings (PDFs, DOCX).

**Columns**:
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `listing_id` (UUID, FK → listings.id): Parent listing
- `file_url` (TEXT): S3 path (e.g., "brokers/{id}/listings/{id}/teaser.pdf")
- `type` (ENUM): `teaser`, `cim_excerpt`, `faq`, `internal_notes`
- `title` (VARCHAR): Document title
- `created_at` (TIMESTAMP): Upload time

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `listing_id`
- FOREIGN KEY `listing_id` → `listings.id` (CASCADE DELETE)

**Sample Row**:
```sql
id: 1
listing_id: 650e8400-e29b-41d4-a716-446655440000
file_url: "brokers/550e.../listings/650e.../teaser.pdf"
type: "teaser"
title: "Coffee Shop - Teaser Document"
created_at: 2024-01-05 11:00:00
```

### 5. listing_document_chunks

Text chunks with vector embeddings for RAG.

**Columns**:
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `listing_document_id` (INTEGER, FK → listing_documents.id)
- `content` (TEXT): Extracted text chunk (~500-1000 tokens)
- `embedding` (VECTOR(1536)): OpenAI embedding vector
- `metadata` (TEXT): JSON metadata (page number, section, etc.)

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `listing_document_id`
- **VECTOR INDEX** on `embedding` using `ivfflat` (for fast similarity search)
- FOREIGN KEY `listing_document_id` → `listing_documents.id` (CASCADE DELETE)

**Vector Index** (created manually):
```sql
CREATE INDEX listing_chunks_embedding_idx
ON listing_document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

**Sample Row**:
```sql
id: 42
listing_document_id: 1
content: "The business operates 7 days a week from 6am to 6pm.
          Current staff includes 5 full-time and 3 part-time employees..."
embedding: [0.023, -0.045, 0.012, ..., 0.089]  # 1536 dimensions
metadata: {"page": 2, "section": "Operations"}
```

**Similarity Search** (example):
```sql
SELECT content, metadata,
       embedding <-> '[query_embedding]'::vector AS distance
FROM listing_document_chunks
WHERE listing_document_id IN (
  SELECT id FROM listing_documents WHERE listing_id = '...'
)
ORDER BY distance
LIMIT 3;
```

### 6. leads

Contact information for prospects.

**Columns**:
- `id` (UUID, PK): Unique lead ID
- `broker_id` (UUID, FK → brokers.id): Owner broker
- `email` (VARCHAR): Lead's email address
- `name` (VARCHAR): Lead's name (optional, extracted from email)
- `type` (ENUM): `buyer`, `seller`, `other`
- `lead_score` (INTEGER): Qualification score (0-100, optional)
- `created_at` (TIMESTAMP): First contact time
- `updated_at` (TIMESTAMP): Last activity time

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `broker_id`
- UNIQUE INDEX on `(broker_id, email)`
- FOREIGN KEY `broker_id` → `brokers.id` (CASCADE DELETE)

**Sample Row**:
```sql
id: 750e8400-e29b-41d4-a716-446655440000
broker_id: 550e8400-e29b-41d4-a716-446655440000
email: "buyer@example.com"
name: "Jane Smith"
type: "buyer"
lead_score: 75
created_at: 2024-01-10 09:15:00
updated_at: 2024-01-15 16:30:00
```

### 7. ndas

NDA tracking for lead-listing pairs.

**Columns**:
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `lead_id` (UUID, FK → leads.id)
- `listing_id` (UUID, FK → listings.id)
- `status` (ENUM): `sent`, `signed`, `rejected`, `revoked`
- `nda_url` (VARCHAR): NDA document URL
- `signed_at` (TIMESTAMP): Signature timestamp (NULL if not signed)

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `(lead_id, listing_id)`
- UNIQUE INDEX on `(lead_id, listing_id)`
- FOREIGN KEY `lead_id` → `leads.id` (CASCADE DELETE)
- FOREIGN KEY `listing_id` → `listings.id` (CASCADE DELETE)

**Sample Row**:
```sql
id: 1
lead_id: 750e8400-e29b-41d4-a716-446655440000
listing_id: 650e8400-e29b-41d4-a716-446655440000
status: "signed"
nda_url: "https://example.com/nda-123.pdf"
signed_at: 2024-01-12 14:25:00
```

### 8. email_threads

Conversation threads between leads and broker.

**Columns**:
- `id` (UUID, PK): Thread UUID
- `broker_id` (UUID, FK → brokers.id)
- `lead_id` (UUID, FK → leads.id)
- `listing_id` (UUID, FK → listings.id, NULLABLE): Associated listing (if identified)
- `external_thread_id` (VARCHAR): Gmail thread ID
- `status` (ENUM): `open`, `closed`, `needs_broker`
- `last_agent_action` (ENUM): `none`, `auto_reply_sent`, `draft_created`, `escalated`
- `created_at` (TIMESTAMP): First message time
- `updated_at` (TIMESTAMP): Last message time

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `(broker_id, status)`
- INDEX on `listing_id`
- FOREIGN KEY `broker_id` → `brokers.id` (CASCADE DELETE)
- FOREIGN KEY `lead_id` → `leads.id` (CASCADE DELETE)
- FOREIGN KEY `listing_id` → `listings.id` (SET NULL)

**Sample Row**:
```sql
id: 850e8400-e29b-41d4-a716-446655440000
broker_id: 550e8400-e29b-41d4-a716-446655440000
lead_id: 750e8400-e29b-41d4-a716-446655440000
listing_id: 650e8400-e29b-41d4-a716-446655440000
external_thread_id: "thread_18c5d..."
status: "open"
last_agent_action: "auto_reply_sent"
created_at: 2024-01-15 10:00:00
updated_at: 2024-01-15 10:15:00
```

### 9. email_messages

Individual emails within threads.

**Columns**:
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `email_thread_id` (UUID, FK → email_threads.id)
- `direction` (ENUM): `inbound`, `outbound`
- `from_email` (VARCHAR)
- `to_email` (VARCHAR)
- `subject` (TEXT)
- `body_text` (TEXT): Plain text body
- `sent_at` (TIMESTAMP): Email timestamp
- `raw_metadata` (JSONB): Full Gmail message metadata
- `sent_by` (ENUM): `lead`, `broker`, `agent`

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `(email_thread_id, sent_at)`
- FOREIGN KEY `email_thread_id` → `email_threads.id` (CASCADE DELETE)

**Sample Row**:
```sql
id: 123
email_thread_id: 850e8400-e29b-41d4-a716-446655440000
direction: "inbound"
from_email: "buyer@example.com"
to_email: "john@brokers.com"
subject: "Question about SF-CAFE-001"
body_text: "Is this listing still available? Can you share more details?"
sent_at: 2024-01-15 10:00:00
raw_metadata: {"messageId": "...", "headers": [...]}
sent_by: "lead"
```

### 10. agent_runs

LLM execution logs for debugging and monitoring.

**Columns**:
- `id` (INTEGER, PK, AUTO_INCREMENT)
- `email_thread_id` (UUID, FK → email_threads.id)
- `llm_model` (VARCHAR): Model used (e.g., "gpt-4-turbo-preview")
- `prompt` (TEXT): Full prompt sent to LLM
- `response` (TEXT): LLM's response text
- `tools_called` (JSONB): Array of {name, arguments, result}
- `confidence_score` (NUMERIC(3,2)): 0.00 to 1.00
- `final_action` (ENUM): `answer`, `ask_nda`, `book_meeting`, `escalate`
- `error_flag` (BOOLEAN): True if execution failed
- `created_at` (TIMESTAMP): Execution time

**Indexes**:
- PRIMARY KEY on `id`
- INDEX on `email_thread_id`
- INDEX on `created_at` (for analytics)
- FOREIGN KEY `email_thread_id` → `email_threads.id` (CASCADE DELETE)

**Sample Row**:
```sql
id: 456
email_thread_id: 850e8400-e29b-41d4-a716-446655440000
llm_model: "gpt-4-turbo-preview"
prompt: "You are an AI assistant... [full prompt]"
response: "Yes, this listing is still available..."
tools_called: [
  {
    "name": "identify_listing",
    "arguments": {"email_text": "..."},
    "result": {"listing_id": "...", "confidence": 0.85}
  },
  {
    "name": "get_listing_summary",
    "arguments": {"listing_id": "..."},
    "result": {"code": "SF-CAFE-001", "asking_price": 450000}
  }
]
confidence_score: 0.85
final_action: "answer"
error_flag: false
created_at: 2024-01-15 10:12:00
```

## Common Queries

### Get all open threads for broker

```sql
SELECT et.*, l.title as listing_title, ld.name as lead_name
FROM email_threads et
LEFT JOIN listings l ON et.listing_id = l.id
LEFT JOIN leads ld ON et.lead_id = ld.id
WHERE et.broker_id = ? AND et.status = 'open'
ORDER BY et.updated_at DESC;
```

### Get thread with messages

```sql
SELECT
  et.*,
  json_agg(
    json_build_object(
      'id', em.id,
      'direction', em.direction,
      'body_text', em.body_text,
      'sent_at', em.sent_at,
      'sent_by', em.sent_by
    ) ORDER BY em.sent_at
  ) as messages
FROM email_threads et
LEFT JOIN email_messages em ON em.email_thread_id = et.id
WHERE et.id = ?
GROUP BY et.id;
```

### Vector similarity search

```sql
SELECT ldc.content, ldc.metadata,
       ldc.embedding <-> ?::vector AS distance
FROM listing_document_chunks ldc
JOIN listing_documents ld ON ldc.listing_document_id = ld.id
WHERE ld.listing_id = ?
ORDER BY distance
LIMIT 3;
```

### Agent performance metrics

```sql
SELECT
  final_action,
  COUNT(*) as count,
  AVG(confidence_score) as avg_confidence
FROM agent_runs
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY final_action;
```

## Migration Strategy

Managed with Alembic:

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Backup & Recovery

- **Automated backups**: Daily snapshots (managed Postgres)
- **Point-in-time recovery**: Available for last 7 days
- **Critical tables**: `brokers`, `listings`, `email_threads`
- **Rebuilable**: `listing_document_chunks` (can regenerate embeddings)

## Performance Tuning

### Indexes to watch

- `email_threads (broker_id, status)`: Hot query path
- `email_messages (thread_id, sent_at)`: Message ordering
- `listing_document_chunks (embedding)`: Vector search

### Query optimization

- Use `EXPLAIN ANALYZE` for slow queries
- Consider partitioning `email_messages` by date (if >1M rows)
- Archive old threads periodically

### Connection pooling

- Pool size: 5-10 connections
- Max overflow: 10
- Recycle: 3600 seconds
