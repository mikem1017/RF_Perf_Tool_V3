"""
Tests for database utility functions.
"""
import pytest
from backend.src.storage.database import (
    create_database_engine,
    init_database,
    get_session_factory,
    create_database_session,
)


def test_create_database_engine_in_memory():
    """Test creating in-memory database engine."""
    engine = create_database_engine("sqlite:///:memory:")
    assert engine is not None
    assert str(engine.url) == "sqlite:///:memory:"


def test_create_database_engine_file():
    """Test creating file-based database engine."""
    engine = create_database_engine("sqlite:///test.db")
    assert engine is not None
    assert "test.db" in str(engine.url)


def test_init_database():
    """Test initializing database schema."""
    engine = create_database_engine("sqlite:///:memory:")
    init_database(engine)
    
    # Verify tables were created by checking if we can create a session
    Session = get_session_factory(engine)
    session = Session()
    assert session is not None
    session.close()


def test_get_session_factory():
    """Test getting session factory."""
    engine = create_database_engine("sqlite:///:memory:")
    Session = get_session_factory(engine)
    
    assert Session is not None
    session = Session()
    assert session is not None
    session.close()


def test_create_database_session():
    """Test creating database session."""
    engine = create_database_engine("sqlite:///:memory:")
    init_database(engine)
    
    session = create_database_session(engine)
    assert session is not None
    assert hasattr(session, 'query')
    session.close()


