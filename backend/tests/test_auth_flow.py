"""Integration tests — Authentication flow."""


def test_login_success(client):
    resp = client.post(
        "/api/auth/login",
        json={"clearance_id": "OP-7729", "passphrase": "password"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["operator"]["id"] == "OP-7729"
    assert data["operator"]["role"] == "command"
    
    # Check that a refresh_token cookie was set
    cookies = resp.cookies
    assert "refresh_token" in cookies


def test_login_invalid_passphrase_rejected(client):
    resp = client.post(
        "/api/auth/login",
        json={"clearance_id": "OP-7729", "passphrase": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_me_endpoint(client, headers):
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    me = resp.json()
    assert me["id"] == "OP-7729"
    assert me["clearance"] == "TS/SCI"


def test_me_without_token_rejected(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_refresh_token(client):
    # 1. Login to get cookie
    resp1 = client.post(
        "/api/auth/login",
        json={"clearance_id": "OP-7729", "passphrase": "password"},
    )
    assert resp1.status_code == 200
    refresh_token = resp1.cookies.get("refresh_token")
    
    # 2. Call refresh
    resp2 = client.post(
        "/api/auth/refresh",
        cookies={"refresh_token": refresh_token}
    )
    assert resp2.status_code == 200
    assert "token" in resp2.json()


def test_logout_revokes_token(client, headers):
    resp = client.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200
    
    # Verify the token is now blacklisted
    resp2 = client.get("/api/auth/me", headers=headers)
    assert resp2.status_code == 401
    assert resp2.json()["detail"] == "Token has been revoked."
