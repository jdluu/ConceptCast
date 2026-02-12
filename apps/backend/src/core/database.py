import os
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../../conceptcast.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class JobRecord(Base):
    """
    SQLAlchemy model for storing job state and artifacts.

    Attributes:
        job_id (str): Unique identifier for the job (UUID).
        topic (str): The main concept topic requested.
        target_audience (str): The target audience for the explanation.
        status (str): Current status of the job (e.g., 'planning', 'completed').
        current_step (str | None): The specific step currently executing.
        plan (dict | None): The generated curriculum plan JSON.
        validation (dict | None): The validation results JSON.
        storyboard (dict | None): The generated storyboard JSON.
        manim_code (str | None): The generated Manim Python code.
        video_url (str | None): URL to the rendered video file.
        error (str | None): Error message if the job failed.
        mode (str): Execution mode ('live' or 'mock').
        created_at (datetime): Timestamp when the job was created.
        updated_at (datetime): Timestamp when the job was last updated.
    """

    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True, index=True)
    topic: Mapped[str] = mapped_column(String, index=True)
    target_audience: Mapped[str] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="planning")
    current_step: Mapped[str | None] = mapped_column(String, nullable=True)
    plan: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    validation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    storyboard: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    manim_code: Mapped[str | None] = mapped_column(String, nullable=True)
    video_url: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    mode: Mapped[str] = mapped_column(String, default="live")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


def init_db() -> None:
    """
    Initializes the database tables.

    Side Effects:
        Creates all tables defined in the declarative base if they do not exist.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, Any, None]:
    """
    Dependency to get a database session.

    Yields:
        Session: A standard SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
