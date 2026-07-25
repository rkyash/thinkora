<div align="center">
  <img src="frontend/public/thinkora_logo_icon.png" alt="Thinkora Icon" width="104" height="98" />
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="frontend/public/thinkora_logo_text_dark.png">
    <source media="(prefers-color-scheme: light)" srcset="frontend/public/thinkora_logo_text_light.png">
    <img alt="Thinkora Logo" src="frontend/public/thinkora_logo_text_light.png" width="420" />
  </picture>

  <br />
  <p>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>READ &bull; UNDERSTAND &bull; THINK BETTER</b></p>
  <br />

  <p>Your local-first, AI-powered document chat and knowledge management application<br />(Open-Source NotebookLM Alternative).</p>

  <p>
    <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT" /></a>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+" /></a>
    <a href="https://reactjs.org/"><img src="https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black" alt="React 19" /></a>
    <a href="https://www.docker.com/"><img src="https://img.shields.io/badge/Docker-Enabled-2496ED.svg?logo=docker&logoColor=white" alt="Docker" /></a>
    <a href="http://makeapullrequest.com"><img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg" alt="PRs Welcome" /></a>
  </p>
</div>

---

## 📑 Table of Contents

- [About Thinkora](#-about-thinkora)
- [Key Features](#-key-features)
- [Screenshots](#-screenshots)
- [Quick Start](#-quick-start)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Documentation](#-documentation)
- [Contributing](#-contributing)
- [License](#-license)

---

## 📖 About Thinkora

Thinkora is a powerful, local-first AI document chat application designed as an open-source alternative to NotebookLM. It allows you to upload various document types (PDF, DOCX, TXT, etc.), chat with them using Retrieval-Augmented Generation (RAG), and generate powerful learning tools like flashcards, quizzes, study guides, knowledge graphs, and audio overviews. With a focus on privacy and flexibility, Thinkora runs on your own hardware, requiring no mandatory cloud subscriptions.

---

## ✨ Key Features

- 🔒 **Local-First & Privacy-Focused**: Your data stays on your machine. No mandatory cloud accounts required.
- 🤖 **Multi-LLM Support**: Seamlessly integrate with OpenAI, Anthropic, Gemini, Groq, Mistral, OpenRouter, or run local models via Ollama using LiteLLM.
- 💬 **Advanced RAG Chat**: Chat with your documents contextually with real-time streaming (SSE) responses.
- 🎓 **Study Tools Generation**: Automatically create flashcards, quizzes, and comprehensive study guides from your documents.
- 🕸️ **Knowledge Graphs**: Visualize relationships in your data with interactive node-based knowledge graphs.
- 🎧 **Audio Overviews**: Generate and listen to synthesized audio summaries and briefings of your documents.

---

## 📸 Screenshots

<!-- TODO: Add screenshots -->

> **Note:** Screenshots of the UI, Chat interface, Knowledge Graphs, and Study Tools will be added here.

## Dashboard

![Dashboard](/docs/screenshots/dashboard.png)

---

## Workspace

![notebook](/docs/screenshots/workspace.png)

---

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) API keys for cloud LLM providers, or a local Ollama instance.

### Method 1: Automated Script (Recommended)

The easiest way to get Thinkora up and running:

```bash
# Clone the repository
git clone https://github.com/rkyash/thinkora.git
cd thinkora

# Run the bootstrap script
./start.sh

# Or run using Make
make up
```

### Method 2: Manual Docker Compose

If you prefer to start the services manually:

```bash
# Start all production services (PostgreSQL, Redis, Qdrant, API, Worker, Frontend)
docker compose up -d

# Check logs to ensure everything started correctly
docker compose logs -f
```

_(For development, use `docker compose -f docker-compose.dev.yml up -d` to spin up just the infrastructure while running frontend/backend natively)._

---

## 🛠 Technology Stack

| Category           | Technologies                                                                                                             |
| :----------------- | :----------------------------------------------------------------------------------------------------------------------- |
| **Frontend**       | React 19, Vite, TypeScript, Tailwind CSS v3, shadcn/ui, Zustand, TanStack Query v5, Framer Motion, @xyflow/react, TipTap |
| **Backend**        | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Alembic, asyncpg                                             |
| **AI/ML**          | LangChain, LangGraph, LiteLLM, sentence-transformers (all-MiniLM-L6-v2)                                                  |
| **Infrastructure** | PostgreSQL 16, Redis 7, Qdrant (Vector DB), Celery (Workers), Nginx, Docker Compose                                      |

---

## 📂 Project Structure

```text
thinkora/
├── backend/            # FastAPI backend, DB models, AI services, background workers
│   ├── app/
│   │   ├── api/        # REST endpoints organized by feature
│   │   ├── bootstrap/  # App startup and initialization scripts
│   │   ├── core/       # Configuration, security, database setups
│   │   ├── events/     # SSE event handling
│   │   ├── middlewares/ # Custom middleware
│   │   ├── models/     # SQLAlchemy database models
│   │   ├── repositories/ # Data access layer
│   │   ├── schemas/    # Pydantic validation schemas
│   │   ├── services/   # Business logic (LLM, RAG, Parsing)
│   │   └── workers/    # Celery tasks for asynchronous processing
├── frontend/           # React 19 application
│   ├── src/
│   │   ├── api/        # Axios API clients
│   │   ├── components/ # React components (UI and Feature-specific)
│   │   ├── pages/      # Route definitions
│   │   └── stores/     # Zustand state management
├── docs/               # Project documentation
├── docker-compose.yml  # Production Docker configuration
└── start.sh            # Bootstrap and startup script
```

---

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

- [Developer Guide](docs/DEVELOPER_GUIDE.md) — Setup, development workflow, and coding patterns
- [Architecture Overview](docs/ARCHITECTURE.md) — System design, data flows, and diagrams
- [API Reference](docs/API_REFERENCE.md) — Complete REST API endpoint documentation
- [Database Schema](docs/DATABASE.md) — Models, ER diagrams, and migration guide
- [Troubleshooting](docs/TROUBLESHOOTING.md) — Common issues and solutions
- [FAQ](docs/FAQ.md) — Frequently asked questions

---

## 🤝 Contributing

We welcome contributions from the community! If you'd like to help improve Thinkora, please check out our [Contributing Guidelines](CONTRIBUTING.md).

- Submit bug reports and feature requests via GitHub Issues.
- Open Pull Requests with improvements or fixes.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
