import pytest


@pytest.fixture
def shared_trip(client):
    response = client.post(
        "/api/trips",
        json={
            "name": "Sharable trip",
            "currency": "USD",
            "members": [
                {"name": "Alice", "is_self": True},
                {"name": "Bob"},
            ],
        },
    )
    assert response.status_code == 201
    return response.json()


def test_trip_creation_returns_share_token(shared_trip):
    assert shared_trip["share_token"] is not None
    assert len(shared_trip["share_token"]) >= 16


def test_get_shared_trip_without_auth(unauth_client, client, shared_trip):
    token = shared_trip["share_token"]
    r = unauth_client.get(f"/api/share/{token}")
    assert r.status_code == 200
    assert r.json()["name"] == "Sharable trip"


def test_invalid_share_token_404s(unauth_client):
    r = unauth_client.get("/api/share/not-a-real-token")
    assert r.status_code == 404


def test_add_expense_via_share_link(unauth_client, client, shared_trip):
    token = shared_trip["share_token"]
    member_ids = [m["id"] for m in shared_trip["members"]]

    # Anonymous client (no auth header) can add an expense
    bare_client = unauth_client  # has no Authorization header
    r = bare_client.post(
        f"/api/share/{token}/expenses",
        json={
            "description": "Drinks",
            "amount_cents": 4000,
            "expense_date": "2026-06-03",
            "paid_by_member_id": member_ids[1],
            "participant_ids": member_ids,
        },
    )
    assert r.status_code == 201
    assert r.json()["payer_name"] == "Bob"

    # And it shows up for the owner
    r2 = client.get(f"/api/trips/{shared_trip['id']}/expenses")
    assert r2.status_code == 200
    assert len(r2.json()) == 1


def test_shared_balances_and_settlements(unauth_client, client, shared_trip):
    token = shared_trip["share_token"]
    member_ids = [m["id"] for m in shared_trip["members"]]
    unauth_client.post(
        f"/api/share/{token}/expenses",
        json={
            "description": "Dinner",
            "amount_cents": 5000,
            "expense_date": "2026-06-03",
            "paid_by_member_id": member_ids[0],
            "participant_ids": member_ids,
        },
    )

    balances = unauth_client.get(f"/api/share/{token}/balances").json()
    by_id = {b["member_id"]: b for b in balances}
    assert by_id[member_ids[0]]["net_balance"] == 2500
    assert by_id[member_ids[1]]["net_balance"] == -2500

    settlements = unauth_client.get(f"/api/share/{token}/settlements").json()
    assert len(settlements) == 1
    assert settlements[0]["amount_cents"] == 2500


def test_rotate_share_token_invalidates_old_link(client, shared_trip, unauth_client):
    old_token = shared_trip["share_token"]
    rotate = client.post(f"/api/trips/{shared_trip['id']}/rotate-share-token")
    assert rotate.status_code == 200
    new_token = rotate.json()["share_token"]
    assert new_token != old_token

    # Old token no longer works
    bare = unauth_client
    assert bare.get(f"/api/share/{old_token}").status_code == 404
    # New token works
    assert bare.get(f"/api/share/{new_token}").status_code == 200


def test_share_link_cannot_delete_trip(unauth_client, shared_trip):
    # Owner-only routes shouldn't have a public share-route counterpart
    token = shared_trip["share_token"]
    # There's no /api/share/{token}/delete or /api/share/{token} DELETE
    r = unauth_client.delete(f"/api/share/{token}")
    assert r.status_code == 405  # method not allowed
