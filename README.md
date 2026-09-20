# CyberSentinel

AI-powered cyber incident investigation and response platform.

CyberSentinel does **not** exist to dump raw alerts. It turns fragmented security events into a single, explainable incident through:

**Observe → Detect → Investigate → Reason → Plan → Act → Verify**

This repository is a production-shaped MVP for a **defensive** SOC demonstration. Every response action is **simulated**. It does not disable real accounts, isolate real hosts, or run destructive commands.

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

## Tech stack

| Layer | Stack |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, React Router, Axios, Recharts, Lucide |
| Backend | Python, FastAPI, Pydantic, Uvicorn, python-dotenv, httpx |
| Database | Supabase PostgreSQL (not SQLite) |
| AI | OpenAI-compatible HTTP API via env vars, with heuristic fallback |
| Auth | Supabase Auth **or** `DEMO_MODE` analyst login |

## Folder structure

```
cybersentinel/
├── frontend/                 # SOC console
├── backend/                  # FastAPI API
├── database/                 # schema.sql, seed.sql
├── sample-data/              # attack / normal / suspicious logs
├── docker-compose.yml
├── Dockerfile
└── README.md
```

## Database setup (Supabase)

1. Create a Supabase project.
2. Open **SQL → New query**.
3. Paste and run [`database/schema.sql`](database/schema.sql).
4. Paste and run [`database/seed.sql`](database/seed.sql).
5. Confirm tables: `profiles`, `security_logs`, `assets`, `incidents`, `incident_events`, `investigations`, `recommendations`, `response_actions`, `threat_intelligence`, `audit_logs`, `detection_rules`.

Row Level Security is **enabled**. The anon key cannot read incident tables. The API uses the **service role** key server-side and writes audit records.

### Authentication options

**A. Demo login (local / demo environments)**

Set `DEMO_MODE=true` on the backend. Sign in with:

- Email: `sofia.alvarez@cybersentinel.demo`
- Password: `DemoAnalyst!123` (change this in production)

**B. Supabase Auth (production)**

1. Authentication → Providers → Email enabled.
2. Create users (emails can match seed profiles).
3. Set `SUPABASE_JWT_SECRET` from Project Settings → API (JWT secret) so FastAPI can verify access tokens.
4. Optionally set user metadata `role` to `analyst`, `senior_analyst`, or `admin`.

If Auth user IDs differ from seeded `profiles.id`, update `profiles` so `id` matches `auth.users.id`, or rely on email lookup.

