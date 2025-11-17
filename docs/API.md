# API Documentation

Base URL: `http://localhost:8000/api/v1` (development)

All endpoints return JSON. Authenticated endpoints require `Authorization: Bearer <token>` header.

## Authentication

### POST /auth/login

Login and receive JWT tokens.

**Request:**
```json
{
  "email": "broker@example.com",
  "password": "password123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhb...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhb...",
  "token_type": "bearer"
}
```

**Errors:**
- `401`: Invalid credentials
- `422`: Validation error

### POST /auth/refresh

Refresh access token using refresh token.

**Request:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhb..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhb...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhb...",
  "token_type": "bearer"
}
```

## Brokers

### GET /brokers/me

Get current authenticated broker's profile.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Broker",
  "email": "broker@example.com",
  "timezone": "America/New_York",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Settings

### GET /settings

Get broker settings.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": 1,
  "broker_id": "550e8400-e29b-41d4-a716-446655440000",
  "auto_send_enabled": false,
  "batch_windows": [
    {"start": "09:00", "end": "09:30"},
    {"start": "12:00", "end": "12:30"},
    {"start": "16:00", "end": "16:30"}
  ],
  "calendly_link": "https://calendly.com/broker/intro-call",
  "default_nda_url": "https://example.com/nda-form",
  "llm_model": "gpt-4-turbo-preview"
}
```

### PATCH /settings

Update broker settings (partial update).

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "auto_send_enabled": true,
  "batch_windows": [
    {"start": "10:00", "end": "10:30"}
  ]
}
```

**Response:** `200 OK` (same as GET)

## Listings

### GET /listings

Get all listings for current broker with optional filters.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `pending`, `sold`, `archived`)
- `search` (optional): Search in code, title, description
- `skip` (optional): Offset for pagination (default: 0)
- `limit` (optional): Limit results (default: 100, max: 500)

**Example:** `GET /listings?status=active&search=coffee&skip=0&limit=10`

**Response:** `200 OK`
```json
{
  "total": 42,
  "listings": [
    {
      "id": "650e8400-e29b-41d4-a716-446655440000",
      "broker_id": "550e8400-e29b-41d4-a716-446655440000",
      "code": "ABC123",
      "title": "Specialty Coffee Shop",
      "status": "active",
      "asking_price": "450000.00",
      "revenue": "750000.00",
      "sde": "150000.00",
      "location_region": "Vancouver, BC",
      "confidentiality_level": "high",
      "short_description": "High-traffic location...",
      "notes": "Internal notes here",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### POST /listings

Create a new listing.

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "code": "ABC123",
  "title": "Specialty Coffee Shop",
  "status": "active",
  "asking_price": 450000,
  "revenue": 750000,
  "sde": 150000,
  "location_region": "Vancouver, BC",
  "confidentiality_level": "high",
  "short_description": "High-traffic location with loyal customer base",
  "notes": "Seller motivated"
}
```

**Response:** `201 Created`
```json
{
  "id": "650e8400-e29b-41d4-a716-446655440000",
  ...
}
```

**Errors:**
- `400`: Code already exists for this broker
- `422`: Validation error

### GET /listings/{id}

Get a specific listing by ID.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (single listing object)

**Errors:**
- `404`: Listing not found

### PATCH /listings/{id}

Update a listing (partial update).

**Headers:** `Authorization: Bearer <token>`

**Request:**
```json
{
  "asking_price": 475000,
  "short_description": "Updated description"
}
```

**Response:** `200 OK` (updated listing object)

### DELETE /listings/{id}

Soft delete a listing (sets status to `archived`).

**Headers:** `Authorization: Bearer <token>`

**Response:** `204 No Content`

## Leads

### GET /leads

Get all leads for current broker.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `skip` (optional): Offset for pagination
- `limit` (optional): Limit results

**Response:** `200 OK`
```json
[
  {
    "id": "750e8400-e29b-41d4-a716-446655440000",
    "broker_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "buyer@example.com",
    "name": "Jane Buyer",
    "type": "buyer",
    "lead_score": 75,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### GET /leads/{id}

Get a specific lead by ID.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK` (single lead object)

## Email Threads

### GET /email-threads

Get all email threads for current broker.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `status` (optional): Filter by status (`open`, `closed`, `needs_broker`)
- `listing_id` (optional): Filter by listing UUID
- `skip` (optional): Offset
- `limit` (optional): Limit

**Response:** `200 OK`
```json
{
  "total": 15,
  "threads": [
    {
      "id": "850e8400-e29b-41d4-a716-446655440000",
      "broker_id": "550e8400-e29b-41d4-a716-446655440000",
      "lead_id": "750e8400-e29b-41d4-a716-446655440000",
      "listing_id": "650e8400-e29b-41d4-a716-446655440000",
      "external_thread_id": "thread_abc123",
      "status": "open",
      "last_agent_action": "auto_reply_sent",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "messages": [...]
    }
  ]
}
```

### GET /email-threads/{id}

Get a specific thread with all messages.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "850e8400-e29b-41d4-a716-446655440000",
  "broker_id": "550e8400-e29b-41d4-a716-446655440000",
  "lead_id": "750e8400-e29b-41d4-a716-446655440000",
  "listing_id": "650e8400-e29b-41d4-a716-446655440000",
  "external_thread_id": "thread_abc123",
  "status": "open",
  "last_agent_action": "auto_reply_sent",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "messages": [
    {
      "id": 1,
      "direction": "inbound",
      "from_email": "buyer@example.com",
      "to_email": "broker@example.com",
      "subject": "Question about ABC123",
      "body_text": "Is this listing still available?",
      "sent_at": "2024-01-01T10:00:00Z",
      "sent_by": "lead"
    },
    {
      "id": 2,
      "direction": "outbound",
      "from_email": "broker@example.com",
      "to_email": "buyer@example.com",
      "subject": "Re: Question about ABC123",
      "body_text": "Yes, this listing is still active...",
      "sent_at": "2024-01-01T10:15:00Z",
      "sent_by": "agent"
    }
  ]
}
```

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

### Status Codes

- `200`: Success
- `201`: Created
- `204`: No Content (successful deletion)
- `400`: Bad Request (business logic error)
- `401`: Unauthorized (invalid/missing token)
- `403`: Forbidden (missing credentials)
- `404`: Not Found
- `422`: Validation Error (invalid input)
- `500`: Internal Server Error

### Validation Errors (422)

```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

## Rate Limiting

Not implemented in MVP. Future: 100 requests/minute per broker.

## Pagination

Default: `skip=0`, `limit=100`
Maximum: `limit=500`

## Interactive API Docs

When backend is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

These provide interactive testing and full schema documentation.
