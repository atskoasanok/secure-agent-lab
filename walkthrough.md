# Walkthrough: Scaffolding, Testing, and Securing the AI Shopping Assistant

I have completed the full development lifecycle for the ADK 2.0 `shopping-assistant` agent, incorporating robust security guardrails, automated threat modeling, and pre-commit scans.

---

## Part 1: Scaffolding and TDD Verification

### 1. Project Setup
- Scaffolded a new Python ADK 2.0 agent project in `shopping-assistant/` using `agents-cli`.
- Configured model setup in `app/agent.py` to use `gemini-3.5-flash` with dynamic API key loading via `load_dotenv` pointing to the workspace `.env` file.
- Added quality and security packages to `pyproject.toml` (`pre-commit`, `pre-commit-hooks`, `semgrep`).

### 2. Business Logic & Testing
- Implemented `redeem_discount(code: str, user_id: str)` validating against the single-use `DISCOUNT_STORE` and preventing anonymous guest account redemptions (rejecting `guest_*` IDs).
- Wrote isolated, outcome-based unit tests verifying all validation paths in `tests/unit/test_redeem_discount.py`.
- **API telemetry fix**: Patched the `/feedback` endpoint in `app/fast_api_app.py` to catch Cloud Logging API failures and fall back to local logging. This allowed all **9 unit and integration tests** to pass successfully.

---

## Part 2: Implementing Security Guardrails & Gating Hooks

### 1. Secure Coding Standards (`CONTEXT.md`)
Created `shopping-assistant/.agents/CONTEXT.md` defining local secure coding boundaries:
- Enforcing Pydantic validation for tool parameters.
- Restricting raw shell execution.
- Defining a Pre-Commit Remediation Loop to force local agent self-correction.
- Added a **TDD Planning Gate** requiring a dedicated **Security Boundaries & Assertions** section in all implementation plans.

### 2. Git Pre-Commit Gating (Semgrep)
- Created a custom Semgrep rule file `shopping-assistant/.semgrep/rules.yaml` to scan for hardcoded Google API keys matching `AIzaSy[A-Za-z0-9_\-]*`.
- Configured `.pre-commit-config.yaml` to run `end-of-file-fixer`, `trailing-whitespace`, and our custom Semgrep scan on commit.
- Installed the hook using `uv run pre-commit install`.

### 3. Agent Execution Gating (PreToolUse)
- Configured a local agent hook in `shopping-assistant/.agents/hooks.json` to intercept any attempts to run command line tools via `run_command`.
- Created `.agents/scripts/validate_tool_call.py` to inspect command payloads via `stdin` and block destructive commands (like `rm -rf /` or `mkfs`).

### 4. STRIDE Threat Modeling
- Created a custom workspace-level threat modeling skill in `shopping-assistant/.agents/skills/stride-threat-model/SKILL.md`.
- Executed the threat model on the project's codebase, generating a comprehensive `threat_model.md` at the project root covering system boundaries and mitigation items across all six STRIDE pillars.

### 5. Verification & Commit
- Added all files and committed using `uv run git commit -m "feat: implement secure shopping assistant agent and guardrails"`.
- All pre-commit scans (`end-of-file-fixer`, `trailing-whitespace`, and `Semgrep`) passed successfully.

---

## Security & Lifecycle Q&A Summary

### 1. Handling Agent/MCP Offline State
- **Root Cause**: The MCP servers failed to start ("context canceled") because the IDE was launched from a GUI and did not inherit the terminal `$PATH` required to locate relative commands (like `"node"`).
- **Remediation**: Configure absolute paths (e.g., `/opt/homebrew/bin/node`) in the configuration files, and launch the IDE directly from your terminal session (e.g., `antigravity .`) to propagate the path environment.

### 2. Local Secure Context (`CONTEXT.md`)
- **Paved Roads**: Centralizes security policies by enforcing parameter validation via Pydantic, preventing raw shell command executions, and defining a local self-correction loop for git pre-commit hooks.
- **TDD Planning Gate**: Instructs the agent to decompose tasks and identify specific exploit vectors (Security Boundaries & Assertions) up-front during the planning phase, preventing insecure defaults before coding begins.
