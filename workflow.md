# Recommended Implementation Workflow

This workflow is designed to keep the project manageable and controlled. Instead of doing all features at once, we will complete the project in small, reviewable phases with clear deliverables.

---

## Phase 0: Project Setup and Baseline

### Sub-phase 0.1: Repository Structure
- Create root project folders
- Define frontend, backend, data, tests, and docs structure
- Set naming conventions and file organization
- Decide whether we will use Vite + React and FastAPI

### Sub-phase 0.2: Environment Setup
- Initialize frontend project
- Initialize backend project
- Prepare Python virtual environment
- Prepare Node environment
- Create environment variable template for MongoDB, LLM, and ServiceNow settings

### Sub-phase 0.3: Shared Contracts and Definitions
- Define API request/response models
- Define ticket schema
- Define knowledge article schema
- Define automation action schema
- Define demo scenario input/output examples

### Exit criteria for Phase 0
- Repo is organized
- Frontend and backend can start independently
- Core config files are ready
- Team understands the project data flow

### Testing requirement for Phase 0
- Verify the folder structure exists and is usable
- Confirm the root repository is clean and ready for next phase
- Confirm setup commands are documented and repeatable

---

## Phase 1: Foundation

### Sub-phase 1.1: Frontend App Shell
- Create React app shell
- Create main layout
- Create navigation for chat, dashboard, knowledge base, and request pages
- Add basic styling/theme for enterprise UI

### Sub-phase 1.2: Backend App Shell
- Create FastAPI app
- Add health check route
- Add initial router structure
- Add basic CORS and app configuration

### Sub-phase 1.3: MongoDB Foundation
- Set up MongoDB connection layer
- Create database and collection placeholders
- Define connection config and error handling
- Prepare mock or real sample data structure

### Sub-phase 1.4: Documentation and README Base
- Add project overview
- Add setup instructions
- Add local run commands
- Add known limitations and assumptions

### Exit criteria for Phase 1
- Frontend loads without errors
- Backend runs successfully
- MongoDB connection setup is ready
- Project has a clear folder structure and startup path

### Testing requirement for Phase 1
- Run frontend startup to verify no build/runtime errors
- Run backend startup to verify app loads successfully
- Verify the environment variables are recognized correctly
- Check that the app can initialize without crashing

---

## Phase 2: Knowledge Base + RAG

### Sub-phase 2.1: Knowledge Content Preparation
- Create 5–10 IT knowledge documents
- Cover categories such as VPN, password reset, Outlook, Wi-Fi, laptop performance, software installation, app access
- Store raw documents in a data folder

### Sub-phase 2.2: Chunking and Embeddings
- Split articles into meaningful chunks
- Generate embeddings using an open-source sentence-transformers model
- Keep metadata for source article, title, category, and chunk ID

### Sub-phase 2.2.5: Low-End Laptop Optimization and Safe Model Execution
- Check memory, CPU, and disk availability before running model jobs
- Close unnecessary apps, browser tabs, and extra terminals before embedding work
- Use only one Python virtual environment and one active backend process
- Avoid duplicate package installs or parallel model downloads
- Prefer the smallest practical embedding model and keep chunk sizes moderate
- Reuse pre-generated embedding files instead of regenerating vectors repeatedly
- Run the embedding job in a controlled sequence: validate docs -> chunk -> embed -> index
- Stop and restart only when the system is stable enough for heavy CPU work
- Keep a fallback path: if memory is too low, work from existing persisted embeddings instead of re-building
- Record the hardware-safe run settings for future local testing

### Exit criteria for Phase 2.2.5
- The environment is stable enough for model work
- No duplicate heavy processes are running
- The embedding and indexing pipeline can run without frequent crashes or memory bottlenecks
- The team can continue to Phase 2.3 without redoing unnecessary heavy work

### Testing requirement for Phase 2.2.5
- Check available RAM/CPU before starting the model run
- Confirm only the required environment and terminals remain active
- Validate that the embedding script can run in a low-resource state without crashing
- Confirm the generated or persisted embedding artifact is reusable

### Sub-phase 2.3: Vector Store Setup
- Create vector DB integration with FAISS or Chroma
- Store embeddings with article metadata
- Make retrieval queryable by topic and category

