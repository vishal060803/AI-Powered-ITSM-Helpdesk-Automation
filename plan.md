# AI-Powered ITSM & Intelligent Helpdesk Automation Platform

This document is the implementation blueprint for the hackathon project described in the attached PDF. It focuses on building a working prototype, not production-grade architecture. The goal is to create a realistic enterprise-style demo that can be shown live with clear workflows, AI reasoning, RAG-based knowledge retrieval, automation actions, and ServiceNow-style ticketing.

---

## 1. Project Objective

Build a prototype that demonstrates how an employee can:
- ask a question or submit an IT issue,
- get AI classification for intent, category, urgency, and priority,
- retrieve grounded knowledge from an approved IT knowledge base,
- automate safe self-heal operations for common IT issues,
- create or update ServiceNow-style records,
- request software provisioning,
- and escalate when confidence is low or data is unavailable.

The end result should feel like a real enterprise IT service desk, even if it runs with mock APIs and local services.

---

## 2. Implementation Philosophy

We should avoid trying to build every part as a full enterprise system. Instead, we should model the real business flow in a simplified but convincing way:

1. Employee request enters through a portal or chatbot.
2. AI interprets user intent and decides if this is:
   - a knowledge question,
   - a service request,
   - an incident,
   - or an automatable issue.
3. RAG retrieves trusted enterprise knowledge if needed.
4. The AI proposes classification and a suggested resolution.
5. The system either:
   - creates a ticket,
   - executes automation,
   - or escalates to human helpdesk.
6. The audit trail and ticket history are stored and shown in a dashboard.

This structure is both easy to demo and strong enough to explain in a 15–20 minute presentation.

---

## 3. Recommended Technology Stack

### Frontend
- React.js
- Vite or CRA is acceptable for quick setup
- UI can be simple but polished
- Use TypeScript for cleaner API contracts and easier component state management

### Backend
- Python + FastAPI
- Separate routers/services for:
  - AI orchestration,
  - knowledge search,
  - ticketing,
  - automation,
  - software requests

### Database
- MongoDB Atlas or local MongoDB-compatible setup for prototype
- Collections for:
  - tickets
  - users
  - knowledge articles
  - chat history
  - automation audit logs
  - software requests
  - incident/service request metadata

### LLM
- Prefer a small open-source model from Hugging Face such as a lightweight instruction-tuned model
- Reason: easy to run locally, lower cost, and suitable for a hackathon prototype
- Use it for intent detection, summarization, and answer generation

### Embeddings
- SentenceTransformers model
- For prototype, a lightweight sentence-transformer embedding model is good enough

### Vector Store
- FAISS for simplicity and speed
- Chroma is also attractive for quick local experiments
- Choose one and keep the retrieval workflow clean and explainable

### ITSM Integration
- Prefer ServiceNow REST API if available
- If not available, use a mock ServiceNow API that mirrors the same JSON contract and endpoints

---

## 4. Proposed High-Level Architecture

### Core flow
Employee portal -> FastAPI backend -> AI orchestration -> RAG + vector search -> LLM -> automation / ticketing / response

### Layered design
1. Presentation layer
   - Employee portal UI
   - Dashboard UI
   - Knowledge base UI
   - Chat window

2. API layer
   - incident creation
   - chatbot request handling
   - knowledge search
   - automation execution
   - software provisioning request

3. AI + orchestration layer
   - intent classifier
   - knowledge retrieval layer
   - suggestion generation
   - confidence evaluation
   - escalation decision

4. Data layer
   - MongoDB for records and logs
   - vector DB for knowledge retrieval
   - file-based or in-memory knowledge source for prototype if needed

5. Integration layer
   - ServiceNow API wrapper
   - mock ServiceNow endpoints
   - automation service mock APIs (password reset, VPN status, cache clear, service restart, etc.)

---

## 5. Functional Workstreams

### Workstream A: Intelligent Ticket Intake
Goal: turn a natural language employee complaint into a structured incident record.

Implementation approach:
- Employee enters a message like "I cannot connect to VPN since this morning. Authentication keeps failing."
- Backend calls an intent extraction service
- AI parses: intent, category, sub-category, priority, urgency, assignment group, summary, and suggested resolution
- It should map to ServiceNow-style fields
- This data is saved to MongoDB and a ticket is created via ServiceNow or mock API

