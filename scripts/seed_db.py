import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from app.database.connection import AsyncSessionLocal, Base, engine
from app.models.photo_model import Photo
from app.models.user_model import User
from app.services.auth_service import get_password_hash

async def seed_db():
    print("Starting database seeding...")
    async with AsyncSessionLocal() as session:
        # 1. Ensure Admin User exists
        admin_email = "admin@pixlume.online"
        result = await session.execute(select(User).where(User.email == admin_email))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print(f"Creating admin user: {admin_email}")
            admin = User(
                email=admin_email,
                hashed_password=get_password_hash("AdminPath123!"), # Change this in production
                is_active=True
            )
            session.add(admin)
        else:
            print("Admin user already exists.")

        # 2. Add Sample Photos
        result = await session.execute(select(Photo).limit(1))
        existing_photo = result.scalar_one_or_none()
        
        if not existing_photo:
            print("Adding sample photos...")
            sample_photos = [
                {
                    "caption": "Majestic Mountain Range",
                    "categories": ["nature", "landscape"],
                    "tags": ["mountain", "snow", "peaks"],
                    "url_base": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b"
                },
                {
                    "caption": "Urban Skyline at Dusk",
                    "categories": ["urban", "architecture"],
                    "tags": ["city", "lights", "skyline"],
                    "url_base": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab"
                },
                {
                    "caption": "Minimalist Abstract Texture",
                    "categories": ["abstract", "art"],
                    "tags": ["texture", "minimal", "grey"],
                    "url_base": "https://images.unsplash.com/photo-1541701494587-cb58502866ab"
                },
                {
                    "caption": "Serene Forest Path",
                    "categories": ["nature", "forest"],
                    "tags": ["trees", "path", "sunlight"],
                    "url_base": "https://images.unsplash.com/photo-1441974231531-c6227db76b6e"
                },
                {
                    "caption": "Modern Glass Skyscraper",
                    "categories": ["architecture", "minimal"],
                    "tags": ["glass", "reflection", "blue"],
                    "url_base": "https://images.unsplash.com/photo-1449156059431-789995fd201c"
                }
            ]
            
            for p_data in sample_photos:
                p_id = uuid.uuid4()
                # We append unsplash params to simulate variants
                base = p_data["url_base"] + "?auto=format&fit=crop&q=80"
                photo = Photo(
                    id=p_id,
                    caption=p_data["caption"],
                    categories=p_data["categories"],
                    tags=p_data["tags"],
                    thumbnail_url=f"{base}&w=200",
                    image_720_url=f"{base}&w=720",
                    image_1080_url=f"{base}&w=1080",
                    image_2k_url=f"{base}&w=2048",
                    image_4k_url=f"{base}&w=3840",
                    created_at=datetime.now(timezone.utc)
                )
                session.add(photo)
        else:
            print("Photos already exist in database.")

        await session.commit()
        print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_db())
