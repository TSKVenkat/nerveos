<div align="center">

# 🧠 NerveOS

### AI-Native Business Operating System

*Continuously watches your market, inbox, and metrics — then drafts the decisions for you.*

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Self-Hosted](https://img.shields.io/badge/Self--Hosted-✓-purple.svg)](#deployment)

</div>

---

## 🎯 Problem

Growing businesses lack an AI-native **"business nervous system"** that continuously watches their market, customers, and operations and recommends/reviews actions. Instead, they rely on **15+ fragmented apps** and manual coordination.

> Founders and CXOs juggle separate tools for market intel, email, CRM, reporting, and automation — with no AI layer that understands the business end-to-end. Competitor moves, customer signals, and financial health are **visible but not acted on**.

## 💡 Solution

NerveOS is an **AI-powered Business OS for SMBs** that unifies market intelligence, communications, and operations into one reviewable **command center**, where autonomous agents monitor signals, propose actions, and execute **only with human-approved guardrails**.

---

## ✨ Features

### 1. 📡 Market & Competitor Pulse Agent
- **Google Trends** tracking for competitors and keywords
- **RSS/News** aggregation from 10+ sources
- **SearXNG** privacy-friendly web search (offline capable)
- **Stock/Financial** data via yfinance (prices, market cap, PE ratio)
- **Anomaly detection** — price swings, volume spikes
- **AI-generated** competitor analysis and digest
- **Suggested response actions** for each competitive move

### 2. 📧 Inbox & Follow-up Agent
- **IMAP/SMTP** integration for any email provider
- **AI classification** — lead, renewal risk, complaint, partnership, spam
- **Priority scoring** — urgent, high, medium, low
- **Multi-tone draft replies** — professional, friendly, concise
- **Human-in-the-loop** — approve/reject before sending
- **Follow-up tracking** — alerts for unanswered emails
- **Built-in CRM** — contacts, deal stages, pipeline

### 3. 📊 Executive Cockpit
- **Unified KPI dashboard** — MRR, churn, leads, NPS, support tickets
- **Sales pipeline** visualization with deal stages
- **Natural language queries** — *"How did sales compare to last quarter?"*
- **Metric anomaly detection** — automated alerts on 15%+ deviations
- **Morning Briefing** — one-click AI summary of everything important

### 4. 🛡️ Guardrails & Policy Engine
- **Human-in-the-loop by default** — every action goes through approval queue
- **Custom policy rules** — block, require approval, or auto-approve by conditions
- **Deal value protection** — high-value changes require manager approval
- **Complete audit trail** — who suggested, who approved, what happened
- **Privacy-first** — self-hostable, local LLM, private search

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    NerveOS Frontend                       │
│              React + TailwindCSS + Recharts               │
├─────────────────────────────────────────────────────────┤
│                      FastAPI Backend                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │  Market   │ │  Email   │ │Executive │ │  Guardrails │  │
│  │  Intel    │ │  Agent   │ │ Cockpit  │ │  & Policy   │  │
│  │  Agent    │ │          │ │  Agent   │ │  Engine     │  │
│  └─────┬────┘ └────┬─────┘ └────┬─────┘ └──────┬─────┘  │
│        │           │            │               │         │
│  ┌─────┴───────────┴────────────┴───────────────┴─────┐  │
│  │              Agent Orchestrator                      │  │
│  └─────────────────────┬───────────────────────────────┘  │
├────────────────────────┼──────────────────────────────────┤
│  Services Layer        │                                  │
│  ┌─────┐ ┌──────┐ ┌───┴──┐ ┌───────┐ ┌──────┐ ┌──────┐ │
│  │Trend│ │ News │ │  LLM │ │SearXNG│ │Email │ │FinAPI│ │
│  │  s  │ │ RSS  │ │Ollama│ │Search │ │IMAP/ │ │yfinc │ │
│  │     │ │      │ │OpenAI│ │       │ │SMTP  │ │      │ │
│  └─────┘ └──────┘ └──────┘ └───────┘ └──────┘ └──────┘ │
├─────────────────────────────────────────────────────────┤
│  SQLite/PostgreSQL  │  Redis  │  Ollama  │  SearXNG     │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
git clone https://github.com/your-org/nerveos.git
cd nerveos
cp .env.example .env

# Start all services
docker compose up -d

# Pull the LLM model (first time only)
docker compose exec ollama ollama pull llama3.2

# Open dashboard
open http://localhost:3000
```

### Option 2: Local Development

**Backend:**
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start the API server
python main.py
# → API at http://localhost:8000
# → Docs at http://localhost:8000/docs
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# → Dashboard at http://localhost:3000
```

**Dependencies (optional):**
```bash
# Local LLM
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.2

# Private search
docker run -d -p 8888:8080 searxng/searxng
```

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/` | GET | Full executive dashboard |
| `/api/dashboard/briefing` | POST | Generate morning briefing |
| `/api/dashboard/ask` | POST | Natural language business query |
| `/api/dashboard/metrics` | POST | Record a business metric |
| `/api/market/competitors` | GET/POST | CRUD competitors |
| `/api/market/scan` | POST | Run full market intel scan |
| `/api/market/digest` | GET | AI-generated intel digest |
| `/api/market/search` | GET | Quick multi-source search |
| `/api/market/trends` | GET | Google Trends data |
| `/api/market/finance/{ticker}` | GET | Stock info |
| `/api/email/inbox` | GET | AI-classified inbox |
| `/api/email/inbox/{id}/draft` | POST | Generate reply drafts |
| `/api/email/drafts/{id}/approve` | POST | Approve & send draft |
| `/api/email/contacts` | GET/POST | CRM contacts |
| `/api/actions/pending` | GET | Pending approval queue |
| `/api/actions/{id}/approve` | POST | Approve an action |
| `/api/actions/audit` | GET | Full audit trail |
| `/api/actions/policies` | GET/POST | Manage policy rules |

Full interactive docs at **`/docs`** (Swagger UI).

---

## 🔧 Tech Stack (100% Open Source)

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11, FastAPI, SQLAlchemy, Pydantic |
| **Frontend** | React 18, Vite, TailwindCSS, Recharts, Lucide |
| **LLM** | Ollama (local) — llama3.2, mistral, etc. |
| **Search** | SearXNG (self-hosted, privacy-first) |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Cache** | Redis |
| **Trends** | pytrends (Google Trends) |
| **Finance** | yfinance (stock data) |
| **News** | feedparser (RSS/Atom) |
| **Email** | IMAP/SMTP (native Python) |
| **Deploy** | Docker, Docker Compose |

---

## 🗺️ Roadmap

- [x] Market & Competitor Pulse Agent
- [x] Email Agent with AI classification
- [x] Executive Cockpit with NL queries
- [x] Human-in-the-loop guardrails
- [x] Policy engine & audit trail
- [x] Docker self-hosting
- [ ] IPO alerts & stock crash early-warning
- [ ] Slack/Teams integrations
- [ ] Asset valuation monitoring
- [ ] Internal knowledge hub
- [ ] Multi-tenant cloud version
- [ ] Plugin framework for custom agents
- [ ] Stripe/billing integration
- [ ] Advanced charting & reporting
- [ ] Mobile-responsive PWA

---

## 📂 Project Structure

```
nerveos/
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment config template
├── backend/
│   ├── main.py                 # FastAPI app + seed data
│   ├── config.py               # Settings from env vars
│   ├── database.py             # Async SQLAlchemy setup
│   ├── models/
│   │   └── models.py           # All database models
│   ├── agents/
│   │   ├── market_intel.py     # Market intelligence agent
│   │   ├── email_agent.py      # Email triage & reply agent
│   │   ├── executive_cockpit.py# Dashboard & NL query agent
│   │   └── orchestrator.py     # Multi-agent coordinator
│   ├── services/
│   │   ├── llm.py              # Ollama + OpenAI LLM service
│   │   ├── searxng.py          # SearXNG search integration
│   │   ├── trends.py           # Google Trends via pytrends
│   │   ├── news.py             # RSS/news aggregation
│   │   ├── finance.py          # Stock data via yfinance
│   │   └── email_service.py    # IMAP/SMTP service
│   ├── guardrails/
│   │   └── policy_engine.py    # Approval & audit system
│   └── routers/
│       ├── market.py           # Market intel API
│       ├── email.py            # Email agent API
│       ├── dashboard.py        # Dashboard API
│       ├── actions.py          # Actions & policies API
│       └── settings.py         # Health & config API
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Router setup
│   │   ├── components/
│   │   │   └── Layout.jsx      # Sidebar + shell
│   │   ├── pages/
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── MarketIntelPage.jsx
│   │   │   ├── EmailPage.jsx
│   │   │   ├── ActionsPage.jsx
│   │   │   └── SettingsPage.jsx
│   │   ├── lib/
│   │   │   └── api.js          # API client
│   │   └── hooks/
│   │       └── useApi.js       # React hook
│   └── Dockerfile
└── searxng/
    └── settings.yml            # SearXNG config
```

---

## 🎯 AMD Slingshot — Pitch

**One-liner:** *"An AI business OS that continuously watches your market, inbox, and metrics — then drafts the decisions for you."*

**Persona:** 10–200 person B2B startup founder / COO

**Day without NerveOS:** 15 tabs, 8 tools, no clear picture  
**Day with NerveOS:** Wake up to one command center — "Here's what changed, here's what we should do."

**Differentiator:** Multi-agent cross-system orchestration + fully self-hostable + privacy-first (local LLM + private search) — there are very few truly open, self-hostable "AI business OS" products.

---

## 📄 License

MIT — free to use, modify, and self-host.

---

<div align="center">
  <b>Built with ❤️ for the AMD Slingshot Hackathon</b><br/>
  <sub>Future of Work & Productivity Track</sub>
</div>
