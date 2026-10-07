# AI-Powered IT Helpdesk & Intelligent Automation Demo

This project is a working prototype for an enterprise-style IT helpdesk experience. The goal is to demonstrate how employees can submit IT issues, ask support questions, get AI-guided troubleshooting, and route work through an intelligent automation flow that feels like a real ServiceNow-style helpdesk environment.

The solution combines:
- a React frontend for the employee portal,
- a FastAPI backend for APIs and orchestration,
- a knowledge base with vector search and grounded retrieval,
- mock ticketing and automation flows,
- and a dashboard to represent the operational state of support requests.

This is designed as a hackathon / demo prototype, not a production-ready enterprise deployment.

---

## Project Objective

The project targets the following core business challenge:
- employees can describe issues in natural language,
- the system classifies the request,
- the AI retrieves approved troubleshooting knowledge,
- the system decides whether a request can be self-healed,
- and the request is tracked like a real IT service desk ticket.

The main demo scenarios are:
- Intelligent Ticket Intake
- Auto Resolution / Self-Heal Agent
- Knowledge Management Automation
- Self-Service Portal & Chatbot
- Software Provisioning Automation

---

## What We Built So Far

### 1. Frontend Employee Portal
The React app provides a functional demo portal with:
- Chat panel
- Dashboard
- Knowledge Base page
- Requests page
- Ticket creation flow
- Enterprise-styled dashboard cards and request tables

Key implementation files:
- frontend/src/App.jsx
- frontend/src/styles.css
- frontend/src/main.jsx

### 2. Backend App Shell
The FastAPI backend is running with:
- app initialization
- CORS configuration
- health endpoints
- versioned API routing
- app startup lifecycle for MongoDB preparation

Key implementation files:
- backend/app/main.py
- backend/app/routers/health.py
- backend/app/routers/knowledge.py

### 3. Knowledge Base and Search Pipeline
The project includes:
- approved IT knowledge documents in data/knowledge_docs/
- embedding generation pipeline
- Chroma-backed vector search
- source-aware retrieval with metadata such as title, category, topic, and file
- semantic lookup for user questions

Relevant implementation files:
- backend/app/knowledge_pipeline.py
- backend/app/knowledge_vector_store.py
- data/knowledge_docs/
- data/embeddings/knowledge_chunks.jsonl
- data/vector_store/chroma/

### 4. Grounded AI Chat Assistant
The assistant is grounded on approved support content:
- it searches the knowledge base for relevant articles,
- it builds a natural-language response,
- it presents helpful troubleshooting steps,
- and it avoids exposing internal workflow text in the visible user chat output.

Relevant implementation files:
- backend/app/chat_assistant.py
- backend/app/routers/knowledge.py

### 5. Ticket Intake Workflow
The app supports a ticket flow where a user can describe an issue, receive AI classification, create an incident record, and review it in the dashboard. The dashboard loads ticket records from the backend, filters open and resolved tickets, and shows the selected ticket's details, confidence, routing, suggested resolution, and knowledge sources.

Ticket records are kept in memory when MongoDB is unavailable and are also written to MongoDB when the connection is available.

### 6. MongoDB Foundation
The project includes the database foundation for future persistence:
- MongoDB settings
- client creation
- collection preparation
- collection naming for tickets, knowledge, chat, audit, and software requests

Relevant file:
- backend/app/database.py

### 7. Shared Data Contracts
The app has schema definitions for:
- AI orchestration inputs and outputs
- support request metadata
- ticket and incident style records
- knowledge search results
- automation-related payloads

Relevant file:
- backend/app/schemas.py

### 8. Test Coverage
The repository contains automated checks for:
- backend app shell startup
- knowledge retrieval behavior
- knowledge pipeline integration
- foundation-level app functionality

Relevant files:
- tests/

---

## Current Demo Behavior

The app currently supports a believable IT helpdesk demo flow:

1. User opens the portal and asks a support question or creates a ticket.
2. The backend performs knowledge retrieval against approved docs.
3. The assistant crafts a grounded answer using relevant knowledge.
4. The user can view a knowledge search result or ask a live chat question.
5. The dashboard shows a simulated ITSM view with active requests and ticket history.

This is a valid prototype for a hackathon or demo presentation.

---

## Tech Stack

- Frontend: React + Vite
- Backend: FastAPI + Python
- AI / retrieval: sentence-transformers + Chroma
- Database foundation: MongoDB-ready / PyMongo integration
- Data validation: Pydantic
- Testing: Python unittest

---

## Project Structure

- backend/app/ - FastAPI application and service logic
- backend/requirements.txt - Python dependencies
- frontend/ - React frontend
- data/knowledge_docs/ - approved support articles
- data/embeddings/ - generated embedding artifacts
- data/vector_store/chroma/ - vector store persistence
- docs/ - API notes and planning documents
- tests/ - validation suite
- plan.md - project blueprint
- workflow.md - implementation roadmap
- README.md - project overview and status

---

## Setup and Run

### Prerequisites
- Node.js 18+
- Python 3.10+
- A working virtual environment for backend dependencies
- Optional MongoDB local instance or Atlas connection for persistence

