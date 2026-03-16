from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def parse_money_to_cents(value):
    """
    Convert a user-entered money string like '12.50' into integer cents.
    """
    cleaned_value = safe_strip(value).replace(",", "").replace("$", "")

    if not cleaned_value:
        raise ValueError("Amount is required.")

    try:
        amount = Decimal(cleaned_value)
    except InvalidOperation as exc:
        raise ValueError("Enter a valid amount.") from exc

    if amount < 0:
        raise ValueError("Amount cannot be negative.")

    cents = (amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(cents)


def format_cents(amount_cents, currency="USD"):
    """
    Format integer cents as a readable currency string.
    """
    if amount_cents is None:
        amount_cents = 0

    sign = "-" if amount_cents < 0 else ""
    absolute_cents = abs(amount_cents)
    dollars = absolute_cents // 100
    cents = absolute_cents % 100
    return f"{sign}{currency} {dollars:,}.{cents:02d}"


def safe_strip(value):
    """Strip text input and return an empty string for missing values."""
    if value is None:
        return ""
    return value.strip()
