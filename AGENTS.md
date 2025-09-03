# Repository Guidelines

## Project Structure & Modules

- `src/backend`: Core Python logic (agents, data, tools).
- `src/frontend`: Static assets for the public site.
- `tests`: Unit, integration, performance, and UX tests.
- `scripts`: Deployment helpers (`deploy_backend.sh`, `deploy_frontend.sh`).
- Top level: `app.py` (Gradio app), `pyproject.toml`, `.env.example`, `requirements.txt`.

## Build, Test, and Dev Commands

- Create venv: `python -m venv .venv && source .venv/bin/activate`.
- Install deps: `pip install -r requirements.txt`.
- Run app: `python app.py` (starts Gradio on port 7860).
- Tests: `pytest` or `pytest tests/unit -q` (configured via `[tool.pytest.ini_options]`).
- Lint/format (Python): `ruff --fix . && ruff format .`.
- Format (JS/TS only): `prettier --write "**/*.{js,jsx,ts,tsx,css,json,yaml,yml}"`.
- Optional: `pre-commit install && pre-commit run -a` before committing.

## Coding Style & Naming

- Python: Black-compatible, line length 88 (`[tool.black]`). Imports via isort profile "black".
- Linting: Ruff enforced in pre-commit; keep zero warnings.
- Names: `snake_case` for functions/variables, `PascalCase` for classes, module files `lower_snake.py`. Tests `test_*.py` mirroring module paths.
- JS/TS assets: Prettier defaults; avoid formatting HTML from pre-commit (already excluded).

## Testing Guidelines

- Framework: `pytest` with asyncio auto mode. Place tests under `tests/` (unit, integration, performance, ux).
- Name tests `test_<unit>.py` and functions `test_<behavior>()`.
- Add tests with new features and bug fixes; mock external APIs. Run `pytest -q` locally and ensure it passes.

## Commit & Pull Requests

- Commits: Follow Conventional Commits used here (e.g., `feat: ...`, `fix(processor): ...`). Prefer small, focused commits with imperative subjects.
- PRs: Include clear description, linked issues, steps to verify, and screenshots/GIFs for UI-affecting changes. Ensure tests pass and pre-commit hooks are clean.

## Security & Config

- Copy `.env.example` to `.env`; set `OPENAI_API_KEY` and any deploy tokens locally. Never commit secrets.
- Python 3.10+ required. Avoid breaking changes to public interfaces without a migration note in the PR.
