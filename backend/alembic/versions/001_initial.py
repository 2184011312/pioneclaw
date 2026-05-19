"""Initial migration - PioneClaw

Revision ID: 001_initial
Revises:
Create Date: 2026-05-01

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(50), nullable=True),
        sa.Column('avatar', sa.String(255), nullable=True),
        sa.Column('role', sa.String(20), nullable=True, default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('organization_id', sa.String(36), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('position', sa.String(100), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('is_super_admin', sa.Boolean(), default=False),
        sa.Column('is_org_admin', sa.Boolean(), default=False),
        sa.Column('last_login_at', sa.DateTime(), nullable=True),
        sa.Column('last_login_ip', sa.String(45), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_organization_id'), 'users', ['organization_id'], unique=False)

    # 组织表
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('level', sa.Integer(), default=1),
        sa.Column('path', sa.String(500), nullable=True),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(20), default='department'),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['parent_id'], ['organizations.id'], ),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_organizations_code'), 'organizations', ['code'], unique=True)

    # 角色表
    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('code', sa.String(50), nullable=False),
        sa.Column('description', sa.String(200), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('type', sa.String(20), default='custom'),
        sa.Column('level', sa.Integer(), default=0),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('organization_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('code'),
    )
    op.create_index(op.f('ix_roles_code'), 'roles', ['code'], unique=True)

    # 权限表
    op.create_table(
        'permissions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(20), default='app'),
        sa.Column('resource', sa.String(50), nullable=True),
        sa.Column('action', sa.String(20), nullable=True),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('menu_id', sa.String(36), nullable=True),
        sa.Column('is_system', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        sa.ForeignKeyConstraint(['parent_id'], ['permissions.id'], ),
    )
    op.create_index(op.f('ix_permissions_code'), 'permissions', ['code'], unique=True)

    # Agent 表
    op.create_table(
        'agents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model', sa.String(100), default='gpt-4o'),
        sa.Column('max_turns', sa.Integer(), default=20),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_agents_name'), 'agents', ['name'], unique=True)

    # Skill 表
    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), default='custom'),
        sa.Column('scope', sa.String(20), default='personal'),
        sa.Column('package_type', sa.String(20), default='inline'),
        sa.Column('package_size', sa.Integer(), default=0),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_public', sa.Boolean(), default=True),
        sa.Column('creator_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_skills_name'), 'skills', ['name'], unique=True)

    # Agent-Skill 关联表
    op.create_table(
        'agent_skills',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('skill_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['skill_id'], ['skills.id'], ),
    )

    # Memory 表
    op.create_table(
        'memories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('type', sa.String(20), default='fact'),
        sa.Column('key', sa.String(200), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.String(500), nullable=True),
        sa.Column('importance', sa.Integer(), default=3),
        sa.Column('is_archived', sa.Boolean(), default=False),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_memories_key'), 'memories', ['key'], unique=False)

    # Agent Memory 表
    op.create_table(
        'agent_memories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(20), default='fact'),
        sa.Column('project', sa.String(100), nullable=True),
        sa.Column('key', sa.String(200), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('summary', sa.String(500), nullable=True),
        sa.Column('importance', sa.Integer(), default=3),
        sa.Column('is_pinned', sa.Boolean(), default=False),
        sa.Column('is_archived', sa.Boolean(), default=False),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('working_dir', sa.String(500), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
    )
    op.create_index(op.f('ix_agent_memories_key'), 'agent_memories', ['key'], unique=False)

    # Runner 表
    op.create_table(
        'runners',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('host', sa.String(255), nullable=True),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('api_key', sa.String(255), nullable=True),
        sa.Column('capabilities', sa.JSON(), nullable=True),
        sa.Column('version', sa.String(50), nullable=True),
        sa.Column('platform', sa.String(100), nullable=True),
        sa.Column('last_heartbeat', sa.DateTime(), nullable=True),
        sa.Column('current_task', sa.String(100), nullable=True),
        sa.Column('total_tasks', sa.Integer(), default=0),
        sa.Column('success_tasks', sa.Integer(), default=0),
        sa.Column('failed_tasks', sa.Integer(), default=0),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('reject_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
    )
    op.create_index(op.f('ix_runners_name'), 'runners', ['name'], unique=True)

    # Task 表
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='todo'),
        sa.Column('priority', sa.String(20), default='normal'),
        sa.Column('task_type', sa.String(50), default='manual'),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('runner_id', sa.Integer(), nullable=True),
        sa.Column('creator_id', sa.Integer(), nullable=False),
        sa.Column('assignee_id', sa.Integer(), nullable=True),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('due_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['runner_id'], ['runners.id'], ),
        sa.ForeignKeyConstraint(['creator_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['assignee_id'], ['users.id'], ),
    )

    # Task Comment 表
    op.create_table(
        'task_comments',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('mentions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), default=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_id'], ['task_comments.id'], ),
    )
    op.create_index(op.f('ix_task_comments_task_id'), 'task_comments', ['task_id'], unique=False)

    # Cron Job 表
    op.create_table(
        'cron_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('schedule_type', sa.String(20), nullable=True),
        sa.Column('schedule_value', sa.String(100), nullable=True),
        sa.Column('job_type', sa.String(20), default='system'),
        sa.Column('is_enabled', sa.Boolean(), default=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('last_run', sa.DateTime(), nullable=True),
        sa.Column('next_run', sa.DateTime(), nullable=True),
        sa.Column('run_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_cron_jobs_name'), 'cron_jobs', ['name'], unique=True)

    # System Settings 表
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('category', sa.String(50), default='general'),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key'),
    )
    op.create_index(op.f('ix_system_settings_key'), 'system_settings', ['key'], unique=True)

    # API Usage 表
    op.create_table(
        'api_usage',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('call_count', sa.Integer(), default=1),
        sa.Column('input_tokens', sa.Integer(), default=0),
        sa.Column('output_tokens', sa.Integer(), default=0),
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('duration_ms', sa.Integer(), default=0),
        sa.Column('is_success', sa.Boolean(), default=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index(op.f('ix_api_usage_user_id'), 'api_usage', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_usage_created_at'), 'api_usage', ['created_at'], unique=False)

    # AI Model Config 表
    op.create_table(
        'ai_model_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('provider', sa.String(50), default='openai'),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('base_url', sa.String(500), nullable=True),
        sa.Column('api_key', sa.String(500), nullable=True),
        sa.Column('context_window', sa.Integer(), default=128000),
        sa.Column('max_tokens', sa.Integer(), default=4096),
        sa.Column('temperature', sa.Float(), default=0.7),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('extra_config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_index(op.f('ix_ai_model_configs_name'), 'ai_model_configs', ['name'], unique=True)

    # Knowledge Base 表
    op.create_table(
        'knowledge_bases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('description', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_knowledge_bases_name'), 'knowledge_bases', ['name'], unique=False)

    # Knowledge Document 表
    op.create_table(
        'knowledge_documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('knowledge_base_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(200), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('source', sa.String(500), nullable=True),
        sa.Column('doc_type', sa.String(50), default='text'),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('chunk_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['knowledge_base_id'], ['knowledge_bases.id'], ),
    )
    op.create_index(op.f('ix_knowledge_documents_knowledge_base_id'), 'knowledge_documents', ['knowledge_base_id'], unique=False)

    # Agent Execution 表
    op.create_table(
        'agent_executions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('system_prompt', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='running'),
        sa.Column('total_iterations', sa.Integer(), default=0),
        sa.Column('total_tool_calls', sa.Integer(), default=0),
        sa.Column('total_tokens', sa.Integer(), default=0),
        sa.Column('input_tokens', sa.Integer(), default=0),
        sa.Column('output_tokens', sa.Integer(), default=0),
        sa.Column('latency_ms', sa.Integer(), default=0),
        sa.Column('tool_calls', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('model_config_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['model_config_id'], ['ai_model_configs.id'], ),
    )
    op.create_index(op.f('ix_agent_executions_agent_id'), 'agent_executions', ['agent_id'], unique=False)
    op.create_index(op.f('ix_agent_executions_user_id'), 'agent_executions', ['user_id'], unique=False)

    # Wiki 表
    op.create_table(
        'wikis',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('path', sa.String(500), nullable=False),
        sa.Column('parent_id', sa.String(36), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('organization_id', sa.String(36), nullable=True),
        sa.Column('version', sa.Integer(), default=1),
        sa.Column('status', sa.String(20), default='published'),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('path'),
        sa.ForeignKeyConstraint(['parent_id'], ['wikis.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    )
    op.create_index(op.f('ix_wikis_path'), 'wikis', ['path'], unique=True)

    # Wiki Version 表
    op.create_table(
        'wiki_versions',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('wiki_id', sa.String(36), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('change_summary', sa.String(500), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['wiki_id'], ['wikis.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    )
    op.create_index(op.f('ix_wiki_versions_wiki_id'), 'wiki_versions', ['wiki_id'], unique=False)


def downgrade() -> None:
    op.drop_table('wiki_versions')
    op.drop_table('wikis')
    op.drop_table('agent_executions')
    op.drop_table('knowledge_documents')
    op.drop_table('knowledge_bases')
    op.drop_table('ai_model_configs')
    op.drop_table('api_usage')
    op.drop_table('system_settings')
    op.drop_table('cron_jobs')
    op.drop_table('task_comments')
    op.drop_table('tasks')
    op.drop_table('runners')
    op.drop_table('agent_memories')
    op.drop_table('memories')
    op.drop_table('agent_skills')
    op.drop_table('skills')
    op.drop_table('agents')
    op.drop_table('permissions')
    op.drop_table('roles')
    op.drop_table('organizations')
    op.drop_table('users')