### Frontend install

```bash
cd frontend
npm install
```

### Backend install

```bash
cd backend
pip install -r requirements.txt
```

### Run backend

```bash
cd /media/hp/New Volume1/AI_HACKATHON_FRESHER
source /home/hp/.venvs/default/bin/activate
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Run frontend

```bash
cd frontend
npm run dev
```

### Key app URLs
- Backend docs: http://127.0.0.1:8000/docs
- Health route: http://127.0.0.1:8000/health
- API health route: http://127.0.0.1:8000/api/v1/health

### Fast start (Linux Bash)

```bash
cd "/media/hp/New Volume/AI_HACKATHON_FRESHER"
source .venv/bin/activate
export MONGODB_URI="mongodb://127.0.0.1:27017"
export MONGODB_DB="itsm_ai"
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
cd "/media/hp/New Volume/AI_HACKATHON_FRESHER"
npm run frontend:dev
```

---

## Demo Rehearsal and Architecture Brief

- A complete Phase 7.4 rehearsal plan with timing, scenario order, fallback strategy, and architecture summary is available in `docs/demo_runbook.md`.
- Use this as the speaking script for the final hackathon walkthrough.

---

## Knowledge Pipeline

The knowledge base is built from IT support documents and chunked into embeddings for semantic retrieval.

To generate chunks and embeddings:

```bash
cd /media/hp/New Volume1/AI_HACKATHON_FRESHER
source /home/hp/.venvs/default/bin/activate
python -m backend.app.knowledge_pipeline
```

To build and query the vector store:

```bash
cd /media/hp/New Volume1/AI_HACKATHON_FRESHER
source /home/hp/.venvs/default/bin/activate
python -m backend.app.knowledge_vector_store
```

---

## What We Still Need to Do in the Future

This project is not yet complete against the full enterprise brief. Below are the items that still need to be implemented for a stronger production-style demo and final business challenge completion.

### 1. Real MongoDB Persistence
We need to move from the current foundation to a fully working database-backed flow:
- persist tickets in MongoDB,
- save chat history,
- store software requests,
- save automation audit logs,
- support ticket updates and status transitions.

### 2. ServiceNow Integration or Mock ServiceNow API
The project should include a realistic ITSM integration layer:
- create incident records,
- update existing incidents,
- open service requests,
- return ticket IDs and resolution status,
- and mirror a real ServiceNow JSON contract.

### 3. Full Automation Engine
We need to build the actual self-heal layer for safe tasks such as:
- password reset / unlock flows,
- VPN status checks,
- service restarts,
- cache clears,
- app restarts,
- account lockout troubleshooting.

The system must decide:
- whether a workflow is safe,
- whether it is automatable,
- or whether it should escalate to a human agent.

### 4. Audit Logging for Every Action
Every automated step must be logged with:
- time stamp,
- task name,
- result,
- confidence level,
- who/what initiated it,
- whether it succeeded or failed.

### 5. Software Provisioning Workflow
We still need a stronger software request flow:
- employee requests software,
- AI identifies it as a provisioning request,
- service request is created,
- mock provisioning status is tracked,
- UI shows progress and final state.

### 6. Better AI / LLM Integration
The current system is grounded and retrieval-based, but for a stronger solution we should add:
- an open-source LLM from Hugging Face or another lightweight model,
- intent classification and summarization through the model,
- confidence scoring,
- and more structured response generation.

### 7. Expanded Knowledge Coverage
The repository already contains several useful support articles, but we should continue adding more enterprise-ready documents to cover:
- software installation,
- application access,
- endpoint/device management,
- employee onboarding/offboarding,
- account provisioning,
- laptop health checks,
- printer troubleshooting,
- multi-factor authentication issues.

### 8. Stronger Demo UX and Workflow Validation
We should improve the final experience by adding:
- clearer chat/ticket separation,
- better visual states for in-progress and resolved cases,
- ticket detail pages,
- richer request history,
- and polished presentation for a live demo.

### 9. Production-Readiness Hardening
Future work should also include:
- authentication and authorization,
- secure environment variables and secret handling,
- restricted CORS settings,
- production deployment config,
- error monitoring,
- and structured logging.

---

## Current Status Summary

### Completed
- React app shell and portal navigation
- FastAPI backend shell and health API
- knowledge doc collection
- vector store and retrieval workflow
- chat response generation grounded in approved documentation
- ticket intake connected to backend incident creation
- backend ticket list and detail endpoints
- dashboard filters for open and resolved records, with AI analysis details
- basic automated test suite

### Remaining for Full Completion
- real MongoDB-backed records
- ServiceNow/mock service integration
- automation execution workflow and audit trail
- software provisioning automation
- stronger LLM orchestration
- broader product polish and deployment hardening

---

## Final Note

This repository is already a strong demo prototype for an AI-powered IT helpdesk. It demonstrates the core business value clearly: employees can ask for help, get grounded guidance, create operational tickets, and see a modern support portal experience.

The future work focuses on turning this into a more complete enterprise workflow by adding real persistence, real ticketing and automation, and a fuller AI orchestration layer.
