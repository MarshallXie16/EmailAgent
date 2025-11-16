# technical_requirements.md

## 1. Overview & MVP Scope

**Product:**
Email-based AI assistant for business brokers that:

* Ingests inbound emails from a broker mailbox (Gmail for MVP).
* Answers common questions about listings using internal data + documents.
* Gates sensitive info behind NDA + encourages meeting bookings.
* Processes emails in **batches** at configured times to mimic a human assistant.
* Escalates anything ambiguous or high-risk to the broker instead of guessing.

**Out of scope for MVP:**

* Multiple email providers (Exchange, IMAP).
* Self-serve multi-tenant onboarding (we’ll configure tenants manually in DB).
* Full CRM replacement. (We integrate with 1 CRM later; MVP can be internal-only.)

---

## 2. Technology Stack

### 2.1 Frontend (Broker Dashboard)

* **Framework:** Next.js (v14) with React, TypeScript
* **UI:** Tailwind CSS + Headless UI or shadcn/ui
* **Build/Package:** pnpm or yarn, Vite not required (Next.js built-in)
* **Purpose in MVP:**

  * Broker login and simple dashboard:

    * View recent conversations.
    * Toggle agent auto-send / draft-only mode.
    * Configure batch windows and basic settings.

### 2.2 Backend

* **Language:** Python 3.11+
* **Framework:** FastAPI
* **Server:** Uvicorn / Gunicorn
* **Background jobs:**

  * Celery or RQ (Redis-backed) for:

    * Email polling.
    * Batch processing windows.
    * LLM calls.

### 2.3 Databases

* **Primary DB:** PostgreSQL (e.g. managed Postgres on Railway / Supabase / RDS)
* **Vector Search:**

  * Use `pgvector` extension in the same Postgres instance for MVP.
  * If we outgrow it, we can move to separate Qdrant/Pinecone, but not in v1.

### 2.4 Authentication

* **Broker-facing auth only (no public app):**

  * Email/password login for MVP.
  * JWT-based session tokens or NextAuth with credentials provider.
* **Password hashing:** Argon2 or bcrypt.
* **Session storage:**

  * HTTP-only secure cookies.

### 2.5 Hosting

* **Backend + Frontend:**

  * Single monorepo; deploy as:

    * Next.js frontend on Vercel (or same Docker stack as backend if you prefer).
    * FastAPI backend on Railway / Fly.io / Render.
* **Background workers:**

  * Same provider as backend using Docker container.

### 2.6 File Storage

* **Service:** S3-compatible storage (AWS S3, Backblaze, or Supabase storage).
* **Use cases:**

  * Storing listing PDFs (CIM excerpts, teasers).
  * Storing generic FAQ docs and broker materials.
* **Access pattern:**

  * Backend pulls docs → splits into chunks → stores embeddings in `pgvector`.

### 2.7 External Integrations

* **Email:** Gmail API (OAuth2 service account or delegated access).
* **Calendar (for meetings):**

  * MVP: static Calendly link per broker stored in DB.
  * Future: Google Calendar API for time slot generation.
* **LLM provider:** OpenAI (e.g. GPT-4.x function calling).
* **NDA/e-sign (optional in MVP):**

  * MVP: static NDA template link (PDF or webform).
  * Later: integrate with SignWell/DocuSign via API.

---

## 3. System Architecture (Monolith)

### 3.1 High-Level Components

* **API Server (FastAPI)**

  * REST endpoints for:

    * Broker dashboard
    * Listings & leads
    * Settings
  * Internal endpoints for:

    * Webhooks (if used later)
    * Test agent runs

* **Background Worker**

  * Periodic job: Poll new emails from Gmail.
  * Periodic job: Run batch-processing windows.
  * Agent orchestration:

    * Fetch context.
    * Call LLM with tools.
    * Store result.
    * Trigger email send.

* **Frontend**

  * Broker dashboard:

    * Config & logs.
    * Quick view of agent replies.

* **Shared Postgres DB with pgvector**

  * All domain data + embeddings.

### 3.2 API Design Principles

* REST, versioned: `/api/v1/...`
* JSON request/response.
* Auth via Bearer token (for dashboard) or cookie; internal jobs use service tokens.

---

## 4. API Design (REST Endpoints)

### 4.1 Auth & Broker Management

