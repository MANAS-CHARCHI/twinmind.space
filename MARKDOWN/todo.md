# TWINMIND.SPACE — Master Build TODO
> Tasks ordered from environment setup to full system completion.  
> Check off each item as you go. Every section maps to an architecture phase.

---

## 🖥️ STAGE 0 — Environment & Project Setup

### Machine & Tools
- [ ] Verify macOS is up to date (M1 Mac)
- [ ] Install Homebrew if not present
- [ ] Install Python 3.11+ via `pyenv`
- [ ] Install Node.js 20+ via `nvm`
- [ ] Install Docker Desktop for Mac (Apple Silicon build)
- [ ] Install Git and configure global username/email
- [ ] Install `psql` CLI (PostgreSQL client)
- [ ] Install `redis-cli`
- [ ] Install VS Code or Cursor IDE
- [ ] Install Postman or Bruno for API testing

### Project Scaffolding
- [ ] Create root project folder `twinmind-space/`
- [ ] Initialize Git repo (`git init`)
- [ ] Create `.gitignore` (Python, Node, .env, storage/, models/)
- [ ] Create root `README.md` with project overview
- [ ] Create folder structure: `backend/`, `frontend/`, `scripts/`, `storage/`, `migrations/`

### Docker & Services
- [ ] Write `docker-compose.yml` with PostgreSQL 15 (pgvector) + Redis services with volume mounts
- [ ] Run `docker-compose up -d` and verify both services start
- [ ] Connect to PostgreSQL and run `CREATE EXTENSION vector;`
- [ ] Verify Redis connection with `redis-cli ping`

---

## ⚙️ STAGE 1 — Backend Foundation (FastAPI)

### Project Init
- [ ] Create Python virtual environment in `backend/`
- [ ] Create `requirements.txt` with: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `asyncpg`, `pgvector`, `psycopg2-binary`, `redis`, `apscheduler`, `python-dotenv`, `pydantic-settings`, `httpx`, `python-jose`, `passlib`
- [ ] Install all dependencies
- [ ] Create `app/` directory structure: `core/`, `api/v1/`, `agents/`, `memory/`, `services/`, `worker/`

### Config & Environment
- [ ] Create `.env` with: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `LLM_MODEL_PATH`
- [ ] Create `app/core/config.py` using `pydantic-settings`
- [ ] Create `app/core/security.py` (JWT creation, password hashing)
- [ ] Create `app/main.py` with FastAPI app init, CORS, and router includes

### Database Schema (SQLAlchemy + Alembic)
- [ ] Initialize Alembic (`alembic init migrations/`) and configure `alembic.ini`
- [ ] Create SQLAlchemy Base model
- [ ] Create `Users` model (id, email, hashed_password, created_at, is_active, whatsapp_number, global_pause)
- [ ] Create `OAuthTokens` model (user_id, provider, access_token_encrypted, refresh_token, expires_at)
- [ ] Create `Tasks` model (user_id, title, status, due_date, source, metadata)
- [ ] Create `ScheduledJobs` model (user_id, job_type, cron_expr, last_run, next_run, enabled)
- [ ] Create `Notifications` model (user_id, channel, category, message, sent_at, read)
- [ ] Create `DocumentsMetadata` model (user_id, filename, file_path, file_type, uploaded_at, summary)
- [ ] Create `EmailMetadata` model (user_id, message_id, sender, subject, received_at, urgency_score, labels)
- [ ] Create `LinkedInContacts` model (user_id, contact_id, name, title, company, connection_status, last_action)
- [ ] Create `JobApplications` model (user_id, job_id, company, title, status, applied_at, cover_letter_path)
- [ ] Create `ActionLogs` model (user_id, action_type, target, status, timestamp, notes)
- [ ] Create vector tables: `EmailVectors`, `DocumentVectors`, `ResumeVectors`, `ConversationVectors`, `NewsVectors` — all with `(id, user_id, embedding vector(1536), source_id, metadata jsonb)`
- [ ] Generate first Alembic migration and apply it
- [ ] Verify all tables exist in PostgreSQL

