def test_login_success_returns_token_and_user(client, seed):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "adminpass"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["username"] == "admin"
    assert body["user"]["role"] == "admin"


def test_login_wrong_password_is_401(client, seed):
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "nope"},
    )
    assert resp.status_code == 401


def test_protected_route_requires_token(client, seed):
    assert client.get("/api/v1/dashboard").status_code == 401


def test_health_is_public(client, seed):
    assert client.get("/api/v1/health").status_code == 200


def test_me_returns_current_user(client, seed, token):
    resp = client.get("/api/v1/auth/me", headers=token("reviewer"))
    assert resp.status_code == 200
    assert resp.json()["username"] == "rev"


def test_viewer_cannot_approve_reviews(client, seed, token):
    resp = client.post(
        f"/api/v1/reviews/{seed['review_id']}/approve",
        headers=token("viewer"),
    )
    assert resp.status_code == 403


def test_reviewer_cannot_run_batch_status(client, seed, token):
    assert (
        client.post("/api/v1/status/run-all", headers=token("reviewer")).status_code
        == 403
    )


def test_reviewer_cannot_list_users(client, seed, token):
    assert (
        client.get("/api/v1/auth/users", headers=token("reviewer")).status_code == 403
    )


def test_admin_can_manage_users(client, seed, token):
    headers = token("admin")

    created = client.post(
        "/api/v1/auth/users",
        headers=headers,
        json={
            "username": "newbie",
            "full_name": "New Bie",
            "role": "viewer",
            "password": "newbiepass",
        },
    )
    assert created.status_code == 201
    user_id = created.json()["id"]

    promoted = client.patch(
        f"/api/v1/auth/users/{user_id}",
        headers=headers,
        json={"role": "reviewer"},
    )
    assert promoted.status_code == 200
    assert promoted.json()["role"] == "reviewer"

    # new user can now log in
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "newbie", "password": "newbiepass"},
    )
    assert login.status_code == 200


def test_bootstrap_admin_cannot_be_demoted(client, seed, token):
    headers = token("admin")
    users = client.get("/api/v1/auth/users", headers=headers).json()
    admin_id = next(u["id"] for u in users if u["username"] == "admin")

    resp = client.patch(
        f"/api/v1/auth/users/{admin_id}",
        headers=headers,
        json={"role": "viewer"},
    )
    assert resp.status_code == 400


def test_disabled_user_token_is_rejected(client, seed, token):
    admin_headers = token("admin")
    users = client.get("/api/v1/auth/users", headers=admin_headers).json()
    viewer_id = next(u["id"] for u in users if u["username"] == "view")

    viewer_headers = token("viewer")
    assert client.get("/api/v1/dashboard", headers=viewer_headers).status_code == 200

    client.patch(
        f"/api/v1/auth/users/{viewer_id}",
        headers=admin_headers,
        json={"is_active": False},
    )
    assert client.get("/api/v1/dashboard", headers=viewer_headers).status_code == 403
