"""Auth flow tests — exercise the REAL bcrypt hash/verify path.

The rest of the suite bypasses auth via the get_current_user override, so
without these tests the password-hashing code (which broke on bcrypt 5.x) had
zero coverage. Each test uses a unique email because the SQLite test DB is
shared across the session.
"""


def test_register_returns_token(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "newauth@example.com",
        "name": "New Auth User",
        "password": "akshay123",
    })
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "newauth@example.com"
    assert data["user"]["name"] == "New Auth User"


def test_register_duplicate_email_conflicts(client):
    payload = {"email": "dupe@example.com", "name": "Dupe", "password": "secretpw1"}
    first = client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 200, first.text
    second = client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


def test_login_succeeds_with_correct_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "login@example.com",
        "name": "Login User",
        "password": "correct-horse",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "login@example.com",
        "password": "correct-horse",
    })
    assert res.status_code == 200, res.text
    assert res.json()["access_token"]


def test_login_fails_with_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "wrongpw@example.com",
        "name": "Wrong PW",
        "password": "right-password",
    })
    res = client.post("/api/v1/auth/login", json={
        "email": "wrongpw@example.com",
        "password": "not-the-password",
    })
    assert res.status_code == 401


def test_login_unknown_email_rejected(client):
    res = client.post("/api/v1/auth/login", json={
        "email": "nobody@example.com",
        "password": "whatever12",
    })
    assert res.status_code == 401
