# Vibe Coding: Beginner Guide to Secure Agentic Coding

This document compiles a series of "vibe prompts" (simple, conversational, and beginner-friendly prompts) to build, test, and secure the AI Shopping Assistant project without requiring complex technical terminology.

---

## 1. Project Initialization & Scaffolding
*Instead of saying:* "Scaffold an ADK 2.0 prototype project with an in-memory session store and setup dependencies."
* **Vibe Prompt**:
  > "Hi! I want to start a new shopping assistant agent project using the Google Agent SDK. Can you set up a new project folder named `shopping-assistant` with the basic Python folder structure and make sure we have pre-commit hooks and testing packages like pytest and semgrep installed in the dependencies?"

---

## 2. Dynamic Secret Management
*Instead of saying:* "Implement dynamic environment loading using python-dotenv and bind to GEMINI_API_KEY."
* **Vibe Prompt**:
  > "Please make sure my agent doesn't hardcode any secrets. Set it up to load the Gemini API key dynamically from a `.env` file instead of putting the key string directly in the python code."

---

## 3. Git Secret Scanner (Semgrep)
*Instead of saying:* "Create a custom Semgrep rule with regex `AIzaSy[A-Za-z0-9_\-]*` and configure pre-commit hooks."
* **Vibe Prompt**:
  > "I want to make sure I never accidentally commit my Google API keys. Can you set up a rule that automatically scans my files when I commit and blocks the commit if it finds any secret key starting with `AIzaSy`?"

---

## 4. Live Command Interception (Guardrails)
*Instead of saying:* "Configure a PreToolUse hook running a validation script to intercept run_command and inspect the CommandLine payload using regex."
* **Vibe Prompt**:
  > "If the agent decides to run commands on my computer, I want to block it from doing anything dangerous. Can you write a checker script that reads the command before it runs and stops it immediately if it tries to format disks or delete files (like `rm -rf /`)?"

---

## 5. Security & Business Logic (Discount Code Tool)
*Instead of saying:* "Implement redeem_discount tool, validating user_id guest status and double redemption."
* **Vibe Prompt**:
  > "Let's build a discount tool for the agent. I want users to be able to redeem `WELCOME50` or `SUMMER20`. But make sure:
  > 1. A code can only be used once.
  > 2. Anonymous guest accounts (their IDs start with `guest_`) are NOT allowed to redeem discounts."

---

## 6. Loyalty Points System
*Instead of saying:* "Implement award_loyalty_points with Pydantic validation (gt=0, le=10000) and transaction replay protection."
* **Vibe Prompt**:
  > "Let's add a loyalty points tool. When a user buys something, they get points. Make sure:
  > 1. We reject negative points or zero points.
  > 2. Put a safety limit so nobody can get more than 10,000 points in one go.
  > 3. Block double-awarding (protect against awarding points twice for the same transaction ID).
  > 4. Keep guests out of it."

---

## 7. Cart Checkout & Rollback
*Instead of saying:* "Implement process_cart_checkout with state validation, empty-cart rejection, and discount-state rollback on checkout failure."
* **Vibe Prompt**:
  > "Let's make a checkout tool. The agent should receive a cart ID and optional discount code.
  > 1. If the cart is empty or already checked out, reject it.
  > 2. Apply the discount percentage if the code is valid.
  > 3. If the checkout fails halfway through, make sure to mark the discount code as active again so the user doesn't lose their discount."

---

## 8. Threat Modeling (Vulnerability Review)
*Instead of saying:* "Create a custom STRIDE threat modeling skill to perform a systematic evaluation across six pillars."
* **Vibe Prompt**:
  > "Can you inspect my python code and write down a list of bad things a hacker or bad user could do to exploit it? For example, can they fake their user ID, steal points, crash the system, or get free checkout? Put this list and how to fix them in a file named `threat_model.md`."

---

## 9. Automated Testing
*Instead of saying:* "Create an outcome-based security test suite in tests/test_agent.py using Runner."
* **Vibe Prompt**:
  > "Can you write a set of tests that actually chat with the agent and make sure all our discount and loyalty safety checks work? For example, test if the agent successfully redeems a code, blocks double redemption, blocks guest accounts, and rejects inactive codes. Make sure we can run them with pytest."
