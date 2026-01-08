from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.scenario import Scenario
    from app.models.stress_test_result import StressTestResult
    from app.models.user import User


class StressTestRun(Base):
    """Stress test run model - stores simulation parameters."""
    
    __tablename__ = "stress_test_runs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    scenario_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("scenarios.id"), nullable=True
    )
    horizon_months: Mapped[int] = mapped_column(Integer, nullable=False)
    n_sims: Mapped[int] = mapped_column(Integer, nullable=False)
    seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    assumptions_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
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
    user: Mapped["User"] = relationship("User", back_populates="stress_test_runs")
    scenario: Mapped["Scenario | None"] = relationship("Scenario")
    result: Mapped["StressTestResult | None"] = relationship(
        "StressTestResult", back_populates="run", uselist=False
    )
