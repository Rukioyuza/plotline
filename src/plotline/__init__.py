"""plotline: small zero-dependency charts rendered to SVG."""

from .charts import PALETTE, BarChart, Chart, LineChart, ScatterChart, Series
from .scale import BandScale, LinearScale
from .ticks import format_tick, nice_number, nice_ticks

__all__ = [
    "PALETTE",
    "BandScale",
    "BarChart",
    "Chart",
    "LineChart",
    "LinearScale",
    "ScatterChart",
    "Series",
    "format_tick",
    "nice_number",
    "nice_ticks",
]

__version__ = "0.1.0"
