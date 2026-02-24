# TWINMIND.SPACE
## Cognitive Twin System Architecture
### Full Technical Blueprint (v1.0)

---

## 1. PROJECT VISION
TWINMIND.SPACE is a personal AI operating system designed to function as a proactive digital executive assistant.
The system:
* Lives locally (M1 Mac 8GB optimized)
* Uses a local LLM for reasoning
* Integrates email, LinkedIn, Instagram, calendar, documents
* Operates via Web PWA + WhatsApp
* Supports proactive and reactive automation
* Maintains strict human-in-the-loop control
* Separates each user’s memory and data fully
* It is not a chatbot. It is a structured AI orchestration platform.

---

## 2. HIGH LEVEL SYSTEM OVERVIEW
### Architecture Layers:
* Interface Layer
* API Gateway Layer
* Orchestration Layer
* Intelligence Layer (LLM + Embeddings)
* Tool Layer (Email, Calendar, LinkedIn, etc.)
* Memory Layer (Structured + Vector + Markdown)
* Scheduler & Automation Engine
* Notification System
* Storage Layer

### Operational Modes:
* **Reactive Mode:** User-triggered.
* **Proactive Mode:** Scheduled or event-triggered.

---

## 3. USER ISOLATION MODEL
Each user has fully isolated data:

### DATABASE LEVEL:
* All tables include `user_id`.
* All vector embeddings include `user_id` metadata.

### FILE SYSTEM LEVEL:
* `storage/user_{id}/`
    * `persona.md`
    * `memory.md`
    * `activity_log.md`
    * `documents/`
    * `email_cache/`

### VECTOR DATABASE LEVEL:
* Email, Document, Resume, and Conversation vectors filtered by `user_id`.
* NO cross-user contamination allowed.

---

## 4. MEMORY ARCHITECTURE
### 4.1 Structured Memory (PostgreSQL)
* **Tables:** Users, OAuthTokens, Tasks, ScheduledJobs, Notifications, DocumentsMetadata, EmailMetadata, LinkedInContacts, JobApplications, ActionLogs.
* **Purpose:** State management, Scheduling, Auditing, Permissions.

### 4.2 Vector Memory (pgvector)
* **Tables:** EmailVectors, DocumentVectors, ResumeVectors, ConversationVectors, NewsVectors.
* **Schema:** `id`, `user_id`, `embedding`, `source_type`, `source_id`, `metadata` (JSON).
* **Purpose:** Semantic search, Style learning, Similarity ranking.

### 4.3 Narrative Memory (Markdown Files)
* **persona.md:** Career goals, Tone, Industry, Skills, Preferences.
* **memory.md:** High-level knowledge, Summaries, Recurring themes, Maps.
* **activity_log.md:** Past decisions, Major actions, System summaries.
* **Note:** Markdown acts as a routing layer before vector search.

---

## 5. ORCHESTRATION MODEL
**Central Orchestrator:** Handles multi-step logic and confirms actions.
**State Machine:**
`IDLE` -> `MONITORING` -> `PROCESSING_REQUEST` -> `AWAITING_CONFIRMATION` -> `EXECUTING_ACTION` -> `PAUSED` -> `ERROR_STATE`.

---

## 6. EMAIL INTELLIGENCE SYSTEM
* **Initial Setup:** OAuth auth -> Fetch last 50 emails -> Extract tone/structure -> Build style profile -> Update `persona.md`.
* **Monitoring:** 30–60 min heartbeat.
* **Rule-filtering:** Check for meetings, invoices, interviews, deadlines.
* **Urgency:** If urgent -> WhatsApp alert + Push notification.
* **Meeting Detection:** Extract time -> Ask user: Schedule/Remind/Decline.
* **Email Drafting:** Retrieve top similar vectors -> Generate draft -> Show preview -> Await confirmation -> Send only after approval.

---

## 7. CALENDAR + MEETING SYSTEM
* **Capabilities:** Create event/link, Share link, Modify/Cancel event.
* **Flow:** User request -> Parse intent -> Confirm TZ -> Create event -> Generate link -> Ask to share (Email/WhatsApp).
* ***Never auto-share without confirmation.***

---

