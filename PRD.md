# Product Requirement Document (PRD)

## Project Name: Intelligent Bazaar (Compliance-First B2B Partner Matching)
**Document Version:** 1.0.0  
**Status:** Approved / Development Blueprint (Hackathon Edition)  

---

## 1. Introduction & Product Vision

### 1.1 Problem Statement
In the modern international trade landscape, verifying cross-border business-to-business (B2B) partners for regulatory adherence, anti-corruption standards, legal compliance, and quality frameworks is a slow, manual, and error-prone process. Small and Medium Enterprises (SMEs) frequently struggle with complex upload portals, while procurement officers waste valuable cycle times manually checking certificates, trade licenses, and country risk indexes. 

### 1.2 The Vision
**Intelligent Bazaar** is a modern B2B partner-matching platform built on a compliance-first philosophy. Instead of listing suppliers based purely on cost or marketing, it uses automated data extraction, a rigorous, unalterable mathematical scoring model, and conversational AI to verify, score, and rank global suppliers instantly. 

### 1.3 The Core Value Loop
1. **Low Friction Onboarding:** Sellers snap pictures of their trade licenses, ISO certificates, or tax compliances on their phones and send them directly via a localized **WhatsApp Bot**, or use a desktop web app.
2. **Deterministic Vetting (RCI Engine):** The platform parses these documents via computer vision, checks background international trade policies via an embedded RAG layer, and passes metrics into a strict mathematical formula called the **Regulatory Compatibility Index (RCI)**.
3. **Intelligent Match & Explanations:** Buyers receive instantly ranked suppliers alongside an interactive AI summary explaining compliance scores, risk indicators, and simulated "what-if" improvement impacts.

```
[Seller Certifications] ──> [AI Multi-Modal Extraction] ──> [Vector DB RAG Policy Vetting]
                                                                        │
                                                                        ▼
[Ranked AI Matches] <── [Interactive Analytics] <── [Deterministic RCI Math Engine (0-100)]
```

---

## 2. Core Target User Personas & Roles

*   **The Buyer (Sourcing & Procurement Officer):** Wants to find reliable, low-risk B2B suppliers matching a specified product category without falling into regulatory traps or onboarding sanctioned vendors.
*   **The Seller (Supplier / Small Business Owner):** Requires an easy, quick way to declare certifications—often using a mobile interface—and wants actionable insights on how to improve their marketplace trust and search visibility.
*   **The Platform Admin (Compliance Manager):** Needs broad visibility over high-risk vendor trends, aggregate platform stats, and a clean, conversational query tool to extract filtered system records quickly.

---

<!-- ## 3. Product Architecture & Full Directory Layout

The codebase is organized into a clean, decoupled structure: an asynchronous Python backend built on FastAPI and a highly optimized React 19 frontend compiled via Vite.

