# Thinkora FAQ

Welcome to the Thinkora FAQ. This document provides answers to common questions about Thinkora, its features, privacy, setup, and development.

## Table of Contents

- [General](#general)
- [Privacy & Data](#privacy--data)
- [Setup & Installation](#setup--installation)
- [LLM & AI](#llm--ai)
- [Documents & Sources](#documents--sources)
- [Features](#features)
- [Development](#development)

## General

### What is Thinkora?
Thinkora is an open-source, local-first AI-powered document chat application. It serves as an alternative to Google's NotebookLM, allowing users to upload documents, chat with them using Retrieval-Augmented Generation (RAG), generate study tools, create knowledge graphs, and produce audio overviews.

### How is Thinkora different from NotebookLM?
Thinkora is entirely open-source and local-first. Unlike NotebookLM, which requires an internet connection and sends data to Google's servers, Thinkora can be run entirely offline on your own hardware using local LLMs (like Ollama). It also offers extensive customization, supporting multiple LLM providers (via LiteLLM) and optional authentication.

### Is Thinkora free to use?
Yes, Thinkora is completely free and open-source. You can self-host it on your own machine. However, if you choose to use external LLM APIs (like OpenAI or Anthropic), you will be responsible for their API costs.

### What license is Thinkora under?
Thinkora is an open-source project. Please refer to the `LICENSE` file in the repository root for specific licensing details.

## Privacy & Data

### Can I run Thinkora entirely offline?
Yes! By setting up local models (such as Ollama for LLM and the default local embedding model), Thinkora can run entirely offline without needing an internet connection.

### Where are my uploaded files stored?
Your files are stored locally on your server. File contents are typically stored in the directory defined by the `THINKORA_DATA_DIR` or `STORAGE_BACKEND` environment variables, and vector embeddings are stored locally in Qdrant.

### Is my data sent to any external servers?
If you use local LLMs (like Ollama), your data never leaves your machine. However, if you configure external providers (like OpenAI, Anthropic, or Gemini) in your settings, your prompts and relevant document chunks will be sent to those APIs for processing.

### Can I use Thinkora without an account?
Yes. Authentication is completely optional in Thinkora. By default, `AUTH_ENABLED=false` is set in the environment, meaning you can use the application immediately without creating an account.

## Setup & Installation

### What are the system requirements?
Thinkora requires Docker and Docker Compose. For the best experience, we recommend at least 8GB of RAM, especially when running the full infrastructure (PostgreSQL, Redis, Qdrant, API, Celery Workers, and Frontend). 

### What are the hardware requirements for running local LLMs?
Hardware requirements depend on the local LLM you choose to run via Ollama. A 7B parameter model typically requires at least 8GB of VRAM (GPU) or system RAM, while larger models require more. The rest of Thinkora's services are lightweight.

### How do I reset my database completely?
You can stop the infrastructure and remove the underlying Docker volumes. Use the provided Makefile commands:
```bash
make infra-down
```
*Warning: This will delete all your data, including documents, chats, and embeddings if you remove the associated volumes.*

### Which ports does Thinkora use?
By default, the Docker services use the following ports:
- **Frontend (Nginx)**: 80 / 443
- **API (FastAPI)**: 8000
- **PostgreSQL**: 5434
- **Redis**: 6379
- **Qdrant**: 6333 / 6334

## LLM & AI

### Which LLM providers does Thinkora support?
Thinkora supports multiple LLM providers out of the box using LiteLLM. Supported providers include OpenAI, Anthropic, Gemini, Groq, Mistral, OpenRouter, and Ollama.

### How do I configure a new LLM provider?
You can configure providers by setting their respective API keys in your `.env` file (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`). You can then select the `ACTIVE_PROVIDER` and `DEFAULT_MODEL` in your environment or via the application settings UI.

### Can I use Ollama for fully local inference?
Yes, you can configure Thinkora to use Ollama by setting the `OLLAMA_BASE_URL` environment variable to point to your Ollama instance.

### What embedding model is used?
Thinkora uses the `all-MiniLM-L6-v2` model from `sentence-transformers` by default. It runs locally and does not require an external API.

### Can I change the embedding model?
Yes, you can change the embedding model by updating the `EMBEDDING_MODEL` environment variable.

## Documents & Sources

### What file formats are supported?
Thinkora supports various document formats including PDF, DOCX, and TXT files.

### What is the maximum file upload size?
The maximum file size is determined by the `MAX_UPLOAD_SIZE_MB` environment variable. 

### How long does document processing take?
Processing time depends on the length of the document, your system's hardware, and the embedding device (`EMBEDDING_DEVICE`). Small documents process in seconds, while large PDFs may take a few minutes.

### Why is my document stuck in processing?
Document processing is handled asynchronously by Celery workers. If a document is stuck, check the worker service logs for errors. Ensure Redis (the broker) is running and accessible. You can also view the logs using:
```bash
docker logs <worker-container-name>
```

## Features

### What study tools can Thinkora generate?
Thinkora can generate a variety of study tools directly from your documents, including:
- Flashcards
- Quizzes
- Study Guides
- Timelines
- Briefings

### How does the knowledge graph work?
Thinkora extracts entities and relationships from your documents and visualizes them using `@xyflow/react` on the frontend. This creates an interactive knowledge graph that you can traverse to explore connections within your notebook.

### Does Thinkora support audio generation?
Yes! Thinkora supports generating audio overviews (similar to podcasts) of your documents. You can configure the `TTS_PROVIDER` or use a local engine like Kokoro via `KOKORO_BASE_URL`.

### Can I export my data?
You can retrieve your chats, notes, and generated study tools via the API endpoints.

## Development

### How do I add a new API endpoint?
Thinkora uses a strict **Router → Service → Repository → Model** architecture pattern. To add an endpoint:
1. Define the Pydantic schema in `backend/app/schemas/`.
2. Create the data access logic in `backend/app/repositories/`.
3. Add business logic to `backend/app/services/`.
4. Register the route in `backend/app/api/v1/` and ensure it's included in `backend/app/main.py`.

### How do I run tests?
Tests can be run locally or within the Docker container, typically using `pytest`. Refer to the backend documentation or Makefile for specific test commands.

### What's the architecture pattern?
Thinkora utilizes a layered architecture for separation of concerns:
- **Router**: Handles HTTP requests/responses (FastAPI).
- **Service**: Contains business logic (LangChain, integrations).
- **Repository**: Handles database operations (SQLAlchemy async).
- **Model**: Defines the database schema and relationships.

### How do I contribute?
We welcome contributions! Please fork the repository, create a feature branch, and submit a pull request following standard open-source practices.
