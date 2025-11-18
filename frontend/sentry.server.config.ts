/**
 * Sentry configuration for server-side error tracking.
 *
 * Installation:
 * npm install @sentry/nextjs
 *
 * This file is automatically loaded by Next.js via instrumentation.ts
 */

import * as Sentry from '@sentry/nextjs'

const SENTRY_DSN = process.env.SENTRY_DSN
const ENVIRONMENT = process.env.ENVIRONMENT || 'development'

if (SENTRY_DSN && ENVIRONMENT !== 'development') {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: ENVIRONMENT,

    // Performance monitoring
    tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,

    // Error filtering
    beforeSend(event, hint) {
      // Filter out errors we don't want to track
      const error = hint.originalException as Error

      // Ignore expected errors
      const ignoredErrors = [
        'ECONNREFUSED',
        'ETIMEDOUT',
        'ENOTFOUND',
      ]

      if (ignoredErrors.some(msg => error?.message?.includes(msg))) {
        return null
      }

      // Add custom context
      event.tags = {
        ...event.tags,
        service: 'email-agent-frontend-ssr',
      }

      return event
    },

    // Don't send PII
    sendDefaultPii: false,

    // Enable debug in non-production
    debug: ENVIRONMENT !== 'production',

    // Release tracking
    release: process.env.VERCEL_GIT_COMMIT_SHA || process.env.VERSION,
  })
}
