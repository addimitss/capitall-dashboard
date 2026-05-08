# AML Risk Dashboard

Production-ready, Excel-driven AML/risk analytics dashboard with an embedded AI assistant.

## Highlights

- **FastAPI + React (Vite)** — clean, modular, deployment-ready.
- **Generic by default** — adapts to any uploaded workbook; sidebar tabs auto-generated from sheet names.
- **AML-aware bonus features** — Overview tab with workbook-wide KPIs, alert banners (High/Critical customer count, KYC threshold, cross-sheet mismatches), and a top-10 risk leaderboard.
- **Cross-sheet reconciliation** — `Risk Rating Summary` vs `Aggregation Check` mismatch detection, surfaced in the UI **and** auto-injected into the chatbot when the user asks about mismatches/discrepancies.
- **AI chatbot** — Groq today, Bedrock-ready abstraction for tomorrow. Context-aware: knows the active sheet and the entire workbook digest.
- **Optional auth** — flip `AUTH_ENABLED=true` for HMAC-signed bearer tokens with role-based gating (admin/analyst/viewer). Demo accounts included.
- **Optional strict schema validation** — flip `STRICT_SCHEMA=true` to reject any workbook that doesn't match the canonical 9-sheet AML format.
- **Strict color theme** — black `#000000`, dark green `#023020`, blue `#0000FF`, steel blue `#7393B3`, bronze `#CC7722` on white. No off-palette colors anywhere.
- **Dockerised** — `docker compose up` brings the whole stack up.
- **Tested** — backend covered by pytest (services + HTTP integration).

## Run locally (one command)

```bash
./start-dev.sh
```

Sets up a Python venv, installs deps, copies `.env`, and starts both backend (`:8000`) and frontend (`:5173`). Add your `GROQ_API_KEY` to `backend/.env` before chatting.

### Or manually

#### 1. Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                # add GROQ_API_KEY
uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend
```bash
cd frontend
npm install
npm run dev
```

App at <http://localhost:5173>.

## Run with Docker

```bash
cp backend/.env.example backend/.env   # add GROQ_API_KEY
docker compose up --build
```

App at <http://localhost:8080>, API at <http://localhost:8000>.

## Auth (optional)

```ini
# backend/.env
AUTH_ENABLED=true
AUTH_SECRET=replace-with-32+char-random-secret
```

Demo accounts (replace with real DB lookup in production):

| Username | Password | Role | Permissions |
|---|---|---|---|
| `admin` | `admin123` | admin | full |
| `analyst` | `analyst123` | analyst | upload + read |
| `viewer` | `viewer123` | viewer | read-only (no upload, no clear) |

## Strict schema mode (optional)

```ini
STRICT_SCHEMA=true
```

Rejects uploads that don't include all of: *Risk Rating Summary, Customer Master, Transactions, KYC Documents, Network & Devices, Trading Activity, Adverse Media, Aggregation Check* (with the canonical required columns each). Returns a clear 400 error with the missing fields. With strict mode off (default), missing fields are returned as warnings and the dashboard adapts.

## API

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Liveness + provider/auth status |
| `GET` | `/api/auth/config` | Public: tells frontend if auth is enabled |
| `POST` | `/api/auth/login` | Login → bearer token |
| `GET` | `/api/auth/me` | Current user |
| `POST` | `/api/upload` | Upload .xlsx workbook |
| `GET` | `/api/workbook` | Current workbook metadata |
| `DELETE` | `/api/workbook` | Clear in-memory workbook |
| `GET` | `/api/sheets/{name}/meta` | Column metadata |
| `GET` | `/api/sheets/{name}/summary` | Cards + auto-generated charts |
| `POST` | `/api/sheets/{name}/data` | Filtered/sorted/paginated rows |
| `GET` | `/api/insights/overview` | Cross-sheet KPIs, alerts, top risks |
| `GET` | `/api/insights/mismatches` | Risk Summary vs Aggregation Check reconciliation |
| `POST` | `/api/chat` | Context-aware LLM Q&A grounded in the workbook |

