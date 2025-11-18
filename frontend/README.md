# Email Agent Dashboard Frontend

Next.js 14 dashboard for the Email Agent system - an AI-powered email assistant for business brokers.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **Data Fetching**: TanStack Query (React Query)
- **HTTP Client**: Axios
- **Charts**: Recharts
- **Icons**: Lucide React
- **Testing**: Jest + React Testing Library

## Features Implemented

### ✅ EA-DASH-004: Analytics Dashboard
**Main dashboard landing page** (`/dashboard`)

**Features**:
- KPI cards showing:
  - Total emails processed
  - Auto-reply rate
  - Escalation rate
  - Average confidence score
- Period selector (7d, 30d, 90d, all time)
- Interactive charts:
  - Line chart: Email volume over time
  - Pie chart: Actions breakdown (answered, escalated, NDA requested, meeting booked)
  - Bar chart: Top listings by email volume
- Real-time data fetching with automatic refresh
- Responsive design for mobile/tablet/desktop

**API Integration**:
- `GET /api/v1/analytics/overview?period={period}`
- `GET /api/v1/analytics/trends?period={period}`

---

### ✅ EA-DASH-003: Agent Reasoning Display
**Reusable component** (`<AgentReasoningPanel>`)

**Features**:
- Expandable accordion showing:
  - Why agent flagged for review
  - Confidence factors breakdown (positive/negative)
  - Concerns identified
  - Tools called by agent
- Confidence score visualization with color coding:
  - Green (>70%): High confidence
  - Yellow (50-70%): Medium confidence
  - Red (<50%): Low confidence
- Progress bar showing overall confidence
- Syntax-highlighted JSON for tool inputs/outputs

**Usage**:
```tsx
import { AgentReasoningPanel } from '@/components/agent-reasoning-panel'

<AgentReasoningPanel reasoning={agentReasoning} />
```

---

### ✅ EA-DASH-001: Email Activity Log
**Email activity table** (`/dashboard/activity`)

**Features**:
- Paginated table (50 emails per page)
- Columns:
  - Date/time
  - Lead name and email
  - Listing code and title
  - Email subject
  - Status (sent/draft)
  - Sent by (agent/broker/lead)
  - Confidence score with color coding
  - Final action (answered/escalated/etc.)
  - Tools called (badges)
- Pagination controls with page navigation
- Export to CSV button (placeholder)
- Responsive table design

**API Integration**:
- `GET /api/v1/analytics/emails?skip={offset}&limit={limit}`

---

### ✅ EA-DASH-002: Review Queue UI
**Review and approval interface** (`/dashboard/review-queue`)

**Features**:

**Queue List (Left Panel)**:
- Priority-sorted list of emails needing review
- Card-based UI with:
  - Lead name and email
  - Priority badge (High/Medium/Low based on score)
  - Listing code and title
  - Message preview (last 2 lines)
  - Timestamp and confidence score
- Color-coded selection (blue highlight for active)
- Auto-refresh every 30 seconds
- Empty state when queue is clear

**Thread Review Panel (Right Panel)**:
- **Thread Information**:
  - Lead details
  - Listing details with asking price
  - Message count
- **Tabbed Interface**:
  - **Conversation Tab**:
    - Last inbound message (blue background)
    - Agent's proposed response (editable)
    - Response editor with character/word count
  - **Reasoning Tab**:
    - Full agent reasoning panel
    - Confidence breakdown
    - Tools called
    - Concerns and flags
- **Action Buttons**:
  - **Approve & Send**: Send as-is
  - **Edit & Send**: Edit then send
  - **Manual Reply**: Write from scratch
  - **Mark as Resolved**: Close without sending
- **Edit Mode**:
  - Inline response editing
  - Character and word counter
  - Send edited response
  - Cancel editing
- **Loading States**: Processing indicator
- **Error Handling**: Clear error messages

