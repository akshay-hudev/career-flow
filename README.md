# CareerAI — AI-Powered Job Search Platform

A full-stack career assistant: upload a PDF resume, search jobs (Adzuna), rank
resume-to-job matches with TF-IDF cosine similarity, and get Google Gemini–powered
career advice and mock-interview coaching — all behind JWT user authentication.

FastAPI backend + React 18 (Vite) frontend, PostgreSQL, and Redis.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + Vite + Tailwind CSS (react-router v6, axios, react-query) |
| Backend | FastAPI + Python 3.11 (Uvicorn) |
| Auth | JWT (python-jose, HS256) + bcrypt password hashing |
| Database | PostgreSQL 16 + SQLAlchemy ORM (psycopg v3) + Alembic |
| Cache | Redis 7 (job-search results, 1 hr TTL; degrades gracefully if down) |
| Resume parsing | pdfplumber + regex/keyword heuristics, fixed-rubric ATS score |
| Matching | scikit-learn TF-IDF + NumPy cosine similarity |
| AI | Google Gemini via `google-generativeai` (configurable `GEMINI_MODEL`, default 2.5 Flash) |
| Agent | LangGraph pipeline (parse → search → rank → advice) |
| Job data | Adzuna API over httpx (mock fallback when keys are absent) |
| Deployment | Docker (Compose runs Postgres + Redis + backend); Railway + Vercel in prod |

> **Note:** resume parsing and matching are **not** ML/NLP embeddings — there is no
> spaCy and no sentence-transformers in this project. Parsing is `pdfplumber` text
> extraction plus regex/keyword heuristics against a hardcoded ~50-term skill list;
> matching is classic TF-IDF cosine similarity.

## Architecture

```
React SPA (Vite :5173)
   │  /api/v1/*   (Vite dev proxy → :8000, or VITE_API_URL in prod)
   ▼
FastAPI (:8000)        — JWT auth on protected routes
   ├── /auth        register · login · me
   ├── /users       create · get
   ├── /resume      upload (pdfplumber parse + ATS score) · list · get · delete
   ├── /jobs        search (Adzuna + Redis cache, mock fallback) · save · saved · status · delete
   ├── /match       score (TF-IDF cosine + skill gaps) · advice (Gemini)
   ├── /interview   questions · evaluate   (Gemini, stateless)
   └── /agent       run   (LangGraph: parse → search → rank → advice)
   │
   ├── PostgreSQL   (users, resumes, saved_jobs, job_searches)
   └── Redis        (job-search cache, 1 hr TTL)

External services: Adzuna API (job listings) · Google Gemini (advice, interview, summaries)
```

## Features

- **Authentication (JWT)** — register/login with bcrypt-hashed passwords; 7-day
  HS256 tokens. Frontend has a combined login/register page, `UserContext`,
  `ProtectedRoute` gating, and an axios interceptor that auto-logs-out on `401`.
- **Resume upload & parsing** — PDF text extraction with pdfplumber, then
  regex/keyword heuristics for skills, education, companies, and years of
  experience, plus a fixed-rubric ATS score. List / get / delete stored resumes.
- **Job search** — real Adzuna REST calls over httpx (India by default), cached in
  Redis (1 hr TTL). Falls back to built-in mock jobs when Adzuna keys are missing
  or a request fails.
- **Resume ↔ job matching** — scikit-learn TF-IDF vectors + NumPy cosine
  similarity (scaled 0–100), plus keyword-based matched-skills and skill-gap
  analysis against a hardcoded tech-skill list.
- **AI career advice (Gemini)** — improvement suggestions, a cover-letter draft,
  and interview tips per resume/job pair, plus a 3-sentence resume summary.
- **Mock interview (Gemini)** — generates tailored questions
  (technical / behavioral / situational / hr) and evaluates answers (score,
  strengths, improvements, a sample better answer, and a verdict). Stateless — not
  persisted to the database.
- **Saved-jobs board** — track applications across 5 statuses
  (`saved`, `applied`, `interviewing`, `rejected`, `offered`): save, list (filter
  by status), update status, delete.
- **One-shot agent** — `POST /api/v1/agent/run` runs the whole LangGraph pipeline
  from an uploaded PDF: parse → search → rank → advice.
- **Dashboard** — application pipeline and resume overview.

## Quick Start

### 1. Clone and configure
```bash
git clone <your-repo>
cd Capabl
cp .env.example .env
# Edit .env — at minimum set GEMINI_API_KEY for real AI output (see Configuration)
```

### 2. Start infrastructure (Postgres + Redis)
```bash
docker-compose up postgres redis -d
```

