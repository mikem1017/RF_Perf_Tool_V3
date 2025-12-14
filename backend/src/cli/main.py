"""
CLI tool for RF Performance Tool.

Provides command-line interface for testing all functionality without UI.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import List

from backend.src.plugins.s_parameter.parser import parse_filename_metadata
from backend.src.plugins.s_parameter.loader import load_s_parameter_file
from backend.src.plugins.s_parameter.metrics import (
    compute_gain_db,
    compute_vswr,
    compute_return_loss_db,
    compute_gain_flatness,
)
from backend.src.plugins.s_parameter.compliance import evaluate_compliance
from backend.src.plugins.s_parameter.plotting import render_plot
from backend.src.core.schemas.device import DeviceConfig, SParameterConfig, FrequencyBand
from backend.src.core.schemas.requirement_set import RequirementSet, MetricLimit, PassPolicy
from backend.src.core.schemas.plotting import PlotSpec, PlotConfig, PlotSeries
from backend.src.storage.storage_service import StorageService
from backend.src.storage.database import create_database_engine, init_database
from backend.src.storage.sqlite_db import SQLiteDatabase
from sqlalchemy.orm import sessionmaker


def cmd_parse(args):
    """Parse filename metadata."""
    filename = args.filename
    parsed = parse_filename_metadata(filename)
    
    print(f"Parsed metadata from '{filename}':")
    print(f"  Serial Number: {parsed.serial_number or 'N/A'}")
    print(f"  Path: {parsed.path or 'N/A'}")
    print(f"  Part Number: {parsed.part_number or 'N/A'}")
    print(f"  Temperature: {parsed.temperature or 'N/A'}")
    print(f"  Date: {parsed.date or 'N/A'}")
    if parsed.missing_tokens:
        print(f"  Missing tokens: {', '.join(parsed.missing_tokens)}")
    if parsed.unknown_tokens:
        print(f"  Unknown tokens: {', '.join(parsed.unknown_tokens)}")
    
    return 0


def cmd_load(args):
    """Load S-parameter file."""
    file_path = Path(args.file_path)
    
    try:
        network = load_s_parameter_file(file_path)
        print(f"Successfully loaded {file_path}")
        print(f"  Ports: {network.nports}")
        print(f"  Frequency points: {len(network.f)}")
        print(f"  Frequency range: {network.f[0]:.2e} - {network.f[-1]:.2e} Hz")
        return 0
    except Exception as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        return 1


def cmd_compute(args):
    """Compute metrics from S-parameter file."""
    file_path = Path(args.file_path)
    config_path = Path(args.device_config)
    
    # Load device config
    with open(config_path) as f:
        config_data = json.load(f)
    device_config = DeviceConfig(**config_data)
    
    if not device_config.s_parameter_config:
        print("Error: Device config must include s_parameter_config", file=sys.stderr)
        return 1
    
    # Load network
    try:
        network = load_s_parameter_file(file_path)
    except SParameterLoadError as e:
        print(f"Error loading file: {e}", file=sys.stderr)
        return 1
    
    s_config = device_config.s_parameter_config
    
    # Compute metrics
    gain = compute_gain_db(network, s_config.gain_parameter)
    vswr = compute_vswr(network, s_config.input_return_parameter)
    return_loss = compute_return_loss_db(network, s_config.input_return_parameter)
    flatness = compute_gain_flatness(gain, network.f, s_config.operational_band_hz)
    
    print(f"Computed metrics for {file_path.name}:")
    print(f"  Gain ({s_config.gain_parameter}): min={gain.min():.2f} dB, max={gain.max():.2f} dB")
    print(f"  VSWR ({s_config.input_return_parameter}): min={vswr.min():.2f}, max={vswr.max():.2f}")
    print(f"  Return Loss ({s_config.input_return_parameter}): min={return_loss.min():.2f} dB, max={return_loss.max():.2f} dB")
    print(f"  Gain Flatness (operational band): {flatness:.2f} dB")
    
    # Optionally save to JSON
    if args.output:
        output_data = {
            "gain": gain.tolist(),
            "vswr": vswr.tolist(),
            "return_loss": return_loss.tolist(),
            "gain_flatness": flatness,
            "frequencies": network.f.tolist(),
        }
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"\nMetrics saved to {args.output}")
    
    return 0


def cmd_evaluate(args):
    """Evaluate compliance."""
    metrics_path = Path(args.metrics_json)
    requirements_path = Path(args.requirements_json)
    
    # Load metrics
    with open(metrics_path) as f:
        metrics_data = json.load(f)
    
    # Load requirements
    with open(requirements_path) as f:
        req_data = json.load(f)
    requirement_set = RequirementSet(**req_data)
    
    # Convert metrics to numpy arrays
    import numpy as np
    metrics = {
        k: np.array(v) if isinstance(v, list) else v
        for k, v in metrics_data.items()
        if k != "frequencies"
    }
    frequencies = np.array(metrics_data["frequencies"])
    
    # Evaluate
    result = evaluate_compliance(metrics, frequencies, requirement_set)
    
    print("Compliance Evaluation Results:")
    print(f"  Overall Pass: {result.overall_pass}")
    
    for req in result.requirements:
        status = "PASS" if req["passed"] else "FAIL"
        print(f"    {req['requirement_name']}: {status} (value={req['computed_value']:.2f}, limit={req['limit_value']:.2f})")
        if req.get("failure_reason"):
            print(f"      Reason: {req['failure_reason']}")
    
    return 0 if result.overall_pass else 1


def cmd_plot(args):
    """Generate plot."""
    spec_path = Path(args.spec_json)
    config_path = Path(args.config_json)
    output_path = Path(args.output)
    
    # Load plot spec and config
    with open(spec_path) as f:
        spec_data = json.load(f)
    with open(config_path) as f:
        config_data = json.load(f)
    
    plot_spec = PlotSpec(**spec_data)
    plot_config = PlotConfig(**config_data)
    
    # Render plot
    render_plot(plot_spec, plot_config, output_path)
    print(f"Plot saved to {output_path}")
    return 0


def cmd_run(args):
    """Run full pipeline."""
    test_run_id = args.test_run_id
    file_paths = [Path(p) for p in args.file_paths]
    device_config_path = Path(args.device_config)
    requirement_set_path = Path(args.requirement_set)
    
    # Load configs
    with open(device_config_path) as f:
        device_config = DeviceConfig(**json.load(f))
    with open(requirement_set_path) as f:
        requirement_set = RequirementSet(**json.load(f))
    
    # Initialize storage
    storage = StorageService(
        database_url=args.database_url or "sqlite:///rf_tool.db",
        file_storage_path=Path(args.storage_path or "results"),
    )
    
    # Create test run service
    from backend.src.services.test_run_service import TestRunService
    from backend.src.storage.interfaces import IStorageFactory
    
    # TestRunService expects IDatabase and IFileStorage, not IStorageFactory
    # So we need to pass the factory and let it create instances
    # Actually, looking at the service, it takes database and file_storage directly
    service = TestRunService(
        database=storage.create_database(),
        file_storage=storage.create_file_storage(),
    )
    
    # Process
    try:
        service.process_test_run(
            test_run_id=test_run_id,
            file_paths=file_paths,
            device_config=device_config,
            requirement_set=requirement_set,
        )
        print(f"Test run {test_run_id} processed successfully")
        return 0
    except Exception as e:
        print(f"Error processing test run: {e}", file=sys.stderr)
        return 1


def cmd_test_db(args):
    """Test database operations."""
    database_url = args.database_url or "sqlite:///:memory:"
    
    engine = create_database_engine(database_url)
    init_database(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    db = SQLiteDatabase(session)
    
    print("Testing database operations...")
    
    # Create device
    device_id = db.create_device({
        "name": "CLI Test Device",
        "s_parameter_config": {"gain_parameter": "S21"},
    })
    print(f"  Created device: ID={device_id}")
    
    # Get device
    device = db.get_device(device_id)
    print(f"  Retrieved device: {device['name']}")
    
    # Create test stage
    stage_id = db.create_test_stage({"name": "CLI Test Stage"})
    print(f"  Created test stage: ID={stage_id}")
    
    print("Database operations successful!")
    return 0


def cmd_test_storage(args):
    """Test file storage operations."""
    storage_path = Path(args.storage_path or "results")
    from backend.src.storage.file_storage import FilesystemFileStorage
    
    storage = FilesystemFileStorage(storage_path)
    
    print("Testing file storage operations...")
    
    # Store file
    test_content = b"test file content"
    stored_path = storage.store_uploaded_file(1, "test.s2p", test_content)
    print(f"  Stored file: {stored_path}")
    
    # Get file path
    retrieved_path = storage.get_file_path(1, "test.s2p")
    print(f"  Retrieved path: {retrieved_path}")
    
    # Store artifact
    artifact_path = storage.store_artifact(1, "plots", "test.png", b"fake png")
    print(f"  Stored artifact: {artifact_path}")
    
    print("File storage operations successful!")
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="RF Performance Tool CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Parse command
    parse_parser = subparsers.add_parser("parse", help="Parse filename metadata")
    parse_parser.add_argument("filename", help="Filename to parse")
    
    # Load command
    load_parser = subparsers.add_parser("load", help="Load S-parameter file")
    load_parser.add_argument("file_path", help="Path to S-parameter file")
    
    # Compute command
    compute_parser = subparsers.add_parser("compute", help="Compute metrics")
    compute_parser.add_argument("file_path", help="Path to S-parameter file")
    compute_parser.add_argument("device_config", help="Path to device config JSON")
    compute_parser.add_argument("--output", help="Output JSON file for metrics")
    
    # Evaluate command
    eval_parser = subparsers.add_parser("evaluate", help="Evaluate compliance")
    eval_parser.add_argument("metrics_json", help="Path to metrics JSON file")
    eval_parser.add_argument("requirements_json", help="Path to requirements JSON file")
    
    # Plot command
    plot_parser = subparsers.add_parser("plot", help="Generate plot")
    plot_parser.add_argument("spec_json", help="Path to plot spec JSON")
    plot_parser.add_argument("config_json", help="Path to plot config JSON")
    plot_parser.add_argument("output", help="Output PNG file path")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run full pipeline")
    run_parser.add_argument("test_run_id", type=int, help="Test run ID")
    run_parser.add_argument("file_paths", nargs="+", help="S-parameter file paths")
    run_parser.add_argument("device_config", help="Path to device config JSON")
    run_parser.add_argument("requirement_set", help="Path to requirement set JSON")
    run_parser.add_argument("--database-url", help="Database URL (default: sqlite:///rf_tool.db)")
    run_parser.add_argument("--storage-path", help="Storage path (default: results)")
    
    # Test DB command
    test_db_parser = subparsers.add_parser("test-db", help="Test database operations")
    test_db_parser.add_argument("--database-url", help="Database URL (default: sqlite:///:memory:)")
    
    # Test storage command
    test_storage_parser = subparsers.add_parser("test-storage", help="Test file storage operations")
    test_storage_parser.add_argument("--storage-path", help="Storage path (default: results)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Route to command handler
    commands = {
        "parse": cmd_parse,
        "load": cmd_load,
        "compute": cmd_compute,
        "evaluate": cmd_evaluate,
        "plot": cmd_plot,
        "run": cmd_run,
        "test-db": cmd_test_db,
        "test-storage": cmd_test_storage,
    }
    
    handler = commands.get(args.command)
    if handler:
        return handler(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

