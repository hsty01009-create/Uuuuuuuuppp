import aiosqlite

DB = "bot.db"


async def create_db():
    async with aiosqlite.connect(DB) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            accepted INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 100
        )
        """)
        await db.commit()


async def add_user(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users(user_id) VALUES(?)",
            (user_id,)
        )
        await db.commit()


async def accept_rules(user_id):
    async with aiosqlite.connect(DB) as db:
        await db.execute(
            "UPDATE users SET accepted=1 WHERE user_id=?",
            (user_id,)
        )
        await db.commit()


async def is_accepted(user_id):
    async with aiosqlite.connect(DB) as db:
        cur = await db.execute(
            "SELECT accepted FROM users WHERE user_id=?",
            (user_id,)
        )
        row = await cur.fetchone()
        return row and row[0] == 1
