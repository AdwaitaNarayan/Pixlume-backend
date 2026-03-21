import asyncio
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.connection import AsyncSessionLocal
from app.models.user_model import User
from app.services.auth_service import get_password_hash

async def create_user(email: str, password: str):
    print("Connecting to DB to create admin user...")
    async with AsyncSessionLocal() as session:
        # Check if user already exists
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            print(f"Warning: Admin user with email '{email}' already exists.")
            return

        print(f"Creating user {email}...")
        hashed_password = get_password_hash(password)
        new_user = User(email=email, hashed_password=hashed_password)
        session.add(new_user)
        try:
            await session.commit()
            print("Admin user created successfully! You can now login.")
        except Exception as e:
            await session.rollback()
            print(f"Error creating user: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create_admin.py <email> <password>")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2]
    
    asyncio.run(create_user(email, password))
