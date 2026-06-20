# STRIDE Threat Model Assessment: Shopping Assistant Agent

This document presents a systematic threat modeling assessment of the `shopping-assistant` agent graph using the STRIDE methodology.

---

## 1. System Boundaries & Entry Points

- **Client/User Interaction**: The user interacts with the FastAPI server (`app/fast_api_app.py`) via the SSE streaming endpoint `/run_sse` or the `/feedback` endpoint.
- **Workflow & Agent Node**: The request is routed to the `shopping_agent` Workflow, which is powered by `gemini-3.5-flash`.
- **Tooling Execution**: The agent can invoke the custom `redeem_discount` tool.
- **Data/State Layer**: In-memory dictionary `DISCOUNT_STORE` acts as a simulated datastore.

---

## 2. STRIDE Threat Analysis

### 1. Spoofing (Authentication)
*   **Threat**: A user can spoof another user's identity by supplying an arbitrary `user_id` in the API request or chat conversation.
*   **Manifestation**: The `/run_sse` endpoint does not authenticate or map the request to a verified user session. A user could redeem a discount code belonging to or intended for another registered customer.
*   **Mitigation**: Integrate authentication/authorization headers (e.g., JWT) in the FastAPI routes to verify the user identity and enforce that the user ID passed to `redeem_discount` matches the authenticated caller's identity.

### 2. Tampering (Integrity)
*   **Threat**: State tampering or race conditions on the discount store.
*   **Manifestation**: The `DISCOUNT_STORE` is an in-memory dictionary. If multiple concurrent requests are processed (e.g., via multi-threaded Uvicorn), two requests might check `DISCOUNT_STORE[code]` simultaneously before it is updated, leading to double-redemption of a single-use code.
*   **Mitigation**: Implement a lock (e.g., `asyncio.Lock` or database transaction constraints) when reading and writing to the discount store, or move the state to a transactional database (e.g., PostgreSQL/Cloud SQL) with ACID compliance.

### 3. Repudiation (Non-repudiation)
*   **Threat**: Lack of transaction verification or auditing.
*   **Manifestation**: Redemptions are logged in standard stdout/stderr logs or local Python log fallback. However, there is no tamper-proof transaction log (such as cryptographic auditing or ledger database entry) to prove that a specific authenticated user made the redemption.
*   **Mitigation**: Log all redemptions with audit metadata (timestamp, authenticated user IP, session ID, cryptographic hashes) to a write-once secure logging destination.

### 4. Information Disclosure (Confidentiality)
*   **Threat**: Leakage of API keys or PII.
*   **Manifestation**: The initial version had a hardcoded Gemini API key. Although it has been moved to `.env`, any configuration leakage or unhandled exception stack traces returned by FastAPI could expose the environment variable or internal system paths.
*   **Mitigation**: Ensure strict error handling in FastAPI to return generic HTTP exception payloads to clients and keep detailed stack traces logged internally. Use secret manager vaults for managing production API keys.

### 5. Denial of Service (Availability)
*   **Threat**: Cost-based Denial of Service or rate limit exhaustion.
*   **Manifestation**: The `/run_sse` endpoint does not implement rate limiting. A malicious actor could flood the endpoint with inputs, causing the server to exhaust slot/token quotas for the Gemini model or incur high API costs.
*   **Mitigation**: Apply rate-limiting middleware (such as `slowapi` or Cloud Armor) on public endpoints, and configure token/slot quotas on the LLM model client.

### 6. Elevation of Privilege (Authorization)
*   **Threat**: Bypassing role-based access control.
*   **Manifestation**: The `redeem_discount` tool prevents user IDs starting with `"guest_"` from redeeming codes. However, any caller can supply a non-guest user ID (e.g. `"registered_user_123"`) to bypass this check without possessing the actual credentials or authorization for that user.
*   **Mitigation**: Enforce role-based access control (RBAC). The tool should verify caller permissions through the execution context.

---

## 3. Threat Model Summary & Action Items

| Category | Threat | Severity | Action Item |
| :--- | :--- | :--- | :--- |
| **Spoofing** | User identity spoofing in request | High | Enforce JWT/session authentication in API endpoints. |
| **Tampering** | Concurrent race conditions | Medium | Move store to SQL database or apply thread/async locks. |
| **Repudiation** | Missing secure audit logs | Low | Store transaction logs in a tamper-resistant system. |
| **Information Disclosure** | Config / key leak via raw stack traces | Medium | Enforce generic FastAPI error responses. |
| **Denial of Service** | API quota abuse & flood | High | Add rate-limiting middleware to FastAPI routes. |
| **Elevation of Privilege** | Input validation bypass of guest users | High | Validate caller identity context in `redeem_discount`. |