## Environment variables

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
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
```

`VITE_SUPABASE_*` is optional. The console talks to FastAPI, not directly to privileged tables.

Copy from `.env.example` files. **Never commit real secrets.**

## Local development

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env   # then fill values
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### Docker (API)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

## Demo workflow

1. Sign in.
2. Dashboard loads stats from Supabase via FastAPI.
3. Click **Load Demo Attack**.
4. Backend inserts the 10:31–10:36 sample chain (15 failed logins, success, unusual location, privilege escalation, large outbound transfer).
5. Normalization, detection, and correlation create **one** incident: **CS-1042 — Possible Account Compromise**.
6. Risk engine sums configured rule weights (default **91/100** → **CRITICAL**).
7. AI investigation runs (live model if `AI_API_KEY` is set; otherwise a labeled heuristic fallback that still returns structured JSON and **does not invent malware, CVEs, or threat actors**).
8. Confidence is approximately **92%** when the full chain is present.
9. Open the incident. Review timeline, evidence, risk factors, impact, recommendations.
10. Click **Approve** on a response. A sandbox result is stored (`ACTIVE` → `DISABLED` for disable-account). An `audit_logs` row is written.
11. Verification checks for new successful logins after simulated disable. On success the incident becomes **contained**.
12. **Mark resolved** after containment.
13. Refresh the browser: data remains in Supabase.
14. **Reset Demo** deletes only `is_demo` rows and incident **CS-1042**.

## API documentation

Swagger UI is served at `/docs` in development.

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Health |
| POST | `/api/auth/login` | Login |
| GET | `/api/auth/me` | Current analyst |
| GET | `/api/dashboard/stats` | SOC stats |
| GET/POST | `/api/logs` | List / ingest |
| POST | `/api/logs/upload` | JSON/CSV upload |
| GET | `/api/incidents` | List incidents |
| GET | `/api/incidents/{id}` | Incident detail + timeline |
| POST | `/api/incidents/{id}/investigate` | AI investigation |
| GET | `/api/incidents/{id}/evidence` | Evidence pack |
| GET | `/api/incidents/{id}/recommendations` | Recommended actions |
| POST | `/api/incidents/{id}/actions/{action_id}/approve` | Approve + simulate |
| POST | `/api/incidents/{id}/actions/{action_id}/reject` | Reject |
| POST | `/api/incidents/{id}/verify` | Verification |
| GET | `/api/incidents/{id}/report/json` | JSON report |
| GET | `/api/incidents/{id}/report/pdf` | PDF report |
| GET | `/api/assets` | Assets |
| GET/POST | `/api/threat-intel` | Sample indicators |
| POST | `/api/demo/load` | Load demo attack |
| POST | `/api/demo/reset` | Reset demo data |

## Risk model

Matched unique detection-rule weights are summed and clamped to 0–100.

Default demo weights:

| Indicator | Points |
| --- | --- |
| Failed login burst | +12 |
| Successful login after failures | +14 |
| Unusual location | +18 |
| Privilege escalation | +20 |
| Large outbound transfer | +27 |
| **Total** | **91** |

Bands: 0–30 LOW · 31–60 MEDIUM · 61–80 HIGH · 81–100 CRITICAL.

Factors are stored on the incident and shown in the UI.

## AI behavior

- Input is a **structured evidence pack**, not a database dump.
- Output is JSON with classification, scores, summary, reasoning, evidence, attack pattern, impact, recommendations.
- FACTS are separated from ASSESSMENT.
- If `AI_API_KEY` is missing or the provider fails, the heuristic investigator still works and the UI labels the fallback.
- LLM output is treated as untrusted data. It cannot execute tools that change systems.

## Deployment

### 1–4. Supabase

Create project, run `schema.sql`, run `seed.sql`, configure Auth (or keep `DEMO_MODE` only for non-prod).

### 5. Backend env

Set all backend variables on Render, Railway, Fly, or similar. Start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Root directory: `backend` **or** use the repository `Dockerfile`.

### 6. Frontend (Vercel / Netlify)

- Build: `npm run build` in `frontend`
- Output: `dist`
- Set `VITE_API_BASE_URL` to the public API origin **at build time**
- SPA fallback is in `vercel.json` / `netlify.toml`

### 7. CORS

Add the frontend origin to `CORS_ORIGINS` and `FRONTEND_URL`.

### 8. Production checks

- `GET /health` returns supabase `ok`
- Login works
- Load Demo Attack creates CS-1042
- Approve writes `response_actions` + `audit_logs`
- No service-role key in frontend bundle

## Security considerations

- No hardcoded secrets
- Backend validation for logs and uploads (size limit, JSON/CSV parse only)
- Uploaded logs are **never** executed as code or shell
- Role checks on protected routes
- RLS remains enabled; service role is backend-only
- High-impact actions require a human analyst
- Response engine is simulated

## External API keys required

| Key | Required to run core demo? | Purpose |
| --- | --- | --- |
| `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` | **Yes** | PostgreSQL persistence |
| `SUPABASE_ANON_KEY` | For Supabase Auth login | Browser/auth client |
| `SUPABASE_JWT_SECRET` | For verifying Supabase JWTs | API auth |
| `AI_API_KEY` | No (fallback exists) | LLM investigation |

## How the workflow is wired

1. **Frontend** sends JWT on every API call (`src/services/api.ts`).
2. **FastAPI** authenticates the analyst, then writes/reads through the Supabase service client.
3. **Ingestion** normalizes fields into `security_logs.raw_data` plus canonical columns.
4. **Detection** loads `detection_rules` and emits findings.
5. **Correlation** groups by user/asset/IP inside `CORRELATION_WINDOW_MINUTES` (default 15).
6. **Risk** stores score + factor list on `incidents`.
7. **AI** gathers related logs, asset, and sample threat intel, then returns structured JSON into `investigations`.
8. **Recommendations** are persisted; **Approve** creates a simulated `response_actions` row and audit event.
9. **Verify** looks for post-disable successful logins and moves status to `contained` when clean.
10. Polling (~8s) keeps the console updated; the schema is ready for Supabase Realtime later.

## Future improvements

- Native Supabase Realtime subscriptions on incidents and logs
- Additional log source connectors (syslog, cloud trail)
- Playbook versioning and dual-control approvals
- Optional live threat-intel provider behind the same interface
- Fine-grained RBAC (only senior analysts approve isolation)

## License / use

Defensive demonstration only. Do not point this response engine at production identity providers without a separate, reviewed integration.
