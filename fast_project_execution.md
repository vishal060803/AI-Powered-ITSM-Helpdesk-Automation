### Fast Run (Linux Bash)

## One-time setup

```bash
cd "/media/hp/New Volume/AI_HACKATHON_FRESHER"
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r backend/requirements.txt
npm --prefix frontend install
```

## Run backend

```bash
cd "/media/hp/New Volume/AI_HACKATHON_FRESHER"
source .venv/bin/activate
export MONGODB_URI="mongodb://127.0.0.1:27017"
export MONGODB_DB="itsm_ai"
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Run frontend

```bash
cd "/media/hp/New Volume/AI_HACKATHON_FRESHER"
npm run frontend:dev
```

## Quick health checks

```bash
curl "http://127.0.0.1:8000/api/v1/health"
curl "http://127.0.0.1:8000/api/v1/software/catalog"
```
