import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.connection import AsyncSessionLocal
from app.models.user_model import User
from app.services.auth_service import verify_password

async def test():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print("Users in DB:", [u.email for u in users])
        
        # Test password
        for u in users:
            print(f"Is admin123 correct for {u.email}?", verify_password("admin123", u.hashed_password))

if __name__ == "__main__":
    asyncio.run(test())