Expected outputs:
- Intent: Incident
- Category: Network / VPN
- Priority: P2
- Impact / Urgency: Individual / High
- Assignment Group: Network Support
- Summary: VPN authentication failure
- Suggested Resolution: VPN troubleshooting
- ServiceNow incident record created

### Workstream B: Auto Resolution / Self-Heal Agent
Goal: identify safe issues that can be handled without manual intervention.

Implementation approach:
- Detect triggers such as:
  - password expired,
  - account locked,
  - VPN status issue,
  - service restart,
  - cache clear,
  - app restart
- Validate if the issue is low-risk and automatable
- Search knowledge base for the exact procedure
- Execute a mock automation API action sequence
- Validate result
- Record every action in an audit log
- Update the ticket status in ServiceNow or mock service

Example flow:
- Employee: "My password has expired."
- AI decides this is a self-healable issue
- Knowledge lookup finds password reset procedure
- Automation executes reset/unlock or a mock equivalent
- Result is verified and logged
- ServiceNow ticket is updated as resolved or in-progress

### Workstream C: Knowledge Management Automation
Goal: provide approved enterprise knowledge that can answer user questions with source attribution.

Implementation approach:
- Create 5–10 IT knowledge documents
  - VPN troubleshooting
  - Password reset
  - Outlook issue resolution
  - Wi-Fi troubleshooting
  - Laptop performance issues
  - Software installation
  - Application access
- Store documents in a knowledge base
- Before running any model-heavy step, perform a low-end laptop optimization gate:
  - check memory, CPU, and disk availability,
  - close extra apps, browsers, and terminals,
  - keep only one active Python environment,
  - avoid duplicate installs and parallel downloads,
  - prefer smaller chunk sizes and re-use persisted embeddings when possible
- Split them into chunks
- Convert chunks to embeddings
- Save embeddings into FAISS or Chroma
- On question input:
  - retrieve top relevant chunks,
  - pass them to the LLM with a grounded answer prompt,
  - show the article names/sources used
- If the answer is not supported by retrieved context, the system must say it cannot answer confidently and offer to escalate

### Workstream D: Self-Service Portal & AI Chatbot
Goal: let employees ask questions and submit requests in a clean portal.

Implementation approach:
- Create a single web app with:
  - chat panel,
  - request form,
  - dashboard,
  - knowledge base page,
  - AI analysis detail panel
- A user request can be routed into one of four categories:
  - Knowledge Question
  - Incident
  - Service Request
  - Automatable Issue
- The portal should show:
  - AI intent,
  - confidence score,
  - category,
  - summary,
  - suggested resolution,
  - source references

### Workstream E: Software Provisioning Automation
Goal: model a software request workflow aligned with the challenge.

Implementation approach:
- Employee enters a request like “I need Visual Studio Code installed on my laptop.”
- AI classifies as a software provisioning request
- Backend checks a software catalog
- Creates a mock ServiceNow service request record
- A mock provisioning API returns status as “Provisioning”
- The frontend shows request ID and status
- This is a simulated installation flow, not a real installation

---

## 6. AI Orchestration Design

The backend should treat AI as an orchestrator rather than a black box. The recommended structure is:

1. Intent detection
   - Determine if request is knowledge, incident, service request, or automatable issue

2. Context gathering
   - Pull user metadata if available
   - Pull last ticket history if needed
   - Search the knowledge base if the request is uncertain

3. Structured extraction
   - Extract fields into a consistent schema
   - Example schema:
     - intent
     - category
     - sub_category
     - priority
     - impact
     - urgency
     - assignment_group
     - summary
     - suggested_resolution
     - confidence

4. Decision logic
   - If confidence is high and action is supported by docs -> answer or auto-resolve
   - If confidence is medium -> ask follow-up / escalate
   - If low or unsupported -> create helpdesk ticket and say no hallucination

5. Action routing
   - Knowledge answer -> show answer and sources
   - Incident -> create ServiceNow incident
   - Self-heal -> execute mock automation
   - Provisioning -> create software request

This keeps the app organized and helps with explainability.

---

## 7. Data Model Plan

### Ticket collection
- ticket_id
- employee_id
- title
- description
- intent
- category
- sub_category
- priority
- impact
- urgency
- assignment_group
- status
- confidence
- source_documents
- created_at
- updated_at
- serviced_by
- service_now_ref

### Knowledge article collection
- article_id
- title
- category
- sub_category
- content
- chunks
- metadata
- source_file
- created_at
- updated_by

### Chat history collection
- chat_id
- employee_id
- message_content
- role
- intent
- confidence
- resolution
- timestamp