### User Isolation & File System
- [ ] Create `app/core/storage.py`:
  - [ ] Function to create `storage/user_{id}/` on registration with sub-folders: `documents/`, `email_cache/`
  - [ ] Auto-create blank `persona.md`, `memory.md`, `activity_log.md`
  - [ ] Safe read/write/append functions for each markdown file

---

## 🔐 STAGE 2 — Authentication System

### User Auth Endpoints
- [ ] Create `app/api/v1/auth.py` with:
  - [ ] `POST /auth/register` — create user, hash password, init storage folder
  - [ ] `POST /auth/login` — verify password, return JWT access + refresh tokens
  - [ ] `POST /auth/refresh` — rotate tokens
  - [ ] `GET /auth/me` — return current user info
- [ ] Add `get_current_user` dependency using JWT decode
- [ ] Test all auth endpoints in Postman

### Google OAuth (Gmail + Calendar)
- [ ] Enable Gmail API and Google Calendar API in Google Cloud Console
- [ ] Create OAuth 2.0 credentials (Web app type) and note client ID/secret
- [ ] Create `app/services/google_oauth.py`:
  - [ ] Generate Google auth URL with scopes: `gmail.readonly`, `gmail.send`, `calendar.events`
  - [ ] Handle OAuth callback and exchange code for tokens
  - [ ] Encrypt tokens with Fernet and store in `OAuthTokens`
  - [ ] Implement token refresh logic (auto-refresh when expired)
- [ ] Create `GET /auth/google` and `GET /auth/google/callback` endpoints
- [ ] Test full Google OAuth flow end-to-end

---

## 🤖 STAGE 3 — LLM & Embedding Setup

### Local LLM (Ollama)
- [ ] Install Ollama (`brew install ollama`)
- [ ] Pull model: `ollama pull mistral` (or llama3 based on M1 RAM)
- [ ] Verify Ollama `/api/generate` endpoint responds
- [ ] Create `app/core/llm.py`:
  - [ ] `call_llm(prompt, system_prompt) -> str` wrapper
  - [ ] Add timeout and error handling
  - [ ] Log all LLM calls to `ActionLogs`

### Embeddings
- [ ] Choose embedding model (OpenAI `text-embedding-3-small` or local `nomic-embed-text` via Ollama)
- [ ] Create `app/core/embeddings.py`:
  - [ ] `get_embedding(text) -> list[float]`
  - [ ] `get_embeddings_batch(texts) -> list[list[float]]`
- [ ] Test: embed a sentence, store in pgvector, retrieve it

### Vector Memory Layer
- [ ] Create `app/memory/vector_store.py`:
  - [ ] `upsert_embedding(user_id, table, source_id, text, metadata)`
  - [ ] `search_similar(user_id, table, query_text, top_k=5) -> list`
  - [ ] All queries strictly filter by `user_id`
- [ ] Test: upsert two docs for different users, confirm search returns only the correct user's data

### Markdown Memory Layer
- [ ] Create `app/memory/narrative.py`:
  - [ ] `read_persona(user_id)`, `update_persona(user_id, content)`
  - [ ] `append_memory(user_id, note)`, `append_activity(user_id, entry)`
  - [ ] `get_full_context(user_id)` — returns combined persona + memory string for LLM prompt

---

## 📧 STAGE 4 — Email Intelligence System

### Gmail Integration
- [ ] Create `app/services/gmail.py`:
  - [ ] `fetch_recent_emails(user_id, count=50)` using stored OAuth token
  - [ ] Parse: sender, subject, body, date, thread_id, labels
  - [ ] Store metadata in `EmailMetadata`
  - [ ] Cache raw body in `storage/user_{id}/email_cache/{message_id}.txt`
- [ ] Test: fetch and store emails for a real connected user

