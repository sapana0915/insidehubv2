import uuid


def _register_and_login(client):
    suffix = uuid.uuid4().hex[:8]
    email = f"writer_{suffix}@example.com"
    client.post(
        "/api/v1/users/register",
        json={"email": email, "username": f"writer_{suffix}", "password": "password123"},
    )
    token = client.post(
        "/api/v1/users/login", json={"email": email, "password": "password123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_post(client, headers, **overrides):
    body = {
        "title": "Sunrise over Hampi",
        "content": "Boulders, temples and a very early alarm.",
        "category": "travel-stories",
        "images": ["https://example.com/hampi.jpg"],
    }
    body.update(overrides)
    return client.post("/api/v1/posts", json=body, headers=headers)


def test_categories_are_public(client):
    response = client.get("/api/v1/posts/categories")
    assert response.status_code == 200
    slugs = [c["slug"] for c in response.json()]
    assert "travel-stories" in slugs


def test_create_post_embeds_author(client):
    headers = _register_and_login(client)
    response = _create_post(client, headers)
    assert response.status_code == 200
    body = response.json()
    assert body["author"]["username"].startswith("writer_")
    assert body["images"][0]["image_url"] == "https://example.com/hampi.jpg"


def test_invalid_category_rejected(client):
    headers = _register_and_login(client)
    response = _create_post(client, headers, category="not-a-category")
    assert response.status_code == 422


def test_feed_is_public_and_shows_all_authors(client):
    alice = _register_and_login(client)
    bob = _register_and_login(client)
    post_a = _create_post(client, alice, category="food").json()
    post_b = _create_post(client, bob, category="food").json()

    response = client.get("/api/v1/posts", params={"category": "food", "limit": 100})
    assert response.status_code == 200
    ids = {p["id"] for p in response.json()}
    assert {post_a["id"], post_b["id"]} <= ids

    detail = client.get(f"/api/v1/posts/{post_a['id']}")
    assert detail.status_code == 200


def test_only_owner_can_edit_or_delete(client):
    alice = _register_and_login(client)
    bob = _register_and_login(client)
    post = _create_post(client, alice).json()

    assert client.patch(f"/api/v1/posts/{post['id']}", json={"title": "x"}, headers=bob).status_code == 404
    assert client.delete(f"/api/v1/posts/{post['id']}", headers=bob).status_code == 404

    updated = client.patch(f"/api/v1/posts/{post['id']}", json={"title": "New"}, headers=alice)
    assert updated.status_code == 200
    assert updated.json()["title"] == "New"
    assert client.delete(f"/api/v1/posts/{post['id']}", headers=alice).status_code == 200


def test_create_requires_auth(client):
    response = client.post(
        "/api/v1/posts",
        json={"title": "t", "content": "c", "category": "food"},
    )
    assert response.status_code in (401, 403)


def test_me_and_public_profile(client):
    headers = _register_and_login(client)
    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    _create_post(client, headers)

    profile = client.get(f"/api/v1/users/{me.json()['id']}/profile")
    assert profile.status_code == 200
    body = profile.json()
    assert body["post_count"] == 1
    assert "email" not in body


def test_users_cannot_edit_other_users(client):
    alice = _register_and_login(client)
    bob = _register_and_login(client)
    bob_id = client.get("/api/v1/users/me", headers=bob).json()["id"]
    response = client.patch(f"/api/v1/users/{bob_id}", json={"full_name": "Hacked"}, headers=alice)
    assert response.status_code == 404


def test_image_upload(client, tmp_path, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "MEDIA_DIR", str(tmp_path))
    headers = _register_and_login(client)
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 16

    response = client.post(
        "/api/v1/posts/images",
        content=png,
        headers={**headers, "Content-Type": "image/png"},
    )
    assert response.status_code == 201
    assert response.json()["url"].endswith(".png")

    bad = client.post(
        "/api/v1/posts/images",
        content=b"hello",
        headers={**headers, "Content-Type": "text/plain"},
    )
    assert bad.status_code == 422
