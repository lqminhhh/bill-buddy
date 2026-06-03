import pytest

from utils.calculations import (
    calculate_equal_share,
    calculate_net_balance_by_member,
    calculate_total_owed_share_by_member,
    calculate_total_paid_by_member,
    simplify_settlements,
)


@pytest.fixture
def three_members():
    return [
        {"id": 1, "name": "Alex"},
        {"id": 2, "name": "Blair"},
        {"id": 3, "name": "Casey"},
    ]


def _expense(expense_id, amount_cents, paid_by, date="2026-05-22"):
    return {
        "id": expense_id,
        "trip_id": 1,
        "description": "test",
        "amount_cents": amount_cents,
        "expense_date": date,
        "paid_by_member_id": paid_by,
        "notes": "",
    }


def _participants(expense_id, member_ids):
    return [{"expense_id": expense_id, "member_id": mid} for mid in member_ids]


class TestCalculateEqualShare:
    def test_even_split_three_ways(self):
        result = calculate_equal_share(3000, [1, 2, 3])
        assert result == {1: 1000, 2: 1000, 3: 1000}

    def test_single_participant_gets_full_amount(self):
        assert calculate_equal_share(2500, [7]) == {7: 2500}

    def test_zero_amount_splits_to_zero(self):
        assert calculate_equal_share(0, [1, 2]) == {1: 0, 2: 0}

    def test_remainder_distributed_in_participant_order(self):
        # 100 cents / 3 = 33 + remainder 1 → first participant gets the extra cent
        result = calculate_equal_share(100, [1, 2, 3])
        assert result == {1: 34, 2: 33, 3: 33}
        assert sum(result.values()) == 100

    def test_two_cent_remainder_goes_to_first_two(self):
        # 11 cents / 3 = 3 + remainder 2 → first two participants get extras
        result = calculate_equal_share(11, [1, 2, 3])
        assert result == {1: 4, 2: 4, 3: 3}
        assert sum(result.values()) == 11

    def test_remainder_respects_participant_order_not_id_order(self):
        # Order is [3, 1, 2] — member 3 should get the extra cent, not member 1
        result = calculate_equal_share(100, [3, 1, 2])
        assert result == {3: 34, 1: 33, 2: 33}

    def test_negative_amount_raises(self):
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_equal_share(-100, [1, 2])

    def test_empty_participants_raises(self):
        with pytest.raises(ValueError, match="at least one participant"):
            calculate_equal_share(1000, [])


class TestCalculateTotalPaidByMember:
    def test_all_members_appear_even_if_they_paid_nothing(self, three_members):
        expenses = [_expense(1, 3000, paid_by=1)]
        result = calculate_total_paid_by_member(three_members, expenses)
        assert result == {1: 3000, 2: 0, 3: 0}

    def test_multiple_expenses_sum_per_payer(self, three_members):
        expenses = [
            _expense(1, 1000, paid_by=1),
            _expense(2, 2000, paid_by=2),
            _expense(3, 500, paid_by=1),
        ]
        result = calculate_total_paid_by_member(three_members, expenses)
        assert result == {1: 1500, 2: 2000, 3: 0}

    def test_no_expenses_returns_zero_for_everyone(self, three_members):
        assert calculate_total_paid_by_member(three_members, []) == {1: 0, 2: 0, 3: 0}

    def test_unknown_payer_raises(self, three_members):
        expenses = [_expense(1, 1000, paid_by=99)]
        with pytest.raises(ValueError, match="Unknown payer"):
            calculate_total_paid_by_member(three_members, expenses)

    def test_negative_amount_raises(self, three_members):
        expenses = [_expense(1, -100, paid_by=1)]
        with pytest.raises(ValueError, match="cannot be negative"):
            calculate_total_paid_by_member(three_members, expenses)


