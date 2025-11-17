import { render, screen } from '@testing-library/react'
import { AgentReasoningPanel } from '../agent-reasoning-panel'
import { AgentReasoningDetail } from '@/types'

describe('AgentReasoningPanel', () => {
  const mockReasoning: AgentReasoningDetail = {
    why_flagged: 'Lead asked about proprietary financial details',
    confidence: 0.42,
    concerns: ['Potential confidentiality breach', 'No NDA signed'],
    tools_called: ['get_nda_status', 'identify_listing'],
    confidence_factors: {
      positive: [
        { factor: 'Listing identified', weight: 0.3 },
        { factor: 'Standard inquiry pattern', weight: 0.1 },
      ],
      negative: [
        { factor: 'No NDA signed', weight: -0.4 },
        { factor: 'Insufficient documentation', weight: -0.2 },
      ],
    },
  }

  it('renders the component with reasoning data', () => {
    render(<AgentReasoningPanel reasoning={mockReasoning} />)

    expect(screen.getByText('Agent Reasoning')).toBeInTheDocument()
    expect(screen.getByText(/Low Confidence/)).toBeInTheDocument()
    expect(screen.getByText('42%')).toBeInTheDocument()
  })

  it('displays why flagged section', () => {
    render(<AgentReasoningPanel reasoning={mockReasoning} />)

    expect(
      screen.getByText('Lead asked about proprietary financial details')
    ).toBeInTheDocument()
  })

  it('displays concerns', () => {
    render(<AgentReasoningPanel reasoning={mockReasoning} />)

    expect(
      screen.getByText('Potential confidentiality breach')
    ).toBeInTheDocument()
    expect(screen.getByText('No NDA signed')).toBeInTheDocument()
  })

  it('displays tools called', () => {
    render(<AgentReasoningPanel reasoning={mockReasoning} />)

    expect(screen.getByText('get_nda_status')).toBeInTheDocument()
    expect(screen.getByText('identify_listing')).toBeInTheDocument()
  })

  it('shows high confidence badge for high confidence score', () => {
    const highConfidenceReasoning: AgentReasoningDetail = {
      ...mockReasoning,
      confidence: 0.85,
    }

    render(<AgentReasoningPanel reasoning={highConfidenceReasoning} />)

    expect(screen.getByText(/High Confidence/)).toBeInTheDocument()
    expect(screen.getByText('85%')).toBeInTheDocument()
  })

  it('shows medium confidence badge for medium confidence score', () => {
    const mediumConfidenceReasoning: AgentReasoningDetail = {
      ...mockReasoning,
      confidence: 0.65,
    }

    render(<AgentReasoningPanel reasoning={mediumConfidenceReasoning} />)

    expect(screen.getByText(/Medium Confidence/)).toBeInTheDocument()
    expect(screen.getByText('65%')).toBeInTheDocument()
  })

  it('displays confidence factors correctly', () => {
    render(<AgentReasoningPanel reasoning={mockReasoning} />)

    // Positive factors
    expect(screen.getByText('Listing identified')).toBeInTheDocument()
    expect(screen.getByText('Standard inquiry pattern')).toBeInTheDocument()

    // Negative factors
    expect(screen.getByText('Insufficient documentation')).toBeInTheDocument()
  })
})
