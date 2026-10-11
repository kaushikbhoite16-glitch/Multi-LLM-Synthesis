import asyncio
import aiosqlite

async def migrate():
    async with aiosqlite.connect('multi_llm.db') as db:
        cursor = await db.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in await cursor.fetchall()]
        if 'role' not in cols:
            await db.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            await db.commit()
            print("Added 'role' column to users table")
        else:
            print("'role' column already exists")

if __name__ == "__main__":
    asyncio.run(migrate())
