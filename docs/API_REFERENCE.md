# Thinkora API Reference

## Table of Contents
- [Overview](#overview)
- [Authentication](#authentication)
- [Interactive Documentation](#interactive-documentation)
- [Endpoint Reference](#endpoint-reference)
  - [Authentication](#authentication-1)
  - [Workspaces](#workspaces)
  - [Notebooks](#notebooks)
  - [Sources](#sources)
  - [Chat](#chat)
  - [Notes](#notes)
  - [Study Tools](#study-tools)
  - [Audio](#audio)
  - [Knowledge Graph](#knowledge-graph)
  - [Search](#search)
  - [Events](#events)
  - [Settings](#settings)
  - [Health](#health)
- [Request & Response Examples](#request--response-examples)
- [Error Handling](#error-handling)
- [Streaming Responses (SSE)](#streaming-responses-sse)
- [Pagination](#pagination)
- [Rate Limiting](#rate-limiting)

## Overview
The Thinkora backend exposes a RESTful API to interact with workspaces, notebooks, documents, and various AI features. The base URL for all API routes is `/api/v1/`. Responses and requests generally use JSON, with specific endpoints utilizing `multipart/form-data` for file uploads or Server-Sent Events (SSE) for streaming data.

## Authentication
Thinkora uses JWT (JSON Web Token) Bearer tokens for API authentication. Include the token in the `Authorization` header for protected routes:

```http
Authorization: Bearer <your_access_token>
```

> [!NOTE]
> Authentication is optional in Thinkora and can be globally toggled via the `AUTH_ENABLED` environment variable. If `AUTH_ENABLED=false`, all endpoints bypass authentication checks.

### Authentication Flow
1. **Register**: Create a new account at `POST /api/v1/auth/register`.
2. **Login**: Authenticate and retrieve an access token via `POST /api/v1/auth/login`.
3. **Refresh**: Obtain a new access token using a refresh token via `POST /api/v1/auth/refresh`.

## Interactive Documentation
When running the Thinkora backend, interactive API documentation is automatically generated and accessible at:
- **Swagger UI**: `/docs` (Interactive endpoint testing)
- **ReDoc**: `/redoc` (Clean, detailed endpoint reference)

## Endpoint Reference

### Authentication
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `POST` | `/api/v1/auth/register` | Register a new user account. | No |
| `POST` | `/api/v1/auth/login` | Login and retrieve access and refresh tokens. | No |
| `POST` | `/api/v1/auth/refresh` | Refresh an expired access token. | No |

### Workspaces
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/workspaces` | List all workspaces. | Yes |
| `POST` | `/api/v1/workspaces` | Create a new workspace. | Yes |
| `GET` | `/api/v1/workspaces/{id}` | Get details of a specific workspace. | Yes |
| `PUT` | `/api/v1/workspaces/{id}` | Update a workspace. | Yes |
| `DELETE`| `/api/v1/workspaces/{id}` | Delete a workspace. | Yes |

### Notebooks
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/workspaces/{ws_id}/notebooks` | List notebooks in a workspace. | Yes |
| `POST` | `/api/v1/workspaces/{ws_id}/notebooks` | Create a new notebook. | Yes |
| `GET` | `/api/v1/notebooks/{id}` | Get details of a specific notebook. | Yes |
| `PUT` | `/api/v1/notebooks/{id}` | Update a notebook. | Yes |
| `DELETE`| `/api/v1/notebooks/{id}` | Delete a notebook. | Yes |

### Sources
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/notebooks/{nb_id}/sources` | List all sources in a notebook. | Yes |
| `POST` | `/api/v1/notebooks/{nb_id}/sources` | Upload a new source (`multipart/form-data`). | Yes |
| `GET` | `/api/v1/sources/{id}` | Get details of a specific source. | Yes |
| `DELETE`| `/api/v1/sources/{id}` | Delete a source and its vector embeddings. | Yes |
| `GET` | `/api/v1/sources/{id}/status` | Get processing status of a source. | Yes |

### Chat
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/notebooks/{nb_id}/chat/sessions` | List chat sessions for a notebook. | Yes |
| `POST` | `/api/v1/notebooks/{nb_id}/chat/sessions` | Create a new chat session. | Yes |
| `GET` | `/api/v1/chat/sessions/{id}` | Get chat session and history. | Yes |
| `POST` | `/api/v1/chat/sessions/{id}/ask` | Send a message and get streaming response (SSE). | Yes |
| `DELETE`| `/api/v1/chat/sessions/{id}` | Delete a chat session. | Yes |

### Notes
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/notebooks/{nb_id}/notes` | List notes in a notebook. | Yes |
| `POST` | `/api/v1/notebooks/{nb_id}/notes` | Create a new note. | Yes |
| `GET` | `/api/v1/notes/{id}` | Get a specific note. | Yes |
| `PUT` | `/api/v1/notes/{id}` | Update a note. | Yes |
| `DELETE`| `/api/v1/notes/{id}` | Delete a note. | Yes |

### Study Tools
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `POST` | `/api/v1/notebooks/{nb_id}/generate/flashcards`| Generate flashcards from notebook context. | Yes |
| `POST` | `/api/v1/notebooks/{nb_id}/generate/quiz` | Generate a quiz. | Yes |
| `POST` | `/api/v1/notebooks/{nb_id}/generate/study-guide`| Generate a comprehensive study guide. | Yes |
| `POST` | `/api/v1/notebooks/{nb_id}/generate/timeline` | Generate a timeline of events. | Yes |
| `POST` | `/api/v1/notebooks/{nb_id}/generate/briefing` | Generate a briefing document. | Yes |

### Audio
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `POST` | `/api/v1/notebooks/{nb_id}/audio/synthesize` | Generate an audio overview. | Yes |
| `GET` | `/api/v1/notebooks/{nb_id}/audio` | Get the latest generated audio overview. | Yes |

### Knowledge Graph
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `POST` | `/api/v1/notebooks/{nb_id}/graph/generate` | Trigger knowledge graph generation. | Yes |
| `GET` | `/api/v1/notebooks/{nb_id}/graph/nodes` | Get graph nodes. | Yes |
| `GET` | `/api/v1/notebooks/{nb_id}/graph/edges` | Get graph edges. | Yes |

### Search
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/search` | Global semantic search across allowed notebooks. | Yes |

### Events
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/events` | SSE endpoint for real-time task progress and events. | Yes |

### Settings
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/settings` | Get application settings (LLM provider, models, etc.). | Yes |
| `PUT` | `/api/v1/settings` | Update application settings. | Yes |

### Health
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| `GET` | `/api/v1/health` | API health check. | No |

## Request & Response Examples

### Create a Notebook
**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/workspaces/ws_123/notebooks" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Machine Learning Notes",
    "description": "Notes and PDFs on ML algorithms"
  }'
```

**Response (201 Created):**
```json
{
  "id": "nb_456",
  "workspace_id": "ws_123",
  "name": "Machine Learning Notes",
  "description": "Notes and PDFs on ML algorithms",
  "created_at": "2023-10-25T10:00:00Z",
  "updated_at": "2023-10-25T10:00:00Z"
}
```

### Upload a Document (Source)
**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/notebooks/nb_456/sources" \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/document.pdf"
```

**Response (202 Accepted):**
```json
{
  "id": "src_789",
  "notebook_id": "nb_456",
  "filename": "document.pdf",
  "status": "processing",
  "message": "File uploaded and queued for processing"
}
```

### Send a Chat Message (Streaming)
**Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat/sessions/sess_abc/ask" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the main topic of the uploaded document?"
  }'
```

*(See [Streaming Responses](#streaming-responses-sse) for the response format.)*

## Error Handling
The Thinkora API uses standard HTTP status codes to indicate the success or failure of an API request. Errors return a JSON object containing details about the failure.

**Standard Error Format:**
```json
{
  "detail": "Detailed error message explaining what went wrong."
}
```

**Common HTTP Status Codes:**
- `200 OK`: Request succeeded.
- `201 Created`: Resource was successfully created.
- `202 Accepted`: Request accepted and processing asynchronously.
- `400 Bad Request`: Invalid parameters or malformed request payload.
- `401 Unauthorized`: Missing or invalid authentication token.
- `403 Forbidden`: Authenticated, but lacks permissions for the resource.
- `404 Not Found`: The requested resource does not exist.
- `422 Unprocessable Entity`: Validation error (typically Pydantic schema validation).
- `500 Internal Server Error`: An unexpected server-side error occurred.

## Streaming Responses (SSE)
Thinkora uses Server-Sent Events (SSE) for endpoints that generate real-time tokens (e.g., chat completions) or stream task progress (e.g., the global `/api/v1/events` endpoint).

**Chat Completion SSE Example:**
```text
data: {"type": "token", "content": "The"}
data: {"type": "token", "content": " main"}
data: {"type": "token", "content": " topic"}
data: {"type": "token", "content": " is"}
...
data: {"type": "done", "message_id": "msg_xyz"}
```
Clients can consume these streams using native `EventSource` in the browser or HTTP clients capable of streaming response bodies.

## Pagination
Endpoints that return collections (e.g., listing sources or notes) support pagination via query parameters. If not explicitly documented per endpoint, the default pagination mechanism uses:
- `skip`: Number of records to skip (default: 0).
- `limit`: Maximum number of records to return (default: 50, max: 100).

Example: `GET /api/v1/notebooks/nb_456/notes?skip=20&limit=10`

## Rate Limiting
Rate limiting is currently **not implemented** at the application level in Thinkora. If exposing the API publicly, it is recommended to implement rate limiting at the infrastructure level using an API Gateway, Nginx limit_req, or Cloudflare rules to prevent abuse.