### Email Embedding & Style Profile
- [ ] Chunk email bodies and generate embeddings → store in `EmailVectors`
- [ ] Create `app/agents/email_style.py`:
  - [ ] Analyze tone, formality, vocabulary from sent emails
  - [ ] Generate style profile summary via LLM
  - [ ] Write result to `persona.md` under `[Email Style]` section

### Email Triage Agent
- [ ] Create `app/agents/email_triage.py`:
  - [ ] Rule-based filters: detect meetings, invoices, deadlines, interview keywords
  - [ ] Score urgency (0–10), store in `EmailMetadata.urgency_score`
  - [ ] If urgency >= threshold: queue notification
- [ ] Test on a batch of 20 real emails

### Email Draft Agent
- [ ] Create `app/agents/email_draft.py`:
  - [ ] `draft_reply(user_id, email_id)`:
    - [ ] Fetch email context and thread
    - [ ] Vector search for top 5 similar past emails
    - [ ] Load persona/style from `persona.md`
    - [ ] Generate draft via LLM
    - [ ] Store draft, return preview — do NOT send
  - [ ] `send_email(user_id, draft_id)` — only callable after user approves
- [ ] Create endpoints: `POST /email/draft`, `POST /email/send`, `GET /email/inbox`
- [ ] Test: draft → preview → approve → send full flow

---

## 📅 STAGE 5 — Calendar & Meeting System

### Google Calendar Integration
- [ ] Create `app/services/google_calendar.py`:
  - [ ] `list_events(user_id, days=7)`
  - [ ] `create_event(user_id, title, start, end, description, attendees)` — returns event + Meet link
  - [ ] `update_event(user_id, event_id, changes)`
  - [ ] `delete_event(user_id, event_id)`

### Meeting Detection from Email
- [ ] Extend `email_triage.py` to detect meeting request patterns
- [ ] Extract proposed date/time via LLM
- [ ] Queue `CONFIRMATION_REQUIRED` notification: "Meeting detected — Schedule / Remind / Decline?"

### Calendar Endpoints
- [ ] `GET /calendar/events`
- [ ] `POST /calendar/create` (confirm timezone first)
- [ ] `PUT /calendar/update/{event_id}`
- [ ] `DELETE /calendar/cancel/{event_id}`
- [ ] Test all CRUD operations with a real Google account

---

## ⏰ STAGE 6 — Scheduler / Heartbeat Engine

- [ ] Install and configure APScheduler with Redis job store
- [ ] Create `app/worker/scheduler.py` — init scheduler on app startup, load per-user jobs from DB
- [ ] Implement **Email Heartbeat** job (every 30–60 min): fetch emails → triage → queue urgent notifications
- [ ] Stub **Daily 9 AM LinkedIn** job (activate in Stage 10)
- [ ] Stub **Daily 9 AM News Digest** job (activate in Stage 8)
- [ ] Stub **6 PM End-of-Day Audit** job (activate in Stage 10)
- [ ] Add cooldown logic: skip job if last run was within cooldown window
- [ ] Per-user `global_pause` flag: all jobs check this before executing
- [ ] Test: verify heartbeat fires, emails are fetched, notifications queued

---

## 🔔 STAGE 7 — Notification System

### Notification Queue
- [ ] Create `app/worker/notifications.py`:
  - [ ] `queue_notification(user_id, category, message, channel)` with dedup + cooldown checks
  - [ ] Categories: `URGENT`, `REMINDER`, `DIGEST`, `CONFIRMATION_REQUIRED`

### Web Push
- [ ] Generate VAPID keys and store in `.env`
- [ ] Store push subscription object in `Users` table
- [ ] `POST /notifications/subscribe` endpoint
- [ ] `send_web_push(user_id, message)` function
- [ ] Test push notification in browser

### WhatsApp
- [ ] Set up WhatsApp Web automation library account and get credentials
- [ ] Create `app/services/whatsapp.py` with `send_whatsapp(user_id, message)` and error handling
- [ ] Test WhatsApp message delivery end-to-end

