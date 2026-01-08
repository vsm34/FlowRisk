from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.financial_profile import FinancialProfile
    from app.models.scenario import Scenario
    from app.models.stress_test_run import StressTestRun


class User(Base):
    """User model."""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firebase_uid: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Relationships
    profile: Mapped["FinancialProfile | None"] = relationship(
        "FinancialProfile", back_populates="user", uselist=False
    )
    scenarios: Mapped[list["Scenario"]] = relationship(
        "Scenario", back_populates="user", cascade="all, delete-orphan"
    )
    stress_test_runs: Mapped[list["StressTestRun"]] = relationship(
        "StressTestRun", back_populates="user", cascade="all, delete-orphan"
    )
