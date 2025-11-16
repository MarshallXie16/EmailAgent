# Implementation Tasks

## Current Status: Week 1 - Foundations

### Week 1-2: Foundations & Auth (Target: 2 weeks)

#### Backend Setup
- [x] Create project structure
- [x] Create .gitignore
- [x] Create CLAUDE.md with agent instructions
- [x] Create memory.md with architecture decisions
- [x] Create tasks.md (this file)
- [x] Create README.md
- [ ] Initialize Python backend with FastAPI
- [ ] Set up requirements.txt with all dependencies
- [ ] Configure .env.example
- [ ] Set up Black, Flake8, isort for code quality

#### Database
- [ ] Install PostgreSQL locally
- [ ] Install pgvector extension
- [ ] Set up Alembic for migrations
- [ ] Create initial migration with all tables
- [ ] Create SQLAlchemy models
- [ ] Create database connection pool
- [ ] Test connection and basic CRUD

#### Authentication
- [ ] Implement password hashing (Argon2)
- [ ] Create JWT token generation/validation
- [ ] Build POST /api/v1/auth/login endpoint
- [ ] Build POST /api/v1/auth/refresh endpoint
- [ ] Build GET /api/v1/brokers/me endpoint
- [ ] Add auth middleware/dependency
- [ ] Test auth flow end-to-end

#### Broker Settings
- [ ] Build GET /api/v1/settings endpoint
- [ ] Build PATCH /api/v1/settings endpoint
- [ ] Implement settings schema validation
- [ ] Test batch_windows JSONB storage
- [ ] Create seed script for initial broker

#### Frontend Setup
- [ ] Initialize Next.js 14 project
- [ ] Set up TypeScript config
- [ ] Configure Tailwind CSS
- [ ] Install and configure shadcn/ui
- [ ] Create auth context/provider
- [ ] Build login page
- [ ] Build dashboard layout
- [ ] Build settings page
- [ ] Test frontend auth flow

---

### Week 3: Email Ingestion & Listings (Target: 1 week)

#### Listings API
- [ ] Build GET /api/v1/listings endpoint
- [ ] Build POST /api/v1/listings endpoint
- [ ] Build GET /api/v1/listings/{id} endpoint
- [ ] Build PATCH /api/v1/listings/{id} endpoint
- [ ] Build DELETE /api/v1/listings/{id} (soft delete)
- [ ] Implement listing search/filter
- [ ] Write tests for listings CRUD

#### Document Upload & S3
- [ ] Set up S3 client (boto3)
- [ ] Build POST /api/v1/listings/{id}/documents endpoint
- [ ] Implement multipart file upload
- [ ] Generate signed URLs for viewing
- [ ] Test file upload to S3
- [ ] Handle file type validation (PDF, DOCX, TXT)

#### Document Ingestion & Embeddings
- [ ] Build text extraction (pymupdf for PDF, python-docx for DOCX)
- [ ] Implement chunking strategy (500-1000 tokens)
- [ ] Integrate OpenAI embeddings API
- [ ] Build background job for ingestion
- [ ] Create POST /api/v1/listings/{id}/regenerate-embeddings
- [ ] Test vector search queries
- [ ] Build Celery/RQ worker setup

#### Gmail API Setup
- [ ] Set up Google Cloud project
- [ ] Enable Gmail API
- [ ] Create OAuth2 credentials
- [ ] Build OAuth2 flow for token generation
- [ ] Implement poll_gmail_for_new_messages() job
- [ ] Test reading emails from inbox
- [ ] Implement custom label creation ("processed")
- [ ] Test marking emails as processed

#### Email Thread Management
- [ ] Build email parsing logic (headers, body, threading)
- [ ] Implement lead auto-creation from sender email
- [ ] Implement thread auto-creation from Gmail threadId
- [ ] Build GET /api/v1/email-threads endpoint
- [ ] Build GET /api/v1/email-threads/{id} endpoint
- [ ] Build GET /api/v1/leads endpoint
- [ ] Build GET /api/v1/leads/{id} endpoint

#### Frontend - Listings
- [ ] Build listings list page
- [ ] Build listing detail page
- [ ] Build create/edit listing form
- [ ] Build document upload UI
- [ ] Test CRUD operations from UI

---

### Week 4: Agent Core (Target: 1 week)

#### LLM Integration
- [ ] Design system prompt for agent
- [ ] Build OpenAI client wrapper
- [ ] Implement function/tool calling structure
- [ ] Create agent_runs table logging
- [ ] Test basic LLM call with tools

#### Agent Tools
- [ ] Build identify_listing(email_text) tool
- [ ] Build get_listing_summary(listing_id) tool
- [ ] Build search_listing_knowledge(listing_id, query) tool (RAG)
- [ ] Build get_nda_status(lead_id, listing_id) tool
- [ ] Build generate_nda_link(lead_id, listing_id) tool
- [ ] Build get_broker_settings(broker_id) tool
- [ ] Test each tool independently

#### Agent Orchestration
- [ ] Build run_agent_for_thread() function
- [ ] Implement context building (last N messages)
- [ ] Implement response generation
- [ ] Implement confidence scoring
- [ ] Implement escalation logic
- [ ] Store results in agent_runs table
- [ ] Test agent with mock email threads

