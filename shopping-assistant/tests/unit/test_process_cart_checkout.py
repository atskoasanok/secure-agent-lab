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

from app.agent import CART_STORE, ORDER_STORE, DISCOUNT_STORE, process_cart_checkout


def test_checkout_success_no_discount() -> None:
    """Verifies successful checkout of an active cart without a discount code."""
    CART_STORE["CART_TEST_1"] = {
        "user_id": "USER123",
        "items": ["Item A"],
        "total": 100.00,
        "status": "active",
    }
    ORDER_STORE.clear()

    result = process_cart_checkout(cart_id="CART_TEST_1")
    assert result.startswith("Success:")
    assert CART_STORE["CART_TEST_1"]["status"] == "checked_out"
    assert len(ORDER_STORE) == 1

    order_id = list(ORDER_STORE.keys())[0]
    assert ORDER_STORE[order_id]["final_total"] == 100.00
    assert ORDER_STORE[order_id]["discount_code"] is None


def test_checkout_success_with_discount() -> None:
    """Verifies successful checkout with a valid discount code for a registered user."""
    CART_STORE["CART_TEST_2"] = {
        "user_id": "USER123",
        "items": ["Item A"],
        "total": 100.00,
        "status": "active",
    }
    DISCOUNT_STORE.update({"WELCOME50": False})
    ORDER_STORE.clear()

    result = process_cart_checkout(cart_id="CART_TEST_2", discount_code="WELCOME50")
    assert result.startswith("Success:")
    assert CART_STORE["CART_TEST_2"]["status"] == "checked_out"
    assert DISCOUNT_STORE["WELCOME50"] is True

    order_id = list(ORDER_STORE.keys())[0]
    assert ORDER_STORE[order_id]["final_total"] == 50.00
    assert ORDER_STORE[order_id]["discount_code"] == "WELCOME50"


def test_checkout_already_checked_out() -> None:
    """Verifies that checking out an already checked out cart is rejected."""
    CART_STORE["CART_TEST_3"] = {
        "user_id": "USER123",
        "items": ["Item A"],
        "total": 100.00,
        "status": "checked_out",
    }
    ORDER_STORE.clear()

    result = process_cart_checkout(cart_id="CART_TEST_3")
    assert result.startswith("Error:")
    assert "already checked out" in result


def test_checkout_guest_with_discount() -> None:
    """Verifies that guest checkouts with discount codes are rejected."""
    CART_STORE["CART_TEST_4"] = {
        "user_id": "guest_123",
        "items": ["Item A"],
        "total": 100.00,
        "status": "active",
    }
    DISCOUNT_STORE.update({"SUMMER20": False})
    ORDER_STORE.clear()

    result = process_cart_checkout(cart_id="CART_TEST_4", discount_code="SUMMER20")
    assert result.startswith("Error:")
    assert "Registered user account required" in result
    assert DISCOUNT_STORE["SUMMER20"] is False


def test_checkout_empty_cart() -> None:
    """Verifies that checking out an empty cart is rejected."""
    CART_STORE["CART_TEST_5"] = {
        "user_id": "USER123",
        "items": [],
        "total": 0.00,
        "status": "active",
    }
    ORDER_STORE.clear()

    result = process_cart_checkout(cart_id="CART_TEST_5")
    assert result.startswith("Error:")
    assert "empty" in result


def test_checkout_invalid_cart() -> None:
    """Verifies that checking out an invalid cart ID is rejected."""
    result = process_cart_checkout(cart_id="CART_INVALID")
    assert result.startswith("Error:")
    assert "Invalid cart ID" in result
