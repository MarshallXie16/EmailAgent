'use client'

import { cn } from '@/lib/utils'
import { Textarea } from '@/components/ui/textarea'

interface ResponseEditorProps {
  value: string
  onChange: (value: string) => void
  readOnly?: boolean
  placeholder?: string
  className?: string
}

export function ResponseEditor({
  value,
  onChange,
  readOnly = false,
  placeholder = 'Enter your response...',
  className,
}: ResponseEditorProps) {
  return (
    <div
      className={cn(
        'border rounded-lg overflow-hidden',
        readOnly ? 'bg-gray-50 border-gray-200' : 'bg-white border-gray-300',
        className
      )}
    >
      <Textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        readOnly={readOnly}
        placeholder={placeholder}
        className={cn(
          'min-h-[200px] resize-none border-0 focus-visible:ring-0 font-mono text-sm',
          readOnly && 'bg-gray-50 cursor-default'
        )}
      />
      <div className="bg-gray-100 border-t px-3 py-2 text-xs text-gray-500 flex items-center justify-between">
        <div>
          {value.length} characters • ~{Math.ceil(value.split(/\s+/).length)} words
        </div>
        {readOnly && <div className="text-gray-400">Read-only</div>}
      </div>
    </div>
  )
}
