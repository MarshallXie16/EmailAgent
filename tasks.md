# Email Agent - Development Tasks (Jira-Style)

## Sprint Status

**Current Sprint**: Week 3 Complete ✅  
**Next Sprint**: Week 4 - Frontend Development  
**Date**: 2024-01-17

---

## ✅ Completed (Week 1-3)

### Backend Foundation
- ✅ EA-SETUP-001: Project structure and documentation
- ✅ EA-DB-001: Database models and migrations setup
- ✅ EA-AUTH-001: JWT authentication system
- ✅ EA-API-001: All core API endpoints (auth, brokers, settings, listings, leads, threads)
- ✅ EA-SERVICE-001: Gmail API service
- ✅ EA-SERVICE-002: S3 storage service
- ✅ EA-SERVICE-003: OpenAI service (chat + embeddings)
- ✅ EA-SERVICE-004: Document processor
- ✅ EA-AGENT-001: Agent service with 6 tools
- ✅ EA-WORKER-001: Celery setup
- ✅ EA-WORKER-002: Email polling job
- ✅ EA-WORKER-003: Batch processing job
- ✅ EA-WORKER-004: Document ingestion job
- ✅ EA-API-002: Document upload endpoint
- ✅ EA-TEST-001: Comprehensive test suite (70%+ coverage)
- ✅ EA-DOC-001: Architecture documentation
- ✅ EA-DOC-002: API documentation
- ✅ EA-DOC-003: Agent system documentation
- ✅ EA-DOC-004: Database schema documentation

---

## 🟡 In Progress

### EA-DB-002: Implement Vector Search
**Priority**: High | **Type**: Story | **Estimate**: 5 SP

**Description**:  
Implement pgvector similarity search in `search_listing_knowledge()` tool.

**Acceptance Criteria**:
- [ ] Vector index created on `listing_document_chunks.embedding`
- [ ] Cosine similarity search implemented
- [ ] Returns top 3 relevant chunks with distance scores
- [ ] Performance < 100ms per query

**SQL**:
```sql
CREATE INDEX listing_chunks_embedding_idx
ON listing_document_chunks
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
```

---

## 📝 To Do

### High Priority (Week 4-5)

#### EA-FRONT-001: Authentication UI
**Priority**: High | **Type**: Story | **Estimate**: 5 SP

**Description**:  
Build login page and auth context.

**Pages**: `/login`

**Acceptance Criteria**:
- [ ] Login form with validation
- [ ] Calls POST /api/v1/auth/login
- [ ] Stores tokens securely
- [ ] AuthContext for app-wide state
- [ ] Redirects on success/failure
- [ ] Error messages displayed

---

#### EA-FRONT-002: Dashboard Layout
**Priority**: High | **Type**: Task | **Estimate**: 3 SP

**Description**:  
Create main layout with sidebar and header.

**Components**: `<Layout>`, `<Sidebar>`, `<Header>`

**Acceptance Criteria**:
- [ ] Responsive (mobile + desktop)
- [ ] Navigation: Dashboard, Listings, Threads, Settings
- [ ] Active route highlighted
- [ ] User info in header
- [ ] Logout functionality

---

#### EA-FRONT-003: Listings Management UI
**Priority**: High | **Type**: Story | **Estimate**: 8 SP

**Description**:  
Build UI for listings CRUD.

**Pages**: `/listings`, `/listings/new`, `/listings/:id`

**Acceptance Criteria**:
- [ ] Table view with search/filter
- [ ] Pagination (20 per page)
- [ ] Create/edit forms
- [ ] Delete confirmation
- [ ] Document upload UI (drag-and-drop)
- [ ] Document list with signed URLs

---

#### EA-FRONT-004: Email Threads UI
**Priority**: High | **Type**: Story | **Estimate**: 13 SP

**Description**:  
Build email conversation view.

**Pages**: `/threads`, `/threads/:id`

