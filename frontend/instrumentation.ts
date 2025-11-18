/**
 * Next.js instrumentation file for Sentry initialization.
 *
 * This file is automatically loaded by Next.js on both server and client.
 * See: https://nextjs.org/docs/app/building-your-application/optimizing/instrumentation
 */

export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    // Server-side Sentry initialization
    await import('./sentry.server.config')
  }

  if (process.env.NEXT_RUNTIME === 'edge') {
    // Edge runtime Sentry initialization
    await import('./sentry.server.config')
  }
}

export async function onRequestError(
  err: Error,
  request: {
    path: string
    method: string
    headers: Headers
  },
  context: {
    routerKind: 'Pages Router' | 'App Router'
    routePath: string
    routeType: 'render' | 'route' | 'action' | 'middleware'
  }
) {
  // This hook is called whenever an unhandled error occurs in Next.js
  // Sentry automatically captures these errors when initialized
  console.error('Request error:', {
    error: err,
    path: request.path,
    method: request.method,
    routePath: context.routePath,
  })
}
