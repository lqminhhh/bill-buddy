from flask import Flask, abort, redirect, render_template, request, url_for

from utils.db import fetch_all, fetch_one, get_db_connection
from utils.helpers import safe_strip


DEFAULT_CURRENCY = "USD"
MEMBER_FIELD_COUNT = 5


def create_app():
    app = Flask(__name__)

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
        errors = []
        form_data = {
            "name": "",
            "currency": DEFAULT_CURRENCY,
            "member_names": ["", "", ""],
            "self_member_index": "",
        }

        if request.method == "POST":
            form_data = {
                "name": safe_strip(request.form.get("name")),
                "currency": safe_strip(request.form.get("currency")).upper()
                or DEFAULT_CURRENCY,
                "member_names": [
                    safe_strip(request.form.get(f"member_name_{index}"))
                    for index in range(MEMBER_FIELD_COUNT)
                ],
                "self_member_index": safe_strip(request.form.get("self_member_index")),
            }

            member_names = [name for name in form_data["member_names"] if name]

            if not form_data["name"]:
                errors.append("Trip name is required.")

            if not form_data["currency"]:
                errors.append("Currency is required.")
            elif len(form_data["currency"]) != 3:
                errors.append("Currency should be a 3-letter code like USD.")

            if not member_names:
                errors.append("Add at least one member.")

            if form_data["self_member_index"] == "":
                errors.append("Choose exactly one member as yourself.")
            else:
                try:
                    self_member_index = int(form_data["self_member_index"])
                except ValueError:
                    errors.append("Choose a valid member as yourself.")
                    self_member_index = None

                if self_member_index is not None:
                    if self_member_index < 0 or self_member_index >= MEMBER_FIELD_COUNT:
                        errors.append("Choose a valid member as yourself.")
                    elif not form_data["member_names"][self_member_index]:
                        errors.append("The selected 'you' member must have a name.")

            if not errors:
                with get_db_connection() as connection:
                    trip_cursor = connection.execute(
                        """
                        INSERT INTO trips (name, currency)
                        VALUES (?, ?)
                        """,
                        (form_data["name"], form_data["currency"]),
                    )
                    trip_id = trip_cursor.lastrowid

                    for index, member_name in enumerate(form_data["member_names"]):
                        if not member_name:
                            continue

                        is_self = 1 if str(index) == form_data["self_member_index"] else 0
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
            errors=errors,
            form_data=form_data,
            member_field_count=MEMBER_FIELD_COUNT,
        )

    @app.route("/trip/<int:trip_id>")
    def trip_detail(trip_id):
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

        members = fetch_all(
            """
            SELECT id, name, is_self
            FROM members
            WHERE trip_id = ?
            ORDER BY id ASC
            """,
            (trip_id,),
        )

        return render_template("trip_detail.html", trip=trip, members=members)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