**Acceptance Criteria**:
- [ ] Thread list with filters (status, listing)
- [ ] "Needs Attention" badge
- [ ] Chat-style message view
- [ ] Color-coded by sender
- [ ] Agent run details expandable
- [ ] Draft editing capability
- [ ] Override reply composer
- [ ] Send button

---

#### EA-FRONT-005: Settings UI
**Priority**: Medium | **Type**: Story | **Estimate**: 5 SP

**Description**:  
Build settings configuration page.

**Sections**: Batch Windows, Auto-Send, Calendly, NDA, Profile

**Acceptance Criteria**:
- [ ] Auto-send toggle
- [ ] Batch windows editor (time picker)
- [ ] Timezone selector
- [ ] URL inputs with validation
- [ ] Save button with loading state
- [ ] Toast notifications

---

#### EA-API-003: Broker Override Endpoint
**Priority**: Medium | **Type**: Story | **Estimate**: 3 SP

**Description**:  
Allow manual reply composition.

**Endpoint**: `POST /api/v1/email-threads/{id}/override-reply`

**Request Body**:
```json
{
  "body_text": "Manual reply..."
}
```

**Acceptance Criteria**:
- [ ] Validates broker ownership
- [ ] Sends via Gmail API
- [ ] Creates EmailMessage with `sent_by=broker`
- [ ] Updates thread status
- [ ] Returns 200 with details

---

### Week 4 - Dashboard & Admin Panel (Current Focus)

#### EA-DASH-001: Email Activity Log
**Priority**: High | **Type**: Story | **Estimate**: 8 SP

**Description**:
Build comprehensive email activity log showing all agent interactions with leads.

**User Story**:
As a broker, I want to see all emails my agent has sent, so that I can monitor what information is being shared with leads and ensure accuracy.

**Pages**: `/dashboard/activity`, `/dashboard/activity/:threadId`

**Acceptance Criteria**:
- [ ] Table view with columns: Date, Lead, Listing, Subject, Status (sent/draft), Confidence, Action
- [ ] Filter by: date range, listing, lead, status, confidence range
- [ ] Search by subject or email content
- [ ] Pagination (50 per page)
- [ ] Click row to view full email thread
- [ ] Color coding: Green (sent, high confidence), Yellow (draft/needs review), Red (escalated)
- [ ] Export to CSV functionality
- [ ] Real-time updates (polling every 30s or websocket)

**Technical Notes**:
- Query `email_threads` JOIN `email_messages` JOIN `agent_runs`
- Use DataTable component from shadcn/ui
- Implement cursor-based pagination for performance

---

#### EA-DASH-002: Review Queue UI
**Priority**: High | **Type**: Story | **Estimate**: 13 SP

**Description**:
Build review queue where brokers can review, edit, approve, or reject agent-flagged emails.

**User Story**:
As a broker, I want to review emails my agent is uncertain about before they're sent, so that I can maintain quality control and prevent mistakes.

**Pages**: `/dashboard/review-queue`, `/dashboard/review-queue/:threadId`

**Acceptance Criteria**:
- [ ] Queue shows threads with `status=needs_broker` or `requires_review=true`
- [ ] Card layout with: Lead info, listing, proposed response, agent reasoning
- [ ] "Why flagged" section showing agent's uncertainty factors
- [ ] Side-by-side view: conversation history (left), proposed response (right)
- [ ] Three action buttons:
  - **Approve & Send** - Sends as-is
  - **Edit & Send** - Opens composer with pre-filled text
  - **Manual Reply** - Starts from scratch
- [ ] Confidence score visualization (progress bar or gauge)
- [ ] Tools called by agent displayed (badges)
- [ ] "Mark as resolved" without sending (if lead replied elsewhere)
- [ ] Priority sorting (lowest confidence first)
- [ ] Badge count in sidebar navigation

**Technical Notes**:
- Use shadcn/ui Card, Badge, Textarea, Button components
- Rich text editor for manual replies (Tiptap or similar)
- Optimistic UI updates

---

#### EA-DASH-003: Agent Reasoning Display
**Priority**: High | **Type**: Story | **Estimate**: 5 SP

