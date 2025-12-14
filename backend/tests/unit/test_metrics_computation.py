"""
Tests for metrics computation.
"""
import pytest
import numpy as np
import skrf as rf
from backend.src.plugins.s_parameter.metrics import (
    compute_gain_db,
    compute_vswr,
    compute_return_loss_db,
    compute_gain_flatness,
)
from backend.src.core.schemas.device import FrequencyBand


def create_test_network_2port() -> rf.Network:
    """Create a simple 2-port test network."""
    # Create a network with known S-parameters
    freq = rf.Frequency(1e9, 2e9, 2, unit='Hz')
    
    # S-parameters: S21 = 0.5 (magnitude), S11 = 0.1 (magnitude)
    # For S21 = 0.5: Gain = 20*log10(0.5) ≈ -6.02 dB
    # For S11 = 0.1: Return Loss = -20*log10(0.1) = 20 dB
    # VSWR = (1 + 0.1) / (1 - 0.1) = 1.1 / 0.9 ≈ 1.222
    
    s = np.zeros((2, 2, 2), dtype=complex)  # 2 freq, 2 ports, 2 ports
    
    # Frequency 1: 1 GHz
    s[0, 0, 0] = 0.1 + 0j  # S11
    s[0, 1, 0] = 0.5 + 0j  # S21
    s[0, 0, 1] = 0.5 + 0j  # S12
    s[0, 1, 1] = 0.1 + 0j  # S22
    
    # Frequency 2: 2 GHz
    s[1, 0, 0] = 0.1 + 0j  # S11
    s[1, 1, 0] = 0.4 + 0j  # S21 (different for flatness test)
    s[1, 0, 1] = 0.4 + 0j  # S12
    s[1, 1, 1] = 0.1 + 0j  # S22
    
    network = rf.Network(frequency=freq, s=s)
    return network


def test_compute_gain_db():
    """Test gain computation with known S-parameter values."""
    network = create_test_network_2port()
    gain = compute_gain_db(network, "S21")
    
    # S21 = 0.5 -> Gain = 20*log10(0.5) ≈ -6.02 dB
    expected_gain_1 = 20 * np.log10(0.5)
    assert np.isclose(gain[0], expected_gain_1, rtol=1e-3)
    
    # S21 = 0.4 -> Gain = 20*log10(0.4) ≈ -7.96 dB
    expected_gain_2 = 20 * np.log10(0.4)
    assert np.isclose(gain[1], expected_gain_2, rtol=1e-3)


def test_compute_gain_db_formula():
    """Test gain formula: 20*log10(|Sxy|)."""
    network = create_test_network_2port()
    gain = compute_gain_db(network, "S21")
    
    # Verify formula
    s21_mag = np.abs(network.s[:, 1, 0])
    expected = 20 * np.log10(s21_mag)
    np.testing.assert_allclose(gain, expected, rtol=1e-6)


def test_compute_vswr():
    """Test VSWR computation with known S-parameter values."""
    network = create_test_network_2port()
    vswr = compute_vswr(network, "S11")
    
    # S11 = 0.1 -> VSWR = (1 + 0.1) / (1 - 0.1) = 1.1 / 0.9 ≈ 1.222
    expected_vswr = (1 + 0.1) / (1 - 0.1)
    assert np.isclose(vswr[0], expected_vswr, rtol=1e-3)


def test_compute_vswr_formula():
    """Test VSWR formula: (1 + |Γ|) / (1 - |Γ|)."""
    network = create_test_network_2port()
    vswr = compute_vswr(network, "S11")
    
    # Verify formula
    s11_mag = np.abs(network.s[:, 0, 0])
    expected = (1 + s11_mag) / (1 - s11_mag)
    np.testing.assert_allclose(vswr, expected, rtol=1e-6)


