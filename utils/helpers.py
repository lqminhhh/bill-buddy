def format_currency(amount):
    """Return a number as a dollar amount."""
    return f"${amount:,.2f}"


def safe_strip(value):
    """Strip text input and return an empty string for missing values."""
    if value is None:
        return ""
    return value.strip()