**Description**:
Display agent's decision-making process and reasoning for every email interaction.

**User Story**:
As a broker, I want to understand WHY my agent made each decision, so that I can trust the system and identify areas for improvement.

**Component**: `<AgentReasoningPanel>` (reusable in multiple views)

**Acceptance Criteria**:
- [ ] Expandable panel showing:
  - System prompt used
  - Tools called with inputs/outputs
  - Confidence score breakdown
  - Final action determination logic
  - Any warnings or edge cases identified
- [ ] Timeline view of tool execution order
- [ ] Syntax-highlighted JSON for tool inputs/outputs
- [ ] "Confidence factors" list (e.g., "High: Listing code matched", "Low: No NDA on file")
- [ ] Token usage and cost for this interaction
- [ ] Model version used (GPT-4, GPT-3.5, etc.)

**Technical Notes**:
- Store reasoning in `agent_runs.reasoning` JSON field
- Use Accordion component for expandable sections
- Add syntax highlighting library (prism or highlight.js)

---

#### EA-DASH-004: Analytics Dashboard
**Priority**: High | **Type**: Story | **Estimate**: 8 SP

**Description**:
Build analytics dashboard showing key metrics and trends for email agent performance.

**User Story**:
As a broker, I want to see analytics on my agent's performance, so that I can measure ROI and identify optimization opportunities.

**Pages**: `/dashboard` (default landing page)

**Sections**:

**1. KPI Cards** (Top row)
- Total emails processed (this week)
- Auto-reply rate (% sent without review)
- Escalation rate (% flagged for broker)
- Avg confidence score

**2. Charts**
- Line chart: Emails per day (last 30 days)
- Bar chart: Emails by listing (top 10)
- Pie chart: Final actions breakdown (answered, escalated, NDA requested, meeting booked)
- Line chart: Confidence trend over time

**3. Recent Activity** (Bottom)
- Last 10 interactions (mini version of activity log)

**Acceptance Criteria**:
- [ ] All KPIs calculated correctly from database
- [ ] Charts are interactive (hover tooltips, click to filter)
- [ ] Date range selector (7d, 30d, 90d, all time)
- [ ] Responsive design (mobile-friendly)
- [ ] Loading states for async data
- [ ] Auto-refresh every 60 seconds
- [ ] Export dashboard as PDF

**Technical Notes**:
- Use Recharts or Chart.js for visualizations
- Create analytics service to aggregate data
- Consider materialized views for performance

---

#### EA-API-006: Analytics Endpoints
**Priority**: High | **Type**: Task | **Estimate**: 5 SP

**Description**:
Build backend API endpoints to support analytics dashboard.

**Endpoints**:

**GET /api/v1/analytics/overview**
```json
{
  "period": "7d",
  "total_emails": 156,
  "auto_reply_rate": 0.73,
  "escalation_rate": 0.18,
  "avg_confidence": 0.82,
  "nda_request_rate": 0.09
}
```

**GET /api/v1/analytics/emails**
Query params: `?start_date=...&end_date=...&listing_id=...&status=...&skip=0&limit=50`
```json
{
  "emails": [
    {
      "id": "uuid",
      "thread_id": "uuid",
      "lead_name": "John Doe",
      "lead_email": "john@example.com",
      "listing_code": "BIZ123",
      "listing_title": "Coffee Shop",
      "subject": "Re: Inquiry about BIZ123",
      "sent_at": "2024-01-17T10:30:00Z",
      "status": "sent",
      "sent_by": "agent",
      "confidence": 0.85,
      "final_action": "answered",
      "tools_called": ["identify_listing", "get_listing_summary"]
    }
  ],
  "total": 156,
  "skip": 0,
  "limit": 50
}
```

**GET /api/v1/analytics/trends**
```json
{
  "daily_counts": [
    {"date": "2024-01-10", "count": 12},
    {"date": "2024-01-11", "count": 18},
    ...
  ],
  "by_listing": [
    {"listing_code": "BIZ123", "count": 45},
    ...
  ],
  "by_action": {
    "answered": 114,
    "escalated": 28,
    "nda_requested": 14
  }
}
```