**Components**:
- `ThreadReviewPanel`: Main review interface
- `ResponseEditor`: Textarea with formatting and stats
- Integration with `AgentReasoningPanel`

**Workflow**:
1. Select email from queue (left)
2. Review conversation and agent reasoning (right)
3. Choose action:
   - Approve → Sends immediately
   - Edit → Modify text, then send
   - Manual → Write custom reply
   - Resolve → Close without email
4. Success → Queue refreshes, item removed

**API Integration**:
- `GET /api/v1/review-queue`
- `POST /api/v1/review-queue/{id}/approve`
- `POST /api/v1/review-queue/{id}/manual-reply`
- `POST /api/v1/review-queue/{id}/mark-resolved`

**User Experience**:
- Side-by-side layout for context
- Single-click actions for speed
- Undo protection (confirmation dialogs can be added)
- Real-time queue updates
- Mobile-responsive (stacks vertically)

---

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── dashboard/
│   │   │   ├── page.tsx                  # Analytics Dashboard (EA-DASH-004)
│   │   │   ├── activity/
│   │   │   │   └── page.tsx              # Email Activity Log (EA-DASH-001)
│   │   │   └── review-queue/
│   │   │       └── page.tsx              # Review Queue UI (EA-DASH-002) ✅
│   │   ├── layout.tsx                    # Root layout
│   │   ├── providers.tsx                 # React Query provider
│   │   ├── page.tsx                      # Landing page (redirects to /dashboard)
│   │   └── globals.css                   # Global styles + Tailwind
│   ├── components/
│   │   ├── ui/                          # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── badge.tsx
│   │   │   ├── accordion.tsx
│   │   │   ├── table.tsx
│   │   │   ├── tabs.tsx
│   │   │   └── textarea.tsx             # Textarea component ✅
│   │   ├── agent-reasoning-panel.tsx    # Agent Reasoning Display (EA-DASH-003)
│   │   ├── thread-review-panel.tsx      # Thread review interface ✅
│   │   ├── response-editor.tsx          # Response editor with stats ✅
│   │   ├── dashboard-layout.tsx         # Dashboard layout with sidebar
│   │   └── __tests__/                   # Component tests
│   │       ├── agent-reasoning-panel.test.tsx
│   │       ├── thread-review-panel.test.tsx  ✅
│   │       └── response-editor.test.tsx       ✅
│   ├── lib/
│   │   ├── api.ts                       # API client (axios + interceptors)
│   │   └── utils.ts                     # Utility functions
│   └── types/
│       └── index.ts                     # TypeScript interfaces
├── public/                              # Static assets
├── package.json                         # Dependencies
├── tsconfig.json                        # TypeScript configuration
├── tailwind.config.ts                   # Tailwind configuration
├── next.config.js                       # Next.js configuration
├── jest.config.js                       # Jest configuration
└── README.md                            # This file
```

## Getting Started

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.local.example .env.local

# Edit .env.local if needed
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000 in your browser
```

### Build for Production

```bash
# Build the application
npm run build

# Start production server
npm start
```

### Testing

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm test -- --coverage
```

### Linting

```bash
# Run ESLint
npm run lint
```

## Environment Variables

Create a `.env.local` file in the root directory:

```bash
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Integration

The frontend connects to the FastAPI backend using an Axios client configured in `src/lib/api.ts`.

### API Client Features

- **Base URL**: Configured via `NEXT_PUBLIC_API_URL`
- **Authentication**: Automatic Bearer token injection from localStorage
- **Token Refresh**: Redirects to login on 401 errors
- **Type-safe**: All API responses typed with TypeScript interfaces

### API Modules

**Analytics API** (`analyticsApi`):
```typescript
analyticsApi.getOverview(period: '7d' | '30d' | '90d' | 'all')
analyticsApi.getEmails(params: { skip, limit, start_date, end_date, listing_id, status })
analyticsApi.getTrends(period: '7d' | '30d' | '90d' | 'all')
```

