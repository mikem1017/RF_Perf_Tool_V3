"""
Shared pytest fixtures for all tests.
"""
import pytest
import tempfile
import shutil
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_s2p_file():
    """Return path to sample S2P file fixture."""
    # Will be implemented when fixtures are created
    fixture_path = Path(__file__).parent / "fixtures" / "sample_s2p" / "sample.s2p"
    if fixture_path.exists():
        return fixture_path
    pytest.skip("Sample S2P fixture not found")


@pytest.fixture
def sample_s3p_file():
    """Return path to sample S3P file fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_s3p" / "sample.s3p"
    if fixture_path.exists():
        return fixture_path
    pytest.skip("Sample S3P fixture not found")


@pytest.fixture
def sample_s4p_file():
    """Return path to sample S4P file fixture."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_s4p" / "sample.s4p"
    if fixture_path.exists():
        return fixture_path
    pytest.skip("Sample S4P fixture not found")


@pytest.fixture
def in_memory_db():
    """Return SQLite in-memory database connection string."""
    return "sqlite:///:memory:"


@pytest.fixture
def temp_results_dir(temp_dir):
    """Return temporary directory for artifact testing."""
    results_dir = temp_dir / "results"
    results_dir.mkdir()
    return results_dir

