'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { reviewQueueApi } from '@/lib/api'
import { ReviewQueueItem } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AgentReasoningPanel } from '@/components/agent-reasoning-panel'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { formatDate, formatCurrency } from '@/lib/utils'
import {
  CheckCircle2,
  Edit2,
  Send,
  X,
  AlertTriangle,
  User,
  Bot,
  Mail,
} from 'lucide-react'
import { ResponseEditor } from '@/components/response-editor'

interface ThreadReviewPanelProps {
  thread: ReviewQueueItem
  onSuccess: () => void
  onCancel: () => void
}

export function ThreadReviewPanel({
  thread,
  onSuccess,
  onCancel,
}: ThreadReviewPanelProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedResponse, setEditedResponse] = useState(thread.proposed_response)
  const [manualMode, setManualMode] = useState(false)

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (edits?: string) =>
      reviewQueueApi.approve(thread.id, edits),
    onSuccess: () => {
      onSuccess()
    },
  })

  // Manual reply mutation
  const manualReplyMutation = useMutation({
    mutationFn: (bodyText: string) =>
      reviewQueueApi.manualReply(thread.id, bodyText),
    onSuccess: () => {
      onSuccess()
    },
  })

  // Mark resolved mutation
  const markResolvedMutation = useMutation({
    mutationFn: () => reviewQueueApi.markResolved(thread.id),
    onSuccess: () => {
      onSuccess()
    },
  })

  const handleApprove = () => {
    if (isEditing) {
      approveMutation.mutate(editedResponse)
    } else {
      approveMutation.mutate()
    }
  }

  const handleManualReply = () => {
    if (editedResponse.trim()) {
      manualReplyMutation.mutate(editedResponse)
    }
  }

  const handleEdit = () => {
    setIsEditing(true)
    setManualMode(false)
  }

  const handleManual = () => {
    setManualMode(true)
    setIsEditing(false)
    setEditedResponse('')
  }

  const handleCancelEdit = () => {
    setIsEditing(false)
    setManualMode(false)
    setEditedResponse(thread.proposed_response)
  }

  const isLoading =
    approveMutation.isPending ||
    manualReplyMutation.isPending ||
    markResolvedMutation.isPending

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <div>
            <CardTitle>Review Email Thread</CardTitle>
            <div className="flex items-center gap-2 mt-2">
              <Badge variant="outline">{thread.lead.name}</Badge>
              {thread.listing && (
                <Badge variant="secondary">{thread.listing.code}</Badge>
              )}
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={onCancel}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Thread Info */}
        <div className="bg-gray-50 rounded-lg p-4 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Lead:</span>
            <span className="font-medium">{thread.lead.email}</span>
          </div>
          {thread.listing && (
            <>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Listing:</span>
                <span className="font-medium">{thread.listing.title}</span>
              </div>
              {thread.listing.asking_price && (
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-600">Asking Price:</span>
                  <span className="font-medium">
                    {formatCurrency(thread.listing.asking_price)}
                  </span>
                </div>
              )}
            </>
          )}
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Messages:</span>
            <span className="font-medium">{thread.message_count}</span>
          </div>
        </div>

        {/* Tabs for Conversation and Reasoning */}
        <Tabs defaultValue="conversation" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="conversation">Conversation</TabsTrigger>
            <TabsTrigger value="reasoning">Agent Reasoning</TabsTrigger>
          </TabsList>

          <TabsContent value="conversation" className="space-y-4">
            {/* Last Inbound Message */}
            <div>
              <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <User className="h-4 w-4" />
                Lead's Message
              </h4>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="text-xs text-gray-500 mb-2">
                  {formatDate(thread.last_inbound_message.sent_at)}
                </div>
                <div className="text-sm whitespace-pre-wrap">
                  {thread.last_inbound_message.body_text}
                </div>
              </div>
            </div>

            {/* Proposed Response */}
            <div>
              <h4 className="text-sm font-semibold mb-2 flex items-center gap-2">
                <Bot className="h-4 w-4" />
                {manualMode ? 'Your Manual Response' : 'Agent's Proposed Response'}
              </h4>
              <ResponseEditor
                value={editedResponse}
                onChange={setEditedResponse}
                readOnly={!isEditing && !manualMode}
                placeholder={
                  manualMode
                    ? 'Type your custom response here...'
                    : 'Agent response'
                }
              />
            </div>
          </TabsContent>

          <TabsContent value="reasoning">
            <AgentReasoningPanel reasoning={thread.agent_reasoning} />
          </TabsContent>
        </Tabs>

        {/* Action Buttons */}
        <div className="border-t pt-4 space-y-3">
          {/* Primary Actions */}
          {!isEditing && !manualMode ? (
            <div className="grid grid-cols-3 gap-3">
              <Button
                onClick={handleApprove}
                disabled={isLoading}
                className="w-full"
                variant="default"
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Approve & Send
              </Button>
              <Button
                onClick={handleEdit}
                disabled={isLoading}
                className="w-full"
                variant="outline"
              >
                <Edit2 className="h-4 w-4 mr-2" />
                Edit & Send
              </Button>
              <Button
                onClick={handleManual}
                disabled={isLoading}
                className="w-full"
                variant="secondary"
              >
                <Mail className="h-4 w-4 mr-2" />
                Manual Reply
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-3">
              <Button
                onClick={manualMode ? handleManualReply : handleApprove}
                disabled={isLoading || !editedResponse.trim()}
                className="w-full"
                variant="default"
              >
                <Send className="h-4 w-4 mr-2" />
                {manualMode ? 'Send Manual Reply' : 'Send Edited Response'}
              </Button>
              <Button
                onClick={handleCancelEdit}
                disabled={isLoading}
                className="w-full"
                variant="outline"
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            </div>
          )}

          {/* Secondary Actions */}
          <div className="flex justify-between">
            <Button
              onClick={() => markResolvedMutation.mutate()}
              disabled={isLoading}
              variant="ghost"
              size="sm"
              className="text-gray-600"
            >
              Mark as Resolved (No Email)
            </Button>
          </div>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="text-sm text-center text-gray-500 py-2">
            Processing...
          </div>
        )}

        {/* Error State */}
        {(approveMutation.isError ||
          manualReplyMutation.isError ||
          markResolvedMutation.isError) && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-red-800">
              <div className="font-semibold">Error sending email</div>
              <div className="mt-1">
                {approveMutation.error?.message ||
                  manualReplyMutation.error?.message ||
                  markResolvedMutation.error?.message ||
                  'An error occurred. Please try again.'}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
