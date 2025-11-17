# Agent System Documentation

## Overview

The Email Agent is an LLM-powered system that autonomously responds to business listing inquiries while maintaining accuracy, protecting sensitive information, and escalating uncertain cases.

## Core Principles

1. **Accuracy over invention**: Never make up information
2. **Escalate when uncertain**: Better to forward than guess
3. **NDA compliance**: Gate sensitive info behind signed NDAs
4. **Human-like timing**: Batch processing mimics assistant behavior
5. **Broker control**: Override capability builds trust

## System Prompt

Located in `app/services/agent.py::get_system_prompt()`:

```
You are an AI assistant helping a business broker respond to email
inquiries about business listings.

Your role:
- Answer questions about listings using available data
- Gate sensitive information behind NDA requirements
- Encourage high-intent leads to book meetings
- Escalate uncertain or complex questions to the broker

Guidelines:
1. Be professional, friendly, and concise
2. NEVER make up information - only use data from tools
3. For confidential details (full financials, exact address, customer lists):
   - Check NDA status first
   - If no signed NDA, politely request one and provide link
4. For high-intent leads (serious questions, financial capability),
   include Calendly booking link
5. If uncertain or question is legal/tax-related, escalate to broker
6. Keep responses under 200 words

When to escalate:
- Question not answerable with available data
- Legal, tax, or financial advice requests
- Angry or complaint emails
- Ambiguous listing identification
- Confidence < 70%
```

## Available Tools

The agent has access to 6 tools (functions) it can call to gather information:

### 1. identify_listing

**Purpose**: Match email content to a specific listing

**Input**:
```python
{
  "email_text": "I'm interested in listing ABC123..."
}
```

**Output**:
```python
{
  "listing_id": "uuid-here",
  "listing_code": "ABC123",
  "listing_title": "Coffee Shop",
  "confidence": 0.85
}
```

**Logic**:
- Exact match on listing code: +10 points
- Title keyword match (word > 3 chars): +2 points per word
- Confidence = score / 20.0 (capped at 1.0)
- Returns listing if score >= 5

### 2. get_listing_summary

**Purpose**: Get public (non-sensitive) listing information

**Input**:
```python
{
  "listing_id": "uuid-here"
}
```

**Output**:
```python
{
  "code": "ABC123",
  "title": "Specialty Coffee Shop",
  "asking_price": 450000,
  "location_region": "Vancouver, BC",
  "short_description": "High-traffic location...",
  "status": "active"
}
```

**What's included**:
- ✅ Asking price
- ✅ Location (region only, not exact address)
- ✅ Short description
- ✅ Status
- ❌ Detailed financials
- ❌ Owner information
- ❌ Exact address

### 3. search_listing_knowledge

**Purpose**: RAG (Retrieval Augmented Generation) over uploaded documents

**Input**:
```python
{
  "listing_id": "uuid-here",
  "query": "How many employees?"
}
```

**Output**:
```python
[
  {
    "content": "The business currently employs 5 full-time and 3 part-time staff...",
    "metadata": {"page": 2, "source": "teaser.pdf"},
    "relevance": 0.92
  }
]
```

**Implementation**:
- Query embedding generated via OpenAI
- Cosine similarity search in pgvector
- Top 3 chunks returned
- Respects NDA status (controlled by agent logic)

**Note**: Currently stubbed, full implementation in Week 3

### 4. get_nda_status

**Purpose**: Check if lead has signed NDA for listing

**Input**:
```python
{
  "lead_id": "uuid-here",
  "listing_id": "uuid-here"
}
```

**Output**:
```python
{
  "status": "signed",  # or "sent", "none", "rejected", "revoked"
  "signed": true,
  "signed_at": "2024-01-15T14:30:00Z"
}
```

**Status meanings**:
- `none`: No NDA record exists
- `sent`: NDA link sent, not yet signed
- `signed`: NDA signed and active
- `rejected`: Lead declined NDA
- `revoked`: NDA was signed but revoked

### 5. generate_nda_link

