"""add_fts_index_and_search_indexes

Revision ID: ff0be762920b
Revises: d14aec8d7089
Create Date: 2026-07-17 21:05:40.923570

TASK-190: Add PostgreSQL indexes for search scalability.
TASK-191: Add GIN index on tsvector(content) for efficient FTS.
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ff0be762920b'
down_revision: str | Sequence[str] | None = 'd14aec8d7089'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """
    Add search-optimisation indexes:

    1. GIN index on tsvector(english, content) — enables fast FTS without
       computing tsvector on each query.
    2. B-tree on document_chunks.notebook_id — fast filter by notebook.
    3. B-tree on document_chunks.source_id — fast filter by source.
    4. B-tree on graph_nodes.notebook_id — fast graph lookups per notebook.
    5. B-tree on graph_edges.notebook_id — fast edge lookups per notebook.
    """
    # 1. GIN index for full-text search on document_chunks.content
    op.execute(sa.text(
        """
        CREATE INDEX IF NOT EXISTS
            ix_document_chunks_content_fts
        ON document_chunks
        USING GIN (to_tsvector('english', content))
        """
    ))

    # 2. B-tree on document_chunks.notebook_id (filter for per-notebook search)
    op.create_index(
        "ix_document_chunks_notebook_id",
        "document_chunks",
        ["notebook_id"],
        if_not_exists=True,
    )

    # 3. B-tree on document_chunks.source_id (enrichment lookups)
    op.create_index(
        "ix_document_chunks_source_id",
        "document_chunks",
        ["source_id"],
        if_not_exists=True,
    )

    # 4. B-tree on graph_nodes.notebook_id
    op.create_index(
        "ix_graph_nodes_notebook_id",
        "graph_nodes",
        ["notebook_id"],
        if_not_exists=True,
    )

    # 5. B-tree on graph_edges.notebook_id
    op.create_index(
        "ix_graph_edges_notebook_id",
        "graph_edges",
        ["notebook_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    """Drop all indexes added by this migration."""
    op.execute(sa.text("DROP INDEX IF EXISTS ix_document_chunks_content_fts"))
    op.drop_index("ix_document_chunks_notebook_id", table_name="document_chunks", if_exists=True)
    op.drop_index("ix_document_chunks_source_id", table_name="document_chunks", if_exists=True)
    op.drop_index("ix_graph_nodes_notebook_id", table_name="graph_nodes", if_exists=True)
    op.drop_index("ix_graph_edges_notebook_id", table_name="graph_edges", if_exists=True)