**Acceptance Criteria**:
- [ ] All endpoints return correct data
- [ ] Efficient queries (use indexes, avoid N+1)
- [ ] Date filtering works correctly
- [ ] Pagination implemented
- [ ] Proper error handling (404, 422, 500)
- [ ] OpenAPI/Swagger docs updated
- [ ] Tests written (test_analytics.py)

---

#### EA-API-007: Review Queue Endpoints
**Priority**: High | **Type**: Task | **Estimate**: 5 SP

**Description**:
Build backend endpoints for review queue functionality.

**Endpoints**:

**GET /api/v1/review-queue**
```json
{
  "threads": [
    {
      "id": "uuid",
      "lead": {...},
      "listing": {...},
      "status": "needs_broker",
      "last_inbound_message": {...},
      "proposed_response": "...",
      "agent_reasoning": {
        "why_flagged": "Lead asked about proprietary financial details not in CIM",
        "confidence": 0.42,
        "concerns": ["Potential confidentiality breach", "No NDA signed"],
        "tools_called": [...]
      },
      "created_at": "...",
      "priority_score": 8.5
    }
  ],
  "total": 12
}
```

**POST /api/v1/email-threads/{id}/approve**
Body: `{"edits": "optional edited response text"}`
- Sends email (original or edited)
- Updates thread status to `closed` or `open`
- Creates EmailMessage record with `sent_by=broker`

**POST /api/v1/email-threads/{id}/manual-reply**
Body: `{"body_text": "Manual response..."}`
- Sends custom email
- Updates thread status
- Creates EmailMessage record

**POST /api/v1/email-threads/{id}/mark-resolved**
- Updates thread status without sending
- For cases where lead replied elsewhere or issue resolved

**Acceptance Criteria**:
- [ ] Review queue sorted by priority (lowest confidence first)
- [ ] Approve endpoint sends email via Gmail
- [ ] Manual reply endpoint validates broker ownership
- [ ] All actions logged in database
- [ ] Proper authorization (broker can only act on own threads)
- [ ] Tests written (test_review_queue.py)

---

#### EA-DB-003: Agent Reasoning Enhancements
**Priority**: High | **Type**: Task | **Estimate**: 3 SP

**Description**:
Enhance database schema to store detailed agent reasoning and flagging logic.

**Database Changes**:

**1. Add column to `agent_runs` table:**
```sql
ALTER TABLE agent_runs
ADD COLUMN reasoning JSONB;
```

**Structure of reasoning JSONB:**
```json
{
  "why_flagged": "Lead asked about proprietary financial details",
  "confidence_factors": {
    "positive": [
      {"factor": "Listing code matched", "weight": 0.3},
      {"factor": "Standard inquiry pattern", "weight": 0.2}
    ],
    "negative": [
      {"factor": "No NDA signed", "weight": -0.4},
      {"factor": "Confidential data requested", "weight": -0.5}
    ]
  },
  "concerns": ["Potential confidentiality breach"],
  "edge_cases": [],
  "token_usage": {"prompt": 1200, "completion": 450, "total": 1650},
  "cost_usd": 0.0248
}
```

**2. Add column to `email_threads` table:**
```sql
ALTER TABLE email_threads
ADD COLUMN requires_review BOOLEAN DEFAULT FALSE,
ADD COLUMN priority_score DECIMAL(3,2) DEFAULT 5.0;
```

**3. Add index for review queue:**
```sql
CREATE INDEX idx_threads_review_queue
ON email_threads (broker_id, requires_review, priority_score DESC)
WHERE status = 'needs_broker';
```

**Acceptance Criteria**:
- [ ] Migration created (Alembic)
- [ ] AgentService updated to populate reasoning field
- [ ] Confidence calculation logic documented
- [ ] Priority score calculation logic implemented
- [ ] Tests updated to include reasoning field

**Technical Notes**:
- Priority score = (10 - confidence * 10) + urgency_bonus
- Urgency based on: time since last email, number of follow-ups, lead type

