# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ResumeMate is an AI-driven resume agent platform that combines static resume display with AI-powered interactive Q&A functionality. The system uses Dify Chatflow API for personalized resume conversations with bilingual support (Chinese/English).

## Core Architecture

### Backend Structure

- **Main Application**: `app.py` - Gradio interface for the AI resume assistant
- **Dify Integration Layer**: `src/backend/dify/`
  - `client.py` - async httpx client for Dify `/v1/chat-messages` (blocking mode)
  - `adapter.py` - maps Dify JSON response → `SystemResponse`
  - `processor.py` - `DifyProcessor` (main entrypoint, replaces old `ResumeMateProcessor`)
- **Data Models**: `src/backend/models.py` - Pydantic models: `Question`, `SystemResponse`
- **Contact Tools**: `src/backend/tools/contact.py` - Contact information collection and management
- **CMS**: `src/backend/cms/` - Content management system (uses openai-agents SDK internally)

### Frontend Structure

- **Static Site**: `src/frontend/index.html` - Static resume display
- **JavaScript**: `src/frontend/static/js/main.js` - Frontend interactivity (ResumeMateFrontend class)
- **Data Files**:
  - `src/frontend/data/resume-zh.json` - Chinese resume data
  - `src/frontend/data/resume-en.json` - English resume data
  - `src/frontend/data/version.json` - Version control for data updates
- **Styling**: Tailwind CSS for responsive design

## Development Commands

### Environment Setup

```bash
# Activate virtual environment
source .venv/bin/activate

# Or use uv (recommended)
uv sync
```

### Development Workflow

```bash
# Install dependencies
uv sync

# Code formatting
ruff --fix . && ruff format .

# Run tests
pytest
pytest tests/unit/     # Unit tests only
pytest -v              # Verbose output
```

### Running the Application

```bash
# Start the Gradio interface
uv run app.py

# The app runs on http://localhost:7860
```

### Deployment

```bash
# Frontend deployment to GitHub Pages
./scripts/deploy_frontend.sh

# Docker backend deployment
./scripts/build-backend.sh
./scripts/docker-run.sh run
```

## Key Technologies

- **Python 3.10+** with async/await patterns
- **Dify Chatflow API** for AI Q&A (via httpx)
- **OpenAI Agents SDK** for CMS `InfographicAssistantAgent` only
- **Gradio 5.x** for web interface
- **Pydantic 2.0+** for data validation

## Configuration

### Environment Variables (.env)

```
DIFY_API_BASE=https://dify.brianhan.cc/v1
DIFY_API_KEY=app-xxx
DIFY_USER=resumemate-visitor
```

- `DIFY_API_BASE` — Dify API endpoint base URL
- `DIFY_API_KEY` — Dify app API key (required)
- `DIFY_USER` — User identifier sent to Dify (default: `resumemate-visitor`)
- CMS also requires `LITELLM_PROXY_API_KEY` / `LITELLM_PROXY_API_BASE` (see `.env.example`)

### Code Style

- **Black** formatter with 88 character line length
- **isort** for import sorting with black profile
- **flake8** / **ruff** for linting
- Pre-commit hooks automatically enforce formatting

## Testing Strategy

- **Unit tests**: `tests/unit/` - Test individual components
  - `test_dify_client.py` — mock httpx, verifies API call format
  - `test_dify_adapter.py` — verifies Dify response → SystemResponse mapping
  - `test_ai_assistant.py` / `test_ai_assistant_integration.py` — CMS AI assistant
- **pytest-asyncio** for async test support
- Tests should cover both English and Chinese functionality

## Agent Workflow

1. **Question Processing**: User input is structured into `Question` model
2. **Dify Processing**: `DifyProcessor.process_question(question, conversation_id)` calls Dify Chatflow API
   - `conversation_id=""` → Dify creates a new conversation and returns new ID
   - Subsequent calls pass the returned `conversation_id` for multi-turn continuity
3. **Adaptation**: `adapter.adapt()` maps Dify JSON → `(SystemResponse, conversation_id)`
4. **Response Display**: Gradio UI shows answer; `gr.State` stores `conversation_id` for next turn

## Special Considerations

- **Bilingual Support**: System handles both Chinese (Traditional) and English
- **Confidence Scoring**: Fixed at `0.85` (Dify Chatflow does not natively return confidence scores)
- **Action System**: Derived from `outputs.status` in Dify End node output variables
- **Async Processing**: Core processing functions use async/await patterns
- **CMS Isolation**: `src/backend/cms/ai_assistant.py` uses openai-agents SDK independently; do not change its imports

## Current Project Status

### Completed (Dify Migration ✅)

- **Dify Integration Layer**: `src/backend/dify/` — client, adapter, processor
- **Gradio multi-turn**: `gr.State` tracks `conversation_id` across turns
- **Frontend cleanup**: Removed HF Space references, dead `checkGradioStatus`/`updateChatStatus` JS functions
- **Models cleanup**: `models.py` simplified to `Question` + `SystemResponse` only
- **Dependencies**: Removed `langchain`, `chromadb`, `sentence-transformers`, `litellm`; added `httpx`
- **Tests**: New `test_dify_client.py` (5 tests) and `test_dify_adapter.py` (18 tests)


## Development Standards

### Code Quality Guidelines

Based on `.github/instructions/` configurations:

#### JavaScript/Frontend Standards

- Use functional components with hooks instead of class components
- Implement JSDoc comments for all functions, classes, and methods
- Follow conventional commits format: `type(scope): description`
- Use Tailwind CSS with component extraction for repeated UI patterns
- Implement proper error boundaries and loading states

#### Python/Backend Standards

- Use Pydantic models with strict type checking for all data validation
- Implement comprehensive docstrings explaining 'why' not just 'what'
- Follow FastAPI patterns with dependency injection
- Use async endpoints for I/O-bound operations
- Implement proper exception handling with HTTPException

#### Documentation Standards

- Use appropriate heading hierarchy (H1 for titles, H2/H3 for sections)
- Limit line length to 80 characters for readability
- Include YAML front matter for metadata
- Use fenced code blocks with language specification

### Git Workflow

- **Commit Messages**: Use Conventional Commits in Traditional Chinese
  - Format: `type(scope): description`
  - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
  - Example: `feat(agents): 新增問答評估功能`
- **Branching**: Use descriptive feature branch names
- **Reviews**: Follow pull request templates and CODEOWNERS assignments

### Testing Requirements

- Write unit tests for all individual components in `tests/unit/`
- Create integration tests for component interactions in `tests/integration/`
- Achieve high test coverage using pytest for Python and Jest for JavaScript
- Include realistic test scenarios and edge cases
- Use mocking for external dependencies

## Claude Code Workflow Rules

### General Development Guidelines

- 每次完成重構後應該回頭檢視 README.md 是否也需要相應更新內容
- 如果要執行與python相關的程式優先考慮使用"uv run"，或透過"uv init"建立虛擬環境，或使用"uv add"增加依賴包
- 總是先判斷目前專案/使用者scope是否已有設定子代理，若有則將任務分拆給子代理 (Sub Agents) 執行

### Python Environment Management

- Prefer using `uv` for Python package management:
  - `uv run` for executing Python programs
  - `uv init` for creating virtual environments
  - `uv add` for adding dependencies
- This approach ensures consistent dependency management and virtual environment handling

### Task Delegation Strategy

- Always check if the current project/user scope has configured sub-agents
- When sub-agents are available, break down tasks and delegate to appropriate sub-agents
- This ensures optimal task distribution and specialized handling
