# AI-Powered ITSM Helpdesk

A hackathon prototype for an employee IT helpdesk. The intended product combines a React portal, a FastAPI service, MongoDB-backed records, grounded knowledge search, and simulated or ServiceNow-based workflows.

## Current Status

The repository currently contains the React app shell, FastAPI app shell, health endpoints, MongoDB connection and collection initialization, shared data models, and a small automated test suite. The AI, retrieval, and ticketing workflows are planned but are not connected end to end yet.

## Technology and Structure

- Frontend: React 18 and Vite
- Backend: Python 3.10+ and FastAPI
- Database foundation: PyMongo with configurable MongoDB URI
- Data contracts: Pydantic models in `backend/app/schemas.py`
- Frontend source: `frontend/src/`
- Backend source: `backend/app/`
- Knowledge document location: `data/knowledge_docs/`
- Tests: `tests/`
- API contract notes: `docs/api_contracts.md`

## Prerequisites

- Windows with PowerShell, Node.js 18+ and npm
- Python 3.10+
- A local MongoDB service or MongoDB Atlas account for database-backed work; the API can start without a reachable database

If PowerShell reports that `npm` is not recognized after installing Node.js, open a new terminal or add the Node.js install directory to the current session's PATH. For the default Windows installation:

```powershell
$env:Path += ';C:\Program Files\nodejs'
```

## Setup

Run these commands from the repository root.

### Frontend dependencies

```powershell
Set-Location 'D:\AI_HACKATHON_FRESHER\frontend'
npm.cmd install
```

### Backend environment and dependencies

```powershell
Set-Location 'D:\AI_HACKATHON_FRESHER'
py -3.10 -m venv backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
```

If the virtual environment already exists, skip the `venv` command.

### Environment variables

Create a local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Set `MONGODB_URI` to your local MongoDB URI or Atlas connection string and adjust `MONGODB_DB` if needed. Keep real credentials in `.env`; do not commit them. The model and ServiceNow variables are placeholders for later phases and are not currently loaded by an AI or ServiceNow integration.

## Run Locally

Open separate PowerShell terminals.

### Backend

```powershell
Set-Location 'D:\AI_HACKATHON_FRESHER\backend'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

If port `8001` is already occupied, stop the existing backend with `Ctrl+C` in its terminal, or use another port such as `8002`.

### Frontend

```powershell
Set-Location 'D:\AI_HACKATHON_FRESHER\frontend'
npm.cmd run dev
```

Vite prints the frontend URL when it starts, normally `http://localhost:5173`.

### Backend URLs

- App status: `http://127.0.0.1:8001/`
- Health check: `http://127.0.0.1:8001/health`
- Versioned health check: `http://127.0.0.1:8001/api/v1/health`
- Interactive API docs: `http://127.0.0.1:8001/docs`

On startup, the backend reads MongoDB configuration, prepares handles for the `tickets`, `knowledge`, `chat`, `audit`, and `software_requests` collections, and creates missing collections if MongoDB is reachable. If MongoDB is unavailable, the API logs a warning and continues in a degraded mode; database persistence is then unavailable.

## Tests and Build

Run the backend tests from the repository root:

```powershell
Set-Location 'D:\AI_HACKATHON_FRESHER'
.\backend\.venv\Scripts\python.exe -m unittest discover -s tests
```

Build the frontend:

```powershell
Set-Location 'D:\AI_HACKATHON_FRESHER\frontend'
npm.cmd run build
```

## Chunk and Embed Knowledge Articles

Install the backend dependencies, then run the pipeline from the repository root:

```powershell
Set-Location 'D:\AI_HACKATHON_FRESHER'
.\backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.\backend\.venv\Scripts\python.exe -m backend.app.knowledge_pipeline
```

The first run downloads the model configured by `EMBEDDING_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`). The pipeline writes chunk text, normalized embedding vectors, and source metadata as JSON Lines to `data/embeddings/knowledge_chunks.jsonl`. Use `--max-chars` to change the approximate maximum chunk length.

## Build and Query the Knowledge Vector Store

After generating the embedding artifact, index its vectors into the persistent Chroma collection:

```powershell
Set-Location 'D:\AI_HACKATHON_FRESHER'
.\backend\.venv\Scripts\python.exe -m backend.app.knowledge_vector_store
```

Run a semantic search with exact category and topic filters:

```powershell
.\backend\.venv\Scripts\python.exe -m backend.app.knowledge_vector_store --query "VPN connection keeps failing" --category Network --topic VPN --limit 5
```

Chroma persists its local index under `data/vector_store/chroma` by default. Set `CHROMA_PERSIST_DIRECTORY` or `CHROMA_COLLECTION_NAME` in `.env` to customize it.

## Planned Data Flow

The target flow is employee request -> React frontend -> FastAPI -> intent and knowledge processing -> MongoDB records and optional ITSM integration. The repository currently includes the application shells, database foundation, data contracts, demo knowledge articles, chunking and embeddings, and a persistent vector store.

## Limitations and Assumptions

- The MongoDB layer initializes collections but application CRUD workflows and sample-record seeding are not implemented.
- The seven knowledge articles are generic demo examples, not organization-approved support policy.
- The retrieval API and grounded answer generation are not implemented yet; the vector store is currently accessed through its indexing and search CLI.
- ServiceNow credentials are placeholders; neither a real integration nor a mock ServiceNow API has been built.
- Frontend screens are a navigation shell and are not yet connected to backend workflows or persistent data.
- CORS currently permits all origins for development. Restrict allowed origins before deployment.
- No production authentication, authorization, secrets management, or deployment configuration is included.
