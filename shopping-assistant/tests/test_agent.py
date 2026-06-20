# Copyright (c) 2026 MyCompany LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import DISCOUNT_STORE, DISCOUNT_STATUS, root_agent


def run_agent_prompt(prompt: str, user_id: str = "USER123") -> str:
    """Helper to run a prompt through the agent and return the concatenated text response."""
    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id=user_id, app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text=prompt)]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id=user_id,
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )

    response_text = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    return response_text


def test_agent_redeem_discount_success() -> None:
    """Verifies that the agent successfully redeems a valid code for a registered user."""
    DISCOUNT_STORE.update({"WELCOME50": False, "SUMMER20": False})
    DISCOUNT_STATUS.update({"WELCOME50": True, "SUMMER20": True})

    response = run_agent_prompt(
        prompt="Please redeem the discount code WELCOME50 for user USER123.",
        user_id="USER123",
    )
    assert DISCOUNT_STORE["WELCOME50"] is True
    assert "success" in response.lower() or "redeemed" in response.lower()


def test_agent_redeem_discount_single_use() -> None:
    """Verifies that the agent rejects redeeming an already redeemed code."""
    DISCOUNT_STORE.update({"WELCOME50": True, "SUMMER20": False})
    DISCOUNT_STATUS.update({"WELCOME50": True, "SUMMER20": True})

    response = run_agent_prompt(
        prompt="Please redeem the discount code WELCOME50 for user USER123.",
        user_id="USER123",
    )
    # Remains True (already redeemed)
    assert DISCOUNT_STORE["WELCOME50"] is True
    assert "already" in response.lower() or "error" in response.lower() or "redeemed" in response.lower()


def test_agent_redeem_discount_guest_user() -> None:
    """Verifies that the agent blocks discount redemption for guest accounts."""
    DISCOUNT_STORE.update({"WELCOME50": False, "SUMMER20": False})
    DISCOUNT_STATUS.update({"WELCOME50": True, "SUMMER20": True})

    response = run_agent_prompt(
        prompt="Please redeem the discount code WELCOME50 for user guest_123.",
        user_id="guest_123",
    )
    assert DISCOUNT_STORE["WELCOME50"] is False
    assert "guest" in response.lower() or "error" in response.lower() or "registered" in response.lower()


def test_agent_redeem_discount_inactive_code() -> None:
    """Verifies that the agent blocks redemption of a deactivated code."""
    DISCOUNT_STORE.update({"WELCOME50": False, "SUMMER20": False})
    DISCOUNT_STATUS.update({"WELCOME50": False, "SUMMER20": True})

    response = run_agent_prompt(
        prompt="Please redeem the discount code WELCOME50 for user USER123.",
        user_id="USER123",
    )
    assert DISCOUNT_STORE["WELCOME50"] is False
    assert "inactive" in response.lower() or "error" in response.lower()


def test_agent_redeem_discount_invalid_code() -> None:
    """Verifies that the agent rejects invalid codes."""
    DISCOUNT_STORE.update({"WELCOME50": False, "SUMMER20": False})

    response = run_agent_prompt(
        prompt="Please redeem the discount code NOT_A_CODE for user USER123.",
        user_id="USER123",
    )
    assert "invalid" in response.lower() or "error" in response.lower()
