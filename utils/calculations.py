def split_expense_evenly(total_amount, member_count):
    """Return the per-person share for an equal split."""
    if member_count <= 0:
        return 0
    return total_amount / member_count


def build_settlement_summary():
    """Placeholder for future settlement logic."""
    return []
