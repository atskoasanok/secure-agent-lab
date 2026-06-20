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

from app.agent import DISCOUNT_STATUS, DISCOUNT_STORE, update_discount_status, redeem_discount


def test_update_discount_status_success() -> None:
    """Verifies that an authorized admin can deactivate and activate a discount code."""
    DISCOUNT_STATUS.update({"WELCOME50": True})

    # Deactivate
    result = update_discount_status(code="WELCOME50", active=False, admin_id="admin_alice")
    assert result.startswith("Success:")
    assert "deactivated" in result
    assert DISCOUNT_STATUS["WELCOME50"] is False

    # Activate
    result2 = update_discount_status(code="WELCOME50", active=True, admin_id="admin_bob")
    assert result2.startswith("Success:")
    assert "activated" in result2
    assert DISCOUNT_STATUS["WELCOME50"] is True


def test_update_discount_status_non_admin() -> None:
    """Verifies that non-admin accounts are rejected from updating discount status."""
    DISCOUNT_STATUS.update({"WELCOME50": True})

    # Standard user
    result = update_discount_status(code="WELCOME50", active=False, admin_id="USER123")
    assert result.startswith("Error:")
    assert "Administrator privileges required" in result
    assert DISCOUNT_STATUS["WELCOME50"] is True

    # Guest user
    result2 = update_discount_status(code="WELCOME50", active=False, admin_id="guest_abc")
    assert result2.startswith("Error:")
    assert "Administrator privileges required" in result2
    assert DISCOUNT_STATUS["WELCOME50"] is True


def test_update_discount_status_invalid_code() -> None:
    """Verifies that attempting to toggle status of non-existent discount codes is rejected."""
    result = update_discount_status(code="INVALID_CODE", active=False, admin_id="admin_alice")
    assert result.startswith("Error:")
    assert "Invalid discount code" in result


def test_deactivated_code_redemption_fails() -> None:
    """Verifies that a deactivated discount code cannot be redeemed."""
    DISCOUNT_STATUS.update({"WELCOME50": False})
    DISCOUNT_STORE.update({"WELCOME50": False})

    result = redeem_discount(code="WELCOME50", user_id="USER123")
    assert result.startswith("Error:")
    assert "inactive" in result
    assert DISCOUNT_STORE["WELCOME50"] is False
