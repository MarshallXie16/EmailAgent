import { render, screen, fireEvent } from '@testing-library/react'
import { ResponseEditor } from '../response-editor'

describe('ResponseEditor', () => {
  it('renders with initial value', () => {
    const mockOnChange = jest.fn()
    render(
      <ResponseEditor
        value="Test response"
        onChange={mockOnChange}
      />
    )

    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveValue('Test response')
  })

  it('calls onChange when text is typed', () => {
    const mockOnChange = jest.fn()
    render(
      <ResponseEditor
        value=""
        onChange={mockOnChange}
      />
    )

    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'New text' } })

    expect(mockOnChange).toHaveBeenCalledWith('New text')
  })

  it('displays character count', () => {
    const mockOnChange = jest.fn()
    render(
      <ResponseEditor
        value="Hello World"
        onChange={mockOnChange}
      />
    )

    expect(screen.getByText(/11 characters/)).toBeInTheDocument()
  })

  it('displays word count', () => {
    const mockOnChange = jest.fn()
    render(
      <ResponseEditor
        value="Hello World Test"
        onChange={mockOnChange}
      />
    )

    expect(screen.getByText(/~3 words/)).toBeInTheDocument()
  })

  it('is read-only when readOnly prop is true', () => {
    const mockOnChange = jest.fn()
    render(
      <ResponseEditor
        value="Test"
        onChange={mockOnChange}
        readOnly={true}
      />
    )

    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveAttribute('readonly')
    expect(screen.getByText('Read-only')).toBeInTheDocument()
  })

  it('shows placeholder when value is empty', () => {
    const mockOnChange = jest.fn()
    render(
      <ResponseEditor
        value=""
        onChange={mockOnChange}
        placeholder="Enter your response..."
      />
    )

    const textarea = screen.getByRole('textbox')
    expect(textarea).toHaveAttribute('placeholder', 'Enter your response...')
  })

  it('applies custom className', () => {
    const mockOnChange = jest.fn()
    const { container } = render(
      <ResponseEditor
        value="Test"
        onChange={mockOnChange}
        className="custom-class"
      />
    )

    const wrapper = container.querySelector('.custom-class')
    expect(wrapper).toBeInTheDocument()
  })

  it('does not call onChange when read-only', () => {
    const mockOnChange = jest.fn()
    render(
      <ResponseEditor
        value="Test"
        onChange={mockOnChange}
        readOnly={true}
      />
    )

    const textarea = screen.getByRole('textbox')
    fireEvent.change(textarea, { target: { value: 'New text' } })

    // onChange should not be called for read-only textarea
    expect(mockOnChange).not.toHaveBeenCalled()
  })
})
