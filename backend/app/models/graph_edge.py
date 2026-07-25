"""
GraphEdge model — knowledge graph relationships between nodes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.graph_node import GraphNode
    from app.models.notebook import Notebook


class GraphEdge(Base):
    __tablename__ = "graph_edges"

    notebook_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )
    source_node: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False
    )
    target_node: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("graph_nodes.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    notebook: Mapped[Notebook] = relationship(back_populates="graph_edges")  # noqa: F821
    source: Mapped[GraphNode] = relationship(  # noqa: F821
        foreign_keys=[source_node],
    )
    target: Mapped[GraphNode] = relationship(  # noqa: F821
        foreign_keys=[target_node],
    )

    def __repr__(self) -> str:
        return f"<GraphEdge {self.source_node} --{self.label}--> {self.target_node}>"