---

### Medium Priority (Week 5-6)

#### EA-TEST-002: Expand API Tests
**Priority**: Medium | **Type**: Task | **Estimate**: 5 SP

**Description**:  
Increase test coverage to 80%+.

**Tests Needed**:
- [ ] Settings endpoints
- [ ] Email threads endpoints
- [ ] Document upload
- [ ] Error cases (401, 403, 404, 422, 500)

---

#### EA-LOG-001: Structured Logging
**Priority**: Medium | **Type**: Task | **Estimate**: 3 SP

**Description**:  
Implement JSON logging for all services.

**Fields**: timestamp, level, service, broker_id, thread_id, message, extra

**Acceptance Criteria**:
- [ ] JSON format configured
- [ ] Agent runs logged
- [ ] API requests logged (with request ID)
- [ ] Celery tasks logged
- [ ] Error stack traces captured

---

#### EA-DEPLOY-001: Docker Production Config
**Priority**: High | **Type**: Task | **Estimate**: 3 SP

**Description**:  
Production-ready Docker setup.

**Acceptance Criteria**:
- [ ] Multi-stage Dockerfile
- [ ] Image size < 500MB
- [ ] Health checks
- [ ] docker-compose.prod.yml
- [ ] Environment-specific configs

---

#### EA-DEPLOY-002: Railway Deployment
**Priority**: High | **Type**: Task | **Estimate**: 5 SP

**Description**:  
Deploy backend to Railway/Fly.io.

**Services**: FastAPI, Celery Worker, Celery Beat

**Acceptance Criteria**:
- [ ] Railway project created
- [ ] Backend deployed
- [ ] Workers running
- [ ] Beat scheduler active
- [ ] Migrations run on deploy
- [ ] Health check returns 200

---

#### EA-DEPLOY-003: Vercel Deployment
**Priority**: Medium | **Type**: Task | **Estimate**: 2 SP

**Description**:  
Deploy Next.js to Vercel.

**Acceptance Criteria**:
- [ ] Connected to GitHub
- [ ] Auto-deploy on push
- [ ] Environment variables set
- [ ] HTTPS enabled

---

### Low Priority (Post-MVP)

#### EA-MONITOR-001: Sentry Integration
**Priority**: Medium | **Type**: Task | **Estimate**: 2 SP

**Description**:  
Error tracking with Sentry.

**Acceptance Criteria**:
- [ ] SDK installed (backend + frontend)
- [ ] Errors auto-captured
- [ ] Release tracking
- [ ] Email/Slack alerts

---

#### EA-MONITOR-002: Metrics Dashboard
**Priority**: Low | **Type**: Task | **Estimate**: 5 SP

**Description**:  
Create Grafana dashboard for key metrics.

**Metrics**:
- Email processing rate
- Agent auto-reply rate (%)
- Escalation rate (%)
- Override rate (%)
- Avg confidence score
- API response time
- Token usage & cost

**Acceptance Criteria**:
- [ ] Prometheus metrics endpoint
- [ ] Grafana dashboard
- [ ] Alerts for anomalies

---

#### EA-TEST-003: E2E Tests
**Priority**: Low | **Type**: Task | **Estimate**: 8 SP

**Description**:  
Playwright E2E tests for critical journeys.

**Journeys**:
1. Create listing → upload document → view in agent
2. Email received → agent drafts → broker sends
3. NDA question → agent requests NDA → broker updates → follow-up
4. Escalation → broker manual reply

**Acceptance Criteria**:
- [ ] Playwright configured
- [ ] 4 test suites
- [ ] Run in CI/CD
- [ ] Screenshots on failure

---

#### EA-FEAT-001: Multi-Listing Inquiries
**Priority**: Low | **Type**: Feature | **Estimate**: 8 SP

**Description**:  
Handle emails about multiple listings.

**Acceptance Criteria**:
- [ ] Agent identifies multiple listings
- [ ] Responds with summary of all
- [ ] Asks clarifying questions

