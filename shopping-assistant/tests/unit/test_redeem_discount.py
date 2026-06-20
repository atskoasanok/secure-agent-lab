# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from app.agent import DISCOUNT_STATUS, DISCOUNT_STORE, redeem_discount


def test_redeem_discount_success() -> None:
    """Verifies that a valid discount code can be successfully redeemed by a registered user."""
    DISCOUNT_STORE.update({"WELCOME50": False, "SUMMER20": False})
    DISCOUNT_STATUS.update({"WELCOME50": True, "SUMMER20": True})
    result = redeem_discount(code="WELCOME50", user_id="USER123")
    assert result.startswith("Success:")
    assert DISCOUNT_STORE["WELCOME50"] is True


def test_redeem_discount_single_use() -> None:
    """Verifies that a discount code can only be redeemed once."""
    DISCOUNT_STORE.update({"WELCOME50": False, "SUMMER20": False})
    DISCOUNT_STATUS.update({"WELCOME50": True, "SUMMER20": True})
    # First redemption succeeds
    result1 = redeem_discount(code="SUMMER20", user_id="USER456")
    assert result1.startswith("Success:")

    # Second redemption fails
    result2 = redeem_discount(code="SUMMER20", user_id="USER456")
    assert result2.startswith("Error:")
    assert "already been redeemed" in result2


def test_redeem_discount_unregistered_user() -> None:
    """Verifies that an unregistered user ID (e.g. guest_) is rejected from redeeming codes."""
    DISCOUNT_STORE.update({"WELCOME50": False, "SUMMER20": False})
    DISCOUNT_STATUS.update({"WELCOME50": True, "SUMMER20": True})
    result = redeem_discount(code="WELCOME50", user_id="guest_123")
    assert result.startswith("Error:")
    assert "Registered user account required" in result


def test_redeem_discount_invalid_code() -> None:
    """Verifies that invalid discount codes are rejected."""
    DISCOUNT_STORE.update({"WELCOME50": False, "SUMMER20": False})
    DISCOUNT_STATUS.update({"WELCOME50": True, "SUMMER20": True})
    result = redeem_discount(code="NOT_A_CODE", user_id="USER123")
    assert result.startswith("Error:")
    assert "Invalid discount code" in result
