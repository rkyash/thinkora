# Thinkora Troubleshooting Guide

Welcome to the Thinkora Troubleshooting Guide. This document consolidates solutions for common issues encountered during installation, development, and operation of the Thinkora application.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation & Setup Issues](#installation--setup-issues)
- [Database Issues](#database-issues)
- [Backend Issues](#backend-issues)
- [AI & LLM Issues](#ai--llm-issues)
- [Document Processing Issues](#document-processing-issues)
- [Frontend Issues](#frontend-issues)
- [Vector Database Issues](#vector-database-issues)
- [Docker Issues](#docker-issues)
- [Nuclear Reset](#nuclear-reset)
- [Getting Help](#getting-help)

---

## Quick Diagnostics

Before diving into specific issues, run through these quick diagnostic steps:

1. **Check Docker Status**: Ensure Docker is running.
   ```bash
   docker info
   ```
2. **Check Container Logs**: View the logs for any container that is failing or restarting.
   ```bash
   docker compose logs <service-name>
   # Example: docker compose logs api
   ```
3. **Verify Environment Variables**: Ensure your `.env` file exists and is populated correctly (especially `DATABASE_URL`, API keys, etc.).
   ```bash
   cat .env
   ```
4. **Check Service Health**: Verify if the backend API is up.
   ```bash
   curl -I http://localhost:8000/api/v1/health
   ```

---

## Installation & Setup Issues

### Docker daemon not running
- **Symptom**: `Cannot connect to the Docker daemon at unix:///var/run/docker.sock.`
- **Cause**: Docker service is stopped or the user lacks permissions.
- **Solution**:
  Start the Docker service:
  ```bash
  sudo systemctl start docker
  ```
  *(Linux)* Ensure your user is in the `docker` group:
  ```bash
  sudo usermod -aG docker $USER
  ```

### Port conflicts
- **Symptom**: Error starting containers: `Bind for 0.0.0.0:<port> failed: port is already allocated`.
- **Cause**: Ports 5434 (PostgreSQL), 6379 (Redis), 6333 (Qdrant), 8000 (API), or 5173 (Frontend) are in use by other processes.
- **Solution**:
  Find the process using the port and stop it:
  ```bash
  lsof -i :<port>
  kill -9 <PID>
  ```
  Alternatively, update the port mapping in `docker-compose.yml` or `.env`.

### Permission denied errors
- **Symptom**: `Permission denied` when running `./start.sh` or writing to data directories.
- **Cause**: Script isn't executable or Docker volumes lack correct ownership.
- **Solution**:
  Make scripts executable:
  ```bash
  chmod +x start.sh
  ```
  Fix data directory permissions (if mapped locally):
  ```bash
  sudo chown -R 1000:1000 ./data
  ```

### Python/Node version mismatches
- **Symptom**: Syntax errors or missing features during local non-Docker development.
- **Cause**: Using an older version of Python (< 3.11) or Node.js.
- **Solution**:
  Use `nvm` for Node and `pyenv` for Python.
  ```bash
  nvm use 20
  pyenv global 3.11.0
  ```

---

## Database Issues

### PostgreSQL connection refused
- **Symptom**: Backend startup fails with `ConnectionRefusedError: [Errno 111] Connect call failed`.
- **Cause**: Postgres container is not running or hasn't finished initializing.
- **Solution**:
  Check if Postgres is running:
  ```bash
  docker compose ps postgres
  ```
  Wait a few seconds for initialization to complete before starting the backend.

### Alembic migration failures
- **Symptom**: `alembic.util.exc.CommandError: Can't locate revision identified by...` or relation already exists.
- **Cause**: Database schema is out of sync with migration scripts.
- **Solution**:
  If safe (e.g., development environment), reset the database (see Database reset procedure). Otherwise, mark the current revision:
  ```bash
  docker compose exec api alembic stamp head
  ```

### Database reset procedure
- **Symptom**: Corrupt data or unrecoverable schema state.
- **Cause**: Breaking changes in models or manual tampering.
- **Solution**:
  > [!WARNING]
  > This will delete ALL data in your local PostgreSQL database.

  ```bash
  docker compose down -v postgres
  docker compose up -d postgres
  docker compose exec api alembic upgrade head
  ```

### Connection pool exhaustion
- **Symptom**: `TimeoutError: QueuePool limit of size <N> overflow <M> reached`.
- **Cause**: High concurrency or leaked database sessions.
- **Solution**:
  Restart the API service:
  ```bash
  docker compose restart api
  ```
  Ensure backend code uses `async with session` to properly close connections.

---

## Backend Issues

### Import errors / module not found
- **Symptom**: `ModuleNotFoundError: No module named 'xyz'`.
- **Cause**: Missing dependencies or running outside the virtual environment.
- **Solution**:
  If local:
  ```bash
  poetry install  # or pip install -r requirements.txt
  ```
  If Docker: Rebuild the image.
  ```bash
  docker compose build api
  ```

### Pydantic validation errors
- **Symptom**: 422 Unprocessable Entity responses from API.
- **Cause**: Request payload does not match Pydantic v2 schemas.
- **Solution**:
  Check the API logs to see which field is missing or incorrectly typed, and update the frontend payload or API request accordingly.

### CORS errors
- **Symptom**: Browser console shows `Access to fetch at '...' from origin '...' has been blocked by CORS policy`.
- **Cause**: `CORS_ORIGINS` in backend `.env` does not include the frontend URL.
- **Solution**:
  Update `.env`:
  ```env
  CORS_ORIGINS=["http://localhost:5173", "http://localhost:80"]
  ```
  Restart the API container.

### Authentication failures
- **Symptom**: 401 Unauthorized for valid requests.
- **Cause**: Expired token, changed `SECRET_KEY`, or mismatched `AUTH_ENABLED` settings.
- **Solution**:
  Log out and log in again. Ensure `AUTH_ENABLED` is consistent across your environment.

---

## AI & LLM Issues

### Empty model error / BadRequestError
- **Symptom**: `LiteLLMError: Model parameter is empty` or `BadRequestError`.
- **Cause**: Default model is not set or the requested model does not exist.
- **Solution**:
  Ensure `DEFAULT_MODEL` is set in `.env` and matches a model supported by your active provider.

### LiteLLM provider not configured
- **Symptom**: `ValueError: No API key provided for <provider>`.
- **Cause**: Missing API keys in `.env`.
- **Solution**:
  Add the required key (e.g., `OPENAI_API_KEY`) to `.env` and restart the backend.

### API key invalid or expired
- **Symptom**: 401 Unauthorized from OpenAI, Anthropic, etc.
- **Cause**: The provided API key is incorrect, expired, or out of credits.
- **Solution**:
  Verify the key in the provider's dashboard and update your `.env` file.

### Ollama connection issues
- **Symptom**: `Connection refused` when connecting to Ollama.
- **Cause**: Ollama is not running, or `OLLAMA_BASE_URL` is pointing to `localhost` instead of `host.docker.internal` (when API is in Docker).
- **Solution**:
  If using Docker, set:
  ```env
  OLLAMA_BASE_URL=http://host.docker.internal:11434
  ```

### Embedding model download failures
- **Symptom**: Backend hangs or crashes on startup while loading sentence-transformers.
- **Cause**: Network restriction or timeout downloading `all-MiniLM-L6-v2` from Hugging Face.
- **Solution**:
  Set up a proxy or manually download the model to the local cache directory specified by `THINKORA_DATA_DIR`.

---

## Document Processing Issues

### Documents stuck in PROCESSING status
- **Symptom**: Document status remains `PROCESSING` indefinitely.
- **Cause**: Celery worker crashed, or the task was lost.
- **Solution**:
  Check worker logs:
  ```bash
  docker compose logs worker
  ```
  Delete the stuck document and re-upload.

### Celery worker not running
- **Symptom**: Tasks are queued but never start.
- **Cause**: Worker container failed to start.
- **Solution**:
  Verify Redis is running. Restart the worker:
  ```bash
  docker compose restart worker
  ```

### Redis broker connection failed
- **Symptom**: `kombu.exceptions.OperationalError: Error 111 connecting to redis:6379`.
- **Cause**: Redis container is down or unreachable.
- **Solution**:
  Ensure Redis is running:
  ```bash
  docker compose up -d redis
  ```

### Out of memory during large file processing
- **Symptom**: Worker container exits with code 137 (OOM Killer).
- **Cause**: Processing a very large PDF or generating huge embeddings exhausted container RAM.
- **Solution**:
  Increase memory limit for the worker container in `docker-compose.yml` or allocate more RAM to Docker Desktop.

### Unsupported file format
- **Symptom**: Upload fails with 400 Bad Request or processing fails immediately.
- **Cause**: Uploaded file extension is not supported by the parsers.
- **Solution**:
  Convert the file to a supported format (PDF, DOCX, TXT, MD) and retry.

---

## Frontend Issues

### Blank page / build errors
- **Symptom**: White screen on load or Vite build fails.
- **Cause**: TypeScript errors or missing packages.
- **Solution**:
  Run standard frontend checks:
  ```bash
  npm install
  npm run build
  ```

### API connection refused
- **Symptom**: Network error in browser console, unable to fetch data.
- **Cause**: Frontend pointing to wrong backend URL, or backend is down.
- **Solution**:
  Check `VITE_API_URL` in the frontend `.env`. Default should be `http://localhost:8000/api/v1`.

### State management debugging
- **Symptom**: UI not updating properly after actions.
- **Cause**: Zustand store state out of sync.
- **Solution**:
  Install the React DevTools and Redux DevTools extensions in your browser to inspect Zustand stores. Hard refresh (`Ctrl+F5`) to reset state.

---

## Vector Database Issues

### Qdrant connection errors
- **Symptom**: `RpcError: StatusCode.UNAVAILABLE` when chatting or uploading.
- **Cause**: Qdrant container is down or unreachable.
- **Solution**:
  ```bash
  docker compose restart qdrant
  ```

### Collection not found
- **Symptom**: `qdrant_client.http.exceptions.UnexpectedResponse: Collection <notebook_id> not found`.
- **Cause**: Qdrant volume was deleted, but PostgreSQL still has the notebook record.
- **Solution**:
  Re-process the documents in the notebook or delete the notebook and recreate it.

### Search returning empty results
- **Symptom**: AI chat says it doesn't have context, despite documents being processed.
- **Cause**: Embedding mismatch or Qdrant index issues.
- **Solution**:
  Verify the `EMBEDDING_MODEL` hasn't changed. If it did, you must re-upload and re-embed all documents.

---

## Docker Issues

### Container keeps restarting
- **Symptom**: `docker ps` shows container status as `Restarting`.
- **Cause**: Application crashing on startup due to misconfiguration.
- **Solution**:
  Inspect logs:
  ```bash
  docker compose logs <container-name>
  ```
  Look for missing environment variables or connection errors.

### Volume mount problems
- **Symptom**: Code changes aren't reflected in the container, or data isn't persisting.
- **Cause**: Incorrect paths in `docker-compose.yml` or OS-level file sharing restrictions.
- **Solution**:
  Verify volume paths. On Windows/Mac, ensure the project directory is allowed in Docker Desktop file sharing settings.

### Network issues between containers
- **Symptom**: API can't reach PostgreSQL or Qdrant using container hostnames.
- **Cause**: Custom Docker network missing or misconfigured.
- **Solution**:
  Ensure all services are attached to the same network in `docker-compose.yml`. Recreate networks:
  ```bash
  docker compose down
  docker compose up -d
  ```

---

## Nuclear Reset

If everything is completely broken and you want to start from absolute zero, you can perform a nuclear reset.

> [!CAUTION]
> This will permanently delete ALL your local data, including users, workspaces, documents, and vector embeddings. This action cannot be undone.

1. Stop all containers and remove volumes:
   ```bash
   docker compose down -v
   ```
2. Remove local data directories (if mapped):
   ```bash
   sudo rm -rf ./data
   ```
3. Rebuild and start:
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

---

## Getting Help

If this guide didn't solve your problem:
1. Search the [GitHub Issues](https://github.com/rkyash/thinkora/issues) for similar problems.
2. Open a new issue, including:
   - Your OS and environment details
   - Docker and Docker Compose versions
   - Relevant logs (`docker compose logs`)
   - Steps to reproduce the issue
