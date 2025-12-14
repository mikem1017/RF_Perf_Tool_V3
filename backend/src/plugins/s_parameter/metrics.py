"""
S-parameter metrics computation.

Pure functions for computing RF metrics from S-parameter networks.
No side effects, no I/O operations.
"""
import numpy as np
from skrf import Network
from backend.src.core.schemas.device import FrequencyBand


def compute_gain_db(network: Network, sij_param: str) -> np.ndarray:
    """
    Compute gain in dB from S-parameter.
    
    Formula: Gain(dB) = 20 * log10(|Sij|)
    
    Args:
        network: scikit-rf Network object
        sij_param: S-parameter to use (e.g., "S21", "S31")
    
    Returns:
        Array of gain values in dB for each frequency point
    """
    # Extract port numbers from sij_param (e.g., "S21" -> i=2, j=1)
    i = int(sij_param[1])
    j = int(sij_param[2])
    
    # Get S-parameter (0-indexed, so subtract 1)
    s_ij = network.s[:, i-1, j-1]
    
    # Compute magnitude
    s_mag = np.abs(s_ij)
    
    # Compute gain in dB: 20 * log10(|Sij|)
    gain_db = 20 * np.log10(s_mag)
    
    return gain_db


def compute_vswr(network: Network, sii_param: str) -> np.ndarray:
    """
    Compute VSWR from return loss S-parameter.
    
    Formula: VSWR = (1 + |Γ|) / (1 - |Γ|), where Γ = |Sii|
    
    Args:
        network: scikit-rf Network object
        sii_param: Return S-parameter to use (e.g., "S11", "S22")
    
    Returns:
        Array of VSWR values for each frequency point
    """
    # Extract port number from sii_param (e.g., "S11" -> i=1)
    i = int(sii_param[1])
    
    # Get S-parameter (0-indexed, so subtract 1)
    s_ii = network.s[:, i-1, i-1]
    
    # Compute magnitude (reflection coefficient)
    gamma_mag = np.abs(s_ii)
    
    # Compute VSWR: (1 + |Γ|) / (1 - |Γ|)
    # Handle edge case where gamma_mag = 1 (infinite VSWR)
    with np.errstate(divide='ignore', invalid='ignore'):
        vswr = (1 + gamma_mag) / (1 - gamma_mag)
        # Set infinite values to a large number (e.g., 1000)
        vswr = np.where(np.isfinite(vswr), vswr, 1000.0)
    
    return vswr


def compute_return_loss_db(network: Network, sii_param: str) -> np.ndarray:
    """
    Compute return loss in dB from S-parameter.
    
    Formula: ReturnLoss(dB) = -20 * log10(|Sii|)
    
    Args:
        network: scikit-rf Network object
        sii_param: Return S-parameter to use (e.g., "S11", "S22")
    
    Returns:
        Array of return loss values in dB for each frequency point
    """
    # Extract port number from sii_param (e.g., "S11" -> i=1)
    i = int(sii_param[1])
    
    # Get S-parameter (0-indexed, so subtract 1)
    s_ii = network.s[:, i-1, i-1]
    
    # Compute magnitude
    s_mag = np.abs(s_ii)
    
    # Handle zero values (infinite return loss)
    with np.errstate(divide='ignore'):
        return_loss_db = -20 * np.log10(s_mag)
        # Set infinite values to a large number (e.g., 100 dB)
        return_loss_db = np.where(np.isfinite(return_loss_db), return_loss_db, 100.0)
    
    return return_loss_db


def compute_gain_flatness(
    gain_db: np.ndarray,
    frequencies: np.ndarray,
    band: FrequencyBand
) -> float:
    """
    Compute gain flatness (peak-to-peak variation) over a frequency band.
    
    Args:
        gain_db: Array of gain values in dB
        frequencies: Array of frequency values in Hz
        band: Frequency band to evaluate
    
    Returns:
        Peak-to-peak gain variation in dB over the specified band
    """
    # Find frequencies within the band
    mask = (frequencies >= band.start_hz) & (frequencies <= band.stop_hz)
    
    if not np.any(mask):
        raise ValueError(f"No frequency points found in band {band.start_hz} to {band.stop_hz} Hz")
    
    # Extract gain values within the band
    band_gain = gain_db[mask]
    
    # Compute peak-to-peak (max - min)
    gain_flatness = np.max(band_gain) - np.min(band_gain)
    
    return float(gain_flatness)