**Review Queue API** (`reviewQueueApi`):
```typescript
reviewQueueApi.getQueue()
reviewQueueApi.approve(threadId: string, edits?: string)
reviewQueueApi.manualReply(threadId: string, bodyText: string)
reviewQueueApi.markResolved(threadId: string)
```

**Auth API** (`authApi`):
```typescript
authApi.login(email: string, password: string)
authApi.logout()
```

## Component Documentation

### AgentReasoningPanel

Displays detailed agent reasoning with confidence breakdown.

**Props**:
```typescript
interface AgentReasoningPanelProps {
  reasoning: AgentReasoningDetail
  className?: string
}
```

**Example**:
```tsx
<AgentReasoningPanel
  reasoning={{
    why_flagged: "Low confidence score",
    confidence: 0.42,
    concerns: ["No NDA signed"],
    tools_called: ["get_nda_status"],
    confidence_factors: {
      positive: [{ factor: "Listing identified", weight: 0.3 }],
      negative: [{ factor: "No NDA signed", weight: -0.4 }],
    }
  }}
/>
```

### DashboardLayout

Main layout component with sidebar navigation.

**Usage**:
```tsx
import { DashboardLayout } from '@/components/dashboard-layout'

export default function Page() {
  return (
    <DashboardLayout>
      {/* Your page content */}
    </DashboardLayout>
  )
}
```

**Features**:
- Fixed sidebar navigation
- Active route highlighting
- Logout functionality
- Responsive design

## Utility Functions

Located in `src/lib/utils.ts`:

```typescript
// Tailwind CSS class merging
cn(...inputs: ClassValue[]): string

// Format dates
formatDate(date: Date | string): string

// Format currency
formatCurrency(amount: number): string

// Format percentage
formatPercentage(value: number): string
```

## Type Definitions

All TypeScript interfaces are defined in `src/types/index.ts`:

- `AnalyticsOverview`
- `EmailActivityItem`
- `AnalyticsTrends`
- `AgentReasoningDetail`
- `ReviewQueueItem`
- and more...

## Testing

### Test Coverage

Currently tested:
- ✅ `AgentReasoningPanel` - Full component testing

### Running Tests

```bash
# Run all tests
npm test

# Run specific test file
npm test agent-reasoning-panel.test.tsx

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Import repository in Vercel
3. Set environment variables:
   - `NEXT_PUBLIC_API_URL`: Your backend API URL
4. Deploy

### Docker

```bash
# Build Docker image
docker build -t email-agent-frontend .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://api.example.com email-agent-frontend
```

## Future Enhancements

### Planned Improvements (Week 5+)

- Real-time updates via WebSocket
- Advanced filtering in activity log
- CSV export functionality
- User settings page
- Dark mode support
- Mobile app (React Native)

## Performance Optimizations

- **Code Splitting**: Automatic via Next.js App Router
- **Image Optimization**: Next.js Image component
- **Lazy Loading**: React Query with stale-while-revalidate
- **Caching**: React Query cache (1 minute stale time)
- **Bundle Size**: Tree-shaking via Next.js

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Troubleshooting

### API Connection Issues

**Problem**: "Failed to fetch"
**Solution**: Verify backend is running on `http://localhost:8000` and CORS is configured

### Authentication Errors

**Problem**: 401 Unauthorized
**Solution**: Clear localStorage and re-login: `localStorage.removeItem('access_token')`

### Build Errors

**Problem**: Module not found
**Solution**: Delete `node_modules` and `.next`, then run `npm install` and `npm run dev`

## Contributing

1. Create feature branch: `git checkout -b feature/my-feature`
2. Make changes and add tests
3. Run linter: `npm run lint`
4. Run tests: `npm test`
5. Commit: `git commit -m "Add my feature"`
6. Push: `git push origin feature/my-feature`
7. Create Pull Request

## License

Proprietary - All rights reserved

---

**Built with** ❤️ **using Next.js 14 and shadcn/ui**
