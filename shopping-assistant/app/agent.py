# shopping-assistant/app/agent.py
from __future__ import annotations

import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.apps.app import App
from google.adk.models.google_llm import Gemini
from google.adk.workflow import Workflow
from pydantic import BaseModel, Field, ValidationError

# Load project folder .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../../.env"))
api_key = os.environ.get("GEMINI_API_KEY")

model = Gemini(model="gemini-3.5-flash", api_key=api_key)  # type: ignore

# In-memory discount redemption store (simulating database state)
DISCOUNT_STORE: dict[str, bool] = {"WELCOME50": False, "SUMMER20": False}

# In-memory stores for loyalty points
LOYALTY_POINTS_STORE: dict[str, int] = {}
PROCESSED_TRANSACTIONS: set[str] = set()


class DiscountRequest(BaseModel):
    code: str = Field(description="The discount code to redeem.")
    user_id: str = Field(description="The ID of the user requesting redemption.")


class AwardPointsRequest(BaseModel):
    user_id: str = Field(description="The ID of the user receiving the points.")
    points: int = Field(gt=0, le=10000, description="The number of points to award (must be positive and <= 10000).")
    transaction_id: str = Field(description="The unique transaction ID for the purchase.")


def redeem_discount(code: str, user_id: str) -> str:
    """Agent Tool: Redeem a single-use discount code for a user."""
    if code not in DISCOUNT_STORE:
        return "Error: Invalid discount code."
    if DISCOUNT_STORE[code]:
        return "Error: Discount code has already been redeemed."
    if not user_id or user_id.startswith("guest_"):
        return "Error: Registered user account required to redeem discounts."

    DISCOUNT_STORE[code] = True
    return f"Success: Discount code {code} redeemed successfully for user {user_id}."


def award_loyalty_points(user_id: str, points: int, transaction_id: str) -> str:
    """Agent Tool: Award loyalty points to a registered user's account after a successful purchase."""
    try:
        req = AwardPointsRequest(user_id=user_id, points=points, transaction_id=transaction_id)
    except ValidationError as e:
        return f"Error: Validation failed. {e}"

    if not req.user_id or req.user_id.startswith("guest_"):
        return "Error: Registered user account required to award loyalty points."

    if req.transaction_id in PROCESSED_TRANSACTIONS:
        return f"Error: Transaction {req.transaction_id} has already been awarded points."

    PROCESSED_TRANSACTIONS.add(req.transaction_id)
    current_points = LOYALTY_POINTS_STORE.get(req.user_id, 0)
    LOYALTY_POINTS_STORE[req.user_id] = current_points + req.points
    return f"Success: Awarded {req.points} points to user {req.user_id} for transaction {req.transaction_id}."


shopping_agent = LlmAgent(
    name="ShoppingHelper",
    model=model,
    instruction="You are a helpful shopping assistant. Use your tools to redeem discount codes and award loyalty points for users.",
    tools=[redeem_discount, award_loyalty_points],
)

root_workflow = Workflow(
    name="shopping_assistant_workflow", edges=[("START", shopping_agent)]
)

root_agent = root_workflow

app = App(name="app", root_agent=root_workflow)