### Sub-phase 2.4: Retrieval API
- Build a backend endpoint that accepts a question
- Fetch top relevant chunks semantically
- Return ranked results with metadata and sources

### Sub-phase 2.5: Grounded Answer Generation
- Pass retrieved context to the LLM
- Ask the model to answer based only on approved content
- Return answer + source article names + confidence
- Handle unsupported answers safely and explicitly

### Sub-phase 2.6: Knowledge UI
- Show knowledge articles in UI
- Show search results with category filter and source attribution
- Display grounded answer + source references

### Exit criteria for Phase 2
- Questions return grounded responses from approved docs
- Source documents are shown clearly
- Unsupported answers do not hallucinate
- Knowledge base works end-to-end

### Testing requirement for Phase 2
- Test 3–5 representative knowledge questions
- Verify source attribution appears for each response
- Verify unsupported queries return a safe refusal instead of hallucination
- Confirm vector retrieval returns expected top results

---

## Phase 3: AI Intent Detection and Incident Workflow

### Sub-phase 3.1: Intent and Classification Logic
- Define request categories: knowledge question, incident, service request, automatable issue
- Create AI prompt or logic for classification
- Extract structured fields: category, priority, urgency, summary, suggested resolution

### Sub-phase 3.2: Incident Extraction Schema
- Define output schema for AI-generated ticket data
- Add confidence scoring
- Add assignment group logic
- Add mapping for ServiceNow fields

### Sub-phase 3.3: Incident Creation Flow
- Convert AI output to ServiceNow-style payload
- Create mock ServiceNow API layer
- Save incident in MongoDB
- Return ServiceNow reference ID to frontend

**Previous checkpoint:** Work was previously paused here. The incident API and ticket-record creation flow are now implemented.

### Sub-phase 3.4: Ticket Record and Dashboard
- Show single ticket details in dashboard
- Show list of open and resolved tickets
- Show AI analysis details for each ticket
- Load ticket records and details from the backend API
- Connect ticket intake to incident analysis and record creation

**Status:** Complete. The dashboard reads ticket records from the API, filters open and resolved tickets, and displays each selected ticket's AI analysis. Ticket intake creates a backend incident record.

### Exit criteria for Phase 3
- A natural language complaint becomes a structured service record
- ServiceNow or mock API creation works
- Ticket record appears in dashboard
- AI classification is visible in UI

### Testing requirement for Phase 3
- Test at least 3 incident-type inputs
- Verify AI output structure matches expected fields
- Confirm ticket creation succeeds and the record is stored
- Confirm the dashboard shows the correct classification data

---

## Phase 4: Automation and Self-Healing Workflow

### Sub-phase 4.1: Define Safe Automation Cases
- Password expired
- Account lockout
- VPN status check
- Service restart
- Cache clearing
- Application restart

### Sub-phase 4.2: Automatable Issue Detection
- Add logic to decide whether an issue is safe to automate
- Add confidence gating for automation safety
- Block unsafe or unclear actions

### Sub-phase 4.3: Automation Execution Layer
- Create mock APIs for each automation task
- Simulate validation steps after execution
- Return results in a structured output

### Sub-phase 4.4: Audit Log Recording
- Save every action and status in an audit collection
- Log step-by-step execution flow
- Store timestamps and automation result data

### Sub-phase 4.5: Incident Update After Automation
- Update ticket status after automation
- Record whether issue was resolved or escalated
- Show the automated action sequence in UI

### Exit criteria for Phase 4
- Self-healing scenario works end-to-end
- Automation steps are logged
- Final ticket status reflects the result
- Demo flow is demonstrable without real system access

### Testing requirement for Phase 4
- Test at least 2 automation flows such as password reset and VPN status
- Verify each action is recorded in the audit log
- Confirm validation succeeds or fails correctly
- Check that the ticket state updates after automation

---

## Phase 5: Software Provisioning Workflow

### Sub-phase 5.1: Software Catalog
- Define software items like Visual Studio Code, Teams, Adobe Reader, VPN client, etc.
- Add request metadata and expected status lifecycle

