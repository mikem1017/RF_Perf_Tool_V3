"""
Tests for SQLite database get methods (lines 57, 72, 87, 102).
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.src.storage.database import init_database, create_database_engine
from backend.src.storage.sqlite_db import SQLiteDatabase


@pytest.fixture
def db():
    """Create database instance."""
    engine = create_database_engine("sqlite:///:memory:")
    init_database(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return SQLiteDatabase(session)


def test_get_device_none(db):
    """Test get_device returns None for non-existent device (line 57)."""
    device = db.get_device(999)
    assert device is None


def test_get_test_stage_none(db):
    """Test get_test_stage returns None for non-existent stage (line 72)."""
    stage = db.get_test_stage(999)
    assert stage is None


def test_get_requirement_set_none(db):
    """Test get_requirement_set returns None for non-existent set (line 87)."""
    req_set = db.get_requirement_set(999)
    assert req_set is None


def test_get_test_run_none(db):
    """Test get_test_run returns None for non-existent test run (line 102)."""
    test_run = db.get_test_run(999)
    assert test_run is None


