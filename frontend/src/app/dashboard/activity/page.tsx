'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/lib/api'
import { DashboardLayout } from '@/components/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatDate } from '@/lib/utils'
import { ChevronLeft, ChevronRight, Download } from 'lucide-react'
import { EmailActivityItem } from '@/types'

const ITEMS_PER_PAGE = 50

function getStatusBadge(status: string) {
  if (status === 'sent') {
    return <Badge variant="success">Sent</Badge>
  }
  return <Badge variant="secondary">Draft</Badge>
}

function getSentByBadge(sentBy: string) {
  if (sentBy === 'agent') {
    return <Badge variant="default">Agent</Badge>
  } else if (sentBy === 'broker') {
    return <Badge variant="secondary">Broker</Badge>
  }
  return <Badge variant="outline">Lead</Badge>
}

function getConfidenceBadge(confidence?: number) {
  if (!confidence) return <span className="text-gray-400">-</span>

  const variant =
    confidence >= 0.7
      ? 'success'
      : confidence >= 0.5
      ? 'warning'
      : 'destructive'

  return <Badge variant={variant}>{(confidence * 100).toFixed(0)}%</Badge>
}

function getActionBadge(action?: string) {
  if (!action) return <span className="text-gray-400">-</span>

  const variants: Record<string, any> = {
    answer: 'success',
    escalate: 'destructive',
    ask_nda: 'secondary',
    book_meeting: 'default',
  }

  return (
    <Badge variant={variants[action] || 'outline'}>
      {action.replace('_', ' ').toUpperCase()}
    </Badge>
  )
}

export default function EmailActivityPage() {
  const [page, setPage] = useState(0)
  const [filters, setFilters] = useState({
    start_date: '',
    end_date: '',
    listing_id: '',
    status: '',
  })

  // Fetch email activity
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'emails', page, filters],
    queryFn: () =>
      analyticsApi.getEmails({
        ...filters,
        skip: page * ITEMS_PER_PAGE,
        limit: ITEMS_PER_PAGE,
      }),
  })

  const emails = data?.data.emails || []
  const total = data?.data.total || 0
  const totalPages = Math.ceil(total / ITEMS_PER_PAGE)

  const handleExport = () => {
    // TODO: Implement CSV export
    alert('CSV export will be implemented')
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Email Activity Log</h1>
            <p className="text-gray-500 mt-1">
              View all email interactions handled by your agent
            </p>
          </div>

          <Button onClick={handleExport} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Export CSV
          </Button>
        </div>

        {/* Activity Table */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="py-12 text-center">
                <p className="text-gray-400">Loading...</p>
              </div>
            ) : emails.length === 0 ? (
              <div className="py-12 text-center">
                <p className="text-gray-400">No email activity found</p>
              </div>
            ) : (
              <>
                <div className="border rounded-lg">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Lead</TableHead>
                        <TableHead>Listing</TableHead>
                        <TableHead>Subject</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Sent By</TableHead>
                        <TableHead>Confidence</TableHead>
                        <TableHead>Action</TableHead>
                        <TableHead>Tools</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {emails.map((email: EmailActivityItem) => (
                        <TableRow key={email.id} className="hover:bg-gray-50">
                          <TableCell className="text-sm">
                            {formatDate(email.sent_at)}
                          </TableCell>
                          <TableCell>
                            <div>
                              <div className="font-medium text-sm">
                                {email.lead_name}
                              </div>
                              <div className="text-xs text-gray-500">
                                {email.lead_email}
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            {email.listing_code ? (
                              <div>
                                <div className="font-medium text-sm">
                                  {email.listing_code}
                                </div>
                                <div className="text-xs text-gray-500 max-w-[150px] truncate">
                                  {email.listing_title}
                                </div>
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </TableCell>
                          <TableCell className="max-w-[200px]">
                            <div className="truncate text-sm">
                              {email.subject}
                            </div>
                          </TableCell>
                          <TableCell>{getStatusBadge(email.status)}</TableCell>
                          <TableCell>{getSentByBadge(email.sent_by)}</TableCell>
                          <TableCell>
                            {getConfidenceBadge(email.confidence)}
                          </TableCell>
                          <TableCell>
                            {getActionBadge(email.final_action)}
                          </TableCell>
                          <TableCell>
                            {email.tools_called && email.tools_called.length > 0 ? (
                              <div className="flex gap-1 flex-wrap max-w-[150px]">
                                {email.tools_called.slice(0, 2).map((tool, idx) => (
                                  <Badge key={idx} variant="outline" className="text-xs">
                                    {tool}
                                  </Badge>
                                ))}
                                {email.tools_called.length > 2 && (
                                  <Badge variant="outline" className="text-xs">
                                    +{email.tools_called.length - 2}
                                  </Badge>
                                )}
                              </div>
                            ) : (
                              <span className="text-gray-400">-</span>
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>

                {/* Pagination */}
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-gray-500">
                    Showing {page * ITEMS_PER_PAGE + 1} to{' '}
                    {Math.min((page + 1) * ITEMS_PER_PAGE, total)} of {total}{' '}
                    emails
                  </div>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(0, p - 1))}
                      disabled={page === 0}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </Button>
                    <div className="text-sm text-gray-600">
                      Page {page + 1} of {totalPages}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => p + 1)}
                      disabled={page >= totalPages - 1}
                    >
                      Next
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  )
}
