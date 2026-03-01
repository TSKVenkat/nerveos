# NerveOS

**AI-Native Business Operating System**

NerveOS is an open-source, self-hostable business intelligence platform for SMBs and scale-ups. Autonomous agents continuously monitor market signals, communications, and operational metrics, then surface recommended actions through a human-in-the-loop approval workflow.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Self-Hosted](https://img.shields.io/badge/Self--Hosted-Yes-purple.svg)](#deployment)

---

## Problem Statement

Growing businesses lack an AI-native system that continuously monitors their market, customers, and operations while recommending and reviewing actions. In practice, founders and operators rely on fifteen or more fragmented tools for market intelligence, email, CRM, reporting, and automation — with no AI layer that understands the business end-to-end. Competitor moves, customer signals, and financial health are visible in isolation but are never connected or acted upon systematically.

## Solution

NerveOS unifies market intelligence, communications, and operations into a single reviewable command center. Autonomous agents monitor signals, propose actions, and execute only with explicit human approval — enforced by a configurable policy and guardrails engine.

---

## Features

### Market and Competitor Intelligence Agent

- Google Trends tracking for competitors and target keywords
- RSS and news aggregation from multiple sources
- SearXNG private web search (self-hosted, offline-capable)
- Stock and financial data via yfinance (price, market cap, P/E ratio)
- Anomaly detection for price swings and volume spikes
- AI-generated competitor analysis and weekly digest
- Suggested response actions for each competitive development

### Inbox and Follow-up Agent

- IMAP/SMTP integration for any email provider
- AI classification: lead, renewal risk, complaint, partnership, spam
- Priority scoring: urgent, high, medium, low
- Multi-tone draft replies: professional, friendly, concise
- Human-in-the-loop approval before any message is sent
- Follow-up tracking with alerts for unanswered threads
- Built-in contact and deal stage management

### Executive Cockpit

- Unified KPI dashboard covering MRR, churn, leads, NPS, and support volume
- Sales pipeline visualization with deal stage breakdown
- Natural language query interface ("How did sales compare to last quarter?")
- Metric anomaly detection with automated alerts on significant deviations
- One-click morning briefing summarizing all overnight developments

### Guardrails and Policy Engine

- Human-in-the-loop approval queue for every proposed action
- Configurable policy rules: block, require approval, or auto-approve by condition
- Deal value thresholds requiring manager-level approval
- Complete audit trail: suggested by, approved by, outcome, timestamp
- Privacy-first architecture: fully self-hostable with private search

---

## Architecture

```
+----------------------------------------------------------+
|                     NerveOS Frontend                     |
|               React + TailwindCSS + Recharts             |
+----------------------------------------------------------+
|                      FastAPI Backend                     |
|  +-----------+ +-----------+ +----------+ +----------+  |
|  |  Market   | |  Email    | |Executive | |Guardrails|  |
|  |  Intel    | |  Agent    | |  Cockpit | |  Policy  |  |
|  |  Agent    | |           | |  Agent   | |  Engine  |  |
|  +-----+-----+ +-----+-----+ +----+-----+ +----+-----+  |
|        |             |            |             |        |
|  +-----+-------------+------------+-------------+-----+  |
|  |                 Agent Orchestrator                  |  |
|  +-----------------------------------------------------+  |
+----------------------------------------------------------+
|  Services                                                |
|  +-------+ +------+ +-------+ +--------+ +----+ +----+ |
|  |Trends | | News | |  LLM  | |SearXNG | |IMAP| |Fin | |
|  |       | | RSS  | | Grok  | | Search | |SMTP| |API | |
|  +-------+ +------+ +-------+ +--------+ +----+ +----+ |
+----------------------------------------------------------+
|  SQLite / PostgreSQL  |  Redis  |  SearXNG               |
+----------------------------------------------------------+
```

---

## Quick Start

### Option 1: Docker Compose (Recommended)

```bash
git clone https://github.com/your-org/nerveos.git
cd nerveos
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY and email credentials

docker compose up -d
```

The dashboard will be available at `http://localhost:3000`.
The API and interactive documentation will be available at `http://localhost:8000/docs`.

### Option 2: Local Development

**Backend**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

**SearXNG (optional)**

```bash
docker run -d -p 8888:8080 searxng/searxng
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure the following:

| Variable | Description |
|---|---|
| `OPENROUTER_API_KEY` | API key from [openrouter.ai](https://openrouter.ai) |
| `OPENROUTER_MODEL` | Model identifier (default: `x-ai/grok-3-mini-beta`) |
| `OPENROUTER_BASE_URL` | OpenRouter API base URL |
| `IMAP_HOST` / `IMAP_USER` / `IMAP_PASSWORD` | Incoming mail credentials |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | Outgoing mail credentials |
| `SEARXNG_URL` | SearXNG instance URL |
| `DATABASE_URL` | SQLite or PostgreSQL connection string |
| `SECRET_KEY` | Application secret key (change in production) |

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/dashboard/` | GET | Full executive dashboard data |
| `/api/dashboard/briefing` | POST | Generate morning briefing |
| `/api/dashboard/ask` | POST | Natural language business query |
| `/api/dashboard/metrics` | POST | Record a business metric |
| `/api/market/competitors` | GET, POST | Manage competitor records |
| `/api/market/scan` | POST | Run full market intelligence scan |
| `/api/market/digest` | GET | AI-generated intelligence digest |
| `/api/market/search` | GET | Multi-source search |
| `/api/market/trends` | GET | Google Trends data |
| `/api/market/finance/{ticker}` | GET | Stock and financial data |
| `/api/email/inbox` | GET | AI-classified inbox |
| `/api/email/inbox/{id}/draft` | POST | Generate reply drafts |
| `/api/email/drafts/{id}/approve` | POST | Approve and send a draft |
| `/api/email/contacts` | GET, POST | CRM contact management |
| `/api/actions/pending` | GET | Pending approval queue |
| `/api/actions/{id}/approve` | POST | Approve an action |
| `/api/actions/audit` | GET | Full audit trail |
| `/api/actions/policies` | GET, POST | Manage policy rules |

Full interactive documentation is available at `/docs` (Swagger UI).

---

## Technology Stack

All components are open source.

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| Frontend | React 18, Vite, TailwindCSS, Recharts, Lucide |
| LLM | Grok via OpenRouter (`x-ai/grok-3-mini-beta`) |
| Search | SearXNG (self-hosted, privacy-first) |
| Database | SQLite (development) / PostgreSQL (production) |
| Cache | Redis |
| Trends | pytrends (Google Trends API) |
| Finance | yfinance (stock and market data) |
| News | feedparser (RSS/Atom aggregation) |
| Email | IMAP/SMTP (standard Python libraries) |
| Deployment | Docker, Docker Compose |

---

## Roadmap

**Completed**
- Market and Competitor Intelligence Agent
- Email Agent with AI classification and draft replies
- Executive Cockpit with natural language query support
- Human-in-the-loop guardrails and approval workflow
- Policy engine and full audit trail
- Docker self-hosting

**Planned**
- IPO alerts and stock crash early-warning signals
- Slack and Microsoft Teams integrations
- Asset valuation monitoring
- Internal knowledge hub
- Multi-tenant cloud deployment option
- Plugin framework for custom agents
- Stripe and billing integration
- Advanced reporting and chart exports
- Mobile-responsive progressive web app

---

## Project Structure

```
nerveos/
├── docker-compose.yml              # Full stack orchestration
├── .env.example                    # Environment configuration template
├── backend/
│   ├── main.py                     # FastAPI application entry point
│   ├── config.py                   # Settings loaded from environment
│   ├── database.py                 # Async SQLAlchemy configuration
│   ├── models/
│   │   └── models.py               # Database models
│   ├── agents/
│   │   ├── market_intel.py         # Market intelligence agent
│   │   ├── email_agent.py          # Email triage and reply agent
│   │   ├── executive_cockpit.py    # Dashboard and NL query agent
│   │   └── orchestrator.py        # Multi-agent coordinator
│   ├── services/
│   │   ├── llm.py                  # Grok via OpenRouter (LLM client)
│   │   ├── searxng.py              # SearXNG search integration
│   │   ├── trends.py               # Google Trends via pytrends
│   │   ├── news.py                 # RSS and news aggregation
│   │   ├── finance.py              # Stock data via yfinance
│   │   └── email_service.py        # IMAP/SMTP service
│   ├── guardrails/
│   │   └── policy_engine.py        # Approval workflow and audit system
│   └── routers/
│       ├── market.py               # Market intelligence endpoints
│       ├── email.py                # Email agent endpoints
│       ├── dashboard.py            # Dashboard endpoints
│       ├── actions.py              # Actions and policies endpoints
│       └── settings.py             # Health and configuration endpoints
├── frontend/
│   ├── src/
│   │   ├── App.jsx                 # Client-side routing
│   │   ├── components/
│   │   │   └── Layout.jsx          # Sidebar navigation and shell
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── MarketIntelPage.jsx
│   │   │   ├── EmailPage.jsx
│   │   │   ├── ActionsPage.jsx
│   │   │   └── SettingsPage.jsx
│   │   ├── lib/
│   │   │   └── api.js              # API client
│   │   └── hooks/
│   │       └── useApi.js           # React data-fetching hook
│   └── Dockerfile
└── searxng/
    └── settings.yml                # SearXNG configuration
```

---

## License

MIT License. Free to use, modify, and self-host. See [LICENSE](LICENSE) for details.

---

Built for the AMD Slingshot Hackathon — Future of Work and Productivity Track.
