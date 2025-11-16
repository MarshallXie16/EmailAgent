# Email Agent for Business Brokers

An AI-powered email assistant that helps business brokers respond to listing inquiries automatically while maintaining human-like communication and protecting sensitive information.

## Overview

The Email Agent:
- Monitors a broker's Gmail inbox for new inquiries
- Answers common questions about business listings
- Gates confidential information behind NDA requirements
- Encourages high-intent leads to book meetings
- Processes emails in batches (not instant) to feel human
- Escalates uncertain or complex questions to the broker
- Allows brokers to review and override all responses

## Tech Stack

### Backend
- **FastAPI** (Python 3.11+) - REST API server
- **PostgreSQL** with **pgvector** - Database and vector search
- **Celery** or **RQ** - Background job processing
- **Redis** - Job queue and caching
- **OpenAI GPT-4.x** - LLM for agent intelligence
- **Gmail API** - Email ingestion and sending

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components

### Infrastructure
- **S3-compatible storage** - Document storage (PDFs, CIMs)
- **Railway/Fly.io** - Backend hosting
- **Vercel** - Frontend hosting

## Project Structure

```
EmailAgent/
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API routes
│   │   ├── core/        # Config, security, database
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   └── workers/     # Celery tasks
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   ├── requirements.txt
│   └── main.py
├── frontend/            # Next.js application
│   ├── app/            # App router pages
│   ├── components/     # React components
│   ├── lib/            # Utilities
│   ├── public/         # Static assets
│   └── package.json
├── docs/               # Additional documentation
├── design_docs.md      # Complete technical spec
├── CLAUDE.md           # AI agent instructions
├── memory.md           # Project knowledge base
├── tasks.md            # Implementation tracking
└── README.md           # This file
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ with pgvector extension
- Redis (for background jobs)
- Gmail API credentials
- OpenAI API key
- S3-compatible storage credentials

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload

# In another terminal, start Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# And Celery beat for scheduled tasks
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install
# or
pnpm install

# Copy environment file and configure
cp .env.example .env.local
# Edit .env.local with API URL

# Start development server
npm run dev
```

Access the dashboard at `http://localhost:3000`

### Database Setup

```bash
# Install PostgreSQL and pgvector extension
# On Ubuntu:
sudo apt-get install postgresql-14 postgresql-14-pgvector

# Create database
createdb emailagent

# Enable pgvector extension
psql emailagent -c "CREATE EXTENSION vector;"
```

## Environment Variables

### Backend (.env)

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/emailagent

# Redis
REDIS_URL=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=sk-...

# Gmail API
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json
GMAIL_TOKEN_PATH=/path/to/token.json

# S3 Storage
S3_ENDPOINT=https://s3.amazonaws.com
S3_BUCKET=emailagent-docs
S3_ACCESS_KEY=...
S3_SECRET_KEY=...

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App Config
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development Workflow

1. **Read design_docs.md** for complete specifications
2. **Check tasks.md** for current sprint tasks
3. **Review memory.md** for architectural decisions
4. **Implement features** following the 6-week roadmap
5. **Write tests** for all business logic
6. **Update documentation** as you build
7. **Commit frequently** with clear messages

## Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app tests/  # With coverage
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:watch
```

## Deployment

### Backend (Railway/Fly.io)

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and link project
railway login
railway link

# Deploy
railway up
```

### Frontend (Vercel)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
cd frontend
vercel
```

## Key Features

### Week 1-2 (Foundations)
- [x] Project setup
- [ ] Authentication system
- [ ] Broker settings management
- [ ] Listings CRUD
- [ ] Database with pgvector

### Week 3 (Email & Documents)
- [ ] Gmail API integration
- [ ] Email ingestion
- [ ] Document upload to S3
- [ ] Vector embeddings generation
- [ ] Dashboard basics

### Week 4 (Agent Core)
- [ ] LLM integration with tools
- [ ] Batch processing system
- [ ] Basic question answering
- [ ] Draft generation

### Week 5 (Trust & Control)
- [ ] NDA gating logic
- [ ] Calendly integration
- [ ] Broker override system
- [ ] Auto-send toggle

### Week 6 (Hardening)
- [ ] Escalation logic
- [ ] Logging and monitoring
- [ ] Error handling
- [ ] Pilot testing

## Support

For issues or questions, contact the development team.

## License

Proprietary - All rights reserved