```
Intelligent-bazzar/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI instantiation, Lifespan lifecycle management, CORS & static mount
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic-Settings environment manager reading backend/.env
│   │   │   ├── deps.py              # JWT Bearer dependency injection (get_current_user, require_admin)
│   │   │   ├── security.py          # Passlib bcrypt password hashing & PyJWT state mechanics
│   │   │   ├── rci_engine.py        # Pure mathematical, deterministic RCI scoring execution logic
│   │   │   ├── vector_db.py         # Qdrant client factory + local sentence-transformer pipeline
│   │   │   ├── llm.py               # Google Gemini / Gemma-3 client instantiation factory
│   │   │   └── mock_sellers.py      # Hardcoded seed data for initial buyer matching mechanics
│   │   ├── api/routes/              # Modularized API routers aggregated inside api_router
│   │   │   ├── auth.py              # User onboarding, registration, login, and current token mapping
│   │   │   ├── company.py           # Corporate profiles CRUD + RAG-driven compliance analysis
│   │   │   ├── upload.py            # Local directory multi-part upload handling & image extraction
│   │   │   ├── rci.py               # Sandbox routing for dynamic RCI testing & simulations
│   │   │   ├── match.py             # Match engine querying verified seller lists against parameters
│   │   │   ├── explanation.py       # Algorithmic compliance narrative generator
│   │   │   ├── admin.py             # Conversational data filters & platform admin routes
│   │   │   └── whatsapp.py          # Meta Cloud API Webhook (GET confirmation / POST message processing)
│   │   ├── models/                  # Beanie ODM Documents (MongoDB Collections)
│   │   │   ├── user.py              # Account credentials, roles, and profiles
│   │   │   ├── company.py           # Corporate metadata, parsed variables, and actual calculated RCI
│   │   │   ├── document.py          # Individual compliance document files, states, and expirations
│   │   │   └── whatsapp_session.py  # Interactive per-number persistent state machine trackers
│   │   ├── schemas/                 # Pydantic models enforcing request/response typing
│   │   ├── services/                # Core domain business logic orchestrations
│   │   │   ├── document_compliance.py # Required document checklist validation & DC score calculators
│   │   │   ├── explanation.py       # Structured narrative compilers for partner profiles
│   │   │   └── whatsapp_service.py  # Asynchronous background loop for processing WhatsApp bots
│   │   └── ai_services/             # Advanced Gemma / Gemini Extended Layer
│   │       ├── agent.py             # Conversational ReAct (Reasoning & Acting) Policy Agent loop
│   │       ├── multimodal.py        # Vision parsing converting image bytes to structured document JSON
│   │       ├── rag_policy.py        # Ingestion, vector embedding, and similarity search over Qdrant
│   │       ├── localization.py      # Multi-language translation map generator for active responses
│   │       ├── analytics_tools.py   # Admin tool-calling definitions linking strings to DB operations
│   │       ├── cross_doc_audit.py   # System-wide cross-document data consistency and fraud checker
│   │       ├── simulator.py         # "What-if" score prediction engine
│   │       └── json_utils.py        # String sanitization utility separating raw text from LLM JSON blocks
│   ├── requirements.txt
│   ├── .env.example
│   └── uploads/                     # Git-ignored workspace folder for multi-format document tracking
├── frontend/
│   ├── src/
│   │   ├── main.jsx                 # Client context bootstrapping and tailwind configurations
│   │   ├── App.jsx                  # Single Page Application core route structure & security wrappers
│   │   ├── pages/                   # Login, Register, Dashboard, Company, Upload, Rci, Matches, Admin
│   │   ├── components/              # Global Nav frames, route protection guards, feedback alerts
│   │   ├── api/client.js            # Fetch abstraction injection layers handling tokens and auto-401s
│   │   └── store/authStore.js       # Zustand persistent authentication store
│   ├── vite.config.js               # Proxy setup directing /api and /uploads to port 8000
│   └── package.json
└── tests/
    ├── selenium_tests.py            # Historical legacy automated testing suite
    └── manual_test_cases.md         # Full operational verification checklist
```

--- -->

## 4. Feature Set & Detailed Component Breakdowns

### 4.1 Automated Onboarding & Multi-Modal Processing
*   **Web Portal Upload (`/api/upload`):** Traditional file ingestion accepting image types and documents, writing artifacts to local storage, and initializing extraction events.
*   **WhatsApp Intake Node (`/api/whatsapp/webhook`):** Connects to the Meta Cloud API to listen for asynchronous messages.
    *   *Session Router:* If a new number messages the system, it records state in `whatsapp_sessions` and sends a language option menu.
    *   *Localization Node:* Translates out-of-band communications into Spanish, Arabic, Hindi, French, or English based on selection.
    *   *Vision Processing (`ai_services/multimodal.py`):* Sends image inputs directly to the vision model (`gemma-3-27b-it`) to extract key data (Issuer name, Issue/Expiry Dates, Certificate Class) as structured JSON.

### 4.2 The Pure-Math Regulatory Compatibility Index (RCI) Engine
To maintain user trust, the overall compliance score uses a strict mathematical formula instead of open-ended AI estimations. Sub-scores are graded between $0.0$ and $1.0$ across four pillars:

1. **Core Compliance ($	ext{Score}_{	ext{core}}$):**
   $$	ext{Score}_{	ext{core}} = 0.25 \cdot 	ext{AS} + 0.20 \cdot 	ext{DC} + 0.25 \cdot 	ext{RF} + 0.15 \cdot 	ext{CS} + 0.15 \cdot 	ext{PC}$$
   *(AS: Audit Score, DC: Documentation Completeness, RF: Reg Filing, CS: Compliance Standing, PC: Policy Conformance)*

2. **External / Regional Risk ($	ext{Score}_{	ext{external}}$):**
   $$	ext{Score}_{	ext{external}} = 0.40 \cdot 	ext{CR} + 0.30 \cdot 	ext{TLR} + 0.10 \cdot 	ext{MSP} + 0.20 \cdot 	ext{CI}$$
   *(CR: Country Risk, TLR: Trade Law Risk, MSP: Market Sanctions Position, CI: Corruption Index)*

3. **Operational Risk ($	ext{Score}_{	ext{operational}}$):**
   $$	ext{Score}_{	ext{operational}} = 0.60 \cdot 	ext{LR} + 0.40 \cdot 	ext{CCP}$$
   *(LR: Litigation Risk, CCP: Corporate Compliance Program)*

