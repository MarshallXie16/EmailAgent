'use client'

import { useQuery } from '@tanstack/react-query'
import { analyticsApi } from '@/lib/api'
import { DashboardLayout } from '@/components/dashboard-layout'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import {
  Mail,
  TrendingUp,
  AlertCircle,
  CheckCircle2,
  FileText,
  Calendar,
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { formatPercentage, formatDate } from '@/lib/utils'
import { useState } from 'react'

const COLORS = {
  answered: '#10b981',
  escalated: '#f59e0b',
  nda_requested: '#3b82f6',
  meeting_booked: '#8b5cf6',
}

export default function DashboardPage() {
  const [period, setPeriod] = useState<'7d' | '30d' | '90d' | 'all'>('7d')

  // Fetch analytics data
  const { data: overview, isLoading: overviewLoading } = useQuery({
    queryKey: ['analytics', 'overview', period],
    queryFn: () => analyticsApi.getOverview(period),
  })

  const { data: trends, isLoading: trendsLoading } = useQuery({
    queryKey: ['analytics', 'trends', period],
    queryFn: () => analyticsApi.getTrends(period),
  })

  const kpis = overview?.data
  const trendsData = trends?.data

  // Transform pie chart data
  const pieData = trendsData
    ? [
        { name: 'Answered', value: trendsData.by_action.answered },
        { name: 'Escalated', value: trendsData.by_action.escalated },
        { name: 'NDA Requested', value: trendsData.by_action.nda_requested },
        { name: 'Meeting Booked', value: trendsData.by_action.meeting_booked },
      ].filter((item) => item.value > 0)
    : []

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="text-gray-500 mt-1">
              Email agent performance overview
            </p>
          </div>

          {/* Period Selector */}
          <Tabs value={period} onValueChange={(v) => setPeriod(v as any)}>
            <TabsList>
              <TabsTrigger value="7d">7 Days</TabsTrigger>
              <TabsTrigger value="30d">30 Days</TabsTrigger>
              <TabsTrigger value="90d">90 Days</TabsTrigger>
              <TabsTrigger value="all">All Time</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Total Emails
              </CardTitle>
              <Mail className="h-4 w-4 text-gray-400" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">
                {overviewLoading ? '...' : kpis?.total_emails || 0}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Processed in {period === 'all' ? 'all time' : `last ${period}`}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Auto-Reply Rate
              </CardTitle>
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">
                {overviewLoading
                  ? '...'
                  : formatPercentage(kpis?.auto_reply_rate || 0)}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Emails sent without review
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Escalation Rate
              </CardTitle>
              <AlertCircle className="h-4 w-4 text-yellow-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-600">
                {overviewLoading
                  ? '...'
                  : formatPercentage(kpis?.escalation_rate || 0)}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Emails flagged for review
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Avg Confidence
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">
                {overviewLoading
                  ? '...'
                  : formatPercentage(kpis?.avg_confidence || 0)}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Average agent confidence
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Daily Email Volume */}
          <Card>
            <CardHeader>
              <CardTitle>Email Volume Over Time</CardTitle>
            </CardHeader>
            <CardContent>
              {trendsLoading ? (
                <div className="h-64 flex items-center justify-center">
                  <p className="text-gray-400">Loading...</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendsData?.daily_counts || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                      dataKey="date"
                      tick={{ fontSize: 12 }}
                      tickFormatter={(value) =>
                        new Date(value).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                        })
                      }
                    />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey="count"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ fill: '#3b82f6', r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Actions Breakdown */}
          <Card>
            <CardHeader>
              <CardTitle>Actions Breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {trendsLoading ? (
                <div className="h-64 flex items-center justify-center">
                  <p className="text-gray-400">Loading...</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) =>
                        `${name} (${(percent * 100).toFixed(0)}%)`
                      }
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={
                            COLORS[
                              entry.name
                                .toLowerCase()
                                .replace(' ', '_') as keyof typeof COLORS
                            ] || '#94a3b8'
                          }
                        />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Top Listings */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle>Top Listings by Email Volume</CardTitle>
            </CardHeader>
            <CardContent>
              {trendsLoading ? (
                <div className="h-64 flex items-center justify-center">
                  <p className="text-gray-400">Loading...</p>
                </div>
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trendsData?.by_listing || []}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="listing_code" tick={{ fontSize: 12 }} />
                    <YAxis tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  )
}
