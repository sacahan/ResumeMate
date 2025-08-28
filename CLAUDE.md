# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ResumeMate is an AI-driven resume agent platform that combines static resume display with AI-powered interactive Q&A functionality. The system uses RAG (Retrieval Augmented Generation) technology for personalized resume conversations with bilingual support (Chinese/English).

## Core Architecture

### Backend Structure

- **Main Application**: `app.py` - Gradio interface for the AI resume assistant
- **Processing Core**: `src/backend/processor.py` - Coordinates interaction between Analysis and Evaluate agents
- **AI Agents**:
  - `src/backend/agents/analysis.py` - Analyzes user questions and retrieves relevant information
  - `src/backend/agents/evaluate.py` - Evaluates responses and determines system actions
- **Data Models**: `src/backend/models.py` - Pydantic models for Question and SystemResponse
- **RAG Tools**: `src/backend/tools/rag.py` - ChromaDB vector database integration

### Frontend Structure

- **Static Site**: `src/frontend/index.html` - Static resume display
- **JavaScript**: `src/frontend/static/js/main.js` - Frontend interactivity
- **Styling**: Tailwind CSS for responsive design

### Database

- **Vector DB**: ChromaDB stored in `chroma_db/` directory
- **Initialization**: `init_db.py` - Sets up the vector database with resume content

## Development Commands

### Environment Setup

```bash
# Initial setup (creates venv, installs dependencies, generates .env)
chmod +x scripts/setup_dev_env.sh
./scripts/setup_dev_env.sh

# Activate virtual environment
source .venv/bin/activate
```

### Development Workflow

```bash
# Install dependencies
pip install -e ".[dev]"

# Code formatting (pre-commit hook automatically runs these)
isort src tests
black src tests
flake8 src tests

# Run tests
pytest
pytest tests/unit/                    # Unit tests only
pytest tests/integration/            # Integration tests only
pytest -v                           # Verbose output
```

### Running the Application

```bash
# Start the Gradio interface
python app.py

# The app runs on http://localhost:7860
```

### Deployment

```bash
# Backend deployment to HuggingFace Spaces
./scripts/deploy_backend.sh

# Frontend deployment to GitHub Pages
./scripts/deploy_frontend.sh

# Combined deployment
./scripts/deploy.sh
```

## Key Technologies

- **Python 3.10+** with async/await patterns
- **OpenAI Agents SDK** for AI agent implementation
- **Gradio 4.0+** for web interface
- **ChromaDB** for vector storage and retrieval
- **Pydantic 2.0+** for data validation
- **LangChain** for AI workflow orchestration

## Configuration

### Environment Variables (.env)

- `OPENAI_API_KEY` - Required for AI functionality
- Additional configuration in `.env.example`

### Code Style

- **Black** formatter with 88 character line length
- **isort** for import sorting with black profile
- **flake8** for linting
- Pre-commit hooks automatically enforce formatting

## Testing Strategy

- **Unit tests**: `tests/unit/` - Test individual components
- **Integration tests**: `tests/integration/` - Test component interactions
- **pytest-asyncio** for async test support
- Tests should cover both English and Chinese functionality

## Agent Workflow

1. **Question Processing**: User input is structured into `Question` model
2. **Analysis Phase**: `AnalysisAgent` processes question and retrieves relevant resume content
3. **Evaluation Phase**: `EvaluateAgent` evaluates analysis and determines appropriate system action
4. **Response Formatting**: System returns `SystemResponse` with answer, confidence, and action suggestions

## Special Considerations

- **Bilingual Support**: System handles both Chinese (Traditional) and English
- **RAG Integration**: All responses should be grounded in resume content from ChromaDB
- **Confidence Scoring**: Responses include confidence levels for quality assessment
- **Action System**: System can suggest clarification requests or human escalation
- **Async Processing**: Core processing functions use async/await patterns

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