### Sub-phase 5.2: Request Detection Logic
- Determine if a request is a software provisioning request
- Extract software name and employee context
- Generate request summary

### Sub-phase 5.3: Service Request Creation
- Create a ServiceNow-style service request or mock service request
- Return request ID and status
- Save it to MongoDB

### Sub-phase 5.4: Provisioning Status UI
- Show request ID, software, status, and timestamps in UI
- Display a mock status progression like “Requested → Provisioning → Complete”

### Exit criteria for Phase 5
- User can request software from the UI
- Provisioning request is created successfully
- Status update is visible in the system

### Testing requirement for Phase 5
- Test at least 2 software requests
- Confirm request ID and status appear correctly
- Verify the request record is stored and updated
- Confirm provisioning workflow matches the expected mock lifecycle

---

## Phase 6: Employee Portal and Full UI Experience

### Sub-phase 6.1: Chat Interface
- Employee chat input
- Message history
- Response cards with AI summary and next actions
- Buttons for create ticket / accept resolution / escalate

### Sub-phase 6.2: Dashboard Views
- Ticket counts
- Open / resolved / escalated breakdown
- Automation summary
- Software request summary

### Sub-phase 6.3: AI Analysis Panel
- Display intent, category, confidence, resolution, sources, and ServiceNow reference
- Keep this panel visible during incident and request flows

### Sub-phase 6.4: Knowledge Base View
- Search by keyword
- Filter by category
- Display source references and document metadata

### Exit criteria for Phase 6
- Employee self-service portal is functional
- Dashboard and analysis panel are connected to real data
- User can navigate across all major screens

### Testing requirement for Phase 6
- Verify all major UI screens load and navigate correctly
- Confirm the chat, dashboard, knowledge, and request screens are connected to live data flow
- Check responsiveness and basic usability for the demo

---

## Phase 7: Demo Hardening and Validation

### Sub-phase 7.1: Full End-to-End Scenario Testing
- Validate the five mandatory scenario flows
- Verify AI classification and confidence handling
- Confirm ServiceNow or mock integration output
- Confirm audit logging

### Sub-phase 7.2: Safety and Escalation Checks
- Ensure unknown questions do not hallucinate
- Check confidence threshold and escalation rules
- Verify source attribution for all RAG answers

### Sub-phase 7.3: UI Polish and Stability
- Fix broken flows
- Improve visual hierarchy and readability
- Add loading states and basic validation messages
- Confirm all screens look coherent together

### Sub-phase 7.4: Final Demo Preparation
- Rehearse with hidden timing limits in mind
- Ensure the app can be started locally with minimal effort
- Prepare summary explanation for architecture and use cases

### Exit criteria for Phase 7
- All required flows work reliably
- The application is demo-ready
- The presentation can explain the architecture and business value clearly

### Testing requirement for Phase 7
- Test all five required hackathon scenarios end-to-end
- Verify safe escalation behavior for unknown or weak-confidence requests
- Validate that the demo runs smoothly without patchwork fixes
- Confirm final presentation flow is within the expected time window

---

## Execution Strategy

We will follow this order strictly:
1. Setup and base project
2. Low-end laptop optimization and resource validation before heavy model work
3. Knowledge base + RAG
4. Intent detection + incident workflow
5. Automation + audit trail
6. Software provisioning
7. Portal + dashboard polish
8. Final scenario validation

This phased flow helps us build with more control, easier debugging, and better demo confidence. The optimization gate is mandatory before running embedding and vector-store steps because local machine memory and CPU constraints are a real risk for model-heavy work.

---

## Suggested Completion Rule

Each sub-phase is considered complete only when:
- the feature works standalone,
- the output is visible in the UI or API,
- data is stored correctly,
- and it is ready to connect to the next phase without major rework.

This gives us controlled progression and reduces risk of building features out of order.

---

## Mandatory Testing Rule

Before moving from one phase to the next, we must complete a short validation pass for the previous phase.

Required checks:
- Run the relevant startup/build command
- Verify the feature works in isolation
- Validate the expected output with real sample input
- Confirm the data is saved/updated correctly
- Check system stability before heavy model operations, especially on low-end machines
- Record any issues and fix them before proceeding

A phase is not considered complete until it passes its own testing gate.