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
- **Loyalty Points System**: Implemented the `award_loyalty_points(user_id: str, points: int, transaction_id: str)` tool, enforcing:
  - Input validation using Pydantic (`AwardPointsRequest`) ensuring points are positive (`gt=0`) and capped at `10000`.
  - Replay protection checking against a local transaction set (`PROCESSED_TRANSACTIONS`).
  - Registered user validation checking against guest account prefixes.
- **Loyalty Points Verification**: Added isolated, outcome-based unit tests verifying success, guest rejection, negative/zero points, upper limit guard, and replay attack protection in `tests/unit/test_award_loyalty_points.py`. All tests pass successfully.
- **Cart Checkout System**: Implemented the `process_cart_checkout(cart_id: str, discount_code: str | None)` tool, enforcing:
  - Input validation using Pydantic (`CheckoutRequest`).
  - Checking that the cart exists in `CART_STORE`, is active, and is not empty.
  - Applying discount code rules with guest rejection validation.
  - Changing cart state and generating orders in `ORDER_STORE`.
  - Error rollback mechanism, restoring the discount code to active if checkout fails mid-transaction.
- **Cart Checkout Verification**: Added unit tests in `tests/unit/test_process_cart_checkout.py` covering successful checks, discount logic, duplicate checkouts, guest checks, and empty carts. All tests pass successfully.
- **Discount Status Management (Admin)**: Implemented the `update_discount_status(code: str, active: bool, admin_id: str)` tool, enforcing:
  - Input validation using Pydantic (`UpdateDiscountStatusRequest`).
  - Role-based checking asserting that the caller's ID begins with `admin_`.
  - Storing the active status state in `DISCOUNT_STATUS`.
  - Checking active status in the code redemption pipeline and rejecting redemption for inactive codes.
- **Discount Status Management Verification**: Added unit tests in `tests/unit/test_update_discount_status.py` covering successful toggles, non-admin rejection, invalid code handling, and verification that deactivated codes cannot be redeemed. All tests pass successfully.
- **Agent Security Test Suite**: Implemented `tests/test_agent.py` using `Runner` and `InMemorySessionService` to run end-to-end outcome-based tests verifying discount redemption guardrails (success, single-use, guest account debarment, active status toggles, and invalid codes). All tests pass successfully (bringing the test suite to **29 passed** tests).

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

### 3. Hook Choice Trade-offs & Security Barriers
Choosing between Git Hooks, Agent Hooks, and Remote CI/CD Gates requires balancing immediate runtime safety against code integrity:
- **Agent Hooks**: Capture events mid-trajectory to block dangerous tool execution (like system destruction) before they run, but only apply inside the wrapper environment.
- **Git Hooks**: Native to version control to capture bad commits before leaving the machine, but can be bypassed with `--no-verify`.
- **Remote CI/CD Gates**: Ultimate, unbypassable barriers on the cloud servers to prevent bad code from merging, but have a slower feedback loop.

| Barrier Type | Best Used For | Strengths | Weaknesses |
| :--- | :--- | :--- | :--- |
| **Agent Hooks** | Live runtime/tool execution safety (e.g. blocking `rm`, preventing bad calls). | Runs instantly mid-action *before* any damage occurs. | Bypassed if developers run scripts outside the agent wrapper. |
| **Git Hooks (Local)** | Instant developer feedback (formatting, lints, secret scans). | Fast feedback loop; prevents bad commits before leaving local workspace. | Easily bypassed using `git commit --no-verify`. |
| **Remote CI/CD (Cloud)** | Ultimate compliance and pull-request gating. | Unbypassable; isolated runner execution. | Slower feedback loop; only runs after push. |