## 8. LINKEDIN AUTOMATION SYSTEM
* **9 AM Routine:** Search hiring managers -> Rank via resume similarity -> Generate personalized draft -> Present batch for approval -> Send slowly.
* **Job Engine:** Fetch jobs -> Rank via vector match -> Generate cover letters -> Present top 20 -> Manual application only.
* **Prevention:** Store `contact_id` in DB; track connection status.

---

## 9. NEWS INTELLIGENCE ENGINE
* **Daily 9 AM:** Read `persona.md` -> Identify interests -> Fetch news -> Embed & rank -> Select top 10-20 -> Summarize -> Send digest.
* **Storage:** Track sent article IDs to avoid duplicates.

---

## 10. DOCUMENT PROCESSING PIPELINE
* **Upload Flow:** Store local -> Extract (Parse/OCR) -> Chunk -> Embed -> Store vectors -> Update `memory.md`.
* **Retrieval:** "Where is my passport?" -> Search metadata -> Provide path.

---

## 11. SCHEDULER / HEARTBEAT ENGINE
* Runs every X minutes. Checks emails, calendar, tasks, docs, and LinkedIn.
* **Rules-first approach:** LLM used only when necessary.
* **Cooldown:** Prevent repeated alerts/respect spacing.

---

## 12. NOTIFICATION SYSTEM
* **Channels:** Web Push, WhatsApp, In-App.
* **Rules:** No spam, Deduplicate, Cooldown window, Urgency threshold.
* **Categories:** Urgent, Reminder, Digest, Confirmation Required.

---

## 13. AUTOMATION GOVERNANCE
**Mandatory Controls:**
* Outbound approval required
* Daily automation limits
* LinkedIn rate limiting
* Job application approval
* Global pause toggle / Emergency kill switch
* Action logs saved (`user_id`, `type`, `timestamp`, `status`, `target`).

---

## 14. RESOURCE MANAGEMENT (8GB M1)
* Sequential Model Loading: Unload vision model before loading LLM.
* Avoid parallel heavy inference.
* Limit batch sizes and cache embeddings.
* Markdown routing before vector search to reduce compute.

---

## 15. SECURITY MODEL
* OAuth token encryption (No plaintext).
* Access token refresh handling.
* Per-user folder isolation.
* API rate limiting and Action audit trails.

---

## 16. FUTURE SCALABILITY
* **Phase 1:** Single user local.
* **Phase 2:** Multi-user isolation, Containerization.
* **Phase 3:** Cloud vector DB, Object storage, Distributed scheduler.
* **Phase 4:** Multi-agent (Email, Career, Network, Doc, News Agents).

---

## 17. BUILD PHASE STRATEGY
1.  **PHASE 1:** Auth, Isolation, Vector storage, Email ingestion, Draft system.
2.  **PHASE 2:** Scheduler, Urgency detection, Meeting detection.
3.  **PHASE 3:** Calendar/Meet creation, Notification system.
4.  **PHASE 4:** News engine, Persona learning.
5.  **PHASE 5:** LinkedIn semi-automation, Job ranking.
6.  **PHASE 6:** Advanced proactive intelligence.
7.  **PHASE 7:** End-of-Day Finance Audit & Checkbox confirmation system.

---

## 18. SYSTEM PHILOSOPHY
* Assist, not override.
* Suggest, not act blindly.
* Learn gradually.
* Respect platform limits.
* Maintain user control.
* Be explainable and auditable.

---

## PROJECT SETUP STRUCTURE
```text
twinmind-space/
├── backend/                # FastAPI Root
│   ├── app/
│   │   ├── core/           # Security, Config, LLM Init
│   │   ├── api/            # Endpoints (v1)
│   │   ├── agents/         # LangGraph workflows (Email, LinkedIn, etc.)
│   │   ├── memory/         # Logic for pgvector + Markdown retrieval
│   │   ├── services/       # Integrations (Gmail API, LinkedIn Scraper)
│   │   └── worker/         # Proactive "Heartbeat" tasks (APScheduler)
│   ├── migrations/         # DB Schema versions
│   └── storage/            # User-isolated narrative memory (.md files)
├── frontend/               # React PWA
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/          # Custom hooks for state management
│   │   └── services/       # API calling logic
│   └── public/             # PWA manifest, service workers
├── scripts/                # Setup & Model loading scripts
└── docker-compose.yml      # To run PostgreSQL + Redis locally