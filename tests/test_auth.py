def test_signup_returns_token_and_user(unauth_client):
    r = unauth_client.post(
        "/api/auth/signup",
        json={"email": "Alice@Example.com", "password": "supersecret1"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["user"]["email"] == "alice@example.com"  # lowercased


def test_signup_rejects_short_password(unauth_client):
    r = unauth_client.post(
        "/api/auth/signup",
        json={"email": "alice@example.com", "password": "short"},
    )
    assert r.status_code == 422


def test_signup_rejects_duplicate_email(unauth_client):
    unauth_client.post(
        "/api/auth/signup",
        json={"email": "alice@example.com", "password": "supersecret1"},
    )
    r = unauth_client.post(
        "/api/auth/signup",
        json={"email": "alice@example.com", "password": "supersecret2"},
    )
    assert r.status_code == 409


def test_login_returns_token_for_valid_credentials(unauth_client):
    unauth_client.post(
        "/api/auth/signup",
        json={"email": "alice@example.com", "password": "supersecret1"},
    )
    r = unauth_client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "supersecret1"},
    )
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_login_rejects_wrong_password(unauth_client):
    unauth_client.post(
        "/api/auth/signup",
        json={"email": "alice@example.com", "password": "supersecret1"},
    )
    r = unauth_client.post(
        "/api/auth/login",
        json={"email": "alice@example.com", "password": "wrong-password"},
    )
    assert r.status_code == 401


def test_login_rejects_unknown_email(unauth_client):
    r = unauth_client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "whatever1"},
    )
    assert r.status_code == 401


def test_me_returns_current_user(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "user1@example.com"


def test_protected_route_requires_auth(unauth_client):
    r = unauth_client.get("/api/trips")
    assert r.status_code == 401


def test_invalid_token_rejected(unauth_client):
    r = unauth_client.get(
        "/api/trips", headers={"Authorization": "Bearer not-a-real-token"}
    )
    assert r.status_code == 401


def test_owner_isolation(unauth_client):
    # User 1 creates a trip
    r1 = unauth_client.post(
        "/api/auth/signup",
        json={"email": "a@example.com", "password": "supersecret1"},
    )
    token1 = r1.json()["access_token"]
    unauth_client.post(
        "/api/trips",
        headers={"Authorization": f"Bearer {token1}"},
        json={
            "name": "Private trip",
            "currency": "USD",
            "members": [{"name": "A", "is_self": True}],
        },
    )

    # User 2 should not see it
    r2 = unauth_client.post(
        "/api/auth/signup",
        json={"email": "b@example.com", "password": "supersecret1"},
    )
    token2 = r2.json()["access_token"]
    list_r = unauth_client.get(
        "/api/trips",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert list_r.status_code == 200
    assert list_r.json() == []
