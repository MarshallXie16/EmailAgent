'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listingsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Plus, Search, Edit, Trash2, FileText } from 'lucide-react'
import { ListingDialog } from '@/components/listing-dialog'
import { DocumentsDialog } from '@/components/documents-dialog'

interface Listing {
  id: string
  code: string
  title: string
  status: string
  asking_price: number | null
  revenue: number | null
  sde: number | null
  location_region: string | null
  confidentiality_level: string
  short_description: string | null
  created_at: string
}

export default function ListingsPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [editingListing, setEditingListing] = useState<Listing | null>(null)
  const [deletingListing, setDeletingListing] = useState<Listing | null>(null)
  const [documentsListing, setDocumentsListing] = useState<Listing | null>(null)

  const queryClient = useQueryClient()

  // Fetch listings
  const { data, isLoading, refetch } = useQuery({
    queryKey: ['listings', statusFilter, search],
    queryFn: () =>
      listingsApi.getListings({
        status: statusFilter || undefined,
        search: search || undefined,
        limit: 100,
      }),
  })

  const listings = data?.data?.listings || []
  const total = data?.data?.total || 0

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: string) => listingsApi.deleteListing(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] })
      setDeletingListing(null)
    },
  })

  const formatCurrency = (amount: number | null) => {
    if (amount === null) return 'N/A'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(amount)
  }

  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
      active: 'default',
      sold: 'secondary',
      archived: 'outline',
    }
    return (
      <Badge variant={variants[status] || 'default'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    )
  }

  const getConfidentialityBadge = (level: string) => {
    const colors: Record<string, string> = {
      low: 'bg-green-100 text-green-800',
      medium: 'bg-yellow-100 text-yellow-800',
      high: 'bg-red-100 text-red-800',
    }
    return (
      <span
        className={`px-2 py-1 rounded text-xs font-medium ${
          colors[level] || 'bg-gray-100 text-gray-800'
        }`}
      >
        {level.charAt(0).toUpperCase() + level.slice(1)}
      </span>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Listings</h1>
          <p className="text-gray-500">Manage your business listings</p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Listing
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search by code, title, or description..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border rounded-md bg-white"
        >
          <option value="">All Statuses</option>
          <option value="active">Active</option>
          <option value="sold">Sold</option>
          <option value="archived">Archived</option>
        </select>
      </div>

      {/* Table */}
      <div className="border rounded-lg bg-white">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading...</div>
        ) : listings.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No listings found. Create your first listing to get started!
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Code</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Location</TableHead>
                <TableHead>Asking Price</TableHead>
                <TableHead>Revenue</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Confidentiality</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {listings.map((listing: Listing) => (
                <TableRow key={listing.id}>
                  <TableCell className="font-mono font-medium">
                    {listing.code}
                  </TableCell>
                  <TableCell>
                    <div>
                      <div className="font-medium">{listing.title}</div>
                      {listing.short_description && (
                        <div className="text-sm text-gray-500 truncate max-w-xs">
                          {listing.short_description}
                        </div>
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{listing.location_region || 'N/A'}</TableCell>
                  <TableCell>{formatCurrency(listing.asking_price)}</TableCell>
                  <TableCell>{formatCurrency(listing.revenue)}</TableCell>
                  <TableCell>{getStatusBadge(listing.status)}</TableCell>
                  <TableCell>
                    {getConfidentialityBadge(listing.confidentiality_level)}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDocumentsListing(listing)}
                      >
                        <FileText className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setEditingListing(listing)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeletingListing(listing)}
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>

      <div className="text-sm text-gray-500">
        Showing {listings.length} of {total} listings
      </div>

      {/* Create Dialog */}
      <ListingDialog
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
        onSuccess={() => {
          setIsCreateOpen(false)
          refetch()
        }}
      />

      {/* Edit Dialog */}
      {editingListing && (
        <ListingDialog
          open={!!editingListing}
          onOpenChange={(open) => !open && setEditingListing(null)}
          listing={editingListing}
          onSuccess={() => {
            setEditingListing(null)
            refetch()
          }}
        />
      )}

      {/* Delete Confirmation */}
      <Dialog
        open={!!deletingListing}
        onOpenChange={(open) => !open && setDeletingListing(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Listing</DialogTitle>
            <DialogDescription>
              Are you sure you want to archive "{deletingListing?.title}"? This will
              set its status to archived.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeletingListing(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deletingListing && deleteMutation.mutate(deletingListing.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Archiving...' : 'Archive'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Documents Dialog */}
      {documentsListing && (
        <DocumentsDialog
          open={!!documentsListing}
          onOpenChange={(open) => !open && setDocumentsListing(null)}
          listing={documentsListing}
        />
      )}
    </div>
  )
}
