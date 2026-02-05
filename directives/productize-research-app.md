# Directive: Productize Research App

## Goal

Build a production-grade SaaS web application that allows users to purchase and generate comprehensive research dossiers on companies and people.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Next.js       │────▶│   FastAPI       │────▶│   Redis Queue   │
│   Frontend      │◀────│   Backend       │◀────│   + Workers     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │                        │
                               ▼                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │   PostgreSQL    │     │   Research      │
                        │   Database      │     │   Scripts       │
                        └─────────────────┘     └─────────────────┘
```

## Tech Stack

| Layer | Technology | Reason |
|-------|------------|--------|
| Frontend | Next.js 14 + TypeScript | SSR, App Router, great DX |
| Styling | Tailwind CSS + shadcn/ui | Professional, customizable |
| Backend | FastAPI + Python | Same language as research scripts |
| Database | PostgreSQL + SQLAlchemy | Production-grade, reliable |
| Queue | Redis + Celery | Async job processing |
| Auth | JWT + bcrypt | Simple, stateless |
| Payments | Stripe | Industry standard |
| Email | Resend | Developer-friendly |
| Deploy | Docker + Railway/Fly.io | Easy, scalable |

## Database Schema

```sql
-- Users table
users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE,
    password_hash VARCHAR,
    name VARCHAR,
    credits INTEGER DEFAULT 0,
    stripe_customer_id VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)

-- Research jobs table
research_jobs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users,
    target VARCHAR,
    target_type VARCHAR,  -- 'company' | 'person'
    depth VARCHAR,        -- 'quick' | 'standard' | 'deep'
    status VARCHAR,       -- 'pending' | 'processing' | 'completed' | 'failed'
    credits_used INTEGER,
    report_path VARCHAR,
    error_message VARCHAR,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP
)

-- Payments table
payments (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users,
    stripe_payment_id VARCHAR,
    amount_cents INTEGER,
    credits_purchased INTEGER,
    status VARCHAR,
    created_at TIMESTAMP
)
```

## API Endpoints

### Auth
- `POST /api/auth/register` - Create account
- `POST /api/auth/login` - Login, get JWT
- `POST /api/auth/logout` - Invalidate token
- `GET /api/auth/me` - Get current user

### Research
- `POST /api/research` - Create new research job
- `GET /api/research` - List user's jobs
- `GET /api/research/{id}` - Get job status/result
- `GET /api/research/{id}/download` - Download PDF

### Payments
- `POST /api/payments/create-checkout` - Create Stripe checkout
- `POST /api/webhooks/stripe` - Handle Stripe webhooks
- `GET /api/payments/history` - Get payment history

### User
- `GET /api/user/credits` - Get credit balance
- `PATCH /api/user/profile` - Update profile

## Pricing Model

| Tier | Credits | Price | Per Report |
|------|---------|-------|------------|
| Single | 1 | $15 | $15.00 |
| Starter | 5 | $60 | $12.00 |
| Pro | 20 | $200 | $10.00 |
| Enterprise | Custom | Custom | Custom |

Credit costs by depth:
- Quick: 1 credit
- Standard: 2 credits
- Deep: 4 credits

## Frontend Pages

1. **Landing Page** (`/`)
   - Hero with value prop
   - How it works
   - Pricing section
   - Sample report preview
   - CTA to sign up

2. **Auth Pages** (`/login`, `/register`)
   - Clean, minimal forms
   - Social login optional (future)

3. **Dashboard** (`/dashboard`)
   - Credit balance
   - Recent reports
   - Quick research form
   - Usage stats

4. **New Research** (`/research/new`)
   - Target input with autocomplete
   - Type selector
   - Depth selector with credit cost
   - Submit button

5. **Report View** (`/research/[id]`)
   - Status indicator if processing
   - Full report when complete
   - Download PDF button
   - Share link (future)

6. **Buy Credits** (`/credits`)
   - Pricing tiers
   - Stripe checkout integration

7. **Settings** (`/settings`)
   - Profile management
   - Password change
   - Payment history

## Security Requirements

- [ ] Password hashing with bcrypt (cost 12)
- [ ] JWT tokens with 24h expiry
- [ ] HTTPS only in production
- [ ] CORS configured for frontend domain only
- [ ] Rate limiting on auth endpoints
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (React handles this)
- [ ] Stripe webhook signature verification

## Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/research_app

# Redis
REDIS_URL=redis://localhost:6379

# Auth
JWT_SECRET=<random-256-bit-key>
JWT_ALGORITHM=HS256

# Stripe
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_SINGLE=price_...
STRIPE_PRICE_STARTER=price_...
STRIPE_PRICE_PRO=price_...

# Email
RESEND_API_KEY=re_...
FROM_EMAIL=reports@yourdomain.com

# App
FRONTEND_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com
```

## File Structure

```
webapp/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── database.py          # DB connection
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # Auth endpoints
│   │   │   ├── research.py      # Research endpoints
│   │   │   ├── payments.py      # Payment endpoints
│   │   │   └── users.py         # User endpoints
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py      # JWT, password hashing
│   │   │   └── deps.py          # Dependencies
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── research.py
│   │   │   └── payment.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── research.py      # Research orchestration
│   │   │   ├── stripe.py        # Stripe integration
│   │   │   └── email.py         # Email service
│   │   └── workers/
│   │       ├── __init__.py
│   │       └── research.py      # Celery tasks
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic/                 # DB migrations
│
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js app router
│   │   ├── components/          # React components
│   │   ├── lib/                 # Utilities
│   │   └── styles/              # Global styles
│   ├── package.json
│   ├── Dockerfile
│   └── tailwind.config.js
│
├── docker-compose.yml
└── README.md
```

## Changelog

| Date | Change |
|------|--------|
| 2026-01-29 | Created directive |