Full Swagger docs at `/docs` when the backend is running.

## Tests

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

Covers: workbook parsing, query/filter/sort/paginate, schema validation (loose + strict), cross-sheet insights & mismatch detection, auth token round-trip, full HTTP integration flow.

## Switching from Groq → Bedrock

1. `pip install boto3` and add AWS credentials.
2. Implement `BedrockProvider.chat()` in `backend/app/services/llm/bedrock_provider.py` (stub provided).
3. Set `LLM_PROVIDER=bedrock` in `.env` — no other code changes needed.

## Project layout

```
aml-dashboard/
├── backend/
│   ├── app/
│   │   ├── main.py                       # FastAPI + CORS + routers
│   │   ├── config.py                     # pydantic-settings
│   │   ├── state.py                      # Thread-safe in-memory workbook store
│   │   ├── models/schemas.py
│   │   ├── routers/
│   │   │   ├── auth.py                   # /api/auth/*
│   │   │   ├── excel.py                  # /api/upload, /api/sheets/*
│   │   │   ├── insights.py               # /api/insights/overview, /mismatches
│   │   │   └── chat.py                   # /api/chat
│   │   └── services/
│   │       ├── excel_service.py          # parse/summarise/filter/chart/context
│   │       ├── insights_service.py       # cross-sheet KPIs + mismatch detection
│   │       ├── schema.py                 # canonical AML format validation
│   │       ├── auth.py                   # HMAC tokens, RBAC
│   │       └── llm/                      # provider abstraction
│   │           ├── base.py
│   │           ├── factory.py
│   │           ├── groq_provider.py
│   │           └── bedrock_provider.py
│   ├── tests/test_app.py                 # pytest: services + HTTP
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── pytest.ini
│   ├── Dockerfile
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.jsx                       # Layout + auth + routing
│   │   ├── theme.js                      # Approved palette
│   │   ├── styles.css                    # Enterprise styling
│   │   ├── api/client.js                 # Axios + bearer-token interceptor
│   │   ├── hooks/useSheets.js
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Overview.jsx              # Cross-sheet KPIs, alerts, top risks
│   │   │   └── SheetView.jsx
│   │   └── components/
│   │       ├── Sidebar.jsx
│   │       ├── UploadButton.jsx
│   │       ├── SummaryCards.jsx
│   │       ├── Charts.jsx                # Recharts (bar/line/pie)
│   │       ├── DataTable.jsx
│   │       ├── Chatbot.jsx               # Floating drawer
│   │       └── EmptyState.jsx
│   ├── nginx.conf                        # Used by the frontend container
│   ├── Dockerfile
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── docker-compose.yml
├── start-dev.sh
└── README.md
```

## Notes for production

- Workbook is stored in-process. For multi-worker deployments swap `state.py` for Redis or a DB.
- Replace `auth.DEMO_USERS` with a real user store (DB / OIDC / Auth0 / Cognito).
- For very large files, increase `MAX_UPLOAD_MB` and consider streaming parse.
- Rate-limit `/api/chat` and stream Groq SSE responses for better UX.

## Verified against the supplied workbook

End-to-end smoke against `Customer_Underlying_Data_200.xlsx` (200 customers, 72,220 transactions, 9 sheets):

| Metric | Value |
|---|---|
| Customers | 200 |
| Transactions | 72,220 |
| Total volume | ₹4,037,299,315 (~₹403 Cr) |
| Cash transaction % | 26.3% |
| Offshore transactions | 1,696 |
| Adverse media hits | 483 |
| Rating mix | Low 77 · Medium 63 · High 41 · Critical 19 |
| KYC verified | 82.7% (triggers medium alert — threshold 90%) |
| High/Critical alert | 60 customers (top score 92.4 — CUST058 in UAE) |
| Auto-generated overview charts | Rating distribution · Avg AML by country · Monthly volume trend |
| Cross-sheet reconciliation | 0 mismatches (the workbook is internally consistent) |
