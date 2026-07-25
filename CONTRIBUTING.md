# Contributing to Thinkora

First off, thank you for considering contributing to Thinkora! It's people like you that make Thinkora such a great tool. We welcome all contributions, from bug reports and feature requests to documentation improvements and code changes.

This document serves as a guide for contributing to the Thinkora repository. By participating in this project, you agree to abide by our Code of Conduct.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [How to Contribute](#how-to-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Features](#suggesting-features)
   - [Improving Documentation](#improving-documentation)
   - [Submitting Code Changes](#submitting-code-changes)
4. [Development Workflow](#development-workflow)
   - [Branch Naming Convention](#branch-naming-convention)
   - [Commit Message Format](#commit-message-format)
   - [Pull Request Process](#pull-request-process)
   - [Code Review](#code-review)
5. [Coding Standards](#coding-standards)
6. [Architecture Rules](#architecture-rules)
7. [Testing Requirements](#testing-requirements)
8. [Documentation](#documentation)
9. [Acknowledgments](#acknowledgments)

## Code of Conduct

This project and everyone participating in it is governed by the [Thinkora Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## Getting Started

### 1. Fork & Clone
Start by forking the Thinkora repository to your own GitHub account. Then, clone it locally:

```bash
git clone https://github.com/YOUR-USERNAME/thinkora.git
cd thinkora
git remote add upstream https://github.com/thinkora/thinkora.git
```

### 2. Setup Development Environment
Follow our detailed [Developer Guide](DEVELOPER_GUIDE.md) to set up your local development environment. This includes setting up Docker containers, installing dependencies for the backend and frontend, and configuring environment variables.

### 3. Explore the Codebase
Take some time to familiarize yourself with the structure:
- `backend/`: FastAPI Python backend, SQLAlchemy models, LangChain services, and Celery workers.
- `frontend/`: React 19 TypeScript frontend with Vite, Tailwind CSS, and Zustand.

## How to Contribute

### Reporting Bugs
Bugs are tracked as GitHub issues. When creating a bug report, please include:
- A clear, descriptive title.
- Steps to reproduce the bug.
- Expected vs. actual behavior.
- Screenshots, if applicable.
- Environment details (OS, Node.js/Python version, browser).
- Relevant logs from the frontend, backend, or worker containers.

### Suggesting Features
Feature requests are also tracked as GitHub issues. Provide a clear description of the requested feature, explaining *why* it would be useful and providing any potential use cases or UI mockups.

### Improving Documentation
Great documentation is critical! We welcome typo fixes, clearer explanations, and new guides. You can edit documentation directly or submit a PR for larger changes.

### Submitting Code Changes
Before writing a lot of code, check the issue tracker to see if someone is already working on the same thing. If not, comment on the issue you want to work on or create a new one to discuss your proposed solution.

## Development Workflow

### Branch Naming Convention
Please use the following prefixes for your branches:
- `feature/` - for new features (e.g., `feature/knowledge-graph-export`)
- `fix/` - for bug fixes (e.g., `fix/chat-streaming-timeout`)
- `docs/` - for documentation updates (e.g., `docs/update-architecture-diagram`)
- `refactor/` - for code refactoring (e.g., `refactor/extract-rag-service`)

### Commit Message Format
We follow [Conventional Commits](https://www.conventionalcommits.org/). Your commit messages should be structured as follows:
```
<type>: <description>
```
Common types:
- `feat:` A new feature
- `fix:` A bug fix
- `docs:` Documentation only changes
- `refactor:` A code change that neither fixes a bug nor adds a feature
- `test:` Adding missing tests or correcting existing tests
- `chore:` Changes to the build process or auxiliary tools

### Pull Request Process
1. Push your changes to your fork.
2. Open a Pull Request against the `main` branch of the upstream repository.
3. Fill out the PR template completely.
4. Include screenshots or screen recordings for any UI changes.
5. Ensure all tests and linting checks pass.
6. Link the relevant issue(s) in the PR description (e.g., "Fixes #123").

### Code Review Expectations
- Maintainers will review your PR and may request changes.
- Be responsive to feedback and ready to iterate on your code.
- Keep discussions respectful and focused on code quality and project goals.

## Coding Standards

### Backend
- **Style:** Adhere to PEP 8. We use `Ruff` and `Black` for formatting and linting.
- **Typing:** Use strict Python type hints everywhere.
- **Pattern:** Follow our layered architecture: `Router` → `Service` → `Repository` → `Model`.

### Frontend
- **Language:** Strict TypeScript. Avoid `any` types.
- **Components:** Use React functional components and hooks.
- **Styling:** Tailwind CSS v3 and `shadcn/ui` components.
- **State Management:** Use `Zustand` for global state and `TanStack Query` v5 for server state/data fetching.

## Architecture Rules

To maintain a clean and maintainable codebase, we strictly enforce these boundaries:
> [!IMPORTANT]
> 1. **Never import repositories in routers.** Routers should only depend on services.
> 2. **Never put business logic in repositories.** Repositories exist solely for data access and querying.
> 3. **Never execute raw SQL in services.** Services must use repositories for database interactions.
> 4. **All heavy tasks go to Celery workers.** File parsing, large embeddings, LLM batch jobs, and audio generation must be asynchronous background tasks, never blocking API routes.

## Testing Requirements

### Backend
- Framework: `pytest` and `pytest-asyncio`.
- Coverage: Ensure all new services and repositories are tested.
- File naming: Test files must be named `test_<module_name>.py`.

### Frontend
- Framework: `Vitest`.
- Testing approach: Test component behavior, hooks, and utility functions.
- File naming: Test files must be named `<component_name>.test.tsx` or `<module_name>.test.ts`.

## Documentation

When submitting code, ensure you also:
- Update the documentation (`README.md`, `DEVELOPER_GUIDE.md`, etc.) if you change APIs, add environment variables, or modify the architecture.
- Add descriptive Python docstrings to all new functions, classes, and modules in the backend.
- Add JSDoc comments to complex frontend utilities.

## Acknowledgments

Thinkora thrives because of our open-source community. Whether you're fixing a typo, triaging an issue, or implementing a massive new feature—thank you! We appreciate your time, effort, and passion for building better local-first AI tools.
