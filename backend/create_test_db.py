import asyncio
import asyncpg

async def main():
    # Connects to the default 'postgres' database just to run CREATE DATABASE
    conn = await asyncpg.connect(
        user="chemisto",
        password="chemisto_pass",  # same password from your real DATABASE_URL in .env
        host="localhost",
        port=5432,
        database="postgres",
    )
    try:
        await conn.execute("CREATE DATABASE chemisto_test_db OWNER chemisto;")
        print("chemisto_test_db created successfully.")
    except asyncpg.DuplicateDatabaseError:
        print("chemisto_test_db already exists -- nothing to do.")
    finally:
        await conn.close()

asyncio.run(main())