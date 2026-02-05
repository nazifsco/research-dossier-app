# Deployment Guide

## Quick Deploy Options

### Railway (Recommended - Easiest)
1. Push to GitHub
2. Connect Railway to repo
3. Set environment variables (see below)
4. Deploy automatically

### Vercel (Frontend) + Railway (Backend)
- Frontend: Connect Vercel to repo, deploy `/webapp/frontend`
- Backend: Railway for `/webapp/backend`

---

## Environment Variables

### Backend (.env)
```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/dbname
JWT_SECRET=your-random-256-bit-secret

# Payments
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email
RESEND_API_KEY=re_...
FROM_EMAIL=noreply@yourdomain.com

# OAuth
GOOGLE_CLIENT_ID=...apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=...

# LLM
OPENAI_API_KEY=sk-...

# URLs
FRONTEND_URL=https://yourdomain.com
API_URL=https://api.yourdomain.com

# Optional
REDIS_URL=redis://...
DEBUG=false
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

---

## Service Setup

### 1. PostgreSQL
**Options:**
- [Supabase](https://supabase.com) - Free tier, instant setup
- [Neon](https://neon.tech) - Serverless Postgres
- Railway - Built-in database

**After setup:**
```bash
cd webapp/backend
alembic upgrade head
```

### 2. Google OAuth
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create OAuth 2.0 credentials
3. Add redirect URIs:
   - `https://yourdomain.com/auth/google/callback`
   - `http://localhost:3000/auth/google/callback` (dev)
4. Copy Client ID and Secret to `.env`

### 3. Stripe
1. Get keys from [Stripe Dashboard](https://dashboard.stripe.com/apikeys)
2. Set up webhook endpoint: `https://api.yourdomain.com/api/payments/webhook`
3. Listen for: `checkout.session.completed`
4. Copy webhook secret to `.env`

### 4. Resend (Email)
1. Sign up at [Resend](https://resend.com)
2. Add sending domain
3. Copy API key to `.env`

### 5. OpenAI
1. Get API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add to `.env`

---

## Docker Deployment

```bash
# Build and run
cd webapp
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Database Migration

```bash
cd webapp/backend
alembic upgrade head
```

---

## Health Check

After deployment:
- Backend: `https://api.yourdomain.com/health`
- Should return status of all services

---

## Security Checklist

- [ ] `DEBUG=false` in production
- [ ] Change `JWT_SECRET` from default
- [ ] Use PostgreSQL (not SQLite)
- [ ] Enable HTTPS
- [ ] Set proper CORS origins
- [ ] Configure Stripe webhook signature verification
- [ ] Verify Google OAuth redirect URIs
