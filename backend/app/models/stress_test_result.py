from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.stress_test_run import StressTestRun


class StressTestResult(Base):
    """Stress test result model - stores simulation outputs."""
    
    __tablename__ = "stress_test_results"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("stress_test_runs.id"), unique=True, nullable=False, index=True
    )
    summary_metrics_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    drivers_json: Mapped[list] = mapped_column(
        JSON, nullable=False, default=list
    )
    chart_data_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    
    # Relationships
    run: Mapped["StressTestRun"] = relationship(
        "StressTestRun", back_populates="result"
    )
