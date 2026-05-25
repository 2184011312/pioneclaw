"""drop layered_memories table — replaced by app.modules.memory (fish_memory)

Revision ID: 004_drop_layered_memories
Revises: 003_add_reasoning_content
Create Date: 2026-05-23

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '004_drop_layered_memories'
down_revision: Union[str, None] = '003_add_reasoning_content'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS layered_memories")


def downgrade() -> None:
    op.create_table(
        'layered_memories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('uri', sa.String(500), nullable=True),
        sa.Column('parent_uri', sa.String(500), nullable=True),
        sa.Column('layer', sa.Integer(), nullable=True),
        sa.Column('context_type', sa.String(20), nullable=True),
        sa.Column('name', sa.String(200), nullable=True),
        sa.Column('abstract', sa.Text(), nullable=True),
        sa.Column('overview', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('importance', sa.Integer(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(100), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('vector_id', sa.String(200), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_layered_memories_uri', 'layered_memories', ['uri'], unique=True)
    op.create_index('ix_layered_memories_user_id', 'layered_memories', ['user_id'], unique=False)
    op.create_index('ix_layered_memories_session', 'layered_memories', ['session_id', 'layer'], unique=False)