#### Batch Processing
- [ ] Build run_email_batch_for_broker() Celery task
- [ ] Implement timezone-aware scheduling
- [ ] Parse batch_windows from broker_settings
- [ ] Query open threads needing responses
- [ ] Implement draft-only mode (no sending)
- [ ] Test batch job execution
- [ ] Set up Celery beat for scheduling

#### Frontend - Conversations
- [ ] Build email threads list page
- [ ] Build thread detail view (messages + agent response)
- [ ] Build agent run inspector (tools called, confidence)
- [ ] Add filters (status, listing, date)
- [ ] Test viewing agent-generated drafts

---

### Week 5: NDA + Calendly + Auto-Send (Target: 1 week)

#### NDA Gating
- [ ] Build NDA status checking in agent
- [ ] Implement NDA request email template
- [ ] Build NDA recording UI for brokers
- [ ] Test NDA gating flow end-to-end
- [ ] Create manual NDA update endpoint

#### Calendly Integration
- [ ] Store Calendly link in broker_settings
- [ ] Detect high-intent leads in agent logic
- [ ] Include Calendly link in responses
- [ ] Test booking link inclusion

#### Auto-Send & Email Sending
- [ ] Build send_email_via_gmail() function
- [ ] Implement auto_send_enabled toggle
- [ ] Send emails during batch if auto_send=true
- [ ] Create outbound email_messages records
- [ ] Test Gmail sending with proper threading (In-Reply-To)
- [ ] Implement rate limiting (max replies per thread per day)

#### Broker Override
- [ ] Build POST /api/v1/email-threads/{id}/override-reply endpoint
- [ ] Implement manual reply editing in UI
- [ ] Mark overridden messages as sent_by="broker"
- [ ] Test override flow end-to-end

#### Frontend - Settings
- [ ] Build auto-send toggle UI
- [ ] Build batch windows editor (timezone-aware)
- [ ] Build Calendly link input
- [ ] Build NDA URL input
- [ ] Test settings updates

---

### Week 6: Hardening & Pilot (Target: 1 week)

#### Logging & Monitoring
- [ ] Set up structured logging (JSON format)
- [ ] Add request ID tracking
- [ ] Log all LLM calls (prompt, response, cost)
- [ ] Log all email sends
- [ ] Log all agent escalations
- [ ] Set up error alerting (email or Slack webhook)

#### Error Handling
- [ ] Implement retry logic for Gmail API failures
- [ ] Implement retry logic for OpenAI API failures
- [ ] Handle malformed emails gracefully
- [ ] Add input validation on all endpoints
- [ ] Test error scenarios (API down, bad data, etc.)

#### Edge Cases
- [ ] Handle emails with no clear listing match
- [ ] Handle multi-listing inquiries
- [ ] Handle spam/junk emails (basic filtering)
- [ ] Handle broker's own emails (ignore)
- [ ] Handle out-of-office replies
- [ ] Test with real email samples

#### Testing
- [ ] Write unit tests for agent tools
- [ ] Write integration tests for API endpoints
- [ ] Write tests for email parsing
- [ ] Write tests for batch processing logic
- [ ] Achieve >70% code coverage
- [ ] Manual QA of full user journey

#### Documentation
- [ ] Update README with setup instructions
- [ ] Create .env.example with all variables
- [ ] Document API in Swagger/OpenAPI
- [ ] Create broker user guide
- [ ] Document common issues in fixed_bugs.md
- [ ] Create runbook for ops tasks

#### Deployment Prep
- [ ] Create Dockerfile for backend
- [ ] Create docker-compose.yml for local dev
- [ ] Set up Railway/Fly.io project
- [ ] Deploy to staging
- [ ] Test on staging
- [ ] Set up production database
- [ ] Deploy to production
- [ ] Verify all environment variables

#### Pilot Testing
- [ ] Create first broker account
- [ ] Import initial listings
- [ ] Upload sample documents
- [ ] Connect Gmail inbox
- [ ] Run first batch manually
- [ ] Monitor for 1 week
- [ ] Collect feedback
- [ ] Fix critical issues

---

## Backlog (Post-MVP)

### Feature Enhancements
- [ ] Multi-broker support (self-serve onboarding)
- [ ] CRM integration (HubSpot, Salesforce)
- [ ] Google Calendar integration (real meeting slots)
- [ ] Full NDA signing workflow (SignWell/DocuSign)
- [ ] Lead scoring algorithm
- [ ] Email templates editor
- [ ] A/B testing for agent responses
- [ ] Mobile app (React Native)

### Technical Improvements
- [ ] Migrate to separate vector DB (Qdrant/Pinecone)
- [ ] Implement caching layer (Redis for listing summaries)
- [ ] Add rate limiting middleware
- [ ] Implement webhook endpoints for integrations
- [ ] Add analytics dashboard (PostHog)
- [ ] Set up CI/CD pipeline
- [ ] Add E2E tests (Playwright)
- [ ] Performance optimization (DB query tuning)

### Scaling
- [ ] Horizontal scaling for workers
- [ ] Database read replicas
- [ ] CDN for frontend
- [ ] Background job monitoring (Flower)
- [ ] APM integration (Sentry, DataDog)

---

## Technical Debt

_(None yet - will track as we build)_

---

## Bugs

_(None yet - will track as discovered)_

---

## Completed

- [x] Project initialization
- [x] Documentation structure
- [x] .gitignore setup
- [x] CLAUDE.md created
- [x] memory.md created
- [x] tasks.md created
- [x] README.md created
