# Demo Runbook (Phase 7.4)

## 1) Startup with Minimal Effort

Run these in two terminals.

Terminal A (backend):
```bash
cd "/media/hp/New Volume/AI_HACKATHON_FRESHER"
source .venv/bin/activate
export MONGODB_URI="mongodb://127.0.0.1:27017"
export MONGODB_DB="itsm_ai"
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal B (frontend):
```bash
cd "/media/hp/New Volume/AI_HACKATHON_FRESHER"
npm run frontend:dev
```

UI URL: `http://127.0.0.1:5173`  
API docs: `http://127.0.0.1:8000/docs`

---

## 2) Hidden-Timing Rehearsal Plan (8–10 minutes)

### Minute 0–1: Setup proof
- Show backend health (`/api/v1/health`) and app home page.
- Mention that MongoDB can be live or fallback-safe in memory for demo continuity.

### Minute 1–3: Scenario 1 (Intelligent Ticket Intake)
- In Chat, submit a VPN incident sentence.
- Show AI analysis panel (intent/category/confidence/sources).
- Create ticket and switch to Dashboard.

### Minute 3–5: Scenario 2 (Self-Heal + Audit)
- Use a password-expired ticket flow.
- Execute safe automation.
- Show final ticket status (`auto-resolved`) and automation summary/audit visibility.

### Minute 5–6.5: Scenario 3 (Knowledge Management)
- Open Knowledge Base and run Outlook query.
- Show grounded answer + source references + metadata.

### Minute 6.5–8: Scenario 4 (Safety / Escalation)
- Ask an unsafe/unknown question.
- Show low-confidence refusal + escalation-safe behavior.

### Minute 8–9.5: Scenario 5 (Software Provisioning)
- Open Requests tab, submit software request.
- Show request ID, lifecycle progression, and ServiceNow-style reference.

### Minute 9.5–10: Wrap-up
- Summarize architecture and business value in 30–45 seconds.

---

## 3) Architecture Summary (Presentation-ready)

- **Frontend (`React + Vite`)**: Employee portal with Chat, Dashboard, Knowledge Base, and Requests pages.
- **Backend (`FastAPI`)**: API orchestration for chat analysis, incident creation, automation execution, software requests, and dashboard data.
- **Knowledge Layer (`Sentence Transformers + Chroma`)**: Retrieves approved knowledge chunks and provides source-attributed grounded responses.
- **Persistence (`MongoDB + in-memory fallback`)**: Stores tickets, automation logs, and software requests when available; fallback keeps demo robust.
- **Integration Layer (ServiceNow-style mock)**: Returns realistic incident/request references and payload contracts.

---

## 4) Use Cases (Business Value)

1. **Intelligent Ticket Intake**: Natural-language issue becomes structured ITSM record.
2. **Auto Resolution / Self-Heal**: Safe, confidence-gated actions reduce manual load.
3. **Knowledge Management**: Grounded answers reduce hallucination and improve trust.
4. **Employee Self-Service Portal**: Faster support experience and transparent next actions.
5. **Software Provisioning Automation**: Standardized request lifecycle with visible status.

---

## 5) Demo Fallback Plan (If Anything Fails)

- If MongoDB is down: continue with in-memory mode and state that persistence fallback is intentional for resiliency.
- If one API call fails: switch to a known-good scenario input (VPN or password-expired).
- If time is cut: show Scenarios 1, 2, and 5 only, then close with architecture summary.
