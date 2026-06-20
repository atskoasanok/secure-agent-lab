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

# In-memory discount status store (active vs inactive)
DISCOUNT_STATUS: dict[str, bool] = {"WELCOME50": True, "SUMMER20": True}

# In-memory stores for loyalty points
LOYALTY_POINTS_STORE: dict[str, int] = {}
PROCESSED_TRANSACTIONS: set[str] = set()

# In-memory stores for carts and orders
CART_STORE: dict[str, dict] = {
    "CART_123": {
        "user_id": "USER123",
        "items": ["Item A", "Item B"],
        "total": 150.00,
        "status": "active",
    },
    "CART_456": {
        "user_id": "guest_999",
        "items": ["Item C"],
        "total": 45.00,
        "status": "active",
    },
    "CART_EMPTY": {
        "user_id": "USER123",
        "items": [],
        "total": 0.00,
        "status": "active",
    },
}
ORDER_STORE: dict[str, dict] = {}


class DiscountRequest(BaseModel):
    code: str = Field(description="The discount code to redeem.")
    user_id: str = Field(description="The ID of the user requesting redemption.")


class AwardPointsRequest(BaseModel):
    user_id: str = Field(description="The ID of the user receiving the points.")
    points: int = Field(gt=0, le=10000, description="The number of points to award (must be positive and <= 10000).")
    transaction_id: str = Field(description="The unique transaction ID for the purchase.")


class CheckoutRequest(BaseModel):
    cart_id: str = Field(description="The unique ID of the cart to check out.")
    discount_code: str | None = Field(default=None, description="Optional discount code to apply to the cart.")


class UpdateDiscountStatusRequest(BaseModel):
    code: str = Field(description="The discount code to update.")
    active: bool = Field(description="Whether to activate (True) or deactivate (False) the code.")
    admin_id: str = Field(description="The ID of the administrator executing the update.")


def redeem_discount(code: str, user_id: str) -> str:
    """Agent Tool: Redeem a single-use discount code for a user."""
    if code not in DISCOUNT_STORE:
        return "Error: Invalid discount code."
    if code in DISCOUNT_STATUS and not DISCOUNT_STATUS[code]:
        return "Error: Discount code is inactive."
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


def process_cart_checkout(cart_id: str, discount_code: str | None = None) -> str:
    """Agent Tool: Process checkout for a cart, optionally applying a discount code and generating an order."""
    try:
        req = CheckoutRequest(cart_id=cart_id, discount_code=discount_code)
    except ValidationError as e:
        return f"Error: Validation failed. {e}"

    if req.cart_id not in CART_STORE:
        return "Error: Invalid cart ID."

    cart = CART_STORE[req.cart_id]

    if cart["status"] != "active":
        return f"Error: Cart {req.cart_id} is already checked out."

    if not cart["items"] or cart["total"] <= 0:
        return f"Error: Cart {req.cart_id} is empty."

    discount_rate = 0.0
    user_id = cart["user_id"]
    applied_code = None

    if req.discount_code:
        redemption_result = redeem_discount(code=req.discount_code, user_id=user_id)
        if redemption_result.startswith("Error:"):
            return redemption_result

        applied_code = req.discount_code
        if applied_code == "WELCOME50":
            discount_rate = 0.50
        elif applied_code == "SUMMER20":
            discount_rate = 0.20

    try:
        original_total = cart["total"]
        discount_amount = original_total * discount_rate
        final_total = original_total - discount_amount

        cart["status"] = "checked_out"

        order_id = f"ORDER_{req.cart_id}_{len(ORDER_STORE) + 1}"
        ORDER_STORE[order_id] = {
            "cart_id": req.cart_id,
            "user_id": user_id,
            "items": cart["items"],
            "original_total": original_total,
            "discount_code": applied_code,
            "discount_amount": discount_amount,
            "final_total": final_total,
            "status": "processed",
        }

        return f"Success: Cart {req.cart_id} checked out successfully. Order {order_id} created with final total ${final_total:.2f}."
    except Exception as e:
        if applied_code and applied_code in DISCOUNT_STORE:
            DISCOUNT_STORE[applied_code] = False
        return f"Error: Checkout failed. {e}"


def update_discount_status(code: str, active: bool, admin_id: str) -> str:
    """Agent Tool: Update the active status of a discount code (admin only)."""
    try:
        req = UpdateDiscountStatusRequest(code=code, active=active, admin_id=admin_id)
    except ValidationError as e:
        return f"Error: Validation failed. {e}"

    if not req.admin_id or not req.admin_id.startswith("admin_"):
        return "Error: Administrator privileges required to update discount status."

    if req.code not in DISCOUNT_STORE:
        return "Error: Invalid discount code."

    DISCOUNT_STATUS[req.code] = req.active
    status_str = "activated" if req.active else "deactivated"
    return f"Success: Discount code {req.code} has been {status_str} by administrator {req.admin_id}."


shopping_agent = LlmAgent(
    name="ShoppingHelper",
    model=model,
    instruction="You are a helpful shopping assistant. Use your tools to redeem discount codes, award loyalty points, process cart checkout, and update discount status for users.",
    tools=[redeem_discount, award_loyalty_points, process_cart_checkout, update_discount_status],
)

root_workflow = Workflow(
    name="shopping_assistant_workflow", edges=[("START", shopping_agent)]
)

root_agent = root_workflow

app = App(name="app", root_agent=root_workflow)
