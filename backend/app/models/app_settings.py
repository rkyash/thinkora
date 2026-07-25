"""
AppSetting model — key-value configuration store.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AppSetting(Base):
    __tablename__ = "app_settings"

    # Override the UUID PK from Base — settings use string keys
    id: Mapped[str] = mapped_column(String(255), primary_key=True)  # type: ignore[assignment]
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<AppSetting {self.id}={self.value}>"