### Notification Endpoints
- [ ] `GET /notifications` — list unread
- [ ] `POST /notifications/{id}/read`
- [ ] `DELETE /notifications/{id}`

---

## 📰 STAGE 8 — News Intelligence Engine

- [ ] Choose news source API (NewsAPI or Bing News Search) and get API key
- [ ] Create `app/services/news.py` with `fetch_articles(topics, count=30) -> list`
- [ ] Create `app/agents/news_digest.py`:
  - [ ] Read persona interests from `persona.md`
  - [ ] Fetch articles for those topics
  - [ ] Embed articles and store in `NewsVectors`
  - [ ] Rank by similarity to user persona/resume vectors
  - [ ] Filter already-sent article IDs
  - [ ] Select top 10–20, summarize each via LLM
  - [ ] Format and send digest via WhatsApp + Web Push
  - [ ] Store sent article IDs
- [ ] Hook digest into daily 9 AM scheduler
- [ ] Test: full digest generation → delivery

---

## 📄 STAGE 9 — Document Processing Pipeline

### Upload & Processing
- [ ] Create `POST /documents/upload` endpoint — save to `storage/user_{id}/documents/`, store metadata
- [ ] Install: `pdfplumber`, `python-docx`, `pytesseract`
- [ ] Create `app/agents/document_processor.py`:
  - [ ] Detect file type and extract text (PDF / DOCX / TXT / image OCR)
  - [ ] Chunk text into ~500 token segments
  - [ ] Embed chunks and store in `DocumentVectors`
  - [ ] Generate document summary via LLM
  - [ ] Append summary to `memory.md`

### Retrieval Endpoints
- [ ] `GET /documents` — list user documents
- [ ] `GET /documents/search?q=passport` — semantic search
- [ ] `DELETE /documents/{id}` — delete doc and its vectors
- [ ] Test: upload PDF → embed → search by natural language

---

## 💼 STAGE 10 — LinkedIn Semi-Automation

### LinkedIn Service
- [ ] Research and set up LinkedIn data source (RapidAPI LinkedIn or Playwright scraper)
- [ ] Create `app/services/linkedin.py`:
  - [ ] `search_hiring_managers(keywords, location)`
  - [ ] `send_connection_request(contact_id, message)` with rate limit (1 per 2–5 min)
  - [ ] `fetch_job_listings(keywords, location, count=50)`

### Outreach Agent
- [ ] Create `app/agents/linkedin_outreach.py`:
  - [ ] Rank profiles by similarity to resume vectors
  - [ ] Skip contacts already in `LinkedInContacts` DB
  - [ ] Generate personalized message per contact via LLM
  - [ ] Present batch to user for approval — never auto-send
  - [ ] On approval: slow-send with delay, log each to `ActionLogs`

### Job Engine
- [ ] Create `app/agents/job_ranker.py`:
  - [ ] Fetch, embed, and rank job listings against resume vectors
  - [ ] Return top 20 matches with similarity scores
  - [ ] Generate cover letter draft per job via LLM
  - [ ] Store in `JobApplications` with status `DRAFT`

### LinkedIn Endpoints
- [ ] `GET /linkedin/outreach` — return pending batch for approval
- [ ] `POST /linkedin/outreach/approve` — trigger slow send
- [ ] `GET /linkedin/jobs` — return ranked job list
- [ ] `POST /linkedin/jobs/{id}/apply` — mark as applied

---

## 🌐 STAGE 11 — Frontend (React PWA)

### Project Init
- [ ] Init Vite React project in `frontend/`
- [ ] Install: `react-router-dom`, `axios`, `react-query`, `tailwindcss`, Vite PWA plugin
- [ ] Configure Tailwind
- [ ] Set up PWA manifest with app icons and theme color
- [ ] Register service worker

