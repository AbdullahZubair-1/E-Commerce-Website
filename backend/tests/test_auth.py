from tests.conftest import register_customer


async def test_duplicate_email_rejected_on_same_site(client):
    await register_customer(client, "chemisto", "dup@test.com")
    resp = await client.post(
        "/api/v1/auth/register",
        headers={"X-Site-Slug": "chemisto"},
        json={"email": "dup@test.com", "password": "Password123!", "first_name": "Test", "last_name": "User"},
    )
    assert resp.status_code == 409


async def test_login_wrong_password_rejected(client):
    await register_customer(client, "chemisto", "wrongpw@test.com")
    resp = await client.post(
        "/api/v1/auth/login",
        headers={"X-Site-Slug": "chemisto"},
        json={"email": "wrongpw@test.com", "password": "TotallyWrongPassword1!"},
    )
    assert resp.status_code == 401


async def test_protected_route_requires_token(client):
    resp = await client.get("/api/v1/social/friends", headers={"X-Site-Slug": "chemisto"})
    assert resp.status_code == 401


async def test_invalid_token_rejected(client):
    resp = await client.get(
        "/api/v1/social/friends",
        headers={"X-Site-Slug": "chemisto", "Authorization": "Bearer not-a-real-token"},
    )
    assert resp.status_code == 401


async def test_customer_cannot_access_admin_routes(client):
    customer = await register_customer(client, "chemisto", "plaincustomer@test.com")
    resp = await client.get(
        "/api/v1/admin/dashboard",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {customer['access_token']}"},
    )
    assert resp.status_code == 403


async def test_owner_cannot_access_superadmin_routes(client, chemisto_owner_token):
    resp = await client.get(
        "/api/v1/superadmin/dashboard",
        headers={"Authorization": f"Bearer {chemisto_owner_token}"},
    )
    assert resp.status_code == 403


async def test_superadmin_cannot_access_owner_only_routes(client, superadmin_token):
    resp = await client.post(
        "/api/v1/products/",
        headers={"X-Site-Slug": "chemisto", "Authorization": f"Bearer {superadmin_token}"},
        data={"name": "Should Fail", "price": "1.00", "stock_quantity": "1"},
    )
    assert resp.status_code == 403


async def test_registration_validates_password_strength(client):
    resp = await client.post(
        "/api/v1/auth/register",
        headers={"X-Site-Slug": "chemisto"},
        json={"email": "weakpw@test.com", "password": "weak", "first_name": "Test", "last_name": "User"},
    )
    assert resp.status_code == 422


async def test_registration_validates_name_length(client):
    resp = await client.post(
        "/api/v1/auth/register",
        headers={"X-Site-Slug": "chemisto"},
        json={"email": "shortname@test.com", "password": "Password123!", "first_name": "A", "last_name": "User"},
    )
    assert resp.status_code == 422