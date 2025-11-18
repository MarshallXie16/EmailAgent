import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import ListingsPage from '../page'
import { listingsApi } from '@/lib/api'

// Mock API
jest.mock('@/lib/api', () => ({
  listingsApi: {
    getListings: jest.fn(),
    deleteListing: jest.fn(),
  },
}))

// Mock components
jest.mock('@/components/listing-dialog', () => ({
  ListingDialog: ({ open, onOpenChange }: any) =>
    open ? <div data-testid="listing-dialog">Listing Dialog</div> : null,
}))

jest.mock('@/components/documents-dialog', () => ({
  DocumentsDialog: ({ open, onOpenChange }: any) =>
    open ? <div data-testid="documents-dialog">Documents Dialog</div> : null,
}))

const mockListings = [
  {
    id: '1',
    code: 'ABC123',
    title: 'Coffee Shop',
    status: 'active',
    asking_price: 500000,
    revenue: 750000,
    sde: 150000,
    location_region: 'New York, NY',
    confidentiality_level: 'high',
    short_description: 'Established coffee shop',
    created_at: '2024-01-01T00:00:00Z',
  },
  {
    id: '2',
    code: 'XYZ789',
    title: 'Restaurant',
    status: 'active',
    asking_price: 800000,
    revenue: 1200000,
    sde: 250000,
    location_region: 'Los Angeles, CA',
    confidentiality_level: 'medium',
    short_description: 'Popular Italian restaurant',
    created_at: '2024-01-02T00:00:00Z',
  },
]

describe('ListingsPage', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    jest.clearAllMocks()
  })

  const renderPage = () => {
    return render(
      <QueryClientProvider client={queryClient}>
        <ListingsPage />
      </QueryClientProvider>
    )
  }

  it('renders listings page header', () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: [], total: 0 },
    })

    renderPage()

    expect(screen.getByText('Listings')).toBeInTheDocument()
    expect(
      screen.getByText('Manage your business listings')
    ).toBeInTheDocument()
  })

  it('displays loading state', () => {
    ;(listingsApi.getListings as jest.Mock).mockImplementation(
      () => new Promise(() => {})
    )

    renderPage()

    expect(screen.getByText('Loading...')).toBeInTheDocument()
  })

  it('displays empty state when no listings', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: [], total: 0 },
    })

    renderPage()

    await waitFor(() => {
      expect(
        screen.getByText(/No listings found/i)
      ).toBeInTheDocument()
    })
  })

  it('displays listings table', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: mockListings, total: 2 },
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('ABC123')).toBeInTheDocument()
      expect(screen.getByText('Coffee Shop')).toBeInTheDocument()
      expect(screen.getByText('XYZ789')).toBeInTheDocument()
      expect(screen.getByText('Restaurant')).toBeInTheDocument()
    })
  })

  it('opens create dialog when clicking New Listing button', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: [], total: 0 },
    })

    renderPage()

    const newButton = screen.getByRole('button', { name: /New Listing/i })
    fireEvent.click(newButton)

    await waitFor(() => {
      expect(screen.getByTestId('listing-dialog')).toBeInTheDocument()
    })
  })

  it('filters listings by search', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: mockListings, total: 2 },
    })

    renderPage()

    const searchInput = screen.getByPlaceholderText(/Search by code/i)
    fireEvent.change(searchInput, { target: { value: 'Coffee' } })

    await waitFor(() => {
      expect(listingsApi.getListings).toHaveBeenCalledWith(
        expect.objectContaining({
          search: 'Coffee',
        })
      )
    })
  })

  it('filters listings by status', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: mockListings, total: 2 },
    })

    renderPage()

    const statusSelect = screen.getByRole('combobox')
    fireEvent.change(statusSelect, { target: { value: 'active' } })

    await waitFor(() => {
      expect(listingsApi.getListings).toHaveBeenCalledWith(
        expect.objectContaining({
          status: 'active',
        })
      )
    })
  })

  it('displays formatted currency values', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: [mockListings[0]], total: 1 },
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('$500,000')).toBeInTheDocument()
      expect(screen.getByText('$750,000')).toBeInTheDocument()
    })
  })

  it('displays status badges', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: [mockListings[0]], total: 1 },
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument()
    })
  })

  it('displays confidentiality level badges', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: [mockListings[0]], total: 1 },
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('High')).toBeInTheDocument()
    })
  })

  it('displays total count', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: mockListings, total: 2 },
    })

    renderPage()

    await waitFor(() => {
      expect(screen.getByText('Showing 2 of 2 listings')).toBeInTheDocument()
    })
  })

  it('opens delete confirmation dialog', async () => {
    ;(listingsApi.getListings as jest.Mock).mockResolvedValue({
      data: { listings: [mockListings[0]], total: 1 },
    })

    renderPage()

    await waitFor(() => {
      const deleteButtons = screen.getAllByRole('button')
      const deleteButton = deleteButtons.find((btn) =>
        btn.querySelector('[class*="Trash"]')
      )
      if (deleteButton) fireEvent.click(deleteButton)
    })

    await waitFor(() => {
      expect(screen.getByText('Delete Listing')).toBeInTheDocument()
      expect(
        screen.getByText(/Are you sure you want to archive/)
      ).toBeInTheDocument()
    })
  })
})