### Automation audit log collection
- log_id
- ticket_id
- automation_name
- action_sequence
- status
- result
- timestamp
- performed_by

### Software request collection
- request_id
- employee_id
- software_name
- request_type
- status
- service_now_ref
- created_at
- updated_at

This model is enough for the prototype and realistically maps to enterprise needs.

---

## 8. Frontend Screen Plan

### 1. Employee Self-Service Portal
- Chat box for employee questions
- Quick issue templates
- Submit incident/service request
- Show AI-generated summary and suggested resolution
- Show action buttons such as “Create Ticket” or “Auto-Resolve”

### 2. ITSM Dashboard
- Total tickets
- Open tickets
- AI-resolved tickets
- Escalated tickets
- Software requests overview
- Automation status summary
- Recent activity feed

### 3. AI Analysis Panel
- Intent
- Category
- Priority
- Confidence
- Resolution
- Sources used
- ServiceNow reference
- Automation status

### 4. Knowledge Base Screen
- Search by keyword
- Filter by categories like VPN, Outlook, Wi-Fi, Passwords
- List of articles
- RAG result panel showing matches and sources

This covers the required screens from the challenge document.

---

## 9. ServiceNow Integration Plan

### Preferred production path
Use ServiceNow REST API for:
- Create Incident
- Get Incident
- Update Incident
- Create Service Request

### Mock path for hackathon
If ServiceNow access is not available, build a mock ServiceNow API layer that matches the same schema and behavior. This is very useful because it keeps the backend contract clean and demo-friendly.

### API contract design
- POST /api/servicenow/incidents
- GET /api/servicenow/incidents/{id}
- PATCH /api/servicenow/incidents/{id}
- POST /api/servicenow/requests

These endpoints will be called from the backend service, not directly from the frontend.

### Mapping strategy
Map AI-extracted data into ServiceNow-like fields:
- short_description = summary
- category = category
- priority = priority
- impact = impact
- urgency = urgency
- assignment_group = assignment_group
- description = employee complaint + AI reasoning

This gives a strong “production-ready” story during the presentation even if the actual integration is mocked.

---

## 10. Safety, Governance, and Confidence Rules

These are mandatory and should be built into the demo logic.

### No hallucination rule
If the retrieved knowledge is insufficient, the AI must say so clearly instead of inventing an answer.

### Source attribution
Every RAG answer should show:
- article title,
- document source,
- relevant excerpt or chunk,
- confidence score

### Confidence handling
A simple threshold like 0.65 can be used.
- Above threshold: answer directly or resolve automatically
- Below threshold: escalate and create ticket

### Human escalation workflow
If the system cannot confidently answer or the issue is not in the knowledge base, it should:
- stop with a safe message,
- create a helpdesk ticket or incident,
- show the escalation option to the employee

This is critical for business credibility.

---

## 11. Recommended Implementation Phases

### Phase 1: Foundation
- Set up repo structure
- Create frontend app shell
- Create FastAPI backend app
- Configure MongoDB connection and env variables
- Create basic project README and environment instructions

### Phase 2A: Low-End Laptop Optimization and Safe Model Execution
- Check RAM, CPU, and disk availability before any embedding work
- Reduce background load by closing unnecessary apps and stale terminals
- Keep one clean virtual environment and one active backend process
- Avoid duplicate dependency installs and parallel model downloads
- Use the smallest practical embedding configuration and moderate chunk sizes
- Reuse persisted embedding artifacts instead of rebuilding everything repeatedly
- Only continue once the machine is stable enough for vector/index work

### Phase 2: Knowledge Base + RAG
- Prepare 5–10 knowledge documents
- Chunk and embed them only after the optimization gate passes
- Store in vector DB
- Build retrieval endpoint
- Connect to LLM for grounded answer generation
- Show sources in UI

### Phase 3: AI Intent + Incident Workflow
- Build intent extraction service
- Add structured classification logic
- Create mock or real ServiceNow incident creation flow
- Show ticket record in dashboard

### Phase 4: Automation + Audit Logs
- Add automation rules for expired password, unlocked account, VPN check, service restart, cache reset
- Log each step
- Show automation outputs and validation result

### Phase 5: Software Provisioning Flow
- Add catalog of software items
- Create service request and status tracking
- Show worker progress and request IDs

### Phase 6: UI Polish + Demo Readiness
- Finalize screens
- Connect all flows end-to-end
- Add charts, ticket cards, and status indicators
- Validate the five mandatory scenarios

