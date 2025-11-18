'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { listingsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Upload, File, AlertCircle, Loader2 } from 'lucide-react'

interface Listing {
  id: string
  code: string
  title: string
}

interface Document {
  id: string
  title: string
  document_type: string
  file_size: number
  created_at: string
}

interface DocumentsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  listing: Listing
}

export function DocumentsDialog({
  open,
  onOpenChange,
  listing,
}: DocumentsDialogProps) {
  const queryClient = useQueryClient()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [documentType, setDocumentType] = useState('cim')
  const [error, setError] = useState('')

  // Fetch documents
  const { data, isLoading } = useQuery({
    queryKey: ['documents', listing.id],
    queryFn: () => listingsApi.getDocuments(listing.id),
    enabled: open,
  })

  const documents: Document[] = data?.data?.documents || []

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: () => {
      if (!selectedFile) throw new Error('No file selected')
      return listingsApi.uploadDocument(listing.id, selectedFile, documentType)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', listing.id] })
      setSelectedFile(null)
      setDocumentType('cim')
      setError('')
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Upload failed')
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      // Validate file type
      const validTypes = [
        'application/pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ]
      if (!validTypes.includes(file.type)) {
        setError('Only PDF and DOCX files are supported')
        return
      }

      // Validate file size (10MB max)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB')
        return
      }

      setSelectedFile(file)
      setError('')
    }
  }

  const handleUpload = () => {
    if (!selectedFile) {
      setError('Please select a file')
      return
    }
    uploadMutation.mutate()
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const getDocumentTypeBadge = (type: string) => {
    const variants: Record<string, 'default' | 'secondary' | 'outline'> = {
      cim: 'default',
      teaser: 'secondary',
      financials: 'outline',
    }
    return (
      <Badge variant={variants[type] || 'outline'}>
        {type.toUpperCase()}
      </Badge>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Listing Documents</DialogTitle>
          <DialogDescription>
            {listing.code} - {listing.title}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Upload Section */}
          <div className="border-2 border-dashed rounded-lg p-6 space-y-4">
            <div className="space-y-2">
              <Label>Upload Document</Label>
              <div className="flex gap-4">
                <select
                  value={documentType}
                  onChange={(e) => setDocumentType(e.target.value)}
                  disabled={uploadMutation.isPending}
                  className="px-3 py-2 border rounded-md"
                >
                  <option value="cim">CIM (Confidential Information Memorandum)</option>
                  <option value="teaser">Teaser</option>
                  <option value="financials">Financials</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>

            <div className="space-y-2">
              <input
                type="file"
                onChange={handleFileChange}
                accept=".pdf,.docx"
                disabled={uploadMutation.isPending}
                className="block w-full text-sm text-gray-500
                  file:mr-4 file:py-2 file:px-4
                  file:rounded-md file:border-0
                  file:text-sm file:font-medium
                  file:bg-blue-50 file:text-blue-700
                  hover:file:bg-blue-100
                  disabled:opacity-50"
              />
              <p className="text-xs text-gray-500">
                Supported formats: PDF, DOCX (max 10MB)
              </p>
            </div>

            {selectedFile && (
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                <div className="flex items-center gap-2">
                  <File className="h-4 w-4 text-gray-500" />
                  <span className="text-sm">{selectedFile.name}</span>
                  <span className="text-xs text-gray-500">
                    ({formatFileSize(selectedFile.size)})
                  </span>
                </div>
                <Button
                  onClick={handleUpload}
                  disabled={uploadMutation.isPending}
                  size="sm"
                >
                  {uploadMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Uploading...
                    </>
                  ) : (
                    <>
                      <Upload className="mr-2 h-4 w-4" />
                      Upload
                    </>
                  )}
                </Button>
              </div>
            )}

            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </div>

          {/* Documents List */}
          <div className="space-y-2">
            <Label>Existing Documents</Label>
            {isLoading ? (
              <div className="text-center py-8 text-gray-500">
                Loading documents...
              </div>
            ) : documents.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                No documents uploaded yet
              </div>
            ) : (
              <div className="border rounded-lg divide-y">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="p-4 flex items-center justify-between hover:bg-gray-50"
                  >
                    <div className="flex items-center gap-3">
                      <File className="h-5 w-5 text-gray-400" />
                      <div>
                        <div className="font-medium">{doc.title}</div>
                        <div className="text-sm text-gray-500">
                          {formatFileSize(doc.file_size)} •{' '}
                          {new Date(doc.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {getDocumentTypeBadge(doc.document_type)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
