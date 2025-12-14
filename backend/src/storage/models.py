"""
SQLAlchemy database models.
"""
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey,
    JSON, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Device(Base):
    """Device model."""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    part_number = Column(String(100))
    description = Column(Text)
    s_parameter_config = Column(JSON, nullable=False)  # Stores DeviceConfig.s_parameter_config
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    test_runs = relationship("TestRun", back_populates="device")


class TestStage(Base):
    """Test stage model."""
    __tablename__ = "test_stages"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    test_runs = relationship("TestRun", back_populates="test_stage")
    
    __table_args__ = (
        UniqueConstraint('name', name='uq_test_stages_name'),
    )


class RequirementSet(Base):
    """Requirement set model."""
    __tablename__ = "requirement_sets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    test_type = Column(String(50), nullable=False)
    metric_limits = Column(JSON, nullable=False)  # Stores list of MetricLimit
    pass_policy = Column(JSON)  # Stores PassPolicy
    requirement_hash = Column(String(64), nullable=False)  # SHA-256 hash of requirement set
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    test_runs = relationship("TestRun", back_populates="requirement_set")


class TestRun(Base):
    """Test run model (immutable after completion)."""
    __tablename__ = "test_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)
    test_stage_id = Column(Integer, ForeignKey("test_stages.id"), nullable=False)
    requirement_set_id = Column(Integer, ForeignKey("requirement_sets.id"), nullable=False)
    test_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="created")  # created, processing, completed, failed
    error_message = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime)
    
    # Relationships
    device = relationship("Device", back_populates="test_runs")
    test_stage = relationship("TestStage", back_populates="test_runs")
    requirement_set = relationship("RequirementSet", back_populates="test_runs")
    files = relationship("TestRunFile", back_populates="test_run", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint("status IN ('created', 'processing', 'completed', 'failed')", name='ck_test_runs_status'),
    )


class TestRunFile(Base):
    """Test run file model."""
    __tablename__ = "test_run_files"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    original_filename = Column(String(500), nullable=False)
    stored_path = Column(String(1000), nullable=False)
    effective_metadata = Column(JSON, nullable=False)  # Stores EffectiveMetadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    test_run = relationship("TestRun", back_populates="files")
    metrics = relationship("TestRunMetrics", back_populates="file", uselist=False, cascade="all, delete-orphan")
    compliance = relationship("TestRunCompliance", back_populates="file", uselist=False, cascade="all, delete-orphan")


class TestRunMetrics(Base):
    """Test run metrics model."""
    __tablename__ = "test_run_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("test_run_files.id"), nullable=False, unique=True)
    metrics = Column(JSON, nullable=False)  # Dictionary of metric arrays
    frequencies = Column(JSON, nullable=False)  # Frequency array
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    file = relationship("TestRunFile", back_populates="metrics")
    
    __table_args__ = (
        UniqueConstraint('file_id', name='uq_test_run_metrics_file_id'),
    )


class TestRunCompliance(Base):
    """Test run compliance model."""
    __tablename__ = "test_run_compliance"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    test_run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False)
    file_id = Column(Integer, ForeignKey("test_run_files.id"), nullable=False, unique=True)
    overall_pass = Column(Boolean, nullable=False)
    requirements = Column(JSON, nullable=False)  # List of requirement results
    failure_reasons = Column(JSON)  # List of failure reason strings
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    file = relationship("TestRunFile", back_populates="compliance")
    
    __table_args__ = (
        UniqueConstraint('file_id', name='uq_test_run_compliance_file_id'),
    )

