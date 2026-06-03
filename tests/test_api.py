import pytest


@pytest.fixture
def sample_trip(client):
    response = client.post(
        "/api/trips",
        json={
            "name": "Weekend trip",
            "currency": "USD",
            "members": [
                {"name": "Alex", "is_self": True},
                {"name": "Blair", "is_self": False},
                {"name": "Casey", "is_self": False},
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def _add_expense(client, trip_id, **overrides):
    payload = {
        "description": "Dinner",
        "amount_cents": 3000,
        "expense_date": "2026-05-30",
        "paid_by_member_id": overrides.get("paid_by_member_id"),
        "participant_ids": overrides.get("participant_ids"),
        "notes": None,
    }
    payload.update({k: v for k, v in overrides.items() if k in payload})
    response = client.post(f"/api/trips/{trip_id}/expenses", json=payload)
    return response


# ---------- Health ----------


class TestHealth:
    def test_healthz_ok(self, client):
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"ok": True, "service": "bill-buddy-api"}


# ---------- Trips ----------


class TestTrips:
    def test_list_empty(self, client):
        r = client.get("/api/trips")
        assert r.status_code == 200
        assert r.json() == []

    def test_create_trip_returns_201_with_members(self, client):
        r = client.post(
            "/api/trips",
            json={
                "name": "Test trip",
                "currency": "usd",
                "members": [
                    {"name": "Alex", "is_self": True},
                    {"name": "Blair"},
                ],
            },
        )
        assert r.status_code == 201
        data = r.json()
        assert data["name"] == "Test trip"
        assert data["currency"] == "USD"  # uppercased by validator
        assert len(data["members"]) == 2
        assert any(m["is_self"] == 1 for m in data["members"])

    def test_create_trip_rejects_zero_self_members(self, client):
        r = client.post(
            "/api/trips",
            json={
                "name": "Test",
                "currency": "USD",
                "members": [{"name": "Alex"}, {"name": "Blair"}],
            },
        )
        assert r.status_code == 422

    def test_create_trip_rejects_multiple_self_members(self, client):
        r = client.post(
            "/api/trips",
            json={
                "name": "Test",
                "currency": "USD",
                "members": [
                    {"name": "Alex", "is_self": True},
                    {"name": "Blair", "is_self": True},
                ],
            },
        )
        assert r.status_code == 422

    def test_get_trip_returns_detail(self, client, sample_trip):
        r = client.get(f"/api/trips/{sample_trip['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == sample_trip["id"]
        assert len(r.json()["members"]) == 3

    def test_get_trip_404(self, client):
        assert client.get("/api/trips/99999").status_code == 404

    def test_delete_trip_returns_204(self, client, sample_trip):
        r = client.delete(f"/api/trips/{sample_trip['id']}")
        assert r.status_code == 204
        assert client.get(f"/api/trips/{sample_trip['id']}").status_code == 404


# ---------- Members ----------


class TestMembers:
    def test_add_member_after_creation(self, client, sample_trip):
        r = client.post(
            f"/api/trips/{sample_trip['id']}/members",
            json={"name": "Dana"},
        )
        assert r.status_code == 201
        assert r.json()["name"] == "Dana"

    def test_add_second_self_member_409s(self, client, sample_trip):
        r = client.post(
            f"/api/trips/{sample_trip['id']}/members",
            json={"name": "Dana", "is_self": True},
        )
        assert r.status_code == 409

    def test_remove_member(self, client, sample_trip):
        member_id = sample_trip["members"][-1]["id"]  # Casey, no expenses
        r = client.delete(
            f"/api/trips/{sample_trip['id']}/members/{member_id}"
        )
        assert r.status_code == 204

    def test_remove_member_who_paid_expense_409s(self, client, sample_trip):
        payer_id = sample_trip["members"][0]["id"]
        _add_expense(
            client,
            sample_trip["id"],
            paid_by_member_id=payer_id,
            participant_ids=[payer_id],
        )
        r = client.delete(
            f"/api/trips/{sample_trip['id']}/members/{payer_id}"
        )
        assert r.status_code == 409


# ---------- Expenses ----------


class TestExpenses:
    def test_create_and_get_expense(self, client, sample_trip):
        member_ids = [m["id"] for m in sample_trip["members"]]
        r = _add_expense(
            client,
            sample_trip["id"],
            paid_by_member_id=member_ids[0],
            participant_ids=member_ids,
        )
        assert r.status_code == 201
        data = r.json()
        assert data["amount_cents"] == 3000
        assert data["payer_name"] == sample_trip["members"][0]["name"]
        assert len(data["participants"]) == 3

        r2 = client.get(f"/api/expenses/{data['id']}")
        assert r2.status_code == 200
        assert r2.json()["id"] == data["id"]

    def test_create_expense_invalid_payer(self, client, sample_trip):
        member_ids = [m["id"] for m in sample_trip["members"]]
        r = _add_expense(
            client,
            sample_trip["id"],
            paid_by_member_id=99999,
            participant_ids=member_ids,
        )
        assert r.status_code == 422

    def test_create_expense_invalid_participant(self, client, sample_trip):
        payer_id = sample_trip["members"][0]["id"]
        r = _add_expense(
            client,
            sample_trip["id"],
            paid_by_member_id=payer_id,
            participant_ids=[99999],
        )
        assert r.status_code == 422

    def test_list_expenses_filter_by_payer(self, client, sample_trip):
        a_id, b_id, c_id = [m["id"] for m in sample_trip["members"]]
        _add_expense(
            client, sample_trip["id"], paid_by_member_id=a_id, participant_ids=[a_id, b_id, c_id]
        )
        _add_expense(
            client, sample_trip["id"], paid_by_member_id=b_id, participant_ids=[a_id, b_id, c_id]
        )
        r = client.get(
            f"/api/trips/{sample_trip['id']}/expenses?payer_id={a_id}"
        )
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["paid_by_member_id"] == a_id

    def test_list_expenses_date_filter(self, client, sample_trip):
        a_id, b_id, c_id = [m["id"] for m in sample_trip["members"]]
        _add_expense(
            client, sample_trip["id"],
            paid_by_member_id=a_id, participant_ids=[a_id, b_id, c_id],
            expense_date="2026-05-10",
        )
        _add_expense(
            client, sample_trip["id"],
            paid_by_member_id=a_id, participant_ids=[a_id, b_id, c_id],
            expense_date="2026-06-15",
        )
        r = client.get(
            f"/api/trips/{sample_trip['id']}/expenses?from=2026-06-01"
        )
        assert r.status_code == 200
        assert len(r.json()) == 1
        assert r.json()[0]["expense_date"] == "2026-06-15"

    def test_patch_expense(self, client, sample_trip):
        a_id, b_id, _ = [m["id"] for m in sample_trip["members"]]
        created = _add_expense(
            client, sample_trip["id"], paid_by_member_id=a_id, participant_ids=[a_id, b_id]
        ).json()
        r = client.patch(
            f"/api/expenses/{created['id']}",
            json={"description": "Updated", "amount_cents": 5000},
        )
        assert r.status_code == 200
        assert r.json()["description"] == "Updated"
        assert r.json()["amount_cents"] == 5000

    def test_delete_expense(self, client, sample_trip):
        a_id = sample_trip["members"][0]["id"]
        created = _add_expense(
            client, sample_trip["id"], paid_by_member_id=a_id, participant_ids=[a_id]
        ).json()
        r = client.delete(f"/api/expenses/{created['id']}")
        assert r.status_code == 204
        assert client.get(f"/api/expenses/{created['id']}").status_code == 404


# ---------- Balances / settlements / summary ----------


class TestBalances:
    def test_dinner_for_three_balances(self, client, sample_trip):
        a_id, b_id, c_id = [m["id"] for m in sample_trip["members"]]
        _add_expense(
            client, sample_trip["id"],
            paid_by_member_id=a_id, participant_ids=[a_id, b_id, c_id],
            amount_cents=3000,
        )
        r = client.get(f"/api/trips/{sample_trip['id']}/balances")
        assert r.status_code == 200
        by_id = {b["member_id"]: b for b in r.json()}
        assert by_id[a_id]["net_balance"] == 2000
        assert by_id[b_id]["net_balance"] == -1000
        assert by_id[c_id]["net_balance"] == -1000

    def test_settlements_simplified(self, client, sample_trip):
        a_id, b_id, c_id = [m["id"] for m in sample_trip["members"]]
        _add_expense(
            client, sample_trip["id"],
            paid_by_member_id=a_id, participant_ids=[a_id, b_id, c_id],
            amount_cents=3000,
        )
        r = client.get(f"/api/trips/{sample_trip['id']}/settlements")
        assert r.status_code == 200
        settlements = r.json()
        assert len(settlements) == 2
        assert all(s["to_member_id"] == a_id for s in settlements)
        assert sum(s["amount_cents"] for s in settlements) == 2000

    def test_summary_metrics(self, client, sample_trip):
        a_id, b_id, c_id = [m["id"] for m in sample_trip["members"]]
        _add_expense(
            client, sample_trip["id"],
            paid_by_member_id=a_id, participant_ids=[a_id, b_id, c_id],
            amount_cents=3000,
        )
        r = client.get(f"/api/trips/{sample_trip['id']}/summary")
        assert r.status_code == 200
        data = r.json()
        assert data["total_trip_spending"] == 3000
        assert data["total_expenses"] == 1
        assert data["total_members"] == 3
        assert data["highest_spender"]["amount_cents"] == 3000


# ---------- CSV export ----------


class TestExport:
    def test_csv_export(self, client, sample_trip):
        a_id, b_id, _ = [m["id"] for m in sample_trip["members"]]
        _add_expense(
            client, sample_trip["id"],
            paid_by_member_id=a_id, participant_ids=[a_id, b_id],
            amount_cents=1250,
            expense_date="2026-05-15",
        )
        r = client.get(f"/api/trips/{sample_trip['id']}/expenses.csv")
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("text/csv")
        assert "attachment" in r.headers["content-disposition"]
        body = r.text
        assert "Date,Description,Amount,Paid By,Participants,Notes" in body
        assert "USD 12.50" in body
