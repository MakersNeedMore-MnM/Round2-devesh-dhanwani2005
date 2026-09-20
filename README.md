# Round2-devesh-dhanwani2005
Repository for team devesh.dhanwani2005 for Round 2

## Project: CyberSentinel

AI-powered cyber incident investigation and response platform.

CyberSentinel does **not** exist to dump raw alerts. It turns fragmented security events into a single, explainable incident through:

**Observe → Detect → Investigate → Reason → Plan → Act → Verify**

This repository is a production-shaped MVP for a **defensive** SOC (Security Operations Center) demonstration. Every response action is **simulated** — it does not disable real accounts, isolate real hosts, or run destructive commands.

## Live Demo

- Frontend: `<add your Vercel/Netlify URL here>`
- Backend API health check: `<add your Render URL here>/health`

## Demo Login Credentials

| Role | Email | Password |
| --- | --- | --- |
| Analyst | `sofia.alvarez@cybersentinel.demo` | `DemoAnalyst!123` |
| Senior Analyst | `daniel.okonkwo@cybersentinel.demo` | `DemoSenior!123` |
| Admin | `maya.chen@cybersentinel.demo` | `DemoAdmin!123` |

## Features

- JSON/CSV log ingestion and field normalization
- Configurable rule-based detection
- Time-window correlation into one incident
- Transparent weighted risk scoring
- Provider-independent AI investigation (OpenAI-compatible + heuristic fallback)
- Human approval for high-impact actions
- Simulated containment and verification
- Audit trail persisted in Supabase PostgreSQL
- Dark SOC dashboard (React + Vite + Tailwind)
- Demo Attack workflow that produces incident **CS-1042** (Possible Account Compromise)

## Architecture

```
Frontend (React + Vite + Tailwind)
        ↓  REST (JWT)
FastAPI
        ↓
Detection / Correlation / Risk engines
        ↓
AI investigation service (read-only tools)
        ↓
Supabase PostgreSQL
        ↓
Simulated response engine
        ↓
Verification + audit_logs
```

Secrets such as `SUPABASE_SERVICE_ROLE_KEY` and `AI_API_KEY` live **only** on the backend.

## Tech Stack

| Layer | Stack |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, React Router, Axios, Recharts, Lucide |
| Backend | Python, FastAPI, Pydantic, Uvicorn, python-dotenv, httpx |
| Database | Supabase PostgreSQL |
| AI | OpenAI-compatible HTTP API via env vars, with heuristic fallback |
| Auth | Supabase Auth **or** `DEMO_MODE` analyst login |
| Hosting | Render (backend), Vercel/Netlify (frontend) |

## Folder Structure

```
cybersentinel/
├── frontend/                 # SOC console
├── backend/                  # FastAPI API
├── database/                 # schema.sql, seed.sql
├── sample-data/              # attack / normal / suspicious logs
├── docker-compose.yml
├── Dockerfile
├── render.yaml
└── README.md
```

## Database Setup (Supabase)

1. Create a Supabase project.
2. Open **SQL Editor → New query**.
3. Paste and run `database/schema.sql`.
4. Paste and run `database/seed.sql`.
5. Confirm tables exist: `profiles`, `security_logs`, `assets`, `incidents`, `incident_events`, `investigations`, `recommendations`, `response_actions`, `threat_intelligence`, `audit_logs`, `detection_rules`.

Row Level Security is **enabled**. The anon key cannot read incident tables directly — the API uses the **service role** key server-side.

## Environment Variables

### Backend (`backend/.env`)

```
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_ANON_KEY=
SUPABASE_JWT_SECRET=
AI_API_KEY=
AI_MODEL=gpt-4o-mini
AI_BASE_URL=https://api.openai.com/v1
AI_PROVIDER=openai_compatible
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
DEMO_MODE=true
DEMO_JWT_SECRET=change-me-in-production
DEMO_ANALYST_EMAIL=sofia.alvarez@cybersentinel.demo
DEMO_ANALYST_PASSWORD=DemoAnalyst!123
CORRELATION_WINDOW_MINUTES=15
MAX_UPLOAD_BYTES=2097152
```

### Frontend (`frontend/.env`)

```
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Copy from the `.env.example` files in each folder. **Never commit real secrets** — `.env` is already excluded via `.gitignore`.

## Local Development

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # then fill in the Supabase values
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- API docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open http://localhost:5173

### Docker (API only)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

## Demo Workflow

1. Sign in with one of the demo accounts above.
2. Dashboard loads live stats from Supabase via FastAPI.
3. Click **Load Demo Attack**.
4. Backend inserts a sample attack chain (failed logins → success → unusual location → privilege escalation → large outbound transfer).
5. Detection and correlation combine these into **one** incident: **CS-1042 — Possible Account Compromise**.
6. Risk engine sums rule weights (default **91/100 → CRITICAL**).
7. AI investigation runs (live model if `AI_API_KEY` is set; otherwise a labeled heuristic fallback).
8. Open the incident to review the timeline, evidence, risk factors, and recommendations.
9. Click **Approve** on a response action — a simulated result is stored and an audit log entry is written.
10. Verification checks the outcome; on success the incident moves to **contained**, then can be **marked resolved**.

## Deployment

- **Backend**: deployed on Render, root directory `backend`, start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Frontend**: deployed on Vercel/Netlify, root directory `frontend`, build command `npm run build`, output directory `dist`, with `VITE_API_BASE_URL` set to the live backend URL at build time.
- CORS on the backend (`CORS_ORIGINS`, `FRONTEND_URL`) is updated to include the deployed frontend's URL.

## Security Considerations

- No hardcoded secrets in source code
- Backend validation for log uploads (size limit, JSON/CSV parsing only)
- Uploaded logs are **never** executed as code or shell commands
- Role checks on protected routes (`analyst`, `senior_analyst`, `admin`)
- Row Level Security remains enabled; the service-role key is backend-only
- High-impact response actions require human analyst approval
- The response engine is fully simulated — no real systems are affected

## License / Use

Defensive demonstration only, built for Round 2 of the hackathon. Do not point this response engine at production identity providers without a separate, reviewed integration.
