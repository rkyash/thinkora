"""auto create default user

Revision ID: d14aec8d7089
Revises: 5f313a248c38
Create Date: 2026-06-27 20:30:02.116334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd14aec8d7089'
down_revision: Union[str, Sequence[str], None] = '5f313a248c38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from app.services.auth import hash_password
import uuid

def upgrade() -> None:
    """Upgrade schema."""
    default_email = "admin@thinkora.local"
    default_username = "admin"
    default_password = "admin"
    
    # Check if user already exists
    conn = op.get_bind()
    res = conn.execute(
        sa.text("SELECT id FROM users WHERE email = :email"),
        {"email": default_email}
    ).fetchone()

    if not res:
        hashed_password = hash_password(default_password)
        user_id = str(uuid.uuid4())
        
        conn.execute(
            sa.text(
                """
                INSERT INTO users (id, email, username, hashed_password, is_active)
                VALUES (:id, :email, :username, :hashed_password, :is_active)
                """
            ),
            {
                "id": user_id,
                "email": default_email,
                "username": default_username,
                "hashed_password": hashed_password,
                "is_active": True
            }
        )

def downgrade() -> None:
    """Downgrade schema."""
    default_email = "admin@thinkora.local"
    
    conn = op.get_bind()
    conn.execute(
        sa.text("DELETE FROM users WHERE email = :email"),
        {"email": default_email}
    )