4. **Macro Economic Positioning ($	ext{Score}_{	ext{macro}}$):**
   $$	ext{Score}_{	ext{macro}} = 0.50 \cdot 	ext{FH} + 0.30 \cdot 	ext{FB} + 0.20 \cdot 	ext{DV}$$
   *(FH: Financial Health, FB: Financial Backing, DV: Demand Volatility)*

#### Composition, Penalty, and Absolute Gating Logic
The base composite calculation aggregates the individual pillars using fixed weights:
$$	ext{Base}_{	ext{composite}} = 0.50 \cdot 	ext{Score}_{	ext{core}} + 0.25 \cdot 	ext{Score}_{	ext{external}} + 0.15 \cdot 	ext{Score}_{	ext{operational}} + 0.10 \cdot 	ext{Score}_{	ext{macro}}$$

A dynamic penalty is applied based on the completeness of required documents ($	ext{DC}$):
$$	ext{Penalty}_{	ext{missing\_doc}} = 0.70 + 0.30 \cdot 	ext{DC}$$

An absolute security override applies a binary legal block to sanctioned entities:
$$	ext{Block}_{	ext{legal}} =  egin{cases} 0 & 	ext{if } 	ext{MSP} = 0 	ext{ (Sanctioned Entity)} \ 1 & 	ext{if } 	ext{MSP} > 0 	ext{ (Clear)} \end{cases}$$

The final 0-100 RCI value is calculated as follows:
$$	ext{RCI} = 	ext{round}\left(100 \cdot 	ext{Block}_{	ext{legal}} \cdot 	ext{Penalty}_{	ext{missing\_doc}} \cdot 	ext{Base}_{	ext{composite}}, \, 2
ight)$$

---

## 5. Advanced Gemma Engine Evolutions (Expected End-State Innovations)

### 5.1 Conversational ReAct Policy Agent (`ai_services/agent.py`)
Upgrades the simple message flow into an active **Reasoning and Acting** agent loop. When a supplier sends ambiguous text inquiries via WhatsApp (e.g., *"Does my municipal tax document count as a cross-border trade license?"*), the agent reasons through the text, uses a system tool to query the Qdrant trade policy index, and generates a structured, helpful explanation in the user's selected language.

### 5.2 Conversational Analytics Database Engine (`ai_services/analytics_tools.py`)
Replaces the static, hardcoded administrative tables with a dynamic, conversational query system. Administrators can look up operational metrics using natural language (e.g., *"Show me all sellers in the textile industry who are missing an ISO certificate but have an RCI over 80"*). The model translates this text query into a clean JSON tool call, runs the target MongoDB aggregate index, and returns structural data tables straight to the UI.

### 5.3 Cross-Document Compliance & Fraud Verification (`ai_services/cross_doc_audit.py`)
This module scans all uploaded documents simultaneously to cross-verify information across the company's profile. It checks for issues like corporate name variations, mismatching registry locations, overlapping expiry data, and duplicate template numbers. If high-risk contradictions are detected, the system sets an internal risk flag that recalculates the corporate stability metric.

### 5.4 AI Compliance Gap Advisor & Simulator Matrix (`ai_services/simulator.py`)
Explains the mathematical RCI score in natural, user-friendly language without altering the fixed scoring formulas. It isolates the compliance gaps most impacting the vendor's score and provides an interactive simulation interface. This allows users to model "what-if" scenarios, such as: *"How much will my search ranking improve if I renew my expired tax certificate or add an ISO 9001 certification?"*

### 5.5 Automated Strategic Due Diligence Report Engine (`ai_services/explanation.py`)
Converts structured compliance information into a complete, downloadable markdown compliance report. This report includes an executive summary, clear risk scores, cross-document audit logs, a timeline of upcoming document expirations, and a clear onboarding safety recommendation, drastically reducing vendor review times for procurement teams.

---

## 6. End-State Functional Requirements & Deliverables

1.  **Unified Cross-Platform Core:** An integrated API platform connected to an interactive frontend UI with built-in route protection guards (`Buyer`, `Seller`, `Admin`) mapping actions securely.
2.  **Multilingual Mobile Portal:** A responsive WhatsApp workflow capable of guiding global sellers through document submissions and handling open-ended policy questions using an intelligent ReAct agent loop.
3.  **Audit-Ready Matching Engine:** A verifiable supplier ranking dashboard featuring transparent scoring components, interactive simulation toggles, and downloadable due diligence reports.
4.  **Admin Command Center:** An advanced admin dashboard featuring conversational analytics powered by dynamic database query translations.
PRD.md
Displaying PRD.md.