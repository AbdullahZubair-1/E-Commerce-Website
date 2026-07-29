"""
Shared pytest fixtures for the backend test suite.

Design decisions (worth knowing before adding new tests):
- Runs against your REAL database (same DATABASE_URL as the app), but every
  connection this suite makes is scoped to a dedicated Postgres SCHEMA
  ("pytest_test") via asyncpg's search_path setting -- not a separate
  database. This avoids needing the CREATEDB privilege (which a database
  user doesn't get by default, only a Postgres superuser does); creating a
  schema inside a database you already own doesn't need that privilege.
  Your real data, which lives in the "public" schema, is never touched --
  this suite only ever creates/drops/queries tables inside pytest_test.
- Tables are created directly from the SQLAlchemy models
  (Base.metadata.create_all) rather than running Alembic migrations --
  faster, and sufficient since we only care about the current schema.
- Every test function gets a fully reset database: all tables in
  pytest_test are truncated and the two sites + owner accounts +
  superadmin are reseeded fresh, via the same seed_sites_and_owners() the
  real app uses on startup.
"""
import os
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Import settings first (this reads your real .env / DATABASE_URL) rather
# than overriding it -- this suite deliberately reuses your existing
# database connection, just scoped to its own schema.
from app.core.config import settings

TEST_SCHEMA = "pytest_test"

# A dedicated engine, pointed at the same database as the real app, but
# with every connection's search_path pinned to the test schema. This is
# separate from app.database.session's own engine so the two never
# interfere, and so this file doesn't need DATABASE_URL overridden at all.
test_engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"server_settings": {"search_path": TEST_SCHEMA}},
)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, autoflush=False, autocommit=False)

os.environ["SECRET_KEY"] = os.environ.get("SECRET_KEY") or "test-secret-key-for-pytest-only"

from app.main import app
from app.database.session import Base
from app.core.seed import SITE_SEEDS
from app.core.security import get_password_hash
from app.core.config import settings
from app.models.site import Site
from app.models.user import User
from app.database import session as app_session_module

# Point the REAL app's own engine/session at the test schema too, for the
# duration of the test run -- this is what makes get_db() (used by every
# request the test client makes) land in pytest_test instead of your real
# data, without needing to touch app.database.session's source code.
app_session_module.engine = test_engine
app_session_module.AsyncSessionLocal = TestSessionLocal


async def _seed_test_data() -> None:
    """A test-local copy of app.core.seed.seed_sites_and_owners(), using
    TestSessionLocal explicitly rather than calling the real function.
    The real one does `from app.database.session import AsyncSessionLocal`
    at its OWN module level -- a direct name binding made at import time,
    which reassigning app.database.session.AsyncSessionLocal afterwards
    does NOT retroactively redirect. Calling it directly would silently
    keep writing to your real database instead of the test schema."""
    async with TestSessionLocal() as db:
        for slug, name, owner_email, owner_password, first_name, last_name in SITE_SEEDS:
            result = await db.execute(select(Site).where(Site.slug == slug))
            site = result.scalar_one_or_none()
            if not site:
                site = Site(slug=slug, name=name)
                db.add(site)
                await db.flush()

            result = await db.execute(
                select(User).where(User.site_id == site.id, User.is_owner == True)  # noqa: E712
            )
            if result.scalar_one_or_none():
                continue

            owner = User(
                site_id=site.id,
                email=owner_email.lower(),
                first_name=first_name,
                last_name=last_name,
                hashed_password=get_password_hash(owner_password),
                is_owner=True,
            )
            db.add(owner)

        result = await db.execute(select(User).where(User.is_superadmin == True))  # noqa: E712
        if not result.scalar_one_or_none():
            superadmin = User(
                site_id=None,
                email=settings.SUPERADMIN_EMAIL.lower(),
                first_name=settings.SUPERADMIN_FIRST_NAME,
                last_name=settings.SUPERADMIN_LAST_NAME,
                hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
                is_owner=False,
                is_superadmin=True,
            )
            db.add(superadmin)

        await db.commit()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_schema():
    """Create the dedicated test schema and every table inside it, once,
    at the start of the whole test session."""
    async with test_engine.begin() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{TEST_SCHEMA}"'))
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.execute(text(f'DROP SCHEMA IF EXISTS "{TEST_SCHEMA}" CASCADE'))
    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _reset_database():
    """Wipe every table in the test schema and reseed the two sites +
    owners + superadmin before every single test function, so tests can
    never see each other's leftover data."""
    async with test_engine.begin() as conn:
        result = await conn.execute(text(
            "SELECT tablename FROM pg_tables WHERE schemaname = :schema"
        ), {"schema": TEST_SCHEMA})
        tables = [row[0] for row in result.fetchall() if row[0] != "alembic_version"]
        if tables:
            quoted = ", ".join(f'"{TEST_SCHEMA}"."{t}"' for t in tables)
            await conn.execute(text(f"TRUNCATE TABLE {quoted} RESTART IDENTITY CASCADE"))
    await _seed_test_data()
    yield


@pytest_asyncio.fixture
async def client():
    """An httpx client that talks directly to the FastAPI app in-process --
    no real server/port needed."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db():
    """A raw DB session (scoped to the test schema), for tests that need to
    set up data the API alone can't easily produce."""
    async with TestSessionLocal() as session:
        yield session


# --- Known IDs for the two seeded sites (must match app/core/seed.py) ---
CHEMISTO_SITE_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CHEMISTO_FOOD_SITE_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest_asyncio.fixture
async def chemisto_owner_token(client):
    resp = await client.post(
        "/api/v1/auth/login",
        headers={"X-Site-Slug": "chemisto"},
        json={"email": "owner@chemisto.com", "password": "ChemistoOwner2024!"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def chemisto_food_owner_token(client):
    resp = await client.post(
        "/api/v1/auth/login",
        headers={"X-Site-Slug": "chemisto-food"},
        json={"email": "owner@chemistofood.com", "password": "ChemistoFoodOwner2024!"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


@pytest_asyncio.fixture
async def superadmin_token(client):
    resp = await client.post(
        "/api/v1/auth/superadmin-login",
        json={"email": "superadmin@chemisto.org", "password": "SuperAdmin2024!"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["data"]["access_token"]


async def register_customer(client, site_slug: str, email: str, password: str = "Password123!") -> dict:
    """Helper: register a fresh customer on a given site, return the full
    {access_token, user} payload."""
    resp = await client.post(
        "/api/v1/auth/register",
        headers={"X-Site-Slug": site_slug},
        json={"email": email, "password": password, "first_name": "Test", "last_name": "User"},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]