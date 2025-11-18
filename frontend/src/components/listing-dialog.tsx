'use client'

import { useState, useEffect } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { listingsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertCircle } from 'lucide-react'

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
  notes: string | null
}

interface ListingDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  listing?: Listing
  onSuccess?: () => void
}

export function ListingDialog({
  open,
  onOpenChange,
  listing,
  onSuccess,
}: ListingDialogProps) {
  const queryClient = useQueryClient()
  const isEditing = !!listing

  const [formData, setFormData] = useState({
    code: '',
    title: '',
    status: 'active',
    asking_price: '',
    revenue: '',
    sde: '',
    location_region: '',
    confidentiality_level: 'medium',
    short_description: '',
    notes: '',
  })

  const [error, setError] = useState('')

  // Load listing data when editing
  useEffect(() => {
    if (listing) {
      setFormData({
        code: listing.code,
        title: listing.title,
        status: listing.status,
        asking_price: listing.asking_price?.toString() || '',
        revenue: listing.revenue?.toString() || '',
        sde: listing.sde?.toString() || '',
        location_region: listing.location_region || '',
        confidentiality_level: listing.confidentiality_level,
        short_description: listing.short_description || '',
        notes: listing.notes || '',
      })
    } else {
      // Reset form for create
      setFormData({
        code: '',
        title: '',
        status: 'active',
        asking_price: '',
        revenue: '',
        sde: '',
        location_region: '',
        confidentiality_level: 'medium',
        short_description: '',
        notes: '',
      })
    }
    setError('')
  }, [listing, open])

  // Create/Update mutation
  const mutation = useMutation({
    mutationFn: async () => {
      const data = {
        ...formData,
        asking_price: formData.asking_price
          ? parseFloat(formData.asking_price)
          : undefined,
        revenue: formData.revenue ? parseFloat(formData.revenue) : undefined,
        sde: formData.sde ? parseFloat(formData.sde) : undefined,
      }

      if (isEditing) {
        // Remove code from update payload (can't change code)
        const { code, ...updateData } = data
        return listingsApi.updateListing(listing.id, updateData)
      } else {
        return listingsApi.createListing(data as any)
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['listings'] })
      onSuccess?.()
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'An error occurred')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    // Validation
    if (!formData.code.trim()) {
      setError('Listing code is required')
      return
    }
    if (!formData.title.trim()) {
      setError('Title is required')
      return
    }

    mutation.mutate()
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {isEditing ? 'Edit Listing' : 'Create New Listing'}
          </DialogTitle>
          <DialogDescription>
            {isEditing
              ? 'Update the listing details below.'
              : 'Enter the details for the new listing.'}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="code">
                Listing Code <span className="text-red-500">*</span>
              </Label>
              <Input
                id="code"
                value={formData.code}
                onChange={(e) =>
                  setFormData({ ...formData, code: e.target.value })
                }
                placeholder="ABC123"
                disabled={isEditing || mutation.isPending}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="status">Status</Label>
              <select
                id="status"
                value={formData.status}
                onChange={(e) =>
                  setFormData({ ...formData, status: e.target.value })
                }
                disabled={mutation.isPending}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="active">Active</option>
                <option value="sold">Sold</option>
                <option value="archived">Archived</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="title">
              Title <span className="text-red-500">*</span>
            </Label>
            <Input
              id="title"
              value={formData.title}
              onChange={(e) =>
                setFormData({ ...formData, title: e.target.value })
              }
              placeholder="Established Coffee Shop"
              disabled={mutation.isPending}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="location_region">Location</Label>
            <Input
              id="location_region"
              value={formData.location_region}
              onChange={(e) =>
                setFormData({ ...formData, location_region: e.target.value })
              }
              placeholder="New York, NY"
              disabled={mutation.isPending}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="asking_price">Asking Price ($)</Label>
              <Input
                id="asking_price"
                type="number"
                value={formData.asking_price}
                onChange={(e) =>
                  setFormData({ ...formData, asking_price: e.target.value })
                }
                placeholder="500000"
                disabled={mutation.isPending}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="revenue">Revenue ($)</Label>
              <Input
                id="revenue"
                type="number"
                value={formData.revenue}
                onChange={(e) =>
                  setFormData({ ...formData, revenue: e.target.value })
                }
                placeholder="750000"
                disabled={mutation.isPending}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="sde">SDE ($)</Label>
              <Input
                id="sde"
                type="number"
                value={formData.sde}
                onChange={(e) =>
                  setFormData({ ...formData, sde: e.target.value })
                }
                placeholder="150000"
                disabled={mutation.isPending}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="confidentiality_level">Confidentiality Level</Label>
            <select
              id="confidentiality_level"
              value={formData.confidentiality_level}
              onChange={(e) =>
                setFormData({
                  ...formData,
                  confidentiality_level: e.target.value,
                })
              }
              disabled={mutation.isPending}
              className="w-full px-3 py-2 border rounded-md"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="short_description">Short Description</Label>
            <Textarea
              id="short_description"
              value={formData.short_description}
              onChange={(e) =>
                setFormData({ ...formData, short_description: e.target.value })
              }
              placeholder="Brief description of the business..."
              rows={3}
              disabled={mutation.isPending}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Internal Notes</Label>
            <Textarea
              id="notes"
              value={formData.notes}
              onChange={(e) =>
                setFormData({ ...formData, notes: e.target.value })
              }
              placeholder="Private notes for internal use..."
              rows={3}
              disabled={mutation.isPending}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={mutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending
                ? isEditing
                  ? 'Updating...'
                  : 'Creating...'
                : isEditing
                ? 'Update Listing'
                : 'Create Listing'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
