# Azure App Service Deployment Guide

This repo is structured for deployment as **two separate Azure Web Apps** from one repository:

- `/backend` → Backend FastAPI Web App
- `/frontend` → Frontend Streamlit Web App

---

## Recommended Deployment Model

```
Users
  │
  ▼
Frontend Web App  (Streamlit)          e.g. https://mangos-frontend.azurewebsites.net
  │  calls via HTTP/SSE
  ▼
Backend Web App   (FastAPI + Gunicorn) e.g. https://mangos-backend.azurewebsites.net
  │
  ├── Azure OpenAI (commercial Azure)
  └── Azure AI Search (commercial Azure)
```

Share **only the frontend URL** with stakeholders. All Azure secrets stay in backend App Settings.

---

## 1. Backend Deployment

### Create the Web App

- **OS**: Linux
- **Runtime**: Python 3.11 (or 3.12)
- **Pricing tier**: B2 or higher (streaming + gunicorn workers need adequate memory)

### Deploy the `/backend` folder only

Using Azure CLI:
```bash
cd backend
zip -r ../backend.zip .
az webapp deploy --resource-group <rg> --name <backend-app-name> \
    --src-path ../backend.zip --type zip
```

Or use VS Code Azure App Service extension → right-click `/backend` → Deploy to Web App.

### Startup command

In **Configuration → General settings → Startup Command**:
```
gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app
```

### Required App Settings (Configuration → Application settings)

| Setting | Value |
|---|---|
| `AZURE_OPENAI_ENDPOINT` | `https://<resource>.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | `<key>` |
| `AZURE_OPENAI_API_VERSION` | `2024-06-01` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | `<chat-deployment-name>` |
| `AZURE_OPENAI_CHAT_DEPLOYMENT_NAME` | `<chat-deployment-name>` |
| `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT` | `<embeddings-deployment-name>` |
| `AZURE_SEARCH_ENDPOINT` | `https://<search>.search.windows.net` |
| `AZURE_SEARCH_API_KEY` | `<search-key>` |
| `AZURE_SEARCH_INDEX` | `rag-mangostechm-index-finalv2` |
| `ALLOWED_ORIGINS` | `https://<frontend-app-name>.azurewebsites.net` |
| `TRACE_MODE` | `true` (set to `false` in production to reduce log noise) |

Field mapping settings use sensible defaults matching the index schema, so you only need to set them if your index differs from the defaults. See `.env.backend.example` for the full list.

### Test the backend health endpoint

```
https://<backend-app-name>.azurewebsites.net/health
```

Expected response:
```json
{"status": "ok"}
```

---

## 2. Frontend Deployment

### Create the Web App

- **OS**: Linux
- **Runtime**: Python 3.11 (or 3.12)
- **Pricing tier**: B1 or higher

### Deploy the `/frontend` folder only

Using Azure CLI:
```bash
cd frontend
zip -r ../frontend.zip .
az webapp deploy --resource-group <rg> --name <frontend-app-name> \
    --src-path ../frontend.zip --type zip
```

Or use VS Code Azure App Service extension → right-click `/frontend` → Deploy to Web App.

### Startup command

In **Configuration → General settings → Startup Command**:
```
python -m streamlit run app.py --server.port 8000 --server.address 0.0.0.0
```

> Note: Azure App Service routes external traffic to port 8000 by default for Python apps. Streamlit must bind to this port.

### Required App Settings (Configuration → Application settings)

| Setting | Value |
|---|---|
| `BACKEND_URL` | `https://<backend-app-name>.azurewebsites.net` |
| `FRONTEND_TITLE` | `MANGOS Tech Manual Agent` (optional) |

### Share the frontend URL

```
https://<frontend-app-name>.azurewebsites.net
```

This is the URL you give to stakeholders. They open it in any browser and the chatbot is ready to use.

---

## 3. Local Development

### Backend (from repo root or backend folder)

```bash
cd backend
pip install -r requirements.txt
# Copy .env.backend.example to .env and fill in your values
cp ../.env.backend.example .env
uvicorn app.main:app --reload --port 8000
```

Health check: http://localhost:8000/health

### Frontend (from repo root or frontend folder)

```bash
cd frontend
pip install -r requirements.txt
# Copy .env.frontend.example to .env and fill in your values
cp ../.env.frontend.example .env
streamlit run app.py
```

Frontend opens at: http://localhost:8501

---

## 4. Notes

### CORS
The backend `ALLOWED_ORIGINS` env var should list the frontend App Service URL in production:
```
ALLOWED_ORIGINS=https://mangos-frontend.azurewebsites.net
```
Defaults to `*` (allow all) if not set, which is fine for internal/dev deployments.

### Secrets
All Azure credentials (`AZURE_OPENAI_API_KEY`, `AZURE_SEARCH_API_KEY`) belong in **backend** App Settings only. The frontend has no access to these — it only needs `BACKEND_URL`.

### Streaming
The backend uses Server-Sent Events (SSE) for streaming. Azure App Service supports SSE natively. If you place a CDN or Front Door in front of the backend, ensure streaming / chunked transfer is not buffered.

### Session memory
The backend uses in-memory session storage (`InMemoryHistoryProvider`). Multi-turn memory is maintained per process. If you scale to multiple instances, sessions may not persist across instances — this is acceptable for the current dev deployment.

### Scaling
- Backend: start with 2 gunicorn workers (`-w 2`). Increase workers or scale up the App Service plan if latency is high under load.
- Frontend: Streamlit is single-process; scale out by increasing instance count if needed.

### Logs
Backend logs include `TRACE |` prefixed lines showing retrieval pipeline details. View them in **Log stream** in the Azure portal. Set `TRACE_MODE=false` to reduce verbosity once the deployment is validated.
