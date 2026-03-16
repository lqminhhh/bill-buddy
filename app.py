from datetime import date

from flask import Flask, abort, redirect, render_template, request, url_for

from utils.calculations import (
    calculate_net_balance_by_member,
    calculate_total_owed_share_by_member,
    calculate_total_paid_by_member,
    simplify_settlements,
)
from utils.db import fetch_all, fetch_one, get_db_connection
from utils.helpers import format_cents, parse_money_to_cents, safe_strip


DEFAULT_CURRENCY = "USD"


def create_app():
    app = Flask(__name__)

    @app.context_processor
    def inject_template_helpers():
        return {"format_cents": format_cents}

    @app.route("/")
    def index():
        trips = fetch_all(
            """
            SELECT id, name, currency, created_at
            FROM trips
            ORDER BY created_at DESC, id DESC
            """
        )
        return render_template("index.html", trips=trips)

    @app.route("/trip/new", methods=["GET", "POST"])
    def create_trip():
        step = "setup"
        errors = []
        form_data = {
            "name": "",
            "currency": DEFAULT_CURRENCY,
            "participant_count": "1",
            "member_names": [],
            "self_member_index": "",
        }

        if request.method == "POST":
            step = request.form.get("step", "setup")

            if step == "setup":
                form_data = _build_trip_setup_form_data(request.form)
                errors, cleaned_data = _validate_trip_setup_form(form_data)

                if not errors:
                    step = "members"
                    form_data["participant_count"] = str(cleaned_data["participant_count"])
                    form_data["member_names"] = [""] * cleaned_data["participant_count"]

            elif step == "members":
                form_data = _build_trip_members_form_data(request.form)
                errors, cleaned_data = _validate_trip_members_form(form_data)

                if not errors:
                    with get_db_connection() as connection:
                        trip_cursor = connection.execute(
                            """
                            INSERT INTO trips (name, currency)
                            VALUES (?, ?)
                            """,
                            (cleaned_data["name"], cleaned_data["currency"]),
                        )
                        trip_id = trip_cursor.lastrowid

                        for index, member_name in enumerate(cleaned_data["member_names"]):
                            is_self = 1 if index == cleaned_data["self_member_index"] else 0
                            connection.execute(
                                """
                                INSERT INTO members (trip_id, name, is_self)
                                VALUES (?, ?, ?)
                                """,
                                (trip_id, member_name, is_self),
                            )

                    return redirect(url_for("trip_detail", trip_id=trip_id))

        return render_template(
            "create_trip.html",
            step=step,
            errors=errors,
            form_data=form_data,
        )

    @app.route("/trip/<int:trip_id>")
    def trip_detail(trip_id):
        trip = _get_trip_or_404(trip_id)
        members = _get_trip_members(trip_id)
        expenses = _get_trip_expenses(trip_id)
        expense_participants = _get_trip_expense_participants(trip_id)
        balance_summary = _build_member_balance_summary(
            members, expenses, expense_participants
        )
        settlement_summary = _build_settlement_summary(
            members, expenses, expense_participants, trip["currency"]
        )

        return render_template(
            "trip_detail.html",
            trip=trip,
            members=members,
            expenses=expenses,
            balance_summary=balance_summary,
            settlement_summary=settlement_summary,
        )

    @app.route("/trip/<int:trip_id>/delete", methods=["GET", "POST"])
    def delete_trip(trip_id):
        trip = _get_trip_or_404(trip_id)

        if request.method == "POST":
            with get_db_connection() as connection:
                connection.execute(
                    """
                    DELETE FROM trips
                    WHERE id = ?
                    """,
                    (trip_id,),
                )

            return redirect(url_for("index"))

        return render_template("delete_trip.html", trip=trip)

    @app.route("/trip/<int:trip_id>/expense/new", methods=["GET", "POST"])
    def add_expense(trip_id):
        trip = _get_trip_or_404(trip_id)
        members = _get_trip_members(trip_id)
        errors = []
        form_data = {
            "description": "",
            "amount": "",
            "expense_date": date.today().isoformat(),
            "paid_by_member_id": "",
            "participant_ids": [],
            "notes": "",
        }

        if request.method == "POST":
            form_data = _build_expense_form_data(request.form)
            errors, cleaned_data = _validate_expense_form(form_data, members)

            if not errors:
                with get_db_connection() as connection:
                    expense_id = _insert_expense(connection, trip_id, cleaned_data)
                    _replace_expense_participants(
                        connection, expense_id, cleaned_data["participant_ids"]
                    )

                return redirect(url_for("trip_detail", trip_id=trip_id))

        return render_template(
            "add_expense.html",
            trip=trip,
            members=members,
            errors=errors,
            form_data=form_data,
        )

    @app.route("/trip/<int:trip_id>/expense/<int:expense_id>/edit", methods=["GET", "POST"])
    def edit_expense(trip_id, expense_id):
        trip = _get_trip_or_404(trip_id)
        members = _get_trip_members(trip_id)
        expense = _get_trip_expense_or_404(trip_id, expense_id)

        if request.method == "POST":
            form_data = _build_expense_form_data(request.form)
            errors, cleaned_data = _validate_expense_form(form_data, members)

            if not errors:
                with get_db_connection() as connection:
                    connection.execute(
                        """
                        UPDATE expenses
                        SET description = ?, amount_cents = ?, expense_date = ?,
                            paid_by_member_id = ?, notes = ?
                        WHERE id = ? AND trip_id = ?
                        """,
                        (
                            cleaned_data["description"],
                            cleaned_data["amount_cents"],
                            cleaned_data["expense_date"],
                            cleaned_data["paid_by_member_id"],
                            cleaned_data["notes"],
                            expense_id,
                            trip_id,
                        ),
                    )
                    _replace_expense_participants(
                        connection, expense_id, cleaned_data["participant_ids"]
                    )

                return redirect(url_for("trip_detail", trip_id=trip_id))
        else:
            form_data = _build_expense_form_data_from_expense(expense)
            errors = []

        return render_template(
            "edit_expense.html",
            trip=trip,
            expense=expense,
            members=members,
            errors=errors,
            form_data=form_data,
        )

    @app.route("/trip/<int:trip_id>/expense/<int:expense_id>/delete", methods=["POST"])
    def delete_expense(trip_id, expense_id):
        _get_trip_or_404(trip_id)
        _get_trip_expense_or_404(trip_id, expense_id)

        with get_db_connection() as connection:
            connection.execute(
                """
                DELETE FROM expenses
                WHERE id = ? AND trip_id = ?
                """,
                (expense_id, trip_id),
            )

        return redirect(url_for("trip_detail", trip_id=trip_id))

    return app


