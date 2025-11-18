"""Add pgvector index for listing document chunks

Revision ID: 002
Revises: 001
Create Date: 2024-01-17

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Add vector index for similarity search."""

    # Enable pgvector extension (if not already enabled)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Create IVFFlat index for fast vector similarity search
    # IVFFlat is good for datasets < 1M vectors
    # lists = 100 is a good starting point (rule of thumb: sqrt(num_rows))
    op.execute("""
        CREATE INDEX IF NOT EXISTS listing_chunks_embedding_idx
        ON listing_document_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # Note: For better accuracy, you can increase 'lists' as data grows:
    # - 100 lists for ~10K vectors
    # - 1000 lists for ~1M vectors
    # Trade-off: More lists = better accuracy but slower indexing


def downgrade():
    """Remove vector index."""

    op.execute('DROP INDEX IF EXISTS listing_chunks_embedding_idx')

    # Note: We don't drop the extension as other tables might use it
    # If you want to fully remove: op.execute('DROP EXTENSION IF EXISTS vector')