### 3. Run the backend
```bash
# Run from the PROJECT ROOT — the app imports `backend.*`, so it must not be run from inside backend/
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```
API is now at http://localhost:8000 (docs at http://localhost:8000/docs).

### 4. Run the frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

> **Docker note:** `docker-compose.yml` defines **Postgres, Redis, and the backend**
> — there is **no** frontend service. `docker-compose up --build` runs the API on
> :8000; you still start the frontend with `npm run dev`.

## Configuration

Backend settings are read from `.env` (see `.env.example`). Env vars and defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | *(empty)* | **Required for real AI output** (advice, interview, summaries). Without it, those endpoints return canned fallback content instead of failing. |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model name. |
| `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` | *(empty)* | Optional. Without them, job search serves realistic **mock** Indian job data. |
| `SECRET_KEY` | `change-this-in-production` | Signs JWTs. **Must be overridden in production.** |
| `DATABASE_URL` | `postgresql+psycopg://postgres:password@localhost:5432/careerdb` | Postgres URL (psycopg v3). A bare `postgres://` / `postgresql://` is auto-rewritten to `postgresql+psycopg://`. |
| `REDIS_URL` | `redis://localhost:6379/0` | Job-search cache. If Redis is unreachable, caching no-ops (no crash). |
| `DEBUG` | `True` | Debug flag. |
| `CORS_ORIGINS` | `["*"]` | Allowed origins (see Known Issues — CORS is currently hardcoded to `*` in `main.py`). |
| `VITE_API_URL` *(frontend)* | *(empty in dev)* | Production API base; used as `${VITE_API_URL}/api/v1`. In dev it's empty and the Vite proxy forwards `/api` → `:8000`. |

### API keys

| Service | Required | Free tier | Link |
|---------|----------|-----------|------|
| Gemini | For real AI output | Yes (generous) | https://aistudio.google.com/app/apikey |
| Adzuna | No (mock fallback) | Yes (500 calls/day) | https://developer.adzuna.com/ |

## API Endpoints

All under prefix `/api/v1`. Routes marked 🔒 require a JWT (`Authorization: Bearer <token>`).

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/auth/register` | Create account, returns JWT + user |
| POST | `/auth/login` | Authenticate, returns JWT + user |
| GET | `/auth/me` 🔒 | Current authenticated user |
| POST | `/users/` | Idempotent, passwordless user create (returns existing on duplicate email) |
| GET | `/users/{user_id}` | Fetch a user |
| POST | `/resume/upload` 🔒 | Upload & parse a PDF, compute ATS score |
| GET | `/resume/{user_id}/list` | List a user's resumes |
| GET | `/resume/{resume_id}` | Get one resume |
| DELETE | `/resume/{resume_id}` | Delete a resume |
| POST | `/jobs/search` | Adzuna search (optional semantic rank via `?resume_id`) |
| POST | `/jobs/save` | Save a job to the board (`?user_id`) |
| GET | `/jobs/saved/{user_id}` | List saved jobs (optional `?status`) |
| PATCH | `/jobs/saved/{job_id}/status` | Update application status |
| DELETE | `/jobs/saved/{job_id}` | Remove a saved job |
| POST | `/match/score` | Score a resume against job descriptions (cosine + skill gaps) |
| POST | `/match/advice` | Full Gemini advice (skill gaps, cover letter, interview tips) |
| POST | `/interview/questions` | Generate interview questions by type |
| POST | `/interview/evaluate` | Evaluate a mock-interview answer |
| POST | `/agent/run` | One-shot LangGraph pipeline from an uploaded PDF |
| GET | `/` , `/health` | Liveness checks (inline in `main.py`, no prefix) |

## Data Model

Four tables (SQLAlchemy ORM, `backend/models/models.py`):

- **users** — `id`, `email` (unique), `name`, `hashed_password` (nullable — allows
  passwordless rows from `POST /users/`), `created_at`.
- **resumes** — `user_id`, `filename`, `raw_text`, `parsed_data` (JSON),
  `embedding_json` (JSON TF-IDF vector), `ats_score`, `uploaded_at`.
- **saved_jobs** — denormalized job data + `match_score`, `status`
  (`JobStatus` enum: `saved` / `applied` / `interviewing` / `rejected` /
  `offered`), `notes`, `applied_at`.
- **job_searches** — search-history log (`query`, `location`, `results_count`).

> There is **no** `interviews` table — the mock-interview feature is stateless
> (LLM-only) and its results are not stored.

## Project Structure

```
Capabl/
├── backend/
│   ├── main.py                 # FastAPI app, CORS, router wiring, / and /health
│   ├── config.py               # Settings (pydantic-settings)
│   ├── database.py             # SQLAlchemy engine (psycopg v3; normalizes DATABASE_URL)
│   ├── dependencies.py         # get_db, get_current_user (JWT)
│   ├── models/models.py        # ORM: users, resumes, saved_jobs, job_searches
│   ├── schemas/schemas.py      # Pydantic request/response schemas
│   ├── routers/
│   │   ├── auth.py             # register, login, me
│   │   ├── users.py            # create, get
│   │   ├── resume.py           # upload, list, get, delete
│   │   ├── jobs.py             # search, save, saved, status, delete
│   │   ├── match.py            # score, advice
│   │   ├── interview.py        # questions, evaluate
│   │   └── agent.py            # run (LangGraph pipeline)
│   ├── services/
│   │   ├── auth_service.py     # bcrypt hashing + JWT create/verify
│   │   ├── resume_parser.py    # pdfplumber + regex/keyword heuristics + ATS score
│   │   ├── semantic_matcher.py # scikit-learn TF-IDF + NumPy cosine similarity
│   │   ├── job_search.py       # Adzuna (httpx) + Redis cache + mock fallback
│   │   ├── llm_service.py      # Gemini: advice, resume summary
│   │   ├── interview_service.py# Gemini: questions, answer evaluation
│   │   └── career_agent.py     # LangGraph StateGraph
│   ├── alembic/versions/001_initial.py   # single-head migration (all 4 tables)
│   └── tests/                  # 53 tests across 8 files + conftest.py
└── frontend/
    └── src/
        ├── App.jsx             # routes + ProtectedRoute
        ├── context/UserContext.jsx
        ├── api/client.js       # axios client, JWT interceptor, 401 auto-logout
        ├── pages/              # Dashboard, JobSearch, ResumeAnalysis, SavedJobs, MockInterview, LoginPage
        └── components/         # Navbar, JobCard, MatchScoreBar, ResumeUpload, CareerAdviceModal
