import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        user="postgres",
        password="PASTE_YOUR_POSTGRES_SUPERUSER_PASSWORD_HERE",
        host="localhost",
        port=5432,
        database="postgres",
    )
    try:
        await conn.execute("ALTER ROLE chemisto CREATEDB;")
        print("Granted CREATEDB to chemisto.")
    finally:
        await conn.close()

asyncio.run(main())