---

## 12. Demo Scenario Plan

The prototype must be able to demonstrate the exact business flows in the PDF.

### Scenario 1: Intelligent Ticket Intake
Input: “My VPN is not connecting.”
Expected flow:
- AI classifies as Incident
- Detects Network / VPN
- Creates ticket with priority and assignment info
- ServiceNow or mock integration records the incident

### Scenario 2: Self-Healing / Auto Resolution
Input: “My password has expired.”
Expected flow:
- AI decides it is an automatable issue
- Knowledge search finds password reset procedure
- Automation executes mock password reset or unlock flow
- Validation occurs
- Ticket is updated

### Scenario 3: RAG / Knowledge Query
Input: “How do I troubleshoot Outlook synchronization?”
Expected flow:
- Vector search finds relevant knowledge documents
- LLM answers grounded in retrieved context
- Sources are shown to the user

### Scenario 4: Software Provisioning
Input: “I need Visual Studio Code.”
Expected flow:
- AI identifies as service request
- Lookup in software catalog
- Service request created
- Provisioning status shown in UI

### Scenario 5: Unknown Question
Input: unsupported/unrelated or missing context
Expected flow:
- AI says it does not have enough approved knowledge
- No hallucination
- Escalation or ticket option offered

These five scenarios should be rehearsed before the final demo.

---

## 13. Key Project Decisions

### Why FastAPI?
It is lightweight, Python-native, and very easy to integrate with ML/RAG services and REST APIs.

### Why React?
It handles interactive dashboards, chat panels, and quick UI iteration very effectively.

### Why MongoDB?
It works well for document-based ticketing, chat records, metadata, and audit logs.

### Why a small open-source LLM?
Because the goal is a working hackathon prototype with realistic behavior, not production-scale GPU inference.

### Why FAISS/Chroma?
Because the knowledge-base flow needs fast semantic retrieval, and both are suitable for local prototype use.

---

## 14. Risks and How to Handle Them

### Risk: LLM output is not stable
Mitigation: keep prompts simple, use structured extraction, enforce output schema, and use knowledge grounding.

### Risk: Knowledge retrieval is weak
Mitigation: create high-quality sample docs and test them with realistic search queries.

### Risk: ServiceNow is unavailable
Mitigation: implement a mock ServiceNow API with the same contract so the app can still be demoed reliably.

### Risk: Demo flow becomes too complex
Mitigation: keep the feature set to the five required flows, emphasize quality over quantity.

### Risk: UI becomes too cluttered
Mitigation: maintain a minimal but polished design with clearly separated screens and states.

---

## 15. Recommended Repo Structure

A clean structure will help keep the project manageable:

- frontend/
  - src/
  - public/
  - package.json

- backend/
  - app/
  - api/
  - services/
  - models/
  - config/
  - requirements.txt

- data/
  - knowledge_docs/
  - sample_data/

- vector_db/
  - embeddings/

- tests/
  - api_tests/
  - scenario_tests/

- README.md

This structure is simple enough for teamwork and still mirrors a real platform architecture.

---

## 16. Acceptance Criteria for the Prototype

The project should be considered ready when:
- an employee can submit a request in a React UI,
- the backend can classify the issue with AI,
- a knowledge question can return grounded answers with sources,
- an incident can be created via ServiceNow mock API,
- a self-healing issue can execute a mock automation flow and log the action,
- a software request can be created and tracked,
- the dashboard shows ticket states and audit information,
- low-confidence questions are escalated or blocked safely,
- the five scenarios can be demonstrated in under 15–20 minutes.

---

## 17. Final Recommendation

The best strategy is to build a compact but realistic system around one coherent flow:

User input -> AI intent detection -> knowledge retrieval / automation decision -> ServiceNow integration -> dashboard and audit trail.

This flow is the heart of the project and matches the business challenge exactly. Build the project around this story, keep the UI simple and polished, keep the AI logic explainable, and make the demo extremely crisp and scenario-driven.

The implementation should prioritize:
- clarity,
- end-to-end flow,
- business relevance,
- safe AI decisions,
- and strong live demo execution.

This is the right approach for a hackathon prototype where the evaluation focuses on enterprise-style thinking, working workflows, and technical storytelling.

---

## 18. Next Immediate Step

The next phase will be to define exact project folders, service boundaries, and the step-by-step implementation sequence before we begin actual coding. The plan here is ready to be turned into execution tasks.
