import { renderHook, act, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import { AuthProvider, useAuth } from '../auth-context'
import { authApi } from '@/lib/api'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock API
jest.mock('@/lib/api', () => ({
  authApi: {
    login: jest.fn(),
    getProfile: jest.fn(),
    logout: jest.fn(),
  },
}))

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {}

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString()
    },
    removeItem: (key: string) => {
      delete store[key]
    },
    clear: () => {
      store = {}
    },
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
})

describe('AuthContext', () => {
  const mockPush = jest.fn()
  const mockBroker = {
    id: '1',
    email: 'test@example.com',
    name: 'Test Broker',
    timezone: 'America/New_York',
  }

  beforeEach(() => {
    jest.clearAllMocks()
    localStorageMock.clear()
    ;(useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
  })

  it('provides auth context values', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current).toHaveProperty('user')
    expect(result.current).toHaveProperty('loading')
    expect(result.current).toHaveProperty('login')
    expect(result.current).toHaveProperty('logout')
    expect(result.current).toHaveProperty('isAuthenticated')
  })

  it('initializes with loading state', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    expect(result.current.loading).toBe(true)
    expect(result.current.user).toBe(null)
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('checks authentication on mount if token exists', async () => {
    localStorageMock.setItem('access_token', 'test-token')
    ;(authApi.getProfile as jest.Mock).mockResolvedValue({ data: mockBroker })

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
      expect(result.current.user).toEqual(mockBroker)
      expect(result.current.isAuthenticated).toBe(true)
    })

    expect(authApi.getProfile).toHaveBeenCalled()
  })

  it('does not check authentication if no token exists', async () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(authApi.getProfile).not.toHaveBeenCalled()
    expect(result.current.user).toBe(null)
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('logs in successfully', async () => {
    ;(authApi.login as jest.Mock).mockResolvedValue({
      data: {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
      },
    })
    ;(authApi.getProfile as jest.Mock).mockResolvedValue({ data: mockBroker })

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await act(async () => {
      await result.current.login('test@example.com', 'password123')
    })

    expect(authApi.login).toHaveBeenCalledWith('test@example.com', 'password123')
    expect(localStorageMock.getItem('access_token')).toBe('new-access-token')
    expect(localStorageMock.getItem('refresh_token')).toBe('new-refresh-token')
    expect(result.current.user).toEqual(mockBroker)
    expect(result.current.isAuthenticated).toBe(true)
    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('handles login failure', async () => {
    ;(authApi.login as jest.Mock).mockRejectedValue({
      response: {
        data: {
          detail: 'Invalid credentials',
        },
      },
    })

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    await expect(
      act(async () => {
        await result.current.login('test@example.com', 'wrongpassword')
      })
    ).rejects.toThrow('Invalid credentials')

    expect(result.current.user).toBe(null)
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('logs out successfully', async () => {
    localStorageMock.setItem('access_token', 'test-token')
    localStorageMock.setItem('refresh_token', 'test-refresh-token')

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    act(() => {
      result.current.logout()
    })

    expect(localStorageMock.getItem('access_token')).toBe(null)
    expect(localStorageMock.getItem('refresh_token')).toBe(null)
    expect(result.current.user).toBe(null)
    expect(result.current.isAuthenticated).toBe(false)
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('clears tokens on profile fetch failure', async () => {
    localStorageMock.setItem('access_token', 'invalid-token')
    ;(authApi.getProfile as jest.Mock).mockRejectedValue(new Error('Unauthorized'))

    const wrapper = ({ children }: { children: React.ReactNode }) => (
      <AuthProvider>{children}</AuthProvider>
    )

    const { result } = renderHook(() => useAuth(), { wrapper })

    await waitFor(() => {
      expect(result.current.loading).toBe(false)
    })

    expect(localStorageMock.getItem('access_token')).toBe(null)
    expect(localStorageMock.getItem('refresh_token')).toBe(null)
    expect(result.current.user).toBe(null)
    expect(result.current.isAuthenticated).toBe(false)
  })

  it('throws error when useAuth is used outside AuthProvider', () => {
    // Suppress console.error for this test
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {})

    expect(() => {
      renderHook(() => useAuth())
    }).toThrow('useAuth must be used within an AuthProvider')

    consoleError.mockRestore()
  })
})
