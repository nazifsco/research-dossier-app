"""Add Google OAuth support to users table.

Revision ID: 002_add_google_oauth
Revises: 001_initial
Create Date: 2025-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_google_oauth'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add google_id column
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)

    # Make password_hash nullable (for OAuth-only users)
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=True)


def downgrade() -> None:
    # Make password_hash required again
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=False)

    # Remove google_id
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_column('users', 'google_id')
