# AGENTS.md

This file serves as the static context configuration for all AI coding agents working on this project.

## 1. Project Context
* **Name**: `secure-agent-lab`
* **Purpose**: Core repository for building, running, testing, and evaluating autonomous AI agents using the Google Antigravity SDK.

## 2. Environment Rules
* **Python Interpreter**: ALWAYS use the Python interpreter located at `./.venv/bin/python` to run any scripts or tools. Do not use the global `python` or `python3` command.
* **Package Management**: Use the `uv` command-line tool to manage packages or install new dependencies (e.g. `uv pip install`).
* **Environment Variables**: Local API keys (e.g., `GEMINI_API_KEY`, `OPENAI_API_KEY`) must be loaded from `.env` using `python-dotenv`.

## 3. Directory Structure & Conventions
* **`src/`**: All production source code.
  * **`src/config.py`**: Configuration builder.
  * **`src/agents/`**: Agent configurations and definitions.
  * **`src/tools/`**: Custom python tools.
  * **`src/skills/`**: Domain-specific dynamic context files.
* **`tests/`**: Contains deterministic tests verifying custom tools and framework setup.
* **`evals/`**: Contains agent evaluation scripts, datasets, and scorecards.

## 4. Coding Guidelines
* **Async by default**: The Google Antigravity SDK runs asynchronously. Always use `async`/`await` for agent interactions and asynchronous operations.
* **Type Hinting**: All new Python code must include proper type hints.
* **Pydantic**: Use Pydantic v2 schemas for structured tool parameters and agent configuration.
* **Test before Implementation**: Whenever implementing a new tool or agent logic, write unit tests in `tests/` to verify behavior before writing the implementation.
