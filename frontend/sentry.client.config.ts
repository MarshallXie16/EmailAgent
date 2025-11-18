/**
 * Sentry configuration for client-side error tracking.
 *
 * Installation:
 * npm install @sentry/nextjs
 *
 * This file is automatically loaded by Next.js via instrumentation.ts
 */

import * as Sentry from '@sentry/nextjs'

const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN
const ENVIRONMENT = process.env.NEXT_PUBLIC_ENVIRONMENT || 'development'

if (SENTRY_DSN && ENVIRONMENT !== 'development') {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: ENVIRONMENT,

    // Performance monitoring
    tracesSampleRate: ENVIRONMENT === 'production' ? 0.1 : 1.0,

    // Session replay (optional)
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,

    // Integrations
    integrations: [
      new Sentry.BrowserTracing({
        // Enable automatic instrumentation of browser performance
        tracePropagationTargets: [
          'localhost',
          /^https:\/\/yourapp\.com/,
        ],
      }),
      new Sentry.Replay({
        // Privacy settings for session replay
        maskAllText: true,
        blockAllMedia: true,
      }),
    ],

    // Error filtering
    beforeSend(event, hint) {
      // Filter out errors we don't want to track
      const error = hint.originalException as Error

      // Ignore network errors
      if (error?.message?.includes('Network Error')) {
        return null
      }

      // Ignore canceled requests
      if (error?.message?.includes('canceled')) {
        return null
      }

      // Add custom context
      event.tags = {
        ...event.tags,
        service: 'email-agent-frontend',
      }

      return event
    },

    // Don't send PII
    sendDefaultPii: false,

    // Enable debug in non-production
    debug: ENVIRONMENT !== 'production',
  })
}
