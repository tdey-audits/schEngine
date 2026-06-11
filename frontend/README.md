# schEngine Frontend

Next.js paper-builder workspace for the CBSE Class 10 Mathematics generation API.

## Run locally

From the repo root, start the FastAPI backend:

```bash
.backend-venv/bin/python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Then start the frontend:

```bash
cd frontend
npm run dev
```

Open:

```text
http://localhost:3000
```

The frontend proxies `/api/v1/*` to the backend. Override the backend URL with:

```bash
SCHENGINE_API_BASE=http://127.0.0.1:8000 npm run dev
```

## Build

```bash
npm run build
```
