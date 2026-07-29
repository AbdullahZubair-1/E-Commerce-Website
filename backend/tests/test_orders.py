from tests.conftest import register_customer


async def _create_product(client, owner_token, name="Test Product", price="10.00", stock=5):
    resp = await client.post(
        "/api/v1/products/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {owner_token}"},
        data={"name": name, "price": price, "stock_quantity": str(stock)},
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["data"]


async def test_placing_order_with_empty_cart_is_rejected(client):
    customer = await register_customer(client, "chemisto", "emptycart@test.com")
    resp = await client.post(
        "/api/v1/orders/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"shipping_address": "123 Empty Cart Street"},
    )
    assert resp.status_code == 400


async def test_order_decrements_stock_correctly(client, chemisto_owner_token):
    product = await _create_product(client, chemisto_owner_token, name="Stock Test Item", stock=5)
    customer = await register_customer(client, "chemisto", "stocktest@test.com")

    await client.post(
        "/api/v1/cart/items",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"product_id": product["id"], "quantity": 3},
    )
    order = await client.post(
        "/api/v1/orders/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"shipping_address": "123 Stock Test Street"},
    )
    assert order.status_code == 200, order.text

    updated = await client.get(f"/api/v1/products/{product['id']}", headers={"X-Site-Slug": "chemisto"})
    assert updated.json()["data"]["stock_quantity"] == 2  # 5 - 3


async def test_order_exceeding_stock_is_rejected(client, chemisto_owner_token):
    product = await _create_product(client, chemisto_owner_token, name="Low Stock Item", stock=2)
    customer = await register_customer(client, "chemisto", "overstock@test.com")

    await client.post(
        "/api/v1/cart/items",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"product_id": product["id"], "quantity": 10},
    )
    order = await client.post(
        "/api/v1/orders/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"shipping_address": "123 Overstock Street"},
    )
    assert order.status_code == 400


async def test_order_total_calculated_correctly_across_multiple_items(client, chemisto_owner_token):
    product_a = await _create_product(client, chemisto_owner_token, name="Item A", price="10.00", stock=10)
    product_b = await _create_product(client, chemisto_owner_token, name="Item B", price="7.50", stock=10)
    customer = await register_customer(client, "chemisto", "totaltest@test.com")

    await client.post(
        "/api/v1/cart/items",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"product_id": product_a["id"], "quantity": 2},
    )
    await client.post(
        "/api/v1/cart/items",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"product_id": product_b["id"], "quantity": 3},
    )
    order = await client.post(
        "/api/v1/orders/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"shipping_address": "123 Total Test Street"},
    )
    assert order.status_code == 200, order.text
    # 2 * 10.00 + 3 * 7.50 = 20.00 + 22.50 = 42.50
    assert float(order.json()["data"]["total_amount"]) == 42.50


async def test_order_clears_the_cart(client, chemisto_owner_token):
    product = await _create_product(client, chemisto_owner_token, name="Cart Clear Item", stock=10)
    customer = await register_customer(client, "chemisto", "cartclear@test.com")

    await client.post(
        "/api/v1/cart/items",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"product_id": product["id"], "quantity": 1},
    )
    await client.post(
        "/api/v1/orders/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"shipping_address": "123 Cart Clear Street"},
    )

    cart = await client.get(
        "/api/v1/cart/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
    )
    assert cart.json()["data"]["items"] == []


async def test_customer_cannot_update_order_status(client, chemisto_owner_token):
    product = await _create_product(client, chemisto_owner_token, name="Status Test Item", stock=10)
    customer = await register_customer(client, "chemisto", "statustest@test.com")
    await client.post(
        "/api/v1/cart/items",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"product_id": product["id"], "quantity": 1},
    )
    order = await client.post(
        "/api/v1/orders/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"shipping_address": "123 Status Test Street"},
    )
    order_id = order.json()["data"]["id"]

    resp = await client.patch(
        f"/api/v1/orders/admin/{order_id}/status",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"status": "shipped"},
    )
    assert resp.status_code == 403


async def test_owner_can_update_order_status(client, chemisto_owner_token):
    product = await _create_product(client, chemisto_owner_token, name="Owner Status Item", stock=10)
    customer = await register_customer(client, "chemisto", "ownerstatus@test.com")
    await client.post(
        "/api/v1/cart/items",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"product_id": product["id"], "quantity": 1},
    )
    order = await client.post(
        "/api/v1/orders/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
        json={"shipping_address": "123 Owner Status Street"},
    )
    order_id = order.json()["data"]["id"]

    resp = await client.patch(
        f"/api/v1/orders/admin/{order_id}/status",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {chemisto_owner_token}"},
        json={"status": "shipped"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["status"] == "shipped"