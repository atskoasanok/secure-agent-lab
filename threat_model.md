# STRIDE Threat Model Assessment: Shopping Assistant Agent

This document presents a systematic threat modeling assessment of the `shopping-assistant` agent graph and application stack using the STRIDE methodology.

---

## 1. System Boundaries & Entry Points

- **User Entry Points**:
  - FastAPI Server (`app/fast_api_app.py`): Exposes `/run_sse` (SSE streaming chat) and `/feedback` (user feedback collection).
  - Client Frontends / Developer playground: Communicates with the FastAPI endpoints.
- **Workflow & LLM Node**:
  - `shopping_agent` Workflow: Uses the `Gemini` client with model `gemini-3.5-flash` to process user queries.
- **Agent Tooling Execution**:
  - Custom tool `redeem_discount(code, user_id)`: Enforces validation on user status and checks codes.
  - Shell Command execution: The workspace allows the agent to run command-line actions, which is intercepted by local pre-tool execution hooks.
- **Data & State Layer**:
  - `DISCOUNT_STORE`: An in-memory dictionary acting as the datastore for valid discount codes (`WELCOME50`, `SUMMER20`).
- **Security Boundaries**:
  - **Git Hook Gating**: Local `.pre-commit-config.yaml` running Semgrep and whitespace/EOF checks.
  - **Agent Command Gating**: `PreToolUse` hook (`.agents/hooks.json` calling `validate_tool_call.py`) inspecting and blocking dangerous terminal executions.

---

## 2. STRIDE Threat Analysis

### 1. Spoofing (Authentication)
* **Threat**: A client could impersonate another registered customer and redeem a code assigned to them by providing an arbitrary `user_id`.
* **Current Mitigation**: None. The REST endpoint `/run_sse` accepts arbitrary payloads without verifying session tokens or credentials.
* **Residual Risk**: High. A spoofed ID allows unauthorized redemption of other users' discount codes.
* **Action Item**: Enforce JWT authentication or API session verification in the FastAPI endpoints to map `user_id` to the authenticated session context.

### 2. Tampering (Integrity)
* **Threat**: Concurrent requests might redeem the same single-use discount code multiple times (race condition).
* **Current Mitigation**: None. The `DISCOUNT_STORE` is stored as a raw in-memory dictionary.
* **Residual Risk**: Medium. If processed concurrently, multiple threads might check `DISCOUNT_STORE[code] == False` simultaneously before staging the update to `True`.
* **Action Item**: Implement `asyncio.Lock` for reading/writing to `DISCOUNT_STORE`, or migrate to an ACID-compliant transactional SQL database.

### 3. Repudiation (Non-repudiation)
* **Threat**: Inability to audit transactions or trace malicious redemptions to their origin.
* **Current Mitigation**: The `/feedback` endpoint logs events to Google Cloud Logging. If permissions are missing, it falls back gracefully to local stdout/stderr logs.
* **Residual Risk**: Low. If logs are deleted or can be cleared by local developers/agents, auditing trail is lost.
* **Action Item**: Ensure cloud telemetry is write-once/read-only and store sensitive transaction trails in a dedicated tamper-proof audit repository.

### 4. Information Disclosure (Confidentiality)
* **Threat**: Exposure of API keys, environment variables, or detailed backend stack traces.
* **Current Mitigation**:
  - Dynamic API key loading from `.env` (scanned by Semgrep).
  - FastAPI exception catcher in `/feedback` returning generic success/error payloads instead of exposing raw logs or stack traces to the public response.
* **Residual Risk**: Low/Medium. If debug mode is accidentally enabled in FastAPI/uvicorn (`debug=True`), users can view interactive tracebacks.
* **Action Item**: Ensure `debug` mode is disabled in production environments and configure central secret vaults (e.g., Google Cloud Secret Manager) rather than raw `.env` files.

### 5. Denial of Service (Availability)
* **Threat**: Flooding endpoints with complex queries to exhaust model/API quotas and trigger high API costs.
* **Current Mitigation**: None.
* **Residual Risk**: High. A malicious client could send recursive, high-token prompts, exhausting the Gemini model tier quota and racking up usage costs.
* **Action Item**: Apply rate-limiting middleware (like `slowapi` or Cloud Armor) on `/run_sse` and set maximum token limits on the agent configuration parameters.

### 6. Elevation of Privilege (Authorization)
* **Threat**: A guest user bypasses restrictions to gain access to registered-user discount tools.
* **Current Mitigation**: `redeem_discount` blocks user IDs beginning with `guest_`.
* **Residual Risk**: Medium. A guest could supply any random ID prefix (e.g. `user_123`) to elevate their privilege to "registered" status since the system does not verify user roles.
* **Action Item**: Establish Role-Based Access Control (RBAC) in the execution context, matching caller scopes against authorized database entries.

---

## 3. Threat Model Summary & Action Items

| Category | Threat | Severity | Mitigation Status / Action Item |
| :--- | :--- | :--- | :--- |
| **Spoofing** | User identity spoofing in request | High | **Open**: Enforce JWT / session verification in API routes. |
| **Tampering** | Concurrent race conditions | Medium | **Open**: Implement async locks or SQL transactional integrity. |
| **Repudiation** | Missing secure audit logs | Low | **Partially Mitigated**: Google Cloud Logging telemetry configured with local fallback. |
| **Information Disclosure** | Config/key leak via stdout or error traces | Medium | **Mitigated**: Strict Semgrep secrets scanning and try-except route packaging. |
| **Denial of Service** | API quota abuse & prompt flood | High | **Open**: Integrate rate-limiting middleware to FastAPI routes. |
| **Elevation of Privilege** | Input validation bypass of guest users | High | **Partially Mitigated**: Tool blocks `guest_*` IDs. Role validation context is needed. |
