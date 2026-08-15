# CareerAI — AI-Powered Job Search Platform

A production-grade career assistant with semantic job matching, resume analysis, and AI-powered career advice.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | FastAPI + Python 3.11 |
| Database | PostgreSQL + SQLAlchemy ORM |
| Cache | Redis (job search results, TTL 1hr) |
| NLP | spaCy (NER) + sentence-transformers (embeddings) |
| AI | Google Gemini 1.5 Flash |
| Job Search | Adzuna API (with mock fallback) |
| Deployment | Docker Compose |

## Architecture

```
React Frontend (Vite :5173)
        ↓ /api/v1/* (proxied)
FastAPI Backend (:8000)
    ├── POST /api/v1/resume/upload     → pdfplumber + spaCy + embedding
    ├── POST /api/v1/jobs/search       → Adzuna API + Redis cache
    ├── POST /api/v1/match/score       → cosine similarity scoring
    └── POST /api/v1/match/advice      → Gemini cover letter + tips
        ↓
PostgreSQL (users, resumes, saved_jobs)
Redis (job search cache)
```

## Quick Start

### 1. Clone and configure
```bash
git clone <your-repo>
cd career-platform
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 2. Start infrastructure
```bash
docker-compose up postgres redis -d
```

### 3. Run backend
```bash
# Run from the PROJECT ROOT — the app imports `backend.*`, so it must not be run from inside backend/
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

### 4. Run frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

### Or run everything with Docker
```bash
docker-compose up --build
```

## API Keys

| Service | Required | Free Tier | Link |
|---------|----------|-----------|------|
| Gemini | Yes | Yes (generous) | https://aistudio.google.com/app/apikey |
| Adzuna | No | Yes (500 calls/day) | https://developer.adzuna.com/ |

> Without Adzuna keys, the app serves realistic mock Indian job data automatically.

## Features

- **Resume Upload & Parsing** — PDF extraction with pdfplumber, entity recognition with spaCy, ATS scoring
- **Semantic Job Matching** — sentence-transformers embeddings + cosine similarity (not keyword matching)
- **AI Career Advice** — Gemini generates cover letters, skill gap analysis, interview tips
- **Job Search** — Adzuna API with Redis caching (1hr TTL), mock fallback for dev
- **Kanban Job Board** — Track applications: Saved → Applied → Interviewing → Offered
- **Dashboard** — Application pipeline stats and resume health overview

## Project Structure

```
career-platform/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings
│   ├── database.py             # SQLAlchemy engine
│   ├── models/models.py        # ORM models
│   ├── schemas/schemas.py      # Pydantic schemas
│   ├── routers/
│   │   ├── users.py
│   │   ├── resume.py
│   │   ├── jobs.py
│   │   └── match.py
│   └── services/
│       ├── resume_parser.py    # pdfplumber + spaCy
│       ├── semantic_matcher.py # sentence-transformers
│       ├── job_search.py       # Adzuna + Redis
│       └── llm_service.py      # Gemini
└── frontend/
    └── src/
        ├── pages/
        │   ├── Dashboard.jsx
        │   ├── JobSearch.jsx
        │   ├── ResumeAnalysis.jsx
        │   └── SavedJobs.jsx
        └── components/
            ├── Navbar.jsx
            ├── JobCard.jsx
            ├── MatchScoreBar.jsx
            ├── ResumeUpload.jsx
            └── CareerAdviceModal.jsx
```

## Running Tests

```bash
# From project root
pytest backend/tests/ -v

# With coverage
pip install pytest-cov
pytest backend/tests/ --cov=backend --cov-report=term-missing
```

## Database Migrations (Alembic)

```bash
cd backend

# Apply migrations (creates all tables)
alembic upgrade head

# Create a new migration after model changes
alembic revision --autogenerate -m "add column xyz"

# Roll back one step
alembic downgrade -1
```

## Deployment

**Backend → Railway**
1. Push to GitHub
2. Create Railway project → connect repo → set env vars from `.env.example`
3. Railway auto-deploys on every push to `main`

**Frontend → Vercel**
1. Import GitHub repo on vercel.com
2. Set root to `frontend/`, build command `npm run build`, output `dist`
3. Add env var: `VITE_API_URL=https://your-railway-backend.up.railway.app`

## Resume Bullets (use these after building)

```
• Architected a semantic job-matching engine using sentence-transformer embeddings
  (all-MiniLM-L6-v2), replacing keyword matching with continuous cosine similarity
  scoring across live job listings.

• Built a structured resume parsing pipeline with spaCy NER for typed entity
  extraction (skills, companies, education) and ATS scoring engine.

• Integrated Redis caching layer with TTL-based invalidation for Adzuna API,
  eliminating redundant calls on repeat searches.

• Designed decoupled REST API (FastAPI, PostgreSQL, SQLAlchemy ORM) with Pydantic
  validation, consumed by a React/Tailwind frontend with Kanban job tracking.

• Implemented Gemini LLM integration for personalized cover letter generation,
  skill gap analysis, and interview coaching per job-resume pair.
```
