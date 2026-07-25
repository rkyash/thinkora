"""
GraphNode model — knowledge graph entity nodes.
"""

from sqlalchemy import Enum, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import GraphNodeType
from app.database import Base


class GraphNode(Base):
    __tablename__ = "graph_nodes"

    notebook_id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False
    )
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[GraphNodeType] = mapped_column(
        Enum(GraphNodeType, name="graph_node_type"), nullable=False
    )
    x_pos: Mapped[float | None] = mapped_column(Float, nullable=True)
    y_pos: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    notebook: Mapped["Notebook"] = relationship(back_populates="graph_nodes")  # noqa: F821

    def __repr__(self) -> str:
        return f"<GraphNode {self.label} ({self.type.value})>"
