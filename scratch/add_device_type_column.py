
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

async def migrate():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print("Adding device_type column to photos table...")
        try:
            await conn.execute(text("ALTER TABLE photos ADD COLUMN device_type VARCHAR(20) DEFAULT 'desktop' NOT NULL;"))
            await conn.execute(text("CREATE INDEX ix_photos_device_type ON photos(device_type);"))
            print("Successfully added column and index.")
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