---

#### EA-FEAT-002: CRM Integration (HubSpot)
**Priority**: Low | **Type**: Feature | **Estimate**: 13 SP

**Description**:  
Sync leads and activities with HubSpot.

**Acceptance Criteria**:
- [ ] Leads synced on creation
- [ ] Email activities logged
- [ ] Agent responses as notes
- [ ] Bidirectional sync

---

#### EA-FEAT-003: Advanced NDA (DocuSign)
**Priority**: Low | **Type**: Feature | **Estimate**: 8 SP

**Description**:  
E-signature workflow integration.

**Acceptance Criteria**:
- [ ] Create envelope via API
- [ ] Send to lead email
- [ ] Webhook for signature
- [ ] Auto-update status
- [ ] Confirmation email

---

#### EA-FEAT-004: Lead Scoring
**Priority**: Low | **Type**: Feature | **Estimate**: 8 SP

**Description**:  
Auto-score leads based on engagement.

**Factors**: Email count, question depth, response time, NDA signed, meeting booked, financial keywords

**Acceptance Criteria**:
- [ ] Scoring algorithm
- [ ] Score updated after each interaction
- [ ] High scores highlighted in UI
- [ ] Displayed in thread view

---

#### EA-FEAT-005: Google Calendar Integration
**Priority**: Low | **Type**: Feature | **Estimate**: 8 SP

**Description**:  
Dynamic meeting slots from Google Calendar.

**Acceptance Criteria**:
- [ ] API connected
- [ ] Tool: `get_available_slots(broker_id, days=7)`
- [ ] Returns 2-3 slots
- [ ] Lead confirms via reply
- [ ] Adds to broker calendar

---

#### EA-FEAT-006: Email Templates
**Priority**: Low | **Type**: Feature | **Estimate**: 5 SP

**Description**:  
Customizable email templates.

**Types**: NDA request, meeting invite, general inquiry, escalation

**Acceptance Criteria**:
- [ ] Template editor (rich text)
- [ ] Variable placeholders `{{lead.name}}`
- [ ] Preview mode
- [ ] Stored in broker_settings
- [ ] Agent uses custom templates

---

## 📊 Sprint Metrics

### Week 1-2 (Completed)
- **Planned**: 45 SP
- **Completed**: 45 SP
- **Velocity**: 22.5 SP/week

### Week 3 (Completed)
- **Planned**: 30 SP
- **Completed**: 30 SP
- **Velocity**: 30 SP/week

### Week 4 (In Planning → In Progress)
- **Planned**: 47 SP
- **Focus**: Dashboard & Admin Panel (analytics, review queue, agent reasoning)
- **Tickets**: EA-DASH-001 to EA-DASH-004, EA-API-006 to EA-API-007, EA-DB-003
- **Backend**: 13 SP | **Frontend**: 34 SP

---

## 🏷️ Legend

**Priority**:
- 🔴 High - Critical path, blocking other work
- 🟡 Medium - Important but not blocking
- 🟢 Low - Nice to have, future enhancement

**Status**:
- ✅ Done - Completed and tested
- 🟡 In Progress - Currently being worked on
- 📝 To Do - Not started
- ⏸️ Blocked - Waiting on dependencies
- ❌ Cancelled - No longer needed

**Estimate (Story Points)**:
- 1 SP = 1-2 hours
- 2 SP = 2-4 hours
- 3 SP = 4-6 hours
- 5 SP = 1 day
- 8 SP = 2 days
- 13 SP = 3-4 days

---

## 📝 Notes

### Definition of Done
1. Code implemented and peer reviewed
2. Tests written (unit + integration)
3. Documentation updated
4. Deployed to staging
5. Product owner approved

### Velocity Tracking
- **Historical**: 22.5 SP/week (Weeks 1-2), 30 SP/week (Week 3)
- **Target**: 25-30 SP/week

### Risk Items
- Gmail API quota limits (10,000 requests/day)
- OpenAI rate limits and costs
- pgvector performance at scale (monitor when >10k chunks)
