"""
Test run service - orchestrates the full analysis pipeline.

Pure business logic, no FastAPI dependencies.
Uses dependency injection for storage interfaces.
"""
from typing import List, Optional
from pathlib import Path
import numpy as np
from skrf import Network

from backend.src.storage.interfaces import IDatabase, IFileStorage
from backend.src.plugins.s_parameter.parser import parse_filename_metadata
from backend.src.plugins.s_parameter.loader import load_s_parameter_file
from backend.src.plugins.s_parameter.metrics import (
    compute_gain_db,
    compute_vswr,
    compute_return_loss_db,
    compute_gain_flatness,
)
from backend.src.plugins.s_parameter.compliance import evaluate_compliance
from backend.src.core.schemas.device import DeviceConfig, SParameterConfig
from backend.src.core.schemas.requirement_set import RequirementSet
from backend.src.core.schemas.metadata import EffectiveMetadata, UserOverrides
from backend.src.core.schemas.test_run import TestRunStatus


class TestRunService:
    """Service for processing test runs."""
    
    def __init__(self, database: IDatabase, file_storage: IFileStorage):
        """
        Initialize service with storage dependencies.
        
        Args:
            database: Database interface
            file_storage: File storage interface
        """
        self.db = database
        self.file_storage = file_storage
    
    def process_test_run(
        self,
        test_run_id: int,
        file_paths: List[Path],
        device_config: DeviceConfig,
        requirement_set: RequirementSet,
    ) -> None:
        """
        Process a test run: parse, load, compute, evaluate, plot.
        
        Args:
            test_run_id: Test run ID
            file_paths: List of S-parameter file paths to process
            device_config: Device configuration
            requirement_set: Requirement set for evaluation
        """
        # Update status to processing
        self.db.update_test_run_status(test_run_id, "processing")
        
        try:
            s_param_config = device_config.s_parameter_config
            if not s_param_config:
                raise ValueError("Device config must include S-parameter configuration")
            
            # Process each file
            for file_path in file_paths:
                # 1. Parse filename metadata
                filename = file_path.name
                parsed_metadata = parse_filename_metadata(filename)
                
                # 2. Load S-parameter file
                network = load_s_parameter_file(file_path)
                
                # 3. Store uploaded file
                file_content = file_path.read_bytes()
                stored_path = self.file_storage.store_uploaded_file(
                    test_run_id, filename, file_content
                )
                
                # 4. Create effective metadata (no overrides for now)
                effective_metadata = EffectiveMetadata.from_parsed_and_overrides(parsed_metadata)
                
                # 5. Add file to test run
                file_id = self.db.add_test_run_file(test_run_id, {
                    "original_filename": filename,
                    "stored_path": str(stored_path),
                    "effective_metadata": effective_metadata.model_dump(),
                })
                
                # 6. Compute metrics
                metrics_dict = self._compute_all_metrics(
                    network, s_param_config, device_config
                )
                
                # 7. Store metrics
                self.db.store_metrics(test_run_id, file_id, {
                    "metrics": {k: v.tolist() if isinstance(v, np.ndarray) else v 
                               for k, v in metrics_dict.items()},
                    "frequencies": network.f.tolist(),
                })
                
                # 8. Evaluate compliance
                compliance_result = evaluate_compliance(
                    metrics_dict,
                    network.f,
                    requirement_set,
                )
                
                # 9. Store compliance results
                self.db.store_compliance(test_run_id, file_id, {
                    "overall_pass": compliance_result.overall_pass,
                    "requirements": compliance_result.requirements,
                    "failure_reasons": compliance_result.failure_reasons,
                })
            
            # Update status to completed
            self.db.update_test_run_status(test_run_id, "completed")
            
        except Exception as e:
            # Update status to failed
            self.db.update_test_run_status(test_run_id, "failed", str(e))
            raise
    
    def _compute_all_metrics(
        self,
        network: Network,
        s_param_config: SParameterConfig,
        device_config: DeviceConfig,
    ) -> dict:
        """
        Compute all metrics for a network.
        
        Returns:
            Dictionary of metric arrays keyed by metric name
        """
        metrics = {}
        
        # Compute gain
        gain_db = compute_gain_db(network, s_param_config.gain_parameter)
        metrics["gain"] = gain_db
        
        # Compute VSWR
        vswr = compute_vswr(network, s_param_config.input_return_parameter)
        metrics["vswr"] = vswr
        
        # Compute return loss
        return_loss_db = compute_return_loss_db(
            network, s_param_config.input_return_parameter
        )
        metrics["return_loss"] = return_loss_db
        
        # Compute gain flatness (operational band)
        gain_flatness_op = compute_gain_flatness(
            gain_db, network.f, s_param_config.operational_band_hz
        )
        metrics["gain_flatness_operational"] = gain_flatness_op
        
        # Compute gain flatness (wideband)
        gain_flatness_wb = compute_gain_flatness(
            gain_db, network.f, s_param_config.wideband_band_hz
        )
        metrics["gain_flatness_wideband"] = gain_flatness_wb
        
        return metrics

