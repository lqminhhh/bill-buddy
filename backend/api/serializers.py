from api.models import Expense


def serialize_expense(expense: Expense) -> dict:
    return {
        "id": expense.id,
        "description": expense.description,
        "amount_cents": expense.amount_cents,
        "expense_date": expense.expense_date,
        "paid_by_member_id": expense.paid_by_member_id,
        "payer_name": expense.payer.name,
        "notes": expense.notes,
        "participants": [
            {"id": ep.member.id, "name": ep.member.name}
            for ep in sorted(
                expense.participants, key=lambda ep: ep.member.name.lower()
            )
        ],
    }
