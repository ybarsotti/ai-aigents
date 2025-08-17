# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
- `./scripts/dev_setup.sh` - Create virtual environment and install dependencies
- `source .venv/bin/activate` - Activate the virtual environment

### Code Quality
- `./scripts/format.sh` - Format code using ruff (includes import sorting)
- `./scripts/validate.sh` - Lint with ruff and type check with mypy
- `./scripts/test.sh` - Run tests using pytest

### Docker Development
- `ag ws up` - Start the complete workspace (Streamlit UI, FastAPI, Postgres)
- `ag ws down` - Stop the workspace
- Requires `OPENAI_API_KEY` environment variable to be set

### Service URLs (Docker)
- Streamlit UI: http://localhost:8501
- FastAPI docs: http://localhost:8000/docs
- Postgres: localhost:5432

## Architecture Overview

This is a production-grade agentic system built with the Agno framework consisting of three main layers:

### Core Components
1. **Streamlit UI** (`ui/`) - Multi-page web interface for interacting with agents, teams, and workflows
2. **FastAPI Server** (`api/`) - REST API with versioned routes for programmatic access
3. **Postgres Database** (`db/`) - Database with pgvector extension for vector storage and retrieval

### Agent System Structure
- **Individual Agents** (`agents/`) - Sage (RAG-based knowledge), Scholar (web research), Operator
- **Teams** (`teams/`) - Multi-language team, Finance research team, Operator team
- **Workflows** (`workflows/`) - Blog post generator, Investment report generator

### Key Directories
- `agents/` - Individual AI agents with specific capabilities
- `teams/` - Multi-agent teams that collaborate on tasks
- `workflows/` - Structured multi-step processes
- `api/routes/` - FastAPI route definitions organized by feature
- `ui/pages/` - Streamlit page components for each agent/team/workflow
- `db/tables/` - SQLAlchemy table definitions
- `db/migrations/` - Alembic database migration files
- `workspace/` - Infrastructure and secrets management
- `scripts/` - Development and deployment automation

### Configuration
- Uses `pyproject.toml` for Python dependency management with uv
- Ruff for linting and formatting (120 character line length)
- MyPy for type checking with strict settings
- Environment-based configuration via Pydantic settings classes
- Docker Compose for local development with service orchestration

### Database
- PostgreSQL with pgvector extension for vector operations
- Alembic for database migrations
- SQLAlchemy ORM for data access
- Automatic migration on container startup

### External Integrations
- OpenAI API for LLM capabilities
- DuckDuckGo for web search
- Exa API for enhanced search
- YFinance for financial data
- Agno monitoring and observability

## Development Patterns

### Agent Development
Agents inherit from the Agno framework and are configured via settings classes. Each agent has its own module in `agents/` with dedicated UI pages.

### API Development
FastAPI routes are organized by version in `api/routes/`. Use dependency injection for database sessions and follow RESTful conventions.

### UI Development
Streamlit pages are in `ui/pages/` with shared components in `ui/utils.py`. Each page corresponds to an agent, team, or workflow.

### Database Schema
Table definitions are in `db/tables/` using SQLAlchemy. Create migrations with Alembic for schema changes.