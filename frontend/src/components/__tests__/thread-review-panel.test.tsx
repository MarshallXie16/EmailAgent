import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThreadReviewPanel } from '../thread-review-panel'
import { ReviewQueueItem } from '@/types'
import { reviewQueueApi } from '@/lib/api'

// Mock the API
jest.mock('@/lib/api', () => ({
  reviewQueueApi: {
    approve: jest.fn(),
    manualReply: jest.fn(),
    markResolved: jest.fn(),
  },
}))

const mockThread: ReviewQueueItem = {
  id: 'thread-123',
  lead: {
    id: 'lead-123',
    name: 'John Doe',
    email: 'john@example.com',
    type: 'buyer',
  },
  listing: {
    id: 'listing-123',
    code: 'BIZ123',
    title: 'Coffee Shop',
    asking_price: 500000,
  },
  status: 'needs_broker',
  last_inbound_message: {
    id: 1,
    direction: 'inbound',
    from_email: 'john@example.com',
    to_email: 'broker@example.com',
    body_text: 'I am interested in this listing. Can you provide more details?',
    sent_at: '2024-01-17T10:00:00Z',
    sent_by: 'lead',
  },
  proposed_response: 'Thank you for your interest! I would be happy to provide more details.',
  agent_reasoning: {
    why_flagged: 'Standard inquiry',
    confidence: 0.85,
    concerns: [],
    tools_called: ['identify_listing', 'get_listing_summary'],
    confidence_factors: {
      positive: [{ factor: 'Listing identified', weight: 0.3 }],
      negative: [],
    },
  },
  created_at: '2024-01-17T09:00:00Z',
  priority_score: 5.0,
  message_count: 3,
}

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('ThreadReviewPanel', () => {
  const mockOnSuccess = jest.fn()
  const mockOnCancel = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders thread information correctly', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText('John Doe')).toBeInTheDocument()
    expect(screen.getByText('BIZ123')).toBeInTheDocument()
    expect(screen.getByText('Coffee Shop')).toBeInTheDocument()
    expect(screen.getByText('$500,000')).toBeInTheDocument()
  })

  it('displays the last inbound message', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    expect(
      screen.getByText('I am interested in this listing. Can you provide more details?')
    ).toBeInTheDocument()
  })

  it('displays the proposed response', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    expect(
      screen.getByText('Thank you for your interest! I would be happy to provide more details.')
    ).toBeInTheDocument()
  })

  it('shows approve and send button', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText('Approve & Send')).toBeInTheDocument()
  })

  it('shows edit and send button', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText('Edit & Send')).toBeInTheDocument()
  })

  it('shows manual reply button', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText('Manual Reply')).toBeInTheDocument()
  })

  it('calls approve API when approve button is clicked', async () => {
    const mockApprove = reviewQueueApi.approve as jest.Mock
    mockApprove.mockResolvedValue({ data: { status: 'success' } })

    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    const approveButton = screen.getByText('Approve & Send')
    fireEvent.click(approveButton)

    await waitFor(() => {
      expect(mockApprove).toHaveBeenCalledWith('thread-123', undefined)
    })
  })

  it('enables edit mode when edit button is clicked', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    const editButton = screen.getByText('Edit & Send')
    fireEvent.click(editButton)

    expect(screen.getByText('Send Edited Response')).toBeInTheDocument()
    expect(screen.getByText('Cancel')).toBeInTheDocument()
  })

  it('enables manual mode when manual reply is clicked', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    const manualButton = screen.getByText('Manual Reply')
    fireEvent.click(manualButton)

    expect(screen.getByText('Send Manual Reply')).toBeInTheDocument()
    expect(screen.getByText('Your Manual Response')).toBeInTheDocument()
  })

  it('calls onCancel when cancel button is clicked', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    const cancelButton = screen.getAllByRole('button').find((btn) =>
      btn.querySelector('svg')?.classList.contains('lucide-x')
    )

    if (cancelButton) {
      fireEvent.click(cancelButton)
      expect(mockOnCancel).toHaveBeenCalled()
    }
  })

  it('displays agent reasoning in reasoning tab', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    const reasoningTab = screen.getByText('Agent Reasoning')
    fireEvent.click(reasoningTab)

    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('shows mark as resolved button', () => {
    render(
      <ThreadReviewPanel
        thread={mockThread}
        onSuccess={mockOnSuccess}
        onCancel={mockOnCancel}
      />,
      { wrapper: createWrapper() }
    )

    expect(screen.getByText('Mark as Resolved (No Email)')).toBeInTheDocument()
  })
})
