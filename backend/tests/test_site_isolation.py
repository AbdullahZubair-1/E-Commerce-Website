"""
Site isolation is the single most important property of this platform --
almost every real bug found during development was some form of "does
Chemisto's data leak into Chemisto Food, or vice versa." These tests assert
that boundary directly, across every feature that's supposed to respect it.
"""
from tests.conftest import register_customer


async def test_product_created_on_one_site_invisible_on_the_other(client, chemisto_owner_token):
    create = await client.post(
        "/api/v1/products/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {chemisto_owner_token}"},
        data={"name": "Isolation Test Product", "price": "9.99", "stock_quantity": "5"},
    )
    assert create.status_code == 201, create.text

    chemisto_list = await client.get("/api/v1/products/", headers={"X-Site-Slug": "chemisto"})
    names = [p["name"] for p in chemisto_list.json()["data"]["items"]]
    assert "Isolation Test Product" in names

    food_list = await client.get("/api/v1/products/", headers={"X-Site-Slug": "chemisto-food"})
    food_names = [p["name"] for p in food_list.json()["data"]["items"]]
    assert "Isolation Test Product" not in food_names


async def test_same_email_can_register_independently_on_both_sites(client):
    email = "shared-email@test.com"
    r1 = await register_customer(client, "chemisto", email)
    r2 = await register_customer(client, "chemisto-food", email)
    assert r1["user"]["id"] != r2["user"]["id"]


async def test_customer_cannot_login_on_wrong_site(client):
    await register_customer(client, "chemisto", "chemisto-only@test.com")
    resp = await client.post(
        "/api/v1/auth/login",
        headers={"X-Site-Slug": "chemisto-food"},
        json={"email": "chemisto-only@test.com", "password": "Password123!"},
    )
    assert resp.status_code == 401


async def test_owner_token_cannot_manage_other_sites_products(client, chemisto_owner_token):
    resp = await client.post(
        "/api/v1/products/",
        headers={"X-Site-Slug": "chemisto-food", "Authorization": f"Bearer {chemisto_owner_token}"},
        data={"name": "Should Not Be Allowed", "price": "1.00", "stock_quantity": "1"},
    )
    # The owner's own site_id is used server-side regardless of the header,
    # so this either creates it under the OWNER's real site (chemisto), or
    # is rejected -- either way it must never land on chemisto-food.
    assert resp.status_code in (200, 201, 403)
    food_list = await client.get("/api/v1/products/", headers={"X-Site-Slug": "chemisto-food"})
    names = [p["name"] for p in food_list.json()["data"]["items"]]
    assert "Should Not Be Allowed" not in names


async def test_friend_search_finds_nobody_across_sites(client):
    await register_customer(client, "chemisto-food", "findme@test.com")
    alice = await register_customer(client, "chemisto", "alice-search@test.com")

    resp = await client.get(
        "/api/v1/social/search",
        params={"q": "findme"},
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {alice['access_token']}"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == []


async def test_cannot_friend_request_a_user_on_another_site_by_guessing_id(client):
    food_user = await register_customer(client, "chemisto-food", "guess-target@test.com")
    alice = await register_customer(client, "chemisto", "alice-guess@test.com")

    resp = await client.post(
        "/api/v1/social/friend-requests",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {alice['access_token']}"},
        json={"addressee_id": food_user["user"]["id"]},
    )
    assert resp.status_code == 404


async def test_admin_notification_only_visible_to_the_correct_site_owner(
    client, chemisto_owner_token, chemisto_food_owner_token
):
    alice = await register_customer(client, "chemisto", "alice-notif@test.com")

    products = await client.get("/api/v1/products/", headers={"X-Site-Slug": "chemisto"})
    items = products.json()["data"]["items"]
    if not items:
        create = await client.post(
            "/api/v1/products/",
            headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {chemisto_owner_token}"},
            data={"name": "Notif Test Product", "price": "5.00", "stock_quantity": "10"},
        )
        product_id = create.json()["data"]["id"]
    else:
        product_id = items[0]["id"]

    await client.post(
        "/api/v1/cart/items",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {alice['access_token']}"},
        json={"product_id": product_id, "quantity": 1},
    )
    order = await client.post(
        "/api/v1/orders/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {alice['access_token']}"},
        json={"shipping_address": "123 Isolation Test Street"},
    )
    assert order.status_code == 200, order.text

    chemisto_notifs = await client.get(
        "/api/v1/admin/notifications/", headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {chemisto_owner_token}"}
    )
    assert len(chemisto_notifs.json()["data"]) >= 1

    food_notifs = await client.get(
        "/api/v1/admin/notifications/", headers={"X-Site-Slug": "chemisto-food", "Authorization": f"Bearer {chemisto_food_owner_token}"}
    )
    assert food_notifs.json()["data"] == []