```

## Running Tests

```bash
# From the project root
pytest backend/tests/ -v
```

53 tests across 8 files: unit tests for the resume parser and TF-IDF matcher, a
mocked-service test of the LangGraph agent, and FastAPI `TestClient` tests for the
auth, users, resume-match, jobs, and interview endpoints. Tests run on SQLite and
create tables via `Base.metadata.create_all` (not Alembic); `conftest.py` overrides
`get_current_user`, so endpoint tests run as a fixed test user.

## Database Migrations (Alembic)

```bash
cd backend
alembic upgrade head          # apply migrations (creates all tables)
alembic revision --autogenerate -m "describe change"
alembic downgrade -1
```

There is one migration head, `001_initial`, which creates all four tables, the
`jobstatus` enum, and indexes.

## Deployment

**Backend → Railway** (`railway.toml`): Dockerfile build (`backend/Dockerfile`,
`python:3.11-slim`), Uvicorn on `$PORT`, healthcheck `/health`.

**Frontend → Vercel** (`vercel.json`): set root to `frontend/`, build `npm run build`,
output `dist`.

### ⚠️ Deploy-host mismatch (unresolved)

The repo currently disagrees on where the backend is hosted:

| Config | Points backend at |
|--------|-------------------|
| `railway.toml` | **Railway** (Dockerfile deploy) |
| `frontend/.env.production` + `vercel.json` | **Render** (`career-platform-rtdk.onrender.com`) |

Harmless while running locally, but **before deploying, pick one host** and make
all three consistent (set `frontend/.env.production` → `VITE_API_URL` and the
`vercel.json` rewrite to the chosen backend URL).

## Known Issues & Security

Running **local-only** for now — a few issues are tracked but deliberately deferred:

- **Security (do not expose publicly yet):** several routes trust a client-supplied
  `user_id` with no ownership check, some are unauthenticated (IDOR), and the
  default `SECRET_KEY` is a placeholder. CORS is hardcoded to `*` in `main.py`.
  Full details and recommended fixes: [`SECURITY_NOTES.md`](SECURITY_NOTES.md).
- **Matching caveat:** `/match/score` fits the resume and job together (shared
  vocabulary → meaningful score), but job-ranking fits each job's TF-IDF vector
  independently, so those ranking scores compare mismatched vocabularies — treat
  them as rough signals, not calibrated similarities.
- **Maintenance:** `google-generativeai` is deprecated (SDK sunset by Google); plan
  a migration to the `google-genai` SDK. `langchain-core` is declared but the full
  `langchain` package is not.
