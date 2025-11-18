# Sentry Error Tracking Setup Guide

This guide explains how to set up Sentry error tracking for the Email Agent application.

## Overview

Sentry provides real-time error tracking and performance monitoring for both backend and frontend:
- **Backend**: FastAPI, Celery workers, and background tasks
- **Frontend**: Next.js (client-side and server-side rendering)

## Prerequisites

- Sentry account (free tier available at [sentry.io](https://sentry.io))
- Project created in Sentry
- DSN (Data Source Name) from your Sentry project

## Backend Setup

### 1. Install Dependencies

The Sentry SDK is already included in `requirements.txt`:
```txt
sentry-sdk==1.40.0
```

Install it:
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variable

Add your Sentry DSN to `.env.prod`:
```bash
SENTRY_DSN=https://your-sentry-dsn@sentry.io/your-project-id
```

**Note**: Sentry is automatically disabled in development environments.

### 3. Verify Configuration

The backend automatically initializes Sentry on startup:
- **FastAPI**: Captures HTTP request errors and performance
- **Celery**: Tracks background task failures and performance
- **SQLAlchemy**: Monitors database query performance
- **Redis**: Tracks cache operation performance

### 4. Test Error Tracking

Create a test error:
```python
# In any endpoint
raise Exception("Test Sentry error tracking")
```

Check your Sentry dashboard to verify the error appears.

## Frontend Setup

### 1. Install Dependencies

Install the Sentry Next.js SDK:
```bash
cd frontend
npm install @sentry/nextjs
```

### 2. Configure Environment Variables

Add to `.env.local` (development) or `.env.production`:
```bash
# Public variable (visible to browser)
NEXT_PUBLIC_SENTRY_DSN=https://your-sentry-dsn@sentry.io/your-project-id
NEXT_PUBLIC_ENVIRONMENT=production

# Server-only variable
SENTRY_DSN=https://your-sentry-dsN@sentry.io/your-project-id
ENVIRONMENT=production

# Optional: Release tracking
VERCEL_GIT_COMMIT_SHA=abc123  # Auto-set by Vercel
VERSION=1.0.0
```

### 3. Configuration Files

The following files are already configured:
- `sentry.client.config.ts` - Client-side error tracking
- `sentry.server.config.ts` - Server-side error tracking
- `instrumentation.ts` - Automatic initialization

### 4. Verify Setup

Build and run the frontend:
```bash
npm run build
npm start
```

Test error tracking by triggering an error in the browser console or creating a test error in a component.

## Features

### Backend Features

**Automatic Error Capture**:
- Unhandled exceptions in API endpoints
- Celery task failures
- Database query errors
- Redis operation errors

**Performance Monitoring**:
- HTTP request duration
- Database query performance
- Celery task duration
- Custom transaction tracking

**Context Enrichment**:
- Request path and method
- User/broker ID (when authenticated)
- Environment (production, staging, etc.)
- Release version (Git commit SHA)
- Custom tags and context

**Error Filtering**:
- Ignores health check endpoints (`/health`, `/`)
- Filters out timeout errors
- Filters out cancellation errors
- Customizable via `before_send_filter()`

### Frontend Features

**Client-Side Tracking**:
- Unhandled JavaScript errors
- Promise rejections
- React component errors
- API request failures

**Server-Side Tracking**:
- SSR errors
- API route errors
- Middleware errors
- Build-time errors

**Session Replay** (Optional):
- Records user sessions when errors occur
- Privacy-focused (masks PII by default)
- Helps reproduce bugs

**Performance Monitoring**:
- Page load times
- Component render duration
- API request duration
- Core Web Vitals

**Error Filtering**:
- Ignores network errors
- Filters canceled requests
- Customizable via `beforeSend()`

## Configuration Options

### Sample Rates

Adjust in `backend/app/core/sentry.py` and frontend configs:

**Backend**:
```python
# Transaction (performance) sampling
'production': 0.1,   # 10% of requests
'staging': 0.5,      # 50% of requests

# Profiling sampling
'production': 0.01,  # 1% of requests
'staging': 0.1,      # 10% of requests
```

**Frontend**:
```typescript
// Transaction sampling
tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0

// Session replay sampling
replaysSessionSampleRate: 0.1,       // 10% of sessions
replaysOnErrorSampleRate: 1.0,       // 100% when errors occur
```

### Filtering Errors

**Backend** (`backend/app/core/sentry.py`):
```python
def before_send_filter(event, hint):
    # Add custom filtering logic
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        # Ignore specific error types
        if exc_type.__name__ in ['TimeoutError', 'CancelledError']:
            return None

    return event
```

**Frontend** (`sentry.client.config.ts`):
```typescript
beforeSend(event, hint) {
  const error = hint.originalException as Error

  // Ignore network errors
  if (error?.message?.includes('Network Error')) {
    return null
  }

  return event
}
```

### Custom Context

**Backend**:
```python
from app.core.sentry import set_user_context, set_context, capture_exception

# Set user context
set_user_context(user_id="broker-123", email="broker@example.com")

# Set custom context
set_context("listing", {"id": "listing-456", "code": "ABC123"})

# Manually capture exception
try:
    risky_operation()
except Exception as e:
    capture_exception(e, listing_id="listing-456")
```

**Frontend**:
```typescript
import * as Sentry from '@sentry/nextjs'

// Set user context
Sentry.setUser({
  id: 'broker-123',
  email: 'broker@example.com',
})

// Set custom context
Sentry.setContext('listing', {
  id: 'listing-456',
  code: 'ABC123',
})

// Manually capture exception
try {
  riskyOperation()
} catch (error) {
  Sentry.captureException(error)
}
```

## Monitoring Best Practices

### 1. Set Up Alerts

Configure Sentry alerts for:
- New error types
- Error spike detection
- Performance degradation
- Failed Celery tasks

### 2. Organize with Releases

Tag deployments with release versions:
```bash
# In CI/CD pipeline
export GIT_COMMIT_SHA=$(git rev-parse HEAD)
export VERSION="1.0.0"
```

Sentry automatically tracks:
- Which errors occurred in which release
- Regression detection
- Deploy notifications

### 3. Use Issue Tracking

Link Sentry to your issue tracker:
- GitHub Issues
- Jira
- Linear
- Asana

### 4. Review Performance

Monitor performance metrics:
- Slow API endpoints (> 1s response time)
- Slow database queries (> 500ms)
- Slow Celery tasks (> 30s)
- High memory usage

### 5. Set Up Dashboards

Create custom Sentry dashboards for:
- Error rate trends
- Performance metrics
- User impact (affected users)
- Geographic distribution

## Troubleshooting

### Errors Not Appearing

**Check**:
1. `SENTRY_DSN` is set correctly
2. Environment is not `development`
3. Error is not being filtered by `before_send`
4. Network connectivity to Sentry

**Test manually**:
```python
# Backend
from app.core.sentry import capture_message
capture_message("Test message", level="info")
```

```typescript
// Frontend
import * as Sentry from '@sentry/nextjs'
Sentry.captureMessage('Test message')
```

### Too Many Events

**Reduce volume**:
1. Lower sample rates
2. Add more filters in `before_send`
3. Ignore specific error types
4. Filter out noisy endpoints

### Missing Context

**Add context**:
```python
# Backend - in middleware or dependencies
from app.core.sentry import set_user_context
set_user_context(user_id=current_user.id, email=current_user.email)
```

## Cost Optimization

Sentry pricing is based on events (errors + transactions):

### Free Tier
- 5,000 errors/month
- 10,000 transactions/month
- 7-day retention

### Optimization Tips

1. **Reduce Transaction Volume**:
   - Lower `tracesSampleRate` (e.g., 0.1 = 10%)
   - Filter out health checks (already done)
   - Sample only slow requests

2. **Reduce Error Volume**:
   - Fix recurring errors quickly
   - Filter expected errors (timeouts, cancellations)
   - Rate limit similar errors

3. **Use Spike Protection**:
   - Enable spike protection in Sentry settings
   - Set max events per minute
   - Auto-reject after threshold

4. **Focus on Production**:
   - Disable Sentry in development
   - Use lower sampling in staging
   - Full sampling only in production

## Security Considerations

### PII (Personally Identifiable Information)

Both backend and frontend are configured with `sendDefaultPii: false`.

**Additional protection**:
```python
# Backend - scrub sensitive data
def before_send_filter(event, hint):
    # Remove sensitive fields
    if 'request' in event:
        if 'headers' in event['request']:
            event['request']['headers'].pop('Authorization', None)

    return event
```

### Data Scrubbing

Sentry automatically scrubs common sensitive fields:
- `password`
- `secret`
- `api_key`
- `token`
- Credit card numbers
- Social security numbers

### Session Replay Privacy

Session replay is configured to:
- Mask all text by default
- Block all media (images, videos)
- Exclude sensitive forms

## Next Steps

1. **Create Sentry Project**: Go to [sentry.io](https://sentry.io) and create a project
2. **Get DSN**: Copy your DSN from project settings
3. **Configure Environments**: Add DSN to `.env.prod` (backend) and `.env.production` (frontend)
4. **Deploy**: Deploy your application with Sentry configured
5. **Test**: Trigger a test error and verify it appears in Sentry
6. **Set Up Alerts**: Configure alerts for critical errors
7. **Monitor**: Check Sentry dashboard regularly

## Resources

- [Sentry Documentation](https://docs.sentry.io/)
- [Sentry Python SDK](https://docs.sentry.io/platforms/python/)
- [Sentry Next.js SDK](https://docs.sentry.io/platforms/javascript/guides/nextjs/)
- [Performance Monitoring](https://docs.sentry.io/product/performance/)
- [Session Replay](https://docs.sentry.io/product/session-replay/)
