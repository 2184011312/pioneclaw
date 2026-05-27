"""add skill_eval_results table

Revision ID: 004_add_skill_eval_results
Revises: 003_add_reasoning_content
Create Date: 2026-05-22

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004_add_skill_eval_results'
down_revision: Union[str, None] = '003_add_reasoning_content'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'skill_eval_results',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('skill_name', sa.String(255), nullable=False, index=True),
        sa.Column('eval_type', sa.String(50), nullable=False),
        sa.Column('eval_mode', sa.String(50), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('dimensions', sa.JSON(), nullable=False),
        sa.Column('static_checks', sa.JSON(), nullable=True),
        sa.Column('redflag_hits', sa.JSON(), nullable=True),
        sa.Column('suggestions', sa.JSON(), nullable=True),
        sa.Column('optimized_content', sa.Text(), nullable=True),
        sa.Column('diff_text', sa.Text(), nullable=True),
        sa.Column('llm_raw_response', sa.Text(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('model_used', sa.String(100), nullable=False, server_default=''),
        sa.Column('tokens_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('creator_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table('skill_eval_results')