**Purpose**: Create trackable NDA URL for lead

**Input**:
```python
{
  "lead_id": "uuid-here",
  "listing_id": "uuid-here",
  "broker_id": "uuid-here"
}
```

**Output**:
```python
"https://example.com/nda-form?lead_id=uuid&listing_id=uuid"
```

**Features**:
- Uses broker's `default_nda_url` from settings
- Appends tracking parameters
- Future: Could integrate with DocuSign/SignWell API

### 6. get_broker_settings

**Purpose**: Get broker preferences (Calendly, auto-send, etc.)

**Input**:
```python
{
  "broker_id": "uuid-here"
}
```

**Output**:
```python
{
  "calendly_link": "https://calendly.com/broker/intro-call",
  "auto_send_enabled": false
}
```

## Decision Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Receive Email                                             │
│    - Parse from/to/subject/body                             │
│    - Identify lead (create if new)                          │
│    - Link to thread (or create)                             │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Build Context                                             │
│    - Load last 10 messages in thread                        │
│    - Add system prompt                                      │
│    - Provide tool definitions                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. LLM Call #1 (with tools)                                 │
│    - GPT-4 analyzes email                                   │
│    - Decides which tools to call                            │
│    - Returns tool_calls array                               │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Tool Execution                                            │
│    For each tool_call:                                      │
│      - Parse function name & arguments                      │
│      - Execute corresponding AgentTool method               │
│      - Collect results                                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. LLM Call #2 (with tool results)                          │
│    - Add tool results to conversation                       │
│    - LLM synthesizes final response                         │
│    - No more tool calls needed                              │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. Determine Final Action                                   │
│    Heuristics:                                              │
│      - "escalate"/"forward" in response → ESCALATE          │
│      - "nda" in response → ASK_NDA                          │
│      - "meeting"/"call" in response → BOOK_MEETING          │
│      - Default → ANSWER                                     │
│    Confidence:                                              │
│      - Default 0.8                                          │
│      - If escalate → 0.3                                    │
└─────────────────┬───────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. Store & Act                                               │
│    - Create AgentRun record (prompt, response, tools, etc.) │
│    - If auto_send_enabled:                                  │
│        └─> Send via Gmail                                   │
│    - Else:                                                   │
│        └─> Save as draft for broker review                  │
└─────────────────────────────────────────────────────────────┘
```

## Example Conversations

### Example 1: Basic Inquiry (Public Info)

**Inbound Email**:
> Subject: Question about ABC123
>
> Hi, is this coffee shop still available? What's the asking price?

**Agent Process**:
1. Tools called:
   - `identify_listing("...is this coffee shop...")` → ABC123
   - `get_listing_summary(ABC123)` → {price: $450k, status: active}
2. Response generated:
   > Yes, this coffee shop (ABC123) is still available! The asking
   > price is $450,000. It's a high-traffic location in Vancouver, BC
   > with a loyal customer base. Would you like to schedule a call to
   > discuss further? [Calendly link]
3. Final action: `BOOK_MEETING`
4. Confidence: 0.85

**Outcome**: Email sent automatically (if auto_send enabled)

### Example 2: Sensitive Question (NDA Required)

**Inbound Email**:
> What are the exact sales numbers for the last 3 years? Also, who
> are the main suppliers?

**Agent Process**:
1. Tools called:
   - `identify_listing(...)` → ABC123
   - `get_nda_status(lead_id, ABC123)` → {status: "none", signed: false}
   - `generate_nda_link(...)` → "https://example.com/nda?..."
2. Response generated:
   > Thank you for your interest! Detailed financial information and
   > supplier details are confidential and require a signed NDA. You can
   > review and sign the NDA here: [link]. Once signed, I'll be happy to
   > share comprehensive financials.
3. Final action: `ASK_NDA`
4. Confidence: 0.90

**Outcome**: Email sent with NDA link

### Example 3: Escalation (Uncertain)

**Inbound Email**:
> I'm interested but I need to understand the tax implications for a
> Canadian buyer purchasing a US business. Can you advise?

**Agent Process**:
1. Tools called:
   - `identify_listing(...)` → ABC123
2. Response generated:
   > Thank you for your question. Tax implications for cross-border
   > acquisitions are complex and require professional tax advice. I'll
   > forward your inquiry to the broker who can connect you with
   > qualified advisors. Expect a response within 24 hours.
3. Final action: `ESCALATE`
4. Confidence: 0.30

**Outcome**:
- Thread status → `needs_broker`
- No auto-send (even if enabled)
- Broker sees in "Needs Attention" queue

### Example 4: High-Intent Lead (Meeting Booking)

**Inbound Email**:
> I'm a qualified buyer with $500k cash. I've reviewed the teaser and
> I'm very interested. Can we schedule a call this week?

**Agent Process**:
1. Tools called:
   - `identify_listing(...)` → ABC123
   - `get_broker_settings(broker_id)` → {calendly_link: "..."}
2. Response generated:
   > Great to hear you're interested and have reviewed the materials!
   > I'd be happy to arrange a call. You can book a time directly on
   > the broker's calendar here: [Calendly link]. Looking forward to
   > speaking with you!
3. Final action: `BOOK_MEETING`
4. Confidence: 0.95

**Outcome**: Email sent with Calendly link

## Confidence Scoring

Currently simple heuristics (to be ML-based in future):

- **High (0.8-1.0)**: Clear question, listing identified, data available
- **Medium (0.5-0.7)**: Some ambiguity, partial data
- **Low (0.0-0.4)**: Uncertain, missing data, complex question

**Threshold**: If confidence < 0.7 → Escalate

## Token Usage Tracking

Each `AgentRun` stores:
```python
{
  "usage": {
    "prompt_tokens": 1500,
    "completion_tokens": 300,
    "total_tokens": 1800
  }
}
```

This enables:
- Cost monitoring
- Budget alerts
- Optimization opportunities

## Batch Processing

Agent runs are triggered by `run_email_batch_for_broker()` Celery task:

**Schedule**: Configured batch windows (e.g., 9am, 12pm, 4pm)

**Logic**:
1. Query threads where `status=open` and has new inbound message since last outbound
2. For each thread:
   - Load conversation history (last 10 messages)
   - Call `AgentService.generate_response()`
   - Store `AgentRun`
   - Send or draft based on `auto_send_enabled`

**Randomization**: Small delay (1-5 minutes) between emails to appear human

## Future Enhancements

### Week 6+

1. **Improved Confidence Scoring**:
   - ML model trained on broker feedback
   - Tool execution success rates
   - Historical accuracy per question type

2. **Learning from Overrides**:
   - Track when broker edits agent responses
   - Fine-tune system prompt
   - Build FAQ from common overrides

3. **Advanced NDA Logic**:
   - Auto-trigger NDA for specific questions
   - Track NDA expiration
   - Remind leads to sign

4. **Multi-Listing Inquiries**:
   - Handle "Do you have any restaurants?" queries
   - Compare multiple listings
   - Recommend best fit

5. **Sentiment Analysis**:
   - Detect frustration/anger → Immediate escalation
   - Detect high intent → Priority routing

6. **A/B Testing**:
   - Test different response styles
   - Optimize Calendly inclusion timing
   - Measure lead conversion rates

## Monitoring & Debugging

**Key Metrics**:
- Auto-reply rate (% of emails handled autonomously)
- Escalation rate (target: <20%)
- Override rate (% of drafts edited by broker)
- Average confidence score
- Response time (batch window to send)

**Debugging**:
- All `AgentRun` records stored with full prompt, response, and tools
- Broker can view in thread detail page
- "Replay" capability to re-run agent with same inputs

## Testing

See `backend/tests/test_agent.py`:
- Tool execution tests (mocked DB)
- Response generation (mocked OpenAI)
- System prompt validation
- Tool definition schema

Run: `pytest backend/tests/test_agent.py -v`
