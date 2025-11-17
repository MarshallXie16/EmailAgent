"""Add agent reasoning and review queue fields

Revision ID: 001
Revises:
Create Date: 2024-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add reasoning field to agent_runs and review queue fields to email_threads."""

    # Add reasoning column to agent_runs
    op.add_column('agent_runs',
        sa.Column('reasoning', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )

    # Add review queue columns to email_threads
    op.add_column('email_threads',
        sa.Column('requires_review', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column('email_threads',
        sa.Column('priority_score', sa.Numeric(precision=4, scale=2), nullable=False, server_default='5.0')
    )

    # Add indexes for review queue
    op.create_index('ix_email_threads_requires_review', 'email_threads', ['requires_review'])

    # Add composite index for review queue filtering
    op.create_index(
        'idx_threads_review_queue',
        'email_threads',
        ['broker_id', 'requires_review', sa.text('priority_score DESC')],
        postgresql_where=sa.text("status = 'needs_broker'")
    )


def downgrade():
    """Remove reasoning field and review queue fields."""

    # Drop indexes
    op.drop_index('idx_threads_review_queue', table_name='email_threads')
    op.drop_index('ix_email_threads_requires_review', table_name='email_threads')

    # Drop columns from email_threads
    op.drop_column('email_threads', 'priority_score')
    op.drop_column('email_threads', 'requires_review')

    # Drop reasoning column from agent_runs
    op.drop_column('agent_runs', 'reasoning')
