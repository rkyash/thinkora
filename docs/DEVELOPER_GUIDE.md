# Thinkora Developer Guide

Welcome to the Thinkora Developer Guide! This document provides everything you need to set up your development environment, understand the architecture, and start contributing to Thinkora.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Manual Setup](#manual-setup)
4. [Service URLs](#service-urls)
5. [Backend Development](#backend-development)
   - [Code Quality — Run Before Pushing](#code-quality--run-before-pushing)
6. [Frontend Development](#frontend-development)
7. [Database Migrations](#database-migrations)
8. [Docker Commands](#docker-commands)
9. [IDE Setup](#ide-setup)
10. [Debugging Tips](#debugging-tips)
11. [Common Development Tasks](#common-development-tasks)

---

## Prerequisites

Before you begin, ensure you have the following installed on your machine:

- **Docker & Docker Compose**: For running infrastructure (Database, Redis, Qdrant).
- **Python 3.11+**: For backend development.
- **Node.js 18+ & npm**: For frontend development.
- **Git**: For version control.

---

## Quick Start

The easiest way to get the entire stack running is using the provided start script.

```bash
./start.sh
```

**What it does:**
- Checks and verifies dependencies.
- Copies example `.env` files if they don't exist.
- Starts infrastructure using Docker Compose (Postgres, Redis, Qdrant).
- Sets up the Python virtual environment and installs backend dependencies.
- Runs database migrations.
- Installs frontend dependencies.
- Starts the backend, frontend, and Celery worker in a single terminal using a multiplexer or background processes.

---

## Manual Setup

If you prefer to run services individually for better control and debugging, follow these steps:

### 1. Infrastructure

Start the supporting services (Postgres, Redis, Qdrant) using the `make` command:

```bash
make infra-up
```

### 2. Backend

Open a new terminal and navigate to the backend directory:

```bash
cd backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend

Open another terminal and navigate to the frontend directory:

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

---

## Service URLs

When running locally, the services are available at the following URLs:

| Service | URL / Port | Description |
|---|---|---|
| Frontend | [http://localhost:5173](http://localhost:5173) | Vite development server |
| Backend API | [http://localhost:8000](http://localhost:8000) | FastAPI application |
| Swagger Docs | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API documentation |
| PostgreSQL | `localhost:5434` | Relational database (custom port to avoid conflicts) |
| Redis | `localhost:6379` | Message broker and caching |
| Qdrant | `localhost:6333` | Vector database |

---

## Backend Development

The backend uses FastAPI and follows a layered architecture pattern: **Router → Service → Repository → Model**.

### Architecture Rules

- **Routers (`app/api/v1/`)**: Handle HTTP requests/responses, validate inputs using schemas, and call services. They should contain minimal business logic.
- **Services (`app/services/`)**: Contain the core business logic. They call repositories for data access and coordinate different operations.
- **Repositories (`app/repositories/`)**: Handle all direct database operations (SQLAlchemy queries). Services should not write queries directly.
- **Models (`app/models/`)**: Define the SQLAlchemy database schema.

### Adding a New Endpoint

1. **Create/Update Schemas (`app/schemas/`)**:
   ```python
   # app/schemas/item.py
   from pydantic import BaseModel

   class ItemCreate(BaseModel):
       name: str
       description: str | None = None
   ```

2. **Create/Update Repository (`app/repositories/`)**:
   ```python
   # app/repositories/item_repo.py
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.models.item import Item

   async def create_item(db: AsyncSession, item_data: dict):
       new_item = Item(**item_data)
       db.add(new_item)
       await db.commit()
       await db.refresh(new_item)
       return new_item
   ```

3. **Create/Update Service (`app/services/`)**:
   ```python
   # app/services/item_service.py
   from app.repositories import item_repo
   from sqlalchemy.ext.asyncio import AsyncSession

   async def create_item(db: AsyncSession, item_data: dict):
       # Add business logic here if needed
       return await item_repo.create_item(db, item_data)
   ```

4. **Create/Update Router (`app/api/v1/`)**:
   ```python
   # app/api/v1/items.py
   from fastapi import APIRouter, Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.core.database import get_db
   from app.schemas.item import ItemCreate
   from app.services import item_service

   router = APIRouter()

   @router.post("/")
   async def create_item_endpoint(item: ItemCreate, db: AsyncSession = Depends(get_db)):
       return await item_service.create_item(db, item.model_dump())
   ```

### Adding a New Model

1. Create the model in `app/models/`:
   ```python
   # app/models/item.py
   from sqlalchemy import Column, Integer, String
   from app.core.database import Base

   class Item(Base):
       __tablename__ = "items"
       id = Column(Integer, primary_key=True, index=True)
       name = Column(String, index=True)
   ```
2. Import it in `app/models/__init__.py` so Alembic detects it.
3. Generate a migration: `alembic revision --autogenerate -m "Add items table"`
4. Apply it: `alembic upgrade head`

### Working with Background Tasks (Celery)

For long-running tasks (like parsing documents or generating embeddings), we use Celery.

1. Define a task in `app/workers/`:
   ```python
   from app.core.celery_app import celery_app

   @celery_app.task
   def process_document_task(doc_id: int):
       # Task logic here
       pass
   ```
2. Call it from a service:
   ```python
   process_document_task.delay(doc_id=123)
   ```

### Code Quality — Run Before Pushing

> ⚠️ CI will fail if these checks don't pass. Always run them locally before pushing.

#### Backend

```bash
cd backend

# Activate virtual environment first (ruff & mypy are dev dependencies, not global)
source .venv/bin/activate

# 1. Lint — checks code style and fixes auto-fixable issues
ruff check . --fix

# 2. Format — ensures consistent code formatting
ruff format .

# 3. Type check
mypy app/
```

Run all three in one shot:

```bash
source .venv/bin/activate && ruff check . --fix && ruff format . && mypy app/
```

#### Frontend

```bash
cd frontend

# 1. Lint
npm run lint

# 2. Type check
npx tsc --noEmit

# 3. Build validation (catches import/compile errors)
npm run build
```

#### What CI checks (mirrors the above)

| Check | Command | Scope |
|---|---|---|
| Backend lint | `ruff check . --fix` | `backend/` |
| Backend format | `ruff format --check .` | `backend/` |
| Backend types | `mypy app/` | `backend/app/` |
| Backend tests | `pytest` | `backend/tests/` |
| Frontend lint | `npm run lint` (oxlint) | `frontend/src/` |
| Frontend types | `npx tsc --noEmit` | `frontend/` |
| Frontend build | `npm run build` | `frontend/` |

---

### Testing

Run backend tests using pytest:

```bash
cd backend
pytest
# Or run specific tests
pytest tests/test_api.py
```

---

## Frontend Development

The frontend is built with React 19, Vite, and TypeScript.

### Architecture Overview

- **`api/`**: Axios configurations and API client methods mapping to backend endpoints.
- **`components/`**: Feature-specific components and generic `ui/` components (shadcn/ui).
- **`pages/`**: Top-level route components.
- **`stores/`**: Global client state (Zustand).
- **`hooks/`**: Custom React hooks (often wrapping TanStack Query).

### Adding a New Page/Component

1. Create the page in `src/pages/`:
   ```tsx
   export default function ItemsPage() {
     return <div>Items</div>;
   }
   ```
2. Add the route in `src/App.tsx`.
3. Create related components in `src/components/items/`.

### State Management

- **Client State (Zustand)**: Use for UI state (e.g., sidebar toggles, current workspace).
- **Server State (TanStack Query)**: Use for fetching, caching, and updating asynchronous data.

```tsx
// Example Query Hook
import { useQuery } from '@tanstack/react-query';
import { getItems } from '@/api/items';

export function useItems() {
  return useQuery({
    queryKey: ['items'],
    queryFn: getItems,
  });
}
```

### Styling

We use **Tailwind CSS** for utility classes and **shadcn/ui** for accessible, customizable components.

- To add a new shadcn component: `npx shadcn-ui@latest add button`

### API Integration

Define API calls in `src/api/` using the configured Axios instance:

```typescript
import api from './index';

export const getItems = async () => {
  const response = await api.get('/v1/items');
  return response.data;
};
```

---

## Database Migrations

Common Alembic commands for managing the database schema:

| Command | Description |
|---|---|
| `alembic revision --autogenerate -m "msg"` | Generate a new migration script based on model changes |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Revert the last applied migration |
| `alembic history` | View migration history |
| `alembic current` | Show current applied revision |

---

## Docker Commands Reference

| Command | Description |
|---|---|
| `make infra-up` | Start infrastructure (DB, Redis, Qdrant) in background |
| `make infra-down` | Stop infrastructure containers |
| `make infra-logs` | View infrastructure logs |
| `make up` | Start entire application (prod mode) via Docker Compose |
| `make down` | Stop entire application |
| `docker compose -f docker-compose.dev.yml up -d` | Start dev infra directly |

---

## IDE Setup

### Recommended VSCode Extensions

- **Python**: Core Python support
- **Pylance**: Fast feature-rich language support for Python
- **Ruff**: Python linter and formatter
- **ESLint**: JavaScript/TypeScript linting
- **Prettier - Code formatter**: Frontend formatting
- **Tailwind CSS IntelliSense**: Autocomplete for Tailwind classes
- **Docker**: For managing containers

---

## Debugging Tips

- **Backend Logs**: Run `uvicorn` manually to see real-time error traces, or check container logs if running in Docker (`docker logs -f thinkora-api`).
- **Worker Logs**: Start a celery worker manually in a terminal to see task errors:
  ```bash
  cd backend && celery -A app.core.celery_app worker --loglevel=info
  ```
- **Database Access**: Connect to Postgres directly using a client like DBeaver or psql:
  `psql -h localhost -p 5434 -U postgres -d thinkora`
- **Vector DB**: Qdrant has a built-in dashboard accessible at `http://localhost:6333/dashboard`.

---

## Common Development Tasks

- **Resetting the Database**: Drop the DB schema, run migrations, or simply delete the docker volume: `docker volume rm thinkora_postgres_data`.
- **Updating Dependencies**: 
  - Backend: Edit `requirements.txt` and run `pip install -r requirements.txt`.
  - Frontend: `npm install <package>`.
- **Running a Single Service**: Use `make infra-up` and run just the frontend or backend locally as needed.