def _get_trip_or_404(trip_id):
    trip = fetch_one(
        """
        SELECT id, name, currency, created_at
        FROM trips
        WHERE id = ?
        """,
        (trip_id,),
    )

    if trip is None:
        abort(404)

    return trip


def _get_trip_members(trip_id):
    rows = fetch_all(
        """
        SELECT id, name, is_self
        FROM members
        WHERE trip_id = ?
        ORDER BY id ASC
        """,
        (trip_id,),
    )
    return [dict(row) for row in rows]


def _get_trip_expenses(trip_id):
    expense_rows = fetch_all(
        """
        SELECT
            expenses.id,
            expenses.description,
            expenses.amount_cents,
            expenses.expense_date,
            expenses.notes,
            expenses.paid_by_member_id,
            payer.name AS payer_name
        FROM expenses
        JOIN members AS payer ON payer.id = expenses.paid_by_member_id
        WHERE expenses.trip_id = ?
        ORDER BY expenses.expense_date DESC, expenses.id DESC
        """,
        (trip_id,),
    )

    participant_rows = fetch_all(
        """
        SELECT
            expense_participants.expense_id,
            members.id AS member_id,
            members.name
        FROM expense_participants
        JOIN members ON members.id = expense_participants.member_id
        JOIN expenses ON expenses.id = expense_participants.expense_id
        WHERE expenses.trip_id = ?
        ORDER BY expense_participants.expense_id ASC, members.name ASC
        """,
        (trip_id,),
    )

    participants_by_expense = {}
    for row in participant_rows:
        participants_by_expense.setdefault(row["expense_id"], []).append(
            {"id": row["member_id"], "name": row["name"]}
        )

    expenses = []
    for row in expense_rows:
        expense = dict(row)
        expense["participants"] = participants_by_expense.get(row["id"], [])
        expenses.append(expense)

    return expenses


