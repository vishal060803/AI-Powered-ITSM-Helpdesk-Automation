# Fast Project Execution Plan

This plan is designed to finish the project with lower token and development overhead while keeping the quality intact. The goal is not to skip validation, but to reduce unnecessary exploration, avoid duplicate work, and keep each phase small and measurable.

---

## Objective

Complete the project efficiently by:
- using the already working backend/frontend foundation
- focusing only on required features for the final demo
- avoiding broad exploration or speculative implementation
- validating each phase with minimal smoke tests
- reusing existing architecture and code patterns already in the repo

---

## Core Execution Rules

### 1. Do not start new work without a clear deliverable
Every step must answer one question:
- What is the smallest feature that moves the project forward?
- What can be validated in under 5 minutes?

### 2. Reuse existing code before creating new files
Before adding anything new:
- check whether a route, schema, utility, or test pattern already exists
- extend existing modules instead of creating parallel implementations
- keep naming and structure consistent with the current repo

### 3. Limit scope to the final demo path
Do not build extra features not required for the final working demo. Keep focus on:
- backend app shell
- Mongo-ready setup
- knowledge docs and retrieval API
- simple frontend UI shell
- working request flow and answer display

### 4. Use minimal validation, not broad testing
Use short smoke tests instead of full-suite exploration:
- backend health checks
- one retrieval query
- one frontend build check
- one end-to-end request path

### 5. Prefer stable, already-validated dependencies
Do not reintroduce heavy or experimental stacks.
- Use CPU-friendly Python setup for Linux
- keep the same FastAPI + React structure already working
- avoid unnecessary package churn

---

## Recommended Project Finish Strategy

### Phase A: Stabilize the foundation
1. Confirm backend starts successfully with the working CPU-safe environment.
2. Confirm frontend build runs successfully.
3. Confirm health endpoints and retrieval endpoint respond.
4. Fix only blockers, not general cleanup.

Deliverable: app runs locally without startup issues.

### Phase B: Keep the working knowledge flow only
1. Use the existing markdown knowledge docs.
2. Reuse the current chunking and vector store logic.
3. Confirm the search API returns ranked knowledge results.
4. Show source article metadata clearly in the response.

Deliverable: a working knowledge Q&A flow.

### Phase C: Complete the minimal user request flow
1. Build a basic frontend form for user questions or incident requests.
2. Connect the frontend to the backend retrieval endpoint.
3. Show result cards with source metadata.
4. Add a minimal loading and error state.

Deliverable: user can submit a request and see response.

### Phase D: Optional but minimal improvement
Only if time remains:
- add a simple dashboard card
- add a status display for request processing
- improve the UI styling slightly

Do not do large system expansion beyond this point.

---

## Fast Decision Tree

### If a task is already implemented
- use it
- validate it
- don’t rewrite it

### If a task is partially implemented
- finish the missing part only
- do not redesign the surrounding module

### If a task is uncertain
- implement the smallest working version
- validate immediately
- avoid deep refactors

### If a feature is not needed for the final demo
- postpone it
- do not spend token budget on it

---

## Validation Checklist (Minimal but Sufficient)

### Backend
- run app successfully
- `/health` returns status OK
- `/api/v1/health` returns status OK
- knowledge search returns ranked results

### Frontend
- npm install works
- npm build works
- vite dev server starts
- page loads without blank screen

### End-to-end
- user submits a question
- API responds with results
- UI displays the answer and source info

---

## Recommended Execution Order

1. Backend startup validation
2. Frontend build validation
3. Retrieval API validation
4. Frontend-to-backend connection
5. Minimal polished UI
6. Final smoke test

This ordering keeps the work linear, reduces debugging confusion, and avoids wasted time on features that are not needed for the final result.

---

## Token-Efficient Working Pattern

Use this loop for every task:
1. Identify the exact missing feature.
2. Read only the relevant file(s).
3. Implement the smallest fix.
4. Run the smallest possible validation.
5. Move to the next item.

This reduces context churn and keeps the project moving without quality loss.

---

## Final Principle

Finish the project by building the shortest reliable path to a working demo, not by building the broadest system possible. The project is already structured well enough to move quickly. The best way to stay efficient is to stay narrow, validate early, and avoid duplicates.

---

## Immediate Next Tasks

1. Confirm backend health and retrieval API are working in the selected environment.
2. Confirm frontend dev server starts correctly.
3. Connect the main frontend form to the backend search endpoint.
4. Show retrieval result cards with source information.
5. Run one final smoke test and stop once the demo works.
