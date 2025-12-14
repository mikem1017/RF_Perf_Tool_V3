"""
Plotting models (PlotSpec and PlotConfig).
"""
from pydantic import BaseModel, Field
from typing import Optional
import numpy as np


class PlotSeries(BaseModel):
    """Data series for plotting."""
    frequency_hz: list[float] = Field(..., description="Frequency array in Hz")
    values: list[float] = Field(..., description="Y-axis values")
    label: str = Field(..., description="Series label")
    trace_identity: Optional[str] = Field(None, description="Trace identity (e.g., PRI, RED)")
    parameter_identity: Optional[str] = Field(None, description="Parameter identity (e.g., Gain S21)")

    class Config:
        arbitrary_types_allowed = True


class PlotSpec(BaseModel):
    """Plot specification (what to plot)."""
    series: list[PlotSeries] = Field(..., description="Data series to plot")
    title: str = Field(..., description="Plot title")
    subtitle: Optional[str] = Field(None, description="Plot subtitle (metadata)")
    x_label: str = Field(default="Frequency (Hz)", description="X-axis label")
    y_label: str = Field(..., description="Y-axis label")
    x_unit: Optional[str] = Field(None, description="X-axis unit (e.g., 'GHz')")
    y_unit: Optional[str] = Field(None, description="Y-axis unit (e.g., 'dB')")


class PlotConfig(BaseModel):
    """Plot configuration (how to render)."""
    x_min: Optional[float] = Field(None, description="X-axis minimum")
    x_max: Optional[float] = Field(None, description="X-axis maximum")
    y_min: Optional[float] = Field(None, description="Y-axis minimum")
    y_max: Optional[float] = Field(None, description="Y-axis maximum")
    legend_visible: bool = Field(default=True, description="Show legend")
    legend_location: str = Field(default="best", description="Legend location")
    grid_visible: bool = Field(default=True, description="Show grid")
    grid_alpha: float = Field(default=0.3, ge=0.0, le=1.0, description="Grid transparency")
    figure_width: float = Field(default=10.0, gt=0, description="Figure width in inches")
    figure_height: float = Field(default=6.0, gt=0, description="Figure height in inches")
    dpi: int = Field(default=100, gt=0, description="DPI for export")
    line_style_pri: str = Field(default="solid", description="Line style for PRI")
    line_style_red: str = Field(default="dashed", description="Line style for RED")
    color_pri: str = Field(default="blue", description="Color for PRI")
    color_red: str = Field(default="red", description="Color for RED")

