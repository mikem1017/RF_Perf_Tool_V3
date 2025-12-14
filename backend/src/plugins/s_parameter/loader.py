"""
S-parameter file loader using scikit-rf.

Supports S2P, S3P, S4P file formats.
This is a boundary component (reads filesystem).
"""
from pathlib import Path
from typing import Union
import skrf as rf
from skrf import Network


def load_s_parameter_file(file_path: Union[str, Path]) -> Network:
    """
    Load an S-parameter file using scikit-rf.
    
    Args:
        file_path: Path to S-parameter file (.s2p, .s3p, .s4p)
    
    Returns:
        scikit-rf Network object
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid or unsupported
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"S-parameter file not found: {file_path}")
    
    # Check file extension
    suffix = file_path.suffix.lower()
    if suffix not in ('.s1p', '.s2p', '.s3p', '.s4p'):
        raise ValueError(f"Unsupported S-parameter file format: {suffix}. Supported: .s1p, .s2p, .s3p, .s4p")
    
    try:
        # Load network using scikit-rf
        network = rf.Network(str(file_path))
        return network
    except Exception as e:
        raise ValueError(f"Failed to load S-parameter file {file_path}: {str(e)}") from e