def test_compute_vswr_perfect_match():
    """Test VSWR with perfect match (S11 = 0)."""
    freq = rf.Frequency(1e9, 1e9, 1, unit='Hz')
    s = np.zeros((1, 2, 2), dtype=complex)
    s[0, 0, 0] = 0.0 + 0j  # Perfect match
    network = rf.Network(frequency=freq, s=s)
    
    vswr = compute_vswr(network, "S11")
    # Perfect match: VSWR = 1.0
    assert np.isclose(vswr[0], 1.0, rtol=1e-6)


def test_compute_return_loss_db():
    """Test return loss computation with known S-parameter values."""
    network = create_test_network_2port()
    return_loss = compute_return_loss_db(network, "S11")
    
    # S11 = 0.1 -> Return Loss = -20*log10(0.1) = 20 dB
    expected_rl = -20 * np.log10(0.1)
    assert np.isclose(return_loss[0], expected_rl, rtol=1e-3)


def test_compute_return_loss_db_formula():
    """Test return loss formula: -20*log10(|Sii|)."""
    network = create_test_network_2port()
    return_loss = compute_return_loss_db(network, "S11")
    
    # Verify formula
    s11_mag = np.abs(network.s[:, 0, 0])
    expected = -20 * np.log10(s11_mag)
    np.testing.assert_allclose(return_loss, expected, rtol=1e-6)


def test_compute_return_loss_perfect_match():
    """Test return loss with perfect match (S11 = 0)."""
    freq = rf.Frequency(1e9, 1e9, 1, unit='Hz')
    s = np.zeros((1, 2, 2), dtype=complex)
    s[0, 0, 0] = 0.0 + 0j  # Perfect match
    network = rf.Network(frequency=freq, s=s)
    
    return_loss = compute_return_loss_db(network, "S11")
    # Perfect match: return loss should be very high (handled as 100 dB)
    assert return_loss[0] >= 100.0


def test_compute_gain_flatness():
    """Test gain flatness computation."""
    network = create_test_network_2port()
    gain = compute_gain_db(network, "S21")
    frequencies = network.f
    
    # Band from 1e9 to 2e9 Hz
    band = FrequencyBand(start_hz=1e9, stop_hz=2e9)
    flatness = compute_gain_flatness(gain, frequencies, band)
    
    # Gain at 1 GHz: 20*log10(0.5) ≈ -6.02 dB
    # Gain at 2 GHz: 20*log10(0.4) ≈ -7.96 dB
    # Flatness = -6.02 - (-7.96) = 1.94 dB
    expected_flatness = 20 * np.log10(0.5) - 20 * np.log10(0.4)
    assert np.isclose(flatness, expected_flatness, rtol=1e-2)


def test_compute_gain_flatness_out_of_band():
    """Test gain flatness with out-of-band frequencies."""
    network = create_test_network_2port()
    gain = compute_gain_db(network, "S21")
    frequencies = network.f
    
    # Band outside the network frequencies
    band = FrequencyBand(start_hz=3e9, stop_hz=4e9)
    
    with pytest.raises(ValueError, match="No frequency points found"):
        compute_gain_flatness(gain, frequencies, band)


def test_compute_gain_db_different_sij():
    """Test gain computation with different Sij parameters."""
    network = create_test_network_2port()
    
    # Test S21
    gain_s21 = compute_gain_db(network, "S21")
    assert len(gain_s21) == 2
    
    # Test S12 (should be same as S21 in this test network)
    gain_s12 = compute_gain_db(network, "S12")
    np.testing.assert_allclose(gain_s21, gain_s12, rtol=1e-6)


def test_compute_vswr_different_sii():
    """Test VSWR computation with different Sii parameters."""
    network = create_test_network_2port()
    
    # Test S11
    vswr_s11 = compute_vswr(network, "S11")
    assert len(vswr_s11) == 2
    
    # Test S22 (should be same as S11 in this test network)
    vswr_s22 = compute_vswr(network, "S22")
    np.testing.assert_allclose(vswr_s11, vswr_s22, rtol=1e-6)

