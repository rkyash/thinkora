# Thinkora Backend

This directory contains the backend API for Thinkora, built with [FastAPI](https://fastapi.tiangolo.com/) and Python 3.11+. It handles AI orchestration, document processing, database interactions, and real-time streaming for chat and task progress.

## Architecture

The backend follows a strict layered architecture: **Router → Service → Repository → Model**.

* **Router**: Handles HTTP requests/responses, payload validation, and passes data to services.
* **Service**: Contains business logic, AI interactions, and orchestrates actions across multiple repositories.
* **Repository**: Handles all database interactions using SQLAlchemy.
* **Model**: SQLAlchemy models defining the database schema.

## Project Structure

```
backend/
├── app/
│   ├── api/          # Routers (endpoints) grouped by API version (v1/)
│   ├── bootstrap/    # App startup and initialization scripts
│   ├── core/         # Configuration, security, database setup, dependencies
│   ├── events/       # SSE event handling for real-time updates
│   ├── middlewares/  # Custom middleware (CORS, logging, etc.)
│   ├── models/       # SQLAlchemy ORM models
│   ├── repositories/ # Data access layer
│   ├── schemas/      # Pydantic schemas for request/response validation
│   ├── services/     # Business logic layer (LLM, RAG, Parsing)
│   ├── workers/      # Celery task definitions (document processing, etc.)
│   └── main.py       # FastAPI application entry point
├── tests/            # Pytest test suite
├── alembic/          # Database migrations
├── alembic.ini       # Alembic configuration
├── requirements.txt  # Project dependencies
└── Makefile          # Common commands
```

## Setup Instructions

1. **Prerequisites**: Python 3.11+ is required. Make sure Postgres, Redis, and Qdrant are running (see the main project `docker-compose.dev.yml`).

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Migrations**:
   Ensure `DATABASE_URL` is set in your environment, then run:
   ```bash
   alembic upgrade head
   ```

5. **Start the Development Server**:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Common Commands (Makefile)

Use the provided `Makefile` for convenience (from the project root):
* `make up` - Start all production containers.
* `make down` - Stop all containers.
* `make infra-up` - Start only infrastructure services (Postgres, Redis, Qdrant) for local dev.
* `make infra-down` - Stop infrastructure services.
* `make infra-logs` - View infrastructure logs.

## Testing

Tests are written using `pytest`.

To run the test suite:
```bash
pytest
```

## Key Dependencies

| Dependency | Purpose |
|---|---|
| **FastAPI** | High-performance API framework |
| **SQLAlchemy 2.0** | Async ORM for Postgres interaction |
| **Pydantic v2** | Data validation and serialization |
| **Alembic** | Database migrations |
| **LiteLLM** | Multi-LLM provider proxy |
| **LangChain / LangGraph** | AI/RAG orchestration and pipelines |
| **sentence-transformers** | Local embeddings (all-MiniLM-L6-v2) |
| **Celery** | Asynchronous task queue for document processing |

## Documentation

For full project documentation, see the [main documentation](../README.md).
