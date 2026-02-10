import os
from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../../conceptcast.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class JobRecord(Base):
    __tablename__ = "jobs"

    job_id = Column(String, primary_key=True, index=True)
    status = Column(String, default="planning")
    request_data = Column(JSON)  # Stores the original request
    plan_data = Column(JSON, nullable=True)
    validation_data = Column(JSON, nullable=True)
    storyboard_data = Column(JSON, nullable=True)
    manim_code = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    error = Column(String, nullable=True)
    mode = Column(String, default="live")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


def init_db():
    """
    Initializes the database schema.

    Creates all tables defined in the SQLAlchemy models if they do not exist.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    Dependency for obtaining a database session.

    Yields:
        Session: A SQLAlchemy database session.

    Side Effects:
        Closes the session after the request is completed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