def _get_trip_expense_participants(trip_id):
    rows = fetch_all(
        """
        SELECT
            expense_participants.expense_id,
            expense_participants.member_id
        FROM expense_participants
        JOIN expenses ON expenses.id = expense_participants.expense_id
        WHERE expenses.trip_id = ?
        ORDER BY expense_participants.expense_id ASC, expense_participants.member_id ASC
        """,
        (trip_id,),
    )
    return [dict(row) for row in rows]


def _get_trip_expense_or_404(trip_id, expense_id):
    row = fetch_one(
        """
        SELECT
            id,
            trip_id,
            description,
            amount_cents,
            expense_date,
            paid_by_member_id,
            notes
        FROM expenses
        WHERE id = ? AND trip_id = ?
        """,
        (expense_id, trip_id),
    )

    if row is None:
        abort(404)

    expense = dict(row)
    participant_rows = fetch_all(
        """
        SELECT member_id
        FROM expense_participants
        WHERE expense_id = ?
        ORDER BY member_id ASC
        """,
        (expense_id,),
    )
    expense["participant_ids"] = [str(row["member_id"]) for row in participant_rows]
    return expense


def _build_member_balance_summary(members, expenses, expense_participants):
    paid_by_member = calculate_total_paid_by_member(members, expenses)
    share_by_member = calculate_total_owed_share_by_member(
        members, expenses, expense_participants
    )
    net_by_member = calculate_net_balance_by_member(
        members, expenses, expense_participants
    )

    summary = []
    for member in members:
        net_balance = net_by_member[member["id"]]
        summary.append(
            {
                "id": member["id"],
                "name": member["name"],
                "is_self": member["is_self"],
                "total_paid": paid_by_member[member["id"]],
                "total_share": share_by_member[member["id"]],
                "net_balance": net_balance,
                "balance_class": _get_balance_class(net_balance),
            }
        )

    return summary


def _build_settlement_summary(members, expenses, expense_participants, currency):
    net_by_member = calculate_net_balance_by_member(
        members, expenses, expense_participants
    )
    settlements = simplify_settlements(net_by_member)
    member_names = {member["id"]: member["name"] for member in members}

    lines = []
    for settlement in settlements:
        from_name = member_names[settlement["from_member_id"]]
        to_name = member_names[settlement["to_member_id"]]
        formatted_amount = format_cents(settlement["amount_cents"], currency)
        lines.append(
            {
                "from_member_name": from_name,
                "to_member_name": to_name,
                "amount_cents": settlement["amount_cents"],
                "formatted_amount": formatted_amount,
                "text": f"{from_name} pays {to_name} {formatted_amount}",
            }
        )

    return lines


def _build_trip_setup_form_data(form):
    return {
        "name": safe_strip(form.get("name")),
        "currency": safe_strip(form.get("currency")).upper() or DEFAULT_CURRENCY,
        "participant_count": safe_strip(form.get("participant_count")),
        "member_names": [],
        "self_member_index": "",
    }


def _build_trip_members_form_data(form):
    participant_count = safe_strip(form.get("participant_count"))

    try:
        count_value = int(participant_count)
    except ValueError:
        count_value = 0

    return {
        "name": safe_strip(form.get("name")),
        "currency": safe_strip(form.get("currency")).upper() or DEFAULT_CURRENCY,
        "participant_count": participant_count,
        "member_names": [
            safe_strip(form.get(f"member_name_{index}")) for index in range(max(count_value, 0))
        ],
        "self_member_index": safe_strip(form.get("self_member_index")),
    }


def _validate_trip_setup_form(form_data):
    errors = []

    if not form_data["name"]:
        errors.append("Trip name is required.")

    if not form_data["currency"]:
        errors.append("Currency is required.")
    elif len(form_data["currency"]) != 3:
        errors.append("Currency should be a 3-letter code like USD.")

    try:
        participant_count = int(form_data["participant_count"])
    except ValueError:
        participant_count = None
        errors.append("Participant count must be a whole number.")

    if participant_count is not None and participant_count < 1:
        errors.append("Participant count must be at least 1.")

    cleaned_data = {
        "name": form_data["name"],
        "currency": form_data["currency"],
        "participant_count": participant_count,
    }

    return errors, cleaned_data