### Core Layout
- [ ] App routing: `/login`, `/register`, `/dashboard`, `/email`, `/calendar`, `/documents`, `/linkedin`, `/notifications`, `/settings`
- [ ] Persistent sidebar (desktop) + bottom nav (mobile)
- [ ] Auth context with JWT storage and silent refresh

### Pages
- [ ] **Dashboard** — today's schedule, unread notifications, pending approvals, quick actions
- [ ] **Email** — triaged inbox with urgency badges, draft preview, approve/edit/discard/send
- [ ] **Calendar** — weekly/monthly view, create event form with TZ picker, show Meet link
- [ ] **Documents** — drag-and-drop upload, document list with summaries, semantic search
- [ ] **LinkedIn** — outreach batch with approve/edit/skip, ranked job list with cover letters
- [ ] **Notifications** — list by category, mark read, dismiss
- [ ] **Settings** — Google OAuth connect, WhatsApp number, automation toggles, kill switch, persona.md editor

### PWA
- [ ] Web push subscription on login
- [ ] Test "Add to Home Screen" on iOS Safari
- [ ] Test offline graceful degradation

---

## 🛡️ STAGE 12 — Governance & Security Hardening

- [ ] All outbound actions (email send, LinkedIn message) require explicit user approval — enforce at API level
- [ ] Daily action limits per user — configurable, enforced in scheduler
- [ ] LinkedIn max connections/day enforced in scheduler job
- [ ] Global pause toggle: all jobs check `Users.global_pause` before executing
- [ ] Emergency kill switch: `POST /admin/kill` sets all users to paused
- [ ] Encrypt OAuth tokens at rest with Fernet (`cryptography`)
- [ ] Add rate limiting to all public endpoints (`slowapi`)
- [ ] Audit all DB queries — confirm every query has `WHERE user_id = :uid`
- [ ] Add HTTPS (self-signed cert locally)
- [ ] Ensure all endpoints require `get_current_user` dependency
- [ ] Every outbound action writes a row to `ActionLogs`

---

## 🔍 STAGE 13 — Testing & QA

### Backend
- [ ] Set up `pytest` + `pytest-asyncio`
- [ ] Unit tests: auth, vector store user isolation, email triage, email draft, doc chunking
- [ ] Integration tests: email fetch→triage→draft→approve→send, doc upload→embed→search, news digest→send
- [ ] Achieve >80% coverage on core modules

### Frontend
- [ ] Set up `vitest` + `@testing-library/react`
- [ ] Test auth flow and protected routes
- [ ] Test email approval flow component

### End-to-End (Playwright)
- [ ] Register new user → connect Google → fetch email → approve draft → send
- [ ] Upload document → search by natural language query

---

## 📦 STAGE 14 — Deployment & Ops

- [ ] Write `scripts/start.sh` (Docker, backend, scheduler, frontend)
- [ ] Write `scripts/stop.sh`
- [ ] Write `scripts/backup.sh` (`pg_dump` + `storage/` tar backup)
- [ ] Configure uvicorn with `--workers 1` for M1 8GB
- [ ] Set up log rotation for backend logs
- [ ] Profile memory usage under realistic load (500+ emails, 50+ docs)
- [ ] Test sequential model loading — confirm no parallel heavy inference
- [ ] Write `Dockerfile` for backend (cloud-ready)
- [ ] Write `Dockerfile` for frontend (nginx)
- [ ] Document all required environment variables in `SETUP.md`

---

## 🎯 STAGE 15 — Final Polish

- [ ] Review FastAPI auto-docs at `/docs` — ensure all endpoints documented
- [ ] Write `SETUP.md` step-by-step install guide
- [ ] Final security audit: every endpoint requires auth
- [ ] Final UX pass: mobile responsiveness on PWA
- [ ] Review all `ActionLogs` for any missed audit points
- [ ] Record demo walkthrough
- [ ] Celebrate 🎉

---

**Legend:** `[ ]` Not started · `[x]` Complete · `[~]` In progress · `[!]` Blocked

*v1.0 — Generated from TWINMIND.SPACE Architecture Blueprint*
