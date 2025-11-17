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

### Week 4 (In Planning)
- **Target**: 35 SP
- **Focus**: Frontend development + deployment prep

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
