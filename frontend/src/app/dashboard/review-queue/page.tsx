'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { reviewQueueApi } from '@/lib/api'
import { DashboardLayout } from '@/components/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ReviewQueueItem } from '@/types'
import { formatDate, formatCurrency } from '@/lib/utils'
import { AlertCircle, CheckCircle2, Edit, Send, X } from 'lucide-react'
import { ThreadReviewPanel } from '@/components/thread-review-panel'

function getPriorityBadge(priority: number) {
  if (priority >= 7) {
    return (
      <Badge variant="destructive" className="font-semibold">
        High Priority
      </Badge>
    )
  } else if (priority >= 4) {
    return (
      <Badge variant="warning" className="font-semibold">
        Medium Priority
      </Badge>
    )
  }
  return (
    <Badge variant="secondary" className="font-semibold">
      Low Priority
    </Badge>
  )
}

export default function ReviewQueuePage() {
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const queryClient = useQueryClient()

  // Fetch review queue
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['review-queue'],
    queryFn: () => reviewQueueApi.getQueue(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const threads = data?.data.threads || []
  const selectedThread = threads.find((t) => t.id === selectedThreadId)

  // Handle thread selection
  const handleSelectThread = (threadId: string) => {
    setSelectedThreadId(threadId)
  }

  // Handle actions success
  const handleActionSuccess = () => {
    // Refetch the queue
    refetch()
    // Clear selection
    setSelectedThreadId(null)
    // Invalidate analytics to update metrics
    queryClient.invalidateQueries({ queryKey: ['analytics'] })
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Review Queue</h1>
            <p className="text-gray-500 mt-1">
              Review and approve emails flagged by your agent
            </p>
          </div>

          {!isLoading && (
            <Badge variant={threads.length > 0 ? 'warning' : 'success'} className="text-lg px-4 py-2">
              {threads.length} {threads.length === 1 ? 'email' : 'emails'} pending
            </Badge>
          )}
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Queue List - Left Side (2 columns on large screens) */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle>
                  Pending Reviews
                  {!isLoading && threads.length > 0 && (
                    <span className="text-sm font-normal text-gray-500 ml-2">
                      (sorted by priority)
                    </span>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="py-12 text-center">
                    <p className="text-gray-400">Loading...</p>
                  </div>
                ) : threads.length === 0 ? (
                  <div className="py-12 text-center">
                    <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
                    <p className="text-gray-600 font-medium">All caught up!</p>
                    <p className="text-gray-400 text-sm mt-1">
                      No emails need review at the moment
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[calc(100vh-300px)] overflow-y-auto">
                    {threads.map((thread) => (
                      <div
                        key={thread.id}
                        onClick={() => handleSelectThread(thread.id)}
                        className={`border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md ${
                          selectedThreadId === thread.id
                            ? 'border-blue-500 bg-blue-50 shadow-md'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        {/* Header */}
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex-1">
                            <div className="font-semibold text-sm">
                              {thread.lead.name}
                            </div>
                            <div className="text-xs text-gray-500">
                              {thread.lead.email}
                            </div>
                          </div>
                          {getPriorityBadge(thread.priority_score)}
                        </div>

                        {/* Listing */}
                        {thread.listing && (
                          <div className="mb-2">
                            <Badge variant="outline" className="text-xs">
                              {thread.listing.code}
                            </Badge>
                            <span className="text-xs text-gray-600 ml-2">
                              {thread.listing.title}
                            </span>
                          </div>
                        )}

                        {/* Last Message Preview */}
                        <div className="text-xs text-gray-600 mb-2 line-clamp-2">
                          {thread.last_inbound_message.body_text}
                        </div>

                        {/* Footer */}
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-gray-400">
                            {formatDate(thread.last_inbound_message.sent_at)}
                          </span>
                          <div className="flex items-center gap-1">
                            <AlertCircle className="h-3 w-3 text-yellow-600" />
                            <span className="text-yellow-700 font-medium">
                              {(thread.agent_reasoning.confidence * 100).toFixed(0)}%
                              confidence
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Thread Detail - Right Side (3 columns on large screens) */}
          <div className="lg:col-span-3">
            {selectedThread ? (
              <ThreadReviewPanel
                thread={selectedThread}
                onSuccess={handleActionSuccess}
                onCancel={() => setSelectedThreadId(null)}
              />
            ) : (
              <Card className="h-full">
                <CardContent className="flex items-center justify-center h-[calc(100vh-300px)]">
                  <div className="text-center text-gray-400">
                    <AlertCircle className="h-16 w-16 mx-auto mb-4 opacity-50" />
                    <p className="text-lg font-medium">Select an email to review</p>
                    <p className="text-sm mt-1">
                      Choose an email from the left to see details and take action
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}
