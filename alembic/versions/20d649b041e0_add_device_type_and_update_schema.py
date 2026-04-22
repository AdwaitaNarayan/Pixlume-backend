"""Add device_type and update schema

Revision ID: 20d649b041e0
Revises: caac42906e1c
Create Date: 2026-04-22 23:11:13.673213

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20d649b041e0'
down_revision: Union[str, Sequence[str], None] = 'caac42906e1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema safely."""
    # 1. Add the missing device_type column ONLY if it doesn't exist
    op.execute("ALTER TABLE photos ADD COLUMN IF NOT EXISTS device_type VARCHAR(20) DEFAULT 'desktop' NOT NULL")
    
    # 2. Add the comment (can be run multiple times safely)
    op.execute("COMMENT ON COLUMN photos.device_type IS 'Type of device the photo is optimized for: desktop, mobile, or both'")
    
    # 3. Create the index ONLY if it doesn't exist
    op.execute("CREATE INDEX IF NOT EXISTS ix_photos_device_type ON photos (device_type)")
    
    # 4. Update comment on tags
    op.execute("COMMENT ON COLUMN photos.tags IS 'Searchable array of tag strings'")
    
    # 5. Update users.created_at to NOT NULL (safely)
    op.execute("ALTER TABLE users ALTER COLUMN created_at SET NOT NULL")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE users ALTER COLUMN created_at DROP NOT NULL")
    op.execute("COMMENT ON COLUMN photos.tags IS NULL")
    op.execute("DROP INDEX IF EXISTS ix_photos_device_type")
    op.execute("ALTER TABLE photos DROP COLUMN IF EXISTS device_type")
