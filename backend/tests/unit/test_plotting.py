"""
Tests for plotting system.
"""
import pytest
from pathlib import Path
from backend.src.plugins.s_parameter.plotting import render_plot
from backend.src.core.schemas.plotting import (
    PlotSpec,
    PlotConfig,
    PlotSeries,
)


def create_sample_plot_spec() -> PlotSpec:
    """Create a sample plot specification."""
    series = PlotSeries(
        frequency_hz=[1e9, 2e9, 3e9],
        values=[-10.0, -9.0, -8.0],
        label="PRI Gain",
        trace_identity="PRI",
        parameter_identity="Gain S21",
    )
    return PlotSpec(
        series=[series],
        title="Test Plot",
        subtitle="SN1234, PRI, L567890",
        y_label="Gain (dB)",
        x_label="Frequency",
        x_unit="GHz",
    )


def test_render_plot_basic(temp_dir):
    """Test basic plot rendering."""
    plot_spec = create_sample_plot_spec()
    plot_config = PlotConfig()
    output_path = temp_dir / "test_plot.png"
    
    result_path = render_plot(plot_spec, plot_config, output_path)
    
    assert result_path == output_path
    assert output_path.exists()
    assert output_path.stat().st_size > 1000  # File should be reasonable size


def test_render_plot_file_exists(temp_dir):
    """Test that plot file is created."""
    plot_spec = create_sample_plot_spec()
    plot_config = PlotConfig()
    output_path = temp_dir / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    assert output_path.exists()
    assert output_path.suffix == ".png"


def test_render_plot_file_size(temp_dir):
    """Test that plot file has reasonable size."""
    plot_spec = create_sample_plot_spec()
    plot_config = PlotConfig()
    output_path = temp_dir / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    file_size = output_path.stat().st_size
    assert file_size > 5000  # PNG should be at least 5KB


def test_render_plot_pri_red_styling(temp_dir):
    """Test PRI vs RED line styling."""
    pri_series = PlotSeries(
        frequency_hz=[1e9, 2e9],
        values=[-10.0, -9.0],
        label="PRI Gain",
        trace_identity="PRI",
    )
    red_series = PlotSeries(
        frequency_hz=[1e9, 2e9],
        values=[-11.0, -10.0],
        label="RED Gain",
        trace_identity="RED",
    )
    plot_spec = PlotSpec(
        series=[pri_series, red_series],
        title="Gain Comparison",
        y_label="Gain (dB)",
    )
    plot_config = PlotConfig(
        line_style_pri="solid",
        line_style_red="dashed",
        color_pri="blue",
        color_red="red",
    )
    output_path = temp_dir / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    assert output_path.exists()


def test_render_plot_axis_limits(temp_dir):
    """Test axis limits application."""
    plot_spec = create_sample_plot_spec()
    plot_config = PlotConfig(
        x_min=0.5,
        x_max=3.5,
        y_min=-15.0,
        y_max=-5.0,
    )
    output_path = temp_dir / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    assert output_path.exists()


def test_render_plot_subtitle(temp_dir):
    """Test subtitle generation."""
    plot_spec = PlotSpec(
        series=[create_sample_plot_spec().series[0]],
        title="Gain Plot",
        subtitle="SN1234, PRI, L567890, AMB, 2024-01-01",
        y_label="Gain (dB)",
    )
    plot_config = PlotConfig()
    output_path = temp_dir / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    assert output_path.exists()


def test_render_plot_legend(temp_dir):
    """Test legend visibility."""
    plot_spec = create_sample_plot_spec()
    plot_config = PlotConfig(legend_visible=True, legend_location="upper right")
    output_path = temp_dir / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    assert output_path.exists()


def test_render_plot_no_legend(temp_dir):
    """Test plot without legend."""
    plot_spec = create_sample_plot_spec()
    plot_config = PlotConfig(legend_visible=False)
    output_path = temp_dir / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    assert output_path.exists()


def test_render_plot_grid(temp_dir):
    """Test grid visibility."""
    plot_spec = create_sample_plot_spec()
    plot_config = PlotConfig(grid_visible=True, grid_alpha=0.3)
    output_path = temp_dir / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    assert output_path.exists()


def test_render_plot_frequency_unit_conversion(temp_dir):
    """Test frequency unit conversion (Hz to GHz)."""
    series = PlotSeries(
        frequency_hz=[1e9, 2e9, 3e9],  # 1, 2, 3 GHz
        values=[-10.0, -9.0, -8.0],
        label="Gain",
    )
    plot_spec = PlotSpec(
        series=[series],
        title="Gain",
        y_label="Gain (dB)",
        x_unit="GHz",
    )
    plot_config = PlotConfig()
    output_path = temp_dir / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    assert output_path.exists()


def test_render_plot_creates_directory(temp_dir):
    """Test that plot creates parent directory if needed."""
    plot_spec = create_sample_plot_spec()
    plot_config = PlotConfig()
    output_path = temp_dir / "subdir" / "test_plot.png"
    
    render_plot(plot_spec, plot_config, output_path)
    
    assert output_path.exists()
    assert output_path.parent.exists()
