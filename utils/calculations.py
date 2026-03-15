from collections import defaultdict


def calculate_equal_share(amount_cents, participant_ids):
    """
    Split an expense equally across the selected participants.

    Any leftover cents are distributed one by one in participant order so the
    total always adds up exactly to amount_cents.
    """
    if amount_cents < 0:
        raise ValueError("amount_cents cannot be negative")

    if not participant_ids:
        raise ValueError("An expense must have at least one participant")

    base_share = amount_cents // len(participant_ids)
    remainder = amount_cents % len(participant_ids)
    shares = {}

    for index, member_id in enumerate(participant_ids):
        extra_cent = 1 if index < remainder else 0
        shares[member_id] = base_share + extra_cent

    return shares


def calculate_total_paid_by_member(members, expenses):
    """
    Return how much each member paid across all expenses.

    Output format:
    {
        member_id: amount_cents
    }
    """
    totals = {member["id"]: 0 for member in members}
    member_ids = set(totals)

    for expense in expenses:
        payer_id = expense["paid_by_member_id"]
        amount_cents = expense["amount_cents"]

        if amount_cents < 0:
            raise ValueError("Expense amounts cannot be negative")

        if payer_id not in member_ids:
            raise ValueError(f"Unknown payer member_id: {payer_id}")

        totals[payer_id] += amount_cents

    return totals


def calculate_total_owed_share_by_member(members, expenses, expense_participants):
    """
    Return how much each member owes based on the expenses they participated in.

    expense_participants should be a list of dictionaries like:
    {"expense_id": 1, "member_id": 2}
    """
    totals = {member["id"]: 0 for member in members}
    member_ids = set(totals)
    participants_by_expense = _group_participants_by_expense(expense_participants)
    expenses_by_id = {expense["id"]: expense for expense in expenses}

    for expense_id, expense in expenses_by_id.items():
        amount_cents = expense["amount_cents"]
        participant_ids = participants_by_expense.get(expense_id, [])

        if amount_cents < 0:
            raise ValueError("Expense amounts cannot be negative")

        shares = calculate_equal_share(amount_cents, participant_ids)

        for member_id, share_cents in shares.items():
            if member_id not in member_ids:
                raise ValueError(f"Unknown participant member_id: {member_id}")
            totals[member_id] += share_cents

    return totals


def calculate_net_balance_by_member(members, expenses, expense_participants):
    """
    Return each member's net balance.

    net balance = total paid - total share
    Positive means the member should receive money.
    Negative means the member owes money.
    """
    paid_totals = calculate_total_paid_by_member(members, expenses)
    owed_totals = calculate_total_owed_share_by_member(
        members, expenses, expense_participants
    )

    return {
        member_id: paid_totals[member_id] - owed_totals[member_id]
        for member_id in paid_totals
    }


def simplify_settlements(net_balances):
    """
    Convert net balances into a minimal-looking set of settlement transfers.

    Input format:
    {
        member_id: net_balance_cents
    }

    Output format:
    [
        {"from_member_id": 2, "to_member_id": 1, "amount_cents": 1250}
    ]
    """
    creditors = []
    debtors = []

    for member_id, balance_cents in sorted(net_balances.items()):
        if balance_cents > 0:
            creditors.append({"member_id": member_id, "amount_cents": balance_cents})
        elif balance_cents < 0:
            debtors.append({"member_id": member_id, "amount_cents": -balance_cents})

    settlements = []
    creditor_index = 0
    debtor_index = 0

    while debtor_index < len(debtors) and creditor_index < len(creditors):
        debtor = debtors[debtor_index]
        creditor = creditors[creditor_index]
        payment_cents = min(debtor["amount_cents"], creditor["amount_cents"])

        settlements.append(
            {
                "from_member_id": debtor["member_id"],
                "to_member_id": creditor["member_id"],
                "amount_cents": payment_cents,
            }
        )

        debtor["amount_cents"] -= payment_cents
        creditor["amount_cents"] -= payment_cents

        if debtor["amount_cents"] == 0:
            debtor_index += 1

        if creditor["amount_cents"] == 0:
            creditor_index += 1

    return settlements


def build_settlement_summary(members, expenses, expense_participants):
    """
    Return all calculation results together in one structure.

    This is a convenience wrapper for the individual pure functions.
    """
    paid_by_member = calculate_total_paid_by_member(members, expenses)
    owed_by_member = calculate_total_owed_share_by_member(
        members, expenses, expense_participants
    )
    net_balances = {
        member_id: paid_by_member[member_id] - owed_by_member[member_id]
        for member_id in paid_by_member
    }

    return {
        "paid_by_member": paid_by_member,
        "owed_by_member": owed_by_member,
        "net_balances": net_balances,
        "settlements": simplify_settlements(net_balances),
    }


def get_example_data():
    """
    Small example dataset for quick manual testing.

    Expected result:
    - Member 1 paid 3000 cents total
    - Each of the 3 members owes 1000 cents
    - Net balances become:
      {1: 2000, 2: -1000, 3: -1000}
    - Settlements become:
      [
          {"from_member_id": 2, "to_member_id": 1, "amount_cents": 1000},
          {"from_member_id": 3, "to_member_id": 1, "amount_cents": 1000}
      ]
    """
    members = [
        {"id": 1, "name": "Alex"},
        {"id": 2, "name": "Blair"},
        {"id": 3, "name": "Casey"},
    ]

    expenses = [
        {
            "id": 1,
            "trip_id": 1,
            "description": "Dinner",
            "amount_cents": 3000,
            "expense_date": "2026-03-15",
            "paid_by_member_id": 1,
            "notes": "",
        }
    ]

    expense_participants = [
        {"expense_id": 1, "member_id": 1},
        {"expense_id": 1, "member_id": 2},
        {"expense_id": 1, "member_id": 3},
    ]

    return members, expenses, expense_participants


def _group_participants_by_expense(expense_participants):
    """Group participant member ids by expense id."""
    grouped = defaultdict(list)

    for item in expense_participants:
        expense_id = item["expense_id"]
        member_id = item["member_id"]

        if member_id not in grouped[expense_id]:
            grouped[expense_id].append(member_id)

    return dict(grouped)