* `POST /api/v1/auth/login`

  * Body: `{ email, password }`
  * Response: `{ access_token, refresh_token }`

* `POST /api/v1/auth/refresh`

  * Body: `{ refresh_token }`
  * Response: `{ access_token }`

* `GET /api/v1/brokers/me`

  * Returns broker profile and settings.

### 4.2 Listings

* `GET /api/v1/listings`

  * Query: `status`, `search`
  * Response: list of listings for logged-in broker.

* `POST /api/v1/listings`

  * Body:

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
      "short_description": "High-traffic location...",
      "notes": "Internal broker notes"
    }
    ```
  * Logic:

    * Create listing.
    * Optionally trigger ingestion of attached docs (if file upload included).

* `GET /api/v1/listings/{id}`

* `PATCH /api/v1/listings/{id}`

* `DELETE /api/v1/listings/{id}` (soft delete `status = archived`).

### 4.3 Listing Knowledge Ingestion

* `POST /api/v1/listings/{id}/documents`

  * Multipart form:

    * `file`: PDF, DOCX, or text file.
    * `type`: `"teaser" | "cim_excerpt" | "faq" | "internal_notes"`
  * Logic:

    * Store file in S3.
    * Extract text (e.g. using pdfminer/pymupdf).
    * Chunk + embed.
    * Insert rows in `listing_documents` + `listing_document_chunks` (with vectors).

* `POST /api/v1/listings/{id}/regenerate-embeddings`

  * Recompute embeddings for all docs for this listing.

### 4.4 Leads, Threads, and Emails

* `GET /api/v1/leads`

  * List leads for broker.

* `GET /api/v1/leads/{id}`

  * Show lead details + recent threads.

* `GET /api/v1/email-threads`

  * Parameters: `status`, `listing_id`
  * Returns thread metadata.

* `GET /api/v1/email-threads/{id}`

  * Includes messages + agent responses.

* `POST /api/v1/email-threads/{id}/override-reply`

  * Body: `{ body_text }`
  * Logic:

    * Replace agent-drafted response with broker’s manual text.
    * Mark as `sent_by = "broker"` and send via Gmail.

### 4.5 Settings & Batch Windows

* `GET /api/v1/settings`
* `PATCH /api/v1/settings`

  * Body example:

    ```json
    {
      "auto_send_enabled": true,
      "batch_windows": [
        {"start": "09:00", "end": "09:30"},
        {"start": "12:00", "end": "12:30"},
        {"start": "16:00", "end": "16:30"}
      ],
      "calendly_link": "https://calendly.com/broker/intro-call",
      "default_nda_url": "https://example.com/nda-form"
    }
    ```

### 4.6 Internal/Tooling Endpoints

* `POST /api/v1/agent/test-run`

  * For internal testing from dashboard: simulate a prompt and show response without sending email.

---

## 5. Database Schema (Normalized)

### 5.1 Tables

**brokers**

* `id` (PK, UUID)
* `name`
* `email` (login)
* `password_hash`
* `timezone`
* `created_at`
* `updated_at`

**broker_settings**

* `id` (PK)
* `broker_id` (FK → brokers)
* `auto_send_enabled` (bool)
* `batch_windows` (JSONB: array of `{start, end}`)
* `calendly_link` (text)
* `default_nda_url` (text)
* `llm_model` (text) – future flexibility
* Index: `(broker_id)`

**listings**

* `id` (PK, UUID)
* `broker_id` (FK → brokers)
* `code` (unique per broker)
* `title`
* `status` (`active`, `pending`, `sold`, `archived`)
* `asking_price` (numeric)
* `revenue` (numeric)
* `sde` (numeric)
* `location_region` (text)
* `confidentiality_level` (`low`, `medium`, `high`)
* `short_description` (text)
* `notes` (text, internal)
* `created_at`, `updated_at`
* Indexes: `(broker_id)`, `(code)`, `(status, broker_id)`

**listing_documents**

* `id` (PK)
* `listing_id` (FK → listings)
* `file_url` (S3 path)
* `type` (enum)
* `title`
* `created_at`

**listing_document_chunks**

* `id` (PK)
* `listing_document_id` (FK → listing_documents)
* `content` (text)
* `embedding` (vector)
* `metadata` (JSONB: page number, section)
* Index: vector index on `embedding` using `ivfflat` or similar.

**leads**

* `id` (PK, UUID)
* `broker_id` (FK)
* `email`
* `name`
* `type` (`buyer`, `seller`, `other`)
* `lead_score` (int, nullable)
* `created_at`, `updated_at`
* Unique: `(broker_id, email)`

**ndas**

* `id` (PK)
* `lead_id` (FK → leads)
* `listing_id` (FK → listings)
* `status` (`sent`, `signed`, `rejected`, `revoked`)
* `nda_url` (text)
* `signed_at` (nullable)
* Index: `(lead_id, listing_id)`

**email_threads**

* `id` (PK, UUID)
* `broker_id` (FK)
* `lead_id` (FK)
* `listing_id` (FK, nullable)
* `external_thread_id` (Gmail thread ID)
* `status` (`open`, `closed`, `needs_broker`)
* `last_agent_action` (`none`, `auto_reply_sent`, `draft_created`, `escalated`)
* `created_at`, `updated_at`
* Index: `(broker_id, status)`

**email_messages**

* `id` (PK)
* `email_thread_id` (FK)
* `direction` (`inbound`, `outbound`)
* `from_email`
* `to_email`
* `subject`
* `body_text` (text)
* `sent_at` (timestamp)
* `raw_metadata` (JSONB)
* `sent_by` (`lead`, `broker`, `agent`)
* Index: `(email_thread_id, sent_at)`

**agent_runs**

* `id` (PK)
* `email_thread_id` (FK)
* `llm_model`
* `prompt` (text)
* `response` (text)
* `tools_called` (JSONB)
* `confidence_score` (numeric)
* `final_action` (`answer`, `ask_nda`, `book_meeting`, `escalate`)
* `error_flag` (bool)
* `created_at`

---

## 6. File / Asset Handling

* **Upload path pattern:**

  * `brokers/{broker_id}/listings/{listing_id}/{document_type}/{filename}`
* **Ingestion flow:**

  1. User uploads file via POST `/listings/{id}/documents`.
  2. Backend stores to S3.
  3. Worker:

     * Extracts text.
     * Splits into ~500–1000 token chunks.
     * Embeds chunks (OpenAI embeddings).
     * Inserts into `listing_document_chunks` with vector column.
* **Serving to broker:**

  * Signed URLs from S3 for viewing in dashboard.

---

## 7. Core Features – Technical Spec

### 7.1 Feature: Email Ingestion (Gmail)

**Endpoints / Jobs:**

* Background job: `poll_gmail_for_new_messages()`

  * Runs every 5–10 minutes.
  * Uses Gmail API:

    * Search for messages with label `inbox` and **not** labeled `processed`.
  * For each new message:

    * Get full message.
    * Parse headers, body.
    * Identify or create `Lead` (via `from_email`).
    * Identify or create `EmailThread` (via `threadId` + `In-Reply-To`).
    * Insert `email_messages` row.
    * Label message as `processed` in Gmail (custom label).
    * Mark thread as `pending_processing`.

**Data Models:** as per DB schema.

**Business Logic:**

* Simple heuristics to determine `listing_id`:

  * Match listing code or title in subject/body.
  * If multiple matches: leave null; agent will ask clarifying question.
* If email from broker’s own address: ignore.

**Integrations:**

* Gmail API with OAuth2 credentials for each broker mailbox OR service account for one shared mailbox (MVP: one broker → one mailbox).

---

### 7.2 Feature: Batch Processing & Agent Run

**Job:** `run_email_batch_for_broker(broker_id)`

* Triggered:

  * By scheduler at configured `batch_windows` (in broker timezone).
* Steps:

  1. Load `broker_settings`.
  2. Query `email_threads` where:

     * `status = 'open'` and
     * there is at least one inbound message since the last outbound.
  3. For each thread:

     * Load last N messages (e.g. 10).
     * Build context for LLM:

       * Thread messages (trimmed).
       * Broker profile & settings.
       * Listing summary (if available).
     * Call internal `run_agent_for_thread()` (LLM + tools).
  4. Store agent result in `agent_runs`.
  5. If `auto_send_enabled`:

     * Immediately send response via Gmail API.
     * Insert outbound `email_messages` row (`direction='outbound'`, `sent_by='agent'`).
  6. If not auto-send:

     * Store as draft:

       * Via Gmail draft API (optional) **and** mark in DB for broker review.

**Tools inside agent (implemented as Python functions, exposed to LLM via tool-calling):**

* `identify_listing(email_text) -> { listing_id, confidence }`
* `get_listing_summary(listing_id)`
* `search_listing_knowledge(listing_id, query)`
* `get_nda_status(lead_id, listing_id)`
* `generate_nda_link(lead_id, listing_id)` (return stored `default_nda_url` + query params).
* `get_broker_settings(broker_id)`
* Future: `get_available_meeting_slots(broker_id)`

**Business Logic (LLM-side via system prompt):**

* If question is basic (availability, price range, region, high-level desc):

  * Answer using `get_listing_summary`.
* If question touches confidential fields (full address, customer list, detailed financials):

  * Check `get_nda_status`.
  * If not signed:

    * Respond with NDA request email, include link from `generate_nda_link`.
  * If signed:

    * Use `search_listing_knowledge` to answer, but still high-level.
* If unclear or model uncertain:

  * Choose `final_action = 'escalate'`.
  * Reply with generic “forwarding to broker” or skip auto-response.
  * Mark thread `status='needs_broker'`.

---

### 7.3 Feature: NDA Gating

**Endpoints (back-office / manual for MVP):**

* MVP does **not** need full NDA API integration; we only:

  * Store `default_nda_url` in `broker_settings`.
  * Allow broker to manually update `ndas` table once they see signed NDA.

**Future (optional):**

* Webhook endpoint: `POST /api/v1/nda/webhook`

  * To mark NDA as signed when PDF is executed via SignWell/DocuSign.

**Business Logic (MVP):**

* Agent can:

  * Include NDA link in reply.
  * Ask lead to confirm once signed.
* Broker manually updates NDA status in dashboard or via simple form.

---

### 7.4 Feature: Meeting Booking

**MVP Design:**

* No direct calendar integration.
* Use `calendly_link` from `broker_settings`.

**Business Logic:**

* Agent encourages high-intent leads to:

  * Click booking link.
  * Alternatively, propose a couple of time ranges manually.

**Future:**

* Use Google Calendar API to generate 2–3 concrete slots.

---

### 7.5 Feature: Broker Dashboard

**Endpoints:**

* `GET /api/v1/email-threads` – list
* `GET /api/v1/email-threads/{id}` – detail + messages + latest agent run
* `POST /api/v1/email-threads/{id}/override-reply` – send custom reply
* `GET /api/v1/settings` / `PATCH /api/v1/settings`

**Business Logic:**

* Allow broker to:

  * See how agent responded.
  * Toggle auto-send / draft-only mode.
  * Modify batch windows.
  * Provide Calendly + NDA URL.

**Frontend:**

* 2–3 pages:

  * Dashboard (list of recent threads).
  * Thread detail.
  * Settings.

---

## 8. Security & Compliance (MVP Level)

### 8.1 Authentication Flow

* Broker logs in via email + password.
* Backend:

  * Verifies credentials.
  * Issues JWT access + refresh tokens.
* Frontend:

  * Stores tokens in HTTP-only cookies.
  * Includes access token in API calls.

### 8.2 Basic Security Checklist (MVP)

* HTTPS only on all endpoints.
* Input validation with Pydantic models (FastAPI).
* Prepared statements via ORM (SQLAlchemy / SQLModel) to avoid SQL injection.
* Role-based access:

  * Broker can only read/write data for their `broker_id`.
* Do **not** store:

  * Gmail or NDA provider passwords in plain text.
* Limit LLM output:

  * Protect against prompt injection by:

    * Clear system prompt that prioritizes internal rules.
    * No direct user-provided instructions being executed as code.

---

## 9. Scaling Considerations (Document Only)

**Potential bottlenecks:**

* LLM calls for every email thread at every batch.
* Vector search queries on `listing_document_chunks`.
* Gmail polling overhead at scale.

**Caching opportunities:**

* Cache listing summaries and common FAQ embeddings.
* Cache per-listing high-level answers (e.g. “availability”, “asking price”) in Redis.

**DB optimization:**

* Add composite indexes for frequent queries:

  * `email_threads (broker_id, status, updated_at DESC)`
  * `email_messages (email_thread_id, sent_at)`
* Archive old threads to a separate table / partition.

**When to consider microservices:**

* When:

  * Multiple brokers with thousands of listings.
  * Email volume > ~10k messages/day.
* Break out:

  * Email ingestion service.
  * Agent / LLM orchestration service.
  * Vector search service (external).

---

## 10. Implementation Timeline (1–2 Devs, Realistic)

**Week 1–2: Foundations**

* Set up monorepo (frontend + backend).
* Implement auth & broker settings.
* Spin up Postgres with pgvector.
* Basic DB schema migrations.

**Week 3: Email + Listings**

* Gmail polling job (single mailbox).
* Listings CRUD + simple UI in dashboard.
* Ingestion of listing docs + embeddings.

**Week 4: Agent v1**

* Implement tool functions.
* System prompt + OpenAI tool-calling integration.
* Agent batch job that:

  * Reads threads.
  * Produces draft responses (no auto-send).
* Dashboard page to view conversations.

**Week 5: Auto-Send + NDA + Calendly**

* Add `auto_send_enabled` + batch windows.
* NDA link gating in responses.
* Support Calendly link in agent replies.
* Broker override flow.

**Week 6: Hardening & Pilot**

* Logging, basic monitoring.
* Edge-case handling for email parsing.
* Manual QA + dogfooding with 1 broker.
* Prepare for first live test.

Total: **~6 weeks** for a working MVP with one broker tenant.

---

# user_stories.md

## 1. Scope & Personas

**Personas:**

* **Broker Admin (“Broker”)**

  * Owns listings, receives inquiries, wants to save time.
* **Lead / Prospect**

  * Sends email about a listing or about selling/buying.
* **System (Agent)**

  * Internal actor that processes emails and drafts/sends replies.

Focus: MVP stories that validate core assumptions:

* The agent can respond usefully to common listing questions.
* NDA gating + booking links are enough to funnel serious leads.
* Brokers trust the agent because they can see & override.

---

## 2. Onboarding Stories

### Story 2.1 – Broker Signup & Login

**Story**
As a **broker**
I want to **log into a secure dashboard**
So that **I can configure and monitor the email agent**

**Acceptance Criteria**

* [ ] Broker can create an account or be created by admin with email + password.
* [ ] Broker can log in and see their own dashboard only.
* [ ] Incorrect credentials return a clear error message.
* [ ] Session persists during a browser session and logs out after inactivity.

---

### Story 2.2 – Configure Basic Settings

**Story**
As a **broker**
I want to **configure my agent settings (batch times, auto-send, links)**
So that **the agent behaves in a way that matches my workflow**

**Acceptance Criteria**

* [ ] Broker can toggle auto-send on/off.
* [ ] Broker can add/edit up to 3 batch windows in their local timezone.
* [ ] Broker can save a Calendly link.
* [ ] Broker can save a default NDA URL.
* [ ] Changes are persisted and reflected in the next batch run.

---

### Story 2.3 – Connect Mailbox (MVP: one shared Gmail)

**Story**
As a **broker**
I want to **have my main inquiry inbox connected to the agent**
So that **incoming emails are automatically processed**

**Acceptance Criteria**

* [ ] System can read new emails from a designated Gmail inbox.
* [ ] Each new inbound email is recorded as a `lead` + `email_thread`.
* [ ] Emails already labeled as processed are not re-ingested.
* [ ] System marks processed emails in Gmail with a custom label.

*(For MVP, mailbox connection is configured by devs / ops, not self-serve.)*

---

## 3. Core Value Stories (Main Feature)

### Story 3.1 – Auto-Answer Basic Listing Questions

**Story**
As a **lead interested in a listing**
I want to **receive a prompt, accurate reply with basic info**
So that **I can quickly assess if the listing is worth pursuing**

**Acceptance Criteria**

* [ ] When a lead emails with a subject or body referencing a listing code or title:

  * [ ] The system associates the email with the correct listing (when unambiguous).
* [ ] For questions about:

  * availability, asking price, high-level description, region,
    the agent uses:
  * [ ] Listing structured data (DB) and/or listing docs (vector DB).
* [ ] The agent’s reply:

  * [ ] Provides accurate information based on data in the system.
  * [ ] Does not invent details that are not present in DB/docs.
  * [ ] Acknowledges when information is not available and avoids guessing.

---

### Story 3.2 – Gate Sensitive Information Behind NDA

**Story**
As a **broker**
I want the **agent to require an NDA before sharing sensitive details**
So that **confidential information is protected**

**Acceptance Criteria**

* [ ] For questions about detailed financials, exact address, or sensitive operational details:

  * [ ] The agent checks NDA status for the lead/listing.
* [ ] If no NDA exists:

  * [ ] The agent replies with a polite explanation of the NDA requirement.
  * [ ] The reply includes the broker’s NDA link from settings.
* [ ] If an NDA is marked as signed:

  * [ ] The agent can share additional info but still avoids overly specific disclosures if not present in docs.
* [ ] The system records NDA status in the lead’s profile.

---

### Story 3.3 – Encourage Booking a Call for High-Intent Leads

**Story**
As a **high-intent lead**
I want to **quickly book time with the broker**
So that **I can discuss the opportunity in more depth**

**Acceptance Criteria**

* [ ] When the agent identifies a high-intent lead (e.g., specific questions, clear financial capability hints):

  * [ ] The agent includes a Calendly link in the reply.
  * [ ] The invitation to book is phrased clearly and naturally.
* [ ] Broker can see which threads included booking links.
* [ ] The agent does not overuse booking links for obviously low-intent/spam messages.

---

### Story 3.4 – Batch-Style Responses (Human-Like Timing)

**Story**
As a **lead**
I want the **reply timing to feel human**
So that **I trust the interaction and don’t feel spammed**

**Acceptance Criteria**

* [ ] The system processes inbound emails only during configured batch windows.
* [ ] Replies are sent within those windows with small, random delays per email.
* [ ] Leads do not receive more than a configurable number of responses per day (per thread).

---

## 4. Retention Stories (Trust & Control)

### Story 4.1 – Broker Review of Conversations

**Story**
As a **broker**
I want to **see what the agent is saying to leads**
So that **I can trust it and correct mistakes**

**Acceptance Criteria**

* [ ] Broker dashboard shows a list of recent email threads.
* [ ] Each thread shows:

  * [ ] Lead name/email.
  * [ ] Listing (if detected).
  * [ ] Last 5–10 messages (inbound + outbound).
  * [ ] Tag indicating whether reply was sent by agent or broker.
* [ ] Broker can filter threads by status: open, closed, needs broker.

---

### Story 4.2 – Override Agent Replies

**Story**
As a **broker**
I want to **override or edit the agent’s drafted reply**
So that **I stay in control of sensitive or nuanced communications**

**Acceptance Criteria**

* [ ] When auto-send is **disabled**, the agent’s replies are saved as drafts only (DB + optionally Gmail drafts).
* [ ] Broker can open a thread and:

  * [ ] See the agent’s suggested reply.
  * [ ] Edit the text.
  * [ ] Send the modified reply from the dashboard.
* [ ] System marks the final reply as `sent_by = broker`.
* [ ] When auto-send is enabled, broker can still see the sent replies but cannot retroactively change sent emails.

---

### Story 4.3 – Escalate Uncertain Questions

**Story**
As a **broker**
I want the **agent to escalate uncertain or risky questions instead of guessing**
So that **I avoid misinformation and liability**

**Acceptance Criteria**

* [ ] Agent can mark a thread as `needs_broker` when:

  * [ ] Information requested is not found in the system.
  * [ ] The query is ambiguous, legal/tax-related, or politically sensitive.
* [ ] For such threads:

  * [ ] The agent either sends a very generic “forwarding to broker” response, or sends nothing.
* [ ] These threads appear in a dedicated “Needs my attention” view in the dashboard.

---

## 5. Supporting Stories (NDA, Scheduling, Listings)

### Story 5.1 – Add and Maintain Listings

**Story**
As a **broker**
I want to **add and update listing details**
So that **the agent has accurate data to work from**

**Acceptance Criteria**

* [ ] Broker can create a listing with:

  * [ ] Basic fields: code, title, asking price, revenue, SDE, region, status.
* [ ] Broker can update listing status (active, pending, sold, archived).
* [ ] Only `active` listings are used by the agent to propose opportunities.
* [ ] Listing changes are reflected in new responses (no stale values).

---

### Story 5.2 – Upload Supporting Documents

**Story**
As a **broker**
I want to **upload supporting docs (teasers, CIM excerpts, FAQs)**
So that **the agent can answer more nuanced questions**

**Acceptance Criteria**

* [ ] Broker can upload at least PDFs as listing documents.
* [ ] Upload completes and shows file name + type in listing detail view.
* [ ] System ingests content into vector DB (background job).
* [ ] After ingestion:

  * [ ] Agent can answer questions based on these docs (e.g. staff count, lease summary).

---

### Story 5.3 – Record NDA Status

**Story**
As a **broker**
I want to **record when a lead has signed an NDA**
So that **the agent knows what to share**

**Acceptance Criteria**

* [ ] Broker can manually set NDA status (none/sent/signed) for a lead/listing pair.
* [ ] Signed status is visible in lead + thread view.
* [ ] Agent uses this status when deciding how much info to reveal.

---

## 6. Additional Considerations

### 6.1 Rough Cost Estimates (Per Month, MVP Scale)

Assume 1–3 brokers, low volume to start.

* **Backend hosting (FastAPI + worker):** ~$20–50 (Railway/Fly.io basic plan).
* **Postgres (with pgvector):** ~$15–50 (managed).
* **Frontend hosting (Vercel / similar):** $0–20 (hobby or small pro plan).
* **S3-compatible storage:** $5–10 (low volume of documents).
* **OpenAI usage:**

  * Assume ~1,000 agent runs/month to start.
  * ~$10–50 depending on model/length.
* **Total rough MVP infra:** **$50–150/month** at low volume.

---

### 6.2 Analytics Plan (Day One)

Track minimal but high-signal metrics:

* **Email-level:**

  * Number of inbound emails.
  * Number of threads handled by agent vs escalated.
  * Time from inbound to first reply.

* **Lead-level:**

  * NDAs requested vs NDAs signed.
  * Number of leads clicking booking link (via UTM or Calendly stats).

* **Broker-level:**

  * Auto-send vs draft-only usage.
  * Agent reply acceptance rate:

    * % of agent drafts sent without modification.

Implementation:

* Simple event logging via backend → Postgres `events` table or a third-party like PostHog (not required for MVP, but easy win).

---

### 6.3 Support Strategy

MVP assumption: internal pilot with a few brokers.

* Support handled directly by devs via:

  * Shared Slack/WhatsApp group or email.
* Monitoring:

  * Minimal logs + alerts:

    * Gmail polling failures.
    * LLM API failures.
    * DB connection issues.
* Simple “Report issue” button in dashboard:

  * Sends context + notes to dev support email.

---

### 6.4 Documentation Needs

For MVP:

* **Broker-facing docs (1–2 pages each):**

  * “Getting Started”

    * How the agent works conceptually.
    * What types of emails it handles.
  * “Configuration Guide”

    * How to set batch windows, NDA URL, Calendly link.
  * “Trust & Control”

    * How to review conversations.
    * How to override or disable auto-send.

* **Internal dev docs:**

  * `README` for local setup.
  * Short docs on:

    * Gmail integration.
    * LLM prompt + tools design.
    * DB schema overview.

---

## 7. Implementation Timeline (Aligned with Technical Plan)

Useful for planning sprints around stories.

**Week 1–2 (Onboarding + Listings)**

* Stories:

  * 2.1 Broker Signup & Login
  * 2.2 Configure Basic Settings
  * 5.1 Add and Maintain Listings
* Deliverable:

  * Broker can log in, configure settings, create/update listings.

**Week 3 (Email Ingestion + Dashboard Basics)**

* Stories:

  * 2.3 Connect Mailbox (MVP, configured by devs)
  * 5.2 Upload Supporting Documents
  * 4.1 Broker Review of Conversations (basic version)
* Deliverable:

  * Emails show up in dashboard as threads; documents are ingested.

**Week 4 (Agent Core Value)**

* Stories:

  * 3.1 Auto-Answer Basic Listing Questions
  * 3.4 Batch-Style Responses
* Deliverable:

  * Agent drafts basic replies during batch windows (draft-only mode).

**Week 5 (NDA + Booking + Trust)**

* Stories:

  * 3.2 Gate Sensitive Information Behind NDA
  * 3.3 Encourage Booking a Call
  * 4.2 Override Agent Replies
  * 5.3 Record NDA Status
* Deliverable:

  * Full flow: NDA gating + booking link + broker overrides.

**Week 6 (Retention and Hardening)**

* Stories:

  * 4.3 Escalate Uncertain Questions
  * Analytics + basic support hooks
* Deliverable:

  * System robust enough for a real broker to use with real leads.
