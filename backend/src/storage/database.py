"""
Database initialization and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path
from typing import Optional
from .models import Base


def create_database_engine(database_url: str = "sqlite:///:memory:"):
    """
    Create SQLAlchemy engine.
    
    Args:
        database_url: Database URL (default: in-memory SQLite)
    
    Returns:
        SQLAlchemy engine
    """
    if database_url.startswith("sqlite"):
        # Use StaticPool for in-memory SQLite to allow multiple connections
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if ":memory:" in database_url else {},
            poolclass=StaticPool if ":memory:" in database_url else None,
            echo=False,  # Set to True for SQL debugging
        )
    else:
        engine = create_engine(database_url, echo=False)
    
    return engine


def init_database(engine):
    """Initialize database schema."""
    Base.metadata.create_all(engine)


def get_session_factory(engine):
    """Get session factory."""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def create_database_session(engine) -> Session:
    """Create a database session."""
    Session = get_session_factory(engine)
    return Session()

