import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { useRouter } from 'next/navigation'
import LoginPage from '@/app/login/page'
import { useAuth } from '@/contexts/auth-context'

// Mock next/navigation
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
}))

// Mock auth context
jest.mock('@/contexts/auth-context', () => ({
  useAuth: jest.fn(),
}))

describe('LoginPage', () => {
  const mockPush = jest.fn()
  const mockLogin = jest.fn()

  beforeEach(() => {
    jest.clearAllMocks()
    ;(useRouter as jest.Mock).mockReturnValue({
      push: mockPush,
    })
    ;(useAuth as jest.Mock).mockReturnValue({
      login: mockLogin,
    })
  })

  it('renders login form', () => {
    render(<LoginPage />)

    expect(screen.getByText('Email Agent')).toBeInTheDocument()
    expect(screen.getByText('Sign in to your broker dashboard')).toBeInTheDocument()
    expect(screen.getByLabelText('Email')).toBeInTheDocument()
    expect(screen.getByLabelText('Password')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Sign in' })).toBeInTheDocument()
  })

  it('allows user to type email and password', () => {
    render(<LoginPage />)

    const emailInput = screen.getByLabelText('Email') as HTMLInputElement
    const passwordInput = screen.getByLabelText('Password') as HTMLInputElement

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })

    expect(emailInput.value).toBe('test@example.com')
    expect(passwordInput.value).toBe('password123')
  })

  it('calls login function on form submit', async () => {
    mockLogin.mockResolvedValue(undefined)

    render(<LoginPage />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: 'Sign in' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123')
    })
  })

  it('displays error message on login failure', async () => {
    mockLogin.mockRejectedValue(new Error('Invalid credentials'))

    render(<LoginPage />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: 'Sign in' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'wrongpassword' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })

  it('shows loading state during login', async () => {
    mockLogin.mockImplementation(() => new Promise(() => {})) // Never resolves

    render(<LoginPage />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: 'Sign in' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(screen.getByText('Signing in...')).toBeInTheDocument()
      expect(submitButton).toBeDisabled()
    })
  })

  it('disables form inputs during login', async () => {
    mockLogin.mockImplementation(() => new Promise(() => {}))

    render(<LoginPage />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Password')
    const submitButton = screen.getByRole('button', { name: 'Sign in' })

    fireEvent.change(emailInput, { target: { value: 'test@example.com' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    fireEvent.click(submitButton)

    await waitFor(() => {
      expect(emailInput).toBeDisabled()
      expect(passwordInput).toBeDisabled()
    })
  })

  it('requires email and password fields', () => {
    render(<LoginPage />)

    const emailInput = screen.getByLabelText('Email')
    const passwordInput = screen.getByLabelText('Password')

    expect(emailInput).toHaveAttribute('required')
    expect(passwordInput).toHaveAttribute('required')
  })

  it('displays support message', () => {
    render(<LoginPage />)

    expect(
      screen.getByText('For support, contact your system administrator')
    ).toBeInTheDocument()
  })
})