def _validate_trip_members_form(form_data):
    errors, cleaned_setup = _validate_trip_setup_form(form_data)
    participant_count = cleaned_setup["participant_count"]

    if participant_count is None:
        participant_count = 0

    if len(form_data["member_names"]) != participant_count:
        errors.append("Member list does not match participant count.")

    if any(not member_name for member_name in form_data["member_names"]):
        errors.append("All member names must be filled.")

    try:
        self_member_index = int(form_data["self_member_index"])
    except ValueError:
        self_member_index = None
        errors.append("Choose exactly one member as yourself.")

    if self_member_index is not None:
        if self_member_index < 0 or self_member_index >= participant_count:
            errors.append("Choose a valid member as yourself.")

    cleaned_data = {
        "name": cleaned_setup["name"],
        "currency": cleaned_setup["currency"],
        "participant_count": participant_count,
        "member_names": form_data["member_names"],
        "self_member_index": self_member_index,
    }

    return errors, cleaned_data


def _build_expense_form_data(form):
    return {
        "description": safe_strip(form.get("description")),
        "amount": safe_strip(form.get("amount")),
        "expense_date": safe_strip(form.get("expense_date")),
        "paid_by_member_id": safe_strip(form.get("paid_by_member_id")),
        "participant_ids": form.getlist("participant_ids"),
        "notes": safe_strip(form.get("notes")),
    }


def _build_expense_form_data_from_expense(expense):
    return {
        "description": expense["description"],
        "amount": f"{expense['amount_cents'] / 100:.2f}",
        "expense_date": expense["expense_date"],
        "paid_by_member_id": str(expense["paid_by_member_id"]),
        "participant_ids": expense["participant_ids"],
        "notes": expense["notes"] or "",
    }


def _validate_expense_form(form_data, members):
    member_ids = {member["id"] for member in members}
    errors = []

    if not form_data["description"]:
        errors.append("Description is required.")

    try:
        amount_cents = parse_money_to_cents(form_data["amount"])
    except ValueError as exc:
        errors.append(str(exc))
        amount_cents = None

    if not form_data["expense_date"]:
        errors.append("Date is required.")

    try:
        paid_by_member_id = int(form_data["paid_by_member_id"])
    except ValueError:
        errors.append("Choose who paid for this expense.")
        paid_by_member_id = None

    if paid_by_member_id is not None and paid_by_member_id not in member_ids:
        errors.append("Choose a valid trip member as the payer.")

    participant_ids = []
    if not form_data["participant_ids"]:
        errors.append("Select at least one participant.")
    else:
        try:
            participant_ids = [int(member_id) for member_id in form_data["participant_ids"]]
        except ValueError:
            errors.append("Participants must be valid trip members.")

    if participant_ids:
        invalid_participants = [
            member_id for member_id in participant_ids if member_id not in member_ids
        ]
        if invalid_participants:
            errors.append("Participants must be valid trip members.")

    cleaned_data = {
        "description": form_data["description"],
        "amount_cents": amount_cents,
        "expense_date": form_data["expense_date"],
        "paid_by_member_id": paid_by_member_id,
        "participant_ids": participant_ids,
        "notes": form_data["notes"] or None,
    }

    return errors, cleaned_data


def _insert_expense(connection, trip_id, cleaned_data):
    cursor = connection.execute(
        """
        INSERT INTO expenses (
            trip_id,
            description,
            amount_cents,
            expense_date,
            paid_by_member_id,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            trip_id,
            cleaned_data["description"],
            cleaned_data["amount_cents"],
            cleaned_data["expense_date"],
            cleaned_data["paid_by_member_id"],
            cleaned_data["notes"],
        ),
    )
    return cursor.lastrowid


def _replace_expense_participants(connection, expense_id, participant_ids):
    connection.execute(
        "DELETE FROM expense_participants WHERE expense_id = ?",
        (expense_id,),
    )

    for participant_id in participant_ids:
        connection.execute(
            """
            INSERT INTO expense_participants (expense_id, member_id)
            VALUES (?, ?)
            """,
            (expense_id, participant_id),
        )


def _get_balance_class(net_balance):
    if net_balance > 0:
        return "balance-positive"
    if net_balance < 0:
        return "balance-negative"
    return "balance-neutral"


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
