from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.database import Base


class ThoughtRecord(Base):
    """SQLAlchemy model representing a single streaming log from an AI agent.

    Moved from JSON blobs to a granular relational model to allow highly
    concurrent stream appending without locking the entire JobRecord.
    """

    __tablename__ = "thoughts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(
        String, ForeignKey("jobs.job_id", ondelete="CASCADE"), index=True
    )
    agent: Mapped[str] = mapped_column(String, index=True)
    phase: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(String)
    ts: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), index=True
    )

    job = relationship("JobRecord", back_populates="thoughts")
