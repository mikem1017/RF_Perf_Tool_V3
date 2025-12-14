"""
Plotting system for S-parameter data.

Uses matplotlib to generate PNG plots.
This is a boundary component (writes filesystem).
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import numpy as np
from backend.src.core.schemas.plotting import PlotSpec, PlotConfig


def render_plot(plot_spec: PlotSpec, plot_config: PlotConfig, output_path: Path) -> Path:
    """
    Render a plot to PNG file.
    
    Args:
        plot_spec: Plot specification (what to plot)
        plot_config: Plot configuration (how to render)
        output_path: Path to output PNG file
    
    Returns:
        Path to generated PNG file
    """
    # Create figure
    fig, ax = plt.subplots(figsize=(plot_config.figure_width, plot_config.figure_height), dpi=plot_config.dpi)
    
    # Plot each series
    for series in plot_spec.series:
        # Convert frequency to appropriate unit if specified
        freq = np.array(series.frequency_hz)
        if plot_spec.x_unit == "GHz":
            freq = freq / 1e9
        elif plot_spec.x_unit == "MHz":
            freq = freq / 1e6
        
        # Determine line style based on trace identity
        if series.trace_identity == "PRI":
            linestyle = plot_config.line_style_pri
            color = plot_config.color_pri
        elif series.trace_identity == "RED":
            linestyle = plot_config.line_style_red
            color = plot_config.color_red
        else:
            linestyle = "solid"
            color = "blue"
        
        # Plot the series
        ax.plot(freq, series.values, label=series.label, linestyle=linestyle, color=color)
    
    # Set axis limits
    if plot_config.x_min is not None:
        ax.set_xlim(left=plot_config.x_min)
    if plot_config.x_max is not None:
        ax.set_xlim(right=plot_config.x_max)
    if plot_config.y_min is not None:
        ax.set_ylim(bottom=plot_config.y_min)
    if plot_config.y_max is not None:
        ax.set_ylim(top=plot_config.y_max)
    
    # Set labels
    x_label = plot_spec.x_label
    if plot_spec.x_unit:
        x_label = f"{x_label} ({plot_spec.x_unit})"
    ax.set_xlabel(x_label)
    ax.set_ylabel(plot_spec.y_label)
    
    # Set title and subtitle
    title = plot_spec.title
    if plot_spec.subtitle:
        title = f"{title}\n{plot_spec.subtitle}"
    ax.set_title(title)
    
    # Configure legend
    if plot_config.legend_visible:
        ax.legend(loc=plot_config.legend_location)
    
    # Configure grid
    if plot_config.grid_visible:
        ax.grid(True, alpha=plot_config.grid_alpha)
    
    # Save figure
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=plot_config.dpi, bbox_inches='tight')
    plt.close(fig)
    
    return output_path

