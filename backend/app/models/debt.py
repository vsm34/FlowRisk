from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile


class Debt(Base):
    """Debt model - belongs to a financial profile."""
    
    __tablename__ = "debts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    profile_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("financial_profiles.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    apr: Mapped[float] = mapped_column(
        Numeric(6, 5), nullable=False
    )  # Store as decimal fraction (e.g., 0.0499 for 4.99%)
    min_payment: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    
    # Relationships
    profile: Mapped["FinancialProfile"] = relationship(
        "FinancialProfile", back_populates="debts"
    )
