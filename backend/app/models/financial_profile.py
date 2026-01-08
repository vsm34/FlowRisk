from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.debt import Debt
    from app.models.user import User


class FinancialProfile(Base):
    """Financial profile model - one per user."""
    
    __tablename__ = "financial_profiles"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )
    monthly_income: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sigma_income: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.05
    )
    fixed_expenses: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    variable_expenses: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    sigma_variable: Mapped[float] = mapped_column(
        Numeric(5, 4), nullable=False, default=0.10
    )
    liquid_savings: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    assumptions_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
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
    user: Mapped["User"] = relationship("User", back_populates="profile")
    debts: Mapped[list["Debt"]] = relationship(
        "Debt", back_populates="profile", cascade="all, delete-orphan"
    )
