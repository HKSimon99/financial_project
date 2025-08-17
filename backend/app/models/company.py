from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Company(Base):
    """Represents a listed company."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False, index=True)
    ticker: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    exchange: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)
    sector: Mapped[str | None] = mapped_column(String)
    aliases: Mapped[list | dict | None] = mapped_column(JSONB)
    popularity: Mapped[float | None] = mapped_column(Float, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
