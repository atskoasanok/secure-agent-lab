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

from app.agent import LOYALTY_POINTS_STORE, PROCESSED_TRANSACTIONS, award_loyalty_points


def test_award_loyalty_points_success() -> None:
    """Verifies that points are successfully awarded to a registered user for a unique transaction."""
    LOYALTY_POINTS_STORE.clear()
    PROCESSED_TRANSACTIONS.clear()

    result = award_loyalty_points(user_id="USER123", points=50, transaction_id="TX_101")
    assert result.startswith("Success:")
    assert LOYALTY_POINTS_STORE["USER123"] == 50
    assert "TX_101" in PROCESSED_TRANSACTIONS


def test_award_loyalty_points_guest_user() -> None:
    """Verifies that guest accounts are rejected from receiving loyalty points."""
    LOYALTY_POINTS_STORE.clear()
    PROCESSED_TRANSACTIONS.clear()

    result = award_loyalty_points(user_id="guest_123", points=50, transaction_id="TX_102")
    assert result.startswith("Error:")
    assert "Registered user account required" in result
    assert "guest_123" not in LOYALTY_POINTS_STORE


def test_award_loyalty_points_non_positive_points() -> None:
    """Verifies that zero or negative points are blocked by Pydantic validation."""
    LOYALTY_POINTS_STORE.clear()
    PROCESSED_TRANSACTIONS.clear()

    # Test zero
    result1 = award_loyalty_points(user_id="USER123", points=0, transaction_id="TX_103")
    assert result1.startswith("Error: Validation failed.")

    # Test negative
    result2 = award_loyalty_points(user_id="USER123", points=-10, transaction_id="TX_104")
    assert result2.startswith("Error: Validation failed.")


def test_award_loyalty_points_max_points_limit() -> None:
    """Verifies that points above the upper threshold (10,000) are blocked."""
    LOYALTY_POINTS_STORE.clear()
    PROCESSED_TRANSACTIONS.clear()

    result = award_loyalty_points(user_id="USER123", points=10001, transaction_id="TX_105")
    assert result.startswith("Error: Validation failed.")


def test_award_loyalty_points_replay_attack() -> None:
    """Verifies that the same transaction_id cannot be processed twice to award points."""
    LOYALTY_POINTS_STORE.clear()
    PROCESSED_TRANSACTIONS.clear()

    # First award succeeds
    result1 = award_loyalty_points(user_id="USER123", points=100, transaction_id="TX_200")
    assert result1.startswith("Success:")
    assert LOYALTY_POINTS_STORE["USER123"] == 100

    # Second award with same transaction_id fails
    result2 = award_loyalty_points(user_id="USER123", points=50, transaction_id="TX_200")
    assert result2.startswith("Error:")
    assert "already been awarded points" in result2
    assert LOYALTY_POINTS_STORE["USER123"] == 100  # remains unchanged