class TestCalculateTotalOwedShareByMember:
    def test_equal_split_across_all_members(self, three_members):
        expenses = [_expense(1, 3000, paid_by=1)]
        participants = _participants(1, [1, 2, 3])
        result = calculate_total_owed_share_by_member(
            three_members, expenses, participants
        )
        assert result == {1: 1000, 2: 1000, 3: 1000}

    def test_subset_split_only_charges_participants(self, three_members):
        expenses = [_expense(1, 2000, paid_by=1)]
        participants = _participants(1, [1, 2])  # Casey not included
        result = calculate_total_owed_share_by_member(
            three_members, expenses, participants
        )
        assert result == {1: 1000, 2: 1000, 3: 0}

    def test_remainder_cents_are_distributed(self, three_members):
        # 10 cents split 3 ways → 4 + 3 + 3, totals must equal 10
        expenses = [_expense(1, 10, paid_by=1)]
        participants = _participants(1, [1, 2, 3])
        result = calculate_total_owed_share_by_member(
            three_members, expenses, participants
        )
        assert sum(result.values()) == 10

    def test_multiple_expenses_accumulate(self, three_members):
        expenses = [
            _expense(1, 3000, paid_by=1),
            _expense(2, 1500, paid_by=2),
        ]
        participants = _participants(1, [1, 2, 3]) + _participants(2, [1, 2])
        result = calculate_total_owed_share_by_member(
            three_members, expenses, participants
        )
        # expense 1: each owes 1000. expense 2: Alex+Blair each owe 750.
        assert result == {1: 1750, 2: 1750, 3: 1000}


class TestCalculateNetBalanceByMember:
    def test_payer_who_covers_full_dinner_for_three(self, three_members):
        expenses = [_expense(1, 3000, paid_by=1)]
        participants = _participants(1, [1, 2, 3])
        result = calculate_net_balance_by_member(
            three_members, expenses, participants
        )
        # Alex paid 3000, owes 1000 → +2000. Others paid 0, owe 1000 → -1000.
        assert result == {1: 2000, 2: -1000, 3: -1000}

    def test_balances_sum_to_zero(self, three_members):
        expenses = [
            _expense(1, 1234, paid_by=1),
            _expense(2, 5678, paid_by=2),
            _expense(3, 999, paid_by=3),
        ]
        participants = (
            _participants(1, [1, 2, 3])
            + _participants(2, [1, 2])
            + _participants(3, [2, 3])
        )
        result = calculate_net_balance_by_member(
            three_members, expenses, participants
        )
        # Net balances across all members must always sum to zero (conservation)
        assert sum(result.values()) == 0

    def test_no_expenses_yields_zero_balances(self, three_members):
        result = calculate_net_balance_by_member(three_members, [], [])
        assert result == {1: 0, 2: 0, 3: 0}


class TestSimplifySettlements:
    def test_single_debtor_single_creditor(self):
        settlements = simplify_settlements({1: 1000, 2: -1000})
        assert settlements == [
            {"from_member_id": 2, "to_member_id": 1, "amount_cents": 1000}
        ]

    def test_one_creditor_two_debtors(self):
        settlements = simplify_settlements({1: 2000, 2: -1000, 3: -1000})
        assert {"from_member_id": 2, "to_member_id": 1, "amount_cents": 1000} in settlements
        assert {"from_member_id": 3, "to_member_id": 1, "amount_cents": 1000} in settlements
        assert len(settlements) == 2

    def test_all_settled_returns_empty(self):
        assert simplify_settlements({1: 0, 2: 0, 3: 0}) == []

    def test_transferred_amounts_balance_creditors_and_debtors(self):
        balances = {1: 1500, 2: -500, 3: -1000, 4: 0}
        settlements = simplify_settlements(balances)
        total_transferred = sum(s["amount_cents"] for s in settlements)
        total_owed = sum(-b for b in balances.values() if b < 0)
        assert total_transferred == total_owed

    def test_settlements_never_reference_zero_balance_member(self):
        balances = {1: 1000, 2: -1000, 3: 0}
        settlements = simplify_settlements(balances)
        referenced = {s["from_member_id"] for s in settlements} | {
            s["to_member_id"] for s in settlements
        }
        assert 3 not in referenced
