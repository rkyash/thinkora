# Database Architecture

This document outlines the data layer for the Thinkora project. Thinkora utilizes a hybrid database architecture combining relational, vector, and key-value stores to provide a robust backend for AI-powered document interactions.

## Table of Contents
- [Overview](#overview)
- [Entity-Relationship Diagram](#entity-relationship-diagram)
- [Model Details](#model-details)
- [Vector Storage (Qdrant)](#vector-storage-qdrant)
- [Caching & Queues (Redis)](#caching--queues-redis)
- [Migration Management (Alembic)](#migration-management-alembic)
- [Database Configuration](#database-configuration)
- [Best Practices](#best-practices)

## Overview
Thinkora relies on three primary database systems:
1. **PostgreSQL**: The primary relational store for users, workspaces, notebooks, metadata, chat history, and generated study tools.
2. **Qdrant**: The vector database used for storing document embeddings to enable Retrieval-Augmented Generation (RAG).
3. **Redis**: Used as a fast key-value store for caching, Celery task queuing (broker/backend), and Server-Sent Events (SSE) broadcasting.

## Entity-Relationship Diagram
The following Mermaid diagram illustrates the relational models stored in PostgreSQL.

```mermaid
erDiagram
    User ||--o{ Workspace : owns
    Workspace ||--o{ Notebook : contains
    Notebook ||--o{ Source : contains
    Notebook ||--o{ ChatSession : hosts
    Notebook ||--o{ Note : contains
    Notebook ||--o{ Flashcard : contains
    Notebook ||--o{ Quiz : contains
    Notebook ||--o{ GraphNode : contains
    Notebook ||--o{ Generation : tracks
    Source ||--o{ DocumentChunk : splits-into
    ChatSession ||--o{ Message : contains
    Quiz ||--o{ QuizQuestion : contains
    GraphNode ||--o{ GraphEdge : source
    GraphNode ||--o{ GraphEdge : target

    User {
        uuid id PK
        string email
        string name
        string hashed_password
        datetime created_at
        datetime updated_at
    }
    
    Workspace {
        uuid id PK
        string name
        uuid user_id FK
        datetime created_at
        datetime updated_at
    }
    
    Notebook {
        uuid id PK
        string title
        string description
        uuid workspace_id FK
        datetime created_at
        datetime updated_at
    }
    
    Source {
        uuid id PK
        string filename
        string file_type
        enum status
        uuid notebook_id FK
        string file_path
        datetime created_at
    }
    
    DocumentChunk {
        uuid id PK
        text content
        uuid source_id FK
        int chunk_index
        jsonb metadata
    }
    
    ChatSession {
        uuid id PK
        string title
        uuid notebook_id FK
        datetime created_at
    }
    
    Message {
        uuid id PK
        enum role
        text content
        uuid session_id FK
        datetime created_at
    }
    
    Note {
        uuid id PK
        string title
        text content
        uuid notebook_id FK
        datetime created_at
        datetime updated_at
    }
    
    Flashcard {
        uuid id PK
        text front
        text back
        uuid notebook_id FK
    }
    
    Quiz {
        uuid id PK
        string title
        uuid notebook_id FK
    }
    
    QuizQuestion {
        uuid id PK
        text question
        jsonb options
        string correct_answer
        uuid quiz_id FK
    }
    
    GraphNode {
        uuid id PK
        string label
        string type
        uuid notebook_id FK
    }
    
    GraphEdge {
        uuid id PK
        uuid source_node_id FK
        uuid target_node_id FK
        string relationship
    }
    
    AppSetting {
        string key PK
        jsonb value
    }
    
    Generation {
        uuid id PK
        string type
        string status
        uuid notebook_id FK
        datetime created_at
    }
```

## Model Details

### User & Workspace
- **User**: Stores authentication details. `id` (UUID), `email` (String, unique, indexed), `hashed_password` (String).
- **Workspace**: Top-level organizational unit for a user's notebooks.

### Notebook & Source
- **Notebook**: A container for a related set of documents (sources), chat sessions, and generated assets.
- **Source**: Represents an uploaded document. `status` is an Enum tracking the parsing/embedding lifecycle (`PENDING`, `PROCESSING`, `READY`, `FAILED`).
- **DocumentChunk**: The text chunks parsed from a `Source`. Contains raw `content` and `metadata` for precise citation.

### Chat & Study Tools
- **ChatSession** / **Message**: Stores conversation history. `role` in Message distinguishes between `user` and `assistant`.
- **Note**: Rich-text notes created within a notebook.
- **Flashcard** / **Quiz** / **QuizQuestion**: Study assets generated from the notebook's corpus.

### Knowledge Graph
- **GraphNode** / **GraphEdge**: Represents entities and their relationships extracted from documents. Tied to a specific `notebook_id`.

### System
- **AppSetting**: Global application configurations stored as key-value pairs (using JSONB for values).
- **Generation**: Tracks async generation tasks (e.g., creating study guides, audio overviews).

## Vector Storage (Qdrant)
Qdrant is utilized for similarity search across document chunks.
- **Collection Strategy**: We use one collection globally, or alternatively, one collection per notebook. Given Qdrant's payload filtering efficiency, a single collection with notebook ID filtering is highly optimal.
- **Vector Dimensions**: `384` dimensions (optimized for the `all-MiniLM-L6-v2` sentence-transformers embedding model).
- **Payload Schema**: Each point in Qdrant contains a payload with at minimum:
  - `chunk_id` (UUID mapping to PostgreSQL `DocumentChunk`)
  - `source_id` (UUID)
  - `notebook_id` (UUID)
- **Filtering**: During RAG, semantic search queries are strictly filtered by `notebook_id` in the Qdrant payload to ensure data isolation.

## Caching & Queues (Redis)
Redis serves three critical roles in Thinkora's architecture:
1. **Celery Broker**: Queues asynchronous tasks such as document parsing, embedding generation, and large LLM generation jobs.
2. **Result Backend**: Stores the output or status of Celery tasks.
3. **SSE Event Channel**: Manages Pub/Sub for Server-Sent Events, streaming chat responses and real-time generation progress to the frontend.

## Migration Management (Alembic)
Database schemas are managed using Alembic, integrated with SQLAlchemy.

- **Create a Migration**: After modifying models in `backend/app/models/`, generate a script:
  ```bash
  alembic revision --autogenerate -m "describe_changes"
  ```
- **Apply Migrations**: Upgrade the database to the latest schema:
  ```bash
  alembic upgrade head
  ```
- **Rollback Migrations**: Downgrade by one revision:
  ```bash
  alembic downgrade -1
  ```
- **Auto Migrate**: The environment variable `AUTO_MIGRATE=true` can be set to automatically apply pending migrations on application startup.

## Database Configuration
Thinkora uses `asyncpg` to connect to PostgreSQL asynchronously.

- **Environment Variable**: `DATABASE_URL`
- **Format**: `postgresql+asyncpg://user:password@host:port/dbname`
- **Session Management**: SQLAlchemy `async_sessionmaker` provides isolated async sessions for FastAPI dependency injection.

## Best Practices
1. **Primary Keys**: Use UUIDv4 for all primary keys to obscure sequential IDs, simplify distributed generation, and ease potential future sharding.
2. **Timestamps**: Ensure `created_at` and `updated_at` (with auto-update triggers or SQLAlchemy event hooks) exist on mutable models.
3. **Foreign Keys & Cascades**: Use `ON DELETE CASCADE` for parent-child relationships (e.g., deleting a Notebook should recursively delete its Sources, Chats, and Notes).
4. **Indexes**: Create indexes on frequently queried foreign keys (e.g., `notebook_id`) and search fields (e.g., User `email`) to optimize query performance.
5. **Async DB Operations**: Always use asynchronous SQLAlchemy queries (`select`, `execute`) within the API layer to prevent blocking the event loop.
