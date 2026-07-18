# Dhandha.com


A compliance-first B2B partner-matching platform. Sellers upload trade/compliance documents (trade license, ISO certificate, tax compliance, export permit, quality certification, etc.), the platform computes a **Regulatory Compatibility Index (RCI)** for each company, and buyers get ranked matches with an AI-generated explanation of *why* a given partner is (or isn't) a good fit. A WhatsApp bot lets sellers submit certificate photos directly from their phone instead of using the web upload form.

- **Backend**: FastAPI + Beanie/Motor (async MongoDB), JWT auth, Google Gemini (via `google-genai`) for document extraction/translation/explanations, Qdrant for a small RAG layer over trade-policy text.
- **Frontend**: React 19 + Vite, Tailwind CSS v4, Zustand (auth state), React Router v7.

---

## 1. Project layout

```
Intelligent-bazzar/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, lifespan (Mongo/Beanie/Qdrant init), CORS, /uploads static mount, /api/health
│   │   ├── core/
│   │   │   ├── config.py        # Settings (pydantic-settings), reads backend/.env
│   │   │   ├── deps.py          # get_current_user / require_admin (JWT bearer auth)
│   │   │   ├── security.py      # bcrypt password hashing, JWT create/decode
│   │   │   ├── rci_engine.py    # pure-math RCI scoring formula
│   │   │   ├── vector_db.py     # Qdrant client + sentence-transformers embedding model
│   │   │   ├── llm.py           # cached google-genai client factory
│   │   │   └── mock_sellers.py  # hardcoded seller list used by /api/match
│   │   ├── api/routes/          # one file per resource; aggregated into api_router
│   │   │   ├── auth.py          # register / login / me
│   │   │   ├── company.py       # company profile CRUD + run-compliance (RAG regulatory-fit check)
│   │   │   ├── upload.py        # document upload + AI extraction
│   │   │   ├── rci.py           # standalone RCI calculation endpoint
│   │   │   ├── match.py         # buyer-facing seller matching against mock sellers
│   │   │   ├── explanation.py   # rule-based match explanation between two companies
│   │   │   ├── admin.py         # admin-only stats/user/company listing
│   │   │   └── whatsapp.py      # Meta WhatsApp Cloud API webhook
│   │   ├── models/              # Beanie Documents (MongoDB collections)
│   │   │   ├── user.py          # users
│   │   │   ├── company.py       # companies
│   │   │   ├── document.py      # documents
│   │   │   └── whatsapp_session.py  # whatsapp_sessions (per-phone-number chat state)
│   │   ├── schemas/              # Pydantic request/response models (auth, company, rci, match, multimodal)
│   │   ├── services/
│   │   │   ├── document_compliance.py  # required-doc matching, DC (documentation completeness) score
│   │   │   ├── explanation.py          # rule-based buyer/seller match narrative
│   │   │   └── whatsapp_service.py     # WhatsApp bot orchestration (session/language/message flow)
│   │   └── ai_services/          # Gemini/Gemma LLM integration layer
│   │       ├── agent.py          # agentic vendor-evaluation loop (recompute RCI, ask for missing docs)
│   │       ├── multimodal.py     # certificate image → structured data (vision model)
│   │       ├── rag_policy.py     # Qdrant ingest + retrieval + regulatory-fit scoring
│   │       ├── localization.py   # translate outbound bot messages into the user's chosen language
│   │       └── json_utils.py     # strip markdown fences from LLM JSON output before parsing
│   ├── requirements.txt
│   ├── .env.example
│   └── uploads/                  # uploaded document files (served at /uploads, git-ignored)
│
├── frontend/
│   ├── src/
│   │   ├── main.jsx / App.jsx    # entry point, BrowserRouter, route table
│   │   ├── pages/                 # Login, Register, Dashboard, Company, Upload, Rci, Matches, Admin
│   │   ├── components/            # Layout (nav shell), ProtectedRoute/AdminRoute guards, Alert
│   │   ├── api/client.js          # fetch wrapper, attaches JWT, auto-logout on 401
│   │   └── store/authStore.js     # Zustand store (token/user), persisted to localStorage
│   ├── vite.config.js             # dev-server proxy: /api and /uploads → localhost:8000
│   └── package.json
│
└── tests/
    ├── selenium_tests.py         # written against an earlier vanilla-JS frontend — not current
    └── manual_test_cases.md      # manual QA checklist
```

---

## 2. Setup

### Prerequisites
- Python 3.11+
- Node.js v18+
- MongoDB (local or Atlas)
- Optional: a Google AI Studio API key (Gemini) for document extraction/translation/RAG features; a Qdrant instance (or leave unset to use an in-memory Qdrant); Meta WhatsApp Cloud API credentials for the WhatsApp bot

### Backend

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in secrets, see below
uvicorn app.main:app --reload --port 8000
```

API: http://localhost:8000 · interactive docs: http://localhost:8000/docs · health check: `GET /api/health`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The Vite dev server proxies `/api` and `/uploads` to `http://localhost:8000` (see `frontend/vite.config.js`), so the frontend always calls relative paths and never needs CORS in dev.

### Environment variables (`backend/.env`)

| Variable | Purpose | Default / notes |
|---|---|---|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/compliance_b2b` |
| `JWT_SECRET` | JWT signing secret | change in any real deployment |
| `JWT_EXPIRE_DAYS` | Token lifetime | `7` |
| `PORT` | Uvicorn port | `8000` in `.env.example`; `app/core/config.py`'s in-code default is `5000` — set `PORT` explicitly or pass `--port` to uvicorn |
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:5173` |
| `GEMINI_API_KEY` | Google AI Studio key | required for document extraction, RAG regulatory-fit scoring, WhatsApp message localization, and the agentic missing-document prompts. Get one at https://aistudio.google.com/apikey |
| `GEMINI_VISION_MODEL` | Model used to parse certificate images | `.env.example` suggests `gemma-3-27b-it`; confirm what your key actually has access to via `client.models.list()` |
| `GEMINI_TEXT_MODEL` | Model used for RAG/translation text calls | `.env.example` suggests `gemini-2.0-flash` |
| `QDRANT_URL` / `QDRANT_API_KEY` | Vector DB for trade-policy RAG | leave both unset to use an in-memory Qdrant instance (fine for local/dev) |
| `WHATSAPP_ACCESS_TOKEN` / `WHATSAPP_PHONE_NUMBER_ID` / `WHATSAPP_VERIFY_TOKEN` | Meta WhatsApp Cloud API | required only if you're wiring up the WhatsApp bot; see https://developers.facebook.com/apps |
| `WHATSAPP_API_VERSION` | Graph API version | `v20.0` |
| `WHATSAPP_APP_SECRET` | Enables `X-Hub-Signature-256` verification on the webhook | optional locally, **required** for any deployment reachable from the public internet |

If a feature's env vars are left blank (Gemini, Qdrant, WhatsApp), the corresponding routes will error or no-op when called — the rest of the app (auth, company profiles, manual RCI calculation, matching) works without them.

---

## 3. Core workflow

1. **Register / login** (`/api/auth`) — buyer, seller, or admin role; returns a JWT used as `Authorization: Bearer <token>` on every subsequent call.
2. **Create a company profile** (`/api/company`) — name, country, industry, trade category, contact info. One company per user.
3. **Upload compliance documents** — either through the web UI (`POST /api/upload`, multipart form) or by sending a photo to the WhatsApp bot. Uploaded files are extracted (via Gemini vision or a simulated fallback) into structured fields (issuer, issue/expiry date, certificate type) and stored as a `ComplianceDocument`.
4. **RCI calculation** — `app/core/rci_engine.py` combines four weighted sub-scores (core compliance, external/country risk, operational, macro) into a single 0–100 Regulatory Compatibility Index, with a documentation-completeness penalty and a hard legal block if the company is sanctioned (see formula below). This runs automatically after `run-compliance`/document upload flows, or on demand via `POST /api/rci/calculate`.
5. **Matching** — buyers call `GET /api/match`, which filters a fixed mock-seller list (`app/core/mock_sellers.py`) by minimum RCI and documentation-completeness thresholds.
6. **Explanation** — `GET /api/explanation/{company_id}` produces a rule-based recommendation (reasons, warnings, an overall tier) comparing the buyer's own company to the candidate.
7. **Admin** — `/api/admin/*` gives aggregate stats and full user/company listings, gated by `require_admin`.

### WhatsApp bot flow (`app/services/whatsapp_service.py`)

Meta sends inbound messages to `POST /api/whatsapp/webhook` (verified via `GET /api/whatsapp/webhook` challenge-response, and optionally HMAC-signed with `WHATSAPP_APP_SECRET`). The webhook returns 200 immediately and hands off to `process_whatsapp_message` as a background task (so Meta doesn't retry on slow LLM calls):

- First message from a new phone number → session created (`WhatsAppSession`, `whatsapp_sessions` collection) → bot sends an interactive language-selector list.
- User picks a language → session moves to `active`, all future bot replies are localized into that language (`ai_services/localization.py`).
- Once active, an image message is downloaded, parsed into structured certificate data (`ai_services/multimodal.py`), matched to a `Company` by its stored `whatsapp_number`, and run through the agentic evaluation loop (`ai_services/agent.py`), which updates the company's RCI and may ask (via WhatsApp) for whichever required document is still missing.
- Text messages (once active) get a localized prompt asking the user to send a certificate photo instead.

---

## 4. RCI formula (`app/core/rci_engine.py`)

Inputs are four groups of 0–1 sub-scores (`app/schemas/rci.py`):

- **Core**: Audit Score (`AS`), Documentation Completeness (`DC`), Regulatory Filing (`RF`), Compliance Standing (`CS`), Policy Conformance (`PC`)
- **External**: Country Risk (`CR`), Trade Law Risk (`TLR`), Market Sanctions Position (`MSP`, 0 = sanctioned), Corruption Index (`CI`)
- **Operational**: Litigation Risk (`LR`), Corporate Compliance Program (`CCP`)
- **Macro**: Financial Health (`FH`), Financial Backing (`FB`), Demand Volatility (`DV`)

```
core_score        = 0.25·AS + 0.20·DC + 0.25·RF + 0.15·CS + 0.15·PC
external_score    = 0.40·CR + 0.30·TLR + 0.10·MSP + 0.20·CI
operational_score = 0.60·LR + 0.40·CCP
macro_score       = 0.50·FH + 0.30·FB + 0.20·DV

base_composite = 0.50·core_score + 0.25·external_score + 0.15·operational_score + 0.10·macro_score

missing_doc_penalty = 0.7 + 0.3·DC          # ranges 0.7–1.0 depending on documentation completeness
legal_block         = 0 if MSP == 0 else 1  # sanctioned companies are hard-zeroed

RCI = round(100 · legal_block · missing_doc_penalty · base_composite, 2)   # 0–100
```

`DC` (Documentation Completeness) itself is computed in `app/services/document_compliance.py` as the fraction of required document types (trade license, ISO certificate, tax compliance, export permit, quality certification) that are present and currently valid (not expired).

---

## 5. API reference

Auth is JWT bearer-token only (`Authorization: Bearer <token>`) — no cookie/session fallback.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | – | Register a new user (buyer/seller/admin) |
| POST | `/api/auth/login` | – | Login, returns JWT |
| GET | `/api/auth/me` | ✓ | Current user |
| POST | `/api/company` | ✓ | Create company profile |
| GET | `/api/company/me` | ✓ | Get own company |
| PUT | `/api/company/me` | ✓ | Update own company |
| GET | `/api/company/all` | ✓ | List all companies |
| POST | `/api/company/{company_id}/run-compliance` | ✓ | RAG-based regulatory-fit check, recomputes RCI |
| POST | `/api/upload` | ✓ | Upload a compliance document (multipart) |
| GET | `/api/upload/my-documents` | ✓ | List own company's documents |
| POST | `/api/documents/extract` | ✓ | AI vision extraction of an uploaded certificate image |
| POST | `/api/rci/calculate` | ✓ | Calculate RCI from posted subcomponents |
| POST | `/api/match` | ✓ | Get matching sellers (by min RCI / min DC) |
| GET | `/api/explanation/{company_id}` | ✓ | Get match explanation vs. own company |
| GET | `/api/admin/stats` | Admin | Aggregate system stats |
| GET | `/api/admin/users` | Admin | All users |
| GET | `/api/admin/companies` | Admin | All companies, sorted by RCI |
| GET / POST | `/api/whatsapp/webhook` | – (Meta-signed) | WhatsApp Cloud API webhook (verification / inbound messages) |
| GET | `/api/health` | – | Health check |

---

## 6. User roles

| Role | Capabilities |
|---|---|
| Buyer | Create/view own company, search partners, view matches & explanations |
| Seller | Upload documents (web or WhatsApp), view own compliance status/RCI |
| Admin | All of the above + `/api/admin/*` (user/company management, system stats) |

---

## 7. Testing

- `tests/manual_test_cases.md` — manual QA checklist.
- `tests/selenium_tests.py` — written against an earlier vanilla-JS frontend; the DOM it targets no longer matches the current React app, so treat it as historical reference rather than a runnable suite.

No automated backend test suite exists yet; verify changes manually against `http://localhost:8000/docs` and the running frontend.
